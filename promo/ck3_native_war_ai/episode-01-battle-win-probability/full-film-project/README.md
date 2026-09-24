# 第 1 集完整 EdgeTTS 版：预制作入口

第 26 日事件行的后续实机回读已固化为[共享选中行报告](../../../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_selected_phase_event_row.json)：确认为原版 `knight_killed`，内部抽签与整场胜率仍未闭合。全片脚本和字幕只能在这一证据边界内写结论。

本目录是[导演案](../director-plan.md)的完整片项目配置，目标 20–40 分钟；目前状态为**预制作**，尚无完整成片或可公开的整场胜率百分比。`preproduction-0001` 是 `xar-promo init` 自动生成、绑定初始配置字节的历史 run；配置增补五章后另开独立 run，不覆盖前者。

2026-09-25 使用当时查询到的最新正式 `xar-promo` **v0.2.1**，wheel SHA-256 `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`，解释器 `D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe`。新 run 位于 `D:\workspace\ck3_native_war_ai_promo_work\episode01-full-film-preproduction-attempt-001\run\run-manifest.json`，已经按内容哈希保全五项原始输入：266.4 秒墨西拿战斗净片、唯一系列音乐母版、镜头逐秒可见性审计、最新条件击杀效果审计，以及工具链/声线/混音来源记录。配置和 run 的 `authoring` 全字节校验均为 GREEN；这只验证预制作文件完整，不等于 `build`、全片审阅或人工签核。

后续新拍摄、旁白、字幕、编码或失败重试各开独立 attempt/run。实机画面必须延用[热点跟随与镜头证据](../camera-follow-footage-ledger.md)；旁白为 `zh-CN-XiaoxiaoNeural`、语速 `-12%`，只用 `Quiet Courtly Tension.wav`，配乐固定 `-17 dB`、无 ducking。生成整片之前仍要通过[事件效果反馈](../../../../docs/ck3-native-ai/combat-phase-feedback-battle-horizon.md)、增援/退出、终局及跨条件校准门禁，并让同源胜率进入游玩智能体的实际决策。现阶段 `planner_usable=false`。
