# Desired gameplay pause over an independent clock MCP

The authoritative generic owner is `tools/ck3_clock_pause_mcp.py` in this
repository. It consumes the existing native clock reader, frozen-profile guard
and desktop observation backend. A project supplies only profile data and a
client adapter. No suite control implementation, native bridge change, new DLL,
attachment or restart is required. The ordinary campaign's existing client and
native session remain open and unchanged.

R8 repeatedly returned `CK3 map state is unavailable` from native pause while
independent clock reads and reviewed gameplay remained valid. That native text
merges full-snapshot, readiness and command-queue failures; it does not identify
the cause or prove a pending-mail veto. The root operator preserved each RED
and recovered through a fresh running-clock check, the existing controlled SPACE
operation and paused-clock readback. This controller moves that generic recovery
capability to its authoritative owner. It does not reinterpret or replay the
original failed native command.

## Frozen profile and tools

The profile has exactly seven fields: `schema_version=1`, `guard_profile`,
`guard_profile_sha256`, `userdir`, `evidence_directory`, `game_version`, and
`pause_shortcut_sha256`. The first six use the existing clock-profile contract.
The controller profile is a new artifact with its own SHA-256; adding the
seventh field must not reuse the old clock profile's hash. Paths are absolute
target-side configuration, never tool arguments.

From the verified `<installation>/binaries/ck3.exe`, the controller derives
`<installation>/game/gui/shortcuts.shortcuts`. The supplied SHA-256 must match
the complete bytes and exactly one assignment must bind `pause="SPACE"`.
It checks those source bytes again before an action. No project path, build SHA,
key choice, mod ID or run identity is hardcoded into the generic controller.
Current clock ABI support remains the existing exact CK3 1.20.0.2 reader.

The official MCP server exposes only three closed, zero-argument tools:

| Tool | Contract |
| --- | --- |
| `ck3_query_clock_pause_profile_v1 {}` | Guarded target, source qualification and current clock |
| `ck3_read_profile_native_clock_v1 {}` | Independent guarded native clock, no injection or input |
| `ck3_pause_profile_gameplay_v1 {}` | Desired paused state; zero or one fixed SPACE dispatch |

The shared guard verifies PID, process creation time, executable/hash, installed
build, HWND/foreground/geometry, exact isolated `-userdir`, Steam UI host and
core-client continuity, offline configuration, pinned task-bus CLI and an
exclusive lease no older than ten minutes. Any crash artifact in this userdir
rejects the operation, including during the postcondition wait. It never acquires
or refreshes another operator's lease or moves focus.

## One dispatch and actual readback

An initialized native clock must have a real played character, local player,
positive raw date, Boolean paused state and ordinary speed. Its source evidence
must identify the exact executable and the existing read-only `0x410` process
access. Source identities remain fixed during this controller session.

Already paused means zero input. Running means at most one fixed SPACE, with
before/after labeled screenshots and released SPACE/modifier checks. After the
last key-state check, a complete guard runs immediately before dispatch. Input
delivery alone is an ACK. Success requires guarded independent reads observing
`paused=true`, nondecreasing raw date and the same local player, including after
the evidence capture. The wait is bounded to five seconds and retries only
reads. SPACE is an engine toggle; observations before dispatch do not make it
atomic with a concurrent engine state change. The final readback determines the
business result.

Every result uses its own `ck3.clock-pause-profile-receipt.v1` identity and
evidence directory. Success is `gameplay_pause_verified`, never a fabricated
native bridge status. Any failure returns or preserves RED. Before calling the
input driver, the controller consumes the dispatch in memory; timeout, guard
failure, unresolved input or receipt-write failure cannot reopen it. After an
attempted input failure, subsequent pause calls return the retained failure
without dispatch. Clock reads remain available if their guard passes. A failed
receipt write is not claimed to have produced an evidence file. Only a verified
result successfully written to disk clears the consumed state for a later pause.

## Ordinary policy consumer

The optional public entry is
`await native_campaign_autoplay.run(existing_native_client, config, pause_provider=controller_client)`.
Omitting `pause_provider` keeps the original native pause path. The provider
uses only its two fixed inspect/pause tools. Resume, event query/choice, speed and
save still go through the existing native client and retain their strict
contracts. There is no automatic fallback or replay after controller RED.

The policy preserves complete controller request/response receipts separately
from native receipts. Its handshake requires a distinct server session and
stable controller profile hash. The controller target's PID/HWND/create time,
build, EXE path/hash, userdir and version must agree with the guarded native
inspect and actual bridge hello. After successful independent clock proof, the
policy waits only on native snapshots until they also show paused state at or
after that actual clock date. This does not replace or impersonate the native
session. A thin queue adapter may implement `call_tool` by forwarding to the
root's existing persistent official client; it must not rewrite identities or
statuses.

```python
from mcp import Client, StdioServerParameters
from mcp.client.stdio import stdio_client
from native_campaign_autoplay import run

parameters = StdioServerParameters(
    command=qualified_python,
    args=[str(authoritative_main / "tools/ck3_clock_pause_mcp.py"),
          "--profile", str(frozen_controller_profile)],
    cwd=authoritative_main,
)
async with Client(stdio_client(parameters), cache=None) as controller_client:
    result = await run(existing_native_queue_client, config,
                       pause_provider=controller_client)
```

Keep this context alive for the bounded policy attempt. Exiting it closes only
the independent controller transport. It must not close, restart or attach the
existing native campaign client. Disable client response caching for fresh
clock observations. The command is a deployment example, not an MCP tool
accepting arbitrary processes or commands.

## Qualification boundary

The package passed 48 offline tests:
`python -m unittest test_ck3_clock_pause_mcp test_native_campaign_autoplay test_ck3_native_clock_reader`
from `tools`. They cover a real official MCP controller client consumed by the
policy, zero-input already-paused/guard rejection, delayed true state, unknown
clock/key state, source ambiguity/mismatch, one-input timeout, crash after
input, final-key-check foreground change, failed receipt writes without replay,
target/session mismatch, distinct receipts and default native compatibility.
The production fixed driver is tested to call only `press("space", presses=1)`.

A separate read-only source qualification read the installed 29,312 shortcut
bytes, SHA-256
`d2aa3a6f3a9de9729d778e240920e5a15f724d1f5b0adee5861ef6831797cd66`,
and the unique binding at line 12. The reader SHA-256 was
`ce96b681e035d6378b685f61db448b101251d26262a475c029684995b7905ff3`;
its authoritative source contract matched EXE SHA-256
`ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d`.
These are recorded qualification evidence, not constants accepted for every
future installation. No live action or new native build was performed here;
prior full-build RED limitations remain. The package does not prove campaign
length. `open_kaishek` prevalidation is not applicable to Python MCP transport,
fixed desktop input and source qualification; existing clock ABI fixtures were
included instead. Live acceptance requires the root's frozen profile, unchanged
campaign identity, original receipts and actual paused-clock proof.
