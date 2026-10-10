# Current negotiated quote: trigger root-scope gate (1.20.0.4)

The complete actual helper is `372B4C0..372B550` (144 bytes), raw SHA
`1d0c56999dcfc97758a34b23894c4763994ff6e141fffa687595c7a921c98ae8`.
Its actual caller is the held `372E000..372E42E` body: `372E23A` calls it with
RCX=the selected trigger and RDX=`[aliases+0]`, the original root scope. The
caller tests AL at `372E23F`; false eventually sets DIL=0, while true permits the
later trigger virtual `+C8`. A scope-compatible result does not prove `+C8`
returned true or that the negotiated interaction can send.

The helper calls trigger virtual `+58` with unchanged receiver, obtaining AX.
It then reads WORD `[root_scope+0]`. Nonzero preferred AX equal to that WORD
returns AL=1. Otherwise virtual `+60` receives the trigger and an owned 16-byte
two-QWORD mask destination. An all-zero mask returns 1. A nonempty mask and zero
root kind returns 0. Kinds 1 through 128 test bit `(kind-1)&63` in word
`(kind-1)>>6`. A nonempty mask with kind above 128 indexes beyond the source-proved
two words; the bounded model preserves unknown. Preferred-kind and empty-mask
short circuits remain valid before that boundary.

No literal child CALL exists in the helper. The selected trigger class and the
actual `+58/+60` targets/output layouts are not currently held. Copying their
slot addresses does not copy their returned AX or written mask. No getter,
trigger, `+C8`, effect or game action is invoked by this component.

The read-only API uses the shared current-query Frame and guarded Access. It
requires the exact build/frame and the supplied original scope identity, then
copies the root WORD, trigger vptr and raw slot58/slot60 addresses. Those raw
copies remain separate from unavailable getter outputs. A failed read stays
partial, and mismatched frame/root causes no read.

The pure projection accepts explicitly supplied preferred AX and two mask words
with matching Frame/trigger/root provenance. Its result is labelled conditional.
`getter_output_source_ready` and `qualified_ready` remain false by construction;
`returned_byte` stays null. There is no truth/source-ready input setter. The
parent `372E000` wrapper consumes only independently qualified results and keeps
its current output unknown. A future source owner must prove the actual getter
implementation/producer before any such output can be qualified.

The `SourceLeafFrame12004` overload supports another existing caller snapshot
without constructing prisoner roles or a new clock. It requires exact producer
RVA `372B4C0`, the companion Frame's confirmed caller snapshot and nonzero
receiver/scope identities. If that Frame already holds a scope WORD, the copied
or conditionally supplied WORD must match it. A mismatch retains partial raw
input and no conditional result. This overload shares the same raw-copy and
conditional calculation core; slot addresses remain raw, getter qualification
stays false, and the native returned byte remains null.

The original prisoner no-main cases are included only in owner35's new connected-quote compound.
They check literal source branch vectors, the 64/65/128 boundary, missing data,
out-of-known-mask kinds, current Frame identity and partial copies. Supplied
fixture values never become a native getter witness. Owner10 alone compiles and
runs that compound; authored cases are not GREEN without its actual receipt.
No old63b source/journal or focused tests were changed or reexecuted.
The separate generic no-main fragment checks caller snapshot, producer and
scope-word identity at this new entrance. It does not repeat the twelve
original mathematical vectors. Owner09's new Lifestyle compound alone invokes
this generic fragment once; owner35 does not call it. Owner10 executes each
parent's one compound, with no standalone child test.

External source proof and API pins are in
`D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-63c/DELIVERY.json`.
The helper required one finite cache-first 144-byte acquisition using the shared
O_EXCL range claim; no old/full executable or section/hash census was read.
