# G2 ordinary campaign / R796 submitted-pending handoff

Handoff date: 2026-09-17 (Asia/Shanghai)

Scope: R795/R796 ordinary WarID5 exit, response-window repair, preview/Council queue, Git and live-state boundary.

Authoritative G2 contract: [`../autonomous-agent-progress/g2-requirements-v1.json`](../autonomous-agent-progress/g2-requirements-v1.json)

## Current conclusion

The bounded ordinary preview remains the only user-startable delivery and stays GO. Formal G2 remains **1/8**, GEN-034 remains **2/4**, and Council remains **1/4**. R796 did not end WarID5 and did not create a durable post-action checkpoint.

The immediate strategy defect is repaired statically by `836ad237`: a submitted white peace may require the native 4-9 day AI reply window. When every exact military route is unsafe, the planner now advances one day at a time through the tenth-day observation boundary, never requeries or resubmits, and fails explicitly if the old WarID remains. This repair has not yet received a new live run.

## R795 harness RED

R795 used the prepared R794 history260 staging and source `67f65d820bad0945aeeaf7e09786cd5f46c55bfb`. No-launch prepare/rebind/preflight was GREEN, with:

- environment SHA-256 `5104D7E4D7C7207553B1F247AAE11E1866AB60E21DEA1BAD4B4484AADE7F5A64`;
- target driver SHA-256 `8D17FCDAA41BF88CB752641408C3B2B5B28660755A072510A22A6563089A325F`;
- unchanged checkpoint SHA-256 `55A51F5D6329C2682C9108FB190BDE10592BA19EBC4AF518671290E17B1FDE82`;
- rebind receipt SHA-256 `93338E77D55339393D403518927FA506BEAF7640972E44E3C55177ADEDEFFBC0`;
- preflight report SHA-256 `9ABBB6219658526794899D88EF3CF761BA3E32B952E69E69A1BC4B8C947863C1`.

The formal run used outer timeout 600 with readiness timeout 720. It stopped at 602.96 seconds before semantic readiness, after transport and exact adapter readiness but before any semantic turn. Query/action/checkpoint counts are all zero.

- report: `D:\ck3_mod_rewrite_process_assets\g2-r795-cold-stage-r794-h260-20260916T162722Z-845327f5\formal-r795\formal-report.txt`
- report SHA-256: `6F53E81DD823D4B53671F9AFA8C0141FD064C890D00CEB13A19AB52C37657625`
- receipt SHA-256: `6F4A70A1F57B5A99B9FD9AE55EE1E25ABEE3502ABE62F8D4E29A1300218952FB`
- seal SHA-256: `164B1BD5DEC374B45C50C26C188A3C2157C0B7A6CC5F1F619C0807C9A953118B`
- closed ledger SHA-256: `646360938170649DBBBE40F35D3EA84BE2F6AA20A50B981FCE979330555770AF`

The operator contract now records that the outer timeout must exceed readiness and cover the measured startup tail. This host already measured 636.443 seconds, so R796 used 810/720.

## R796 production result

R796 used the same staging root and a new process. Cold restore correctly truncated abandoned R794 history261-264 back to checkpoint history260/date `53149872`, then appended its own restore lineage.

The six-turn sequence was:

1. fresh `query-war-termination-options-5`;
2. `life-advance`, six game days to `53150016`;
3. fresh termination query;
4. exactly one `offer-white-peace-5`, phase `native_war_de_jure_no_safe_route_white_peace`, ACK submitted and typed result `submitted_pending`;
5. exactly one `life-advance`, one game day to `53150040`;
6. terminal `native_war_no_safe_exact_route`, with old WarID5 still present.

The frozen response row had `decision_status_raw=0`, `would_accept_now=true` and AI acceptance raw `2200000`. No duplicate offer, surrender, declaration or unrelated gameplay action occurred. The source checkpoint stayed unchanged; final driver history was 269.

- report: `D:\ck3_mod_rewrite_process_assets\g2-r795-cold-stage-r794-h260-20260916T162722Z-845327f5\formal-r796-white-peace\formal-report.txt`
- report SHA-256: `F92AFE0EA0672073D884EA8FD54416E031745C5D48E6860A5C2D16E2D7D52A09`
- receipt SHA-256: `17D4EA6A9BE4B25B12F5653F6138E53076D04777DA96C3E3590C2E0E5DA4A398`
- final driver SHA-256: `1502679F7E3A1D6376C90F670CB33171F2B949D27649CBC64CCD200383922312`
- seal SHA-256: `A7A20DBAB361C8E1F40427C6846D6C4A52C82C68038E7469DF8C0257153B561A`
- closed ledger SHA-256: `0E8BC7CD41A4CDE774A85E6BBF4281C1D724B30B0ACA1B7D777CACE86434ED81`

CK3 and injector inventory returned to zero.

## Root cause and static repair

The implementation only forced one same-day response advance. From the next game day onward it restored ordinary military OODA; in this exact scene every route remained unsafe, so the planner terminated before the known asynchronous reply window could elapse.

The native evidence was already closed: `_character_interactions.info` has `ai_min_reply_days=4 / ai_max_reply_days=9`, and the prior production white-peace loop observed the old WarID disappear on the tenth daily advance. Commit `836ad237` therefore changes only the no-safe-route continuation:

- a matching `submitted_pending` history row remains the one-shot fence;
- elapsed days 1 through 9 select one `life-advance` each;
- no termination query or offer is selected inside that response window;
- at day 10 with the old WarID still present, the planner returns `native_war_white_peace_postcondition_unresolved` and no action;
- the existing 720-raw proposal cooldown remains unchanged.

Validation:

- focused normal: 3 tests, 2 subtests GREEN;
- focused `python -O`: 3 tests, 2 subtests GREEN;
- full `test_gameplay_bridge.py`: 231 tests, 82 subtests GREEN;
- `git diff --check`: GREEN.

No native ABI, MCP schema, public capability or `open_kaishek` adaptation changed.

## Live recovery boundary

Do **not** launch another CK3 round from this handoff without resolving the timeline boundary below.

The only durable save is the pre-action checkpoint at history260. R796's offer and response-day advance exist only in the sealed driver tail; the process is gone, and cold restore intentionally truncates post-checkpoint history. Consequently:

- retaining the R796 action row would falsely fence a save in which the proposal never happened;
- truncating it and immediately offering again would be a new action on a rolled-back timeline, but the inherited handoff explicitly forbids retrying an unconfirmed proposal without a recovery decision;
- there is no durable post-action save from which a read-only confirmation can continue.

The next live owner must first record an explicit decision that the history260 checkpoint is an authorized timeline rollback and that one new, fresh-frame proposal is permitted under source containing `836ad237`. If that authorization is not present, remain static-only. Do not infer permission from the code fix.

If replay is authorized, require all of the following in one bounded chain:

1. current remote master and a clean source checkout containing `836ad237` or its descendant;
2. no-launch rebind/preflight against the unchanged history260 pair;
3. `timeout/readiness` no smaller than the measured-safe 810/720 pair unless newer host measurements justify another pair;
4. one fresh CK3 process and at most one `offer-white-peace-5`;
5. daily response observation with no duplicate query/offer inside the native window;
6. independent old-WarID disappearance plus observable postwar state;
7. a post-action/postwar checkpoint and complete process cleanup;
8. a new round cold-restoring that checkpoint, proving the old action is consumed and not repeated.

Any unknown state or RED is sealed and not retried unchanged. Council remains behind this chain.

## Git and workspace

- clean integration clone: `C:\workspace\g2-war-r794-no-safe-exit-20260917`
- working branch: `codex/g2-r795-white-peace-20260917`
- response-window source commit: `836ad237`
- runtime artifacts remain under `D:\ck3_mod_rewrite_process_assets`; do not copy them into Git
- do not reset or clean the shared `Z:\ck3_mod_rewrite` workspace

After this handoff/report commit is pushed, use the resulting remote `master` as the next Git baseline. The preview artifact and formal requirement counts remain unchanged.
