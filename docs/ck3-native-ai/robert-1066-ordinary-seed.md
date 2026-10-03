# Robert 1066 ordinary seed: exact-build input ledger

Status (2026-09-23): static-ready only for the Robert-specific target binding. No Robert `ordinary_campaign_succession` / `xar_off` paired checkpoint or production date has been observed. The existing Murchad seed and PRV008 preview retain their own evidence and bytes.

Frozen CK3 1.19.0.6-steam23530548 EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`. Stock `game/common/bookmarks/bookmarks/00_bookmarks.txt` SHA-256 `820C8F3F5A99CF1141A21A34F0661A7300E5D12938BB3EA7EA07A84A0D3BEB14`; `game/gui/frontend_bookmarks.gui` SHA-256 `C853B48F42A5A3B84208B2FC570C02F5FCB5DA217133553C6A5B70B7F8F0F267`.

The stock `bm_1066_rags_to_riches` bookmark starts on `1066.9.15` (`date_raw=53144328`). Its Robert the Fox entry is `bookmark_rags_to_riches_duke_robert`, `d_apulia`, `feudal_government` (stock lines 1663–1674). `history_id=1128` identifies the source definition; it is never a dynamic UI index or an asserted live player ID. The former Murchad target uses `bookmark_rags_to_riches_petty_king_murchad`, `d_munster`, also feudal (lines 1491–1500).

The native private bookmark producer already supports a build-time `XAR_CK3_FEUDAL_1066_TARGET_ROBERT_V1=ON` target. Its source-key scan finds exactly one current element, reads final native government, and passes that element to the original selected-character setter; the typed StartGame action uses the stock Bookmarks button. For Robert, the controlled runner must explicitly request Robert's key and match the producer's current `candidate_keys[supported_1066_candidate_index]` before **any** typed selection. The independent next model must still identify the same key and selected index. The first stable paused map must match the bookmark date and player; a later application-main pump must precede the public same-revision campaign-root query. Root must confirm the same player, feudal government and `xar_off` rule; only then may the initial save/driver pair be materialized. There is no gameplay date advance in this seed stage.

```mermaid
flowchart LR
  A[Official MCP NewGame] --> B[Bookmarks]
  B --> C[Private exact-build model: 1066 bookmark, Robert key, feudal]
  C --> D[Typed original selected-character setter]
  D --> E[Independent selected model]
  E --> F[Typed stock StartGame once]
  F --> G[Stable paused map and later main pump]
  G --> H[Public campaign-root: same player/date, feudal, xar_off]
  H --> I[Ordinary no-pact save + driver checkpoint]
  I -. Formal auto-run and cold restore still require live evidence .-> J[Robert campaign]
```

The stage uses a fresh prepared `ordinary_campaign_succession` / `xar_off` state under a non-C drive. A Murchad save cannot be renamed, rebound or edited into a Robert start. The run must pin source commit, Robert-target DLL full SHA, injector SHA, frozen EXE SHA, stock bookmark/GUI SHA, prepared environment/profile digest, mod load order (`mod/xar_autoplayer.mod` only), selected key and model frame, typed action receipts, public root, checkpoint save/driver SHA, and allocated run ID. An unconfirmed selection or StartGame stops as RED without retry.

Reusable Murchad evidence covers the generic NewGame → Bookmarks route, exact-build model/typed StartGame mechanism, public root contract and ordinary seed binding. It does not establish Robert's selected key, initial actor, paired checkpoint, first-day lifestyle choice, campaign outcomes or any Robert time-span credit. Historical fixed Robert visual/OCR openings remain visual regression evidence, not this production seed.

## 2026-10-02: current Robert archive and offline continuation checklist

The seed-binding section above is a dated 2026-09-23 record. The current
iteration uses **Robert as its sole test entry**. While the user plays manually,
background work is limited to retained-file analysis, external staging,
implementation/build work already authorized by root, documentation and
reviewable argv. No CK3/Steam/SDK/pipe operation or real profile prepare,
rebind, preflight or launch is executed until the user explicitly releases
CK3 for agent control. Murchad and other-government experiments are paused;
their outcomes cannot supply Robert evidence.

The latest verified retained Robert source is **full4031/saveh4029**,
actor29829, raw53220000, campaign `native-29829-2bc2d599f7f9`, ordinary
`xar_off`. CK3 **1.20.0.3 / Steam build25652598**, EXE SHA-256
`94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`,
already restored this pair in actual GAME PID74408 then new PID115688.
The normal opaque save is79,280,616 bytes, SHA-256
`e4d4eaad6f253bde013392c6973461e61adaa3c06d92f234ec72f2594ed87529`;
complete cold driver SHA-256 is
`d93b10ccfd4f0010d261fd4245bd86ffea2bb59ad9bc8a36fe656d1f8384713d`.
The complete archived tail is preserved; h4029 is the save anchor, not the
full-history count. The original full4028/saveh4025 with legal omitted/null
goal remains untouched as historical input.

Robert remains **3153/36524 durable days**. The restored goal is
`dynasty_continuity`, origin/current29829, progress
`reconciled_successions=0`, `last_succession=null`: this is the actual typed
goal established by the normal consumer in the restored archive, not manually
filled or reconstructed from the 3153-day count. The day counter and goal
progress are distinct; neither establishes a completed century/inheritance
loop. Same-campaign goal and
government cold evidence is described in
[ordinary campaign continuity](ordinary-campaign-goal-continuity.md).
The archived state does not describe the user's current manual-play frame.
All future identity, legality, cost, candidate, result and material observations
must bind a fresh paused snapshot and its actual revision.
The query configurations below are `static-ready` file plans, not verified
live readiness or future capability credit.

| Priority | Actual archived input at raw53220000 | Ready next input and limitation |
|---|---|---|
| P0 Guy pending result | `player-child-default-formal-v1.json`:38988/candidate37909/recipient34332, accepted input, receipt pending, no independent material result. Only3 days separate its input from the saved date; that is not a timeout verdict. | Existing normal `query_child_default_result_private(driver, pending=unchanged_pending, cold=actual_PID_change)`. Consume the pending result; do not resend a proposal. |
| P0 first-heir continuity | `first-heir-marriage-formal-v1.json` retains historical verified betrothal38822↔38718. Latest root expects38822 for five titles and Guy38988 for title2173: split-successor risk. | Fresh current-first-heir bilateral relation, outcome/lineage and existing resolved-ledger cold read, then the existing alliance query. Historical betrothal does not establish today's relation or alliance. |
| P1 Council comparison | Six core seats have holders. Robert's Steward is32716 on `task_collect_taxes`; there is no proven core vacancy. Auxiliary vacancy coverage is incomplete. | Existing fresh root, Steward candidates/final gates and Develop value queries. Candidate improvement and task benefit are absent from this archive; never import Murchad holder39761 or its outcome. |
| P1 economic inputs | Latest h4031 root reports monthly income raw373295/Q100000=3.73295. Full driver history and the three sidecars publish no construction world/pending/material/province-income/candidate record. | Existing `query_construction_private(..., expected_revision=fresh_revision, material_receipt=True)` and production probe. Missing archived material does not prove absence of current construction. |
| P1 Sway/vassal inputs | Latest h4031 root has10 direct landed vassals and `player_targeting_faction_count=1`. Scheme/Sway and faction-specialized archived records are0; this does not prove no current scheme or an empty slot. Vassal opinions and faction member/leader information are missing. | Fresh paused snapshot/root and actual visible pending context; actual-target Sway probe, then conditional independent outcome opinion; if fresh faction count>0, same-frame native gift-candidate query. No political target is selected from archived IDs. |

The existing Sway sequence uses `ck3_query_active_scheme_sway_target_private_v1`
with an actual current native/root character and fresh revision, followed only
when available by `ck3_query_active_scheme_sway_outcome_opinion_private_v1`
for that same target. `ck3_query_faction_gift_candidate_private_v1` is a narrow
native gift-candidate read, not proof of a complete member/leader/opinion
roster. Its input uses a same-frame root only when the fresh targeting-faction
count is positive. Any current active/applied/pending instance is retained;
fullID/generation and existing per-instance readers bind only actual new
responses. The source package lists existing readonly permit flags; no
startup, new Sway, gift action or final packet change is made here.

The third ledger, `player-prisoner-ransom-formal-v1.json`, is historical
resolved/applied with a verified postcondition. Its action and gain are not
replayed or credited again. Robert's archived cold frame has spouse34730;
the generic goal focus `marriage` is not an instruction to marry the ruler
again. Laws, construction and schemes likewise use fresh current inputs and
normal existing consumers, never replayed historical commands.

Seven source byte streams—full driver, latest save, episode-seed metadata and
opaque seed, and all three ledgers—are already copied unchanged into external
review staging. Original files and real state/profile are unchanged. The
planned destination is a fresh independent Robert state. Official
`rebind-ordinary-seed-v1` retains/asserts the existing pipe
`\\.\pipe\xar-g2-robert-1066-seed-66f926d`; no manual pipe, goal, history or
episode rewrite is required. Official prepare/verify, byte stage, ordinary
rebind and receipt-derived no-launch preflight are reviewable recipes only.
Actual rebound driver SHA is obtained from the rebind receipt, never predicted.
All future managed/auto-run startup argv use `--start-minimized`; MCP remains
a pure client and receives no startup flag. Normal cold consumers own saved
prefix and physical restore lineage; the full source archive remains retained.

Evidence root is `artifacts/g2-maintainer-2026-10-02/resume-12003/`:

- Actual .3 paired proof: `m7-robert/paused-intent-19a0e945-v4/paired-proof-20261002-01/M7-PAUSED-COLD-PROOF.json`.
- Once-read latest inventory: `m7-robert/LATEST-ROBERT-PAIR-INVENTORY-20261002.json`. It read694 project driver headers, matched347 of the same episode, parsed all headers, and found no later saved pair than raw53220000/h4029 within its recorded roots.
- Seven-file staging/receipt: `m7-robert/robert-mainline-file-review-4031-h4029-01/`; source inventory SHA-256 `784212213f1015f41c5e0185cf61aae212aca42b332a6bdca739a94f28748f31`.
- Total offline backlog and pending runtime parameters: `m7-robert/ROBERT-OFFLINE-BACKLOG-20261002.md`, `m7-robert/ROBERT-V17-PENDING-ADOPT-PARAMETERS.json`.
- Family fields and exact future entries: `m5-family/ROBERT-4031-FAMILY-OFFLINE-BACKLOG-20261002.json`, SHA-256 `46376a59d0f1b29d035062bb39282b39b335a793575432e0d722ecd190d3d8f2`.
- Council fields: `m4-council/robert-offline-opportunities/REPORT.json`, SHA-256 `7e78d90f0caad49e0ba00984d58396b1e3713b4667d3149dee308bfd30bc8bc9`; adjacent Steward/Develop readonly call files require fresh revisions.
- Construction fields/production read entry: `m4-construction/robert-archive-20261002/REPORT.json`.
- Sway/vassal actual fields: `m4-sway/robert-latest-opaque-scheme/REPORT-FIELDS.json`, SHA-256 `14613bd4b46882755e40a46dc94c0bea82329156825208f8075c8d5efdf4e8bb`; adjacent `ROOT-CONTEXT-CALLS.json` and `FRESH-QUERY-DEPENDENCIES.json` are prepared conditional reads, with no archived target/instance bound for execution.

New immutable Python source is
`2929bf666cf6d8ea5dddd5f398a76ab157a55417`. Root has adopted actual v17
native metadata: 959 compiled-input bindings, DLL7,924,224 bytes/SHA-256
`ac5f188d0a63e0633eb20ac70adc29a6f15ed2d7df729698429e606e9765e23c`,
63 ON/6 OFF flags, one strict DLL build GREEN. Actual compiler tree is
`e3b52f09`; its native inputs are equivalent to immutable source2929bf66
by the root's one recorded empty diff. No recompilation is falsely assigned
to source2929bf66. The file-only official packet is at
`m7-robert/robert-mainline-v17-2929bf66-review-01/ROOT-PACKET.json`, binding
the actual `runtime-freeze-2929bf66-v17.json` and native manifest. No real
state/profile consumer or game process has been executed from that packet.
The separately observed
[official CI run](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/36976539734)
for `e3b52f09dc3f51fbeedee21a0e2c05e7992feae2` completed **SUCCESS**;
its retained receipt is `official-ci-e3b52f09/terminal-status.json`. That CI
is for its exact earlier commit and does not establish v17 runtime or live
compatibility. Existing .3 paused/cold evidence is reused, not reclassified
as v17 live.

Offline work cannot confirm fresh family outcomes, today's Council/Develop
benefit, construction completion/net income, new saved days, natural matched
succession, or broad M7 qualification. Existing episode hold findings describe
legacy implementation, not a new release protocol or permanent user ban.
No new gameplay/material/day/qualification credit is assigned by this
checklist; M7 remains `in_progress`.

## Resumed v17 Robert cold startup diagnostic, 2026-10-02

The user released CK3 and confirmed Steam offline at 17:27 CST. This ends
the manual-play-only interval described above. Root resumed the same ordinary
Robert entry using the official packet and minimized GAME PID81664; no
historical marriage, ransom, law, construction or scheme action was replayed.
The session startup witness retains the actual e4d4eaad checkpoint at h4029.
The game log reached InGame/history completion at 09:37:55 UTC, but the first
direct helper exhausted its 600-second readiness wait and closed normally RED.

The root's existing-driver diagnostics at 09:51:23 UTC establish a connected
hello for PID81664, exact .3 EXE SHA/build match and adapter `ready`, with
`semantic_state_available=false`, no heartbeat, zero rejected state snapshots,
zero publish diagnostics and no transport error. This attempt therefore does
not establish a fresh Robert goal, government, map or saved-day frame. The
existing cold startup already supplies `-loadsave=xar_checkpoint`; no missing
restore queue or preliminary SDK snapshot call was found.

The bounded source comparison found identical ASTs for the v16/v17 minimized
window readers, minimizer, initial process ShowWindow settings and continuous
minimized enforcement. The prior actual minimized Murchad v16 context,
checkpoint and two-day loop are a counterexample to a general claim that
minimization suppresses all state publication; none of its gameplay credit is
imported into Robert. The existing foreground helper restores, raises and
acquires focus, while the managed supervisor reapplies minimization every
0.5 seconds. Neither is an existing no-focus recovery command. The remaining
concrete dependency is the native owner's current hello-to-heartbeat/state
publisher analysis; this note does not assign a root cause or add an action.

Retained inputs are `m7-robert/actual-v17-mainline-01/06-managed-first-session/stdout.log`,
`m7-robert/actual-v17-paused-intent-01/first-paused-01/result.json` and
`m7-robert/actual-v17-multidomain-readonly-01/diagnostics-01/result.json` under
the same evidence root. The bounded comparison is
`m7-robert/actual-v17-paused-intent-01/BOOT-CONTROL-COMPARISON-01.json`, SHA-256
`37cc5547e45a7324c15f7d84bee8ab00e9f18a251d6b20efad09fef66896a80a`.
Robert's historical3153/36524 days and archived typed-goal progress0 remain
separate unchanged counts; this failed startup adds0 days,0 actions and0 M7
qualification credit.

## Actual v16 fallback frame and government recovery, 2026-10-02

Root prepared a separate v16 state from the same retained full4031/saveh4029
pair and the adopted `d4f377d9` runtime. Minimized GAME PID109676 reached a
living paused Robert map at raw53220000. The accepted frame restores actor29829,
episode `native-29829-2bc2d599f7f9`, ordinary succession/xar_off and the original
`dynasty_continuity` goal with progress0. Identity adoption is complete; the
observed frame has no active event or pending character interaction. A bounded
read of the three current ledger files confirms their original retained SHA-256
values; no historical action was replayed.

The retained first direct attempt reached this frame, then returned RED at
`government-runtime-query` after3.931 seconds with
`government runtime adapter command_result unavailable`. The transport folds
missing, mismatched or unsuccessful command results into that error; it does
not retain the initial raw cause. Both the previously successful v4 and this
v16 native metadata have the government query flag ON, and the first direct
driver permit was enabled. The evidence does not establish a missing flag,
timeout or ABI cause.

Root subsequently queried the existing government interface through its
registered MCP wrapper on the same PID. The actual002 packet and native wire
establish `available`, `feudal_government`, `core_landed`, `core_supported`,
44 effective features, `requirements_met=true`, `same_frame_ready=true` and
`core_adapter_ready=true`. Player and date remain29829/raw53220000; queried and
post native snapshot IDs are both `native:3`. This is actual government
observation, not an inferred family from source or another seed. The first
RED remains preserved, and another government query is unnecessary.

The same managed process can now supply the normal formal plan. The external
baseline-only recipe offers normal checkpoint plus a new minimized GAME PID
goal/save/ledger comparison; it deliberately skips government and next-plan
comparison, so those results cannot be credited from that narrower scope.
At this recording, new checkpoint, new-PID baseline cold and normal next-plan
results are still pending. Historical3153/36524 days, goal progress0 and M7
`in_progress` remain unchanged; this observation adds0 days and0 actions.

The first failure and accepted047/048/049 files remain under
`m7-robert/robert-mainline-v16-fallback-review-01/paused-intent-01/first-paused-01/`.
The same-PID002 packet and `native-wire.jsonl` are under
`m7-robert/actual-v16-multidomain-01/capture-01/`.
The bounded summary and actual three-ledger pins are
`m7-robert/robert-mainline-v16-fallback-review-01/paused-intent-02/ACTUAL-FIRST-FRAME-AND-GOVERNMENT-01.json`,
SHA-256 `3ce2e5e148803d4df0cc7946d4b282f5445c622cf78afabfc71909d8e1bf788b`.

## Current saved continuation and cold plan, 2026-10-02

The actual normal nonwar turn now executed `life-advance` for one natural day,
raw53220000→53220024, and returned paused with a material checkpoint. At that
turn's close, save/full history are h4052/full4052, save79,579,117 bytes/SHA-256
`1610b9b4c00d258566fb51744b604240362e50ea38b31c9171dae02fbfd7c167`;
the retained driver is48,960,585 bytes/SHA-256
`767cb6e202148b021c789a0e55e21cb0b9b79c68ed722db83e04382e4080cdf4`.
This adds1 saved Robert day to the historical3153, giving3154/36524. The last
observed typed-goal progress remains the separate pre-advance value0;
post-day goal observation is pending at this recording. This is one actual
turn and saved day, not a century loop or natural-succession completion.

Python source is now `c0f53e9bdce2990f4ad23fdf05126e7af3051c47`, officially
attached to the existing native v16 process. Native DLL/source remain
`83a811d717b836f589f76c91fc03f205235aac70bb72c50842258d701468a6ff` /
`d4f377d97b7a4f97ac85151610adbc4d4df818f8`; the original prepared environment
digest `aa263acb4c2cfdbfb11c77c02a109db59dc2cd4b4c23deaf9c8c816139016612`
is preserved. New Python provenance does not imply new native compilation.
The closed turn is `robert-mainline-date-hold-fix-01/actual-normal-clock-execution-01/result.json`.

The M3 paused assessment at the earlier raw53220000 frame confirms main
heir38822, five county-or-higher titles→38822 and county2173→Guy38988,
`split_successors`, with no natural succession. Its source boundary matters:
the law snapshot normalizer sorts successor arrays numerically; its first
ID30253 is not the ordered primary heir. Crown Authority1 legality/cost does
not prove partition disappeared. The retained assessment is
`m3-robert/current-succession-01/ASSESSMENT.json`, SHA-256
`7d5579162e5d6621baee0a13f9c604ac920e7222f4270d4fd492bf2603e0fc51`.
Later actor/heir/material conclusions must use the post-day observations.

The next cold continuation uses the current state and final normal checkpoint,
not a replay of full4031/save4029 or a hard pin to this intermediate h4052.
Root closes the current consumers, stops normally, then the external renderer
retains the latest complete pair and all five family/Council/Sway ledgers.
The old v16 official managed launcher verifies the valid old environment and
reads the current v2 save/history anchor with `--cold-start-checkpoint` and
`--start-minimized`. New Python then uses the official explicit ordinary
environment binder to attach. No prepare, original-pair stage, manual state
rewrite or environment rebind is needed for this unchanged state/profile.

Before advancing the new GAME PID, root reattaches the existing Sway instance
full134217986/gen8/target34333 through its completion query and three recorder
reads with cursor0. The Sway owner's `COLD-REATTACH-CALLS.json` SHA-256 is
`dc04c7bfb7188270234a842c41cc110d45b76b52d9c53709ef14ac977f9ea5b5`, under
`m4-sway/robert-v16-rings-attached-01/`. This does not resend Sway Start.
`m7-robert/current-v16-native-c0f53e9b-cold-01/ROOT-CURRENT-COLD-RECIPE.json`
is the file-only argv recipe; its latest-state bind and actual new-PID cold
results are still pending. M7 remains `in_progress`.

## Actual current-checkpoint cold and consumed intent, 2026-10-02

Root subsequently retained the final current pair at full4054/saveh4053,
raw53220024, then normally stopped GAME109676 and cold-started minimized
GAME101084. The qualified direct baseline returned GREEN at11:46:21 UTC:
Robert29829, the original episode, saved `dynasty_continuity` goal and all five
family/Council/Sway ledger hashes match the actual current source. Goal progress
is still `reconciled_successions=0`, `last_succession=null`. The physical save is
79,579,117 bytes/SHA-256
`4ea3cfae9c15a9972a6af30f4a2af8ad2736d04c45f91986db2fd1212975bb03`.
The existing cold consumer retains the saved history prefix and records its
physical restore lineage at h4054. The archived pre-cold expectation remains
available as source evidence; the actual post-cold driver has
`succession_expectation=null`, so this result does not claim an active restored
expectation. No goal, history or ledger was manually reconstructed.

The subsequent nine-call batch closed GREEN on the same GAME101084. Before any
new time advance, its first four existing Sway reads reattached the same
full134217986/gen8/target34333 instance and completion recorders; Start was not
resent. Campaign root, law, first-heir relationship, diagnostics and actual
government observation then closed. Native DLL/source remain the adopted v16
`83a811d7…68a6ff` / `d4f377d9`; Python remains the independently pinned
`c0f53e9b` source attached through the unchanged old environment.

The first following formal turn actually selected and executed `life-advance`
for one day. Its `result.plan.campaign_goal_plan_used` uses this same
`dynasty_continuity` campaign/current29829, progress0, marriage focus and the
family100/partition60 priorities. Its
`campaign_government_context_used` reports actual `feudal_government`,
`core_landed`, 44 effective features, `core_adapter_ready=true` and
`ordinary_goal_context_ready=true`. This proves the saved intent and actual
government context reached the normal planner after the new-PID cold restore.
Additional durable-day credit awaits the final saved continuation checkpoint;
at this recording3154/36524 remains the saved total and M7 remains `in_progress`.

The baseline is
`m7-robert/current-v16-native-c0f53e9b-cold-01/latest-final-checkpoint-bound/actual-cold-goal-01/result.json`;
the nine-call receipt is `m7-robert/actual-cold-material-101084-01/result.json`.
The consumed plan is
`m7-robert/actual-cold-following-family-sway-01/turn-001/result.json`.
The compact file-only summaries are
`m7-robert/CURRENT-COLD-CONTINUITY-101084-01.json` and
`m7-robert/COLD-FOLLOWING-CONSUMED-INTENT-101084-01.json`. The first extractor's
top-level plan lookup returned null; the separate corrected summary reads the
actual nested `result.plan`, and the original extraction is retained.

The next native v18 candidate uses public source
`1a0a3ca0027face9e10714ec70bf3ca4eafc8469` and the latest normal current pair,
including all five ledgers and the then-current expectation. It requires its
own official profile and environment binding after native metadata adoption.
It does not reuse the old D4 environment as a v18 compile identity or stage the
old full4031/save4029 pair. Candidate preparation is file-only; no v18 paused,
cold or gameplay credit is inferred from this working v16 continuation.

The following batch is now closed with three executed `life-advance` turns,
zero natural modals and three saved natural days, raw53220024→53220096. Its
normal checkpoint is h4065/full4065,80,076,282 bytes/SHA-256
`8f3517957d7697a2cbf780f3caedae3ae951a12a52a414378e5738e8ceb186aa`;
the full retained driver is49,131,360 bytes/SHA-256
`1db0dd4a2eefa90f542cdc7cd5bb84bab493d63daff89ff7dcbd925b9ac1f187`.
The final frame is paused. Together with the pre-cold saved day, this stage
adds4 durable days to historical3153, giving3157/36524. The existing Sway
applied ledger is consumed by the first following normal turn and remains
`already_applied` in later turns; Start is not replayed. The actual close is
`m7-robert/actual-cold-following-family-sway-01/result.json`, SHA-256
`f442894e16081f63bcd742d70630528e6dad2590b961c265cf2660e4799a3570`.
This is a same-campaign saved-goal cold/normal-continuation loop; it does not
complete M7's broader identity/government matrix or a natural succession.
The v18 source1a0a3ca0 native build has an actual C1061 compiler RED and awaits
the native owner's minimal fix and adopted final metadata. Its successful CI
does not establish a usable DLL. Candidate rendering therefore accepts the
root's final source/freeze and latest current pair rather than pinning either
this intermediate h4065 or the failed build identity as the future entry.

## Latest saved Robert continuation and v19 candidate, 2026-10-02

The existing finite normal continuation has now closed with15 actual saved
days, raw53220096→53220456, and a paused final frame. Its three turns requested
1/7/7 days and actually observed1/5/9; credit follows the observed15-day date
delta. Combined with the preceding4 saved days, this iteration adds19 days to
historical3153, giving3172/36524. The same Robert29829/original episode remains
the sole entry; this does not complete M7 or add another identity/government.

The closed current checkpoint is h4075/full4075,83,192,479 bytes/SHA-256
`dd4d3f772147778e7308a85f0e09336b491f00ad4f6e067e1d11564dfb5d23ec`;
the full driver is49,277,053 bytes/SHA-256
`49b547a68df99c2fe8e4c4aecd20d1bf6605a12a68aba908791cd1882f454b72`.
The actual close is `m7-robert/finite-normal-7day-actual-01/result.json`.
The capture owner's existing
`m7-robert/normal-time-value-01/FINITE-PRODUCTION-LIVE-PROOF.json` and
`REPORT-FIELDS-LIVE-INCREMENT.json` supply the verified counts/pins and capture
cost boundaries; no duplicate driver/save/ledger inventory or static test is
required for this note. Requested30-day continuation and explicit stop reasons
remain unobserved. Its measured remaining cost is planning/enrichment; the
capture result is not a controlled wall-time speedup comparison.

The next independent candidate is native v19/public source
`716acfecc6c487e2b48942c6a6030c8b7012e5d5`; its build/adoption is pending at this
recording. The unchanged CURRENT renderer accepts the final adopted freeze
plus explicit v19 target state/output. It retains the latest stopped complete
pair, current typed goal/expectation, five ledgers and immutable seed through
official prepare/verify, opaque staging, ordinary rebind and receipt-derived
preflight. It does not stage the historical full4031/save4029 pair. Every
rendered game startup is minimized. The exact parameter recipe is
`m7-robert/CURRENT-CANDIDATE-V19-PARAMETERS-01.json`; it has not copied live
state or executed any profile/game/client operation. Actual v19 new-PID
paused goal/five-ledger/restore proof is still required before v19 readiness
or further gameplay credit can be reported.

## Current native v19 / Python412 normal continuation, 2026-10-02

The canonical topic retained its published3172-day content and exact prior
SHA-256 before this append; no older topic was substituted. Root's new actual
closed normal window uses native source `716acfecc6c487e2b48942c6a6030c8b7012e5d5`,
Python `41291bf2315f11b6748affce318e1e456a6f8918`, the new officially prepared
v19 environment and owned GAME70968. One actual `life-advance` turn added7
saved days, raw53220456→53220624, and ended paused with no natural modal.
Robert is now3179/36524, this iteration26 new durable days. The current goal
still has0 reconciled successions; no natural succession or M7 matrix
completion is credited.

The current pair is h4081/full4081: save84,495,805 bytes/SHA-256
`ce9c7b4aa8ac70664920696fa9629f58e738b28aa7e8227a7c8ded66bddfec60`,
driver49,329,974 bytes/SHA-256
`91c383a0a147895464c5b7c3fe61415d68cb09e5ed9c4e66b27433d49f7384e1`.
The actual close is `m7-robert/planning-reuse-412-actual-01/result.json`.
Its original Sway action remains `already_applied`; the actual target is34333,
full134217986/gen8, and Start is not replayed. Native source, Python source and
prepared environment are separate recorded identities; this is not an old D4
environment relabeled as v19.

The next file-only recipe,
`m7-robert/NORMAL-30DAY-MCP412-ROOT-RECIPE-01.json`, reuses the current MCP412
entry and existing finite normal runner with target30 actual advance days and
max16 turns. It permits the existing family/first-heir, Council, government and
Sway34333 consumers, without enabling construction. The existing
`--private-activity-feast-queries` is already present in MCP412, mapped by the
factory to `allow_private_activity_feast_lifecycle_observation`; the normal
paused planner uses `reconcile_feast_lifecycle_private_v1`. The same finite
runner already delegates natural events to `consume_natural_event_service`.
Feast continuation therefore needs no new flag or policy rewrite and does not
resend a start action. Actual modal, lifecycle, turn and checkpoint results
must be consumed after the root-owned run closes; prepared30-day argv adds no
day credit and does not promise an exact30-day final delta. M7 remains
`in_progress`.

## Closed normal30 window and remaining Feast lifecycle, 2026-10-02

Root's requested30-day window has closed GREEN with39 actual saved days,
raw53220624→53221560. Five executed `life-advance` turns observed1/9/9/9/11
days; one natural modal advanced its event instance and preserved the actor
and date. The independent M2 owner owns that event's choice/material analysis.
Robert remains alive29829 in the original episode, paused, with the saved
`dynasty_continuity` goal,0 reconciled successions and `last_succession=null`.
The saved total is3218/36524, this iteration65 new days. The requested30 is
not substituted for the observed39, and neither implies M7 completion.

The full saved pair is h4098/full4098: checkpoint85,621,047 bytes/SHA-256
`7708b4bd2d0ed05040185d15e2f88ecc29706f629d7a5e1d8e53c631ca56ba40`,
driver49,556,602 bytes/SHA-256
`46b7fed0e0272bab151e16178dfb8337d0cd643271e79ba2b2302f5d46998675`.
The actual result is `m7-robert/normal-30day-412-actual-01/result.json`.
Root's once-produced stage summary is
`m7-robert/normal-30day-412-stage-fields-01.json`,99,762 bytes/SHA-256
`8337636efb6921ea6052aed37dd17c764a2ae01a61a7df44b1365edcd9e5e819`.
The normal turns continue to use the current campaign goal and observed
feudal/core_landed government context. No current war/army/default-horizon
fields are exported by this stage summary, so it does not establish a
no-war branch or native default30 horizon.

Feast activity83886111 has five actual `lifecycle_observed` samples, all
`ongoing`, with native completed/invalidated/terminal false. The latest sample
is raw53221296/native37, before the final11-day advance; no terminal or latest
final-frame lifecycle result is inferred from the saved end date. The samples
retain `benefit_verified=false` and no attribution of counter changes to the
Feast. Event material and Feast terminal/value proof remain distinct.

`m7-robert/NORMAL-90DAY-MCP412-ROOT-RECIPE-01.json` prepares the next current
normal window, target90/max32, with the same production time policy and
existing family/Council/government/Sway34333 permissions. Only the finite
runner owns its existing natural-event consumer; no second default event
consumer, new Feast start or construction action is added. Existing Feast
lifecycle reconciliation continues until an actual native terminal result is
observed. This prepared window adds0 days or completion credit.

## Actual v23 current-checkpoint cold baseline, 2026-10-03

The existing qualified helper closed GREEN at 2026-10-02 18:53:34 UTC
(2026-10-03 02:53:34 Asia/Shanghai), with scope
`ordinary_paused_goal_checkpoint_baseline`. Root restored the latest saved
v22 pair into the independently prepared v23 profile. Actual GAME6280 differs
from the archived GAME119508; Robert29829 is alive, paused and map-ready at
raw53222640 in the original episode `native-29829-2bc2d599f7f9`.
The normal consumer retained the saved `dynasty_continuity` goal with
origin/current29829, `reconciled_successions=0` and `last_succession=null`.

The normal source prefix remains full4169/saveanchor4169. Its ordinary cold
restore adds h4170 with the actual previous/new PID lineage, yielding full4170;
this is not a new save or elapsed day. The saved checkpoint remains85,802,882
bytes/SHA-256
`6005a5c86b796cc0875fc2c1987da4f54d4167386bf0bd76be16393173965ced`.
The after-close driver pin reported by the qualified helper is50,193,329
bytes/SHA-256
`59ac7ed1f93104c08efe13273049d439d5d3d4b6081fded1ddefd688b08da0d5`.
All six carried production ledgers passed the helper's actual saved-pin
comparison: first-heir marriage, child default, prisoner ransom, Council,
Sway and `activity-feast-stage5-start-private-v1.json`. No appointment,
marriage proposal, Feast Start or Sway Start was replayed. The archived
succession expectation remains source evidence; the ordinary cold consumer
cleared the active expectation to null, which is distinct from the preserved
campaign goal.

Public runtime, native metadata and actual compiler source are all
`2c435dcb7ef0a0cfd775c3bfd26e7b37daea0d1d`. The adopted v23 DLL is8,043,520
bytes/SHA-256
`d47b7f11ee4041e9721e28baab5e3d9ac809d12da18e017887bb194cc7a252c9`.
Official ordinary rebind retained the save bytes and bound the new environment
`d1f020b6ba01b4718f6797746afb6f75e0bd979fc280f4acb4ecf7619e66011e`.
Root separately observed HWND9969350 for GAME6280 with `minimized=true`; that
window observation is Root's tool evidence, not a field exported by the
qualified baseline result.

The exact evidence is
`m7-robert/robert-mainline-v23-current-review-01/actual-candidate-cold-goal-01/result.json`,
with its `ROOT-PACKET.json` and `official-rebind-01.json`. Startup readiness
initially returned two transient unavailable observations before the map
became ready; the retained overall result is GREEN. This attempt deliberately
skipped the government query and next planner, executed no planned step and
added0 Robert days. It verifies this new-PID saved-goal/six-ledger cold baseline;
it does not establish a new government loop, resolve a pending domain outcome,
add a G2 qualification slot or complete M7. Subsequent live domain queries and
normal continuation remain separately owned by Root.

## Actual v24 current-checkpoint cold baseline, 2026-10-03

Root's actual v24 qualified helper closed GREEN at
`2026-10-02T20:03:47.809030+00:00`, with scope
`ordinary_paused_goal_checkpoint_baseline`. GAME38520 differs from the archived
GAME6280; Robert29829 remains alive,
paused and map-ready at raw53222952 in the original
episode `native-29829-2bc2d599f7f9`. The saved `dynasty_continuity` goal retains
origin/current29829, `reconciled_successions=0`
and `last_succession=null`.

The full source history is4192; the
normal cold consumer reports full4192/saveanchor4191.
The carried checkpoint is86,097,310 bytes/SHA-256
`2e1a27f33e020fd86628ccab4af23376b91591d364c3ffb1e7298b1b1e7d1ed7`. Official ordinary rebind retained the save bytes.
The actual after-close driver pin is50,325,456 bytes/SHA-256
`57f04dad3f5629ad6768ca140c47aee798764c46ed2b2e8068862f73c462304a`. All six production ledger pins passed the existing
qualified helper. Goal, opaque pending/applied records and full history were
not manually rewritten, and no appointment, marriage proposal, Feast Start or
Sway Start was replayed. The actual post-cold succession expectation is
`null`; source expectation evidence remains separate from the
persisted goal.

The runtime source is `6c87eb77568601499ab98a43f9cbea4c2ee870f6`, native metadata source is
`6c87eb77568601499ab98a43f9cbea4c2ee870f6`, and actual compiler source is
`6c87eb77568601499ab98a43f9cbea4c2ee870f6`. The v24 DLL is8,075,776
bytes/SHA-256 `77101b5388890088f013f1f06249e0066547f6ec41249484602a3eebbb5b9dec`. The official new environment is
`8a98da66b7bc798e6b30c7f7e2821e287775cb6353fba108edacf895a7651f0c`. Root independently observed
GAME38520/HWND6299886 as visible and minimized; that window observation is
Root's tool evidence, not a field emitted by this qualified helper.

Evidence is
`m7-robert/robert-mainline-v24-current-review-01/actual-candidate-cold-goal-01/result.json`,
its `ROOT-PACKET.json` and `official-rebind-01.json`; compact exact pins are in
`m7-robert/V24-CURRENT-COLD-REPORT-FIELDS-01.json`. This limited baseline skipped
government and the next planner, executed no planned step and added0 natural
days or qualification slots. Root's preceding durable total remains3276/36524,
this iteration123 days; G2 remains5/8 and the nonwar matrix1/4. M7 remains
`in_progress`. Current monthly-piety/Sway observations and further normal
continuation require their separate closed root-owned results.

## Actual v25 cold and saved normal continuation, 2026-10-03

The root-owned v25 qualified cold baseline closed GREEN with scope
`ordinary_paused_goal_checkpoint_baseline`. New GAME95636 differs from archived
GAME38520; Robert29829 remains alive, paused and map-ready
at raw53224008 in the original episode
`native-29829-2bc2d599f7f9`. The saved `dynasty_continuity` goal and all six
production ledger pins passed the actual helper. The dynamic source pair was
full4269/save4269; the normal cold
restore reports full4270/saveanchor4269.
No natural day, action replay, new identity or qualification slot is credited
to this baseline. Government and the next planner were intentionally skipped
by the baseline; subsequent normal-plan evidence is recorded separately.

Official v25 runtime, native metadata and actual compiler source are
`f9da88f9119223b150356ec110392c0f67073cc1`, with environment
`7678c6bd47000ff770e8d9b176d6675c4f69070c95866fb090461891488d899f`. The adopted DLL is8,117,760
bytes/SHA-256 `4119de2275a9d1adfbc951fe93a8d8e407519301f36c8818567ec04ac83b033e`. The subsequent normal window uses Python source
`a5882a567c0223884df0770494f60648677eab00` with the qualified native/environment
above; that Python source is not claimed as the DLL compiler source.

The requested8-day window closed `normal-time-target-reached` with
12 actual saved days, raw53224008→53224296.
Returned plans contain4 actual campaign-goal
contexts and4 actual government contexts.
The final frame is paused and retains the same Robert episode and typed goal;
reconciled successions remain0
and `last_succession=null`.
The new full saved pair is h4276/full4276:
checkpoint86,735,234 bytes/SHA-256 `90e6579a8772bc51321b855a57afe25abcc47b942023b98b0f0c214250a6ae6d`, driver
51,347,352 bytes/SHA-256 `8cea61400b332ec4b25955c94d4d771dc8f80f11168d147a7e0951bcaa8914ad`. Robert is now3332/36524,
this iteration179 saved days, with84 saved days in the current day03 stage.
Requested8 is not substituted for the observed12.

The closed combined9-call harness is GREEN at PID95636/raw53224008, with actual
query frame `native:3`/revision2. It publishes monthly total piety43750/Q100000
and the current chaplain task's monthly piety45000/Q100000 as distinct native
values. Spiritual fulfillment progress is available with current raw500000,
level index3 and progress-percent raw5833300/Q100000; its explicit
`is_monthly_change=false` prevents treating this progress gauge as monthly
growth. The original Feast83886111 publishes native completed=true,
invalidated=false, attending_count18 and target37265 in that list. Guest opinion
is82; `impressed_opinion` is independently observed present with value10 while
the two hosted-feast modifiers are absent. These readonly materials do not
alone attribute that modifier to this Feast or create a new reward credit.

The separate Holy Loan capability remains RED with exact
`loan_amount_expression_unavailable`. The failed amount expression returns
before decision/debt getters, so their defaults do not prove eligibility,
costs or absence of debt. Generic religion completion is not claimed.
Economic observation and war read-only permission do not imply a spending or
war action. Root's new Python performance path omits two redundant Chancellor
queries; domain owners retain the economic, task, Feast and performance
proofs. Existing global M2 and M5 Murchad completion is not withdrawn by this
separate failure. Global G2 remains5/8, nonwar1/4 and M7 `in_progress`, with no
new natural-succession credit from this same-Robert continuation.

Exact cold evidence is
`m7-robert/robert-mainline-v25-current-review-01/actual-candidate-cold-goal-01/result.json`
and its `ROOT-PACKET.json`. The actual normal close is
`m7-robert/v25-a588-normal8-with-economic-observation-01/result.json`; its
once-produced summary is `m7-robert/v25-a588-normal8-stage-fields-01.json`.
The nine-call compact input is
`actual-v25-religion-feast-sway-combined-01/REPORT-FIELDS.json`, SHA-256
`dd9f1b015d5207895b179fe52108d6beac9e66fc329b7aa0b0ec52d9c5872e5f`. Combined exact pins and actual plan contexts are in
`m7-robert/V25-CURRENT-COLD-REPORT-FIELDS-01.json`. The first external topic
formatter had a harness KeyError for the driver metadata key; it was corrected
from cached compact fields using `command_history_length`. No cold, normal or
live query was repeated for that documentation fix. This delivery did not
read current state or pending SDK directories, rewrite gameplay data or run
tests/Git.

## Actual v26 cold and nineteen saved normal days, 2026-10-03

The v26 actual root-owned qualified cold baseline is GREEN at new GAME15592,
replacing GAME95636. Robert29829 is alive and paused/map-ready at raw53225304,
with the original episode and saved `dynasty_continuity` goal. Full4294/
saveanchor4293, all six production ledger pins and ten opaque carried streams
are preserved through the official independent-profile path. The cold source
checkpoint is87,015,203 bytes/SHA-256 `e83cda5ffc51bf043d02ed45d0c7b912adc471d51780b21f5db5d8d07b3c409e`. This baseline
adds0 natural days or qualification slots; its government query and next
planner are intentionally skipped.

Public runtime, native metadata and actual compiler source are
`1bb3eee96e00216464e8269ec5153c60b22aca43`, with new environment
`b554570173119d39f56d8a3e0dfa2c05fd21c4d4425ab771a18b33905c346adf`. The actual DLL is
8,117,248 bytes/SHA-256 `5bfd1cb73e048c91187cd446b4b29c4f17c6b084cf22b6d07a83d7a55636d904`. The following same-PID normal
window uses that qualified source/native/environment; it is not a new seed
or replay of a pending submission.

The requested16-day window closed `normal-time-target-reached` with
19 actual saved days across4
formal turns and0 natural modals,
raw53225304→53225760, ending paused.
Its actual returned plans contain4 saved campaign-goal contexts
and4 observed government contexts, followed by successful
normal execution. Goal origin/current remain29829, with
`reconciled_successions=0` and
`last_succession=null`.
The saved pair is h4299/full4299:
checkpoint87,142,531 bytes/SHA-256 `841f15b9eadf5f90b2a804a043396c7d711ea3da5f58625f2b5b1a3476277473`, driver
51,547,517 bytes/SHA-256 `7452d1acbf5adb8192cc081f09054fa12710d57c05173a9ec7ac5e12d39df951`. Robert is now3393/36524,
this iteration240 saved days; the current day03 stage has145 saved days.
Requested16 is not substituted for observed19, and no natural succession or
new M7 matrix identity is credited.

One existing-driver cold lifestyle query on the actual native:3 frame confirms
`tax_man_perk` owned for this Robert, with formal precondition `ready`,
stewardship wealth focus,0 unspent perk points,8 used stewardship points and21
owned perks. This is a fresh owned-state primitive, separated from the
historical ledger receipt; no perk was newly submitted or credited again.
Its legal-focus-candidate readiness remains false, so the owned query is not
promoted to an available focus-change action. Root also reports that v26 now
observes Holy Loan amount300, while the decision reader remains capability
RED. The planned v27 void-getter repair is static work and does not establish
current debt, decision legality or a complete religion loop.

Cold evidence is
`m7-robert/robert-mainline-v26-current-review-01/actual-candidate-cold-goal-01/result.json`;
its already-frozen compact fields are
`m7-robert/V26-CURRENT-COLD-REPORT-FIELDS-01.json`. The normal close is
`m7-robert/v26-holy-life-following-normal16-01/result.json`, summarized once in
`m7-robert/v26-holy-life-normal16-stage-fields-01.json`. The fresh lifestyle
material is `m4-lifestyle/v26-actual-tax-man-cold-01/life/summary.json`.
Delivery pins and actual normal plan contexts are in
`m7-robert/V26-CURRENT-COLD-NORMAL-REPORT-FIELDS-01.json`. This update used
cached cold fields and new closed summaries; it did not reread old cold raw,
access current state/SDK or rerun gameplay/tests/Git. M7 remains `in_progress`.

## Actual v27 cold and one hundred saved normal days, 2026-10-03

The actual v27 qualified cold baseline is GREEN at new GAME64876, replacing
GAME15592. Robert29829 remains alive, paused and map-ready at raw53226552 in
the original episode `native-29829-2bc2d599f7f9`, with the saved
`dynasty_continuity` goal and all six ledger pins verified. Ten opaque streams
were carried through the official current-pair path. Its normal source pair
has saveanchor4309; the actual cold consumer reports full4310/save4309.
The carried checkpoint is87,736,994 bytes/SHA-256 `bdae8c8e62b96a03e1f78f8c7d0f73ebdb2e55d932d8ea9a835f1a7936cba40a`.
This cold baseline adds0 natural days, action replays or qualification slots.

Public runtime, native metadata and actual compiler source are
`f30579bf6405e183192c96ea6b9bc35dddd11eec`, bound to new environment
`b8a8f48f37324884afa8d7055cd764f0c45c5af9ae82b34e18c62894f1b916be`. The adopted DLL is
8,126,976 bytes/SHA-256 `dd7213463527f18662e5b0374a1555e98ab5303dc84c1c349ac3648ffff175ba`. The following normal window
uses the same qualified source/native/environment and GAME64876; the baseline
itself skipped government and the next planner, so actual normal-plan use is
the separate evidence below.

The requested100-day window closed `normal-time-target-reached` with
100 actual saved days,25
formal turns and0 natural modals,
raw53226552→53228952, ending paused.
Formal turn count comes from this sole closed summary rather than from the
save-history delta or requested day target. Returned normal plans contain
25 saved campaign-goal contexts and25 observed
government contexts, used by the normal execution. Goal origin/current remain
29829, with `reconciled_successions=0`
and `last_succession=null`.
The saved pair is h4357/full4357:
checkpoint88,439,522 bytes/SHA-256 `13975cb88e26e499847874d79edcfdce3ad2186e9b82d7a5ae909f028599e7a8`, driver
52,288,988 bytes/SHA-256 `a25a4894989c9f0fbae8c41455e26a00879bb36f9f9fd9b48914c2361302e63f`. Robert now has3526/36524
durable days, this iteration373 days, and278 saved days in the current day03
stage. No natural succession or new M7 identity/matrix completion is credited.

Root's closed religious readonly preview now observes a Holy Loan quote of
300 gold plus50 piety and religious renewal/communion terms costing100 piety.
The Orthodox candidate153 native paid path is `can_take=false`, with a777-piety
quote versus365.7625 player piety in that same paused preview. These quote and
legality observations are primitives; they do not establish a paid operation
or a complete religion OODA. Original faith is unchanged and paid actions
remain0. The preview is kept distinct from the later normal100 end frame;
current post-window costs or eligibility are not inferred. No unpublished
clergy source or subsequent game run is required for this closed-stage report.

Exact cold evidence is
`m7-robert/robert-mainline-v27-current-review-01/actual-candidate-cold-goal-01/result.json`;
its cached compact fields are `m7-robert/V27-CURRENT-COLD-REPORT-FIELDS-01.json`.
The normal close is
`m7-robert/v27-religion-read-following-normal100-01/result.json`, summarized
once in `m7-robert/v27-religion-normal100-stage-fields-01.json`. Combined pins
and actual plan contexts are in
`m7-robert/V27-CURRENT-COLD-NORMAL-REPORT-FIELDS-01.json`. This update used the
cached cold report and new closed normal summary; it did not reread old cold
raw or access current state/SDK, rerun gameplay/tests or perform Git work.
M7 remains `in_progress`.

## Saved v27 continuation and actual v28 cold, 2026-10-03

The preceding v27 requested30-day window closed `normal-time-target-reached` with
37 actual saved days,4
formal turns and0 natural modals,
raw53228952→53229840, ending paused.
All4 returned formal plans used the saved
campaign goal and4 observed
government contexts. Robert remains the original29829/episode, with
`reconciled_successions=0` and
`last_succession=null`.
The normal window's pair is h4366/full4366:
checkpoint88,913,610 bytes/SHA-256 `06e7e905f6ed77bd5f47f5bd6abad630d4f0786a3a8f713afb4780460621ffe5`, driver
52,399,701 bytes/SHA-256 `d45476aaebb90775caa174aadacde3f630a8230f4817ac08d8b2d9dfb9ac801e`. The saved total is now
3563/36524, this iteration410 days, with315 saved days in the current day03
stage. Observed37 is used instead of requested30.

Root then made the separate normal prestop checkpoint4367, stopped GAME64876,
and officially prepared/staged/rebound the current pair into v28. The actual
qualified cold baseline closed GREEN at new GAME24044, paused
and map-ready at the unchanged raw53229840, with the same
Robert29829/episode/saved `dynasty_continuity` goal and0 reconciled successions.
It verifies all six ledger pins and ten carried opaque streams. The normal
source history is4367; actual cold reports
full4368/saveanchor4367 through its
normal restore lineage. Official rebind retains the checkpoint bytes:
88,913,610 bytes/SHA-256 `0b4318079f2bda821a957f5128efb6c92ffd452b98fd121901f79e222b0514c4`.
The after-close driver pin is52,401,366 bytes/SHA-256
`64336c77dc9da400c76457625bbf09bd25e70de3b4b210861876be29a150d322`. Save4366 belongs to the preceding37-day window;
save4367 belongs to this current cold pair. They are not interchangeable.

V28 public runtime source is `c01b76dbd86b37e6bd1dae4519e2027eab2bbd81`, native metadata
source is `c01b76dbd86b37e6bd1dae4519e2027eab2bbd81`, and actual compiler source is
`c01b76dbd86b37e6bd1dae4519e2027eab2bbd81`. The official new environment is
`a9de6fd7782000b45a5e08f0732087bc7ae29e4fca6943f128dd4311886b79cb`. Its DLL is8,126,976
bytes/SHA-256 `80845fb309b9d223605e8d29c0acc79f2c4e62fbeb1046fbb7b2ff269acd8ce8`. Root reports the managed game minimized;
this documentation extraction performed no window or game operation.

Cold adds0 days, action replays or qualification slots. Its government query
and next planner were skipped; the preceding normal37 execution supplies
the actual goal/government-plan evidence and is not a post-v28 normal run.
The clergy query currently owned by Root and later normal continuation are
not part of this closed baseline. Natural succession remains0 and M7 remains
`in_progress`.

The normal close is
`m7-robert/v27-next-normal30-awaiting-clergy-01/result.json`, with cached compact
`m7-robert/V27-NORMAL37-REPORT-FIELDS-01.json`. New cold evidence is
`m7-robert/robert-mainline-v28-current-review-01/actual-candidate-cold-goal-01/result.json`,
its `ROOT-PACKET.json` and `official-rebind-01.json`. Exact new cold pins are
in `m7-robert/V28-CURRENT-COLD-REPORT-FIELDS-01.json`; chronological delivery
fields are `m7-robert/V28-CURRENT-COLD-NORMAL37-REPORT-FIELDS-01.json`.
This increment reused the37-day compact and read only the new closed cold
metadata. It did not reread old cold/normal100/LIFE raw, inspect pending query
directories, access current state/SDK or rerun gameplay/tests/Git.

## Actual v28 following continuation: 101 saved days, 2026-10-03

After the actual v28 cold baseline above, the same owned GAME24044 closed the
requested100-day normal window `normal-time-target-reached` with
101 actual saved days, raw53229840→53232264,
ending paused. Its sole closed summary contains12
formal turns and0 natural modals. Root's actual
breakdown is2 Guy betrothal/alliance result-consumer steps and10
`life-advance` steps; the12 formal turns are not12 clock advances. The returned
plans contain12 saved campaign-goal contexts and12
observed government contexts, followed by normal execution. Domain owners
retain the family result/receipt details rather than duplicating that business
analysis here.

Robert remains29829 in the original episode, with the saved
`dynasty_continuity` goal, `reconciled_successions=0`
and `last_succession=null`. The current
qualified native source remains `c01b76dbd86b37e6bd1dae4519e2027eab2bbd81`, with
environment `a9de6fd7782000b45a5e08f0732087bc7ae29e4fca6943f128dd4311886b79cb`. The full
saved pair is h4389/full4389:
checkpoint89,680,288 bytes/SHA-256 `f2f6f0969249dd929e825404c75ca027d08135de268bd9af9085c189d64438a2`, driver
52,676,422 bytes/SHA-256 `24102fa7dcd23622baebcd2727ca8ca1c1d99c7fe80246d6ef4590df67701534`. The durable total is
3664/36524, this iteration511 days; the current day03 stage has416 saved days.
Observed101 is used instead of requested100. No new natural succession,
identity or M7 matrix completion is credited.

Root's independent clergy query has released an actual available readonly
primitive with `nativeCanFire=false`. That observation does not authorize or
perform a dismissal, create a paid religious operation, add days or establish
a complete religion OODA. The first following Sway two-call material is also
GREEN under its own owner; no reward attribution or Sway result is added from
the passage of101 days alone.

The exact new normal close is
`m7-robert/v28-clergy-following-normal100-01/result.json`; its once-produced
stage fields are `m7-robert/v28-clergy-normal100-stage-fields-01.json`.
New compact delivery is
`m7-robert/V28-CURRENT-COLD-NORMAL101-REPORT-FIELDS-01.json`. It references the
already-released `m7-robert/V28-CURRENT-COLD-NORMAL37-REPORT-FIELDS-01.json` for
the prior37-day/cold chronology rather than rereading those packages. This
update read only the new closed summary and preserved the existing topic;
it performed no old cold/normal/LIFE raw parsing, current-state/SDK access,
gameplay rerun, tests or Git. M7 remains `in_progress`.

## Failed v28 normal100 prefix and durable 94-day recovery, 2026-10-03

The next requested100-day window ended with actual `status=error`
and exit1 after94 elapsed days. Its exact
failure is `BridgeUnavailableError: private sway native RED: published_frame_changed`. The retained attempt is not whole GREEN and
did not complete100 days. The closed summary contains31 formal
results:30 `life-advance` results and one current-first-heir betrothal-fulfillment
submission with `typed_status=receipt_pending`. That pending submission is
not an independently verified marriage outcome in this failed batch.

Root then performed a fresh readonly checkpoint through the existing official
MCP owner. That recovery closed `GREEN`, with actual paused
raw53234520 and checkpoint h4451, 90,454,144 bytes/SHA-256
`cf964132e20987f01a226ba082dd46f0eab2fcfe879a692f32997e05f3c729d6`. This normal save makes the94-day prefix durable:
3758/36524 total, this iteration605 days and510 saved days in the current
day03 stage. The recovered days are distinct from successful completion of
the interrupted100-day runner. No driver/full-history pin was fabricated or
read from live state for this report.

The recovered paused frame also contains event21 `marriage_interaction.0010`.
The private-Sway failure and this event are recorded as co-occurring; the
metadata does not prove that the event or its instructions caused
`published_frame_changed`. Root's existing event consumer accepted a choice,
advanced the instance and observed `active_event=null` at the same actor/date,
then materialized checkpoint h4455, 90,453,215 bytes/SHA-256
`323c83951479b6aa11a73131663a753a9b5bb2ab76d833ff35e3f6cb0ccdcf4d`. Event resolution adds0 elapsed days. Its retained
resolver reports `natural_provenance_verified=false` and no new live milestone
credit, so this cleanup is not promoted to a new natural-event qualification.
The separate family query concerns current first heir38822 and peer38718,
not Guy; its relation/outcome analysis stays with Root and the family owner.

GAME24044 still uses qualified native c01b76dbd86b37e6bd1dae4519e2027eab2bbd81.
Robert29829/original episode and the saved `dynasty_continuity` goal remain,
with `reconciled_successions=0` and
`last_succession=null`. Public
v29 d1b5b4c5 and its running strict build are future adoption work; the reported
documentation CI37079823259 SUCCESS does not turn this failure into game
GREEN. The following7-day window has not been consumed or credited in this
increment; final stage cutoff waits for that actual closed save. M7 remains
`in_progress`, with no new natural-succession credit.

The failed attempt is
`m7-robert/v28-next-normal100-awaiting-religion-leaves-01/result.json`.
Actual recovery is `m7-robert/v28-normal94-frame-change-recovery-save-01/result.json`;
event21 cleanup is `m2-events/v28-marriage-success21-resolve-save-01/result.json`.
Compact evidence and pins are `m7-robert/V28-NORMAL94-RECOVERY-REPORT-FIELDS-01.json`.
This increment read only these new closed metadata files, preserved the failed
attempt and reused prior delivery by reference; it did not audit the whole
fault, reread old packages, access current state/SDK or run gameplay/tests/Git.

## Partial following7 and actual v29 cold, 2026-10-03

The following requested7-day window closed with
`status=existing_consumer_not_ready` and exit0, saving only2 days,
raw53234520→53234568. Exit0 does not mean
the7-day target completed. Its3 recorded formal results comprise
the first `query-observed-first-heir-marriage-result` consumption and2
`life-advance` steps. Root's family owner independently observes the bilateral
marriage38822↔38718; this is the current first heir, not Guy. No new alliance
was observed, and none is inferred from marriage or the event title.

Turn4 encountered naturally arriving event22 `coming_of_age.1002`, with
`registry_notregistered`; it was not actively generated to create a fixture.
The existing consumer stopped and saved its actual2-day prefix. This is a
concrete registry-readiness gap, not a claim that the7-day continuation is
whole GREEN. The saved pair is h4461/full4461:
checkpoint90,534,708 bytes/SHA-256 `0a690bde85c3b96879b1d0bcca6317deb97fd2891ec57fae601bf8d9106882ca`, driver
53,602,019 bytes/SHA-256 `2678d52c6492dbf9efaf62148e8ca45c3d29dfaae7f4a0d3579a80c9644804b6`. The current durable
total is3760/36524, this iteration607 days and512 saved days in the current
day03 stage. The preceding94-day recovery remains separate, with its failed
normal100 attempt still RED.

Root's separate prestop checkpoint4462 was then officially carried into v29.
The actual new GAME120436 cold baseline is GREEN, paused/map-ready
at unchanged raw53234568, with the same Robert29829/episode,
saved `dynasty_continuity` goal, six ledger pins and ten opaque streams.
Source full4462 restores to full4463/
saveanchor4462. The current cold checkpoint is
90,534,708 bytes/SHA-256 `74eba78a3750500550f07cfbc275532ec7652fea6e52ec6f5cb9470872e522bf`;
the after-close driver pin is53,603,685 bytes/SHA-256
`aa12fa7860b239749b17aa4aa14680f37f00cba0cf27f1efa3c4038e4453ec70`. The partial window's save4461 and this cold save4462
are distinct actual anchors.

V29 runtime source is `d1b5b4c5583fa428d9226d4ebe4431e0c8db3579`, native metadata source is
`d1b5b4c5583fa428d9226d4ebe4431e0c8db3579`, and actual compiler source is
`d1b5b4c5583fa428d9226d4ebe4431e0c8db3579`. The official environment is
`de0dd8c86b8d2edc11bf4475edfab62e8485076ebc8a8a60f93106b80ddd2345`. Its DLL is8,150,528
bytes/SHA-256 `d3a851b9062a7b49e229ddd1cd92fd9b4781e14299b15788633bde1e5dffd31a`. Root's strict build66.285s and CI37080832186
SUCCESS remain build/CI evidence; the closed new-PID result is the actual
gameplay restore evidence. Cold adds0 days or qualification slots, skips
government/next-plan and performs no action replay. Goal reconciled
successions remain0, with
`last_succession=null`.

The current v29 religion query is not part of this closed extraction; no new
religious eligibility, quote, paid operation or full religion OODA is filled
from older previews. Event22 registration and later following execution stay
with their owners. M7 remains `in_progress`, without new natural-succession
or matrix-completion credit.

The new partial close is
`m7-robert/v28-marriage21-following-normal7-01/result.json`, summarized once in
`m7-robert/v28-marriage21-normal7-stage-fields-01.json`. New cold evidence is
`m7-robert/robert-mainline-v29-current-review-01/actual-candidate-cold-goal-01/result.json`,
its `ROOT-PACKET.json` and `official-rebind-01.json`. Delivery fields are
`m7-robert/V29-CURRENT-COLD-NORMAL2-REPORT-FIELDS-01.json`, referencing the
already-released recovered94 compact rather than rereading it. This update
did not inspect old fault/LIFE raw, pending religion outputs or current state,
invoke SDK/game operations, repeat tests or perform Git work.

## Actual v30 current-checkpoint cold baseline, 2026-10-03

After Root's separate v29 prestop save/full4464, official v30 preparation,
verification, opaque staging, ordinary rebind and preflight completed. The
new root-owned qualified cold baseline has now closed `GREEN`
with scope `ordinary_paused_goal_checkpoint_baseline` at actual GAME57484, distinct
from previous GAME120436. Robert29829 is
alive, paused and map-ready at unchanged raw53234568 in the
original episode `native-29829-2bc2d599f7f9`. The actual helper verifies the
saved `dynasty_continuity` goal and all six ledger pins; ten opaque streams
were carried through the official current-pair path. Source
full4464 restores normally to
full4465/saveanchor4464.

The carried checkpoint is90,534,727 bytes/SHA-256
`102ba9c82e41e26331ddc3ed1a79ac989eda2fc3be7ebb2ffa253ea5e3e3b8ee`. Official rebind preserved its bytes; the new
after-close driver pin is53,606,427 bytes/SHA-256
`14034b7c9c566bcde0ea15774c718993178e896e1ed496c98ced739540f93b7b`. No goal, episode, ledger or history was manually
rewritten. Public runtime source is `3223af636a1b7807064046f1c8e38805c5732731`, native
metadata source is `3223af636a1b7807064046f1c8e38805c5732731`, and actual compiler
source is `3223af636a1b7807064046f1c8e38805c5732731`. The new environment
is `5f2dd1f30d7aecb4c6d217179b3e40c49df3477968945cef0e6e81a72584a8bb`. Its DLL is
8,174,080 bytes/SHA-256 `f8d50afce2251d6f4c8a9f33ef159bdaae91c02133c3d4aca1255f125997550f`. Root reports strict
build65.752536s/960raw/500TUs/497uniqueCPP/0reuse/4targets; those build facts
remain separate from this actual paused/new-PID cold proof. Managed startup
requested minimization; launcher session78027 is not the game PID.

This limited baseline skipped government/next-plan, executed no planned step
and adds0 natural days or qualification slots. Durable totals remain
3760/36524, this iteration607 days and512 saved days in the current day03
stage. Goal `reconciled_successions=0`
and `last_succession=null` remain.
The prior published-frame failure/94-day recovery and partial2-day following7
remain unchanged; neither is reclassified as a completed normal target.

Event22 `coming_of_age.1002` remains the current pending event reported by
Root. Registry and HoF query publication are static-ready at this recording;
no new live event selection, HoF observation or religion OODA is claimed from
the cold baseline. Sway four-reader reattachment, HoF query, event resolution
and later following execution remain separately root-owned pending results.
M7 remains `in_progress`, with no natural-succession or matrix credit added.

New exact evidence is
`m7-robert/robert-mainline-v30-current-review-01/actual-candidate-cold-goal-01/result.json`.
It reuses `m7-robert/V30-CURRENT-COLD-PENDING-REPORT-FIELDS-01.json` for the
already-read official packet/rebind metadata; the actual result supersedes
that pending status. New delivery fields are
`m7-robert/V30-CURRENT-COLD-REPORT-FIELDS-01.json`. This update read the actual
new result once, reused cached preparation, and preserved the existing
topic. It did not reread old94/2/LIFE raw, inspect pending query outputs or
running driver, access SDK/game, rerun tests or perform Git work.

## Actual v30 following7 saved8, 2026-10-03

The new root-owned following window closed `normal-time-target-reached`
(Root observed exit0) at actual GAME57484. The request was7 days; actual
normal execution and the saved clock delta are8 days, raw53234568
to raw53234760. The final Robert29829 frame is paused and
alive in the original episode `native-29829-2bc2d599f7f9`. This fixed cutoff
is3768/36524 durable days,615 new days in this iteration and520 saved days
in the current day03 stage; a later root-owned window is outside this record.

The closed result contains4 formal result rows:
1 `life-advance` steps and3 family
result queries, with0 modal-consumer rows. The query
order was:

- Turn1: `query-player-child-default-marriage-result-v1-private`, typed status `betrothal`.
- Turn2: `query-player-child-default-alliance-result-v1-private`, typed status `None`.
- Turn3: `query-observed-first-heir-marriage-result-v1-private`, typed status `marriage`.

The first two queries consume the existing Guy betrothal/alliance-result
path; the third reads the existing first-heir typed marriage. These are
result reads, not new marriage/betrothal submissions or attributed rewards.
The actual returned plans contain saved-goal use on4
rows and government context use on4
rows. The persisted `dynasty_continuity` goal still has
`reconciled_successions=0` and
`last_succession=null`; no natural
succession or extra M7 qualification is claimed.

Normal checkpoint and full history are both4472.
The checkpoint is90,456,351 bytes/SHA-256
`944752e1b3820ebac76fccc13174f974840c0d0c9d8420d489ba39fbdbc55bc0`; the after-close driver is53,654,546
bytes/SHA-256 `c1237531d037b680db20544c8ba9d34e0e62ed1dfeca1df66254ef9d0f1be65f` with full history
4472. Native, public Python and environment
source remain the separate actual v30 cold pins above. The prior cold carried
all six ledgers and ten opaque streams; this continuation did not replay
their applied actions or rebuild the campaign goal.

Root separately reports event22 `coming_of_age.1002` resolved, independently
gone on the same actor/date paused frame and saved at4468, with0 additional
days or credited material benefit. Its domain proof remains with the
event/Feast owner at `m2-events/v30-coming-age1002-resolve-save-01`; this
normal-window extraction did not reread that full packet. HoF's current
query remains an actual partial observation with amount `null` and a real
fault being repaired; neither a full primitive nor religion OODA is inferred.
The prior Sway published-frame RED and recovered94 days, partial2-day window
and the new cold proof retain their separate statuses. Global G2 stays5/8,
nonwar2/4 and M7 `in_progress`. The current nonwar count is the already-closed
NWLIFE original TaxMan next/cold outcome loop plus NW-FAMILY; the central
ledger has used2/4 since3664. This corrects the global summary field and
adds no new credit from the current cold or eight-day window.

Exact new evidence is
`m7-robert/v30-comingage-following-normal7-01/result.json`, extracted once to
`m7-robert/V30-NORMAL8-STAGE-FIELDS-01.json`. The compact combined delivery is
`m7-robert/V30-CURRENT-COLD-NORMAL8-REPORT-FIELDS-01.json`, reusing the cached
`m7-robert/V30-CURRENT-COLD-REPORT-FIELDS-01.json`. No old94/2/cold raw,
running state, SDK, game, tests or Git were used for this increment.

## Actual normal30 and v31 current-checkpoint cold, 2026-10-03

The next v30 normal window closed `normal-time-target-reached` (Root observed
exit0), saving exactly30 days from raw53234760
to raw53235480. Its30 formal result rows
are all `life-advance`, with0 modal-consumer rows.
All30 returned plans use the preserved goal,
and all30 contain the actual
government context. Robert29829 remains alive and paused in the original
episode. The fixed normal cutoff is3798/36524 durable days,645 new days in
this iteration and550 saved days in the current day03 stage.

That normal save and full history are both4533; its
checkpoint is90,867,177 bytes/SHA-256
`7fde325081a6520ca98f938fbd9f44ed0c754f43a1a8599c0f86754e2d7f56fd`, and driver is54,499,423 bytes/SHA-256
`610743229e2e5b51ab1a4397269333b0d2c595d1c847ff5509c9d794a01906b1`. Root's separate prestop checkpoint then supplies
the CURRENT source full4534/save4534
used by official v31 continuation, rather than replaying an older archive.

After the previous managed v30 session closed normally, Root's official
prepare, verify, ten-stream staging, ordinary rebind and preflight completed
EXIT0. The new actual cold result is `GREEN` with scope
`ordinary_paused_goal_checkpoint_baseline` at GAME97992, distinct from old
GAME57484. It verifies the same Robert,
episode, saved `dynasty_continuity` goal and all six ledger pins at unchanged
raw53235480. Source full4534
restores normally to full4535/saveanchor4534.
The carried checkpoint is90,867,177 bytes/SHA-256
`fedf0860bf8943cae80170faacb9e67f9d4c801fdcbe5656bf2aa6aee54da1ee`; official rebind preserved its bytes. The new
after-close driver is54,501,086 bytes/SHA-256 `f112cef01c875defe6d730eb9d86952723fba6165975ab949c0fbeaaaeff11b5`.
No goal, episode, history or applied action was manually rewritten/replayed.

Public runtime source is `db46311827eeffe24f5a093ecc9461e12c828b40`, native metadata source
is `db46311827eeffe24f5a093ecc9461e12c828b40`, and actual compiler source is
`db46311827eeffe24f5a093ecc9461e12c828b40`. The official new environment is
`0a50491fa8f311d5abe36d341cfacfae635962bba9faa836ff032285eb8564a3`. DLL is8,174,080 bytes/SHA-256
`bbb584b6ae5860fc7ab4cedd3e4982de4c016758738ae0cc7b3c9f79496e35de`; final manifest is236,256
bytes/SHA-256 `257826ef7881a3794e8a65f40e301ca5d496adbf0f218b2654da9e68e3a84533`. Root reports strict
build65.833214s/960raw/500TUs/497uniqueCPP/0reuse/4productiontargets and official
CI run37084824555 SUCCESS. Build/CI facts remain separate from the actual
paused cold proof. Managed startup requests minimization; tool session52002
is not the game PID.

This cold scope skips government/next-plan, executes no planned step and
adds0 days or qualification slots. The preceding30-day normal window is the
actual goal/government execution evidence; it is not rerun by this cold.
Goal `reconciled_successions=0` and
`last_succession=null` remain.
Global G2 remains5/8, nonwar2/4 and M7 `in_progress`. Root's upcoming Sway
reattachment and new HoF amount query are outside this cutoff: no amount,
full HoF primitive or religion OODA is inferred from the new build/cold.

New exact cold evidence is
`m7-robert/robert-mainline-v31-current-review-01/actual-candidate-cold-goal-01/result.json`,
with that directory's `ROOT-PACKET.json` and `official-rebind-01.json` read
once as metadata. The normal evidence is cached
`m7-robert/V30-NORMAL30-REPORT-FIELDS-01.json`, retaining its one extraction
of `m7-robert/v30-next-normal30-awaiting-gold-fix-01/result.json`.
The combined delivery is `m7-robert/V31-CURRENT-COLD-NORMAL30-REPORT-FIELDS-01.json`,
also referencing the cached preceding cold/eight-day cutoff. No old failure
raw, opaque rehash, current state, pending query, SDK/game, tests or Git were
used for this increment.

## Actual v31 budget29, v32 cold and following7, 2026-10-03

The next v31 window closed `turn-budget-boundary` (Root observed exit0),
saving29 days rather than completing its request
of30 days. Its32 formal rows are the three
existing family-result reads (Guy betrothal, alliance result and first-heir
typed marriage) followed by29 `life-advance` steps, with0 modal-consumer
rows. All32 actual returned plans use the preserved goal and government
context. They read results, rather than resubmitting marriages or claiming
new action rewards. This intermediate durable cutoff is3827/resume674/day03+579
at raw53236176, save/full4594.
The checkpoint is90,931,077 bytes/SHA-256 `75deda82c678759ae5fdd7ba1e853ad0b09df71263bd9737cacd62a7e5dbd298`;
driver is55,318,366 bytes/SHA-256 `fc3008d717d9985a1b8e4c95a5b06608855dca7e0ecaa1c9eb88c9066af6a992`.
The29-day budget boundary remains partial against its30-day target.

Root's separate prestop checkpoint then supplies current
full4595/save4595 for official v32
continuation. Prepare/rebind/preflight completed GREEN. New GAME
109732 is distinct from old GAME97992;
the actual qualified cold result closed `GREEN` with scope
`ordinary_paused_goal_checkpoint_baseline`. At unchanged raw53236176, the same Robert29829,
original episode, saved `dynasty_continuity` goal and all six ledger pins
verify; ten opaque streams carry through the current-pair path.
Source full4595 restores normally to
full4596/saveanchor4595.
The carried checkpoint is90,931,077 bytes/SHA-256
`60f734e20c9d0b8d50e21d968ea051c297cc435807c02b2fd55e3136a9660176`; rebind preserves its bytes. The new after-close driver
is55,320,033 bytes/SHA-256
`eabe34ab17a79612b04e635f8977a83c51d6a96e90cc404d89d977f96fdd0559`. This cold scope skips
government/next-plan, executes no planned step and adds0 days or slots.

Public runtime source is `8cf176b436b6b0024fb591d4114b92448146181a`, native metadata source
is `8cf176b436b6b0024fb591d4114b92448146181a`, and actual compiler source is
`8cf176b436b6b0024fb591d4114b92448146181a`. The new environment is
`a659ee553736c3a9429a961711411090ed6b53931a9c1a202f057b3179397486`. DLL is8,213,504
bytes/SHA-256 `c709e1991d221abac1a066528968c437346a65ed8e401b04195323273c98a52a`; manifest is
238,388 bytes/SHA-256 `48b3dc6d93d5c224bf25a0fdd1b404874ba586030973cf8e7e019f17366ea6f2`.
Root reports strict969raw/505TUs/502uniqueCPP/0reuse and CI run37087106124
SUCCESS. The strict tool session97058 is not a timing value or game PID.
Those build/CI facts remain separate from the actual paused cold baseline.
Managed startup requests minimization.

The new same-PID v32 following window has now closed
`normal-time-target-reached` (Root observed exit0), saving exactly7
days from raw53236176 to raw53236344.
It contains10 formal rows, including
7 `life-advance` steps and
3 existing
family-result queries, with0 modal-consumer rows.
Its actual returned plans use the saved goal on10
rows and government context on10
rows. The final Robert29829 frame remains alive and paused in the original
episode; goal `reconciled_successions=0`
and `last_succession=null` remain.

The new fixed cutoff is3834/36524 durable days,681 new days this iteration
and586 saved days in the current day03 stage. Save and full history are
both4611, checkpoint90,886,952 bytes/SHA-256
`1927e6392eac3baeed592a27650546884e0bf8437d677a2e249a99a092b5d6b6`; final driver is55,520,371 bytes/SHA-256
`b538eadac58ffdf58a9989bcf3a5e87ff0160acb75c9ecf80e2c282ad7960e9a`. The normal continuation supplies actual goal/government
execution evidence without replaying applied ledger actions. Global G2
stays5/8, nonwar2/4 and M7 `in_progress`, with0 new natural-succession or
matrix credit. Upcoming three religion queries and a new normal100 window
are outside this cutoff; no future amount, paid outcome or time count is
filled here, and no religion domain readiness is inferred from build/CI.

Exact new following evidence is
`m7-robert/v32-religion-type-tax-following-normal7-01/result.json`, extracted
once to `m7-robert/V32-NORMAL7-STAGE-FIELDS-01.json`. The earlier29-day window
and actual v32 cold metadata were already cached in
`m7-robert/V31-NORMAL29-REPORT-FIELDS-01.json` and
`m7-robert/V32-CURRENT-COLD-NORMAL29-CACHED-REPORT-FIELDS-01.json`.
Combined delivery is `m7-robert/V32-CURRENT-COLD-NORMAL29-AND7-REPORT-FIELDS-01.json`.
This increment reused those caches, did not reread old raw/opaque streams or
pending query outputs, and used no current state, SDK/game, tests or Git.
