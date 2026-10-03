# R0001 三档普通 GUI 宣战费用

本轮实际普通宣战均发生于旧R0001 production（source9112候选，修复前），CK3 1.20.0.3，罗贝尔history1128／原生31254；六个原生快照均paused、日期53144328、同一玩家、资源scale100000。它证明三档普通入口与实际战争创建，不证明修复候选已拉齐防守方或结算通过。

| 借口 | 原生快照 | 普通对手／目标 | 窗口预览：威望／虔诚 | 实际总扣款：威望／虔诚 | 战争／目标ID |
| --- | --- | --- | --- | --- | --- |
| 公国 | 010→014 | Richard 32512／d_capua | 50／200 | 50／300 | war4／2221 |
| 王国 | 017→018 | Naples Sergios 32909／k_sicily | 250／1000 | 250／1000 | war5／2189 |
| 帝国 | 019→020 | Salerno Gisulf 34954／e_byzantium | 1250／5000 | 1250／5100 | war6／1295 |

公国虔诚raw `10015000000→9985000000`，差300；王国 `9985000000→9885000000`，差1000；帝国 `9885000000→9375000000`，差5100。威望raw分别 `10220000000→10215000000`、`10215000000→10190000000`、`10190000000→10065000000`，差50／250／1250。014与017余额相同，018与019余额相同，没有把中间另一时刻余额当成本次前态。原生response的文本JSON与structuredContent读出的余额一致。

维护脚本的CB基础费用仍为公国100威望／200虔诚、王国500／1000、帝国2500／5000。prestige字段乘原版 `common_cb_prestige_cost_multiplier`，piety字段加原版 `common_cb_impious_piety_cost`。本角色窗口威望为基础值的一半，只证明该角色与这些场景的实际费用，不能把0.5当作所有玩家固定倍率。帝国原始预览图 `djc-empire-preview-01.png` 已直接审阅，窗口显示5000虔诚／1250威望，目标拜占庭帝国；实际余额少5100，不把5000精确总扣款标PASS。公国200精确总扣款同样不是PASS；王国当前场景总扣款与预览相同。

原版另有声明后的虔诚机制。`game/common/scripted_effects/00_war_effects.txt:289–303` 的 `on_declared_war` 分支要求主防守者与进攻方faith相同，且进攻方rite具有 `tenet_peace_of_god_same_faith_war_piety_penalty`，随后执行 `add_piety=medium_piety_loss`。`game/common/script_values/00_basic_values.txt:1133` 定义 `medium_piety_value=100`，`:1147–1149` 定义该loss为0减该值，即-100。参数来自 `common/religion/tenet_types/00_pam_tenets.txt:72–77`。三个冻结CB的on_declaration都调用 `on_declared_war=yes`，因此保留原版宣战后果是明确源码合同；这项-100不是CB的cost字段。

这项条件效果数值与公国、帝国多出的100吻合，历史数据里Robert和Richard为roman_rite、Sergios为byzantine_rite，支持进一步核对同信仰条件。R0001日志没有记录该条件的实际求值或执行trace，原生快照也没有这两个predicate的直接读口；因此这里只将其记为有源码支持的解释候选，没有声称已逐分支证实原因。后续可在新场景宣战前只读核对当前faith等式和进攻方rite参数，并分别保存CB预览与操作总余额差，不以历史religion设定代替live状态。

2026-10-03勘误：初次摘要沿用公国预览200，未实际计算raw差，错误写为总扣200。机器审计R0001要求expected200时触发AssertionError，输入脚本、54项前置证据及失败回执保留在 `C:/workspace/two-mod-maintenance-20261003/de-jure-fee-evidence-R0001/`；没有把这个审计错误归为CK3产品RED。新审计R0002直接验证实际300，永久回执为 [三档费用证据索引](gui-fee-evidence-2026-10-03-R0002.json)，SHA-256 `4d264b85da40ca4ac5c15a20f9d15ed0ae38990e6f38c3af7a5af37a53c9d912`。54个完整原始文件（冻结16文件production、六个原生回执、三档截图及坐标回执、fresh日志、4份原版来源）保存于 `C:/workspace/two-mod-maintenance-20261003/de-jure-fee-evidence-R0002/`；旧证据和R0001执行树保持原样。

本轮不新增runtime改动，不启动或控制游戏。进程退出、profile恢复及R0002修复候选验收由root独立保存回执；本记录没有把stop请求写成cleanup已完成，也没有发布事实。
