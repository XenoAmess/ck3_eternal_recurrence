# G2 Truce native callsite observer (2026-09-02)

## Result

The private direct-evaluator route is closed after the context-pointer-fix live
still ended inside its first evaluator invocation.  The next distinct seam is a
private, read-only observer around the two exact native `CAddTruce` calls.  It
does not submit an evaluator request of its own.

The implementation is `static-ready`.  No CK3 process was started for this
package and no live row or `evaluated_days` value is claimed.

## Frozen failed-live boundary

The one authorized context-pointer-fix live retained a durable `pre_call` row
and then CK3 exited before the first return:

- report SHA-256:
  `1A238BFE5194CE94E9C3CB784360E98E9A99EF758D0802D33478F52DC91C45AC`;
- durable JSONL SHA-256:
  `D15B54483D879826995789213E58B705A4933F44E7ACD4C7EFD248E421B31228`;
- terminal/cleanup summary SHA-256:
  `2EFCA10AAC8A32AAC8248C6048D1EA50DC0A49475CFD56921A1E9FA678300998`;
- exact index-7 path and Truce vtable RVA `0x4461CA8` were verified;
- `script_value = Truce+0x108` and evaluator RVA `0x3373000` were verified;
- `effect_context=0x68BD9D00E0` and the loaded pointer
  `evaluation_context=0x68BD9D0110`; this proves the pointer-load fix was in
  effect, but it was insufficient to make an out-of-callsite invocation safe;
- `planned_call_count=2`, `completed_call_count=0`, `evaluated_days=null`;
- no Context effect, war termination or other mutation was executed; all CK3,
  probe and runner processes were gone after cleanup, and source inputs were
  unchanged.

Therefore another private direct call would repeat a disproven seam.  Future
evidence must come from native control flow.

## Exact hooks

The observer is frozen to CK3 `1.19.0.6`, executable SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.

| Site | Patched exact sequence | Native call | Continuation | Inputs |
| --- | --- | --- | --- | --- |
| 0 | `0x2EDAF01`, 19 bytes | `0x2EDAF0F` | `0x2EDAF14` | `RCX=RSI+0x108`, `RDX=R15`, `R8=[R15+0x28]` |
| 1 | `0x2EDB58F`, 20 bytes | `0x2EDB59E` | `0x2EDB5A3` | `RCX=RSI+0x108`, `RDX=R12`, `R8=[R12+0x28]` |

Each trampoline replays only the covered native argument setup, durably keeps
the original native call in place as relocated control flow, and records:

- before: site, `RCX`, `RDX`, `R8`, thread ID and QPC;
- after: signed `EAX`, thread ID and QPC.

The trampoline preserves flags and volatile general registers around each
observer thunk.  It does not execute a Context effect, publish an action or
submit an extra `0x3373000` invocation.

## Install and rollback contract

The CMake option
`XAR_CK3_ENABLE_G2_TRUCE_NATIVE_CALLSITE_OBSERVER_V1` is `OFF` by default.
Only a private build includes its heartbeat object and install branch.  Exact
build admission and proof that the primary thread is suspended are mandatory;
runtime address overrides are fixture-only.

CMake rejects a build that enables this observer together with the retired
direct-evaluator private capture, so a native-observer candidate cannot also
submit the disproven standalone request.

Both anchors are verified and both stubs are allocated/protected before the
first target write.  Installation is one two-site transaction: if the second
write fails, the first site is restored.  Uninstall restores both exact anchors
in reverse order before releasing ownership.  A rollback that cannot prove the
original bytes remains an explicit RED and retains ownership/state.

The default heartbeat, public ABI, capability list and readiness gates are
unchanged.

## Static acceptance

- MSVC 19.51 private DLL build: GREEN;
- native fixture: default-off/exact-build gate, two-site pre/post fields,
  generated trampoline identities, uninstall restore and second-site failure
  rollback: GREEN;
- Python source/ABI contract: GREEN.

The fixture contract is
`native_bridge/research/g2_truce_native_callsite_observer_v1_abi.json`.  A
future live, if separately authorized and scheduled, needs only one bounded
native execution and must stop after stable matching pre/post rows or a typed
terminal.  It must not enable the retired direct-evaluator capture.
