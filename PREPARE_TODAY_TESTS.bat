@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py prepare_today.py
) else (
  python prepare_today.py
)
if errorlevel 1 (
  echo.
  echo ERROR: Upar dikhayi gayi problem ko theek karein.
  pause
  exit /b 1
)
echo.
echo Done. Preview: docs\index.html
start "" "%~dp0docs\index.html"
pause
