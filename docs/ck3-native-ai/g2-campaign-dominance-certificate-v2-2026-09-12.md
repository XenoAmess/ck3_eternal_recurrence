# G2 campaign dominance certificate v2

Status: **GEN-034-A complete / production-live input reused / no CK3 launch / no action**.

## Problem and corrected scope

The previous `raiktor-campaign-dominance-certificate-v1` combined measured military state, a full campaign forecast, owner utility intervals, finance endurance and tail-risk valuation in one object. The repository had a strict consumer but no producer for that whole object. R471 later supplied the concrete missing fact needed by the current G2 work package: a stable official MCP reading of both sides' strategic power on the frozen active-war checkpoint.

GEN-034-A now closes only that factual transformation. `raiktor-campaign-dominance-certificate-v2` binds three unchanged paused snapshots around two consecutive official MCP queries and publishes the measured power relation. It does not rename the ratio as a battle forecast or utility evaluation. Those later policy inputs remain separate.

## Provider contract

`raiktor_campaign_dominance_provider.py` requires:

- the before, between and after snapshots to retain snapshot/public/native revision, date, connection generation, PID, episode, actor, WarID and primary opponent;
- one unique active war in the requested identity, with the player as primary attacker;
- two consecutive `query-war-entry-assessments-v1` results on that same frame;
- the target scope to be exactly `active_war_primary_opponent`;
- every native readiness flag to be true;
- identical power decomposition in both results and an internally consistent fixed-point ratio.

The output classifies only `actor_stronger`, `opponent_stronger` or `equal`. It fixes `campaign_outcome_forecast_ready=false`, `exit_utility_ready=false`, `recommended_outcome=null` and `action_ready=false`.

The three-way intake accepts and retains this v2 certificate as `measured_power_dominance`. This connects the production observation to the planner input ledger without relaxing the existing recommendation or submit gates.

## R471 conversion

The hash-bound CLI consumed the preserved R471 report plus its GREEN offline reclassification. It did not start or attach to CK3 and did not query the bridge.

- source report: `Z:\ck3_mod_rewrite\_runtime\g2-r471-active-war-power-fix-20260912\report.json`, SHA-256 `F467676201497A75C08ED5F6C72AFE64618337C73EFD2BA816B981470CE1E7CD`
- reclassification: `Z:\ck3_mod_rewrite\_runtime\g2-r471-active-war-power-fix-20260912\reclassification.json`, SHA-256 `D8F43EABC2A38F451FCAB1FE8DAEEB157EF8C62439B904DF96E8AFA301E924C9`
- output receipt: `Z:\ck3_mod_rewrite\_runtime\g2-gen034-a-campaign-dominance-20260912\r471-certificate.json`, 3,176 bytes, SHA-256 `AB0DB5678F65631D63E5A54BA66B61A6F5956179C0A4D3970B78BEAC5E9E0569`
- observed actor power: `13,075,500,000`
- observed opponent power: `16,770,900,000`
- target-minus-actor power: `3,695,400,000`
- native ratio: `128262 / 100000`
- factual relation: `opponent_stronger`

The receipt remains bound to CK3 `1.19.0.6`, WarID `33554473`, actor `29829`, opponent `28551`, date raw `53183856` and snapshot `native:3` through the source report.

## Validation and remaining work

The provider plus its three-way intake retention tests pass `11/11` under normal and optimized Python. The CLI compiled and converted the real R471 artifacts successfully. No broad suite and no CK3 rerun were used.

GEN-034 is now `2/4`: A and B are complete. C still needs one bounded same-frame white-peace terms/utility comparison, and D still needs one recommendation, one action, postwar verification, checkpoint and cold restore. The global G2 milestone count remains `0/8` until the complete visible OODA milestone closes.
