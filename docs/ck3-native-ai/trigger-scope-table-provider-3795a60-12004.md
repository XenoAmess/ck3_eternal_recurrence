# Actual trigger scope-table provider at3795A60

The readonly leaf copies the scope-table header and one selected descriptor
callback pointer for the existing42/35 CanSend and09 Lifestyle callers. Its
inputs use35's generic original query frame. It introduces no prisoner role
substitution, active getter, constructor, class traversal or validator call.

Exact source is CK3 1.20.0.4 / Steam25734779, EXE SHA-256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
The complete171-byte body occupies `[3795A60,3795B0B)`, cached pdata
ordinal189201, body SHA-256
`74f3ba610c253e1afad81379d178ae120fc3862dc1065a03907e0b439a3bccde`.
It was reused from the current .4 source cache documented by
`Z:/ck3_mod_rewrite_process_assets/g2-migration-20261007/m7-crown-cooldown-12004/native/character-scope-registry03/FAMILY-MAP.json`.
This package acquired zero new native body bytes. No old executable,
full executable/hash/PE/pdata scan, SDK or game operation was performed.

The reviewed source, source-before-code freeze and graph are
`D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-30e/SOURCE-CLOSED-CONTRACT.json`,
`SOURCE-INPUTS-FROZEN.json` and `research-graph.md`. The graph is generated
from that directory's `research-plan.json`; initialization and validator
result edges remain unknown.

Both returning paths put the static inline table identity
`module+54F2AF0` in RAX. The fast path compares signed DWORD
`module+5D7A1D4` with the actual calling thread's TLS epoch at
`[GS:58] -> QWORD0 -> DWORD+10`. The slow path calls4223A84, tests
guard==-1, invokes initialization through IAT4938598 and singleton54F2B08
slot20, registers43A1E10 through4223F24, and calls4223A24. The three
direct children were reported to02 for separate ownership. Their
semantics and the dynamic allocator/initializer targets are not guessed.
Complete pointer return source does not qualify initialized state or
prove that the actual getter returned in the current query.

The actual42 caller has these literal inputs:

| Instruction | Consumption |
| --- | --- |
| 372E068..372E070 | Original primary-scope WORD is zero: bypass table provider and root validator |
| 372E079..372E089 | Call3795A60; compare signed table DWORD+C with copied zero-extended WORD kind |
| 372E08B..372E09F | Call the same provider; select QWORD table0 + kind*80 when signed count>kind |
| 372E0A4 | Otherwise use static fallback descriptor module+54F5310 |
| 372E0A7..372E0AE | Copy descriptor QWORD+10 and call it with original primary-scope token |

The descriptor stride is **80 decimal / 0x50**, matching `(kind*5)<<4`.
The selected callback pointer is an input identity. Its address alone
cannot identify a dynamic class/body, validate the scope, or provide a
returned Boolean. The reader therefore publishes no validator output.

`ReadTriggerScopeTableProvider3795A6012004(access,frame,copied_root_kind)`
uses the frozen generic `SourceLeafReadOnlyAccess12004` and
`SourceReadFrame12004`. The frame is copied unchanged, including its
original identity/domain/date/revision/sequence/epoch. The frame guard
admits raw reads and grants no callback/initialization result.

The raw observation independently preserves the guard DWORD, source
return table identity, data QWORD0, capacity DWORD8, signed count DWORDC,
original copied WORD kind, selected descriptor and QWORD validator+10.
Unknown fields are nullopt; copied null pointers remain optional0.
Known kind0 avoids all unused table reads. Unknown kind still permits
independent header copies without selecting a descriptor. Signed negative
count and count==kind take the source fallback; an unread count does not.
Unread data/capacity does not erase a known fallback pointer. A positive
selected-table branch with null/unread data keeps the descriptor unknown.
The copied descriptor validator pointer may be zero without being invoked.

At most five successful scalar copies and their bookends are read, with
no collection scan or class enumeration. The observation retains raw
first copies and an independent unchanged-copy fact. Failed or changed
copies stay partial. `initialized_state` and
`descriptor_validator_returned_raw_u8` remain unknown, while native return
observation, initializer closure and callback execution remain false.
Raw header completeness does not promote an initialized table or CanSend
or Lifestyle truth.

The header/implementation/new no-main cases form a shared candidate for
42/35/09's existing query path. The new export
`VerifyTriggerScopeTableProvider3795A60ConnectedCases12004()` contains16
focused raw-copy cases for10's sole first connected compound. This worker
compiled or executed no fixture, old Person/release/vector test, native
provider or runtime getter. Source span/return-pointer closure is separate
from future central execution and actual paused query evidence.
