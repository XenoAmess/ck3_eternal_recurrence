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

## First evaluator attempt: envelope diagnostic RED

The single authorized evaluator attempt passed readiness and exact-build
proof, then ended after `166.314s` with CK3 process exit code `1`. The old
runner surfaced only `official MCP result lacks structured_content` and wrote
`mcp_sequence=null`; no private v3 JSONL was created, so the reader and
evaluator result were not observed. Source hashes were unchanged, no mutation
or time advance occurred, and all CK3/probe/python processes exited.

Frozen terminal evidence:

- report SHA-256
  `4460C7E89A5F16BBE194A295D7C207788FCD38CE52D60359C8FEF5D746FBE383`;
- terminal summary SHA-256
  `EF5AB8F1913554AC26010DDC676B1753A2199684A33A56B4A56B94B26D1D5D28`.

The runner now parses each official MCP result immediately. A result without
object-valued `structured_content` raises typed
`OfficialMcpResultEnvelopeError` and preserves the failed tool, concrete result
type, `is_error`, original content blocks, and structured-content value in the
final report's `mcp_sequence`. It does not parse text as a successful payload
and therefore does not relax exact-build, readiness, or result gates. The
deterministic regression fixture is pinned to the real report SHA and its
observed terminal shape (`mcp_sequence=null`, readiness present, exact-build
GREEN, process exit `1`, JSONL absent).

This diagnostic fix alone was not a reason to repeat the evaluator live. The
same candidate placed its first row after the native calls, so another process
exit could again have left no evaluator-boundary evidence.

## Durable evaluator boundary candidate

The next private-only candidate closes that evidence gap without changing the
call target or inputs. Immediately before the first evaluator call it appends
one `xar.ck3.g2_truce_private_evaluator_boundary.v1` JSONL row and calls
`FlushFileBuffers`. The row freezes the exact index-7 path, verified Truce
object and `0x4461CA8` vtable, script-value object `+0x108`, effect and
evaluation contexts, evaluator function and `0x3373000` RVA, and
`planned_call_count=2`. If append or flush fails, the evaluator is not called.

After each returned call, `post_call_1` and `post_call_2` are independently
appended and flushed with completed-call count and the corresponding result.
Thus a CK3 process exit inside the first native evaluator can still leave the
durable `pre_call` boundary; a later exit can distinguish one returned call
from two. The previous aggregate v3 row remains a final summary when control
returns normally.

The native fixture covers both terminal shapes: a deterministic simulated
process exit after the durable pre-call row produces exactly one boundary row
and zero evaluator calls, while a stable `1825/1825` run produces ordered
`pre_call`, `post_call_1`, and `post_call_2` rows. The feature remains under
the same OFF-by-default private build flag. It neither executes the Context
effect nor exposes a public field, readiness claim, or mutation path. This is
a static-ready candidate only. Python source-contract tests are `8/8` GREEN,
the MSVC 19.51 Release instrumented bridge build is GREEN, and its focused
native fixture is GREEN. No CK3 process was launched for this package.
