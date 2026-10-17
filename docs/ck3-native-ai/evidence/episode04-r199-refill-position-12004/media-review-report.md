# R199 offline media audit (bounded)

- `machine_id`: `desktop-3fevhd2-1c74096080`; observed 2026-10-17 13:25:37 UTC on the execution machine (`tools/ck3_live_run_id.py machine`).
- Scene: `D:/workspace/ck3_native_war_ai_promo_work/e04-r199-refill-add-a01`; source head `26449eb2676b4ccb71cb818fb0cc398b0a5fd1e6`; run `desktop-3fevhd2-1c74096080--vanilla--R0199`.
- Source raw: `raw-r199-refill-a01/raw.mkv`, 110,560,976 bytes, SHA-256 `8394c5e177752d4493ab8e93507855efc056c8353b7cc2e69345078da23d6f05`. This full-file hash is **reused from Finish**, not independently recalculated in this audit. Finish response `responses/r199-refill-a01-ready-record-finish-once.json` is 5,234 bytes, SHA-256 `2dd8010a8d7632cee5790838d9a49e8a9f5e359def164aee9b87f0ab85aeb4ac` (independently checked). Scope `R199-MAP-SCOPE.actual-a01.json` pins the local FFmpeg 9.0.1 binary; no raw copy was made.

## Results

| Check | Observed result | Audit disposition |
| --- | --- | --- |
| Recorder Finish | `NORMAL_TREE_EMPTY`, exit 0, job empty, capture guard null, partial video false | Normal recorder exit only |
| Planned wall duration | Start 12:56:46.953548 UTC, Finish 13:00:31.591465 UTC = **224.637917 s**, plan 180 s; excess **44.637917 s** | `planned_duration_exceeded: true`; duration gate **FAIL** |
| Container/video | Matroska, H.264 constrained baseline, 1280×720, 30 fps, encoded duration 180.000 s, no audio stream | Probe readable; encoded duration does not cancel the wall-duration failure |
| Full AV decode and PTS | Exactly one full video decode, exit 0: 5,400 frames, decoded frame numbers 0…5399; PTS 0.000…179.967 s, strictly increasing; adjacent intervals 0.033 s ×3599 and 0.034 s ×1800; no decode errors found. No audio stream to decode. | Media decodes and timing is continuous at frame granularity |
| Limited visual review | Six original-size 1280×720 JPEG samples at encoded 0, 30, 40, 120, 170, 179 s. At 0/30 s the army panel shows 1,173 and no route; at 40/120/170/179 s a route toward the south is visible. All six show the paused map and in-game date 1067-02-23. The 179 s end sample still shows that date. No desktop border or outside window is visible in these samples. | Sampled on-camera move-route change; no sampled on-camera next day. This is **not** certification that every intervening frame is clean. |
| Native context | `r199-move-home-2629-once-a01.json` records owner 31254's army 18 ordinary move command to 2629 at 12:57:23 UTC, with native postcondition/route. `r199-advance-one-day-once-a01.json` and independent after-day snapshot record date_raw 53148192→53148216; command packet timestamp 12:59:54 UTC, after the nominal 180 s recording horizon. Wall timestamps are search clues, **not encoded PTS**. | Native one-day advancement is separate evidence; this raw does **not** establish that the natural day appears on camera. No ADD probe/ADD result. Player army movement does not establish vassal AI behavior. |

The pre/post route visual bracket is only **30–40 s by six-frame sampling**; it is not a frame-exact transition bound. The original video ends at 180 s encoded, while Finish occurred 224.638 s after Start. The sampled final frame remains at the pre-advance game date. There is no honest continuous-clean span certification or business-positive ADD claim from this audit.

`continuous_clean_certified: false`; `human_1x_approved: false`; `signoff: false`; `ADD_proven: false`; `on_camera_natural_day_proven: false`.

## Evidence and retention

`ffprobe.json` is the exact probe output. `decode-pts.log` is the one full-decode `showinfo` trace. `frame-*.jpg` are the six bounded samples. `asset-manifest.json` lists local file sizes and SHA-256. The external lane remains below 12 MiB and uses the shared D-volume pool without copying the raw. Review these derived assets after 48 hours under `docs/storage-retention-policy.json`; protect the original scene evidence according to its active use and policy, with a separate expiry review. No SDK, CK3, desktop, or main-repository mutation was performed.
