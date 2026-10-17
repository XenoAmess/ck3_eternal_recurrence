# 第一期R8 W：实际解除纳杰夫与玩家信仰的圣地关系（1.20.0.4）

R8从原C2冷载后，按原版正常资格对普通圣地纳杰夫32执行一次abandon。独立后态读到Faith50名单6→5、实际支付1000虔诚；纳杰夫世界对象及Faith51的主要圣地关系保留，其他五处已读等级与库存完整不变。此动作减少本Faith的普通圣地数量，没有释放主要圣地名额。

`machine_id: 4-8e1c2f1861`，run `4-8e1c2f1861--faith-and-power--R0008`；原始观察覆盖2026-10-17T16:22:01.539360+00:00至16:24:53.585976+00:00，离线投影时间16:29:41 UTC。PID21564/create1792253831.3987103，source `02eea1e57a44a733cb833038b55a5fdc7bd4302a`，a06 DLL SHA-256 `7a5ef6ca4eeb05c56d0f96b2ace2409bff704d067e66136f2b29dd253c3475c7`。1.20.0.4/build25734779的EXE、冻结argv、逐份回执与静态源码绑定见[小证据](faith-and-power-episode01-r8-abandon-12004.evidence.json)。本研究仅消费固定W回执，不更新进行中的游戏状态。

输入为原 `C2-nadjaf-adopted-funded.ck3`，50,210,503B/SHA-256 `7bd48c5eb8c51a24badd02ba57cb030dba3526da4483479ae9adc231cea7ea7e`，配置enabled_mods=[]且哈希匹配冻结输入。原C2继承已披露的累计额外+5000虔诚、个人Maliki准备与此前采用纳杰夫的费用；用户授权原文为“允许独立机制实验存档，明确标注准备内容（推荐）”。R8本场初始钱包为4250，个人rite15、Faith50/mainrite13；没有沿用[R7 P重规划](faith-and-power-episode01-replanning-r7-12004.md)降麦加/升纳杰夫后的等级，也没有沿用[R7圣物链](faith-and-power-episode01-relic-r7-12004.md)撤回后的1750钱包。

T为当前Faith圣地总数，E为其中主要数，R=T−E为普通数：

| 独立读回 | C2冷载/W基线 | abandon后 |
|---|---|---|
| 当前Faith50成员顺序 | [26,27,0,14,29,32] | [26,27,0,14,29] |
| T/E/R | 6/3/3 | 5/3/2 |
| 虔诚钱包 | 4250 | 3250 |
| public/native snapshot revision | 3/2 | 4/3 |
| 日期/暂停 | 51394920/true | 51394920/true |
| 纳杰夫32关联Faith及等级 | Faith51主要、Faith50普通 | Faith51主要 |
| 纳杰夫库存/三个槽 | []/[null,null,null] | []/[null,null,null] |

16:23:42.513300–42.718907+00:00的原生detail独立读到action=abandon、decision_key=abandon_holy_site_decision、actor15893、parameter/selected site均32、普通规则native_can_confirm=true且bypass_raw=0。原生要求显示当前Faith的普通圣地成员、管理权与圣地总数“多于1个”；报价raw100000000/scale100000=1000虔诚、affordable=true，abandon冷却尚不存在。

16:24:50.799654–51.158985+00:00单次confirm回执只证明dispatch，`business_outcome_observed=false`；附带snapshot仍为4250前态。之后独立snapshot才读到3250，独立名单、明确指定site32的查询、relic-context与冷却查询分别读回业务结果，最晚16:24:53.585976+00:00。没有把ACK或附带旧snapshot当成付款/移除证明，也不因详情消失重复提交。

明确指定site32后的原生对象仍available，key=nadjaf、barony6650；其associated_faiths只移除Faith50，Faith51的available/member/eminent=true与基线一致。后继relic-context也独立读到associated_faith_ids由[51,50]变为[51]。这支持按 `(faith_id, holy_site_id)` 保存成员边，而非将玩家名单缺项当成世界对象删除。

余下五处的完整已读site行与前态逐项相同，包括全部关联Faith及等级、barony/type与库存字段；加上明确查询的site32，所有已观测圣地库存artifact IDs前后均为：

| site ID / key | 完整artifact IDs |
|---|---|
| 26 / mecca | [60] |
| 27 / medina | [61,62] |
| 0 / jerusalem | [63] |
| 14 / baghdad | [64] |
| 29 / sinai | [65] |
| 32 / nadjaf | [] |

`0`是有效Jerusalem ID，不能用真假值判断缺失。嵌入库存身份保持HolySite owner与对应ID；`artifact_objects_resolved=false`，本组未读玩家个人库存或具体神器的完整所有权，不能将空列表扩写成神器归还/归属不变的业务结论。

县主上下文也相同：county6649/barony6650、holder15436、holder rite13/Faith50。其 `county_holder_faith_associated` 从true变false，表明县主持信仰已经不在该站点的关联名单。cached/current Active前后均false，rarity均0且cache_evaluation_disagreement=false；本例没有Active由true关停的实测，也不能据显示仍Inactive推断成员关系未变。

独立abandon冷却查询读到present=true/active=true，expiry_raw51438720、current_counter_raw51394920，unit为native_decision_clock_counter，calendar_conversion_observed=false。保留原始计数，不换算到期日；只为该决议结算冷却，不代替promote/demote/Create的独立资格。

原版静态来源为 `common/decisions/50_holy_site_decisions.txt`，SHA-256 `80ad6a6045bdafdce514cbccf59a9cd1370eaef6749d510adcec759468065fb4`。337–359行检查管理权、当前Faith普通成员及总数下限；361–371行定义基础1000虔诚、免费条件和冷却；391–396行从actor Faith移除关系。378–387行另有“没有其他关联Faith且县主持存在”时将所供圣物转交县主持的条件分支。该退还分支只作源码知识：本例仍有Faith51且库存原为空，未验证非空库存、最后一个Faith退出或神器返还。后续好感/角色修正与免费次数同样没有独立后验。

供智能体采用的规划约束：

1. 区分总数与主要数。P降级使T不变/E减少；本次abandon使T减少/E不变。本次退出后的E仍为3；若规划目标是减少E，应另行评估降级，动作选择要对应具体瓶颈。
2. 对退出后的目标进行明确ID查询，比较其他Faith的成员/等级、站点对象和库存。不要因它离开玩家列表就丢掉世界引用；其他Faith可能继续使用同一地点。
3. 对弃用计划预先检查正常原生资格、下限、精确成本、决议冷却和潜在非空库存去向，再单次提交。用独立钱包/名单/目标/冷却后态结算；结果不明时继续查询，不盲目重发。
4. 将县主持Faith关联、圣物认可、缓存Active和当前计算分别保存。本例某个条件门发生变化而Active始终false，单个可见布尔值不足以描述机制状态。
5. 退还规则不能从空库存案例授格；实际涉及神器时需另取每件owner、个人/站点库存与槽位前后证据。不能默认神器回到玩家。
6. W之后创建新圣地仍是独立决策；名单变短不证明Create的类型、合法性或世界创建已完成。须由后继fresh原生上下文及其自身提交/后态结算，不复用W的合法性。

本候选只结算W这一原生操作；奉献度、政治代价、受益者修正、完整自动规划器集成、媒体人审、R8闭场、后续Create与whole-product验收均不由本组证据授予。原母档、R7/R8历史和原片均未修改。

后继补注（machine_id: 4-8e1c2f1861）：[R8 D3保存与正常闭场](faith-and-power-episode01-r8-closure.md)及[小回执](faith-and-power-episode01-r8-closure.json)补齐本篇建立后的事件。2026-10-17T16:42:44.947187–45.194231+00:00独立OS0，16:43:34.062600+00:00 CAS11495 done/resources[]；D3已保存/冻结，但Driver绑定不匹配、未冷载。public verify原exit2/research holder完成，三raw正常收尾仍未人审，whole-product业务资格不增加。原尚未闭场边界保留为当时截点。
