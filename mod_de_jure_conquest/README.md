# 公国／王国／帝国法理征服（XenoAmess维护版）

独立维护目录。上游为白绮的 [Workshop 3600021457](https://steamcommunity.com/sharedfiles/filedetails/?id=3600021457)。维护版必须创建新的 Workshop 物品，不得更新上游物品。

当前阶段：**1.0.0 候选源码、16文件九语静态与可复现构建通过；尚未执行 CK3 实机、未发布。** 验收目标为 CK3 `1.20.0.3 (Crozier)`、Steam build `25652598`，descriptor 声明 `1.20.*`。九语是格式／键／占位符认证；版本声明不等于整个1.20系列均通过实机。

文档入口：

- [功能分析](docs/functional-analysis.md)
- [来源与环境冻结](docs/upstream.md)
- [适配计划](docs/adaptation-plan.md)
- [测试计划](docs/test-plan.md)
- [当前测试报告](docs/test-report.md)
- [发布流程](docs/release-plan.md)
- [源码适配记录](docs/implementation.md)

保留上游实际基础费用：公国 100 威望／200 虔诚，王国 500／1000，帝国 2500／5000；原版消费修正继续生效。上游页面资源列顺序与源码相反，维护文档以冻结源码为准。三档威望等级仍为 2／3／4。只启用维护版或上游其中一个，避免相同公开 CB ID 重复加载。

开发入口：`tools/validate_static.py`；正式九语追加 `--release-localization`。`tools/build_release.py --check` 复验完整 allowlist 的 manifest／ZIP；正式上传只用该工具 staging。`tools/gen_acceptance_fixture.py --output <fresh-external-directory>` 只生成外置夹具，不启动游戏；`tools/verify_fixture_log.py` 只读原生 marker，不能替代完整实机报告。

产品源码、专属工具与文档归本目录；正式上传树只包含明确 allowlist 的运行文件。`docs/`、`tools/`、夹具、原始快照与测试日志不得上传。来源文件永久保留于外置 attempt。
