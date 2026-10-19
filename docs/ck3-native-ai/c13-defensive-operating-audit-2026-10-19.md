# C13：防守停滞、军费机会与真实决策边界

machine_id: `xenoamess-full-tower-eb9d2c1186`。审计身份于 `2026-10-19T13:41:19Z` 通过 `tools/ck3_live_run_id.py machine` 核对；运行包封闭时间 `2026-10-19T13:34:24.399709Z`。本次仅读 owner 指定的 closed 小件、M5 的真实 DTO 投影与冻结 src12 源码；0 新 RPC、0 活 Driver/SAVE/桌面读取，未改现场或策略。精确路径、大小、SHA-256 与纯函数探针见[证据 JSON](evidence/c13-defensive-operating-audit-2026-10-19.json)。源码基线 `d789ece0cb15a7e45a251fec266aa409d22e5286`，不将后续 canonical 修复追认为当前 C13 已采用。

C13 的主要问题是已有观察续行路径拒绝了真实 Army DTO，进而让普通军费评估也无法获得回合。当前证据支持修复此停滞；还不足以声称有一条已经验证、能持续打赢两场防守或避免失地的方案。不能把“仍有986名已集结士兵”当成胜率，也不能把“目标不在直辖集合”当成领地安全。

## 当前真实局面与四个零天回合

FULL6347 从3033到3037个 settled cycles，日期始终为 raw53202696，即 `1073.5.15/day2432`；当前玩家40526，episode `native-40526-1bec95182886`，frame native1280/public2、connection generation3。6355 的当前钱包为193.02034金。

| 原 AUTO | 实际选择 | 能证明什么 |
| --- | --- | --- |
| 6348 | `query-war-results-window-v1` | 到期的战果窗口观察；不产生游戏天数或战果。 |
| 6350 | `query-war-termination-options-16777269` | 同帧查询第一场战争的当前终战条件，query51。 |
| 6352 | `query-war-termination-options-16777278` | 同帧查询第二场战争的当前终战条件，query52。 |
| 6354 | `query-army-strengths-v1` | 原生兵力观察；不产生军队命令、战斗或游戏天数。 |

这四次都是实际只读消费，不是四次成功运营。6356 随后 `blocked`，`selected_step=null`、phase=`native_war_no_safe_exact_route`，无提交/执行信用。唯一具名拒绝为2633省的 `current_exact_siege_rejected/not_player_besieging`。该列表不能证明全地图所有移动目标都被原生逐一判为非法。C12 旧终战缓存的到期时间不能继续充作 C13 尚未查询的理由：两场终战条件在这里已经重读。

## 目前哪些选择有证据

| 方向 | 当前实际消费及限制 |
| --- | --- |
| 守战16777269 | 玩家为主要防守方，county_conquest_cb，score−26，战争296天；原生分解为占领26、战斗/囚禁/计时均0。目标标题2196。 |
| 守战16777278 | 玩家为主要防守方，individual_county_de_jure_cb，score−90，战争1295天；分解为战斗33、占领31、计时26、囚禁0。目标标题2488。 |
| 当前军队 | own public33554800在2633，regular/可控、静止、无路线、无交战/撤退。原生 siege184549422 的 selected besieger 是另一支不可控军队67109009；own occurrence 明确 `eligible=false`。当前不能把本军算作正在围城，更不能据此发动突击或领取围城推进成果。 |
| 当前敌军观察 | 三个不同敌军ID合计2999，own已集结986；单场分别531、2468。当前敌军在2604/2619且已观测路线为空。它们用于当前操作风险；没有未集结援军、未来到场或战斗胜率信用。 |
| 白和/胜利 | 两场 CB 都允许存在白和这种结果，但当前原生 validator 对白和与胜利均为false、available=false。AI acceptance 数字不能覆盖这个准入结果。 |
| 投降 | 两场原生 surrender validator/available/auto_accept 均true；具体CB条款 `terms_observable=false`，recipient response unavailable。它是可提交的败战动作，不是已经比较过长期损失的优选，更不是本次授权执行的动作。 |
| 建设与军费 | 当前 war priority 对两场都保护现金、延后可选新建；优先16777278再16777269。此保护已在6356真实 plan 消费，不能说原策略完全没看战争。 |
| 雇佣/退款/借款 | 本帧没有新市场报价、退款报价、贷款条件/到账或对应提交后验。旧6337市场属于6天前，不能用其558候选/eligible0替代本帧。没有依据将未知融资或取消退款计为可花现金。 |
| 外交及家族 | plan 仍携带 dynasty continuity、当前统治者婚姻与继承目标，但这个只读前缀没有一个已准入并执行的结盟/婚姻/借款等替代动作。目标事实不等于存在当前合法候选。 |

两目标都未命中当前 root 的主头衔或直辖交集，`defeat_title_transfer_verified=false`。这保留了目标身份信息，却没有完整揭示封臣、realm 或后续继承的损失；此处没有完整 realm county/Q/K 评分，不能重演“把直辖当全领地”的旧错误。本次只审当前两战争，不将旧30年10→2归到它们。

## 为什么已经有一天观察分支，仍然长期没选

冻结 src12 的 `_stationary_excluded_siege_one_day_watch_plan`（strategy.py:21764–21866）已经为这种“本军静止、明确不贡献当前围城、无已观测来袭路线”的情况设计了至多一天、speed1、日期观察后重规划的分支。它不移动、不突击，也不证明未来接触安全。

但该函数21813–21814又要求 `Army.native_carmy_id`。真实 Army tuple 没有这个字段。既有 `siege_subject_contribution_v1.py:17–43` 的正确合同，是在当前 province occurrence 中按 `public_unit_id == subject.army_id` 关联 native CArmy；本场该行给33554783，own public ID为33554800，而不是从 Army 直接取 native pointer。因此旧判断实际是 `33554783 == None`，必定拒绝。此前 synthetic fixture 借用了独立 strength DTO 的字段塞入 Army，掩盖了这条拒绝。

M5 独占修复了此接缝，并用[真实 DTO fixture](../../ck3_autonomous_player/tests/unit/fixtures/war6356_current_army_dto_v1.json)及[纠正证据](evidence/war6356-army-dto-schema-correction-2026-10-19.json)保留旧失败、移除虚构字段与未知 occurrence 拒绝。其定向32项通过属于离线结果；本审计不重复矩阵，也不把它当成 C13 已推进一天。可持续收益是让真实小步观察回到普通规划器，而非证明这个站位已经有效保地。

## 一个被连带饿死的实际消费者

冻结 src12 `bridge/service.py:2399–2410` 在普通策略/撤退规划后调用现有 `plan_war_mercenary_turn_v1`。该 consumer 的94–112行只在已选择 life-advance 或 contact-horizon 的 quiet 机会继续。6356 `selected_step=null`，因而在读取 construction ledger、融资能力缺口、mercenary ledger与当前市场之前返回。真实 plan 也没有这些后续评估字段。

这解释了“保军费 reasons 已产出，为什么没有新财务机会评估”。修复一天观察路由可重新给现有 consumer 抢在时间推进前查询市场的机会；查询、原生合法报价、及时到场与实际雇佣后验仍是不同层次。本次没有证据说明新的市场一定有可买且能到场的公司，或193金足够覆盖报价、维护与承诺。

另一个明确的政策边界是 `war_emergency_budget_v1.py:17–39`：应急破常规现金缓冲的特例覆盖已识别主头衔/major direct 防御或合格政治生存风险并要求恶化证据。对6356原始 priority 两行执行冻结原函数，结果均level0。当前 −90战争的目标不命中该范围，derived priority 的局部敌占/攻城数组也为空；战争总占领分不能被伪装成缺失的具体省份身份。此结果不是原生购买不合法证明。若要扩展到其他 realm 内县目标，需先把目标持有人、realm关系、CB实际损失与当前可改善局势的报价接起来，作为策略变化评估，不能仅因负分或兵数改现金授权。

## 本轮留下的具体经验与后续边界

1. 实际 consumer 的 DTO 合同必须用未增字段的原生小投影验证；不能从另一接口借身份字段修饰 fixture。M5 已存独立[持久工程经验](../../tools/g2_saved_campaign/war_observation_dto_lessons_20261019.json)，不把旧初局运行资格闭包扩大，也不冒称该记录已被运行智能体自动加载。
2. 将“没有可执行军队命令”误提升为“没有可合法观察的一天”，会连带阻断普通军费消费者。验证恢复时要分别核原路由、军费查询机会与真实日期前进，不能只看 selected step 或单测。
3. 保留现金、防止可选浪费已在当前计划生效；保留资金却没有当前可用采购/融资信息，仍不能完成防守目标。下轮应先沿修复后的原消费者核当前报价及融资缺口，禁止旧报价续命或预支未知贷款。
4. 白和当前不可用是已确认条件；投降材料比较不全是另一条缺口。不得把危急战分、兵数或可提交投降代替长期效用比较。当前无法保证保地，也没有理由凭这组小证据擅自投降。

本审计只新增文档与小证据，不改 M5 的策略、当前现场或融资政策。code3 预算上限48KiB；最终实际净增与 pins 随闭场报给 Root/storage。小记录复核日期 `2027-04-17`，原 closed 包的保留期限继续由 owner 按通用存储策略管理，未来重型写入预留0。
