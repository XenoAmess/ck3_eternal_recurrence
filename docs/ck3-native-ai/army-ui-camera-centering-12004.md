# Army selection and camera centering — CK3 1.20.0.4

2026-10-16 correction. The current 1.20.0.4 title-camera capability is an existing typed route. A legacy ABI manifest or a C++ namespace named `ck3_11906` does not establish that the current route is unavailable. The earlier research response made that unsupported inference; this note corrects it without rewriting the historical manifest.

## Current actual result

Root independently observed the following in the current paused session on machine `desktop-3fevhd2-1c74096080`:

- Current capabilities advertised `game.command.center-map-on-landed-title-v1`.
- The occupation query associated Province2635 with TitleID2192; a subsequent title query returned the exact key `b_palermo`.
- The typed center result reported exact CK3 `1.20.0.4`, executable SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`, backend `ck3-1.20.0.4-native-title-map-navigation-v1`, `status=centered`, `postcondition_verified=true`, and camera `settled=true`, with Province2635 provenance.
- The separate asynchronous realm-camera status was `not_requested`. That status does not negate the completed typed title-camera command.

The exact response paths, observation times, byte pins, request arguments and literal native result are preserved in [the small actual projection](evidence/army-ui-camera-centering-12004/actual-projection.json). The title query and center command both report date_raw53147520. The center command binds episode `native-31254-75ef9942b4cf` and connection generation1; capability discovery is earlier and is not represented as a same-frame title observation. This lane performed no SDK call, game operation, desktop input, build or new executable read.

## Source mapping and limits

| Existing source | What it establishes |
| --- | --- |
| `native_bridge/src/ingame_ui_navigation_v1.cpp:53,265–273,989–993` | Army selection invokes `void(handler*, uint32 fullCUnitID, bool)`, currently with `(handler,id,true)`. The existing ABI calls the bool `replace_selection`; there is no established camera bool to expose. |
| `native_bridge/include/xar_bridge/ck3_12004_ingame_ui.hpp:8` | Exact .4 Army selection binds `AF9000`. Selection identity/readback is separate from camera centering. |
| `src/xar_autoplayer/bridge/mcp_server.py:3618` | Existing public typed title-camera tool is `ck3_center_map_on_landed_title_v1`; its published capability must be checked in the actual current session. |
| `native_bridge/research/title_map_navigation_v1_abi.json:3–12` | This particular legacy manifest describes 1.19.0.6. It does not enumerate or veto newer runtime bindings. |
| Current actual capability and typed result | Establish the .4 backend's presence and the recorded title-camera success for this machine/session, rather than inferring them from the legacy namespace or manifest. |

Paths in the table are relative to `ck3_autonomous_player/`. The .4 implementation's complete internal camera call chain was not re-audited here; no new RVA or parameter is inferred from this correction.

For a shot near an army, Root can resolve the current location's actual landed-title key, use the advertised typed title-camera route, verify its independent settled postcondition, and then select the army panel. Title bounds provide the title-centered view observed by that command; they do not promise the army model's exact pixel center, continuous army tracking, or a new `center_army` API. Current full IDs, runtime binding and returned title key must be read rather than guessed.
