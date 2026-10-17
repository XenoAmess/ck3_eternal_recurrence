# R198 military toggle 原片离线媒体审计

- 审查机器：`machine_id: desktop-3fevhd2-1c74096080`，实际审查时间 2026-10-17 11:44 UTC。来源身份锁定 `R198-IDENTITY-SCOPE.actual.json`（8794 B，SHA-256 `47824977b62b390534f375924190daa1abe133d417d2ee3c1beeeb0466a3af77`）；录制 finish 原 packet（5288 B，SHA-256 `43a1a656b4ab89f1912b5bc3bc43cbc1a42a4b1a65a3f3a5eb2e7b20d3347a5e`）。
- 原片由 finish packet 的 `body.raw.path` 读取：`D:/workspace/ck3_native_war_ai_promo_work/e04-r198-military-toggle-a01/raw-r198-military-a01/raw.mkv`，32,908,524 B；finish 已完成的 SHA-256 为 `73ba63f6a249addf7ced95d54001f7b338e4be091bd5bb90491cab627eb62472`。本审查未重复哈希或复制原片。finish 报告 `NORMAL_TREE_EMPTY`、`capture_guard_error: null`、`partial_assets_retained: true`、`clean_spans_certified: false`。
- 使用 scope 中确切 FFmpeg 路径，实际 SHA-256 复核为 `57c56e369d5b4873b4d93fc1a1d833cb7cd8bc9325c14b05c34ce60b22842d8a`。同分发版 ffprobe 读回 57.266 秒、1280×720、30 fps、H.264、单视频流、无音频流。一次全视频解码加 showinfo PTS 得 1718 帧，编号 0–1717，PTS 0.000–57.233 秒；所有 PTS 严格递增，相邻差为 33 ms（1145 次）或 34 ms（572 次），解码退出码 0。没有音轨可解码。

## 画面及转场

最多 8 张原尺寸选帧已用满，见 [asset-manifest.json](asset-manifest.json) 的逐文件 SHA-256。0 秒是 CK3 地图；20 秒军事面板正在淡入；30 秒右下“每月补员”勾选；39、42、45、50、56 秒均为未勾选。八帧均显示 1280×720 客户端画面，未见桌面边框或外部窗口。游戏日期保持公元 1067 年 2 月 23 日，并显示暂停。

对 28–41 秒仅做 24×24 checkbox ROI 的短程解码与 framemd5：局部 0–248 帧为勾选态，249 帧为单帧中间态，250 帧起为未勾选态。28 秒 seek 的首帧全图 checksum 与全片解码的第 840 帧完全一致，因此转场映射到原片第 1088 帧 / PTS 36.267 秒仍勾选，第 1089 帧 / 36.300 秒为中间态，第 1090 帧 / 36.333 秒起未勾选。原生 [MILITARY-TAKE.actual.json](../e04-r198-military-toggle-a01/research-film-a01/MILITARY-TAKE.actual.json)（SHA-256 `c52f9ddec07775e95357a547814ebd47dcb44bca7860bb50aa9c3f2973e529a3`）独立记录 owner 31254 的 raw 4A9 从 1 到 0、`verified_desired`、两次 hold 15/20 秒，日期未推进。该回执的 wall/monotonic 时间只用于搜索定位，没有充当视频 PTS。

## C02-09 候选及资格

可交给 composer 的连续编码帧候选为半开区间 **`source_frames: [780,1675)`**，恰好 **895 帧 / 29.833333 秒**，首帧 PTS 26.000 秒，末帧第 1674 帧 PTS 55.800 秒；容纳窗口 `[780,1680)` 有 900 帧，对应约 `[26,56)` 秒。此窗口包含前态、精确 checkbox 转场和后态，首端在军事面板淡入结束之后。第 26–56 秒的面板边缘 ROI 仍出现 5 段像素变化；这些数据与稀疏全图选帧只支持**连续可解码、局部可读的候选**，不能认证整段无遮挡、逐帧 clean。连续 clean 审核仍为 `PENDING`。

基础媒体可解码性和玩家画面上的 checkbox 前后态有证据；**人工 1×、human signoff 均为 false**。owner 31254 的玩家操作演示不能外推为封臣 AI 实测或业务正例。该片也没有自然日期推进。

本包全部写在新外置 lane，逐文件身份见 manifest；无主仓或 canonical 路径更改。派生物按通用存储策略在 2026-10-19 11:44 UTC 复核，原片后续保留由原场次 owner 判断。
