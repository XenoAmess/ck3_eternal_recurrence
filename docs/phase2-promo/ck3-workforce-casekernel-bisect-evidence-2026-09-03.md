# CK3 workforce + case-kernel 依赖闭包 A/B（2026-09-03）

## 输入

- 隔离 product：workforce 变体（152 文件）+ `zg361_case_kernel_effects.txt` 与 `zg361_case_kernel_triggers.txt`，合计 154 文件、13,082,245 bytes。
- CK3 1.19.0.6 / Steam buildid 23530548；matching Release bridge；完整 pinned settings 与 warm shadercache。
- report：`Z:\ck3_mod_rewrite\_runtime\formal-phase2-workforce-casekernel-20260903\report.json`
- 本轮不载入存档、不执行 gameplay、不点击协议/通知/商店、不购买或付款。

## 结果

- PID 19864 于 12:17:44（Asia/Shanghai）启动；`debug.log` 于 12:18:29 达到 `Total of : 881`。
- 约五分钟内未出现 `End loading of history`、`Setting idler 'Frontend'` 或 bridge-ready receipt；进程保持响应但约 11.8 GB working set。
- `error.log` 记录 24 条解析错误，主要是 workforce endgame 引用未纳入的 manager trigger（例如 `zg361_mg_m360_collective_cost_c1_can_apply_trigger`）。
- WM_CLOSE 后等待无响应；中断 disposable observer 触发受控清理。独立进程清单确认 CK3 与 injector 均已消失。原始 report 的 close/shutdown 字段因 observer 中断为空，不能将本轮记为 Frontend GREEN。

## 判定

case-kernel 本身在 b1+case-kernel 闭包中可在约 51 秒到 Frontend；加入 workforce 后因缺少 manager 依赖出现 parser 错误并在 on_action 881 后长加载。下一步应先补齐 manager trigger/value 的最小依赖闭包，再重新进行唯一 CK3 A/B。
