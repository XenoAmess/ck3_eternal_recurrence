# ArmyStrengths manager roster payload: bounded source result

Recorded 2026-10-10 03:40 Asia/Shanghai. Status: **research / NO_NEW_SOURCE**.
This investigation does not claim a throughput improvement, a new native
qualification, or a change to G2 readiness.

The proposed per-army full-ID filter cannot preserve the current production
contract. The six largest inputs are complete ArmyManager roster predictions,
not per-army owned capture journals. Their raw occurrence order, global pending
table and independently recomputed readiness are required by the current typed
normalizers and projectors. No C++ change, fixture, build or live request was
added for this hypothesis.

## Actual observation reused

Root reported ordinary Army query 08 at **106.574511 seconds**, with an
87,146,185-byte retained response. The separate later ordinary response 18 was
already parsed once by the replenishment worker. This investigation reuses its
thin measurements instead of parsing either large response again:

- [Response 18](D:/codex-ck3-background-spill/g2-live-20261010-r85-retry02/r0084-person-readonly-sdk-hot01/operator/gameplay-responses/100-r85-native60-sustained-root01-000018-normal.json).
- [Payload contributors](D:/codex-ck3-background-spill/r85-native60-army-loss-analysis/ARMY18-ACTUAL-PAYLOAD-CONTRIBUTORS.json).
- [Strength and full-ID facts](D:/codex-ck3-background-spill/r85-native60-army-loss-analysis/ARMY18-ACTUAL-LOSS-AND-STRENGTH.json).

Response 18's compact selected result is 43,960,122 bytes. Its two Army rows
account for 43,920,242 bytes. Public Army218104048 maps to native CArmy67109093
with39 regiments; enemy public Army134218098 maps to CArmy167772499 with8.

| Input present in each Army row | Compact bytes per row | Native occurrences |
| --- | ---: | ---: |
| `current_pre_date_pending_update_inputs_v1` | 7,732,514 | 464; pending table has524 records |
| `current_daily_assault_roster_admission_v1` | 3,302,062 | 464 |
| `current_post_admission_refresh_inputs_v1` | 3,051,501 | 464 |
| `current_selected_title_holder_owner_relation_v1` | 1,881,782 | 464 |
| `current_army_combat_roles_phase_inputs_v1` | 1,599,082 | 464 |
| `current_army_flag31_inputs_v1` | 1,159,984 | 464 |

Together these six fields across two rows occupy37,453,850 bytes, about85.2%
of the Army row payload. Equal byte counts alone are not an evaluated equality
comparison. The outer response's extra bytes were not attributed to a second
text serialization: the measured text block in response18 contains only1108
characters. Query08 timing and response18 depth measurements remain separate
observations; neither proves where the query's wall time was spent.

## Source binding and decisive dependencies

The source baseline is the qualified coherent Native61 source commit
`4d3ba1d2b8dd8d460a2be3bdd663c859244832b3`, materialized at
`D:/codex-ck3-background-spill/gbs-runtime61-guardian-qualified60-source`.
Missing Python simulation files were read from the same Git object into the
isolated sparse source checkout `D:/aq01`. No newer public or unrelated truce
source was mixed into this investigation.

1. [`ReadArmyStrengthsForScope`](../../ck3_autonomous_player/native_bridge/src/ck3_12002_army.cpp#L1305)
   owns query-wide optional values outside the selected Army loop. It reads the
   manager-wide roster once and assigns the same captured values into each
   selected Army row. The repetition is real in the producer design; it is
   not caused by the loss journal or a new history export.
2. [`ReadCurrentDailyAssaultRosterAdmission12003`](../../ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12003_daily_assault_roster_admission.hpp#L458)
   reads the original vector from ArmyManager+0x50 and visits every occurrence.
   Its completeness flags compare occurrence count with the captured native
   count and apply `all_of` to the whole roster.
3. The [roster normalizer](../../ck3_autonomous_player/src/xar_autoplayer/bridge/army_daily_assault_roster_admission_contract.py#L294),
   [pending normalizer](../../ck3_autonomous_player/src/xar_autoplayer/bridge/army_pre_date_pending_update_contract.py#L107)
   and [post-admission normalizer](../../ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_post_admission_refresh_contract.py#L75)
   explicitly reject filtered or relabeled original occurrence pairs. The
   selected-holder, combat-role and flag31 normalizers enforce the same rule.
4. The [roster projector](../../ck3_autonomous_player/src/xar_autoplayer/simulation/army_daily_assault_roster_admission_12003.py#L408)
   recomputes full coverage, contiguous native indices and all-row readiness.
   It derives an ordered request prefix; an earlier incomplete occurrence
   closes that prefix. Changing native count or renumbering a selected subset
   would describe a different capture rather than preserve this contract.
5. The [pending projector](../../ck3_autonomous_player/src/xar_autoplayer/simulation/army_pre_date_pending_update_12003.py#L109)
   replays original roster order into shared physical slots, pending-table
   placement state and map count. An incomplete earlier occurrence stops later
   rows. At lines270–309 it carries physical mutations into subsequent steps
   and requires completed original occurrence count to equal the captured
   native roster count. Unselected armies can therefore affect a later
   selected Army's conditional placement as well as whole-family readiness.
6. The [post-admission projector](../../ck3_autonomous_player/src/xar_autoplayer/simulation/army_current_post_admission_refresh_12003.py#L194)
   independently recomputes all-roster numeric completeness. The Service
   projects these inputs for each selected Army; it does not redefine them as
   owned per-army journals.

## Delivery boundary

No per-army filtering candidate is authored: it would remove required global
inputs or change existing normalizer / readiness semantics. No native whole
fixture or registered consumer test is justified for an absent production
change. The current live loop and Native62 Person source work remain
independent.

The actual volume observation remains useful for a future explicitly selected
lossless representation change. Such work would have to retain the complete
manager capture, native order and full-ID joins and expand it for the existing
normalizers. This note does not design, authorize or implement that separate
wire / DTO change, nor claim that it would fix the measured106-second latency.
