# Actual4 Title Finder route to the current Byzantine holder

Status: shipped GUI/text source route, 2026-10-07. Runtime identity reuses
CK3 1.20.0.4 / Steam25734779 and Root's exact EXE freeze. This lane sent no
input, made no query and read no EXE or running-game memory.

## Exact ordinary GUI route

1. `game/gui/shortcuts.shortcuts:49` maps `find_title_shortcut` to `V`.
   `hud.gui:1078-1084` opens `find_title` with `ToggleGameView`; the additional
   HUD shortcut at 6234-6237 uses the same mapping.
2. `window_find_title.gui:2-6` defines `find_title_view`, logical size 450x700,
   anchored top-right at {-80,130}. The search field is named `input`:37;
   edits call `FindTitleView.OnEdit`:39, Return calls `OnDone`:38. The source
   does not expose native search matching rules or prove that internal keys
   such as `e_byzantium` are accepted as user search text.
3. The actual original localization maps `e_byzantium` to `Byzantine Empire`
   in English (`localization/english/titles_l_english.yml:16282`) and
   `拜占庭帝国` in simplified Chinese (`simp_chinese/titles_l_simp_chinese.yml:16281`).
   Use the current UI language's display name; inspect the actual result.
4. `title_grid`:45 uses `FindTitleView.GetTitles`:51. Each `title_button`:57
   is 50 logical pixels high:59 and clicks
   `ToggleOnCoatOfArmsClick(Title.GetID)`:61. Its valid-holder label is
   `Title.GetNameNoTooltip|U`:67. Select the actual Byzantine Empire row;
   the source does not justify assuming that an arbitrary first result is it.
5. `window_title.gui:4-5` defines `title_view_window`, width628 and full height
   on the left. Its holder area is visible only when the title has a holder
   at 1777-1778. The current-holder component binds
   `TitleViewWindow.GetTitle.GetHolder`:2011-2013; the stock comment at 2039
   identifies this as the bottom-left part of the title window.
6. The holder's portrait is a 165x200 container:2149-2153 using `portrait_torso`.
   That type inherits `portrait_base` (`shared/portraits.gui:965,971`).
   Its left click is `DefaultOnCharacterClick(Character.GetID)`:2939.
   Opening this actual portrait selects the title's current holder; it does
   not rely on a fixed historical character ID or the internal test logs.

Logical layout dimensions are source geometry. Root's owned HWND/screenshot
provides current screen/UI-scale coordinates; this lane did not invent pixel
clicks, focus changes or WM success from these source definitions.

## Root's R71 startup counterexample

Root reports an actual successful ordinary Rurik side start using the official
`-skip -bookmark=bm_867_adventurers -play=d_novgorod` inputs: isolated userdir07
F11 screenshot `screenshots/2026_10_07_2.png` shows paused 2 January 867.
This is Root's actual observation, distinct from this lane's source route.
It avoids waiting for the previously unreachable menu.

Root also reports mod startup/success log entries at 16:43:36, while internal
character-basics test logging still exists. Preserve the engine-test scheduling
cause as unproved. A startup-hook or success log is not an independent reading
of the current Byzantine holder or the traits visible on that holder; inspect
that actual character view for those assertions.

Exact paths and source assertions are in the external
[TITLE-FINDER-CURRENT-HOLDER-SOURCE-ROUTE.json](Z:/ck3_mod_rewrite_process_assets/byzantium-867-review-20261007/frontend-main-reachability-12004/TITLE-FINDER-CURRENT-HOLDER-SOURCE-ROUTE.json).
