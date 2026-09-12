# R553-R555 promotion profile and TGP travel interrupt RED

## Verdict

The R553-R555 take is retained as a failed attempt and contributes no accepted Phase 2 footage. It completed two clean spans, then stopped before input on the previously unknown vanilla event `tgp_travel_events.0030`. P1 remains `9/9` GREEN and P2 remains `0/8`: the eight spans must still come from one continuous clean take.

The earlier promotion preflight defect is closed. Promo capture now requires the full existing Phase 2 capability profile before FFmpeg starts, including `zhongguo_promotion_compensation_v1_query_supported=true`. The focused promotion-only bridge used in this run advertised that complete profile.

## CK3 round record

- R553/PID `73392` was the Frontend warm-up and was terminated before gameplay.
- R554/PID `175096` was the first gameplay process. It passed loader, full MCP capability, seed and media gates. FFmpeg/PID `5808` started only after those gates.
- R554 completed `phase2_fact_quota_calibration` and `phase2_receipt_appeal_pip` as clean spans.
- The canonical player-manager checkpoint restore terminated R554 and started R555/PID `196812` with the same product tree and promotion-only bridge.
- R555 drained the already contracted `sway_outcome.1001` and `stress_threshold.1011`, then stopped before selection on `tgp_travel_events.0030`.
- Cleanup is GREEN. R553, R554, R555, CK3, FFmpeg and the injector have no surviving process.

## Runtime and artifacts

The bridge build is `Z:\ck3_mod_rewrite\_runtime\native-builds\p2-r553-r554-promo-profile-471ded2-20260912`. Only `XAR_CK3_ENABLE_ZHONGGUO_PROMOTION_COMPENSATION_CANDIDATE_V1` is enabled. Its DLL is 2,600,960 bytes with SHA-256 `54D46BD8211518D74FFFA055EF9A2D8270BEC3C2300A04701ED870E9C358CE27`; the injector SHA-256 is `DAEBAF9A1587B12B102CC0FF512948103A1EE9ED31AAB8A88A5B25198A3A1E0F`.

The attempt root is `Z:\ck3_mod_rewrite\_runtime\p2-capture-r553-r560-471ded2-20260912\capture`:

- top-level `report.json`: `F0F5EB91CCB11E7810A19CA04C07CEFB1C99FE493F333773B52D1A3DE7A53CF5`
- `evidence-index.json`: `C3BD5A454E33483DE9E357AC58EC68B86CA5493D29174BC93A84E499CED7546B`
- cell `report.json`: `3850AFBDAF043A7D89D34A8B6CFFE8C55131E5F75B520FDD4322299928FBA526`
- cleanup evidence: `CB1EA02D6AFF0192CBFD115D4D1CD1567AFF6D100C98B743590D75D1F4603B59`
- capture timeline: `FD2D3C71E3A01907F19DE3EF9B673EE0D607513CC64444DD3C85341B4406816C`
- failed MKV: 92,612,860 bytes, `464815768319E95EA624B501706AEA722AA3C388DBDC6FB35B947AF661CB2AAA`
- Stage 10 RED artifact: `C6AC0B6EE128AB6C9FA6209E090C92F936546908D97D03CA53FB4BDD1191680C`

## Exact-build event analysis

The frozen build is CK3 `1.19.0.6`, EXE SHA-256 beginning `2D00` and ending `DB86`. The live frame had root/player `27181`, date raw `53155992`, instance `21`, two enabled options at native indices `0` and `1`, and saved scopes `travel_plan` (`travel_plan`) plus `poem_province` (`province`). No input was attempted.

The event definition is `Crusader Kings III/game/events/travel_events/tgp_travel_events.txt`, lines 311-496, SHA-256 `42B8B1E56C029054FBC4E0B3964511A980D9B5053C47BFF980CD3F5F3924DB37`. Its caller is the `travel_events_on_action` pool in `Crusader Kings III/game/common/on_action/travel_on_actions.txt`, lines 715-951, with candidate weight 100 at line 934 and SHA-256 `7E433A0D6969E09CFED1D9DC50FB5276D944354024D6D2E045B314355F41040C`.

Option 0 adds a five-day travel delay and enters a stochastic learning contest with possible lifestyle/traveler XP, a trait or stress. Option 1 only applies medium stress loss and has no resource cost or follow-up event. The reusable safe contract therefore selects displayed option 2/native index 1. The event has a ten-year cooldown and is not a one-shot event.

## Closure and next live step

Commit `f66937f797777966147510b628f59eca8ff88351` adds the strict reusable event definition, exact-build caller/source evidence, the R555 observation, portable evidence blobs and focused manager-interrupt coverage. Manager recovery passes `11/11` in normal and optimized modes; source-index and portable-bundle checks pass in both modes; source-index, portable-evidence and knowledge-MCP unit coverage passes `24/24`.

This is data within the existing vanilla-event MCP schema and endpoint, so it does not change the public interface, version or dependency surface for open_kaishek. The next bounded attempt starts at R556 and must prove this event drains safely before any footage can count toward the one-take `8/8` gate.
