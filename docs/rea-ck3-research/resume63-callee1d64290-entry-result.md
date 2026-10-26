# resume63 首个有限 callee 查询：入口拒绝

`machine_id: xenoamess-full-tower-eb9d2c1186`，2026-10-26 UTC。本记录接续[框架方法与问题定义](resume63-framework-workflow.md)。本题 `0x1D64290..0x1D64376` 的230 B、反汇编、CFG与语义均为 **NOT_RUN**。

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

没有重试、绕过 guard、改旧回执或用普通 Jar 代替完整包。Root 已交 accounting/Host 在共享生产路径核对历史 completed 读取的合法修复；取得实际修复和重新资格后，用 fresh 卡、standing 与新 run_id 再执行。原900秒执行窗到 `2026-10-26T15:02:08.004Z`，不自动续期。其间仍可复用已持原件和推进 Java 迁移。
