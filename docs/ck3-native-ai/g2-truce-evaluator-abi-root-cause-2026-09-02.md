# G2 truce evaluator ABI root cause (2026-09-02)

This exact-build, static-only slice explains the first-call `process_exit`
captured by the private index7 evaluator candidate. It does not start CK3,
execute an effect, alter the public wire/readiness contract, or authorize a
war mutation.

## Result

The three-parameter MSVC x64 signature is correct. The process exit is not
explained by a missing fourth/fifth parameter or a `thiscall` mismatch. The
wrong value was passed as the third argument:

| input | native `CAddTruce` construction | private candidate construction |
| --- | --- | --- |
| `RCX` | script value at `CAddTruce+0x108` | same; correct |
| `RDX` | populated effect context | same; lifetime spans the call |
| `R8` | pointer loaded from `*(void **)(effect_context+0x28)` | address of the field, `effect_context+0x28` |

Both direct `CAddTruce` callsites show the load explicitly:

- `0x2EDAF0F`, owner PDATA begins `0x2EDAD20`: `mov r8,[r15+0x28]`;
- `0x2EDB59E`, owner PDATA begins `0x2EDB3A0`: `mov r8,[r12+0x28]`.

The independent wrapper at `0x2EDC1B0..0x2EDC209` ends with
`mov r8,[rdx+0x28]` and a tail jump to `0x3373000`. This confirms that
`+0x28` identifies a pointer-valued field to load, not a subobject address to
pass.

The durable live boundary matches the bad construction exactly: effect
context `0x5B2FD01B0`, evaluation context `0x5B2FD01D8` (exactly `+0x28`),
one flushed `pre_call` row, no `post_call` row, then `process_exit`. Its
terminal summary SHA-256 is
`C4157B5E48D9634E79146A970C254914DEBB1C6B57F0A81459EAFD4DD0493574`.
This correlation supplies the concrete failure evidence; the static callsites
supply the correct operand semantics.

## ABI and PDATA freeze

Evaluator RVA `0x3373000` owns PDATA
`0x3373000..0x337312F`, unwind RVA `0x4C92B1C`. Its entry binds:

- `RCX -> RBX` (script value);
- `RDX -> RBP` (effect context);
- `R8 -> RSI` (evaluation context).

The first `R9` reference is an overwrite at `0x3373046`; no incoming `R9`
value or caller stack argument is consumed. The function directly accesses no
`FS:`/`GS:` location. That does not prove nested evaluator helpers are free of
thread/TLS assumptions, but no such assumption is needed to explain this
failure: the third-argument kind already differs from every native construction
examined.

The extractor enumerates all exact `E8/E9 rel32` xrefs to the evaluator and
binds each to an exception-directory function: 78 calls and one tail jump.
The frozen fixture records the complete RVA list, the two `CAddTruce` owners,
function hashes, wrapper bytes, and the non-runtime boundary:

- [`extract_g2_truce_evaluator_abi.py`](../../ck3_autonomous_player/native_bridge/research/extract_g2_truce_evaluator_abi.py)
- [`g2_truce_evaluator_abi_root_cause_v1.json`](../../ck3_autonomous_player/native_bridge/research/g2_truce_evaluator_abi_root_cause_v1.json)

## Context lifetime and next distinct seam

The private bridge constructs and populates `WarEffectContextStorage` before
the observer call and destroys it only after the observer returns. The effect
context storage lifetime therefore covers the evaluator invocation. The exact
dynamic type of the pointer stored at `+0x28` remains opaque; the native ABI
only requires that its stored pointer value be forwarded as `R8`.

The next distinct private seam is deliberately narrow: load
`LoadAt<void *>(effect_context, 0x28)`, reject null, and pass that loaded value
as `R8`, leaving the `+0x108` script value, effect-context argument, evaluator
RVA, public ABI/readiness, and all mutation paths unchanged. A later live would
only be necessary to verify that corrected private input and capture the two
returned `evaluated_days`; this static package itself does not request or run
that live.
