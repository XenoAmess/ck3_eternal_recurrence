# R6 multiple event correspondence — read-only save and screenshot report

Native operation 0043 selected instance 12, option 1. It selected the proposal event's **wait** option; it did not cast the source-school ballot. Both hash-verified actual saves and the actual loaded production event script prove the following mapping.

| Saved instance | Event | Actual root / character | Visible purpose | 0042 → 0044 |
| --- | --- | --- | --- | --- |
| 10 | `lyd.210` | char 31254 / 31254 | 本派授权之议; source-school ballot | present, exact event entries unchanged |
| 11 | `lyd.212` | char 31254 / 31254 | affected-player personal consent | present, exact event entries unchanged |
| 12 | `lyd.200` | char 31254 / 31254 | proposal / wait or cancel | removed |

All three saved scopes have actor 31254, school rite 169, serial 1, terms 1 and nonce 1 (the saved fixed-point identity is 100000 for those values). Instances 10 and 11 carry voter 31254. Instance 12 carries saved voter 65861 and a doctrine snapshot item, but its root and target character are 31254. The loaded source loop saves each `lyd_c2_voter`, then dispatches `lyd.210` and `lyd.212`; after the loop the initiator calls the snapshot helper and `lyd.200`. The inherited voter label is therefore not event ownership. This explanation is source-grounded inference; the root/target identities are direct saved facts.

The archived native receipt independently records 12 → 11, option 1 (native index 0), with played character 31254 still paused. The two existing actual PNGs were visually inspected in this turn: both show title **本派授权之议** and options **我授权此人签署本轮条款** / **我不赞成这项授权**. That text uniquely matches `lyd.210` in the loaded Chinese localization. The visible front therefore corresponds to retained ballot 10 by content. No screenshot exposes its numeric instance ID; this is a content-based correspondence, not a read of the GUI's numeric identity. Native `active_event` cannot be equated with the visible front in this multi-popup situation.

| Actual character | Saved source/consent state in both saves |
| --- | --- |
| 31254 | Source elector owner 31254 / serial 1 / rite 169 and affected-player records exist; no `lyd_c2_vote_owner/serial/nonce/yes` records and no personal-consent `lyd_c2_player_owner/serial/nonce` records. Source total 4, source yes 2, player total 1. |
| 65856 | Source elector and actual affirmative ticket: vote owner 31254, serial 1, nonce 1, vote yes 1. |
| 65857 | Rite 159; no `lyd_c2_*` ticket records and absent from the actual source-elector list. |
| 65860 | Source elector / vote reply records exist for owner 31254, serial 1, nonce 1; `lyd_c2_vote_yes` has type value but identity is omitted. No affirmative value 1 is manufactured. |
| 65861 | Source elector and actual affirmative ticket: vote owner 31254, serial 1, nonce 1, vote yes 1. |

The actual source-elector list is `[31254, 65856, 65860, 65861]`. All five characters' LYD variables/lists are unchanged across the two saves. Source quorum arithmetic is `3 × 2 − 2 × 4 = −2`, below the loaded quorum threshold of zero. The native operation therefore supplied neither a new player ballot nor personal consent. Variables stored as type value with omitted identity remain raw omissions in this report; absence of an entire ticket is distinct from an omitted numeric field.

The actual plaintext save format has repeated top-level `player_event` and `triggered_event` records. There are no literal `eventmanager`, `event_manager`, `pendingevents` or `pending_events` sections in these artifacts. Every actual saved `lyd.*` event definition occurrence was inspected: 0042 has delayed `lyd.229` plus player events `lyd.210`, `lyd.212`, `lyd.200`; 0044 has delayed `lyd.229` plus `lyd.210`, `lyd.212`. The queued expiry event's root is 31254 and date is 1067.9.17; it is exactly unchanged. NPC ballot events are no longer queued in these saves, and only their actual saved reply tickets are reported. Runtime EventManager/PendingEvents structures were not read or called.

Evidence: `REPORT.json`, `SUPPLEMENT.json`, original and supplemental character/event excerpts, exact loaded script/localization copies, archived native selection/checkpoint receipts, and both copied actual PNGs. `INDEX.json` binds the first package; `INDEX-final.json` additionally binds this append-only supplement. Whole source saves remain at their original external paths and are SHA-256 checked before and after reading: 0042 `7b5adbc84232b6c1159f4d472cd87778b5910c4f1594399e118a6116edb1a42c`; 0044 `7ee7fb562d37874fb479559bef0c6d069f43320bdd908537c5466d07d5a1ecf2`.

No game input, native call, tracked edit, Git operation, mount change, or manufactured vote/consent was performed. This identifies event correspondence and ticket state only; it does not mark C2 authorization, native migration, complete R6 or whole-log acceptance GREEN.
