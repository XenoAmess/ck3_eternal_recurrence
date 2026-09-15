# Active scheme paused-live harness v1 private contract

Status: **fixture-ready reusable harness**. This package provides the bounded
runner, report verifier, and normal/optimized fixtures. It does not contain a
candidate, shared build/bridge/schema/MCP wiring, a CK3 launch path, or a live
artifact. Those gaps remain RED for production-live readiness.

## Purpose and inputs

`active_scheme_paused_live_harness_v1_private.py` consumes exactly one
`active-scheme-paused-live-candidate-v1-private` manifest and an injected
backend that connects the already frozen SCHEME2–7 private interfaces. The
manifest is supplied by path with its expected SHA-256. The harness reads and
hashes the raw manifest before JSON parsing, then verifies every listed
artifact by relative path, byte length, and SHA-256. Absolute paths and parent
traversal are excluded so the same candidate bundle can be moved between
authorized users and machines without changing its contract.

A candidate contains:

- exact game version and executable SHA-256;
- a unique candidate ID and request ID;
- one allowlisted interaction, its fixed scheme type, actor and character
  target;
- the expected paused snapshot capture epoch, container generation, and game
  date;
- the selected murder starter package, or an empty value for sway;
- one or more hash-bound relative artifacts.

The only mappings are `sway_interaction → sway → 0x5783F850` and
`start_murder_interaction → murder → 0xDF3F9819`. No candidate manifest or
candidate binary is included in this work package.

## Ordered transaction

After all candidate hashes pass, the harness atomically creates a persistent
attempt marker keyed by the manifest SHA-256. Marker existence consumes the
candidate before any backend callback. A process exit or typed RED therefore
cannot authorize another submit with the same candidate. The marker is never
removed by the runner.

The injected backend is called in this fixed order:

1. capture a paused, application-main-thread active-scheme snapshot;
2. resolve the exact stable-key interaction definition;
3. capture the character-interaction precondition;
4. submit once through SCHEME5–7 and return its ACK;
5. invoke SCHEME5's fresh active-scheme receipt verifier.

Every callback returns raw JSON bytes. The harness writes those exact bytes to
an exclusive file and computes its SHA-256 before parsing or validating the
stage. The next callback is not entered until the prior raw file exists. This
preserves malformed and RED evidence instead of replacing it with a normalized
summary.

The snapshot must match the hash-bound candidate frame. The definition must
round-trip the expected key, type, exact hash, nonzero resolver-owned
generation, and proof epoch. The precondition must remain in the same paused
frame, match actor/target/key/type, and close shown/valid/can-start plus preview
and murder-starter semantics. The ACK must be
`submitted_verification_pending`, carry exactly one submit call, and match the
snapshot. It is never accepted as the postcondition. GREEN requires the fresh
receipt to be `applied`, have a later capture epoch, preserve the request ID,
and identify one new scheme instance.

## RED and retry semantics

Failures retain a machine-readable `failure` key. Examples include
`candidate_hash_mismatch`, `candidate_artifact_hash_mismatch`,
`candidate_already_consumed`, `snapshot_not_paused`, `definition_mismatch`,
`can_start_scheme_denied`, `submit_rejected`, and `receipt_not_fresh`. A
failure after the attempt marker is created updates that marker to RED and
leaves all raw files already captured. `submit_call_count` is set before the
single submit callback and the harness has no retry branch.

Calling the runner again with the same candidate hash returns
`candidate_already_consumed` before any backend method. A new attempt requires
a newly built and separately hash-bound candidate. This harness does not
decide whether creating that candidate is authorized.

## Verification and test boundary

`verify_active_scheme_paused_live_harness_v1_private.py` independently
re-hashes the candidate manifest, all candidate assets, all five raw stage
files, and checks the persistent attempt marker. It accepts only the exact
five-stage order, raw-first state, one submit, disabled same-candidate retry,
and a GREEN fresh receipt report.

Run the standalone fixtures from the repository root:

```console
py ck3_autonomous_player/native_bridge/research/test_active_scheme_paused_live_harness_v1_private.py
py -O ck3_autonomous_player/native_bridge/research/test_active_scheme_paused_live_harness_v1_private.py
```

The fixtures cover sway and murder GREEN, raw-before-parse preservation,
manifest and artifact hash rejection, definition/precondition/submit/receipt
typed RED, and same-candidate retry rejection after both GREEN and RED. They
use an injected backend and are not live CK3 evidence.
