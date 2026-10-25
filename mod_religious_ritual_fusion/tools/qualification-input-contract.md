# Source qualification input contract

`source-qualifications --inputs REQUEST.json --output NEW_EXTERNAL_DIRECTORY` binds a clean checkout to retained execution evidence. It does not execute tests, compile native code, prepare a runtime, or authorize a game. The output directory must not exist and must be outside the repository. Freeze the complete source delta with the existing shared producer after the final clean commit and a fresh scene admission; a software verification admission is insufficient for that freeze.

The request is schema version 1. Unknown fields, null mandatory values, duplicate JSON keys, coercion of booleans/floats/strings to integers, and numeric enum values are rejected. Every pin has exactly `{ "path": "ABSOLUTE_FILE", "bytes": 123, "sha256": "64_lowercase_hex" }`. Paths refer to existing immutable originals, not copied receipts with rewritten identities. The following is a structural example, not executable evidence; replace every placeholder and compute every pin from its real file.

```json
{
  "schemaVersion": 1,
  "machineId": "4-8e1c2f1861",
  "repository": "C:/workspace/ck3_eternal_recurrence",
  "sourceCommit": "FINAL_40_LOWERCASE_HEX",
  "sourceDelta": { "path": "ABSOLUTE_FRESH_DELTA", "bytes": 1, "sha256": "ACTUAL_64_HEX" },
  "classifierProgram": { "path": "C:/workspace/ck3_eternal_recurrence/tools/ck3_mod_acceptance_build_runtime.py", "bytes": 1, "sha256": "ACTUAL_64_HEX" },
  "previousHostDelta": { "path": "ABSOLUTE_RETAINED_HOST_DELTA", "bytes": 1, "sha256": "ACTUAL_64_HEX" },
  "chains": [
    { "chain": "PUBLIC_CONTROL", "previousQualification": { "path": "ABSOLUTE_PRIOR_PUBLIC_Q", "bytes": 1, "sha256": "ACTUAL_64_HEX" }, "proofs": [] },
    { "chain": "CASE_HOOKS", "previousQualification": { "path": "ABSOLUTE_PRIOR_CASE_Q", "bytes": 1, "sha256": "ACTUAL_64_HEX" }, "proofs": [] },
    { "chain": "SHARED_HOST", "previousQualification": { "path": "ABSOLUTE_PRIOR_HOST_Q", "bytes": 1, "sha256": "ACTUAL_64_HEX" }, "proofs": [] },
    { "chain": "SHARED_SDK_DELTA", "previousQualification": { "path": "ABSOLUTE_PRIOR_SDK_Q", "bytes": 1, "sha256": "ACTUAL_64_HEX" }, "proofs": [] },
    { "chain": "PILGRIMAGE_WIRE_SEAM", "previousQualification": { "path": "ABSOLUTE_PRIOR_SEAM_Q", "bytes": 1, "sha256": "ACTUAL_64_HEX" }, "proofs": [] },
    { "chain": "OTHER_SOURCE_DELTA", "previousQualification": { "path": "ABSOLUTE_PRIOR_OTHER_Q", "bytes": 1, "sha256": "ACTUAL_64_HEX" }, "proofs": [
      { "kind": "COMMAND_SOURCE_EXECUTION", "receipt": { "path": "ABSOLUTE_FRESH_EXECUTION_RECEIPT", "bytes": 1, "sha256": "ACTUAL_64_HEX" } }
    ] }
  ]
}
```

Exactly six unique chain plans are required. Supply a proof to each chain whose required files it covers. Proof kinds are `COMMAND_VALIDATION` (retained legacy execution format), `COMMAND_SOURCE_EXECUTION` (fresh explicit execution format below), `MAVEN_REVIEW` (the existing typed review report with actual successful Maven log/count), and `SOURCE_REVIEW` (explicit unselected source-only review). A source-only review can cover only `other_source_delta` or `case_hooks` files, supplies no execution credit, and retains its previous knowledge proof. It cannot qualify selected control, SDK, or host code.

For each required file, the producer checks either byte equality with its pinned predecessor or an explicit per-file source proof. Every dependency listed by an execution proof must also have a current matching proof. A Maven receipt does not cover unlisted files. The full delta is checked against the pinned base runtime/source index and actual Git diff. Unsupported additional chains and deletions produce a GAP. A GAP emits only `RESULT.actual.json` and no partial qualification set.

Fresh execution receipt fields:

```json
{
  "schema": "ck3-command-source-execution-v1",
  "machine_id": "4-8e1c2f1861",
  "source_commit": "ACTUAL_EXECUTION_BASE_40_HEX",
  "source_identity": "SCOPED_WORKING_TREE",
  "started_at_utc": "ACTUAL_OFFSET_AWARE_START",
  "observed_at_utc": "ACTUAL_OFFSET_AWARE_FINISH",
  "result": "PASS",
  "exit_code": 0,
  "skipped": 0,
  "commands_run": 1,
  "source_unchanged_during_execution": true,
  "source_pins": [ { "path": "ABSOLUTE_SOURCE", "bytes": 1, "sha256": "ACTUAL_64_HEX" } ],
  "source_pins_after": [ { "path": "ABSOLUTE_SOURCE", "bytes": 1, "sha256": "ACTUAL_64_HEX" } ],
  "command_results": [ { "path": "ABSOLUTE_ORIGINAL_COMMAND_RESULT", "bytes": 1, "sha256": "ACTUAL_64_HEX" } ]
}
```

`source_identity` is exactly `CLEAN_COMMIT` or `SCOPED_WORKING_TREE`; preserve the actual execution commit/dirty scope rather than relabeling it to a later clean commit. Observe source signatures before starting commands and again after their original waits. Optional `input_pins` and `input_pins_after`, when used for external inputs/artifacts, must both exist, remain identical in order and values, and resolve to actual unchanged files. They do not provide repository source coverage.

Each original command result requires `machine_id`, `result: "PASS"`, `original_wait_returncode: 0`, `skipped: 0`, nonempty textual `argv`, absolute repository `cwd`, positive integer `pid`, string `process_create_time_seconds` observed from that process, offset-aware `started_at_utc`/`finished_at_utc`, and `log` as an actual file pin. Optional `exit_code` must be exact integer zero. Record the original wait, timeout/termination disposition and other operator metadata honestly; failed or timed-out commands cannot become PASS receipts. Process birth uses decimal seconds as a string, not a FILETIME claim. Preserve native FileID/FILETIME separately as decimal strings when present. The producer does not launch an execution runner.

Successful output contains six `QUALIFICATION.<wire_chain>.actual.json` files, `NATIVE-SHARED-HOST-DELTA.actual.json`, and `RESULT.actual.json`. Historical finite test counters remain explicitly attributed to their original immutable qualification; new proofs retain their own execution identities. Producer status `SOURCE_BOUND_NOT_LIVE` is not live qualification. Retained compiled inputs and independently reviewed host change are checked; the existing native-source-binding producer and the real shared runtime consumers must then validate the resulting receipts. No native rebuild is claimed.

Regression scope: six JUnit methods, including actual producer to all six unchanged shared `qualify` consumers, classifier parity, wrong types/roundtrip, missing coverage, original wait validation, fresh pre/post source proof, and successful Maven log/count binding. Two methods invoke the existing Python modules using `-B -X utf8`; no new Python production module is created. Set `-Drrf.python=C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe` to select the existing qualified interpreter. Otherwise the tests use the repository venv if present, then `python`. These imports need the existing shared modules and standard library; no new dependency installation is requested. Maven is run only by the coordinating operator after all source owners close writes.
