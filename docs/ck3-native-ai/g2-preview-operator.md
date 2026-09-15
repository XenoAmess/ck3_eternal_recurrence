# Standard-feudal preview operator contract

This is the bounded path for qualifying a normal production checkpoint and then checking one real strategy action. It does not change the native driver, public MCP schema, or formal planner. The read-only eligibility tool calls the existing exact-build public `query_campaign_root_context_v1` through the controlled application-main path; the gameplay run itself must use `agent.py native-auto-run` / `ck3_auto_turn` in the normal production strategy loop. A private query, process survival, ACK, or date movement alone cannot make the preview usable.

The frozen package carries an operator JSON manifest with **actual host paths and hashes**, including the CK3 EXE, clean agent source checkout, independent prepared production-only state, immutable source save, paired driver state, exact Release DLL and injector, configured named pipe, episode identity/date, one supported government and one expected natural semantic action. Paths are values in that package, never constants in the tools. Keep its source save unchanged; do not copy CK3 into the agent package. The supported combination is one CK3 `1.19.0.6` exact EXE SHA, `feudal_government`, one enabled production mod descriptor and a recorded `disabled_dlcs` list. Installed DLC descriptors are an inventory, not proof of loaded entitlement. Record the profile's actual `dlc_load.json` and settings before advertising a DLC combination.

The manifest used by these tools has this interface. Fields shown in angle brackets are filled with real values and verified in the frozen package before use; they are not launch commands to hand to a user:

```json
{
  "source_commit": "<40-character agent/native source commit>",
  "source_repo": "<clean candidate runtime checkout>",
  "python": "<validated Python executable>",
  "game_dir": "<CK3 install root>",
  "game_exe_sha256": "<exact ck3.exe SHA-256>",
  "state_dir": "<independent prepared state>",
  "source_save": "<immutable source xar_checkpoint.ck3>",
  "checkpoint_sha256": "<source and prepared save SHA-256>",
  "driver_state_sha256": "<paired driver-state SHA-256 at admission>",
  "episode_character_id": 0,
  "episode_run_id": "<checkpoint episode run ID>",
  "date_raw": 0,
  "pipe": "<paired Windows named pipe>",
  "dll": "<same-source Release xar_ck3_bridge.dll>",
  "dll_sha256": "<DLL SHA-256>",
  "injector": "<same-source Release xar_ck3_bridge_injector.exe>",
  "injector_sha256": "<injector SHA-256>",
  "environment_sha256": "<prepared profile environment SHA-256>",
  "production_tree_sha256": "<production mod projection SHA-256>",
  "formal_report": "<new evidence directory/formal-report.txt>",
  "supported_government": "feudal_government",
  "timeout_seconds": 390,
  "session_ceiling_seconds": 480,
  "readiness_timeout_seconds": 300,
  "formal_turns": 20,
  "preview_action": {
    "kind": "pending_reply",
    "definition_key": "pay_ransom_interaction",
    "step": "reject-pending-character-interaction",
    "result_status": "rejected",
    "rule_id": "ordinary-reject-unique-accept-v1"
  }
}
```

The expected action fields are **verification assertions**, never action arguments passed to the agent. The agent discovers the pending request and its signed full ID from a real paused frame and chooses the reply under its installed policy. If a checkpoint has an unconfirmed prior action, first query actual paused game state and its receipt; do not submit another reply blindly.

First take exclusive CK3 ownership and confirm all managed CK3 processes are dead. For an independent fresh state, run the formal `prepare-profile` and `verify-profile` commands from the pinned candidate runtime, copy the immutable paired save to `state/profile/save games/xar_checkpoint.ck3` and driver state to `state/native-session/driver-state.json`, and run the existing no-launch `native-one-generation-preflight` with the episode/save/driver pins from the manifest. `prepare-profile` itself refuses while CK3 is running. Keep the source/copy SHA mapping and preflight report; a structurally valid preflight is not live evidence.

The operator then runs the reusable scope check. This starts and recycles at most one CK3 process only when `--preflight-only` has passed and the global single-instance ledger assigns ownership. Each `--output` path is new and holds one attempt. The tool submits no input, date advance or gameplay action:

```powershell
$previewManifestPath = '<path to frozen operator manifest>'
$previewOutputDir = '<new evidence directory>'
& '<validated Python executable>' -B tools/g2_preview_eligibility.py --manifest $previewManifestPath --output $previewOutputDir
```

The exact frozen package replaces those three path values with validated paths. `GREEN_READ_ONLY` requires two managed same-version paused public campaign-root queries, the played episode/date, `government.key=feudal_government`, empty war/event/pending/army state, unchanged save and proven process cleanup. A null/unknown government, stale frame, timeout, surviving CK3 or nonempty mandatory pending state is not GREEN. The current bounded scene has 390 seconds for the stage, a 480-second underlying native-session ceiling (`390+90` grace), and 300 seconds for paused readiness. The owner's process ledger records the actual round; no tool assigns a round or assumes an expired lock means the old process died.

After eligibility is GREEN, confirm the prior process is dead, allocate a new actual round, and invoke the **formal production entry** directly with values from the frozen manifest:

```powershell
$preview = Get-Content -LiteralPath $previewManifestPath -Raw | ConvertFrom-Json
$agentEntry = Join-Path $preview.source_repo 'ck3_autonomous_player/agent.py'
& $preview.python -B $agentEntry --state-dir $preview.state_dir --game-dir $preview.game_dir --bridge-mode native-headless --bridge-pipe $preview.pipe --bridge-dll $preview.dll --bridge-injector $preview.injector native-auto-run --turns $preview.formal_turns --timeout $preview.timeout_seconds --readiness-timeout $preview.readiness_timeout_seconds --cold-start-checkpoint | Tee-Object -FilePath $preview.formal_report
$nativeAutoRunExitCode = $LASTEXITCODE
```

The CLI prints `Operator stop request file: <absolute path>` to stderr; record that line along with the complete JSON stdout and `$nativeAutoRunExitCode` in the independent attempt. `Tee-Object` preserves the complete stdout report; PowerShell 5.1 writes it as UTF-16, which `tools/verify_g2_preview_action.py` can read. The formal bounded run only passes the preview action slice when it makes a real nonempty policy decision from the exact natural request, submits one typed action, sees an independent later paused frame where the old full pending ID has disappeared, has a later successful strategy turn that does not repeat the action, saves a checkpoint **after** the action, and proves single-instance cleanup. `no_semantic_action`, timeout, RED and unexecuted are recorded separately. Existing historical same-seed behavior can guide scene selection but cannot substitute for this frozen combination's live result.

The evidence checker is read-only and extracts the signed pending ID from the new report; it never takes a CharacterID or request ID as an operator action parameter:

```powershell
& $preview.python -B tools/verify_g2_preview_action.py --manifest $previewManifestPath --eligibility-report '<eligibility report.json>' --formal-report '<complete native-auto-run JSON report>' --output '<new verification report.json>'
```

At a safe post-action checkpoint, preserve the game save, paired `native-session/driver-state.json`, agent episode/high-level objective state, pending-action/receipt mapping, binary/agent/profile versions, reports and SHA-256 values together. A read-only qualification run may update driver-state command history or last bridge PID while leaving the save unchanged; compare before/after and use the **current** driver-state SHA in the next exact preflight. Do not silently restore an older driver-state or claim that all artifacts remained one version if a later Python/native fix changes them.

To check controllable stop on Windows, keep the formal `native-auto-run` process active. In a **second** PowerShell process, derive the request path from the pinned manifest, confirm it equals the absolute path printed by this CLI, and request stop after a verified gameplay turn has reached a safe paused frame:

```powershell
$preview = Get-Content -LiteralPath $previewManifestPath -Raw | ConvertFrom-Json
$stopRequest = Join-Path $preview.state_dir 'native-auto-run.stop'
Set-Content -LiteralPath $stopRequest -Value stop
```

The tested d112 CLI watches this request and routes it to the existing operator-stop checkpoint boundary; it consumes and clears the file. A stale request already present at launch is rejected before CK3 starts. Confirm the formal report says `operator_stop_checkpointed` and `outcome=operator_stopped`, a compatible paired checkpoint was saved, `cleanup.ok=true`, and the CK3 process tree is dead. `operator_stop_checkpoint_deferred`, a surviving process or an unresolved action is a failed stop gate. Windows PowerShell Ctrl+C did not reliably reach Python's stop handler in the controlled console attempts; it is not the documented operator method.

Preserve the post-stop `state/profile/save games/xar_checkpoint.ck3` together with `state/native-session/driver-state.json` and their fresh SHA-256 values. After the old process is confirmed dead, the owner allocates a new actual round. With the same prepared state, derive the current paired hashes, run the existing **no-launch** preflight, then the formal cold restore; create an independent report directory for this attempt:

```powershell
$preview = Get-Content -LiteralPath $previewManifestPath -Raw | ConvertFrom-Json
$agentEntry = Join-Path $preview.source_repo 'ck3_autonomous_player/agent.py'
$checkpointPath = Join-Path $preview.state_dir 'profile/save games/xar_checkpoint.ck3'
$driverStatePath = Join-Path $preview.state_dir 'native-session/driver-state.json'
$preview.checkpoint_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $checkpointPath).Hash.ToLowerInvariant()
$preview.driver_state_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $driverStatePath).Hash.ToLowerInvariant()
$coldRestoreEvidenceDir = Join-Path (Split-Path -Parent $preview.state_dir) ('cold-restore-' + (Get-Date -Format 'yyyyMMddTHHmmss'))
New-Item -ItemType Directory -Path $coldRestoreEvidenceDir -ErrorAction Stop | Out-Null
$coldRestoreReport = Join-Path $coldRestoreEvidenceDir 'formal-report.txt'
& $preview.python -B $agentEntry --state-dir $preview.state_dir --game-dir $preview.game_dir --bridge-mode native-headless --bridge-pipe $preview.pipe --bridge-dll $preview.dll --bridge-injector $preview.injector native-one-generation-preflight --expected-character-id $preview.episode_character_id --expected-episode-run-id $preview.episode_run_id --expected-checkpoint-sha256 $preview.checkpoint_sha256 --expected-driver-state-sha256 $preview.driver_state_sha256
if ($LASTEXITCODE -ne 0) { throw 'cold-restore preflight blocked; CK3 was not launched' }
& $preview.python -B $agentEntry --state-dir $preview.state_dir --game-dir $preview.game_dir --bridge-mode native-headless --bridge-pipe $preview.pipe --bridge-dll $preview.dll --bridge-injector $preview.injector native-auto-run --turns 5 --timeout $preview.timeout_seconds --readiness-timeout $preview.readiness_timeout_seconds --cold-start-checkpoint | Tee-Object -FilePath $coldRestoreReport
$coldRestoreExitCode = $LASTEXITCODE
```

The preflight must return `ready/ok=true` before launching. Verify the old action's material result first, retain the same episode/high-level goal, continue visible gameplay without repeating the consumed full ID, and save another checkpoint. Same-process reload or mere Python deserialization does not meet cold restore.

The checker and operator path are reusable versioned assets for any authorized machine that can read the repository. Their use still depends on a legally installed, exact CK3 build and a host capable of running it; a read-only MCP query available on another machine does not certify that host can execute CK3. This tool set adds no native ABI, MCP schema or `open_kaishek` runtime protocol change. The frozen package must cite the actual live round/report and clearly limit supported gameplay; it is only ready for delivery after the semantic action, stop/checkpoint and new-round cold restore gates pass.
