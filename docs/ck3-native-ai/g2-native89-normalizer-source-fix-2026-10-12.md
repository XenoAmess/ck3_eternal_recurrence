# Native89 whole-build normalization, 2026-10-12

Native89 actually compiled all 917 owners and captured their dependencies.
Its explicit archive continuation produced 597 ordered members; the following
link-only continuation succeeded after binding the installed resource-tool
directory. This remains build evidence, without Game or M7 credit.

The actual dependency-verification packet is 45,460,300 bytes. The normalizer's
old 32 MiB JSON bound could not admit it. Its JSON bound is now finite 64 MiB;
input and proof bounds remain 64 KiB, with an explicit artifact bound.

The first normalization invocation then exposed a separate source defect:
`deps()` saved its raw dependency JSON reference in `ref`, overwrote that local
for each header, and returned the last header reference. The whole-build join
correctly rejected it. The fix saves and returns the raw reference in `dr`;
the per-header checks, raw-reference hashes and strict dependency join remain.

The exact reviewed fixed source is 20,478 bytes, SHA-256
`b5a05d8f2082e364aa477c4f24289117955b37db7d5468e1b12e4e4c736e1a1b`.
Two reviewers reused the prior complete 389-line review and independently read
the bounded changes; Root also read them and checked exact byte differences.
No suite, fixture or verification import was run.

The first actual failure has exit 2 and preserves `deps o`. A subsequent actual
caller's 300-second wait expired, although its slower child later wrote the
whole-build proof. That second proof has no independently observed child exit
code and is not adopted for runtime. Root selected separate third input/proof/
execution paths and finite 900-second supervision, preserving all prior files.

Evidence remains external under `g2-native89-production01/closure03`:
`ROOT-WHOLE917-NORMALIZER-ACTUAL-STOP.json`,
`ROOT-WHOLE917-NORMALIZER-ACTUAL-STOP-02.json` and
`ROOT-WHOLE917-CLOSURE-PROOF-02.json`. A proof file alone is insufficient;
runtime adoption requires actual exit 0, proof readback and the independent
execution receipt. The third invocation was pending at this record's creation.

At 04:06:19 UTC, the third invocation actually exited 0 after 530.62 seconds.
Root read the complete proof and external execution receipt. The proof binds
all 917 fresh owners and dependency outputs, zero reused owners, 597 exact
ordered archive members and the actual link closure to SDK91
`50a1a5451227d1b30f42394dd02ddfbaea26a1ff`. The 17,807,360-byte DLL has SHA-256
`7d97c73e24a68db1cf6cc67b7cb684a551fd0130df5d5a13bf5e092ac0e2fc02`.

The independent proof is `ROOT-WHOLE917-CLOSURE-PROOF-03.json`, 10,475 bytes,
SHA-256 `e2077b1cbbc58b42ce09f2a0913c3670ad0c2aef3c651543e8de07872f94c00d`.
Its execution receipt is `ROOT-WHOLE917-NORMALIZER-EXECUTION-03.json`, 2,123
bytes, SHA-256 `b2d9b825714d3579d275dff4e92a15d882880ce592fde11a7031795089a38edd`.
The first failure and second timeout proof remain unchanged. No normalizer
process termination occurred in the unsuccessful timeout-cleanup attempts.

Root derived separate small loader metadata, preserving the exact three
original helper EXE rows and their original provenance, and adding the actual
new DLL row. No helper binary was rehashed or copied for this derivation.
An initial metadata summary used an absent `name` key after writing the three
metadata files; the corrected summary read and compared those files without
overwriting them. This compile closure does not grant Game, family or M7
qualification. R104 runtime adoption remains a separate actual operation.

## R104 actual runtime, 05:35 UTC update

Root adopted the homogeneous Native89 DLL for a separate R104 ordinary
campaign attempt. The new Game PID is 191172, with kernel creation ticks
`134362549441966160`; it remained minimized. Fresh desktop pixels were reviewed
to confirm Steam offline before the actual launch. No Steam mode change or
desktop test fixture occurred.

The first SDK qualification wrapper failed before SDK startup or RPC:
`ModuleNotFoundError: No module named 'native_source_profile'`. Its phase RED,
stderr and empty guard leaf remain unchanged. An explicitly separate Source27
startup repair inserted the reviewed F22 source directory into this wrapper's
Python search path before the original stdio owner was executed. It did not
reprepare the campaign, relaunch the Game or resend a business request.

The repaired held SDK session observed five original core-readiness timeouts,
then a sixth ready result. Its single full paused snapshot subsequently passed
all thirteen qualification checks at 05:26:29 UTC. These are thirteen checks,
not thirteen accepted capability families or R104 final full13 closure. The
actual frame was date 53290320, public revision 2, native revision 1, living
actor 29829, run `native-29829-2bc2d599f7f9`, bridge PID 191172 and connection
generation 1. Ordinary succession remained `xar_off` and the campaign goal
retained zero reconciled successions.

The first ordinary `ck3_auto_turn` was submitted once to that same held SDK.
Its original response completed at 05:35:18 UTC with status `executed` and
step `private-query-player-construction-receipt-v1`. It rechecked a restored
construction receipt and returned the same date/public/native frame. Historical
plan observations remain historical; they are not current-build qualifications.
No new date, natural successor or SAVE was established. Verified saved-day
credit remains the R103 baseline of 6082, with zero additional saved days.

Actual evidence is external below
`native71-continuation-20261010/runtime-01/native84-resume-20261012/native89-r0104/`:

- `managed/operator/ROOT-R85-COLD-CORE-WAIT.json`, including all original core outcomes.
- `managed/operator/ROOT-R85-COLD-PAUSED-SNAPSHOT-QUALIFIED.json` and its original full response.
- `root-first-ordinary01/ROOT-ACTUAL-FIRST-ORDINARY.json`.
- `managed/operator/gameplay-responses/810-r0104-first-ordinary-000001-normal.json`.

The SDK application, outer supervisor and Game were still running at this
update. No final SAVE, normal Game exit, natural M7 acceptance or R104 final
freeze is inferred from startup, source review or the ordinary response.

The original source/build review deadline remains 2026-10-12 16:47:28.264315 UTC.
The current saved campaign and its full13 input keep their separate limited
protection. Copies and source fixes do not extend either deadline; reclamation
continues under the common storage policy.

## R104 user occupation and local release, 06:26 UTC update

The next four original ordinary requests completed without replay. Three
continued the construction-receipt queries on the same known frame. The fifth
ordinary request returned at 06:11:30 UTC with step
`query-observed-first-heir-marriage-result-v1-private` and result status
`marriage`; its result did not establish a new ending frame. These source and
receipt observations add no new date, SAVE, saved-day or natural M7 credit.

The user then reserved this machine for their own CK3 play and prohibited
further managed CK3 use. Root stopped all new Game/SDK requests and desktop
work. A proposed one-shot WM_CLOSE refused before submission because the
previous HWND no longer belonged to the selected PID. The subsequent held
kernel-identity observation confirmed old Game PID 191172 and its exact
creation ticks had already exited, with actual exit code 1. No close message
or forced termination was sent; an orderly Game exit or its cause is not proved.

Root atomically published one local `exit_client` marker to the existing file
inbox. The original reader handles that marker by returning before any MCP
call; it was not a Game RPC. The outer reader finished at 06:24:30 UTC with
actual exit code 0. At 06:26:35 UTC, a separate held kernel identity observation
confirmed SDK application PID 26348, creation ticks `134362559499577153`, had
exited with actual code 0. The screen keeper released its own CAS lease at
06:23:23 UTC, sequence 2375. Steam mode, OBS, ToDesk and user-owned processes
were not changed by these release operations.

The new small external records are
`ROOT-USER-OCCUPATION-LOCAL-RELEASE.json` and
`ROOT-USER-OCCUPATION-SDK-OBSERVATION.json`, beside the existing R104 packet;
screen release is in the separate `r104-screen-preparation/SCREEN-KEEPER-STOPPED.json`.
Original response files, failures and last verified R103 saved baseline remain
unchanged. This release is not a new final SAVE/full13 freeze, SDK durability
acceptance or normal Game-exit proof. Saved-day credit stays 6082 plus 0.

The existing 64-lane research team continues pure background source work and
master integration. No further EXE reads, Game/SDK requests, screen operation
or test execution are authorized in this attempt while the user occupies CK3.
The original storage deadlines remain in force.
