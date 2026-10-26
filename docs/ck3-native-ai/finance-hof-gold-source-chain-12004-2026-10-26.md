# 向宗教领袖请求资金：1.20.0.4 来源链与真实迁移缺口

`machine_id: xenoamess-full-tower-eb9d2c1186`。研究于2026-10-26恢复任务期间进行，仅读取当前安装文本、已持有迁移证据和源码。安装见证为 `resume61/formal_release/INSTALLATION-WITNESS02.json`（`2026-10-25T21:43:36.139626Z`，SHA-256 `49f08808eb15dd2eb2d24d05f400c7dd68cf1d4d7de14741e2efbbd7417c339c`）：`1.20.0.4` / Steam `25734779` / BetaKey `1.20.0`；EXE元数据未变，复用 SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。没有新读/哈希EXE，不把安装见证当作 loaded Game。

原版 `hof_ask_for_gold_interaction` 是独立融资渠道。金币或国库资源在**接受请求的 effect**中支付；发送、预览、接受度、通知或信件确认均不证明实际到账。[旧1.20.0.3专题](religion-catholic-head-of-faith-gold-native-ai-12003.md)已有完整普通请求只读 primitive 的历史负例，含58.33566金币报价、shown=false/CanSend=false；那不是本机当前1.20.0.4的报价、可执行资格或收益。

[同源生成图](finance-hof-gold-source-graph-12004-2026-10-26.md)绑定28份文本/源码/迁移证据，分别画出 GUI、原生AI、bridge与未闭边。本次没有修改预算policy、动作、flag、router、native或Java生产实现；它不成为首场启动的新门禁。

## 谁是候选，谁实际收到请求

当前 `00_religious_interactions.txt:6791` 的 AI candidate sources 共六域：`head_of_faith`、`religious_head_challenger`、`realm_priest_superior`、`superior`、`realm_priest_top_superior`、`councillors`。quick trigger 要求目标成年。`_character_interactions.info` 明确多个域组合；本互动未设置 `max` 或 `chance`。这不证明native内部枚举、缓存、去重、遍历顺序或最终目标选择已经恢复。

玩家GUI先给定目标，再进入redirect；AI候选域不是玩家完整合法目录。redirect在 `scope:actor` 下执行：

- 低于国王的actor，原目标是其信仰领袖且存在合格superior时，神权actor转向自己的superior，其余转向本廷司祭的superior。
- 国王以上以自己/司祭的superior为原目标时，若信仰是精神领袖型并有合格、非自身/非当前目标的宗教领袖，则改向该领袖。
- 最终资格还保留无superior时自家公爵以上神权司祭的fallback；不能因普通head读口返回缺头就断言完全没有合法资助对象。

请求必须保留完整构造后角色：actor、recipient、secondary actor/recipient、intermediary、puppet_or_actor。显示资格以 `puppet_or_actor` 的信仰/可玩身份等为依据，付款对象和金额基数使用 `scope:actor`；二者不能按“都是罗贝尔”直接合并。普通旧leaf只从当前faith head开始构造一次请求并允许原生redirect，未实现六域候选搜索。

## 显示、合法性、成本与冷却

显示要求recipient不等于puppet_or_actor，后者为可玩角色、信仰具精神领袖或教区参数、不是ecclesiastical政府，并满足允许的宗教领袖/挑战者/神职目标；recipient与puppet_or_actor同信仰。PAM反教皇及其追随关系继续适用，原版另有反教皇资助互动，不能只按名称重定向给任意神职角色。

实际失败条件分列：

| 输入 | 当前脚本条件 |
|---|---|
| 付款者资源 | 有treasury则treasury≥最终Q，否则gold≥Q |
| 合法神职对象 | 精神领袖/挑战者、本人或本廷司祭的superior，或上述fallback |
| actor虔诚 | 至少 `major_piety_value=250`，使用hook仍要满足此发送资格 |
| PAM虔诚等级 | 世俗actor须等级≥3或具神学代理傀儡；神权actor等级≥1 |
| actor阻点 | 未被绝罚、不与recipient交战、没有向神职承诺朝圣修正、非未改革信仰、反教皇路径符合 |
| 对recipient冷却 | 3年；当前原生CanSend才是实际冷却许可来源 |

`is_available` 里额外的piety、绝罚、`hof_request_cooldown`和有地/神权条件包在 `is_ai=yes` 分支，不能加到人类actor上。另一个anti-spam触发器只限制AI向人类recipient请求；发送时在人类recipient上设置3年同互动接收flag，并给AI请求者设置国王以上1年、公爵2年、其他4年flag。它与普通recipient三年冷却是两组独立状态。

声明cost只有 influence：默认0；选择影响力选项时60。该选项要求actor使用影响力政府、足额且与recipient同top realm，接受度加25。hook选项要求可用hook，选择后是独立auto-accept分支；选项并非互斥。朝圣选项另有PAM显示/资格。**250虔诚通常在on_accept扣除**，不是通用cost vector；选hook则使用hook并免该扣除。声明十资源cost中piety=0不能解释为免费请求。

## 最终数额与三种支付资源

`01_dynamic_values.txt:351` 明确“付款神职是当前scope；所求金额按申请者缩放”。native quote必须用有效recipient为root，并保留命名actor/recipient及原上下文：

`B = actor.head_of_faith_treasury_or_gold_value`

`Q = max(50, min(B, effective_cleric_treasury_or_gold × 0.5))`

actor无treasury时，B为18个月脚本收入，限幅50至时代调整的1500；actor有treasury时，B为18个月可变国库收入，限幅150至时代调整的4500，有culture的霸权还把该上限乘2。没有culture的时代上限倍数为1，早期以前0.75、早期1、高期1.5、晚期3。本value没有动态普通gold值里的向上取5操作，不能擅自取整。

Q最后才应用最低50，因此不能声称“永远不超过付款者余额一半”。发送资格又独立要求付款者余额至少Q。资格、quote、接受后effect在不同时间可能重新求值；没有证据证明旧quote被冻结为实际支付金额。

| 接受时付款者 | 接受actor | 脚本实际effect |
|---|---|---|
| 有treasury | 神权 | `pay_treasury_or_gold(target=actor,value=Q)`；文本意图保留教会国库资源 |
| 有treasury | 非神权，即使actor也有treasury | `pay_treasury_to_gold(target=actor,value=Q)` |
| 没有treasury | 任意 | `pay_short_term_gold(target=actor,gold=Q)` |

三种effect的exact native钱包应用仍由原生付款研究独立闭合，不能根据effect名或已满足gold资格推定短期预算、实际扣款/到账和事务性。该路线也不是holy-order借款，不能继承借款额度、债务或还款状态。实际到账资源可能是treasury，不能把同额数字无条件加到个人金币军费。

## 接受权重与AI发起意愿是两棵树

原版最终接受度必须读native，下面是已固定的完整脚本依赖组，数值都是score，不能解释为概率或只相加几个因素当完整答案。

| 接受度输入组 | 脚本项 |
|---|---|
| 主体 | base -40；Ear of Clergy +25；recipient→actor意见×0.5；同语言+5 |
| 资源 | recipient资源超过2500的超额×0.1，最多+50；recipient高贪婪-20；actor按medium/major/massive treasury动态门槛分三档富裕惩罚-25/-50/-75 |
| 战争 | 主攻未被绝罚的同信仰主防守者-50；参加进攻的非GHW圣战/绝罚战+30；参加防守的非GHW圣战+50；这些条件分别写出，并非自动互斥 |
| 行为/神圣血统 | 与礼仪有关的通奸/私通-25；谋杀-50；不被收件人礼仪允许的乱伦-50；被本礼仪谴责的弑亲-50；指定圣血/典范等特质+5或+15 |
| 关系 | 亲族/同家族/同宗族分支，父母+25；朋友+25、挚友+50、情人+10、宿敌-100、死敌-500；按实际关系和排除条件执行 |
| 虔诚与罪性 | 每美德+10；piety level>1时5×等级；等级>2且破产另5×等级；每罪性-10；人类hard/very-hard另-25/-75 |
| Celestial hierarchy | 满足神职→世俗统治者参数+20；同信仰指定个人信条按actor与recipient虔诚等级差×10 |
| PAM神职关系 | recipient恰为神学代理+100；非神权且无神学代理-25；不同rite -20，recipient对actor rite的满足度高/低另+25/-25；core或permitted信条被recipient禁止分别-100/-40 |
| 选项 | 影响力+25；承诺朝圣加独立script value；选中合法hook进入auto_accept |

`ai_will_do` 是发起方意愿，base0：hook -1、神职actor -25、实际条件 `<tier_county` 且recipient不足3000时-50（注释写Counts，不改写实际比较符）、非独立公爵且recipient不足3000时-25、向人类HoF -50。战争且gold低于medium +50；债务且recipient符合荣誉/热忱条件+50；严重债务再+50；多余虔诚且非贫穷誓言/慷慨+25；正贪婪值加该值。recipient≥1000并且actor为经济扩张性格、有额外虔诚、或好战且 `war_chest_gold < war_chest_gold_maximum` 时，再加最多50的溢出金库项；建设/虔诚建设性格-100，曼荼罗-100。

这些 `war_chest_gold` 输入的native producer/cadence未在本专题恢复，不能命名成我方owned commitments或雇佣应急reserve。AI检查频率为伯爵36个月、公爵24个月、王国/帝国/霸权6个月、男爵0；不是玩家紧急资金策略的既定等待期。实际AI scheduler caller、候选索引/缓存和重算时点仍unknown。

## 什么时候才算支付，之后还发生什么

声明AI答复延迟1–5日；on_accept先执行付款/虔诚或hook、朝圣承诺，再触发actor的 `religious_interaction.3`。该信件immediate只在 `show_as_tooltip` 中重复付款effect；确认信件没有再次支付。信件还按当前战争选展示用war_target scope，不能把描述当新的财政动作。

接受effect另含recipient AI对actor -20请求资金意见；指定诡计/荣誉/热忱条件下可让recipient取得对actor的favor hook；狂热封臣对actor -10意见，10年衰减且可叠加。承诺朝圣为10年，月虔诚-25%且精神满足度损失倍率+25%，并阻止后续此请求。教会局势还可能给actor建设/军团费用/补员或宫廷相关的5年或10年修正并触发局势catalyst，须保留实际对应phase，不能只记录金币。

on_decline对recipient扣25虔诚，actor收到 `.32`；其中refusal -50意见只对AI actor生效。这个路径没有actor250虔诚扣除，但不能据静态正文推断发送时影响力费用何时退回。付款/未付款、费用/退费、通知与实际后态分别验收，UNKNOWN请求不重放。

## 实际1.20.0.4实现缺口与已有复用入口

`native_religion` 确认当前原生HoF mailbox仍有1.20.0.3版本/SHA硬锁；目前只读本leaf不能因配置flag而在1.20.0.4工作。本包核对现存来源，已有多数通用输入，不需要再全图复制、重新捕获或给旧RVA统一减0x20。

| 需要的输入 | 已有精确来源/入口 | 边界 |
|---|---|---|
| definition、two-role、refresh/finalize、validator、cost、score、hash | `BindInteractionContext12004`；`prisoner/current4-context-release/ROOT-DELIVERY.json`固定完整body和消费布局 | query binder，不授send command或HoF当前结果 |
| context和definition布局 | 上述proof：size338、scope+8、roles2D8..2EC、option rows2258/count2264/stride730/flag368；auto trigger2290/scalar2718 | 无需把旧.3布局仅凭相似假定为.4 |
| whole shown | `ck3_12004_sway.cpp` 的3079690；Sway迁移已持完整224B source | 不能用CanSend代替shown |
| option set/read与outer answer | Family/Grant逐项映射：30788C0/3078860、307BC60；intermediary score307C340 | 当前选项仍须真实读回全部未选中 |
| 宗教领袖身份 | `BindRiteGovernanceImage12004(...).heads`已有实际4context及FaithHead2439DF0/title2443F80 | 要正确同帧读head，不能回到old `BindRiteHeadsImage12002` |
| 保留命名角色的Q | `ReadNamedInteractionFixedExact12004`，scope clone373ACF0、evaluate37542D0及已闭scratch/清理 | root=effective recipient、named actor/recipient，不能用actor-only loan helper |
| 现存序列化 | `Render12004BuildIdentity` 会按真实4descriptor转换嵌套version/SHA/schema/backend；bridge也有实际frame renderer | 仅在实际4producer已合法绑定时适用，render不能让old native调用安全 |
| Java实际consumer | `ReligionTemporalFinance.normalizeEnvelope` L94当前把GOLD/LOAN/TITLES/REPENTANCE限定CROZIER3；schema函数L109只转02前缀 | native迁移后必须同步真实consumer及renderer产物回归，不能手改测试JSON |

当前Java观察源 SHA为 `234c0f3479694ee9047c56cf1d2b6ca4050e1ee2ca25fc807bacaa39391cc3c1`，属于Host mutable树当时的事实，不是以后永远有效的版本。这个双端缺口已交 `native_religion`、机制lead；M6确认不拥有该consumer，本专题未擅自整叶覆盖。

最小后继施工是复用上述实际4输入，在原有普通head只读leaf中补正确descriptor/frame/bindings，再沿真实renderer→Java decoder验证。完整六域候选/无头fallback是额外未实现范围，不能把最小leaf成功称为完整融资搜索。新actor、当前Shown/CanSend/option/cost/Q/接受度以及最终资源与全部liability，都需要对应的新鲜原生结果。

## 本轮核验

现有 `native_research_plan.py init/check/render` 的最终check为 `HOF-GOLD-CHECK23b.json`，exit0，核对28份文件；图声明13条static-confirmed、6条unknown、5个业务问题pending。`semantic_correctness_verified=false`、`live_execution_performed=false`。初稿check23只校验当时草稿；随后纠正见证时间的叙述笔误并重新生成最终图，check23b及最终plan hash为本次交付依据，没有重跑游戏或业务。

机器包为 `D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/native_war_cash/HOF-GOLD-PLAN23.json`。无新EXE读取、Game/MCP、JVM/Maven、C++、动作或游戏日；原版/迁移大文件仅引用，没有复制。本轮不为融资增加新gate，不停止普通战役，未到账资金credit仍为0。容量及活跃依赖于 `2026-10-26T08:00:00Z`复核，不自动续保护。

