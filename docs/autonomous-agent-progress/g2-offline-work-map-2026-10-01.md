# G2 八项里程碑：仍可后台施工的实际缺口

2026-10-02 授权更新：项目所有者已全面开放 faith/religion、rite、doctrine、tenet、fervor、改宗、宗教改革、clergy、holy order、圣战与大圣战的深入研究与实现。下列冻结记录中的旧宗教暂缓仅保留当时事实，已全部撤销；详见[当前授权](../../AGENTS.md)。2026-10-03 项目所有者已取消全部非战限制，全面授权战争与战斗的研究、原生观测、实现、策略及实机执行。 旧战争研究停止、执行OFF、非战范围及战争维护者独占规则均已撤销；冻结产物中的OFF/零动作仍保留为当时事实。原生 AI 研究优先、exact-build 绑定、Robert 29829 原普通战役唯一入口、玩家限定和最小化/不抢焦点继续执行；授权不等于能力完成。

后续施工入口：先沿[宗教整合](../ck3-native-ai/ck3-1.20.0.2-religion-integration.md)、[教义与Tenet](../ck3-native-ai/religion_doctrine12002_overview.md)和[改革](../ck3-native-ai/religion-reform12002-overview.md)的原生树与已有只读查询补齐当前exact-build输入；自然宗教事件按真实选项、作用域与效果接回事件消费者。Holy order等未闭合分支继续定位原生资格、成本、对象状态及结果查询，先交付只读bridge/MCP，再据罗贝尔paused材料设计和验证策略；旧版实机证据不自动继承。

2026-10-01，Asia/Shanghai。用户追问八项 G2 是否已经完全没有不占实机的工作。本次四线程只读核对冻结主线 `0acff9b35f778de3d70ebb48816841986f692127` 的需求、生产源码与原生专题；未查询或操作 CK3、进程、pipe、桌面、Steam，也未重跑已 GREEN 的验证。

**仍有可离线施工的工作。** 13:11 的交付已完成当批 LIFE／建设／FAMILY／campaign 状态／事件合同／JOINT 修复及文件准备；“现在确实只剩实机”不能作为整个 G2 的结论。下面是尚未移植或实现的生产能力，不把旧 primitive、既有消费者或只缺自然阳性的分支重新列为开发工作。里程碑分母仍为 **3/8**。

## 八项逐项结论

| 里程碑 | 现行状态 | 可继续的离线工作 | 确须实际游戏的边界 |
| --- | --- | --- | --- |
| M0 三路战争退出 | complete | 本次未发现需要重做已闭合窄路径的依据；更广战争输入归 M5 | 新版及更广场景资格不能由旧结果外推 |
| M1 实体目录与核心回合 | complete | 新版 core/campaign 投影已交付；完整派系威胁读口归 M4 | 新增 provider 的同帧 paused 互证 |
| M2 自然事件语义循环 | in_progress | 当批 192 个有界契约源适配已交付；按实际新版 RED 做后续具体源修复，不另造自然事件等待 worker | 指定自然事件、多个选项的材料结果与下一 turn；source-compatible 不等于完整 utility |
| M3 继承与领地存续 | complete | 不重做已有继承／estate reconciliation；跨继承高层目标续接归 M7 | 自然死亡、后继角色继续与更广矩阵 |
| M4 和平治理 | in_progress | **新版议会候选／四类 gate／任命、完整派系威胁、赠礼原生链** | 新版真实场景及合法动作的独立后置、next-turn/cold、两年窗口 |
| M5 家庭外交与完整战争 | not_started（沿用正式 milestone 状态） | **战争现金来源与 producer、多战争资源聚合、婚配长期承诺、宣战参与者与未来补给输入** | 实际同帧机会、真实资源争用与完整选择→行动→结果循环 |
| M6 谋略／制度／活动 | not_started（沿用正式 milestone 状态） | **既有 Sway、realm law、Feast 链的 1.20 原生迁移与结果观测**；Found Kingdom capture 作为备选 | 一项谋略完成、制度／囚犯动作、决议或法律、完整活动生命周期 |
| M7 身份适配与长期资格 | not_started（沿用正式 milestone 状态） | **普通 campaign 高层目标跨 checkpoint／继承续接、既有 GOV observer 的新版 feature profile 与封建消费** | 多 ruler／seed／government、百年／整局及实际冷恢复资格 |

`not_started` 是原有正式里程碑字段，不表示该域从未写过代码；已有私有读口、动作或 primitive 继续保留原范围。这份检查不修改八项完成定义或将离线 fixture 晋级 live。

## 第一波：治理所需的新版原生口

1. **议会完整链迁移。** [新版 council 专题](../ck3-native-ai/ck3-1.20.0.2-nonwar-council.md)只恢复现任与 active task 状态。现有 [typed 任命绑定](../../ck3_autonomous_player/native_bridge/include/xar_bridge/council_assign_councillor_action_v1.hpp)仍锁旧版本／EXE；候选 producer、`IsCouncillor`、`IsGuest`、候选 pending、replacement `CanConfirm` 仍在旧 [final gates](../../ck3_autonomous_player/native_bridge/src/council_production_final_gates_v1.cpp)与 [steward binding](../../ck3_autonomous_player/native_bridge/src/council_composition_steward_candidates_binding_v1.cpp)。可后台重新闭合新版调用链／临时 vector 生命周期，复用现有 DTO、shared runtime、typed submit 和独立 receipt，补实际 provider／版本分派／wire fixture。四类真实阳性仍由实机提供。
2. **派系威胁从 count 升为真实生产数据。** [公共 reader](../../ck3_autonomous_player/native_bridge/src/player_faction_alerts_v1.cpp)第 205–225、344 行仍走 `MaterializeCountOnly`，rows 与县域 exposure unavailable；新版 campaign-root 也只投影 targeting count。现有完整 DTO／consumer／部分旧版 row getter 可复用。可离线迁移 full faction IDs、opaque type、目标、nullable leader、members、at-war 与原生最终 danger/power/discontent 输入，再接同一查询。数量与真实危险度不同，原 R0348 无人物成员不能让 gift-only 策略代替威胁识别。
3. **已有 gift 链的 native 接收端迁移。** [receivers](../../ck3_autonomous_player/native_bridge/src/faction_gift_receivers_v1.cpp)仍使用 `Exact11906`、旧 land/faction 布局及原生互动入口。正式 consumer、pending、receipt 与 cold 接线已经存在；只迁移新版 final CanSend、原生费用／opinion preview、typed submit 和独立后置 receiver。依赖上一项真实派系数据，有合法人物成员才进入实机动作，不能制造赠礼对象。

## 第二波：M5 的共享资源与长期输入

- **战争现金来源。** [正式 collector](../../ck3_autonomous_player/src/xar_autoplayer/m5_formal_proposal_collector.py)第 231 行明确没有 runtime producer；[金额模块](../../ck3_autonomous_player/src/xar_autoplayer/m5_war_cash_resource_v1.py)只是外部输入→收据。[R0266 原生账本](../ck3-native-ai/r0266-war-cash-resource-2026-09-28.md)第 24／28 行已给出维护资源 helper，下层虚表目标和经济槽位仍未闭合。后台可继续 1.20 exact 来源逆向、只读 producer 和现有收据适配；当前维护、未来期限与政策储备分别保留语义，不以净月收入猜战争成本。
- **多战争资源聚合。** 同一 collector 第 159／257 行明确仅支持一场、返回 `multiple_wars_cash_aggregation_unavailable`。在真实来源闭合后，为全部 WarID 聚合共享军队、pending 金钱、盟友／角色占用与期限。共享军费先闭合归属再合并，不能简单按 WarID 重复相加；沿用现有预留与 dispatcher；2026-10-03已取消战争意愿与执行的非战授权限制，策略调整先依据原生树和真实输入，具体现场/date hold按当时运行事实协调。
- **婚配长期结果与义务。** [机会选择器](../../ck3_autonomous_player/src/xar_autoplayer/m5_observed_opportunity_selector.py)第 271 行仍将 `child_dynasty_result`、`alliance_result`、`alliance_war_obligation`、`betrothal_break_cost` 列为 unpriced。人物家系／年龄／生育 provider 已交付；下一项是候选 lineality 的结果、解除婚约代价与具体联盟战争义务的原生最终结果口，先原生树／ABI／query，再策略消费。
- **真实参战与未来补给。** [joint shortlist](../../ck3_autonomous_player/src/xar_autoplayer/m5_joint_shortlist.py)第 23–24 行及 [prewar 专题](../ck3-native-ai/prewar-encounter-inputs.md)第 557、731–741 行仍缺 declaration-bound participants/allies 与假设集结／未来路线来源。可以后台追原生最终结果与实现只读 provider；既有 current-army supply 不等于未来补给。该域旧 war owner 独占源链与政策的分工限制已于2026-10-03撤销；后续可直接推进原生树、只读provider、策略与Robert原战役实机，现场操作仍按当前唯一实例协调。

已有分析 intake、shortlist、budget selector、dispatcher、正式 proposal collector 和单次 pending 预留不能重报为“联合策略完全未实现”。历史已有 1 建设＋5 婚配的同帧 eligible 提案；缺口也不能简写成“还没有五候选”。

## 第三波：M6 复用现有实现移植

- **Sway：** [现有 binder](../../ck3_autonomous_player/native_bridge/include/xar_bridge/active_scheme_state_v1_private_native_binder.hpp)仍冻结 1.19；可迁移活跃实例／manager／CanSend／opinion／typed submit 及结果观测。R0342 新 PID 已真实读到 matching Sway、ledger applied，未完成谋略。只追 Sway 完成／失败与实际好感后置，不建另一套通用谋略框架。见[配对证据](../ck3-native-ai/sway-pending-checkpoint-pairing-2026-09-29.md)。
- **Realm law：** [生产 transport](../../ck3_autonomous_player/native_bridge/src/realm_law_paused_private_transport_v1.cpp)仍调用 `...11906` reader；可迁移 active collection、law DB、候选、最终 CanEnact、完整费用／原因，再为有价值的一条法律复用现有 LAW8 source/resolver/receipt。R0334 的 CA0／CA1 和 207 prestige 是旧版真实读口，不能重造或把“合法可负担”当成必选。见[既有 final terms](../ck3-native-ai/realm-law-final-terms-11906.md)。
- **Feast：** [Stage5 Start](../../ck3_autonomous_player/native_bridge/src/activity_feast_stage5_start_v1.cpp)及 [common commit](../../ck3_autonomous_player/native_bridge/include/xar_bridge/activity_feast_stage5_start_v1.hpp)仍锁旧 ABI。可迁移现有 owner／stage、location、final gate、四费用、guest join／arrival、hosted identity，再追原生完成／失效与收益口。formal Start consumer、value policy 与 following-turn 已存在；R0403 的 CanStart=false 负结果保持，不能造资格或把 Start 当成活动完成。见[既有 formal entry](../ck3-native-ai/activity-feast-stage5-start-formal-entry-1.19.0.6.md)。
- **备选 Found Kingdom：** [现有内部路线](../ck3-native-ai/major-decision-found-kingdom-internal-route.md)第 44–63 行明确生产 precondition 身份/capture 未齐、postcondition capture 未实现。可补单一定义的新版 capture 并复用 DECISION8。M6 接受一项非宗教 decision **或** law，先交付已有法律路线，不同时展开两个新矩阵。

本页初期范围曾暂缓一般宗教与 holy order，该限制已由2026-10-02全面开放授权撤销。宗教、holy order与以上其他工作均可先完成原生树／ABI、provider、同一 MCP 与必要 fixture，最终最多 `static-ready`；完成生命周期与收益仍必须实机。Holy order缺失的原生资格、成本、对象状态和结果查询是可继续施工入口，不能因旧禁令停工。

## 第四波：M7 的连续整局输入

1. **普通 campaign 高层目标续接。** [driver](../../ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py)当前保存 episode/checkpoint/history/succession expectation/lifecycle，继承新建 episode；[现有 plan](../../ck3_autonomous_player/src/xar_autoplayer/strategy.py)第 19926、19970、20007 行是 one-life-visible-outcomes-v1，死亡结束该 episode，reader 仅接受 `one_life_roguelike`。可复用 priority/focus 消费链与 persisted-v2，补普通 campaign 语义目标／进度在 checkpoint 和继承后的保留及下一 plan 消费。已有 [继承合同测试](../../ck3_autonomous_player/tests/unit/test_succession_transition_contract.py)第 520／644 行覆盖 persist→restore→successor→formal auto_turn，可扩同一 fixture。不能只加一个永不消费的 schema 字段，也不复制 driver 或继承系统。
2. **GOV observer 的新版封建消费。** [既有 binder](../../ck3_autonomous_player/native_bridge/include/xar_bridge/government_runtime_adapter_bridge_binder_v1.hpp)锁旧版本；[observer](../../ck3_autonomous_player/native_bridge/src/government_runtime_adapter_observer_v1.cpp)的 44-key profile 含 `barter_troops`，而 [新版 producer](../../ck3_autonomous_player/native_bridge/src/ck3_12002_features.cpp)已移除它、加入 `by_god_alone`。数量同为 44 不能视为同一输入。沿现有 observer/source adapter/binder，先完成新版真实 feature producer→feudal core selector→默认关闭的私有调用链；其它政府保持既有 `adapter_spec_ready_not_implemented`。不重建 registry 或宣称 18 政府实现齐全。

高层目标收益校准、独立 seeds、跨政府及百年／整局资格需要实际材料。离线 replay 不增加这些分母；2026-10-03已撤销战争授权限制，实际现场占用仍按当前运行事实协调。

## 并行与验收安排

下一轮可同时推进议会、派系威胁、战争现金、Sway、realm law、Feast、campaign 目标记忆、GOV feature 消费；gift、多战争聚合分别跟随其输入依赖。源码文件可以分域并行，公共 CMake／bridge／mailbox 由单一集成 owner 接回，用 64 jobs 联编。

每包复用现有 DTO／MCP／消费者与已经通过的证据；新增或变更的原生输入先冻结 1.20 EXE 与原生树，随后实现和一次必要聚焦验证、立即交付。实机只承担该包实际 paused／动作／结果／next-turn／规定 cold，不阻挡尚有施工入口的其它包。

## 14:33:47 实际实施入口

用户已要求执行并提高并行，以上12个实际包及中央接线进入施工。状态、测试、commit与实际剩余项维护在[实施账本](g2-offline-implementation-2026-10-01.md)，本页保留13:57源核对的历史判断。开始施工不代表新增能力完成。
