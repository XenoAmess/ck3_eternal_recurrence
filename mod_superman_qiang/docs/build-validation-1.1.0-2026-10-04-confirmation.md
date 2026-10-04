# 1.1.0 查询确认窗修复的局部构建门

正常生产存档 R21 的右键查询仍弹出空白确认窗。唯一运行改动是在交互定义加入 `needs_confirmation = { always = no }`；生成器和原版依据已由执行者冻结。[原版依据与运行修复收据](build-evidence-1.1.0-2026-10-04-confirmation-A0001/runtime-fix-report.json) 及 [vanilla 来源](build-evidence-1.1.0-2026-10-04-confirmation-A0001/runtime-fix-vanilla-sources.json) 保留当时字节。

候选 `superman-qiang-1.1.0-live-A0004` 的 22 文件相对 A0003 逐一核对，只有交互新增这一行，另外 21 文件逐字节不变。独立静态合同要求关闭确认窗；删除该字段或改为 `always = yes` 的两个新增负例均返回 RED。原先 [L0 A0001 报告](build-report-1.1.0-2026-10-04-L0-A0001.json) 是此次确认窗修复前的候选证据，保持原样，本报告追加新门而不覆盖旧事实。

本次实际通过：20 生成文件逐字节检查、静态验证、现有 8 项 runtime 测试（73 个独立负例）、5 项发布测试、唯一受影响交互文件的实际 JAR parse/roundTrip（零 diagnostics），以及候选 build/manifest verify。没有重复健康四叶语法检查或健康 20 案例实机矩阵。parser 只认证文本语法；R22 正常界面仍须验证一次点击直接通知和查询只读。

候选 staging 为 `C:\ck3-superman-qiang-1.1.0-20261004\live-candidate-A0004\mod_superman_qiang`，manifest 基线提交为 `ff5b112d8bde46948538678b58705ad88b69e406`，`git_tag=null`。交互/生成器的唯一未提交改动和对应静态回归源码已另存精确快照；此候选不能冒充最终干净源码或正式 tag。

- manifest SHA-256：`92dffc1e2dd66bc5a72dfa797632b320b5b6d8bf8a43ce4712a203b4e684fda5`。
- ZIP SHA-256：`bd85845dbc7c9ddb19749c14f6a4f20576d488619d7c7e035dab874f68b29cf4`。
- 外置 closure SHA-256：`bcb3d75b31b158389a4aa4a22a7a0c34d6b4087982fc563de290de9079f5611b`。

[完整局部门报告](build-report-1.1.0-2026-10-04-confirmation-A0001.json) 与 `build-evidence-1.1.0-2026-10-04-confirmation-A0001/` 保存实际命令、原始 stdout/stderr、唯一 parser corpus、22 文件 manifest、21 文件不变证明及源码快照。候选已交给 acceptance 进行 R22；本报告不宣称原生界面通过或外部发布完成。
