# Price oracle and model-index runtime contract

Machine provenance: `4-8e1c2f1861`, installed CK3 1.21.0 (Florin), Steam build 26622941. These are implementation contracts; source compilation, native loading, business correctness, save/reload and measured performance require separate evidence.

## Reference and execution

All prices use integer gold cents per contract lot. For coins a lot is 100 coins. `xfm_last_price_cents` is the last executed spot trade; `xfm_best_bid_cents/xfm_best_ask_cents` describe funded spot orders. Neither is a settlement reference by itself. `xfm_index_cents` is the qualified reference. `xfm_mark_cents` is the common daily settlement mark, currently equal to the qualified reference. An executable liquidation price is the price and quantity actually filled against an independent funded futures counterparty; no oracle value promises a buyer, gold or repayment.

The native callback `xfm_oracle_record_trade_effect` runs on the coin only after a genuine funded spot execution. Its immutable call context is `scope:xfm_trade_coin/buyer/seller/buyer_holder/seller_holder`, where buyer/seller are account stories and holder aliases are their economic beneficiaries, preferring `xfm_beneficial_owner` to the technical custodian. Numeric scope values are `xfm_trade_price_cents/lots/notional_cents/day`. A trade rejected as an oracle sample remains a real spot trade.

## Bounded sampling and qualifications

Each coin stores one current bucket, at most 16 participant references and 14 fixed completed-day slots; no trade story is created for this oracle. Each slot has an observation day, an integer VWAP and participant count. The fixed scan is 14 slots per coin per financial day; there is no AI by coin matrix.

A sample requires positive price/size, at least 100 cents of actual notional, two different economic beneficiaries, neither beneficiary equal to the coin controller, and neither beneficiary already used in the same coin's current-day sample set. At most eight samples are accepted daily. The first qualifying samples are used in execution order; this bound is disclosed and does not claim to identify collusion between distinct people. Each sample's VWAP weight is capped at 1,000 actual lots; excess real volume still remains in the exchange's normal volume statistics.

A completed day qualifies with at least four accepted trades/eight distinct beneficiaries and at least 1,000 cents of weighted notional. Its VWAP is `floor(sum(price * min(lots, 1000)) / sum(min(lots, 1000)))`. Current incomplete days never determine settlement.

On rollover to financial day D, the oracle publishes the actual closed bucket's accepted-sample volume as `xfm_last_completed_qualified_volume_cents` with `xfm_last_completed_volume_day` before resetting `xfm_qualified_volume_cents` for D. The listing demand window consumes this publication only when its day is exactly D-1 and newer than `xfm_last_listing_volume_day`, then records that consumed day, including a genuine zero-volume day. Repeated hooks cannot count it twice; current-day trades, missing publications and older skipped buckets are excluded rather than replayed or relabeled. This volume follows the sample eligibility and capped weight above; it does not require an entire day to qualify as a settlement reference.

The reference takes valid completed days from the latest 14 calendar days, removes exactly one highest and one lowest daily VWAP, and floors the mean of the remaining values. Seven valid days authorize leverage up to 3. All 14 valid days, at least 112 participant-day observations, and at least 30 days since listing authorize leverage up to 10. These are single-venue limits. The player can choose lower supported leverage values. No present producer claims multiple independent venues or authorizes 20 times leverage.

The latest qualified complete day must be at most two days old. Fewer than seven valid days or stale observations set quality and maximum leverage to zero. Previously reliable index/mark values remain historical values; they do not authorize new risk, termination or a zero-price settlement. Obligations and dispute claims remain outstanding while pending. Genuine large independent trades influence daily VWAP and therefore later reference prices; the index is neither permanently fixed nor directly set by propaganda.

| Field | Meaning |
| --- | --- |
| `xfm_oracle_quality` | 0 pending; 1 single venue; 2 actual multiple independent venues (no current producer); 3 disclosed model index |
| `xfm_oracle_day` | Financial day of the current publication/computation |
| `xfm_oracle_last_valid_day` | Most recent valid completed trade day; model indexes use their actual observation day |
| `xfm_oracle_valid_days` | Number of qualifying completed days in the current 14-day coin window |
| `xfm_max_leverage` | 0 pending, 3 initial mature coin, 10 mature liquid coin, 5 model index |
| `xfm_oracle_reason` | 0 reliable, 1 insufficient observations, 2 stale reference |
| `xfm_oracle_model_index` | 1 only for a model index, 0 for a coin |
| `xfm_oracle_source_id` | 1 = `spot:xfm-central-exchange`; 2 = `model:xfm-fixed-county-basket-v1`; asset ID remains separate |
| `xfm_oracle_reliable_trigger` | Current publication, positive reference and mark, and quality above zero |

Issuer delisting/termination must consume the reliable trigger, never merely a historical positive mark. Unreliable delisting claims remain pending. Market game rules may further restrict opening risk without deleting existing obligations or blocking legitimate settlement.

## Three model indexes

These are cash-settled Mod observation indexes, not native floating grain prices, minted commodity inventories or physical redemption promises. IDs are `index:grain`, `index:military` and `index:trade`. Native index stories are `xfm_oracle_index`, registered in `xfm_index_registry`; globals are `xfm_grain_index/xfm_military_index/xfm_trade_index`. `xfm_index_id` is respectively 1, 2 or 3 and `xfm_asset_kind = 2`.

At first initialization the basket records up to 32 distinct capital counties of independent rulers, ordered by primary title tier. The recorded county identities remain fixed. Succession changes the county's actual holder, not the membership. Missing holders are excluded from that day's sample. No global daily replacement scan is performed; fewer than eight observed counties makes the model pending.

Let P be floored mean prosperity, C floored mean control, both bounded to 0..100, and W be floored war share in basis points, 0..10,000. The raw daily model, floored and bounded to 3,000..30,000 before denomination, is:

- Grain: `10000 + 0.4W + 40(100-C) - 50P`.
- Military supply: `10000 + 0.8W + 20(100-C) + 20P`.
- Trade: `10000 - 0.5W - 30(100-C) + 80P`.

Newly created index stories persist `xfm_model_quote_divisor = 100`. On each successful county observation, publication computes `floor(raw_model / 100)` once, before assigning the same cents-per-lot value to both `xfm_index_cents` and `xfm_mark_cents`. Thus the published model range is 30..300 cents (0.30..3.00 gold) per lot. Initial price remains zero/unqualified until the first sufficient observation. An insufficient observation preserves the historical quoted mark but removes current qualification. The raw county formulas and source ID `model:xfm-fixed-county-basket-v1` remain the same; denomination is separately persisted and selected by the SAVE auditor.

An existing index without this field keeps its original 3,000..30,000-cent unit. There is no backfill, rebasing, replacement of permanent asset IDs, or rewrite of existing orders, balances, position marks, settlement journals or claims. All contracts for that legacy asset, including later contracts, continue in its legacy unit. A same-state cold comparison retains the optional divisor field and must detect its loss or change. The Java reference uses explicit divisor 100 for a new index; the original constructor retains legacy divisor 1. This is still a source contract, not proof of actual SAVE encoding or reload.

One index lot is a cash contract at its displayed gold quotation, not 100 physical goods. Variation is `(new mark - prior mark) * lots` in cents; a one-lot move from 1.00 to 1.10 gold transfers 0.10 gold before fees. Leverage changes required collateral, not the cash value of a lot or that variation. The existing UI converts cents to gold once for mark, index, limit and depth; no additional UI division by the story divisor is applied. Coin lots remain 100 coins and their denomination is unchanged.

At model mark 100 cents, the 120-cent upper order band requires 121 cents for one lot at 1x, 41 cents at 3x, or 25 cents at 5x, including the rounded fee reserve. Actual fill collateral follows the real resting execution price. The unchanged AI five-percent budget plus five-gold living reserve therefore requires at least 29.20 gold of legal personal liquidity at 1x or 13.20 gold at 3x. These are calculated eligibility thresholds, not an observed count of funded AI or available counterparties. Fixed real-notional liquidity thresholds for perpetual funding remain unchanged; small contracts do not manufacture qualifying volume or an executable close.

These disclosed formulas intentionally respond differently to war, disrupted control and prosperity. Quality is MODEL_INDEX (3), maximum leverage 5, and the observation must be from the requested day. There is no fabricated last-traded spot price. The model mark does not supply liquidation liquidity; margin/debt rules still apply when a futures order cannot be filled.

## Verified local 1.21 syntax sources

Sources were read from the installed `game/` directory on the machine above:

- `common/script_values/00_activity_values.txt:1064` and :2699 use `capital_province.county.prosperity_level` and `county.prosperity_level`; :2700 uses `county.county_control`. Old `development_level` is not assumed.
- `common/defines/00_defines.txt:1207` and :2027 document county prosperity 0..100; :1078 defines prosperity level thresholds.
- `common/scripted_effects/00_decisions_effects.txt:3211` uses `ordered_independent_ruler` with `order_by = primary_title.tier`.
- `common/scripted_effects/gdp_merchant_scripted_effects.txt:3207` uses an ordered iterator with `max` and `check_range_bounds = no`; the basket's bounded ordered ruler iterator uses that common iterator contract.
- `common/scripted_effects/07_dlc_ep3_scripted_effects.txt:3027` uses ordered independent rulers and `capital_county`; bounded iterator `max` follows the common current iterator contract.
- `common/scripted_effects/gdp_merchant_scripted_effects.txt:1131` uses `every_in_list = { variable = ... }` and `clear_variable_list`.
- `common/scripted_effects/00_war_effects.txt:2544` uses `is_target_in_variable_list = { name = ... target = ... }`.
- `common/script_values/00_dynasty_values.txt:28` uses `modulo`; ordinary `floor/min/max` follow native script-value operators.

The exact Java reference is `oracle.WindowPriceOracle`; `PriceOracle/PriceQuote/Quality` are the single futures-facing contract. Every quote includes the permanent asset ID, publication day, index/mark, leverage ceiling, quality, termination eligibility, reason, last valid observation day and an explicit source ID. Java results validate the specified arithmetic and qualifications; they do not by themselves certify CK3 arithmetic, native scope lifetime, save persistence or frame time.

Local source SHA-256 values at implementation time:

| Source | SHA-256 |
| --- | --- |
| `00_activity_values.txt` | `2c0182df0ad129deddf62ef18891c93ef1238fa262acf695df7a223d55bd8f14` |
| `00_defines.txt` | `a28c9eccaa3990691190f3073eac7a272679995062739fb90de2b156ec2af753` |
| `00_decisions_effects.txt` | `aafcb5cd7b7446d18706e1e3feed7a0023cf4cd89d854a733af8943fe5b3154e` |
| `gdp_merchant_scripted_effects.txt` | `44b987f213985620046f6439bc8471f46cbd9d6bb5f140d898507dcbf8bc0298` |
| `00_war_effects.txt` | `6741fbd7477f0e995c783d70f148d8fe6017d0046ed5261811496ff67d455807` |
| `00_dynasty_values.txt` | `155c5ecaa647e6659a55bd3365cf17f89e342b6839ff30d764f54ec2be02532d` |
