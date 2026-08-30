# ZhongGuo 361 Workshop Media

The eight tracked JPEGs are deterministic, presentation-only crops from one
final complete `GREEN` CK3 promo capture. They are real game captures, not
generated illustrations; the untouched PNG evidence and raw video remain at
the external artifact location below. Slots 1–2 explicitly show the corrected
strict first-cycle `7 / 14 / 2` distribution; slot 3 freezes that same corrected
cohort but crops the aggregate counters out of frame. Slots 7–8 show the real
#001 and #361 policy cards from the same run. The earlier `7 / 16 / 0` JPEGs
remain in Git history and external process artifacts only; they are **RED for
publication** and were not deleted.

The renderer binds slots 1–6 through frozen source/output hashes and slots 7–8
through `workshop/media-policy-lock.json`. Raw-to-JPEG reproduction requires
both report layers to be GREEN, the live
`bootstrap_first_review_strict_7_14_2` marker, and one matching artifact root
for all eight projections. Workshop JPEGs must not be put in the mod release
staging.

## Evidence source

- Artifact root: `Z:\ck3_mod_rewrite_process_assets\zg361\promo\captures\zga_20260830_0930_clean_2fa2ac8_mcp`
- Capture directory: `cell/`
- Acceptance result: `GREEN`, CK3 `1.19.0.6`, isolated userdir, 2560×1440
- Report SHA-256: `786b451b305fc5fccde3fa2650ed2969d6ef51941761d045cbd26249b8c493b1`
- Evidence-index SHA-256: `f22ecda2041bf3ed52f3f0109fb7e0860b23478c1fecb126e67242626442fd40`
- Timeline SHA-256: `02f39dc0cef2f62e558592f96e49cf38cc07b4e1487054364ac6854655497f3b`
- Raw-capture SHA-256: `4d85d5d38a9d89c230153efc66146a0c25afd23f0e50120795d7c82cf016ca67`
- Media policy-lock SHA-256: `1e48a487c0831abc2209d8c5934ab1cfc7292d9546554edd6d17f34c91c06b82`
- Renderer: `tools/compose_workshop_media.py`; Pillow JPEG quality 90,
  optimized progressive 4:4:4 (`subsampling=0`); each output is below
  Steam's 2,000,000-byte limit.

## Projections and upload order

| Order | Feature / 功能 | Acceptance source | Source SHA-256 | Crop `(left, top, right, bottom)` | Workshop JPEG | Dimensions | Bytes | Output SHA-256 |
|---:|---|---|---|---|---|---:|---:|---|
| 1 | Calibration meeting / 绩效校准会议 | `cell/06_calibration_event.png` | `d384bfe4b717892a7923613ac4f191856fdf4d85868927b71250dee4d86013b8` | `420,280,1610,875` | `media/01_calibration_meeting.jpg` | 1190×595 | 175,673 | `60c11f4407ef2e52496cdcbbea16a0e2abae016be572b003164d55d6967327f4` |
| 2 | Frozen review cohort / 冻结考核名单 | `cell/07_result_summary.png` | `bfeaf077634a057e00d18599c4b7825e7f7a2787990b4ca18221796b6dfd6406` | `430,275,1605,885` | `media/02_review_cohort_frozen.jpg` | 1175×610 | 194,850 | `b0f9467a933fc0ced16b44bc05d2cfe0e61bd9a1f7958d1090bf2197a2c93ef6` |
| 3 | 30/60/10 scoreboard / 天朝官员考核榜 | `cell/08_scoreboard_panel.png` | `8b10e6e1d8715a084091777200cf8e456748f66a9c087426badb683054535e37` | `430,130,1640,1020` | `media/03_scoreboard.jpg` | 1210×890 | 185,618 | `bd6b588e6a508a7b36cfb2d052efa4babfdbbde60fc0696f68e4c6a7ed18311c` |
| 4 | Semi-mandatory Jingcha / 京察之期 | `cell/09_jingcha_mandate_event.png` | `a158e9dd21503eddfea8a6df7f4268800e3bb5f725f3749651166668619d9eed` | `420,280,1610,875` | `media/04_jingcha_mandate.jpg` | 1190×595 | 177,396 | `6c2af19da15624eea28a82b359fb0dbc3e7029205e512da95b367aded4420634` |
| 5 | Free Jingcha activity / 免费京察活动 | `cell/09_jingcha_activity_detail.png` | `7cd1c532ab7bad63e6e4573687c975f29c2fb1bfb954cf815e76a172a99c8eb7` | `720,120,2000,1200` | `media/05_free_jingcha_activity.jpg` | 1280×1080 | 339,651 | `0f001de99c51d71d8f6ead09fa0989aec3b880e8cb399bec1e0614985d99c201` |
| 6 | Actual 3.25 outcome / 上司考定 3.25 | `cell/10_superior_result.png` | `1faf5ca71c6140aff2f1aeaf8d9662f0caf3d35cf2927199edfd0e7dafa6d435` | `430,275,1605,885` | `media/06_superior_325_result.jpg` | 1175×610 | 167,511 | `3a341668248ade6102d2a1e1b5c9ed07501ea352cf1798f14929a177b967f287` |
| 7 | KPI evidence policy / #001 KPI 分项证据单 | `cell/12_policy_001_event.png` | `19416e472a4983388b1e0106937cf046013a393958f6bd4654a0f0aca93d1720` | `420,280,1610,875` | `media/07_policy_001_kpi_evidence.jpg` | 1190×595 | 159,357 | `d992ce8f1c3d4004791f9509709283557dee39050cdc160f5be9519e6ca0a2a3` |
| 8 | Performance charter / #361 三六一绩效宪章 | `cell/12_policy_361_event.png` | `73b2929e1c3d3f2725a0c262dafcdbe4a35e0015526417698dfc91ae22c2465d` | `420,280,1610,875` | `media/08_policy_361_charter.jpg` | 1190×595 | 168,539 | `b7fb05cda6ee489a50982fb6acff1652b36127c112bbe6b70053e4a8c6d1ed45` |

Slots 7–8 are frozen in `workshop/media-policy-lock.json`, created only after
the complete promo run passed the report/index/timeline/MKV provenance
contract. The renderer rejects every output at 2,000,000 bytes or above.

Recommended captions (Chinese first) are:

1. `校准会：名单就在你手里，锅也在 / Calibration: the list—and the liability—is yours`
2. `刚性 361：23 人分成 7 个 3.75、14 个 3.5、2 个 3.25 / Strict 361: 23 officials become 7 / 14 / 2`
3. `考核榜：排名、KPI、价值观与档位全部上墙 / Scoreboard: rank, KPI, values and rating—on the wall`
4. `京察之期：免费，但不办会写进你的下一份考核 / Jingcha: free, but skipping it follows you into review`
5. `京察活动：原版活动界面里，费用明确为“无花费” / Jingcha activity: the native activity UI explicitly shows “no cost”`
6. `上司考定：画面明示 3.25、KPI 与名次；国库/金币/贤能/俸禄四重后果由同轮实机对账核验 / Superior result: 3.25, KPI and rank on screen; fourfold consequences verified in the same run`
7. `#001 KPI 分项证据单：年底打分之前，先把证据摊桌上 / #001 KPI evidence: put the receipts on the table before rating season`
8. `#361 三六一绩效宪章：开了三十年会，终于决定以后怎么开会 / #361 Performance Charter: after thirty years of meetings, rules for the next meeting`

## Reproduction and integrity check

From the repository root, render the tracked projection without changing the
source artifact:

```powershell
& "tools\.venv\Scripts\python.exe" "mod_zhongguo_style\tools\compose_workshop_media.py"
& "tools\.venv\Scripts\python.exe" "mod_zhongguo_style\tools\compose_workshop_media.py" --check
& "tools\.venv\Scripts\python.exe" "mod_zhongguo_style\tools\test_compose_workshop_media.py"
python mod_zhongguo_style/tools/compose_workshop_media.py --check-tracked
```

The renderer pins all eight source PNG and output JPEG hashes and rejects
unexpected JPEGs in `workshop/media/`. The `--check-tracked` form is the
CI-safe integrity check for machines that do not hold the external raw
artifact; it verifies the exact eight-file inventory, JPEG decoding,
dimensions, size limits and pinned output hashes. It does not replace the local
raw-to-JPEG reproduction check. Neither mode deletes, rewrites or moves the
external artifact. If a future final GREEN run is intentionally adopted,
update the default artifact, all source/output hashes, policy lock and this
document together; do not mix captures from different runs.

For a future replacement capture, create the policy lock beside the preserved
capture first. This validates the root/cell reports, evidence index, timeline
marks, raw MKV, all six captured policy cards, and exact source hashes before
it writes any lock. It does not write JPEGs:

```powershell
$capture = "Z:\ck3_mod_rewrite_process_assets\zg361\promo\captures\<final-green-run>"
$lock = "$capture\release\workshop-media-policy-lock.json"

& "tools\.venv\Scripts\python.exe" "mod_zhongguo_style\tools\compose_workshop_media.py" `
  --artifacts $capture --create-policy-lock $lock

& "tools\.venv\Scripts\python.exe" "mod_zhongguo_style\tools\compose_workshop_media.py" `
  --artifacts $capture --policy-lock $lock --policy-cards-only `
  --output "$capture\release\workshop-media-preview"
```

Visually inspect the two preview JPEGs, retain that external lock and preview,
then adopt the reviewed lock as `workshop/media-policy-lock.json` together with
the same run's `DEFAULT_ARTIFACTS` path and updated six base-image pins. A
default render/check expects all eight files; `--check-tracked` consumes the
committed lock without needing the external artifact. A lock from any other
artifact root is rejected during raw-to-JPEG reproduction.

## Publication handoff

When the Workshop BBCode is updated, first commit and push these JPEGs. Then
embed `raw.githubusercontent.com` URLs pinned to **that image-bearing commit**
(not a branch, blob page, redirect or release asset) in the follow-up BBCode
commit. Upload the final eight files in table order to the Steam media strip. Steam
CDN URLs and an on-page visual check belong in the later publication report.

This is not another gameplay test: it is a faithful crop/compression
projection of the accepted run. The separate final video still needs its own
clean gameplay footage; these stills are deliberately preserved as evidence
and may also serve as video cutaways.
