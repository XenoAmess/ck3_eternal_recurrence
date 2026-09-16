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

```text
python tools/g2_preview_eligibility.py --manifest <frozen-operator-manifest.json> --output <new-evidence-directory>
```

The exact frozen package replaces those three path values with validated paths. `GREEN_READ_ONLY` requires two managed same-version paused public campaign-root queries, the played episode/date, `government.key=feudal_government`, empty war/event/pending/army state, unchanged save and proven process cleanup. A null/unknown government, stale frame, timeout, surviving CK3 or nonempty mandatory pending state is not GREEN. The current bounded scene has 390 seconds for the stage, a 480-second underlying native-session ceiling (`390+90` grace), and 300 seconds for paused readiness. The owner's process ledger records the actual round; no tool assigns a round or assumes an expired lock means the old process died.

After eligibility is GREEN, confirm the prior process is dead, allocate a new actual round, and invoke the **formal production entry** directly with values from the frozen manifest:

```text
python tools/g2_preview_operator.py run --manifest <frozen-operator-manifest.json> --output <new-formal-attempt-directory>
```

For the bounded M3 blocker diagnosis only, the same formal operator also has a
private, default-off single-query entry.  `R776A` is the evidence-slice label;
the value passed to `--private-timeline-query-round-id` is the actual monotonic
single-instance owner round and therefore remains `R<number>` (for that slice,
`R776`).  The manifest must pin the source commit containing this entry and its
same-source Release DLL/injector:

```text
python tools/g2_preview_operator.py query-current-timeline-blocker-context-v1 --manifest <frozen-R776A-operator-manifest.json> --output <new-R776A-read-only-attempt-directory> --private-timeline-query-round-id R776 --timeout 390 --readiness-timeout 300
```

This mode runs the existing no-launch one-generation preflight, then enters the
production `agent.py native-query-current-timeline-blocker-context-v1` path.
It owns one cold-start `native_session`, waits for one exact paused map-ready
frame, calls `query-current-timeline-blocker-context-v1` exactly once, and
recycles the process.  `GREEN_READ_ONLY` requires the query envelope to retain
`private_build=true`, `read_only=true`, and `advertised=false`; the save hash,
paused frame, date and query-before/query-after command history must be
identical.  The cold start may change the driver-state hash, but its history
delta must be exactly one successful `native-session-cold-start`
`restore-checkpoint` row bound to the pinned checkpoint, and the persisted
post-run history must equal the query-after history.  Managed process cleanup
must be proven.  The receipt records the source commit,
agent/operator hashes, actual round, query envelope and cleanup.  This entry has
no planner, Close, marriage, `death-terminal`, Python successor continuation,
date advance, checkpoint write, UI input or gameplay action path.  It remains
private and cannot advertise the capability.

The Python operator prints `Operator stop request file: <absolute path>` before launch and preserves complete UTF-8 stdout, stderr, preflight output, exit codes and a JSON receipt in the new attempt directory. The formal bounded run only passes the preview action slice when it makes a real nonempty policy decision from the exact natural request, submits one typed action, sees an independent later paused frame where the old full pending ID has disappeared, has a later successful strategy turn that does not repeat the action, saves a checkpoint **after** the action, and proves single-instance cleanup. `no_semantic_action`, timeout, RED and unexecuted are recorded separately. Existing historical same-seed behavior can guide scene selection but cannot substitute for this frozen combination's live result.

The evidence checker is read-only and extracts the signed pending ID from the new report; it never takes a CharacterID or request ID as an operator action parameter:

```text
python tools/verify_g2_preview_action.py --manifest <frozen-operator-manifest.json> --eligibility-report <eligibility-report.json> --formal-report <complete-native-auto-run-report.txt> --output <new-verification-report.json>
```

At a safe post-action checkpoint, preserve the game save, paired `native-session/driver-state.json`, agent episode/high-level objective state, pending-action/receipt mapping, binary/agent/profile versions, reports and SHA-256 values together. A read-only qualification run may update driver-state command history or last bridge PID while leaving the save unchanged; compare before/after and use the **current** driver-state SHA in the next exact preflight. Do not silently restore an older driver-state or claim that all artifacts remained one version if a later Python/native fix changes them.

To check controllable stop on Windows, keep the formal `native-auto-run` process active. In a **second Python process**, derive the request path from the pinned manifest, confirm it equals the absolute path printed by this CLI, and request stop after a verified gameplay turn has reached a safe paused frame:

```text
python tools/g2_preview_operator.py request-stop --manifest <frozen-operator-manifest.json>
```

The tested d112 CLI watches this request and routes it to the existing operator-stop checkpoint boundary; it consumes and clears the file. A stale request already present at launch is rejected before CK3 starts. Confirm the formal report says `operator_stop_checkpointed` and `outcome=operator_stopped`, a compatible paired checkpoint was saved, `cleanup.ok=true`, and the CK3 process tree is dead. `operator_stop_checkpoint_deferred`, a surviving process or an unresolved action is a failed stop gate. Console interrupt did not reliably reach Python's stop handler in the controlled attempts; it is not the documented operator method.

Preserve the post-stop `state/profile/save games/xar_checkpoint.ck3` together with `state/native-session/driver-state.json` and their fresh SHA-256 values. After the old process is confirmed dead, the owner allocates a new actual round. With the same prepared state, derive the current paired hashes, run the existing **no-launch** preflight, then the formal cold restore; create an independent report directory for this attempt:

```text
python tools/g2_preview_operator.py run --manifest <frozen-operator-manifest.json> --output <new-cold-restore-attempt-directory> --turns 5
```

The preflight must return `ready/ok=true` before launching. Verify the old action's material result first, retain the same episode/high-level goal, continue visible gameplay without repeating the consumed full ID, and save another checkpoint. Same-process reload or mere Python deserialization does not meet cold restore.

The checker and operator path are reusable versioned assets for any authorized machine that can read the repository. Their use still depends on a legally installed, exact CK3 build and a host capable of running it; a read-only MCP query available on another machine does not certify that host can execute CK3. This tool set adds no native ABI, MCP schema or `open_kaishek` runtime protocol change. The frozen package must cite the actual live round/report and clearly limit supported gameplay; it is only ready for delivery after the semantic action, stop/checkpoint and new-round cold restore gates pass.
