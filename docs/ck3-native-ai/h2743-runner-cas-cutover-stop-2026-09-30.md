# H2743 current-HEAD v5 live CAS cutover stop

The current-HEAD v5 runner still begins live preparation and `--run` with
`LIVE_STOP_CAS_MIGRATION_PENDING`. This branch also makes its old
`screen_lease()` list/stale check and `renew_screen_lease()` bare heartbeat
reject the v5 candidate before any task-bus subprocess. It does not connect
the isolated CAS protocol from Draft #732 to the authoritative bus or launch
CK3. Older H2743 candidate behavior is retained.

Draft #732's isolated protocol and its temporary-bus normal/`-O` tests already
exercise exact CLI source/installed SHA, fresh claim, expected-sequence
heartbeat/release, stale and `done+screen` conflict, wrong expected sequence,
event gap, and fail-closed readback. Those tests do not establish a safe live
supervisor route.

## Concrete blockers to a live runner connection

1. The current `prepare_no_launch()` and `run()` accept a caller-supplied task
   ID and assume an external screen owner; they do not atomically claim one.
   The managed profile subprocess, native-session supervisor, watchdog and CK3
   child do not share an audited launch fence with the task-bus owner.
2. `prepare_no_launch()` waits only for its direct CLI process. `run()` checks
   `ck3.exe` names after exit but does not bind a complete child process tree
   and creation identities to a cleanup receipt. Draft #732's
   `release(cleanup_proven=True)` is fixture-only and cannot justify releasing
   the authoritative screen resource. If a profile subprocess's 60-second
   lease renewal raises, its current call path has no `finally` that stops and
   reaps that subprocess; a returned exception does not prove cleanup.
3. The native-session watchdog and main thread can both renew during error
   handling. The isolated CAS protocol has no shared operation lock, so two
   concurrent expected-sequence heartbeats could conflict. A production
   supervisor needs serialized ownership changes and a failed-heartbeat STOP
   that preserves the worker and descendant-process evidence.
4. The authoritative installed bus CLI is still old, the historical XQOL
   `running+screen` record is unreleased, and other screen-capable launchers
   still need the same CAS fence. A fresh claim must fail until these are
   resolved through their own audited work.

A later cutover needs a shared claim-to-launch-to-cleanup fence, exact worker
and descendant process evidence, a release method bound to that evidence's
bytes and SHA-256, migrated callers, a fresh Steam offline image review, and
independent live admission. The runner-byte change in this branch also means
the frozen attempt 17 seal remains historical and cannot be reinterpreted as
a seal of this future runner. No authority write, screen claim, CK3 session,
native H2743 read or gameplay action occurred here.

## Code-only verification

The frozen external report is
`D:/ck3-research-artifacts/h2743-runner-cas-cutover-stop-20260930/attempt-01/result.json`
(SHA-256 `FA5D06B0A99F12222B9082282CF91BA83A4A0D81B1F1240C0EAB2BE3EA970317`).
With the reviewed #685 bus source pinned by SHA, the v5 runner tests pass
11/11 in normal mode and 11/11 under `-O`; the temporary-bus CAS protocol
tests pass 9/9 in each mode. The runner hard-stop test mocks
`subprocess.run` and `subprocess.Popen`; it verifies that neither call is
reached through these two helper paths before the guards. This is
`CODE_ONLY_GREEN_LIVE_STOP`, not live admission.
