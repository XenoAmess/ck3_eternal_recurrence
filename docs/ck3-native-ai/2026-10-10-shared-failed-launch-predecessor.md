# Shared allocator: an ended safe failed launch can be a predecessor

R0041 exhausted its original 600-second saved-startup readiness deadline before
the engine logged Setup completion. Delayed injection was never admitted;
there were 714 connection-wait observations, zero native campaign frames and
zero case steps. Its original host Popen returned 1. The immutable report keeps
`cleanup_ok=false` and `session.report=null`.

The allocator previously required `closed_session(report)` to be true before
examining any other predecessor facts. Calling that exact function on the R0041
report returned false and reproduced `Previous live session has not proved
complete cleanup`. This rejected an ended launch whose exception came from the
runtime's completed safe-failure cleanup path, before a SessionHandle could be
returned to the host.

The allocator now records a separate `previous-shared-failed-launch` predecessor
when the original report is finished, its managed thread finished, its exact
session error is `launch_error` followed by `CK3 launch contract failed safely`,
and no case steps or readiness result exist. The original retained host Popen
must have returned integer 1 for the same frozen run and host PID. The report's
state must match the frozen state, and its current unsafe, PID and watchdog-ready
controls must all be absent. A historical watchdog-start receipt may remain.

The branch records the original report and host receipt hashes, current control
absence, `original_cleanup_ok=false`, unknown original CK3 exit code and unknown
original final Job count. It does not grant typed normal exit or business credit.
Returned native sessions still require the original complete native shutdown
proof; an incomplete returned session cannot use the failed-launch branch.

Both predecessor routes then use the existing machine identity, latest machine
allocation, keeper/release CAS and fresh full-machine runtime process inventory
checks. The failed launch cannot be reused as a first-machine bootstrap. No
allocator, launch, screen operation or process signal was executed for this fix.

Validation used six focused failed-launch tests plus the existing normal
predecessor/CAS and mocked allocation-to-original-keeper tests: eight passed.
The actual R0041 files passed only the new file-level predecessor subgate;
complete successor allocation and subsequent gameplay remain untested.

External immutable evidence:

- `C:/workspace/ck3_lyd_runtime_20261004/r41-failed-launch-allocator-reproduction-20261010-001/ORIGINAL-REJECTION.actual.json`
  (863 bytes; SHA-256 `bad9ff44059b60f7e7bff52c01f34316544af8987098f6c845c15918a09c0887`).
- `C:/workspace/ck3_lyd_runtime_20261004/r41-failed-launch-allocator-validation-20261010-001/RESULT.actual.json`
  (1,210 bytes; SHA-256 `f45b3ae4ed0d9c05241e4068558e33c766f922b9c19126df947f85b587be352f`).
- `C:/workspace/ck3_lyd_runtime_20261004/r41-failed-launch-allocator-validation-20261010-001/R41-FILE-ONLY-SUBGATE.actual.json`
  (2,380 bytes; SHA-256 `21b3af66445ea3abbea39e44b22e8039b81b6d6a1712360b6fb9df4e82e22b2e`).
- `C:/workspace/ck3_lyd_runtime_20261004/r41-startup-and-cleanup-diagnostic-20261010-001/INDEX.json`
  contains the earlier frozen-source cleanup analysis and separately timestamped
  current process absence. Current absence is not original HANDLE exit evidence.

R0041 remains startup RED. Whole-product acceptance remains NOT_GREEN.
