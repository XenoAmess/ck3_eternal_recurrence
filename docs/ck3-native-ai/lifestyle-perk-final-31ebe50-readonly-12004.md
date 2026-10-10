# Lifestyle selected-perk tail predicate, CK3 1.20.0.4

The new reader connects the literal `288B1B0 -> 31EBE50` current selected-perk
predicate. It projects guarded source conditions and returns `optional<bool>`.
It obtains source-model false on the two closed rejection paths: the selected
perk is already owned, or a required perk is absent. The reached compiled-trigger
output remains unavailable when its actual producer or witness is unavailable.
This implements a partial current predicate, not full `can_select` qualification.

The held build is CK3 1.20.0.4, Steam build 25734779, EXE SHA-256
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`.
`SOURCE-31EBE50.json` records one new finite 682-byte capture of the actual
`.pdata` interval `[31EBE50,31EC0FA)`, ending at RET `31EC0F9`. Its body SHA-256
is `5824a73f2a9b79f7b699e63b9c72c53ec216c8d741efb61bab76ede133cd3a79`.
The caller is 16d's independently held 113-byte `288B1B0` source. No old EXE,
whole EXE hash, section census, native validator or game call is performed here.

## Literal ABI and demand

`288B209` loads selected Perk from original command `+28`, and `288B219` tail
jumps with RCX=selected Perk, RDX=resolved Character, R8=null diagnostic writer.
R8 retains pointer semantics in the public API. A nonnull writer is outside the
projected scope and returns unavailable before reads. The incoming command in R9
is unused on the truth path; its later cleanup overwrite is not a truth input.

The saved Character is real source data. `31EBE55` stores incoming RDX at entry
RSP+10. Seven pushes put RBP at entry RSP-128, so RBP+138 is that same saved slot.
`31EC034` passes its address to `9D78D0`; it is not an uninitialized argument.

1. Fresh `2919340(Character)` returns the owned collection identity, then
   `A11CC0(collection,&selectedPerk)` supplies the initial membership condition.
   A true membership condition immediately returns false.
2. Perk QWORD `+448` and signed DWORD `+454` describe prerequisite pointer
   occurrences, stride eight. Each occurrence retains its full QWORD, including
   zero and duplicates. Each iteration performs a fresh getter and membership
   demand. The first absent prerequisite immediately returns false.
3. After admission, 18c projects the source-defined Character context, with a
   fresh Character `+18` DWORD and a definition mask. This storage is owned
   source-equivalent input; it is not an observed native stack context.
4. The reader calls 09d's pure adapter for the literal `37998D0(Perk+80,context,0)`.
   Only an available source-returned byte is canonicalized with `byte != 0`,
   matching `31EC060 TEST AL`. Context readiness does not supply that byte.

A fifth, optional software output points to 09d's typed truth observation. The
reader resets it at entry and copies the same reached 09 result once, without a
second demand. Source rejections and failed context projection leave it empty.
The admitted nonzero Perk identity identifies a reached observation. This
companion carries already-read raw vtable and `+58/+60/+C8` slot facts for later
precise source work; the slots are not getter or evaluator outputs. The native
R8 diagnostic pointer keeps its separate fourth-argument semantics.
The copied child-frame scope address identifies temporary software storage,
whose lifetime ends on return. It must not be dereferenced later or reused as a
natural stack context. Copied scalar fields and native receiver/slot facts retain
their recorded current-query meaning.

The `2919340` nonnull-extension branch and supplied actual same-thread TLS fast
branch reuse 36c. Missing TLS or its initialization path stays unavailable.
The membership algorithm is 27c's unchanged full-QWORD `A11CC0` reader, including
the literal reloaded-end comparison. Its adapter sets only the actual key field;
unused M4 frame metadata remains zero and is never a natural-history claim.
The exact-build binding is inherited from 16d's qualified input carrier.

The existing M5 collection ceiling of 512 also bounds copied prerequisite
occurrences. Negative extents, over-bound extents and failed reads stay
unavailable. A finite caller callback remains responsible for its real shared
read/byte guard; exhaustion never supplies a false condition.

## Current truth frontier

The null diagnostic path at `37998F6` tail jumps to `372DF10`, which always calls
`372E000`. There is no empty-trigger shortcut that supplies true. The reached
dynamic virtual producer at `+C8` needs its actual receiver/target contract and
qualified returned-byte evidence. Missing producer evidence or an absent current
query source frame keeps the final optional truth unknown.

The nullable frame companion is copied from an existing accepted query. The
reader does not invent frame identity, snapshot confirmation, game date or other
metadata from the projected context. Early source rejection does not demand
that later frame. Source projection, input readiness and a fixture do not prove
live native execution or complete positive `can_select` behavior.

## Validation and integration

The global no-main export `RunLifestylePerkFinalNaturalFocus12004()` supplies eight
new connector cases. They cover writer-pointer scope, missing TLS, membership
bound, prerequisite rejection, independently fresh getter failure, legal zero
and duplicate keys, negative extent, and context-ready but unavailable truth.
16d owns the distinct connected fallback-Character/owned-Perk rejection case.
No old 62 Army case or generic 27 M4 export is replayed.

Root delegated the sole new M5 compound build and execution to 16. Its actual
`continuation-16d/root-first/compile-fix-retry01/RESULT.json` records exit zero for
the only native fixture run, with all nine new fragments completed. This includes
the eight new 62c cases, whose production/header/case pins remained unchanged.
The initial 22 compiler invocations failed before linking or running; the
necessary retry used 13 invocations, retained ten successful objects and linked
once with `/std:c++20 /W4 /WX`. The original `root-first/RESULT.json` remains RED
history. The separate Python export ran once, passed 24 new cases and consumed
the unchanged production wire. Worker 62 compiled and ran nothing.

The amended 18c header adds explicit software alignment padding, preserving the
native raw extent, defined mask and API. Other retry amendments concern typed
fixture literals, progress flushing and a required compile-only transport TU.
The actual Defender receipt reports `settings_failed`: reused object provenance
outside the retry build was rejected before a settings call. The permanent EXE
exclusion remains pending independently of the fixture result.

Production needs the new 62c TU, 36c getter, reused 27c reader, 18c/48c pure
projection and 09d's truth adapter dependencies. These results establish the
implemented source rejections and nullable boundaries. The descriptor callback,
dynamic `+58`/`+60` outputs and final `+C8` returned byte remain unqualified, so
complete positive `can_select` and live behavior remain unknown. Root owns
repository adoption and shared wiring.

The external package retains its exact source proofs, dependency pins, candidate
freeze and patch. Its four MiB peak is a suballocation of Root's existing manual
20 GiB parallel budget. Active inputs receive a dated seven-day review, without
automatic renewal; obsolete derived copies follow the common storage policy.
