# Phase-two promo authoring and claim matrix

The machine-readable authority is
[`phase2-authoring-claims.json`](phase2-authoring-claims.json). It is a
Chinese-first narration draft with simultaneous Simplified Chinese and English
subtitle lines. Simplified Chinese remains the primary visual/subtitle layer and
English remains secondary. This is the ZhongGuo phase-two promo contract, not
the monthly English-primary show-off contract. The intended voice remains
`zh-CN-XiaoxiaoNeural`.

The ledger is deliberately **not** builder input. All ten source chapters remain
`planned`, and every drafted cue remains `release_usable=false`. This authoring
pass did not call TTS, render subtitles, invoke FFmpeg, capture CK3, or create a
replacement image/video. Promotion into `phase2-promo-project.json` happens only
after the corresponding real footage and claim can be reviewed.

## Evidence boundary

- The opening and finale are future generated bilingual cards. They are required
  for a candidate but prove no gameplay capability.
- Chapters 2 through 9 bind, in order, to the eight canonical producer keys in
  `tools/zhongguo_phase2_promo_producer.py`. Each ledger row also freezes the
  matching provider-observed postcondition from
  `tools/zhongguo_phase2_capture_choreography.py`.
- All eight gameplay cues require real managed CK3 clean spans bound to one
  canonical seed/save lineage and the same exact source commit/tree, game
  version/EXE, and product-only mod mount. Each span must keep its own
  pre-action-post session/PID/generation/revision chain continuous and bind
  start/end checkpoint hashes, the provider-observed postcondition, and GREEN
  cleanup. Clean CK3 restarts are allowed between spans; fixtures, old
  phase-one or old-version footage, generated cards, MCP schemas, and command
  ACKs cannot satisfy the requirement.
- `static-ready` describes the current evidence available to write a bounded
  draft. It does not mean `fixture-live`, `production-live`, `complete`, or
  `release-ready`.
- The final wording may be shortened after the real footage duration is known.
  Claims may not be strengthened unless the lineage-bound evidence and human review
  support them.

## Review through `d0fa156`

The 2026-09-03 content review is frozen in the JSON `readiness_review` block.
At `d0fa15670fc9b0c049cc6d9228c839c04135e21c`, there are still zero verified
lineage-bound phase-two clean spans. The latest phase-two terminal remains
`RED/LegalConsentNotAuthorized`: the run stopped before the producer seam,
recorded zero producer entries, and generated no footage. The exact evidence is
`docs/ck3-native-ai/phase2-producer-identity-live-2026-09-02.md`. This newer
terminal is now a hash-bound authoring authority; it does not promote any claim.

The review found six cue-level overclaim risks relative to the current capture
postconditions and narrowed them before footage arrives:

- fact/quota no longer says calibration debt persisted when the span only proves
  a visible identity-ready calibration event and an observed revision change;
- receipt/PIP no longer promises cross-cycle persistence before the same-case
  selected response is provider-observed;
- manager governance no longer bundles refusal, team snapshot, and accountability
  into one terminal-event proof;
- promotion no longer claims both successful settlement and failed reservation
  release from a one-path span;
- projects and incidents no longer infer reorganization/shared-office effects or
  closure from a button/command ACK.

Every gameplay claim now lists the additional visible observations needed before
its cue can be promoted. If the eventual clean span lacks any listed observation,
the operator must rewrite or drop that clause; passing the generic choreography
postcondition alone is insufficient.

The planned source finale title still says "organizational capability complete,"
which directly conflicts with its own cannot-claim boundary. Because the source
project must remain untouched and `planned` before footage review, both generated
chapters now carry reviewed replacement titles in this authoring ledger. Promotion
must copy those titles as well as the cue; the validator rejects any generated
title containing the completion claim.

## Subtitle editorial guard

Every cue provides one or two explicit Simplified Chinese lines and one or two
English lines. Chinese lines reproduce the spoken narration exactly; every line
must end at a sentence or clause boundary. The frozen promotion mapping joins
those editorial lines with newline separators in the future project subtitle
input. The promo renderer converts those separators to explicit ASS semantic
breaks and may still wrap within each line according to rendered width.

The validate-only guard constructs this exact future `id+narration+subtitles`
cue shape and rejects stray embedded breaks, malformed track sets, or lost
semantic separators. It also uses conservative display-width limits (48
East-Asian display units for Chinese, 78 for English) before the promo tool
performs its later font-based wrapping and 1920x1080 safe-area check. Passing
this editorial guard does not replace final font-measured layout or rendered
subtitle inspection.

Run the read-only check with:

```powershell
py mod_zhongguo_style/tools/validate_phase2_authoring_claims.py --validate-only
py mod_zhongguo_style/tools/test_validate_phase2_authoring_claims.py
py -O mod_zhongguo_style/tools/test_validate_phase2_authoring_claims.py
```

The validator pins the current phase-two project, creative brief, promo manifest,
readiness ledger, and latest phase-two live terminal by SHA-256; checks the exact
ten-chapter order, Chinese-primary/English-secondary visual hierarchy, Xiaoxiao
voice, canonical span/postcondition bindings, required visible observations,
project-cue projection, subtitle line limits, repository evidence paths, and
pending release states; and has no write or render mode.

The final-video no-media planner binds this exact ledger by bytes and SHA-256:

```powershell
py tools/plan_zhongguo_phase2_final_promo.py `
  --output <new-runbook.json> `
  --capture-root <lineage-bound-green-capture> `
  --seed-preflight-report <preflight.json> `
  --media-preflight-report <media-receipt.json> `
  --expected-media-preflight-sha256 <receipt-sha256> `
  --tts-cache <future-content-addressed-cache> `
  --work-dir <future-new-attempt>
```

All ten validated draft claims make the runbook authoring-input gate GREEN; the
source project deliberately remains `planned` until the first 1× review proves
which claims the real footage supports. Missing footage therefore remains the
typed `footage_pending` blocker, not `authoring_pending`. The planner only writes
JSON and does not fetch, render subtitles, invoke TTS/FFmpeg, or create a video.
Its first future production step still requires fetching the standalone promo
tool and proving a clean `HEAD == origin/main` before refreshing the media
receipt or running any builder command.

The runbook also revalidates the environment receipt's exact SHA-256 and its
bound preflight implementation/project config. It requires the no-secret
Xiaoxiao provider record, in-memory measured wrapping, no-ASS/no-encode
attestation, and the H.264/yuv420p/1920×1080 plus AAC 48 kHz stereo capability
contract. Its authoring section exposes all eight canonical producer keys,
provider-observed postconditions, and per-span visible-observation lists. With
the current receipt and absent live inputs, the production-start boundary is
typed `fresh_promo_tool_fetch_required`, `footage_pending`, and
`publish_target_pending`; the environment itself can remain GREEN without
claiming that the final video is ready.

`--capture-root` is consumed through the dedicated media-entry intake schema
`zg361_phase2_footage_intake`; this does not extend or reinterpret the native
observer schema. It accepts only the runner's canonical `report.json`,
`cell/promo/capture-timeline.json`, `evidence-index.json`, and
`cell/04_phase2_seed_loaded.json` paths. It byte-verifies those files, the
nonempty raw recording, and every clean-frame image/gate against the same
evidence index. The legacy schema still accepts an unchanged all-eight-span
single managed session. The span-session-v2 schema instead requires one
canonical seed/save lineage and exact source/game/mod-mount identity across all
eight spans. Within each span, pre → action → post must remain on one managed
session/PID/generation with an explicitly linked revision chain, byte-bound
start/end checkpoints in the same save lineage, a provider-observed GREEN
postcondition, and GREEN process/driver cleanup. Different spans may use clean
CK3 restarts and therefore different PIDs or connection generations. The seed
generation → loaded-seed proof remains a separate save-hash and source-
provenance continuity gate; seed generation and capture may use different
managed sessions.
Ordered recording marks and eight clean-frame gates are still mandatory.
Missing, partial, intra-span discontinuous, lineage-drifting, phase-one,
old-version, fixture, or hash-mismatched input stays typed `footage_pending`;
the planner neither repairs nor promotes it.

A GREEN intake is an immutable source binding, not a one-use token. The same
verified eight-span bundle may feed two independent edit projects. Each project
and candidate must independently bind the unchanged timeline/report/index/raw,
checkpoint, and gate hashes; reusing the bundle neither copies nor regenerates
footage and cannot upgrade an unsupported claim.

Inspect an existing capture without producing media:

```powershell
py tools/zhongguo_phase2_footage_intake.py `
  --capture-root <lineage-bound-green-capture> `
  --output <new-intake-report.json>
```

The same intake now runs inside
`mod_zhongguo_style/tools/build_phase2_promo_video.py` for both validation and
full-candidate execution. After the fresh promo-tool media receipt is bound, a
RED intake raises typed `footage_pending` before ready-authoring checks, TTS
cache access, subtitle layout, composer construction, FFmpeg, or attempt-folder
creation. The planner and builder share one dependency DAG: promo-tool refresh
and receipt → verified eight-span footage → first full-speed source review and
authoring promotion → Xiaoxiao cache validation → zh-CN/en subtitle safe-zone
layout → composition → claims audit → final full-speed review and sign-off →
export → explicit publication. The two 1× reviews remain human gates and are
never inferred from automated validation.

## Publication target authority

There is currently no named external video platform, account, credential
reference, or upload authorization in the handover or project documents. Local
artifact paths and the offline xar_promo export bundle are not publication;
the Steam Workshop media-strip instructions cover static images, not this
video. The planner therefore reports typed `publish_target_pending` and emits
no upload command. The explicit validate-only authority and publication-receipt
fields are documented in `phase2-publish-target.md`.

## Final completion attestation

Planning readiness and a rendered candidate are not completion. The runbook
accepts an optional `--completion-attestation` and stays RED with typed pending
codes until its final read-only gate closes every boundary. The attestation
must point to existing, byte-bound files; the validator never creates them.

The final gate requires the same candidate bytes in the native xar_promo run
manifest, latest approved signoff, bound ffprobe envelope, claims audit, both
independent named 1× review receipts, export manifest and exported file, and
publication receipt. The probe must report H.264/yuv420p 1920×1080 video, AAC
48 kHz stereo, and a positive duration below 1,200 seconds. The export remains
the existing offline `xar_promo_release_bundle` with its exact allowlist; the
separate publication receipt must match the owner-approved target/platform/
account, contain a non-placeholder HTTPS locator under its authorized prefix,
timestamp, `remote_verified=true`, and hashes for the same candidate and export
manifest. Missing boundaries are reported as `candidate_media_pending`,
`claims_audit_pending`, `review_round_1_pending`,
`review_round_2_pending`, `export_pending`, `publish_target_pending`, and
`publish_pending`.
`footage_pending` is always ordered before them when the real eight-span input
is absent. Only an empty blocker list and a GREEN completion gate changes the
runbook status to `COMPLETE`.
