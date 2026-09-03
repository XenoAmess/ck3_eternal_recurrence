# CK3 direct-union 分组启动 A/B（2026-09-03）

## 输入与范围

- 隔离 direct-union product：201 files、15,243,695 bytes；包含 b1、incident、manager、b2、workforce 与 case-kernel 组合，另挂载 Phase2 seed fixture。
- CK3 1.19.0.6 / Steam buildid 23530548；当前 matching Release bridge；完整 pinned settings 与 warm shadercache。
- report：`Z:\ck3_mod_rewrite\_runtime\formal-phase2-direct-union-20260903\report.json`
- 未载入存档、未执行 gameplay、未点击协议/通知/商店、未购买或付款。

## 结果

- PID 24600 于 12:24:43（Asia/Shanghai）启动；`debug.log` 于 12:25:28 达到 `Total of : 881`。
- 约五分钟内没有 `End loading of history`、`Setting idler 'Frontend'` 或 bridge-ready receipt；进程保持响应，约 11.8 GB working set。
- `error.log` 仅有两条明确 parser 错误：`zg361_b1_peer_submission_actor_trigger` 与 `zg361_b1_peer_submission_recipient_trigger` 未定义。
- WM_CLOSE 等待后无响应；中断 disposable observer 触发受控清理，独立进程清单确认 CK3 与 injector 已消失。原始 report 的 close/shutdown 字段因 observer 中断为空。

## 判定

direct-union v1 仍未在限定窗口进入 Frontend，且存在可定位的 B1 trigger 缺口。下一轮应使用已替换新版 `zg361_triggers.txt` 的 direct-union-v2，验证修复这两个未知符号后是否解除长加载。
