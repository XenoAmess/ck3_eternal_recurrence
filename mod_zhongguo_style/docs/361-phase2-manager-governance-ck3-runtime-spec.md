# 361 二期：管理者与制度运营 CK3 运行时规格（F032–036、AK345–354）

## Readiness boundary

- Readiness: `static-ready`
- MCP evidence: 首次启动只取得 loader/material RED 与 cleanup GREEN；没有业务 snapshot
- CK3 live evidence: `RED only`，未进入 paused gameplay
- 目标编号：`032–036` 与 `345–354`，共 15 项。
- 明确不含：`312–333`；该段属于职业/学习子包，不得由本运行时抢占。
- 本规格证明的是确定生成、产品脚本、状态/收据/期限/资源合同与 L0 静态测试。它不是 fixture-live、production-live 或发版签核。

## 一、独立产物与集成边界

唯一生成器是 `tools/gen_361_manager_governance_runtime.py`，生成：

- 七个按用途拆分的 effect 文件：
  - `common/scripted_effects/zg361_manager_governance_core_adapters_effects.txt`
  - `common/scripted_effects/zg361_manager_governance_dispatch_effects.txt`
  - `common/scripted_effects/zg361_manager_review_effects.txt`
  - `common/scripted_effects/zg361_policy_intake_effects.txt`
  - `common/scripted_effects/zg361_policy_audit_effects.txt`
  - `common/scripted_effects/zg361_policy_history_effects.txt`
  - `common/scripted_effects/zg361_policy_fairness_effects.txt`
- `common/scripted_triggers/zg361_manager_governance_runtime_triggers.txt`
- `common/script_values/zg361_manager_governance_runtime_values.txt`
- `events/zg361_manager_governance_runtime_events.txt`
- 简中、英文及七份英文结构占位本地化，共九份 yml。

### Effect 文件边界证据（2026-09-04，静态）

历史生成单体为 `386,750 B / 43 effects`，SHA-256
`53120757ab63b1694a3c2b93ef4ac7a409a71300767ce93382720a246d0dab18`。它仅保留为生成器内存中的
语义基线，不再是产品文件。当前七片依次为：

| 用途片 | bytes | effects |
|---|---:|---:|
| core adapters / shared hook / #360 | 85,371 | 10 |
| dispatch / ticket / team snapshot | 16,244 | 7 |
| F032–036 manager review | 98,971 | 6 |
| AK345–348 intake / override / exception | 67,760 | 8 |
| AK349–350 audit / benchmark | 34,390 | 4 |
| AK351–352 pilot / history | 32,427 | 3 |
| AK353–354 capacity / fairness / due resolver | 45,651 | 5 |

总计 `380,814 B / 43 effects`，最大单片 `10`，`>10=0 / >20=0`，没有例外。L0 会把七片逐 effect
映射回历史 aggregate 并验证每个 block 字节完全一致，同时拒绝缺失、重复、额外定义及旧单体残留。这里没有启动 CK3，
所以这项证据只达到 `static-ready`；下一次 B3 product projection 实机应记录 loader 时长与首错。若出现加载性能 RED，按
`docs/testing-workflow.md` 的同条件文件边界 A/B 规程继续细拆，不能把静态分片本身写成加载 GREEN 或根因证明。

### 首次 B3 live：material/call-graph closure RED

这份失败证据不提升能力状态，B3 readiness 仍为 `static-ready-live-pending`。
`ce458af` 的首次真实启动在 `310.617 s` 后 RED，outer/cell/final-error SHA-256 分别为
`B319F853623FF9443F3941F4078559D6E24CDBF0EF5D75BDCEBE269A5D961923`、
`8CCD24257185BB39529BCEC0FAE9F03ACAABCF281455CE55BC49D6C159E4AC56`、
`C52DC7DAA975A6EA8EB60CCEF5429E35B0299CCD4A090EEFBEE995EE491956CF`；native cleanup GREEN。CK3 真实打印的首错是
stage-10 调用未物化的 `zg361_p2c_record_stage_effect` / `zg361_p2c_record_red_effect`。递归静态 closure 又证明同一
provider 文件还供应 `zg361_p2c_mark_lane_busy_effect` / `zg361_p2c_schedule_pump_effect`；后两项不是冒充的 live log。

故这轮是候选投影漏选 central dispatch provider 的 material/call-graph closure RED，不是单文件大小的因果证据，不触发
size A/B。`ce458af` 全产品边界审计为 427 files / 3,718 effects / max non-legacy 10 / target misses 0 / `>20` violations 0。
只有闭合更早 parser/material/call-graph 错误后仍出现纯 loader-performance RED，才按同条件规程继续拆分 A/B。完整证据见
[`docs/phase2-promo/b3-manager-first-live-startup-red-2026-09-04.md`](../../docs/phase2-promo/b3-manager-first-live-startup-red-2026-09-04.md)。

确定性语义 oracle 是 `tools/zg361_manager_governance_model.py`，其测试是
`tools/test_zg361_manager_governance_model.py`；CK3 生成层测试是
`tools/test_zg361_manager_governance_runtime.py`。oracle 的 readiness 固定为
`python-l0-only`，不以 Python 通过冒充 CK3/MCP 实机。

本包不写 B1、B2、考核榜、共享 case kernel、中央 effects/events/interactions，也不新增顶层 GUI 按钮。中央 stage 10 已调用：

```text
zg361_mg_dispatch_subordinate_managers_effect
```

三处共享 hook 已由共享文件 owner 合并，并由运行时测试锁定：

1. `common/script_values/zg361_values.txt`：在 `zg361_kpi_organization_evidence_value` 内、现有 `zg361_manager_mechanism_kpi_value` 分支之后添加 `add = zg361_mg_due_organization_kpi_value`。它属于官方第 8 分项，不得向 `zg361_kpi_value` 添加第 9 个 addend。
2. `common/scripted_effects/zg361_effects.txt`：紧跟唯一的 `zg361_b2_consume_management_debt_effect = yes` 添加 `zg361_mg_settle_due_organization_kpi_effect = yes`。此时八分项与总分已冻结，settler 只结清本次已读 token。
3. 同一 shared effects：把 `zg361_rank_cohort_effect` 内唯一的 `set_variable = { name = zg361_bottom_slots value = zg361_bottom_slots_value }` 替换为 `zg361_mg_set_bottom_slots_effect = yes`。adapter 先保留 core 值，仅在本轮确实消费到 F035 token 时改用 10/5/0 冻结值。

`tools/test_zg361_manager_governance_runtime.py` 会锁住三个唯一 anchor、包内 adapter、官方 KPI 仍恰好八项以及新值不在总分顶层。完成 MCP-first 实机以前不得把本包写成 live；不用 OCR 或测试决议伪造通过。

## 二、角色权限

1. 管理行为必须通过 `zg361_is_celestial_liege_trigger`：天朝制、在任、有地、公爵及以上。
2. 合格玩家走可见报告；合格 AI 天朝制公爵及以上属于项目所有者授权的第二 AI 例外，只走后台，不弹可见事件。
3. 伯爵和男爵继续通过 `zg361_is_reviewable_vassal_trigger` 被直属上司考核，但不能打开 F/AK 管理案件。
4. 管理者不是考核豁免对象。F/AK 案件固定为 `owner = 直属上司`、`subject = 经理本人`，并要求 `subject.liege = owner`。
5. 上级只读取经理团队的七项冻结汇总；孙级角色 ID 数固定为 0，不能把下下级个人偷偷塞进上级考核榜。

## 三、共享案件状态

### F：manager review

```text
snapshot_ready(1)
  --032 score frozen team--> manager_scored(2)
  --033 explain profile--> reason_coded(3)
  --034 freeze nine-box--> nine_boxed(4)
  --036 append annual/decade log--> reported(5, closed)
```

`035` 在 state 1 内先冻结真实 `ratio_override > game rule` 的 strict/relaxed/off 分布及三档守恒收据，不自行推进状态；`032` 必须先消费这张收据。

### AK：policy version

```text
drafted(1)             : 345 + 346
piloted(2)             : 347 + 348
effective(3)           : 349 + 350
exception_audited(4)   : 351 + 352
measured(5)            : 353 + 354
migrated(6, closed)
```

每一阶段的两个编号都形成独立 typed receipt；两张收据及该阶段守恒条件同时满足，stage dispatcher 才能调用共享 case kernel 推进。

### 复合对象身份与版本

A/B 不是只写一个 choice 常量。每项都冻结一份业务对象：

```text
object_id + owner + subject + cycle + case + state + revision + route + kind
```

其中 `object_id` 是 subject 本地的稳定短号；跨人物、跨周期的权威身份必须使用完整复合字段，不能只拿短号比较。Python oracle 的稳定 ID 由
`mechanism + owner + subject + cycle + case` 计算，`revision` 只产生内容版本，不换对象 ID；内容另有 `content_hash`。Python oracle 对同一完整 case identity 保存冻结输入 fingerprint：完全相同的重放是 exact no-op，偷换 route 或输入是 stale RED。CK3 runtime 先把本次请求 route 归一化：没有 `zg361_mechanism_NNN_choice` 或值越界都明确等于 A，而不是“缺变量就跳过比较”；因此 B/C 首次成功后删掉 choice 再重放，同样是 route 冲突并写 stale RED 2。

每个编号还把实际参与结果的数值事实（含“变量存在”位）折叠成 `requested_input_fingerprint`，A/B 冻结到 `object_input_fingerprint`，C 冻结到 `debt_input_fingerprint`。同 owner/subject/cycle/case 与同 route 下，指纹不等也写 stale RED 2，不能用已经存在的 receipt 掩盖偷换输入。字符引用等不能直接进入 CK3 数值运算的 opaque payload 写 presence 位；其实际 producer 拥有的 `team_snapshot_revision`、`offcycle_input_revision`、`override_input_revision` 与 `fairness_input_revision` 同时进入指纹。不存在 producer 的通用 `zg361_mechanism_NNN_input_revision` 已删除，不能靠外部手工加一伪造版本链。资源余额不进入指纹，因为 349/353 会亲自改变余额，权威防重由 reserve/settle receipt 承担。相同 route、相同指纹、相同 receipt 的重放才是 exact no-op，不再写业务或 RED。旧 delayed ticket 由五元 guard 直接 stale no-op，owner 也不能在相同 token 上漂移。

C 明确不生成伪业务对象，而是生成一项可消费制度债：

```text
mechanism + source owner + subject + source cycle + source case + source state + source revision
due_cycle = source cycle + 1
status = pending(1) -> settled(2)
```

`zg361_mg_consume_due_policy_debts_effect` 只在下一轮及以后、由当时的直属上司入口消费一次；到期判断与 `settled_cycle` 都使用 `root.var:zg361_review_serial`，不能误用受评经理自己的旧 serial。原 source owner 永不改写，另记 `settled_by_owner`。每项债向下一轮 032 团队快照写 `manager_score_delta = -3` 及真实 due cycle；快照只在 due 到达后消费，并同时删除 delta 与 due，避免提前或重复扣分。精确重复 settlement 是 no-op，改写已结清债为 stale RED。

旧的全局 `mg_policy_debt`、`mg_policy_debt_settled` 与 `mg_exception_renewal_count` 只有累加写入、没有任何决策 reader，现已退役，
不得用初始化零值掩盖。制度债的权威仍是每个机制独立的 source identity、due/status/settled receipt；例外续期的权威仍是 #348
expiry token、evidence 与 outcome。经理分只消费这些可追溯业务对象。

F032/F033/F034/F036 的 C receipt 与 A/B 一样调用共享 stage transition 并安排下一张 ticket；C 只是“不造该编号业务对象”，不是“把整份经理案卷卡死”。混合路线也必须继续走：035C 后的 032A/B 不读取旧 `distribution_conserved`；032C 后的 033/034/036 用显式 `available=0, basis=0`，不会拿上一周期经理分冒充本周期；033C/034C 在最终报告中同样显示 unavailable，而不是漏字段或回显旧案。

AK 的 stage barrier 同样 route-aware：347C 以“未做覆盖天然保持 quota neutral”通过守恒门，349C 以“未启动审计、没有未结 capacity”通过结算门；其余 C receipt 与配对编号共同推进正常阶段。跨阶段 consumer 也按 receipt choice 选源：345C/346C 让 350/353 使用显式默认 basis；350C 让 352 建立 `new_series=1`、`source_available=0` 的新序列对象；352C 让 354 使用 mapping basis 0。历史 A/B 变量可以继续留作档案，但 C 路径绝不读取它们。

## 四、逐编号 CK3 合同

| ID | typed operation | 实际写入 | 后续 consumer / 不变量 |
|---:|---|---|---|
| 032 | `manager.score_frozen_team` | 七项团队冻结分项、管理者总分、拒办京察收据、下一轮 component-8 token | `source_team_serial < superior review_serial`；下一轮官方 organization 分项读取后单次结清；拒办只匹配保存的上司/年份 |
| 033 | `manager.explain_profile_decision` | 五个 `[-25,25]` 理由码、画像版本、一次关系覆盖、申诉风险 | 理由总分进入年度制度日志；不得反写 KPI/档位 |
| 034 | `manager.freeze_nine_box` | 两轮冻结分、绩效轴、潜力轴、九宫格编码 | 少于两轮时明确写 `ready=0/code=0` 与非致命 typed RED 6，但仍记收据并推进，避免首轮永久卡案；只读，不扣钱、不改 KPI/档位/HC |
| 035 | `manager.freeze_distribution_mode` | `ratio_override > game rule` 的 strict/relaxed/off、top/middle/bottom、next-cycle token | `top + middle + bottom = cohort`；仅 strict 在 `n>=5` 时保底一名；下一轮 rank 单次结清 |
| 036 | `manager.compile_decade_report` | 按 owner 分段的连续年度累积、十年 ready、奖金净流、上一轮经理分 | owner 变化、年份断档或上一段已满十年时重开；同年重复由 receipt 拒绝 |
| 345 | `policy.freeze_next_cycle_calendar` | 年度/半年/季度次数、行政工时、effective cycle | 只从 `current case cycle + 1` 生效；同周期玩家/AI 合批标记为 1 |
| 346 | `policy.consume_material_offcycle_signal` | 从真实翻案/PIP/校准快照产生的重大信号、动作、revision、一次消费收据 | 没有真实 signal 不造 input；`cohort_reruns = 0`；pending→settled/discarded |
| 347 | `policy.consume_override_point` | 实际 `grade_reason` 推/抬配对的 beneficiary、bearer、两个 result case、reason、revision | before/after cohort 数相等；没有真实配对不伪造覆盖；pending→settled/discarded |
| 348 | `policy.expire_or_renew_exception` | owner/subject/cycle/case/state/expiry token | 365 日到期；无新事实恢复默认，有新证据才续期；旧 token stale no-op |
| 349 | `policy.run_reproducible_audit` | 样本率、风险数、seed、抽样 fingerprint、clean/findings、到期修复完成收据 | 透明度只降比例不免审；行政 capacity reserve→settle；只有真实 A 路线审计可完成上轮修复 |
| 350 | `policy.version_benchmark` | old/new version、未来生效周期、阈值、解释码、旧历史快照 | 旧值/公式/版本不重算；新版本复用 345 的未来 effective cycle |
| 351 | `policy.measure_regional_pilot` | 互斥 pilot/control、预登记指标、冻结结果及差异 | 两区域与全部结果齐备前 `result_ready=0` 且不计算差值；仍以“不可用”收据推进，避免小领地永久卡案 |
| 352 | `policy.map_immutable_history` | original value/formula/version、mapping version、映射值或新序列 | original 三字段永不删除/覆盖；354 继续读取 mapping version |
| 353 | `policy.charge_admin_capacity` | 表单、会议、申诉、校准、打断工时及总额 | capacity reserve→settle，可守卫退款；错误/翻案反弹写入下一轮 032 经理分 |
| 354 | `policy.recompute_fairness_metrics` | 快照真实送达/申诉/翻案/离职/健康离职计数、raw/reported 三率、gap、gaming、修复 token | 原始 0 保持为 0，仅分母保底；B 产生 next-cycle 修复，349A 完成后下一次 354A 单次 `trust +5` |

### A/B/C 路由差异

| ID | A：证据/治理路线 | B：政治/捷径路线 | C：延期路线 |
|---:|---|---|---|
| 032 | 七项具名冻结汇总全部进入经理分 | 只用冻结汇总，对负向交付/京察/申诉/留任作惩罚性聚合 | 不造经理评分对象；下一轮制度债 |
| 033 | 画像权重决定五项理由码，不做人情改档 | 允许一次 `[-1,+1]` 人情覆盖，保留 before/after 与申诉风险 10 | 不造画像说明对象；下一轮制度债 |
| 034 | 两轮以上才分类；首轮 `ready=0/code=0` 但正常结案 | 用当前轮快标，下一轮失效并记录短视风险 | 不造九宫格对象；下一轮制度债 |
| 035 | 冻结经理自己的 `zg361_ratio_override`（10/5/0），缺失时读取 strict/relaxed/off game rule；无合法 producer 就 typed unavailable | 强制 strict 10% | 不造分布快照；下一轮制度债 |
| 036 | 追加按 owner 分段的年度账，十个连续年度形成十年报 | 只做当年亮点卡，`history_rows=0` 且标 causal warning | 不造年度/十年报对象；下一轮制度债 |
| 345 | 年度一次正式评审 + 一次轻 check-in；20 行政工时、30 天反馈 | 季度四次；72 工时、7 天反馈，并记短期偏差 25 / 疲劳 30 | 不造日历对象；下一轮制度债 |
| 346 | 真实翻案/PIP/校准信号一次消费，不重排原 cohort | 保留原榜，同时记录独立 rerank 风险；仍只消费同一真实 signal | 丢弃 pending signal，不造业务对象；下一轮制度债 |
| 347 | 消费实际 `grade_reason` 2/4 与 1/3 配出的覆盖点 | 放宽预算，但仍只能消费真实配对并留双 result case | 丢弃 pending pair，不造覆盖账；下一轮制度债 |
| 348 | 365 日到期；有新证据从处理日再续 365 日，否则恢复默认 | grandfather，无截止日，记录特权累积/公平风险 | 不造例外票据；下一轮制度债 |
| 349 | 20% 风险优先 + 可复现随机抽样；clean 结果增加制度信任 | 5% 低抽样、无 clean 信任，保留严重漏检风险 | 不造审计对象；下一轮制度债 |
| 350 | 战略难度解释新阈值，旧历史不重算 | 按 top growth 自动棘轮，保留 ratchet risk | 不造版本对象；下一轮制度债 |
| 351 | 预登记 pilot/control，互斥且结果齐全后才算差值 | 全境直接铺开，无因果对照并记录迁移风险 | 不造试点对象；下一轮制度债 |
| 352 | 新建 comparable mapping layer，三项 original 字段只读 | 用最新公式重算派生层，显式标 contamination risk | 不造映射对象；下一轮制度债 |
| 353 | 五类真实工时全部扣 capacity；显示真实总额和精简项 | 仍扣全部真实 capacity，但报表藏成 0，并把隐藏损耗计入下轮经理分 | 不造行政成本对象；下一轮制度债 |
| 354 | raw 三率按真实 count 重算；仅消费 349A 已完成的上轮修复 receipt 并单次 `trust +5` | 制造漂亮 reported 三率，留下 gaming，并产生下一轮修复 token | 丢弃本轮 fairness input，不造公平审计对象；下一轮制度债 |

035 的三模式计算另有纯函数 `compute_distribution_snapshot`。快照包含真实规则来源、review serial、分母、三档数量与 hash；后续切换政策只会产生新 revision，不会回写旧周期。strict 为 10% 末位并在 cohort≥5 时保底一名，relaxed 为 5% 且不伪造保底，off 为 0；不存在 mixed、绝对线或外部任意 distribution knob。

### 真实 producer 账本

- 团队快照只读取本轮直属下属的真实 result identity：`result_case_owner/cycle_serial/case_serial`。送达来自 `result_delivery_method > 0`；申诉来自 `result_appeal_outcome = 1/2`，其中只有 1 是翻案；校准推/抬来自 `result_grade_reason = 1..4`。
- PIP 成功只认 `b2_pip_state = 3` 且 `b2_pip_graduation_receipt = b2_pip_case`，并复核 PIP owner/cycle；离职只认 `b2_m075_state = 3`、`actual_exit = 1` 及 owner/cycle/case，健康离职另要求 `neutral_record = 1`。
- 不存在的 `zg361_result_regrade_delta` 与 `zg361_b2_m016_outcome` 已从 generator、generated runtime 与 tests 清除；不能用名字看似合理的死变量冒充业务事实。
- snapshot 自身绑定 F owner/subject/cycle/case 并递增 producer-owned revision；同一 F token replay 直接复用，不二次读取/消费。346、347、354 各自把 revision 与 source identity 冻结为 pending(1)，唯一 consumer 改为 settled(2)，C 改为 discarded(3)。
- F032 A/B 产生 `organization_input_status=1`、source identity/revision、`component=8` 与严格验证的 `due_cycle=source+1`。active B1 在 KPI 前已经推进 `b1_cycle_serial`，所以 value 与 settler 都用 `b1_cycle_serial >= due_cycle`；legacy/no-B1 在 compute 后才推进 `review_serial`，所以用 `review_serial >= source_cycle`。二者由 generator 的同一段 guard 逐字注入 value/settler，防止一个读到而另一个不结清。下轮 official organization value 读取后 setter 改为 2；旧 token 因 status 不再贡献。
- F035 使用同一 active-B1/legacy 双周期规则。rank adapter 每次先把 `applied_this_rank=0`，只有本次真正消费 due token 才置 1 并覆盖 bottom slots，随后删除瞬时 flag；历史 effective mode 因而不能在晚一轮或重放时漏入。

### #360 的 MG-owned 经理成本桥

本包不接管 Workforce 的 #360 collective 案卷、三 cohort 分区或 owner realm-trust 事务，只拥有三名经理的真实分数成本。为让
Workforce 能先对三人做全局预检、再在同一同步 effect 内原子结算，生成器提供三组无动态变量名的固定入口：

```text
zg361_mg_m360_collective_cost_c1_can_apply_trigger
zg361_mg_m360_collective_cost_c2_can_apply_trigger
zg361_mg_m360_collective_cost_c3_can_apply_trigger

zg361_mg_m360_apply_collective_cost_c1_effect
zg361_mg_m360_apply_collective_cost_c2_effect
zg361_mg_m360_apply_collective_cost_c3_effect
```

调用时 `this` 必须是相应 cohort 的 frozen manager，且调用者先保存
`scope:zg361_we_m360_cost_owner`（AL owner）与 `scope:zg361_we_m360_cost_subject`（持有 sealed collective 的 AL subject）。
adapter 不接受调用者传入 score、cost、receipt ID 或 hash；它只读 sealed collective 的 owner/subject/cycle/case/state、
settlement、route 与相应 cohort，并要求 `cohort_id = settlement_id * 10 + ordinal`。每个 cohort 还必须冻结
`mg_cycle/mg_case/mg_snapshot_source_serial/b1_cycle/b1_case`，供 MG 反查真实来源。

manager review snapshot 现在同时冻结当时可用的 B1 #360 source manager/cycle/case。预检逐字段核对：

- F 已以同 owner/manager/mg cycle/mg case 到达 `state=5, active=0`；team snapshot 的 owner/subject/cycle/case 和
  `snapshot_source_serial` 全部一致；
- #036 receipt 与 object 均为同一 F tuple、state 4，choice 只能是 A/B，不能拿 C 的“无报告”路线冒充真实经理案卷；
- 当前 B1 source 与 snapshot 冻结的 B1 manager/cycle/case 完全一致，state 8；member/agenda count+hash、quota 与
  all-meet receipt 必须逐项等于 sealed collective；还必须是 `status=1, sealed=1`，且产品生成的 source ID/hash
  与 MG snapshot 冻结值相等。换一轮 B1、换一名经理或换一个 cohort 都不能通过。

当前 producer 的路线合同是确定的。Route A 把该 cohort 的全部真实 C 候选作为获批例外，因此
`forced_count=0` 且 **`cost = exception_count = quota`**；approver 必须是这名经理的合格天朝制直属上司。正成本还要求
`report_score_available=1`、真实 `zg361_mg_manager_score` 存在、首次结算前等于冻结 report baseline 且余额足够。
apply 记录 before，向真实 `zg361_mg_manager_score` 直接加 `-cost`，再记录 after/delta；不修改已经结案的
`zg361_mg_report_manager_score`、#036 object 或十年历史。Route B 强制 `forced_count=quota, exception_count=0, cost=0`，
不要求 manager score 或 report availability，也不创建伪造的零值 cost receipt；它返回 N/A，由 Workforce 记录
`manager_cost_required=0 / verified=1 / receipt=N/A`。

Route A 的正成本 receipt 由 MG 自己生成 `id = cohort_id * 1000 + 360`，hash 由 ID、route、cost 派生，并冻结
owner、AL subject/cycle/case、settlement ID/hash、cohort/ordinal/manager、MG snapshot identity+revision、B1 cycle/case/source ID/hash、
route/quota/exception/cost 与 score before/after/delta。完全相同的 receipt 重放返回 result 2，绝不再次扣分；同 receipt ID
或同 settlement+cohort 却有任一 tuple/cost 漂移写 typed RED 2 且零业务写入。只有更晚的 AL cycle/case 才能覆盖 manager
scope 的 latest receipt。任何其他来源不完整或不变量失败写 typed RED 4。这里不读取、更不维护旧的
`zg361_we_manager_score`；Workforce 只能复制 MG receipt 作为当前 #360 的证据。

### Q121–128 只读投影边界

Q 的对象与状态权威只属于 `zg361_career_hc_runtime_effects.txt`。管理者包只调用
`zg361_mg_project_career_hc_q_receipts_effect` 读取 Career/HC 已结算的 receipt，不调用任何
`zg361_case_q_open/advance/close`，不调用 Q core/consumer，也不写任何 `zg361_ch_*` 变量。

投影必须同时满足 `consumed=1`、`business_consumed=1`、owner/subject/cycle/case、以及冻结 stage：

```text
121/122 -> state 1
123/124 -> state 2
125/126 -> state 3
127/128 -> state 4
```

A/B 只复制 Career/HC 权威 `manager_object_{id,owner,subject,cycle,case,state,revision}`；CK3 adapter 复核对象 owner/subject/cycle/case/state/route 与 receipt 相等并复制权威 revision。Python oracle 还要求调用者提供同一 typed authoritative object，并把 revision 一并逐字段复核，不允许只给一包手工 fields 就自称来自 Career/HC。C 必须不带对象，只投影 route/value，`authoritative_object_present=0`。完全相同的投影重放是 no-op；同 token 改 route/value、倒退到旧 cycle/case/state、或同 token 换 owner 都写 typed stale RED 2。manager 自己的 `zg361_mg_qNNN_*` 只是只读缓存，不是第二份 Q 案卷或业务状态。

## 五、京察核心合同

现有产品链保持：

- `activity_zg361_jingcha.cost.treasury = 0` 且 `ui_predicted_cost = 0`；京察本身免费。
- 玩家定期召集令第一项是默认举办并打开原生活动规划器；拒办是第二个明确抗命选项。
- 合格 AI 不走活动 UI，后台默认履责。
- `zg361_kpi_jingcha_evidence_value` 在冻结 KPI 时读取保存的原上司并精确减 50；`zg361_compute_kpi_effect` 先冻结证据，再清除 marker，所以同一拒办只消费一次，调任后的新上司不能继承。

既有 `zg361_refused_jingcha` modifier 的默认数值仍为 -20，但玩家在 `zg361.40` 第二项明确拒办时，正式事件 caller 已直接调用 `zg361_mg_refuse_jingcha_exact_effect`，不再先走旧 `zg361_refuse_jingcha_effect` 再靠 F032 自愈。该 effect 在清理 mandate 前冻结 `owner = 发令时直属上司`、`subject = 拒办经理本人`、`cycle/case = 当期 B1 绩效季 token`（极端旧存档缺 token 时以 mandate year 派生稳定 fallback），并记录 state/revision/operation/year、`opinion_delta=-25` 与 receipt status。随后先移除同名旧实例，再用动态 `opinion = -25` 安装唯一实例；具备考核资格的原上司同时写一次性 `-50` 下轮 KPI 重大理由和 `reviewer_eligible=1`。最后才统一清理 pending/superior/reviewer/year，故生命周期清理不能抹掉本次业务身份。

承诺举办后 D+300 仍未完成属于自动违约，不是玩家在弹窗中“明确拒办”；它暂时保留既有 deadline failure effect。两条路径均不改变京察免费、第一项默认举办、AI 后台履责、独立顶级领主 prestige fallback 或伯爵/男爵只受评的既有合同。F032 的旧存档兼容归一化仍保留，但只是迁移兜底，不再冒充明确拒办的正式 caller。

## 六、原子资源与收费边界

本 15 项 manifest/L0 合同中没有金币货币，`349` 与 `353` 的成本是 `capacity_hours`。因此这里不凭空扣国库或个人金币；用户要求的“凡收费机制必须国库 + 个人双付款”仍是全局硬合同，等实际金币收费编号接线时执行。

本包两笔 capacity 事务都使用共享 kernel：

```text
全量 owner/subject/cycle/case/state 预检
  -> reserve
  -> settle
  ->（仅有效同案 receipt）refund
```

余额不足写 typed RED 5，不发生领域扣款；重复 settle/refund 与 stale token 只 no-op。退款 effect 分别是 `zg361_mg_refund_audit_capacity_effect` 与 `zg361_mg_refund_admin_capacity_effect`。

## 七、deadline、幂等与 typed RED

- F 四个阶段事件、AK 五个阶段事件都带 owner、subject、cycle、case、expected state。
- 348 的到期事件额外带 expiry；案件关闭后 token 仍独立有效，但 successor owner/cycle/case/state/expiry 任一不符即 stale no-op。
- 每个编号拥有六字段 mechanism receipt：owner、subject、cycle、case、state、choice。
- typed RED 数字稳定：1 permission、2 stale、3 duplicate、4 invariant、5 resource exhausted、6 insufficient frozen history。
- stale deadline 只留 `debug_log`，不得修正新案、发第二份资源或推进 successor 状态。

## 八、本地化边界

简中与英文是本轮创作并静态审阅的源文案。法、德、日、韩、波、俄、西文件仅为 English structural placeholders，用来保持九语言结构可加载；它们是 not release-grade translations。普通开发不提前投入七语发布审计，正式 release 前再按仓库工作流完成翻译和实机抽检。

玩家的 F 结果事件直接显示本案冻结的 `zg361_mg_report_manager_score`、来源轮次、当前轮次、理由合计和九宫格编码，明确解决“上司给我考核，窗口却不写我的绩效是多少”的问题。三个结果都同时显示 availability；上游选 C 时写 0 + unavailable，不能把上一周期同名变量当成本案结果。AI 永不弹这两个报告事件。

## 九、静态验收与下一步实机

```powershell
py -m py_compile tools/gen_361_manager_governance_runtime.py tools/zg361_manager_governance_model.py tools/test_zg361_manager_governance_model.py tools/test_zg361_manager_governance_runtime.py
py tools/gen_361_manager_governance_runtime.py --check
py tools/test_zg361_manager_governance_model.py
py -O tools/test_zg361_manager_governance_model.py
py tools/test_zg361_manager_governance_runtime.py
py -O tools/test_zg361_manager_governance_runtime.py
py ../tools/test_zg361_phase2_b3_manager_governance_action_cell.py
py -O ../tools/test_zg361_phase2_b3_manager_governance_action_cell.py
py ../tools/test_run_zhongguo_promo_capture.py
py -O ../tools/test_run_zhongguo_promo_capture.py
```

L0 批量覆盖 15 项的 A/B/C、每项一个原子 negative、exact duplicate、归一化 route 冲突、输入 fingerprint 冲突、successor/stale、owner drift、route-C 债创建/到期/一次消费，以及 Q 八项三路线只读投影；同时锁住 F 与 AK 的上游 C / 下游 A-B 混合组合，不允许旧值穿透。京察回归另断言 `zg361.40.b -> zg361_mg_refuse_jingcha_exact_effect` 的正式直连、清理前冻结四元业务身份、直属上司 -25 与合格考核上司下轮 -50。CK3 静态层另锁住 351 的两个
`ordered_vassal position = 0/1` 和显式 manager scope，防止再次把第 0 位经理漏掉或在 vassal scope 误读 `root.var`。这些仍只是 L0，不替代下一段的 MCP-first 实机矩阵。

正式 `run_zhongguo_acceptance.py` 已注册
`manager_governance_gameplay_action_and_postcondition_matrix` 并接入 B3 action-cell handler；manager snapshot capability/query flag
也属于 full Phase2 capability profile。当前 native typed selector 尚未绑定，registry 与 handler 因而固定输出
`provider_pending / static-ready`：`gameplay_action_executed=false`、`action_cell_invoked=false`、
`action_ack_is_business_postcondition=false`，且没有 provider postcondition 时绝不进入 GREEN。focused B2 capability profile
仍只要求原来的 B2 子集，不会被 B3 缺口阻断。未来 selector 必须提供 provider-observed 的“AI 直属经理 + 该经理直属下属”
身份，随后 handler 才调用 action cell；action cell 又必须观察 B1 新 receipt 与 B3 F035/F032 joined postcondition，ACK 不能替代查询结果。

下一步通过 MCP 查询角色、上司、review/case/state/receipt/capacity/opinion/KPI；禁止优先 OCR。一次 CK3 启动应批量跑完：玩家经理、授权 AI 公爵经理、伯爵/男爵只受评、F032 下一轮 component-8 一次结算、F035 下一轮真实 bottom slots、346/347/354 pending→settled/discarded、拒办京察、资源不足、重复 ticket、stale deadline、十年/版本迁移等矩阵。没有这批 paused snapshot 与日志之前，状态保持 `static-ready`。
