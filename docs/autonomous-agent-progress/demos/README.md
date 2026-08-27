# Show-off 视频规范与索引

本目录维护自动游玩智能体月报与阶段里程碑的演示索引。视频用于直观展示真实能力，但不能替代 exact-build ABI、
production live artifact 或测试报告。日报和周报只要求文字，不再有固定视频交付。

## 硬性标准

- 每个自然月 27 日 00:00（Asia/Shanghai）必须为当月月报产出一条完整能力 show-off 视频。
- 英语为主叙事和主要视觉层级，简体中文作为画面内副标题/字幕。
- 开场卡、阶段切换、游戏过程 lower-third、最终证据卡都必须中英双语；不能只在 Markdown 里另附中文。
- 中文字幕优先在句号、分号、冒号、逗号及语义短语边界断句，并在合成时按字体、字号与安全区测量实际渲染宽度；一条字幕
  可分成多行，但任何一行都不得越出安全区、被裁切或覆盖关键证据。仅凭字符数估算不能代替成片抽帧检查。
- 能展示实机就展示实机。不能用 schema、ACK、单元测试输出或预录鼠标宏冒充“观察 → 决策 → 操作 → 验证”。
- 最终卡必须显示与视频对应的关键 live evidence；能力边界也必须在视频或配套手册中说明。
- 成片必须完成可解码、时长、分辨率、帧率、中文渲染、字幕安全区、关键场景入镜和结尾证据卡抽检。

## 文件与元数据

大体积视频不进入 Git，默认保存在：

```text
artifacts/demos/YYYY-MM-DD/
```

月报至少记录：

| 字段 | 要求 |
|---|---|
| video path | 本机绝对路径或仓库相对路径 |
| size / SHA-256 | 精确字节数与完整哈希 |
| duration / geometry | 时长、宽高、帧率 |
| codec / audio | 视频与音频编码；无解说时明确 silent track |
| language | `English primary + Simplified Chinese subtitles` |
| live artifact | 与本次录制同一 run 的路径、SHA、GREEN/RED |
| honest boundary | fixture/production、是否选择、尚未闭合能力 |

录制器、字幕模板和验证脚本属于可复现基础设施，应提交进仓库。生成的 MP4、artifact 和 sidecar 留在 `artifacts/`，
由报告记录其路径与哈希。

## 旁白合成

- 后续 show-off 视频构建固定使用 `edge-tts==7.2.8`，默认英语女声为 `en-GB-SoniaNeural`；manifest 的
  `voice` 字段和命令行 `--voice` 均表示 Edge voice short name。不再提供 Windows SAPI fallback。
- 无可用缓存的 clean synthesis 需要联网访问 Edge 语音服务；已有通过指纹和媒体验证的逐章缓存可直接复用。
  `--force` 会跳过缓存并重新合成，因此同样需要联网。
- 上述迁移只影响未来构建。2026-08 canonical 月报成片仍使用 Windows SAPI / `Microsoft David Desktop`；
  不重制该历史成片，其路径、时长和 SHA-256 保持不变。历史 manifest 冻结在提交 `be7fc8b`，SHA-256 为
  `BFC4F38B3F47882888EB7B5AE754CD67125D8CE81D4BAA2649C302D688A72B32`；仓库当前同名 manifest 已切换为
  后续 Edge TTS 构建输入，不能拿它替代历史 sidecar 记录的冻结字节。

## 月报节奏

- 月报视频不是最后一天录像的简单复制；它必须盘点截至当月截止时仍然成立的全部能力，并逐项显示证据等级与未闭合边界。
- 日报、周报及阶段性录像可复用为月报素材，但月报必须形成独立成片、独立 sidecar、完整哈希和当月媒体抽检结果。
- 日报和周报无需视频；是否存在可选阶段录像不影响它们完成或收口。
- 新视频取代失败或语言不合规版本后，报告只把通过抽检的版本列为 canonical；废弃版本不得继续被称为最终成片。

## 当前索引

| 日期/周期 | 类型 | 手册 | 状态 |
|---|---|---|---|
| 2026-08 | 月报 | [完整能力月报](../monthly/2026-08.md) / [成片 storyboard](2026-08-27-full-capability-showcase-storyboard.md) | canonical 重制版已通过字幕安全区、媒体与内容抽检 |
| 2026-08-27 | 历史阶段素材 | [原生事件窗口读取](2026-08-27-event-window.md) | 双语阶段成片已通过抽检；不是日报必需品，也不是 2026-08 正式月报成片 |
