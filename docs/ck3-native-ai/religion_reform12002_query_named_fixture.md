# CK3 1.20.0.2 宗教改革专用 named-slot 单场景验收

状态：**static-ready named queue fixture**。本次仅闭合中央新增的
`permitted_executor_religion_reform12002` 实际准入，没有启动或访问 CK3。
完整库与原 12 场景双模式证据见 [caller fixture](religion-reform12002-query-caller-fixture.md)。

新 `religion_reform12002_query_named_test.cpp` 只读 include 冻结的 caller test，
将其原 `main` 重命名为 `FrozenReform12CaseMainNotExecuted`，**未调用该函数、未运行旧矩阵**。
新 main 只运行原有 `visible-create` backing 的一个现成场景，使用真实生产 provider 与序列化器。
在 submit 前将 `permitted_executor` 与旧 religion permit 清空，
仅将实际 callback 注册到改革专用 runtime field。
随后实际执行 `TrySubmit → owner ObservePumpDrain → Enter/Read/Finish → Wait/Reclaim → complete command_result`。
准入由现有生产 mailbox 判断，夹具没有替换 admission 或补结果 metadata。

MSVC `/O2 /W4 /WX`：**1 case / 7 checks GREEN**。
产物为 `Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-reform\query-named\attempt-002`；
`result.json` SHA-256：`fd76be53f3a2a00ae112d874c64fcd7302d8cdb7582a1af1d4f785844e4a6ed7`。
实际 wire 为该目录的 `wire/visible-create.json`，包含完整 `protocol_version:1`、
private/read-only/accepted/advertised metadata 与实际当前 draft create/cost/Doctrine selection。

构建复用前轮被冻结的 `/O2` 生产对象，不重新编译原改革库或调用旧 getter 矩阵。
仅编译新 test 及变化所需的 `main_thread_query_mailbox_v1.cpp`、`ck3_12002_query_mailbox.cpp`
和中央已修正的 `ck3_12002_religion_context.cpp`。对象来源、SHA 与完整源/defs 列表都在 receipt 中。
首轮在文件准备阶段发现旧 context 对象对应的源 SHA 已因中央 current-context 修复变化，
所以未执行编译或 case；保留为 stale cached input 的 harness 记录。
加入该真实变化所需的 context 增量编译后，唯一单场景验证 GREEN。

defs：

```text
XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1=1
XAR_REFORM_MAILBOX_STANDALONE_ADAPTER=1
```

第二个定义只供该离线 fixture 的 adapter stub，不能用于生产 DLL。
本场景证明 runtime named admission 和实际队列流转；没有调用 install-environment propagation，
生产 environment 设置由中央全 DLL 构建与接线证据覆盖。
真实 paused CK3 及 MCP 行为仍由 root 实机验收，当前不声称 live 或改革动作 OODA。
