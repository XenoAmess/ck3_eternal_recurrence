# 供奉之后，谁能把圣物拿走？

本研究供第一期讲解与游玩智能体规划使用。范围为 CK3 1.20.0.4 / Steam build 25734779 的原版脚本和对应原生消费链；没有运行游戏、提交动作或采样自然 AI。源码基线 `d1c2bc7eb568a4eab3f55c065adb645a9dbace6f`，`machine_id: 4-8e1c2f1861`。本轮原文读取始于 `2026-10-18T02:15:57Z`。Root 于 `02:15:13Z` 实际重新核验 EXE，回执为外置 `episode01/revision-v4-20261018/ROOT-TASK-START-PREFLIGHT.json`，SHA `31454a0cc17a43f1dc4cfb8434521b558289138087b45bf5f59958891ea15504`；EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。PE 的 `1.0.0.0` 文件版本不充当游戏版本。

## 可用于玩家讲解的正文

把圣物放进圣地以后，先别把它当作自己的寄存箱。圣物已经进入这个圣地的库存，原来是谁捐的，并不是以后取回时的收件规则。直接取走，拿到物品的是这次执行动作的人；用一件新圣物直接替换旧圣物，旧物也交给这次执行替换的人。它不会自动回到原捐献者手里。

谁有这个管理资格？原版规则列了三个身份：圣地所在伯爵领的持有者，这个伯爵领持有者的最高领主，以及这个地方所属圣职区头衔的持有者。只做中间一层领主，或者只是全教信仰领袖，并不会凭这个身份自动获得这里的权限；还要看他是否同时符合上面三个地方身份之一。

供奉又比取走多几道门。你要从自己的物品中选择一件，圣地必须已经属于你的信仰；新物品还要通过伯爵领持有者当前信仰的圣物认可判定，并且有原版允许的槽位。这里有两个不同的信仰：操作人的信仰，决定这里是不是你的圣地；伯爵领持有者的信仰，参与判断新物品能否供奉。占领了别人的圣地，并不等于已经把它变成自己信仰的圣地。

单独取走的地域权限仍是那三个身份，但这条规则没有再要求圣地属于操作人的信仰，也没有要求操作人的信仰认可这件旧物。能拿走异教圣物，不代表没有代价。是否合法、谁会生气、会不会出现夺回圣物的战争理由，是后面分别计算的事。

那 AI 会不会拿走玩家捐的东西？原版确实写了专门给 AI 的供奉和取走决议，不是只有玩家按钮。单独取走那条，有一组很具体的保护：AI 要与最高领主同信仰，最高领主也必须由 AI 控制；自己的信仰领袖要么不存在，要么同样是 AI。一个人类最高领主，或这个信仰的人类信仰领袖，会挡住这一条 AI 单独清理决议。它还要是可用的 AI 成年人，达到狂热条件，并且从自己直辖的伯爵领内寻找物品，不是随便伸手去拿整个世界的库存。

它主要清理两种东西：自己信仰的圣地里、自己却不认可的物品；或者这里关联了一个敌对信仰，那个信仰还存在县级信徒，而且认可这件物品。对于共享圣地，真正执行的效果还会保护“这里也属于我教、我教也认可”的圣物，不能只因为敌教也喜欢它就一起拔走。

不过，人类最高领主的保护不能扩写成“我捐的东西绝对安全”。AI 的另一条供奉决议没有同一组人类最高领主、信仰领袖限制。它的原版设计意图是挑自己拥有的高稀有度圣物，优先考虑参与计算的圣物稀有度总和为零的主要圣地，再从合法的本教圣地中选择。它没有指定槽位，原版会替它选；如果最终选到已有旧物的槽位，就存在直接替换的路径。旧物交给这次操作的 AI。源码没有在这里查“这是不是人类曾经捐赠的物品”。这是原版配置存在的风险；本研究没有观察到某个 AI 在本局自然完成了这种替换，也不能把配置的执行倾向当作一段已经发生的偷取记录。

关系后果也不能只看“捐了加十五，拿走减二十”这一句话。正面的十五点好感，要先进入供奉的特定稀有度和认可分支，再逐人筛选：认可新圣物的宗教狂热立场直属封臣、符合狂热条件并认可它的各级上级领主，以及符合条件的本教信仰领袖。这是这些人对操作人的好感，不是操作人对他们的好感。

取走自己信仰认可的旧物，且没有用同档或更高稀有度的新物替代时，脚本会按旧物档次扣虔诚，并显式扣奉献经验。符合条件的同教宗教狂热立场、少数族群立场直属封臣，同教宗教狂热立场同僚，以及认可旧物的狂热上级领主，会对操作人产生负面好感。相关信仰的信仰领袖另有一段筛选，仍要有县级信徒、确有信仰领袖，而且该领袖认可这件圣物。不是地图上所有信仰都会一起生气。

用同档或更好的物品替换，能避开刚才那段本教取走费用，却不等于没有政治后果。另一个分支仍会检查其他信仰的封臣、同僚和上级领主；他们若认可被拿走的旧物，仍可能对操作人产生负面好感。这段没有同一组宗教狂热立场、少数族群立场限制。两种好感修正都设置了十年并逐渐衰减，也不能把十年理解为最后一天才一次清零。

所以，规划时要看具体是空槽供奉、同档替换、升档替换、降档替换，还是先拿出来再放进去。单独取出一件最高档圣物，脚本的基础损失是五百虔诚，并显式有五百奉献经验损失；若在两件都被自己信仰认可等条件下，把四档换成三档，还可能叠加新供奉那一段的负差额，形成七百五十虔诚的条件算例。不要把这个算例当成所有替换的统一价格。奉献总量、等级和好感最终怎样变化，都应当独立读回。

最后，界面提示异教统治者可能取得“夺回圣物”的战争理由，也不等于游戏已经为所有异教统治者发了一张宣战许可证。真正的战争理由还检查双方信仰、双方对物品的认可、能否转移，以及攻击者身份；AI 还有更高的狂热与头衔门槛。拿走圣物时看到警告，应该进一步评估潜在敌人，而不是把警告文字当作已经成立的战争。

## 人类操作的完整条件链

这里的“完整”是当前原版路径的分层链，不能用其中某一张脚本表替代最终原生 Can。三种动作均须解析真实 site/artifact full reference 与对象 magic；ID 索引存在或一个代理布尔值不足以证明对象有效。

| 层 | 供奉空槽 / 直接替换 | 单独取走 |
|---|---|---|
| 正常玩家物品来源 | 当前玩家库存候选，操作前独立核物品所有者和库存成员 | 当前圣地库存中的实际成员 |
| 地域规则 | 伯爵领持有者、伯爵领持有者最高领主、圣职区头衔持有者三者 OR | 相同三者 OR |
| 操作人信仰与圣地 | `actor.faith.is_faith_holy_site=site` | 移除规则中没有这一额外门 |
| 新物认可 | `2531200` 按伯爵领持有者当前信仰判断；不把“伯爵领持有者信仰关联此圣地”偷偷加成这个 helper 的条件 | 无新物；不要求操作人认可旧物 |
| 槽位 | 合法且类别兼容的显式槽；否则 `2C805E0` 原生选择器；必须找到实际可用槽 | `22E4420` 核确在该圣地库存 |
| 装备许可 | `22E44A0` 的 HolySite 分支检查槽类别与 `30FE7B0` 动态条件 | 无同一套新物装备条件 |
| 脚本规则 | 新物 `1D64FD0`；有有效旧物再调用旧物 `1D651F0`，replacing=新物 | 旧物 `1D651F0`，replacing=空 |
| 当前按钮 | 当前选择对象有效、不是已经归本站的物品，并在当前窗口重新 Can | 当前选择必须属于本站，再重新 Can |
| 实际执行 | 原版 handler 重新检查；receiver 解析目标、选实际槽、改变归属/装备并触发两个回调 | receiver 核库存成员，回调后给有效 actor；无有效 actor 的异常分支只卸下，不伪称给伯爵领持有者 |

原文 `02_holy_sites.txt:6–26/52–64`，原生 `29AB4F0:29AB4F0–29AB728`、`29ABB20:29ABB20–29ABC0E`。新物所有权是正常玩家 GUI 候选/本项目动作准入另核的条件；**裸 CanEnshrine 返回 true 本身不证明当前玩家拥有新物**。当前按钮、显式 artifact Can、当前选择槽与实际自动目标槽是四种不同事实。

`30FE7B0` 本轮审到 `30FE881`：slot 对象 `+164` 无条件记录时直接 true，否则用该对象 `+118` 的条件在 holy-site 上下文求值。早期缺失 pdata 记录的 function 查找真实失败，随后从确认入口做有限 cache 解码，未读 EXE。原版 `common/artifacts/slots/01_holy_site.txt:7–20` 的三个 holy_relic 槽均允许任意 type/category，没有额外装备 trigger；有 mod 改动时必须重新核原定义和原生 Can，不能用此原版结论绕过检查。

原生 receiver `29AADE0` 中，新物 `2530300(new,site)`，非空旧物 `252FDD0(old,actor)`，再装备新物。`29AB8A0` 单独取走也以 `252FDD0(old,actor)` 收件。两处都不查原捐献者。GUI 的 `HOLY_SITE_REMOVE_REQUIRES_HOLDER` 短提示只写“伯爵领持有者”，不足以覆盖原版完整三地域 OR；同文件 `holy_site_not_holder_or_top_liege` 才列出三者。

## 两个回调与每一类意见对象

记 A=操作人，F=A 当前信仰，N=新物，O=被换走/取走的旧物，R(X,f)=对指定信仰调用真实 `is_holy_relic_for`。不能以动态认可列表为空推断 R=false。

| 分支 | 真实门 | 资源效果 | 哪些人对 A 改变意见 |
|---|---|---|---|
| 新物供奉奖励段（inventory_on_actions 138–295） | nullable `scope:replacing ?= { R(O,F), O.rarity_level >= N.rarity_level }` 令 flag=no；并且 R(N,F) 与 flag=no | `add_piety=B(N)-B(O)`；没有把 effect 名改写成“只动钱包”的资格 | A 的直属宗教狂热立场封臣且 R(N,其信仰)；A 各上级领主满足 ai_zeal≥50 或 devoted/zealous 且认可 N；F 信仰领袖存在、不是 A、认可 N：各 `+15` |
| 旧物本教损失段（333–353,385–460） | R(O,F) 且（无 N 或 N.rarity_level < O.rarity_level）令移除 flag=no | `add_piety_and_experience=-B(O)` | A 同 F 的直属宗教狂热立场封臣、同 F 的直属少数族群立场封臣；有上级时，上级的同 F 宗教狂热立场直属封臣；A 各上级满足 ai_zeal≥50 或 devoted/zealous 且认可 O：各 `-20` |
| 相关信仰领袖段（355–383） | 移除 flag=no；枚举 S 关联信仰，num_county_followers>0；领袖存在、不是 A、领袖信仰认可 O | 无这一段的额外资源效果 | 这些信仰领袖对 A `-20`；这段独立于下面的 if/else 分派 |
| 其余移除段（462–522） | 上述本教损失 if 不成立；`else_if` 本身**没有 limit** | `custom_tooltip` 显示夺回 CB 文案，不直接 grant CB | A 直属封臣；有上级时的同僚和各上级；各须 R(O,其信仰) 且（其 faith!=F 或移除 flag=no）：`-20`。**没有**宗教狂热立场/少数族群立场额外门 |

两种 modifier 原文 `pam_opinions.txt:111–120`：正面 `enshrined_holy_relic_at_holy_site=+15`，负面 `removed_holy_relic_from_holy_site=-20`，各 `years=10,decaying=yes`。每个 add_opinion 的 target 都是 A。一次动作中同一人可能符合多个角色；本包不将重复循环写入机械累加成数倍，也不从多个角色名推造实际总意见后态。不同正/负 modifier 可以同时成为需要核对的分支。

正面封臣筛选没有统一 same-faith=F；认可新物的异教宗教狂热立场也可能进入。移除本教费用段的直属封臣却明确要求同 F。其余移除段又按逐人认可筛选，而非按封臣立场筛选。信仰领袖负面段有 `num_county_followers>0`，不能从“关联信仰列表存在”推断每位领袖都受影响。奉献等级影响与这两种十年意见 modifier 是不同量。

`B(common/masterwork/famed/illustrious)=50/100/250/500`，来自 `00_basic_values.txt:1132–1158`。若已有非空 O、两件被 F 认可、旧四档新三档，供奉段为 `250-500=-250`，移除段再显式 `-500`，钱包的条件源码和为 `-750`；移除段显式奉献经验 `-500`。新供奉段的 `add_piety` 对奉献的引擎语义与最终独立读回必须另核，不能仅因为名字没有 experience 就断言不影响奉献。空槽使用 nullable scope，不能在本离线模型里擅自把不存在 O 的条件赋真/假以承诺固定奖励；以真实原生效果预览与后读为准。

升档或同档替换会令移除本教费用段不成立，但可能走“其余移除”对认可旧物的异教关系对象产生 -20，并显示 CB 警告。降档则可能同时有新物的 +15 分支与旧物的 -20 分支。不能用注释“better artifact”反转原文的 `>=` 或 `<`，也不能把“直接替换”当作先取出、再供奉两次动作的价格。

## 夺回 CB 警告的实质

`inventory_on_actions.txt:464–467` 只是 `custom_tooltip`。真正的 `reclaim_relic_artifact_war` 在 `01_ep1_wars.txt:342–427` 及 `00_artifact_triggers.txt:2223–2248` 检查：

- 攻守 faith 不同；普通圣物要被攻击者认可、而不被防御者认可，且没有 `artifact_prevent_transfer`。
- 攻击者不是 landless adventurer；AI 额外 ai_zeal≥100、至少公爵，人类不受这两个 AI 门限制；AI 另有 only-against-neighbors 配置。
- AI 的 against 检查从防御者本人库存找；人类分支还可检查防御者的不同信仰下属库存。伊比利亚斗争圣物走另一套条件，不能混成“所有物品”。
- 这只是该 CB 的局部规则，仍需整个原生宣战合法性。胜利时按当时合格物品转给攻击者，并非回原捐献者或自动回圣地（450–510）。

## AI 候选、评分、调用者与自然执行必须分别记账

本段复核独立子研究 [ai-callgraph-review.md](evidence/holy-site-relic-management-ai-opinion12004/ai/ai-callgraph-review.md) 和该目录的小型原文/原生包。五层分别如下：

| 层 | 本轮结论 | 不授予的结论 |
|---|---|---|
| 动作合法 | 脚本 trigger 构造原命令、调用完整 Can；AI script effect 再核 Can | 不是 AI 候选或选择结果 |
| AI 候选 | `ai_enshrine_artifact_decision` 从自有物品与本教站寻找；`ai_remove_enshrined_artifact_decision` 从直辖伯爵领取条件候选 | is_valid 的见证 pair 不保证是 effect 的最终 pair |
| 排序/选择 | 供奉按 artifact_rarity 排序 max=1，注释“最高”；主要站先缓存总数为零再随机回退；取走为条件 sweep | 默认排序方向/平手的引擎消费未在本包独立验证；没有自然随机轨迹；不伪造政治收益综合评分 |
| 调度/原生消费 | 原版 `.info` 把 tier interval 定义为月、ai_will_do 为百分比；script effect 已对齐到原命令 guard→receiver | 原生 scheduler 本次 actor 的当次决议 firing 仍未闭，不能从 base100 推本局事件次数 |
| 自然结果 | 本包无新实机样本 | 不能写已经被 AI 拿走、100%每年被拿、或绝对不会被拿 |

两条决议配置 county=24个月，duchy/kingdom/empire/hegemony=12个月，barony=0（不考虑）；`base=100` 是检查到且满足门槛时配置执行概率100%。这不是每月概率，也不是每12个月保证业务成功一次。

供奉的 is_valid 只要求存在合法 pair；effect 却重新排序取一件，再找站点，不保证这件仍可找到合法站点。effect 还没有重新写 is_valid 中独立的 `is_holy_relic=yes` 条件。取走 is_valid 的敌教 Case B 没写 effect 后续的共享保护块。不能把前置布尔值代替真实枚举和后续 guard。

实际原生 script 链已与 GUI 分开：

- `can_enshrine_holy_site_artifact` 的 trigger 方法 `2B0CDA0..2B0D009` → `29AB4F0`；remove trigger `2B0D040..2B0D259` → `29ABB20`，两者只返回许可。
- `enshrine_holy_site_artifact` 的 `CEnshrineHolySiteArtifactEffect` 方法 `2CC31B0..2CC346B` 在 `2CC3352` 核 guard，通过后在 `2CC3360` 直接调用 `29AADE0`。
- remove effect `2CC34A0..2CC36FB` 在 `2CC35F0` 核 guard，通过后在 `2CC35FE` 直接调用 `29AB8A0`。
- 这里 actor 来自脚本 root 的 Character fullID，不是 GUI GetPlayer。该 effect 路径没有走 GUI clone/queue；只读 MCP 不得调用这些 receiver。当前原生 AI scheduler→decision effect 的当次自然调用仍是明确缺口。

自动 picker `2C805E0..2C806CB` 完整体另已复读：首个兼容空槽优先，否则选兼容已占用槽中最低旧 rarity；严格更低才更新，因此平手保留原序。它不读 donor、物品历史、认可或政治代价，也不比较新物是否比旧物更好。这个机械选槽规则与 AI 的物品排序是两个 producer，不能混成一个评分。

人类 top_liege / 人类 HoF 条件只出现在 AI 单独清理决议，不在 AI 供奉决议。AI 的“直接持有县”也不能外推成任何中间领主可随意拿全领国库存。`is_available_ai_adult` 原文另有旅行、活动、监禁、疾病等 availability 条件，详见子包原文；一个 AI 成年不代表当次可用。

本研究还发现战争中的 `siege.0032` 圣物事件候选，属于另一条路径；本包没有闭合该事件自然触发 caller 或采到一次执行。单独清理决议的人类保护不能扩写成战争中也绝对安全。两条圣地管理决议没有 `at_war=no`，不能称为“仅和平时期才会触发”。没有自然样本不表示该路径不存在。

## 可复用 MCP 与最小缺口

当前 MCP 是**当前人类玩家/实际窗口**合同，不接受任意 actor 以伪装 NPC 决策。以下仅列现有接口形状，未在本轮调用：

```text
ck3_query_player_holy_site_relic_permissions_v1(expected_revision, holy_site_id, artifact_id=None)
ck3_query_player_holy_site_relic_action_context_v1(expected_revision, holy_site_id, artifact_id)
ck3_query_player_holy_site_relic_context_v1(expected_revision, holy_site_id)
ck3_query_holy_site_planning_knowledge_v1(action, ck3_build="1.20.0.4")  # 来源知识，不替代当前状态
```

可复用 `artifact_permissions.can_enshrine/can_remove`、`current_buttons`、`player_inventory`、`window_context.slot_mode/selected_slot_index`、`destination.effective_slot_index/replacing_artifact_id/replacing_artifact`、`artifact_ownership`、`selected_action_effect_description`、两个 disabled tooltip、`preview_identity_sha256`。认可矩阵已有“关联信仰+玩家信仰+伯爵领持有者信仰”与“slots+候选+请求物品”的并集，逐格 available/value，未知保持 null；它没有涵盖所有封臣/同僚/上级信仰。

动作工具已有一次性 intent、revision/preview 与旧物精确绑定；ACK 保持 pending，仍需独立库存/所有者/槽位/虔诚/奉献后读。不能为本专题另建一个绕开 Can、旧物或 once guard 的取物接口。

最小新增建议为只读的“关系后果/AI风险解释”投影，而非代替游戏执行：

1. 基于上述现有 action context 加原版分支模型，列出 candidate opinion subjects 的 fullID、关系角色、faith、stance、狂热/特质条件、逐物认可、来源行；资格缺失保留 unknown。不把已有矩阵的缺格当 false。
2. 若要回答某个 NPC **当前**是否会考虑，需独立 AI decision 观测合同：actor 是否 AI/可用成年、top_liege 及 faith/head 是否人类、直辖伯爵领、敌意、关联/县级信徒、候选原序和最高排序结果、随机目标、Can 与 effect 保护；不能复用人类 GetPlayer 的 Can 伪造。
3. 要写“本局 AI 实际取走”，还缺自然调度触发、该 decision 实际执行 actor/候选/目标/槽位，以及独立物品归属差集；本轮全部未知。静态 base100、Can=true 或 receiver 可达都不是这项结果。

本包没有新建 MCP 实现、没有扩大动作资格。补齐后的静态知识应进入已有 planning knowledge；实时读取仍沿已有 exact build、actual fullref/window/frame、未知不升级的守卫。

## 来源与边界

- 本轮 fresh stock 原文与 SHA：`stock-source-excerpts-a01.json`（生成后与 manifest 绑定），含 rights、on-actions、opinion、基础数值、CB、原版 GUI/槽。
- 本轮 AI 详细来源/原生 trigger-effect 接线由 `ai/` 独立记录；自然 scheduler 与自然执行仍按该记录的 unknown 边，不以源命中授实机资格。
- 复读既有完整原生包：`EP/relic-candidate/native-source/function-029ab4f0.json`、`function-029abb20.json`、`function-01d64fd0.json`、`function-01d651f0.json`；完整 receiver 在 `EP/relic-candidate/permission-candidate-a01/source-guard/enshrine-receiver-complete.json` 与 `remove-receiver-complete.json`。本轮重新审阅这些字节派生的对齐 asm，未复制 EXE 或大段缓存。
- 原 `holy-site-relic-native-permissions12004.md` 与 shared-relic 研究是导航；本轮实际脚本 SHA 与原 manifest 一致，具体结论仍落到上列原文/原生调用消费。没有因为历史 R7/R9 等 human 实验而声称自然 AI 已验收。


## 本轮交接说明

本文是修正后的 final 文稿；`permissions-opinion-v4.md`、a01 plan/check 原样保留。final 将“历任上级”改为“各级上级”，避免把当前领主链误说成历史领主；将最高稀有度表述限定为原版设计意图，并补 AI 的独立候选/配置/实际调用者/自然执行边界。

AI 子包封后语义补注见 [wording-clarification-a02.md](evidence/holy-site-relic-management-ai-opinion12004/ai/wording-clarification-a02.md)：remove trigger 的 factory `2B0D8A0` 只到 RTTI/定位，未新增审完整 body，不把高层静态链当每一条中间工厂指令全闭；已经审阅的注册 token、实际 guard consumer、两条 effect→receiver 证据保留。AI 子包 a01/pins 不覆盖，本 final 也不授自然执行信用。

Root 和术语研究子线程均没有提供已经闭合的 `add_piety` 正负奉献 consumer。本包因此保留该未知边；显式 `add_piety_and_experience=-500` 不足以单独证明降档整个动作的奉献总差精确等于 -500。旧稿若写总差，应待对应引擎闭链与实测后读后再定稿。

## 2026-10-18 add_piety 负值奉献影响补注

当前 1.20.0.4 EXE 的注册→编译执行器→实际写入 consumer 已闭合：普通 `add_piety` 的负值只减虔诚钱包；`add_piety_and_experience` 的负值同时减钱包与奉献。双认可四档换三档且两段原版回调均进入时，−750 虔诚／−500 奉献可作为未调整基础值算例；两个效果均先经过原版资源倍率，不能当作实测净差。正值普通效果在负钱包时先补债，余量才增加奉献。详见[原生正负分支与限定](holy-site-piety-experience-consumer12004.md)。此前冻结原件中的未知声明保留为历史知识状态，本补注闭合该具体未知边；没有新增游戏实测。机器 `4-8e1c2f1861`。
