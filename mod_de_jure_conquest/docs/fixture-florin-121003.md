# Fresh-tier scripted matrix preparation for Florin 1.21.0.3

This follow-up changes fixture tooling only. Production runtime, gameplay and
Workshop3812510217 are unchanged. Machine desktop-3fevhd2-1c74096080;
reviewed engine 1.21.0.3/26785313, EXE SHA
859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28.
All fresh Game/Native/GUI/payment/peace/SaveLoad/full-product checks are NOT_RUN.

Generate three separate fresh single-player Robert1128 games at 1066.9.15. Load
the exact production projection plus exactly ONE matching fixture. Never combine
tier fixtures in the same game. The Runtime owner must independently bind each
new scene, runtime/fixture/EXE hashes, real date/paused state, logs and normal exit.

```text
python -B -X utf8 mod_de_jure_conquest/tools/gen_acceptance_fixture.py --tier duchy --output <fresh-duchy-fixture>
python -B -X utf8 mod_de_jure_conquest/tools/gen_acceptance_fixture.py --tier kingdom --output <fresh-kingdom-fixture>
python -B -X utf8 mod_de_jure_conquest/tools/gen_acceptance_fixture.py --tier empire --output <fresh-empire-fixture>
```

Each tier keeps the original three outcomes and eight predicates per outcome:
AI refusal, distinct realms, native can_declare_war, native participants, actual
production-captured goal, exact county owners, ended war and unchanged outside /
already-owned counties. All 72 original PASS names and complete limit blocks are
protected by regression. BEGIN/DONE are not extra business assertions; DJC01--13
remain full acceptance obligations rather than thirteen markers.

Each reset grants the original counties back using the official granted title
transaction, refills funds, applies negative add_stress, and cancels only the
player-to-primary-top-liege truce. Only the captured Naples holder is eligible
for an independency transaction, only if it was actually independent in this
fresh game and is now under the player. HRE vassals are never mass-liberated.
The ready event runs two days later, requires the two-day flag to have expired,
and reads actual stress=0, exact holders, living actors, AI primary, top lieges
outside the player, funds, prestige level, absent directed truce and unchanged
outside/player-owned counties. Original distinct-realms and native eligibility
predicates must pass before start_war. One matching created war is required.

The next day reads actual production participants and the war-local captured
goal before end_war; another day reads county/outside state and ended war. Each
failed check stops successor scheduling and opens the known fixture realm
failure event900, with no automatic stock-event selection, forced war, queue
purge or repair after failure. Native war creation/settlement is scripted setup,
not normal GUI declaration payment or native peace-entry legality.

From day0 the nominal tier schedule is: init1, reset2, ready4, inspect5, result6;
reset7/ready9/inspect10/result11; reset12/ready14/inspect15/result16. Each tier
has max18 natural days, absolute latest date1066.10.3 and watchdog901 at day18.
Normal completion opens known visible realm event800 with an empty close option;
failure opens900. These request the ordinary single-player event pause. The
Runtime owner must actually observe the known window and paused date, keep the
calendar paused and end normally. No Game pause API or minimize/front-focus
exception is invented. Actual callback timing remains a fresh-game assertion.

Stock game_start.txt:5784--5790 schedules Robert bookmark.1070 at days35--120.
The three separate day18 runs avoid that earliest boundary. Default --tier all
still emits the complete 72-marker contract, nominal46/max48 days; it does not
avoid Robert's event and is not the recommended fresh-game recipe. Do not change
dates, delete pending stock events or auto-select an unknown event to get through.

Verify each original log with its own emitted contract, then aggregate three
different exact log/contract pairs. Repeated --log and --contract arguments are
paired by their respective order. Existing one-log CLI and legacy v1 all-tier
contracts remain supported; report targets must be fresh.

```text
python -B -X utf8 mod_de_jure_conquest/tools/verify_fixture_log.py --log <duchy-debug.log> --contract <duchy-fixture>/fixture-contract.json --report <fresh-duchy-report.json>
python -B -X utf8 mod_de_jure_conquest/tools/verify_fixture_log.py --aggregate --log <duchy-debug.log> --contract <duchy-fixture>/fixture-contract.json --log <kingdom-debug.log> --contract <kingdom-fixture>/fixture-contract.json --log <empire-debug.log> --contract <empire-fixture>/fixture-contract.json --report <fresh-aggregate.json>
```

Aggregation requires exactly duchy/kingdom/empire, each of its original24 markers
exactly once, a disjoint exact72-name union, one BEGIN/DONE per log and no FAIL,
STOP or unknown PASS. Duplicate/missing markers, swapped or repeated tiers,
reused paths, altered marker contracts, booleans in integer fields and malformed
inputs are rejected. Three log files alone cannot prove three fresh games; their
actual run/scene and exit bindings remain independent mandatory evidence.

Software qualification uses synthetic unit logs clearly labeled NOT GAME. No
synthetic PASS log is actual game evidence. Ordinary GUI fees, resource/level
boundaries, native peace legality, invalidation/deaths, concurrent wars, automatic
armies, physical Save/Load, Chinese actual GUI and coexistence remain independent
DJC01--13 obligations. See test-plan.md and migration-florin-121003.md; no old
1.20 qualification or basic-load zero-day case fills these gaps.

Optional final-duchy same-world ordinary GUI/physical SaveLoad observer: see
[gui-save-observer-florin-121003.md](gui-save-observer-florin-121003.md). It does not
replace any original matrix predicate, actual GUI action or physical Load proof.
