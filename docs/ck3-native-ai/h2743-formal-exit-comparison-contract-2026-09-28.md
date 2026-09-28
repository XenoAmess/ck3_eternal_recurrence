# H2743 守方退出：条款与续战风险的纯函数比较合同

`formal_defender_exit_comparison.py` 提供 `compare_defender_dejure_surrender_cost_to_continuation_risk` 和 `formal_surrender_action_preconditions`。它们只处理传入的数据，不连接 CK3、不查询 native bridge、不提交投降。当前 [H2743 只读 baseline](h2743-dejure-exit-read-port-plan-2026-09-28.md) 的三类 material delta 仍为 `null`；[V2 静态计划](h2743-dejure-exit-v2-fail-closed-plan-2026-09-28.md) 的 F 和目标作用域仍未知，因此真实 H2743 输入必定返回 `unavailable`。

## 比较准入

四份输入共享**完全相同**的帧身份：checkpoint SHA-256、snapshot ID、公开和原生 revision、raw date、episode、connection generation、WarID、主攻／守方 ID、CB key/index 和目标 TitleID 列表。这里只支持主守方的 `individual_county_de_jure_cb` 投降，原生选项必须同帧合法且收件方现在接受，绝对结果为 `attacker_victory`。缺项、重复行、布尔冒充整数、错误帧／WarID／双方、按钮不可用或不接受均返回 `status=unavailable`，`comparison/recommended_outcome/action_literal=null`。

| 材料或风险域 | 准入条件 |
| --- | --- |
| 运行时目标和领地／封臣 | 条款中的目标作用域 TitleID 必须属于当前目标列表；完整 old→new 操作集必须至少覆盖每个目标 Title 的 holder 变化，操作不能重复或新旧相同。此为结构门，不代替 producer 对实际图的证明。 |
| F 与资源 | `cb_prestige_factor` 有 Q100000 原值及证据哈希；主攻／守双方各七类资源有唯一、有符号 Q100000 终战差额。不能以余额、历史 −30 威望或静态公式冒充本帧差额。 |
| 停战与条件效果 | 同帧定向停战为攻击方→防守方，含正天数、到期 raw date 与证据哈希；条件资源效果树覆盖非空节点集且未解决节点为空。纯函数不能认证该覆盖声明，正式 producer 必须独立核验准确脚本树。 |
| 续战风险 | 相同帧与有界正天数，双方七类资源分别给出 lower/upper signed delta；领地／封臣风险操作、战分区间、完整接触参战集合及证据哈希齐全。区间缺项或上下界倒置即拒绝。 |

满足准入后，函数只逐项判断**投降有符号资源差额**位于续战有符号差额区间的下方、区间内或上方。它保留两边的 title／封臣操作、停战、续战战分区间，不把县、金币、名望、伤亡强行换算成同一种效用，也不发明概率或阈值。返回 `status=componentwise_comparable_no_policy`、稳定的 `comparison_sha256`，但 `aggregate_preference/recommended_outcome/action_literal` 仍为 `null`。输出深拷贝输入数据；动作前置检查重新计算该摘要，拒绝事后篡改。完整合成测试验证此数学关系；合成证据哈希不是真实 producer 的签名或 H2743 结论。

## 正式退出动作前置合同

`formal_surrender_action_preconditions` 另外要求：有上述完整比较、有来源的策略选择绑定该比较 SHA 与当前帧、以及未消费的**同一 checkpoint** 单次授权。它只检查结构，即便这些合成字段齐全也返回 `submission_enabled=false`、`action_literal=null`，因为纯函数无法验证授权真实性或行动前原生按钮的新鲜性。正式接线还需：

1. 经审计的策略政策与风险阈值，并核实其来源和适用 WarID；不能让 `componentwise_comparable` 自动等于“应该投降”。
2. 从授权原件校验批准人、单次范围、checkpoint 与是否已消费；R0197 的一次性授权不能复用。
3. 提交前重新取得同帧 native options 和 material/risk 输入；任一 revision、战争身份或选项变化都要重新比较。正式策略 selected-step 门禁在此以前继续阻断本 WarID 的投降／白和平。
4. 另行实现明确的提交者与终战后置条件验证，保存动作前后 exact 原生证据；本模块没有提交路径。

当前交付是复用比较与授权**前置结构**，不是 H2743 可执行退出决策。真实终战 title／封臣、F、条件资源差额、停战和有界续战风险仍待原生同帧 producer 和独立策略验收。
