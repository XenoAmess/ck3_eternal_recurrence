# Phase-two completion observer ready-to-live (2026-09-02)

The exact-build read-only observer is implemented at `0x3B9DEA7` and is ready
for one separately authorized live run. It remains disabled in default builds.

The 15-byte hook replays the frozen state read/classification and preserves the
two native destinations: non-complete states continue at `0x3B9DEB6`, while
states 2 and 3 enter the original retire path at `0x3B9DF63`. Only the complete
path calls the observer. The callback at `[RBX+0x38]` is selected only when its
vtable slot-2 target is exact RVA `0x88B480`; all other tasks are ignored.

Private atomic telemetry records selected event/state counts, thread ID,
`QueryPerformanceCounter` timestamp, task/callback identity, reference count,
whether state 3 was already observed, and whether reference count 1 means this
consume will take the native retire path. A private-option heartbeat object
named `phase2_completion_observer_v1` exposes those fields to the existing
seed-gate transport. The field is compiled out of default builds, so neither
the public ABI nor default heartbeat schema changes.

Installation is admitted only for the pinned build while the newly created
primary thread is suspended. The component uses the existing transactional
anchor/protection/write/flush lifecycle. Focused fixtures cover exact install,
selected and rejected callback identities, state 2/3 telemetry, exact
uninstall restoration, and recoverable installation rollback. The hook never
writes CK3 task state, reference counts, callbacks, or control data.

No CK3 process was started for this package. Phase two remains
**native-readiness RED + private observer ready-to-live**.
