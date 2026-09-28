# 第 2 集外置录像到 CK3 adapter 的两阶段封装

2026-09-28 核验独立仓库最新正式 Release 为 `xar-promo-toolchain v0.2.1`，wheel SHA-256 为
`F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`；主 worktree
`D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe` 实际报告 `xar-promo 0.2.1`，
顶层、`start-run`、`validate` 帮助已核。本 secondary worktree 没有自己的 `.venv`；下列命令
显式使用该解释器，`prepare` 清单记录本次 wheel URL、SHA 与版本。若未来有新正式版，先遵守
`AGENTS.md` 更新 wheel pin 和环境再开新 attempt。

现有受管会话的 `ck3-output/capture-report.json` 是
`ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO`。外部 `recording-*/recorder-final.json` 即使是
`ENCODED_UNREVIEWED`，仍不能直接成为 adapter GREEN；`marks.jsonl` 的
`approx_seconds_from_recorder_start` 是墙钟导航，不是原始视频 PTS。
[`prepare_existing_capture_bundle.py`](prepare_existing_capture_bundle.py) 分两阶段，只创建新外置目录；
旧 attempt、原 capture report、原 raw、旧失败记录均不修改。

## 阶段一：原件清单

在受管 CK3 录制结束、screen lease 释放后，为**每条** raw 分别运行。`--output` 必须是尚不存在、
位于旧 attempt 之外的新目录：

```text
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe promo/ck3_native_war_ai/episode-02-battle-second-half/prepare_existing_capture_bundle.py prepare --attempt D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-pair-20260928-a05-live --recorder D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-pair-20260928-a05-live/recording-e2-09-terminal-a02 --output D:/workspace/ck3_native_war_ai_promo_work/episode02-a05-a02-adapter-pending-NEW
```

工具逐字节复核原 raw、完整 ffprobe、marks、会话报告、控制回执及截图的 byte/SHA，生成
`source-manifest.json`。状态固定为 `PENDING_CLEAN_REVIEW`，`adapter_eligible=false`，
`media_pts_seconds=null`；没有 `report.json`、timeline、evidence index。它既不复制 GB 级原片，
也不解码、抽帧、签核。若原件被改写、尚未封口或混入另一 attempt，拒绝建立清单。

## 阶段二：真实审帧后生成正式 bundle

审阅者需先按原速完整看该条 raw，并对**每个**拟用区间审阅精确首末媒体 PTS 帧及连续画面。
用同一脚本的 `extract-frame` 从完整 ffprobe 选**真实存在的 PTS**，生成 PNG、FFmpeg 原始
stdout/stderr、命令和 `EXTRACTED_UNREVIEWED` 回执。首末帧各开一个新目录；此命令会解码
原 raw，须在录制结束后执行：

```text
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe promo/ck3_native_war_ai/episode-02-battle-second-half/prepare_existing_capture_bundle.py extract-frame --source-manifest D:/workspace/ck3_native_war_ai_promo_work/episode02-a05-a02-adapter-pending-NEW/source-manifest.json --pts-seconds EXACT_EXISTING_FRAME_PTS --output D:/workspace/ck3_native_war_ai_promo_work/episode02-a05-a02-begin-frame-NEW
```

抽帧器用 `select=eq(n\,INDEX),showinfo`，将 FFmpeg 实际解码 PTS 与原 ffprobe 精确比对；
不匹配则保留 RED attempt，不交付可审图。其回执结构为：

```json
{
  "result": "EXTRACTED_UNREVIEWED",
  "raw": {"path": "ABSOLUTE_ORIGINAL_RAW", "bytes": 0, "sha256": "64_HEX"},
  "image": {"path": "ABSOLUTE_EXTRACTED_PNG", "bytes": 0, "sha256": "64_HEX"},
  "pts_seconds": "EXACT_FFPROBE_FRAME_PTS",
  "decoded_index": 0,
  "ffprobe": {"path": "ABSOLUTE_ORIGINAL_FFPROBE", "bytes": 0, "sha256": "64_HEX"},
  "command": {"path": "ABSOLUTE_EXTRACT_COMMAND_JSON", "bytes": 0, "sha256": "64_HEX"},
  "stdout": {"path": "ABSOLUTE_FFMPEG_STDOUT", "bytes": 0, "sha256": "64_HEX"},
  "stderr": {"path": "ABSOLUTE_FFMPEG_STDERR", "bytes": 0, "sha256": "64_HEX"},
  "human_review_performed": false
}
```

该回执必须记录实际抽出的帧 PTS，不能用墙钟 mark、帧序号÷30 或标称 fps 猜测。阶段二重核
原 session/recorder 清单关系、抽帧命令所选 raw/帧号、原始 FFmpeg `showinfo` PTS、区间内最大相邻
PTS gap ≤0.2 秒；它不会解码画面或替人审片。A05 a02 的 271.267–278.833 秒 gap 为 7.566 秒，
跨它的候选必拒。

审阅者另立不可变 `human-review.json`，字段为：

```json
{
  "schema": "xar.war-promo.exact-span-human-review/v1",
  "reviewer": {"kind": "human", "id": "ACTUAL_REVIEWER"},
  "reviewed_at_utc": "ACTUAL_TIMESTAMP_WITH_TIMEZONE",
  "review_scope": "full_raw_1x_and_exact_span_endpoints",
  "human_1x_full_raw_review_performed": true,
  "gameplay_hud_visible_at_recording_start": true,
  "loading_excluded_from_selected_spans": true,
  "source_manifest": {"path": "ABSOLUTE_PENDING_SOURCE_MANIFEST", "bytes": 0, "sha256": "64_HEX"},
  "raw": {"path": "ABSOLUTE_ORIGINAL_RAW", "bytes": 0, "sha256": "64_HEX"},
  "spans": [{
    "span_id": "ACTUAL_UNIQUE_SPAN_ID",
    "begin_pts_seconds": "EXACT_FIRST_FRAME_PTS",
    "end_pts_seconds": "EXACT_LAST_FRAME_PTS",
    "continuous_visual_review_performed": true,
    "source_identity_visible_and_checked": true,
    "no_foreign_overlay": true,
    "begin_frame": {
      "pts_seconds": "EXACT_FIRST_FRAME_PTS",
      "image": {"path": "ABSOLUTE_BEGIN_PNG", "bytes": 0, "sha256": "64_HEX"},
      "extraction_receipt": {"path": "ABSOLUTE_BEGIN_EXTRACTION_JSON", "bytes": 0, "sha256": "64_HEX"},
      "reviewed_at_1x": true, "gameplay_hud": true,
      "source_identity_visible": true, "no_loading": true
    },
    "end_frame": {
      "pts_seconds": "EXACT_LAST_FRAME_PTS",
      "image": {"path": "ABSOLUTE_END_PNG", "bytes": 0, "sha256": "64_HEX"},
      "extraction_receipt": {"path": "ABSOLUTE_END_EXTRACTION_JSON", "bytes": 0, "sha256": "64_HEX"},
      "reviewed_at_1x": true, "gameplay_hud": true,
      "source_identity_visible": true, "no_loading": true
    }
  }]
}
```

模板中的布尔值是**待实际审阅后填写的要求**，不能复制模板当作审阅记录。
对每条 raw 使用新目录独立封装：

```text
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe promo/ck3_native_war_ai/episode-02-battle-second-half/prepare_existing_capture_bundle.py package --source-manifest D:/workspace/ck3_native_war_ai_promo_work/episode02-a05-a02-adapter-pending-NEW/source-manifest.json --human-review D:/workspace/ck3_native_war_ai_promo_work/REVIEW-NEW.json --output D:/workspace/ck3_native_war_ai_promo_work/episode02-a05-a02-adapter-bundle-NEW
```

封装器复制原 raw 和绑定证据到新 bundle，生成 adapter 标准 `report.json`、
`cell/promo/capture-timeline.json`、`evidence-index.json` 及逐端点 gate，然后**实际调用**
`xar_promo.adapters.ck3.load_capture_bundle(...).verify_unchanged()`。只在这一步成功后写
`bundle-receipt.json`；失败保留新目录及 `failure.json`，重试另开目录。adapter GREEN 仅覆盖
这份 human review **声称**已审过的所选 spans；工具只能核其时间和文件绑定，不能观察人是否
真的全程观看。它不把旧 no-video report 改写为 GREEN，也不代表成片已按 1× 完整观看或签核。
新 bundle 中 adapter 消费的媒体与证据文件齐备，但复制的来源清单和审阅回执仍含原 attempt
的绝对路径；完整来源追溯仍需保留旧 attempt。成片重新编码后须对精确成片 bytes 单独人工签核。

轻量夹具测试：

```text
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe promo/ck3_native_war_ai/episode-02-battle-second-half/test_prepare_existing_capture_bundle.py
```
