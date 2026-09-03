# CK3 b2 依赖闭包 A/B（2026-09-03）

- 输入：core+b1+case_kernel+b2，75 files、8,223,681 bytes；新版 triggers；matching Release bridge、完整 pinned settings/warm shadercache。
- report：`Z:\ck3_mod_rewrite\_runtime\formal-phase2-b2-20260903\report.json`
- PID 63240 于 12:44:27 启动；12:45:12 达到 `Total of : 881`；12:45:18 出现 `Setting idler 'Frontend'`、`End loading of history`，startup duration 50.343936 秒。
- 收到 bridge hello；WM_CLOSE 12:45:23，退出码 0，`cleanup_proven=true`，CK3/injector/watchdog 树清空。
- `error.log` 2772 行，主要为 unused variables/list targets；未见阻止 Frontend 的 parser 错误。

判定：b2 依赖闭包启动 GREEN。incident、manager、b2 单组均能约 50 秒到 Frontend；下一步可验证不含 workforce 的多组 union，再针对 workforce 长加载做最小区段二分。
