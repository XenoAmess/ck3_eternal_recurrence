# 原版 AI 会供奉、换物或取走吗（1.20.0.4，v4 窄研究）

原版确实配置了两条 AI 专用决议：一条供奉自有圣物，另一条有条件地清走圣地物品。供奉决议没有指定槽位；如果原生自动选槽实际选中非空槽，且完整供奉／旧物移除许可都通过，就会走同命令替换。它们都没有检查“原捐献者是不是人类”。这可以形成玩家供奉物被后来 AI 操作的风险，不能写成 AI 已经偷走、一定会偷，或所有有权限的 AI 都会尝试。

`machine_id: 4-8e1c2f1861`。本包只读主树 `d1c2bc7eb568a4eab3f55c065adb645a9dbace6f`，读取原版脚本与既有 exact-build cache；没有 CK3、Steam、桌面、SDK、构建、注入或自然采样。目标 EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518` 的本轮身份由 Root 的 `revision-v4-20261018/ROOT-TASK-START-PREFLIGHT.json` 在 `2026-10-18T02:15:13.270021Z` 重新核验，本子线程没有重新 hash／复制 EXE。本文的脚本和边界出处在 [source-contract.json](source-contract.json)、[pins](source-pins.json)；问题／边／未知由 [research-plan.json](research-plan.json) 统一生成 [research-graph.md](research-graph.md)。

## 先分清五层

| 层 | 已闭合的内容 | 仍不能代替的事实 |
|---|---|---|
| 动作合法性 | `can_enshrine_holy_site_artifact`／`can_remove_holy_site_artifact` 最终进入原生命令 guard | 合法不等于有 AI 候选，不等于被选中 |
| AI 候选 | 两个 AI-only decision 的真实 `is_valid` 和 `effect` 枚举来源 | `is_valid` 的见证组合不必是 effect 后来选中的组合 |
| 选择／评分 | 供奉按 `artifact_rarity` 排序取一件（原注释为最高），站点先零有效总量的主要站点再随机回退；移除为条件 sweep | 没有政治／受益者净值／原捐献者损失的统一评分；未验证 rarity 平手规则或自然随机分布 |
| 配置调度及调用 | 按最高头衔等级配置月份间隔、`base=100`；脚本 effect 到 guard 再到 receiver 的静态链 | exact native AI scheduler 的实际入口、每 actor 的下一检查时刻和本局自然 firing 未闭合 |
| 自然执行 | 本窄包没有自然 AI 轨迹 | 没观测不能变成“不会”，静态存在也不能变成“已经发生” |

## 供奉：可包含直接替换，不保证选到可执行组合

原版 `common/decisions/50_holy_site_decisions.txt:636–736`，全文 SHA `80ad6a6045bdafdce514cbccf59a9cd1370eaef6749d510adcec759468065fb4`：

1. `is_shown` 要求 AI；`ai_potential` 要求有物品；`is_valid` 要求 `is_available_ai_adult`，并在**自有物品 × 本信仰关联圣地**中找到至少一组：物品是圣物、被自己的 Faith 认可，且对该站 `can_enshrine_holy_site_artifact=true`。
2. `effect` 重新从自有物品中筛 `is_holy_relic_for=root.faith`，按 `artifact_rarity` 排序取 `max=1`。没有先把“对任意目标站完整合法”的物品筛好再排名。因此合法的低档物品曾使 `is_valid` 成立，并不保证最高那件还能找到合法站点；effect 也未重写 `is_valid` 中显式 `is_holy_relic=yes` 那一行。
3. 对选中的这件，先随机取本信仰的主要圣地，要求 `total_active_artifact_rarity_sum=0` 且当前原生供奉 guard 允许；找不到再随机取本信仰任意合法圣地。**总有效等级为零不等于物理槽空。** 所选站可以有不被县主信仰认可的旧物。
4. 最后执行 `enshrine_holy_site_artifact`，没有 `slot` 参数。实际有效槽仍由原版处理；只有实际选到非空槽才构成替换。

既有完整 picker `2C805E0..2C806CB` 原包已复读：先按原序取第一个兼容空槽；没有兼容空槽时，取兼容已占用槽中旧物 rarity 最低者，平手保先前 index。它不比较新旧档差、认可、收益、原捐献者、物品历史或政治费用，也不保证新物比旧物更好。调用者已另做完整许可检查，picker 自己不是 AI 的战略评分器。

因此，不能解说成“AI 会优先抢走玩家最高档圣物”或“AI 只会升级换物”。准确条件是：**AI 的新物／站点选中后，若实际 picker 选中玩家曾供奉的旧物所在非空槽，且最终两段许可通过，原供奉 receiver 会换入新物，把旧物交本次 AI actor。**接收者不按原捐献者返还。

这条供奉决议没有“最高领主必须 AI”或“本信仰宗教领袖必须 AI”的限制。人类最高领主可能阻止下一节的特定清理决议，却不能由此推导其领内 AI 合法供奉／替换也被全面禁止。

## 单独取走：有直辖县、信仰、性格及人类参与限制

同文件 `738–908` 的 `ai_remove_enshrined_artifact_decision`：

| 阶段 | 实际条件／来源 |
|---|---|
| `ai_potential` | 有 `zealous`，或 `ai_zeal>=25` |
| actor 可用性 | `is_available_ai_adult`；具体 availability 子 trigger 另有存活、成年、非旅行／非军队／非监禁／非无能、疾病、活动等条件，并非所有成年 AI 均合格 |
| 政治条件 | actor Faith 等于 top_liege Faith；top_liege 必须 AI；**actor 自己 Faith**的宗教领袖不存在或为 AI |
| 地理候选 | actor **直接持有的县**中的实际圣地；不是其全部领国的任意圣地 |
| `is_valid` Case A | 圣地关联 actor Faith，并有一件不被 actor Faith 认可、且原生可移除的物品 |
| `is_valid` Case B | 有另一个关联 Faith，县信众数>0，actor Faith 对其 hostility≥`faith_hostile_level`；有被该 Faith 认可且原生可移除的物品 |
| effect | 遍历全部符合的直辖县／站／关联信仰／已供奉物；Case A 清理本教不认可的物；Case B 筛选被上述敌对信仰认可的物，并另加原文 `NOT { is_holy_relic_for=root.faith; site.any_holy_site_faith=this=root.faith }` 块。原注释意图是避免清走本教也认可的本教圣地物品；多子句逻辑引擎语义本包未另闭。每件再进入原生 effect／guard |

Case B 的 `is_valid` 没有 effect 的上述额外保护块。因此有资格见证不代表这轮 sweep 必然移走某物；本文保留两阶段原文，不把一个布尔值当作执行结果。该保护块的多子句逻辑引擎本体不是本窄包的新研究，完整条件以冻结源码为准。

这个决议没有原捐献者／人类来源的筛选。若人类曾捐献的物品现在属于站点、落入实际筛选且原生 guard 允许，它没有因人类来源自动免疫。但“我在场”也不是足够的判据：人类 top liege 会使这条决议不成立；人类宗教领袖这一准入条件只检查 AI actor 的当前 Faith，不能外推为所有其他关联 Faith 的圣物都免于该决议。

## 原生 caller 已排除 GUI 混淆

以下是静态绑定，RVA 都指相同 exact EXE；逐体 SHA／指令范围见 `source-contract.json` 和 `static-packet-boundary-check-a01.json`。

| 脚本入口 | 注册／工厂／类型 | 实际消费方法 | 原生合法与执行 |
|---|---|---|---|
| `can_enshrine_holy_site_artifact` | `588E70` token→CTriggerEntry；entry factory `2B0D800` 构造 vtable `47A2F00` 的 `CCanEnshrineHolySiteArtifactTrigger` | vtable+`C8`→`2B0CDA0..2B0D009` | 栈 command `4770930`，读取其+`30`→guard `29AB4F0`，返回 bool；无提交 |
| `can_remove_holy_site_artifact` | `588F10` token→CTriggerEntry；`CCanRemoveHolySiteArtifactTrigger` vtable `47A2FE0` | vtable+`C8`→`2B0D040..2B0D259` | 栈 command `47707D0`，+`30`→guard `29ABB20`，返回 bool；无提交 |
| `enshrine_holy_site_artifact` | `5C5160` token→CEffectEntry；factory `2CC4640` 构造 vtable `48366B0` 的 `CEnshrineHolySiteArtifactEffect` | vtable+`B0`→`2CC31B0..2CC346B` | `2CC3352` call guard `29AB4F0`；false跳过，true于 `2CC3360` 以 command+`18` 直接 call receiver `29AADE0` |
| `remove_holy_site_artifact` | `5C5210` token→CEffectEntry；factory `2CC46E0` 构造 vtable `48365E8` 的 `CRemoveHolySiteArtifactEffect` | vtable+`B0`→`2CC34A0..2CC36FB` | `2CC35F0` call guard `29ABB20`；false跳过，true于 `2CC35FE` 直接 call receiver `29AB8A0` |

这里的 actor 来自脚本 root 的 Character scope（tag4/fullID），不是 HolySite GUI 全局当前玩家。AI 决议写明的这条 script-effect 路径会在 guard 后直接进入 receiver；没有经过 GUI `17D7580/17D76C0` 的 clone／`37F06D0` queue 提交。不能把 GUI 的 Can=true、点击 callback 或队列 ACK 当作 AI 调度证据，也不能为实现只读 MCP 调用这些 mutating receiver。

**没闭合的具体边**是：exact native 的 AI 时间／actor eligibility scheduler →这两个已注册 decision 的当次 effect 调用，及其自然选择与世界后态。现有 cache 的 pdata 对相关调用者缺 `85458/89754`；两个有限 locator block 只找到 `ai_decision.cpp` 错误日志与 `ai_decisions.csv` 计时输出，均排除为自然调度证明。没有 fallback 到 EXE，也没有扩大完整调度扫描。`.info` 给配置月份，不能反推出本存档下一次检查日期、每月概率或自然次数。

## 配置频率及概率的准确说法

两条决议都是：barony=0，county=24，duchy／kingdom／empire／hegemony=12。fresh `_decisions.info:152–176` 明确单位为**最高头衔等级对应的月**，0=永不考虑。`ai_will_do={base=100}`；`.info:267–268` 把这个值定义为执行概率百分比，100 表示检查到且满足其他门槛时配置上总会选执行。它不是“每年必成功供奉一次”，effect 重选的失配、实际原生 guard、未知调度与后态仍存在。本包没有自然样本来估计概率分布或实测频率。

## 对游玩智能体的最小补强

已有玩家权限 MCP 使用真实 HolySite 窗口和**当前玩家**全局 actor；不能把它用在一个 AI 身上后声称读到了该 AI 的真实许可。现有只读 context 的站点／认可矩阵仍有价值，可先作为风险解释的基础，未知项保留。

最小新增读取建议复用现有 relic-context 的可选结果域 `ai_risk_observation`，先限当前站点的**实际县主**这个 AI actor，明确 coverage 只到该 actor／单独清理候选。字段至少包括完整 actor/faith/top-liege/head ID 与 AI 标记、zeal/zealous、来源明确的 availability、直辖县与站点关系、每件实际槽物品的关联信仰认可和 hostility/follower 条件、原生 explicit-actor guard 结果或真实 unknown。若要覆盖供奉／替换，还必须读取该 AI 的真实自有 Inventory、rarity、效果阶段的站点候选和实际 picker 目标，不能拿人类玩家库存代替。没有合格 actor-aware getter／provider 时先返回观测缺口；不切玩家、不改全局 actor、不强制决议、不刷新世界。

静态预测分开保存：`legal_action`、`ai_candidate`、`configured_choice`、`natural_invocation_observed`、`world_postcondition_observed`。前三层不会把后两层变成 true；权限 true 不直接生成“AI会偷”的结论。规划器可据当前 AI 政治条件和物品认可把站点列为需要观察的资产风险，再权衡另换管理者、选多教认可物、保留个人圣物等真实可行动作，不由本研究增加阻塞整局的总门禁。

自然验证的最窄增量是在 Root 另行授权的正常运行窗口中，被动记录一个 actor 的真实 decision key、调用时间／帧、effect实际选中 pair、guard、receiver及后来独立 owner/slot/actor inventory 变化；还应读实际资源／意见。不可主动调用决议制造一次“自然”样本；没有调用的有限窗口也不能证明不会发生。

另发现原版 `events/siege_events.txt:1235–1295` 的 `siege.0032` 是不同的围攻圣物事件候选路径；这些条件中没有 AI-only 门，含站点／物品偏好及随机 effect。全文 SHA `b855e3a26fa65a400d2488ec0f29c1be71fcc9380579f092096a5a63e75bd672`，实际路径与 `1210–1320` 小摘录见 [stock-ai-decision-excerpts-a01.json](stock-ai-decision-excerpts-a01.json)。它不属于本两条和平时期 AI 决议；本包未闭该事件触发 caller 或测概率，不能把对清理决议的限制外推为战争中绝对安全。

## 范围与保留

本包只生成小型证据／派生文本，整个自有 `ai/` 上限6 MiB，计入父16 MiB与 Root 本轮84 MiB研究及台账总 cap；没有建设独立配额或重置旧资产期限。Root实际容量准入 `storage/RESEARCH-STORAGE-ACTIVE-a01.json` 生效于 `2026-10-18T02:21:06.281383Z`，下次审核 `06:21:06.281383Z`。源 cache 只引用不复制；本包派生 packet 默认48小时后复核，小型结论按共同 record 类180天复核。没有任何跨机器安装／自然实测信用。
