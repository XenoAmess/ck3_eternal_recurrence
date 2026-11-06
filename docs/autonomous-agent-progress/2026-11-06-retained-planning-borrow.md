# Retained planning read handoff

Feast preparation could run after its short active collector scope had closed, while the same actual planning round still retained its qualified Ready capture. The pure consumer then rejected it with `pure Driver/history consumer requires an already active actual collector lease`.

`NativeReadinessCollector.borrowCurrent` now accepts that existing producer-owned retained round through its unchanged strict `retainedPlanningRead` path. The active-scope path is preserved. The fallback requires the identical borrowed Session and an actually captured round, excludes held/public/first-checkpoint modes, and repeats the original frame, source, head, history, owner, and deadline checks. It creates no capture, refresh, scope carrier, or permission.

The one changed production translation unit compiled successfully: 38 classes in 6.973255 seconds, with all class structures unchanged. The two new regression methods use the existing public producer and memory fixture. A necessary existing 524-byte test factory compiled once (1 class, 3.0087812 seconds); the changed test compiled once (8 classes, 6.8318132 seconds). Only the two new methods ran: 2 passed, none failed, errored, or skipped, in 5.430772 seconds of process wall time. The old seven methods and all fixture/import code were retained and were not rerun; production classes were reused.

The regression verifies same-round preparation after the active scope ends, identical captured frame/Driver, zero additional packet reception or dispatch, rejection without a captured round or with a foreign Session, rejection before and after head changes, original exception identity, and scope cleanup. The memory ports and synthetic source qualifications establish software behavior, not a physical Root/Native lease.

The actual B39 report separately showed FEAST `KEPT` with its complete native read and retained original choice, passing the former lease rejection. That batch later stopped at a distinct cadence source-pin mismatch before any action dispatch. This does not establish a started/completed activity, full M6/M7 acceptance, saved days, or a speed improvement.

Source owner: `/root/m6_continue`; formal owner: `/root/java_continue`. The formal production patch preserves its two existing whitespace-only differences and otherwise matches the qualified source. Test source matches the qualified input exactly. No model result is treated as runtime evidence.
