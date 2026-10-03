# R0002 产品核心核验候选归档

本目录保存核验时冻结的 [JSON 报告](report.json) 与 [Markdown 报告](report.md)，原字节未修改。结论是 `PRODUCT_CORE_PASS_WITH_FIXTURE_DIAGNOSTIC`；`overall_clean_acceptance=false`、`release_ready=false`。报告末尾“未写入仓库”及“后继夹具尚无 engine GREEN”描述的是候选生成时刻，入库动作没有改写这份历史记录。

父任务在真实决议界面选择 Rossano 转城市，原生人物状态证明同日暂停时金币 `1246 → 846`，支付 400；随后原生日志状态断言证明 Rossano 是玩家直辖城市，未选中的首都仍为城堡。另有六种生产 effect 与四种负路径的十项状态 PASS。effect 矩阵与这一次真实 GUI 执行分别记证据。

整轮唯一脚本错误来自外置夹具 `events/chtt_events.txt:17` 对已经为城堡的地产再次设置城堡类型。不能把这轮记录标为无错误实机验收，也不能以产品状态 PASS 宣称发布完成。R0003 的保存重载、修正后无错误矩阵与过程清理仍由父任务在另一次证据中核验。

[证据索引](evidence-index.json) 给出保留快照根、逐文件 size 与 SHA-256；报告中的相对 evidence 路径以外置 `C:/workspace/two-mod-maintenance-20261003/holding-R0002-verification-candidate/` 为根。本目录仅归档报告与索引；七份原生日志、状态快照、inbox 脚本和生产 manifest 永久保留在该外置目录。索引的 `source` 是最初运行来源，复核时采用保留快照，避免后续运行现场改变原文件。

夹具的最小修复、生成器同步和逐文件一致验证见 [修复说明](../fixture-initialization-fix-2026-10-03.md)。此前 R0001／R0002 的早期边界记录与旧静态报告均未覆盖。

当前范围更正：[只进行简体中文实机；其他八语只检查格式](../localization-acceptance-policy-2026-10-03.md)。同目录冻结report里的多语pending／未来提示是历史计划，已撤销；原字节和SHA不改，也不把未执行外语步骤记为PASS。
