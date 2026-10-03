# 地产类型转换（XenoAmess维护版）

这是 `Change the holding types` 的独立第三方维护工作目录。上游 Workshop `3337428403` 只用于注明来源；维护版新物品为 `3812510834`；后续更新仅针对维护版。

当前状态（2026-10-03）：**1.0.0已公开发布至[新维护版Workshop物品 3812510834](https://steamcommunity.com/sharedfiles/filedetails/?id=3812510834)**。CK3 1.20.0.3中文实机验收、正式构建、完整更新说明匿名回读、中文媒体及全新订阅缓存复核通过；Steam已恢复离线。**只实机验收简体中文，其他八语仅格式检查。** 详细结果和已知限制见[正式发布报告](docs/release-1.0.0-2026-10-03/README.md)。历史外语实机和失败attempt仅保留为诊断证据，不作为中文签核。

- [功能分析](docs/function-analysis.md)
- [来源冻结记录](docs/upstream.md)
- [CK3 适配计划](docs/adaptation-plan.md)
- [测试计划](docs/test-plan.md)
- [当前测试报告](docs/test-report-2026-10-03.md)
- [正式九语静态报告](docs/release-static-R0003-2026-10-03.json)
- [实机attempt边界](docs/live-attempt-status-2026-10-03.md)

维护方法沿用仓库的 `mod_auto_upgrade_buildings`：原始字节另存、源码与发布 staging 分离、精确游戏版本绑定、静态检查、隔离实机和发布后的公开及订阅缓存读回。产品源码、配置和证据索引放在本目录，各产品独立验收。

保留六个转换决议的公开 ID 和个人金币费用。修复 CK3 1.20 的地产选择器 API；仅允许玩家转换已有、本人直辖、未出租、无在建的男爵领。转换可能损失不兼容建筑，且不能解除原版政府与继承规则。

工具从仓库根执行，`<verified-python>` 是已验证的实际解释器：

```text
<verified-python> mod_change_holding_types/tools/validate_static.py --game-root <ck3-game-directory> --report <new-report.json>
<verified-python> mod_change_holding_types/tools/build_release.py --check
<verified-python> mod_change_holding_types/tools/prepare_live_fixture.py --output <new-external-fixture-directory>
```

正式构建和九语格式检查增加 `--release-localization`；构建指定 `--output <new-external-staging-directory>`，不直接上传本目录。普通静态开发的简中／英文基准比较只涉及key和格式；其他语言同样只检查格式。实机入口与验收提示只使用简体中文。
