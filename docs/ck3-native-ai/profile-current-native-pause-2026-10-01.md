# Profile-bound pause of a running ordinary campaign

The authoritative Python consumer owns this capability; mod repositories only
supply frozen profile data. `ck3_pause_profile_simulation_v1` accepts `{}` with
no additional properties. It operates solely on the already verified attachment
of its persistent server and retains that server's session/pipe/run identity.
It does not attach, reconnect, replace the frozen DLL or accept an external
revision, process, command, key, coordinate or date.

A running campaign publishes new semantic frames. The existing revision-bound
simulation tool reads the caller's exact revision before and after its task-bus
poll and foreground/offline/lease guards. The clock can advance during these
checks, causing a pre-submission refusal. A deterministic test reproduces this
through the same production wrapper without issuing a command. Event selection,
checkpoint creation and resume still retain their original exact revision gates.

The new tool polls the pinned task bus, repeats the existing full profile guard,
then records a current map-ready native snapshot. It calls the existing
`GameplayBridgeService.execute_step("pause-map", expected_revision=None)` once.
The provider itself takes its submission snapshot and sends that actual native
revision in the request (`native_driver.py`, near line 8828). This is a stateless
target of `paused=true`, so the caller need not keep
an earlier running frame stable during foreground and offline checks.

The frozen 1.20 native implementation already supports this operation.
`ck3_12002_commands.cpp::SubmitPauseMap` rereads the current core/map/player
state and submits the bound player pause command, or returns `already_paused`.
The `bridge.cpp` pause branch publishes a timeline snapshot even for that
idempotent result. This Python tool adds no native ABI and changes no production
artifact or AI policy.

Success requires the existing exact PID/build hello, map-ready native readback,
`paused=true`, no backwards raw date, and the full post-operation guard. The
guard binds HWND/process continuity, isolated `-userdir`, foreground, exclusive
fresh lease, Steam offline client/UI continuity and pinned task-bus identity.
Any entry in the isolated `crashes` directory before or after inspection rejects
success. A live PID alone does not establish healthy play. The receipt records
before/after snapshots, the final observation, fixed session and profile hash,
and `revision_binding="provider_submission_frame"`. Any failure after the one
submission produces RED with evidence; the tool does not replay the command.

Validation: 40 clock/profile/campaign/semantic consumer tests passed. They
include the real provider with an advancing native frame and one transport
request bound to its latest revision; the older stale-revision route issues
zero commands. Offline/foreground/userdir/lease/crash/map failures issue zero
commands. ACK without pause, timeout, changed PID, a backwards date and a new
crash package produce RED after exactly one submission. Closed MCP schema and
strict event/save/resume revision checks remain covered. Command:

```text
python -m unittest test_ck3_native_campaign_projection test_ck3_native_clock_reader test_ck3_native_profile_mcp test_desktop_semantic_action_mcp
```

Run it from `tools/` using the main Python 3.13 interpreter with its existing MCP
and desktop dependencies. `open_kaishek` preflight is not applicable: this change
composes native transport and Win32/process guards, with no CK3 script semantics.
The frozen C4 ordinary native qualification remains scoped; its complete
default build is still RED. No desktop or game operation was performed by this
package. Live acceptance belongs to the exclusive consuming client.
