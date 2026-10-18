# Finite maintenance writer watch: ordinary native campaign owner

This is a source candidate for CK3 1.20.0.4, based on a5744dd8d2efd6bfcb84af2dd0d424ee00efaa33. It does not qualify a native build, attach a debugger, or establish a maintenance payment. R215 remains core-only.

The R214 original Save-independent snapshot has `episode_projection="native_campaign"` and no `episode_run_id` key. It is incorrect to stringify that absence, substitute a managed run alias, or grant the compiled a07 observer a new parameter. The default `episode_bound_v1` still requires the original nonempty episode string. Only the explicit `native_campaign_owned_no_load_v2` mode accepts an original null or missing episode in an ordinary native campaign.

The new mode binds the original paired snapshot and payment journal to PID, exact process FILETIME, native connection generation, player Character full ID, local player, GameState, native revision/date, no-load controlled window/payment epoch, current Character/context addresses, and the retained 0x28F7840 callsite anchor. The common collector uses the existing CaseClient and only snapshot plus `payment_sampling="query"`; it does not enable sampling or start a watch. Its caller must explicitly pass the new mode. A manufactured FullArmy managed-run alias is not an acceptable native episode input.

The metadata records an empty `episode_id` together with explicit null/version fields. Admission and raw observation use v2 schemas with JSON null and preserve whether the original key existed. The observer requires `--ordinary-null-owner-binding`; v2 metadata without that option and legacy mode with an empty episode are rejected. Legacy raw v1 remains separate.

Before ordinary admission, the SYSTEM build receipt must contain the exact new maintained `cold_observer.cpp` source hash. The frozen a07 source is 23,688 bytes, SHA256 `24b9d584ee451ef822c6386484efcda2578072cb5569ce1740b910e3bbadd0ee`; its 102,912-byte executable SHA256 `67e5f6c0bb43ff0c00116be7356da25d792d1eb275a85fe719bf0b7bff32cce9` remains incompatible. The maintained baseline additionally contains the optional known-copy caller capture, so it must not be labeled the a07 compiled source.

The new native checks read process creation FILETIME, the mapped image/known instruction anchor, GameState slot at module+0x5C68C50 twice, CDate at GameState+8, absolute day at +0x9C, Character ID/magic/alive state, and the Character+0x1C0 context twice. The date range is the admitted day through one actual day. Connection generation, local player, controlled window and epoch are bound from the actual paired native/public inputs and must be checked by the Root controller's fresh pre/post reads; those metadata values are not claimed as independently read by the external executable.

The independent Root driver delta preserves its held Popen, unique Start, ready/armed gate, original single clock, natural timeout and restore/detach rules. Ordinary mode requires an explicit exact new `build_card` pin and exact 15-item observer argv; legacy mode retains the 14-item contract. That external delta is not an automatically registered public actor or a future scene authorization.

One offline production compound exercises the actual R214 missing-key frame through prepare ownership, metadata, actual consumer binding/projection, explicit build-card, common collector, and Root argv seam. Cash/FILETIME/native raw in that compound are synthetic, with no SDK, game, native build or debugger execution. A future new observer build, exact SYSTEM exclusion readback, focused cold qualification, fresh paired inputs and a separate Root DR admission are still required. No writer hit, military payer, paid amount or cadence is established; even a same-value write remains a write observation rather than payment evidence.

Canonical offline check after application:

```text
python -B -O ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/test_owner_binding.py --repo <repo> --output <new-result.json>
```

The portable candidate receipt retains exact pre/post source pins, the historical a07 comparison, focused results, and the separate external Root driver delta. It does not copy large game wire files.
