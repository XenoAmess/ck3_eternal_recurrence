# 借款事件：原生选择命令的窄合法性边界

`machine_id: xenoamess-full-tower-eb9d2c1186`。本轮复用已有 1.20.0.4／build25734779 的静态迁移原件，EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。旧采集机器没有机器 ID，记为 `unknown`；本轮只读原件，不追认旧现场所属机器，也没有新 EXE 读取或 Game。

Resume60 的 loan07 已证明 bridge 检查当前实例、玩家及 native index 范围并提交队列，但未证明引擎如何处理禁用选项。现在从 native_schemes_events 共享的 `EVENT-ACTIONS-NATIVE-CLOSURE.json`，复用了 actual4 的 **Select primary validation slot `+0x30 = 0x29BDFC0`**。它与真正 execute 的 secondary `+8 = 0x29BDDE0` 是不同入口。

实际原件：`Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/shared-span-cache/new-029BDFC0-029BDFF8.bin`，56 B，SHA `5fda353d3b03118febc29c44364a49c6e848b29ee8f294ce3a5e2f66ba379ae3`。已完整解码，两个返回分支都在窗内。

| 当前入口的实际指令 | 证明范围 |
| --- | --- |
| `29BDFC4` 从 primary command `+0x20` 取 event ID，`ID <= 0` 返回 false | 这是该入口的 ID 条件，不是我方通用 opaque-handle 合同，也不是给别的接口新增正数守卫 |
| `29BDFCB..29BDFD9` 取得 GameData 并形成 `+0x34480` receiver | 具体 receiver 的内部存储语义由后续 callee 决定 |
| `29BDFE0 -> 29C56F0`，其返回值非空则 true，否则 false | 此 body 只向 callee 传 receiver 和 event ID；本轮未展开该 callee |
| 两条路径均 `RET` | 这是完整 56 B 的直接分支，不是只见首 pdata 段 |

这个 body 没有读取 command `+0x24` 的 choice，也没有直接读取物化 option 的 enabled／shown-as-unavailable 字段。**它不能证明禁用项可以执行**：`29C56F0`、通用 command 分派和真正的选项处理 `37BA990` 仍有各自范围；不能用一个外层 validator 缺少直接比较，推断完整引擎不存在最终检查。

选项执行顺序直接复用 OutcomeArchive 的[既有源码研究](event-select-execution-poststate-order-12004-2026-10-26.md)，不重新审采它的 execute body。Select 先运行嵌套命令及 manager 处理，再进入 `37BA990`。ledger_writer 的[后继86](event-removal-container-segments-12004.md)已用实际 batch02 原件闭合该正常索引路径的尾元素搬移、槽清理与 count 递减。因此 manager 实例退出、选项入口被调用、借款脚本写债及真正转款依然是不同事实；这里只证明静态顺序，没有观察一次真实贷款。

```mermaid
flowchart LR
  B[bridge当前实例/玩家/index范围] -->|已有source| V[primary validator读取event ID]
  V -->|实际CALL| L[29C56F0返回非空判定]
  L -. unknown: callee与最终合法性仍待闭 .-> E[actual execute]
  E -->|OA/ledger静态顺序| R[manager槽移除/count递减]
  R -->|OA静态顺序| O[37BA990选项入口]
  O -. unknown: 完整效果和可归因付款 .-> P[贷款双方钱包/债务/list后态]
```

后继只从实际 caller 定位 `29C56F0`：既有 runtime metadata 给出 `0x29C56F0..0x29C5776`／134 B；本轮未找到相同起点的共享 raw。新窗如需采集只交 sole b64 owner，不自行读 EXE，也不因研究进展启用任何贷款 flag。

本结果没有改变 cash21／LoanFinancingCodec 的字段，没有新增动作、守卫或回归；完整贷款资格、实际 offer、最终支付和到账继续未知，未到账资金 credit 为零，UNKNOWN 原动作不得重放。
