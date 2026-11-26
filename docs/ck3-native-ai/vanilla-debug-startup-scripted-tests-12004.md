# Vanilla startup executes internal scripted tests with and without debug on actual4

Status: actual evidence plus bounded source review, updated 2026-10-07 08:38:36 UTC. The game is CK3
1.20.0.4 / Steam build 25734779; exact EXE identity reuses Root's freeze.
This lane performed no launch, process inspection, EXE read, hash, build,
test-runner invocation, SDK call or new live query.

## Actual Vanilla05 result

The original launch receipt records only executable, `-gdpr-compliant`,
isolated `-userdir=...real-test-userdir-05` and `-debug_mode`.
Its native bridge is null; driver/MCP query count is zero; no bridge/DLL/injector
was used. This is actual input evidence, not an assumption about the wrapper.

The existing game.log line 65 at 16:16:40 cites
`scripted_tests.cpp:332` and `tests/character_basics.txt:139`
(`test_close_family`). Thus the native scripted-test runner executed.
Debug.log lines 9857-9872 record a transfer from Konstantinos 1732 to Harold 122;
game.log line 53 records Harold/history 122 already holding Byzantium.

The installed stock `game/tests/200_qa_inheritance_tests.txt:45-58`
directly matches that mutation: block `get_byz`, name
`Harold gains Byzantium`, character target 122, effect
`get_title = title:e_byzantium`, expectation that the title is held.
`character_basics.txt` also contains genuine flag/trait/death/creation effects.
These are executable test definitions; the observation is not inferred from
BootDate, load-history or InGame idler names.

## tests.txt is not an identified startup input

Actual userdir 05 `tests.txt` is exactly:

```text
Tests:
[ OK ] Error log
```

Its content is a status summary, with no command, suite selector, effect or
startup instruction. The held actual runtime source, retry02 runner and scoped
GUI/settings provide no read/write entry for it. Its exact native producer and
any engine reader remain unproved within the permitted text/source scope.
Do not delete or rewrite this report as a supposed way to stop script tests.
The summary also does not describe every actual game script-test result.

## Launch and settings closure

The bounded runtime `_ck3_launch_command:2352-2385` creates only executable,
gdpr and userdir arguments; explicit continue-last-save/load-save are optional.
The launch/CreateProcess path forwards that list. EnvironmentSpec has no
generic extra/test argument field; its settings renderer writes tutorial,
cloud, display and language settings.

Actual userdir 05's expanded `pdx_settings.txt` has no startup, bookmark, menu,
automated_test, skip, debug_mode, load or continue setting. Its tutorial/language
values differ from the renderer template, so this review does not invent its
creation provenance.

The shipped `game/_commandline_options.info` documents `-debug_mode` as
developer mode, `-skip` as direct startup/history skip, `-bookmark` as
bookmark selection, and a separate `-automated_test` option. The actual05
argv contains none of the latter three. Bounded original defines/settings
do not expose a script-test scheduling guard.

The exact internal branch from the observed startup inputs to scripted-tests
execution remains unproved without further native-engine source evidence.
The real no-Bridge/no-MCP execution narrows the cause to the game/input context;
it does not by itself prove that debug_mode is the specific guard.

## Vanilla06 disproves debug removal as prevention

Root's actual R70/Vanilla06 receipt contains exactly executable,
`-gdpr-compliant` and isolated `-userdir=...real-test-userdir-06`.
Bridge/DLL/injector use remains false and driver/MCP query count remains zero.
Root still observed the automatic 1066 lobby. The no-debug run also genuinely
executed native scripted tests: game.log lines 21/24 at 16:27:10 name
`tests/000_history_1066_tests.txt:18/45`; lines 26/33 name
`tests/000_powerful_vassals.txt:2/16`; line 45 at 16:27:11 names
`tests/character_basics.txt:139`. These are `scripted_tests.cpp:332` entries.
Thus `-debug_mode` is not a necessary condition for either observed outcome;
removing it did not fix the startup or stop the internal tests.

The single bounded debug.log selection records Frontend at 16:26:09,
Bookmark at 16:26:13, generation completion at 16:26:24 and Load Save at
16:26:29. No unselected InGame entry is inferred. Vanilla06 `tests.txt` still
contains only the same 24-byte summary. These hot logs were read once.

The actual06 runner imports held g110-r16 runtime, returns the original
command unchanged, disables Bridge environment configuration and launches
with continue-last-save false. Runtime passes `cwd=spec.game_exe.parent`
(the actual binaries directory) and `lpEnvironment=None` to CreateProcess.
This inherits the caller environment; actual inherited values are not recorded
by the receipt and were not inspected or dumped. The reviewed creation path
does not read `game_launchoptions` or turn environment values into arguments.

Actual root/binaries file metadata contains no startup options text. A bounded
installation filename search for launch-options, commandline and test-settings
files finds only `_commandline_options.info` and `launcher-settings.json`.
The latter's normal `exeArgs` is only `-gdpr-compliant`; its Debug alternative
adds only `-debug_mode`. Scoped Steam localconfig parsing finds no
`LaunchOptions` field under app 1158310; no account/token data is exported.
This does not prove which internal engine guard scheduled the tests.

## Source-confirmed ordinary 867 bookmark option

The shipped `game/_commandline_options.info:15-16` defines
`-bookmark=<bookmark_name>` to choose a bookmark/start-year. The installed
`game/common/bookmarks/bookmarks/00_bookmarks.txt:671-679` defines the playable
`bm_867_adventurers` with date 867.1.1; lines 713-724 define Rurik 40605 and
`d_novgorod` inside that bookmark. The concrete normal-side input candidate is
the existing three-argument launch plus `-bookmark=bm_867_adventurers`.
This uses a documented bookmark selector, with no console, forced date/effect
or character grant. Source evidence does not qualify it as suppressing tests,
reaching the mainmenu, or starting a normal Rurik campaign; Root owns that
actual outcome. No invented menu/test-disable flag is proposed.

[The existing normal Rurik 867 route](frontend-debug-startup-main-menu-12004.md)
remains the original selected-bookmark/ruler route. Preserve Vanilla05 and
R67/R68 logs/failures; an empty paused preview or test-mutated history is not
evidence that a legitimate normal 867 campaign was started.

Full paths, command/JSONpointer assertions, source lines and boundaries are in
[VANILLA05-INTERNAL-TESTS-READONLY-REVIEW.json](Z:/ck3_mod_rewrite_process_assets/byzantium-867-review-20261007/frontend-main-reachability-12004/VANILLA05-INTERNAL-TESTS-READONLY-REVIEW.json).
The distinct no-debug counterresult and concrete bookmark recipe are in
[VANILLA06-NO-DEBUG-COUNTERRESULT-REVIEW.json](Z:/ck3_mod_rewrite_process_assets/byzantium-867-review-20261007/frontend-main-reachability-12004/VANILLA06-NO-DEBUG-COUNTERRESULT-REVIEW.json).

## Root's later R71 ordinary-side startup result

Root reports that the documented `-skip -bookmark=bm_867_adventurers
-play=d_novgorod` route actually reached normal paused Rurik on 2 January 867,
with isolated userdir07 F11 screenshot `screenshots/2026_10_07_2.png`.
This is an actual startup outcome supplied by Root, not qualification of a
test-disable option. Internal character-basics logging still exists; the
test-scheduling cause remains unproved and is not a new startup gate.
The mod's success log does not establish the current Byzantine holder or
that holder's traits. Use the [current-holder GUI route](title-finder-current-holder-gui-route-12004.md)
for Root's independent owned-UI observation.
