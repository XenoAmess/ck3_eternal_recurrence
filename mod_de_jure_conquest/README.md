# 公国／王国／帝国法理征服（XenoAmess维护版）

独立维护目录。上游为白绮的 [Workshop 3600021457](https://steamcommunity.com/sharedfiles/filedetails/?id=3600021457)。维护版物品为 `3812510217`；后续更新仅针对维护版，不得更新上游物品。

当前状态（2026-10-03）：**1.0.0已公开发布至[新维护版Workshop物品 3812510217](https://steamcommunity.com/sharedfiles/filedetails/?id=3812510217)**。CK3 1.20.0.3中文实机验收、正式构建、完整更新说明匿名回读、中文媒体及全新订阅缓存复核通过；Steam已恢复离线。**只实机验收简体中文，其他八语仅格式检查。** 详细结果和已知限制见[正式发布报告](docs/release-1.0.0-2026-10-03/README.md)。历史外语实机和失败attempt仅保留为诊断证据，不作为中文签核。

文档入口：

- [功能分析](docs/functional-analysis.md)
- [来源与环境冻结](docs/upstream.md)
- [适配计划](docs/adaptation-plan.md)
- [测试计划](docs/test-plan.md)
- [当前测试报告](docs/test-report.md)
- [简中最终验收与诊断边界](docs/cn-live-acceptance-2026-10-03.md)
- [发布流程](docs/release-plan.md)
- [源码适配记录](docs/implementation.md)
- [R0002矩阵失败与最小夹具修复](docs/matrix-native-eligibility-red-2026-10-03.md)

保留上游实际基础费用：公国 100 威望／200 虔诚，王国 500／1000，帝国 2500／5000；原版消费修正继续生效。上游页面资源列顺序与源码相反，维护文档以冻结源码为准。三档威望等级仍为 2／3／4。只启用维护版或上游其中一个，避免相同公开 CB ID 重复加载。

开发入口：`tools/validate_static.py`；正式九语追加 `--release-localization`。`tools/build_release.py --check` 复验完整 allowlist 的 manifest／ZIP；正式上传只用该工具 staging。`tools/gen_acceptance_fixture.py --output <fresh-external-directory>` 只生成外置夹具，不启动游戏；`tools/verify_fixture_log.py` 只读原生 marker，不能替代完整实机报告。

产品源码、专属工具与文档归本目录；正式上传树只包含明确 allowlist 的运行文件。`docs/`、`tools/`、夹具、原始快照与测试日志不得上传。来源文件永久保留于外置 attempt。

当前语言政策见 [language-acceptance-policy.md](docs/language-acceptance-policy.md)：仅简体中文真实游戏验收，其他八语仅格式规范检查，不要求语义、术语、母语审阅或翻译完成度。`--release-localization` 不调用翻译服务、不判断正文是否英文、不启动游戏。
