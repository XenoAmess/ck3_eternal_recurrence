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

## d13 正式运行图准备与实际拒绝

机器 `4-8e1c2f1861` 的正式 successor 已在 `2026-10-24T17:01:11Z` 实际完成 41 个受影响 TU、archive 和生产链接，五组 fixture 及额外只读四包均退出 0。正式 DLL 为 15,711,744 bytes，SHA-256 `ff6916d2ff3cff737803c910ac28452ad1d141fe540b7a0994e05197f91a74af`；`build/native-qualified-a01/native-a01/PUBLIC-RUNTIME-QUALIFICATION.actual.json` 及公共 `qualify_native` 消费回执保留完整 FileAPI／来源／旧链接输入／Defender 闭包。手工 DLL 仍只作此前有限编译证据。

最终提交 `d13c6721b281235dad3628674b85b1b321118b33` 的 SDK 87、wire seam 115、public-control／case-hooks 1290 次实际测试执行均零跳过；host 879 为相关完整组的重叠汇总，不能与前述数字相加称独立测试总量。先前 mypy 1.15 与 CI 指定 2.4 的类型推断差异，以及缺少两份 HOF 原生包导致的 skip 均保留原 RED；隔离使用 2.4、读取本机实际同 SHA 原生原件后，受影响完整步骤已实际通过。

公共 builder 随后真实拒绝 RRF 两项已有查询能力：`ck3_query_player_religion_doctrines_v1` 与 `ck3_query_player_religion_tenets_v1` 未进入全局额外能力规则。真实 native profile 的两项 PRIVATE_QUERY flags 均为 ON；正在修共享规则及生产者到 MCP 工厂的回归。拒绝发生在运行目录写入前，不是实机故障，也不授游戏通过；游戏和商店截图仍未执行。修复形成普通后继提交，旧资格保全，同源部分以实际逐文件相等绑定复用，不把继承结果写成新提交重跑。

容量准入已为 a06／rev78：总新峰值仍 1 GiB，native 160 MiB、cache 288 MiB、save 240 MiB、截图 208 MiB、wire 80 MiB、runtime 16 MiB、闭场 32 MiB。native 清点曾漏掉 SDK 临时 VS 生成树，已如实补记；精确回收可重建未引用元数据后，全范围现存 151,649,355 bytes，低于 native 子限。旧 RED 类型缓存和 pip 派生缓存已精确回收，原日志／参数／源 Pin 保留。实际原件、用途及回收清单均在工作根，不改写旧回执。

独立存档工具来自 [Rakaly 官方发布](https://github.com/rakaly/cli/releases/tag/v0.8.22)，本机实读版本 0.8.22、EXE 6,867,456 bytes、SHA-256 `9d3404f6eb08db3a3d2196a5b2e1ce9b4c8687f2d7df60a4f79cafe75f043101`。来源摘要见 `runtime-tools-a01/PROVENANCE.actual.json`，不留重复 ZIP、不改 PATH、不为第三方加 Defender 排除。其 [官方变更记录](https://github.com/rakaly/cli/blob/master/CHANGELOG.md)列明 0.8.21 已增加 CK3 1.20 支持；本场存档的实际解码及对象图仍须现场验证。

能力漏项已修入同一共享 builder 的三行规则：两项 native flag，以及 Tenets 在注册工厂中的既有权限镜像。新增闭环回归实际验证生成器→Selection argv→MCP 工厂，并逐项验证 native flag OFF／缺失及未授工具权限时拒绝、不写运行目录。canonical host 本身已经具有对应权限设置，不需改动。最终完整 CI 四命令实际 26+64+28=118 次测试执行、0 skip，两项 CI 静态与额外完整 builder mypy 均退出 0；原件 `public-chain-a01/runtime-capability-fix-a03/validation.actual.json` SHA-256 `27fa2156ef6ae8ccd5b291955e607364b131aa186e58de00277803dafaafdfd0`。它明确记录待提交源码身份，不冒充已对未来 commit 执行；后继以实际字节相等绑定最终提交。

下一次实际构建通过了 native／capability 校验，写入候选 `runtime-a01` 后，因 builder 无条件调用 generic adapter 不提供的可选 `validate_contract` 而失败。该不完整目录和原始退出／错误保留，不作 runnable runtime 使用。修复与公共 Selection 的既有合同一致：仅当钩子可调用时，在 `case_imports` 中执行；有钩子的拒绝继续向上传播，不给 generic 添加空实现。

机器 `4-8e1c2f1861` 于 `2026-10-24T17:55Z` 完成受影响完整 CI 命令组：26+66+28=120 次测试执行、0 skip，以及 CI 静态和额外完整 builder strict mypy，原进程均退出 0。新增回归用实际 RRF core 注册项及真实 generic adapter，覆盖 plain／gzip 的 writer→MCP 工厂→公共 prepare→preflight；输入明确为 synthetic 元数据，不声称运行 Java fixture 或游戏。已有 validator 的非法合同仍实际拒绝，写入的失败候选不产生 STATIC 验证。原始命令、等待结果和日志位于工作根 `public-chain-a01/generic-adapter-fix-a03/`。后续使用全新 `runtime-a02`；游戏内业务和截图状态仍为 NOT_RUN。
