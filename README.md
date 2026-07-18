# GameHelper Steam

ПК-приложение для локального анализа Steam-библиотеки: показывает общее время, количество игр и список игр с часами.

Основной режим работает без API key и без входа в Steam через приложение. GameHelper читает локальные файлы установленного Steam:

- `steamapps/appmanifest_*.acf` — установленные игры и их названия;
- `userdata/*/config/localconfig.vdf` — локально сохраненное время игры.

## Запуск

Обычный запуск красивого desktop-интерфейса:

```powershell
.\run_gamehelper.bat
```

Или напрямую:

```powershell
python desktop_web_app.py
```

Кнопка `Сканировать` делает только локальный поиск. Кнопка `Обновить названия` может обратиться к публичной странице Steam Store без API key, чтобы дозаполнить названия для старых или удаленных игр, где локальный Steam хранит только AppID.

## Дополнительно

Сборка `.exe`:

```powershell
python -m PyInstaller --noconsole --onefile --name GameHelperSteam --icon sh.ico --add-data "public;public" --add-data "sh.ico;." --add-data "back.png;." --add-data "app_config.json;." --add-data "SamHelper\bin\x86\Release;SamHelper" desktop_web_app.py
```

Готовый файл появится здесь: `dist\GameHelperSteam.exe`.

Сборка установщика:

```powershell
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer\GameHelperSteam.iss
```

Готовый установщик появится здесь: `dist\GameHelperSteamSetup.exe`.

## GitHub Releases и обновления

Приложение умеет проверять новую версию через GitHub Releases. Для подключения:

1. Создай репозиторий на GitHub и залей исходники.
2. В `app_config.json` укажи репозиторий в формате `owner/repo`.
3. Перед релизом обнови `version` в `app_config.json` и `MyAppVersion` в `installer/GameHelperSteam.iss`.
4. Собери `GameHelperSteam.exe` и `GameHelperSteamSetup.exe`.
5. Создай GitHub Release с тегом `vX.Y.Z` и прикрепи файл `GameHelperSteamSetup.exe`.

После этого кнопка проверки обновлений в настройках будет сравнивать текущую версию с последним GitHub Release и открывать страницу установки новой версии.

Серверный запуск для тестов:

```powershell
python app.py
```
