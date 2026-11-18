# Florin personal gold and explicit isolated settings

The CK3 1.21.0 agent can read personal gold through the public Native-owner endpoint. This is a narrow observation and does not provide a complete snapshot, treasury, monthly cash flow, Driver adoption or Root/MCP readiness.

`NativeGameTransport.readPersonalGoldFrameReceived(deadline)` consumes the exact advertised 1.21.0 capability and preserves the original ACK, connection custody and deadline. Its private receipt cannot become a Core-control or complete-snapshot receipt. `PersonalGoldFrame` preserves signed 64-bit `raw` with scale `100000`; unavailable data retains its reason and original nested Core rather than inventing zero.

`NativeOwnerSnapshotMain268` accepts snapshot configuration schema `xar.native-owner-snapshot-config/v5`, mode `personal_gold_frame`. This performs one read and archives its original ACK and existing passive heartbeat. It does not submit a control command. Older endpoint modes remain available under their existing schemas.

The real C++ serializer fixtures are checked into Native transport test resources with exact byte and SHA checks. Six DTO cases passed in two phases after the integer-token regression was fixed; the private receiver and endpoint then passed seven cases. Legacy public/protected descriptors were preserved. Runtime also observed personal gold `47986038 / 100000` on the existing actor `31254`, date `53177016`, in a minimized paused 1.21.0 scene. This is personal-balance evidence only.

## Explicit profile input

The older `PreparedProfile.vanilla()` continues to prepare only the NoMods selection. It does not create game settings or promise to suppress tutorial prompts.

`PreparedProfile.vanilla(FileRef settingsSeed)` adds an explicit original settings file. The launch-plan codec emits `xar.java-game-launch-plan/v5` with required top-level `pdx_settings_seed` (`path`, `bytes`, `sha256`); v1–v4 reject that new field. The independent snapshot configuration v5 above has a different schema and purpose.

The source must be an absolute normalized file with positive size no greater than 1 MiB. The plan publisher includes its real content and file-identity witness. Immediately before Game creation, the lifecycle revalidates the source and copies exactly those bytes into the selected isolated profile's `pdx_settings.txt`. An identical destination is preserved; a conflicting destination or changed source rejects creation. No global user-profile settings are read or overwritten, and no undeclared settings defaults are added. Saved child plans preserve the same explicit seed.

Sixteen filesystem/codec regressions passed, including legacy NoMods behavior, real copied bytes, conflicting destinations, changed source, identity replacement, schema rejection and Saved-plan propagation. This guarantees explicit input handling; it does not establish settings as the sole cause of a particular scene's loading time.

## Actor foundation and versioned full observations

The independent `actor_foundation_frame` endpoint uses snapshot configuration v6 and a private read-only receipt. Resource and relationship groups preserve their own availability and original reasons. Signed resource values, full signed IDs, scalar `-1` absence and observed vector order are retained. This partial DTO does not apply the older complete-character relationship rules and cannot become a Core-control or complete-snapshot receipt. Thirteen software cases passed; Runtime then read resources and family data from the original paired 87MB save and observed a separate natural exit.

A qualified Florin Full producer advertises both `game.state.snapshot` and `game.query.fresh-full-state.v1`. Its original state and actor carry distinct `ck3_1210_full_state_v1` / `ck3_1210_played_character_v1` markers plus the exact build tuple. The receiver requires those markers to match the held HELLO, while the shared semantic normalizer uses the same explicit version branch during replay. Legacy unmarked normalization is retained. New signed family IDs do not relax stress, relationship completeness, duplicate, primary-member, trait or legacy-domain checks.

The existing snapshot configuration v1 with `core_prefix_only=false` performs one independent Full read. A matching original state packet and ACK remain separately required. Twenty-two focused cases passed, including authentic C++ packets, new versioned DATA, legacy semantic regressions and receiver rejection boundaries. Runtime then received one independent versioned Full Snapshot and its ACK from the original paired save, followed by a separate natural exit; no Driver or domain adoption was performed. The paused read-only producer does not enable ordinary clock/SAVE actions, running Complete observations, Driver adoption or Root/MCP domain readiness. The endpoint also archives the naturally received heartbeat through its existing passive diagnostics getter, without another Native query.

The Windows seed comparison additionally accepts equivalent `D:/...` and `D:\...` spellings by comparing Paths, exact bytes and SHA. Two regressions preserve tamper and file-identity rejection. This changes validation only; the original request identity/body is not normalized or replayed. Game changes to the destination settings after startup are not prohibited by the seed contract.
