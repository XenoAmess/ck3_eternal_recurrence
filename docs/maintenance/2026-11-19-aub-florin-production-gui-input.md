# AUB Florin production decision GUI input

machine_id: desktop-3fevhd2-1c74096080
Source HEAD supplied by Root:0f28fde03c, frozen while R23 Runtime owns the scene.
Target CK3 1.21.0 Florin/build26622941, EXE SHA
2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc.
This fixture/case is source input only: every new Game/GUI/cooldown behavior and
whole-product outcome is NOT_RUN. No product, legacy runner or registry is changed.

## Original requirement and source boundary

The legacy tools/run_auto_upgrade_buildings_acceptance.py:588–745 enumerates all
six real policy labels, scrolls to each, checks localized hover text/no raw keys,
previews treasury_only_pause, personal_only_continue and treasury_first_continue,
then confirms only treasury_first_continue. This is not six actual transaction
matrices. Keep those three preview samples and the initial actual default view.

The two original GUI requirement keys remain exactly:
actual_enable_disable_decision_surface and actual_decision_cooldown_readback
(tools/ck3_mod_acceptance_cases/auto_upgrade_buildings_source_upgrade_core.json:29–30).
The old script has no numeric cooldown getter. Current production
common/decisions/build_decision.txt has no cooldown field: Enable is shown to a
human with enable absent and is_valid alwaysyes; Disable is shown with enable
present and is_valid alwaysyes. Its only Enable execution schedules the original
auto_build.0003 atday1. Disable removes four flags and does not clear queued seeds.
The original wording therefore requires actual behavior readback, not a fabricated
Native number. Same paused-day immediate reappearance/availability/execution of
Enable after actual Disable is the declared observable result. Keep both the
original key and this explicit limitation in Root's actual report.

No smaller existing fixture is safe to mount for this purpose: money, ordinary,
duchy and legacy core scenes write production flags/resources or call production
effects. This dedicated aubgu fixture writes only its own phase/date/resource
baseline variables, observes product flags and opens known Realm windows. It
does not operate the product, add money, mutate a province, change a player, call
auto_build, set/remove product flags, clear global state or delete queued work.
The emitter rejects foreign/production effects, resource/flag writes, non-aubgu
variables and foreign/delayed events before creating output. No parallel runner.

## Inputs and safe ordering

Use the existing shared runtime with a new admitted scene and exact product
projection plus this fixture last. Select normal1066 Robert1128 in the frontend;
do not switch the player by fixture/console. Confirm actual living human identity,
fresh world/profile and initial production-disabled state. Only Root's authorized
current sharedGUI channel performs the actions below; old Native DLL/getters,
another machine's scene or old screenshots have no new credit. Unknown stock
events stop the flow; do not choose an option automatically.

All business is on startupday0, manually paused. maximum_natural_days1 is only
an outer admission envelope. allow_calendar_advance isfalse, every observer
requires elapsed_days0, and the operator must never resume to productionday1.
Script date equality is not independent proof of pause: retain actual pause/date
evidence at every GUI boundary. No Save, advance_day or production scan is needed.

1. Known aubgu.800 start appears only after actual Robert/alive/human and all four
   product flags absent are read. The fixture stores exact initial date/gold/
   prestige/piety/treasury-mode (and actual treasury only when applicable), with
   no resource mutation. Record actual actor, date, pause and funds separately.
   Close the known window while manually paused.
2. Open the actual production Enable decision, not the differently named fixture
   observer. Record the actual initial default treasury-first/continue selection,
   all six policy labels and reachable hovers, and no exposed implementation
   tokens (aub_,_choice_tooltip,is_ai,has_character_flag,character_flag). Retain
   original previews: treasury-only/pause, personal-only/continue, then finally
   treasury-first/continue. These are selection previews, not three purchases.
3. Click the actual second-step and final production confirmation. Retain the
   treasury fallback/no split/continue confirmation copy and actual transition
   to Disable. Then click “Fixture: observe first production Enable” (Chinese:
   “夹具：观察首次生产启用”). Known810 is shown only after enable on and each
   of the three policy flags absent, same actor/date and exact original resources.
   The observer never proves the selection or click; those need actual GUI evidence.
4. Close810 while manually paused. Execute actual production Disable and retain
   the decision disappearance/Enable return and funds/date evidence. Click the
   separate first-Disable observer. Known820 requires all four flags absent with
   the same actor/date/resources.
5. Close820 while paused. Immediately reopen the actual Enable decision on this
   original date. Retain actual availability/confirmability, not just a marker
   or source is_valid. Execute treasury-first/continue again. Click the re-enabled
   observer; known830 requires actual enabled/default flags with unchanged date
   and resources. This stronger behavioral sample supplies the original cooldown
   requirement without claiming a numeric getter.
6. Close830 while paused. Execute actual production Disable again, retaining
   actual GUI action/funds/date evidence. Click final-Disable observer. Known840
   DONE requires all flags clear and unchanged exact actor/date/resources.
7. Leave the product disabled and the timeline paused. Root records independent
   GUI assertions, all seven required read-only markers exactly once, unfiltered
   original logs, final date/resources and actual normal exit. Do not advance to
   let queued production work “settle”. Both real Enable actions may legitimately
   have queued their original day1 seed; the fixture never removes them, and this
   scene grants no internal queue-cardinality or unique-loop credit.

Every failed readback sets only aubgu_phase=-1 and opens known aubgu.900 without
a successor callback. Preserve its real state and reason; do not fix flags, seed
or resources to turn the scene green. Known-window acknowledgment alone is not
actual GUI execution, affordability, progress or final product acceptance.

## Evidence and unchanged scope

Root must independently bind production labels/default/three preview selections,
six hovers, both final confirmations, actual Disable execution, same-day immediate
Enable availability and repeat execution, actual funds/date/pause and normal close.
The seven script markers prove only their stated read-only predicates. Missing
GUI proof keeps the two original GUI requirements false even if all markers exist.

R9's17 money/domain assertions, the three actual-succession requirements, all
building/quota/holding/special/Mandala/duchy cells, raw-log qualification and
publication remain separate. Nothing in this input package changes those tests,
production flags or their old results. The money fixture already observed the
representative production selection on Roger; that is not new Robert Disable or
same-day availability proof. No full-product PASS comes from this case.

Prepare through existing tools/prepare_aub_1_20_fixture.py --scenario florin-gui
with explicit --repo and a fresh external --output. engine_identity reads exact
installed metadata only; it does not qualify Native ABI or operate Game/Steam.
Root still needs to wire the new case into its own current runtime allocation.
Preserve the unchanged producer/base source pins in the private candidate manifest.
