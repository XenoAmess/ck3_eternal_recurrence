# Resume a loaded native profile and inspect pending mail

The generic profile MCP can reconnect an already loaded bridge after a normal Python endpoint shutdown. It preserves the CK3 process, loaded DLL, original attach claim and campaign clock. It creates a new Python session and requires a strictly newer native `connection_generation`; it does not claim continuity of the old transport generation. This capability belongs to the authoritative main repository. External projects keep their run profiles, gameplay decisions and acceptance evidence in their own repositories.

## Existing native contract

`native_bridge/src/bridge.cpp` keeps `WorkerState` outside the reconnect loop. `ConnectToHost` opens the original fixed pipe; `RunConnectedSession` increments the connection generation and sends a new hello. Closing the Python named-pipe endpoint does not inject, unload the DLL or stop that worker. This package consumes that existing lifecycle, without a native build or DLL replacement. The reviewed frozen patch3 artifact is described in [nullable saved-character qualification](nullable-saved-character-scope-1.20.0.3.md).

The frozen patch3 source includes the pending-context reader and reply command. The exact-build reuse ledger covers the events and pending-context manifests, and the Python contract accepts the exact patch3 build/provenance. The earlier nine native qualification scopes did not independently qualify pending-context live behavior. Compiled support and passing Python fixtures therefore do not establish that a particular live mail query or reply succeeds.

## Closed tools

| Tool | Inputs | Result boundary |
| --- | --- | --- |
| `ck3_resume_profile_bridge_v1` | None | `resumed_snapshot_verified` only after fresh hello, generation, paused campaign and independent clock checks |
| `ck3_query_profile_pending_interaction_v1` | `pending_interaction_id: int`, `expected_revision: int` | Guarded read of the existing typed context; an unavailable context remains unavailable |
| `ck3_reply_profile_pending_interaction_v1` | `accept: bool`, `pending_interaction_id: int`, `expected_revision: int` | One existing native reply, followed by bounded reads confirming that the old pending instance cleared/replaced while date and pause remain unchanged |

All tools reject unknown arguments. PID, executable, build, pipe, session, DLL and run identity come from target-side frozen evidence/profile data. Query/reply require a paused map-ready frame and the full positive int32 pending ID, with exact public revision. Their real driver retains its sender, native revision, date, provenance, auto-notification and command-validator checks. Exposing reply adds no accept/reject policy and does not infer war membership, money transfer or other mechanical outcomes from a transport ACK.

## Operator handoff

1. Keep the game paused and the existing profile/guard/lease valid. Make the old endpoint's **last profile receipt** a successful `ck3_take_profile_native_snapshot_v1` call. Preserve its session, generation and receipt path. A last query, checkpoint, inspect or RED receipt does not satisfy this resume preflight.
2. Normally close only the old Python client/server endpoint. Keep the CK3 process, loaded DLL and lease keeper unchanged. Do not invoke the injector or the attach tool.
3. Start a persistent official consumer with the updated main Python module and the **same original profile file and hash**. The profile schema is unchanged. Instantiate `NativeProfileService(load_profile(path))`, `create_server(service)`, and `Client(server, cache=None)`.
4. Call the no-argument resume tool once. Check its business status, new session ID, original claim/receipt hashes, strictly newer generation, exact target and unchanged paused date/speed/event/pending frame. The service obtains the original pipe from the immutable claim. It never overwrites that claim or the first attach/RED evidence.
5. Take a fresh snapshot and query the current pending ID with its fresh revision. Review the actual available typed context and applicable source contract before deciding whether to reply. If a reply is authorized, obtain a fresh paused revision and submit the explicit boolean once. Confirm the old instance clears and separately read any intended gameplay result.

Resume first verifies process creation time, executable/build, HWND/foreground, Steam client/UI process continuity and offline state, lease, crash sentinel, isolated userdir and DLL hash. Before starting an endpoint it requires one successful original attach and its latest paused snapshot receipt, with matching claim/profile/target identity. After starting it, bounded reads require a fresh generation and the same paused campaign state, with independent native clocks before/after. This entry point supports the original-attach handoff; it does not search arbitrary pipes or reconstruct a missing evidence chain. A later resume from a resumed session is outside this contract.

Once an endpoint start is attempted, any failure is retained as RED, closes that new endpoint and consumes the service's one-shot result. Repeating resume or attach on that service does not reconnect or inject. It never restarts CK3, replays a reply, resets elapsed simulation days or uses GUI/OCR input. The operator must preserve failures and investigate before any further recovery.

With official `Client(..., cache=None)`, `list_tools()` returns a result whose tools are in `.tools`; `call_tool()` returns a raw result. Check `.is_error` and then `.structured_content` business status. An ACK or lack of a Python exception is not success. A persistent caller must keep the endpoint open; changing files on disk does not register new tools in an existing server.

## Qualification and limits

Focused profile fixtures cover successful original-pipe handoff, new generation/session, immutable claim/old evidence, invalid identity/clock/lease/crash/artifact rejection before endpoint creation, stale/late hello, post-read failure, query drift/unavailability, strict reply arguments, delayed readback, single submission on timeout/rejection, and official uncached MCP schema/result behavior. They make no live process or desktop calls. The existing real-driver pending-context Python suite also passes; no native production source, bridge DLL, policy or pause controller changed.

Commands from the repository root, with `ck3_autonomous_player/src` and `tools` on `PYTHONPATH`:

```text
python -m unittest discover -s tools -p test_ck3_native_profile*.py
python -m unittest discover -s ck3_autonomous_player/tests/unit -p test_pending_character_interaction_context_v1_bridge.py
```

The work package records 32 profile tests and 25 existing pending-driver tests passing. Initial fixture failures from uncached SDK return-shape assumptions and an overly short fake-provider deadline remain in ignored receipts; they were corrected without expanding production behavior. `_runtime/native-profile-resume-qualification-001.json` binds the final source/tests to their captured outputs and unchanged native epoch. This is scoped Python qualification, not a fresh native all-target build, a live reconnect/query/reply result, a complete interaction-effect preview or a completed century campaign.

## Operator-owned live regression, 2026-10-02

The operator exercised Python consumer `0700e17546d27d76fa1e37085d3d69db642c4988` against exact CK3 1.20.0.3/build25652598 with the already loaded, qualified patch3 DLL. Normal old-endpoint shutdown and new-endpoint resume kept the same game PID/DLL, original profile/claim and paused campaign. The new session reported native generation 1 to 2, independent clocks both `date_raw=77629680`, `speed=5`, `paused=true`, and the same pending mail. Resume reported `uses_injection=false`; this was an endpoint restart, with no game restart or new DLL attachment.

| Frozen project-owned receipt | SHA-256 | Observed result |
| --- | --- | --- |
| `0001-resume.json` | `16cb182fe332649981606ff9ad01897311b8fd6da39b9921a009faad7135a7c2` | `resumed_snapshot_verified`, new session/generation, unchanged paused state |
| `0003-pending-query.json` | `8735e9345becb0cf692020bd3acf6b8f26c3c518f806ba172770f165851a9233` | `native_pending_query_verified`, context available with partial semantics |
| `0004-pending-reply.json` | `ee77cfe0673bd84beea26271ee4aa89effee8031b9e6440ccf4dbd47cc596550` | `native_gameplay_postcondition_verified`, old instance cleared, revision 2 to 3, paused date unchanged |

A fresh snapshot confirmed the cleared instance. The operator then retained a complete same-date checkpoint and resumed normal simulation; cumulative elapsed days continued from the original baseline. Raw receipts, saves, project decisions and original RED remain in the independent project; main retains the reusable recovery method and these evidence identities. This documentation update changes neither the running Python consumer epoch nor native artifacts.

The available query established definition/roles, local routing, a 59-day remaining deadline, and accept/reject legality. It retained `interaction_semantic_decision_ready=false`: target type `war` was available, but its typed identity was unavailable with `generic_scope_payload_identity_not_closed`; structured exchanges/effect preview and special outcome terms were also unavailable. A present target type is not a verified target identity. Available zero actor costs explicitly described `application_timing=on_send` and `pending_payment_state=already_applied`; they do not prove that a later assistance arrangement is free or has no conditional payment.

The operator used a separately reviewed exact source contract and an immutable same-instance save to decide the explicit reply, without changing readiness or weakening the typed query/command guards. Clearing the old pending instance confirms that reply's bounded business postcondition. War participation, obligations, combat and eventual payment require separate evidence; they are not established by these generic receipts. This observed recovery/query/reply pass does not establish complete effect preview, universal interaction support or century stability.
