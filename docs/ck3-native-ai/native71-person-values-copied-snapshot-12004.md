# Person transfer owned value snapshot adapter

2026-10-10. This new31b adapter reuses the frozen31 guarded Model+E0 copy,
source contracts and old focused qualification without rereading native bodies
or running the old fixture. SOURCE-FREEZE.json and INTERFACE-FREEZE.json were
written before adapter code. New validation belongs to29b's single cross-block
compound; no standalone31b test invocation is added.

`CapturePersonTransferValuesSnapshot12004` consumes29b's typed scope containing
the original before occurrence, the current before/completed event, phase,
side, actual Model and original return RVA. It passes through13's existing
guarded reader via a synchronous stack shim. It calls the old value copier
once; it creates no event clock, hook, getter, native call or allocator model.
Root calls this adapter only from the already exact-build-bound producer.

The returned `PersonTransferValuesSnapshot12004` preserves the old raw DTO's
independent data/capacity/count fields, optional signedQ64 source interpretation
and precise missing reason. `values_q64_raw_bits` contains exact ordered
`bit_cast<uint64_t>` representations of the same owned signed values. Zeros,
duplicates, INT64_MIN and INT64_MAX keep their actual positions and bits.
No float conversion or property arithmetic occurs.

The required `maximum_payload_bytes` is a caller observation budget. The shim
recognizes the old copier's one Model+EC count read, retaining its true signed
value. If a nonnegative count times8 exceeds budget, it refuses that legacy
count response before vector allocation, then restores the true raw count.
Payload remains absent with `values_payload_budget_exceeded`; descriptor fields
remain independently visible. Normal operation reads each header and payload
once. There is no truncated count, repeated read or invented native limit.

`descriptor_copy_complete` requires independently copied data/capacity/count.
`payload_copy_complete` requires the value operand's own nonnegative count and
complete ordered array of that size. Zero has an owned empty array; unread or
negative count does not. Missing capacity can leave payload complete while
descriptor is partial. `declared_operand_copy_complete` is their conjunction;
none of these flags asserts clock/Model lineage or key/value pairing.

The component wire schema preserves raw Q64 hex, optional signed decimal
interpretation, descriptor/count, scope, budget and partial reason. It is the
typed producer's proposed serialization contract; shared serializer and
normalizer adoption remain Root-owned. Typed scopes must not be replaced by a
retention ordinal or a current Model query.

29b combines this component with30b ordered keys from the same actual snapshot.
It must retain both independent counts and positively establish completeness,
matching counts, exact Model/context/PC identities and occurrence/thread/clock/
phase before a paired PC is consumable. Full prepared/installed attribution
also requires the retained preparation completed PC and this exact Ci copied
PC comparisons. The value adapter alone cannot unlock58's numeric seam or
qualify a natural FullPerson/Entry transfer.
