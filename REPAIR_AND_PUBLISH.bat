@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo ==================================================
echo BTS EMERGENCY IPHONE SCRIPT REPAIR + GITHUB PUSH
echo ==================================================
python build_site.py
if errorlevel 1 goto :fail
git add -A
git commit -m "Repair iPhone test JavaScript syntax and submit flow"
if errorlevel 1 echo No new commit needed or commit skipped.
git push origin main
if errorlevel 1 goto :fail
echo.
echo SUCCESS: iPhone script repair published.
echo Website: https://bilaspurtestseries.com/bts-daily-tests/
echo Portal links now include a fresh cache version.
echo GitHub update ko live hone me 1-2 minute lag sakte hain.
pause
exit /b 0
:fail
echo.
echo ERROR: Publish rok diya gaya. Upar JavaScript check ya Git error dekhein.
echo Broken files GitHub par push nahi ki gayi hain.
pause
exit /b 1
