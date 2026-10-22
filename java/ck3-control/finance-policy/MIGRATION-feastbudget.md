# Feast budget leaf migration

This lane provides the pure `FeastBudgetPolicy.observe(Request)` and strict `FeastBudgetCodec.assess(byte[])` in package `org.xar.ck3.control.finance.feastbudget`. It replaces the computation in `activity_feast_stage5_budget_v1.observe_feast_start_budget_v1`; it does not yet switch the original callers. No file reads, Game queries, RPC, ledger writes, native legality, Start submission, or extra service is added. Root integrates the leaf into the existing Quarkus host and the single authority after the complete consumer chain passes.

The adapter must call the original four validated ledger readers under the existing owner and project their current `pending` values into the explicit `ledgers` wrapper. It must not infer clear from a missing field, bypass a reader exception, reuse a stale observation, or treat this result as a complete M5 military budget. Original reader outputs remain authoritative; this leaf has no custody or continuation authority.

## Preserved behavior

- The exclusive paused frame binds actor, native revision, queried revision, date and post snapshot ID. Frame failure wins before the active-war, interaction and spending-intent checks.
- Active war IDs must be positive integers. Missing/null war observation is unavailable. A missing interaction observation differs from an explicit null clear interaction.
- Pending priority is construction, faction gift, first-heir marriage, then child marriage. Any unresolved intent blocks the allocation; zero existing reservations are emitted only after all four readers report clear.
- Gold floor is 20,000,000 raw, scale 100,000. During war, same-frame available maximum monthly gold maintenance allocates exactly 18 months. All arithmetic is exact `BigInteger`; there is no overflow, floating conversion, rounding or assumed future income.
- Unknown war cash reserve remains JSON null; observed zero emits zero and the supporting financial reservation. A peaceful result also keeps the old null reserve. The allocation explicitly does not claim a future-cost upper bound or complete war-cash receipt.
- Output preserves the original status/reason/frame/budget/optional-financial-reservation JSON contract. The Stage 5 value consumer still applies costs, balances, military reserve and legality; this observer alone never returns a Start permission.

The new wrapper is exact-key constrained and versioned `xar.feast-budget-projection.v1`. Existing SDK snapshot, inputs, root and normalized ledger containers are extensible projections. Consumed scalar tokens are validated before domain construction. Boolean, floating or string substitutes for integer identity/amount/scale fields are rejected, including old Python equality loopholes. These stricter token rejections are intentional user-required contract corrections, not reported as byte-equivalent old acceptance. Typed request re-encoding preserves consumed missing/null/value distinctions and omits unrelated SDK fields. Ledger pending payloads are projected to presence only; their content remains in original evidence.

## All known consumers and porting order

| Original consumer | Fields / next port |
| --- | --- |
| `bridge/service.py`, `_plan_private_feast_normal_v1` | Same-frame observer output `budget` into `assess_feast_start_private_v1`, with full observation in opportunity evidence (budget call at original line 3555). |
| `native_auto_run.py`, Stage 5 Start assessment (original line 8164) | Same budget and observation after original post-query same-frame checks. |
| `war_mercenary_consumer_v1.py` (original line 236) | Requires observed status, retains full observation and passes it to `assess_mercenary_reinforcement_v1`. |
| `wartime_construction_cash_v1.py` (original line 234) | Supplies current four reader outputs; allocation is input to the separate construction cash policy. |
| `faction_gift_wartime_cash_v1.py` (original line 133) | Supplies allocation only after current root/commitment check; separate gift policy remains responsible for quoted emergency contract. |
| `war_reinforcement_finance_v1.py` | Imports the 18-month constant; Java counterpart should use `MAINTENANCE_RESERVATION_MONTHS`, preserving its own finance contract. |
| `faction_gift_wartime_cash_v1.py` | Also imports the same 18-month coefficient; avoid a second independent constant during final integration. |

Read original producer tests `test_activity_feast_stage5_budget_v1.py` and the ordinary consumer checks in `test_war_emergency_budget_v1.py`, alongside the source consumers above. The unchanged existing Python consumers remain the compatibility oracle. Consumer integration and real business effects have not been qualified by this leaf.

## Captured regression and execution status

Committed `src/test/resources/feastbudget/original-producer-golden.json`: 30 original producer executions, 37,430 bytes, SHA-256 `bd3aea63baf65c1fcbe36310d629cd3813343ca29e2f3de3b68603db8ec7b338`. Capture observed at `2026-10-22T13:34:51.649028+00:00`, machine `xenoamess-full-tower-eb9d2c1186`; source bindings in the artifact pin producer, resource keys and all four readers. The unchanged real producer ran in an isolated D-volume temporary directory. Actual reader calls established the default empty-directory ledger shapes; dependency seams supplied read-only ledger projections, including synthetic pending variants. No original producer function was mocked and no Game or native interface was used. This is software input/output evidence, not a production ledger or live-game receipt.

Eight JUnit tests consume only this committed golden and Java code. They cover all 30 differential outcomes, typed serialization round-trips, literal integer rejection, wrapper/ledger missing and duplicate keys, invalid UTF-8, interaction presence, exact uint64-sized maintenance multiplication, and extensible SDK containers. Maven execution is reserved to the shared M7 builder; this lane has not run Maven or claimed Java tests passed. Persistent CI and actual caller replacement remain Root integration work. Source/golden budget is below 192 KiB; D scratch was removed by the capture's temporary-directory context.
