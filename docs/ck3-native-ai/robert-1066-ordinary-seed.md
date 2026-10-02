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
