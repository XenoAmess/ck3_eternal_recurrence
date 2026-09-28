# H3911 realm law active collection: first read-only native anchor

Status: `static-ready private first anchor`; no CK3 was launched for this work
package. This does not qualify a law candidate or enable a law action.

## Why this frame matters

The official H3911/raw53219928 pair identifies the played Robert character as
`29829`, with `feudal_government` and
`government_uses_crown_authority`. Its last `query-campaign-root-context-v1`
shows title 2173's first heir as 38988 while primary duchy 2141 and the other
listed titles have first heir 38822. The same driver records
`succession_expectation.risk_state=split_successors`. The 3,921 recorded
commands contain no law query or law action, and the campaign-root response has
no active law, candidate, native final legality or cost field. The split is a
reason to observe a law opportunity; it does not prove a particular enactment
is legal or valuable after cost.

Source identity is the R0321 H3911 `SOURCE-PAIR-IDENTITY.json`, whose save SHA-256
is `5EFB3B3CF3EE7368C6C12D4C984B4A0366AA8A971409165016E3DC24725A4746`
and driver SHA-256 is
`DE09EA8B3648FAE89F90E5459991BC66AE52154971948DB39C353D05EEAAEE33`.
This package only read that existing paired driver; it did not add a game date,
query receipt or new game action.

## Exact-build chain

The executable is CK3 1.19.0.6, SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
The new machine-readable contract
`realm_law_active_collection_11906_abi.json` freezes four instruction spans:

```mermaid
flowchart LR
  A[played CCharacter] --> B[+0x1B8 law context]
  B --> C[+0x200 active law collection]
  C --> D[+0x00 CLaw pointer array]
  C --> E[+0x0C signed count]
  D --> F[each CLaw +0x18 MSVC string]
  F --> G[copied active law keys]
  G -. next native research .-> H[candidate law objects]
  H -. missing .-> I[engine-final CanEnact and cost]
```

`0x260AC30` returns `CCharacter+0x1B8 -> +0x200`, or the native empty
fallback if that context is absent. `0x260ACB0` and `0x28BC040` independently
walk the collection's data pointer and signed count as an array of `CLaw*`.
`0x2C7B300` reads the law object's MSVC string at `+0x18`; its size and
capacity fields are at `+0x28/+0x30`, with inline characters or a heap pointer
at `+0x18`. The current private reader copies these keys through a supplied
read-memory callback and returns no native pointers. The value at `CLaw+0x38`
is compared to choose the old law when enacting another one, but its semantic
identity remains unknown and is not exported as a group key.

The reader lives in `realm_law_active_collection_11906.cpp`. It is not wired to
shared bridge, CMake, mailbox, protocol or MCP. The caller must still supply a
fresh full-generation played-character resolution on the paused application
main thread; this work does not add that caller. The exact span verifier ran in
normal Python and `-O`, both 4/4 GREEN. Its standalone reader fixture ran under
MSVC `/std:c++20 /W4 /WX` in `/Od` and `/O2`, both 4/4 GREEN. Fixture memory is
not a CK3 paused readback.

## Next exact input

Resolve the current H3911 law keys in a paused frame, then locate candidate
`CLaw` objects for the observed feudal crown-authority and succession groups.
For each relevant candidate, read the same-source final `can_have`, `can_pass`,
`CanEnact`, opaque failure reason and charged currency cost. LAW3's existing
two-sample source adapter can then compare the full value snapshot. A legal
beneficial action and its formal consumer remain separate later gates. No
religious law group or government matrix is included.
