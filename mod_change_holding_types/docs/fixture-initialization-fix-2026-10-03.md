# 2026-10-03 外置夹具城堡初始化修复

R0002 的真实 GUI 转换与生产 effect 状态断言通过，但外置夹具在已经为城堡的地产上无条件执行 `set_holding_type = castle_holding`，产生一项脚本诊断。这项诊断位于 `events/chtt_events.txt:17`，没有将整轮改写为无错误实机 GREEN。[冻结的 R0002 候选报告](live-R0002-core-2026-10-03/README.md) 保留产品结果、错误和未完成项。

修复仅为夹具的城堡初始化添加 `if` 条件：`NOT = { has_holding_type = castle_holding }` 时才设置类型。六个生产转换 effect、玩家入口、目标条件、费用和本地化没有变化。原外置 `holding-live-fixture-01` 保持原字节；后继夹具放在全新 `holding-live-fixture-02`，本次没有改写已加载的 R0003 运行副本。

[夹具 diff](holding-live-fixture-02-2026-10-03.diff) 的 SHA-256 为 `b526e682689bc5c92c67e7b98e5c050f00dae6982b9e22017f370eaeb547d528`；[后继结构预验](holding-live-fixture-02-preflight-2026-10-03.json) 记录 `original_fixture_unchanged=true`、`runtime_source_changed=false`，且没有声称引擎语义已通过。Open Kaishek 根目录缺失是环境边界。

同一保护条件已同步到产品的 `tools/prepare_live_fixture.py`，随后使用实体 Python `3.13` 生成全新外置 `C:/workspace/two-mod-maintenance-20261003/holding-live-fixture-generator-fixed/`。[生成器核验](holding-live-fixture-generator-fixed-verification-2026-10-03.json) 为 GREEN：它与 R0003 已加载的 `holding-live-fixture-02` 有相同的三文件 inventory，逐文件 bytes、size、SHA-256 完全一致。

| 文件 | 字节数 | SHA-256 |
| --- | --- | --- |
| `common/on_action/chtt_on_actions.txt` | 232 | `cebb3384c7d0e45fade0719fef3f6f7872ebc84d6903e98373fe845f89b770a6` |
| `descriptor.mod` | 82 | `9c3bede238e7e45cea7814f02c991efecf417ba86dd10a9fe3f0ab792e351fd7` |
| `events/chtt_events.txt` | 3669 | `72fac24f77544135d15a35398658c15d8619d7aa1617fa47eaee63d42e19be9b` |

生成器核验报告原字节 SHA-256 为 `39f3068c9809f108efd3ad280bc63c4a5aee021d75dc3c46ca777d1d7b144997`。本次检查没有启动游戏，没有再次运行产品静态或 release build；它证明仓库生成器能重现后继夹具，不增加 R0003 的实机结论。R0003 的保存重载与无错误矩阵需另存父任务实际结果。

此前报告永久保留，修复及候选归档为新的独立记录。正式发布、公开完整 Change Notes、订阅缓存复核与永久 changelog 仍是父任务的独立交付。
