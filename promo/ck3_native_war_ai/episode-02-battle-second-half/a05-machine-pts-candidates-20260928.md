# E2-09 A05 原始录像 PTS 候选窗

2026-09-28，只读机器筛选。逐帧原件汇总为 `D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-pair-a05-pts-audit-20260928-a02.json`，9434 bytes，SHA-256 `4AA962EACFF774CA910FB2E8E5230B7282816334A15085B165A9CA06CDBF64BC`。本轮新外置回执 `D:/ck3-research-artifacts/episode02-a05-pts-span-verification-20260928/attempt-03/a05-pts-span-candidates.json`，SHA-256 `98BD4FE38B87EBC0596744303E2A4A8921E5E6AD09F0FB7D4AE8979E532D9897`，状态为 **`PTS_CANDIDATES_ONLY_NOT_CLEAN_SPANS`**。代码从 `recorder-final.json` 校验原始 raw/完整 ffprobe 的 bytes/SHA 与帧数、首尾 PTS；重用上轮已核 raw SHA 并再核当前字节数，未另读数 GB raw。

| 独立 raw | 候选精确 PTS 秒 | 导航标记 | 本轮逐帧最大 gap | 下一步 |
| --- | ---: | --- | ---: | --- |
| `recording-e2-09-terminal-a01` | 245–270 | WarID4 前态约 256.967 | 0.067 s | 审面板完整性与来源标签 |
| 同上 | 350–450 | 第 27 日约 367.667、第 28 日约 435.333 | 0.067 s | 审日期/战斗 UI 与遮挡 |
| `recording-e2-09-terminal-a02` | 60–170 | 第 28 日约 73.467、第 29 日约 154.133 | 0.067 s | 审跨日画面与控制回执 |
| 同上 | 200–250 | 第 30 日约 226.200 | 0.067 s | 审原生日期锚 |
| 同上 | 300–350 | 第 31 日约 328.900 | 0.067 s | 审 gap 后单独段 |
| 同上 | 385–500 | writer 约 397.333、WarID4 后态约 487.700 | 0.100 s | 审同段终局/后态、报告与可见性 |
| 同上 | **250–300：拒绝** | 跨 day30/day31 的 raw 缺帧 | **7.566 s** | 禁止认证为一段 clean span |

这些是取帧搜索窗，不是已认证的剪辑边界。a02 还有 37.933–38.700 秒的 0.767 秒 gap 和 179.600–180.067 秒的 0.467 秒 gap，故不能从整条 `ENCODED_UNREVIEWED` 推断连续；未来每个 clean span 须按**自身**精确 begin/end 重算全帧 PTS。mark 的墙钟秒与最近视频 PTS 只用于导航，不能直接成为 clean 边界。a01 原始 raw SHA `C2E3AB8B0E60171316DD445B999B95E91227211666FE78CCF797F733AFDA315B`，a02 原始 raw SHA `25A13691259215848D77EAAB8AED9C0E281AF59A8AEB126E5D726EC6FE73A9BC`；各自原始分辨率均为 1920×1080，未来 2560×1440 reel 必须明示上采样。

正式 adapter 准入还缺同 attempt GREEN `report.json` / timeline / evidence index、所选 exact PTS clean span 和每段源身份可见标签的保全帧。建议 reel 在画面上标 `E2-09 · <最终 clean attempt_id> · A05 当前回放 · PTS <begin–end>`，实际字幕与标签审计绑定 reel SHA、原 raw SHA、帧位置和帧 bytes/SHA；不同 a01/a02 要分别标。此处的录像标识只是暂用名，不能替代最终 clean receipt 中的 `attempt_id`。历史 `024` 的 `-50` 卡若上屏，只能显式写“历史研究 024／非当前录制”；不能成为 A05 writer 数值或画面的实时证据。人工 1× 完整审阅、来源标签截图和终局数值投影仍待完成。
