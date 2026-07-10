@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ==============================================
echo BTS AUTO ARRANGE + IPHONE BUILD + GITHUB PUSH
echo ==============================================
echo.

where git >nul 2>nul
if errorlevel 1 (
  echo ERROR: Git install nahi mila.
  pause
  exit /b 1
)

where py >nul 2>nul
if %errorlevel%==0 (
  py prepare_by_file_date.py
) else (
  python prepare_by_file_date.py
)
if errorlevel 1 (
  echo.
  echo ERROR: Arrange/build fail hua. Upar ka message dekhein.
  pause
  exit /b 1
)

git add -A
git diff --cached --quiet
if %errorlevel%==0 (
  echo.
  echo Koi naya change nahi mila. Portal already updated hai.
  pause
  exit /b 0
)

git commit -m "Arrange iPhone tests by file date and Week Day"
if errorlevel 1 (
  echo ERROR: Git commit fail hua.
  pause
  exit /b 1
)

git push origin main
if errorlevel 1 (
  echo ERROR: Git push fail hua. Login/Internet check karein.
  pause
  exit /b 1
)

echo.
echo SUCCESS: Sample removed, files arranged, portal published.
echo Website: https://bilaspurtestseries.com/bts-daily-tests/
echo GitHub update ko live hone me 1-2 minute lag sakte hain.
pause
endlocal
