# H2743 profile CLI cleanup and live launch fence contract

H2743 current-HEAD v5 still rejects `--prepare-live-profile` and `--run`
at `require_live_bus_migration()` before any profile or game launch. The
profile CLI cleanup change in this branch applies to the existing legacy
`--prepare-no-launch` path and does not enable a v5 live path. It does not
reinterpret the frozen attempt 17 static seal or the isolated CAS protocol
from Draft #732.

## Current code-level repair

`call_profile_cli()` runs each profile command through one direct `Popen`
handle. It applies the v5 live hard-stop as its first executable statement,
including when imported and called directly. If waiting or screen renewal
raises, it writes a new per-command
`*-unsafe-cleanup.json` before trying to terminate the child. Its `finally`
path waits for that direct child and uses `kill()` plus another wait when
terminate/wait fails. It then writes a separate `*-cleanup-result.json`.
Both receipts state `process_tree_cleanup_proven: false`, and the unsafe
marker remains even if the direct child is reaped. A failed or absent marker
or unreaped child is a manual-recovery STOP. This is a local leak repair,
not authority screen release evidence.

## Boundaries found in the current implementation

| Boundary | Current evidence | Missing production proof |
| --- | --- | --- |
| Profile CLI | H2743 runner `call_profile_cli()` now holds the direct Python child handle and records a RED marker before cleanup. | Descendant identity and Job containment; direct `Popen.wait()` alone does not prove the tree is gone. |
| Native-session supervisor | H2743 runner `run()` holds a direct Python `Popen` PID and return code. | The supervisor's exact process creation identity and all children bound to the same screen claim; `cleanup-red.manual_recovery_required` currently checks only `process.poll()`. |
| CK3 child | `native_session.py` calls `runtime.stop_tracked()`, whose result includes exact CK3 PID and creation date, Job active-process count, watchdog state and final CK3 inventory. | The H2743 runner does not parse and bind that final result to its own supervisor and CAS claim. Its independent name-only `ck3.exe` scan is insufficient. |
| Screen CAS | Draft #732 validates fresh claim, expected-sequence heartbeat/release and locked bus readback in an isolated bus. | A shared claim-to-launch fence, serialized renewals and cleanup receipt SHA binding. `release(cleanup_proven=True)` is fixture-only. |

## Required shared helper before live cutover

R0368 or an equivalent shared launch helper must provide a reviewed,
callable contract that:

1. Accepts an exact claim token containing canonical bus path, pinned
   source/installed CLI SHA, task ID, claim event sequence and current
   expected sequence. It verifies ownership under the same bus lock or
   equivalent authority fence immediately across child creation. A separate
   readback followed by unrestricted `Popen` is insufficient.
2. Starts the profile CLI and native-session supervisor under an audited
   containment primitive. Its start receipt records immutable process PID,
   creation identity, image path/hash, parent identity, command SHA and
   claim-token SHA. CK3's nested Job/watchdog model must be compatible;
   failure to establish containment stops before resume.
3. On lease failure, timeout, read failure or normal exit, stops and reaps
   every process attributable to the claim. Its cleanup receipt binds all
   start identities, native-session `shutdown` proof, Job empty state,
   watchdog absent state and final CK3 inventory, then records exact bytes
   and SHA-256. Unknown or escaped descendants keep the unsafe marker and
   block release.
4. Serializes CAS heartbeat/release across main thread and watchdog. A
   failed/ambiguous heartbeat stops new work and keeps the screen claim
   until process cleanup and an independently reviewed release decision.
5. Makes all screen-capable callers honor the same fence. The installed
   authority CLI and historical XQOL stale owner must be resolved through
   their separate audited cutovers before any H2743 authority claim.

The H2743 runner can consume that contract only after the helper and bus
cutover are independently reviewed and their exact source/installed bytes
are pinned. Until then, v5 production remains `LIVE_STOP_CAS_MIGRATION_PENDING`.
The current R0368 `windows_injector_job.py` protects one injector process
with `ActiveProcessLimit=1`; it does not implement this shared profile CLI,
native-session supervisor and CK3 claim-to-launch fence.

## Code-only verification

The append-only report is
`D:/ck3-research-artifacts/h2743-runner-cas-cutover-stop-20260930/attempt-02/result.json`
(SHA-256 `482CC952B827DBDB055E59063C076E7F12B8EA22B5448EC362C500726B46FC35`).
Normal and `-O` each pass 7/7 fake-process cleanup tests and 11/11 existing
v5 runner tests. No profile CLI, CK3, Steam or authoritative task-bus
operation ran in these tests. The exact current runner's `--check-static`
normal and `-O` results are frozen separately at
`D:/ck3-research-artifacts/h2743-runner-cas-cutover-stop-20260930/attempt-03/result.json`
(SHA-256 `82566F753969F642DB7AFA4DE03631B96A62E8AE7603F1CC8844480BE41A0C1F`),
both exit 0. Those probes do not admit live work.
