# Ordinary campaign checkpoint lifecycle metadata

R8 consumed frozen `67f8c101cd4604a54f969a13bf89f6b6147d1a25` with
`episode_projection="native_campaign"`. Its native event and save operations
succeeded, but `checkpoint.succession_lifecycle` reported the legacy driver
default `rogue_one_life` / `xar_on`. That dictionary is not an observed CK3 game
rule or a description of the current save's native succession policy.

The source trace is explicit. With no lifecycle binding, the driver constructor
retains `legacy_rogue_one_life_binding_v1()` for existing callers. The previous
`_execute_save_checkpoint` copied it into the checkpoint result after native
submission and file materialization/SHA-256 verification. The same report can
be stored in Python command history and driver-state JSON, separate from the
CK3 save file. `GameplayBridgeService.save_checkpoint` forwards the result;
it does not translate that dictionary into rules or native commands.

The actual 1.20 `SubmitSaveCheckpoint` reads core state, constructs the fixed
autosave command/name and submits a native command copy. The request contains
the step and current native revision; no lifecycle dictionary, XAR rule or
succession policy enters it. The `native_campaign` snapshot projection returns
before one-life episode binding, leaving episode character/run IDs null. Seed
creation also returns without writing an episode seed when those IDs are absent.
This trace establishes that the reported default did not change rules,
inheritance or engine save bytes. It does not independently prove what the
actual game's rules or future inheritance outcomes are; those require native
or save-content evidence.

The narrow future-consumer repair changes only checkpoint reporting in
`NativeHeadlessGameplayDriver`. Native-campaign saved and unavailable checkpoint
results now carry `episode_projection="native_campaign"` and
`succession_lifecycle=null`. One-life callers retain their existing metadata.
Internal legacy controller configuration and driver-state schema remain
unchanged; neither is CK3 rule evidence. No bridge ABI, native save request,
engine save bytes or gameplay strategy is changed.

Validation passed 46 clock/profile/campaign/wait/semantic tests. New real-provider
`FakeEndpoint` tests execute both campaign and legacy saves, assert exactly one
unchanged native save request, match actual fixture bytes/SHA-256, and check null
episode IDs/no seed for native mode. Another test covers unavailable save-dir
metadata. Existing checkpoint materialization and unavailable-dir regressions
also pass. Command from `tools/`:

```text
python -m unittest test_ck3_native_campaign_projection test_ck3_native_clock_reader test_ck3_native_profile_mcp test_ck3_native_profile_wait test_desktop_semantic_action_mcp
```

Ownership stays in the authoritative SDK here. `open_kaishek` preflight is not
applicable to Python result metadata around native autosave; no CK3 script
semantics are changed. No live input, service replacement, DLL replacement or
attachment occurred in this package. R8 remains frozen at `67f8c101`; its old
receipts must retain their exact legacy report and must not be interpreted as
game-rule evidence or rewritten to this future metadata format.
