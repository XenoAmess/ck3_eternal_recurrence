# 战果窗口首次只读拒绝的非致命观察

本包补齐 SDK32 三叶修复之后仍未覆盖的 results 首次查询失败。公共源码已准备，独立离线复核通过；**没有安装到正在运行的 SDK32，没有此分支的实机复现验收**。当前游戏及录像继续运行，不为公开收口切换现场。

`execute_war_results_window_v1` 仅将精确查询 `query-war-results-window-v1` 的原始 `command_result(ok=false,error=state_changed)` 转为 `technical_read_deferred`。原始请求、请求 ID、公共与 Native 修订、连接代际及源帧均保留。结果仍是可见性 unknown、未接受、未关闭，没有日期、业务或 UI 关闭信用，也不重发原请求。关闭操作、超时、owner 失败和任意其他拒绝继续抛错。

原生依据是 `native_bridge/src/ingame_ui_navigation_v1.cpp:1310–1313` 的唯一 `state_changed` 返回：它位于 GUI owner/mailbox 上下文赋值及 `TrySubmitMainThreadQuery` 之前。当前快照、revision、旧快照存在性或 fresh read/equality 中哪一项失败仍未知；本包没有声称修好原生竞争根因。

普通入口是 `GameplayBridgeService.auto_turn` → Driver 的专用 `query_war_results_window_v1` → transport/wire。便携测试使用真实 Service 和 NativeHeadless Driver，只替换 Native I/O；公共序号 2 与 Native 序号 40 分别绑定。查询软拒绝后，下一次普通规划选到已有 clock，原失败查询不在同帧重发。新 12 项与相关 UI 回归共 25 项通过。

独立复核还实际使用正式队列 AST loader、完整 canonical wrapper、`check_after(AUTO)`、`full_loop(max1)`、persist 与真实 atomic bound。只增加一次 typed nonmaterial 观察，日期／业务／close 均为零，TURN 为 2,454 字节。原先对 observed/executed 入口的疑虑未复现，没有为此增加源码分支。此为合成 Native 回执的离线生产链验证，不能当作实机验收。

- [精确源码与原件 pins](SOURCE-PINS.json)
- [独立复核](REVIEW-FINAL.json)及[正式队列回放](FORMAL-QUEUE-REVIEW.json)
- [原 SDK32 最小 patch](SDK32-TO-RESULTS-FIRST-FAILURE.patch)
- [自含分类函数原件](war_results_first_failure_classifier_extension.py)
- 公共复用函数：`tools/g2_saved_campaign/war_results_first_read_outcome.py`；普通产品源不会自动加载场次分类器。

第五批 `18393cce` 的 Official 38967170365 与 Linear 38967169970 均已 success。SDK32 的既有连续进展与本候选验证分开记录；稳定 30 年、低于 1 秒／日、0.5 秒／日目标均未完成，优先级保持这个顺序。没有 Native 新构建、WAL 或其他性能实验混入本包。
