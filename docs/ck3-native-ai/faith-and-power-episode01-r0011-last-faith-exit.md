# R0011：最后一个关联信仰退出后的圣物返还

机器`4-8e1c2f1861`，CK3 1.20.0.4，冻结源码`e23f9de04018b638c62e0b72d39d88b56f0010cb`。R0011是重新冷载原C2的独立场次，PID14764；没有先放弃旧圣地、额外添加资源或推进日期。精确来源与实际UTC见同名`.evidence.json`。它与[共享圣地退出](faith-and-power-episode01-r9-r0010-observations.md)共同提供两个不同分支，不能混用基线。

本场创建智慧圣地326后，Faith50圣地数6→7，326为普通、仅关联Faith50，237在slot0，县主为玩家15893，Active=true/有效稀有度4，钱包4250→2250。随后取得全新原版正常CanConfirm=true、bypass0、报价1000、affordable=true、冷却未激活的读回，再提交一次放弃。独立后验是钱包1250、Faith圣地数回到6，原六个完整站点DTO均未变。

**最后一个关联信仰退出后，圣地对象仍存在且可读。** 对326的独立查询返回available=true、关联列表空、库存空；不能讲成圣地已销毁。更关键的返还证明来自20:51:03.125844–03.667025Z对237的独立所有权读回：character owner=15893、holy-site owner=null、玩家owned引用为true、玩家库存含237、未装备。该次读取借用仍可用的圣地14上下文，不表示237归圣地14，也不是根据空槽猜测返还。

原版县主返还规则来自已有exact source：`common/decisions/50_holy_site_decisions.txt`373–396，在没有其他关联Faith且存在county holder时先把库存交该县主，再移除本Faith关联。本场actor与county holder同为15893，所以实际只证明237归该角色，不能用这个场景实证区分“给操作者”还是“给县主”。对比R0010直接替换旧物归actor、共享退出库存留站点，应分别规划三种路径；也不能承诺关联已空的旧对象可以立即重新采用。

最初一次打开放弃UI在Python预派发阶段被拒，随后detail没有有效定义、CanConfirm为null；这不等于原版正常条件禁用，也不是已提交的放弃业务失败。恢复后仅重新打开UI，再于20:49:07.631628–08.072670Z取得新正常报价；唯一成功Confirm于20:50:29附近提交，20:50:30.008520Z完成，随后独立读回业务结果。没有重放未知结果的Confirm。

创建动作已有录制；成功的最后Faith退出动作未被录到，第二take在成功UI恢复之前结束。原两take已消耗、第二take120秒封顶是Root现场交接的媒体边界，单项原生后验不能当作退出动作原片。对外可说“最后关联退出后，独立读回确认旧物返还，而圣地成为无关联、空库存对象”，不得伪装成完整录到动作。

冻结scoped收据于2026-10-17T20:52:13.862891Z仍记正常闭场待定；本候选不据任务消息预填关闭完成。单项业务结果不授整产品/发布PASS。新增历史案例可由create/abandon知识查询发现，但保持`state_observed=false`、`current_world_state_observed=false`、`native_legality=null`、`action_ready=false`。


## 2026-10-17 UTC 后继闭场勘误：正常游戏退出，原生trace仍RED

machine_id仍为`4-8e1c2f1861`。上述20:52:13Z冻结收据及其pending原文保留；后继实际证据见[独立闭场记录](faith-and-power-episode01-r0011-closure.json)。游戏PID14764经原生GUI正常退出，独立retained OS0及正常关闭资格true；原public进程16340实际wait0、keeper实际0。**原native host18004实际wait1，原报告仍RED/error=null/cleanup=true**，原因是早先`r10-value-abandon-open-decision-a01`的MCP错误仍留在整段trace中，后续continue成功没有把它洗成PASS。

普通normal-close helper坚持host0条件，故拒绝STOP；没有放松该门、伪造host0或改RED为GREEN。Root以本场明确绑定的mixed-result proof，执行仅回收资源的协作keeper STOP，再取得原keeper退出与CAS11619，于2026-10-17T21:06:31.538158Z释放，state=done/resources=[]。正常游戏退出、资源释放、独立单项业务成功与整段trace资格分别记录；本场不能写“全部0”或“trace PASS”，整产品/发布仍false。
