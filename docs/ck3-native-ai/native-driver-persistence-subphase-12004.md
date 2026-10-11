# Full Driver persistence timing: actual R94 cost and subphase observation

R94 SDK79 actually recorded33.245702s for hello-restoration persistence and
34.3137648s for normal532 persistence, with fullDriver3,045,926,449B. The existing
aggregate timer starts before the write/state locks. It includes lock waiting,
compact JSON serialization plus LF, UTF8 encoding and synchronous atomic write.
The33s observation alone does not identify which stage dominates.

The production encoder already directly references complete history, without
cloning it, and uses compact separators with no pretty-print/sort. No compacting,
history trimming, async write, new storage schema or dependency was introduced.
The single native_driver.py change adds optional scalar timing rows through the
existing XAR_CK3_ARMY_TIMING_JSONL logger: write-lock wait, state-lock wait, JSON+LF,
UTF8 and the original atomic-write wrapper. Complete fields/history, lock scopes,
dirty state, early return, error handling and original aggregate row remain.
The disabled profile path retains the encoder's original no-argument call.

Child rows share the original timer's monotonic value as a diagnostic step;
native_request_id stays None. The unchanged aggregate row has no child token,
so the children can be grouped but are not claimed to sum exactly to the total.
Small logging overhead also remains inside that aggregate. A session with no
bridge PID can naturally produce only the two lock rows and the original total.

Root adopted the exact candidate and Python compilation succeeded. Qualification
is static-ready; no new functional test was needed for optional logging, and no
real stage measurements or runtime speedup are claimed. CurrentR95 SDK/Native
source452 is untouched. The diagnostics will enter a later already-needed SDK
source switch; that actual trace must precede any performance fix.

Source package: D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-32/persist-serialization-source80/DELIVERY.json.
Base Git source452b4e315314633f304208214fca169781c8b485; file content SHA256
2daba0de546670601f7a33eab859dd1db50936f1956aa8e84e1abed4e48b2938.
Adopted content SHA256 e9c2bd08f44266c58dde7bcbe12bc4f4bf297cb8ca31d5029fd02386d407ff41.
