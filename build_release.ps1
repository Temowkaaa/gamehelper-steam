$ErrorActionPreference = "Stop"

Get-Process -Name GameHelperSteam -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

python -m PyInstaller `
  --noconsole `
  --onefile `
  --name GameHelperSteam `
  --icon sh.ico `
  --add-data "public;public" `
  --add-data "sh.ico;." `
  --add-data "back.png;." `
  --add-data "app_config.json;." `
  --add-data "SamHelper\bin\x86\Release;SamHelper" `
  desktop_web_app.py

& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer\GameHelperSteam.iss
