# Active scheme paused-live native glue v1 private

Status: **candidate-core ready when production callbacks are supplied**. This
package composes the SCHEME2–7 private observer, source adapter, stable-key
definition resolver, semantic action core, and native command adapter into one
application-main-thread transaction surface. It does not add a public bridge
command, MCP capability, or schema, and it contains no concrete candidate or
live artifact.

## Composition boundary

`active_scheme_paused_live_native_glue_v1_private.hpp/.cpp` accepts three
already frozen inputs:

1. a SCHEME3 source access, normally produced by the SCHEME4 exact-build native
   binder;
2. a native precondition capture callback;
3. an incomplete SCHEME6 command binding plus the SCHEME7 definition binding.

Binding first requires the same CK3 `1.19.0.6` executable SHA-256 across every
component. It rejects missing source or precondition callbacks, installs the
SCHEME7 resolver into the command binding, then installs SCHEME6 into SCHEME5.
The returned readiness separates exact build, observation, definition,
precondition, and single-submit binding. `candidate_core_ready` becomes true
only after every component binds.

The glue owns no engine pointer. It stores callback contexts and the private
adapter states only. Each operation requires equal nonzero current and
application-main thread IDs and rejects nested execution. It installs those
IDs only for the synchronous call, then clears them.

The five methods directly match the SCHEME8 backend stages:

1. `CaptureActiveSchemePausedLiveSnapshotV1Private` calls the SCHEME3/4
   double-read observer.
2. `ResolveActiveSchemePausedLiveDefinitionV1Private` calls SCHEME7's exact
   getter/hash/native-lookup/canonical-key resolver.
3. `CaptureActiveSchemePausedLivePreconditionV1Private` obtains the copied
   native character-interaction precondition.
4. `ExecuteActiveSchemePausedLiveNativeGlueV1Private` runs SCHEME5 through
   SCHEME6 and accepts only a pending ACK with exactly one submit call.
5. `VerifyActiveSchemePausedLiveNativeGlueReceiptV1Private` invokes SCHEME5's
   fresh SCHEME4 observation receipt and accepts only an applied new instance.

Failures remain typed as binding, ownership, observation, definition,
precondition, action, or receipt RED. The underlying source and semantic
failure enums remain available on the glue state. A pending submit ACK does
not become a GREEN receipt.

## Candidate build registration

The default-off CMake option
`XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1` registers only the
SCHEME2–9 private source files in `xar_ck3_bridge`. Default builds remain
unchanged. Enabling the option compiles the candidate core but does not expose
or advertise it. A future concrete candidate must add its private mailbox
executor/backend wrapper and supply the production callbacks below before the
component can run.

## Concrete candidate readiness

A useful unique candidate **cannot yet be produced from this commit alone**.
The standard build can now compile the complete candidate core, but these
production bindings remain absent:

- the exact native precondition reader for shown, validity,
  `can_start_scheme`, previews, and the four murder starter options;
- SCHEME6's production low-level callbacks for full character identity,
  submit-route/manager generation, context construction/validation, command
  construction, one submit, and both release paths;
- the private main-thread mailbox executor and raw JSON backend used by the
  SCHEME8 harness;
- one fixed checkpoint and resulting DLL/injector/manifest hashes.

These are real construction dependencies, not warnings. Setting the CMake
option without them only compiles unadvertised code and must not be described
as a runnable or production-live candidate. The next minimum package is the
exact-build precondition/command callback binder; after that, a thin private
mailbox/backend wrapper can produce the single hash-bound candidate.

## Focused verification

The C++ fixture composes all private layers with copied offline callbacks and
checks basic sway and complex murder through snapshot, definition,
precondition, one submit, and fresh receipt. It also covers exact-image binding
failure, main-thread and reentrancy gates, source/definition/precondition
stage RED, stale-receipt RED, and the SCHEME7 collision/lifecycle matrix.

The portable Python driver discovers MSVC from the developer environment or
installed Visual Studio directories. Normal Python builds `/Od`; `python -O`
builds `/O2 /DNDEBUG`. Both use `/W4 /WX` and temporary isolated output:

```powershell
py ck3_autonomous_player/native_bridge/research/test_active_scheme_paused_live_native_glue_v1_private.py
py -O ck3_autonomous_player/native_bridge/research/test_active_scheme_paused_live_native_glue_v1_private.py
```

These are fixtures. No CK3 process was started and no live status is claimed.
