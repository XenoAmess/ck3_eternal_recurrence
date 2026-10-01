# XQOL 1.20 native payment context correction

Date: 2026-10-01. Exact game: CK3 1.20.0.2, Steam build 25588574, EXE SHA-256 `ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d`.

The official-engine R0003 celestial governor matrix passed its strict native baseline, scored successor, removal, death and disable assertions. Its later `payment_full_only` assertion failed. That failed attempt remains preserved; the original callback overwrote expected payment fields and executed the next matrix before diagnostic collection, so its precise failed condition cannot be reconstructed.

Controlled diagnostics in the same game proved that a fresh weak-hook full target paid 50 exactly, while targets with wallets 2 and 1 retained their money and hooks. All eight transaction conditions also remained true across one actual game day. This does not establish daily income as the cause of the original failure.

A separate controlled read on the actual historical courtier `han_9622` (internal ID 40946) established the missing native context: with wallet temporarily 100, the uncapped quote was 15 without a bound recipient and 50 with `recipient=this`; the native capped quote was also 50. The wallet was restored from 100 to its original 0. CK3 1.20's `normal_ransom_cost_value` explicitly reads this recipient context for rich courtiers, and its obligation quote reads actor context for strong hooks.

The production full-payment loop now binds each recipient before its uncapped eligibility check and calls the unchanged native interaction. The generated quote still differs from the frozen native value only by removal of the final wallet cap. The native formula, strong-hook multiplier, interaction, hook use and transfer rounding are retained.

The external fixture now binds actor and each recipient before computing expected transfers, uses the native capped quote for the transfer prediction, and verifies full and partial transactions immediately after their production effects. It records expected and actual gold/count, all three target identities/wallets, and the eight individual conditions before the verification callback can overwrite them. Native equality can take the floor-of-wallet branch; positive strong-hook checks must record a freshly evaluated quote and use a wallet above that quote rather than assume fractional equality transfers the whole quote.

Evidence: `C:/workspace/ck3-upgrade-20261001/live/4-8e1c2f1861--xenoamess-quality-of-life--R0003/payment-diagnostic-001` through `payment-diagnostic-006`; necessary generator/static/build/parser checks in `C:/workspace/ck3-upgrade-20261001/audits/xqol-payment-context-fixture-001/checks.json`. The first checked prepared fixture predates the added transaction diagnostic and is retained; its replacement must have its own receipt and parser report.

Status: production and fixture corrections are candidates until a fresh affected payment cell verifies the frozen corrected production bytes. The original R0003 is not an overall PASS. No supported-version metadata, product version, old native ABI, Workshop release or seven-language release claim is changed by this package.
