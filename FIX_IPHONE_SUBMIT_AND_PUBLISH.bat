@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo ==============================================
echo BTS IPHONE FINAL SUBMIT FIX + GITHUB PUBLISH
echo ==============================================
python build_site.py
if errorlevel 1 goto :fail
git add -A
git commit -m "Fix iPhone Safari final submit storage handling"
if errorlevel 1 echo No new commit needed or commit skipped.
git push origin main
if errorlevel 1 goto :fail
echo.
echo SUCCESS: iPhone Final Submit fix published.
echo Website: https://bilaspurtestseries.com/bts-daily-tests/
echo Live update me 1-2 minute lag sakte hain.
pause
exit /b 0
:fail
echo.
echo ERROR: Fix publish nahi hua. Upar ka message dekhein.
pause
exit /b 1
