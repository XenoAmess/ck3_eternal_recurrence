# GEN-034-D candidate builder handoff (2026-09-21)

## Current boundary

This package is now **production-live capture / terminal continuation RED**.
Canonical R0024 captured the six source executions from one new Raiktor
creation and handed the same process to production `native_auto_run`, but that
call failed during prelaunch profile validation, before the planner or turn
limit could run. The deterministic return is `session_exit` / `failed` with
`attempted_turns=0`, so no matching terminal intercept or terminal action was
possible. GEN-034-D therefore remains `3/4`, the authoritative G2 count remains
`1/8`, and R458 is not reused as final evidence.

The package was integrated through
`fd69f836455e0a81721d877de25b22a3bc52d1dc`; the live attempt ran from current
`origin/master@08cfd3df8d22b5548f4cafa190f5fa6f41895af3`. R884 and all newer
preview runs had been reclaimed before the GEN034-D run. R0024 cleanup closed
the driver and left no CK3 process. Read-only `verify_profile` reproduces the
root cause: the formal profile lacks `xar-autoplayer-environment.json`. The next
fix is to run the supported formal profile prepare/verify flow on a successor
continuation from the frozen safe pair; do not hand-author the manifest or
launch another natural-source search.

Final candidate tip: `b9e3357dfb14825092e66d9b92acc4e5347b070a`.
The previously reviewed `fe64549f3e89488d905a280895cfefa5271e2a17`
candidate was rebased without conflicts onto
`origin/master@b9cf5981c8408e1e63d5a7063783ce5a7a15a377`. The last two code-bearing
commits make the generated receipt byte-stable across a clean LF checkout and
refreeze the 479-file closure; this closes the pre-launch digest RED found by
independent review of the earlier `0cb0887c` candidate.

## Frozen runtime and candidate

- Durable runtime archive:
  `Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-runtime-b9e3357d-20260921`
  (ZIP SHA-256
  `53D4A2F34D0F835E1AA0B54A34AF973C8FEFEF378BB221F321714319ED75BFAF`)
- Candidate bundle:
  `Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-candidate-b9e3357d-20260921`
- Bundle manifest: `gen034-d-candidate-bundle.json`, SHA-256
  `68FEB8FAAFC240DC54EB5367C474D30CE511941E86E7BD0581AE94075D102389`
- Outer-owner manifest SHA-256:
  `DB5DB89FAD26F8B985CAD26DA545370C8D45BB42E8D574D53A30C7DCFD44BB6D`
- Lifecycle manifest SHA-256:
  `66CBCEE242289542C991F0681EB08D18FD65C2E8ECC3E5AD058424BD0EF87095`
- Live-adapter manifest SHA-256:
  `A152B818A87F483AA2E5DADA13BA0052FACFCE0237984DB8802C4F45C91E96D2`

Release binaries from the f342 private source were rebuilt with the VS18 Release
configuration:

| File | Size | SHA-256 |
| --- | ---: | --- |
| `xar_ck3_bridge.dll` | 3,135,488 | `D90F17673D54B37C5B2EF6832624C31386C5905815E2A218AE7ADF7C1C4722AB` |
| `xar_ck3_bridge_injector.exe` | 39,936 | `B3BFE5A603E7772A2E294841E80547F7D795CF4049673ECF76C49A5075CEC52A` |
| `xar_ck3_raiktor_war_bound_private_capture_v1.exe` | 113,664 | `EEE39F858E941E1500DA13FB11906814FA4D70EE42DED894CFDEB03ACEF709B8` |

The exact CK3 executable remains bound to
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
The generic exit-terms reader remains disabled.

## Verification already completed

- Candidate bundle: `verified-no-launch`.
- Outer owner: `GREEN_STATIC_EXCLUSIVE_OUTER_OWNER_NO_LAUNCH`.
- Lifecycle: `GREEN_STATIC_SOURCE_SPECIFIC_LIFECYCLE_RUNNER`.
- Candidate live preflight:
  `READY_TO_RUN_G2_SOURCE_SPECIFIC_LIFECYCLE`, mode
  `candidate-source-to-formal-terminal-intercept`.
- Candidate live preflight SHA-256:
  `1B3F456890EC4258D2F1EC1A5A8C8B51FAC64F1702E0B22C3EFB7D5D1D9E4F31`.
- Focused normal suite: `397 passed`.
- Focused optimized suite: `397 passed` (the normal pytest warning about
  assertions outside tests being disabled under `-O` is the only warning).
- Python compilation and `git diff --check`: passed.

No non-hash functional failure remained in the pre-launch builder or runner
tests. The subsequent live evidence and its RED boundary are recorded below.

## R0023 / R0024 live result

- Canonical R0023 (legacy R892) was allocated, then immediately marked
  `voided` because `candidate-live-run-preflight.json` already existed. The
  close reason is `preflight-output-preexisted-no-process-created`; no CK3 or
  injector process was created and it contributes no live evidence.
- Canonical R0024 (legacy R893) is `completed-red`. The exact run report is
  `candidate-live-attempt-01/report.json`, SHA-256
  `2813E802D8FC39BB2E5161447A1D94C054BC28CA1648BE5AA57024BB6DAC0315`.
  Its failure is `formal native_auto_run did not reach a matching terminal
  intercept`. The verified underlying failure occurs in formal prelaunch:
  `candidate-state/profile/xar-autoplayer-environment.json` is absent, and a
  read-only `verify_profile` reproduces that missing-manifest error. The return
  is deterministically `session_exit` / `failed` / `attempted_turns=0`; this is
  not a planner or `candidate-turn-limit` outcome.
- `candidate-live-attempt-01/capture.json`, SHA-256
  `FF76C8E14DA90959303DEF32AB601C6DA44C4D737AA1484E342CD70DC3B7EB04`,
  is GREEN and contains exactly six source-bound executions for natural
  `bookmark.1071.a`, actor `29829`, and WarID `16777285`. The read-only observer
  restored its breakpoint byte and detached successfully.
- The safe recovery checkpoint is
  `candidate-state/profile/save games/xar_checkpoint.ck3`, history `1`, date
  `53173176`, SHA-256
  `2661E9F0717521BBE7F8B7D8554331CA56F1D850D7FE9186704D3B7125A8F8D9`.
  Its paired driver state is
  `candidate-state/native-session/driver-state.json`, SHA-256
  `BC0B9BD103C8265F67B1F6ECE77DE79CE85F5FCA23F310F4D034895C7B8B7ADD`.
- No matching terminal plan was intercepted, no terminal action was submitted,
  and `candidate-live-attempt-01/action-runner-input.json` was not emitted.
  R0024 is immutable and the action runner cannot be invoked directly; it is
  therefore not authorized yet.
- Cleanup is GREEN: driver closed, PID `106748` was reclaimed, and
  `remaining_ck3=[]`. The six-source capture is reusable evidence, but it is
  not a terminal result, postwar certificate, cold restore, or GEN-034-D
  completion.

## Consumed live command

The command below was the exact argv used for R0024. It is retained only for
provenance. Do **not** rerun it to create another natural source while the safe
R0024 capture/checkpoint pair remains valid.

```powershell
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" -B "Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-runtime-b9e3357d-20260921\ck3_autonomous_player\native_bridge\research\run_g2_source_specific_war_loss_live_adapter.py" --manifest "Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-candidate-b9e3357d-20260921\g2_source_specific_war_loss_live_adapter_v1_manifest.json" --preflight-output "Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-candidate-b9e3357d-20260921\candidate-live-run-preflight.json" --artifact-dir "Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-candidate-b9e3357d-20260921\candidate-live-attempt-01" --userdir "Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-candidate-b9e3357d-20260921\candidate-state\profile" --profile-settings-template "Z:\ck3_mod_rewrite_process_assets\g2-gen034-r707-masterf342-20260915\state\profile\pdx_settings.txt" --expected-profile-settings-sha256 592AB6C67BF24600FA3679509F63E0688DDF45A372FE709E71D7F35CD48F5244 --expected-shadercache-tree-sha256 43896A031A779E8816E6B4F9B2C402C748BABF4B98BF500730A55DFBCF0907CD --game-root "Z:\ck3_mod_rewrite\Crusader Kings III" --capture-executable "Z:\ck3_mod_rewrite_process_assets\zg361\g2-source-specific-war-loss-provider-r450-20260911\build-msvc\Release\xar_ck3_raiktor_war_bound_private_capture_v1.exe" --bridge-dll "Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-private-f342-20260915\build\Release\xar_ck3_bridge.dll" --bridge-injector "Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-private-f342-20260915\build\Release\xar_ck3_bridge_injector.exe" --expected-character-id 29829 --candidate-terminal-intercept --candidate-turn-limit 256 --candidate-timeout 1800.0 --authorize-private-live
```

The original command contract was:

1. One new natural Raiktor creation supplies exactly six source-bound capture
   records, and the bridge continues on the same CK3 PID.
2. Formal `native_auto_run` selects a matching white-peace or surrender terminal
   plan and stops before submitting it.
3. A game checkpoint and native driver state are frozen, and the report says
   `action_submitted: false`.
4. `candidate-live-attempt-01/action-runner-input.json` exists and contains the
   immutable source capture, checkpoint, driver state, identity, and the only
   valid action-runner argv.

R0024 satisfied item 1 and retained a safe checkpoint, but did not reach item 2;
items 3-4 were consequently not closed. Do not substitute a private terminal
action, enable the generic terms reader, overwrite `candidate-live-attempt-01`,
or retry a terminal action blindly.

## Next focused continuation

1. Keep R0024 and `candidate-live-attempt-01` immutable. Prepare a successor
   continuation profile from the frozen history-1 checkpoint and paired driver
   state through the supported formal profile-preparation flow; do not create
   `xar-autoplayer-environment.json` by hand.
2. Run the formal read-only `verify_profile` gate and require it to pass before
   starting CK3. Add only the focused normal/optimized regression for this
   prepare/verify boundary; do not broaden the runner or acceptance matrix.
3. After the prelaunch gate passes, re-run production `native_auto_run` in one
   managed CK3 process. Reuse the immutable six-source capture and confirm it is
   not generated a second time. The current `session_exit` / `failed` /
   `attempted_turns=0` result is pre-planner and must not be attributed to the
   planner or turn limit.
4. If and only if formal `native_auto_run` returns a matching terminal plan,
   freeze the pre-submit checkpoint and emit the action-runner input. Then use
   the existing action-runner continuation below. On another RED, preserve the
   new return artifact and reclaim the process without submitting a terminal
   action.

## Action-runner continuation

After the focused continuation succeeds, execute only the `runner_command` emitted in
`candidate-live-attempt-01/action-runner-input.json`. It is generated from the
actual WarID, character, date, checkpoint, driver state, and capture hashes, so
it cannot be written correctly before the live candidate exists.

The action runner must prove, in order: same-frame comparison of continue,
white peace and surrender; exactly one selected terminal action; independent
postwar state and persisted truce; a real process recycle and cold restore; one
independent production turn after restore; and no replay of the terminal action.
ACK alone is not sufficient.

## Compatibility impact

There is no public MCP schema, capability advertisement, wire protocol, or
open_kaishek interface change. The only shared Python seam is an optional
`before_submit` callback used by this candidate to checkpoint and intercept a
formal plan; default production behavior is unchanged. No open_kaishek adapter
update is required for this package.
