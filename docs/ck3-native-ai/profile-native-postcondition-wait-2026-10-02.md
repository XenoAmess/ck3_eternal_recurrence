# Wait for the native semantic result after one ACK

The frozen `67f8c101cd4604a54f969a13bf89f6b6147d1a25` consumer submitted
resume once in R8 at 2026-10-01 15:49:22 UTC, then reported RED because its
immediate cached snapshot still said paused. A later read-only native snapshot
at 15:50:44 UTC and independent clock at 15:50:52 UTC both showed
`paused=false` and raw date `77536008`. The operation materialized after ACK;
the wrapper did not wait for that cache update. The original RED remains valid
evidence of the wrapper failure and must not be rewritten as an immediate
verified result.

The authoritative profile MCP now observes the postcondition for up to five
seconds after its one provider invocation. Each attempt reads a native snapshot
and checks the complete profile guards before and after it. Pending semantic
state is polled at up to 50 ms intervals; no iteration invokes a game command,
replays an event, changes the caller revision or injects a DLL. A process/build,
userdir, foreground, Steam offline, exclusive lease, crash-package or map-ready
failure ends immediately as RED. Expired pending state also returns RED with
its original before frame and receipt. The deadline bounds retrying native
state; the individual existing guard calls retain their own finite operations.

| Operation | Verified result |
| --- | --- |
| Pause/resume, including current-frame pause | Exact target `paused` boolean in a native map-ready frame; current-frame pause also rejects backwards raw date. |
| Speed | Requested native speed value. |
| Event option | The selected old full event instance is no longer active. |
| Checkpoint | Existing provider materialization wait plus actual isolated save path, positive bytes, matching size/SHA-256 and submitted raw date. Invalid save metadata/file identity fails immediately. |

Only a private pending-state exception is retried. Malformed output, failed
native identity or guard exceptions are never treated as transient success.
Strict event/save/resume revision gates before submission remain unchanged.
The no-argument current-frame pause still binds the real provider's submission
frame. The complete native full-build RED and frozen C4 ordinary qualification
remain unchanged.

Validation passed 44 clock/profile/campaign/wait/semantic tests. Four new tests
exercise the real `NativeHeadlessGameplayDriver` and `GameplayBridgeService`
with an offline `FakeEndpoint`: resume/speed/pause ACK is released before a
subsequent native frame, an event exits in a later native frame, a checkpoint
file appears after save ACK, and a crash package appearing after resume ACK
fails without replay. The simulation frame producer is released only after the
production verifier has observed the pending semantic state. Existing tests
cover deadline RED, missing event/save state and strict revision refusals.
All paths assert exactly one or zero transport submissions as appropriate.

```text
python -m unittest test_ck3_native_campaign_projection test_ck3_native_clock_reader test_ck3_native_profile_mcp test_ck3_native_profile_wait test_desktop_semantic_action_mcp
```

Run from `tools/` with the main dependency-qualified Python 3.13 interpreter.
`open_kaishek` preflight is not applicable to native pipe/cache and Win32 guard
composition; this change involves no CK3 script runtime subset. Generic
ownership stays in this main repository. No desktop, running service, DLL or
game operation was changed by this package. R8 retains its frozen `67f8c101`
service; its exclusive owner can preserve later read-only evidence of late
materialization without resending the submitted action.
