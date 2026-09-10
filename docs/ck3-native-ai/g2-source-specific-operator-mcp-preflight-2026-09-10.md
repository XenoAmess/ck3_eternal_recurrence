# G2 source-specific operator MCP no-launch profile

Status: **portable profile generator static-ready / no-launch only / G2 live not run**.

## What this closes

`prepare_g2_source_specific_operator_profile.py` turns the existing portable
path overrides in the G2 source-specific live adapter into one target-side
operator MCP deployment profile. The caller supplies the target identity,
endpoint, repository clone, Python, CK3 files, relocated runtime bundle,
profile settings and output directories. The checked-in generator contains no
operator name, machine name, deployment root or CK3 `R{n}`.

The generated profile exposes exactly one job:
`g2-source-specific-no-launch-preflight`. Its frozen command ends in
`--verify-only` and does not contain `--authorize-private-live`,
`--artifact-dir` or `--userdir`. The job has no stdin controls and no CK3
exclusive-process gate because it never starts, attaches to, focuses, injects
into, stops or controls CK3. It may therefore run while another owner retains
the CK3 slot; the adapter only records the unchanged process inventory.

Every file consumed by the command is recorded in `required_paths` with its
size and SHA-256: Python, live-adapter manifest, profile settings, all fourteen
manifest dependencies, the exact game files and the relocated capture/bridge
binaries. The settings sibling `shadercache` is required as a directory; its
full warm-cache inspection remains owned by the existing adapter preflight.
The preflight output must be absent, preserving the adapter's one-shot receipt
contract.

## Per-target generation

Run the generator from any clone. All deployment-specific values below belong
to that target machine and are intentionally not committed:

```powershell
$repo = (Resolve-Path '<repository-clone>').Path
$runtimeBundle = (Resolve-Path '<byte-identical-runtime-bundle>').Path
$deployment = '<external-operator-deployment-directory>'

& '<target-python>' -B `
  "$repo\ck3_autonomous_player\native_bridge\research\prepare_g2_source_specific_operator_profile.py" `
  --target-id '<portable-target-id>' `
  --display-name '<display-name>' `
  --token-user '<exact-target-token-user>' `
  --desktop '<exact-target-desktop>' `
  --machine '<exact-target-machine>' `
  --endpoint-port '<unused-target-port>' `
  --advertised-url '<client-reachable-MCP-URL>' `
  --state-directory "$deployment\state" `
  --repository-root "$repo" `
  --python-executable '<target-python>' `
  --preflight-output "$deployment\g2-no-launch-preflight.json" `
  --profile-settings-template '<known-good-profile>\pdx_settings.txt' `
  --game-executable '<CK3-install>\binaries\ck3.exe' `
  --bookmark-events '<CK3-install>\game\events\bookmark_events.txt' `
  --capture-executable "$runtimeBundle\xar_ck3_raiktor_war_bound_private_capture_v1.exe" `
  --bridge-dll "$runtimeBundle\xar_ck3_bridge.dll" `
  --bridge-injector "$runtimeBundle\xar_ck3_bridge_injector.exe" `
  --profile-output "$deployment\operator-profile.json"
```

The manifest path defaults to the manifest in that clone; `--manifest` may
select an equivalent location. Runtime overrides must still match the
manifest's frozen hashes. A machine with different bytes receives RED during
generation, before an operator server or job is started.

Start the generic target-side server with the generated profile, then use the
normal MCP order: capabilities → status → preflight → handoff. Handoff runs
only the frozen no-launch check. A GREEN adapter receipt can inform a later,
separately frozen exclusive live job; this profile itself cannot be edited or
controlled into a live invocation.

## Evidence and readiness boundary

Focused tests construct an unrelated temporary clone, target identity and
runtime bundle, then load the generated result with the production operator
profile parser. They assert exact hash rows, relocated path precedence,
absence of account/round constants, no live flags, no CK3 controls and
fail-closed hash drift/output reuse. The suite passes in normal and Python
`-O` modes.

A current-machine no-launch smoke generated
`Z:\ck3_mod_rewrite\_runtime\g2-portable-operator-preflight-7f21638-20260910\operator-profile.json`
with SHA-256
`5C0C7D980A37B351C94D93208CA6A243167D7BD471B103031B483EB7D16A5A8D`.
Executing that profile's frozen command directly produced
`preflight.json`, 13,157 bytes, SHA-256
`C4DE6B43A5D7AE549B0224B949382AA5A97BCDAE89B8F77D73F09AC926337158`.
The receipt reports `READY_TO_RUN_G2_SOURCE_SPECIFIC_LIFECYCLE`, all fourteen
manifest dependencies matched, process inventories were identical, and the
warm shadercache was ready with 4,976 files / 217,711,007 bytes / tree
`309AF6F1D0D18B204DB14DC9EBFACCBD3BAEACA138ED616D3F181C6FDFB15942`.
No operator server or CK3 action was needed for this smoke.

This is a deployment portability improvement only. It changes no native
bridge or MCP public schema/API/ABI, creates no live evidence and does not
promote source-specific loss, comparison, decision, action, automatic
surrender or `GEN-034` readiness. T1 therefore remains at **90%** until the
exclusive source-specific lifecycle is actually run. `open_kaishek` requires
no code change for this package.
