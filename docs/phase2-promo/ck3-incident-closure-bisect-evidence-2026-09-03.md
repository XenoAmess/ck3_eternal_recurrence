# CK3 incident 依赖闭包 A/B（2026-09-03）

- 输入：core+b1+case_kernel+incident，76 files、8,690,935 bytes；新版 4,497-byte `zg361_triggers.txt`；matching Release bridge、完整 pinned settings/warm shadercache。
- report：`Z:\ck3_mod_rewrite\_runtime\formal-phase2-incident-20260903\report.json`
- PID 52456 于 12:38:52 启动；12:39:38 达到 `Total of : 881`；12:39:43–44 出现 `Setting idler 'Frontend'` 与 `End loading of history`，启动约 51 秒。
- 收到 bridge hello；WM_CLOSE 于 12:39:49 发送，退出码 0，`cleanup_proven=true`，CK3/injector/watchdog 树清空。
- `error.log` 3634 行，当前尾部为 unused variable/list 警告；未见阻止 Frontend 的明确 unknown/parser 错误。

判定：incident 依赖闭包启动 GREEN。与 workforce+case_kernel 长加载对照，incident 不是当前 post-on_action stall 的充分原因；可继续 manager/b2 单组定位。未执行存档、gameplay、协议/商店或购买动作。
