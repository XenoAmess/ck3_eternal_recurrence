# CK3 1.20.0.3：战损、溃退与人物结果的 stock 输入

2026-10-03，file-only research；未连接游戏、未执行 MCP、未操作窗口、未运行测试。读取的是当前安装目录 `Z:/SteamLibrary/steamapps/common/Crusader Kings III/game/`，不是仓库里的较旧游戏副本。任务的 exact-build 锚为 CK3 `1.20.0.3` / Steam `25652598` / EXE SHA-256 `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`，沿用协调者已冻结的身份；本包逐文件冻结实际读取的 stock 字节，见 `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/battle-casualty-outcomes/stock/STOCK-EVIDENCE.json`。

施工前已读 `Z:/g35/docs/ck3-native-ai/combat-casualty-chain-explainer.md`、`ck3-1.20.0.2-combat-migration.md` 与 `ck3-1.20.0.2-battle-migration.md`。前者明确是 1.19.0.6 公式/实机解释，后两者明确绑定 1.20.0.2；本包不会把这些旧构建的地址、公式、fixture 或终局证据升级为 .3 验收。当前战争与战斗授权已全面开放。

## 可以直接复用的当前 stock 事实

| 当前安装版事实 | 文件与行号 | 对首战观测的意义 |
| --- | --- | --- |
| `COMBAT_ROLL_DAYS=3`，`COMBAT_EVENT_DAYS=5`，`MANEUVER_PHASE_DAYS=3` | `common/defines/00_defines.txt:584–591` | 日推进可能改变 roll、phase 与人物；不会把一次 ACK 当成状态结果。 |
| 主战 `BASE_RATIO_CASUALTIES_CONVERSION=0.3` | 同文件 `:598` | 是基础配置；不是全战最终死亡率，也不是每名骑士的死亡率。 |
| `PURSUIT_PHASE_DAYS=3`，追击硬伤转换配置 `=1`，pursuit 属性倍率 `0.5`、base toughness项 `0.05`、最低项 `0.01` | 同文件 `:599,609–612` | 胜负出现后仍可能有追击损失；主战结束时的人数不能冒充追击后的最终人数。配置与注释不证明 .3 原生乘除/截断次序。 |
| 手动撤退配置 `MIN_DAYS_BEFORE_MANUAL_RETREAT=14` | 同文件 `:606` | 不自行推算 inclusive day 边界；沿用实际原生合法性观测。 |
| `NArmy.MOVEMENT_SPEED_RETREAT=4.5`，普通速度 `3` | 同文件 `:633–634` | 撤退是可回读的军队路线/状态变化；不是胜败或伤亡的同义词。 |
| shattered retreat 偏好距离7、省份上限15；自己realm340、war friend200、enemy−250、距离倍率−50等权重 | 同文件 `:706–723` | 只是目的地打分输入，不能由它猜出本战实际撤退目标。 |
| AI撤退注释是预测比率低于 `0.45` **且**（显著兵力在别处 **或** 附近更好防守地）；better terrain距离 `2`，elsewhere strength比例 `0.25` | `common/defines/ai/00_ai.txt:1270–1305` | 是 stock 条件账本；未读取 .3 原生调用链时，不把人数比或自己的预测当成 AI 已满足这些条件。 |

本次对当前 `00_defines.txt` 检索 COMBAT/BATTLE/WIPE/ROUT/MORALE/CASUALT/RETREAT，没有找到定义自动败退、stackwipe或自然主战终止阈值的配置。所见 `BASE_DEFENDER_MORALE` 等是围城段，不是野战士气。这是本次文件范围的阴性结果，不意味着引擎没有终止判定；相关 .3 原生分支由负责原生战斗链的工作包闭合。本包不补猜测阈值，也不要求全场预测闭合后才允许实际操军。

## 阶段人物事件不是兵员伤亡概率

`common/combat_phase_events/_combat_phase_events.info:1–24` 明确：按 `COMBAT_EVENT_DAYS` 对参战人物评估，`type=commander/knight`；`chance` 是对其他有效事件的加权选择，空 effect 的 none 行内部会省略排队。因此不能把某个基础权重直接念成百分比。

当前骑士行的基础权重为 none `2000`、wounded `100`、maimed `40`、killed `30`，分别在 `00_knight_phase_events.txt:1–5,546–559,758–771,968–972`。能力、伤势、人数、文化、rite、职务、accolade等会改变有效集合或权重；例如 `knight_killed` 包含 `rite_has_parameter=death_is_glory`（`:1007–1010`）。本包没有计算人物死亡概率或复用旧构建 RNG 排程。

骑士受伤行排除 `wounded rank=3`（`:549–556`），选中后调用 `increase_wounds_effect`（`:734,753`）；致残行调用 `maimed_in_battle_effect`（`:949,963`），后者部分分支会加深伤势（`common/scripted_effects/20_health_effects.txt:1355–1395`）。直接骑士死亡行记录 battle_event / slain_side_knights，并执行 `death_battle`，有合格对侧骑士时写 killer（`00_knight_phase_events.txt:1271–1337`）。

**指挥官不能套用骑士的伤势排除。** 当前 `00_commander_phase_events.txt` 中 none/wounded/maimed/killed 基础权重是 `1000/25/10/5`（`:1–5,43–55,152–166,268–296`）。`commander_wounded.is_valid` 实际写 `wounded rank<=3`（`:46–52`），其 effect 调用 `increase_wounds_effect`（`:127,146`）。该 effect 对 rank3 执行 `death_fight`（`20_health_effects.txt:1332–1352`）。这是源码分支事实，未证明当前某名未受伤指挥官的 rank trigger 如何取值或该行真实权重，故不据此报告发生死亡。

`commander_killed` 的资格为已经 `wounded>=1`，或 martial与prowess均 `<=low_skill_rating`，同时排除 very_easy玩家和极端征服者（`00_commander_phase_events.txt:271–293`）。它随后执行 `death_battle`（`:391–413`）。兵团硬伤数值与这些人物 effect 是不同结果链。

## 当前战后俘虏与死亡入口

`common/on_action/combat_on_actions.txt:12–24` 的胜方入口 `on_combat_end_winner` 调用 `combat_event.1001`。旧 `common/on_action/knight_on_actions.txt:8–17` 的 `commanders.0011` 是注释禁用；**不能据旧入口禁用推断当前没有指挥官捕获。**

`events/war_events/combat_events.txt:584–597` 当前 `.1001` 是 hidden combat_side 事件，只在胜方 primary participant 与对侧 primary participant **确实处于战争**、且不是战教程时触发；脚本注释明确仅敌对、没有战争的战斗不取战俘。随后从实际战争 iterator 取 `combat_war`（`:601–630`）。本包不把只处于同省/敌对的两支军队混成同一场战争或同一 CCombat。

败方指挥官有 no-effect / capture 的随机列表，基础 `90/10`（`:640–751`）。存活、prowess、stalwart leader、brave/craven、伤残、参战bodyguard/garuda、acclaimed、culture以及 `scope:wipe` 改变权重；wipe 把 no-effect权重乘 `0.20`（`:693–697`）。这不是恒定10%捕获率。列表末尾明确说明这条战后列表不杀指挥官，以免惩罚负伤后的撤退（`:752`）；它不取消前述阶段中的指挥官死亡路径。

败方每名骑士的列表为基础 no-effect `85`、imprison `10`、death `5`（`:760–878`），也有人物状态与wipe修正。人物须存活才能进入capture/death支路。capture记录 `combatant_captured_in_battle`（`:863–872`）；death记录 `combatant_killed_in_battle`或无killer变体并执行 `death_battle`（`:978–1014`）。已在阶段中死亡的骑士另从 `slain_side_knights` 并入双方战后死者列表（`:1024–1039`），避免把他们再杀一次。

捕获候选列表随后触发 `.1002`（`:1087–1096`）；`.1002` 对仍存活且尚未被囚禁的候选，由 `combat_winner` 实际 `imprison` 为 `house_arrest`（`:1283–1297`）。**battle_event或候选列表是过程，人物实际jailer/囚禁状态才是捕获结果。** 本包不推断本次首战是否已经捕获某人。

```mermaid
flowchart TD
    Combat[实际 CCombat 的双方成员与人物] --> Pulse[COMBAT_EVENT_DAYS 阶段人物事件]
    Pulse --> Weighted[所有有效 commander / knight 行加权选择]
    Weighted --> Wound[增加伤势或致残]
    Weighted --> Death[death_battle / 已3级伤势的 death_fight]
    Combat -. .3 原生结束与 wipe 判定未由本包读取 .-> End[自然结束 / 胜方]
    End --> War{双方 primary participant 真实交战?}
    War -->|是| Event1001[on_combat_end_winner → combat_event.1001]
    War -->|否| NoPow[这条链不取战俘]
    Event1001 --> Commander[败方指挥官 no-effect / capture]
    Event1001 --> Knights[败方骑士 no-effect / capture / death]
    Commander --> Candidates[prisoners_of_war 候选与 battle_event]
    Knights --> Candidates
    Candidates --> ActualPrison[combat_event.1002 → 存活且未囚禁者 house_arrest]
    Death --> ActualDeath[人物 alive / death reason / killer 回读]
```

## 首战前后够用的观察记录

这是一份已有观测口的消费建议，不新增动作门禁，不要求先求整场胜率，也不要求为了本包再跑已成功的查询。

1. 战前或第一次实际接触：保存同一 paused帧的原始revision/date，**实际Full CombatID与完整双方成员**、本军真实CUnit/CArmy身份、当前人数、已观测commander/knight身份。只记录已有公开字段，不能把路径上的假想敌我分区当成本军已参战。
2. 一次正常时间推进后：对已知CombatID回读phase/day/winner及双方membership，对实际受影响军队回读人数、in_combat/retreating、当前省份与实际路线。若当前 .3 reader已提供各entry starting/current/soft/hard与owner ledger则消费同帧原始值；不沿用 .19 的公式解释把当前缺失数值补出来。
3. 自然终局：消费已有terminal journal的该CombatID记录/normal result、结果记录与先前cursor，再看原army backlink、撤退路线和幸存人数。仅 `combat_not_found`、军队 `in_combat=false` 或 ACK 不足以单独宣称胜利/stackwipe；具体终局以已存在的原生结果字段为据。
4. 人物与战争增量：已有查询能回读时，对此前实际commander/knights作 alive/伤势/囚禁与jailer差分，记录新增真实俘虏；同一WarID回读实际score/termination状态。已实际回读且没有人物变化才记零，未读取则保留未观测，不用基础权重预测谁该死。战斗胜利与整个派系战争结束分别记录。

兵力差分要连同增援/离开membership解释；`战前人数−当前人数` 不能自行等同永久死亡。追击后软伤可能变化，军队退出combat也可能是撤退或终局后的路线转移。首战回路可以先交付真实操军与观察到的战果；未采用完整AI预测/人物 RNG/损失模拟时，记录质量差距即可。

Readiness：本包是 `research` / 当前安装版 stock 输入账本；不新增native代码，不声称static-ready或live。遗留：.3自动结束/wipe分支及原生定点损失公式由原生链工作包验证；当前人物/俘虏查询的具体可用字段由现有bridge消费方决定。没有Git commit/push，协调者接纳后将本包链接并并入当日日报/周报。
