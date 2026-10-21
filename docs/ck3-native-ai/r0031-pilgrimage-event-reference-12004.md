# R0031 新旅行事件：供游玩智能体查阅的来源与实际记录

机器 `4-8e1c2f1861`；CK3 `1.20.0.4`；原件来自同机历史运行 `R0031`，不能作为调用者的当前世界状态。当前目录为外置 copy-ready 候选，未修改正在运行的 checkout。

| 原生定义 ID | 已分析的内容 | 精确资料 |
|---|---|---|
| `travel_start_event.1060` | 复用开程事件来源，不与同尾号的意图事件混用 | [旧来源](../../promo/ck3_faith_and_power/episode02/docs/knowledge/travel-start-1060-source-analysis.json)、[本次实例1](../../promo/ck3_faith_and_power/episode02/docs/knowledge/r0031-events-001-003-occurrence.json) |
| `pilgrimage_intent.1060` | 昔日的帝国：三个实际显示选项及第四个冒险者分支；本次选默想古帝国 | [来源和全部选项效果](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-intent-1060-source-analysis.json)、[本次实例2](../../promo/ck3_faith_and_power/episode02/docs/knowledge/r0031-events-001-003-occurrence.json) |
| `travel_danger_events.1012` | 诱人的水果：警告、让同行者尝、自己尝；区分玩家和同行者受影响范围 | [来源和全部选项效果](../../promo/ck3_faith_and_power/episode02/docs/knowledge/travel-danger-1012-source-analysis.json)、[本次实例3](../../promo/ck3_faith_and_power/episode02/docs/knowledge/r0031-events-001-003-occurrence.json) |

古帝国首项声明50虔诚、十天延时，并只在世俗朝圣类型推进世俗表现；本次同日原生确得50虔诚，不能因此说本趟虔诚表现增加。学识对抗的成功修正和额外减压、另一项的古信仰修正／技能／经验，均须另取实际后态。两项对抗不是固定五五开。源码的多人暂停 helper 不等于单人实际多走九十天。

“等等，万一有毒呢？！”仍可能使玩家和同行者接触植物并得到五年皮疹修正；另一分支给玩家学识生活方式经验。让同行者吃和自己吃会把有毒／有益修正作用于不同人物。不要把潘多尔夫36310的后果记到玩家31254，也不要把未选择的吃水果分支之旅行者经验发给本次警告项。本次三钱包和压力未变，不证明健康、修正、经验或满足度没有变化。

三次实际选择都采用第一显示项，均有 ACK 和独立旧窗消失。原回执记录了当时冻结执行树缺少 `source_compatibility_1_20_0_4.json`、专用 registry reader 无法加载的缺口。后续修复不追认这三次为专用策略执行。

查阅方法：用 fresh native definition ID 在上表定位，读取来源 SHA／条件／人物 scope，再与当前原生显示顺序和合法性核对。这里是**已分析来源**，不是新策略授权；已有合法专用策略仍优先，未知按用户首显规则继续，结果未知不重复提交。

离线原生检查已用既有 `normalize_current_event_window_context_v1` 读取三个原样 native context。外置接线候选还用现有注册 MCP `ck3_query_vanilla_event_knowledge_v1` 实际读到了两个新定义的选项效果、来源 SHA 和本次后验，并检查了未知 ID 和错误 build。候选只在精确 `1.20.0.4` 返回 `analysis.source_analysis_completed=true`；`status=unavailable`、`unavailable_reason=source_analyzed_no_occurrence_contract`、`contract=null`，表示来源已分析，但没有可执行的完整实例合同。它不会启用专用动作或改变首显策略。

查询参数为 `event_definition_key` 和 `ck3_build`。用定义 `pilgrimage_intent.1060` 或 `travel_danger_events.1012`、build `1.20.0.4` 即可读到来源，不需要运行游戏。调用者仍须检查 fresh native scopes／显示顺序／合法性；本次历史标签和原生索引不是新窗口的按钮许可。上述生产接线是外置候选验证结果，只有实际合入后，正式 SDK 才会返回这些新增来源。当前 R0031 已发生选择的策略缺口保持原样。

Additional actual source-reviewed definitions: [6770](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-6770-source-analysis.json), [6830](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-6830-source-analysis.json), [6820](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-6820-source-analysis.json). All have the same source-only query boundary. The [complete batch index](../../promo/ck3_faith_and_power/episode02/docs/knowledge/r0031-events-001-013-index.json) contains13 real inputs and12 real selections, not13 selections. The unshown fourth source branch of intent1060 now records native index=null and source_order_index=3; an authored source position is not a native observation.
