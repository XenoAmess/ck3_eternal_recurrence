# 2026-10-03 当前测试报告

产品：地产类型转换（XenoAmess维护版）。上游：`3337428403`。维护版 ID：尚未创建。

| 层次 | 状态 | 实际证据 |
| --- | --- | --- |
| 公开页面研究 | 完成 | 读取上游标题、作者、功能说明、更新时间与新版故障反馈 |
| 当前原版脚本研究 | 完成 | 安装 build `25652598` 的七种 holding definitions、当前 native selector、原版 `set_holding_type` 用例和继承字段 |
| 完整 CK3 version／EXE SHA 绑定 | 已冻结 | `1.20.0.3`／build `25652598`，EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6` |
| 上游源字节与逐文件 manifest | 完成 | 10 文件／232740 字节，[来源记录](upstream.md)与[逐文件 manifest](upstream-manifest-2026-10-03.json) |
| 产品代码适配 | 完成 | `title_valid`／`DecisionViewWidgetSelectBarony` API、root人物引用、六生产effect、明确玩家与目标边界 |
| 产品 L0／可复现构建 | GREEN（正式九语候选） | [正式静态 R0003](release-static-R0003-2026-10-03.json)，17运行文件；canonical LF double-build manifest／ZIP bytes一致 |
| Open Kaishek 离线加速器 | environment unavailable | [来源预验回执](holding-kaishek-source-01.json)：`open_kaishek-root-missing`，没有工具执行或引擎语义 GREEN |
| 外置实机夹具准备 | 已冻结；结果待实机回执 | [fixture manifest](holding-live-fixture-01.fixture.json)，10 PASS声明＋START／END＋AI actor到达，声明不等于结果 |
| 产品 CK3 实机验收 | R0002进行中，未GREEN | [R0001／R0002边界记录](live-attempt-status-2026-10-03.md)：R0001 harness RED；R0002 exact-build handshake成功但DLL frontend route capability缺失 |
| 新 Workshop 发布／缓存／Change Notes | 未执行 | 没有创建、上传或公开发布事实 |

首次静态 [attempt01](holding-static-attempt-01.json) 为 harness RED：结构扫描器把同名参数化 trigger 调用与顶层定义一并计数，误报 7 个定义。修复当前层 block 识别后 attempt02 GREEN；失败报告仍保留，没有修改为 GREEN。

attempt02 对六目标、当前 native GUI method、actor作用域、个人费用token、入口／effect玩家限制、已有且本人直辖／未出租／无在建目标、BOM、44个CN/EN key与实际运行allowlist进行检查。它只证明源码结构及当前原版接口匹配，没有启动游戏。

attempt03 在相同 runtime bytes 上补齐共享来源allowlist检查、严格本地化parser、实际CK3 EXE SHA、当前原版费用token与两个innovation definition检查，结果GREEN，报告SHA-256 `bcaaba9cd1fa5ca091ac6b5f0897f36d4cf18712095e337c26d07fe279d7c4b8`。当前原版 `main_cost_base=400` → `main_cost_tier_1` → `main_building_tier_1_cost`，这是源码层基准，不是实际GUI付款读回。产品Python全部编译通过；外置fixture文件与其冻结manifest逐字节相符。

先前10文件可复现检查的 manifest SHA-256 为 `cd6aa819e665440cfe5dc61b62359781a1831930940070e8d485147cdff2abe9`，ZIP SHA-256 为 `f8c14f5c8e8a690a0a4045f95b765232f6ca283cd4392922578997608d56c759`。其原始报告保留；正式九语结果使用新的文件数及构建hash。

九语canonical LF候选已另行完成：[正式静态R0003](release-static-R0003-2026-10-03.json)绑定 commit `1734e7e50c87955179393ebf854cc4f3567c805d`，17文件、`release_localization=true`、零错误；报告原字节SHA-256为 `8a4310e95dd23ea4a5d2051395149ede2c9f9819faab0ba7a46d52b9c35b2c42`。父任务双构建结果为manifest SHA `950d63627d87cc8b3139ec77d5a97e9e917989d0dd0b395add143fe0c0d4ba35`、ZIP SHA `e72508770b964de9026c986b58be8b4bb12a43b5cf1686c0493b8a3e08728776`。这些是正式候选静态事实，不能写成已上传或实机通过。

[九语覆盖报告](localization-coverage-2026-10-03.json)保留MiniMax候选修正、44key完整覆盖和token／格式边界；它明确没有九语实机和母语审阅。旧CN/EN报告和失败attempt继续保留。

本报告不把页面评论当作确定根因，也不把自动升级建筑历史结果当成本产品验收。实机与发布结果应另存当次实际命令与回执，再追加日期记录；失败 attempt 不覆盖。

参考：[功能分析](function-analysis.md)、[来源记录](upstream.md)、[适配计划](adaptation-plan.md)、[测试计划](test-plan.md)。

## 2026-10-03 补记：R0003 重载与干净矩阵

[R0003 冻结核验报告](live-R0003-reload-2026-10-03/README.md) 已记录实际 ready snapshot002：人物 `31254`、同日 `53144328`、暂停、金币 `846`，保存 bytes 与 R0002 保存源 size／SHA 一致。原生日志证明 Rossano 的玩家直辖城市结果持久化，未选中首都仍为城堡。修正后的 fixture02 十项生产矩阵 PASS，连同两项保存状态共十二 PASS，START／END／AI actor 完整；捕获 error.log 为零字节。R0002 原错误继续保留。

英文截图已观察六名称、费用400和条件；完整 warning 的无遮挡稳定截图及七语视觉尚待 R0004 独立结果，母语审阅未完成。结论只适用本机固定 `1.20.0.3` EXE/build，不外推整个 `1.20.*` 系列，也不代表发布、公开 Change Notes、缓存或 changelog 已交付。早期 Taranto 地名误记以 [追加勘误](corrections-2026-10-03.md) 更正为 Trani／特拉尼，原候选不覆盖。
