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


## First actual SDK81 timing window

R96 actual source749809a7 cold13 was GREEN at01:30:53.931010Z. The
[sole small-log read](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-32/persist-phase-parser-sdk81/actual-r0096-first-read01/RESULT.json) at01:30:25.090745Z--01:30:25.179784Z
saw two child rows: writer wait7200ns and state wait4400ns, token907903738220800,
source lines1/2. The serialization, UTF8, atomic wrapper and aggregate rows were
not yet present at that time. This is partial actual observation, not zero values,
a completed persistence measurement or speedup. No Driver body was read or
hashed, and no additional Game query was needed. The original ordinary path
continues with the full Driver and synchronous persistence.


## Completed R96 samples

[The sole completed-stage read](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-32/persist-phase-parser-sdk81/actual-completed-read02/RESULT.json) at01:35:00Z observed five
complete child groups: JSON+LF14.6619730--16.9956831s, UTF81.3959788--1.7398051s,
atomic wrapper17.2069761--17.7650871s, lock waits at most7.2us. Five independent
aggregate rows ranged34.0997363--36.3948561s; they have no child token and are
not exact-sum joins. One group was still partial at that read, which was not
repeated. The atomic wrapper boundary does not distinguish temporary write
from replace, so no I/O substep or speedup is inferred.31's narrow source review
will decide the smallest useful optional split for the next already-needed SDK
change. The service-query history-free optimization was already adopted in7498;
35's source comparison returned NO_NEW_WORK using the prior60-case qualification.


## Optional atomic write/replace split for the next required SDK upgrade

The actual17s wrapper samples justified separating its two synchronous steps.
31's Environment/native_driver patch adds optional existing-token stages
`driver.full_state_temp_write_bytes` and `driver.full_state_replace`, using the
same logger and original temporary path/bytes/replace/exception handling. With
profiling off, the two-argument writer call and lazy-import-free branch stay.
Root adopted both files and py_compile exited0 at observed01:49:36Z. No new
functional test or profiling-only SDK restart. These stages enter SDK82 with
the already-needed marriage admission diagnostic; actual values and performance
improvements remain unobserved. Existing whole-wrapper and aggregate rows stay.
