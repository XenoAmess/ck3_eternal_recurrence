# Ransom scope support copy: actual CK3 1.20.0.4

Actual `373ACF0` reaches `3727180` at `373ADBD` with `RCX=out_scope+118`
and `RDX=original_scope+118`. The complete reached copy CFG is 394 bytes across
five physical runtime-function rows. Its source copies an ordered vector of
32-byte raw records, DWORD `+28`, and the `+30` vector member, then calls
`3727EC0`. The parent's initial zeros do not describe the returned copy.

`ReadPrisonerScopeCloneSupport11812004` consumes the existing selected-quote
guarded read access and current frame. It requires the exact image and the
original scope at `interaction_context+8`. It reads the two raw source vector
data values and signed counts, plus DWORD `+28`, in that same query. It calls
no native copy, allocator, destructor, predicate or queue.

The implemented branch requires both read source counts to be exactly zero.
Actual `889660` on the fresh zero destination count only writes count zero.
The reused `37282B0` / `889780` empty path preserves the fresh `+30` data,
capacity, count and allocator. Actual `3727580` then returns canonical AL zero
with no writes or calls. It does not depend on DWORD `+28`. This matches
`3727EC0`'s canonical comparison for fresh DWORD `+48=FFFFFFFF`, so the final
helper skips registration and leaves the returned fields unchanged.

The returned 80-byte support projection defines `[0,2C)` and `[30,4F)`;
`2C..2F` and `4F` remain undefined. The two returned data pointers, capacities
and counts are known zero. The module-relative vtable and allocator values
come from the actual parent initializer joined with the closed helper write
bounds. DWORD `+28` retains its actual raw source value, including a nonzero
value. These are field facts for this branch, with no semantic scope labels
assigned to raw records.

The projection retains original source member/data identities as input
provenance. A zero count qualifies an empty ordered input list. It has no
physical cloned support or allocated buffer identity. The facts belong to the
caller's copied current quote frame. A missing source read, changed frame,
negative count or nonempty copy path leaves returned-field qualification
unavailable; default array zeros have no defined mask.

The positive vector path still requires an actual allocation identity and
applicable element-copy/lifetime evidence. The general final-helper mismatch
may register a receiver pointer; an absent physical destination cannot be
turned into that pointer. Those branches are not qualified by the empty path.

Source contracts and finite capture receipts are external in
`D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-53c/`.
`SOURCE-FREEZE-CLOSED-EMPTY.json` precedes the production header. Helper proofs
are reused from 17e, 48d, 20e and 40d; 15e's positive install proof is separate.
This leaf acquired 394 new actual bytes, read no old executable, and ran no
native copy or previous qualification.

The six new cases have no standalone main and feed the current selected-quote
compound owned by 35, run once by 10. They exercise nonnull raw source data
with zero counts, a nonzero copied DWORD, the exact mask and absent physical
clone, and nonempty, negative, failed-read and changed-frame frontiers.
Validation is AUTHORED_NOTRUN until the central compound receipt is linked.
No live clone, native query outcome or ransom action is claimed.
