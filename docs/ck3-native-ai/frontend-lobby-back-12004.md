# Actual4 lobby Back private step

Status: `static-ready` source candidate, authored 2026-10-07; compilation and
game execution belong to Root and have not been performed by this source lane.

The concrete trigger is the R67 isolated debug launch landing in the
choose-any-character lobby at 1066.9.16 instead of the harness's expected main
menu. One owned Escape hid the lobby overlay and exposed the empty-player
paused table map; it did not perform the Back button's `ReturnToMenu` callback.
No new ordinary campaign or 867 test effect is established by those observations.

Actual evidence is under
`Z:/ck3_mod_rewrite_process_assets/byzantium-867-review-20261007/`:

- `real-test-state-03/root-responses/001-independent-current-frontend-route.json`
  accepted the route `lobby` with runtime entry18, frozen source 750b8c51.
- `real-test-state-03/root-responses/005-current-frontend-tree.json` contains
  966 widgets. The unnamed, visible, enabled Back button is at child path
  `[1,1,1,0,0]` below `lobbyview`.
- `real-test-userdir-03/screenshots/2026_10_07_1.png` shows that lobby and Back;
  `2026_10_07_2.png` shows the state after the owned Escape.
- `frontend-main-reachability-12004/R67-BACK-RECEIVER-AND-SHORTCUT.json` records
  the existing source alignment. Actual4 `game/gui/multiplayer_lobby.gui`'s
  `lobby_view_back_onclick` overrides the template callback with `[ReturnToMenu]`;
  that Back template declares no keyboard shortcut.

The private native `execute_step` string is
`activate-frontend-lobby-back-v1`, with `expected_revision: 0`, using the existing
frontend mailbox and actual4 GUI environment. It maps to internal operation
`lobby_back = 41`. The receiver requires the resolved route `lobby`, follows the
fixed path above, and reuses `DispatchFixedGuiWidgetNativeV1` with the current
widget's observed vtable and the existing GUI admission. There is no caller
supplied widget path or pointer. The standard successful dispatch response is
`acknowledged_verification_pending`; a later actual route observation must
establish the visible outcome. The current held entry18 DLL predates this step.

The source change is limited to the existing `frontend_gui_route_v1.hpp`,
`frontend_gui_route_v1.cpp` and `bridge.cpp`. There is no new CMake target,
translation unit, advertised capability, registered MCP tool, or DTO layout.
Root's existing dependency-aware incremental builder selects the affected
header dependents and refreshes the Runtime archive/DLL as needed. Direct
private native submission uses the existing frontend helper; the registered
generic `ck3_execute_step` public action inventory does not publish this step.

The action retains the full pre/post `SameExecutionBoundary` comparison. The
earlier query-only drift repair is described in
[frontend-query-startup-drift-12004.md](frontend-query-startup-drift-12004.md).
No action boundary relaxation, additional ABI gate, test matrix, or new EXE read
is part of this repair. Whether ReturnToMenu completes and what boundary it
changes remain actual-run questions; the source candidate is not live evidence.
