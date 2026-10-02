# 2026-10-03 当前测试报告

产品：地产类型转换（XenoAmess维护版）。上游：`3337428403`。维护版 ID：尚未创建。

| 层次 | 状态 | 实际证据 |
| --- | --- | --- |
| 公开页面研究 | 完成 | 读取上游标题、作者、功能说明、更新时间与新版故障反馈 |
| 当前原版脚本研究 | 完成 | 安装 build `25652598` 的七种 holding definitions、当前 native selector、原版 `set_holding_type` 用例和继承字段 |
| 完整 CK3 version／EXE SHA 绑定 | 已冻结 | `1.20.0.3`／build `25652598`，EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6` |
| 上游源字节与逐文件 manifest | 完成 | 10 文件／232740 字节，[来源记录](upstream.md)与[逐文件 manifest](upstream-manifest-2026-10-03.json) |
| 产品代码适配 | 完成 | `title_valid`／`DecisionViewWidgetSelectBarony` API、root人物引用、六生产effect、明确玩家与目标边界 |
| 产品 L0／可复现构建 | GREEN（简中／英文） | [最终静态 attempt03](holding-static-attempt-03.json)，10运行文件；double-build manifest／ZIP bytes一致 |
| Open Kaishek 离线加速器 | environment unavailable | [来源预验回执](holding-kaishek-source-01.json)：`open_kaishek-root-missing`，没有工具执行或引擎语义 GREEN |
| 外置实机夹具准备 | 完成，未执行 | [fixture manifest](holding-live-fixture-01.fixture.json)，10 PASS声明＋START／END＋AI actor到达；源码仅结构检查 |
| 产品 CK3 实机验收 | 未执行 | 未启动 CK3，没有实机 run ID 或 GREEN |
| 新 Workshop 发布／缓存／Change Notes | 未执行 | 没有创建、上传或公开发布事实 |

首次静态 [attempt01](holding-static-attempt-01.json) 为 harness RED：结构扫描器把同名参数化 trigger 调用与顶层定义一并计数，误报 7 个定义。修复当前层 block 识别后 attempt02 GREEN；失败报告仍保留，没有修改为 GREEN。

attempt02 对六目标、当前 native GUI method、actor作用域、个人费用token、入口／effect玩家限制、已有且本人直辖／未出租／无在建目标、BOM、44个CN/EN key与实际运行allowlist进行检查。它只证明源码结构及当前原版接口匹配，没有启动游戏。

attempt03 在相同 runtime bytes 上补齐共享来源allowlist检查、严格本地化parser、实际CK3 EXE SHA、当前原版费用token与两个innovation definition检查，结果GREEN，报告SHA-256 `bcaaba9cd1fa5ca091ac6b5f0897f36d4cf18712095e337c26d07fe279d7c4b8`。当前原版 `main_cost_base=400` → `main_cost_tier_1` → `main_building_tier_1_cost`，这是源码层基准，不是实际GUI付款读回。产品Python全部编译通过；外置fixture文件与其冻结manifest逐字节相符。

当前10文件可复现检查的 manifest SHA-256 为 `cd6aa819e665440cfe5dc61b62359781a1831930940070e8d485147cdff2abe9`，ZIP SHA-256 为 `f8c14f5c8e8a690a0a4045f95b765232f6ca283cd4392922578997608d56c759`。后续正式九语会改变文件数及构建hash，需另保存正式结果，不覆盖本次候选。

本报告不把页面评论当作确定根因，也不把自动升级建筑历史结果当成本产品验收。实机与发布结果应另存当次实际命令与回执，再追加日期记录；失败 attempt 不覆盖。

参考：[功能分析](function-analysis.md)、[来源记录](upstream.md)、[适配计划](adaptation-plan.md)、[测试计划](test-plan.md)。
