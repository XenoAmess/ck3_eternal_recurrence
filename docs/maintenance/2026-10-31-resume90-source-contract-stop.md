# resume90 明确资料合同错误的规划终态

machine_id: `xenoamess-full-tower-eb9d2c1186`。观察时间：2026-10-30T17:46Z。执行者：Root；所有编测输出位于 `D:/ck3-state/resume90-root/source-contract-stop`。本包未修改 S/MB，未发游戏动作、未调用本地模型。

## 问题与结果

`SessionController` 在 planning scope 或领域完成器报告 Published 后，原来立即丢弃本轮计划并重新规划。这对需要刷新帧的动作和暂时缺少输入仍然必要，但也掩盖已经明确拒绝资料的结果。Family 的解码错误又共用 INCOMPLETE_PRODUCTION_CHAIN；经可选 M5 收集器时，其停止原因还会被字符串化成一般私有资料缺失。

本包增加 `SOURCE_CONTRACT_REJECTED`：Family 已有 IllegalArgumentException 捕获产生该类型；MilitaryPeacetimeRuntime 与 M5 用受控异常保留这个类型；Controller 在两处 Published 分支先识别此明确原因，返回 PLANNER_STOPPED。其他停止原因仍按原有发布/重新观察路径处理。未增加重试次数、启动校验或提交重放。

原生查询暂时 Unavailable 的实际 reason 同步保留在 MissingInput 文本中，普通缺失继续返回 Wait。公开 PlanningWire 使用既有 enum name 编解码；新增值已验证往返。

## 实际验证与边界

- 初版三生产叶严格 javac 0；两完整测试类 77 个方法，75P/2F/0 skipped，包含 scope/domain 两条明确错误停止、普通缺失继续重新观察的三个新方法。
- 两个失败在完全未修改的原源码及原测试上单独复现为 2F：SessionControllerRegressionTest#lateObservationCannotEnqueueActualJournalDataUnderAnExtendedDeadline（no captured incident expected），FamilyRecordedBetrothalFulfillmentTest#fixedPairAdultLegalityAndUnknownReadsRetainTheirExistingGates（末段原用例期望 Replace 而得到 Stop）。保留 inherited-original-* 原始诊断；不将完整类报告为全绿。
- 初次红对照 4 方法为 1P/3F。Controller/Family 逻辑仍为旧版，仅为表达新事件加上测试所需 enum 常量；它不是不加 enum 的原封旧二进制比较。Family 当时在原长用例中添加断言，最终改为独立方法。
- 最终五生产叶、两测试源及既有 OperatorRebindConsumerTest 帮助源严格编译：followon02 exit0/4.431s；Family 解码类型错误与 Family→M5 收集器→PlanningWire 两个新方法通过。同组暂缺资料测试因错误期望 Stop 得到 Wait 而失败；修正测试期望后 followon03 严格编译 exit0/4.199s，仅重跑该失败方法 1P/1.557s，未重跑两个已绿方法。
- 保留最初 followon 编译失败（异常字段序列化 warning、缺 Family 导入）和修正记录。最终异常仅保存 message，再构造强类型 Stop；使用显式全名调用。

这些回归使用仓库现有软件 fixture 与显式收集器端口；不证明真实 Native READ 归属、真实磁盘发布或 CK3 新动作。最终五叶组合未重新跑完前述 77 方法，也未做全 Maven/CI；后继生产 owner 负责增量集成。新增真实游戏日、SAVE、RESTORE 均为 0。本包不作为 worker101 历史恢复修复的前置。

## 文件与保留

SOURCE.json 保存七个源码前像；SOURCE.patch 仅含五生产叶与两测试叶。DELIVERY.json 另列本报告，供唯一 Java writer 按清单正常发布。编译命令、耗时与退出码在同目录各 *.json，JUnit 原始 XML 在对应 *-reports 目录。当前问题闭合及生产采用前保留；2026-11-07 复核，小型源码/日志可替代后不保留派生 classes。
