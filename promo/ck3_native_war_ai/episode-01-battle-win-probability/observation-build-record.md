# 第 1 集 EdgeTTS 观察版交付记录

2026-09-25 按用户调整后的范围，先用现有已确认的原生机制完成一部 20–40 分钟的完整**审片候选**，再继续研究整场预测。题目为《十字军之王3：一场仗是怎么算出来的》。本版按原版结算顺序解释参战身份、地形与战宽、有效属性、优势和主战伤害、定点截断、逐兵团伤亡、骑士事件以及下一日状态；不发布未校准的整场胜率百分比。准确性边界见[导演案](director-plan.md)、[脚本](full-film-script.json)与 [`docs/ck3-native-ai`](../../../docs/ck3-native-ai/battle-simulation.md)。

## 成片身份与传输

- 本地最终文件：`D:\workspace\ck3_native_war_ai_promo_work\episode01-observation-film-attempt-003\CK3-War-AI-Episode-1-Observation-EdgeTTS-20260925.mp4`。
- SHA-256：`19506F5E850958F734524B393B4A3B44525F86EE77816A67F5ED65A0E00AEC0F`；`172,889,234` 字节；`1208.921354` 秒（20 分 08.9 秒）；H.264 2560×1440/30 fps、AAC 48 kHz 双声道。
- OneDrive 客户端固定文件夹：`C:\Users\1\OneDrive\CK3-War-AI-20260923`，仅复制这一份最终 MP4。目标本地字节、SHA 与源一致；客户端 UI Automation 回读该文件“已上传到 CK3-War-AI-20260923”。未对其他云文件发起下载。两份回执保存在 attempt-003，并按哈希纳入 run。
- 这是等待用户审片的候选；自动验证和抽帧包不等于人工按 1× 完整观看。`human_1x_review=not-performed`，没有 `signoff`。

## 制作与验证

- `xar-promo` 使用当时最新正式 v0.2.1，wheel SHA-256 `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`，解释器为仓库 `tools/.venv/Scripts/python.exe`。新 run：`D:\workspace\ck3_native_war_ai_promo_work\episode01-observation-film-attempt-003\run\run-manifest.json`；41 项原始输入逐字节保全。`validate --profile authoring`、`plan --validate-only`、`build` 成功；最终混音文件作为独立 derived deliverable 保全。
- 25 段 EdgeTTS `zh-CN-XiaoxiaoNeural`、`-12%`，实测旁白合计 1208.90 秒。只用原系列主题《Quiet Courtly Tension》，主题 SHA-256 `FDA2464FB4B06CD9A2F0196E5C40CA311EB693EC263C996E4CCC24A6ADA8803F`，循环播放、固定 -17 dB；旁白 0 dB、无 ducking、无自动归一化。混音回执保全滤镜和 FFmpeg argv。
- 实机段共剪入 266.0 秒不重复的墨西拿完整战斗净片。该同存档独立重放在第 6 天后与研究回执数值分叉，画面只用作原版战斗和镜头证据；精确数值只引用对应原始回执。净片 267/267 个逐秒抽样均保有战斗标记，镜头热点选择器与游玩智能体共用。
- 对最终混音文件做 ffprobe 媒体绑定与全视频帧、全音频样本 FFmpeg 解码，退出码 0；技术报告为 `technical-checks-passed-pending-human-review`。抽样复查实机战斗面板与图卡证据行的字幕安全区；另由 `xar-promo review` 生成待人工审阅的章节／转场抽帧包，不制造人工签核。
- attempt-001 的 24 段旁白不到 20 分钟；attempt-002 虽完成编码，但图卡脚注与字幕相撞、实机字幕遮住战斗面板，已保存 layout QC RED 报告和两张问题帧，未上传。attempt-003 另开 run/workdir 修正版，不覆盖失败尝试。

## 研究边界

原版主战单日对拍已覆盖一条回执的 54 个兵团伤亡行零差；冻结第 26 日骑士事件已确认载入索引 11、战报与稍后死亡／兵团退出。深层抽签和完整写集、增援／撤退、终局与跨条件校准仍未闭合；共享游玩智能体保持 `planner_usable=false`，不因本片交付而放开自动进攻门禁。后续研究继续沿[战斗反馈文档](../../../docs/ck3-native-ai/combat-phase-feedback-battle-horizon.md)的剩余门禁推进。
