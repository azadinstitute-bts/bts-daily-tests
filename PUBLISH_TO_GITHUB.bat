@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py build_site.py
) else (
  python build_site.py
)
if errorlevel 1 (
  echo Build failed.
  pause
  exit /b 1
)
git add -A
git diff --cached --quiet
if %errorlevel%==0 (
  echo Koi naya change nahi mila.
  pause
  exit /b 0
)
git commit -m "Publish daily tests"
if errorlevel 1 (
  echo Commit failed.
  pause
  exit /b 1
)
git push origin main
if errorlevel 1 (
  echo Push failed. GitHub login check karein.
  pause
  exit /b 1
)
echo.
echo Website update GitHub par push ho gaya.
pause
