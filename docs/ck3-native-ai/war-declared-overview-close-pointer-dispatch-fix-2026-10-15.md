# 宣战概要窗口固定 Close 修复（2026-10-15）

P07 AUTO7 的 `close-war-declared-overview-v1` 已通过暂停帧、同一 owner、窗口可见、`dismiss` 控件和回调资格检查，却返回 `dispatch_attempted=true`、`dispatch_invoked=false`、`native_handled=false`。原生后置观察仍为可见，正确保留 `verification_pending`，没有关闭成功信用。

原回执位于本机 `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation41-cold-prep/p07-responses/0007-1-result.json`，SHA-256 为 `1ccf437328f7d0b9920bb08c0c7172285c68a49cb27bd2a664b2e62f4cd1ecbe`。完整原件由主流程保留；本候选的 `P07-AUTO7-FAILURE-AND-GUI.json` 只摘录真实 native leaf、原件 hash 和原版 GUI hash，不复制大份历史轨迹。

## 已定位路径

实际实现位于 `ck3_autonomous_player/native_bridge/src/ingame_ui_navigation_v1.cpp`。旧宣战概要分支先调用 `WarDeclaredPointerV1`，以 `std::hex` 生成小写地址，再交给 `DispatchZhongguoScoreboardActionNativeV1`。后者在 `zhongguo_scoreboard_action_v1.cpp` 的 `ValidPointer` 中只接受 `0-9` 与大写 `A-F`，含小写字母的地址在 GUI 调用前即被拒绝。这个问题与模型推理和屏幕识别无关。实际 production action.cpp 的离线 fixture 已复现 `0xabcdef` 被拒绝且 native 调用次数仍为零；同一 fixture 的正确大写传输可以执行。

原版实际文件是 `game/gui/window_war_declared_overview.gui`。底部 `dismiss` 和标题 `button_close` 都绑定 `[WarDeclaredOverviewWindow.Close]`。战争结果窗早已走固定 `WarResultsWindow.Dismiss` 回调分支，未经过这个有大小写不匹配的指针字符串路径，所以两类窗口的调用路径不同。该来源差异不能替代宣战窗口真实关闭验收。

本次将两个固定战争窗口的关闭归到 `DispatchFixedWarWindowCloseV1`：保留现有构建、游戏主线程、暂停帧、owner、模态、按钮可见/启用和 callback 资格检查；再次确认同一 root、控件和 vtable；只允许结果窗 `close_button` 或宣战概要 `dismiss`/`button_close`，且只有一个实际绑定的回调。直接按已确认的 .4 GUI slot2 ABI 传入 callback object 与控件指针地址，不再格式化/解析原生指针。未开放任意窗口、任意按钮或地址参数。

宣战概要回执新增 `close_stage`、`close_exception_code`，区分未尝试、预检拒绝、回调进入、回调返回和异常；SDK 接受旧 B17 字段集及完整新字段集，拒绝矛盾或多余字段。回调返回仍不代表关闭成功，必须同一 owner 的独立原生后读回证明隐藏或不存在；仍可见、异常及读回缺失均没有关闭信用。主流程对 pending 的处理由同期独立优化任务维护。

## 候选与验证

完整增量候选位于本机 `D:/codex-ck3-demos/2026-10-14-robert-30year/realm-camera-native-candidate03/`，DLL SHA-256 为 `29768ab0872f5dc4510bae3f3cc229886aab2c00e99ad0d3976150130eac0c7d`，大小 18,104,832 bytes。保留 candidate02 原件及身份，只替换其 B17 c0339 UI 对象，保留全境镜头、声明查询 profiling 和其他全部不可变链接输入。B17 实际冻结 UI 源码与本次公共父提交 `b9aba7df` 逐行相同；构建保存实际 include hashes、完整编译/链接参数、原 runtime archive hash 与所有保留对象 hash。

定向 Python 测试覆盖真实 Driver 传输、旧字段兼容、Close trace、pending 不授信、伪造拒绝以及独立关闭后置条件。原生离线 DLL 测试运行实际 production action.cpp 回归、正确传输 fixture、禁用控件拒绝，以及 callback ABI、空预检、控件指针失效和 SEH 不重放。构建/测试不连接 Game pipe、不操作桌面、不注入 DLL，新 EXE 为零。

这些证据证明源码修复与离线候选有效。该候选尚未部署；需主任务在自然存档边界完成受管冷载并取得 `closed_verified` 的实际回执及桌面 1 画面。此处不声称现有游戏进程已修复，也不声称全境镜头已通过像素覆盖验收。实际交付清单与测试数以候选目录 `DELIVERY.json` 为准。

## 现有游戏的调用边界

现有 `ck3_close_war_declared_overview_v1` 只接 `expected_revision`，地址由旧 Native 内部生成，不能在 Python 端改成大写。`DispatchFixedGuiWidgetNativeV1` 是内部 C++ 函数，未作为公共 MCP 或 DLL 导出。接收地址的 scoreboard action 有固定投影、ACL 和指纹，不能改用宣战窗口；frontend action 也固定了 route 和 root。

现有未知强制弹窗 port 直接调用实际 slot2；但只有新鲜 query 证明该窗口就是当前 exclusive modal receiver 且存在可用选项，才适用。宣战概要是普通 `layer=middle` 窗口，不能仅凭视觉遮挡认定其属于强制 modal。禁止伪造 modal 身份或用 scoreboard/任意点击绕过固定 scope。
