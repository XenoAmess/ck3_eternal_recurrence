# R0368 actor army role: paused read-only interface boundary

## Observed state

The R0368 source request concerns actor `29829` in episode
`native-29829-2bc2d599f7f9` at date raw `53219928`. The activity planner
reported `activity_feast` Stage 5 `final_can_start=false` and a localized
commander-or-knight failure, with zero selected nonhost guests and no Start.
The source's 2026-09-29 correction says that this R0368 process has ended and
its report contains **no typed army-role row**. The current role and any safe
release boundary are therefore unknown. The corrected report SHA-256 is
`883CC43B513CE7F01A18A61DB27ACCA923F2F3D781F5836306AC0B7FCEE39EB6`;
the first request omitted two hex characters in that value.

An earlier, distinct H3928 `query-combat-simulation-inputs-v3` row observed
public ArmyID `83886367`, native CArmyID `50331794`, owner `29829`, current
province `2610`, and commander `29829`; the actor was absent from that row's
14 knight members. This is historical evidence from another native query.
Matching episode and date fields do not make it a role observation in the
R0368 paused frame. Its fixed WAR excerpt is
`R0345-H3928-WAR-SIEGE-FORECAST-RED/SOURCE-R0345-H3928-V3-RAW-EXCERPT-v1.json`,
SHA-256 `C91DDA8284E414D96FA7705AA0881A048CF0CAB2F83AB4817F7826F5C5A63F67`.

## Existing native source

The public `player_armies` snapshot and private
`query-m5-war-primary-current-v1-...` expose ArmyID, owner, province and
route, but no actor commander/knight assignment. The battle-control selected
commander and knight fields describe a bound active combat, so they do not
answer an ordinary raised-army role question. The existing V3 hypothetical
combat-input command can expose a selected army's native commander and knight
members; it also requires a contact scenario and its completeness belongs to
that hypothetical query. It must not be used as a general role or war-action
gate.

The verified CK3 `1.19.0.6` anchors already used by the combat adapter are:

| Field | Existing source and check |
| --- | --- |
| Public and native army identity | `CUnit+0x178` CArmyID, `CArmy+0x10` exact ID, `CArmy+0x124` reverse CUnit ID, `CUnit+0x174` owner; see `prewar_scope_v1.cpp` `ReadOneSample`. |
| Commander | `CArmy+0x120` full CharacterID, `-1` absent; resolve exact `CCharacter+0x18` and compare the native `get_army_commander` helper; see `ck3_11906.cpp` `ReadCombatCommander`. |
| Knight | Complete `CArmy+0x38/+0x40/+0x44` regiment ID array; each exact CRegiment's `+0x140` army link and `+0x148` CharacterID, checked against `CCharacter+0x1B0` link whose `+0xF8` is the regiment ID; see `ck3_11906.cpp` `ReadCombatKnights`. |
| Army state | Current/target province, route, retreat and combat IDs have separate native sources; the current H3937 R0271 work is still resolving battle/siege participant coverage. A role query cannot promote these fields into a safe role-release decision. |

## Minimal future private query

Candidate step: `query-war-actor-army-role-v1-<actor-character-id>-<public-army-id>`.
Keep it disabled until its own static and exact paused live acceptance. It is
an independent query; it does not change H3937 phase-0 or the R0271 date gate.

1. Require paused and map-ready state, exact played actor and positive canonical
   IDs, a single native revision, and before/after snapshot identity, date and
   connection generation equality. Reject an unbound episode or changed save.
2. Resolve the requested public CUnit and native CArmy with both ID/backlink
   checks. Return public ArmyID, native CArmyID, owner, province and typed army
   state with a source/revision tag. Compare those fields to the same-frame
   public `player_armies` row. A missing or contradictory row is `unavailable`.
3. Read the commander ID through `CArmy+0x120`, validate the character pointer
   and native helper, and report `is_commander_of_requested_army` as true or
   false only if this chain is complete. A failure is `unknown`, never false.
4. Traverse the entire bounded regiment array, resolve every CRegiment and
   validate each army and character reverse link. Report
   `is_knight_in_requested_army` as true or false only after the entire array
   is complete. Include matching regiment ID when true. A partial array or
   generation change is `unknown`, never false.
5. Limit negative claims to **this requested army**. Establishing that the
   actor has no role in any army needs separate complete live-army enumeration
   or a verified character-level reverse index. If that proof is absent, return
   `global_commander_or_knight_status=unknown` even when both requested-army
   flags are false. Preserve the raw activity CanStart read as a separate
   source; do not derive role identity from translated failure text.
6. The command returns no release action, role mutator, activity Start, date
   advance or changed war policy. Return typed `unavailable_stage` for failed
   identities, unsupported game versions, stale frames and missing bindings.

The release decision is a later war-policy step. It needs the exact current
assignment, a complete army and contact/siege state, a valid replacement plan,
and a qualified nonwar benefit. R0271 remains RED, so this interface gives no
date or role-release credit. Its first live use requires a new exact paused
attempt and separate screen/offline admission; the ended R0368 frame cannot be
retroactively upgraded.
