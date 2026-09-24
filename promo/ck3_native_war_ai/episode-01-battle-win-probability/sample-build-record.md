# 第 1 集 EdgeTTS 样片制作记录

2026-09-24 的第一版视听样片对应[导演案](director-plan.md)、[七段旁白](sample-script.json)及[镜头表](sample-timeline.json)。它完整回答“战前力量比较为什么不是整场胜率”这一窄问题；不是已完成的整场胜率正片，也不包含一个已校准的整场百分比。

| 项 | 本次绑定 |
| --- | --- |
| 输出 | `CK3-War-AI-Episode-1-EdgeTTS-Sample-20260924.mp4`，260.255 秒，2560×1440、30 fps、48 kHz 立体声，28,171,782 bytes；SHA-256 `2b315750846be997e8c6c00792fc09f26f83ea1de5d19ff69c6b4ce424a2d583` |
| 旁白 | EdgeTTS `zh-CN-XiaoxiaoNeural`，`-12%`；七段逐 cue 请求、返回音频、时间边界和重试记录保存在本次 run 的 speech process archive；无人工配音签核 |
| 配乐 | 唯一母版 `Quiet Courtly Tension.wav`，SHA-256 `fda2464fb4b06cd9a2f0196e5c40ca311eb693ec263c996e4ccc24a6ada8803f`；旁白 0 dB、音乐固定 -17 dB，首 2 秒淡入、尾 8 秒淡出，无 ducking 或自动归一化 |
| 实机画面 | 开场 32.77 秒取自此前保留的 CASE-W 原版 CK3 战时观察 `V3-22`，已在画面和口播中注明为**另一场战争的情境**；不能据此证明 R0220 的同步战斗画面或 AI 决策因果。后续为有出处的教学卡。 |
| 原版事实 | [战斗结算研究](../../../docs/ck3-native-ai/battle-simulation.md)中的预测器/逐日结算分离，以及 R0220 **一个**主阶段 tick 的 54 行兵团伤亡零差；不把它扩大为 54 场战斗或整场终局对拍。 |
| 工具链 | 官方最新正式 `xar-promo` v0.2.1 wheel；发布 SHA-256 `f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621`。使用 `start-run`、`preserve`、只读 `plan`、`build`、`validate` 和 `review`。 |
| run | `D:\workspace\ck3_native_war_ai_promo_work\episode01-edge-sample-attempt-001\run\run-manifest.json`。源配置、composer、EdgeTTS 音频、原始上下文片段、主题曲、最终 MP4、技术回执、审阅包和 OneDrive 回读均以 SHA 保存在 run；全部中间过程留在同一 attempt 目录。 |
| 验证 | native build 成功；最终片全流解码通过；精确音频混合回执、bound probe、24 帧选择性审阅包及 OneDrive 客户端活动回读均已保存。该审阅包是 `pending-human-review`，不代表已按 1× 完整观看或人工签核。 |
| 交付 | 仅把这一 MP4 复制到既有 OneDrive 客户端固定同步目录 `C:\Users\1\OneDrive\CK3-War-AI-20260923`；本地目标 SHA 与源文件一致，客户端活动中心回读为“已上传到 CK3-War-AI-20260923”。未更改 OneDrive 同步规则，未调用云端下载。 |

本样片的判断范围：预测比例不等于整场胜率；R0220 的零差仅支持该日数值对拍。下一阶段仍须补同一 CombatID 从战前到终局的 trace 与画面、非空事件反馈、动态增援/退出/撤退以及跨战例校准，之后才可按导演案报出整场胜率百分比。
