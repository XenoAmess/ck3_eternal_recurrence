# ZhongGuo phase-two promo producer scaffold

`zhongguo_phase2_promo_producer.py` is only the hand-off boundary for the
future real-game visual producer.  It does not launch CK3, invoke FFmpeg,
inspect the desktop, call `PromoRecorder.start()`/`clean_hold()`/`stop()`, or
write capture artifacts.  It cannot make a static or MCP-only run look like
video evidence.

The producer-neutral eight-span action catalogue and executor live in
`zhongguo_phase2_capture_choreography.py`.  Its definitions bind every fixed
span to product event keys, GUI surfaces, MCP queries/actions, a concrete
runner action entrypoint, and a provider-observed postcondition.  The executor
first requires the ready seed, GREEN seed install, matching native PID/session,
GREEN loader/capability gate, paused map snapshot, and all eight real span
handlers.  It calls `clean_hold()` only after the corresponding handler has
returned both `surface_visible=True` and `postcondition_green=True`; a missing
gate or RED action raises `Phase2ChoreographyBlocked` and never creates a clean
gate for that span.  This module does not register a producer or start/stop a
recorder.

Build an unregistered scaffold while the runtime implementation is absent:

```python
from zhongguo_phase2_promo_producer import (
    make_phase2_promo_capture_scaffold,
)

producer = make_phase2_promo_capture_scaffold(
    runtime_probe=read_only_real_runtime_probe,
    choreography=real_phase2_choreography,
)
```

The probe receives one `Phase2PromoCaptureContext` and must return a mapping
with `ready=True` only after it has established the real CK3 runtime needed by
the choreography.  The choreography receives the same context plus that probe
result, performs the actual gameplay/UI work, and returns the runner evidence
object.  The scaffold forwards no defaults: mode, version, and the complete
canonical eight-span `capture_contract` must be present and exact.  Missing
dependencies, an unavailable runtime, or malformed evidence raises a typed
`RED` with `reason_code` and JSON-compatible `evidence`; no clean-frame gate is
created on those paths.  The scaffold exposes that structured envelope to its
direct caller, and the acceptance runner preserves it as
`phase2_promo_producer_error` in the cell and matrix reports.  If the delegate
includes an optional `result` field, it must be exactly `GREEN`; omitting it leaves the
runner's outer capture result in charge, and the runner rejects any explicit
non-`GREEN` value before accepting the hand-off.

Only a future producer with both real dependencies should register the
callable:

```python
from run_zhongguo_acceptance import register_phase2_promo_capture_producer
from zhongguo_phase2_promo_producer import install_phase2_promo_capture_scaffold

install_phase2_promo_capture_scaffold(
    register_phase2_promo_capture_producer,
    runtime_probe=read_only_real_runtime_probe,
    choreography=real_phase2_choreography,
)
```

The install helper is explicit and has no import-time registration.  It
refuses to register an unconfigured scaffold, preserving the runner's existing
preflight `producer hook is unavailable` RED until a real phase-two runtime
and choreography are available.  Passing a probe result or evidence object
from a static test does not establish `fixture-live` or `production-live`;
those statuses still require the runner's real CK3 capture, clean-frame gates,
and downstream review contracts.

The seed-preflight binding also requires the capture root's GREEN `report.json`
for the adapter's report/index contract.  A timeline with a matching source
identity but no report is retained as a typed `capture_identity_unbound`
candidate blocker; it must not be described as bound.

After a successful full build reaches final-duration verification, the phase-two
CLI rechecks the CK3 adapter's load-time bytes/SHA-256 snapshot with
`CaptureBundle.verify_unchanged()` before writing the pipeline result or
candidate run.  A changed or missing source is retained as a RED attempt with
the typed `capture-source-immutability` phase for diagnosis.
