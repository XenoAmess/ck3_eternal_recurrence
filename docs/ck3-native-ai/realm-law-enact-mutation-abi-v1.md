# Realm law enact mutation ABI v1 (private exact-build freeze)

## Status and evidence boundary

This private freeze closes the static native mutation blocker for CK3
`1.19.0.6`. It is bound to `binaries/ck3.exe` SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`,
file size `95206008`, preferred base `0x140000000`, and image size
`0x5C2D000`.

The machine-readable evidence is
`ck3_autonomous_player/native_bridge/research/realm_law_enact_mutation_v1_abi.json`.
The Python verifier checks the whole executable identity, PE metadata, instruction
span hashes, exception-directory entries, relative calls, relocated pointers,
native registry numbers, and native strings. The C++ verifier applies the same
fail-closed proof to a supplied image reader. It hashes only relocation-stable
instruction bytes and checks live image pointers against the supplied module
base.

This is `static-ready native ABI`. No CK3 instance was started. Queue acceptance
remains ACK/pending until a later paused snapshot proves the effective law,
resource delta, and succession shape.

## Receiver and final legality

`GuiLaw` uses the Microsoft x64 convention: `RCX` is `this`, the first two fields
are a `CLaw*` at `+0x00` and a captured played-character identity pointer at
`+0x08`, and Boolean results return in `AL`. `0x3DDF770` compares the captured
identity to the current full generation-bearing ID at module `+0x4FE7EE0`,
resolves the character through storage `+0x570C130` with fallback
`+0x570C138`, requires `CCharacter+0x1B8`, rejects an invalid or already-active
law, and calls the engine-final evaluator:

```text
0x2C7D930(CLaw* law, CCharacter* actor, void* error_sink) -> AL
```

The command-side validator `0x2C7DAA0` has the same register contract and reaches
that evaluator. Native glue must resolve identities again and repeat this final
gate immediately before submission. Raw `CLaw*`, `CCharacter*`, containers, or
prior legality results cannot cross frames.

## Enact, command dispatch, and mutation

The exact native path is:

```text
Enact registration 0x7DF870 -> callback 0x3DE0880
  -> popup builder 0x3DDF8C0
  -> CEnactLawConfirmationPopup confirm slot +0x48 = 0x3DDEEC0
  -> submit 0x973E00(manager module+0x57621F0, command, flags 0x0E)
  -> clone slot +0x40 = 0x25EC5B0
  -> locked queue 0x341D990
  -> primary execution slot +0x38 = 0x803620
  -> framework gate 0x26B2750 -> router 0x26B2890
  -> secondary slot +0x08 = 0x25E2640
  -> 0x260ACB0(character, law, 7, null)
  -> logical apply 0x25FF0F0
  -> finalizer 0x25FEFA0
```

`0x3DDEEC0` constructs the engine-owned `CAddLawCommand` as a `0x30` byte
object. Its primary vtable is module `+0x4323730`, its secondary vtable is module
`+0x4323700` at object `+0x18`, its full actor ID is at `+0x20`, and its target
`CLaw*` is at `+0x28`. Calling `0x260ACB0` directly would bypass the command
validator, clone, queue, and engine dispatch. The supported integration boundary
is to build the exact command on the application main thread and submit it
through `0x973E00` after a fresh native preflight.

The observed constant `7` and submit flags `0x0E` are frozen as instruction
evidence; this document does not assign guessed semantic names to those values.

Within `0x260ACB0`, the engine creates a transient context over the character law
collection and selects an existing entry whose value at `CLaw+0x38` equals the
target's value at `CLaw+0x38`. The exact meaning of that field is not named here.
`0x25FF0F0` removes and compacts the old entry in
`[0x25FF1A2,0x25FF1F5)`, inserts the target in
`[0x25FF22F,0x25FF25B)`, and marks the change at `0x25FF267`.
The finalizer emits native registry token `0x328A`, registered as
`law_changed`.

## Vtables and serializer

| Object / slot | Exact target | Role |
| --- | ---: | --- |
| `CAddLawCommand` primary `+0x30` | `0x25E2690` | validator adapter |
| primary `+0x38` | `0x803620` | framework execution adjustor |
| primary `+0x40` | `0x25EC5B0` | `0x30` byte heap clone |
| primary `+0x48` | `0x25EC630` | native class key `0x2FF3` |
| primary `+0x80` | `0x25E26E0` | serializer |
| primary `+0x88` | `0x25E2780` | field deserializer |
| secondary `+0x08` | `0x25E2640` | actual executor |
| popup primary `+0x38` | `0x3DDEF20` | confirm-time re-evaluation |
| popup primary `+0x48` | `0x3DDEEC0` | command construction and submit |

The serializer writes command `+0x20` under tag `0x6EC` (`character`) and the
persistent target-law identity reached from `+0x28` under tag `0x2FF2` (`law`).
The deserializer span `[0x25E2780,0x25E2849)` consumes those same tags. Native
registry entry `0x2FF3` names the command `add_law`.

## Verification

Run the read-only executable verifier in both Python modes:

```console
py ck3_autonomous_player/native_bridge/research/verify_realm_law_enact_mutation_v1.py --exe "Crusader Kings III/binaries/ck3.exe"
py -O ck3_autonomous_player/native_bridge/research/verify_realm_law_enact_mutation_v1.py --exe "Crusader Kings III/binaries/ck3.exe"
```

Compile `realm_law_enact_mutation_abi_v1.cpp` together with its standalone test
under MSVC `/std:c++20 /W4 /WX`, then repeat with `/O2`. The test covers the
exact image GREEN path and typed failures for instruction drift, relocation
base drift, registry number drift, invalid readers, and failed reads.

LAW7 now connects LAW5 to this verifier and exact command boundary through the
private operation-table glue documented in
`realm-law-native-shared-glue-v1.md`. Shared CMake, bridge, schema, MCP and
application-main scheduling remain outside that private package. The next
integration step must register the glue and obtain one paused native submission
plus a later receipt. The submit return from `0x973E00` proves only that the
locked queue retained the clone; it cannot be reported as enactment success.
