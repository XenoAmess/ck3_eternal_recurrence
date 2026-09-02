# ZhongGuo phase-two promo producer adapter

`zhongguo_phase2_promo_producer.py` contains the strict hand-off scaffold and
the concrete managed-runtime adapter.  The adapter does not launch CK3; it
reuses the acceptance runner's managed seed/session/loader context, paused-map
probe, and loaded-seed proof.  Recorder lifecycle remains unreachable until
those real gates and all eight visual handlers are ready.

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

`run_zhongguo_acceptance.py --phase2-promo-capture` installs the managed
adapter when no explicit producer override exists.  Product-specific visual
handlers register by canonical producer key:

```python
from run_zhongguo_acceptance import register_phase2_promo_visual_primitive

register_phase2_promo_visual_primitive(
    "facts-quota-calibration",
    expose_real_facts_quota_calibration_surface,
)
```

The registry adapter implements the producer-neutral `Phase2SpanDriver` and
delegates ordering, readiness, surface/postcondition checks, and clean holds to
`run_phase2_capture_choreography`.  Registration order cannot change the
contract order.  The current incomplete registry returns typed RED
`span_handlers_missing` before `PromoRecorder.start()`; a missing canonical
seed stays typed RED `seed_not_ready`.  Passing static mappings does not
establish `fixture-live` or `production-live`; those statuses still require a
real CK3 capture, all eight clean-frame gates, and downstream review.

The seed-preflight binding also requires the capture root's GREEN `report.json`
for the adapter's report/index contract.  A timeline with a matching source
identity but no report is retained as a typed `capture_identity_unbound`
candidate blocker; it must not be described as bound.

After a successful full build reaches final-duration verification, the phase-two
CLI rechecks the CK3 adapter's load-time bytes/SHA-256 snapshot with
`CaptureBundle.verify_unchanged()` before writing the pipeline result or
candidate run.  A changed or missing source is retained as a RED attempt with
the typed `capture-source-immutability` phase for diagnosis.
