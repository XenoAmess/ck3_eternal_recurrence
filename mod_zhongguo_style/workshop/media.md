# ZhongGuo 361 Workshop Media

These six JPEGs are deterministic, presentation-only crops from the final
`GREEN` CK3 acceptance artifact. They are real game captures, not generated
illustrations; the untouched PNG evidence remains at the external artifact
location below. The JPEGs are for the Workshop description/gallery and must
not be put in the mod release staging.

## Evidence source

- Artifact root: `Z:\ck3_mod_rewrite_process_assets\zg361\runs\zga_20260829_061314_ea5f04ad`
- Capture directory: `cell/`
- Acceptance result: `GREEN`, CK3 `1.19.0.6`, isolated userdir, 2560×1440
- Report SHA-256: `dccf8b87d990ba3ed3074fae3391e5004e6cd8b07a5c80750bc344e7f9024c25`
- Evidence-index SHA-256: `b3f88f34a1a84db2414339b01ae10246c59dc8390a46a29a2286904f9ee38df7`
- Renderer: `tools/compose_workshop_media.py`; Pillow JPEG quality 90,
  optimized progressive 4:4:4 (`subsampling=0`); each output is below
  Steam's 2,000,000-byte limit.

## Projections and upload order

| Order | Feature / 功能 | Acceptance source | Source SHA-256 | Crop `(left, top, right, bottom)` | Workshop JPEG | Dimensions | Bytes | Output SHA-256 |
|---:|---|---|---|---|---|---:|---:|---|
| 1 | Calibration meeting / 绩效校准会议 | `cell/06_calibration_event.png` | `8e1813d538be9f95736d9f07eb88b7bcb719320d421eb37dfbcfce649bd65aab` | `420,280,1610,875` | `media/01_calibration_meeting.jpg` | 1190×595 | 166,163 | `abdc899a14ce6ce0f48df5af0e18290efa65971e65ebea3e39eb94bba59575a2` |
| 2 | Frozen review cohort / 冻结考核名单 | `cell/07_result_summary.png` | `b020a11ea9e8e10db7aaace83dff11bbde05cb9b2af6a64b3aa9ce55d92b2f7d` | `430,275,1605,885` | `media/02_review_cohort_frozen.jpg` | 1175×610 | 184,750 | `9ca4d85efb4be45f16927912343509e81ec9722a190a1d4a805a50fe3b8adccf` |
| 3 | 30/60/10 scoreboard / 天朝官员考核榜 | `cell/08_scoreboard_panel.png` | `bb45518330ea20399d0b73f6776c72ac5da6f3ebdf1e2c84dc6643430ad9aca3` | `430,130,1640,1020` | `media/03_scoreboard.jpg` | 1210×890 | 180,041 | `98d06d1661745761ab94d90628eedbf67668e5e77a74863ce5c46c27753fb790` |
| 4 | Semi-mandatory Jingcha / 京察之期 | `cell/09_jingcha_mandate_event.png` | `9f7bb4ee382677c035d6256da3d5c113959e2026b3a1ef59fce33d22ae53cb06` | `420,280,1610,875` | `media/04_jingcha_mandate.jpg` | 1190×595 | 167,248 | `77dc6bd7da79ed79448c849f6597298291cb33bf73653517604e76417071ea64` |
| 5 | Free Jingcha activity / 免费京察活动 | `cell/09_jingcha_activity_detail.png` | `c34f54b69898f8bf5a630226b86dfb185cf3acc2052faa0183d7f771e10123c1` | `720,120,2000,1200` | `media/05_free_jingcha_activity.jpg` | 1280×1080 | 302,381 | `784b2f2b3cb3c763990ea4133064600a2fb66e5602ef3dfa6c7429fc74b0f9d4` |
| 6 | Actual 3.25 outcome / 上司考定 3.25 | `cell/10_superior_result.png` | `93ecfad072711b6caa1759fefa267f492897e36b8ce14905230541a7f7eab46f` | `430,275,1605,885` | `media/06_superior_325_result.jpg` | 1175×610 | 162,398 | `58ac67ad919a93f279c0d21de53e1244d9e83b58071a910260c8c60b59f28bd1` |

Recommended captions (Chinese first) are:

1. `校准会：名单就在你手里，锅也在 / Calibration: the list—and the liability—is yours`
2. `名单冻结：3.75、3.5、3.25，先别急着开香槟 / Cohort frozen: 3.75, 3.5, 3.25—hold the champagne`
3. `考核榜：排名、KPI、价值观与档位全部上墙 / Scoreboard: rank, KPI, values and rating—on the wall`
4. `京察之期：免费，但不办会写进你的下一份考核 / Jingcha: free, but skipping it follows you into review`
5. `京察活动：原版活动界面里，费用明确为“无花费” / Jingcha activity: the native activity UI explicitly shows “no cost”`
6. `上司考定：3.25，KPI、名次与三重后果一次讲清 / Superior's rating: 3.25, with KPI, rank and consequences`

## Reproduction and integrity check

From the repository root, render the tracked projection without changing the
source artifact:

```powershell
& "tools\.venv\Scripts\python.exe" "mod_zhongguo_style\tools\compose_workshop_media.py"
& "tools\.venv\Scripts\python.exe" "mod_zhongguo_style\tools\compose_workshop_media.py" --check
```

The renderer pins all six source PNG hashes and rejects unexpected JPEGs in
`workshop/media/`. It does not delete, rewrite or move the external artifact.
If a future final GREEN run is intentionally adopted, update the six source
hashes, crop table, output hashes and this document together; do not claim an
old crop as current evidence.

## Publication handoff

When the Workshop BBCode is updated, first commit and push these JPEGs. Then
embed `raw.githubusercontent.com` URLs pinned to **that image-bearing commit**
(not a branch, blob page, redirect or release asset) in the follow-up BBCode
commit. Upload the six files in table order to the Steam media strip. Steam
CDN URLs and an on-page visual check belong in the later publication report.

This is not another gameplay test: it is a faithful crop/compression
projection of the accepted run. The separate final video still needs its own
clean gameplay footage; these stills are deliberately preserved as evidence
and may also serve as video cutaways.
