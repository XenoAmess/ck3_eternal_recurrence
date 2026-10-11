# R55 duplicate inputs reclaimed

ROOT actually removed four exact SAVE replicas (366678829 logical bytes) and all 3740 listed RUN55 input-snapshot shadercache files (146942067 logical bytes). Every original command and batch returned 0. All SAVE source/target SHA checks completed before any SAVE deletion; each cache deletion held both source and target through SHA verification and absence readback.

The independent R55 initial checkpoint 86fe... and original0240 1d98... remain retained. All CASE6 mutable cache (148147375 B), immutable R54 seed, source/runtime inputs, business/origin metadata and other unlisted files remain protected. No directories were recursively removed. The exact old target bytes are now unavailable at their original paths; the tombstones preserve their reconstruction identities without manufacturing replacement evidence.

The two CREDIT-EVENT files are independent one-time events, still unclaimed. Combined new logical deletion is 513620896 B; allocation API sums are separate from volume free deltas, which are not exclusive causal credit. Do not recount the previous R54 cache, five-SAVE or R52 events. This package does not claim 013 capacity.

Original executor sources, plans, identity JSONL and detailed audits remain external under exact original pins. Only the five small original result receipts are copied. No source, complete identity/detail ledger, SAVE/cache body or binary was copied, reread, rehashed, scanned, compressed or removed during this aggregation. Original detailed-audit deadlines stay 30 days and compact reviews 180 days from actual deletion; no existing TTL is renewed. R55 administrative closure remains separate from normal-exit and business acceptance.
