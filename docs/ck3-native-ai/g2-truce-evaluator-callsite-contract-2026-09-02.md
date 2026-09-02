# G2 truce evaluator call-site contract (2026-09-02)

This is a bounded, read-only exact-build slice for the `GEN-034`
`evaluated_days` gap.  It does not alter the public v1 wire, readiness bits,
native offsets, action routes, or CK3 runtime.

## Static result

The pinned CK3 `1.19.0.6` executable is
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
Both direct `CAddTruce` call sequences resolve to evaluator RVA `0x3373000`
with the same MSVC x64 argument shape:

| input | exact source |
| --- | --- |
| script value (`RCX`) | `[RSI+0x108]` |
| effect context (`RDX`) | current effect object (`R15` or `R12`) |
| evaluation context (`R8`) | pointer value loaded from `*(void **)(effect_context+0x28)` |
| result | signed `int32` in `EAX`, consumed immediately by the caller |

The two bounded sequences are anchored at `0x2EDAF01..0x2EDAF14` (call at
`0x2EDAF0F`) and `0x2EDB58F..0x2EDB5A3` (call at `0x2EDB59E`).  The complete
bytes, span digests, evaluator entry span, and post-call consumers are frozen
in [`raiktor_truce_evaluator_callsite_v1_abi.json`](../../ck3_autonomous_player/native_bridge/research/raiktor_truce_evaluator_callsite_v1_abi.json).

Here and in the original JSON, bracket notation means a memory load. It does
not mean the address of the `+0x28` field. The later exact ABI root-cause
slice records why that distinction matters.

The reusable verifier is:

```powershell
py -3.13 ck3_autonomous_player/native_bridge/research/verify_raiktor_truce_evaluator_callsite_v1.py `
  --exe 'Z:\ck3_mod_rewrite\Crusader Kings III\binaries\ck3.exe'
```

It reads only the executable and exits `PASS`/`FAIL`; it never starts or
attaches to CK3.  The focused contract test also checks the relative-call
targets and all frozen span digests:

```powershell
py -3.13 -m unittest ck3_autonomous_player.tests.unit.test_raiktor_truce_evaluator_callsite_contract -v
```

## Boundary and next entry

This closes the static evaluator/call-site identity only.  It does not prove
that the loaded runtime tree supplies a valid duration object, that the
evaluator returns a stable value in the paused artifact, or that CK3 persists
an expiry date.  The current live report therefore remains
`evaluated_days_observable=false`, `truce_ready=false`, and `GEN-034` unresolved.

The next smallest evidence entry is one exact-build paused private observation
of the evaluator input/result (or a test-only capture before the existing
output reset).  It must run the open_kaishek offline preflight first and must
not widen the public schema or enable surrender/white-peace writes.
