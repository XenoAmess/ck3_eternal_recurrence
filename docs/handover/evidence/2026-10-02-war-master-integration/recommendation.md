# CK3 upgrade integration scope — read-only analysis, 2026-10-02

Observed origin/master: `67184ba9d`. All four requested source worktrees were clean under `git -c core.longpaths=true status --short --branch`. No source files, refs, or remote state were changed by this analysis. External JSON reports in this directory retain complete commit/path inventories.

## Primary source closure

| Source | Current exact tip | Unique commits against master | Value |
| --- | --- | --- | --- |
| codex/war-series-brown-gold-20261001 | 04bf1fe17de2a351288b70d9292316535d69d7de | 28 | a04–a09 source, evidence and failures, audited narration, BGM compositor, delivery/review records, latest handover |
| codex/war-e2-mechanism-closure-20261001 | c4e87182397e19ccb4112617bde13168d96eb50d | 15 | R0148/R0149 conclusions, all original UI/observer/trace/identifier append patches |
| ie | ff1b17dc294fb416667f849636d07dadf47f2567 | 6 | H3937 physical inventory/single query/queued wakes, H2743 stock predicate source and consumer closure |

`431461d6841604ebd19e65670661ca2a732dbff8` and all earlier war-e2 capture tips are ancestors of `c4e871823`; no additional merge is needed for those branches. The three primary tips are mutually independent. Shared d5f3c5121 isolation policy appears in video and ie histories.

Fourth major source: `96acba4f1da547b523683eaa5ce346207c03b877` (`origin/codex/episode02-review-preview-20260930`). It includes the older full episode source closure and is not an ancestor of the three primary tips/master. Of its 238 changed paths, 188 are absent from all current primary/master trees. These include historical subtitle/PTS/reel/assembly modules, source-bound cards, capture audits, associated tests and original research records. Merely merging the three primary tips would omit these valuable second-episode sources.

One extra older episode tip has three paths outside the preview tree: `a3fdd31ca8631644cb6341b85db2ae0b29b7c1b4` (`promo/episode02-raw-visual-index-20260928`) adds `e2-05-a02-transition-localization-20260929.md`, `list_e2_05_frozen_pts.py`, `test_list_e2_05_frozen_pts.py`. Other maximal episode tips (including English review, cards, subtitle, historical terminal TTS and production declarations) add no distinct missing paths beyond these sources. That is a path-preservation finding, not proof every modified overlapping blob is semantically identical.

## Already delivered into master

`git cherry -v origin/master codex/war-e2-mechanism-closure-20261001` proves the first three commits are patch equivalent:

- 59ca8861d = main 97abec0f9: managed gameplay recorder wiring.
- fd3656fc5 = main 6685cc8b7: process gates and retained injector evidence.
- 475bdbffd = main b387fe5ba: sealed rebuilt JD11 pair binding.

Main `62e6cb41c` explicitly projected only a 20-file dependency closure from frozen preview `96acba4`/`62e39f9`, rather than merging the whole preview tree. Main `7f09ac3b8` has later a03 UI review source. Main also already delivered H3 canonical `ba885d0f3` and ROLE canonical `fb32a5ca5`; preserve their current production logic when reconciling ie's older projected sources. Non-ancestry alone does not mean those features are absent.

## Additional related war archive closure

The ie handover addendum references related H2743/H3937 and R0266 work whose producer/consumer code was selectively projected, leaving many standalone tests, read-only researchers and historical knowledge documents absent from master and ie. Complete absent-path coverage across those directly associated ref families is recorded in `missing-path-cover.json`. A compact greedy source set is:

| Frozen source tip | Additional paths after previously selected sources |
| --- | --- |
| 96acba4f1da547b523683eaa5ce346207c03b877 | 188 |
| 78d75e0185da638473109ad11005a5cb04eb5850 — H2743 managed readonly entry | 85 |
| 356793e197393387eea9558eeaec7bf23cde95af — R0266/H3937 pending source | 81 |
| 5cec58c6cc3214a131e05763df6f8d9599719cb3 — H3937 R0117 static seal | 34 |
| a3fdd31ca8631644cb6341b85db2ae0b29b7c1b4 — older episode raw index | 3 |
| 9e2076c97e9ceebd06eaf5ac701e13f711fc9049 — H3937 worker proof | 2 |
| b13925c22ad68508b3c283b0f148894a2209e9d3 — H3937 legacy retirement | 2 |
| beaa9a19e20e8b886ce7ab426e4bf26c18c455c8 — H2743 predicate source documentation | 1 |
| 38b28769b4c905c2041f11700bbad2808a6d0256 — watchdog custody test | 1 |
| bc4225176ef94e586097707d6a12ce0783cf217a — one-day recovery contract | 1 |

This is 398 distinct currently missing paths and avoids arbitrarily merging every obsolete branch. Each of these ten sources owns at least one missing path that no other maximal candidate supplies; therefore ten is minimal for complete missing-path coverage within these explicitly scoped ref families. `integration-plan.json` retains those exclusive-path witnesses plus the exact per-tip and union commit/path sets relative to master: 605 unique commits and 10,608 changed paths including the three primary tips. This does not assert every old modified shared blob is valuable or semantically approved. Additional historical conflicting versions remain in their original commits; preserve source refs rather than overwriting newer master behavior with old branch whole-file copies. The task does not require exercising each old live runner.

## Conflict and compatibility requirements

- Research overlaps 26 master-changed paths, including CMake, `bridge.cpp`, `game_adapter.cpp`, frontend route/owner context, mailbox, Python native driver/MCP/session/runtime, recorder/capture entry and bus. Ie overlaps 10 master-changed paths. Video overlaps AGENTS plus daily/weekly/meeting progress documents; preserve both chronology and latest master facts.
- Preserve master ck3_12002/ck3_12003 adapters/dispatcher and current version identities. New original in-game UI reader and combat observers hardcode CK3 1.19.0.6 RVAs, GUI hash and EXE hash. Retain their exact-build guards and historical labels; do not advertise them as 1.20-supported abilities.
- H2743 predicate and H3937 original source are likewise exact 1.19 research. Macro defaults must remain OFF; their old pair pins and run receipts cannot certify the new merged binary or updated game.
- Recount 11906 capability initializer after composing source changes: main base count is 102, research increments to 104 for two UI capabilities, ie adds one de-jure exit capability but still declares base 102. A combined initializer is expected to require 105; compiler verification should determine the exact count.
- Research enlarges native/Python frame capacity and trace ring. Preserve paired capacities and reject cap+1 rather than reverting one transport side during shared-file resolution.
- Research identifier table append admits stable existing-prefix extension. Retain guards; do not replace with unconditional append admission.
- The old AGENTS freeze-master and absolute offline policies have been superseded within this task by explicit user authorization to upgrade Steam CK3 and merge all valuable results. Record this as a dated task exception while retaining default offline policy and historical instructions as history; do not let an old unconditional clause obstruct authorized work or permanently remove other user safeguards.
- Preserve .gitattributes additions binding exact LF/binary evidence bytes. Sparse trees must not be used to infer deletions. The video branch adds 10,006 tracked paths, mostly preserved research attempts; no raw asset cleanup is appropriate.
- R0148/R0149 refer to Steam build 23530548 / CK3 1.19.0.6. Keep their finite claims, remaining nonzero-screen/nonempty-growth gaps, historical RED and unresolved statuses. Current a09 is pending full human 1×/listening signoff and remote byte readback remains unverified.

## Directed validation after integration

Use the explicitly verified main worktree venv for Python; sparse secondary trees do not have their own venv. No new video run is needed just to integrate sources, so no TTS, render or invented human signoff should be run.

1. Existing Python tests changed by research: native bridge runtime, screen process provider, in-game UI navigation, trace publish failure preservation, native frame capacity. H2743 predicate consumer and H3937 single-query tests cover source/frame/pair admission.
2. Focused capture tests: integration capture operator entry, JD11 pair, recorder Job, screen bus lease/process-create gates; these check that current master 1.20 process and CAS fixes survive the historical-source integration.
3. Compile the merged native DLL/injector with current version adapters. New focused CTest targets include combat scoped transition chain, scoped character variable monitor, combat phase managed/ring, protocol, in-game UI navigation and main-thread mailbox. H2743 standalone fake-memory/route targets must be explicitly enabled via `XAR_CK3_BUILD_H2743_STOCK_PREDICATE_FIXTURE_V1=ON`; production reader macro remains OFF for default build.
4. Run pertinent current CK3 1.20.0.3 adapter/identity/frontend registration tests to prevent regression in the mainline's newly qualified backend. Static integration cannot establish native live support on the newly upgraded game.
5. Historical verifier CLI scripts require specific frozen run inputs, fresh output paths and sometimes fixture stdout. Reuse/rehash history read-only if needed; do not rerun them into old attempts or reinterpret saved 1.19 material as newer native truth.
6. Compare video/config/evidence source bytes against frozen branch tree and inventory. Verify critical a09 SHA/media facts read-only if desired; source integration alone does not create a new final MP4, cloud delivery or human approval.

Integration can proceed sequentially from current master: H2743 managed readonly package 78d75e0, cash package 356793e, H3937 seal 5cec58c, worker proof 9e2076c, legacy retirement b13925c, predicate source doc beaa9a1, watchdog test 38b2876, recovery doc bc42251, historical preview 96acba4, historical raw index a3fdd31, current ie ff1b17d, current research c4e8718, then current video/handover 04bf1fe. The late primary tips restore the latest historical source projections and narrations after their precursor archive closures. Resolve conflicts by function/section, rather than using whole-file ours/theirs for shared native/runtime code; retain current master 1.20 implementation throughout. `integration-plan.json` records this exact suggested order.
