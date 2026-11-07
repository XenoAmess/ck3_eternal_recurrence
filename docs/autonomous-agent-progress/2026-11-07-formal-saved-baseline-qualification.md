# 正式 Saved 基线：类型与独立 DATA 资格补齐

这是对[先前源码审阅切点](2026-11-07-saved-original-recovery-software.md)的后继记录。先前六 TU 的编译失败、46 个部分产物和当时组合 RUN 未开始的事实保留；本次没有为使编译通过而删除检查、改写范围外源码或覆盖实际运行版本。

## 明确的有限编译单元

只编译七个既有、未改动的正式文件：application 的 `SavedAttachmentSourceStore`，以及 local-service 的 `RootApplicationAssembly`、`RootApplicationSession`、`NativeDriverObservationProducer`、`RootJavaSavedBootstrap`、`RootOrdinaryRuntimeAssembly`、`RootLoadedSavedResumeMain250`。前四个补齐已声明的 source-result／SavedLive 类型依赖，后三个是待闭合的 P101 正式 service 文件。

原失败中完整的 `SavedCheckpointMaterialEvidence`1／`ContinuityBatchJournal`20／`OrdinaryCycleTransitions`25 个 class，按确切源码、原字节、SourceFile 与双向 nests 复用。没有隐式新增 support 源或编译整棵 SDK。

本次七 TU 首次实际 exit0，产出 88 个 class，耗时 14.4602343 秒；与原 46 个 class 构成 134 个 class 的软件组合。目标 API 的实际描述符、完整 nests 和 `Core.SavedLiveToken` 的 private 构造器已核对。资源于 `2026-11-07T04:48:06.241932Z` 释放。

## 实际组合验证

随后复用原两个 DATA 测试 class，不重编测试源码，对新正式组合仅运行原两个方法。实际取得 2P／0E／0F／0skip，exit0／contract true，耗时 5.3743913 秒，资源于 `2026-11-07T04:56:08.692151Z` 释放。

验证范围仍只是不可变原 Driver／marker 的 episode 与新 transport session 身份，以及严格七字段 schema 路由。它没有创建或执行 Root／SavedLive 图，没有 Native 查询、动作派发、当前 head47 准入或 Game 操作。类型和 DATA 组合通过，不等于这些未运行路径的行为验收，也不等于实际部署。

本次补齐的是独立软件资格。冻结 head47 的 reserved child1、原 UNKNOWN、旧命令和空 child／无玩法写入门保持；P100 被 provider 拒绝的链没有重投、改写或换岗继续。**自动游玩仍未恢复，整体性能目标没有据此通过。**

## 精确导航

机器前缀：`D:/ck3-state/resume91-java-delivery/ordinary-p0-20261105/loaded-saved-original-recovery101/`。

- `FORMAL-BASELINE-SEVEN-TU-READY02.json`：11218 B，SHA-256 `1399a990d10166ba1c6f3fbd4930d2383563e2f17bfdca1dea2f7d0da0f7a72f`。
- `OWNER-FORMAL-BASELINE-DELIVERY02.json`：3321 B，SHA-256 `f13a3556cc7ca305f959a300b06f2741f3c058eb036ac8c35db651149876872b`。包含两次实际 phase、close、类型／API／nests 与旧 46 个 class 复用原件的 pin。
- `native-formal-baseline02/SEVEN-SOURCE-OUTPUT-NESTS-AND-DECLARED-APIS.json`：2887 B，SHA-256 `7661e38073f36158839f0611ef10dee4ecf830c057eca3a0abff5b36d3e0f057`。
- 本次 JUnit XML：81854 B，SHA-256 `7896864b56f26ca732fb31f6a7bee4f44550f7cfd8f81bc7c80563ee29c09548`。

七个源及原 46 个 class 的独立核验：`D:/ck3-state/resume91-root/loaded-saved-original-recovery-independent101/FORMAL-SEVEN-BASELINE-SIGNATURES-AND-EXACT-REUSE46-07.json`，28394 B，SHA-256 `563c3bb580e471148fa1035c4b9689b0559b3c04f9d75f94f6f081e0bbe514eb`。
