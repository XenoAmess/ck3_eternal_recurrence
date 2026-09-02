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
