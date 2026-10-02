# R0266 H3937: owned pending source bytes, diagnostic only

Status: **RED for a real war-cash producer**. The H3937 paused episode is
`native-29829-2bc2d599f7f9`, native revision 3, public revision 4,
`date_raw=53219928`, WarID `16777231`. Its fixed WAR selected-step receipt
explicitly says `null`. There is no matching selected movement or hire to
price. Neither that null nor an empty owned ledger proves a zero fee. All five
formal war-cash amounts and the budget horizon remain `null`; the M5 formal
receipt remains false. This candidate does not alter the H3937 game state.

## Frozen owned-writer subset

`inspect_owned_pending_source_bytes_v1` is a read-only inspector for the
existing append-only `war_cash_pending_ledger_v1` journal. Given a paused
snapshot, exact checkpoint bytes and SHA-256, exact ledger file SHA-256, and
one exact evidence file for every unresolved reservation, it checks the
journal hash chain, played CharacterID, episode, WarID, native/public revision,
snapshot ID, date, and each quote's checkpoint and frame. The ledger and each
quote file are capped at 4 MiB; the checkpoint is streamed with a 256 MiB cap.
It makes no CK3 or GUI call. If any supplied bytes or identities differ, the
inspector raises instead of emitting a number. If the owned ledger is absent
or has no unresolved reservation, its candidate amount is `null`, never zero.

On a fully matching **synthetic** fixture, the inspector emits
`recorded_unresolved_quote_sum_raw_candidate=125000` for one writer. It always
emits `pending_war_cash_raw=null`, `formal_cash_eligible=false`,
`complete_writer_coverage_proven=false`, `native_quote_semantics_proven=false`,
and `same_frame_native_postcheck_proven=false`. A SHA proves that the supplied
price evidence bytes match the journal's claim. It does not prove those bytes
are a pure CK3 quote, use the correct payer or action, reflect the payment
stage, or include all other game/driver writers. A source checkpoint hash in
the journal is likewise a writer claim; checking file bytes does not itself
prove the native bridge used that checkpoint. The diagnostic is intentionally
ineligible for the five formal M5 cash fields.

## Exact native ABI gap

The [H3937 producer audit](r0266-h3937-native-war-cash-producer-proposal-2026-09-29.md)
identifies three tempting paths and why none is a safe cash source now:

| Path | Missing proof before an amount could be formal |
| --- | --- |
| `PreviewMoveArmy` | It returns route/legality, not a cash amount. H3937 selected action is explicitly null. A future quote needs a current typed step, complete route, payer and WarID identity, numeric command price, and no-other-fee proof for zero. |
| `FleetPredictionMapIcon` fee at `*(icon+0x68)+0x78`, calculator `0x22775F0` | The fee is a cached GUI prediction; prediction records may aggregate units. The calculator's optional-details and transitive side effects are unclosed. Icon/record-to-selected ArmyID, route, payer, live frame and debit-stage mappings are absent. Calling it from the bridge is not approved. |
| `MilitaryView.GetGoldMilitaryExpenses` / `0x290A720` | A rendered monthly rate is not an actual debit or one-day upper bound. The function writes caller output and has unresolved virtual/helper calls. The passive topbar layout/refresh gate was RED in H3911 attempt-05. Even a valid player-wide rate needs allocation, next debit timing, other transactions, and a bounded recheck horizon. |

The GUI mercenary `GetCostDesc` callback `0xC1F600` yields formatted text;
there is no proved numeric hire/renewal quote and command ABI. Native
`ReadSnapshot` treasury raw before/after is only a net change while income
and other deductions remain unisolated. Neither method can fill a war-cost
field by subtraction or monthly-rate division.

The focused journal tests run 13/13 in normal Python and 13/13 under `-O`.
They cover exact byte matches, changed quote/checkpoint/ledger bytes, stale
frame, strict WarID typing, and absent/empty ledger semantics. No H3937 live numeric quote was
observed. To graduate the subset, a producer must give a current typed action,
an independently audited pure numeric native quote and actual receipt, then
prove all relevant writers and replay/postcondition reconciliation. A policy
owner must separately supply the minimum reserve, horizon and future risk
method. Until then the request in the fixed OneDrive `WAR/R0266-H3937-WAR-CASH-20260929/`
directory remains open.

## 2026-10-02 provenance addendum: distinct H3937 frame records

PR [#449](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/449) head `3bc267e0d3c565249f9a93ac24e33acb0a44ded7` preserved a different opening identity for this historical source note: snapshot `native:4`, native revision `4`, public revision `5`, with the same episode/date/WarID. The existing opening above records native revision `3`, public revision `4` and remains unchanged. These source versions are retained as distinct records; matching date/episode alone does not make their frame identities interchangeable. Neither record supplies a live numeric quote or a formal cash producer.

This addendum imports provenance from the frozen CK3 1.19.0.6 research branch. It does not install its driver lifecycle hooks or candidate cash contracts in the current 1.20 runtime, and does not reclassify the synthetic writer-subset tests as native amount evidence. The complete source response is retained under `historical_pr449_20260928_20260930` in the [R0266 response](../autonomous-agent-progress/coordination/war-requests/responses/WAR-ROBERT-R0266-JOINT-CASH-20260928.json).
