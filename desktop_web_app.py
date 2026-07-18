from __future__ import annotations

import socket
import sys
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path

import webview

from app import Handler


APP_ID = "GameHelper.Steam.Local"
MAIN_WIDTH = 1360
MAIN_HEIGHT = 930


def resource_path(name: str) -> Path:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return root / name


def set_windows_app_id() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass


def set_dark_titlebar(title: str) -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes

        hwnd = None
        for _ in range(30):
            hwnd = ctypes.windll.user32.FindWindowW(None, title)
            if hwnd:
                break
            time.sleep(0.1)
        if not hwnd:
            return

        enabled = ctypes.c_int(1)
        caption_color = wintypes.DWORD(0x00171310)
        text_color = wintypes.DWORD(0x00F8F3EE)

        for attr in (20, 19):
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                attr,
                ctypes.byref(enabled),
                ctypes.sizeof(enabled),
            )
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            35,
            ctypes.byref(caption_color),
            ctypes.sizeof(caption_color),
        )
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            36,
            ctypes.byref(text_color),
            ctypes.sizeof(text_color),
        )
    except Exception:
        pass


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def start_server(port: int) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def main() -> None:
    set_windows_app_id()
    port = find_free_port()
    server = start_server(port)
    icon_path = resource_path("sh.ico")
    title = "GameHelper Steam"

    window = webview.create_window(
        title,
        f"http://127.0.0.1:{port}",
        width=MAIN_WIDTH,
        height=MAIN_HEIGHT,
        min_size=(1100, 720),
        background_color="#101317",
    )

    def on_closed() -> None:
        threading.Thread(target=server.shutdown, daemon=True).start()

    window.events.closed += on_closed
    webview.start(
        func=lambda: threading.Thread(target=set_dark_titlebar, args=(title,), daemon=True).start(),
        icon=str(icon_path) if icon_path.exists() else None,
    )


if __name__ == "__main__":
    main()
