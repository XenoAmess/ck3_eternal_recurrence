# 普通规划器实际消费：优先研究玩家本人的头衔宣称

**找到并修正了一处真实的战略排序缺口：明确能为玩家本人争夺头衔的宣称，在普通候选排序里曾排到五个遗物战争目标之后。** 本次改变的是研究目标的战略优先级，不能作为策略等价的性能优化，也不授宣战、胜利或领土增加信用。

`machine_id: xenoamess-full-tower-eb9d2c1186`；本次UTC、实际来源SHA和软件验证在[小证据](evidence/ordinary-planner-objective-priority-2026-10-19.json)。只读本轮已封小AUTO投影、src03/canonical源码和已固定SHA的小型原版文本；0Game/MCP/OBS调用，0SAVE/Driver/媒体正文读取，0热改COW。所有后验均是过去已完成请求或离线软件结果。

## 零日轮实际在做什么

runtime提供了 `N/p51-fresh1066-v20261019-prepare01/CLOSED-FRAGMENT-0161-0194-COMPACT48.json`，78,837 B、SHA `1b522bd23573b3bf3ac52875e731788da8567408c94831cdfc2ef4b2c3464601`，封定于2026-10-19T04:34:47.077294Z。它覆盖游戏第38→61日，不是完整0→61日。业务来源为 `063531c4b2bc64f52b80a78b8a2b8e9f55112964`。

| 已读小AUTO | 实际消费/结果 | 范围 |
| --- | --- | --- |
| 162/166/170/174 | `query-war-results-window-v1`，观察战争结果窗口 | 四个不同当前帧的零日查询，不能计成推进或胜利。 |
| 164/168/172 | 宣战机会cooldown后原`life-advance`分别推进8/8/7日 | 这23日真实推进；等待30日是既有政策，不是本次新增限流。 |
| 178/180/182/184/186 | 五个`reclaim_relic_artifact_war`目标的原生力量查询 | 同一暂停native98，依次29373/29732/32563/36058/36723。 |
| 188/190 | 玩家本人的`claim_cb`，target7219，claimant31254 | 原生力量查询目标33388/38828；晚于上述五次遗物目标。 |
| 192 | `make_tributary_cb`目标26904的原生力量查询 | 朝贡CB保留为合法候选，不能因target_titles为空断言没有政治/领土后果。 |
| 194 | 重复before-submit callback异常 | 原错误保留；不能当已执行行动，也不能重发该未知请求。 |

以上直接读回15份成功AUTO中，12份为零日查询、3份推进。176为614,845 B的索引 `oversized_not_observed`，本次没有读取正文或补造其结果。不能把这个片段的80%零日比例外推为全61日精确统计。178–192的八次力量查询各查了不同目标，不能冒称八次同一RPC重复；问题在研究优先级及投入方向。

另一份已封0131–0143小索引证明137真实执行升级王权，139随后走独立材料验证。因而不能说普通规划器只产reason而没有政务消费。164等已有当前家庭订婚/后继观测，当前risk投影提示partition split；这些观测不等于已经完成继承准备。片段没有新的战争，不能由本次资料检验战时采购、资金门或防御部署实际效果；也没有足够小材料证明可选建设/婚配在全61日内分别被什么条件延期。

`campaign_goal_plan_used`确实只列婚姻/继承连续性两项，不能把它当已经包含领地增长、军费或长期投资的统一战略效用。普通规划器另有真实战争/政务消费者。本次选择修一个已有决策接缝，不用扩大一份目标JSON来冒充这些消费者已优化。

## 来源先于策略

src03与修改前canonical的`strategy.py`全文相同：1,032,197 B，SHA `4dc6d947f7280c42d7471d84975178e5cabf7a4815271cdee00a2f2bbb3b6193`。旧 `_preferred_native_declaration` 用`"claim" in key`进入claim优先档，`reclaim_relic_artifact_war`也命中；双方title数再比较时，遗物战的0个title排到玩家claim的1个title之前。实际178–192的顺序与这个消费链一致。

先核[Native26已冻结来源清单](evidence/native26-actor-zero-mod-source-admission-2026-10-19.json)，再读其 `00_claim.txt`，20,230 B、SHA `887bf0197401cb17cb4588978add556ab6b429bf55cb482e3e5f2d0e8351cfd4`。472–487创建`conquest_claim`变更，将`target_titles`与`scope:claimant`传入`setup_claim_cb`后resolve。因此只有claimant确为当前玩家，才能提升为玩家本人的头衔目标；替别人的宣称开战不等于自身扩张，实际结算仍需引擎解析和独立后验。

另核既有跨机来源知识的 `01_ep1_wars.txt`，本次当前机器读到的16,701 B全文SHA仍为 `21c1ab2e4fef36b869469bcc0d28b9c18efc026d63de62af708642cde289eb95`。441–537胜利分支中的直接对象转移是符合条件的artifact交给attacker，没有直接title/vassal变更段。其他资源/政治helper和间接后果保持区分；不从“没有target_title”推任何未知CB没有领土作用。该静态读取只证明这些文本，不补授当前游戏加载来源或安装业务资格。

## 最小落地与边界

新增[独立优先级叶](../../ck3_autonomous_player/src/xar_autoplayer/declaration_objective_priority_v1.py)，仅当以下条件全部满足才进入优先档：当前玩家ID为正整数、原生候选`source=native`、exact`claim_cb`、claimant等于当前玩家、目标头衔列表非空且全部为正整数。缺claimant/空title/他人claim/未知CB/朝贡均保持原fallback。

普通 `_preferred_native_declaration` 主路及alternative路接入该档位，当前玩家ID取已有snapshot。**该档位只用于尚未评估的研究目标，并放在原evidence/native power排序之后；已有assessment的目标不使用该优先档。** 因而已评估为不利的本人claim不能遮蔽更好的已评估其他CB；原生最终合法性和force admission保持原门。该改变没有把力量比变成胜率、没有增加任何可执行step、没有放宽当前军力阈值，也不承诺目标7219实际取得或一定值得开战。

从真实178–192抽取的[10KB八候选小夹具](../../ck3_autonomous_player/tests/unit/fixtures/robert_v20261019_declaration_order_178_192.json)，包含原来源SHA、机器、帧、原生候选与力量值。它不是完整宣战集合或完整snapshot，离线结果是：

| 同一已观察子集 | 旧排序控制 | 新策略 |
| --- | --- | --- |
| 尚未查询力量时 | 遗物战29373先研究 | 玩家本人claim33388、目标title7219先研究。 |
| 已有192结束时八份同帧力量结果 | 力量排序先选朝贡26904 | 继续按原排序选26904；不让较差的已评估claim饿死其他机会。 |

第二行是192已完成之后的候选排序离线推演，不表示194实际已产生这个plan，更不是新实机宣战。首次研究顺序提前，不意味确认会少查几个目标；若所有候选都需完整评估，仍会合法查询。未知/朝贡保留fallback，任何未来缺输入仍按原路线合法推进。

初候选曾把objective放在evidence前：6项测试（`d54c73`）通过却未覆盖坏claim遮蔽其他已评估机会。Root独立审阅指出这一策略缺口后，最终收窄为仅未评估研究排序，保留初候选源码SHA、回放及原测试历史。增加唯一针对性边界：真实claim33388的己方基础力量低于敌方总力量，而朝贡26904相反，后者必须保持优先。**最终7 tests / 0.001s / exit0**（`5b6ecd`）。原完整 `test_ordinary_prewar_force_admission_v2.py` 在初候选时pytest一次执行 **41 passed / 1.42s / exit0**（`aad988`）；它证明当时原force门未改，不能外推初候选已覆盖上述饥饿边界。最终没有修改任何force阈值/legality，未重跑整仓矩阵或宣称当前吞吐/战果改善。

本轮由Root合批freeze采用；当前src03冻结树未修改，实际新SDK导入需新来源回执。后续只复用普通AUTO的小plan/result观察其选择，不为本改动增加RPC、重放194或强行开战。小型源码/记录按通用存储策略1.0.0，新增总量低于64KiB、无重型输出/删除/预留；原片/SAVE期限与容量资格没有刷新。
