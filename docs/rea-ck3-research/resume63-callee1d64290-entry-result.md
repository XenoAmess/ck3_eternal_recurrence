# resume63 首个有限 callee 查询：入口拒绝

`machine_id: xenoamess-full-tower-eb9d2c1186`，2026-10-26 UTC。本记录接续[框架方法与问题定义](resume63-framework-workflow.md)。**原 Shared attempt 在 child 前拒绝，研究状态为 NOT_RUN**；下述失败保持不变。后继 Root 授权的官方 direct service 已另取230 B并闭场，见本页末段。

新容量实际准入后，重新绑定当前 EXE、11 个 runtime/工具/source/delivery 原件，并生成本轮 fresh standing、ENTRY。现有 `SourceGraphCommandSpecProducer` 实际 exit 0 生成 BINDING/SPEC/INVOCATION；这只完成机械入口元数据生产。

首个 `SharedOwnedCommand` 实际执行在业务 child 启动前拒绝，outer 4.447 秒、exit 1：

```text
File reference changed: .../STORAGE-SHORT-COMMIT-HEAD-V1.json
validateAttemptFinancial → readAttemptLease
→ verifyCompletedAccounting → verifiedCompletedReceipt
→ SharedOwnedCommand.verifyPackagedSource → authorize
```

历史 S26 完整包的 completed accounting reader 仍要求旧 financial 中 mutable HEAD 的 exact pin；新容量 CAS 后当前 HEAD 已变。`observeCurrent=false` 分支也会在 `ControlBuild.java:1618` 遍历这些 FileRef 并验证。这个真实失败发生在原 Shared 入口，没有启动 Capstone 或 REA/Rizin，没有新保留的230 B、terminal或业务 Job；不能标为 Job0 或原生研究通过。fresh RAM 为40988553216 B，commit 可用128286130176 B，资源门槛通过。

失败原件为 [PRE-CHILD-FAILURE01.json](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee1d64290-01/PRE-CHILD-FAILURE01.json>)，4366 B、SHA `bb20b413bd6c3a22b851d6e6a2cdf3c50e47d6ee84017ce7b4884f7837b56b33`；它固定 actual argv、fresh binding/spec、RAM、stdout/stderr、退出与来源引用。M5 独立读回了同一异常栈，并保留 callee 缺口。

没有重放该 Shared attempt、改旧回执或用普通 Jar 代替完整包。Root 已交 accounting/Host 修共享生产路径；该路径后续仍须实际修复并重新资格。原900秒执行窗到 `2026-10-26T15:02:08.004Z`，不自动续期。

## 前向追加：官方服务实际完成

Root 在上述失败后明确授权现有官方共享服务的正常 direct 入口；新 [DIRECT-ROUTE-PLAN01.json](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee1d64290-01/DIRECT-ROUTE-PLAN01.json>) 固定此路由。使用已装 `createReverseEngineeringService`、原装 Windows owned-process 与单次有限命令，没有修改旧 S26、REA 或 runner。Capstone 独立读当前 PE/RF230 B，REA/Rizin 新返回48条、局部5块6边；M5 独立复核原件、相对目标和数据流通过。

Rizin exit0、未截断，原装 provider close 在14:56:50.786Z完成，服务 close 无错误；own PID 在14:59:32.236Z读回不存在。case在15:01:16.579Z、原截止前闭场。官方查询结果与调用来源见 [CASE-RECEIPT01.json](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee1d64290-01/CASE-RECEIPT01.json>) 和 [CASE-CLOSED01.json](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee1d64290-01/CASE-CLOSED01.json>)；exact bytes/SHA 见 [sources.json](sources.json)。

这仅证明两decoder一致、正常局部控制流与原始低byte返回。六direct/两virtual call的语义、副作用、异常及领域含义仍未知。外层exec exit0不等于Job0，其峰值与Job0均为 NOT_MEASURED，Shared资格为 NOT_GRANTED。两题完整范围和成本另见[实验记录](experiments.md#resume63两次新增有限查询)。旧版记录保留于提交 `e735f2a0ed56e666e5f5d0977a7e532ff861f23c`，没有回填旧哈希或把旧失败改绿。
