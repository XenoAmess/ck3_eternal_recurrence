# Mandala Purge Workshop Screenshots

Both Workshop images are deterministic JPEG projections of the final real CK3 `1.19.0.6` acceptance capture. They are not generated illustrations and are excluded from the exact 15-file mod staging.

## Evidence source

- Artifact: `C:\Users\1\AppData\Local\Temp\mrma_20260908_044123_6e4451cd`
- Report result: GREEN
- Report SHA-256: `6ebd3d055f3ca1816512ebac925999695f80de8f73e3d09151fd050130ad6547`
- Source: `cell/08_acceptance_summary_event_full.png`
- Source dimensions/bytes/SHA-256: 2560×1440 / 4,948,867 / `8eb4519fb1fd182f17d6a2f352806dbcd9c316d8fa71c958f7e7f4f341abc114`
- Renderer: `tools/compose_remove_mandala_workshop_media.py`, Pillow quality 90, optimized progressive JPEG, 4:4:4

## Upload order

| Order | Feature / 功能 | Crop `(left, top, right, bottom)` | File | Dimensions | Bytes | SHA-256 |
|---:|---|---|---|---:|---:|---|
| 1 | Full live acceptance and map / 完整实机验收事件与地图 | `0,0,2560,1440` | `workshop/remove_mandala_media/01_live_acceptance_full.jpg` | 2560×1440 | 874,686 | `8bdffe05e9f3bfa81486cb0b1958faef36eb53dd54831da17066b25a66b6ebb5` |
| 2 | Readable acceptance-event detail / 可读的验收事件细节 | `560,320,1990,1110` | `workshop/remove_mandala_media/02_live_acceptance_event.jpg` | 1430×790 | 199,465 | `439b17cd0f1155a46a4439312b29e468d7430db9f18f5ee122ec2061b4d8e41a` |

Recommended captions:

1. `All start, delayed, recurring and AI-redirect checks passed / 开局、延迟、周期与 AI 转制拦截全部通过`
2. `No Mandala rulers; no Temple Citadels / 曼荼罗制统治者与寺庙城寨均归零`

## Publication evidence

- Workshop item: [`3797711947`](https://steamcommunity.com/sharedfiles/filedetails/?id=3797711947)
- Published publicly: 2026-09-08 (Asia/Shanghai)
- Uploaded through the owner page in ledger order: `01_live_acceptance_full.jpg`, then `02_live_acceptance_event.jpg`
- Owner-page verification: both thumbnails were visible; selecting each displayed the corresponding full-map/event view in the media strip
- Steam public details API verification: `result=1`, `visibility=0`, exact title `Mandala Purge — 肃清曼荼罗伪信`, published payload size `777270`
- The owner page did not expose stable public CDN URLs in its management UI. Publication is therefore bound by item ID, visible media order, the tracked exact source hashes above, and the fresh 15-file subscribed-cache verification in the acceptance report; no CDN hash is invented.
