# 原 SavedEntry 的 episode 身份与显式恢复路由

本单元只交付通用 Entry／身份／schema 软件。当前冻结 head47 含 reserved child1，原 UNKNOWN 与空 child／无玩法写入门保留；本次源码发表不授运行准入、只读查询、动作重放或新增保存日，也不继续 P100 已被 provider 拒绝的诊断链。

## 改动

新增严格七字段 schema `xar.java-loaded-saved-original-recovery-request/v1`，显式选择既有同 Game 恢复 API。原 retained、preentry 与 passive 三种 schema 保持各自原路径，不按 marker 是否存在隐式降级。

原 SavedEntry 的共同来源校验与旧 retained 的“动作历史必须为空”职责分开：旧 retained 仍强制空动作历史；新路由只取得共同来源 DATA，动作历史仍须通过后续既有实际恢复验证。它不会取得无写入证明或绕过 reserved child 门。

episode 身份由 marker、原完整 Driver 的长度／SHA、baseline、opening、Game 与 actor 共同绑定；原 episode 可以与新 transport session 不同。新路由禁止退回初始 Entry。真实接管成功后才在原 custody 合同下释放 preparation，再进入循环；旧三个模式的 custody 时序保持。

四个正式源码文件仅移植已审阅的 28 处改动。每处均可逐字节逆回正式前像；范围外已有正式源码保留，没有整件覆盖实际运行版本。

## 软件验证与限制

独立实际变体由 05 新编 Assembly／CLI 的 9 个 class，与 04 源码未变且完整的 Batch20／Bootstrap9 组合为 38 个 class。04 的首次编译 exit1、29 个部分产物与后继修正分别保留；后继通过不改写原失败。

两个独立 DATA 方法在同一次运行中取得 2P／0E／0F／0skip，全部编测资源真实释放。测试只使用冻结的原 Driver／marker 身份与严格 header DATA，验证 episode 与 transport session 分离、错误身份／hash 拒绝、旧三模式和新 schema 的 exact 字段门；没有私有 issuer、custody 或实际恢复 fixture。

**正式整件的组合类型验证尚未闭合。** 最小六 TU 尝试在既有正式范围外体遇到缺失的 D 二进制 API：`SavedAttachmentSourceStore.RequalifiedConfirmed.requireRetainedResult(Session)` 与 `RootApplicationAssembly.Core.promoteSavedLive(RootApplicationSession)`。后者又引用既有正式 `Core.SavedLiveToken`、`RootApplicationSession.bindSavedLiveToken`、`NativeDriverObservationProducer.activateSavedLive`；有限 D 变体没有匹配实现。原六 TU 编译失败、46 个部分产物及组合 RUN 未开始均保留。没有为此删除旧检查、替换范围外源码或扩大 SDK 编译。

因此，本次正式交付是源码审阅通过、独立实际变体软件与 DATA 通过；不声称正式整件已编译通过或已装载。正式源码既有 SavedLive／source-result 二进制基线的资格债独立保存，不能借实际变体的绿色结果替代。

## 精确交付导航

机器目录前缀：`D:/ck3-state/resume91-java-delivery/ordinary-p0-20261105/loaded-saved-original-recovery101/`。

- `OWNER-SOFTWARE-DELIVERY05.json`：8245 B，SHA-256 `e25d1e7344d2f758cf504233ed643c755e97dff460569f1270b77f34c93ea701`。
- `SOURCE-READY-FORMAL01.json`：7485 B，SHA-256 `a88840cb05cdb6adffdfc4a38ed9ffd1052798fcec3bb96860e085a89f61bd61`。
- `FORMAL-DEPENDENCY-DEBT-PLAN01.json`：4348 B，SHA-256 `e1bfa400e9bd150cc63115789cd96783d67a0dba40780017b68a0984a85b58bf`。
- `FORMAL01-ACTUAL-RED46-AND-BOUNDED-SAVEDLIVE-ABI-FRONTIER01.json`：6539 B，SHA-256 `208948328b61e569aabc8e16622b447f0d2f5caa28728bfa666d7b51a737e547`。

源码独审：`D:/ck3-state/resume91-root/loaded-saved-original-recovery-independent101/FORMAL01-28-OWNED-RAW-AND-PRESERVED-PRIOR-OUTSIDE05.json`，22619 B，SHA-256 `9c9ffe5e8ed0a7e6970137175cbf6bf0bfc047cc3c3214714728ed941e23b90d`。
