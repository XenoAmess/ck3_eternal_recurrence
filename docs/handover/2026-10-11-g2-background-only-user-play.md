# G2 background-only continuation while the owner plays CK3

Recorded 2026-10-11T05:05:16.995792+00:00, after the owner's explicit instruction to prohibit CK3 use on
this machine and continue G2 research in the background. This instruction remains
in force until the owner explicitly lifts it. Do not launch, attach, inject,
query, send RPC/input, change windows, or run real-game acceptance on this machine.
Do not operate Steam or the owner's game. Offline source research, implementation,
compilation and necessary new software qualification remain authorized, with the
existing64-agent team. Root integrates useful changes into master; no archive
branches are created for this work.

## Owner-authorized manual startup repair

The owner subsequently reported a failed manual launch and explicitly requested
repair. This grants agent01 the narrow Steam/launcher repair and startup
verification needed to restore the owner's game. It does not resume SDK,
injection, automated play, RPC, ordinary-campaign continuation or acceptance.
The general local-game prohibition above remains in force after the repair.

Today's launcher log records `spawn ck3.exe ENOENT` at05:27,05:29 and05:32 UTC.
The stock executable exists and launcher settings point to the correct binaries
directory. Steam's CK3 workshop update committed with NoError; the screenshot's
patch progress does not establish a CK3 installation fault. The identical
Oct6 inherited-environment incident and its proven remedy are documented in
[testing workflow](../testing-workflow.md#codex-环境启动-steam-导致-launcher-enoent2026-10-06-实测).
Current read-only confirmation found `NODEFAULTCURRENTDIRECTORYINEXEPATH=1`
in both Steam158580 and Launcher174856. Agent01 normally closed the failed
launcher and Steam, then started Steam171884 with only that key removed from
its inherited environment at2026-10-11T05:44:32.012Z. No system environment,
game files, mode or playset was changed. See the
[current environment receipt](D:/codex-ck3-background-spill/native71-continuation-20261010/runtime-01/native84-r0099/manual-startup-diagnosis01/ROOT-ACTUAL-SINGLE-STARTUP-ENV-KEY.json)
and [normal restart receipt](D:/codex-ck3-background-spill/native71-continuation-20261010/runtime-01/native84-r0099/manual-startup-diagnosis01/ROOT-ACTUAL-CLEAN-STEAM-NORMAL-RESTART.json).
The owner then explicitly cancelled testing and ordered pure background G2
work. Startup verification is `NOT_RUN_CANCELLED_BY_OWNER`: the single Steam
applaunch request opened Launcher66584, but Start Game was never invoked.
No controller remains able to send further input. Steam and the launcher were
left for the owner. See the
[cancellation receipt](D:/codex-ck3-background-spill/native71-continuation-20261010/runtime-01/native84-r0099/manual-startup-diagnosis01/ROOT-ACTUAL-MANUAL-STARTUP-DIAGNOSIS-CANCELLED-BY-OWNER.json).
This continuation performs source work and master integration only; no local
tests, game launches, Steam/window operations or automated play are resumed.

## Retained actual progress and cancelled execution

R99 same-PID recovery passed13/13 at2026-10-11T04:43:29.913656Z, Source594,
owned Game169036, original Robert29829 episode. Response600 succeeded:
private-query-player-construction-receipt-v1, result applied, raw53290176.
The subsequent D-only controller failed because --current-save was bound to the
binary xar_checkpoint.ck3 instead of the existing SAVE JSON response. No610 RPC
was submitted, no new game day or SAVE occurred. Original failed artifacts remain.
The corrected resume600 recipe is authored but must NOT execute while this ban
is in force. Its input is the actual R98 520 SAVE JSON, not the binary save body.

Saved baseline remains6077/H10134, with R98 complete13 recovery and applied Gift
ledger retained. Five daily SAVEs to6082 are deferred by the owner, Gift remaining0.
M4 complete, G2 6/8, NW2 2/4, M6 partial, M7 incomplete, natural succession0.
No research or offline test result grants new live or saved-day credit.

01 cancelled subsequent automation: SDK reader48949 exited0 and keeper20375
exited0, thread_exited=true/failure=null; release.ok=true/resources[], CAS1976
at2026-10-11T05:04:11.875130Z. The [actual user-stop receipt](D:/codex-ck3-background-spill/native71-continuation-20261010/runtime-01/native84-r0099/ROOT-RUNTIME99-USER-STOPPED-RESULT.json)
records the outcome. Game169036, managed wrapper117272 and owned job30d27ecb
were preserved, with no Game query/input/window/close/kill operation.
02 coordinates functional research/implementation packages from the existing
native decision trees and one-generation blocker ledger. Root owns master and
the consolidated daily/weekly reports; workers submit evidence and report fields.
