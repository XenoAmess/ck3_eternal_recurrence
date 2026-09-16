# FEUDAL-1066-START-B0: default-OFF private integration seam

This work package is pinned to CK3 1.19.0.6, ck3.exe SHA-256
2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86.
R740 proved one legal Murchad candidate in a Bookmarks model frame but read
selected_character_index=-1. It did not create a 1066 campaign.

The native selector now has a separate frontend operation
select_supported_1066_character = 13. It re-reads the exact current
GameSetup owner, selected Bookmark key/date, unique key-derived element,
collection bounds/parent and final government before calling original setter
RVA 0xF707E0 once on application-main. The same-frame index is diagnostic.
The controlled runner sends a separate model query and requires the new frame
to select the same current key before submitting existing StartGame once.
The native StartGame operation also re-probes that index and verifies the
selected projection plus original button fireability.

bridge.cpp and CMakeLists.txt remain the single writer's files and were not
edited by this package. The bridge.cpp integration is three narrow additions
under the existing default-OFF
XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1 flag:

1. Accept private protocol step select-frontend-supported-1066-character-v1
   in the same frontend request condition that accepts the private
   activate-frontend-start-selected-bookmark-v1 step.
2. Map that step to FrontendGuiRouteOperationV1::select_supported_1066_character
   before the existing StartGame mapping.
3. Keep the current ACK-pending response only when target_resolved and
   dispatch_invoked. On refusal, return the selector's unavailable_reason
   as RED/rejection evidence. An already-submitted setter with a lost reply
   must not be repeated.

frontend_bookmark_model_probe_v1.cpp and frontend_gui_route_v1.cpp are already
linked by the native bridge. No new CMake source is required. The controlled
runner option --bookmarks-read-only --bookmarks-model-private
--bookmarks-select-start-private first uses official MCP NewGame/Bookmarks,
then the private typed selector and StartGame protocol, independent paused
public campaign-root, and a material paired checkpoint. It is an acceptance
route; native_auto_run consumption, cold restore and the full campaign remain
separate gates. There is no public MCP query/action registration or capability
advertisement in this source package.

Compatibility: this private default-OFF protocol step changes no frozen
preview DLL, production action surface or open_kaishek frontend contract.
The public frontend query/action adapters and open_kaishek impact must be
re-evaluated after real selected-model, StartGame and paused campaign results.
The existing Bookmarks model query is a version-bound read-only native
research asset; public MCP mapping and general-asset registration remain
pending. This private selector is not advertised as a general MCP asset.

## FEUDAL-1066-PRIVATE-BRIDGE-GLUE source candidate

The separate bridge glue package accepts the selector protocol step under the
same default-OFF feature option as private StartGame, maps it to operation 13,
and returns the native selector's refusal reason when no setter was submitted.
Only a resolved target plus a submitted setter receives
`acknowledged_verification_pending`; that ACK still requires an independent
Bookmarks model requery before StartGame. The exact CK3 EXE SHA above was
rechecked locally. Both /Od and /O2 bridge.cpp compilation with the private
selector and model options passed, as did seven focused controlled-runner
ordering tests. This is source/ABI evidence only; no game action was run by
this package. Public protocol registration and capability advertising remain
OFF.

## R747 typed selector admission RED

R747 used the sealed fa7275 Release DLL and the same CK3 1.19.0.6 EXE SHA
above. The official MCP NewGame/Bookmarks path produced a fresh native
`identity_ready` model: the selected index was -1, the selected Bookmark was
`bm_1066_rags_to_riches`, and the current Murchad key-derived target was
index 0 among five distinct dynamic keys with final feudal government. The
controlled runner sent one typed
`select-frontend-supported-1066-character-v1` request and received
`command_result.ok=false, error="unsupported native gameplay step"` in
0.011 seconds. The selector and StartGame had not reached application-main;
StartGame was not submitted. The failed artifact remains at
`C:/g2feudal1066-live/candidate-typed-private-01/typed-private-live.json`
with SHA-256
`4A95DC44D368122D98371D026FC07DD423DE8BD97DA1B3BB96122E489C41B628`.

The deterministic cause is the earlier top-level `bridge.cpp`
`execute_step` admission check: it exempted the private Bookmarks model
probe but omitted the two private selector/StartGame steps. The frontend
mailbox mapping itself was compiled but unreachable. The narrow source fix
exempts those two exact steps only when
`XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1` is ON;
the existing application-main legality checks, next-frame Bookmarks requery,
ACK-pending semantics, public OFF state and unknown-action no-retry behavior
still apply. This RED stays open until a new frozen DLL passes real paused
frame/StartGame material results; a static build cannot close it.

## Ordinary `xar_off` seed binding

The controlled runner now has an explicit
`--ordinary-campaign-xar-off-seed` mode. It is valid only together with
`--bookmarks-read-only --bookmarks-model-private
--bookmarks-select-start-private`. The supplied `--state-dir` must already
have been prepared with `prepare-profile --xar-enabled xar_off`, and
`--source-profile` must name that same state directory's `profile`; this mode
does not copy or relabel another run. Before launching CK3 it performs the
normal prepared-profile verification, requires exactly one
`xar_enabled=xar_off` rule plus a valid environment digest, and rejects stale
driver/checkpoint state. The driver is then created with an
`ordinary_campaign_succession`/fresh-no-pact lifecycle binding.

The public campaign-root must independently report `xar_off`, no `xar_on`,
and ready selected-rule telemetry. The paired checkpoint gate additionally
requires that the command result, persisted driver state, persisted
`last_checkpoint`, and its command-history anchor all contain that exact
binding. This prevents the earlier R750/R751 `xar_on` save from being
relabelled as the standard ordinary campaign.

R782 exercised this seed path on the frozen build. A fresh CK3 process created
the Murchad/1066/standard-feudal campaign with `xar_off`, wrote a lifecycle-bound
checkpoint at `date_raw=53144328`, and returned the entire process tree to zero.
The controlled live report is
`C:/ck3_mod_rewrite_process_assets/g2-r782-ordinary-xar-off-seed-20260916/live-attempt-02`
(SHA-256 `695234CFE699CA9145246FE0747D422CCE76FFFE31309148A222F5B05B70FBB1`);
the seed save/driver pair is `94FA7F56...89F41` / `66EC923D...31C42`.

R783 then launched a different CK3 PID through formal `native-auto-run`, cold
restored that pair, and completed 20/20 bounded turns. Its strategy queried
legal declarations and exact power in paused frame `native:8`, submitted one
typed declaration, observed `war_changed` in independent frame `native:9`, and
the next formal turn consumed WarID 5 through the termination-options query.
Later turns raised ArmyID 33, observed gathering become regular, issued a
previewed move, and reached combat before the final paired checkpoint. The
formal report is
`C:/ck3_mod_rewrite_process_assets/g2-r782-ordinary-xar-off-seed-20260916/r783-formal-attempt-03/stdout.jsonl`
(SHA-256 `EF35A85242A95D3FE07A2C3EA8B5D6B3C932E38C49FFFC6E03A2D824AE459337`);
the independent verdict is `r783-verdict.json` (SHA-256
`8F9F6D1A278E4BD25BAD02371C585CA21F94077EC254AEFB30329C1223D9FA7F`).
The final save/driver pair is `74294B03...EDF1A` / `354D4DE3...FE34B`, and
cleanup was proven.

This closes the live seed and same-state formal cold-restore gate. It does not
yet make a portable ordinary preview ZIP: the operator must carry the
`xar_off`/ordinary/no-pact triple, and a copied seed must be rebound to the
target prepared environment without changing the CK3 save bytes. It also does
not prove natural same-campaign succession or a 1066-to-1453 campaign.
