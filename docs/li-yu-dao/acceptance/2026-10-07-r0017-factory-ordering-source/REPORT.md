# R0017 前的 factory 顺序候选：仅源码验证

R0016 已正常关闭并释放屏幕独占。七个政治头衔的冷读回完整 AST 均等于 R0015 的正式立教 B5；其中五个头衔的继承列表仍不同于原始 0240。冷载没有消除该变化，因此 I3b 的政治完整性仍未通过。原始失败不改写，见 [R0016 归档](../2026-10-07-r0016-9208b46/REPORT.md)。

本次只改变宗教头衔 factory 的顺序：先设置两个所有权标记与四项属性，再将新头衔关联至 Faith，随后授予持有人并 resolve，最后生成家徽、添加宗教头衔继承法并执行已有的 realm-law 清理。该候选利用已确认的 1.20.0.3 setter 路径：头衔尚无有效持有人时，不进入持有人 realm-law 维护；后续 resolve 的实际影响仍未知。它不是已证明的业务修复。

只应用两个 authored template 和针对性测试；生成文件由 `mod_li_yu_dao/tools/gen_runtime.py` 重建。生成结果与审阅候选精确一致。测试仍保护原 factory 的全部 effect 值，仅将明确声明的顺序变换归一化后比较冻结的 AST 指纹，同时单独断言新顺序。实机的完整政治 AST 合同没有降低。

ROOT 实际验证：12 项 factory-law 测试、70 文件静态校验及两次可复现 release 构建均退出 0。新业务树的双构建 manifest SHA-256 为 `786b2e7079406386658bbb805eaa7651f6ce8dc8c0f8dc27f3bd45532936b083`，ZIP SHA-256 为 `d20100b462e2fe4520a29154ef06b0c5554540f8988a322f3b66e97bd11734d1`。这些结果只证明源码与构建检查；native 编译、正式批准、政治保持性、冷载、C3 和 I4 仍待执行。

外置原件永久保留于 `C:/workspace/ck3_lyd_runtime_20261004/`：

- `r15-factory-head-before-holder-candidate-20261007-002/UNVALIDATED-ORDERING.incremental.patch`，6481 字节，SHA `134914236784622f51582ec9ee0a256e0347aea7be8b3fd1d3c646eec4cd41cf`。
- `r17-root-factory-ordering-apply-20261007-001/RESULT.actual.json`，记录 source-only 应用及生成文件未由 patch 修改。
- `r17-root-factory-ordering-source-checks-20261007-001/`，保存精确 argv、SOURCE、三份实际 RESULT 与 stdout/stderr。
- `r16-actual-closed-boundary-20261007-001/PREVIOUS-BOUNDARY.actual.json`，3082 字节，SHA `b09f54dcac006d9dd355b567a42dc8bc811b0b0be2f6fcd5db85b5a72326a1b2`，为下一轮实际进程及 lease 闭合依据。

下一轮从原始 0240 启动，先保存同帧冷基线并核对七个政治 AST，再走正式批准链；成功后的独立保存与冷载都必须保持政治头衔及其他受保护状态。不能恢复旧继承列表来补过验收。整个产品保持 **NOT_GREEN**，未发布 Workshop。
