# 361 二期项目、功劳、汇报与矩阵协作 CK3 静态运行时

状态：**CK3 script static-ready / not live**

权威生成器：`tools/gen_361_credit_project_runtime.py`

生成结果：

- `common/scripted_effects/zg361_credit_project_portfolio_lifecycle_effects.txt`
- `common/scripted_effects/zg361_credit_project_{e,i,j,r}_{orchestration,policy_debt}_effects.txt`
- `common/scripted_effects/zg361_credit_project_mNNN_<purpose>_effects.txt`（每项机制一个 consumer + A/B/C routes）
- `events/zg361_credit_project_runtime_events.txt`
- `localization/*/zg361_credit_project_l_*.yml`

专测：`tools/test_gen_361_credit_project_runtime.py`

Python 参考合同仍为 `tools/zg361_phase3_credit_project_model.py`；本包没有修改该模型、B1、B2、scoreboard、shared case kernel、on_action 或任何中央派发文件。

## Effect 文件边界与证据

旧 `zg361_credit_project_runtime_effects.txt` 单文件约 1.31 MB、含 156 个顶层 effect，现已退役。生成器按用途产出 36 个 shard：portfolio lifecycle 1 个、四域 policy-debt 4 个、四域 orchestration 4 个、27 项机制各 1 个。每个文件含 4–8 个 effect，最大文件小于 54 KB；没有超过 10 个、也没有需要实机例外说明的文件。

`--check` 会把旧 monolith 残留判作 drift，普通生成会在全部 shard 写出后删除该旧文件。专测还把 36 个 shard 按生成顺序拼接，并逐个比较全部 156 个顶层 effect 的名称、顺序与完整定义体，确保拆分只改变文件边界。这个约束用于降低加载边界风险和提升故障定位性；它本身不构成“此前启动问题由文件过大造成”的因果证据，本包仍保持 static-ready / not live，后续加载性能结论必须来自真实 CK3 artifact。

## 语义权威与冲突裁决

本包逐号路线的权威优先级是：

1. `tools/mechanism_acceptance/acceptance_*.json` 中每个编号的 acceptance/runtime program；
2. `docs/361-phase2-full-implementation-program.md` 第 59 行规定的 `C = mechanism-specific policy.defer`；
3. 本规格、生成器及其生成投影。

因此，旧细粒度设计表或旧文案中把 C 写成第三条业务方案的内容不再是运行时权威。下列 27 项的 **C 全部是纯 `policy.defer`**，不能因为机制标题涉及抢功、汇报、PIP、止损等主题，就在 C 中偷偷创建相应业务对象。A/B 保留原有业务语义。

## 精确范围与状态图

本包精确 CK3-wires 27 项，不多号、不漏号：

| 案卷 | 编号 | 执行顺序与共享 kernel 状态 |
|---|---|---|
| E 功劳与资源 | 026–031 | `030,026 @1 → 027,031 @2 → 028 @3 → 029 @4 → closed` |
| I 汇报与注意力 | 054–061 | `061,054 @1 → 056,057 @2 → 058,059 @3 → 055,060 @4 → closed` |
| J 矩阵与交接 | 062–068 | `063 @1 → 062,065 @2 → 064 @3 → 066,067,068 @4 → closed` |
| R 项目治理 | 129–134 | `131 @1 → 129,134 @2 → 130 @3 → 132 @4 → 133 @5 → closed` |

四案卷按 `E → I → J → R` 串行打开。每个 stage 只有该 stage 的全部机制留下当前五元 receipt 后，才能调用 shared kernel 的唯一 advance edge。

## 角色与公开入口

公开入口是 manager-scope scripted effect：

```text
zg361_cp_open_portfolio_effect = { SUBJECT = <direct assessed vassal> }
```

这是本包唯一暴露给 central dispatcher 的 manager-scope portfolio adapter。每次调用时，它先在 `SUBJECT` 上执行本包唯一 due-debt aggregate，再决定能否打开新 portfolio；任何 future、stale、cross-owner 或损坏的 pending debt 都会置 fail-closed 标记，阻止本次新案覆盖旧债。

ROOT 必须通过既有 `zg361_is_celestial_liege_trigger`，也就是在世、有地、天朝制、公爵及以上。玩家 ROOT 收到顺序决策卡；符合相同门槛的 AI ROOT 只走后台确定路线，不打开 GUI。`SUBJECT` 必须是其直属、在世、有地官员；伯爵和男爵可以作为 SUBJECT，但本包没有任何 subject-side open、reserve、allocation 或 assess 入口。四个 `*_subject_read_effect` 只允许本人读取可见 revision。

玩家只会在首案打开时收到第一张卡。每个编号的下一张卡均通过 `days = 1` 排队；E→I、I→J、J→R 三条跨案卷边使用带完整关闭身份校验的 hidden D+1 queue event。故 adapter 不会在同一游戏日弹出 27 个窗口；AI 仍只有无 GUI 的后台队列。

initializer 必须同时保存两种不同生命周期的 subject 引用：`zg361_cp_portfolio_subject_scope` 只是在当前调用内供跨 scope 写值的 temporary saved scope；`zg361_cp_portfolio_subject` 必须用 `set_variable ... value = this` 写成受评人身上的持久 character variable，供下一周期 deferred cleanup 在存读档后继续做身份核验。saved scope 不能替代持久 variable。

本包不新增 on_action 或中央调度；中央现已通过同一个公开 adapter 调用本包，包内只拥有一次 due pass，避免多入口重复扣分。

## 五元身份、receipt 与 A/B 事务

每次操作冻结并核对：

`owner + subject + cycle + case + state`

每个编号只有一组互斥 receipt：`receipt_owner/subject/cycle/case/state/choice`。A/B route 依次执行完整身份与资源预检、`zg361_case_kernel_record_operation_effect`、业务与资源写、五元 write ticket、provenance，随后立刻调用该编号的 downstream consumer。状态码固定为：

- `1 applied`
- `2 idempotent no-op`
- `3 stale no-op`
- `4 typed RED`（不得留下 receipt、业务写或资源写）

每个 A/B consumer 再次核对 write tuple 与当前案卷 tuple，冻结 `consumed_*` 和对玩家/后续机制可读的具体结果。单纯 binding、事件标题、receipt 或字段存在均不计作业务机制实现。

## C：纯延期，不创建业务事实

C 与 A/B 共用完整五元 guard、互斥 receipt 和 stage barrier，但其 applied payload 仅做以下事情：

- 把本机制的 semantic choice 锁为 `3`，并消耗该案卷一个 operation slot；
- 精确冻结一笔五元债：`debt_owner/debt_subject/debt_cycle/debt_case/debt_state`；
- 同时冻结 `debt_mechanism`、`debt_due_cycle = cycle + 1`、`debt_status = pending`、`debt_audit_state = opened` 和 `debt_business_object_created = 0`；
- 把 portfolio 标记为 deferred、把跨周期 cleanup 状态标记为 pending，并把 open-debt 计数恰好增加一次。

C 不读取业务对象作为造债前置，不创建或修改项目、汇报、功劳、注意力、HC、晋升等业务对象或资源，不写 `write_*`/business provenance，也不调用 A/B downstream consumer。相同 receipt 的重放只得到 `idempotent no-op`，不会再开第二笔债。不同 choice 也不能覆盖已经存在的 receipt。

## 下周期债务消费与绩效后果

`zg361_cp_consume_due_policy_debts_effect` 是包内唯一 aggregate；公开 adapter 每次调用它一次，并逐号调用 27 个固定 consumer 各一次。单债 consumer 必须同时验证：

- 五元 debt、`mechanism/due/status/audit/business_object_created` 全部存在且值合法；
- 原 C receipt 的五元身份逐字段等于 debt，且 `receipt_choice = 3`；
- 当前 `root` 正是冻结 owner、当前 `this` 正是冻结 subject；
- `root.zg361_review_serial` **恰好等于** `debt_due_cycle`。

只有 exact due 才会结算。成功路径仅一次向冻结 owner 的既有 `zg361_b2_management_debt` 加一，作为下一轮 KPI/绩效计算的真实组织后果；然后写 `status = settled`、`audit_state = consumed`、`settled_by = root`、`settled_cycle = root.review_serial` 与 `performance_sink = 1`，并把 open/settled 计数各移动一次。它不补做被延期的业务对象。

已经 settled 且 `settled_by/settled_cycle` 匹配的精确重放只写 audit-only consumer status，不再触达 B2 sink。当前周期小于 due 是 future，当前周期大于 due 是 stale；cross-owner、cross-subject、receipt 身份不符、字段缺失或其他损坏 pending 也均 fail closed。上述路径都不能结算、不能重写 owner、不能开新 portfolio。初始化新 portfolio 只把当期 `portfolio_deferred` 清零，不抹掉累计 open/settled debt 账。

aggregate 只有在逐号消费结束后仍无 blocked 标记、open-debt 已归零、portfolio 确实 deferred 且 cleanup 仍为 pending 时，才调用一次 `zg361_cp_settle_deferred_portfolio_effect`。该 effect 是跨周期清理旧 portfolio 的唯一入口：它释放确实存在的旧 project remainder、关闭确实存在的旧 active project，并把 cleanup 标成 settled。重复 adapter 调用因 cleanup 状态已经终结而 no-op；缺失项目时也不会创建身份、version 或 deadline。由此，C 当期没有间接修改业务对象或资源，清理发生在所有制度债于下周期 exact due 结清之后。

## 首次延期后的确定性闭合

首次 C 之后，本 portfolio 的后续路线必须继续 C：

- 玩家事件的 A/B option 变为不可用，C 始终保留；
- authorized AI 检查 deferred flag 后确定性调用 C；
- C 仍留下合法 receipt，因此 stage barrier 和 E→I→J→R 队列可以正常闭合，而不会因缺少项目/汇报对象让后续 A/B 进入死锁。

同周期 finalizer 不释放容量、不关闭项目，也不写任何项目或汇报对象。它为 deferred portfolio 使用 `available + spent + remaining = 100` 的冻结守恒式（保留旧 reservation），同时验证注意力和晋升槽账，并显式写 `final_deferred = 1`。真正释放由下一周期 exact-due aggregate 在全部制度债结清后一次性完成。若 C 在 #030 就发生、项目从未存在，跨周期 cleanup 不伪造 owner、identity、version、deadline 或 report object；它也不会拿缺失业务对象冒充完整 A/B portfolio。

## A/B 业务守恒与跨机制消费

- #030 的 A/B 创建唯一稳定项目对象并分别预留 40/60 容量；其余 A/B 必须先验证对象身份再提交，并递增 version。#054 的 A/B 另建独立汇报对象；其后 A/B 签字、路由、阅读、风险和创意仲裁沿同一对象递增版本。
- 27 个业务 consumer 只服务 A/B，发布项目身份、version、deadline 与 active/cancelled/stopped 状态；I 域材料 consumer 还发布汇报 identity/version/deadline。receipt 不能替代这些业务对象或可见投影。
- #027 的 A/B subject/manager/cross-department 签字贡献严格合计 10000 bp；#028 的 A/B 抢功转移和审计回拨净零；#056 的 A/B 从 claimed ledger 建立 report ledger；#057 的 A/B 只签署合计 10000 bp 的版本。
- 跨部门 reviewer 的身份参与 A/B 的三方签名、附件、抄送、创意来源、岗位归属与 shared metric 依赖消费。#058 A/B 只写 routed recipients，#055 A/B 才真实扣 attention。
- #063 A/B 权重分别为 70/30 与 50/50，均严格合计 100；#064 A 只有新旧上司双签且 successor 合法时才改变 future active manager，`historical_owner` 永远只读。
- #129 B 最多消耗一个晋升槽；#130 A/B 的调岗披露与角色证据有具名 source/destination manager；#131 A/B 在结果前锁定项目轨道；#132 A/B 的 business stop 与 individual judgement 分账；#133 A/B 的学习消费与具名责任分账；#134 A/B 只写一个最终 owner。
- #068 A/B 只读取既有 B2 `zg361_b2_pip_state` 判断历史 PIP，不写任何 B2 字段。只有 due-debt consumer 可写本包唯一授权的 `zg361_b2_management_debt` sink。

未发生 C 时，正常 final conservation 同时要求容量、注意力、晋升槽与 10000 bp 贡献账守恒，项目槽释放，项目对象 version 精确为 27、状态为 cancelled/stopped，汇报对象 version 精确为 7。

## 本地化、测试与证据边界

简体中文和英文为日常开发文案。所有 27 项 C 使用统一的 `policy.defer` 文案；法、德、日、韩、波、俄、西文件使用英文结构占位，只证明 key 结构可加载，不是发布翻译。

静态专测覆盖精确 ID、A/B 旧业务、C 无业务写、五元债、exact-due 单次 sink、settled duplicate、future/stale/cross-owner fail-closed、public adapter ordering、玩家/AI deferred cascade 与最终守恒；普通模式和 `python -O` 必须同时通过。

本包没有启动 CK3，没有 parser 输出、paused snapshot、MCP、fixture 或生产实机证据。因此最高状态只能是 `static-ready`，不能标记 `fixture-live`、`production-live` 或 `complete`。静态 GREEN 不能替代中央调用、玩家/AI 双路线、跨周期消费、存读档和实机日志验收。

## #026 contribution receipt 跨包合同

#026 的 A/B 成功事务在 shared case-kernel operation 成功、`case_e_revision` 已递增之后，额外签发一份供后续指标包消费的业务 receipt：

- `zg361_cp_contribution_receipt_cursor` 是受评人作用域、跨 portfolio 保留的单调游标；不存在时从零初始化，每次 #026 A/B 成功恰好加一；
- `zg361_cp_m26_contribution_receipt_id` 取本次游标值；
- `zg361_cp_m26_contribution_receipt_revision` 取本次成功操作后的 `zg361_case_e_revision`；
- receipt 仍由既有 `zg361_cp_m26_receipt_owner/subject/cycle/case` 四元身份限定，贡献值仍读取既有 `zg361_cp_m26_visible_value`。

这两个字段只由 #026 A/B 的真实业务写路径产生；C 延期不签发 contribution receipt，也不允许由 case serial、choice ACK 或事件名反推 receipt。Phase 3 初始化器只能在 owner 等于当前 root、subject 等于当前 this、cycle 等于当前 review serial，且 receipt ID/revision 均为正数时冻结该来源。此次只增加无玩家可见文本的持久变量，不新增或修改本地化 key。
