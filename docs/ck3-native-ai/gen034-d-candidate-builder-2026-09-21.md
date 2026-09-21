# GEN-034-D candidate builder handoff (2026-09-21)

## Current boundary

This package is **static-ready; live not executed**. It prepares the one allowed
new Raiktor creation-time run for GEN-034-D, captures the six source executions,
hands the same process to the production `native_auto_run` loop, and intercepts
the first matching terminal plan before submission. It does not close GEN-034-D,
does not change the authoritative G2 count, and does not reuse R458 as final
evidence.

R884 had been reclaimed and process inventory contained no CK3, bridge injector,
or native-agent process before this package was prepared. No CK3 process was
started while building or verifying it.

Final candidate tip: `0cb0887caed55c04429105c2768c9ea01ca2d04e`.
The previously reviewed `fe64549f3e89488d905a280895cfefa5271e2a17`
candidate was rebased without conflicts onto
`origin/master@d559faa6d7094cc953f238ef03e9e491cd7e7027`; the final commit only
refreezes the 479-file runtime closure after the R888 strategy/native-driver
changes.

## Frozen runtime and candidate

- Durable runtime archive:
  `Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-runtime-0cb0887c-20260921`
  (ZIP SHA-256
  `E0E278C098EBC52DC5951CC7872C1251C5B5AD0B0EA46CB96D5B1A529B61D0F3`)
- Candidate bundle:
  `Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-candidate-0cb0887c-20260921`
- Bundle manifest: `gen034-d-candidate-bundle.json`, SHA-256
  `978026AD6BCE6DF32DABCECB629081DA306795D32DC31B55BE726CA173A5BE50`
- Outer-owner manifest SHA-256:
  `4F2ECBA2969D7C82106E0DEB1D539D91956CF2B0B353087B0D15AC1907EE9C88`
- Lifecycle manifest SHA-256:
  `50C06D7C1C0753B9E31D322F4C5EAAE70CC65DA5B280FDA3081AE4E711EAE882`
- Live-adapter manifest SHA-256:
  `A82837C0EA015911618209F7F21E0BA02A6CD3B02AF4A5576F7D4971889C3F10`

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
  `5CE8E7505BBF2EFB82AA053A7EDF5D97EE6BF808501A9DA443088A6D924735A8`.
- Focused normal suite: `397 passed`.
- Focused optimized suite: `397 passed` (the normal pytest warning about
  assertions outside tests being disabled under `-O` is the only warning).
- Python compilation and `git diff --check`: passed.

No non-hash functional failure remains in the builder or runner tests. Live
evidence is deliberately still absent.

## The one next live command

First acquire the single CK3 slot and perform a fresh process-zero check. Then
execute the `candidate_command` array in `gen034-d-candidate-bundle.json`
argv-for-argv. Its current rendered command is:

```powershell
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" -B "Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-runtime-0cb0887c-20260921\ck3_autonomous_player\native_bridge\research\run_g2_source_specific_war_loss_live_adapter.py" --manifest "Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-candidate-0cb0887c-20260921\g2_source_specific_war_loss_live_adapter_v1_manifest.json" --preflight-output "Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-candidate-0cb0887c-20260921\candidate-live-run-preflight.json" --artifact-dir "Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-candidate-0cb0887c-20260921\candidate-live-attempt-01" --userdir "Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-candidate-0cb0887c-20260921\candidate-state\profile" --profile-settings-template "Z:\ck3_mod_rewrite_process_assets\g2-gen034-r707-masterf342-20260915\state\profile\pdx_settings.txt" --expected-profile-settings-sha256 592AB6C67BF24600FA3679509F63E0688DDF45A372FE709E71D7F35CD48F5244 --expected-shadercache-tree-sha256 43896A031A779E8816E6B4F9B2C402C748BABF4B98BF500730A55DFBCF0907CD --game-root "Z:\ck3_mod_rewrite\Crusader Kings III" --capture-executable "Z:\ck3_mod_rewrite_process_assets\zg361\g2-source-specific-war-loss-provider-r450-20260911\build-msvc\Release\xar_ck3_raiktor_war_bound_private_capture_v1.exe" --bridge-dll "Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-private-f342-20260915\build\Release\xar_ck3_bridge.dll" --bridge-injector "Z:\ck3_mod_rewrite_process_assets\g2-gen034-d-private-f342-20260915\build\Release\xar_ck3_bridge_injector.exe" --expected-character-id 29829 --candidate-terminal-intercept --candidate-turn-limit 256 --candidate-timeout 1800.0 --authorize-private-live
```

This command must finish with all of these assertions:

1. One new natural Raiktor creation supplies exactly six source-bound capture
   records, and the bridge continues on the same CK3 PID.
2. Formal `native_auto_run` selects a matching white-peace or surrender terminal
   plan and stops before submitting it.
3. A game checkpoint and native driver state are frozen, and the report says
   `action_submitted: false`.
4. `candidate-live-attempt-01/action-runner-input.json` exists and contains the
   immutable source capture, checkpoint, driver state, identity, and the only
   valid action-runner argv.

Do not substitute a private terminal action and do not enable the generic terms
reader. On RED, retain `candidate-live-attempt-01` and do not retry the terminal
action blindly.

## Action-runner continuation

After the candidate succeeds, execute only the `runner_command` emitted in
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
