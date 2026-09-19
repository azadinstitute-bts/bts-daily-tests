# BTS Student Web App — Android 6078 Parity Audit

Date: 2026-09-20
Reference Android release: 1.0.45+6078
Backend baseline: student-api v145
Base web commit: e7e19bb4d818531f58e719d315dca5a4baf42cff
Parity branch: web-parity-6078-20260920

## Safety scope
- Production/main was not modified during implementation.
- No Supabase schema/data/function changes were made for this web parity pass.
- Existing student attempts/results/session tables were not mutated.
- Repo contains deployment artifacts only (no React/Vite source tree or package.json), so changes were limited to targeted compiled bundles plus an isolated parity helper.
- Root and docs deployment copies are kept byte-identical.

## Verified pre-existing gaps found
1. Web client did not send current client build metadata, so current demo minimum-build policy could reject web demo calls.
2. Demo UI still hardcoded Week 1 behavior instead of trusting backend demo access.
3. Demo dashboard requested only the default locked/premium catalog limit instead of Android's full limit 500.
4. Premium demo cards were not handled as a first-class status.
5. Multi-attempt backend support existed but web exposed no safe re-attempt flow/history.
6. Practice submit redirected to the official result instead of the just-submitted practice attempt.
7. Web Question Report opened WhatsApp directly and bypassed the protected backend snapshot/report ID flow.
8. Demo-to-paid safe upgrade hook was missing.
9. Varg 2 Hindi/English were absent from legacy course-filter fallbacks.
10. General support still used WhatsApp instead of the neutral phone dialer.
11. Upcoming label was not Android-parity wording.
12. Long subject/topic metadata was ellipsized instead of wrapping.
13. No web dark-mode parity / matching-grid dark contrast.
14. Backend demo notice was not surfaced with one-time dismissal.

## Implemented parity
- Client identity: web-6078 / app_version_code 6078 / client_build 6078 / api_contract_version 1.
- Dashboard catalog limit 500.
- Backend-controlled demo catalog; removed Week 1 client hardcode.
- Premium cards + generic non-week-specific premium message.
- Re-attempt button using backend can_reattempt/attempt counts.
- Attempt History modal using get_attempt_history.
- Specific attempt result review via attempt_id.
- Practice submission opens its own result while official rank remains backend-controlled.
- Safe demo-to-paid upgrade_demo_session bootstrap.
- Protected report_question flow for live test and result review; backend generates report snapshot/support message.
- Dynamic backend demo courses remain authoritative.
- Varg 2 Hindi/English fallback mapping added.
- Access Code wording humanized.
- Upcoming Tests wording.
- Long subject/topic wrapping.
- Call Support via tel:+919669946966 on login/menu; general support WhatsApp removed.
- Question-report WhatsApp remains only after protected backend report creation.
- Dark/light toggle and matching/structured-question dark contrast.
- Dynamic backend demo notice with demo_flash_id one-time dismissal.

## Static validation
PASS:
- Modern bundle syntax parse.
- Legacy bundle syntax parse.
- Parity helper syntax parse.
- Root/docs modern bundle identical.
- Root/docs legacy bundle identical.
- Root/docs helper/CSS/index identical.
- Branch is based on current main and is not behind main.
- Only web deployment files are changed.

## Final backend read-only sanity
- student-api: v145
- attempt policy: 7 total attempts; attempt 1 official; 6 practice; ranking FIRST_ATTEMPT_ONLY
- demo course options: 15
- Varg 2 Hindi demo rows: 7
- Varg 2 English demo rows: 7
- enabled demo mappings: 102
- verified Week-7 mappings: 102/102
- enabled mappings outside Week 7: 0
- no backend mutation was performed during this web parity pass

## Runtime browser smoke
PASS — non-destructive Chromium integration smoke on the compiled parity branch.

Evidence:
- GitHub Actions run: #10 / run id 35471922674
- Tested commit: 0db49c15528a0645a5e164726a6bb102e0598e2a
- Result markers: `SMOKE_PASS: branch runtime + mocked API integration` and `STATIC_WIRING_PASS`
- Browser console/page diagnostics: no application errors during the passing run
- The smoke mocked student-api responses, so it did not create sessions, attempts, results, or question reports in production.

Covered:
- first-run Privacy & Data Disclosure consent
- paid login flow
- Free Demo login flow
- Varg 2 Hindi and Varg 2 English demo selector options
- demo available + premium card rendering and ordering
- web-6078 metadata on student-api requests
- dashboard limit 500
- dashboard Call Support
- dark -> light mode
- paid Varg 2 Hindi filtering using production-shaped entitlement/test data
- Attempt History: 2/7 used, Official first attempt, Practice second attempt
- practice-attempt result routing with `attempt_id`
- helper dark/light toggle and login Call Support
- static wiring for `report_question`, `upgrade_demo_session`, and build 6078

## Production contract read-only verification
PASS — current student-api v145 source and current production data shapes were inspected without writes.

Client/backend contract:
- All 10 student-api actions called by the parity bundle/helper are routed by v145: `verify_session`, `upgrade_demo_session`, `get_dashboard`, `get_demo_courses`, `get_test_public`, `submit_native_result`, `get_attempt_history`, `get_result_detail`, `get_leaderboard`, `report_question`.
- `get_test_public` is the attempt start/resume authority and returns the attempt token/timestamps used by the web client.
- `submit_native_result` requires the same `attempt_token`, `submission_id`, `test_code`, and answers sent by the web client.
- v145 marks attempt 1 as official/ranked and later attempts as practice while preserving the official rank.
- `get_attempt_history` returns the fields consumed by the helper: max/used/remaining plus attempt id/number, official flag, score/total and submitted time.
- `get_result_detail` accepts `attempt_id` and binds it to the logged-in mobile + test before returning a practice result.
- `report_question` validates session/access or the attempt token and creates the protected backend snapshot/report ID; the client does not submit its own question snapshot.
- build 6078 uses the backend timer rule of 6/5 minute per question (50Q = 60 minutes, 100Q = 120 minutes).

Production mapping shape:
- Active Varg 2 Hindi entitlements use canonical `course_id=varg2_hindi`.
- Week-7 Hindi tests use `Teacher - Hindi` / `Varg 2 Hindi`; Week-7 English tests use `Teacher - English` / `Varg 2 English`.
- An earlier smoke failure using a generic `course=Teacher` entitlement was classified as an unrealistic test-harness shape, not an application defect; the production-shaped rerun passed.

## Remaining limitation
A live production submit/report mutation was intentionally not executed. That would create or alter real student/session/attempt/result/report data, and Free Demo validation itself can create a demo student row. With the compiled-browser smoke plus source-level v145 contract verification passing, a synthetic production write would add comparatively little information while increasing production-data risk.

## Deployment gate
Focused/offline/runtime evidence is now sufficient for a controlled deployment gate:
- static bundle validation: PASS
- root/docs parity: PASS
- production configuration/mapping read-only sanity: PASS
- compiled Chromium integration smoke: PASS
- student-api v145 action/payload/response contract alignment: PASS
- live production mutating submit/report proof: NOT RUN by design

After merge, verify the live site read-only first (asset/version load, login screen, demo selector availability, theme/support controls). Any real account attempt/submit should be treated as normal production usage, not synthetic test data.

