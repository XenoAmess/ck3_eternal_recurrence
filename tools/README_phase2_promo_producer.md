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

The pre-record seed proof is schema v2.  It queries
`query-loaded-feature-manifest-v1` on the same paused snapshot and binds its
snapshot ID, public/native revisions and date before checking every span's
`all_under_heaven` / `merit_admin` effective flags and the opaque runtime
`All Under Heaven` script key.  Its eight-row matrix also carries the exact
event definitions, machine-readable `event_window:<key>` or
`named_widget:<name>` surface, and MCP query/action requirements.  These rows
deliberately say `provider_ready_claimed=false`: a source definition or loaded
DLC flag cannot prove that a later event/GUI is visible.  The registered live
handler must still provide that proof at span execution.  The default composite
driver now owns all eight handler names, so `span_handlers_missing` applies only
to the compatibility registry path or a regressed custom driver; it is not the
current default blocker.  Eight static owners still do not claim any provider
live proof.

`zhongguo_phase2_visual_handlers.py` supplies the real-surface adapter for the
four catalogue entries that previously had no visual-handler boundary.  The
scoreboard adapter consumes the existing production action cell and accepts
only an `open` action with advertised capability, independently verified
postcondition and a typed-visible modal in the later query.  Promotion,
projects/metrics and cross-cycle/endgame consume exact source and result event
keys through `query-current-event-window-context-v1` and
`select-event-option-N`; their injected bounded advancement and provider
verifier must both return GREEN, and the verifier must explicitly attest
`provider_observed=true`.  An ACK, a result event, or a static fixture alone is
therefore insufficient.  `CompositePhase2SpanDriver` combines these four
handlers with the four already-owned gameplay handlers without allowing two
delegates to claim the same handler.

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
adapter when no explicit producer override exists.  Its context-bound driver
combines the existing B2/manager/workforce/incident acceptance action cells
with `Phase2VisualHandlerAdapter`, so the default readiness inventory owns all
eight canonical handlers.  The workforce delegate uses the production-seed
preflight and never activates the dynamic acceptance fixture.  Missing or RED
provider proof remains a typed per-span RED and cannot create a clean hold.

Tests and explicit producer overrides may still register a product-specific
visual primitive by canonical producer key:

```python
from run_zhongguo_acceptance import register_phase2_promo_visual_primitive

register_phase2_promo_visual_primitive(
    "facts-quota-calibration",
    expose_real_facts_quota_calibration_surface,
)
```

The compatibility registry adapter implements the producer-neutral `Phase2SpanDriver` and
delegates ordering, readiness, surface/postcondition checks, and clean holds to
`run_phase2_capture_choreography`.  Registration order cannot change the
contract order.  A missing canonical seed stays typed RED `seed_not_ready`
before the span-driver factory and `PromoRecorder.start()` are reachable.
Passing static mappings does not
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

`run_zhongguo_phase2_capture_attempt.py` is the one-command hand-off for a
fresh eight-span attempt.  Without `--execute` it only creates an external
`capture-plan.json`; it never starts CK3, the recorder, FFmpeg, or a media
build.  The plan binds a GREEN filtered-completion observer, a non-legacy
ready seed contract, the fresh byte-addressed media preflight receipt, the
bridge pair, all eight default handlers, the schema-v2 loaded-seed gate,
clean-frame begin/end marks, finite runner timeouts, and managed cleanup.  A
missing observer or seed remains typed `waiting-for-bound-inputs`; the old
`98687d...` save is explicitly rejected.  Only a blocker-free plan may cross
the sole `--execute` subprocess boundary, which delegates directly to
`run_zhongguo_acceptance.py --phase2-promo-capture` in a new capture directory.
