const scanButton = document.querySelector("#scan-button");
const startupLoader = document.querySelector("#startup-loader");
const startupMessage = document.querySelector("#startup-message");
const statusBox = document.querySelector("#status");
const summary = document.querySelector("#summary");
const homeInsights = document.querySelector("#home-insights");
const homeShowcase = document.querySelector("#home-showcase");
const homeDetails = document.querySelector("#home-details");
const heroGame = document.querySelector("#hero-game");
const spotlightGames = document.querySelector("#spotlight-games");
const results = document.querySelector("#results");
const totalHours = document.querySelector("#total-hours");
const gameCount = document.querySelector("#game-count");
const playedCount = document.querySelector("#played-count");
const accountCard = document.querySelector("#account-card");
const accountName = document.querySelector("#account-name");
const accountAvatar = document.querySelector("#account-avatar");
const settingsButton = document.querySelector("#settings-button");
const languageSelect = document.querySelector("#language-select");
const backgroundSelect = document.querySelector("#background-select");
const accountSelect = document.querySelector("#account-select");
const accountSelectNote = document.querySelector("#account-select-note");
const settingsSteamPath = document.querySelector("#settings-steam-path");
const settingsGameCount = document.querySelector("#settings-game-count");
const settingsAppVersion = document.querySelector("#settings-app-version");
const updateStatus = document.querySelector("#update-status");
const checkUpdateButton = document.querySelector("#check-update-button");
const openUpdateButton = document.querySelector("#open-update-button");
const gamesList = document.querySelector("#games");
const unfinishedGamesList = document.querySelector("#unfinished-games");
const favoriteGamesList = document.querySelector("#favorite-games");
const wantGamesList = document.querySelector("#want-games");
const tierList = document.querySelector("#tier-list");
const tierModal = document.querySelector("#tier-modal");
const tierModalKicker = document.querySelector("#tier-modal-kicker");
const tierModalTitle = document.querySelector("#tier-modal-title");
const tierGameSearch = document.querySelector("#tier-game-search");
const tierGameList = document.querySelector("#tier-game-list");
const samGameSearch = document.querySelector("#sam-game-search");
const samGames = document.querySelector("#sam-games");
const samSelectedGame = document.querySelector("#sam-selected-game");
const samSummary = document.querySelector("#sam-summary");
const samAchievements = document.querySelector("#sam-achievements");
const searchInput = document.querySelector("#search");
const minHoursInput = document.querySelector("#min-hours");
const sortOrderInput = document.querySelector("#sort-order");
const tabButtons = document.querySelectorAll(".tab");
const views = document.querySelectorAll(".view");

let currentGames = [];
let activeTab = "home";
let statusHideTimer = 0;
let samStatus = { installed: false };
let samCatalog = new Map();
let selectedSamAppId = "";
let selectedSamAchievements = [];
let activeTier = "";
let currentAccounts = [];
let currentPayload = null;
let latestUpdateInfo = null;
let selectedAccountId = localStorage.getItem("gamehelperAccountId") || "";
const settings = loadSettings();
const tierOrder = ["S", "A", "B", "C", "D"];
const i18n = {
  ru: {
    "tab.home": "Главная",
    "tab.games": "Список игр",
    "tab.unfinished": "Не пройденные",
    "tab.favorites": "Избранное",
    "tab.want": "Хочу поиграть",
    "tab.rating": "Рейтинг",
    "tab.achievements": "Достижения",
    "settings.title": "Настройки",
    "settings.subtitle": "Параметры интерфейса, аккаунта Steam и информация о приложении.",
    "settings.interface": "Интерфейс",
    "settings.language": "Язык",
    "settings.background": "Фон",
    "settings.backgroundOn": "Фон включён",
    "settings.backgroundOff": "Без фона",
    "settings.user": "Пользователь",
    "settings.about": "О приложении",
    "settings.appName": "Название",
    "settings.version": "Версия",
    "settings.mode": "Режим",
    "settings.modeValue": "Локальный анализ Steam без API-ключа",
    "settings.games": "Игры",
    "settings.data": "Данные",
    "settings.dataValue": "Названия и изображения кешируются локально",
    "settings.multiAccount": "После выбора пользователя библиотека будет перечитана из его локальных данных Steam.",
    "settings.singleAccount": "В локальных данных Steam найден один пользователь.",
    "settings.gameStats": "{total} в библиотеке · {played} с часами",
    "update.title": "Обновления",
    "update.notChecked": "Проверка ещё не запускалась",
    "update.check": "Проверить",
    "update.checking": "Проверяю GitHub Releases...",
    "update.open": "Открыть",
    "update.available": "Доступна версия {version}",
    "update.actual": "Установлена актуальная версия {version}",
    "update.notConfigured": "GitHub Releases пока не подключены",
    "update.failed": "Не удалось проверить обновления",
    "update.opened": "Открываю страницу обновления.",
    "startup.prepare": "Читаю Steam и подготавливаю библиотеку...",
    "startup.readNames": "Читаю Steam и обновляю названия игр...",
    "startup.readLocal": "Читаю локальные данные Steam...",
    "action.scan": "Сканировать локально",
    "action.close": "Закрыть",
    "tabs.label": "Разделы",
    "filter.search": "Поиск",
    "common.library": "Библиотека",
    "filter.minHours": "Минимум часов",
    "filter.sort": "Сортировка",
    "placeholder.gameName": "Название игры",
    "placeholder.findGame": "Найти игру",
    "sort.hoursDesc": "Часы: больше сначала",
    "sort.hoursAsc": "Часы: меньше сначала",
    "sort.lastLaunch": "Последний запуск",
    "sort.nameAsc": "Название А-Я",
    "unit.hoursShort": "ч",
    "unit.achievementsShort": "достиж.",
    "status.readNames": "Читаю Steam и обновляю названия...",
    "status.readLocal": "Читаю локальные данные Steam...",
    "status.libraryUpdated": "Библиотека обновлена.",
    "empty.noData": "Пока нет данных",
    "empty.empty": "Пока пусто",
    "empty.noGamesByFilters": "Нет игр под выбранные фильтры.",
    "empty.noZeroGames": "В локальных данных нет игр с нулевым временем.",
    "empty.noFavorites": "В избранном пока нет игр.",
    "empty.noWant": "В списке пока нет игр.",
    "empty.noSearchGames": "Нет игр под выбранный поиск.",
    "home.totalHours": "Всего часов",
    "home.totalHoursDetail": "Суммарно по активному аккаунту",
    "home.playedGames": "Сыгранные игры",
    "home.playedGamesDetail": "Больше нуля часов · всего {total}",
    "home.averageTime": "Среднее время",
    "home.averageTimeDetail": "На одну сыгранную игру",
    "home.zeroTime": "Без времени",
    "home.zeroTimeDetail": "Не запускались или 0 часов",
    "home.mainGame": "Главная игра аккаунта",
    "home.lastLaunch": "Последний запуск",
    "home.noDate": "Нет даты",
    "home.favoritesDetail": "Отмечай игры звездой в списке",
    "home.wantDetail": "Добавляй игры закладкой в списке",
    "home.favoriteCount": "{count} отмечено",
    "home.wantCount": "{count} в списке",
    "home.topTime": "Топ по времени",
    "home.topTimeDetail": "Игры, где наиграно больше всего часов",
    "home.noTime": "Без времени",
    "home.noTimeDetail": "Не запускались или Steam показывает 0 часов",
    "game.lastLaunch": "Последний запуск: {date}",
    "game.noLastLaunch": "Нет данных о последнем запуске",
    "game.zeroPlayed": "Запускалась, но 0 часов",
    "game.neverPlayed": "Не запускалась",
    "game.unconfirmed": "Не подтверждено",
    "tier.addTo": "Добавить игру в {tier}",
    "tier.kicker": "Тир {tier}",
    "tier.chooseGame": "Выбери игру",
    "tier.notFound": "Игры не найдены.",
    "tier.current": "сейчас {tier}",
    "tier.selected": "Выбрана",
    "tier.add": "Добавить",
    "tier.remove": "Убрать из рейтинга",
    "sam.chooseGame": "Выбери игру",
    "sam.placeholderDetail": "Здесь появится прогресс, список достижений и доступные действия.",
    "sam.notFound": "Ничего не найдено",
    "sam.changeSearch": "Измени поиск слева, чтобы выбрать игру.",
    "sam.loading": "Загружаю достижения через Steamworks...",
    "sam.loaded": "Достижения загружены.",
    "sam.loadFailed": "Не удалось загрузить достижения.",
    "sam.selectedGame": "Выбранная игра",
    "sam.unlockAll": "Получить все",
    "sam.noClosed": "Нет доступных закрытых достижений",
    "sam.unlockAllTitle": "Открыть все доступные достижения этой игры",
    "sam.total": "Всего",
    "sam.unlocked": "Открыто",
    "sam.locked": "Закрыто",
    "sam.achievements": "достижений",
    "sam.left": "осталось",
    "sam.noAchievements": "Для этой игры достижения не найдены.",
    "sam.hiddenAchievement": "Скрытое достижение",
    "sam.protected": "Защищено",
    "sam.close": "Закрыть",
    "sam.open": "Открыть",
    "sam.opening": "Открываю...",
    "summary.totalHours": "Всего часов",
    "summary.playedGames": "Сыгранные игры",
    "summary.withLaunchDate": "С датой запуска",
    "unfinished.title": "Не пройденные",
    "unfinished.subtitle": "Игры без времени: не запускались или Steam показывает 0 часов.",
    "achievements.title": "Достижения Steam",
    "achievements.subtitle": "Выбери игру в библиотеке, чтобы посмотреть достижения.",
    "favorites.title": "Избранное",
    "want.title": "Хочу поиграть",
    "rating.title": "Рейтинг игр",
    "rating.subtitle": "Нажимай плюс в нужном тире и выбирай игру из библиотеки.",
  },
  en: {
    "tab.home": "Home",
    "tab.games": "Games",
    "tab.unfinished": "Unplayed",
    "tab.favorites": "Favorites",
    "tab.want": "Play Later",
    "tab.rating": "Rating",
    "tab.achievements": "Achievements",
    "settings.title": "Settings",
    "settings.subtitle": "Interface, Steam account, and application information.",
    "settings.interface": "Interface",
    "settings.language": "Language",
    "settings.background": "Background",
    "settings.backgroundOn": "Background on",
    "settings.backgroundOff": "No background",
    "settings.user": "User",
    "settings.about": "About",
    "settings.appName": "Name",
    "settings.version": "Version",
    "settings.mode": "Mode",
    "settings.modeValue": "Local Steam analysis without an API key",
    "settings.games": "Games",
    "settings.data": "Data",
    "settings.dataValue": "Names and images are cached locally",
    "settings.multiAccount": "After selecting a user, the library will be reread from that Steam account's local data.",
    "settings.singleAccount": "One user was found in local Steam data.",
    "settings.gameStats": "{total} in library · {played} with playtime",
    "update.title": "Updates",
    "update.notChecked": "No update check yet",
    "update.check": "Check",
    "update.checking": "Checking GitHub Releases...",
    "update.open": "Open",
    "update.available": "Version {version} is available",
    "update.actual": "Version {version} is current",
    "update.notConfigured": "GitHub Releases are not connected yet",
    "update.failed": "Failed to check updates",
    "update.opened": "Opening update page.",
    "startup.prepare": "Reading Steam and preparing your library...",
    "startup.readNames": "Reading Steam and updating game names...",
    "startup.readLocal": "Reading local Steam data...",
    "action.scan": "Scan locally",
    "action.close": "Close",
    "tabs.label": "Sections",
    "filter.search": "Search",
    "common.library": "Library",
    "filter.minHours": "Minimum hours",
    "filter.sort": "Sort",
    "placeholder.gameName": "Game name",
    "placeholder.findGame": "Find a game",
    "sort.hoursDesc": "Hours: highest first",
    "sort.hoursAsc": "Hours: lowest first",
    "sort.lastLaunch": "Last launch",
    "sort.nameAsc": "Name A-Z",
    "unit.hoursShort": "h",
    "unit.achievementsShort": "ach.",
    "status.readNames": "Reading Steam and updating names...",
    "status.readLocal": "Reading local Steam data...",
    "status.libraryUpdated": "Library updated.",
    "empty.noData": "No data yet",
    "empty.empty": "Empty",
    "empty.noGamesByFilters": "No games match these filters.",
    "empty.noZeroGames": "No zero-time games found in local data.",
    "empty.noFavorites": "No favorite games yet.",
    "empty.noWant": "No games in this list yet.",
    "empty.noSearchGames": "No games match this search.",
    "home.totalHours": "Total hours",
    "home.totalHoursDetail": "Total for the active account",
    "home.playedGames": "Played games",
    "home.playedGamesDetail": "More than zero hours · {total} total",
    "home.averageTime": "Average time",
    "home.averageTimeDetail": "Per played game",
    "home.zeroTime": "No time",
    "home.zeroTimeDetail": "Never launched or 0 hours",
    "home.mainGame": "Main account game",
    "home.lastLaunch": "Last launch",
    "home.noDate": "No date",
    "home.favoritesDetail": "Mark games with a star in the list",
    "home.wantDetail": "Add games with a bookmark in the list",
    "home.favoriteCount": "{count} marked",
    "home.wantCount": "{count} in list",
    "home.topTime": "Top by time",
    "home.topTimeDetail": "Games with the most playtime",
    "home.noTime": "No time",
    "home.noTimeDetail": "Never launched or Steam shows 0 hours",
    "game.lastLaunch": "Last launch: {date}",
    "game.noLastLaunch": "No last launch data",
    "game.zeroPlayed": "Launched, but 0 hours",
    "game.neverPlayed": "Never launched",
    "game.unconfirmed": "Unconfirmed",
    "tier.addTo": "Add game to {tier}",
    "tier.kicker": "Tier {tier}",
    "tier.chooseGame": "Choose a game",
    "tier.notFound": "No games found.",
    "tier.current": "currently {tier}",
    "tier.selected": "Selected",
    "tier.add": "Add",
    "tier.remove": "Remove from rating",
    "sam.chooseGame": "Choose a game",
    "sam.placeholderDetail": "Progress, achievements, and available actions will appear here.",
    "sam.notFound": "Nothing found",
    "sam.changeSearch": "Change the search on the left to choose a game.",
    "sam.loading": "Loading achievements through Steamworks...",
    "sam.loaded": "Achievements loaded.",
    "sam.loadFailed": "Failed to load achievements.",
    "sam.selectedGame": "Selected game",
    "sam.unlockAll": "Unlock all",
    "sam.noClosed": "No available locked achievements",
    "sam.unlockAllTitle": "Unlock all available achievements for this game",
    "sam.total": "Total",
    "sam.unlocked": "Unlocked",
    "sam.locked": "Locked",
    "sam.achievements": "achievements",
    "sam.left": "left",
    "sam.noAchievements": "No achievements found for this game.",
    "sam.hiddenAchievement": "Hidden achievement",
    "sam.protected": "Protected",
    "sam.close": "Lock",
    "sam.open": "Unlock",
    "sam.opening": "Unlocking...",
    "summary.totalHours": "Total hours",
    "summary.playedGames": "Played games",
    "summary.withLaunchDate": "With launch date",
    "unfinished.title": "Unplayed",
    "unfinished.subtitle": "Games with no time: never launched or Steam shows 0 hours.",
    "achievements.title": "Steam Achievements",
    "achievements.subtitle": "Choose a game from your library to view achievements.",
    "favorites.title": "Favorites",
    "want.title": "Play Later",
    "rating.title": "Game Rating",
    "rating.subtitle": "Press plus in a tier and choose a game from your library.",
  },
};
const saved = {
  favorites: loadSavedSet("gamehelperFavorites"),
  want: loadSavedSet("gamehelperWant"),
};
const ratings = loadRatings();

scanButton.addEventListener("click", () => scanLocal(true));
settingsButton.addEventListener("click", () => setActiveTab("settings"));
checkUpdateButton.addEventListener("click", checkForUpdates);
openUpdateButton.addEventListener("click", openUpdatePage);
samGameSearch.addEventListener("input", renderSamGameList);
tierGameSearch.addEventListener("input", renderTierModalGames);
languageSelect.addEventListener("change", () => {
  settings.language = languageSelect.value;
  saveSettings();
  applySettings();
  renderAll();
  if (currentPayload) {
    renderSettings(currentPayload);
  }
});
backgroundSelect.addEventListener("change", () => {
  settings.background = backgroundSelect.value;
  saveSettings();
  applySettings();
});
accountSelect.addEventListener("change", () => {
  selectedAccountId = accountSelect.value;
  localStorage.setItem("gamehelperAccountId", selectedAccountId);
  scanLocal(true);
});
tierModal.addEventListener("click", (event) => {
  if (event.target.closest("[data-close-tier-modal]")) {
    closeTierModal();
  }
});
window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !tierModal.hidden) {
    closeTierModal();
  }
});

for (const button of tabButtons) {
  button.addEventListener("click", () => setActiveTab(button.dataset.tab));
}

searchInput.addEventListener("input", renderAll);
minHoursInput.addEventListener("input", renderAll);
sortOrderInput.addEventListener("change", renderAll);

initializeApp();

function initializeApp() {
  applySettings();
  scanLocal(true, true);
}

async function scanLocal(fetchNames, startup = false, retryAccount = true) {
  if (startup) {
    showStartupLoader(fetchNames ? t("startup.readNames") : t("startup.readLocal"));
  } else {
    setStatus(fetchNames ? t("status.readNames") : t("status.readLocal"), "loading");
  }
  summary.hidden = true;
  homeInsights.hidden = true;
  homeShowcase.hidden = true;
  homeDetails.hidden = true;
  results.hidden = true;
  gamesList.replaceChildren();
  homeInsights.replaceChildren();
  heroGame.replaceChildren();
  spotlightGames.replaceChildren();
  homeDetails.replaceChildren();

  try {
    const params = new URLSearchParams({ fetch_names: fetchNames ? "1" : "0" });
    if (selectedAccountId) {
      params.set("account_id", selectedAccountId);
    }
    const response = await fetch(`/api/local-games?${params}`);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Не удалось получить данные.");
    }
    render(payload);
    refreshSamStatus();
  } catch (error) {
    if (retryAccount && selectedAccountId && error.message.includes("Steam-аккаунт не найден")) {
      selectedAccountId = "";
      localStorage.removeItem("gamehelperAccountId");
      await scanLocal(fetchNames, startup, false);
      return;
    }
    if (startup) {
      hideStartupLoader();
    }
    setStatus(error.message, "error");
  }
}

function render(payload) {
  currentPayload = payload;
  currentGames = payload.games;
  currentAccounts = payload.accounts || [];
  selectedAccountId = payload.account?.accountId || selectedAccountId;
  localStorage.setItem("gamehelperAccountId", selectedAccountId);
  const timedGamesCount = currentGames.filter((game) => game.minutes > 0).length;
  totalHours.textContent = formatNumber(payload.totalHours);
  gameCount.textContent = formatNumber(timedGamesCount);
  playedCount.textContent = formatNumber(payload.playedGames);
  renderAccount(payload.account);
  renderSettings(payload);
  summary.hidden = false;
  homeInsights.hidden = false;
  homeShowcase.hidden = false;
  homeDetails.hidden = false;
  setStatus(t("status.libraryUpdated"), "ok");
  renderAll();
  setActiveTab(activeTab);
  hideStartupLoader();
}

function showStartupLoader(message) {
  startupMessage.textContent = message;
  startupLoader.hidden = false;
}

function hideStartupLoader() {
  startupLoader.classList.add("is-hidden");
  window.setTimeout(() => {
    startupLoader.hidden = true;
  }, 220);
}

function renderAccount(account) {
  accountName.textContent = account.accountName ? `${account.name} (${account.accountName})` : account.name;
  accountAvatar.src = account.avatarUrl;
  accountAvatar.onerror = () => {
    accountAvatar.removeAttribute("src");
    accountAvatar.alt = account.name;
    accountAvatar.dataset.fallback = initials(account.name);
  };
  accountCard.hidden = false;
}

function setActiveTab(tab) {
  activeTab = tab;
  settingsButton.classList.toggle("is-active", tab === "settings");
  for (const button of tabButtons) {
    button.classList.toggle("is-active", button.dataset.tab === tab);
  }
  for (const view of views) {
    view.hidden = view.dataset.view !== tab;
    view.classList.toggle("is-active", view.dataset.view === tab);
  }
}

function applySettings() {
  languageSelect.value = settings.language;
  backgroundSelect.value = settings.background;
  document.documentElement.lang = settings.language;
  document.body.dataset.background = settings.background;
  translateStatic();
  renderUpdateStatus();
}

function t(key, replacements = {}) {
  const dictionary = i18n[settings.language] || i18n.ru;
  let value = dictionary[key] || i18n.ru[key] || key;
  for (const [name, replacement] of Object.entries(replacements)) {
    value = value.replace(`{${name}}`, replacement);
  }
  return value;
}

function translateStatic() {
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    node.placeholder = t(node.dataset.i18nPlaceholder);
  });
  document.querySelectorAll("[data-i18n-title]").forEach((node) => {
    node.title = t(node.dataset.i18nTitle);
  });
  document.querySelectorAll("[data-i18n-aria]").forEach((node) => {
    node.ariaLabel = t(node.dataset.i18nAria);
  });
  settingsButton.title = t("settings.title");
  settingsButton.ariaLabel = t("settings.title");
}

function loadSettings() {
  try {
    const parsed = JSON.parse(localStorage.getItem("gamehelperSettings") || "{}");
    return {
      language: parsed.language === "en" ? "en" : "ru",
      background: parsed.background === "none" ? "none" : "art",
    };
  } catch {
    return { language: "ru", background: "art" };
  }
}

function saveSettings() {
  localStorage.setItem("gamehelperSettings", JSON.stringify(settings));
}

function renderSettings(payload) {
  accountSelect.replaceChildren();
  for (const account of currentAccounts) {
    const option = document.createElement("option");
    option.value = account.accountId;
    option.textContent = account.accountName ? `${account.name} (${account.accountName})` : account.name;
    accountSelect.append(option);
  }
  accountSelect.value = payload.account?.accountId || selectedAccountId;
  accountSelect.disabled = currentAccounts.length <= 1;
  accountSelectNote.textContent = currentAccounts.length > 1 ? t("settings.multiAccount") : t("settings.singleAccount");
  settingsSteamPath.textContent = payload.steamPath || "-";
  settingsGameCount.textContent = t("settings.gameStats", {
    total: formatNumber(payload.gameCount || currentGames.length),
    played: formatNumber(currentGames.filter((game) => game.minutes > 0).length),
  });
  if (!settingsAppVersion.textContent || settingsAppVersion.textContent === "-") {
    settingsAppVersion.textContent = latestUpdateInfo?.currentVersion || "-";
  }
}

function renderUpdateStatus() {
  if (!latestUpdateInfo) {
    updateStatus.textContent = t("update.notChecked");
    openUpdateButton.hidden = true;
    return;
  }
  settingsAppVersion.textContent = latestUpdateInfo.currentVersion || "-";
  if (!latestUpdateInfo.configured) {
    updateStatus.textContent = t("update.notConfigured");
    openUpdateButton.hidden = true;
  } else if (latestUpdateInfo.updateAvailable) {
    updateStatus.textContent = t("update.available", { version: latestUpdateInfo.latestVersion });
    openUpdateButton.hidden = false;
  } else {
    updateStatus.textContent = t("update.actual", { version: latestUpdateInfo.currentVersion });
    openUpdateButton.hidden = true;
  }
}

async function checkForUpdates() {
  checkUpdateButton.disabled = true;
  updateStatus.textContent = t("update.checking");
  openUpdateButton.hidden = true;
  try {
    const response = await fetch("/api/update");
    const payload = await response.json();
    if (!response.ok || payload.error) {
      throw new Error(payload.error || t("update.failed"));
    }
    latestUpdateInfo = payload;
    renderUpdateStatus();
  } catch (error) {
    updateStatus.textContent = error.message || t("update.failed");
  } finally {
    checkUpdateButton.disabled = false;
  }
}

async function openUpdatePage() {
  openUpdateButton.disabled = true;
  try {
    const response = await fetch("/api/update/open");
    const payload = await response.json();
    if (!response.ok || payload.error) {
      throw new Error(payload.error || t("update.failed"));
    }
    showStatus(t("update.opened"), "ok");
  } catch (error) {
    showStatus(error.message || t("update.failed"), "error");
  } finally {
    openUpdateButton.disabled = false;
  }
}

function renderAll() {
  renderHome();
  renderGameList();
  renderUnfinishedList();
  renderSamGameList();
  renderSavedList("favorites", favoriteGamesList, t("empty.noFavorites"));
  renderSavedList("want", wantGamesList, t("empty.noWant"));
  renderTierList();
}

function renderHome() {
  const timed = currentGames.filter((game) => game.minutes > 0);
  const launched = currentGames.filter(hasRealLastPlayed);
  const mostPlayed = currentGames[0];
  const latest = [...launched].sort((a, b) => realLastPlayed(b) - realLastPlayed(a))[0];
  const favoriteGames = currentGames.filter((game) => saved.favorites.has(String(game.appid)));
  const wantGames = currentGames.filter((game) => saved.want.has(String(game.appid)));
  const zeroHoursCount = unplayedGames().length;
  const totalMinutes = currentGames.reduce((sum, game) => sum + game.minutes, 0);
  const averageHours = timed.length ? totalMinutes / timed.length / 60 : 0;
  const favoritesCount = saved.favorites.size;
  const wantCount = saved.want.size;

  homeInsights.replaceChildren(
    createInsightCard(t("home.totalHours"), `${formatNumber(totalMinutes / 60)} ${t("unit.hoursShort")}`, t("home.totalHoursDetail")),
    createInsightCard(t("home.playedGames"), formatNumber(timed.length), t("home.playedGamesDetail", { total: currentGames.length })),
    createInsightCard(t("home.averageTime"), `${formatNumber(averageHours)} ${t("unit.hoursShort")}`, t("home.averageTimeDetail")),
    createInsightCard(t("home.zeroTime"), formatNumber(zeroHoursCount), t("home.zeroTimeDetail")),
  );

  heroGame.replaceChildren();
  spotlightGames.replaceChildren();
  if (!mostPlayed) {
    return;
  }

  renderHeroGame(mostPlayed);
  spotlightGames.append(
    createSpotlightCard(t("home.lastLaunch"), latest, latest && hasRealLastPlayed(latest) ? formatDate(latest.lastPlayed) : t("home.noDate")),
    createSpotlightCard(t("tab.favorites"), favoriteGames[0], favoriteGames.length ? t("home.favoriteCount", { count: favoriteGames.length }) : t("home.favoritesDetail")),
    createSpotlightCard(t("tab.want"), wantGames[0], wantGames.length ? t("home.wantCount", { count: wantGames.length }) : t("home.wantDetail")),
  );

  const topByHours = [...timed].sort((a, b) => b.minutes - a.minutes).slice(0, 5);
  const zeroHourGames = unplayedGames()
    .sort((a, b) => realLastPlayed(b) - realLastPlayed(a) || a.name.localeCompare(b.name, "ru", { sensitivity: "base" }))
    .slice(0, 5);

  homeDetails.replaceChildren(
    createHomePanel(t("home.topTime"), t("home.topTimeDetail"), topByHours, (game) => `${formatNumber(game.hours)} ${t("unit.hoursShort")}`),
    createHomePanel(t("home.noTime"), t("home.noTimeDetail"), zeroHourGames, (game) => hasRealLastPlayed(game) ? formatDate(game.lastPlayed) : t("game.neverPlayed")),
  );

  preloadSteamImages([mostPlayed, latest, ...favoriteGames.slice(0, 1), ...wantGames.slice(0, 1), ...topByHours, ...zeroHourGames]);
}

function createHomePanel(title, subtitle, games, detailForGame) {
  const panel = document.createElement("article");
  panel.className = "home-panel";

  const header = document.createElement("header");
  const titleNode = document.createElement("h3");
  titleNode.textContent = title;
  const subtitleNode = document.createElement("p");
  subtitleNode.textContent = subtitle;
  header.append(titleNode, subtitleNode);

  const list = document.createElement("div");
  list.className = "home-panel-list";
  if (!games.length) {
    const empty = document.createElement("span");
    empty.className = "home-panel-empty";
    empty.textContent = t("empty.noData");
    list.append(empty);
  } else {
    for (const game of games) {
      list.append(createHomeMiniGame(game, detailForGame(game)));
    }
  }

  panel.append(header, list);
  return panel;
}

function createHomeMiniGame(game, detail) {
  const row = document.createElement("a");
  row.className = "home-mini-game";
  row.href = game.storeUrl;
  row.target = "_blank";
  row.rel = "noreferrer";

  const image = document.createElement("img");
  image.src = game.iconUrl;
  image.alt = "";
  image.loading = "lazy";
  image.addEventListener("error", () => {
    image.replaceWith(createImageFallback(game));
  });

  const name = document.createElement("strong");
  name.textContent = game.name;
  const meta = document.createElement("small");
  meta.textContent = detail;

  row.append(image, name, meta);
  return row;
}

function createInsightCard(label, value, detail) {
  const card = document.createElement("article");
  card.className = "insight-card";
  const labelNode = document.createElement("span");
  labelNode.textContent = label;
  const valueNode = document.createElement("strong");
  valueNode.textContent = value;
  const detailNode = document.createElement("small");
  detailNode.textContent = detail;
  card.append(labelNode, valueNode, detailNode);
  return card;
}

function renderGameList() {
  const query = searchInput.value.trim().toLowerCase();
  const minHours = Number(minHoursInput.value || 0);
  const visibleGames = currentGames.filter((game) => isVisibleLibraryGame(game)).filter((game) => {
    const passesHours = minHours <= 0 ? game.minutes > 0 : game.hours >= minHours;
    return game.name.toLowerCase().includes(query) && passesHours;
  });
  sortGames(visibleGames, sortOrderInput.value);
  gamesList.replaceChildren();
  renderCards(visibleGames, gamesList, t("empty.noGamesByFilters"));
}

function renderUnfinishedList() {
  const games = unplayedGames();
  games.sort((a, b) => realLastPlayed(b) - realLastPlayed(a) || a.name.localeCompare(b.name, "ru", { sensitivity: "base" }));
  unfinishedGamesList.replaceChildren();
  renderCards(games, unfinishedGamesList, t("empty.noZeroGames"));
}

function unplayedGames() {
  return currentGames.filter((game) => game.minutes === 0 && !game.isSteamUtility && !game.isPlaceholderName);
}

function isVisibleLibraryGame(game) {
  return game.minutes > 0 || game.accountLinked || game.isInstalled;
}

function sortGames(games, sortOrder) {
  const byName = (a, b) => a.name.localeCompare(b.name, "ru", { sensitivity: "base" });
  games.sort((a, b) => {
    if (sortOrder === "hours-asc") {
      return a.minutes - b.minutes || byName(a, b);
    }
    if (sortOrder === "last-desc") {
      return realLastPlayed(b) - realLastPlayed(a) || b.minutes - a.minutes || byName(a, b);
    }
    if (sortOrder === "name-asc") {
      return byName(a, b);
    }
    return b.minutes - a.minutes || byName(a, b);
  });
}

function renderHeroGame(game) {
  heroGame.style.backgroundImage = `linear-gradient(90deg, rgba(13, 18, 24, .96), rgba(13, 18, 24, .62), rgba(13, 18, 24, .25)), url("${headerImage(game)}")`;

  const label = document.createElement("span");
  label.className = "feature-label";
  label.textContent = t("home.mainGame");

  const title = document.createElement("a");
  title.href = game.storeUrl;
  title.target = "_blank";
  title.rel = "noreferrer";
  title.textContent = game.name;

  const details = document.createElement("p");
  details.textContent = `${formatNumber(game.hours)} ${t("unit.hoursShort")} в Steam · ${hasRealLastPlayed(game) ? `${t("sort.lastLaunch").toLowerCase()} ${formatDate(game.lastPlayed)}` : t("home.noDate").toLowerCase()}`;

  heroGame.append(label, title, details);
}

function createSpotlightCard(label, game, detail) {
  const card = document.createElement("article");
  card.className = "spotlight-card";
  if (game) {
    card.style.backgroundImage = `linear-gradient(180deg, rgba(14, 18, 24, .12), rgba(14, 18, 24, .92)), url("${headerImage(game)}")`;
  } else {
    card.classList.add("is-empty");
  }

  const labelNode = document.createElement("span");
  labelNode.className = "feature-label";
  labelNode.textContent = label;

  const title = game ? document.createElement("a") : document.createElement("strong");
  if (game) {
    title.href = game.storeUrl;
    title.target = "_blank";
    title.rel = "noreferrer";
  }
  title.textContent = game ? game.name : t("empty.empty");

  const detailNode = document.createElement("small");
  detailNode.textContent = game ? `${detail} · ${formatNumber(game.hours)} ${t("unit.hoursShort")}` : detail;

  if (!game) {
    const logo = document.createElement("img");
    logo.className = "empty-logo";
    logo.src = "/sh.ico";
    logo.alt = "";
    card.append(labelNode, logo, title, detailNode);
  } else {
    card.append(labelNode, title, detailNode);
  }
  return card;
}

function renderSavedList(kind, container, emptyText) {
  const ids = saved[kind];
  const games = currentGames.filter((game) => ids.has(String(game.appid)));
  container.replaceChildren();
  renderCards(games, container, emptyText);
}

function renderCards(games, container, emptyText) {
  if (!games.length) {
    container.append(createEmptyState(emptyText));
    return;
  }

  for (const game of games) {
    container.append(createGameCard(game));
  }
}

function createEmptyState(text) {
  const empty = document.createElement("article");
  empty.className = "empty-state";

  const logo = document.createElement("img");
  logo.src = "/sh.ico";
  logo.alt = "";

  const title = document.createElement("strong");
  title.textContent = t("empty.empty");

  const detail = document.createElement("span");
  detail.textContent = text;

  empty.append(logo, title, detail);
  return empty;
}

function createGameCard(game) {
  const card = document.createElement("article");
  card.className = "game";

  const image = document.createElement("img");
  image.src = game.iconUrl;
  image.alt = "";
  image.loading = "lazy";
  image.addEventListener("error", () => {
    image.replaceWith(createImageFallback(game));
  });

  const info = document.createElement("div");
  info.className = "game-info";

  const title = document.createElement("a");
  title.href = game.storeUrl;
  title.target = "_blank";
  title.rel = "noreferrer";
  title.textContent = game.name;

  const meta = document.createElement("span");
  meta.textContent = hasRealLastPlayed(game)
    ? t("game.lastLaunch", { date: formatDate(game.lastPlayed) })
    : t("game.noLastLaunch");

  info.append(title, meta);
  if (game.minutes === 0) {
    const badge = document.createElement("span");
    badge.className = hasRealLastPlayed(game) ? "game-badge is-zero" : "game-badge is-never";
    badge.textContent = hasRealLastPlayed(game) ? t("game.zeroPlayed") : t("game.neverPlayed");
    info.append(badge);
    if (!game.accountLinked) {
      const unconfirmed = document.createElement("span");
      unconfirmed.className = "game-badge is-unconfirmed";
      unconfirmed.textContent = t("game.unconfirmed");
      info.append(unconfirmed);
    }
  }

  const actions = document.createElement("div");
  actions.className = "game-actions";
  actions.append(
    createToggleButton("favorites", game, t("tab.favorites"), starIcon()),
    createToggleButton("want", game, t("tab.want"), bookmarkIcon()),
  );

  const hours = document.createElement("strong");
  hours.className = "hours";
  hours.textContent = `${formatNumber(game.hours)} ${t("unit.hoursShort")}`;

  card.append(image, info, actions, hours);
  return card;
}

function createToggleButton(kind, game, label, icon) {
  const appid = String(game.appid);
  const button = document.createElement("button");
  button.className = "icon-toggle";
  button.type = "button";
  button.title = label;
  button.ariaLabel = label;
  button.innerHTML = icon;
  button.classList.toggle("is-active", saved[kind].has(appid));
  button.addEventListener("click", () => {
    toggleSaved(kind, appid);
  });
  return button;
}

function toggleSaved(kind, appid) {
  const set = saved[kind];
  if (set.has(appid)) {
    set.delete(appid);
  } else {
    set.add(appid);
  }
  localStorage.setItem(storageKey(kind), JSON.stringify([...set]));
  renderAll();
}

function renderTierList() {
  tierList.replaceChildren();
  const gamesById = new Map(currentGames.map((game) => [String(game.appid), game]));

  for (const tier of tierOrder) {
    const games = Object.entries(ratings)
      .filter(([, value]) => value === tier)
      .map(([appid]) => gamesById.get(appid))
      .filter(Boolean)
      .sort((a, b) => b.minutes - a.minutes || a.name.localeCompare(b.name, "ru", { sensitivity: "base" }));
    tierList.append(createTierRow(tier, games));
  }
}

function createTierRow(tier, games) {
  const row = document.createElement("article");
  row.className = `tier-row tier-${tier.toLowerCase()}`;

  const label = document.createElement("strong");
  label.className = "tier-label";
  label.textContent = tier;

  const items = document.createElement("div");
  items.className = "tier-items";
  for (const game of games) {
    items.append(createTierGame(game, tier));
  }
  items.append(createTierAddButton(tier));

  row.append(label, items);
  return row;
}

function createTierAddButton(tier) {
  const button = document.createElement("button");
  button.className = "tier-add";
  button.type = "button";
  button.title = t("tier.addTo", { tier });
  button.ariaLabel = button.title;
  button.textContent = "+";
  button.addEventListener("click", () => openTierModal(tier));
  return button;
}

function openTierModal(tier) {
  activeTier = tier;
  tierModalKicker.textContent = t("tier.kicker", { tier });
  tierModalTitle.textContent = t("tier.chooseGame");
  tierGameSearch.value = "";
  tierModal.hidden = false;
  renderTierModalGames();
  tierGameSearch.focus();
}

function closeTierModal() {
  tierModal.hidden = true;
  activeTier = "";
}

function renderTierModalGames() {
  const query = tierGameSearch.value.trim().toLowerCase();
  const games = currentGames
    .filter((game) => isVisibleLibraryGame(game))
    .filter((game) => game.name.toLowerCase().includes(query))
    .sort((a, b) => b.minutes - a.minutes || a.name.localeCompare(b.name, "ru", { sensitivity: "base" }));

  tierGameList.replaceChildren();
  if (!games.length) {
    tierGameList.append(createEmptyState(t("tier.notFound")));
    return;
  }

  for (const game of games) {
    tierGameList.append(createTierModalGame(game));
  }
}

function createTierModalGame(game) {
  const appid = String(game.appid);
  const button = document.createElement("button");
  button.className = "tier-picker-game";
  button.type = "button";
  button.classList.toggle("is-current", ratings[appid] === activeTier);

  const image = document.createElement("img");
  image.src = game.iconUrl;
  image.alt = "";
  image.loading = "lazy";
  image.addEventListener("error", () => {
    image.replaceWith(createImageFallback(game));
  });

  const info = document.createElement("span");
  const title = document.createElement("strong");
  title.textContent = game.name;
  const meta = document.createElement("small");
  meta.textContent = ratings[appid]
    ? `${formatNumber(game.hours)} ${t("unit.hoursShort")} · ${t("tier.current", { tier: ratings[appid] })}`
    : `${formatNumber(game.hours)} ${t("unit.hoursShort")}`;
  info.append(title, meta);

  const action = document.createElement("em");
  action.textContent = ratings[appid] === activeTier ? t("tier.selected") : t("tier.add");

  button.append(image, info, action);
  button.addEventListener("click", () => {
    ratings[appid] = activeTier;
    saveRatings();
    renderAll();
    closeTierModal();
  });
  return button;
}

function createTierGame(game, tier) {
  const card = document.createElement("article");
  card.className = "tier-game";

  const image = document.createElement("img");
  image.src = game.iconUrl;
  image.alt = "";
  image.loading = "lazy";
  image.addEventListener("error", () => {
    image.replaceWith(createImageFallback(game));
  });

  const title = document.createElement("strong");
  title.textContent = game.name;
  const meta = document.createElement("small");
  meta.textContent = `${formatNumber(game.hours)} ${t("unit.hoursShort")}`;

  const remove = document.createElement("button");
  remove.type = "button";
  remove.title = t("tier.remove");
  remove.ariaLabel = t("tier.remove");
  remove.textContent = "×";
  remove.addEventListener("click", () => {
    delete ratings[String(game.appid)];
    saveRatings();
    renderAll();
  });

  card.append(image, title, meta, remove);
  return card;
}

function loadSavedSet(key) {
  try {
    return new Set(JSON.parse(localStorage.getItem(key) || "[]").map(String));
  } catch {
    return new Set();
  }
}

function storageKey(kind) {
  if (kind === "favorites") {
    return "gamehelperFavorites";
  }
  return "gamehelperWant";
}

function loadRatings() {
  try {
    const parsed = JSON.parse(localStorage.getItem("gamehelperRatings") || "{}");
    return Object.fromEntries(
      Object.entries(parsed).filter(([appid, tier]) => /^\d+$/.test(appid) && tierOrder.includes(tier)),
    );
  } catch {
    return {};
  }
}

function saveRatings() {
  localStorage.setItem("gamehelperRatings", JSON.stringify(ratings));
}

async function refreshSamStatus() {
  try {
    const response = await fetch("/api/sam/status");
    const payload = await response.json();
    samStatus = response.ok ? payload : { installed: false };
  } catch {
    samStatus = { installed: false };
  }
  await refreshSamCatalog();
  renderAll();
}

async function refreshSamCatalog() {
  samCatalog = new Map();
  try {
    const response = await fetch("/api/sam/catalog");
    const payload = await response.json();
    if (!response.ok) {
      return;
    }
    samCatalog = new Map((payload.games || []).map((item) => [String(item.appid), item]));
  } catch {
    samCatalog = new Map();
  }
}

function renderSamGameList() {
  const query = samGameSearch.value.trim().toLowerCase();
  const games = currentGames
    .filter((game) => game.minutes > 0)
    .filter((game) => game.name.toLowerCase().includes(query))
    .sort((a, b) => b.minutes - a.minutes || a.name.localeCompare(b.name, "ru", { sensitivity: "base" }));

  samGames.replaceChildren();
  if (!games.length) {
    samGames.append(createEmptyState(t("empty.noSearchGames")));
    if (!selectedSamAppId) {
      renderSamPlaceholder(t("sam.notFound"), t("sam.changeSearch"));
    }
    return;
  }
  if (selectedSamAppId && !currentGames.some((game) => String(game.appid) === selectedSamAppId)) {
    selectedSamAppId = "";
  }
  for (const game of games) {
    samGames.append(createSamGameButton(game));
  }
  if (!selectedSamAppId && !samAchievements.children.length) {
    renderSamPlaceholder(t("sam.chooseGame"), t("sam.placeholderDetail"));
  }
}

function createSamGameButton(game) {
  const button = document.createElement("button");
  button.className = "sam-game-button";
  button.type = "button";
  button.classList.toggle("is-active", String(game.appid) === selectedSamAppId);

  const image = document.createElement("img");
  image.src = game.iconUrl;
  image.alt = "";
  image.loading = "lazy";
  image.addEventListener("error", () => {
    image.replaceWith(createImageFallback(game));
  });

  const info = document.createElement("span");
  const title = document.createElement("strong");
  title.textContent = game.name;
  const meta = document.createElement("small");
  const catalogItem = samCatalog.get(String(game.appid));
  meta.textContent = catalogItem?.total
    ? `${formatNumber(game.hours)} ${t("unit.hoursShort")} · ${catalogItem.total} ${t("unit.achievementsShort")}`
    : `${formatNumber(game.hours)} ${t("unit.hoursShort")}${hasRealLastPlayed(game) ? ` · ${formatDate(game.lastPlayed)}` : ""}`;
  info.append(title, meta);

  button.append(image, info);
  if (catalogItem?.allProtected || catalogItem?.partlyProtected) {
    const badge = document.createElement("em");
    badge.className = `sam-lock-badge is-corner${catalogItem.allProtected ? "" : " is-partial"}`;
    badge.title = catalogItem.allProtected ? "Достижения защищены" : "Часть достижений защищена";
    badge.setAttribute("aria-label", badge.title);
    badge.innerHTML = `
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M7 10V8a5 5 0 0 1 10 0v2" />
        <path d="M6 10h12a1 1 0 0 1 1 1v8a1 1 0 0 1 -1 1H6a1 1 0 0 1 -1 -1v-8a1 1 0 0 1 1 -1z" />
        <path d="M12 14v2" />
      </svg>
    `;
    button.append(badge);
  }

  button.addEventListener("click", () => loadSamAchievements(game));
  return button;
}

async function loadSamAchievements(game) {
  const appid = String(game?.appid || selectedSamAppId || "");
  if (!appid) {
    samSummary.hidden = true;
    samSelectedGame.hidden = true;
    renderSamPlaceholder(t("sam.chooseGame"), t("sam.placeholderDetail"));
    return;
  }
  selectedSamAppId = appid;
  selectedSamAchievements = [];
  renderSamGameList();
  setStatus(t("sam.loading"), "loading");
  renderSamSelectedGame(game || currentGames.find((item) => String(item.appid) === appid));
  samAchievements.replaceChildren();
  samSummary.hidden = true;
  try {
    const response = await fetch(`/api/sam/achievements?appid=${encodeURIComponent(appid)}`);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || t("sam.loadFailed"));
    }
    renderSamAchievements(payload);
    setStatus(t("sam.loaded"), "ok");
  } catch (error) {
    setStatus(error.message, "error");
    samAchievements.append(createEmptyState(error.message));
  }
}

function renderSamPlaceholder(titleText, detailText) {
  samSelectedGame.hidden = true;
  samSummary.hidden = true;
  const empty = document.createElement("article");
  empty.className = "sam-empty";

  const logo = document.createElement("img");
  logo.src = "/sh.ico";
  logo.alt = "";

  const title = document.createElement("strong");
  title.textContent = titleText;

  const detail = document.createElement("span");
  detail.textContent = detailText;

  empty.append(logo, title, detail);
  samAchievements.replaceChildren(empty);
}

function renderSamSelectedGame(game) {
  if (!game) {
    samSelectedGame.hidden = true;
    return;
  }
  samSelectedGame.hidden = false;
  samSelectedGame.style.backgroundImage = `linear-gradient(90deg, rgba(15, 19, 24, .96), rgba(15, 19, 24, .76)), url("${headerImage(game)}")`;

  const image = document.createElement("img");
  image.src = game.iconUrl;
  image.alt = "";
  image.addEventListener("error", () => {
    image.replaceWith(createImageFallback(game));
  });

  const info = document.createElement("div");
  const label = document.createElement("span");
  label.textContent = t("sam.selectedGame");
  const title = document.createElement("strong");
  title.textContent = game.name;
  const meta = document.createElement("small");
  meta.textContent = `${formatNumber(game.hours)} ${t("unit.hoursShort")} в Steam${hasRealLastPlayed(game) ? ` · ${t("sort.lastLaunch").toLowerCase()} ${formatDate(game.lastPlayed)}` : ""}`;
  info.append(label, title, meta);

  const action = document.createElement("button");
  action.type = "button";
  action.className = "sam-unlock-all";
  action.textContent = t("sam.unlockAll");
  action.disabled = !selectedSamAchievements.some((achievement) => !achievement.isAchieved && achievement.canEdit !== false);
  action.title = action.disabled
    ? t("sam.noClosed")
    : t("sam.unlockAllTitle");
  action.addEventListener("click", unlockAllSamAchievements);

  samSelectedGame.replaceChildren(image, info, action);
}

function renderSamAchievements(payload) {
  selectedSamAchievements = payload.achievements || [];
  renderSamSelectedGame(currentGames.find((game) => String(game.appid) === String(payload.appid)));
  const percent = payload.total ? Math.round((payload.unlocked / payload.total) * 100) : 0;
  samSummary.hidden = false;
  samSummary.replaceChildren(
    createInsightCard(t("sam.total"), formatNumber(payload.total), t("sam.achievements")),
    createInsightCard(t("sam.unlocked"), formatNumber(payload.unlocked), `${percent}%`),
    createInsightCard(t("sam.locked"), formatNumber(payload.total - payload.unlocked), t("sam.left")),
  );

  samAchievements.replaceChildren();
  if (!payload.achievements?.length) {
    samAchievements.append(createEmptyState(t("sam.noAchievements")));
    return;
  }
  for (const achievement of payload.achievements) {
    samAchievements.append(createAchievementCard(payload.appid, achievement));
  }
}

function createAchievementCard(appid, achievement) {
  const card = document.createElement("article");
  card.className = "achievement";
  card.classList.toggle("is-unlocked", achievement.isAchieved);

  const image = document.createElement("img");
  image.src = achievement.icon || "/sh.ico";
  image.alt = "";
  image.loading = "lazy";
  image.addEventListener("error", () => {
    image.src = "/sh.ico";
  });

  const info = document.createElement("div");
  const title = document.createElement("strong");
  title.textContent = achievement.name;
  const detail = document.createElement("span");
  detail.textContent = achievement.description || (achievement.isHidden ? t("sam.hiddenAchievement") : achievement.id);
  info.append(title, detail);

  const state = document.createElement("button");
  state.type = "button";
  state.className = "achievement-toggle";
  if (achievement.canEdit === false) {
    state.textContent = t("sam.protected");
    state.disabled = true;
    state.title = "Steam или игра не разрешает менять это достижение локально";
    card.classList.add("is-protected");
  } else {
    state.textContent = achievement.isAchieved ? t("sam.close") : t("sam.open");
    state.addEventListener("click", () => toggleAchievement(appid, achievement, !achievement.isAchieved));
  }

  card.append(image, info, state);
  return card;
}

async function toggleAchievement(appid, achievement, achieved) {
  if (achievement.canEdit === false) {
    setStatus("Это достижение защищено Steam или самой игрой и не меняется локально.", "error");
    return;
  }
  setStatus(achieved ? "Открываю достижение..." : "Закрываю достижение...", "loading");
  try {
    const params = new URLSearchParams({ appid, id: achievement.id, achieved: achieved ? "1" : "0" });
    const response = await fetch(`/api/sam/achievement?${params}`);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Steam не принял изменение.");
    }
    achievement.isAchieved = achieved;
    await loadSamAchievements({ appid });
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function unlockAllSamAchievements() {
  const appid = String(selectedSamAppId || "");
  const targets = selectedSamAchievements.filter((achievement) => !achievement.isAchieved && achievement.canEdit !== false);
  if (!appid || !targets.length) {
    setStatus(t("sam.noClosed"), "error");
    return;
  }

  const button = samSelectedGame.querySelector(".sam-unlock-all");
  if (button) {
    button.disabled = true;
    button.textContent = t("sam.opening");
  }

  setStatus(`Открываю достижения: 0 из ${targets.length}`, "loading");
  let done = 0;
  try {
    for (const achievement of targets) {
      const params = new URLSearchParams({ appid, id: achievement.id, achieved: "1" });
      const response = await fetch(`/api/sam/achievement?${params}`);
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Steam не принял изменение.");
      }
      done += 1;
      setStatus(`Открываю достижения: ${done} из ${targets.length}`, "loading");
    }
    await loadSamAchievements({ appid });
    setStatus(`Открыто достижений: ${done}`, "ok");
  } catch (error) {
    setStatus(`${error.message} Открыто: ${done} из ${targets.length}.`, "error");
    await loadSamAchievements({ appid });
  }
}

function setStatus(message, type) {
  window.clearTimeout(statusHideTimer);
  statusBox.textContent = message;
  statusBox.dataset.type = type;
  statusBox.classList.toggle("is-visible", Boolean(message));

  if (type === "ok") {
    statusHideTimer = window.setTimeout(() => {
      statusBox.classList.remove("is-visible");
    }, 2600);
  }
}

function formatNumber(value) {
  return new Intl.NumberFormat(settings.language === "en" ? "en-US" : "ru-RU", { maximumFractionDigits: 1 }).format(value);
}

function realLastPlayed(game) {
  return Number(game.lastPlayed || 0) > 86400 ? Number(game.lastPlayed) : 0;
}

function hasRealLastPlayed(game) {
  return realLastPlayed(game) > 0;
}

function formatDate(timestamp) {
  return new Date(timestamp * 1000).toLocaleDateString("ru-RU");
}

function createImageFallback(game) {
  const fallback = document.createElement("div");
  fallback.className = "image-fallback";
  fallback.textContent = game.name.startsWith("App ") ? `#${game.appid}` : initials(game.name);
  return fallback;
}

function headerImage(game) {
  return `/api/image?appid=${encodeURIComponent(game.appid)}&type=header`;
}

function preloadSteamImages(games) {
  const urls = new Set();
  for (const game of games) {
    if (!game) {
      continue;
    }
    urls.add(game.iconUrl);
    urls.add(headerImage(game));
  }
  for (const url of urls) {
    const image = new Image();
    image.src = url;
  }
}

function initials(name) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase();
}

function starIcon() {
  return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 2.7 5.5 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1-4.4-4.3 6.1-.9L12 3Z"/></svg>';
}

function bookmarkIcon() {
  return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 4h12v17l-6-4-6 4V4Z"/></svg>';
}

function trophyIcon() {
  return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 21h8"/><path d="M12 17v4"/><path d="M7 4h10v5a5 5 0 0 1-10 0V4Z"/><path d="M5 5H3v3a4 4 0 0 0 4 4"/><path d="M19 5h2v3a4 4 0 0 1-4 4"/></svg>';
}
