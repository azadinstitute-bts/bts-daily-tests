BTS DAILY TEST PORTAL - FAST SETUP

Repository:
https://github.com/azadinstitute-bts/bts-daily-tests

FIRST DEPLOY
1. Is ZIP ko Extract All karein.
2. Extracted BTS_QUICK_DEPLOY folder kholein.
3. DEPLOY_NOW.bat double-click karein.
4. GitHub login/authorization aaye to allow karein.
5. GitHub me Settings > Pages kholein.
6. Source: Deploy from a branch
7. Branch: main
8. Folder: /docs
9. Save.

DAILY / WEEKLY HTML UPLOAD WORKFLOW
1. Apni Own Form HTML files incoming folder me copy karein.
2. ARRANGE_AND_PUBLISH.bat double-click karein.
3. Script file name / TEST_TITLE se Week aur Day padhega.
4. Date modified ignore hogi.
5. Schedule base: Week 1 Day 1 = 06 July 2026 IST.
6. Weekly Combined file me Day na ho to usko Week ka Day 7 maana jayega.
7. Script iPhone-compatible docs build karega, commit karega aur GitHub push karega.
8. 1-2 minute baad students ko portal URL dein.

EXAMPLES
- Week_1_Day_06 -> 2026-07-11
- Week_1_Weekly_Combined -> 2026-07-12
- Week_2_Day_01 -> 2026-07-13

IMPORTANT
- Original HTML daily_uploads folder me unchanged rehti hain.
- docs folder me iPhone-compatible web copies banti hain.
- Existing shared links preserve karne ke liye build old manifest filenames reuse karta hai.
- Repository public hai; page source technical users dekh sakte hain.
