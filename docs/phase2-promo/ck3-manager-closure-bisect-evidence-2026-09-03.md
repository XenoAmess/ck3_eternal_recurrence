# CK3 manager 依赖闭包 A/B（2026-09-03）

- 输入：core+b1+case_kernel+manager，77 files、8,374,508 bytes；新版 triggers；matching Release bridge、完整 pinned settings/warm shadercache。
- report：`Z:\ck3_mod_rewrite\_runtime\formal-phase2-manager-20260903\report.json`
- PID 54344 于 12:42:04 启动；12:42:50 达到 `Total of : 881`；12:42:56 出现 `Setting idler 'Frontend'`、`End loading of history`，startup 约 52 秒。
- 收到 bridge hello；WM_CLOSE 12:43:01，退出码 0，`cleanup_proven=true`，CK3/injector/watchdog 树清空。
- `error.log` 3090 行，主要为 unused variables/targets；未见阻止 Frontend 的 parser 错误。

判定：manager 依赖闭包启动 GREEN。manager 不是当前 broad/workforce 组合长加载的充分原因；后续应验证多组 union 与 workforce 分段。
