# 《战斗后半笔账》镜头与取材门

2026-09-28 预制。`研究回执已得`只表示数字/状态有原始来源，不表示有可剪的同身份原速游戏录像；每个新录制 attempt 保留自己的 config、source save、raw、控制报告、时间轴、截图、clean span 和 SHA。

| 镜头 | 需要看见的内容 | 已有研究来源 | 录制/剪辑状态 |
| --- | --- | --- | --- |
| E2-01 地图与身份 | 墨西拿 `2633`、CombatID `16777218`、WarID `4`、双方旗帜与战斗面板，给观众建立空间。 | [第 1 集镜头账](../episode-01-battle-win-probability/camera-follow-footage-ledger.md) | 有独立重放 266.4 秒可见性筛选拼接画面；adapter bundle 与人工审阅未完成。只能作为标注来源的上下文候选，精确数值另拍。 |
| E2-02 追击起算 | attempt-004 第 28 日 phase、双方当前人数、败方软伤池、追击/掩护与逐团预算。 | [追击 v4](../../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_pursuit_parity_v4.json) | 研究回执与同轨迹 100 秒原速 raw `gameplay-messina-pursuit-to-terminal.mkv` 已得；抽样 PTS 仅见第 28–30 日，须审 clean span。 |
| E2-03 三日写回 | 第 28→29、29→30、30→31 日每团 soft/hard 与终局前状态；每日预算重算，不能首日损失乘三。 | [逐日对拍](../../../docs/ck3-native-ai/battle-simulation-episode01-live-case.md#2026-09-26-追击三日同一独立回放的逐团与账本对拍) | 数值条件对拍已得；现有 100 秒 raw 未覆盖第 31 日和第 32 日终局，须以新 attempt 补录并按其实际轨迹重算数字。 |
| E2-04 致残事件 | 第 5 日事件、目标骑士 `34333`、第 6 日有效勇武及 61 号兵团攻防变化，保留“骑士仍在名册”。 | [次帧原生输入](../../../docs/ck3-native-ai/combat-phase-event-trace.md#致残写回进入第-6-天智能体输入) | 前后存档与 v3 已得；039→040 是同一后存档字节冷启动只读次帧。两次 attempt 均无可用连续录像，UI 前后画面未取得。 |
| E2-05 击杀抽签 | 第 26 日 `knight_killed` 的 14 人候选、原生 draw/index、被选中 34120、目标 33437 死亡脱团；第 27 日名册单列复核。 | [020 原生抽签及狭窄写回](../../../docs/ck3-native-ai/combat-phase-event-trace.md#2026-09-26-第-26-日骑士击杀者抽签实机闭合)、[070 独立权重实采](../../../docs/ck3-native-ai/combat-phase-event-trace.md#2026-09-27-第-26-日成长列表选择器权重实采)、[036→038 后档次帧链](../../../docs/ck3-native-ai/combat-phase-event-trace.md#事件后的下一帧智能体输入) | 研究回执已得；020、070、036、038 均无连续录像，起止截图不是骑士 UI。正式战报/人物画面未取得，须补录并用新轨迹数字；020、070、036→038 必须分轨标注。不得把成长列表父 draw 当作实际抽签。 |
| E2-06 增援入场 | 第 11→12 日 ArmyID `22`/13 团加入；旧双方 entry 与缓存残差、新军起始/当前人数、返回后双方缓存。 | [085 原版同钩子](../../../docs/ck3-native-ai/join-width-production-and-fire.md#085-双方-full-entry-同钩子实采与缓存差额) | collector 局部 captured，附带 battle-control 查询曾 RED；085 只有远离战场的地图起止截图、无连续录像。精确 UI 画面未取得，须居中墨西拿、打开战斗面板并补录。 |
| E2-07 战宽到出伤 | base `1645→2467`、final `1480→2220`，同 CombatID/ArmyID/日期首次 side0 出伤读取 `2220`。 | [085 同次入场与三点战宽](../../../docs/ck3-native-ai/join-width-production-and-fire.md#085-双方-full-entry-同钩子实采与缓存差额)；[083](../../../docs/ck3-native-ai/join-width-production-and-fire.md#083-同一次自然增援的三点实采)仅作独立复证 | 085 的数值链已得；计算卡可制作，游戏画面需按 085 的轨迹配对，不能拼接 083 的画面。 |
| E2-08 正常终局 | 第 32 日 `normal_result`、winner side0、败方军队退出旧 CombatID 并进入 retreating，战争面板变化。 | [同案终局](../../../docs/ck3-native-ai/battle-simulation-episode01-live-case.md#2026-09-26-追击三日同一独立回放的逐团与账本对拍) | 原生终局已得，100 秒 raw 未拍到终局，d32 截图被事件覆盖；正式 UI 结果镜头未取得，须补录并按新轨迹核数字。只称败后撤退，不称 AI 主动撤退。 |
| E2-09 战争账本 | 原生 writer 的分子、八桶分母、CB 倍率与封顶逐步入账，结果为进攻方战分 `-50`。 | [战分 writer](../../../docs/ck3-native-ai/battle-terminal-and-reentry.md#2026-09-26-梅西纳单场战分同一次原生-writer-的完整输入与写回) | 算术原件/共用核已得；024 只有远离战场的地图起止截图、无连续录像。须聚焦战场和 WarID `4` 面板，补拍前后图及 clean span。 |

**剪辑准入**：每个取用镜头都须有 `attempt ID + source save SHA + game build + CombatID/WarID + 原生日期 + raw 媒体 SHA + clean span PTS + 对应控制回执 SHA`。不同 attempt 只能作为明确标注的对照，不能用切镜头隐去随机轨迹切换。非零败方掩护、主动撤退和整场条件胜率仍是研究待拍，不能用本表任一局部镜头替代。
