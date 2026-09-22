# G2-M5 R0082：五候选联合选择的最小观测缺口

状态：`read-only gap audit`，不是新策略、实机动作或 M5 完成证据。冻结 CK3
`1.19.0.6`，EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；
审阅的仓库基线为 `master@b7b42980a893e02617a8330a892b82a895954c12`。
本页仅更新 [R736 联合输入账本](m5-r736-joint-selector-inputs-2026-09-16.md)
在 R0082 新 query 与后续私有婚姻动作进入源码后的决策边界。

## 已观察到什么，不能推出什么

[R0082 原生只读结果](<Z:/ck3_mod_rewrite_process_assets/g2-m5-observed-heir-legality-65c84ed-20260922/live-R0082/observed-first-heir-legality.json>)
SHA-256 `D7C3FE9BC820983BE6E747A2415DCDDC69F4FD5A10E88D65DC4543759A8B698A`：
同一 paused native revision `3`、玩家 `29829`、首继承人 `38822`，
`657/657` 个不同候选同时通过 complete Can Send 与原生最终答复；
每行仅含五角色身份、`recipient_ai_accept_raw`、最终答复和合法性，
`native_rank` 全为 `null`。这已满足“确有至少五个不同合法家庭候选”的**发现**前提，
不满足收益评分、正式动作、物质结果或下一轮消费。
原版 [婚姻树](marriage-and-alliance.md) 的接收者 `ai_accept` 是对方答复，
不是玩家的联盟价值、继承人收益或长期承诺价格；人类玩家的 AI Strategy
在 R720 真实场景中不可用，不能把枚举顺序伪装成原生排名。

原版 [宣战树](war-declaration.md) 和 [战前输入树](prewar-encounter-inputs.md)
分别证明 native 战略相对军力及一部分强制参战者、当前军队/路线来源。
这些不等于自愿盟友会到场、未来补给、战役损耗、退出价格或胜率。
[当前主力补给](m5-primary-current-army-supply-source-2026-09-16.md) 与
[单战争 readback](m5-war-primary-current-readback-2026-09-16.md) 仍为源码级、未接
application-main paused 私有查询；不能拿其静态字段冒充 R0082 同帧观测。
现有 `joint_candidate_ledger.py` 因此正确地只计合法机会，始终返回
`joint_selection_ready=false`、`selected_step=null`；且其婚姻输入是另一个
*ranked* schema，不能直接吞入 R0082 的 unranked 家庭行。

`observed_heir_marriage_private_action_v1.py` 提供默认关闭的 typed 提交和
后续双向婚姻/订婚读回合同，但尚无同版本实机提交、联盟结果、pending cold
reconciliation 或正式策略消费者。它不能替代选择前观测，也不应在普通
production / MCP 注册或广告。

## 按依赖排序的最小只读补口

| 次序 | 同一 paused 帧所需字段或结果 | 现有来源与精确缺口 | 完成该项才解除的等待 |
| --- | --- | --- | --- |
| 0：复用，无新 ABI | 玩家/首继承人完整 ID、native revision/date、当前 gold raw/scale 与月收入、active WarID/双方、玩家现有 army ID/位置；当前 declarable rows 和至少五个不同的当前 final-legal 家庭行 | `campaign-root`、`state_snapshot`、公共宣战查询和 R0082 私有合法性 query 已有；R0082 文件本身未保留 treasury/active wars/armies，不能跨帧拼接 | 让后续 readback 与真实资源和多战争占用绑定，而不是把缺失视为零 |
| 1：继承人婚配逐行价值 | 每一拟比较候选的实际 secondary pair、成人婚姻/订婚结果类型、lineality/已选择 option、当前双方关系、具体将形成或维持的联盟双方完整 ID、当前联盟/承诺及其期限或取消代价；必要 faith 只消费原生最终判定 | 私有合法性行只有角色、接受度、答复；现有私有动作的双向 spouse/betrothed 仅是**事后**合同；`MarriageInfo.GetAllianceItems`/任意双人 alliance getter 的 exact-build 来源已登记但候选级预测和 paused 发布未闭合 | 在五个真实合法家庭候选之间比较收益与长期义务，并使预期/实际联盟可验证 |
| 2：单个当前合法宣战的有限风险 | 同 declaration ID 的有效 primary defender、强制/自愿参战者及哪方、可调用/可拒绝的盟友和宗主最终判定、当前 CUnit↔CArmy owner/位置/路线/`CArmy+0x180` 补给、目标进军路线与时长、declared cost、预计 gold/兵力消耗和 white-peace/surrender/败战法律结果 | native power query只给战略 ratio；forced defender、当前主力 supply/route 有静态 ABI/源码，尚需主线程同帧 paused readback；自愿盟友、未来路线补给、战役消耗与退出价格仍是独立 unknown | 把战争与“现在结婚/保留现金/处理现有战争”放在同一预算和多战争约束下；没有这些字段时不提交泛化宣战 |
| 3：非 bridge 的显式策略量表 | 对联盟、继承人角色、时间、现金储备、未来义务及战后稳定性的版本化目标权重与阈值，绑定当前高层目标和已有 WarID | 不能从 native legality、rank 或相对 power 自动推出；需在上述真实字段到达后由策略定义并以相同单位校准 | 五个以上不同合法候选的确定性机会成本比较及一个 typed 动作 |

次序 0 可在下一次已授权同版本 paused 读中直接收集，不应新建 bridge。
次序 1/2 只扩充决策所需的只读 native/MCP 口，先 exact-build 来源和
版本绑定 fixture，再在真实 paused snapshot 核实；不要为本项扩展通用宗教或
holy order。所有候选必须绑定同一 actor/heir、generation-bound IDs、声明
identity 和 native revision。字段缺失返回 typed unavailable，不将 `null`
当作零或 `false`。这只是正确消费实时游戏状态的已有合同，不是新增通用安全门。

在 1/2/3 未闭合前，`>=5` 只表示真实合法候选数量，不表示
`joint_selection_ready`。最短可验收路径是五条不同当前 final-legal 行的同帧
价值/成本读回 → 正式策略比较婚姻/外交/战争/等待的机会成本 → 恰好一个
typed 动作 → 独立物质后置 → 下一 turn 消费，必要时从配对 checkpoint
cold restore；不能用私有直调或 ACK 代替正式闭环。G2-M5 权威状态仍为
`not_started`。
