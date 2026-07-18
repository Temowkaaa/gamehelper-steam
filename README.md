# GameHelper Steam

GameHelper Steam - desktop-приложение для Windows, которое локально анализирует Steam-аккаунт и показывает библиотеку игр, часы, избранное, список "хочу поиграть", рейтинг и достижения.

Приложение работает без Steam Web API key и без авторизации внутри GameHelper. Оно читает локальные данные установленного Steam на ПК пользователя.

## Установка

Скачай последнюю версию установщика:

[GameHelperSteamSetup.exe](https://github.com/Temowkaaa/gamehelper-steam/releases/latest/download/GameHelperSteamSetup.exe)

После установки приложение запускается как обычная Windows-программа.

## Возможности

- локальный поиск активного Steam-аккаунта;
- список игр с часами и последним запуском;
- фильтры и сортировка по времени;
- отдельный список игр без времени;
- избранное и "хочу поиграть";
- тир-лист/рейтинг игр;
- просмотр достижений Steam;
- локальный кэш названий и изображений игр;
- проверка обновлений через GitHub Releases.

## Обновления

В приложении есть проверка обновлений в настройках. Новые версии публикуются в GitHub Releases:

[Releases](https://github.com/Temowkaaa/gamehelper-steam/releases)

Если доступна новая версия, GameHelper откроет страницу или установщик обновления.

## Для разработки

Основной desktop-запуск:

```powershell
python desktop_web_app.py
```

Сборка `exe` и установщика:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_release.ps1
```

Готовые файлы появляются в папке `dist`:

- `GameHelperSteam.exe`
- `GameHelperSteamSetup.exe`

Перед новым релизом нужно обновить версию в:

- `app_config.json`
- `installer/GameHelperSteam.iss`

Затем собрать проект, создать новый GitHub Release с тегом вида `v1.0.1` и прикрепить `GameHelperSteamSetup.exe`.
