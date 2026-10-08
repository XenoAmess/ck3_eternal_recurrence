# Current Council task owner tax component, CK3 1.20.0.4

2026-10-08. Baseline `6ee7dea1b4d2fa4ecb05223f12c66b7afe72ac2d`.
Exact game: **1.20.0.4 / Steam25734779**, EXE SHA
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
Version/source pins are reused; this worker reads no EXE, starts no SDK/game,
and runs no build, project import or test.

The goal is the actual current task's evaluated owner `domain_tax_mult`
component. It is a multiplier before other owner/global aggregation, not gold
income and not a quote for another councillor or a task switch. The present
stage is **research/source capture**. No numeric leaf or live value is claimed.

## Stock and native source first

The installed stock `00_steward_tasks.txt:69–73` defines current Collect
Taxes owner modifier `domain_tax_mult=1`, scaled by
`steward_collect_taxes_total_scale`. `99_steward_values.txt:63–137` retains
the stewardship base plus owner/perk/house/culture conditions. These exact
selected stock lines were read; no stock/EXE hash or old matrix was rerun.
The existing [tax value topic](council-collect-taxes-value-probe-2026-09-29.md)
explains why a skill difference or `stewardship/200` is not a native quote.

| Input | Current evidence | Use |
| --- | --- | --- |
| Requested seat, actual task, owner/incumbent | Actual4 private selected-seat reader is source-closed and already qualified | Bind the current task to the existing native/public frame |
| Task key, frozen, original scopes | Shared actual4 county-conversion ABI: TaskType key18, ActiveTask frozen39, original scopes40 | Reuse the same ActiveTask source proof; no dynamic PositionType key read |
| Task owner evaluator | Root's first299B capture matched `31ABE10 -> 31ABDF0` | Current method source/ABI roles are now held; a match alone does not close every callee |
| Numeric getter prefix | Held37B mapping `2303700 -> 23036E0`; ordinary-ID local continuation pending126B | Whole evaluated owner output is the receiver: IDs0/countC, values68 |
| Owned evaluated modifier cleanup | Root matched complete actual4 `9F24F0..9F259D`,173B | Release the original internal buffers and shared/string objects; outer storage stays caller-owned |
| Aggregate construction | Root matched actual207 semantic bytes at2872480 | Caller-owned output initialization: ID vector0, value vector68, SSO190, shared1B0 |
| Descriptor table locator | Root matched actual17B initializer at2C4DC3F, table480C2A0/count609 | Locate actual typed records; this supplies no tax numeric ID |
| Tax modifier numeric ID/keyword record | NOT_HELD | Resolve the selected typed descriptor; never borrow piety ID97 |

Root executed the owner299B capture once near **06:47:19Z**:
`SOURCE_CAPTURE_MATCHED`, complete old/new decode, normalized retained operands,
ordered edge shape and local flow equal; **299B / 1 fresh read**. No callback
was installed. Receipt:
`Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261008/council-current-task-domain-tax/owner-map01/SELECTED-TASK-OWNER-CAPTURE.json`.

The actual body recursively follows TaskType+1358 clone, builds ScriptContext
from the original scopes' incumbent and owner IDs, evaluates collection+438
through **2872480**, cleans its local context, and returns caller-owned output.
Source uses shared context helpers889F60,373A0F0,889700,889780. Those role
references are recorded; new callee source is not implicitly authorized.
Root subsequently executed the cleanup173B and table-locator17B captures once,
both `SOURCE_CAPTURE_MATCHED`, about0.869s and0.696s respectively. These are
**190B / 2 fresh reads**, native calls0; the tax ID remains unproved. Receipts
are `cleanup-map01/SELECTED-FOLLOWON-CAPTURE.json` and
`tax-table-locator-map01/SELECTED-FOLLOWON-CAPTURE.json` in the same package.

Actual cleanup `9F24F0` decrements/releases owned shared object+1B0, destroys
SSO string+190 through the already-bound shared856050, releases sparse
numeric buffer+68 through its stored allocator+78, and releases the ID buffer
at0 through its original allocator+10. It leaves the caller's outer storage
intact. Shared ScriptContext cleanup889700/889780 remains a different object.
This method proof does not bind new callees or authorize a native invocation.

The17B actual initializer is at`2C4DC3F..2C4DC50`: its LEA resolves to typed
descriptor table`480C2A0`; the constructor count remains609. No descriptor,
localization literal or keyword bytes were included. Existing named cache
metadata contains no actual descriptor-prefix bytes and no named tax row.

Root then executed only207 semantic bytes of `2872480..287254F`, once,
`SOURCE_CAPTURE_MATCHED`, about0.8948s/1freshread/nativecalls0. Its result is
`aggregate-map01/SELECTED-AGGREGATE-CAPTURE.json`. It initializes the output's
ID and value buffers, evaluates each parsed declaration in the supplied
ScriptContext, merges/finalizes into that output and returns the output pointer.
Its constructor/declaration/merge/finalizer calls are recorded roles; this
capture does not separately qualify their bodies.

The numeric receiver distinction matters for this implementation. Cached
old ordinary-ID source searches uint16 IDs at`RCX+0`, count`RCX+C`, and reads
the matching int64 from the pointer at`RCX+68`. Therefore the standalone
owner output is passed **as a whole**, not as output+68. Existing
`battle_current_own_nested_modifier_reader.hpp` uses Character's outer
aggregate+68 to reach its nested modifier object; that outer offset does not
apply again to the independently constructed task owner output. Cleanup and
the actual constructor show the standalone0/68 parallel-buffer relationship.

The held37B getter source ends just after the ordinary branch's first
`movsxd r9,[RCX+C]`; only itsFFFF-to-zero return is wholly inside those37B.
Real tax IDs take the remaining local binary search. The next126B plan closes
that local branch without re-reading the prefix, expanding a callee or
replaying any qualified Army/Battle fixture.

```mermaid
flowchart TD
    S[Stock Collect Taxes owner modifier domain_tax_mult] --> Q[Existing selected-seat private Council query]
    Q --> T[Actual4 full task / owner / incumbent / requested seat]
    T --> C[Original scopes40 and TaskType / frozen39 shared source]
    C --> E[Root matched owner evaluator31ABDF0,299B]
    E --> M[Owned evaluated modifier aggregate]
    M --> G[Held numeric getter23036E0 prefix, whole owner output]
    I[Tax keyword / descriptor numeric ID] -. NOT_HELD: bounded locator then named record .-> G
    E --> A[Matched207B constructor: IDs0 / values68]
    A --> G
    G -. ordinary-ID local continuation126B pending .-> N[Binary search and signed int64 / absent zero]
    M --> D[Matched173B cleanup: release original internal allocations]
    N -. pending numeric ID .-> L[One optional current-tax numeric leaf]
    D -. pending ID and local numeric source .-> L
    L -. FIRST NOTRUN .-> W[Whole producer and sole registered consumer]
    W -. Root paused value pending .-> P[Production decision input]
    P -. counterfactual candidate / task-switch growth unknown .-> U[Full tax-versus-development utility]
```

## Smallest existing interface

Use existing `ck3_query_council_final_gates_private_v1(expected_revision,
position_key="councillor_steward")` or its underlying private composition
query. The final-gates operation first runs the same selected-seat transaction.

`ck3_12004_council_candidates.cpp:132–195` resolves the requested position
through2684EE0, round-trips the task ID, validates owner and PositionType
pointer, and copies the **requested** stable key. `before.active_task` and
validated incumbent are available near391–411; existing recapture471–478
remains the final transaction check. This bypasses the unresolved dynamic
PositionType CString key.

The current actual4 full-root `ReadCouncilProjection` at
`ck3_12004_campaign.cpp:1226–1243` instead returns empty positions with
`actual4_council_position_key_source_unavailable`. Therefore the qualified
ordinary job-progress consumer is source integration, not proof that actual4
full-root job rows are live. Do not reconstruct all positions for this tax
leaf. Current selected-seat task context can travel with the numeric leaf.

After native inputs close, add one optional current-task owner tax component
to the existing selected `position` DTO. Preserve task identity/key/frozen
with that observation; distinguish evaluated component from effective
application when frozen. Keep available signed raw/scale100000 and explicit
unavailable reason, including legal native zero. Do not change outer query
availability, CanSend, candidate selection, root readiness, CLI or tool list.

The insertion must survive `ProjectCouncilCompositionCandidatesPublicV1`
near516. The existing actual4 serializer521 and private mailbox codec carry
the whole DTO. Extend only the optional position field admission in
`council_composition_candidates_contract.py:58,216,324`; private transport
already forwards and normalizes complete `position` for both private tools.

## Remaining bounded source, no speculative call

External package:
`Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261008/council-current-task-domain-tax/`.

Completed owner299B/cleanup173B/locator17B/constructor207B receipts are reused;
no recapture. `NEXT-NUMERIC-LOCAL-CONTINUATION-126B-PLAN.json` declares only
actual`[2303705,2303783)` corresponding to fully cached old
`[2303725,23037A3)`. New begin is the next PC of the held getter's ordinary
branch prefix; corresponding cached ordinal must agree. The126B old local
continuation has no call and ends atRET. The already-mapped prefix37B,13B
padding and following membership method are excluded.

`tax-id-metadata/NEXT-TAX-DESCRIPTOR-PREFIX-6272B-PLAN.json` declares a fixed
112 pointer-record prefix`[480C2A0,480DB20)`,56B per row, one read. This covers
the previous named resource group at ordinal105/106; it does not assert that
the tax row is inside. Each pointer record supplies localization VA at0,
uint16 numeric ID28 and uint32 keyword2C. No pointer is automatically followed.

A separate metadata lane found no held descriptor-prefix bytes. Record reads alone
do not name the tax ID: the actual selected localization/keyword association
still needs its own exact literal/keyword source. There is no guessed tax row,
piety97 alias, automatic whole609-table scan or automatic pointer-following.

These pending plans use Root central shared claims, retain member/immediate
operands, and stop on NOTMATCHED. Any additional necessary source gets a
separate finite manifest; method match labels do not close all callees.

## FIRST and capability boundary

Implementation and FIRST remain **NOTRUN**. Once the native numeric input and
owned lifetime close, one new whole producer must exercise actual
`ReadCouncilCandidates12004`, the leaf, `SerializeCouncilCandidates12004`
and private mailbox envelope. One new registered consumer consumes those
same compiled wires through real Driver private transport, strict position
normalizer, and existing private final-gates MCP tool. No hand-composed outer
wire or replay of old Council/piety/native GREEN cases supplies tax evidence.

This input supports current task benefit/resource decisions. It does not
pretend a new Council assignment, an applied gold delta, a vassal/faction
intervention, a paired replacement quote, or M4 completion. Ordinary mainline
gameplay and the existing explicit17520-hour M4 window continue independently.
