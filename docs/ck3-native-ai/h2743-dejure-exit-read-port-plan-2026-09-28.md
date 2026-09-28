# Robert H2743 法理县战争：最小只读终战条款读口

本页是 **producer 实施合同**，不是已取得的 H2743 投降条款。输入固定为 WarID `16777231`、原生暂停帧 `native:3`、原始日期 `53217264`、主守方 Robert `29829`、`individual_county_de_jure_cb`（原生索引 `17`）、目标 TitleID `2128`。[同帧实证](h2743-native-exit-readonly-2026-09-28.md)仅证明投降合法且对手接受，不能证明 title／封臣、资源或停战的终态。

## 已有读口与不能复用的路径

| 域 | 当前可靠输入 | 本次缺口 |
| --- | --- | --- |
| 战争身份、选项 | 原生暂停帧的 WarID、双方身份、CB index/key、目标 TitleID、投降 validator 与接受结果 | 投降后的逐项条款 |
| Title、人物、资源 | 精确 H2743 save 的 holder／liege／封臣及双方金币、虔诚、威望前态；原生快照的 Robert 金币、威望前态 | 同帧完整实体图、实际旧→新操作和双方有符号资源差额 |
| 延续风险 | H2743→H2825 的已发生 15 日路线：守方战分 −12→−24、第一日曾至 −25 | 下次接触／围城的同帧参战集合、损失分布与退出比较 |

生产 `ReadWarTerminationTerms` 只处理 `claim_cb`／`raiktor_claim_cb`，本 CB 返回 `unsupported_casus_belli`。通用 `ReadWarTerminationExitTerms` 在旧版 live crash 后明确禁用；不得重新打开 loaded-effect preview（`ck3_11906.cpp:18689–18695`）。`ReadPrimaryExitResources` 已有双主将七种余额和月收入 helper（`ck3_11906.cpp:5026–5144`），但目前被禁用的上层查询挡住，而且余额只表示**前态**。为 H2743 单独暴露余额可作为第一阶段，只能输出 `baseline_observed`，不能生成 delta。

## 独立 producer 的最小输出

建议新增精确版本的 `ReadDefenderDeJureExitTermsV1`，与通用 exit-terms 读口分离；仅准入 exact EXE/DLL 指纹、主守方、这个 CB 和一场有效 WarID。输出必须绑定 before/after 原生 snapshot ID、raw date、WarID、双方 ID、CB key/index、目标 TitleID 列表、查询版本与每项来源。单域不可读时给有类型的 `unavailable_reason`，**不能用空数组或数值 0 表示已确认无变化**。总 `material_complete` 仅在所有下列域完成且同帧身份未变时为真：

1. **Title／封臣**：先只读取得当前 target_titles 的运行时完整列表、每个 title 的 holder/de-jure/de-facto 领主、下属 title，以及相关人物的个人 liege／直属封臣边；再由一个已静态审计的纯计算器给出逐项 `old→new` title holder、title liege、人物 liege／vassal 和 claim 操作。`00_dejure_war.txt:455–472` 只声明 `type=conquest`、`add_claim_on_loss=yes`、循环内保存临时 `target`、循环外**一次** `setup_de_jure_cb` 和 `resolve`；WarID 的 `[2128]` 列表不等于该语句的 `scope:target` 引用已读回。只有在目标作用域、完整分支条件、变更对象写集合以及 `resolve` 的对应提交语义都已证明时，才能把纯计算器的输出标为条款；否则返回 `runtime_target_scope_and_de_jure_change_semantics_unproven`。不能在原游戏态上执行 effect 或依赖其 preview 获取 change 对象。
2. **双方资源**：借用身份复核后的直接余额 helper 读取 gold、prestige、prestige experience、piety、piety experience、legitimacy、stress 和月收入。单独读取 `cb_prestige_factor` 的实际原始值及 scale，并为 on_victory 中每一条会触及主将资源的条件效果证明触发条件或标记未知。原版 `00_dejure_war.txt:475–484` 配合 `00_casus_belli_effects.txt:35–160`，只给出 Robert **直接当前威望效果** `max(-10 × F, -1000)`、Landolf **直接威望经验效果** `min(10 × F, 1000)`（`F=cb_prestige_factor`）；由于本帧 F 未读且可能有其他效果，它们不是本次总 delta。原版 `00_casus_belli_effects.txt` SHA-256 为 `9F7C77CC9342B1197B1C802A2D465E56F7521458B103DEC84F5EB7222E45F18C`。`pay_short_term_gold_reparations_effect(GOLD_VALUE=3)` 在攻击方战败的 `on_defeat`，不在此次守方投降的 `on_victory`；不得由此推出本次 gold delta 为 0。legitimacy、LAAMP 合同报酬和曼荼罗宗教效果等条件支路还须逐项核对，不能默认零。发布总 delta 必须含币种、人物、raw/scale、符号和逐效果来源；任何条件效果未闭合时保持 unknown。
3. **定向停战与其他即时结果**：`add_truce_attacker_victory_effect` 的脚本在 `00_war_effects.txt:1895–1903` 指向 attacker→defender、`result=victory`，但具体实际 days／expiry 与同帧条件仍需只读参数求值和身份复核；既有 `ReadRaiktorActualTruceExpiryV1` 是**行动后实际休战**读口，不能把它的结果或 R0197 旧结果作为 H2743 的行动前保证。战俘释放、合同报酬、曼荼罗等条件效果同理逐域证明或返回 unknown。

读口输出应把 `baseline`、`script_route`、`projected_delta` 和 `observed_postcondition` 作为不同字段／证据层级。当前只有前两层的一部分；除非纯计算器的输入和完整语义均验收，否则 `projected_delta` 也不得标为 complete。

## 建造与暂停实机验证顺序

1. 在不启动游戏的静态阶段，固定精确 EXE、`00_dejure_war.txt`、`00_casus_belli_effects.txt`、`00_war_effects.txt` 哈希；补全 `setup_de_jure_cb`／`resolve` 的传递写集合与目标作用域解析。先写纯计算器与 provenance 断言，完整性无法证明时拒绝输出。早期 [R0197 单次真实投降](war31-r0197-one-shot-live-result-2026-09-28.md)只可作**独立回归样本**，不能当 H2743 常量或唯一正确性证明。
2. 先对直接余额、target_titles 和当前实体图做 fixture／负例测试：错误 WarID、换帧、目标增减、人物消失、CB 不匹配、未解析的条件效果一律 fail closed。新读口不得调用禁用的 loaded-effect preview，也不得提交任何游戏命令。
3. 等 R0271 与 R0266 的实机优先级释放、取得当次 Steam 离线新鲜画面和屏幕独占后，使用已校验四件 H2743 原件创建**新的**外置 attempt。对同一暂停帧重复查询两次，比对 before/after snapshot、资源、目标和同一 save SHA；保存原始 payload、stderr、版本与全字段哈希。任何身份漂移或查询崩溃为 RED，原 attempt 原样保留。不能只凭保存层前态或合成测试宣称 live GREEN。
4. 只有条款与 R0271 同帧围城／接触分区、有界续战风险同时可读，正式退出策略才能比较投降、当前不可用的白和平与继续作战。行动提交与终战后置条件属于另一个授权和验收阶段；H2743 当前没有可复用的投降授权。

截至本页，最小缺口是 **完整 de-jure 变更语义和同帧运行时输入**，其次是 `F`、条件资源效果、定向休战的精确期限与 R0271 风险读数。没有这些读数，就不能把脚本类别或旧结果包装成当前可执行的终战决策。

## 2026-09-28 安全子集实现状态

草稿 PR #448 追加了 `ReadDefenderDeJureExitTermsV1` 原生读口和显式 `query-defender-de-jure-exit-terms-v1-<WarID>` 查询。当前代码只采集 CB/主守方/目标 TitleID 身份，以及双方七种**当前余额**和月金币收入；前后重复读取资源与战争列表，并在 bridge 命令层核对已发布暂停帧。其 JSON 明确给 `title_vassal_delta=null`、`signed_resource_delta=null`、`directed_truce=null`、`material_complete=false` 和各自的 typed unavailable 原因。Python 投影严格要求 14 项余额、两份收入、同一 native revision 与目标列表，拒绝非空 delta 或冒充 material complete，且不产出 exit action literal。该查询有独立 capability，但不进入正式规划器候选 action_steps。

这份子集仍为**静态／合成测试候选**，尚无 H2743 暂停实机回读；它也没有闭合 title／封臣、终战资源或停战。不能把 `available_baseline` 解读为 `material_complete`，不能据此解除终战门禁。Windows Release 原生构建通过，候选 DLL SHA-256 为 `FD8B5C7873C22BE32ACF2E421D2A9F625AE8FF3FB4D5408DB7F6E6AF15321470`；聚焦 Python 测试常规及 `-O` 各 4/4 通过。构建后的静态审查又把双方人物扩展和合法性对象非空、原生主将 ID 前后不变加入 fail-closed 门禁，避免共用 helper 在对象缺失时填零。外置 `attempt-08-dejure-baseline-no-launch` 和 `attempt-09-dejure-baseline-no-launch` 均已核验精确四件源资产，但 `prepare-profile` 检测到 R0271 正在使用的 `ck3.exe`，按环境门拒绝；两次环境 RED 均原样保留，未启动 H2743 游戏。R0271／R0266 屏幕释放后需另建 attempt 完成无启动预检，随后取得当次 Steam 离线新鲜画面与屏幕独占，才可做暂停帧只读查询。
