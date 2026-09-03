# CK3 direct-union-v2 启动 A/B（2026-09-03）

- 输入：direct-union-v2，201 files、15,245,061 bytes；已替换新版 `zg361_triggers.txt`，matching Release bridge、完整 pinned settings/warm shadercache、Phase2 fixture。
- report：`Z:\ck3_mod_rewrite\_runtime\formal-phase2-direct-union-v2-20260903\report.json`
- PID 25604 于 12:31:36 启动，12:32:21 达到 `Total of : 881`；截至 5 分钟上限没有 `End loading of history`、`Setting idler 'Frontend'` 或 bridge-ready receipt。
- `error.log` 为空（v1 的两个未知 B1 trigger 已消失），但仍在 on_action 后长加载。
- WM_CLOSE 后等待无响应；中断 disposable observer 触发受控回收，独立进程清单确认 CK3/injector 已消失。原始 report 的 close/shutdown 字段为空，不能将本轮记为 Frontend GREEN。

判定：v2 已排除 v1 的 B1 trigger parser 错误，但 direct-union 组合仍未在限定窗口进入 Frontend；后续需按 incident、manager、b2 单组定位。未执行存档、gameplay、协议/商店或购买动作。
