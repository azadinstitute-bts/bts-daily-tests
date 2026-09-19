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

## Deployment gate
Do not merge to main until a focused browser smoke covers:
- paid login
- free demo login
- Varg 2 Hindi/English demo selector
- demo available + premium ordering
- one official attempt + one practice re-attempt
- practice result + attempt history
- question report
- dark/light toggle
- Call Support
- Varg 2 Hindi paid filtering if a suitable account is available

This checkpoint intentionally keeps live production unchanged until runtime smoke is accepted.
