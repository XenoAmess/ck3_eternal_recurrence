# 旧 mod 验收入口不可达代码清理（2026-10-10）

按通用存储策略 1.0.0 和公共验收入口永久规则，本批移除五个旧 runner `main` 中已经不可能执行的独立实机编排尾段：体验优化、重整河山、自动升级建筑、肃清曼荼罗伪信、牛来。

这些入口原有逻辑已穷尽两条路径：非 preflight 返回 2 并指向公共入口；preflight 调用原预检后返回 0。旧尾段仍包含分配场次、创建 profile、运行 cell 和写报告等已退役流程。清理仅删除第二个返回之后的死代码，保留原签名、CLI 参数、拒绝提示、预检及全部底层函数、产品 fixture、markers 和注册数据。当前及以后实机仍仅从 `tools/ck3_mod_acceptance.py` 进入。

现有公共产品 registry 仍引用旧 runner 的底层实现，因此没有整文件删除或重写旧业务合同。正式 staging、14 个 builder、现行冻结 runtime/native、活跃 prepared/state、发布记录及原始 GREEN/RED 证据均不属于本次代码变更。历史源码由本次父提交保留，按固定 Git commit 可恢复；没有重写 Git 历史。

候选只读验证：每个文件除被删 main 尾段外，全部 AST 节点及 main 前缀保持等同；五个候选均可 compile。复用现有 mock-provider 验收入口测试 10 项及 open_kaishek 静态调用边界测试 2 项，共 12 项通过；没有导入实机 runner、执行 CK3、访问桌面或重跑业务矩阵。该结果只证明本次代码退役等价，不授予任何产品功能 PASS。

外置候选与实际回执：`C:/workspace/ck3-upgrade-20261010/history-code-cleanup-readonly-candidate-01/`。代码候选由 Root 统一采纳后才成为仓库变更；子线程没有写 Main 或执行 Git mutation。本批没有回收数据文件，不把源码行数或 Git diff 大小冒充实际磁盘释放量。历史数据实际回收由独立磁盘 lane 记录，两个 lane 不重叠。

本记录在 2027-04-08 复核归纳；当前真实引用的旧 runner 底层实现由公共入口继续消费，不以文件年龄判定废弃。当前活跃外置输入的限期保护归其 owner 台账，本记录不自动延长保护。
