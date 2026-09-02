# Phase-two completion-state consumer (2026-09-02)

The completion value `2` published at `0x3B9CFD7` is consumed by a bounded
scheduler polling path. This package used static exact-build evidence only and
did not start CK3.

Within frozen slice `[0x3B9A190,0x3B9E266)`, four reads at `0x3B9A1EA`,
`0x3B9A241`, `0x3B9B9A4`, and `0x3B9B9E0` test state zero before trying to
execute work. The only completion classifier is `0x3B9DEA7` inside PDATA
function `[0x3B9DD50,0x3B9E025)`: it reads `[RBX+0x60]`, maps values 2 and 3
to the completion branch at `0x3B9DEB0`, and decrements reference count
`[RBX+0x64]`.

On the final reference, `0x3B9DF7B` publishes retired state 3, the callback at
`[RBX+0x38]` is destroyed and cleared at `0x3B9DF94..0x3B9DF97`, and its task
storage is released through owner `[RBX+0x58]` at `0x3B9DFAA`. The consumer
has exactly two direct call sites, `0x3B9E10B` and `0x3B9E175`, both in wrapper
`[0x3B9E030,0x3B9E266)`.

This closes the actual release as a scheduler poll/retire edge; no explicit OS
wait or signal exists in the bounded path. The smallest future read-only
observation entry is `0x3B9DEA7`: read the task pointer in `RBX`, state at
`+0x60`, callback at `+0x38`, and callback vtable slot 2 target. Filtering the
slot target to RVA `0x88B480` selects the exact loader task already frozen by
prior evidence. This static contract needs no new live run and does not itself
install a production hook or change public schema.

The extractor artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\completion-consumer-static-extract.json`,
SHA-256 `4E189772BEAD64B7EBE0E6804155CF66AB885770E7DDD76BF37C5BAE9E2CDCD9`.
Phase two remains **native-readiness RED + static completion consumer bound**.
