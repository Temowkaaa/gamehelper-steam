from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import webbrowser
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse
from urllib.request import Request, urlopen


ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", ROOT))
PUBLIC_DIR = BUNDLE_ROOT / "public"
DATA_DIR = ROOT / "data"
IMAGE_CACHE_DIR = DATA_DIR / "image_cache"
APP_NAMES_CACHE = DATA_DIR / "steam_app_names.json"
APP_NAME_FAILURES_CACHE = DATA_DIR / "steam_app_name_failures.json"
BUNDLED_APP_NAMES_CACHE = BUNDLE_ROOT / "data" / "steam_app_names.json"
APP_NAME_FAILURE_TTL = 7 * 24 * 60 * 60
STEAM_API = "https://api.steampowered.com"
SAM_RELEASE_API = "https://api.github.com/repos/gibbed/SteamAchievementManager/releases/latest"
SAM_DIR = ROOT / "tools" / "SteamAchievementManager"

APP_CONFIG: dict[str, Any] = {}
for config_path in (BUNDLE_ROOT / "app_config.json", ROOT / "app_config.json"):
    if not config_path.exists():
        continue
    try:
        APP_CONFIG = json.loads(config_path.read_text(encoding="utf-8"))
        break
    except (OSError, json.JSONDecodeError):
        pass

APP_VERSION = os.getenv("GAMEHELPER_VERSION", str(APP_CONFIG.get("version") or "1.0.0"))
GITHUB_REPO = os.getenv("GAMEHELPER_GITHUB_REPO", str(APP_CONFIG.get("githubRepo") or ""))
GITHUB_RELEASE_API = (
    os.getenv("GAMEHELPER_RELEASE_API")
    or (f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest" if GITHUB_REPO else "")
)
INSTALLER_ASSET_RE = re.compile(r"GameHelperSteamSetup.*\.exe$", re.IGNORECASE)
KNOWN_APP_NAMES = {
    218: "Source SDK Base 2007",
    480: "Spacewar",
    745: "Counter-Strike: Global Offensive - SDK",
    760: "Steam Screenshots",
    205790: "Dota 2 Test",
    226410: "RIDGE RACER™ Driftopia",
    391750: "Rust SDK",
    1024020: "DayZ Experimental",
    1523600: "Builder Simulator Demo",
    1874390: "CROWZ Demo",
    2122820: "Manor Lords Demo",
    2654630: "Soulmask Demo",
    3092450: "inZOI: Creative Studio",
    3772580: "Car Service Together Demo",
}
STEAM_UTILITY_APP_IDS = {7, 760, 228980}
STEAM_ID64_OFFSET = 76561197960265728
STEAM_IMAGE_TYPES = {
    "capsule": ("capsule_184x69.jpg", "image/jpeg"),
    "header": ("header.jpg", "image/jpeg"),
}
KV_TYPE_NONE = 0
KV_TYPE_STRING = 1
KV_TYPE_INT32 = 2
KV_TYPE_FLOAT32 = 3
KV_TYPE_POINTER = 4
KV_TYPE_WIDE_STRING = 5
KV_TYPE_COLOR = 6
KV_TYPE_UINT64 = 7
KV_TYPE_END = 8


class ApiError(Exception):
    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


def request_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "gamehelper/1.0"})
    try:
        with urlopen(request, timeout=8) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code == 403:
            raise ApiError(
                "Steam отклонил запрос. Проверь API key и публичность профиля.",
                403,
            ) from error
        raise ApiError(f"Steam API вернул ошибку HTTP {error.code}.", error.code) from error
    except URLError as error:
        raise ApiError(f"Не удалось подключиться к Steam API: {error.reason}.", 502) from error
    except json.JSONDecodeError as error:
        raise ApiError("Steam API вернул неожиданный ответ.", 502) from error


def request_json_optional(url: str) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "gamehelper/1.0"})
    try:
        with urlopen(request, timeout=8) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, json.JSONDecodeError):
        return {}


def request_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "gamehelper/1.0"})
    try:
        with urlopen(request, timeout=6) as response:
            return response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError):
        return ""


def request_bytes(url: str, timeout: int = 60) -> bytes:
    request = Request(url, headers={"User-Agent": "gamehelper/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read()
    except HTTPError as error:
        raise ApiError(f"Не удалось скачать файл: HTTP {error.code}.", error.code) from error
    except URLError as error:
        raise ApiError(f"Не удалось подключиться для скачивания: {error.reason}.", 502) from error


def detect_image_content_type(body: bytes) -> str | None:
    if body.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if body.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if body.startswith(b"RIFF") and body[8:12] == b"WEBP":
        return "image/webp"
    return None


def version_parts(version: str) -> tuple[int, ...]:
    text = str(version or "").strip().lstrip("vV")
    parts = re.findall(r"\d+", text)
    return tuple(int(part) for part in parts[:4]) if parts else (0,)


def load_update_info() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "configured": bool(GITHUB_RELEASE_API),
        "currentVersion": APP_VERSION,
        "latestVersion": APP_VERSION,
        "updateAvailable": False,
        "releaseUrl": "",
        "installerUrl": "",
    }
    if not GITHUB_RELEASE_API:
        return payload

    release = request_json_optional(GITHUB_RELEASE_API)
    latest_tag = str(release.get("tag_name") or release.get("name") or APP_VERSION).strip()
    release_url = str(release.get("html_url") or "")
    installer_url = ""
    for asset in release.get("assets") or []:
        if not isinstance(asset, dict):
            continue
        name = str(asset.get("name") or "")
        browser_download_url = str(asset.get("browser_download_url") or "")
        if browser_download_url and INSTALLER_ASSET_RE.search(name):
            installer_url = browser_download_url
            break

    payload.update(
        {
            "latestVersion": latest_tag.lstrip("vV") or APP_VERSION,
            "updateAvailable": version_parts(latest_tag) > version_parts(APP_VERSION),
            "releaseUrl": release_url,
            "installerUrl": installer_url,
        }
    )
    return payload


def cached_steam_image_url(app_id: int, image_type: str) -> str:
    return f"/api/image?appid={app_id}&type={quote(image_type)}"


def image_cache_path(app_id: int, image_type: str) -> Path:
    image_name, _ = STEAM_IMAGE_TYPES[image_type]
    return IMAGE_CACHE_DIR / str(app_id) / image_name


def fetch_store_image_urls(app_id: int, image_type: str) -> list[str]:
    url = "https://store.steampowered.com/api/appdetails?" + urlencode(
        {
            "appids": app_id,
            "filters": "basic",
            "cc": "us",
            "l": "english",
        }
    )
    try:
        data = request_json(url).get(str(app_id), {})
    except ApiError:
        return []

    if not data.get("success"):
        return []

    details = data.get("data") or {}
    if not isinstance(details, dict):
        return []

    if image_type == "header":
        keys = ("header_image", "capsule_imagev5", "capsule_image")
    else:
        keys = ("capsule_image", "capsule_imagev5", "header_image")

    urls = []
    for key in keys:
        value = details.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            urls.append(value)
    return urls


def steam_image_candidates(app_id: int, image_type: str) -> list[str]:
    image_name, _ = STEAM_IMAGE_TYPES[image_type]
    urls = [
        f"https://cdn.cloudflare.steamstatic.com/steam/apps/{app_id}/{image_name}",
        f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/{image_name}",
        f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{app_id}/{image_name}",
    ]
    urls.extend(fetch_store_image_urls(app_id, image_type))
    return list(dict.fromkeys(urls))


def read_or_download_steam_image(app_id: int, image_type: str) -> tuple[bytes, str]:
    if image_type not in STEAM_IMAGE_TYPES:
        raise ApiError("Некорректный тип изображения.", 400)

    cache_path = image_cache_path(app_id, image_type)
    _, content_type = STEAM_IMAGE_TYPES[image_type]
    if cache_path.exists() and cache_path.stat().st_size > 0:
        body = cache_path.read_bytes()
        detected_content_type = detect_image_content_type(body)
        if detected_content_type:
            return body, detected_content_type
        try:
            cache_path.unlink()
        except OSError:
            pass

    last_error: ApiError | None = None
    for url in steam_image_candidates(app_id, image_type):
        try:
            body = request_bytes(url, timeout=12)
        except ApiError as error:
            last_error = error
            continue

        detected_content_type = detect_image_content_type(body)
        if not body or not detected_content_type:
            last_error = ApiError("Steam вернул некорректное изображение.", 502)
            continue

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(body)
        return body, detected_content_type

    raise last_error or ApiError("Не удалось найти изображение игры в Steam.", 404)


def load_cached_app_names() -> dict[int, str]:
    names = dict(KNOWN_APP_NAMES)
    for cache_path in (BUNDLED_APP_NAMES_CACHE, APP_NAMES_CACHE):
        if not cache_path.exists():
            continue
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            names.update({int(app_id): normalize_app_name(name, int(app_id)) for app_id, name in cached.items()})
        except (OSError, ValueError, TypeError):
            pass
    return names


def save_cached_app_names(names: dict[int, str]) -> None:
    try:
        DATA_DIR.mkdir(exist_ok=True)
        names = {app_id: normalize_app_name(name, app_id) for app_id, name in names.items()}
        APP_NAMES_CACHE.write_text(
            json.dumps(names, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
    except OSError:
        pass


def load_failed_app_name_lookups() -> dict[int, float]:
    if not APP_NAME_FAILURES_CACHE.exists():
        return {}
    try:
        cached = json.loads(APP_NAME_FAILURES_CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    now = time.time()
    return {
        int(app_id): float(timestamp)
        for app_id, timestamp in cached.items()
        if str(app_id).isdigit() and now - float(timestamp) < APP_NAME_FAILURE_TTL
    }


def save_failed_app_name_lookups(failures: dict[int, float]) -> None:
    try:
        DATA_DIR.mkdir(exist_ok=True)
        APP_NAME_FAILURES_CACHE.write_text(
            json.dumps(failures, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
    except OSError:
        pass


def is_placeholder_name(app_id: int, name: Any) -> bool:
    return not name or str(name).strip() == f"App {app_id}"


def normalize_app_name(name: Any, app_id: int | None = None) -> str:
    text = re.sub(r"\s+", " ", str(name or "")).strip()
    for prefix in ("Steam Community ::", "Steam Community:"):
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix) :].strip()
    if text.lower() in {"steam community", "site error", "error", "access denied"}:
        return f"App {app_id}" if app_id else ""
    return text or (f"App {app_id}" if app_id else "")


def clean_page_title(title: str, marker: str) -> str | None:
    title = unescape(title).strip()
    if title.endswith(marker):
        title = title[: -len(marker)].strip()
    if title.startswith(marker):
        title = title[len(marker) :].strip()
    title = re.sub(r"\s+", " ", title)
    title = normalize_app_name(title)
    if not title or title.lower() in {"welcome to steam", "steam community", "error", "access denied"}:
        return None
    return title


def fetch_title_name(url: str, suffix: str) -> str | None:
    text = request_text(url)
    match = re.search(r"<title>\s*(.*?)\s*</title>", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return clean_page_title(match.group(1), suffix)


def fetch_store_app_name(app_id: int) -> str | None:
    url = "https://store.steampowered.com/api/appdetails?" + urlencode(
        {"appids": str(app_id), "filters": "basic", "cc": "us", "l": "english"}
    )
    try:
        payload = request_json(url)
    except ApiError:
        payload = {}

    app_payload = payload.get(str(app_id), {})
    if app_payload.get("success") is True:
        data = app_payload.get("data", {})
        name = data.get("name")
        if name:
            return normalize_app_name(name, app_id)

    name = (
        fetch_title_name(f"https://store.steampowered.com/app/{app_id}", " on Steam")
        or fetch_title_name(f"https://steamcommunity.com/app/{app_id}", "Steam Community ::")
    )
    return normalize_app_name(name, app_id) if name else None


def fill_missing_app_names(games: dict[int, dict[str, Any]]) -> dict[int, str]:
    names = {
        app_id: name
        for app_id, name in load_cached_app_names().items()
        if not is_placeholder_name(app_id, name)
    }
    failures = load_failed_app_name_lookups()
    missing = [
        app_id
        for app_id, game in games.items()
        if is_placeholder_name(app_id, game.get("name"))
    ]
    missing = [app_id for app_id in missing if app_id not in names and app_id not in failures]
    if missing:
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(fetch_store_app_name, app_id): app_id for app_id in missing}
            for future in as_completed(futures):
                try:
                    name = future.result()
                except Exception:
                    name = None
                if name:
                    names[futures[future]] = name
                else:
                    failures[futures[future]] = time.time()

        still_missing = [app_id for app_id in missing if app_id not in names and app_id not in failures]
        for app_id in still_missing:
            time.sleep(0.15)
            try:
                name = fetch_store_app_name(app_id)
            except Exception:
                name = None
            if name:
                names[app_id] = name
                failures.pop(app_id, None)
            else:
                failures[app_id] = time.time()
        save_cached_app_names(names)
        save_failed_app_name_lookups(failures)
    return names


def parse_vdf(text: str) -> dict[str, Any]:
    tokens = re.findall(r'"((?:\\.|[^"\\])*)"|([{}])', text)
    root: dict[str, Any] = {}
    stack = [root]
    pending_key: str | None = None

    for raw_string, brace in tokens:
        if brace == "{":
            if pending_key is None:
                continue
            child: dict[str, Any] = {}
            stack[-1][pending_key] = child
            stack.append(child)
            pending_key = None
            continue
        if brace == "}":
            if len(stack) > 1:
                stack.pop()
            pending_key = None
            continue

        value = raw_string.replace(r"\"", '"').replace(r"\\", "\\")
        if pending_key is None:
            pending_key = value
        else:
            stack[-1][pending_key] = value
            pending_key = None

    return root


def read_vdf(path: Path) -> dict[str, Any]:
    try:
        return parse_vdf(path.read_text(encoding="utf-8", errors="replace"))
    except OSError as error:
        raise ApiError(f"Не удалось прочитать {path}: {error}", 500) from error


def find_steam_path() -> Path:
    candidates = []
    if sys.platform == "win32":
        try:
            import winreg

            for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                for subkey in (
                    r"Software\Valve\Steam",
                    r"Software\WOW6432Node\Valve\Steam",
                ):
                    try:
                        with winreg.OpenKey(root, subkey) as key:
                            value, _ = winreg.QueryValueEx(key, "SteamPath")
                            candidates.append(Path(value))
                    except OSError:
                        pass
        except ImportError:
            pass
        candidates.extend(
            [
                Path(os.environ.get("ProgramFiles(x86)", "")) / "Steam",
                Path(os.environ.get("ProgramFiles", "")) / "Steam",
            ]
        )
    else:
        candidates.extend(
            [
                Path.home() / ".steam" / "steam",
                Path.home() / ".local" / "share" / "Steam",
            ]
        )

    for candidate in candidates:
        if candidate and (candidate / "steamapps").exists():
            return candidate
    raise ApiError("Не удалось найти установленный Steam на этом компьютере.", 404)


def find_library_paths(steam_path: Path) -> list[Path]:
    libraries = [steam_path]
    libraryfolders = steam_path / "steamapps" / "libraryfolders.vdf"
    if libraryfolders.exists():
        data = read_vdf(libraryfolders).get("libraryfolders", {})
        if isinstance(data, dict):
            for value in data.values():
                if isinstance(value, dict) and value.get("path"):
                    libraries.append(Path(str(value["path"])))

    unique = []
    seen = set()
    for library in libraries:
        normalized = str(library).lower()
        if normalized not in seen and (library / "steamapps").exists():
            seen.add(normalized)
            unique.append(library)
    return unique


def steam_id64_to_account_id(steam_id: int) -> int:
    return steam_id - STEAM_ID64_OFFSET


def account_id_to_steam_id64(account_id: int) -> int:
    return account_id + STEAM_ID64_OFFSET


def load_steam_accounts(steam_path: Path) -> list[dict[str, Any]]:
    accounts_by_id: dict[int, dict[str, Any]] = {}
    loginusers = steam_path / "config" / "loginusers.vdf"
    if loginusers.exists():
        data = read_vdf(loginusers).get("users", {})
        if isinstance(data, dict):
            for raw_steam_id, user in data.items():
                if not str(raw_steam_id).isdigit() or not isinstance(user, dict):
                    continue
                steam_id = int(raw_steam_id)
                account_id = steam_id64_to_account_id(steam_id)
                persona = user.get("PersonaName") or user.get("AccountName") or str(account_id)
                accounts_by_id[account_id] = {
                    "accountId": str(account_id),
                    "steamId": str(steam_id),
                    "name": str(persona),
                    "accountName": str(user.get("AccountName") or ""),
                    "mostRecent": str(user.get("MostRecent") or "0") == "1",
                }

    userdata = steam_path / "userdata"
    if userdata.exists():
        for folder in userdata.iterdir():
            if not folder.is_dir() or not folder.name.isdigit():
                continue
            account_id = int(folder.name)
            accounts_by_id.setdefault(
                account_id,
                {
                    "accountId": str(account_id),
                    "steamId": str(account_id_to_steam_id64(account_id)),
                    "name": folder.name,
                    "accountName": "",
                    "mostRecent": False,
                },
            )

    return sorted(
        accounts_by_id.values(),
        key=lambda account: (not account["mostRecent"], account["name"].lower()),
    )


def select_account(steam_path: Path, account_id: str | None = None) -> dict[str, Any]:
    accounts = load_steam_accounts(steam_path)
    if not accounts:
        raise ApiError("Не удалось найти локальные Steam-аккаунты в папке userdata.", 404)
    if account_id:
        for account in accounts:
            if account["accountId"] == account_id:
                return account
        raise ApiError("Выбранный Steam-аккаунт не найден в локальных данных.", 404)
    return next((account for account in accounts if account["mostRecent"]), accounts[0])


def load_installed_games(libraries: list[Path]) -> dict[int, dict[str, Any]]:
    games: dict[int, dict[str, Any]] = {}
    for library in libraries:
        for manifest_path in (library / "steamapps").glob("appmanifest_*.acf"):
            data = read_vdf(manifest_path).get("AppState", {})
            if not isinstance(data, dict) or not str(data.get("appid", "")).isdigit():
                continue
            app_id = int(data["appid"])
            games[app_id] = {
                "appid": app_id,
                "name": normalize_app_name(data.get("name"), app_id),
                "minutes": 0,
                "lastPlayed": int(data.get("LastUpdated") or 0),
                "source": "installed",
            }
    return games


def load_installed_game_names(libraries: list[Path]) -> dict[int, str]:
    names = {}
    for app_id, game in load_installed_games(libraries).items():
        if game.get("name"):
            names[app_id] = normalize_app_name(game["name"], app_id)
    return names


def find_apps_sections(value: Any) -> list[dict[str, Any]]:
    sections = []
    if not isinstance(value, dict):
        return sections
    for key, child in value.items():
        if key.lower() == "apps" and isinstance(child, dict):
            if any(str(app_id).isdigit() and isinstance(app, dict) for app_id, app in child.items()):
                sections.append(child)
        sections.extend(find_apps_sections(child))
    return sections


def load_account_playtime(steam_path: Path, account_id: str) -> dict[int, dict[str, Any]]:
    localconfig = steam_path / "userdata" / account_id / "config" / "localconfig.vdf"
    if not localconfig.exists():
        raise ApiError(f"Для аккаунта {account_id} не найден localconfig.vdf.", 404)

    games: dict[int, dict[str, Any]] = {}
    data = read_vdf(localconfig)
    for apps in find_apps_sections(data):
        for raw_app_id, app_data in apps.items():
            if not str(raw_app_id).isdigit() or not isinstance(app_data, dict):
                continue
            app_id = int(raw_app_id)
            minutes = int(app_data.get("Playtime") or 0)
            last_played = int(app_data.get("LastPlayed") or 0)
            existing = games.get(app_id)
            if existing:
                existing["minutes"] = max(int(existing.get("minutes", 0)), minutes)
                existing["lastPlayed"] = max(int(existing.get("lastPlayed", 0)), last_played)
                if is_placeholder_name(app_id, existing.get("name")) and app_data.get("Name"):
                    existing["name"] = normalize_app_name(app_data["Name"], app_id)
                continue
            games[app_id] = {
                "appid": app_id,
                "name": normalize_app_name(app_data.get("Name"), app_id),
                "minutes": minutes,
                "lastPlayed": last_played,
                "source": "account-local-cache",
            }
    return games


def load_account_app_metadata(steam_path: Path, account_id: str) -> dict[str, set[int]]:
    localconfig = steam_path / "userdata" / account_id / "config" / "localconfig.vdf"
    if not localconfig.exists():
        return {"tickets": set(), "userConfig": set()}

    data = read_vdf(localconfig)
    store = data.get("UserLocalConfigStore", {})
    if not isinstance(store, dict):
        return {"tickets": set(), "userConfig": set()}

    tickets = {
        int(app_id)
        for app_id in (store.get("apptickets", {}) or {}).keys()
        if str(app_id).isdigit()
    }
    user_config = {
        int(app_id)
        for app_id in (store.get("UserAppConfig", {}) or {}).keys()
        if str(app_id).isdigit()
    }
    return {"tickets": tickets, "userConfig": user_config}


def load_local_games(fetch_names: bool = True, account_id: str | None = None) -> dict[str, Any]:
    steam_path = find_steam_path()
    libraries = find_library_paths(steam_path)
    accounts = load_steam_accounts(steam_path)
    account = dict(select_account(steam_path, account_id))
    account["avatarUrl"] = f"/api/avatar?steam_id={quote(account['steamId'])}"
    installed_names = load_installed_game_names(libraries)
    games = load_account_playtime(steam_path, account["accountId"])
    account_app_metadata = load_account_app_metadata(steam_path, account["accountId"])
    for app_id, name in installed_names.items():
        if app_id in games and games[app_id].get("name") == f"App {app_id}":
            games[app_id]["name"] = name
    app_names = fill_missing_app_names(games) if fetch_names else load_cached_app_names()

    normalized_games = []
    total_minutes = 0
    played_games = 0
    for game in games.values():
        app_id = int(game["appid"])
        minutes = int(game.get("minutes", 0))
        name = game.get("name")
        if is_placeholder_name(app_id, name):
            name = app_names.get(app_id, f"App {app_id}")
        name = normalize_app_name(name, app_id)
        is_placeholder = is_placeholder_name(app_id, name)
        has_account_ticket = app_id in account_app_metadata["tickets"]
        has_user_config = app_id in account_app_metadata["userConfig"]
        is_installed = app_id in installed_names
        account_linked = minutes > 0 or has_account_ticket or has_user_config
        if int(game.get("lastPlayed", 0)) > 86400:
            played_games += 1
        total_minutes += minutes
        normalized_games.append(
            {
                "appid": app_id,
                "name": name,
                "minutes": minutes,
                "hours": round(minutes / 60, 1),
                "lastPlayed": int(game.get("lastPlayed", 0)),
                "accountLinked": account_linked,
                "hasAccountTicket": has_account_ticket,
                "hasUserConfig": has_user_config,
                "isInstalled": is_installed,
                "isSteamUtility": app_id in STEAM_UTILITY_APP_IDS,
                "isPlaceholderName": is_placeholder,
                "iconUrl": cached_steam_image_url(app_id, "capsule"),
                "storeUrl": f"https://store.steampowered.com/app/{app_id}/",
            }
        )

    normalized_games.sort(key=lambda item: (-item["minutes"], item["name"].lower()))

    return {
        "steamId": "local",
        "source": "local",
        "steamPath": str(steam_path),
        "account": account,
        "accounts": accounts,
        "namesUpdated": fetch_names,
        "gameCount": len(normalized_games),
        "playedGames": played_games,
        "totalMinutes": total_minutes,
        "totalHours": round(total_minutes / 60, 1),
        "games": normalized_games,
    }


def find_sam_files() -> dict[str, str | None]:
    candidates = [
        ROOT / "SAM.Game.exe",
        ROOT / "SAM.Picker.exe",
        SAM_DIR / "SAM.Game.exe",
        SAM_DIR / "SAM.Picker.exe",
    ]
    for folder in (ROOT / "tools", SAM_DIR):
        if folder.exists():
            candidates.extend(folder.rglob("SAM.Game.exe"))
            candidates.extend(folder.rglob("SAM.Picker.exe"))

    game_exe = None
    picker_exe = None
    for candidate in candidates:
        if not candidate.exists():
            continue
        name = candidate.name.lower()
        if name == "sam.game.exe" and not game_exe:
            game_exe = str(candidate)
        if name == "sam.picker.exe" and not picker_exe:
            picker_exe = str(candidate)
    return {"gameExe": game_exe, "pickerExe": picker_exe}


def get_sam_status() -> dict[str, Any]:
    files = find_sam_files()
    helper = find_sam_helper()
    return {
        "installed": bool(helper),
        "integrated": bool(helper),
        "helperExe": helper,
        "gameExe": files["gameExe"],
        "pickerExe": files["pickerExe"],
        "installDir": str(SAM_DIR),
    }


def find_sam_helper() -> str | None:
    candidates = [
        ROOT / "SamHelper" / "bin" / "x86" / "Release" / "GameHelper.SamHelper.exe",
        BUNDLE_ROOT / "SamHelper" / "GameHelper.SamHelper.exe",
        ROOT / "SamHelper" / "GameHelper.SamHelper.exe",
    ]
    return next((str(path) for path in candidates if path.exists()), None)


def run_sam_helper(args: list[str]) -> dict[str, Any]:
    helper = find_sam_helper()
    if not helper:
        raise ApiError("Встроенный SAM helper не найден. Пересобери приложение.", 500)
    env = dict(os.environ)
    env["GAMEHELPER_STEAM_PATH"] = str(find_steam_path())
    process = subprocess.run(
        [helper, *args],
        cwd=str(Path(helper).parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        timeout=25,
    )
    output = (process.stdout or "").strip()
    try:
        payload = json.loads(output) if output else {}
    except json.JSONDecodeError as error:
        raise ApiError(f"SAM helper вернул неожиданный ответ: {output}", 500) from error
    if process.returncode != 0 or payload.get("ok") is False:
        raise ApiError(str(payload.get("error") or "SAM helper завершился с ошибкой."), 500)
    return payload


def load_sam_achievements(app_id: int) -> dict[str, Any]:
    definitions = load_achievement_definitions(app_id)
    if not definitions:
        return {"ok": True, "appid": app_id, "total": 0, "unlocked": 0, "achievements": []}
    states = run_sam_helper(["states", str(app_id), *[item["id"] for item in definitions]])
    states_by_id = {item["id"]: item for item in states.get("achievements", [])}
    achievements = []
    for definition in definitions:
        state = states_by_id.get(definition["id"], {})
        is_achieved = bool(state.get("isAchieved"))
        unlock_time = int(state.get("unlockTime") or 0)
        achievements.append(
            {
                **definition,
                "isAchieved": is_achieved,
                "unlockTime": unlock_time,
                "canEdit": achievement_can_edit(definition),
                "icon": achievement_icon_url(
                    app_id,
                    definition["iconNormal"] if is_achieved else definition["iconLocked"] or definition["iconNormal"],
                ),
            }
        )
    return {
        "ok": True,
        "appid": app_id,
        "total": len(achievements),
        "unlocked": sum(1 for item in achievements if item["isAchieved"]),
        "achievements": achievements,
    }


def load_sam_catalog() -> dict[str, Any]:
    steam_path = find_steam_path()
    schema_dir = steam_path / "appcache" / "stats"
    games = []
    if not schema_dir.exists():
        return {"ok": True, "games": games}

    for schema_path in schema_dir.glob("UserGameStatsSchema_*.bin"):
        app_id_text = schema_path.stem.removeprefix("UserGameStatsSchema_")
        if not app_id_text.isdigit():
            continue
        try:
            definitions = load_achievement_definitions(int(app_id_text))
        except ApiError:
            continue
        total = len(definitions)
        if total <= 0:
            continue
        protected = sum(1 for item in definitions if not achievement_can_edit(item))
        games.append(
            {
                "appid": int(app_id_text),
                "total": total,
                "protected": protected,
                "allProtected": protected == total,
                "partlyProtected": 0 < protected < total,
            }
        )
    return {"ok": True, "games": games}


def set_sam_achievement(app_id: int, achievement_id: str, achieved: bool) -> dict[str, Any]:
    if not achievement_id:
        raise ApiError("Не указан ID достижения.", 400)
    definition = next((item for item in load_achievement_definitions(app_id) if item["id"] == achievement_id), None)
    if definition and not achievement_can_edit(definition):
        raise ApiError("Это достижение защищено Steam или самой игрой и не меняется локально.", 400)
    return run_sam_helper(["set" if achieved else "clear", str(app_id), achievement_id])


def achievement_can_edit(definition: dict[str, Any]) -> bool:
    return (int(definition.get("permission") or 0) & 3) == 0


def achievement_icon_url(app_id: int, icon: str) -> str:
    if not icon:
        return ""
    if icon.startswith("http://") or icon.startswith("https://"):
        return icon
    return f"https://cdn.cloudflare.steamstatic.com/steamcommunity/public/images/apps/{app_id}/{icon}"


def read_c_string(data: bytes, offset: int) -> tuple[str, int]:
    end = data.index(0, offset)
    return data[offset:end].decode("utf-8", errors="replace"), end + 1


def parse_binary_kv_nodes(data: bytes, offset: int = 0) -> tuple[list[dict[str, Any]], int]:
    nodes = []
    length = len(data)
    while offset < length:
        value_type = data[offset]
        offset += 1
        if value_type == KV_TYPE_END:
            break
        name, offset = read_c_string(data, offset)
        node: dict[str, Any] = {"name": name, "type": value_type}
        if value_type == KV_TYPE_NONE:
            children, offset = parse_binary_kv_nodes(data, offset)
            node["children"] = children
        elif value_type == KV_TYPE_STRING:
            node["value"], offset = read_c_string(data, offset)
        elif value_type == KV_TYPE_INT32:
            node["value"] = int.from_bytes(data[offset : offset + 4], "little", signed=True)
            offset += 4
        elif value_type in (KV_TYPE_FLOAT32, KV_TYPE_COLOR, KV_TYPE_POINTER):
            node["value"] = int.from_bytes(data[offset : offset + 4], "little", signed=False)
            offset += 4
        elif value_type == KV_TYPE_UINT64:
            node["value"] = int.from_bytes(data[offset : offset + 8], "little", signed=False)
            offset += 8
        else:
            raise ApiError(f"Неизвестный тип Steam KV {value_type} в схеме достижений.", 500)
        nodes.append(node)
    return nodes, offset


def child(node: dict[str, Any], name: str) -> dict[str, Any] | None:
    for item in node.get("children", []):
        if str(item.get("name", "")).lower() == name.lower():
            return item
    return None


def children_named(node: dict[str, Any], name: str) -> list[dict[str, Any]]:
    return [item for item in node.get("children", []) if str(item.get("name", "")).lower() == name.lower()]


def node_value(node: dict[str, Any] | None, default: Any = "") -> Any:
    if not node:
        return default
    return node.get("value", default)


def localized_value(node: dict[str, Any] | None, language: str, default: str) -> str:
    if not node:
        return default
    if "value" in node:
        return str(node["value"])
    return str(node_value(child(node, language), node_value(child(node, "english"), default)))


def load_achievement_definitions(app_id: int) -> list[dict[str, Any]]:
    steam_path = find_steam_path()
    schema_path = steam_path / "appcache" / "stats" / f"UserGameStatsSchema_{app_id}.bin"
    if not schema_path.exists():
        raise ApiError("Steam не нашел локальную схему достижений. Открой страницу игры в Steam или запусти игру один раз.", 404)
    nodes, _ = parse_binary_kv_nodes(schema_path.read_bytes())
    root = next((item for item in nodes if item["name"] == str(app_id)), None)
    stats = child(root, "stats") if root else None
    if not stats:
        return []

    language = "english"
    definitions = []
    for stat in stats.get("children", []):
        stat_type = str(node_value(child(stat, "type"), "")).lower()
        stat_type_int = int(node_value(child(stat, "type_int"), 0) or 0)
        if stat_type not in {"achievements", "groupachievements"} and stat_type_int not in {4, 5}:
            continue
        for bits in children_named(stat, "bits"):
            for bit in bits.get("children", []):
                display = child(bit, "display") or {}
                achievement_id = str(node_value(child(bit, "name"), ""))
                if not achievement_id:
                    continue
                definitions.append(
                    {
                        "id": achievement_id,
                        "name": localized_value(child(display, "name"), language, achievement_id),
                        "description": localized_value(child(display, "desc"), language, ""),
                        "isHidden": bool(int(node_value(child(display, "hidden"), 0) or 0)),
                        "permission": int(node_value(child(bit, "permission"), 0) or 0),
                        "iconNormal": str(node_value(child(display, "icon"), "")),
                        "iconLocked": str(node_value(child(display, "icon_gray"), "")),
                    }
                )
    return definitions


def install_sam() -> dict[str, Any]:
    release = request_json(SAM_RELEASE_API)
    asset = next(
        (
            item
            for item in release.get("assets", [])
            if isinstance(item, dict)
            and str(item.get("name", "")).lower().endswith(".zip")
            and item.get("browser_download_url")
        ),
        None,
    )
    if not asset:
        raise ApiError("В последнем релизе SteamAchievementManager не найден zip-архив.", 502)

    SAM_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = SAM_DIR / str(asset["name"])
    archive_path.write_bytes(request_bytes(str(asset["browser_download_url"])))
    with zipfile.ZipFile(archive_path) as archive:
        safe_extract_zip(archive, SAM_DIR)

    status = get_sam_status()
    if not status["installed"]:
        raise ApiError("SAM скачан, но SAM.Game.exe или SAM.Picker.exe не найден.", 500)
    status["version"] = release.get("tag_name", "")
    return status


def safe_extract_zip(archive: zipfile.ZipFile, target_dir: Path) -> None:
    root = target_dir.resolve()
    for member in archive.infolist():
        destination = (target_dir / member.filename).resolve()
        if root != destination and root not in destination.parents:
            raise ApiError("Архив SAM содержит некорректный путь.", 400)
    archive.extractall(target_dir)


def launch_sam(app_id: int | None = None) -> dict[str, Any]:
    files = find_sam_files()
    executable = files["gameExe"] if app_id else files["pickerExe"] or files["gameExe"]
    if not executable:
        raise ApiError("SteamAchievementManager не найден. Сначала установи SAM.", 404)

    command = [executable]
    if app_id and Path(executable).name.lower() == "sam.game.exe":
        command.append(str(app_id))
    subprocess.Popen(command, cwd=str(Path(executable).parent), close_fds=True)
    return {"ok": True, "launched": executable}


def extract_profile_id(raw_value: str) -> str:
    value = unquote(raw_value.strip())
    if not value:
        raise ApiError("Укажи SteamID64, vanity name или ссылку на профиль.")

    if re.fullmatch(r"\d{17}", value):
        return value

    if value.startswith("steamcommunity.com/"):
        value = f"https://{value}"
    parsed = urlparse(value if "://" in value else f"https://steamcommunity.com/{value}")
    path_parts = [part for part in parsed.path.split("/") if part]

    if len(path_parts) >= 2 and path_parts[0].lower() == "profiles":
        steam_id = path_parts[1]
        if re.fullmatch(r"\d{17}", steam_id):
            return steam_id
        raise ApiError("В ссылке profiles ожидается SteamID64 из 17 цифр.")

    if len(path_parts) >= 2 and path_parts[0].lower() == "id":
        return path_parts[1]

    return value.removesuffix("/")


def resolve_steam_id(profile: str, api_key: str) -> str:
    profile_id = extract_profile_id(profile)
    if re.fullmatch(r"\d{17}", profile_id):
        return profile_id

    url = (
        f"{STEAM_API}/ISteamUser/ResolveVanityURL/v0001/"
        f"?key={quote(api_key)}&vanityurl={quote(profile_id)}"
    )
    payload = request_json(url)
    response = payload.get("response", {})
    if response.get("success") != 1 or not response.get("steamid"):
        raise ApiError("Не удалось найти Steam-профиль по этому vanity name.")
    return str(response["steamid"])


def load_owned_games(steam_id: str, api_key: str, include_free: bool) -> dict[str, Any]:
    include_free_flag = "1" if include_free else "0"
    url = (
        f"{STEAM_API}/IPlayerService/GetOwnedGames/v0001/"
        f"?key={quote(api_key)}&steamid={quote(steam_id)}&format=json"
        f"&include_appinfo=1&include_played_free_games={include_free_flag}"
    )
    payload = request_json(url)
    games = payload.get("response", {}).get("games")
    if games is None:
        raise ApiError(
            "Steam не отдал список игр. Обычно это значит, что профиль или игровая статистика закрыты.",
            403,
        )

    normalized_games = []
    total_minutes = 0
    played_games = 0

    for game in games:
        minutes = int(game.get("playtime_forever", 0))
        app_id = int(game["appid"])
        if minutes > 0:
            played_games += 1
        total_minutes += minutes
        normalized_games.append(
            {
                "appid": app_id,
                "name": game.get("name", f"App {app_id}"),
                "minutes": minutes,
                "hours": round(minutes / 60, 1),
                "lastPlayed": int(game.get("rtime_last_played", 0)),
                "iconUrl": cached_steam_image_url(app_id, "capsule"),
                "storeUrl": f"https://store.steampowered.com/app/{app_id}/",
            }
        )

    normalized_games.sort(key=lambda item: (-item["minutes"], item["name"].lower()))

    return {
        "steamId": steam_id,
        "gameCount": len(normalized_games),
        "playedGames": played_games,
        "totalMinutes": total_minutes,
        "totalHours": round(total_minutes / 60, 1),
        "games": normalized_games,
    }


def games_to_csv(games: list[dict[str, Any]]) -> str:
    lines = ["AppID;Название;Часы;Минуты;Последний запуск"]
    for game in games:
        last_played = ""
        if int(game.get("lastPlayed", 0)):
            from datetime import datetime

            last_played = datetime.fromtimestamp(int(game["lastPlayed"])).strftime("%d.%m.%Y")
        name = str(game["name"]).replace('"', '""')
        hours = str(game["hours"]).replace(".", ",")
        lines.append(f'{game["appid"]};"{name}";{hours};{game["minutes"]};{last_played}')
    return "\ufeff" + "\n".join(lines)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/sh.ico", "/back.png"}:
            self.path = parsed.path
            self.directory = str(BUNDLE_ROOT)
            return super().do_GET()
        if parsed.path == "/api/image":
            self.handle_image_api(parsed.query)
            return
        if parsed.path == "/api/avatar":
            self.handle_avatar_api(parsed.query)
            return
        if parsed.path == "/api/games":
            self.handle_games_api(parsed.query)
            return
        if parsed.path == "/api/local-games":
            self.handle_local_games_api(parsed.query)
            return
        if parsed.path == "/api/update":
            self.handle_update_api()
            return
        if parsed.path == "/api/update/open":
            self.handle_update_open_api()
            return
        if parsed.path == "/api/sam/status":
            self.handle_sam_status_api()
            return
        if parsed.path == "/api/sam/catalog":
            self.handle_sam_catalog_api()
            return
        if parsed.path == "/api/sam/install":
            self.handle_sam_install_api()
            return
        if parsed.path == "/api/sam/open":
            self.handle_sam_open_api(parsed.query)
            return
        if parsed.path == "/api/sam/achievements":
            self.handle_sam_achievements_api(parsed.query)
            return
        if parsed.path == "/api/sam/achievement":
            self.handle_sam_achievement_api(parsed.query)
            return
        if parsed.path == "/api/export.csv":
            self.handle_export_api()
            return
        super().do_GET()

    def handle_games_api(self, query: str) -> None:
        params = parse_qs(query)
        api_key = first_param(params, "api_key") or os.getenv("STEAM_API_KEY", "")
        profile = first_param(params, "profile")
        include_free = first_param(params, "include_free") != "0"

        try:
            if not api_key:
                raise ApiError("Укажи Steam Web API key или переменную окружения STEAM_API_KEY.")
            if not profile:
                raise ApiError("Укажи SteamID64, vanity name или ссылку на профиль.")
            steam_id = resolve_steam_id(profile, api_key)
            self.write_json(load_owned_games(steam_id, api_key, include_free))
        except ApiError as error:
            self.write_json({"error": str(error)}, error.status)
        except Exception as error:
            self.write_json({"error": f"Непредвиденная ошибка: {error}"}, 500)

    def handle_local_games_api(self, query: str) -> None:
        params = parse_qs(query)
        fetch_names = first_param(params, "fetch_names") == "1"
        account_id = first_param(params, "account_id") or None
        try:
            self.write_json(load_local_games(fetch_names=fetch_names, account_id=account_id))
        except ApiError as error:
            self.write_json({"error": str(error)}, error.status)
        except Exception as error:
            self.write_json({"error": f"Непредвиденная ошибка: {error}"}, 500)

    def handle_update_api(self) -> None:
        try:
            self.write_json(load_update_info())
        except Exception as error:
            self.write_json({"error": f"Непредвиденная ошибка: {error}"}, 500)

    def handle_update_open_api(self) -> None:
        try:
            info = load_update_info()
            url = info.get("installerUrl") or info.get("releaseUrl")
            if not url:
                raise ApiError("Ссылка на обновление пока не настроена.", 404)
            webbrowser.open(str(url))
            self.write_json({"ok": True, "url": url})
        except ApiError as error:
            self.write_json({"error": str(error)}, error.status)
        except Exception as error:
            self.write_json({"error": f"Непредвиденная ошибка: {error}"}, 500)

    def handle_export_api(self) -> None:
        try:
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            account_id = first_param(params, "account_id") or None
            payload = load_local_games(fetch_names=False, account_id=account_id)
            body = games_to_csv(payload["games"]).encode("utf-8-sig")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="steam_hours.csv"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except ApiError as error:
            self.write_json({"error": str(error)}, error.status)
        except Exception as error:
            self.write_json({"error": f"Непредвиденная ошибка: {error}"}, 500)

    def handle_sam_status_api(self) -> None:
        try:
            self.write_json(get_sam_status())
        except Exception as error:
            self.write_json({"error": f"Непредвиденная ошибка: {error}"}, 500)

    def handle_sam_catalog_api(self) -> None:
        try:
            self.write_json(load_sam_catalog())
        except ApiError as error:
            self.write_json({"error": str(error)}, error.status)
        except Exception as error:
            self.write_json({"error": f"Непредвиденная ошибка: {error}"}, 500)

    def handle_sam_install_api(self) -> None:
        try:
            self.write_json(install_sam())
        except ApiError as error:
            self.write_json({"error": str(error)}, error.status)
        except Exception as error:
            self.write_json({"error": f"Непредвиденная ошибка: {error}"}, 500)

    def handle_sam_open_api(self, query: str) -> None:
        try:
            app_id = first_param(parse_qs(query), "appid")
            self.write_json(launch_sam(int(app_id) if app_id.isdigit() else None))
        except ApiError as error:
            self.write_json({"error": str(error)}, error.status)
        except Exception as error:
            self.write_json({"error": f"Непредвиденная ошибка: {error}"}, 500)

    def handle_sam_achievements_api(self, query: str) -> None:
        try:
            app_id = first_param(parse_qs(query), "appid")
            if not app_id.isdigit():
                raise ApiError("Выбери игру для загрузки достижений.", 400)
            self.write_json(load_sam_achievements(int(app_id)))
        except ApiError as error:
            self.write_json({"error": str(error)}, error.status)
        except Exception as error:
            self.write_json({"error": f"Непредвиденная ошибка: {error}"}, 500)

    def handle_sam_achievement_api(self, query: str) -> None:
        try:
            params = parse_qs(query)
            app_id = first_param(params, "appid")
            achievement_id = first_param(params, "id")
            achieved = first_param(params, "achieved") == "1"
            if not app_id.isdigit():
                raise ApiError("Выбери игру для изменения достижения.", 400)
            self.write_json(set_sam_achievement(int(app_id), achievement_id, achieved))
        except ApiError as error:
            self.write_json({"error": str(error)}, error.status)
        except Exception as error:
            self.write_json({"error": f"Непредвиденная ошибка: {error}"}, 500)

    def handle_avatar_api(self, query: str) -> None:
        steam_id = first_param(parse_qs(query), "steam_id")
        if not re.fullmatch(r"\d{17}", steam_id):
            self.write_json({"error": "Некорректный SteamID."}, 400)
            return

        try:
            steam_path = find_steam_path()
            avatar_path = steam_path / "config" / "avatarcache" / f"{steam_id}.png"
            if not avatar_path.exists():
                self.write_json({"error": "Аватар не найден в локальном кеше Steam."}, 404)
                return
            body = avatar_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Cache-Control", "public, max-age=3600")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except ApiError as error:
            self.write_json({"error": str(error)}, error.status)
        except Exception as error:
            self.write_json({"error": f"Непредвиденная ошибка: {error}"}, 500)

    def handle_image_api(self, query: str) -> None:
        params = parse_qs(query)
        app_id = first_param(params, "appid")
        image_type = first_param(params, "type") or "capsule"
        if not app_id.isdigit():
            self.write_json({"error": "Некорректный AppID."}, 400)
            return
        try:
            body, content_type = read_or_download_steam_image(int(app_id), image_type)
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "public, max-age=2592000")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except ApiError as error:
            self.write_json({"error": str(error)}, error.status)
        except Exception as error:
            self.write_json({"error": f"Непредвиденная ошибка: {error}"}, 500)

    def write_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def first_param(params: dict[str, list[str]], name: str) -> str:
    values = params.get(name, [])
    return values[0].strip() if values else ""


def main() -> None:
    port = int(os.getenv("PORT", sys.argv[1] if len(sys.argv) > 1 else "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"GameHelper running at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")


if __name__ == "__main__":
    main()
