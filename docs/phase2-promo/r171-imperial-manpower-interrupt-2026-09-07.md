# R171: imperial manpower interrupt contract

## Live evidence

R171 reached a new paused vanilla event, `ep3_emperor_yearly.8000`, at
`date_raw=53150712` after two already-bound tribute events. The native event
window reported four visible and enabled authored options and eight saved
scopes: `suggestor`, `minimum_development`, three governor scopes, and their
three corresponding landed-title county scopes. The player/root was character
32904. Product runtime diagnostics remained at zero; the run stopped because
the event had no reviewed exact contract, not because the mod became RED.

The frozen bridge hello bound this observation to CK3 `1.19.0.6`, executable
SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
The retained evidence is `Z:\p2m171_a\manager-cycle-recovery.json`.

## Exact-build source review

The source is
`Crusader Kings III/game/events/dlc/ep3/ep3_emperor_yearly_8.txt`.
Its helper effect shows that options 1-3 each remove ten percent development,
rounded up, from one selected governor county; add the ten-year
`ep3_development_sacrifice_modifier`; and apply -20 governor opinion of root.
Option 4 removes two development from the player's capital and adds the
ten-year `ep3_development_waning_modifier`. In
`common/modifiers/07_ep3_modifiers.txt`, the latter also has the larger growth,
tax, and county-opinion penalties.

The acceptance contract therefore selects authored option 1. This keeps the
player capital unchanged while accepting the smallest source-authored external
mutation. It binds all eight saved-scope names and types, all four native
option indices, non-player character identities, and the source-guaranteed
pairwise distinction among the three randomly selected governors. The contract
is isolated in the purpose-specific
`tools/zg361_phase2_promotion_manager_imperial_contracts.py` module rather than
growing the already-large production entry module.

This source review and a static contract test only authorize the next live
drain. They do not mark the manager seed or promotion full tree GREEN.
