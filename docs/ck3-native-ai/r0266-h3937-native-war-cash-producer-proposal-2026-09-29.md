# R0266: H3937/H3911 native war-cash producer boundary

Status: **no new formal amount; all five war-cash amounts and the horizon remain
`null`**. This is a no-screen, no-game-call research proposal for CK3
1.19.0.6 `ck3.exe` SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
The H3911 DLL SHA is `C71F6A5DFE8D23374B5B73F9DFA18AD9455CFF087D36EC93D2D29F7F610E8786`;
the distinct H3937 source manifest identifies DLL SHA
`A8EAC0CD5BEEDF90778C76C14679629A96EDD4F7E7B398EB035B865F776786E9`
and source commit `7265d40b280766390fd9a0cd187903f32d76a246`.
Neither DLL identity or receipt can be carried into the other pair.

The fixed WAR H3937 `RECEIVER-H3937-STATIONARY-READONLY-CANDIDATE-STATUS-v4.json`
sets `decision.selected_step=null`; its source paused-war excerpt does not
contain the complete war/army routes. H3937 therefore has **no selected action
to quote**, and the explicit `null` does not prove a zero-fee action. H3911 did
select `query-war-termination-options-16777231`, but its
query receipt is historical and the [bounded DLL audit](r0326-h3911-war-query-cash-static-audit-2026-09-29.md)
does not close evaluator side effects or deferred charges. It cannot price a
later movement, mercenary hire, or H3937 date decision. The fixed WAR
`RESPONSE-ROBERT-WAR-LIQUIDITY-POLICY-H3911-v1.json` explicitly defers the
war floor, horizon, future bound, and risk amount.

## Candidate native sources

| Need | Exact-build observation | Safe current use and unresolved gate |
| --- | --- | --- |
| Selected immediate action | Existing `PreviewMoveArmy` returns a route and legality, not cash. The stock `FleetPredictionMapIcon` calls calculator `0x22775F0` for a set of 12-byte prediction records; its cached fee raw is at `*(icon+0x68)+0x78`, scale candidate 100000. `GetEmbarkCost` returns that cached row. `MercenaryCompany.GetCostDesc` at callback `0xC1F600` produces a formatted string, not a proven raw hire/extension price. | Do not invoke the fleet calculator or mercenary GUI getter. The fleet function's transitive and optional-details effects are unclosed; the icon may aggregate several units and has no proven link to the selected route, payer, or debit stage. There is no bridge mercenary quote/command ABI. A movement with no observed embark still needs exact route and no-other-fee proof before zero. |
| Current military upkeep | `MilitaryView.GetGoldMilitaryExpenses` reaches `0x290A720`; the topbar expense builder `0x28DC635` also calls it. The GUI current getter `0x11F7D00` reaches `0x11F7370` and writes view state. A deeper character maintenance-vector candidate `0x290BA70..0x290BDAC` takes caller output and character pointers, clears 0x50 output bytes, and reads character `+0x1B8`; contextual helper `0x2395370` has an unresolved indirect call at `0x23953C1`. | No active bridge call is approved. Passive `MilitaryView`/topbar memory reads are diagnostic rate candidates only, after unique instance, full player identity, natural refresh completion, Q100000 layout, full row tree, and paused native-frame checks. GUI tick equality is not refresh completion. A full-player military rate covers forces beyond one WarID and must not be assigned to a single war without an explicit allocation policy. |
| Actual debit and due time | The bridge's native `ReadSnapshot` gets played-character gold raw from extension `+0x100` at scale 100000. `ReadMonthlyGoldIncome` is an income observation, not a military-breakdown or payment-schedule producer. The script `on_army_monthly` runs on an army-ID-dependent 30-day cadence, which does not establish treasury debit timing. | Use native before/after gold to observe a **net** change only. Isolating military payment requires all concurrent income, other spending, war actions, and auto events plus a proven settlement stage. Current and all-raised monthly rates cannot be divided by 30 or declared a one-day upper bound. |

Exact static verifiers `verify_war_cash_embark_quote_candidate.py` and
`verify_war_cash_maintenance_candidate.py` passed against the EXE in this
review; maintenance also passed under `python -O`. Both explicitly output
`safe_to_call_from_live_bridge=false`. The maintenance helper hashes are
`A6D40023A1B422DF749610533E403A8BE054A46D952D36D3785973A5485F6B2F`
for `0x290BA70..0x290BDAC` and
`6AE006D6CA955A245D37429596864593CAC71625AC4A81728A8D46D0D45BB7B9`
for contextual helper `0x2395370..0x2395604`. A separate bounded disassembly
of `0x290A720` shows writes to its caller's output and virtual/helper calls;
it is not a proved pure read of existing state.

## Bounded implementation order

1. On a **new current** exact pair, freeze the formal `selected_step`, typed
   arguments, actor and payer CharacterIDs, WarID set, army/company IDs,
   route origin/target/full route hash, preview sequence, paused snapshot,
   episode, public/native revision, date, PID+creation, and EXE/DLL hashes.
   Reject an absent or explicitly `null` selected step; H3937 has the latter.
   Neither case is a zero-fee quote. Verify payer separately from unit owner
   and from a GUI subject handle.
2. Extend a diagnostic read-only receipt using existing native snapshot gold
   and route output; any topbar or MilitaryView sampling remains passive
   `ReadProcessMemory`. Record quote object identity, source bytes and natural
   refresh completion evidence separately. Return `formal_cash_eligible=false`
   and `immediate_war_action_cost_raw=null` until a command-specific numeric
   quote is independently authenticated. Do not call the GUI refresh/getter.
3. Audit the complete transitive effects and argument ABI of `0x22775F0`
   (including null optional-details path), `0x290BA70`/`0x2395370` and their
   indirect targets, and the numeric mercenary hire/renewal transaction path.
   Only a proved read-only function with a stable actor/payer/action identity
   may become a bridge quote. A formatted tooltip or cached prediction is
   insufficient. Keep query-zero approval separate from movement pricing.
4. To convert a monthly rate to a bounded future cash claim, observe the next
   real debit window with native gold before/after and independently account
   for income and other transactions. Establish the maximum number and size
   of maintenance/replenishment/fleet/contract deductions before the explicit
   next forced recheck, then add separately priced planned actions and a
   versioned, non-overlapping risk policy. If any due time, amount, payer,
   source scope, or policy is missing, keep `future_war_cost_upper_raw`,
   `future_risk_budget_raw`, and `policy_minimum_gold_reserve_raw` null.

The owner request ledger still has no complete priced pending-transaction
scope. `pending_war_cash_raw` remains null even when its recorded subset is
empty. None of these diagnostic paths authorizes a date advance or a joint
construction budget decision.
