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

静态测试为 `tools/test_zg361_manager_governance_runtime.py`。本包不写 B1、B2、考核榜、共享 case kernel、中央 effects/events/interactions，也不新增顶层 GUI 按钮。唯一外部接缝是可调用 effect：

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

玩家的 F 结果事件直接显示 `zg361_mg_manager_score`、来源轮次、当前轮次、理由合计和九宫格编码，明确解决“上司给我考核，窗口却不写我的绩效是多少”的问题。AI 永不弹这两个报告事件。

## 九、静态验收与下一步实机

```powershell
py -m py_compile tools/gen_361_manager_governance_runtime.py tools/test_zg361_manager_governance_runtime.py
py tools/gen_361_manager_governance_runtime.py --check
py -m unittest tools/test_zg361_manager_governance_runtime.py
```

下一步必须先将 callable adapter 接入真实结算 hook，再通过 MCP 查询角色、上司、review/case/state/receipt/capacity/opinion/KPI；禁止优先 OCR。一次 CK3 启动应批量跑完：玩家经理、授权 AI 公爵经理、伯爵/男爵只受评、拒办京察、资源不足、重复 ticket、stale deadline、十年/版本迁移等矩阵。没有这批 paused snapshot 与日志之前，状态保持 `static-ready`。
