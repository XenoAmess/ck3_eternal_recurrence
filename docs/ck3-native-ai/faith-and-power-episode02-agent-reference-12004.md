# 信仰引擎二期：游玩智能体研究入口（1.20.0.4）

本页供游玩智能体在制定宗教行动前查阅，汇合二期机制、来源、需要的当前观测和反例。导演案和视频不是策略规则。知识查询入口为既有 `ck3_query_holy_site_planning_knowledge_v1(action, ck3_build="1.20.0.4")`，其 `knowledge.episode02_research` 返回六个相关专题及仓库相对路径；它不读取游戏、不提供当前许可，也不自动提交行动。

当前接入范围：研究文档可从共享索引找到，结构化摘要可经 MCP 查询；普通 `auto` 尚未自动调用这些二期摘要。拍摄用受控案例也不代表普通规划器已经具有自主朝圣、建制或大圣战策略。新增事件来源分析已持久化，5001／1060／1020／4100 的完整实例合同尚未注册，事件策略不能据此伪造原生实例或选项编号。

例如查询参数 `{"action":"demote","ck3_build":"1.20.0.4"}` 后，先读 `knowledge.episode02_research.topics.site_effects_and_cache`，再沿其 `documents` 查详细来源。朝圣与建制是现有圣地规划查询提供的相关研究，不是新增可执行 action；不能把它们写进该接口的 action 枚举。

## 使用次序与证据等级

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

## 关键来源与已知反例

原版 `common/religion/holy_site_types/00_holy_site_types.txt` SHA-256 为 `0824df55d4cd0a7c6d2c2d8b45bf577cca9ec0e5e1b4a6f699848b8661b17b40`；动态类型来源及完整 source pins 见各研究文档。缓存链来源区分 Rite producer `29CC520 → 24FB270`、角色 aggregate `291C0B0 → 291F080` 与 cached reader `2B0C740`／即时 relic evaluation `265A3F0`；这些来源不能单独证明本次缓存刷新。完整原始 source 合同在下述来源机器 Q/a1-effect-refresh-source-a01/SOURCE-PINS.actual.json，SHA-256 `f0c71136a3a3864c0a1f4b1aaf0530d6bac8a819c9490b63ac353f624bb1fa56`。

以下为历史样本，均属于 `machine_id: 4-8e1c2f1861`，记录汇总时间 `2026-10-20T08:15:32Z`；不能作为另一机器或新局面的输入。原始机器证据根 `E = C:/workspace/ck3-faith-and-power-20261017/episode02`，`Q = E/production-b3-a01/native/qualifications`；外置证据按[通用存储策略](../storage-retention-policy.md)复核，不保证永久可读。

- B15 同 Faith 两名人物的 Rite 不同。地点 27 的主要关系移除和 1000 虔诚付款已证，外交 18／13 与 named Medina +4／+1 未变，缓存新鲜度和净收益仍未知。原 `capture-b15-a01/same-faith-continuation-a01/case-output/a1-same-faith-result.json` SHA-256 `343efbbe8ebd1cd8dcc1b72835fcf2e18624c93610a4876d17d456002d834b7c`。这是否定“关系变化即属性到账”的反例，不是降级无效的普遍结论。
- B17／R0009 Rome Start 的实际主办活动与钱包 243→173 已读回；70 金是该配置活动费。首个自然日后 public pause readback 失败，未完成抵达、阶段结束或归返。原 `capture-b17-a01/SCENE-CLOSURE.actual.json` SHA-256 `5fbfc23af841de14746f123093b5cd37559db69cb01bb8afc80d721514e02757`。该场失败闭场不授完整朝圣信用，旧结果未知的动作不得重发。

## 新事件来源知识

持久研究：[pilgrimage.5001](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-5001-source-analysis.json)、[travel_start_event.1060](../../promo/ck3_faith_and_power/episode02/docs/knowledge/travel-start-1060-source-analysis.json)。1060 的标题“第一次启程”复用了 1000 的本地化 key，不能据标题推断为 definition 1000；其确认选项不是 Start、抵达或主要奖励。

新增持久资料：[travel_events_cities.1020 来源与实际显示变体](../../promo/ck3_faith_and_power/episode02/docs/knowledge/travel-cities-1020-source-analysis.json)、[1060 的 R0012 原生实例观察](../../promo/ck3_faith_and_power/episode02/docs/knowledge/travel-start-1060-r0012-occurrence.json)、[婚约通知的既有拒绝知识复用](../../promo/ck3_faith_and_power/episode02/docs/knowledge/r0012-arrange-marriage-source-occurrence.json)、[事件与通知独立后态](../../promo/ck3_faith_and_power/episode02/docs/knowledge/r0012-event2-interaction35-post.json)。这些是 `machine_id: 4-8e1c2f1861` 的历史 R0012 观察，1060 原生定义已读为 `travel_start_event.1060`，原窗口独立消失；旧 B17 截止资料原样保留，不追认其当时已查询原生定义。旧 5001 来源分析的截止资料保留原样；新的 R0012 原生实例与独立后态另链，不追认旧资料当时已有实机定义。

1020 仅闭合本次基督教圣地观光的实际显示变体：第一显示项提交后旧 instance 2 消失，同暂停日期钱包减少 50 金、压力 0→15。物品创建和额外 7 天旅行延迟仍只有脚本来源，未独立读取库存或新 ETA；这不是抵达、主要朝圣奖励、归返或整趟旅费结论。婚约 35 的 `accepted=false` 表示实际拒绝，后读 pending 消失；不证明婚姻或全部拒绝效果。后续出现相同 definition 仍须重新绑定当前实例、完整作用域和显示顺序，不能复用 native option 4／instance 2。

后续 arrival 资料：[5001 的 R0012 实例](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-5001-r0012-occurrence-analysis.json)、[4100 来源与显示选项](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-4100-source-analysis.json)、[两事件分别提交后的独立后态](../../promo/ck3_faith_and_power/episode02/docs/knowledge/r0012-5001-4100-post.json)。同一来源机器 R0012 的 5001 已读到原生定义并确认旧窗口消失，压力 15→4；该次按钮前后虔诚不变，pilgrim 特质／XP 未独立读取。它支持来源绑定的 Rome 到达事件，不能推出全程结束或归返。

4100 第一显示购买项的 `effect_indicators.rows=[]`，同时 `complete_effect_set=false`、资源变化 unavailable；空图标列表不能理解为免费。原脚本使用动态 `minor_gold_value` 付款，特定 illustrious 分支再乘 1.25。独立后态证实该次额外扣 31.25 金、压力 4→4、该按钮前后虔诚不变；`activity_log score50` 是活动日志评分，不是 50 虔诚。两事件之间的自然日变化与每次按钮差值分开，不把一次价格硬编码给未来事件。徽章完整 ID／所有权、稀有度、装备和属性仍未独立核实，不能写成玩家已获得可用徽章。

这些文件提供版本／来源绑定的已分析知识，尚未自动加载进 `ck3_query_vanilla_event_knowledge_v1` 的完整实例合同。遇到新事件仍须先保存原生 definition／instance、双方角色和实际显示顺序，再按现有原生第一显示项策略继续；仅有画面时不得猜 native ID 或选择成功。完整接线状态和反例在 JSON 中明确标注。

开发入口：[知识摘要模块](../../ck3_autonomous_player/src/xar_autoplayer/holy_site_episode02_research.py)、[既有知识查询](../../ck3_autonomous_player/src/xar_autoplayer/holy_site_planning_knowledge.py)、[MCP 注册](../../ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py)。研究进展与业务、策略接入分别记账；后续接入普通规划器时必须补实际消费证据。

## 本次接入验证

`machine_id: 4-8e1c2f1861`。2026-10-20 首轮新增5项检查实际通过，其中4项通过生产 `create_server` 注册的 MCP／`ClientSession.call_tool` 调用11次，另1项验证纯知识构造不读取文件。覆盖原七个action均可查六专题、外版本拒绝、只读注解、返回隔离和历史不冒当前状态；不需要启动游戏。随后独立审计收窄朝圣费用措辞、增加两条 source-only 事件引用，只对这次数据修订另执行1项新MCP检查／1次调用并通过，未重跑原5项。两轮来源和原始等待分别保留，不合称同一次运行或游戏验收。

Root另逐一核对摘要13个仓库引用与9项实际原版文件SHA，未发现缺失或不匹配；两名独立审阅者核对共享链接、来源、费用、事件与策略边界。证据封装位于上述来源机器 `E/capture-b17-a01/episode02-knowledge-integration-source-a01/DELIVERY.actual.json`；其中区分当时tool输出与后续归档文件。此验证证明知识能被现有MCP查询参考，不能证明普通auto已主动查询或产生游戏收益。
