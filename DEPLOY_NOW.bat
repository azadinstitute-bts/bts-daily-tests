@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "REPO=https://github.com/azadinstitute-bts/bts-daily-tests.git"

where git >nul 2>nul
if errorlevel 1 (
  echo ERROR: Git install nahi mila. Is window ka screenshot bhejiye.
  pause
  exit /b 1
)

where py >nul 2>nul
if %errorlevel%==0 (
  py build_site.py
) else (
  python build_site.py
)
if errorlevel 1 (
  echo ERROR: Website build nahi hua.
  pause
  exit /b 1
)

if not exist ".git" git init

git config user.name "Azad Institute BTS"
git config user.email "azadinstitute-bts@users.noreply.github.com"
git branch -M main

git remote get-url origin >nul 2>nul
if errorlevel 1 (
  git remote add origin "%REPO%"
) else (
  git remote set-url origin "%REPO%"
)

git add -A
git commit -m "Deploy BTS daily test portal"
if errorlevel 1 (
  echo Note: Commit create nahi hua; existing local commit ho sakta hai.
)

echo.
echo GitHub login window aaye to login/authorize karein.
git push -u origin main --force
if errorlevel 1 (
  echo.
  echo ERROR: Push failed. Is window ka screenshot bhejiye.
  pause
  exit /b 1
)

echo.
echo SUCCESS: Repository ki purani files replace ho gayi hain.
echo Ab GitHub Settings - Pages me main branch aur /docs select karna hai.
pause
endlocal
