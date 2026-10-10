# 旧 mod 验收入口不可达代码清理（2026-10-10）

按通用存储策略 1.0.0 和公共验收入口永久规则，本批移除五个旧 runner `main` 中已经不可能执行的独立实机编排尾段：体验优化、重整河山、自动升级建筑、肃清曼荼罗伪信、牛来。

这些入口原有逻辑已穷尽两条路径：非 preflight 返回 2 并指向公共入口；preflight 调用原预检后返回 0。旧尾段仍包含分配场次、创建 profile、运行 cell 和写报告等已退役流程。清理仅删除第二个返回之后的死代码，保留原签名、CLI 参数、拒绝提示、预检及全部底层函数、产品 fixture、markers 和注册数据。当前及以后实机仍仅从 `tools/ck3_mod_acceptance.py` 进入。

现有公共产品 registry 仍引用旧 runner 的底层实现，因此没有整文件删除或重写旧业务合同。正式 staging、14 个 builder、现行冻结 runtime/native、活跃 prepared/state、发布记录及原始 GREEN/RED 证据均不属于本次代码变更。历史源码由本次父提交保留，按固定 Git commit 可恢复；没有重写 Git 历史。

候选只读验证：每个文件除被删 main 尾段外，全部 AST 节点及 main 前缀保持等同；五个候选均可 compile。复用现有 mock-provider 验收入口测试 10 项及 open_kaishek 静态调用边界测试 2 项，共 12 项通过；没有导入实机 runner、执行 CK3、访问桌面或重跑业务矩阵。该结果只证明本次代码退役等价，不授予任何产品功能 PASS。

外置候选与实际回执：`C:/workspace/ck3-upgrade-20261010/history-code-cleanup-readonly-candidate-01/`。代码候选由 Root 统一采纳后才成为仓库变更；子线程没有写 Main 或执行 Git mutation。本批没有回收数据文件，不把源码行数或 Git diff 大小冒充实际磁盘释放量。历史数据实际回收由独立磁盘 lane 记录，两个 lane 不重叠。

本记录在 2027-04-08 复核归纳；当前真实引用的旧 runner 底层实现由公共入口继续消费，不以文件年龄判定废弃。当前活跃外置输入的限期保护归其 owner 台账，本记录不自动延长保护。

## 第二批：主模组、终态与白绮入口

Root 已核候选来源及 gzip 精确往返 pins，并在无现场占用窗口采用。两批合计 837 行不可达代码；实际历史数据回收与永久记录见 [本轮清理结果](history-code-and-capture-cleanup-2026-10-10.md)。

第二批候选清理 `run_acceptance.py`、`run_terminal_acceptance.py`、`run_vivhite_acceptance.py` 中无条件 `return 2` 后的 560 行不可达实机编排；保留原 API、公共入口拒绝提示、CLI 参数、独立 preflight 和全部底层函数。源码 AST 对照确认 main 前缀和其他节点完全相同。旧 `validate_static.py` 与 open_kaishek 静态测试仍把死 main 的调度常量、旧 profile 编排和离线调用当作活跃合同，本批改为检查真实保留的 storage/report helpers、离线 preflight 及已退役入口的明确拒绝，不把死代码保留当作验收能力。

候选复用 5 项现有 legacy-entry CLI/mock 测试及 4 项 open_kaishek 静态边界测试，9 项通过；变动的 runner 静态断言块单独执行通过，5 个变更 Python 文件可 compile。原有真实 preflight 的离线调用顺序仍检查。首个候选静态块实际失败，原因是旧断言还要求死 main 中的 `outside process tree` 日志；仅移除此失效日志断言后通过，真正的 `create_process_via_windows_management` helper 合同仍保留。未导入实机 runner、启动游戏、重跑产品业务矩阵或重建 native/runtime。外置候选与回执位于 `C:/workspace/ck3-upgrade-20261010/history-code-cleanup-readonly-candidate-02/`，源码统一交 Root 采纳。本批数据删除量为 0，不声称磁盘释放收益；第一批及本批原 source pins 保留于各自薄回执和父 Git 提交。
