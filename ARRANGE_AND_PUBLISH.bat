@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ==============================================
echo BTS SCHEDULE ARRANGE + IPHONE BUILD + GITHUB PUSH
echo Week 1 Day 1 = 06 July 2026 IST
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
  py prepare_by_schedule.py
) else (
  python prepare_by_schedule.py
)
if errorlevel 1 (
  echo.
  echo ERROR: Arrange/build fail hua. Upar ka message dekhein.
  pause
  exit /b 1
)

git add daily_uploads docs prepare_by_schedule.py build_site.py ARRANGE_AND_PUBLISH.bat README_FAST_HINDI.txt

git diff --cached --quiet
if %errorlevel%==0 (
  echo.
  echo Koi naya publish change nahi mila. Portal already updated hai.
  pause
  exit /b 0
)

git commit -m "Arrange iPhone tests by schedule date"
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
echo SUCCESS: Files schedule date ke hisab se arranged aur portal published.
echo Website: https://bilaspurtestseries.com/bts-daily-tests/
echo GitHub update ko live hone me 1-2 minute lag sakte hain.
pause
endlocal
