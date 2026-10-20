# Implemented public R06 configuration

The four authorized files are implemented in the shared tree; no commit or runtime action was performed by this lane. `IMPLEMENTED-CASE-INPUTS.template.json` is a binding template, not an admitted case: replace every null runtime/source pin before public prepare/review/run. Keep the normal R10 readiness fields and normal checkpoint/configuration pins from this template. The new optional key is `r06_refill_one_day`; it is mutually exclusive with `r04_county_entry`.

The `producer` object requires exactly: `qualification`, `build_result`, `SYSTEM_receipt`, `cold_result` as exact path/bytes/SHA references; `source_dir`, `observer_exe`, `observer_exe_sha256`, `native_build_source_head`, `native_tree`, `carrier_module_path`, `carrier_source_epoch`, and the five `cmake_defines` in the template. The actual Q must bind the build, observer, both passing V5 cold cases, and compile flags. Its native tree must equal current HEAD's native tree. The actual shared runtime manifest's `qualification.actual_producer` must equal this Q pin, `qualification.native_tree` must agree, and Selection's actual DLL path must equal `carrier_module_path`. The actor does not replace this with a boolean.

After the original six readiness requests, the same supplied CaseClient enters R06, verifies actual save/CLI restore and stationary source, queries full same-frame month/q inputs, then writes `case-output/r06-before-observer-awaiting.json`. It includes current machine/run/PID/exact process FILETIME/date, source producer pins and a small conditional target summary. At this point no observer is launched and no day has advanced.

Root performs the three OS thread metadata samples plus fourth immediate sample with the same actual PID/FILETIME; it explicitly chooses N<=256 plus a positive birth reserve. Existing `worker_next.py.os_threads` can be reused as an isolated query-only function if its input source is pinned; do not invoke that old script's hardcoded main/admit/run routes. No SDK is needed for census.

Write a new source-admission file, then write `r06-before-observer-started.json` at the actor's exact signal path. Both must be newly created, never reused. Source admission shape:

```json
{
  "schema": "xar.r06.public_worker_source_admission.v1",
  "machine_id": "<awaiting.machine_id>",
  "run_id": "<awaiting.run_id>",
  "bridge_pid": 123,
  "process_creation_filetime": 123456789,
  "date_raw": 53149056,
  "observed_at_utc": "<fresh UTC; within 300 seconds>",
  "native_tree": "<actual frozen native tree>",
  "native_qualification": {"path":"<Q>","bytes":1,"sha256":"<actual>"},
  "maximum_owned_threads": 256,
  "birth_reserve_generations": 1,
  "thread_census": {"path":"<three-sample census>","bytes":1,"sha256":"<actual>"},
  "latest_thread_snapshot": {"complete":true,"unresolved":[],"os_list_count":1,"generations":[[1,123456]]},
  "actual_module": {
    "pid":123,"process_created_filetime":123456789,
    "complete_module_metadata_enumeration":true,
    "module":{"path":"<actual loaded qualified xar_ck3_bridge.dll>","base":"<observed>"}
  }
}
```

The referenced census must contain machine_id/run_id/pid/process_creation_FILETIME and exactly three complete `snapshots`; each snapshot, including the fourth, has observed_at_utc (within 300 seconds), complete=true, unresolved=[], os_list_count in1..256, and `generations:[[TID,creationFILETIME],...]`. No duplicate numeric TID within one snapshot. The union across all four snapshots plus positive reserve must fit N. These are budget observations, not debugger ownership proof. Do not copy the illustrative N/reserve/rows as observations.

Owner signal shape (identity numbers copied from the new awaiting marker):

```json
{
  "machine_id":"<actual>","run_id":"<actual>","bridge_pid":123,
  "process_creation_filetime":123456789,"date_raw":53149056,
  "source_admission":{"path":"<new admission>","bytes":1,"sha256":"<actual>"}
}
```

After validating admission, the actor enables only regular_core for the exact CArmy, obtains its final complete full packet, rechecks the selected positive target and prepares the existing producer argv. It then writes standard `before-action-camera-awaiting.json` with action_kind=exact-day, machine/run/PID/date, signal_path=`before-action-camera-started.json`, and terminal_result_path=`R06-REFILL-TERMINAL.json`. Use existing canonical `window_take.py` map-context Start unchanged; its real signal and pinned Start/process-ready receipts release the actor. No Root-created camera API or army UI operation is required. Only a fresh paused snapshot remains before the unique observer launch; all full preparation precedes worker30s.

The exact terminal is `case-output/R06-REFILL-TERMINAL.json`. Bind this as the canonical observer_result; film holds min30s and finishes normally after terminal. The full result is `R06-WORKER-RESULT.json`. It always says full_R06_qualified=false; target instruction ADD is only set after strict original raw/full-parent consumption. Shared entry retains normal game closure. Unknown launch/Arm/Resume/Save is never retried, and unknown or failed observer restoration withholds Save.

At the actual Probe.start boundary, before the once-claim and Popen, the actor reopens the exact pinned source admission and repeats its300-second freshness checks. It also rereads actual Q/build/SYSTEM/cold receipts and hashes the exact observer executable, matching the Q/SYSTEM-bound SHA. A camera wait does not extend census TTL. Changed same-path bytes or expired admission stop with zero claim/Popen/day. `R06-WORKER-PRELAUNCH-VERIFIED.json` records the successful final hash and admission when launch actually proceeds.

Verification performed: focused tests18 PASS, including both independent-review rejection variants; one existing R04 readiness-route regression PASS; diff whitespace PASS. This is source validation, no actual a40/READY/ADD/game qualification. The prior `UNIMPLEMENTED` plan file is historical and superseded for public dispatch by these implemented files.
