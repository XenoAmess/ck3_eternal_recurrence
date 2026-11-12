# 私有 Snapshot 解析树编码（2026-11-13）

post68唯一封闭采样中，`FullJsonTree.encode` 的一个调用组有44个样本：`DriverStateSnapshot.bytes → parsedEntry → decodeParsedComplete → decodeComplete → Loader/Reader`。这些私有子树刚由严格解析器创建，原编码又完整遍历验证再序列化；44是该组样本数，不是CPU时间或44个组。

本单元只将私有 `parsedValue`／`parsedEntry` 的首次编码改为专用私有编码器。节点在 owned raw 严格解析后内持，类型、深度已验证，verifier在完整值构造后才取得树。新 mapper 放在既有 Complete 的私有 static 字段，复制当前 FullJson factory 配置及默认写行为；DecimalTokenNode仍执行原 `writeNumber(token)`，保任意数词法。原 lease合法性／256MiB输出界与IOException包装保持。

`FullJsonTree`源码和公开encoder完全不改；公开Value／HistoryEntry／Complete构造器、Complete.encode、CONSTRUCTION一次性身份、provenStable及surrogate fallback原体保留。不输出公有trustedAST入口，不缓存树或业务结果。新增私字段使该单元须正常fullreload，软件通过不授HCR。

## 有限验证及来源

common单TU仍为原9类；独立测试内嵌完整10911B旧Snapshot，机械逆恢复与冻结原件exact。6项差分首次全P，覆盖slots／orderedhistory／大整数与decimal lexeme／Unicode与旧surrogate域／语法及UTF8错误先序／嵌套verifier、raw及row变更、失败后续与公有伪index拒绝。未分配256MiB+1数组，原上界保留为源码义务，不声称实测整个大尺寸域。

formalBASE与actual整字节同10911／0307…、candidate同12444／69a835…；18个直接及必要小闭包成员的实际first-origin class字节及三个Jackson整jar来源相同，因此合法共用这次1TU／whole6，不重复formal JVM。未外推formal Root平台。

原件在 `F/snapshot-private69-compile02`、`F/snapshot-private69-whole6-junit01` 与 `COMMON-ACTUAL-FORMAL-DEP-REUSE01.json`（34331B／`a587d5d8892d8b619e1c5ba29e0f185d32160188bd97a4061612d59f96c0429e`）。F为 `D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01`。单元汇总 `SOURCE69-WHOLE6-OLD9-API-AND-155JVM-COST01.json`（15588B／`f1c355d82120089f76cf375782f967decceed19502b79e22af1e15f5d28e46dd`）。首模板recorder绑定错误是0JVM前置拒，未改述为源码编译失败。

两个模型完整响应保留：首答非法访问FullJsonTree.JSON(private)且缺IO import；唯一纠错只补import，仍未实现合法私writer。最终部分采用importIO、两个私有caller替换及helper序列化／lease／IO小体；合法mapper、配置、private引用替换、原leasevalidity guard与注释由owner完成。静态缺陷不是实际javac RED；DecimalToken的writeNumber首述正确，owner曾误记writeRawValue后已纠正。

本单元仅软件候选，当前Source68正常业务不为它单独再支付handoff成本。待更大的提前budget-renew／历史prefix单元或具体必要P0组成一致cohort，再由运行岗择实际边界；未授装载、live分支、ROI或10秒／新增确认保存日目标。

后到实际：该单元已与71作为五叶一致cohort实际normalfullreload，2026-11-12T19:38:04.2614466Z同host／同Game恢复LOOP；后续首C66真实结算和71提前续批正分支另见[具名采用及完整窗口](2026-11-13-post-life-early-batch-renewal.md)。这是后到事实，保留上文首次发表时尚未采用的切点；无单叶因果／新增SAVE／10秒授信。
