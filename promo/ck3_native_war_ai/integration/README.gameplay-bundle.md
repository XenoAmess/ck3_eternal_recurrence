# 暂停地图 gameplay bundle 的项目封装器

`package_gameplay_bundle.py` 是本项目的新 producer，不是旧 acceptance runner，不修改 `xar-promo` CK3 adapter。
它只消费完成的真实录制与显式审帧记录，不启动 CK3、不操作桌面、不推断画面、不签发人工 approval。
原录像 attempt、失败记录和旧审阅资产均保持原样；输出目录必须不存在。

当前用途为 CASE-R 暂停地图与原生读回。其 `GREEN` 只表示已完成录制、前置 HUD 证据、实际端点审帧、
前台采样与暂停状态读回满足此 producer 的合同；不能写成自然 AI 宣战或其他策略因果已证实。
前台监测约两秒一次，存在采样间隙；两个端点不是完整录像的连续视觉审看，也不是人工 1× 全片签核。

## 先提取，再真实审帧，再封装

所有命令使用本 worktree 已验证的 `tools/.venv`。以下路径是新 attempt 的示例，不表示已经执行或通过。
`--end-seconds` 是排他的媒体时间；范围须位于实际 probe 时长内。首末帧按实际解码 PTS 选择，
不能把 `r_frame_rate` 或 `avg_frame_rate` 等于 30 当成一秒实际存在 30 个帧。
下面只选择录像中的 5–115 秒，不能因为原计划为 120 秒而假定它实际录满。

```text
tools\.venv\Scripts\python.exe -B promo/ck3_native_war_ai/integration/package_gameplay_bundle.py extract-frames --recording-dir D:/workspace/ck3_war_film_research_20260923/robert-input-case-r1 --begin-seconds 5 --end-seconds 115 --output D:/workspace/ck3_war_film_research_20260923/robert-case-r-frames-NEW
```

这一步要求原目录已有成功的 `recording-result.json`、`ffprobe.json`、前台采样、前后截图、
前置 HUD 审看证据、StartGame 后置与暂停 snapshot。它校验 raw bytes/SHA，解码一次真实 frame timestamps，
再按实际 PTS 真正调用 FFmpeg 提取
`begin.png` 与 `end.png`，保留 argv、stdout、stderr、partial 与 `extraction.json`。
结果永远是 `pending-agent-image-review`，不会生成 GREEN bundle。
首图取 begin 之后（含边界）实际存在的第一帧，末图取排他 end 之前实际存在的最后一帧；
输出记录实际 PTS、time base、decoded index 与请求范围，不能把稀疏帧的序号乘除元数据 FPS 来假造时间。
没有生成 PNG 时，即使 FFmpeg 退出码为 0 也明确报错，保留命令与 stderr，不再落入模糊的 Image.open 异常。

可先独立探测，再通过 `--frame-probe` 精确绑定并复用同一结果，避免重复解码：

```text
tools\.venv\Scripts\python.exe -B promo/ck3_native_war_ai/integration/package_gameplay_bundle.py probe-frames --raw D:/workspace/ck3_war_film_research_20260923/robert-input-case-r1/gameplay.mkv --output D:/workspace/ck3_war_film_research_20260923/robert-case-r-timing-NEW
tools\.venv\Scripts\python.exe -B promo/ck3_native_war_ai/integration/package_gameplay_bundle.py extract-frames --recording-dir D:/workspace/ck3_war_film_research_20260923/robert-input-case-r1 --begin-seconds 5 --end-seconds 115 --frame-probe D:/workspace/ck3_war_film_research_20260923/robert-case-r-timing-NEW/frame-timestamps.json --output D:/workspace/ck3_war_film_research_20260923/robert-case-r-frames-NEW
```

稀疏 PTS 的原片仍可提取真实审阅图，但 `capture_media_compatible=false`，当前封装步骤拒绝把它交给连续
30 fps 的导入合同。不得补帧、复制重复帧、定格、重定时或拉伸以制造通过结果。

2026-09-23 首次真实取材发现：`robert-input-case-r1/gameplay.mkv` 虽标 120 秒、r/avg 均 30，
实际只解码出 1,077 帧（不是 3,600），相邻 PTS 最大间隔 0.2 秒。
旧 `robert-case-r-frames-r1` 的 begin 以 n=150 提取，实际是 17.233 秒；其 end 试图选择不存在的 n=3449。
该 RED attempt 与 begin 图保持原样，不能继续按 5 秒解释。
真实探测证据在外置 `robert-case-r-frame-timing-r1/frame-timestamps.json`，其 [5,115) 首末实际帧为
5.067 秒与 114.967 秒；本次修复不重新解释或修复旧 attempt。

后续录制先只保留一个桌面 recorder，并先做短录，检查实际解码计数、PTS 间隔与编码吞吐后再录正式片段。
并发双录是负载线索，当前时间戳不能证明它是唯一原因。若仍达不到真实连续 30 fps，应改善捕获/编码路径，
或明确另立保留 VFR 时序的导入合同；不能仅加 CFR 输出选项让 FFmpeg 重复帧后宣称已经解决。

实际调用图像查看工具看过这两张 PNG 后，由实际审看者写独立 review JSON。
`reviewer.kind=agent` 诚实标明本次是代理图像审看，不冒充用户或人工签核。
所有 binding 为完整绝对路径、文件字节数与完整 SHA256。`extraction` 和 `frames[].image` 直接取真实提取回执中的值。
下例带占位值，不能直接执行，更不能把未看过的图填成 true：

```json
{
  "schema": "ck3-war-ai.gameplay-frame-review.v1",
  "reviewer": {"kind": "agent", "id": "/root"},
  "reviewed_at_utc": "ACTUAL_TIME_WITH_TIMEZONE",
  "review_scope": "endpoint-images-and-sampled-foreground",
  "span_id": "case-r-paused-map",
  "native_ai_causality_verified": false,
  "human_1x_review_performed": false,
  "signoff_granted": false,
  "frame_synchronous_query_proven": false,
  "continuous_visual_review_performed": false,
  "extraction": {"path": "ABSOLUTE_EXTRACTION_JSON", "bytes": 0, "sha256": "ACTUAL_SHA256"},
  "frames": [
    {
      "phase": "begin",
      "image": {"path": "ABSOLUTE_BEGIN_PNG", "bytes": 0, "sha256": "ACTUAL_SHA256"},
      "observations": {"gameplay_hud": true, "paused_map": true, "no_loading": true, "no_foreign_overlay": true},
      "notes": "这里只填写实际看见的内容；若某项不成立，不生成通过记录。"
    },
    {
      "phase": "end",
      "image": {"path": "ABSOLUTE_END_PNG", "bytes": 0, "sha256": "ACTUAL_SHA256"},
      "observations": {"gameplay_hud": true, "paused_map": true, "no_loading": true, "no_foreign_overlay": true},
      "notes": "这里只填写实际看见的内容。"
    }
  ],
  "native_readback": {
    "association": "same-paused-state-not-frame-synchronized",
    "snapshot_after": {"path": "ABSOLUTE_POST_RECORDING_SNAPSHOT", "bytes": 0, "sha256": "ACTUAL_SHA256"},
    "queries": [{"path": "ABSOLUTE_NATIVE_QUERY_RESPONSE", "bytes": 0, "sha256": "ACTUAL_SHA256"}],
    "notes": "说明读回与暂停场景的真实关系；不把同游戏日期写成同一媒体帧。"
  }
}
```

原生 snapshot/query 使用现有 `{at, result: "CALL_COMPLETED", body: {...}}` MCP 回执。
`snapshot_after` 必须在录像完成后取得，并与录像前 actor/date 相同、`paused/map_ready=true`、匹配原生 bridge build。
查询文件保全实际 payload；这里只验证调用完成与回执时间，不代替具体查询的研究解释。
每个 query 根据真实 `at` 标明录制前、录制墙钟窗口内或录制后。当前 producer 不支持宣称严格同帧同步；
如后续要作同步因果实验，应使用具备该真实证据的新 producer，不得把此字段直接改成 true。

```text
tools\.venv\Scripts\python.exe -B promo/ck3_native_war_ai/integration/package_gameplay_bundle.py package --recording-dir D:/workspace/ck3_war_film_research_20260923/robert-input-case-r1 --review-json D:/workspace/ck3_war_film_research_20260923/robert-case-r-review-NEW.json --producer-script D:/workspace/ck3_war_record_case_r1_20260923.py --output D:/workspace/ck3_war_film_research_20260923/robert-case-r-bundle-NEW
```

额外非绑定材料可重复传 `--evidence ABSOLUTE_PATH`。封装器复制原录制目录所有文件、审看记录、
真实录制脚本、封装器实现及 JSON 中显式 path/bytes/SHA 绑定的引用（包括抽帧审计和 native 请求）。
原始 JSON 字节不改写；`producer-evidence.json` 保存 original → preserved 对照，避免旧绝对路径失去出处。
新 report/timeline/frame gate 的实际引用全部落在新 bundle 内，按真实复制结果生成 SHA。

输出包括 `report.json`、`cell/promo/capture-timeline.json`、`evidence-index.json` 和 `bundle-receipt.json`。
最后真正调用 `xar_promo.adapters.ck3.load_capture_bundle` 验证；没有通过调用就不返回已验证收据。
检查失败不修旧 attempt，部分输出和 `failure.json` 保留，重试使用新目录。
adapter 要求的 `recording_stop_requested` 在此 producer 明确表示成功完成限时录制后的实际媒体末端，
不伪称有人按了停止；`clean_capture_complete` 仅限选定的这一段及声明的采样/端点合同。

经验证后，可将新 bundle 与 `case-r-paused-map` span 交给既有 `capture_media` / `--capture-spec`。
其 `evidence_role` 仍只是剪辑标签；本 CASE-R 素材适合地图背景及读回说明，不能独立充当自然 AI 因果镜头。
