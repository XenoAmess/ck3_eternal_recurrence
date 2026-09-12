# 项目交付状态投影

本目录把已经存在的 P1 gate、P2 source/媒体节点、T1 blocker、T2 同步事务和 RED artifact 投影成一个小型机器入口。它不增加验收门，也不替代原始 artifact、Operator live status、Git 或专题文档。

权威分工如下：

- [`current-state.source.json`](current-state.source.json) 是稳定工作包状态的唯一生成输入；只在工作包收口时更新。
- [`current-state.json`](current-state.json) 是人和程序默认读取的现行投影。
- [`p2-stage-ledger.json`](../phase2-promo/p2-stage-ledger.json) 分开记录 source `4` 项、raw capture `8` 项、一次共享 intake，以及两个 cut 各自的 source review、candidate、自动审计、1× 人审、export 和 publication。
- [`red-indexes/`](red-indexes/) 只保存小于 10 KiB 的 RED 索引；完整现场继续保留在索引所引用的内容寻址 artifact 中。
- [`work-package-resource.template.json`](work-package-resource.template.json) 是并行工作包资源声明模板；[`work-packages/`](work-packages/) 保存独立声明，不写日报或周报。

生成器为 [`tools/project_delivery_state.py`](../../tools/project_delivery_state.py)。在仓库根目录运行：

```powershell
py tools/project_delivery_state.py render --verify-artifacts
py -m unittest tools.test_project_delivery_state
py -O -m unittest tools.test_project_delivery_state
py tools/project_delivery_state.py validate-package docs/project-state/work-packages/<package>.json
```

`--verify-artifacts` 会按 `base + locator + bytes + sha256` 验证本机已有的冻结 artifact。`workspace_root` locator 从包含根仓 checkout 和 `_runtime` 的工作区根解析，不能写死 Windows 用户名、沙箱账号或某次 CK3 pipe。另一台机器如果尚未复制历史 runtime，可省略该参数生成相同投影；已提交的 SHA 和长度仍不可改写。

## 稳定状态与 live 状态

Git 中只保存完成工作包的稳定投影。下面三类瞬时状态不写进 Git：

- 当前 CK3 PID、当前轮次、pipe 和 connection generation 从 `operator_get_status` 读取；
- 当前 live RED 从同一 Operator inventory 读取；
- Git 当前 HEAD、upstream 和远端头从 `git status --branch --porcelain=v2` 与 `git ls-remote` 读取。

`current-state.json` 中的 `*_last_completed_transaction` 是上一个已完成并同步的事务，不冒充读取时的实时仓库状态。投影提交本身不会制造必须把自身 commit hash 写回自身的循环。

## 三轴 RED 结果

每个新 RED index 必须同时发布：

| 字段 | 允许值 | 含义 |
|---|---|---|
| `business_result` | `GREEN / RED / NOT_EVALUATED` | 产品或目标业务后置是否成立 |
| `harness_result` | `GREEN / RED` | runner、consumer、合同和证据装配是否正确 |
| `lifecycle_result` | `GREEN / RED / ACTIVE` | CK3、bridge、worker 和 cleanup 是否受管 |

总 `result` 仍为 `RED`，分类不能降级失败。Python consumer 在输入前拒绝时应写 `business_result=NOT_EVALUATED / harness_result=RED`，不能从总 RED 推导 `product_result=RED`。索引还固定记录 `red_class`、`blocking_scope`、最后成功阶段、输入是否尝试、同帧 retry 资格、绝对游戏日截止、最小 diff 和完整 detail 引用。

首个迁移样本 [`r506-source-event-scalar-scope-invalid.json`](red-indexes/r506-source-event-scalar-scope-invalid.json) 把旧 553 KiB detail 收敛为约 2.2 KiB 索引。它保留原 RED，明确该帧业务未评估、harness 失败、生命周期当时仍 ACTIVE，并回链后来 R508 同进程恢复与 cleanup；它不是现行 blocker。

## P2 ledger 更新规则

P2 的节点只从各自 receipt 提升：

1. source lineage 和 raw capture 使用不同分母，前者不能充当 footage；
2. 八段原片完成后只执行一次共享 intake；
3. 两个 cut 的 source review、candidate、自动审计、1× 人审、export 和 publication 分别记录；
4. 一个 cut 的 GREEN 不能提升另一个 cut；
5. P2 状态变化不能重开已经签收的 P1 `9/9`。

状态只允许 `GREEN / PENDING / RED`。`RED` 必须引用 compact RED index；`PENDING` 可以回链历史 RED，但不得因此冒充当前产品 RED。

## 并行写入

工作包开始前复制资源声明模板，填写精确 `reads`、`writes`、CK3/Operator/product/bridge/T2 布尔字段和阻塞 gate。daily/weekly 的 `report_writers` 固定为 `coordinator`；支线只交独立 package receipt 或资源声明，由协调者汇总。这是冲突信息，不是新的调度门或安全门。

当前 schema 是 `1`。字段或语义发生不兼容变化时递增 schema 并立即同步 `open_kaishek`；仅增加新的稳定状态数据时更新 source、重生成投影并按既有 T2 规则判断兼容影响。
