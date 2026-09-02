# Phase-two promo authoring and claim matrix

The machine-readable authority is
[`phase2-authoring-claims.json`](phase2-authoring-claims.json). It is a
Chinese-first narration draft with simultaneous Simplified Chinese and English
subtitle lines. This is the ZhongGuo phase-two promo contract, not the monthly
English-primary show-off contract. The intended voice remains
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
- All eight gameplay cues require clean spans from one real managed CK3 run.
  Static wiring, fixtures, old phase-one footage, generated cards, MCP schemas,
  and command ACKs cannot satisfy that requirement.
- `static-ready` describes the current evidence available to write a bounded
  draft. It does not mean `fixture-live`, `production-live`, `complete`, or
  `release-ready`.
- The final wording may be shortened after the real footage duration is known.
  Claims may not be strengthened unless the same-run evidence and human review
  support them.

## Subtitle editorial guard

Every cue provides one or two explicit Simplified Chinese lines and one or two
English lines. Chinese lines reproduce the spoken narration exactly and break at
sentence or clause boundaries. The validate-only guard uses conservative display
width limits (48 East-Asian display units for Chinese, 78 for English) before the
promo tool performs its later font-based wrapping and 1920x1080 safe-area check.
Passing this editorial guard does not replace final rendered subtitle inspection.

Run the read-only check with:

```powershell
py mod_zhongguo_style/tools/validate_phase2_authoring_claims.py --validate-only
py mod_zhongguo_style/tools/test_validate_phase2_authoring_claims.py
py -O mod_zhongguo_style/tools/test_validate_phase2_authoring_claims.py
```

The validator pins the current phase-two project, creative brief, promo manifest,
and readiness ledger by SHA-256; checks the exact ten-chapter order, Chinese-first
language policy, Xiaoxiao voice, canonical span/postcondition bindings, subtitle
line limits, repository evidence paths, and pending release states; and has no
write or render mode.

The final-video no-media planner binds this exact ledger by bytes and SHA-256:

```powershell
py tools/plan_zhongguo_phase2_final_promo.py `
  --output <new-runbook.json> `
  --capture-root <same-run-green-capture> `
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

`--capture-root` is consumed through the dedicated media-entry intake schema
`zg361_phase2_footage_intake`; this does not extend or reinterpret the native
observer schema. It accepts only the runner's canonical `report.json`,
`cell/promo/capture-timeline.json`, `evidence-index.json`, and
`cell/04_phase2_seed_loaded.json` paths. It byte-verifies those files, the
nonempty raw recording, and every clean-frame image/gate against the same
evidence index. It then requires one managed PID and connection generation,
valid loaded-seed revision identities, no session restart, ordered recording
marks, eight canonical clean spans, and all eight provider-observed
postconditions GREEN. Missing, partial, cross-session, or hash-mismatched input
stays typed `footage_pending`; the planner neither repairs nor promotes it.

Inspect an existing capture without producing media:

```powershell
py tools/zhongguo_phase2_footage_intake.py `
  --capture-root <same-run-green-capture> `
  --output <new-intake-report.json>
```
