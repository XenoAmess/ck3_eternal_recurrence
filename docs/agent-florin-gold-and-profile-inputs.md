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
