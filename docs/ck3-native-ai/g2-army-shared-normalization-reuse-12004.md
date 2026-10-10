# Army shared input normalization reuse (CK3 1.20.0.4)

Status: source authored; Root consumer FIRST pending. No live latency or G2 credit.

Actual Native60 R0086 Army before/after responses were about93MB and are already
retained with single-pass thin extraction. This work does not reread those bodies.
The future91 source includes qualified Native63 lossless manager sharing. Its
three MCP exits already pack their complete structured result and use small text
summaries; the native Driver expands shared fields with `detached=False`.

The remaining concrete source cost is in `normalize_army_strengths`: it validates
the same expanded manager object once per Army. The six family normalizers are
context-free, preserve order and raw fields, validate their own declared branches,
and return `deepcopy(value)` (including legacy-default normalization). Their
normalization does not depend on the selected Army row. Per-row readiness and
other Army-specific inputs still run independently.

The change keeps a cache inside one normalization call, keyed by normalizer and
input object identity. Its first use validates and copies normally. Later uses
deepcopy that normalized result into the other row. The strong reference to the
input remains in the cache; equality of separate objects is never a cache key.
Legacy expanded rows with separate families continue independent validation.
The private row normalizer defaults to the original uncached behavior.

For two rows sharing all six objects, family validator invocations fall from12
to6. The normalizers still produce12 independent family copies in total: six
original normalizer copies plus six later-row copies. For the retained actual18
counts this removes one validation walk over6×464 roster occurrences and the524
pending-table records, without omitting any field or ordered occurrence. This is
a source-derived work difference, not a measured timing improvement. Native
pipe and public wire bytes do not change from qualified Native63.

The separate direct Service query revalidates its full typed result; this patch
does not bypass that contract. No cache survives a query or substitutes cached
data for a new native result. History, projection, readiness, serializer and ABI
contracts remain unchanged.

Root's single necessary FIRST consumes the retained Native63 actual02
`available-equal-shared.json` packet once. It compares the new batch with the
unchanged uncached row semantics, checks independent legacy validation and mutable
copies, rejects a malformed distinct input, then makes one registered
`ck3_auto_turn` call through the existing real Driver/Service harness. The old
seven-scene method, native producer and build are not rerun.

Oct10/W41: private source candidate only; consumer FIRST pending; zero new live
qualification, zero saved days, zero Army loss proof, no latency claim. Root may
integrate after the sole consumer succeeds. Current SDK624, public814 and frozen
integration91 are untouched; candidate is an independent child of91bf6458.
