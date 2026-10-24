# 实机验收接入：2026-10-25

状态：**准备中；实机尚未执行，商店截图尚未采集。** 用户已授权执行[实机方案](../live-acceptance-plan-2026-10-24.md)，并要求多截可用作商店页面素材的真实画面。本记录随工作包更新，不以源码、准备或 ACK 代替业务通过。

## 已完成的公共接入

产品 `religious-ritual-fusion` 已进入公共产品清单和 canonical run key；`core`、`ui_rejection`、`cold_reload` 三个 case 使用既有 generic adapter。core 按输入区分 rite／faith；冷读走 saved_campaign、0 自然日，不 seed。自定义窗口操作和独立后态仍须现场资格，未授整产品或发布通过。

Java 工具新增严格 fixture request、显式 prebuilt manifest 和独立准备载荷，保持正式 67 文件不混入夹具。新局准备当前玩家的 A／B／另一 Faith 三个来源、明确知识及费用；不调用 RRF 提交来制造结果。观察事件只读取实际状态，不写成功 flag。

机器 `4-8e1c2f1861`：完整 `mvn -B -ntp -f mod_religious_ritual_fusion/tools/pom.xml verify` 于 `2026-10-24T16:11:28Z` 退出 0，23.686 秒，13 tests／0 failure／0 error／0 skipped。公共编号模块 14 项、全 canonical 产品同 runtime 1 项、全注册产品共用 cache 入口 1 项均通过；这些测试没有启动游戏或访问 Steam。

实际 Java CLI 已生成 `C:/workspace/rrf-development-20261024/build/fixture-core-rite-a01` 的 7 文件夹具。公共 prebuilt manifest 为其旁置 `.fixture.json`，5842 bytes，SHA-256 `16ad4bb3b5698fe645a9f2e19e4003360081b037d08e8e119f2822d6cef284ba`。open_kaishek corpus parser 对其中 6 个脚本、11380 bytes 返回 0 errors；corpus SHA-256 `7286cda52970a85f8da060657bf7976555b835544db2ec79a4a91440f7956521`。它只授通用语法范围，不证明原生作用域或 GUI 业务。

## 本机运行准备

机器 ID 来自本轮 `tools/ck3_live_run_id.py machine`，当前只有 C 数据卷，没有 D 盘。根映射保存在 `C:/workspace/rrf-development-20261024/live-admission/MACHINE-ROOT-MAP.a01.actual.json`；不套用另一机器的 D 盘迁移事实。

本机统一容量登记已实际推进为 rev73，准入文件 `ADMISSION.scene-a01.actual.json` SHA-256 `310dee7bc826ee407f47cd46ab17855f24b5eaf83b289df16d539caf1e77f08e`。本轮新增峰值上限 1 GiB，不录视频、不复制游戏；现有 native 编译树和缓存复用，截图子限 288 MiB。有限项目 quota 为 80,000,000,000 bytes，复核 `2026-10-26T16:00Z`；本次准入截止 `2026-10-25T04:00Z`，启动前仍需检查新鲜性与实际消耗。

后台离线 probe 已观察 Steam offline；启动前会重新取得 30 秒以内的合格回执，旧回执不作入场许可。当前没有启动 CK3。最新本机前场 R0046 的原 native 资源终态、keeper 和 CAS 释放已由当前公共 allocator 只读检查通过，可普通接续；其旧 public run=2、normal_close=false 和业务缺口保持，不追认历史通过。

## 当前施工与下一步

现有 MCP 能打开／选择决策定义，但不支持决策内 Rite 目标选择，也不能执行独立 RRF 窗口控件。原生已有 FindTopLevel、控件树和 ShortcutManager 按钮派发底座，正在补通用控件 query／action 及现有 SDK 桥；生产按钮仍经真实 GUI，不以脚本直调替代。

后续顺序为：完成并验证通用原生控件链 → 固定源码／DLL／公共 runtime → 公共 prepare／allocate／preflight → 两模式真实窗口、费用和结果 → 正常保存及独立冷重载 → 受控拒绝／兼容场景与素材收集。进入冻结现场后，修改保全到外置后继包，闭场后再合入。

截图目标为约 24–36 张不同构图，覆盖选择来源、三栏内容、核心／教义选择、最终费用、融合结果、历史及原版宗教详情。原图保留实际尺寸、run／PID／游戏日期／界面状态和 SHA，商店候选避开诊断覆盖、控制台、遮挡和空白控件。真实失败画面作为诊断保存，不包装成成功玩法素材；本轮不合成或伪造实机图。

## 通用控件链后继

两个通用工具已贯通 native／SDK／service／MCP／shared host：`ck3_query_scripted_widget_controls_v1` 查询实际窗口与控件身份；`ck3_activate_scripted_widget_control_v1` 消费该次查询的 opaque widget ID、generation 和 public revision，调用原 ShortcutManager。动作使用 `fresh_revision=false`，后态另取新鲜快照，ACK 不授业务成功。稳定 paused 身份不要求跨调用的 render 帧号相同。

既有 SDK workflow 已加入完整独立 step。本机四阶段配置／编译／native reducer／SDK 组实际退出 0，13 项 SDK 回归包含 C++ 实际 serializer、完整工厂消费者、host revision codec、独立进程 continuation 与严格类型检查。严格检查范围为完整 `gui_window_tree_contract.py` 及实际提取的 6 个新增方法，不声称旧大模块全绿。原始小回执已保全至 `C:/workspace/rrf-development-20261024/sdk-ci-a01`，原执行目录和日志引用保持。

公共 runtime 生产者加入两个 capability 后，使用 `tools/.venv/Scripts/python.exe -X utf8 -m unittest discover -s tools -p test_ck3_mod_acceptance_build_runtime.py`，完整 63 项通过，含两工具经正式 producer 到 SDK／runtime 消费者的 legacy 与 gzip 两路。首次误用无 pydantic 的系统 Python 导致环境错误，未修改生产逻辑来绕过；不将该次失败归为产品实机结果。

实际 native 生产 DLL 位于 `C:/workspace/rrf-development-20261024/build/native-a01/xar_ck3_bridge.dll`，15,710,208 bytes，SHA-256 `5166991c7de5c0ec0d7de06f236b4a34dae57a2a9b0a8ff2fb508ca5ed7e5da4`。7 个受影响 TU 实际严格编译与链接均退出 0，旧冻结 DLL 未改；来源、借用对象、真实依赖和链接回执见同目录 `INCREMENTAL-BUILD.actual.json`。该结果尚不是新 FileAPI qualified runtime 或实际控件通过。

当前正在修复现有 configured successor 对新增 TU 缺少 old_commands／旧 dependencies 的实际拒绝路径；保留严格来源及真实 FileAPI，完成正式资格封包后继续实机。没有伪造 qualification，也没有启动游戏。另已读回当前桌面 1024×768、显示设备实际支持 2560×1440；将在排他现场按实际模式设置并读回，截图不会放大冒充原尺寸。

该拒绝路径已修入既有共享 producer：新增 TU 必须确为新源文件、沿用同 target 的实际编译选项，并实际编译；不接受伪造旧依赖、移除旧生产 TU 或借用新增对象。机器 `4-8e1c2f1861` 于 `2026-10-24T16:43:27.831586Z` 完成全模块 26 项回归，实际原进程退出 0；两个完整模块的 strict mypy 通过。持久 CI 已调用同一测试与静态检查入口。小型原始回执分别位于工作根 `build/producer-checks-a02/RESULT.actual.json` 和 `build/producer-static-a01/RESULT.actual.json`。

正式 successor 仍须从完整旧 archive 链重新计算所有受影响 TU，并生成真实 CMake FileAPI 资格；手工 DLL 不替代它。为覆盖这部分真实输出，既定 1 GiB 总峰值内的 native 子限调整为 192 MiB、截图子限调整为 224 MiB；正式 producer 自身输出上限 160 MiB。总峰值、系统增长预留和其他占用上界保持，最新容量准入以机器工作根的版本化实际回执为准。

新局 fixture 已补真实公共决议入口调用只读观察事件，避免依赖不存在的按定义触发 event 工具。core 按模式触发 `.20/.21`，拒绝场触发 `.30`；仅玩家 Robert 29829 且准备完成可见／可用，不改产品结果。fresh 现为 10 文件，cold 保持 5 文件且无 seed／观察决议。机器 `4-8e1c2f1861` 于 `2026-10-24T16:46:40Z` 完整 Maven verify 通过 13 tests／0 failures／0 skipped，33.272 秒；随后 rite／faith／ui 三种实际 CLI 生成均退出 0。正式 67 文件未变。此前 7 文件输出保留为历史准备输入，不用于新运行。
