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
