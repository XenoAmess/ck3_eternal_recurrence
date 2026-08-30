# 361 二期项目、功劳、汇报与矩阵协作 CK3 静态运行时

状态：**CK3 script static-ready / not live**

权威生成器：`tools/gen_361_credit_project_runtime.py`

生成结果：

- `common/scripted_effects/zg361_credit_project_runtime_effects.txt`
- `events/zg361_credit_project_runtime_events.txt`
- `localization/*/zg361_credit_project_l_*.yml`

专测：`tools/test_gen_361_credit_project_runtime.py`

Python 参考合同仍为 `tools/zg361_phase3_credit_project_model.py`；本包没有修改该模型、B1、B2、scoreboard、shared case kernel、on_action 或任何中央派发文件。

## 精确范围与状态图

本包精确 CK3-wires 27 项，不多号、不漏号：

| 案卷 | 编号 | 执行顺序与共享 kernel 状态 |
|---|---|---|
| E 功劳与资源 | 026–031 | `030,026 @1 → 027,031 @2 → 028 @3 → 029 @4 → closed` |
| I 汇报与注意力 | 054–061 | `061,054 @1 → 056,057 @2 → 058,059 @3 → 055,060 @4 → closed` |
| J 矩阵与交接 | 062–068 | `063 @1 → 062,065 @2 → 064 @3 → 066,067,068 @4 → closed` |
| R 项目治理 | 129–134 | `131 @1 → 129,134 @2 → 130 @3 → 132 @4 → 133 @5 → closed` |

四案卷按 `E → I → J → R` 串行打开，使项目资源先被冻结，再允许汇报消耗、战略取消和止损结算。每个 stage 只有该 stage 全部机制留下当前五元收执后才能调用 shared kernel 的唯一 advance edge。

## 角色与入口

公开入口是 manager-scope scripted effect：

```text
zg361_cp_open_portfolio_effect = { SUBJECT = <direct assessed vassal> }
```

这是本包**唯一**暴露给未来 central dispatcher 的 manager-scope portfolio adapter。adapter 本身只在后台冻结 manager/subject/cycle 与有限资源，并打开 E 的首个编号事件；同一 manager 同一 `zg361_review_serial` 只能开一份 portfolio，重放不会重置另一名 subject 或已在途案卷。

ROOT 必须通过既有 `zg361_is_celestial_liege_trigger`，也就是在世、有地、天朝制、公爵及以上。玩家 ROOT 收到 27 张顺序决策卡；符合相同门槛的 AI ROOT 只走后台确定路线，不打开 GUI。`SUBJECT` 必须是其直属、在世、有地官员；伯爵和男爵可以作为 SUBJECT，但本包没有任何 subject-side open、reserve、allocation 或 assess 入口。四个 `*_subject_read_effect` 只允许本人读取可见 revision。

玩家只会在首案打开时收到第一张卡。每个编号的下一张卡均通过 `days = 1` 排队；E→I、I→J、J→R 三条跨案卷边使用带完整关闭身份校验的 hidden D+1 queue event。故 adapter 不会在同一游戏日弹出 27 个窗口；AI 仍只有无 GUI 的后台队列。

本包不新增 on_action 或中央调度，因此“谁在何时调用公开入口”仍是集成层前置；这不影响本包内的 CK3 effect/event 状态机静态可执行性，也不得冒充 live 闭环。

## 五元身份、事务与收执

每次操作冻结并核对：

`owner + subject + cycle + case + state`

每个编号只有一组互斥 receipt：`receipt_owner/subject/cycle/case/state/choice`。route 先执行完整身份与资源预检，再调用 `zg361_case_kernel_record_operation_effect`；只有 kernel 返回 applied 后才写业务、资源及 provenance，随后立刻调用该编号的 downstream consumer。状态码固定为：

- `1 applied`
- `2 idempotent no-op`
- `3 stale no-op`
- `4 typed RED`（不得留下 receipt、业务写或资源写）

每个 consumer 再次核对 write tuple 与当前案卷 tuple，冻结 `consumed_*` 和对玩家/后续机制可读的具体结果。单纯 binding、事件标题、receipt 或字段存在均不计作机制实现。

## 守恒与跨机制消费

- #030 成功后创建唯一稳定项目对象，冻结 manager、业务 owner、subject、制度 cycle、E 案 origin case、version、截止周期与状态；其余 26 项必须先验证对象身份再提交，并且每次 applied 恰好把 version 加一。#054 另建独立汇报对象，冻结 I 案 identity、version、截止周期及项目 origin case；签字、路由、阅读、风险和创意仲裁沿同一对象递增版本。
- 27 个 consumer 均发布项目身份、version、deadline 与 active/cancelled/stopped 状态；I 域七个材料 consumer 还发布汇报 identity/version/deadline。receipt 只负责幂等，不能替代这些业务对象或可见投影。

- 项目总容量为 100、项目席位为 1。#030 只产生一个赢家并预留 40/60/80；#026 与 #054 从同一剩余容量扣账，汇报不增加 `hard_output`；#066 或 #132 只把未花容量释放一次。
- #027 的 subject/manager/cross-department 签字贡献严格合计 10000 bp。#028 抢功转移和审计回拨各自净零且不改写 signed baseline；#056 从 claimed ledger 建立 report ledger，截功仍净零；#057 只签署合计 10000 bp 的版本。
- 跨部门证据不是装饰字段：portfolio 冻结独立 reviewer；其身份参与 #027 三方签名、#056 附件、#058 抄送、#060 创意来源、#067 岗位归属与 #134 shared metric 依赖消费。
- #058 只写 routed recipients，并把 `seen_count` 保持为 0；#055 才从两个 attention slots 中真实扣账并增加可见度。
- #063 的实线/虚线权重严格合计 100；#064 只有新旧上司双签且 successor 合法时才改变 future active manager，`historical_owner` 永远只读。
- #129 的晋升槽位上限为 1；#130 隐瞒 PIP 且试用失败会把责任写回 source manager；#131 在结果前锁定 exploration/commitment；#132 的 business stop 与 individual judgement 分账；#133 的学习消费与具名责任分账；#134 只写一个最终 owner。
- #068 只读取既有 B2 `zg361_b2_pip_state` 判断是否携带未结 PIP，不写任何 B2 字段；历史记录不占本期 quota。

最终 conservation 同时要求容量、注意力、晋升槽与 10000 bp 贡献账守恒，项目槽释放，项目对象 version 精确为 27、状态为 cancelled/stopped，汇报对象 version 精确为 7。该断言仍是静态脚本合同，不是 CK3 实机证据。

## 本地化与证据边界

简体中文和英文为日常开发文案。法、德、日、韩、波、俄、西文件使用英文结构占位，只证明 key 结构可加载，不是发布翻译。

本包没有启动 CK3，没有 parser 输出、paused snapshot、MCP、fixture 或生产实机证据。因此最高状态只能是 `static-ready`，不能标记 `fixture-live`、`production-live` 或 `complete`。正式集成后仍需中央调用点、游戏内玩家/AI 双路线和存读档实测。

当前生成运行时专测为 40 项，Python 参考模型专测为 38 项；两者都必须同时在普通模式与 `-O` 模式通过。测试数量不改变上述 readiness 边界。
