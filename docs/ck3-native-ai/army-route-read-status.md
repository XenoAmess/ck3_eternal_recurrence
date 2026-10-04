# Native army route read status

The CK3 1.19.0.6 `ReadUnitRoute` reader previously published an empty
`route_province_ids` array both for a valid zero-count route and for an
invalid or unresolvable native path. Its existing route and move-target
fields are unchanged. Each native army row now also publishes:

| `route_read_status` | `route_source_count` | Meaning |
| --- | ---: | --- |
| `complete_empty` | `0` | Header passed the existing bounds checks; no path entries. |
| `complete_nonempty` | positive | Paused read resolved every entry; array length equals source count. |
| `target_only` | positive | Running-map read checked only the last entry; the full route was not traversed. |
| `invalid_header` | `null` | Native count/capacity failed bounds checks. |
| `unresolved_entry` | positive | Header was valid but a path pointer or Province did not resolve. |
| `not_attempted` | `null` | Contract default for a row without a route read. |

The Python normalizer rejects contradictory status/count/route/target
combinations. Older native rows with neither new field remain accepted but
provide no completeness proof. A planner may treat a paused route as complete
only for `complete_empty` or `complete_nonempty` with the matching source
count. `target_only`, absent fields and every failure status leave full route
completeness unproven. This evidence does not enumerate hostile armies or
approve any H3937 date advance.

This is an additive source change to the DLL described by
`h3937-province-local-siege-port.md`. A formal combined H3937 receiver
observation needs a newly built DLL containing both additions, its own SHA,
ordinary rebind and a fresh no-action session. It cannot combine an old DLL
route observation with a later Province read as one same-frame result.

## 2026-10-04 CK3 1.20.0.3 R29 actual move and independent route readback

Root R0029 / PID38372 uses exact CK3 **1.20.0.3 / Steam25652598**, EXE SHA-256 `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`, with frozen `Z:/g61` source `f3f365c53d3708f520e0142a1b81a484b0c31df3`. `ck3_move_army(301989997,472)` was accepted/submitted at raw date53251464. The following independent `ck3_get_war_state` returned native:5/public3 and actually observed that army at Province2619 with **army_state=moving/code7**, target472 observable, full route **[8651,1038,472]**, `complete_nonempty`/source_count3, controllable=true, in_combat=false and retreating=false. This is independent native state after the command, beyond the ACK.

Old player Army184549452 independently remains at2619, regular/code1, empty route with `complete_empty`/count0. War117440524 remains active, playerATT/primary leader=true/score0; enemy Army268435597 remains at510 moving toward470 with its complete12-entry route. Target472 remains unoccupied, fort4/garrison500/besieging_strength0 and no active siege. These rows expose soldiers=null; this readback does not supply an updated force-strength total.

The command date is present in the move result; the independent war DTO itself has no date field. Root's closed zero-day session supplies the shared date53251464/total4464 cut. The army's current province is still2619: movement has started, while departure, arrival, a siege or a battle is not yet observed. This package adds **0 world days** and no arrival/combat credit.

Sole consumption receipt: [r29-route-actual/move472-once/ROOT-DELIVERY.json](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261004/r29-route-actual/move472-once/ROOT-DELIVERY.json). Raw004 move and raw005 independent war readback were each cached once; subsequent work used only those caches. The consumer performed no SDK/pipe/window action, new query, native build or repeated test.

## 2026-10-04 R29 day32 continuation and fresh pre-stop target readback

The move above continued through Root's centrally credited 8+32 normal calendar days. The central day32 summary independently records raw53252424 / native167 / public129: Army301989997 is now at **1038**, **embarked/code4**, target472 observable, controllable=true, remaining complete route **[472]**/source_count1, with no combat or retreat. It has left2619, but has **not arrived at472**. This paragraph reuses only the [central cache summary](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/military-ooda-continuation/ordinary-v56/r29-march-next32-days-consumed01/DAY32-CURRENT-SCOPE-CACHE-EXTRACT.json), not the child's day raw or day cache. The parent has already credited the40 saved days; this topic consumer adds0, with formal total4504 / resumed1351 / Oct4+479.

Root's later zero-day pre-stop SDK79664, normally closed GREEN, queried `ck3_query_war_occupation_targets_v1(117440524)` independently at raw53252424 / native169 / public2 / gen6. It returned accepted/available, read_only=true and a complete collection: defender337 eligible/0 counted occupied, attacker31/0. Goal Province470 (holding1334/legal32309) is now unoccupied, fort6/garrison550; 3711 (holding1352/legal32309) is unoccupied, fort6/garrison565; 472 (holding1359/legal31797) is unoccupied, fort4/garrison500. Each is defender territory with occupier=null/side none/count-opposing=false, besieging_strength0, siege_observable=true and **active_siege=null**. The earlier third-party occupation at470 is absent now; the change does not establish that our army recaptured it.

None of these three rows contains a breach field or an active siege object, so breach is **not observed**, rather than zero. The running R29 DLL remains frozen `g61/f3f365c5`; the current source-tree movement observer at `b513f020` and any newer five siege operands are not credited as live by this packet. No arrival, siege, battle or war victory is added. Fresh three-goal evidence and the combined cached-only receipt are in [r29-route-actual/combined-r29-preview-moving-prestop-goals/ROOT-DELIVERY.json](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261004/r29-route-actual/combined-r29-preview-moving-prestop-goals/ROOT-DELIVERY.json).

## 2026-10-04 R30 cold current-objective readback

Root R0030 / PID120956, frozen `Z:/g62` source `d1b7f18d200cffd302815a05a12c1d3e958ab2de`, returned a fresh `ck3_query_war_occupation_targets_v1(117440524)` accepted/available/read_only at raw53252424 / native3 / public2 / gen2. The complete collection has defender337 eligible/0 counted occupied and attacker31/0. The current goal rows are:

| Province | Occupied / occupier | Fort | Garrison | Besieging strength | Active siege |
|---|---|---:|---:|---:|---|
|470|false / null|6|550|0|null|
|3711|false / null|6|565|0|null|
|472|false / null|4|500|0|null|

All three rows are observable defender territory, occupier side none and opposing-side occupation count=false; the whole368-row collection has no active siege. Breach is not published. With `active_siege=null`, the new five siege operands are **not applicable in this frame** and retain **static-ready** status pending an actual active-siege reading; cold deployment or fixture success does not supply live operand values. SDK59491 normally closed GREEN with normal SAVE; this zero-day query adds0 days, leaving formal4504 / resumed1351 / Oct4+479. Receipt: [r30-first-objectives-once/ROOT-DELIVERY.json](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261004/r29-route-actual/r30-first-objectives-once/ROOT-DELIVERY.json). The sole consumer cached raw014 once, did not read another child's health raw, and made no SDK/window/shared-source/Git mutation or repeated test.
