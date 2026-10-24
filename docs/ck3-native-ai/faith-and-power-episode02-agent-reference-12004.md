# 信仰引擎二期：游玩智能体研究入口（1.20.0.4）

本页供游玩智能体在制定宗教行动前查阅，汇合二期机制、来源、需要的当前观测和反例。导演案和视频不是策略规则。知识查询入口为既有 `ck3_query_holy_site_planning_knowledge_v1(action, ck3_build="1.20.0.4")`，其 `knowledge.episode02_research` 返回六个相关专题及仓库相对路径；它不读取游戏、不提供当前许可，也不自动提交行动。

当前接入范围：研究文档可从共享索引找到，结构化摘要可经 MCP 查询；普通 `auto` 尚未自动调用这些二期摘要。拍摄用受控案例也不代表普通规划器已经具有自主朝圣、建制或大圣战策略。新增事件来源分析已持久化，5001／1060／1020／4100 的完整实例合同尚未注册，事件策略不能据此伪造原生实例或选项编号。

例如查询参数 `{"action":"demote","ck3_build":"1.20.0.4"}` 后，先读 `knowledge.episode02_research.topics.site_effects_and_cache`，再沿其 `documents` 查详细来源。朝圣与建制是现有圣地规划查询提供的相关研究，不是新增可执行 action；不能把它们写进该接口的 action 枚举。

## 使用次序与证据等级

**朝圣机制当前优先入口（2026-10-22）：**先读[当前知识说明](../../promo/ck3_faith_and_power/episode02/docs/pilgrimage-current-knowledge.md)及[机器可读索引](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-current-12004.json)。索引绑定七包14份原件，以精确JSON Pointer继任旧unknown，拆分已闭结论与真实未闭；另绑定本轮实际简中[活动／旅行术语](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-v6-localization-options-12004.json)、[宗教／人物术语](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-v6-localization-religion-12004.json)及头衔等补充。旧来源中的“博学传承／私人信条／旅行主管”等不作为官方名称依据。当前索引可直接查阅；本轮未修改既有MCP摘要或auto路由来自动消费它。

1. 先核实际 CK3 build、原版资源 SHA 及当前运行时能力。版本不符时本页只作研究线索，不能沿用数值和私有接口资格。
2. 查询相关知识，再按下表获取当前角色、完整 ID、Faith、Rite、日期和原生帧；缺失值保持 unknown，不视为零或 false。
3. 核实原生最终许可、完整费用、应急储备、目标与替换物，以及持久 once 账本。提交一次；结果未知时先查原动作，不能重试或换账本规避。
4. 独立读取后态。ACK、定义效果、窗口文字、角色聚合和单来源净收益分别保存。用于下一决策的必须是新鲜观测。

资源文件定义属于静态知识；来源调用链说明 consumer 条件；离线消费者证明接口合同；实机证据只证明指定机器、场次和当时局面。它们不能相互替代。

## 可复用的六个专题

| 主题与研究入口 | 规划时必须读取 | 可复用结论与边界 |
| --- | --- | --- |
| [装备、展示与供奉](../../promo/ck3_faith_and_power/episode02/docs/research-artifacts-and-site-effects.md) | 个人使用 read／post、两类 owner、实际槽、替换物、CanEquip／CanUnequip、物品定义和当前角色总量 | 三种槽域分别判断。`item_modifier_definition` 是定义，角色聚合含全部来源，均不是该物品净增。供奉还须逐 Faith 核认可、县主及当前 Rite；不能只比较 rarity。个人接口见 `ck3_query_player_artifact_personal_use_v1`／`ck3_query_player_artifact_personal_use_action_post_v1`。 |
| [主要关系、受益人与缓存](holy-site-effect-observation-12004.md) | 每名受益者自己的 Rite、Faith、主要名单、县主关系；site cached world state、当前 relic evaluation、人物 aggregate 分开读 | 同 Faith 不代表同 Rite。cached Active／rarity 与即时重算不同，两次相等也不能证明角色缓存已刷新。主要关系改变或支付成功不等于属性净增；`site_attribution_observed=false` 与贡献 unknown 必须保留。 |
| [麦加类型与骑士效果](../../promo/ck3_faith_and_power/episode02/docs/research-artifacts-and-site-effects.md) | 独立完整 site ID、当前类型／关系／Rite、实际认可稀有度、`actual_knight_effectiveness_breakdown`、同帧身份与后态 | 原版县主角色固定骑士效率 `+0.05` 与 Faith scaled `+0.01 × R`、`piety_level_impact_mult +0.01 × R` 是不同项。Knight reader 不读取后一项，不能由骑士总量推出虔诚影响或其他属性；不得重放已消耗的另一地点意图。 |
| [普通朝圣](../../promo/ck3_faith_and_power/episode02/docs/research-pilgrimage.md) | 当前目的地可选性、最终 CanStart、完整十槽活动费用、钱包／储备、Start once 状态、主办活动身份、旅行与事件后态 | 配置活动费不是整趟旅行总费。Start ACK 不等于已出发；活动缺席不等于已归返。抵达、阶段结束、奖励和归返分别确认。现有 `ck3_query_player_pilgrimage_planner_v1`、`ck3_query_player_pilgrimage_activities_v1` 受运行时能力门控制。 |
| [精神领袖建制](../../promo/ck3_faith_and_power/episode02/docs/research-spiritual-head-and-ghw.md) | 实际 Faith／main Rite／宗教领袖、控制与县主条件、奉献等级、完整决议报价／可负担／CanConfirm、原账本、独立领袖／头衔／钱包后态 | 普通圣地可满足脚本计数，仍须全部当前条件；Rite head 不等于 Faith religious head。旧 create_faith 场景不是 create_hof 证据。展示、报价、一次 Confirm 与建制结果分列。 |
| [大圣战](../../promo/ck3_faith_and_power/episode02/docs/research-spiritual-head-and-ghw.md) | 同一当前局面的 Religion／Faith／global 解锁变量、制度、领袖、战争状态、当前 launch 候选及详情 | 解锁文本、能力就绪、可发起条目和实际战争是不同事实；只读两次稳定不授 Declare 许可或宣战成功。需独立合法战争流程，不能由建制自动推导大圣战就绪。 |

字段合同以实际生产 reader 为准：[个人使用](../../ck3_autonomous_player/src/xar_autoplayer/bridge/faith_observers_private_transport_v1.py)、[圣地上下文](../../ck3_autonomous_player/src/xar_autoplayer/bridge/player_holy_site_relic_context_private_transport.py)、[技能总量](../../ck3_autonomous_player/src/xar_autoplayer/bridge/character_skill_effects_private_transport_v1.py)、[骑士总量](../../ck3_autonomous_player/src/xar_autoplayer/bridge/character_knight_effectiveness_private_transport_v1.py)。其中 `cached_world_state` 与 `current_relic_evaluation` 分列；实际名字和字段不能由 UI 文案补造。

## 朝圣专题V5：完整输入、特质与公式

2026-10-22追加用户要求的源研究，观察机器`machine_id: 4-8e1c2f1861`；每份JSON分别保存实际UTC、文件SHA、覆盖范围及未闭项。游玩智能体可按以下仓库路径直接查阅。此处是本页的研究扩展索引，既有MCP六专题返回范围按其实际实现，不将本表冒充新增可执行action或自动规划接线。

| 所需知识 | 完整说明 | 结构化来源与应用边界 |
| --- | --- | --- |
| 开始活动的全部选项 | [类型、忠诚、排场、意图、目的地与旅行设置](../../promo/ck3_faith_and_power/episode02/docs/research-v5-setup-options.md) | [配置JSON](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-v5-setup-options-12004.json)。先核当前DLC、角色资格、完整可选集合与当前费用；静态定义不等于本次可点。 |
| 不同宗教规则与朝觐 | [五档朝圣偏好及Hajj调用链](../../promo/ck3_faith_and_power/episode02/docs/research-v5-doctrines-hajj.md) | [宗教／朝觐JSON](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-v5-doctrines-hajj-12004.json)。逐个消费者区分Religion、Faith、Rite与人物状态；分别核活动、目的地和Hajj自身冷却。 |
| 朝圣者特质全部影响来源 | [获得、XP、倍率、等级效果、移除与活动外入口](../../promo/ck3_faith_and_power/episode02/docs/research-v5-pilgrim-trait-inventory.md) | [完整库存JSON](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-v5-pilgrim-trait-inventory-12004.json)。区分直接状态变化、条件效果和纯AI／事件机会；不能从特质推断已完成几次朝圣。 |
| 费用、虔诚和朝圣者经验 | [有序公式及全部参数](../../promo/ck3_faith_and_power/episode02/docs/research-v5-cost-reward-xp-formulas.md) | [公式JSON](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-v5-cost-reward-xp-formulas-12004.json)。脚本请求、引擎资源调整、当前报价和最终后态分别判断；未知项不代零。 |

后继[精确等级与初始化a02](../../promo/ck3_faith_and_power/episode02/docs/research-v5-native-tier-12004.a02.md)及[结构化来源](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-v5-native-tier-12004.a02.json)闭合源等级块无预差分累计、直接初始化0与重复授予不重置。较早各JSON保留封稿时的unknown，不将它们误作当前仍未研究；正文头部已追加后继说明。AI根字段与track modifier单列，未授组合AI行为总值。

后继[意图候选原生链](../../promo/ck3_faith_and_power/episode02/docs/research-v5-intent-candidates-12004.md)及[结构化来源](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-v5-intent-candidates-12004.json)闭合候选过滤和顺序，明确区分候选出现与按钮可选。共享娱乐在上游是否加入、当前人物完整集合仍未知，不能自行补出第四个动作。

这些文档不授当前实例合同、原生动作许可、未知结果重试或普通auto自动消费。新场次仍须从当前角色及原生完整许可开始；V5导演案用于组织解释，不能替代这些来源。

## 关键来源与已知反例

原版 `common/religion/holy_site_types/00_holy_site_types.txt` SHA-256 为 `0824df55d4cd0a7c6d2c2d8b45bf577cca9ec0e5e1b4a6f699848b8661b17b40`；动态类型来源及完整 source pins 见各研究文档。缓存链来源区分 Rite producer `29CC520 → 24FB270`、角色 aggregate `291C0B0 → 291F080` 与 cached reader `2B0C740`／即时 relic evaluation `265A3F0`；这些来源不能单独证明本次缓存刷新。完整原始 source 合同在下述来源机器 Q/a1-effect-refresh-source-a01/SOURCE-PINS.actual.json，SHA-256 `f0c71136a3a3864c0a1f4b1aaf0530d6bac8a819c9490b63ac353f624bb1fa56`。

以下为历史样本，均属于 `machine_id: 4-8e1c2f1861`，记录汇总时间 `2026-10-20T08:15:32Z`；不能作为另一机器或新局面的输入。原始机器证据根 `E = C:/workspace/ck3-faith-and-power-20261017/episode02`，`Q = E/production-b3-a01/native/qualifications`；外置证据按[通用存储策略](../storage-retention-policy.md)复核，不保证永久可读。

- B15 同 Faith 两名人物的 Rite 不同。地点 27 的主要关系移除和 1000 虔诚付款已证，外交 18／13 与 named Medina +4／+1 未变，缓存新鲜度和净收益仍未知。原 `capture-b15-a01/same-faith-continuation-a01/case-output/a1-same-faith-result.json` SHA-256 `343efbbe8ebd1cd8dcc1b72835fcf2e18624c93610a4876d17d456002d834b7c`。这是否定“关系变化即属性到账”的反例，不是降级无效的普遍结论。
- B17／R0009 Rome Start 的实际主办活动与钱包 243→173 已读回；70 金是该配置活动费。首个自然日后 public pause readback 失败，未完成抵达、阶段结束或归返。原 `capture-b17-a01/SCENE-CLOSURE.actual.json` SHA-256 `5fbfc23af841de14746f123093b5cd37559db69cb01bb8afc80d721514e02757`。该场失败闭场不授完整朝圣信用，旧结果未知的动作不得重发。

## 新事件来源知识

`2026-10-20T15:49Z`补充，来源机器`4-8e1c2f1861`：[historical_char_creation_events.1源码分析](../../promo/ck3_faith_and_power/episode02/docs/knowledge/historical-char-creation-1-source-analysis.json)与[R0013实际实例](../../promo/ck3_faith_and_power/episode02/docs/knowledge/r0013-historical-character-1-observation.json)已持久化。第一显示项会切换玩家，本场15893→41436已经独立证实，不能继续沿用旧人物钱包／收益。该定义原有已分析策略；新1.20.0.4九scope变体已补入共享registry，精确匹配当前作用域、显示次序、enabled及来源SHA后复用第三项保持原人物策略。七项便携消费者通过，不代表第三项已实机执行，也不改变其他未知事件的采集后第一显示项规则。

持久研究：[pilgrimage.5001](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-5001-source-analysis.json)、[travel_start_event.1060](../../promo/ck3_faith_and_power/episode02/docs/knowledge/travel-start-1060-source-analysis.json)。1060 的标题“第一次启程”复用了 1000 的本地化 key，不能据标题推断为 definition 1000；其确认选项不是 Start、抵达或主要奖励。

新增持久资料：[travel_events_cities.1020 来源与实际显示变体](../../promo/ck3_faith_and_power/episode02/docs/knowledge/travel-cities-1020-source-analysis.json)、[1060 的 R0012 原生实例观察](../../promo/ck3_faith_and_power/episode02/docs/knowledge/travel-start-1060-r0012-occurrence.json)、[婚约通知的既有拒绝知识复用](../../promo/ck3_faith_and_power/episode02/docs/knowledge/r0012-arrange-marriage-source-occurrence.json)、[事件与通知独立后态](../../promo/ck3_faith_and_power/episode02/docs/knowledge/r0012-event2-interaction35-post.json)。这些是 `machine_id: 4-8e1c2f1861` 的历史 R0012 观察，1060 原生定义已读为 `travel_start_event.1060`，原窗口独立消失；旧 B17 截止资料原样保留，不追认其当时已查询原生定义。旧 5001 来源分析的截止资料保留原样；新的 R0012 原生实例与独立后态另链，不追认旧资料当时已有实机定义。

1020 仅闭合本次基督教圣地观光的实际显示变体：第一显示项提交后旧 instance 2 消失，同暂停日期钱包减少 50 金、压力 0→15。物品创建和额外 7 天旅行延迟仍只有脚本来源，未独立读取库存或新 ETA；这不是抵达、主要朝圣奖励、归返或整趟旅费结论。婚约 35 的 `accepted=false` 表示实际拒绝，后读 pending 消失；不证明婚姻或全部拒绝效果。后续出现相同 definition 仍须重新绑定当前实例、完整作用域和显示顺序，不能复用 native option 4／instance 2。

后续 arrival 资料：[5001 的 R0012 实例](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-5001-r0012-occurrence-analysis.json)、[4100 来源与显示选项](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-4100-source-analysis.json)、[两事件分别提交后的独立后态](../../promo/ck3_faith_and_power/episode02/docs/knowledge/r0012-5001-4100-post.json)。同一来源机器 R0012 的 5001 已读到原生定义并确认旧窗口消失，压力 15→4；该次按钮前后虔诚不变，pilgrim 特质／XP 未独立读取。它支持来源绑定的 Rome 到达事件，不能推出全程结束或归返。

4100 第一显示购买项的 `effect_indicators.rows=[]`，同时 `complete_effect_set=false`、资源变化 unavailable；空图标列表不能理解为免费。原脚本使用动态 `minor_gold_value` 付款，特定 illustrious 分支再乘 1.25。独立后态证实该次额外扣 31.25 金、压力 4→4、该按钮前后虔诚不变；`activity_log score50` 是活动日志评分，不是 50 虔诚。两事件之间的自然日变化与每次按钮差值分开，不把一次价格硬编码给未来事件。徽章完整 ID／所有权、稀有度、装备和属性仍未独立核实，不能写成玩家已获得可用徽章。

R0014 批次（来源机器 `4-8e1c2f1861`，2026-10-20）：[3001 原版来源分析](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-3001-source-analysis.json)、[3001 实际选择与独立后态](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-3001-r0014-occurrence.json)、[1020 新显示变体](../../promo/ck3_faith_and_power/episode02/docs/knowledge/travel-cities-1020-r0014-display-variant.json)、[五事件完整批次清单](../../promo/ck3_faith_and_power/episode02/docs/knowledge/r0014-event-batch-summary.json)现由同一知识 MCP 的 `episode02_research.topics.pilgrimage.documents` 显式返回。3001 第一显示项已分别确认 ACK、旧窗口消失和同人物同日期虔诚增加 100；条件疾病、pilgrim／learning XP 未独立读取，这不是全程最终结算。1020 新变体只涉及未选学习项的实际显示名称，原版同一选项块存在两个 name 声明，不能凭历史名称／序号推断本次许可。五个实际事件为 1060／3001／1020／5001／4100；该场未观察到 7000／9001、全程结束或人物在家位置，仍是未完成旅程。新增链接不把来源知识升级成完整实例 registry、当前世界状态、原生许可或普通 auto 策略。

R0018 新类已分析资料：[2070 迷信旅伴](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-2070-source-analysis.json)、[1100 个人反思](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-intent-1100-source-analysis.json)、[1040 野兽预兆](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-intent-1040-source-analysis.json)，以及[前三件实际实例](../../promo/ck3_faith_and_power/episode02/docs/knowledge/r0018-events-001-003-occurrence.json)、[第四件与全场截止](../../promo/ck3_faith_and_power/episode02/docs/knowledge/r0018-event004-and-scene-cutoff.json)。均为来源机器 `4-8e1c2f1861` 的历史 R0018 证据；1060 直接复用已有来源，实际全场共4事件、56天／57次推进请求，未抵达／结算／归返，game／host／public-run 退出1／1／2且 normalclose=false。

游玩智能体可调用既有 `ck3_query_holy_site_planning_knowledge_v1`（例如 `{"action":"demote"}`，这是只读知识输入，不执行降级），在 `knowledge.episode02_research.topics.pilgrimage.source_analyzed_events[当前原生definition]` 检索上述三类。`source_analysis_completed=true` 表示其定义／选项／来源SHA与历史原生实例已分析；每条直接返回效果摘要、来源与实际后态文档及未观察项目。`native_legality=null`、`action_ready=false`、`state_observed=false`、`full_occurrence_contract_registered=false`、`ordinary_auto_consumes=false` 始终保留：查得到已分析知识，不等于当前许可、完整事件registry或普通auto已经主动消费。

2070 的 pious 分支是有条件的活动表现提升，不与 ELSE 的直接50虔诚同时发放。1100 声明10年 `monthly_piety_gain_mult=0.1` 修正及条件XP，不代表最终月总收益一定×1.1，更不是按钮立得10虔诚；本次修正成员与XP未独立读到。1040 本次只有2个显示项，选择跟随狍子后同人物同日期虔诚独立增加50；另有源码10天绕行及隐藏预兆后续，实际ETA／后续／XP仍为null。其90天辅助延迟只在多人条件下生效，不能当成本次确定延迟。活动ID0有效；起点已有非零completion stamp不能判终态。前三件已封资料与追加第四件的截止分别保留，不把部分旅程重写为全程。

这些文件提供版本／来源绑定的已分析知识，尚未自动加载进 `ck3_query_vanilla_event_knowledge_v1` 的完整实例合同。已有专用策略仍优先；其余事件先保存原生 definition／instance、双方角色和实际显示顺序，再按当前原生合法第一显示项规则续行，不因缺少完整registry暂停旅程。相同来源与scope／选项形状复用已分析资料，新变体按批离线补齐；仅有画面时不得猜 native ID 或选择成功。完整接线状态和反例在 JSON 中明确标注。

开发入口：[知识摘要模块](../../ck3_autonomous_player/src/xar_autoplayer/holy_site_episode02_research.py)、[既有知识查询](../../ck3_autonomous_player/src/xar_autoplayer/holy_site_planning_knowledge.py)、[MCP 注册](../../ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py)。研究进展与业务、策略接入分别记账；后续接入普通规划器时必须补实际消费证据。

## 本次接入验证

`machine_id: 4-8e1c2f1861`。2026-10-20 首轮新增5项检查实际通过，其中4项通过生产 `create_server` 注册的 MCP／`ClientSession.call_tool` 调用11次，另1项验证纯知识构造不读取文件。覆盖原七个action均可查六专题、外版本拒绝、只读注解、返回隔离和历史不冒当前状态；不需要启动游戏。随后独立审计收窄朝圣费用措辞、增加两条 source-only 事件引用，只对这次数据修订另执行1项新MCP检查／1次调用并通过，未重跑原5项。两轮来源和原始等待分别保留，不合称同一次运行或游戏验收。

Root另逐一核对摘要13个仓库引用与9项实际原版文件SHA，未发现缺失或不匹配；两名独立审阅者核对共享链接、来源、费用、事件与策略边界。证据封装位于上述来源机器 `E/capture-b17-a01/episode02-knowledge-integration-source-a01/DELIVERY.actual.json`；其中区分当时tool输出与后续归档文件。此验证证明知识能被现有MCP查询参考，不能证明普通auto已主动查询或产生游戏收益。

## 升格前先核完整主要名单与宗教上限

[R0021 升格上限来源与真实拒绝](../../promo/ck3_faith_and_power/episode02/docs/knowledge/r0021-promotion-cap-source-analysis.json)现由既有 `ck3_query_holy_site_planning_knowledge_v1({"action":"promote"})` 的 `knowledge.episode02_research.topics.site_effects_and_cache.documents` 返回；没有新增 action、执行工具或普通 auto 策略。

规划时先 fresh 读当前玩家、Faith／Rite／Religion 和完整 Faith site major membership，再求全局 major count 与该 Religion 实际上限。原版默认主要 max3／min1，可以被 Religion 覆盖；不把3写成通用上限。当前 typed limit 缺失时，保留实际原生要求文本与精确 source／override 证据并标明未知，不能编造 typed 读数。再核当前 selected actor／site／decision、normal CanConfirm、native CanConfirm、bypass0、cooldown、完整十槽费用／可负担与储备；免费行动和零报价均不豁免合法性。

历史 R0021（machine_id `4-8e1c2f1861`，2026-10-20T21:35:19Z）Faith103 的完整 site 列表为0／1／3／2／4／32，major 为0／1／3共3，selected32仍 ordinary。normal／native CanConfirm 均false，bypass0；唯一 active failed 条件为count<3。十槽报价均0、可负担、cooldown absent，原生文本显示余2次免费行动，仍不能提交。12次公共调用、零Confirm，按正常关场释放CAS12952；未观察到本场升格、H2或GHW结果。原图仅作旁证，数值取原生读回；这些记录不代表新局面或其他机器的当前许可。

合法降级释放容量→独立后态→正常保存共同实验母档→ordinary／major 两臂，只是未执行候选。每步仍需 fresh 原价／许可／once与独立后态，不改档或补金，不预写成功。HoF 的无主要圣地费用乘数检查整个 Faith 是否存在“root控制且县主同Faith”的主要县，不能由selected site等级判断；释放一处容量后，其他合资格主要县可能让两臂报价相同。该区别用于设计对照，不自动授权任何下一世界动作。


## R0022：完整普通朝圣的事件与结尾证据

现有 `ck3_query_holy_site_planning_knowledge_v1` 的 `episode02_research.topics.pilgrimage.r0022_source_analyzed_events` 按原生定义 ID 索引本轮新增来源；`r0022_complete_event_index_document` 列出全部 15 事件及 1 婚约通知。旧 R18 三事件索引、六 topic、七 action 与 R21 上限资料保持原合同。此项是可检索研究资料，`ordinary_auto_consumes=false`，不授当前事件许可或新增自动执行策略。

- [全场来源和实际选择索引](../../promo/ck3_faith_and_power/episode02/docs/knowledge/r0022-all-event-source-index.json)：每条保留实际 scope、显示 native indices、专用策略/首项策略、ACK 和独立窗口消失。1060、5001、4100、bookmark、教宗诏书及婚约复用已研究来源。1020 当前展示变体单列，不套旧标签。
- [结尾四事实](../../promo/ck3_faith_and_power/episode02/docs/knowledge/r0022-pilgrimage-ending-observed.json)：同一活动 `id=0` 的 `completed=true/invalidated=false`、7000/9001 实际消费、独立当前人物提示原文“位于阿普利亚”。201 实际游戏日对应 204 单日请求，不能互换。原始 `native_business_pass=false` 保留，不据资料页改验收结果。
- [7000 奖励时点](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-7000-source-analysis.json)：正常 on_end 结算先于回顾按钮。本场最后结算前到首次结算后 24 小时观察到虔诚 +125；按钮前后三钱包不变不等于奖励为零，也不把跨日全部变化归于一个 effect。历史 milestone 的宗教 query 因 optional episode 字段守卫失败，未采集的满足度/奉献经验留空。
- [9001 返程来源](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-9001-source-analysis.json)：允许失效分支，脚本完成旅行也能触发；按钮或活动消失单独不证明成功/坐标到家。当前返程窄读满足度 `3500000/100000=35`、奉献累计 `12153148750/100000`、有效等级/上限 `5/5`，仅是返程当前值，不回填历史奖励差；可花虔诚另列，XP 未知仍为 null。

新增来源还包括 3004、intent1030、6840、6750、配偶2601、6800。6840 本次扣15金/得25虔诚；6750 得100虔诚并有压力代价；6800 修道效果作用于同行 NPC，不是玩家。事件日志 score50 不是虔诚。特质、器物拥有者/属性、ETA 或隐藏后续未独立读取就保留未知。

[1701 实际变体](../../promo/ck3_faith_and_power/episode02/docs/knowledge/stress-threshold-1701-r0022-display-variant.json)：五份原版来源 SHA 相同，但当前两个 saved scopes、三个显示项 native `3/6/8` 不符合旧专用合同。现场先调用旧专用路由，真实拒绝形状后依用户首显策略选 native3，本次扣105金；这是动态报价的一次后验，不是未来固定价格，也不是新 registry 已注册。下次智能体可先查研究，再以 fresh native scopes/options/合法性决定，不能把“来源已分析”当“当前可执行”。

Start 配置费本次70金；途中31.25、15、105金分开记录。全程钱包净差混有自然收入和其他事件，不称纯旅费或总报价。每批陌生事件照原生显示与合法策略继续，离线来源分析并行；隐藏后续不得预先认定发生。

## H1 显示对照与独立 H2／H3 来源

[H共同母档／双臂／领袖与大圣战事实](../../promo/ck3_faith_and_power/episode02/docs/knowledge/h-common-mother-arms-hof-ghw-observed.json)由既有知识MCP的 `topics.head_of_faith.historical_h_reference` 及建制／大圣战topic文档指针返回。该引用只供检索历史实证，当前许可仍null、action_ready=false、ordinary_auto_consumes=false，不增加action或执行策略。

来源机器`4-8e1c2f1861`：R23合法降级Jerusalem，主要数3→2并NativeSave新母档bf894；R24／R25从同一新母档分别恢复。R24普通状态两次fresh Native full10报价为300虔诚／225金币。R25已独立证纳杰夫32升格、主要数2→3且升格付款0；升格后的领袖窗口原PTS70.067帧显示200虔诚／150金币。这两项显示数分别少100和75，但**主要臂的完整Native建制报价和CanConfirm仍未知**，不能说已省钱、已付款或已建制。

R25原query因3个named parameters未获reader资格而selected_terms unavailable，full10／Can／cooldown均null；这是读取范围缺口，不是原版拒绝或资金不足。普通臂两个major计数也不是“领地内合资格主要县”计数。R24／R25正常闭场不覆盖各自businessfalse、R25 PARTIAL及原错误；原R21容量拒绝与当时未执行候选原样保留，新进展另记。

R29的H2／H3从独立Parent de0f冷恢复，不能剪成R25续局，也没有借用R24价格。两次fresh Native full10报价均为300虔诚／225金币、可负担且normal／native CanConfirm均true、bypass0；一次canonical Confirm后，独立Faith教首title／holder由null变为18373／65865。付款玩家仍为31254；Faith103／Rite150／mainRite150及两个Rite领袖31254均未变，说明创建Faith教首与现有Rite领袖是不同后态。

独立钱包243金／14800虔诚变为18金／14500虔诚，分别扣225／300；十资源报价已观察，但`quote_settlement_resource_index_join_verified=false`，不能据此声称十资源实际结算全部闭合。独立受领与钱包先采，事件随后DRAINED、events为空；H2 business true不改aggregate business false或whole-product credit false。长期once ledger为`EP02/once-ledgers/h2-create-hof-r19-a01`，本次claim已消费；任何后续相同意图先核原claim与submit marker，已有或unknown只观察，不能换目录／日期重发。本记录不授权重做建制。

其后两次H3读取capture82387／84327：四具名变量均read_available=true、present=false，保留remaining_raw=-1与calendar-unqualified单位，不能改写成bool false、零天或可发动。该Faith链的GHW／War对象为absent，不代表世界和平。实际33行决议中launch匹配0、`requested_decision_key_not_in_actual_rows`；因此最终CanConfirm、目标合法性与日历倒计时仍unknown，launch／war提交均0。`current_group_qualified=true`仅证明这组只读观测成功，原`director_slot25_complete=false`仍保留；全局实现资格、必要前提缺席与最终许可分列。

本知识增量按已封Native case结果完成，未据此声明R29正常闭场或retained OS0；闭场回执尚待独立提供。`final_data_ready=true`表示这些历史来源已齐，不授当前action-ready、完整产品验收或ordinary-auto消费资格。换机器／局面必须重新读取实际身份、价格与许可。

同一JSON的`artifact_pair`由既有`topics.artifacts.artifact_pair_reference`引用：同母档物品267的R27个人装备／R28供奉两臂，两人raw104000／129000（scale100000）均未变；R28两人原生麦加说明+4%→+8%、site缓存rarity4→8，独立物主／site26／slot1／库存[60,267]后态已证。刷新时间、world effects实际应用和单地点净贡献仍未知；不能重算raw或说立即净增。钱包不变不证明总供奉无成本，`total_payment_observed=false`与原businessfalse保留；不升级当前许可或auto消费。

2026-10-21后续整合补注（`machine_id: 4-8e1c2f1861`，06:57Z）：上述最终知识已纳入本次源码整合，注册MCP消费者验证与候选strict检查已通过；冻结C16影片来源不因此改变。R29的[05:14:24Z闭场回执](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b39-h2-h3-a01/SCENE-CLOSURE.actual.json)及[后续行政闭场交付](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b39-h2-h3-a01/full-custody-a01/ADMINISTRATIVE-FAILURE-CLOSURE-DELIVERY.actual.json)现已独立提供：normal_close=false、OS0未证、保留退出码null，public run2／host0／allocator0，CAS13129空资源。现场已释放；研究JSON保留原采样时闭场未知，不追认正常退出或整体业务通过。

## R0031 新增的已分析旅行来源

`ck3_query_vanilla_event_knowledge_v1(event_definition_key, ck3_build="1.20.0.4")` 可按 `pilgrimage_intent.1060`、`travel_danger_events.1012` 返回原版选项效果、来源 SHA 和 R0031 历史后验，详见 [R0031 来源参考](r0031-pilgrimage-event-reference-12004.md)。前者是“昔日的帝国”，不等于同尾号的 `travel_start_event.1060`；后者是“诱人的水果”，必须分清玩家与尝水果同行者的受影响 scope。

这两条的 `analysis.source_analysis_completed=true` 只表示来源已审；响应仍为 `status=unavailable`、`unavailable_reason=source_analyzed_no_occurrence_contract`、`contract=null`。它们没有新的完整实例执行合同，`current_native_legality=null`、`action_ready=false`、`ordinary_auto_consumes=false`。当前原生窗口的显示顺序、scope 与合法性仍须重新读取；本次历史首项选择的 ACK 和独立旧窗消失，不代表专用策略已执行。

R0031 also source-reviewed `pilgrimage.6770`, `pilgrimage.6830` and `pilgrimage.6820`. The same exact-build source-only query returns their effects and canonical source documents, while contract/action-ready remain null/false. The [13-input batch index](../../promo/ck3_faith_and_power/episode02/docs/knowledge/r0031-events-001-013-index.json) preserves12 accepted selections plus independent old-window disappearance; event13 (7000) was queried but not selected after a declined capture checkpoint. These observations do not establish return or whole-journey completion.


## 2026-10-22 R32观察与费用边界补记

机器4-8e1c2f1861的R32只证明本次天主教人物菜单显示三项意图、旅队主管0.10金币月薪及70金币配置报价；没有出发、任命或付款。详见[制作记录与原生来源](../../promo/ck3_faith_and_power/episode02/docs/production-v6-local-review-2026-10-22.md)和[旅行费研究补记](../../promo/ck3_faith_and_power/episode02/docs/research-v6-travel-fee-boundaries.md)。这批资料用于解释与查询，不授予执行资格；其他人物的候选和CanPick、主管出发费、补给和最终合计仍须按各自来源与当前观测判断。

## 2026-10-24 V8：朝圣态度、意图条件与费用研究补记

本节归档已完成的原版1.20.0.4静态研究与历史报价核对，来源机器为 `machine_id: 4-8e1c2f1861`。四份研究记录按原字节保存，保留各自 schema、机器身份、UTC观察时间与来源 SHA；入库时间为 2026-10-24T07:06:10.242123+00:00。它们不表示V8成片已交付、V8审片通过或新增Native业务验收，也没有新增事件动作、普通auto策略或MCP自动消费接线。

| 研究记录 | 已闭合范围与限制 |
| --- | --- |
| [意图条件](evidence/faith-e02-v8-clarity-20261024/intent-conditions.actual.json) | 朝圣态度与意图区别、主持／来宾候选与显示谓词、R32场景绑定；候选显示不等于按钮CanPick。 |
| [旅行选项费用](evidence/faith-e02-v8-clarity-20261024/travel-costs.actual.json) | 29项原版定义目录、直接费用类别及币种分支、主管费用L的未闭边界；无新的当前可选／付款资格。 |
| [活动本体费用](evidence/faith-e02-v8-clarity-20261024/activity-costs.actual.json) | 动态金额、18个修正分支、有序计算和F0／F1逐数示例；均不冒充人物实时报价或整趟旅费。 |
| [历史原生账单核对](evidence/faith-e02-v8-clarity-20261024/native-invoices.actual.json) | R32／R39／R46已保存配置报价及其输入缺口；账单、脚本算例、钱包变化分列，不推断通用最终取整。 |

### 两个“深思熟虑”与候选显示

统一称“活动选项里的朝圣态度（游戏栏名‘忠诚’）”，后续简称“朝圣态度”。同名的是态度选项 `pilgrimage_fidelity_contemplative`（Contemplative）和意图 `reflection_intent`（Reflection），两者中文均为“深思熟虑”；分类Fidelity自身仍名“忠诚”，不能混作人物虔诚奉献等级、忠诚性格或封臣忠诚。前者改变行进速度修正与主虔诚奖励计算，后者提供反思事件／行为资格，不等于立刻领取固定完成奖励。

原版 `pilgrimage.txt:2645–2653` 的主持者显式意图池是深思熟虑（默认）、行善、热忱；来宾显式池仅有深思熟虑。Reflection的自身显示块为空；Altruism检查 `advanced_activities`、人物存活且未被囚禁；Zealotry仅检查 `advanced_activities`。这三个显示谓词不检查天主教、pious类型或人物奉献等级；慷慨、狂热及财富在AI偏好中的条件不是玩家解锁门槛。朝圣态度中的同名档位才要求高级活动功能，并有耐心、朝圣者、朝觐者任一特质；三档完整显示／合法条件见JSON的 `fidelity_matrix`。

R32历史原场actor31254、faith13/catholic、rite0、date53144328，实际显示“深思熟虑、行善、热忱”，人物有效奉献等级为5；三项逐按钮CanPick未全部资格化，不能写“三项均可选”。共享娱乐定义及响应事件不能证明它自动加入朝圣菜单；既有原生候选过滤研究也未完全闭合上游容器继承／合并，不由本场推出全球固定三选一。`advanced_activities`与具体品牌DLC的本地声明映射未闭合：EP2产品资料与 `tours_and_tournaments` 谓词不能直接证明两feature等价。正文用“高级活动功能”，附录保留原key。

### 旅行选项、活动本体与历史报价分开计算

旅行直接费用值的三档为 `2×K×W／5×K×W／10×K×W`，`K=max(primary_title.tier-1,1)`；具有 `well_prepared_perk` 时 `W=0.75`，否则1。它们是不同旅行选项的费用类别，不是同一选项的三档升级。公爵K2的声明算例无技能为4／10／20，该条件成立时为3／7.5／15；不把动态金额向上取5的规则移用到这些定义。实际金币、国库和游牧牧群等分支，以及各项显示／合法门槛，查旅行JSON；没有直接cost字段不表示整趟免费。主管出发费用L的作用域绑定、付款时点及是否已纳入聚合仍未闭合，不能用0.10金币月薪替代L。

F0与F1是声明脚本算例：玩家、公爵tier3／K2、时代E1、月角色收入I10、Q1、非部落、`pilgrimage_pomp_ceremonial`、首都至目的地距离平方50000、低价旅行选项，无其余折扣。先求动态minor=30、medium=60。F0为活动本体60、排场100、距离12、旅行选项4，展开小计 `60+100+12+4=176`。F1只开启 `ep2_activities_legacy_1`，活动本体30、排场75，距离和旅行选项仍12／4，展开小计 `30+75+12+4=121`，差55；不是整张账单打五折。L及完整聚合边界仍未知，不能将这两个小计称为实际整趟总付款，也不能套给R32／R39／R46人物。

活动本体完整顺序、18分支及逐数过程查活动JSON的 `branches`、`groups`、`numeric_models`：先固定减项，再连续乘当前余额；庄园减的是原始 `0.2×B×E`，随后再接后半乘数，最后才与动态minor最低费取较大值；持有户部头衔的85%在最低费之后。独立国王示例为 `140×0.75×0.5−28=24.5`，再取最低费30；交换顺序得42是错误算法。排场、距离、旅行选项另算，不能把本体折扣统乘整张账单。

R32旧图的70金币应解释为“基础60＋距离10”；10不是旅队主管费用。原主管槽为空，0.10是未任命显示的月薪，R32没有出发或付款证据。R39／R46的原生最终报价182／128与诊断聚合181.5／127.5分别保存；这些个例不证明引擎存在通用最终向上取整规则。公式月角色收入I也不能用顶栏净月变化替代。

## V8 清晰度修订交付补注（2026-10-24）

`machine_id: 4-8e1c2f1861`：[V8制作记录](../../promo/ck3_faith_and_power/episode02/docs/production-v8-local-review-2026-10-24.md)已整合上述条件、旅行收费类别、逐步账单与折扣顺序，当前审阅片29:30.933，完整人工听看待审。最终[作者稿](evidence/faith-e02-v8-clarity-20261024/approved-script.localization-reviewed.json)、[素材分页规格](evidence/faith-e02-v8-clarity-20261024/focused-pages.materials.spec.json)、[技能别名页规格](evidence/faith-e02-v8-clarity-20261024/focused-pages.perk-aliases.spec.json)和[原版英文名称核对](evidence/faith-e02-v8-clarity-20261024/english-localization-review.actual.json)已入库。`clerical_justifications_perk`的普通名为教权辩护／Clerical Justifications，无地及游牧UI动态显示高效朝圣者／Prolific Pilgrim，不是两个技能。文化因子C控制动态金币上限150C／300C，不能与收入调整Q混用。此轮仅制作与来源整理，无新实机、Native业务资格、当前动作许可或普通auto消费增量。
