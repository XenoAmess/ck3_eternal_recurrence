# 361 二期：管理者与制度运营 CK3 运行时规格（F032–036、AK345–354）

## Readiness boundary

- Readiness: `static-ready`
- MCP evidence: `none`
- CK3 live evidence: `none`
- 目标编号：`032–036` 与 `345–354`，共 15 项。
- 明确不含：`312–333`；该段属于职业/学习子包，不得由本运行时抢占。
- 本规格证明的是确定生成、产品脚本、状态/收据/期限/资源合同与 L0 静态测试。它不是 fixture-live、production-live 或发版签核。

## 一、独立产物与集成边界

唯一生成器是 `tools/gen_361_manager_governance_runtime.py`，生成：

- `common/scripted_effects/zg361_manager_governance_runtime_effects.txt`
- `events/zg361_manager_governance_runtime_events.txt`
- 简中、英文及七份英文结构占位本地化，共九份 yml。

确定性语义 oracle 是 `tools/zg361_manager_governance_model.py`，其测试是
`tools/test_zg361_manager_governance_model.py`；CK3 生成层测试是
`tools/test_zg361_manager_governance_runtime.py`。oracle 的 readiness 固定为
`python-l0-only`，不以 Python 通过冒充 CK3/MCP 实机。

本包不写 B1、B2、考核榜、共享 case kernel、中央 effects/events/interactions，也不新增顶层 GUI 按钮。唯一外部接缝是可调用 effect：

```text
zg361_mg_dispatch_subordinate_managers_effect
```

它应由结算生命周期在上级 `review_serial` 已确定后调用。当前任务明确禁止修改中央入口，因此本包只交付 callable adapter；在接缝正式接入并完成 MCP-first 实机以前，不得把本包写成 live。这个未接线边界是有意保留的集成 RED，不用 OCR 或测试决议伪造通过。

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

`035` 在 state 1 内先冻结 strict/relaxed/off/mixed 分布及三档守恒收据，不自行推进状态；`032` 必须先消费这张收据。

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

每个编号还把实际参与结果的数值事实（含“变量存在”位）折叠成 `requested_input_fingerprint`，A/B 冻结到 `object_input_fingerprint`，C 冻结到 `debt_input_fingerprint`。同 owner/subject/cycle/case 与同 route 下，指纹不等也写 stale RED 2，不能用已经存在的 receipt 掩盖偷换输入。字符引用等不能直接进入 CK3 数值运算的 opaque payload 会写 presence 位；调用者改变其身份时必须递增 `zg361_mechanism_NNN_input_revision`，该显式 revision 也进入指纹。资源余额不进入指纹，因为 349/353 会亲自改变余额，权威防重由 reserve/settle receipt 承担。相同 route、相同指纹、相同 receipt 的重放才是 exact no-op，不再写业务或 RED。旧 delayed ticket 由五元 guard 直接 stale no-op，owner 也不能在相同 token 上漂移。

C 明确不生成伪业务对象，而是生成一项可消费制度债：

```text
mechanism + source owner + subject + source cycle + source case + source state + source revision
due_cycle = source cycle + 1
status = pending(1) -> settled(2)
```

`zg361_mg_consume_due_policy_debts_effect` 只在下一轮及以后、由当时的直属上司入口消费一次；到期判断与 `settled_cycle` 都使用 `root.var:zg361_review_serial`，不能误用受评经理自己的旧 serial。原 source owner 永不改写，另记 `settled_by_owner`。每项债向下一轮 032 团队快照写 `manager_score_delta = -3`，快照消费后立即删除 delta，避免重复扣分。精确重复 settlement 是 no-op，改写已结清债为 stale RED。

F032/F033/F034/F036 的 C receipt 与 A/B 一样调用共享 stage transition 并安排下一张 ticket；C 只是“不造该编号业务对象”，不是“把整份经理案卷卡死”。混合路线也必须继续走：035C 后的 032A/B 不读取旧 `distribution_conserved`；032C 后的 033/034/036 用显式 `available=0, basis=0`，不会拿上一周期经理分冒充本周期；033C/034C 在最终报告中同样显示 unavailable，而不是漏字段或回显旧案。

AK 的 stage barrier 同样 route-aware：347C 以“未做覆盖天然保持 quota neutral”通过守恒门，349C 以“未启动审计、没有未结 capacity”通过结算门；其余 C receipt 与配对编号共同推进正常阶段。跨阶段 consumer 也按 receipt choice 选源：345C/346C 让 350/353 使用显式默认 basis；350C 让 352 建立 `new_series=1`、`source_available=0` 的新序列对象；352C 让 354 使用 mapping basis 0。历史 A/B 变量可以继续留作档案，但 C 路径绝不读取它们。

## 四、逐编号 CK3 合同

| ID | typed operation | 实际写入 | 后续 consumer / 不变量 |
|---:|---|---|---|
| 032 | `manager.score_frozen_team` | 七项团队冻结分项、管理者总分、拒办京察一次性收据 | `source_team_serial < superior review_serial`；直属上司 owner；拒办只匹配保存的上司/年份 |
| 033 | `manager.explain_profile_decision` | 五个 `[-25,25]` 理由码、画像版本、一次关系覆盖、申诉风险 | 理由总分进入年度制度日志；不得反写 KPI/档位 |
| 034 | `manager.freeze_nine_box` | 两轮冻结分、绩效轴、潜力轴、九宫格编码 | 少于两轮时明确写 `ready=0/code=0` 与非致命 typed RED 6，但仍记收据并推进，避免首轮永久卡案；只读，不扣钱、不改 KPI/档位/HC |
| 035 | `manager.freeze_distribution_mode` | strict/relaxed/off/mixed、top/middle/bottom、后果强度 | `top + middle + bottom = cohort`；`n>=5` 的 strict/relaxed 至少一名末位 |
| 036 | `manager.compile_decade_report` | 按 owner 分段的连续年度累积、十年 ready、奖金净流、上一轮经理分 | owner 变化、年份断档或上一段已满十年时重开；同年重复由 receipt 拒绝 |
| 345 | `policy.freeze_next_cycle_calendar` | 年度/半年/季度次数、行政工时、effective cycle | 只从 `current case cycle + 1` 生效；同周期玩家/AI 合批标记为 1 |
| 346 | `policy.consume_material_offcycle_signal` | 重大信号、三选一动作、一次消费周期 | materiality `<50` 不建案；`cohort_reruns = 0` |
| 347 | `policy.consume_override_point` | beneficiary、bearer、reason、预算/已用点 | before/after cohort 数相等；不消耗点数就不能越预算 |
| 348 | `policy.expire_or_renew_exception` | owner/subject/cycle/case/state/expiry token | 365 日到期；无新事实恢复默认，有新证据才续期；旧 token stale no-op |
| 349 | `policy.run_reproducible_audit` | 样本率、风险数、seed、抽样 fingerprint、clean/findings | 透明度只降比例不免审；行政 capacity reserve→settle，可守卫退款；clean 增制度信任 |
| 350 | `policy.version_benchmark` | old/new version、未来生效周期、阈值、解释码、旧历史快照 | 旧值/公式/版本不重算；新版本复用 345 的未来 effective cycle |
| 351 | `policy.measure_regional_pilot` | 互斥 pilot/control、预登记指标、冻结结果及差异 | 两区域与全部结果齐备前 `result_ready=0` 且不计算差值；仍以“不可用”收据推进，避免小领地永久卡案 |
| 352 | `policy.map_immutable_history` | original value/formula/version、mapping version、映射值或新序列 | original 三字段永不删除/覆盖；354 继续读取 mapping version |
| 353 | `policy.charge_admin_capacity` | 表单、会议、申诉、校准、打断工时及总额 | capacity reserve→settle，可守卫退款；错误/翻案反弹写入下一轮 032 经理分 |
| 354 | `policy.recompute_fairness_metrics` | raw/reported 三率、gap、gaming、披露/修复信用 | 原始送达/申诉/翻案/离职重新计算；披露和修复同时成立才 `trust +5` |

### A/B/C 路由差异

| ID | A：证据/治理路线 | B：政治/捷径路线 | C：延期路线 |
|---:|---|---|---|
| 032 | 七项具名冻结汇总全部进入经理分 | 只用冻结汇总，对负向交付/京察/申诉/留任作惩罚性聚合 | 不造经理评分对象；下一轮制度债 |
| 033 | 画像权重决定五项理由码，不做人情改档 | 允许一次 `[-1,+1]` 人情覆盖，保留 before/after 与申诉风险 10 | 不造画像说明对象；下一轮制度债 |
| 034 | 两轮以上才分类；首轮 `ready=0/code=0` 但正常结案 | 用当前轮快标，下一轮失效并记录短视风险 | 不造九宫格对象；下一轮制度债 |
| 035 | 冻结显式 `zg361_distribution_mode`（1 strict / 2 relaxed / 3 off / 4 mixed，缺省 mixed）、规则来源、阈值与 review serial | 强制 strict 10% | 不造分布快照；下一轮制度债 |
| 036 | 追加按 owner 分段的年度账，十个连续年度形成十年报 | 只做当年亮点卡，`history_rows=0` 且标 causal warning | 不造年度/十年报对象；下一轮制度债 |
| 345 | 年度一次正式评审 + 一次轻 check-in；20 行政工时、30 天反馈 | 季度四次；72 工时、7 天反馈，并记短期偏差 25 / 疲劳 30 | 不造日历对象；下一轮制度债 |
| 346 | 重大信号一次消费，不重排原 cohort | 生成独立 rerank 版本，保留原榜，同时记录 disruption / recency bias | 不造信号对象；下一轮制度债 |
| 347 | 每轮最多两次有 beneficiary/bearer/reason 的覆盖 | 不封顶，但逐笔留审计与申诉风险 | 不造覆盖账；下一轮制度债 |
| 348 | 365 日到期；有新证据从处理日再续 365 日，否则恢复默认 | grandfather，无截止日，记录特权累积/公平风险 | 不造例外票据；下一轮制度债 |
| 349 | 20% 风险优先 + 可复现随机抽样；clean 结果增加制度信任 | 5% 低抽样、无 clean 信任，保留严重漏检风险 | 不造审计对象；下一轮制度债 |
| 350 | 战略难度解释新阈值，旧历史不重算 | 按 top growth 自动棘轮，保留 ratchet risk | 不造版本对象；下一轮制度债 |
| 351 | 预登记 pilot/control，互斥且结果齐全后才算差值 | 全境直接铺开，无因果对照并记录迁移风险 | 不造试点对象；下一轮制度债 |
| 352 | 新建 comparable mapping layer，三项 original 字段只读 | 用最新公式重算派生层，显式标 contamination risk | 不造映射对象；下一轮制度债 |
| 353 | 五类真实工时全部扣 capacity；显示真实总额和精简项 | 仍扣全部真实 capacity，但报表藏成 0，并把隐藏损耗计入下轮经理分 | 不造行政成本对象；下一轮制度债 |
| 354 | raw 三率重算；确有 gap 且主动披露、完成带 ID 的修复后才 `trust +5` | 制造漂亮 reported 三率，但 raw、suppression/reclassification 与 gaming 仍留审计 | 不造公平审计对象；下一轮制度债 |

035 的四模式计算另有纯函数 `compute_distribution_snapshot`。快照包含规则来源、review serial、分母、三档数量、绝对线、all-pass 与 hash；后续切换政策只会产生新快照，不会回写旧周期。strict 为 10% 末位，relaxed 为 5%，off 为 0，mixed 为 10% 且全员过绝对线时只减轻末位后果；四种模式都守恒。

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

既有 `zg361_refused_jingcha` modifier 的默认数值仍为 -20。独立运行时提供 `zg361_mg_refuse_jingcha_exact_effect`：先移除同名旧实例，再用动态 `opinion = -25` 安装唯一实例，并保存原上司/年份精确收据。若旧中央路径已经先加 -20，下一次 F032 消费会在收据不匹配时同样执行“移除旧实例 → 安装 -25”；若 adapter 已执行则不重复加。中央拒办 caller 切换到该 adapter 属后续集成接线，不在本次“不得修改中央文件”的授权内。

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
```

L0 批量覆盖 15 项的 A/B/C、每项一个原子 negative、exact duplicate、归一化 route 冲突、输入 fingerprint 冲突、successor/stale、owner drift、route-C 债创建/到期/一次消费，以及 Q 八项三路线只读投影；同时锁住 F 与 AK 的上游 C / 下游 A-B 混合组合，不允许旧值穿透。CK3 静态层另锁住 351 的两个
`ordered_vassal position = 0/1` 和显式 manager scope，防止再次把第 0 位经理漏掉或在 vassal scope 误读 `root.var`。这些仍只是 L0，不替代下一段的 MCP-first 实机矩阵。

下一步必须先将 callable adapter 接入真实结算 hook，再通过 MCP 查询角色、上司、review/case/state/receipt/capacity/opinion/KPI；禁止优先 OCR。一次 CK3 启动应批量跑完：玩家经理、授权 AI 公爵经理、伯爵/男爵只受评、拒办京察、资源不足、重复 ticket、stale deadline、十年/版本迁移等矩阵。没有这批 paused snapshot 与日志之前，状态保持 `static-ready`。
