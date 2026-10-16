# CK3 战争结果窗口自动清除

普通自动游玩在暂停地图上优先检查原生 `war_results` 窗口。Native 只在已确认的 CK3 1.20.0.4 构建上公开 `query-war-results-window-v1` 和 `close-war-results-window-v1`；MCP 对应提供 `ck3_query_war_results_window_v1` 和 `ck3_close_war_results_window_v1`。查询与关闭都使用当前快照修订、连接代际和独立的游戏主线程执行回执。关闭只投递到该窗口的 `close_button`，必须在原生操作后再次读取，确认窗口不存在或不可见，才记为界面关闭成功。界面关闭本身不计为战争胜利。

普通规划在战争集合变化时立即重新检查；否则，自上次确认窗口清除起每六个游戏日重新检查。2026-10-15 用户将清除目标改为 **10 个游戏日内的弱保证**：不为偶发小幅超时阻塞主流程。保留当前检查节奏，不缩短游戏推进窗口来追求严格截止。请求推进六日不等于实际只经过六日；P13 的实际回执出现过七日和八日推进，须按实际日期记录延迟。若原始关闭请求超时，保留请求 ID 并收取原回执，不重复点击。缺少可核实的原生窗口读回时保留未完成状态。

2026-10-14 的候选源码位于独立 `war-results-auto-dismiss-20261014` 工作树，B14 Native DLL 绑定当前 D 盘演示的游戏进程。该演示在 `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation37/`，录像位于其 `recordings/`，桌面 1 的 OBS 场景同时包含游戏与决策悬浮窗。首次实机 `responses/0005-1-result.json` 在战争仍进行时读到 `war_results` 已注册但不可见，执行了查询而未误发关闭。`responses/0051-1-result.json` 是六个游戏日后的再次查询，同样不可见。**可见结果窗口的自动关闭和七日内读回仍待这场战争实际结束后验收**；查询 ACK、源码测试与录制画面均不能替代该项实机结果。

## 2026-10-15 B15 固定 Dismiss 修复候选

第二场战争胜利后的 P08 `p08-responses/1519-1-result.json` 实测：结果窗可见，已选中底部 `close_button`，但旧分发返回 `dispatch_invoked=false`，窗仍可见，状态为 `verification_pending`，没有关闭成功信用。原版 1.20.0.4 `window_war_results.gui` 将该按钮绑定到 `[WarResultsWindow.Dismiss]`。B15 仅对这个固定窗口保留原有游戏帧、owner、模态和控件资格检查，再核同一按钮及单个回调，直接调用当前构建的 GUI 回调；其他窗口仍走原分发。回执新增 `dismiss_stage` 和 `dismiss_exception_code`，SDK 接收旧 B14 与精确 B15 字段集。回调返回也不算关闭；仍须同一 owner 的原生后置读回证实窗口消失或隐藏。异常和未证实的结果不得自动重试。

本机不可变候选为 `D:/codex-ck3-demos/2026-10-14-robert-30year/native-war-results-b15-final01/`，`FINAL-FREEZE.json` SHA-256 为 `976960f91e9a9fbfce6f28571da3034acef9b07aa92a48b1002f5ca1f880bb67`，Native DLL 为 `146c05e88d94232cc898116b2331bdb4654855ba417e7e2e6da5d6597a6c001f`。仓库源码见 `native_bridge/src/ingame_ui_navigation_v1.cpp`、`native_bridge/include/xar_bridge/war_results_dismiss_adapter_v1.hpp` 与 `src/xar_autoplayer/bridge/war_results_window_contract.py`。定向 Python 测试 `tests/test_war_results_window_contract_b15.py` 连同原优先级测试共 7 项通过；MSVC mock 回调测试 `native_bridge/tests/war_results_dismiss_adapter_v1_test.cpp` 返回 0，覆盖正常返回、空预检和 SEH。`open_kaishek` 当前没有对应的 CK3 GUI 回调 ABI 或该 SDK wire 语义可预验，故此项为 not-applicable。

旧游戏进程 PID 127268 在 WM_CLOSE 等待约 60 秒未退出后需要强制终止；`continuation37/ROOT-ACTUAL-GAME-EXIT.json` 实际记录内核退出码 1、`normal_wm_close_qualified=false`。后续 `continuation38-cold-prep/ROOT-OLD-GAME-EXIT-VERIFIED.json` 只证明旧代际已退出，不能写成正常关闭。B15 已在新的同场续行中加载，P13 的空查询仍读到结果窗隐藏；截至本记录，**尚无 B15 对可见结果窗执行 Dismiss 后 `closed_verified` 的实机回执**。旧七日标准的历史未验收记录保留，当前目标以上述十日弱保证为准。
## 2026-10-17：读取失败与关闭成功分离

SDK31的AUTO104因同帧overview `state_changed` 失败缓存再次阻塞。SDK32三叶窄修复使overview首次精确拒绝
重新规划一次，并使overview/results已有同帧failed读取缓存释放普通规划；保留请求ID、失败原句和unknown可见性。
已知visible与close-pending继续选择原有关闭／独立读回，不会由读失败获得absent、hidden或关闭成功信用。
本批**war-results首次query失败的非致命消费仍未覆盖**，另有后续候选；不能把负缓存释放外推到所有UI错误。
新4项及原优先级回归通过，含Service真实Native查询public2/native40路径；
完整patch及便携用例见[收口包](research/sdk31-route-window-sdk32-ui-defer/README.md)。

## 2026-10-17 后续：首次 results 只读拒绝

公共 transport／Service 已补齐上节未覆盖的精确 query `state_changed`：保留原始请求及失败回执，返回技术读取延后，
窗口可见性仍 unknown，没有关闭、日期或业务信用。原生拒绝发生在 owner mailbox 提交之前；关闭、超时与其他错误不被软化。
真实 Service／NativeDriver 的 12 项新测试及相关回归共 25 项通过，独立正式队列回放也通过。
这是**未部署的源码修复与离线验收**，当前 SDK32 不切换，未将此分支写成实机成功。
[源码、独立复核与限制](research/war-results-first-read-state-changed/README.md)。
