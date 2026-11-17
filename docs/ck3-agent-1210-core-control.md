# CK3 1.21 agent Core and clock control

The exact target is CK3 **1.21.0 (Florin)**, Steam build **26622941**, executable SHA-256 `2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc`. Existing exact-build identities remain supported. Recognizing this executable does not authorize old addresses, full snapshots, frontend layouts, finance, events, or other domain capabilities.

Agent startup through `GameSupervisor` requires `MINIMIZED_NO_ACTIVATE` before creating a Game process. Bootstrap Core retries do not focus, restore, capture, or make a window topmost. The OWNED watchdog continuously reapplies the same minimize-only policy to visible windows belonging to the held Game PID and birth. Each Core control/exit also checks this policy synchronously before consuming its receipt or entering a Native write; missing or failed checks reject with zero control writes. An asynchronous minimize request alone is insufficient: the minimized state must be read back.

An already running owner can use the same shared implementation through `GameSupervisor maintain-background <descriptorPath> <descriptorSHA256> <seconds>`. It verifies the exact descriptor, machine, owner and Game generations, retains only read-only process handles, and never acquires a Job termination right. It exits on target exit, custody loss or its finite deadline. It reports policy unavailability while retrying minimize-only maintenance; the separate Native write check must still succeed before any action. No foreground, restore, input or screenshot API is used.

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

Normal application exit has its own explicit `xar.native-owner-snapshot-config/v4` mode, `core_application_exit`, with the same descriptor and finite timeout fields. It rejects `control_step` and `core_prefix_only`. Only a real partial Core receipt from the same receiver can authorize `normal-exit-application-v1`; an unavailable Core cannot. A partial menu prefix may authorize exit without inventing a played actor. The exit write consumes a transport-lifetime claim and blocks further controls. Its original ACK is archived under `exit/`; `normal_exit_confirmed` remains false until the physical supervisor proves a natural terminal.

Native `queue_status` or `dispatch_status` equal to `indeterminate` becomes sticky UNKNOWN, even when a negative ACK was received. The exact ACK packet and custody are retained alongside the UNKNOWN request. Querying or archiving these originals does not resend a command.

Software validation includes 14 control/CLI/background tests and preservation of the old 47-class public API. The two unchanged C++ producer fixtures also pass the 12 receiver/control tests through classpath resources without machine-specific paths. These are separate test runs with overlapping cases, not an aggregate count of distinct tests. The default 34-module Java test-compilation graph was repaired without claiming the complete test suite passed.

The event source review covers 198 historical keys against the installed source. Its 1.21 public results remain `unavailable`, with `contract=null`; source comparison grants no Native event binding or actionable option. Finance and complete event-window observations still require their own migrated producer contracts.

Background Core reads have been observed on the new executable. The software and ABI results here do not establish actual control effects, a completed SAVE, full observation, Driver adoption, or OODA readiness. Live control qualification remains a separate recorded result.
