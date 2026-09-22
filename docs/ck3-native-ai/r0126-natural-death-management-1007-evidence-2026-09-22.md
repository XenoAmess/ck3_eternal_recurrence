# R0126 natural `death_management.1007` material loop

Status: `production-live loop` for the exact no-killer `.1007` branch in CK3 `1.19.0.6-steam23530548`; the G2-M2 milestone remains in progress because its other required scenes are separate. This was an ordinary bounded campaign continuation. No event was forced, and this review started no CK3 process.

## Immutable sources and identity

| Source | Identity |
| --- | --- |
| Formal report | `Z:/ck3_mod_rewrite/.task-tmp/RUN-001/war-h1531-continuation-source82c6703-nolaunch-20260922/R0126-execution/formal-report.txt`, SHA-256 `931E0C17D0259894AE13B837D65F51E746A4E41A5AB06D9E7D85E7F09FB4F736` |
| Native driver | sibling `state-final/native-session/driver-state.json`, SHA-256 `E2A13A476629E39F85C8677B1A045750D8D6DF47C1B24AACD0C7B2BB9309CE2D`, `1955` command-history rows, final `last_checkpoint.history_index=1955`, no post-checkpoint tail |
| Operator manifest | `R0126-execution/R0126-evidence-manifest.json`, exact EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`, DLL SHA-256 `4E4EC9FF1022B1524D8B775B516F533EBD47A0E25A34272E426A5396CAC51E11`, source commit `82c670335b25fca288b1be3eb50fcaf4993f1640`, `ordinary_campaign_succession/xar_off` |

The formal report's original bytes include one non-UTF-8 segment. Its hash above is over the original bytes; the JSON keys below were inspected with UTF-8 replacement decoding. The native driver JSON provides the exact event scope and command-history rows, without altering either original file.

## Contract comparison

The acceptance contract is [`natural-death-and-heir-event-gate-2026-09-15.md`](natural-death-and-heir-event-gate-2026-09-15.md) and the source-reviewed effect/choice contract is [`heir-death-stress.md`](heir-death-stress.md).

| Required observation | R0126 evidence |
| --- | --- |
| Natural paused event and exact context | Formal turn 138's ordinary war timeline stops at raw date `53376672` for active event instance `24`; turn 139 queries its paused native window. Driver history `1749` reports `death_management.1007`, root CharacterID `36403`, distinct dead CharacterID `35465`, saved `new_memory/character_memory`, `dead_character/character`, `deceased_character_stress/value`, one shown/enabled native option `0`, snapshot `native:237` revision `238`. |
| Registered decision and same-frame pre-value | Formal turn 140 `active_event_registry_choice` has `status=recommended`, source-reviewed sole legal native option `0`, ready `played_character.stress_points` expectation with CharacterID `36403`, starting stress `0`, snapshot `native:237` revision `238`. The source profile records authored base `+20` as non-exact at runtime. |
| One typed action and independent postcondition | Driver history `1750` has exactly one `select-event-option-1` for old instance `24`. Its native post frame is `native:238` revision `239`, still raw date `53376672`, old event `24 -> null`, same living CharacterID `36403`, stress `0 -> 20`. Formal material comparator returns `verified_change`, `delta=20`, relation satisfied. |
| Later formal turn | Formal turn 141 queries the cleared paused frame for war termination, then subsequent turns continue ordinary war decisions. Driver history `1751..1755` shows campaign-root/war queries and a later date advance without another instance-24 selection. The full 1955-row driver history contains exactly one selection for old instance `24`. |
| Paired checkpoint | First post-action checkpoint is driver history `1760`, raw date `53376720`, save SHA-256 `9B3B7C2A01E706CFFFAFC8666AEA3D4624A4680CAA3E4A6F07BCEC4098A31E37`; final checkpoint is history `1955`, raw date `53379144`, save SHA-256 `F9AFFDF734425697E534C8EC25C5DE6214DB7399E1D2049422BBAB4FE3BADE96`, driver SHA above. Formal run is `250/250`, outcome `qualified`, cleanup proven. |

The `.1007` natural recommendation → typed action → material postcondition → later formal turn → paired checkpoint gate is satisfied for this exact no-killer branch. This does not prove the separate `tgp_travel_events.0030` celestial scene, the `.0110` county modifier effect, arbitrary `.1007` scope variants, or another player's natural death/succession. No M2 milestone or G2 aggregate count changes from this one subgate alone. The original R0118 war RED concerned a different WarID and is unaffected by this event result.
