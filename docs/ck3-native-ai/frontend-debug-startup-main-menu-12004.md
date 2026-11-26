# Actual4 debug startup and main-menu reachability

Status: source-only readonly investigation, 2026-10-07 07:42:57 UTC. CK3 1.20.0.4,
Steam build 25734779, EXE SHA-256 98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518.
Identity is reused from Root's installed-build freeze; this lane read no EXE
and performed no launch, process inspection, build, test or SDK query.

R67/R68's current side instance arrived in the 1066 lobby with an empty player.
Root observed that Escape and the owned visual Back action hid the lobby to an
empty paused preview. Those observations establish neither mainmenu nor a
started ordinary campaign. A BootDate/InGame idler log is not a Start outcome.

## Source conclusions

The current original `game/gui/multiplayer_lobby.gui:111-112` overrides its
inherited Back callback with `[ReturnToMenu]`. Its `_hide:13-18` only clears
tabs and closes the lobby helper. Inherited
`jomini/gui/multiplayer_types.gui:1757` requires `LobbyView.CanGoBack`.
A separate owner is diagnosing the current native Back false/failure0;
this investigation does not reimplement or execute that action.

Both actual isolated userdirs 03/04 contain 7,087-byte `pdx_settings.txt`.
Their read contents expose ordinary settings and no startup/menu/bookmark/year
override. `tests.txt` in both is exactly a generated
`Tests: [ OK ] Error log` result. No skip-menu/profile/debug-mode option was
found in the scoped original frontend/bookmark/lobby GUI and shipped settings.

The original `00_bookmarks.txt:1624-1629` marks
`bm_1066_rags_to_riches`, 1066.9.15, as `test_default=yes`.
This is a concrete default-test bookmark marker. Its relationship to
`-debug_mode` startup dispatch remains **unproved** within the permitted
local-data scope; no menu-forcing command-line flag or setting is recommended.

The held retry02 wrapper `run_byzantium_867_background_retry02.py:258-263`
adds `-debug_mode`, launches with `continue_last_save=False:276-277`,
and unconditionally waits for `main_menu:296-302` before NewGame.
That initial-page assumption conflicts with R67/R68's observed lobby.
The held RECIPE JSON's arguments are debug_mode, gdpr-compliant and an
isolated userdir; its `SOURCE_ONLY_NOTRUN` status is retained.
Existing frontend startup-drift research already found no auto-Start use in
the bounded bridge bootstrap/FEUDAL flag production uses; reuse that conclusion.

## Existing normal Rurik 867 route

Use the original selected-ruler route after actual Back reaches mainmenu:

1. Mainmenu `new_game_button` invokes `FrontEndMainView.OnNewGame`
   (`frontend_main.gui:779-784`).
2. Select `bm_group_867` through `SelectBookmarkGroup`
   (`frontend_bookmarks.gui:2891`); the original group has default date 867.1.1.
3. Select `bm_867_adventurers` through `SetSelectedBookmark`
   (`frontend_bookmarks.gui:3240`); it is playable/recommended and in group867
   (`00_bookmarks.txt:671-679`).
4. Select `bookmark_adventurers_rurik_rurikid` through
   `SetSelectedCharacter` (`frontend_bookmarks.gui:193,240`).
   The original record has history ID 40605 and title `d_novgorod`
   (`00_bookmarks.txt:713-724`); Helgi 40606 is a separate option.
5. Original `start_button` invokes `GameSetup.StartGame`, gated by
   `GameSetup.CanStart` (`frontend_bookmarks.gui:2049-2058`);
   the selected-character animation invokes `GameSetup.OnStart:70-72`.

`Pick Any`/`OnCustomStart:78` follows a different branch and is unnecessary.
The existing 1066 preparation-lobby Start does not select a new 867 bookmark.
Source existence of the callbacks does not qualify the side instance's normal
867 start or mod effects; Root retains the actual route/outcome verification.

The complete exact path/line/JSONpointer ledger is
[DEBUG-STARTUP-MAINMENU-READONLY-REVIEW.json](Z:/ck3_mod_rewrite_process_assets/byzantium-867-review-20261007/frontend-main-reachability-12004/DEBUG-STARTUP-MAINMENU-READONLY-REVIEW.json).
R67/R68 failure observations and the independent native Back diagnosis remain
unchanged. No profile edit, novel CLI flag, forced effect, console or character
grant is part of this work.

## Actual no-debug counterresult and documented bookmark input

Root's R70/Vanilla06 launch omitted `-debug_mode` and still automatically
reached the 1066 lobby. Its original logs also name native scripted tests.
Removing debug did not restore the menu or stop those tests; the internal
startup trigger remains unproved within the bounded text/source review.
The official local `_commandline_options.info:16` supports
`-bookmark=bm_867_adventurers` as a concrete normal 867 input candidate.
It does not qualify test suppression or a normal campaign before Root's
actual outcome. See [the distinct counterresult](vanilla-debug-startup-scripted-tests-12004.md).
