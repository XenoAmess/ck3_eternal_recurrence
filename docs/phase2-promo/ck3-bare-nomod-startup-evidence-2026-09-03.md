# CK3 裸启动验证（2026-09-03）

- EXE：`Z:\SteamLibrary\steamapps\common\Crusader Kings III\binaries\ck3.exe`；工作目录为 `binaries`；命令参数：`-nolauncher -noWorkshop -debug_mode -gdpr-compliant -userdir=<disposable profile>`。
- profile：`Z:\ck3_mod_rewrite\_runtime\bare-nomod-20260903\profile`，由已知有效 settings、account、dlc_signature 和 warm DX11 shadercache 组成；无 Mod、无 bridge、无存档。
- PID 4072 启动后，`debug.log` 于 12:48:49 出现 `Setting idler 'Frontend'` 与 `End loading of history`，12:48:50 记录 `Total startup duration: 42.253045 seconds`；`error.log` 为 0 bytes。
- 12:49:38 日志记录 `Quit: Quit event from os`；正常关闭后进程清单为空，无 forced stop、无 crash RVA。
- 证据目录：`Z:\ck3_mod_rewrite\_runtime\bare-nomod-20260903\artifacts`（`screen.png`、`debug.log`、`error.log`）。

判定：正式 Steam EXE/CWD、`-userdir` 和无 Mod 启动链均 GREEN；后续可在同一 profile 逐步加入 bridge，隔离 bridge/guard 影响。未执行 gameplay、协议点击、商店或购买动作。
