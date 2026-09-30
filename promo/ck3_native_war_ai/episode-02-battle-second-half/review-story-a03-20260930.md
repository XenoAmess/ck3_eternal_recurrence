# Episode 2 a03: narrated UI review revision

This revision addresses the five review notes with a shorter causal observation
route: original contact question → knight roster and attributes → arriving army
and revised combat width → pursuit losses → the later replay's war contribution.
The separate replays are identified on screen and in narration; this edit does
not assert that a change in one replay caused the result in another.

## Exact final media

- Local run: `C:/Users/1/AppData/Local/ck3-review-render/episode02-review-20260930-a03-a03/`.
- File: `CK3-War-AI-Episode02-Review-20260930-a03.mp4`.
- Bytes: **61,270,366**.
- SHA-256: `87EECA6F4EA3535B229B8FA6A7E554A6ABA3E599135B494D5A251B9786B99BB7`.
- Video: 389.433333 s, 1920×1080, 30 fps. Audio: 389.454667 s.
- Edge TTS: `zh-CN-XiaoxiaoNeural`, rate `-5%`; 39 Chinese utterances.
- Burned subtitles: 39 Chinese and 39 English cues. Both languages have fixed
  positions within the y900–1080 subtitle region, separate from the UI footer.
- Actual hook ends at 6.466667 s. Robert, Ali, Messina and the review goal are
  introduced by 14.166667 s.
- Five short raw excerpts retain their source labels. The other shots explain
  enlarged original UI pixels while narration continues. Chapter tail holds are zero.

## Checked-in production inputs

- [Project intent](project/review-story-a03-project.json): exact run configuration.
- [Narration and visual intent](project/review-story-a03.json): final v4 bytes,
  SHA `DEA078995E48CF28174F0AF75AFB929728B12BB1C22FF1757563506A8A7822D5`.
  v4 changes only nine English cues' spacing; all Chinese narration is unchanged
  from the independently reviewed v3. All 39 retained audio files were hash checked.
- [Edit mapping](project/review-story-a03-edit.json): actual source paths, still
  assets, raw excerpts and frozen raw identities. Whole raw files were not rehashed.
- [UI board specifications](project/review-story-a03-board-specs.json) and
  [board composer](compose_review_story_boards.py): source pixels, crop rectangles,
  overview marks and separately labelled native records.
- [Project producer](review_story_a03.py): real `prepare`, `narrate-raw`,
  `reuse-narration`, `reuse-processed-narration`, `finish-narration` and `render`
  phases. `render` runs five FFmpeg chapter encodes concurrently and joins them.
  Each new attempt refuses existing output paths and retains command/stdout/stderr.

This is a project composer executed directly, not a claim that the generic
`xar-promo build` CLI was executed. The generic wheel supplies TTS, ASS filter
construction, native `start-run`, preservation and typed append-only records.
The exact ProjectConfig was snapped before production and copied here unchanged.

For this run, the latest formal GitHub Release was queried anew and was **0.2.1**.
Wheel SHA-256: `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`.
The verified interpreter was
`D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe` (Python 3.14.7).
The run retains the release query, environment and script bytes. Future runs must
query the then-current latest formal release and verify its wheel and interpreter.

## Verification evidence

- Vanilla ledger: `C:/Users/1/ck3-video-vanilla-verification-20260930/attempt-a03/verification-v1.json`,
  SHA `0DC37F02A80D8E477A2C773F184A5ABB1DC727D34DA1560A7CA7D1EE8DD6C78F`.
  Unverified healing/rejoining, historical knight arithmetic, voluntary mid-battle
  withdrawal and cross-replay defeat causes are excluded from the narration.
- Machine report: `C:/Users/1/ck3-a03-machine-audit-20260930/attempt-01/new-a03-a03-report.json`,
  SHA `C104B4DBE0A658DF6AC3C1B0F47D0993C2FCD0EB5A41DCA015BE87BED0F5524E`.
  Complete new video decode exited 0 for 11,683 frames. All 78 bilingual cues,
  timings, ASS render bindings and fixed positions passed. Audio/video length
  difference is 21.334 ms. Actual AAC packets, codec configuration and timestamps
  exactly match the preceding render, so its −40 dB / ≥2 s silence result is
  validly reused: **zero qualifying intervals**. No audio listening is claimed.
- Product review: `C:/Users/1/ck3-a03-independent-review-20260930/quality-04/actual-product-review.json`,
  SHA `22568DB345190F62F6965F56920CA8FF4DA1F16676914B2F42E51D74C7CB4701`.
  One ten-frame review of the preceding render found the global subtitle collision.
  Exactly two changed frames from these final bytes resolved that P0; unchanged
  script, source and timing evidence is explicitly bound. No blocker remains in
  this limited review scope.
- Shared final frame package: `shared-actual-frames-a01/shared-frames.json`,
  SHA `0EBFA172178C0C548FC8C785C0F1A01CB0B8B1A3B642A0F1934F1DB17949260A`.
- Native bound probe: `bound-media-probe.json`,
  SHA `90DE6FE972F4119FE16D4D931A044E5A258AF7F3ABBA5E7559DEA2401C7BB48F`.
  It binds the independent retained ffprobe result; no second probe was run.
- Native manifest: `native-run/run-manifest.json`,
  SHA `74553439A30BEE9BD01577649C4728D96082598B5FA4890378DBB26352193DB2`.
  `xar-promo validate` passed with files checked and 39 preserved artifacts,
  typed external-composition/machine/limited-product records and zero signoffs.
- Preservation receipt: `native-preservation-complete.json`,
  SHA `6E2BEBA9B6B8F5C6F36AC984B48ACE95D2267A46187A7A4A9A35B62147121EDA`.

## Retention and review status

The prior delivered a02, first raw-TTS attempt, v2/v3/v4 scripts, the initial
DD25 render, its rejected visual review, the original machine verifier's failed
condition and its appended correction remain unchanged. New a03-a03 output
paths preserve all previous material; no assets were removed.

The final single MP4 was copied to
`C:/Users/1/OneDrive/CK3-War-AI-20260923/CK3-War-AI-Episode02-Review-20260930-a03.mp4`.
Source, copy stream and local target bytes/SHA match the identity above.
At **2026-09-30 16:35:23 CST**, the OneDrive client's Cloud Files metadata
reported `InSyncState=1`, `validated=61270366`, `modified=0`, with all nine
metadata checks passing. Independent remote readback was not performed.
The delivery receipt is
`C:/Users/1/AppData/Local/ck3-review-render/episode02-delivery-20260930-a03/delivery-final-20260930T083558435900Z.json`,
SHA `B6278D14AD3FF22372C3DAE0C898F218E33E22A1D2704A1F14774EDB94591530`.
Only that MP4 was transferred. No cloud-only file, sync setting or game/desktop
state was accessed by this production task.

Machine conditions and targeted visual review passed. **Human complete 1×
review, listening quality, signoff and clean-span certification remain pending.**
