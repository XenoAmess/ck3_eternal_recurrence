# AI 单独清理圣物与夺回圣物战争：V5 精确条件

`machine_id: 4-8e1c2f1861`。本轮于 2026-10-18T06:02Z 起只读复核；代码基线 `fa0d46eec95064a2a25fb2af74abc9bcc5f4bd36`，游戏 1.20.0.4，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。先读原文，06:05:38Z 的 V5 本批准入后才写外置小包。没有运行游戏、SDK、构建或媒体操作。

## 中文讲解依据：仍待全文连续审读

下段按技术条件分组，供作者编排；研究过程措辞与技术表不直接充当冻结旁白。最终表达按[系列方法](../../promo/ck3_faith_and_power/docs/production-lessons.md)与[本期重排](../../promo/ck3_faith_and_power/docs/episode01-revision-v5.md)处理。

原版有一条只供 AI 使用的清理决议。先看操作人：它要带有“狂热”特质，或者 AI 狂热数值至少为 25；还必须是活着、成年且当前可用的 AI。原版的成年参数男女都是 16 岁。这里的可用，要求本人不在旅行、不在军队中、没有被监禁、没有失能，也没有带“致命传染病”标记的疾病。它还要没有参加或筹划活动，也没有命中原版七项忙碌标记检查。这些内部标记用于觐见领主、避世冥想、举行祭祀仪式、向领主请愿、信仰领袖等候请愿者、举办朝会，以及探险灵感角色外出探险的相关流程；它们不是界面上七个正式状态名称。它也不能是原版严格巡游检查下正在被到访的对象。

接着看政治关系：这个 AI 必须和自己的最高领主同信仰，最高领主也必须是 AI。它本教的信仰领袖，要么不存在，要么同样是 AI。因此，人类最高领主，或者这个 AI 所属信仰的人类信仰领袖，都能挡住这一条清理决议。独立 AI 的最高领主就是自己，可以满足这一项。原捐献者是人类、中间某一级领主是人类、其他关联信仰的领袖是人类，都不是这里写出的保护条件。

通过这些条件后，它也只会检查自己直接持有的伯爵领，不会遍历整个领国。逐件清理时，先要求物品不被它本教认可，然后分两类：这里本来就是本教圣地，就清理本教不认可的物品；这里不是本教圣地，则还要有一个关联信仰，仍有伯爵领层面的信众，受到操作人信仰至少“敌对”等级的看待，而且认可这件物品。每件最终仍要通过原版取出许可，才会执行。

这里有一条比注释更强的保护：敌教清理分支要求“本教不认可这件物品”和“这里不属于本教圣地”同时成立。只要本教认可它，就不会被这条单独清理决议拿走。共享圣地里本教不认可的物品，仍可能由前一类清理。这个结论来自实际逻辑运算，不能把两项误读成“只有本教认可、又是本教圣地时才保护”。清理成功的物品交给本次操作的 AI，不按原捐献者返还。这些限制只属于这条单独清理决议，不能用来保证 AI 供奉替换或战争中的圣物绝对安全。

再看“夺回圣物”的战争理由。对 AI，狂热数值必须至少为 100，而且最高持有头衔必须达到公爵级；光有“狂热”特质不能绕过 100 的数值门槛。人类攻击者没有这两项 AI 限制，但所有攻击者都不能是无地冒险者。AI 还被配置为只考虑邻居。

双方信仰必须不同。普通圣物还必须被攻击者信仰认可、不被防御者信仰认可，而且没有禁止转移的物品标记。AI 检查的是防御者本人的物品库存；人类攻击者的分支还能查防御者旗下、与攻击者不同信仰的下属库存。伊比利亚斗争圣物另有专用分支。满足这组局部门槛后，仍要通过完整宣战规则；取物时出现警告，不代表已经发生战争，也不代表每个异教 AI 都有资格打这场仗。本轮没有观察自然 AI 清理或宣战。

## 完整技术条件：决议准入

决议键为 `ai_remove_enshrined_artifact_decision`，原版 `common/decisions/50_holy_site_decisions.txt:738–908`。以下组之间全部 AND：

| 组 | 精确条件 | 正向解释 |
|---|---|---|
| 显示对象 | `is_ai=yes`（755–757） | 决议供 AI 角色使用 |
| AI 潜在资格 | `has_trait=zealous OR ai_zeal>=25`（826–832） | 特质或数值任一成立即可；25 不要求同时有特质 |
| 可用成年 | `is_available_ai_adult=yes`（760） | 展开见下一表，不能只说“成年” |
| 最高领主信仰 | `actor.faith == actor.top_liege.faith`（763） | 同信仰；独立角色 top_liege 为自己 |
| 最高领主控制者 | `actor.top_liege.is_ai=yes`（765–767） | 检查最高领主，不是任意中间领主或原捐献者 |
| 本教信仰领袖 | `NOT exists(actor.faith.religious_head) OR actor.faith.religious_head.is_ai`（768–773） | 检查操作者当前信仰的领袖，非所有关联教派领袖 |
| 可执行见证 | 存在自己直接持有的伯爵领，其某圣地有物品，并满足下面的 A 或 B，且该件原生 `can_remove` 为真（775–824） | `any_held_county` 的存在见证，不是整个领国 |

`is_valid` 的见证 A：`OwnSite(S,F) AND 存在 I: !R(I,F) AND CanRemove(A,S,I)`。

`is_valid` 的见证 B：存在关联信仰 G，`G!=F AND G.num_county_followers>0 AND hostility(F,G)>=2 AND 存在 I: R(I,G) AND CanRemove(A,S,I)`。**这个见证没有 effect 中的额外双项 NOT 保护**，所以决议有效不保证实际一定移走某件物品。信众数量在 G 的信仰 scope 中检查，不能擅自改成“这个圣地所在伯爵领里有该教信徒”。

配置按最高头衔等级检查：男爵 0（不考虑）、伯爵 24 个月、公爵及以上 12 个月（原枚举 `duchy/kingdom/empire/hegemony`）；`ai_will_do.base=100`。原版 `_decisions.info:152–175,267–268` 明确单位与配置概率；这不是每月概率，也不保证每到间隔都成功移物。自然 scheduler 的当次调用、选择与后态仍未观察。

## 完整技术条件：可用成年

原版 `common/scripted_triggers/00_available_for_events_triggers.txt:475–506`；所有行 AND：

| 组件 | 原文要求 |
|---|---|
| 原生快速检查 | `ai=yes; adult=yes; alive=yes; travel=no; in_army=no; imprisoned=no; incapable=no` |
| 疾病 | `has_contagious_deadly_disease_trigger=no`；同文件 17–19 定义为没有携带 `contagious_deadly_disease` flag 的特质，不能扩大为“没有任何疾病” |
| 参与活动 | 外层 `NOR` 中 `exists=involved_activity` 必须为假 |
| 忙碌变量块 | 同一个 `NOR` 中的 `has_variable` 块必须为假；原文列 `homage_liege_scope`、`meditation_character_flag`、`local_shrine_rite`、`petition_liege_character_flag`、`petition_head_of_faith_petitioner`、`holding_court_character_flag`、`gone_adventuring` 七个 `name`。原生 `HasAnyVariable` consumer 只要找到任一个就返回真，所以通过条件是七个都不存在，不是七个同时存在才忙碌 |
| 巡游到访 | 同一个 `NOR` 中 `is_being_visited_on_tour_strict=yes` 必须为假 |
| 筹备活动 | 没有 character flag `planning_an_activity` |

原版 `00_defines.txt:183–184` 的男女成年参数均为 16。`in_army=no` 限制操作人本人，不是要求整个领国没有战争；本决议没有额外 `is_at_war=no`。上述七种 quick 参数在此明确列出，未从另外的更严格 availability helper 偷加健康、和平、统治类型或曼荼罗继承变量门槛。

重复 `name` 的 OR 语义也单独复核：`has_variable` 注册 `721B70` →工厂 `3789390` →编译虚表 `4936C38+C8` 的 `378C580` →`3783CF0..3783D51`，后者遍历输入变量名数组，对任意已保存变量命中即 true。没有凭变量名或临近的 `has_all_variables` 帮助文字猜测。

## 实际 effect：每件物品的 AND／OR

符号：A=AI 操作人，F=A.faith，S=当前圣地，I=当前圣物，G=遍历到的关联信仰；R(I,F) 表示原版 `is_holy_relic_for`；OwnSite(S,F) 表示 S 的关联信仰包含 F。

effect 按 `every_held_county → every_county_holy_site(有物品) → every_holy_site_faith` 遍历，再枚举实际已供奉物。不是只取 `is_valid` 中存下的第一件。

| effect 分支 | 所有条件 AND | 执行 |
|---|---|---|
| A，本教关联信仰 | `G==F AND !R(I,F)`（847–864） | 以 A 为 root 执行 `remove_holy_site_artifact(S,I)` |
| B，其他关联信仰 | `G!=F`（前置 if 的 else）`AND G.num_county_followers>0 AND hostility(F,G)>=2 AND R(I,G) AND !R(I,F) AND !OwnSite(S,F)`（868–900） | 同上，原生 effect 内仍重新核 Can |

因此，在当次条件保持不变的布尔模型中，A/B 合并为：

```text
!R(I,F)
AND (
  OwnSite(S,F)
  OR 存在关联信仰 G:
       G!=F AND G.num_county_followers>0 AND hostility(F,G)>=2 AND R(I,G)
)
AND 最终原生移除许可
```

敌教分支 `NOT{R(I,F); OwnSite(S,F)}` 的真值表为：

| 本教认可 I | S 属于本教 | 该 NOT 块 | 敌教分支 |
|---|---|---|---|
| 否 | 否 | 真 | 仍须其他敌教条件及 Can |
| 是 | 否 | 假 | 保护 |
| 否 | 是 | 假 | 敌教分支保护；A 分支仍可清走不认可物 |
| 是 | 是 | 假 | 保护 |

原生绑定证明 NOT 与 NOR 注册为同一个 `CNotTrigger`，其定义是所有子条件都假才真（NOR）。因此“只有本教认可且是本教圣地才保护”不是这段的完整语义。旧注释和旧研究未知状态保留，本次在新证据中闭合，不能覆盖旧包冒充早已知道。

脚本 `remove_holy_site_artifact` 的既有原生 consumer `2CC34A0..2CC36FB` 在 `2CC35F0` 检查 `29ABB20`，通过才于 `2CC35FE` 调 `29AB8A0`；最后由 `252FDD0(old,A)` 交给有效操作人 A。AI 决议不复用 GUI 当前玩家，不查原捐献者。回调可能改变后续状态，以上不是快照原子 sweep 或自然执行次数的证明。

## 夺回圣物 CB 的精确门槛

`reclaim_relic_artifact_war`，原版 `01_ep1_wars.txt:342–411`：

| 层 | 精确条件 |
|---|---|
| AI 狂热 | AI 时 `ai_zeal>=100`，没有 zealous 特质 OR 旁路（349–354） |
| 头衔 | `highest_held_title_tier>=tier_duchy OR is_ai=no`（355–358）：AI 最高持有头衔至少公爵级，人类不受该条头衔门 |
| 政体 | 所有攻击者均不得有 `government_is_landless_adventurer` flag（359–361） |
| 攻守信仰 | `attacker.faith != defender.faith`（366） |
| AI 库存见证 | 防御者本人有至少一件符合“普通宗教圣物 OR 斗争圣物”条件的物品（367–382） |
| 人类库存见证 | 防御者本人库存，或其不同于攻击者信仰的下属库存，至少一件符合（383–409） |
| AI 配置 | `ai_only_against_neighbors=yes`（345）；另有 `max_ai_diplo_distance_to_title=500`（690），本包不将原生距离单位换成公里 |

普通宗教圣物逐件条件（`00_artifact_triggers.txt:2223–2229`）全部 AND：`R(I,attacker.faith)`、`!R(I,defender.faith)`、没有 `artifact_prevent_transfer` 变量。它没有额外要求攻击者是原捐献者、具有个人物品宣称、该物曾在圣地，或攻守信仰敌意必须达到 2。

斗争圣物另一路（2231–2248）全部 AND：有 `var:relic` 且值为 `flag:iberian_struggle`；攻击者参与伊比利亚斗争；攻击者通过 `islamic_artifact_access_trigger OR christian_artifact_access_trigger`；攻守信仰不同；没有禁止转移变量。本包保持这两个物品访问子 trigger 为原版命名条件，不把它们简化为只检查宗教名字。

以上是该 CB 的脚本局部准入，完整宣战许可、距离实现及当前费用仍应由原生接口判定。脚本的 `ai_score=relic_artifact_war_ai_score_value` 是另一个评分入口，不从 `ai_zeal>=100` 推算 AI 会不会宣战。本轮无自然 AI 执行信用。

来源全文 SHA、精确行见[原版脚本摘录](evidence/holy-site-relic-ai-cleanup12004-v5/stock-source-excerpts-a01.json)；原生注册、完整布尔分支和小型字节证据见[逻辑源码合同](evidence/holy-site-relic-ai-cleanup12004-v5/SOURCE-CONTRACT.logic-not-a01.json)。[结构化规划补注](evidence/holy-site-relic-ai-cleanup12004-v5/planning-clarification.relic-ai-v5.json)可供既有 MCP 知识工具引用，不能充当当前 AI 的权限后读。V5 本批截止 2026-10-18T10:05:38Z；小型机制结论复核期限为 2026-10-25T06:20:00Z。


## 2026-10-18 术语与标记保存对象勘误

本次只读补查的 `machine_id` 为 `4-8e1c2f1861`，观察时间与各文件完整 SHA-256 见[追加来源](evidence/holy-site-relic-ai-cleanup12004-v5/busy-terms-source-a01.json)。复用 exact 1.20.0.4 EXE 绑定；没有游戏执行或新原生采样。原有逻辑证据与七个 raw `name` 不变，本节更正中文解释。

`petition_head_of_faith_petitioner` 保存在接待方 AI 信仰领袖身上，值才是请愿者。`petition_head_of_faith_block_recipient_effect` 的 `scope:recipient` 内检查 `is_ai = yes` 后设置该变量（`11_petition_head_of_faith_effects.txt:28–38`）；`clear_pending` 与 `cleanup` 分别沿接待方变量清除它（17–20、49–51）。因此旧版“向信仰领袖请愿”把标记保存对象说反，应为“AI 信仰领袖正在等候请愿者”。官方 `unavailable_petition_head_of_faith` 也写作“等待正式请愿”，并非请愿者自身的动作名。

下表中的名称是动作或忙碌说明的官方简中文本，流程说明是本次根据 caller 写的普通解释，不能冒充新增 UI 状态。

| 内部标记 | 官方文本与普通说明 | 设置／清除的原版 caller |
|---|---|---|
| `homage_liege_scope` | `pay_homage_decision`：“觐见”；`unavailable_pay_homage`：“觐见你的领主”。本人进行觐见，变量值保存领主 | `30_court_decisions.txt:258–262` 的决议 effect 设置；`pay_homage_clear_variable_effect` 清除（`pay_homage_events.txt:218、235–239`） |
| `meditation_character_flag` | `meditate_in_seclusion_decision`：“避世冥想”；忙碌文案“冥想”。本人进行冥想流程，也有在家选项 | `meditate_at_location_effect` 设置（`religious_decision_events.txt:1238、1256`），在家选项也设置（1371–1378）；取消事件 `.0200` 与结束事件 `.0291` 清除（1193–1195、2111–2112） |
| `local_shrine_rite` | `visit_local_shrine_decision`：“举行一场祭祀仪式”；`unavailable_local_shrine`：“拜访地方神祠”。普通说明用“祭祀仪式相关流程”，不自译“当地神社仪式” | 决议触发 `local_rites.1`（`tgp_east_asia_decisions.txt:633–636`）；`local_shrine_at_location_effect` 设置 flag（`local_shrine_events.txt:20、38–40`）；取消或完成路径清除（57、748、788） |
| `petition_liege_character_flag` | `unavailable_petition_liege`：“向你的领主请愿”。本人是请愿方；决议名称使用动态领主称号 | `30_activity_decisions.txt:914–930` 在本人已在领主首府时启动，或到首府的旅行开始时调用 `petition_liege_start`；该 on_action 设置 flag（`ep1_petition_liege_on_actions.txt:2–8`）；`petition_liege_variable_cleanup_effect` 清除（`00_ep1_hold_court_effects.txt:1627、1636–1639`） |
| `petition_head_of_faith_petitioner` | `unavailable_petition_head_of_faith`：“等待正式请愿”。普通说明为“接待方 AI 信仰领袖等候请愿者” | 保存对象及设置／清除见本节上一段；不能用变量名中的 petitioner 推断保存对象就是请愿者 |
| `holding_court_character_flag` | `hold_court_decision`：“举办朝会”；`unavailable_hold_court`：“主持朝会”。本人为朝会主持方 | 决议触发 `.0011`（`30_activity_decisions.txt:71–77`）；该朝会开场事件设置 flag（`hold_court_events_general.txt:125、178–192`）；退出选项或结束事件 `.0021` 清除（226–230、244、270–273） |
| `gone_adventuring` | `adventure_inspiration`：“探险灵感”。普通说明为“探险灵感角色正在外出探险”，不泛指所有旅行或无地冒险者政体 | `start_adventure_effect` 在 `$ADVENTURER$` 上设置变量（`00_adventure_effects.txt:5–23`）；灵感事件也在 `scope:inspiration_owner` 设置（`ep1_fund_inspiration_events.txt:4693–4699`），清除后送回默认位置（7853–7860） |

本地化关系还可直接核 `00_activity_loc.txt:381–427`：这些条目分别选择官方 `unavailable_*` 文案。官方决议名与忙碌文案可能不同，表中已分开；`gone_adventuring` 引用的是官方灵感类别名，表中没有捏造其独立忙碌状态名。

`contagious_deadly_disease` 是 `has_contagious_deadly_disease_trigger` 通过 `has_trait_with_flag` 检查的内部特质分类标记（`00_available_for_events_triggers.txt:17–19`）。普通说明“没有带致命传染病标记的疾病”对应这条检查，不代表“没有任何疾病”，也不把英文标记当作 UI 新属性。

追加来源包含上述 caller 的有限行片段、完整原文件 SHA-256 及官方本地化 key/行号；它不改动旧 SOURCE-CONTRACT 或 portable JSON，也不把流程解释升级为新的 MCP 逻辑资格。
