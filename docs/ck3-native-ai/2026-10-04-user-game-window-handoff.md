# Robert campaign: user game window handoff

Recorded 2026-10-04, Asia/Shanghai. The user requested CK3 for personal play.

## Desktop and runtime ownership

Root normally stopped its isolated R0028 CK3 process 57052 at 06:41:01.922114 UTC. Managed controller session 97602 exited successfully. All SDK sessions are closed. The user owns the game window now. Do not start CK3, rebind, run live acceptance, inject, or send game input until the user says personal play has finished. Offline files and reports may continue.

This temporary desktop handoff does not restore any nonwar constraint. Combat and religion remain authorized. Keep independent work parallel and use minimized background instances when live work resumes.

## Last normal saved campaign

- Robert 29829; episode `native-29829-2bc2d599f7f9`; ordinary campaign, XAR off, no pact.
- R0028 canonical `xenoamess-full-tower-eb9d2c1186--eternal-recurrence--R0028`; execution `fe1155b8-cbee-447c-bc9c-126703932f52`.
- State: `Z:/ck3_mod_rewrite_process_assets/g2-robert-mainline-12003-v55-20261004/state`.
- Normal checkpoint h7123, raw date 53251464, 95107672 bytes, SHA-256 `5fa096c5a155a14ae5a88e4e46c511584e6474b8b9eb21ffd158c9c9ff062ee4`.
- Last closed capture: `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/runtime-preparation/v56/actual-r28-gather-finish-pre-stop-sway-four-01/result.json`.
- Saved calendar 4464; resumed 1311; October 4 increment 439. Eight new normal days each closed and saved. Natural succession 0; G2 5/8 and NW2 2/4 remain unchanged.

## Actual current military state

War 129 ended after one white-peace offer and three ordinary days, independently verified absent and normally saved. The reply type itself was not observed. Subsequent standdown completed.

Event 25 `bookmark.1071` option 2 started attacker war 117440524 against 35991. The three port objectives are 470, 3711, and 472. The source AI tree was frozen before the choice. Current score is zero.

- Army 184549452: actual 3000/3000, 24 regiments, regular at capital 2619; supply 99.9985/100, monthly change -4.54545, attrition zero.
- Army 301989997: eight-day gathering completed; actual 3681/3884, 41 regiments, regular at 2619; supply 300/300, monthly change -4.54545, attrition zero.
- Enemy 268435597: actual 2459/4702, 41 regiments, moving from 510 toward 470 along the observed 12-province route.
- The two player armies remain distinct. Summed current strength 6681 is not a merged army.
- Commander 34867, quality 28, was the highest current legal candidate and was assigned to 184549452 with independent readback. Robert's higher quality 33 had CanAssign=false and no published reason.
- Army 184549452 has a verified route preview 2619 → 8651 → 1038 → 472, but no movement order. Target supply limit 4025, initial used supply zero; no published ETA or embarkation quote.

Original Sway 134217986 against 34333 remains active. The four pre-stop queries are archived at raw date 53251464: continuation true, chance 45%, three attached empty rings without gaps. The previously verified beneficial +25 loop remains qualified; whole-scheme lifecycle and natural succession remain pending.

## Offline preparation and next live entry

Combined source `f3f365c53d3708f520e0142a1b81a484b0c31df3` is published and frozen in `Z:/g61`. It includes current-person/knight identity, primary levy damage, the Python P1 frozen tick adapter/runner, and the actual-build current cash reader.

The single all-four-target strict Release build, jobs 64, compiled successfully in 77.746665 seconds. Actual build plan, CMake cache, and compile definitions prove 115 flags, 65 on and 50 off, including WAR_CASH. The earlier stdout count 64/51 came from baseline preparation before the selected flags were applied. Official exact-head static CI run 37183133742 succeeded.

Binary freezing hit a real inventory KeyError for generated `white_business_exact_pins_v1.inc`. The offline repair must register the actual generated compiled input with its own hash and generation provenance, then freeze the already successful build. No recompilation is needed. R0029 has not been allocated, prepared, rebound, or launched.

After the user releases the game: complete the freeze-only repair; render the latest full saved pair and ten streams once; perform official prepare/verify/stage, retire R0028, rebind to the normal saved campaign, and preflight. Allocate and launch the next minimized instance. Capture the original four Sway queries before advancing, then make the one paused current-cash query. Continue the port war using actual army and supply state. New battle-loss fields and P1 tick remain static-ready until a real current main battle frame is sampled.
