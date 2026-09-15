# Active scheme precondition and command binders v1 private

Status: **static-ready; thin mailbox/backend and paused live receipt remain**.
This SCHEME10 package supplies the exact CK3 `1.19.0.6` callbacks required by
the SCHEME9 paused-live glue. It adds no public command, schema, or MCP surface.

## Bound native transaction

`active_scheme_precondition_command_binders_v1_private.hpp/.cpp` owns the
SCHEME9 glue state at a stable address and supplies SCHEME6/7 with production
callbacks for:

1. a full-generation CharacterID resolver through `module+0x570C130`, with
   low-24-bit slot, high-8-bit generation, object `+0x18` round-trip, fallback
   rejection, and same-paused-frame double reads;
2. the SCHEME7 character-interaction database getter, stable-key hash, and
   loaded-definition lookup calls;
3. the embedded command manager at `module+0x57621F0`, exact submitter, and a
   transaction-only route fingerprint tied to the paused proof epoch;
4. `CCharacterInteractionContext` construction, starter selection, refresh,
   finalize, and the exact complete validator;
5. `CSendCharacterInteractionCommand` construction, primary/secondary vtable
   and copied-context identity checks, one `0x0E` submit call, copied-context
   release, and original-context release.

The wrapper arms a copied request only for one synchronous SCHEME9 operation.
Every callback also requires the caller-provided current thread ID to equal the
application-main thread ID. Definition, character, route, context, and command
pointers are call-local leases; the state never publishes or caches them.

The command-manager and context generations are deterministic
transaction-local fingerprints. They detect drift inside one paused request;
they are explicitly not native or monotonic engine generations.

## Native precondition

For `start_murder_interaction`, the reader verifies the exact stock source and
runtime shape:

- definition option rows at `+0x2548`, signed count at `+0x2554`, exclusive
  byte at `+0x2A4E`, four rows of stride `0x7D0`, and numeric flag identifier at
  row `+0x3A8`;
- authored order `agent_focus_balance`, `agent_focus_success`,
  `agent_focus_speed`, `agent_focus_secrecy`;
- every numeric flag round-trips through the lookup-only script-identifier
  table; and
- context byte vector `+0x300/+0x30C` contains exactly one selected value that
  matches the request after refresh/finalize.

`sway_interaction` instead requires zero option rows, a nonexclusive definition,
and an empty selected vector. The reader then invokes the exact complete CanSend
validator `0x2C43F00`. A true result closes shown, validity, and
`can_start_scheme` for this exact constructed candidate. A false result remains
RED as `native_complete_validator_rejected`; the binder does not invent which
internal leaf failed.

Success chance, maximum success chance, and secrecy previews remain
`explicitly_unavailable`. This is an accepted SCHEME5 value and records the
absence of a separately proven preview ABI without fabricating numbers.

## Exact evidence and verification

The machine-readable contract is
`active_scheme_precondition_command_binders_1_19_0_6_abi.json`. It freezes the
EXE/source hashes, stock interaction anchors, twelve complete native function
spans, command vtable entries, context/command sizes and option layouts. The
verifier takes an explicit game root, so it does not depend on one user's
installation path:

```console
py ck3_autonomous_player/native_bridge/research/verify_active_scheme_precondition_command_binders_1_19_0_6_abi.py --game-root <authorized-game-root>
py -O ck3_autonomous_player/native_bridge/research/verify_active_scheme_precondition_command_binders_1_19_0_6_abi.py --game-root <authorized-game-root>
py ck3_autonomous_player/native_bridge/research/test_active_scheme_precondition_command_binders_v1_private.py
py -O ck3_autonomous_player/native_bridge/research/test_active_scheme_precondition_command_binders_v1_private.py
```

The `/W4 /WX` fixture covers sway and murder GREEN, exact starter-ID mapping,
validator and starter RED, thread/reentrancy rejection, release counts, fresh
receipt, and a repeated request with only one native submit. These results are
static/fixture evidence. No CK3 process was started.

## Remaining candidate step

The only remaining implementation seam is a thin private application-main
mailbox/backend that translates the SCHEME8 raw stages into these wrapper calls.
It must freeze the candidate request and checkpoint, preserve raw RED artifacts,
expose no public schema/MCP change, and accept success only after the fresh
active-scheme receipt. DLL/injector/manifest hashes and paused sway/murder live
artifacts belong to that candidate run.
