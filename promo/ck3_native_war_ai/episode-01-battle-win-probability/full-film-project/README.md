# 第 1 集 EdgeTTS 观察版：制作入口

2026-09-25 用户明确指定本版为草稿；正式版另用已授权参考声和《Project 因果律》的 IndexTTS 2.5 配置重配、重排并机器核验，制作配置见 [`index-film-project/promo-project.json`](../index-film-project/promo-project.json)。

2026-09-25 用户调整本次看片范围：**先用已经确认的原生机制做一部 20–40 分钟完整视频**，重心是逐步讲清 CK3 一场战斗的输入、逐日算法和可复验实例；不以尚未校准的整场胜率百分比作为本版结论。成片交付后再继续击杀深层抽签、增援／撤退／终局与胜率校准研究。此前 `preproduction-0001` 的原意和素材保持历史原样；本次配置修改后创建新 run。

第 26 日事件行的后续实机回读已固化为[共享选中行报告](../../../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_selected_phase_event_row.json)：确认为原版 `knight_killed`，内部抽签与整场胜率仍未闭合。全片脚本和字幕只能在这一证据边界内写结论。

本目录是[导演案](../director-plan.md)的完整片项目配置，目标 20–40 分钟；观察版使用 25 段脚本与实机镜头制作，仍无可公开的整场胜率百分比。`preproduction-0001` 是 `xar-promo init` 自动生成、绑定初始配置字节的历史 run；配置增补五章后另开独立 run，不覆盖前者。

2026-09-25 使用当时查询到的最新正式 `xar-promo` **v0.2.1**，wheel SHA-256 `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`，解释器 `D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe`。新 run 位于 `D:\workspace\ck3_native_war_ai_promo_work\episode01-full-film-preproduction-attempt-001\run\run-manifest.json`，已经按内容哈希保全五项原始输入：266.4 秒墨西拿战斗净片、唯一系列音乐母版、镜头逐秒可见性审计、最新条件击杀效果审计，以及工具链/声线/混音来源记录。配置和 run 的 `authoring` 全字节校验均为 GREEN；这只验证预制作文件完整，不等于 `build`、全片审阅或人工签核。

后续新拍摄、旁白、字幕、编码或失败重试各开独立 attempt/run。实机画面必须延用[热点跟随与镜头证据](../camera-follow-footage-ledger.md)；旁白为 `zh-CN-XiaoxiaoNeural`、语速 `-12%`，只用 `Quiet Courtly Tension.wav`，配乐固定 `-17 dB`、无 ducking。观察版允许在已确认范围内讲算法、逐日实例及证据边界，但不得把研究中的条件路径当作已校准的整场胜率；后续若改为胜率结论版，仍须通过[事件效果反馈](../../../../docs/ck3-native-ai/combat-phase-feedback-battle-horizon.md)、增援/退出、终局及跨条件校准门禁，并让同源胜率进入游玩智能体决策。现阶段 `planner_usable=false`。

观察版制作输入为 [`full-film-script.json`](../full-film-script.json) 和由其生成的 [`full-film-timeline-v2.json`](../full-film-timeline-v2.json)；[`full-film-timeline.json`](../full-film-timeline.json) 留存第一次 24 段试录的历史时间线，不用于最终成片。EdgeTTS 共 25 段，实测旁白 1208.90 秒；独立净片提供 266.0 秒不重复的原版实机镜头，来源与原研究数值在第 6 天后分叉，因此逐日精确数值只引用对应原始回执。`episode01-observation-film-attempt-001` 留存未达 20 分钟的 24 段试录；`episode01-observation-film-attempt-002` 的抽样画面发现图卡脚注和字幕重叠、实机字幕遮住战斗面板，记录为 layout QC RED，不能作为交付片。`episode01-observation-film-attempt-003` 修正卡片脚注与字幕安全区，复用同一批 EdgeTTS 音频但另开独立 run 与 workdir。每个 TTS 请求、返回、边界和已失败 take 都保留。制作路径在 `D:\workspace\ck3_native_war_ai_promo_work`；两个 25 段 run 各自由 `xar-promo start-run` 创建并按内容哈希保全 41 项输入，第三次 run 的 `validate --profile authoring` 与 `plan --validate-only` 为 GREEN。构建、自动核验与人工签核状态以该 run 的最新报告为准，不用配置校验代替成片验收。

2026-09-25 attempt-003 已产出 20 分 08.9 秒的完整 EdgeTTS 审片候选，最终 MP4 的全程解码、主题混音参数和 OneDrive 客户端上传回读完成。精确 SHA、文件名、制作链与保留的 QC RED 见[交付记录](../observation-build-record.md)。这仍是供用户看片的版本，尚无人工 1× 完整审阅或签核。
