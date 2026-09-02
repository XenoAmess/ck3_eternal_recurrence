# G2 index-7 duration evaluator capture

## Frozen live input

The readiness-300 private run produced two identical
`xar.ck3.g2_truce_private_capture.v2` rows. The exact loaded path was:

`root index7 -> default child1 hidden_effect -> child0 Context -> child0 CAddTruceEffect<0>`.

The final object had vtable RVA `0x4461CA8`; its address was
`0x1D0752B8FB0`, and the frozen duration script-value input was
`0x1D0752B90B8`, exactly object `+0x108`. Evidence:

- private JSONL SHA-256
  `6807E408870D7A7B47E9B6EC609BEFB270FC0E4571912D5FEA4432E09F8705C3`;
- runner report SHA-256
  `24D9661AEC29E8247BF63E54082487BD6A2E296F4E2A0A965227BDB454A63706`;
- cleanup/evidence summary SHA-256
  `27ABEC1CBE11E022C8CB8309BC9889E7FADFC103128D8862798542F2E9B4B0FA`.

The enclosing public terms runner remained RED on its stale production
`19/14/index9` shape contract. The private index-7 path is live; evaluated
days and public readiness are not.

## Static evaluator candidate

The exact-build evaluator ABI remains:

```text
int32 EvaluateTruceDurationDays(
    void *script_value,
    void *effect_context,
    void *evaluation_context)
```

Its RVA is `0x3373000`. Private capture schema v3 extends the already proven
index-7 helper only after exact Truce vtable and `+0x108` checks. It records the
evaluator function/RVA and the exact three-pointer tuple, calls the evaluator
twice with that same tuple, and records both `int32` results, call count,
non-negative status, and equality. A negative or unequal pair is a typed
private terminal rather than a public observation.

This path remains guarded by the existing OFF-by-default
`XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1` build option. It does not execute
the Context effect, does not submit surrender/white-peace/enforce commands,
does not mutate a game object, and does not change public ABI/readiness or the
production resolver constants.

## Static verification

- Python source contract: `6/6` GREEN;
- MSVC 19.51 Release instrumented build: GREEN;
- private native fixture: GREEN; with production root forced to stale `13/12`,
  index 7 completed and the fake evaluator received only the exact frozen tuple
  twice, returning stable `1825/1825`;
- native game-access regression: PASS.

Candidate binary hashes and the single-run manifest are frozen outside the
repository under
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-index7-evaluator-ready-20260902T2040`.
No CK3 process was started while preparing this package. A live run requires a
separate P0-coordinated authorization.
