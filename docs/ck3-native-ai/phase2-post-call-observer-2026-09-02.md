# Phase-two post-call observer (2026-09-02)

The exact runtime caller package bound the selected continuation to
`0x3407DA1`, before its caller-local producer list is transferred, retried and
released. This package implements the corresponding private read-only observer.

The default-off option `XAR_CK3_ENABLE_PHASE2_POST_CALL_OBSERVER_V1` patches the
exact 14-byte anchor `90488B4C24684885C97411488B01` at `0x3407DA1`. Because
that anchor contains a relative `JE`, it is not copied blindly into the RX stub.
The stub replays the load/test and uses explicit absolute exits: null continues
at `0x3407DBD`; non-null loads `[RCX]` and continues at `0x3407DAF`.

At each hit the observer derives the producer-list carrier as `RBP+0xE0`, reads
begin at `+0x0` and count at `+0xC`, then scans at most 4,096 descriptor
pointers. It reads task/owner from descriptor `+0x18/+0x20`, callback/state from
task `+0x38/+0x60`, and callback vtable slot 2. Raw hit/list/descriptor and last
identity fields distinguish a selector miss from a hook miss. Selected state
telemetry publishes only when slot 2 equals `module_base+0x88B480`.

The observer does not write any native task, descriptor, callback, list or
scheduler state. Installation requires the exact build and newly created primary
thread suspension. Anchor validation, page transitions, instruction-cache flush,
recoverable rollback and quiescent uninstall follow the existing private hook
lifecycle.

MSVC x64 Release private-option DLL SHA-256 is
`E5AAC565567D104B2AD6E6718F0089A6211586429DF66CD4E74D1D62EB81004D`.
The separately built default-OFF DLL SHA-256 is
`A81AA4C35006CD678CE2FA9B8DD3C2C544DD3A13DC4DE4E75C77853AC060CAD4`;
private heartbeat tokens are absent. The executable fixture covers selected
state 2, raw selector miss, both relocated exits, uninstall restoration and
recoverable rollback. No CK3 process was started, and public ABI/readiness are
unchanged.
