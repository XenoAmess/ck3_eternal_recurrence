# CK3 战争结果窗口自动清除

普通自动游玩在暂停地图上优先检查原生 `war_results` 窗口。Native 只在已确认的 CK3 1.20.0.4 构建上公开 `query-war-results-window-v1` 和 `close-war-results-window-v1`；MCP 对应提供 `ck3_query_war_results_window_v1` 和 `ck3_close_war_results_window_v1`。查询与关闭都使用当前快照修订、连接代际和独立的游戏主线程执行回执。关闭只投递到该窗口的 `close_button`，必须在原生操作后再次读取，确认窗口不存在或不可见，才记为界面关闭成功。界面关闭本身不计为战争胜利。

普通规划在战争集合变化时立即重新检查；否则，自上次确认窗口清除起每六个游戏日检查一次。带有这两个 Native 能力的生命推进单次最多六日，因此结果窗口出现后，目标是在七个游戏日内发现并关闭。若原始关闭请求超时，保留请求 ID 并收取原回执，不重复点击。缺少可核实的原生窗口读回时保留未完成状态。

2026-10-14 的候选源码位于独立 `war-results-auto-dismiss-20261014` 工作树，B14 Native DLL 绑定当前 D 盘演示的游戏进程。该演示在 `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation37/`，录像位于其 `recordings/`，桌面 1 的 OBS 场景同时包含游戏与决策悬浮窗。首次实机 `responses/0005-1-result.json` 在战争仍进行时读到 `war_results` 已注册但不可见，执行了查询而未误发关闭。`responses/0051-1-result.json` 是六个游戏日后的再次查询，同样不可见。**可见结果窗口的自动关闭和七日内读回仍待这场战争实际结束后验收**；查询 ACK、源码测试与录制画面均不能替代该项实机结果。
