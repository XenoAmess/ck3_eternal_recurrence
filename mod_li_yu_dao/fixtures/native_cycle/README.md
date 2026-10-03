# Li Yu Dao native split/reunion prototype

Status: implementation candidate, static checks only. No game, Steam, save, or tracked repository files were changed by this sub-agent. A loadable CK3 script candidate is not a live acceptance result.

## Layout and use

`mod_li_yu_dao_native_prototype/` is an isolated acceptance mod, not release staging. Namespace and IDs use `lyd_np`. Register it in a disposable `-userdir` with an outer `.mod` whose `path` points to this folder. Do not load it into a valuable save or alongside a second copy of these IDs. The root agent owns game/Steam launch and environment acceptance.

1. Start a fresh bookmark with a playable landed adult ruler who has an adult male direct vassal of county tier or higher. The Chinese imperial fixture is suitable if that condition is proven in the save; no fixed historical character ID is assumed.
2. Take **Initialize the split/reunion fixture / 初始化分合夹具**. This changes the player to `lyd_np_anchor_rite`, one randomly selected qualifying vassal to `lyd_np_branch_rite`, and that vassal's capital county to the branch rite. It establishes marked temporal head titles using the native helper. Run one day and require `LYD_NP_INITIALIZE_PASS` without any failure or relevant script error.
3. For the fast lifecycle experiment, invoke `event lyd_np.9000 <player_character_id>` in the console. This initiates three real `set_parent_faith` / `detach_rite_to_new_faith` pairs. Each transition is checked at D+1 and D+30; later steps run only after successful postconditions. The chain takes roughly 185 game days.
4. Require three each of `LYD_NP_JOIN_D1_PASS`, `LYD_NP_JOIN_D30_PASS`, `LYD_NP_DETACH_D1_PASS`, `LYD_NP_DETACH_D30_PASS`, and exactly one `LYD_NP_THREE_ROUNDS_PASS`. Any `LYD_NP_*FAIL`, assertion, rejected expected transition, missing scope, or relevant engine error is RED. This script does not claim to replace review of error.log.
5. For natural cooldown expiry, use the ordinary join/separate decisions without acceptance mode. Each costs 100 piety and uses the same branch-Rite variable with `years = 5`. Check that the opposite transition is unavailable immediately, across actor succession/save reload, and until the actual five-year expiry; verify it becomes available afterward. No natural-expiry result has been obtained here.

The fast test explicitly logs `LYD_NP_COOLDOWN_BLOCK_PASS` before `LYD_NP_ACCEPTANCE_ONLY_COOLDOWN_CLEARED`. It removes only the fixture's cooldown variable between transitions. It proves repeated operations and timer presence/blocking, NOT natural five-year expiry or decision resource charging. Direct scripted effects do not pay decision costs; test the decisions separately.

## Invariants and intended limits

- Two preset faiths, each with one preset main Rite, are initialized from new IDs. Both use `confucianism_religion`; the Rite definitions explicitly override inherited `doctrine_no_head` with `doctrine_temporal_head`.
- Cores are identical native Confucian-compatible tenets. No global defines/thresholds, tenet weights, or `change_rite_divergence` are changed. This fixture isolates lifecycle capability, not all 36 production rite combinations.
- The receiving main Rite always remains `lyd_np_anchor_rite`. The branch is merged as a minor Rite, then detached only while minor. It stays the same Rite object while its parent Faith changes.
- Cross-faith comparison is explicit: within branch Rite scope, `divergence(root.faith.main_rite)`. Root is the player following the receiving main Rite. Before/after query values are saved as scope values around the operation and printed by `debug_log_scopes`; precise log serialization still needs live inspection.
- The returned dynamic Faith scope is stored as `lyd_np_latest_faith`; subsequent merges read the branch's current parent. The code never assumes the dynamic faith reuses `lyd_np_branch_faith`.
- Head bindings are removed before reparenting. Only titles marked `lyd_np_owned_head` are explicitly destroyed. If the old title/faith objects retain identity, postconditions require no title holder and no old religious-head binding; they do not pretend to prove object garbage collection. A created dynamic Faith must have the branch as main Rite and the chosen vassal as temporal head at both postcondition delays.
- The vassal and its capital county are not re-converted after reparent/detach. Their Faith postconditions therefore test natural migration with the persistent Rite.
- All entry effects and decisions require a player actor. NPCs only serve as the affected branch holder. There are no new global on_actions, AI decision loops, challenger registrations, holy orders, or wars in this fixture. Native AI behavior is not disabled by these guards.
- A failure retains the busy state and marks `lyd_np_failed`, stopping the automatic chain. Do not clear failure state and claim the same attempt passed; fix the candidate and use a new save/attempt.

## P0 questions this experiment can answer, and questions still open

The merge deliberately moves the source faith's last/main Rite to an already populated receiving Faith. That path exists in native church reunions, but whether this custom source becomes empty, dead, or unavailable must be inspected. The old Faith object may remain; this candidate does not invent `destroy_faith` or reuse it as the next dynamic Faith.

Direct `detach_rite_to_new_faith` on a current main/last Rite is NOT used and remains unclosed. Native heresy declaration excludes main Rite. If production permits independent main rites to be recreated, it needs a separate external experiment and explicit rules for an empty source or replacement main Rite.

Also unclosed: automatic >=100 detach refresh timing, different-content pre/post migration divergence, universal convertibility UI, head election after death, nested challengers/followership, holy-order rights, saints/artifacts, NPC actions, long-run save growth and repeated cycle identity. These are outside this minimal same-content lifecycle fixture.

## Current native sources

Source root: `C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III`.
Launcher version: `1.20.0.3 (Crozier)`; raw version `1.20.0.3`; Steam buildid `25652598`. No EXE hash or calling-chain research was performed.

| Source relative to game | Evidence used |
| --- | --- |
| `common/religion/faith_types/_faith_types.info:1–43,60–64` | Faith parent, main-Rite initialization and effective core doctrine inheritance |
| `common/religion/rite_types/_rite_types.info:35–70` | created preset rites, convertibility, Rite group override |
| `common/religion/religion_types/00_confucianism.txt:8–52` | shared religion defaults, particularly no-head and lay clergy |
| `common/religion/doctrine_types/20_doctrines.txt:1230–1258` | temporal head doctrine parameters and clergy incompatibilities |
| `common/scripted_effects/00_religion_effects.txt:347–380` | dynamic temporal head creation/binding and native inheritance laws |
| `common/scripted_effects/00_religion_effects.txt:445–455,1226` | character scope/save patterns and county Rite setter |
| `common/scripted_effects/pam_antipope_effects.txt:267–296` | binding/challenger cleanup and Character-scope `destroy_title` usage |
| `common/scripted_effects/pam_effects.txt:6749–6759,7383–7418` | detach, convertibility setter, source-head removal and reparent with followers |
| `common/casus_belli_types/00_event_war.txt:2057–2064` | Character-scope detach returning Faith, followed by temporal-head setup |
| `common/character_interactions/pam_interactions.txt:28740,28781,28833` | explicit cross-faith Rite-pair divergence query |
| `common/on_action/religion_on_actions.txt:3–55,442–456` | new-Faith refresh and Rite variables with expiration |
| `common/scripted_effects/pam_effects.txt:6355–6371` | `set_variable` with five-year expiration |
| `events/dlc/fp3/fp3_struggle_events.txt:1344–1347` | native `assert_if` failure condition/text syntax |
| `events/courtier_guest_management_events/courtier_guest_management_events.txt:1221–1222` | native debug logging/scopes |

`validate_prototype.py` writes `native-source-evidence.json` and `static-report.json` outside the mod payload, containing exact source hashes and payload hashes. It only checks structure/localization/guard contracts; it does not parse CK3 semantics or grant live approval.
