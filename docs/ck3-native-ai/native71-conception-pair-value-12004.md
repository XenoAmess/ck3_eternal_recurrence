# Native71: actual conception pair-value inputs (1.20.0.4)

Recorded 2026-10-10 / 2026-W41. Exact build is CK3 1.20.0.4, Steam25734779,
retained executable SHA-256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
The complete top-level provider source and its base arithmetic stage are closed.
An independent read-only leaf supplies seven loaded numeric inputs and reproduces
the base stage. Complete provider output, live input availability, probability,
date and the M7/G2 lifecycle remain open.

This external candidate follows the actual scalar consumer in
[current first-heir pregnancy](current-first-heir-pregnancy-entry-12004.md).
It changes no shared driver, service, public serializer, build manifest or
progress index. Root owns repository integration.

## Actual source and ABI

The existing actual664B caller `[0x2929B40,0x2929DD8)` calls provider
`0x2B95670` at `0x2929C2B` with RCX=&caller stack50, RDX=first validated
Character, R8=second validated Character, R9D=3 and fifth argument0. The first
Character has nonzero native sex byte and the second zero, as already established
by that caller. Provider source is actual3877B `[0x2B95670,0x2B96595)`, unwind
RVA52A99D4, supplied once by Root. Its900 decoded instructions have no unresolved
outgoing jumps and one RET at2B9649B; trailing cold branches rejoin this body.

The provider preserves output in RDI, first in R14, second in R13, mode in EBX
and fifth argument in R15. Fifth comes from entryRSP+28 (providerRBP+250).
Zero writers and final writer2B9647B write exactly one Q64 to the caller-owned
output address. RAX returns that same address. There is no second result field.
The caller reads only Q64 at stack50, and its TEST/JE2929C35/C38 rejects exactly
zero. A negative value is not rejected at that gate. Later scalar/modifier
arithmetic and signed clamps are separate.

Root's retained source is
[pair-value-provider-2B95670.json](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-17/root-literal-source/pair-value-provider-2B95670.json),
span SHA-256 `ed8e19f51650aa5a2d778ed4b4a2ee016505b5e8ba4b5f0503e26594fda1caf0`.
The manual branch/operand record is
[PROVIDER-SOURCE-CLOSURE.json](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-17/PROVIDER-SOURCE-CLOSURE.json).
The source-first graph is
[SOURCE-GRAPH-FINAL.md](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-17/SOURCE-GRAPH-FINAL.md).
Graph rendering checks declared references and file integrity; it does not
execute native behavior.

## Mode3, fifth0 branches

Both actual2B96730 per-character predicates receive EDX1 and R8zero. Either
true immediately writes zero. Mode bit0 then queries firstCharacter in the
already qualified inline active-pregnancy manager. A nonnull record rejects.
For firstCharacter's nonempty Family+38 child list, the last full child ID is
resolved through actual Character store or fallback, child+60 date is adjusted
by FF6670, and currentClock+8 <= adjusted date rejects. Empty first list skips
that date branch; it does not establish a check deadline.

Mode bit1 chooses first role only when first+1C0 is nonnull and its native
highest tier is strictly greater; otherwise second is selected, including ties.
The selected Family+38 list is traversed in source order. Each resolved child's
Q64+1D0 must be zero and actual2BAE290 must return false to contribute to count.
Signed count >=2B94ED0(selected,max(2B94DC0(first),2B94DC0(second)),first,second)
rejects. These nested sources have separate owners.

Second raw Q64 comes from2B953E0; first raw Q64 comes from2B951D0. With the
matching initial predicate false, each nonpositive raw result rejects before
the base stage. The independent base function accepts supplied raw values,
including zero/negative, because it represents that numeric stage alone.
Existing ordinary effective-fertility values cannot replace these raw outputs:
the actual raw helpers apply additional arithmetic.

After the base stage, Family+14 reciprocal full-ID linkage can add loaded
numeric addends. If both Family+38 lists are nonempty, either actual2B955C0
common-child parent witness skips the addends. Empty lists bypass that helper.
Both Character+1C0 null selects another loaded multiplier. The final branch
resolves generation IDs through concrete stores and calls actual2BD89A0 on
the resolved receiver; its type name is unqualified here. It selects normal
or alternate relation multipliers. Native2912080 and2912270 reuse existing
actual4 FamilyABI qualifications; actual2912210 is separately owned. There is
no new positivity gate before the final Q64 writer.

Calling the original provider is not advertised as read-only. Its nested callees
were assigned separate source closures. Nonzero fifth argument also reaches
diagnostic string/allocation/global-init activity. This leaf makes no native
function call.

## Independent leaf and arithmetic

[conception_pair_value_inputs_12004.hpp](../../ck3_autonomous_player/native_bridge/include/xar_bridge/conception_pair_value_inputs_12004.hpp)
and
[conception_pair_value_inputs_12004.cpp](../../ck3_autonomous_player/native_bridge/src/conception_pair_value_inputs_12004.cpp)
provide a qualified memory-reader binding and `EvaluateBaseStage`. The binding
requires the caller's actual4 build pin/module base and reads only these Q64
slots. It does not prove a supplied SHA string or invent a live binding.

| Slot RVA | Provider role | Source instruction |
|---|---|---|
| 5C6A1B0 | Base average floor | 2B95FC6 |
| 5C69DB8 | Linked-pair addend | 2B960D9 |
| 5C69DC0 | Linked-pair title-state addend | 2B960F4 |
| 5C69ED0 | Both title-state fields absent multiplier | 2B96117 |
| 5C69DF0 | First relation multiplier | 2B962D9 |
| 5C69E00 | Second relation multiplier | 2B96332 |
| 5C69DF8 | Alternate relation multiplier | 2B963D4 |

These are operational roles, not claimed authored define names or stock values.
A failed slot read returns no loaded-input object and states the failed RVA.
Real zero/negative values remain available. Missing first raw, second raw or
floor stays unavailable in the base result, with no zero/false substitution.

The exact base stage at2B95F87..2B96056 first takes signed minimum. Strictly
below the loaded floor it keeps that minimum. Equality selects the scale
branch. It forms a wrapped64-bit sum and multiplies at scale50000/100000.
Fast path selection uses unsigned wrapped
`sum + 0xB504F333 <= 0x16A09E666`. The slow path splits max(sum,50000) into
signed quotient/remainder, wraps the remainder/minimum product, divides toward
zero and adds the wrapped quotient contribution.

For ordinary inputs the scale branch is the signed average toward zero.
For large negative sums the intermediate product can wrap. With
first=second=INT64_MIN/4 and floor=INT64_MIN, actual source yields0 rather than
the mathematical average. The initial summary's unconditional average wording
was corrected before implementation. This leaf preserves source widths, branch
selection and wraps; its output is a base-stage raw value, not final provider
Q64, eligibility or couple probability.

## Validation and remaining inputs

One focused external native Win64 DLL fixture compiled under GCC14.4.0 with
warnings as errors and passed47 actual checks. The fixture covers threshold
equality, min branch, ordering, signed truncation, fast/split boundary, wrapped
sum/product, missing-input distinctions, exact-slot callback reads, and zero,
negative or failed loaded inputs. Its source is
[conception_pair_value_inputs_12004_test.cpp](../../ck3_autonomous_player/native_bridge/src/conception_pair_value_inputs_12004_test.cpp)
and actual receipt is
[focused-01/VALIDATION.json](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-17/focused-01/VALIDATION.json).
This is fixture execution, with no live CK3 sampling, original provider call,
EXE generation or shared build edit.

Complete provider reproduction next needs separately owned inputs from
continuation45 exclusion predicate;46/47 second/first raw values;48/49/50
selected-role lineage, limit and child count;51 common-child witness;52
second relation predicate;53 last-child date;54 resolved receiver flag.
The top-level actual3877B source is reused across those lanes.

Candidate slots3E8/3F0 remain continuation20's independent observation. Their
clearing/consumer/active-record transition, monthly trigger, birth and natural
succession are not established by this packet. Current runtime household values
are not substituted for unobserved raw-provider results. Initial source-pending
receipts remain historical; latest delivery is
[RESULT-CLOSED.json](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-17/RESULT-CLOSED.json).
Storage categories and explicit review/expiry are in
[STORAGE-CLOSED.json](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-17/STORAGE-CLOSED.json).
