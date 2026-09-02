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

## Frozen no-launch candidate

The observer source remains exactly
`36fafd811b29bba11758d1ebc3929be8cbd4c9d4`.  The heartbeat-only runner and
no-launch verifier are separately pinned at
`abdce016e86f23e509f2d43b13ad311ab26994d9`; this does not change the DLL
source tree.

The immutable candidate is under
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-native-callsite-observer-ready-20260902T231252`:

- ready-to-run manifest SHA-256:
  `469ACAC772AFBA730FD4C669ADE3CFB2728AC0F81B796C9BEF88B5C093B64FDD`;
- no-launch preflight SHA-256:
  `9A971A98AD90C596C21F2665EC4A02958F1AA2669037C1AA4F587837D2E0E3DE`;
- exact source ZIP SHA-256:
  `F3F3E81EFFE0D832A280A81AF96FC2FB267BE6D9A134AB3A0F35F3BA95841E17`;
- private DLL SHA-256:
  `916224B04C2E4AF598C93777218CC99CCC560BEFE69EC7E8E834F8CD5B0E975C`;
- default DLL SHA-256:
  `91F4FE2A7B1A094FDDDD6A7456F0C24942E9D71D259AB91AEA34D5F7CCEB36A0`;
- injector SHA-256:
  `2427ED9E8CE04FB8CEA4A0E62109B1593CC2D820D4B496D8C891A50EB5E80891`;
- native fixture SHA-256:
  `E5492BBFA7944DD825A4AB850B1C64E630FB6AA3D4B104129463532538527D2F`;
- runner/verifier SHA-256:
  `7A5A62BDCFF7A95FFAF2611737B6905CF423CB5F37361F60947D9DF988CAA192` /
  `9F5C68ACEC21EE7CD15A2DA776DD04475E7E5C4FD68ED1AC95B5C2A0999BCFF4`.

The preflight revalidated the executable hash, both exact anchors, every
frozen hash, read-only file attributes, private marker presence, default
marker absence, report/heartbeat schema, project virtual environment, and
the 300-second readiness / 420-second total / 60-second observation bounds.
It also confirmed that CK3 and the probe inventory remained empty and that the
fresh attempt path remained absent.

The single frozen live command only launches the passive runner and samples
cached heartbeats.  It contains no private direct-capture environment, MCP
query, Context effect, surrender, white-peace, enforce, or other mutation.
The future stop condition is two stable native pre/post samples, a typed
terminal, or timeout.  Preparation did not execute that command.

## Bounded live-result postprocessor

`native_bridge/research/analyze_g2_truce_native_callsite_observer_live.py`
is the private, offline consumer for the future runner report.  It reads at
most 32 MiB and 512 heartbeat samples and binds its output to the frozen
manifest SHA-256
`469ACAC772AFBA730FD4C669ADE3CFB2728AC0F81B796C9BEF88B5C093B64FDD`,
source commit `36fafd811b29bba11758d1ebc3929be8cbd4c9d4`, and source ZIP SHA-256
`F3F3E81EFFE0D832A280A81AF96FC2FB267BE6D9A134AB3A0F35F3BA95841E17`.

The typed result contract is:

| Observed boundary | Classification | Status | `evaluated_days` |
| --- | --- | --- | --- |
| exact install/heartbeat, both sites at zero calls | `no_native_callsite_hit` | `NO-GO` | unavailable |
| at least one native pre-call, no native return | `pre_only_native_callsite` | `RED` | unavailable |
| both sites returned and the final two full rows are stable | `two_site_return_observed` | `GREEN` | each site's signed native `EAX` |
| manifest/policy/source mismatch, malformed read, install failure, counter regression, missing sample, or bound exceeded | `read_or_install_failure` | `RED` | unavailable |

A partial return that does not cover both sites is typed
`incomplete_two_site_return` / `NO-GO`; it is not promoted to the successful
two-site result.  The output preserves the exact two call RVAs and the native
register mapping (`RCX=script_value`, `RDX=effect_context`,
`R8=evaluation_context`), plus pre/post thread IDs, QPC values and return
`EAX`.  Install success, ordinary heartbeat presence, and no-hit samples never
become `evaluated_days`; the postprocessor itself never changes public
readiness.

Deterministic fixtures cover no-hit, pre-only, stable two-site return, and
read/install failure.  They also verify the sample bound, evidence hashes,
register/thread/QPC/EAX preservation, and the rule that policy or manifest
mismatch suppresses an otherwise return-shaped result.  This package is
offline-only: it did not modify the frozen READY candidate, start CK3, invoke
the direct evaluator, execute Context, or issue a mutation.

## Static truce aggregation intake

[static-ready; no CK3 launch] The postprocessor now also validates one reusable
session identity from runner readiness, every heartbeat sample, the managed
session and the cold-checkpoint driver anchor. It requires a paused/map-ready
snapshot plus matching snapshot/public/native revisions, date, connection
generation, episode run, episode character and CK3 PID. A mismatch changes the
postprocessor result to `read_or_install_failure / RED` and suppresses both the
identity and `evaluated_days`.

The existing public six-domain projector accepts this postprocessor result as
an optional input. It fills the existing `raiktor-surrender-truce-v1` payload
only when all of the following hold:

- status/classification are exactly `GREEN / two_site_return_observed`;
- manifest SHA, source commit `36fafd811b29bba11758d1ebc3929be8cbd4c9d4`,
  source ZIP and read-only runner-policy proofs match the frozen contract;
- both exact callsites have returned, the final two samples are stable and the
  two signed `EAX` values agree on one nonnegative `evaluated_days`;
- postprocessor session identity matches the aggregate snapshot's
  connection/episode/PID/revision/date identity exactly.

On that narrow path only `truce_ready` becomes true and the value is carried by
the already frozen strict truce schema. Expiry remains
`expiry_observable=false / expiry_date_raw=null`. No-hit, pre-only, partial
return, read/install failure, unequal return, manifest/source drift or session
drift all remain the existing typed `{"available": false}` truce domain.
Because generic/source-specific war-bound evidence is still missing, the
aggregate remains incomplete and `six_dynamic_domains_ready`,
`action_terms_ready`, `decision_ready` and `automatic_surrender_ready` remain
false. No public action or mutation surface was added. This is a static intake
seam, not a claim that a GREEN passive live artifact already exists.

## Runner-to-acceptance evidence path (2026-09-03)

[static-ready; no CK3 launch] The source runner now requires an explicit
`--ready-manifest`.  After its managed session has ended and cleanup has
produced the immutable raw `report.json`, it hashes that exact manifest, runs
the bounded typed postprocessor against the same bytes, and atomically writes
two sibling files:

- `typed-postprocess.json`, containing the complete typed result;
- `acceptance-report.json`, binding the raw report, ready manifest, runner
  source, postprocessor source and typed result by SHA-256.

The postprocessor also requires successful managed cleanup and a runner
terminal coherent with the classified observation. A return-shaped heartbeat
cannot remain GREEN when the raw runner reports failure, an unexpected stop
reason, or unproven cleanup.

The acceptance report carries `identity_bound_truce_input_eligible=true` only
for `GREEN / two_site_return_observed` with observable two-site return values.
That flag only says the typed result may be offered to the already strict
identity-bound projector; it is not an action or decision readiness claim.
No-hit, pre-only, partial-return and read/install terminals retain their typed
non-GREEN classifications.  Every acceptance report keeps expiry and
war-bound observation false, and keeps action terms, decision, and automatic
surrender readiness false.

The no-launch verifier for the next candidate additionally requires the
postprocessor to be a frozen candidate file and the unique command to carry
the manifest-binding argument.  The previously frozen
`469ACAC7...093B64FDD` candidate directory was not modified by this static
package.  Before another live, the integrated runner/postprocessor must be
refrozen into a fresh immutable candidate and pass the updated no-launch
verification.  Only a later authorized live can supply actual native returns;
this wiring package does not supply `evaluated_days` itself.
