# ZhongGuo phase-two promo producer scaffold

`zhongguo_phase2_promo_producer.py` is only the hand-off boundary for the
future real-game visual producer.  It does not launch CK3, invoke FFmpeg,
inspect the desktop, call `PromoRecorder.start()`/`clean_hold()`/`stop()`, or
write capture artifacts.  It cannot make a static or MCP-only run look like
video evidence.

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
created on those paths.

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
