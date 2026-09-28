# 《战斗后半笔账》追击与骑士镜头证据索引（2026-09-28）

状态：**研究数字可用；对应完整原速镜头未齐**。本索引只读核对已冻结的外置原件，没有启动 CK3、录屏或改变任何历史 attempt。`CombatID=16777218`、`WarID=4`、CK3 `1.19.0.6` 是案例身份；相同 CombatID 或相同源存档并不自动证明相同随机轨迹。基础研究见[墨西拿同案](../../../docs/ck3-native-ai/battle-simulation-episode01-live-case.md)、[事件追踪](../../../docs/ck3-native-ai/combat-phase-event-trace.md)、[下一期研究计划](../../../docs/ck3-native-ai/battle-second-half-research-plan-2026-09-26.md)。

## 逐条取材身份

| 取材支线 | 原始来源与可讲结论 | 可剪游戏画面现状 |
| --- | --- | --- |
| `episode01-full-edge-attempt-004` | 从 attempt-002 接战 save `45CCE7E9A7E505C878F661333DE30D6B459DA638259A9E99990A226CE564245F` 独立回放；第 28–32 日原始索引 `terminal-replay-d28-d32.jsonl` SHA-256 `B4F8C8D4E2827650E4401E9FBAB34DE62558641A424382A4C460FEDBD261E160`。追击三日和同次终局可在这一支线里连讲。 | 有 100 秒原速 MKV 和第 28–32 日五张同源截图。MKV 抽帧只见第 28–30 日，第 31 日和第 32 日终局**不在该录像内**；还没有 1× 审核过的 clean span。 |
| `episode01-day05-wound-growth-attempt-039` → `episode01-day06-maim-next-input-attempt-040` | 039 的第 5 日事件使骑士 `34333` 致残；040 逐字节复载 039 后存档 SHA-256 `9ACACDE3E2D1987180EFE5FFDDC32B092146E6116779AF0D4BEBC7C97B9B7F9A`，**不推进日期**地读第 6 日原生 v3 输入。这是一条事件到下一暂停帧的源档绑定链。 | 两次 `capture-report.json` 均为 `raw_video:null`、`recording_complete:false`、`clean_spans:[]`。039/040 的地图截图不证明骑士人物 UI 前后状态；040 `map-start.png` 还被 Windows“如何打开这个文件”对话框遮住。 |
| `episode01-day26-knight-selector-attempt-020` | 从 attempt-010 第 26 日不可变源档 SHA-256 `C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B` 恢复；原生选择器、七边界与前后存档证一次 `knight_killed` 目标选择及狭窄写回。 | `capture-report.json` 明记 `raw_video:null`、`recording_complete:false`、`clean_spans:[]`。`map-end.png` 是远离战场的迷雾地图，不是人物、战报或名册镜头。 |
| `episode01-day26-runtime-weight-attempt-070` → `episode01-day27-next-input-attempt-038` | 070 从上述第 26 日源档另起独立回放，直接回读成长列表运行时权重；038 复载 **070** 后存档 SHA-256 `CD0648D7603290E470ED07261128C05FF449C0FFAEA89D01A1102D0D56208A55`，读第 27 日原生 v3 名册。020 与 070 是独立 attempt，020 的后存档不能冒充 038 的来源。 | 070/038 同样没有 raw video 或 clean span；如正片要展示权重、击杀与次帧名册，应为新拍 attempt 重新绑定实际 run 的画面和回执。 |

## 追击：已证数字与镜头准入

同一次 attempt-004 的第 28 日输入独立链式推演到第 31 日；第 29、30 日没有重新喂入原版败方状态。[追击 v4 逐团结果](../../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_pursuit_parity_v4.json)与原始 `term-d28..d32` 回执绑定。

| 日初→次日 | 24 团 soft 账 | 可读的逐团 hard 账 | 当日 soft→hard（Q100000） |
| --- | ---: | ---: | ---: |
| 28→29 | 24/24 零差 | 23/23 零差 | `2,070,677` |
| 29→30 | 24/24 零差 | 23/23 零差 | `2,097,473` |
| 30→31 | 24/24 零差 | 23/23 零差 | `2,126,119` |

合计 `6,294,269 raw = 62.94269` 人当量；72/72 团 `current_fighting_raw` 不变，69/69 可读 hard 账零差，另一个 entry 的 hard 字段为 `null`，不能填 0。三天胜方 `pursuit_damage_raw` 各为 `75,203,000`，本案**败方掩护聚合为 0**；每天要按缩小的 `toughness_soft` 重算两域预算和逐团比例、余数，不能把首日损失乘三。这里没有原生追击“抽签”证据；“抽签”应留在骑士事件段。非零败方掩护仍缺原版同帧逐团对拍，不能把静态向量讲成已实测。

第 32 日同源终局回执为 `normal_result`、winner side0，玩家 ArmyID `18` 脱离旧 CombatID 并进入 `retreating`，战争进攻方战分 `-5,000,000 raw = -50`。战斗 side0 是敌军，不可把 winner side0 配成玩家赢；败后撤退也不是普通 AI 在战中主动选择撤退。

原始录影片 `D:/workspace/ck3_native_war_ai_promo_work/episode01-full-edge-attempt-004/gameplay-messina-pursuit-to-terminal.mkv`，独立复核 SHA-256 `359BE5CF17D7D838E9A4E1049B0E85CBE5BF9ACF9668B0E43EF467AB4F68D27F`，ffprobe：`100.000000s`、`1024×768`、30 fps。`recorder-terminal-start.json` 的 ffmpeg `-t 100` 与文件一致。外置审片抽帧位于 `D:/ck3-research-artifacts/episode02-pursuit-review-20260928/attempt-01/frame-*.png`，在 PTS 0–60 秒见第 28 日 `1066-12-31`，70–80 秒见第 29 日 `1067-01-01`，90–99 秒见第 30 日 `1067-01-02`。这是采样核验，**还不是完整 1× clean-span 审核**；文件名的 `to-terminal` 不能替代实际 PTS 内容。原始第 28–32 日截图可用于带来源的静态证据板，但第 32 日截图主要被“诺曼人的西西里”事件窗口遮挡，未提供干净的战斗结果 UI。

**须补录**：若影片要呈现连续的三日追击与终局，应从冻结的第 27 日源档另起完整原速录制 attempt，拍第 28 日输入/地图和战斗面板、28→29/29→30/30→31 的日期与面板变化、第 32 日结果/军队撤退/战争面板。新 run 若产生不同逐日随机轨迹，要重取自己的原生 control、逐团账与终局数值并重算；不能把新镜头无标注地配 attempt-004 的 72/72 数字。原版 UI 不直接展示全部 Q100000 逐团字段，计算板须绑定同 run 回执与 media SHA。

## 骑士：已证数字与镜头准入

**第 5 日致残（039→040）**：039 的同日七边界中新追加 `knight_maimed_by_enemy`：目标骑士 `34333`、对手 `47032`；目标后存档由无伤变为 `one_legged + wounded_1`，仍存活，击伤者威望货币 `300→450`、基础勇武仍为 10。成长列表本次选第 0 项，没有基础勇武增加；另一个旧受伤战报在源档已有，不是本次新增。040 的原生 v3 次帧读取维持 51 团、24 名骑士，目标有效勇武 `11→7`，61 号兵团有效伤害 `962.5→612.5`、韧性 `192.5→122.5`，人数仍 1；骑士效能仍 `1.75`。其他骑士与兵团的相关 v3 属性行不变，但正常逐日伤亡另有变化，不能归因于致残。见[第 5 日事件与次帧表](../../../docs/ck3-native-ai/combat-phase-event-trace.md#致残写回进入第-6-天智能体输入)与[冻结输入报告](../../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_knight_maim_next_input.json)。

**第 26 日击杀（020 与 070→038 分轨）**：020 直接捕获 `knight_killed` 选择器的 14 名候选、局部 `draw31=1,400,813,912`、`%14=8`，原版尾项填洞后索引 8 为击杀者 `34120`；稳定删除的索引 8 会误指 `54140`。目标 `33437`/兵团 `65` 在 fire 边界 5 仍存活，边界 6 有 death marker、脱团；后存档记 `death_battle/killer=34120`，基础勇武仍为 2，有效勇武 `4→2`，击杀者威望货币与累计威望各 +150。[020 抽签](../../../docs/ck3-native-ai/combat-phase-event-trace.md#2026-09-26-第-26-日骑士击杀者抽签实机闭合)。070 **另一次独立回放**直接捕获成长列表运行时权重 `[40,30,15]`、列表 draw `51,510,340`、阈值 2、来源第 0 项 `no_op`；这不能写成 020 的同帧权重。[070 权重](../../../docs/ck3-native-ai/combat-phase-event-trace.md#2026-09-27-第-26-日成长列表选择器权重实采)。038 复载 070 的后档，名册 69→68 团、30→29 骑士，仅缺目标 `33437`/团 `65`；这是 070→038 的原版输入消费链，不是 020→038。[次帧名册](../../../docs/ck3-native-ai/combat-phase-event-trace.md#事件后的下一帧智能体输入)。

**须补录**：第 5 日须同一新 attempt 拍事件前战斗面板/骑士人物状态，发生事件的战报或人物 UI，以及第 6 日同一人物伤势和骑士仍在名册；如果新随机路径没有致残 `34333`，不得拿 039/040 的数值配无关画面。第 26 日须拍战斗事件、被击杀者与击杀者的人物/名册、次帧名单与战斗面板；研究钩子的 14 人抽签和权重应做来源明确的计算卡，原版 UI 本身不展示这些内部值。录制 run 须把 source save SHA、原始回执、视频 bytes、日期和 CombatID 一起冻结。

## 可以写入脚本的界限

- 可称“本案给定第 28 日原版输入，三日追击逐团条件计算零差”；不可称“所有掩护条件已实测”或“整场胜率已求出”。
- 可称“本次致残改变下一暂停帧的有效勇武与骑士兵团属性；本次击杀删除一名骑士和其兵团”；不可称所有受伤、死亡、治疗和人物效果写集都已闭合。
- 可称“020 证击杀者选择、070 证成长权重、070→038 证次帧名册”；不能把不同 run 的画面或原始回执剪成无标记的同一次战斗。
- 已有研究回执、地图截图或拍摄计划均不能代替原速游戏录像、clean-span 审核及最后的 1× 全片人工观看。
