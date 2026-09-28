# 《战斗后半笔账》增援与终局证据索引

2026-09-28 只读核验。本文供下一期 E2-06 至 E2-09 的拍摄和剪辑使用。原始研究回执可以制作标明来源的计算卡；它们本身不构成同身份、原速、连续的 CK3 实机镜头。本文没有运行 CK3、修改任何历史 attempt 或取得新的战场录像。

## 身份与独立回放

| 项目 | 入场 attempt-085 | 战分 attempt-024 |
| --- | --- | --- |
| 原版 | CK3 `1.19.0.6`，`ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` | 同左 |
| 来源 | attempt-004 第 11 日不可变存档，SHA-256 `3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953` | attempt-004 第 27 日原生检查点，SHA-256 `f085d8abb89a354fa1004dbe8800505bc952aa8a68c0ea21aab788f9875feeb3` |
| 对象 | `CombatID=16777218`，初帧战争 `WarID=4`，加入 `ArmyID=22` | `CombatID=16777218`，`WarID=4`，败方战争参战者 `CharacterID=29829` |
| 日期 | `53146488→53146512`，恰好原生一天；入场、首次出伤均在 `53146512` | `53146872→53146992`，第 27 日检查点到第 32 日正常终局 |
| 原始结果 | `jfull085-finish.json` SHA-256 `A7F01C89BE66B34A6F2862BAEFC4354EF74507B6D5178E2949C381DEDC32FD88`；`cleanup-check.json` SHA-256 `5FD3CFE8AB9A69D557042B5CA3DE2CC59587C6BA679BF430F2BA15A98337CB37` | `d32-terminal.json` SHA-256 `E55CEFA0AEB57D2F27A0EEF5D9516B85DB9FA5722551A4A83A5BB909DF5BE96F`；`session-result.json` SHA-256 `85400E4632D5C6D8C6EE9FE527B37EA70CC60938C0A77FEAC8DCB3451472B529` |

两者来自同一个原始案例的**不同日期检查点和独立进程回放**。相同 CombatID/WarID 只保证对象身份，不保证随机轨迹相同；成片应分别标注 attempt，不能把 085 画面直接接成 024 的下一镜。原始回执在外置目录 `D:/workspace/ck3_native_war_ai_promo_work/episode01-join-full-entry-live-attempt-085/ck3-output/interactive-requests-responses/jfull085-finish.json` 与 `D:/workspace/ck3_native_war_ai_promo_work/episode01-denominator-live-attempt-024/ck3-output/interactive-requests-responses/d32-terminal.json`。正式镜头来源和剪辑门另见[下一期镜头表](shot-list.md)。

## E2-06 / E2-07：增援入列、缓存与首次出伤

[085 原生专题](../../../docs/ck3-native-ai/join-width-production-and-fire.md#085-双方-full-entry-同钩子实采与缓存差额)和[机器向量](../../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_join_full_entry_085.json)可支持以下**同一次 085 原始 finish**中的算术板。083 是另一条独立三点回放，只宜作为复证；085 已经自己捕获全部三点，不必拼接 083 的第三点。

| 同日边界 | side 0 / side 1 fighting cache，Q100000 | base / final 战宽 | 可上屏解释 |
| --- | ---: | ---: | --- |
| `0x23040A0` join 入口，phase day 7 | `160317482 / 89325449` | `1645 / 1480` | side 0 的 27 条旧 entry 实际合计 `154690163`，缓存高 `5627319`；side 1 的 24 条 entry 合计 `82785368`，缓存高 `6540081`。入口 base `1645` 是历史缓存，不从当前 entry 重新算。 |
| 同一 wrapper 正常返回，phase day 7 | `410690163 / 82785368` | `2467 / 2220` | side 0 roster 末尾新增 ArmyID `22`；旧 51 条 entry 逐 ID 未变。新军 13 条 entry 起始合计 2570 人，但 RegimentID `177` 起始 10、当前 0，故新增 current 只有 2560 人。双方返回缓存与 entry 合计的残差都归零。 |
| 首次 side 0 出伤，phase day 8 | `410690163 / 82785368` | `2467 / 2220` | 原生出伤器收到的宽度入参 `R8D=2220`，与存储的 final 相等。 |

返回后的双侧 current 合计为 `493475531` Q100000，即 `4934.75531` 人当量；取半并截断得到 base `2467`，再按原版梅西纳森林静态宽度乘数 `90000/100000` 截断为 final `2220`。森林乘数不是 085 同帧运行时字段；画面要标为已核对的原版静态输入。`2570` 是基础/起始人数，`2560` 才是这次加入时实际 current，不能混写。full-entry `status=captured,count=2`、join-width `status=captured,count=3`、全 trace `failure_flags=0`，但 `production_trace_ready=false`；085 附带的 battle-control sibling 查询曾单独 RED，不能把整个研究会话称为所有查询 GREEN。

**补拍镜头**：从精确来源存档新开独立受管 attempt，开始录制前把镜头移到墨西拿并打开战斗面板，拍 ArmyID `22` 入列前后军旗/参战列表、日期变化、战宽显示及首次伤亡后的前后状态。保存原始视频、同步原生回执、源档 SHA、时间轴、clean span 和每段媒体 SHA；新回放数字若与 085 不同，就用新回放自己的数字，085 仅作独立研究板。未来增援 ETA、AI 求援指派和通用加入策略仍未由 085 证明；[增援专题](../../../docs/ck3-native-ai/battle-reinforcement-and-join.md)中的独立回放也只证明本例两次入列，不闭合“请求→指派→ETA→同场入列”全链。

## E2-08 / E2-09：正常终局与战争账本

[024 原生 writer 专题](../../../docs/ck3-native-ai/battle-terminal-and-reentry.md#2026-09-26-梅西纳单场战分同一次原生-writer-的完整输入与写回)和[共用只读对拍报告](../../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_battle_score_parity.json)支持同一次 024 第 32 日的逐步计算：

| 输入/计算 | 原生值 | 可讲的含义 |
| --- | ---: | --- |
| 败方 combat side 起始 baseline | `129800000` Q100000，即 1298 人 | 单场侧的起始口径；不是战分分母。 |
| 败方 hard-loss 分子 | `53662042` Q100000，即 536.62042 人当量 | writer 当场读到，不能从 UI 封顶的 50 反推。 |
| 败方战争参战者八桶分母 | `0+675+310+0+0+0+11+0=996` 人 | 战争参战者的军事汇总，不能与 1298 互换。 |
| 原生整数比例 | `min(100000,53662042//996)=53877` Q100000 | 53.877%。 |
| 已加载 CB 战分倍率 | `15000000` Q100000，即 150 | `53877×15000000//100000=8081550` Q100000，即未封顶 80.8155 战分；不要口播成“150 倍”而模糊量纲。 |
| 单场上限与结果 | `min(8081550,5000000)=5000000` Q100000 | row magnitude `+50`；winner 是战争防守方，从战争进攻方看是 `-50`。 |

024 原始 `d32-terminal.json` 同时给 `terminal_kind=normal_result`、winner side 0、败方 side 1、`successor=subject_retreating`、WarID `4`、row index `0` 和 `attacker_relative_delta_raw_q100000=-5000000`。这支持“正常败战后撤退”，不能说“AI 主动选择撤退”；也不代表本场战争总分仅有战斗一项。第 31 日 participant hard 账本与 writer 的终局分子尚有 **10 人当量口径差**，计算板必须使用终局 writer 原生分子。[原生终局专题](../../../docs/ck3-native-ai/battle-terminal-and-reentry.md)另有战争解散的 `no_normal_result` 分支，但它是另一次独立夹具，不应剪入 024 的正常终局连续段。

**补拍镜头**：从第 27 日冻结档另开独立受管 attempt，先拍第 27 日主阶段及第 28–31 日追击/战报的同身份日期锚，再拍第 32 日 winner、败方军队退出旧 CombatID、撤退路线和同一 WarID 的战分 UI 前后；计算卡旁明确“writer 原生回执”与“游戏可见面板”的不同来源。新回放须保留自身战分 writer/terminal 回执，不能仅凭游戏总分变化把 024 的 `-50` 嵌入另一随机轨迹。

## 现有图片的画面准入

已逐张打开 085 和 024 各自 `ck3-output/map-start.png`、`map-end.png`；两份 attempt 目录都没有 `.mp4`。四张截图均为偏离战场的深色地图/战争迷雾，能看到暂停和日期 UI，却看不到战斗面板、入列名单、WarID 或战分；因此**不能充当 E2-06 至 E2-09 的正式实机镜头**。其 SHA-256 分别是：085 start `21B3B06563FFBCE524F83564E5BA84FDF412154DE189F7478F3B3AFF6FDC7994`、end `601076924BB2FF6B4A23CC56C1DD8EEBFA09AB7D88C49C37AA0D8ED174475045`；024 start `325F05E92DD2B5C187796BCDC0C80B19592E3074D6592A4DFA0AAFC87EF268D3`、end `9C6976140786B3F45474EB0F6B9EB2014BD0FCAD7C448D97CD73660BF5587FAD`。

R0271 的受管屏幕需求优先。本索引是无屏幕的研究交付；等屏幕调度允许后，以上补拍均须取得当次新鲜 Steam 离线画面和 `ck3-screen:acquired`，以新 attempt 留存原始视频、控制回执与 clean exit。旧原始研究回执和失败 attempt 保持原样。
