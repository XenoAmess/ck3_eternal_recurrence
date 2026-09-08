# CK3 1.19.0.6 played-character rebind MCP

Status: static-ready; production live validation pending.

The public MCP tool is `ck3_set_played_character_v1(character_id,
expected_revision)`. It is an explicit operator action and is intentionally
excluded from autonomous planner action steps. The native capability is
`game.command.set-played-character-v1-N`.

## Exact-build native path

- CK3 executable: `1.19.0.6`, SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
- `set_player_character` effect executor: RVA `0x2EFDAC0`.
- event handler called by that executor: RVA `0x32AFED0`.
- event vtable: RVA `0x44BE8B8`.
- local-player lookup: RVA `0x346B7C0`; PlayerID offset `0x70`.
- event layout: size `0x28`, type byte `8` at `+0x08`, target CharacterID
  at `+0x18`, PlayerID at `+0x1C`, remote byte `0` at `+0x20`.

The bridge does not write the player-character manager directly. It recreates
the event emitted by CK3's own effect and invokes the same handler on the
paused application-main thread through fixed mailbox slot 28.

## Admission and postcondition

The action requires an exact matching build, a paused map-ready snapshot, a
living current player, a positive generation-bearing CharacterID resolving to
a living character, and a target not controlled by another player. The
published revision is checked before mailbox submission and the complete
native snapshot is checked again inside the owning-thread callback.

`switched` is returned only if a fresh native snapshot immediately resolves
the requested CharacterID as the living local played character while the map
remains paused and ready. `already_played` is idempotent. All other outcomes
are typed rejections: `target_not_found`, `target_dead`,
`target_controlled`, `requires_paused`, `map_not_ready`, `state_changed`,
`postcondition_failed`, `submission_failed`, or `unavailable`.

## Portability boundary

The MCP/Python surface is machine-independent. Native RVAs and the event ABI
are exact-build data: another CK3 build must first be reverse-engineered and
admitted through its own adapter rather than reusing these addresses.
