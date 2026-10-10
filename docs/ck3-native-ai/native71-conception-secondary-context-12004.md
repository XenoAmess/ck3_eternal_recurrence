# Native71: conception secondary context, actual 1.20.0.4

This source and conditional observer packet follows the actual pair-value
provider `2B95670`. It closes the receiver and AL return of its reached
`2BD89A0` helper, using CK3 1.20.0.4 / Steam25734779 and the retained EXE SHA
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
Names below deliberately identify the two stores as A and B. Their domain
names and the writer/lifetime of the final signed field are unproved.

The actual parent is the Root packet
[pair-value-provider-2B95670.json](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-17/root-literal-source/pair-value-provider-2B95670.json).
The reached helper has no containing `.pdata` row. Its extent was established
from its actual entry, every local branch and the true RET, rather than an
adjacent function union: `[2BD89A0,2BD89E7)`, 71 bytes, RET at `2BD89E6`, no
calls or writes. Source acquisition was cache-first with the common O_EXCL
mapper, in disjoint 16, 48 and 8 byte batches. Only 72 new frozen-image bytes
were acquired; the final extra byte is excluded from the body. No old EXE,
image hash, section scan, old FIRST, Game or Git operation occurred.

The complete source and frozen semantic contract are
[HELPER-SOURCE-CLOSED.json](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-54/HELPER-SOURCE-CLOSED.json)
and
[RESOLVER-CONTRACT.json](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-54/RESOLVER-CONTRACT.json).
The source-first plan and diagram are
[SOURCE-PLAN-CLOSED.json](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-54/SOURCE-PLAN-CLOSED.json)
and
[SOURCE-GRAPH-CLOSED.md](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-54/SOURCE-GRAPH-CLOSED.md).
Their check verifies the record structure and input-file identity; manual
instruction/dataflow review establishes the semantics described here.

## Actual receiver chain

| Level | Complete DWORD ID read | Store pointer slot | Fallback pointer slot |
| --- | --- | --- | --- |
| 1 | Character `+B4` | `5D1E2F8` (A) | `5C67670` (A) |
| 2 | Level 1 resolved object `+4B8` | `5D1E300` (B) | `5D1E2E0` (B) |
| 3 | Level 2 resolved receiver `+98` | `5D1E2F8` (A) | `5C67670` (A) |

Level 1 and 2 are the actual parent instructions before calls `2B96241` and
`2B962BD`. Level 3 is the complete helper body. The last lookup uses the
same A store/fallback as level 1, rather than a new third store.

Each lookup masks the low 24 bits only to select an index. It compares that
index unsigned against DWORD `store+2C`, reads the table at QWORD `store+20`,
and reads the entry pointer at `table + index*16 + 8`. It accepts the pointer
only when nonnull and DWORD `object+8` equals the entire requested generation
ID. A null store, index at/beyond the count, null entry or generation mismatch
selects the actual native fallback. That known fallback is distinct from an
observer read failure. A failed copy yields no predicate result.

The parent loads both fallbacks up front. The helper loads its fallback only
on a failed lookup. The independent observer copies a fallback only when that
lookup actually needs it; it records the resolved/fallback provenance. It
uses the existing application-thread current household frame, with no stored
object pointers or IDs carried across frames.

## Return and route consumer

At `2BD89DC`, `CMP DWORD[resolved A object+7D8],0` is followed by `SETG AL`
at `2BD89E3` and RET at `2BD89E6`. The raw input is signed int32. Positive
returns AL=1; zero and negative return AL=0. Only AL is defined as the boolean
result. The remaining RAX bits are not a boolean return ABI.

The parent tests AL at `2B96246` and `2B962C2`. First true short-circuits
directly to the alternate relation route `2B96378`. If first is false, second
true selects that same route. Only both false continue at `2B962CA` into the
normal relation predicates. This packet adds no interpretation or duplicate
qualification of those separately owned family/relation predicates.

## Conditional leaf and focused result

The candidate files are
[conception_secondary_context_12004.hpp](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-54/candidate/include/xar_bridge/conception_secondary_context_12004.hpp)
and
[conception_secondary_context_12004.cpp](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-54/candidate/src/conception_secondary_context_12004.cpp).
They bind the exact version/SHA and the Root-owned read callback/image base.
For an already resolved current household Character and complete expected ID,
they copy the three qualified paths, expose the signed raw and optional
alternate-route predicate, and retain read failures as unavailable. They do
not call the original helper/provider or produce a probability/date.

`SelectConceptionSecondaryRelationPath12004` preserves native short-circuit
information: known first true needs no second input; unknown first remains
unknown, and known first false requires the second input. Root should avoid
reading a second role solely for this route once the first role is true.

One new focused qualification compiled the candidate into a small standalone
fixture DLL and compared it with the exact 71-byte helper executed over owned
buffers. Only its two RIP displacements were relocated to synthetic store and
fallback slots; every opcode, member offset, branch and signed comparison
remained unchanged. Eleven actual-body comparisons passed: int32 extrema,
negative/zero/positive values, generation mismatch with identical low24 bits,
index equal to count, null entry/store, and first/second parent lookup
fallbacks. The same qualification checked unavailable raw input and native
route short-circuit behavior. Both paths left owned input bytes unchanged.
Evidence is
[FOCUSED-VALIDATION.json](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-54/FOCUSED-VALIDATION.json).
This is an offline comparison, not a current household observation or CK3
runtime acceptance. No Game process or SDK was used.

Root owns adoption into shared build/driver/serializer and any current-frame
runtime read. This worker made no repository/core/Git/Game mutation. A new
household input from this leaf will close only this provider branch input;
it does not establish the complete provider first qword, eligibility,
probability, monthly schedule, pregnancy, birth or succession result.

The small source/contract records are retained for review on 2027-04-08.
Current-source protection expires on 2026-10-17; it is not automatically
renewed. The standalone fixture DLL is a rebuildable build artifact due for
review on 2026-10-24, and build logs are derived records due for review after
48 hours. Shared raw spans remain under the Root coordinator's common ledger.
