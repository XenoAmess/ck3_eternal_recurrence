# Activity planning application-main glue (1.19.0.6)

This note records the ACTIVITY5 private glue above the exact-build
`activity_planning_snapshot_v1_native_binder`. It prepares one P0
`activity_feast` snapshot request for execution on an already-paused
application-main frame. It does not add a shared mailbox slot, public schema,
MCP method, planner action, or production capability advertisement.

## Composition and ownership

`ActivityPlanningApplicationGlueStateV1` owns the copied activity key, prepared
request, Activity4 binder, Activity3 source adapter, Activity2 observer, and
the pointer-free terminal result. Configuration accepts caller-owned exact
operations for:

- current frame identity;
- exact-build memory reads and RTTI cast;
- HostView slot-25 final `CanPlanActivity` evaluation;
- the complete native semantic sample.

The glue replaces the operation context with private scoped wrappers before
configuring the binder. Memory reads remain available while the binder admits
the exact image and vtables. Frame, final-evaluator, and semantic operations are
admitted only while `ExecuteActivityPlanningApplicationGlueV1` owns a prepared
request. The final-evaluator wrapper additionally pins the admitted module base
and exact slot-25 address.

The request side copies the stable key and accepts exactly one
`activity_feast` request. It does not invoke CK3. The execution side first asks
the caller for a fresh frame and requires:

- application-main execution;
- a paused game;
- matching snapshot revision, date, live owner, map readiness, and owner ID.

Only after those checks does it enter the two-sample observer transaction.
The result is terminal and exposed through the owned fixed-capacity value.
An observer failure remains a typed unavailable result, while glue, binder, and
source-adapter diagnostics retain the failure layer for the RED artifact.

The caller must serialize prepare, application-main dispatch, and result read.
This package does not install a cross-thread transport or extend the shared
main-thread mailbox ABI.

## Build switch and static acceptance

`XAR_CK3_ENABLE_G2_ACTIVITY_PLANNING_SNAPSHOT_PRIVATE_GLUE_V1=ON` links the
four private activity layers into `xar_ck3_bridge`. It is off by default and
does not call the glue from `bridge.cpp`; the switch proves that the candidate
sources link with the current bridge without changing the public protocol.

The standalone fixture builds all four layers together under MSVC `/W4 /WX`.
Normal and optimized configurations cover exact-build and callback admission,
single-request/key ownership, application-main and paused gates, scoped native
operation counts, complete copied P0 semantics, known-false final-evaluator
data, typed native failure retention, and one-shot result behavior. The default
bridge is also linked independently with the switch left off.

## Candidate and live boundary

Status: `static-ready private application-main glue`.

The next live candidate is not production-wired. Before a paused CK3 run it
still needs both of these activity-owned inputs:

1. caller-supplied exact final-evaluator and complete semantic operations for
   CK3 `1.19.0.6`;
2. a private application-main invocation entry that serializes prepare,
   dispatch, and result collection without extending the shared mailbox ABI.

After those inputs are installed, the candidate may execute one paused
`activity_feast` capture and retain its artifact. Until that run is GREEN, the
capability is neither `production-live` nor `action-ready`. No CK3 instance was
started for ACTIVITY5.
