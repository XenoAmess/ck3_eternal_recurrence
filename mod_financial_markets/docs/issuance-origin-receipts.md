# Immutable fresh-issuance origin receipts

Fresh successful registrations can now retain a constant21-field origin receipt on the coin.
This records a real historical fee and engine identity snapshot; it neither funds nor admits an issuance.
All old business AST, money calls, fee amounts, probabilities and scheduler paths remain unchanged.
Legacy coins, failed fees, failed coin construction and missing/malformed provenance remain unknown.
No migration, backfill, daily log, global scan, new story type, observer or automatic action is added.

The original registration caller clears private trace data, then the PRIMARY account takes a
before-funding snapshot immediately before the original `ensure_funds`. The two next hooks sit
immediately before and after the existing real `xfm_finance_fee_effect`. The latter's actual
success result must be1. Stored private free debit and exchange fee credit must each equal the
original100c/500c request. Primary topup must equal actual personal-gold reduction times100;
gold during the fee and private reserved cents must remain unchanged. Source/account IDs and
legal holder/beneficial owner must still match the same original actor and PRIMARY account.
Only the original caller's successful15000-unit construction and `xfm_issuer_result=1` publishes
the coin receipt, version last. Temporary actor fields and private aliases are always cleared.
Re-entry cannot overwrite an existing receipt. The old `xfm_registration_paid_cents` stays a
nominal terms field and never becomes independent proof merely because it is positive.

`is_ai` and `is_landed` are actual engine predicates sampled during the fresh registration.
Highest tier is independently sampled using installed vanilla `highest_held_title_tier` equality
syntax:1barony,2county,3duchy,4kingdom,5empire,6hegemony; -1 means no known equality matched.
Landlessness is the separate native boolean. It must not be inferred from tier, player identity,
numeric CharacterID, current controller or the mutable state of a later heir.

Receipt fields:

- `xfm_issue_receipt_actor`
- `xfm_issue_receipt_coin_id`
- `xfm_issue_receipt_day`
- `xfm_issue_receipt_fee_cents`
- `xfm_issue_receipt_fees_after`
- `xfm_issue_receipt_fees_before`
- `xfm_issue_receipt_free_after`
- `xfm_issue_receipt_free_before`
- `xfm_issue_receipt_free_pre_fee`
- `xfm_issue_receipt_gold_after`
- `xfm_issue_receipt_gold_before`
- `xfm_issue_receipt_gold_pre_fee`
- `xfm_issue_receipt_highest_tier`
- `xfm_issue_receipt_is_ai`
- `xfm_issue_receipt_is_landed`
- `xfm_issue_receipt_payer`
- `xfm_issue_receipt_payer_id`
- `xfm_issue_receipt_reserved_after`
- `xfm_issue_receipt_reserved_before`
- `xfm_issue_receipt_topup_cents`
- `xfm_issue_receipt_version`

Gold fields are native script gold units with their exact fixed-point fractional part; all `*_cents`
and free/reserved/fee counters use integer cents. `day` is the existing financial day. `actor`,
`payer` and their permanent ID snapshots retain the original issuance identities even if later
ownership changes. A consumer must verify version1, matching coin/account IDs, source/build
provenance, all required fields and the money equalities, rather than trust the version alone.

The existing exact-story reader already retains these fields and their original types/lexemes.
The general financial audit DTO is unchanged and does not project them. An absent version or
field is unknown, never zero/false. A new live receipt is actual financial evidence only after
ordinary business and independent physical SAVE readback; authored script tests are software
credit. Existing redemption3SAVE/35day gates are unchanged, and no extra business action is
authorized by this receipt implementation.

Offline tests execute actual registration, receipt, finance `ensure_funds`, finance fee and
their value/trigger AST. Engine admission, account/story allocation, mint and public-index
operations are explicit fixture ports; these do not claim engine, mint, capacity or GUI acceptance.
The test-only fixed-point interpreter rejects unknown operations. Tests cover real mixed funding,
landless AI, low-rank AI/human snapshots, all six tier equalities, failure/no-receipt paths,
wrong-primary/counter/reservation evidence, legacy and duplicate calls, transient cleanup and
the old business outcome after removing only the new receipt hooks.

On 2026-11-20, machine `4-8e1c2f1861` actually ran the ten new methods plus
PublicIpoDiscovery15, CoinResidentCapacity26 and RedemptionScriptContract45:
96 passed, zero failures/errors/skips, original wait0 in46.0902651s.
The changed real runtime manifest and script contract also passed its focused
BuildContract method, original wait0 in7.878085s. Original reports are retained in
[the software evidence](../../docs/maintenance/evidence/2026-11-20-financial-markets-origin-receipts-ci-repairs.json).
At that software cut these identity receipts had not yet been observed in a live physical SAVE;
R0042 used frozen0449 source and receives no retroactive credit.

R0052 later captured all21 original typed fields of coin85 in each of its two physical SAVE
readbacks, within the existing16-target raw reader limit. Independent exact Fraction arithmetic
passed14 checks: historical financial day198, actor47364, AI1, landed1, tier1=barony,
PRIMARY14201/permanent4781, personal gold48.39355→47.39355, topup100c,
private free0→100→0, reserved0 unchanged, and exchange fees34761→34861.
The historical registration really paid100c from1 gold; all21 fields remained identical across14days.
This is a paid landed baron AI positive, not a landless AI or fresh R52 issuance claim.
Current controller and system-account holder were not substituted for the historical actor.
[Actual receipt, exact arithmetic and source pins](../../docs/maintenance/evidence/2026-11-21-financial-markets-coin85-paid-baron-ai.json).
