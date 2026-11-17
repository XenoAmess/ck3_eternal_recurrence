# CK3 1.21 agent Core and clock control

The exact target is CK3 **1.21.0 (Florin)**, Steam build **26622941**, executable SHA-256 `2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc`. Existing exact-build identities remain supported. Recognizing this executable does not authorize old addresses, full snapshots, frontend layouts, finance, events, or other domain capabilities.

Agent startup through `GameSupervisor` requires `MINIMIZED_NO_ACTIVATE` before creating a Game process. Bootstrap Core retries do not focus, restore, capture, or make a window topmost. Observation and controls use the held owner descriptor and Native pipe while the Game stays minimized.

`NativeOwnerSnapshotMain268` retains its three arguments: owner descriptor, configuration, and an absent output directory. Existing v1 SavedGame reads and v2 menu Core reads remain available. The new explicit configuration is:

```json
{
  "schema": "xar.native-owner-snapshot-config/v3",
  "mode": "core_clock_control",
  "control_step": "pause-map",
  "owner_descriptor": {"path": "D:/actual/owner.json", "bytes": 1, "sha256": "replace-with-the-actual-descriptor-hash"},
  "overall_timeout_seconds": 60,
  "read_timeout_seconds": 30,
  "maximum_frames_per_operation": 128
}
```

The descriptor reference above is illustrative; the caller must measure the actual immutable owner document. Controls are limited to `pause-map`, `resume-map`, `set-speed-1` through `set-speed-5`, and `save-checkpoint`. SAVE submission requires an observed paused Core. Native also checks its exact advertised capability, main-thread role, current prefix, and original deadline before queuing the command.

Each invocation performs one Core query and at most one control submission. Only the private `CoreReceived` occurrence from the identical receiver can authorize submission. Its Game/session/connection, original packet custody, and query deadline must remain valid. The wire uses `expected_revision=0` in this dedicated role and carries the complete observed Core prefix plus an absolute control deadline no later than the original query deadline. It never creates a full-observation permit.

The output retains query originals and separate `control/` originals. An ACK records submission only: `effect_confirmed` and `save_confirmed` remain false. Observe engine state and any physical SAVE independently. UNKNOWN retains its original request ID and packet and must not be replayed.

Software validation includes 14 control/CLI/background tests and preservation of the old 47-class public API. The two unchanged C++ producer fixtures also pass the 12 receiver/control tests through classpath resources without machine-specific paths. These are separate test runs with overlapping cases, not an aggregate count of distinct tests. The default 34-module Java test-compilation graph was repaired without claiming the complete test suite passed.

The event source review covers 198 historical keys against the installed source. Its 1.21 public results remain `unavailable`, with `contract=null`; source comparison grants no Native event binding or actionable option. Finance and complete event-window observations still require their own migrated producer contracts.

Background Core reads have been observed on the new executable. The software and ABI results here do not establish actual control effects, a completed SAVE, full observation, Driver adoption, or OODA readiness. Live control qualification remains a separate recorded result.
