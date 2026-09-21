# GEN-034-D candidate builder handoff (2026-09-21)

## Current boundary

This package is now **production-live first-turn / native observation RED**.
Canonical R0024 captured the six source executions from one new Raiktor
creation. R0025-R0027 then reused that immutable capture/checkpoint/driver pair
through a supported successor continuation instead of creating another natural
source. The profile-preparation and cold-start readiness blockers have been
closed: R0027 reached an exact paused map-ready frame in 95.026 seconds and
entered the first production `native_auto_run` turn.

The first campaign-root query exposed the current blocker. The native producer
returned county titles `2142` and `2173` with `capital_province_id=null` while
advertising `held_title_partition_ready=true`. The strict Python contract
correctly rejected that payload. R0027 therefore has one attempted turn, zero
successful turns, zero gameplay actions, no date advance, no matching terminal
intercept, and no action-runner input. GEN-034-D remains `3/4`, the authoritative
G2 count remains `1/8`, and R458 is not reused as final evidence. The next fix is
the exact-build native county-title capital resolver/readiness advertisement;
do not relax the validator, submit a terminal action, or launch another natural
source search.

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

## R0025-R0027 continuation result

The successor runner change is integrated through
`55429bfbc1c6409f3747ce9a8e257eff19642a1a`; runtime refreeze is
`d044e7523dc87ffa4613da2e9a72b2328abf31f8`. Its 481-file runtime manifest has
SHA-256 `EF05222DA1C124F27A9EDEAFE3C4A3A5A1012331D3125D529CBBAF78F4E8A492`
and tree SHA-256
`8DDCFEA7D07CA61C03181791CC27AF6B3E3C98FB984A1436F81B425A38132154`.
Focused continuation/runtime-manifest/live-adapter/native-auto-run tests passed
`132/132` under normal Python and `132/132` under `-O`. The exact no-launch
preflight is READY, SHA-256
`C8767DACA714C355AB63A5E2198BF155E87AB26AAD5D9CED7473178CDA8A0E7E`.

- R0025 (legacy R894) is `completed-red`. The old runner bound cold-start
  readiness to `bridge_attach_seconds=60`; at 61.572 seconds the bridge, build,
  and adapter were ready but the map/date were not. It attempted zero turns and
  reclaimed the process. Outer report SHA-256 is
  `AF60DDE3E7CB11062592DA3A83B1D7E101965664BA89541B7477E1146A87863F`;
  native report SHA-256 is
  `1D936E0ECD0D4C25C74D8AD1A48CE6DE0AB5EF50F4148B5C2AA18ECAEA8000ED`.
  This live result justified the new explicit `--readiness-timeout`, default
  `720s`.
- R0026 (legacy R895) is `completed-red` before CK3 creation. The operator used
  system `py -3.13`, so formal profile preparation correctly rejected the
  missing frozen distribution `nvidia-cublas`. Report SHA-256 is
  `88280B717F9A84FB28725CE2A2AE0B22F73F12390DFDC0A7E2CF254C70C27A50`.
  This was interpreter drift, not a dependency-contract defect. The required
  interpreter is `Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe`, SHA-256
  `D70FCED7F461F38F9F224D8673FB74E96E4FACB4283FF4E8697543B457FEA8A0`;
  do not weaken the distribution gate.
- R0027 (legacy R896) used that interpreter. Formal state preparation, rebind,
  cold-checkpoint validation, and runtime-closure checks passed. New CK3 PID
  `27616` reached map-ready at date `53173176`, actor `29829`, WarID `16777285`,
  with restored driver state and a ready mailbox. The first accepted
  `query-campaign-root-context-v1` payload then failed normalization with
  `held_title_partition[1].capital_province_id must be present only for a
  county`. Outer report SHA-256 is
  `FEFC9A11E2F750347F9A3CDBE159F1D6862FE4D13824B8788AC77E4554B98CCA`;
  native report SHA-256 is
  `74CA99461FB036921588F8552D237FAD1959ADF5AD7C190D1EAE72F5B3A36666`.
  Cleanup is GREEN and no action was submitted.

The raw R0027 payload is retained in
`g2-gen034-d-continuation-d044e752-r0027-20260921/candidate-continuation-attempt-01-formal-state/native-session/driver-state.json`.
Its held-title rows are duchy `2141 / tier_raw=3 / capital=null` (valid), county
`2142 / tier_raw=2 / capital=null` (invalid), and county
`2173 / tier_raw=2 / capital=null` (invalid), while
`held_title_partition_ready=true`. The ABI requires a non-null resolver result
for a county and requires the complete partition to become unavailable on
resolution failure. Fix the native producer; do not treat unknown as a legal
zero value.

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

1. Keep R0024 and `candidate-live-attempt-01` immutable. Freeze the exact bridge
   source/binary and inspect the county-title capital resolver using the R0027
   raw payload as the failing paused-frame fixture.
2. Make county rows publish the real capital province. If a resolver genuinely
   fails on a frame, mark the complete held-title partition unavailable rather
   than pairing a null county capital with `held_title_partition_ready=true`.
   Keep the strict Python validator and close the observation with an exact
   paused snapshot, not only a serialized fixture.
3. Run only the affected native Release and normal/optimized Python tests,
   rebase/push, refreeze the runtime closure, and create a new clean runtime
   worktree and no-launch preflight.
4. Confirm process-zero, allocate R0028 or a higher actually unused round, use
   the frozen absolute venv interpreter, and create fresh attempt/formal-state
   directories from the immutable R0024 pair. Do not overwrite or resume the
   R0027 writable state.
5. If and only if production `native_auto_run` returns a matching terminal plan,
   freeze the pre-submit checkpoint and use the emitted action-runner command.
   On another RED, preserve it and reclaim the process without submitting a
   terminal action.

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

The readiness-timeout change has no public MCP schema, capability advertisement,
wire protocol, or open_kaishek interface impact. R0027 is an existing
exact-build native campaign-root producer defect. If its resolver fix changes
field availability, manifest identity, or the binary, update the versioned
MCP/ABI asset and compatibility note together; do not hide the malformed value
in an adapter. No open_kaishek adapter update is required yet.
