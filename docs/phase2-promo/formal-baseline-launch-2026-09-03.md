# CK3 无 mod/无 bridge 正式基线启动回执（2026-09-03）

本回执记录一次受控的原生 CK3 启动。它只验证游戏本体能否在正常交互桌面进入 Frontend，不代表 Phase2 bridge、mod 或宣传素材采集已经通过。

## 运行身份

| 字段 | 值 |
|---|---|
| 启动时间（本地） | 2026-09-03 09:29:54 左右 |
| 目标桌面 | `WinSta0\\Default`，Session 1 交互控制台 |
| CK3 可执行文件 | `Z:\\SteamLibrary\\steamapps\\common\\Crusader Kings III\\binaries\\ck3.exe` |
| EXE SHA-256 | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| 进程 | PID `4776` |
| 参数 | `-gdpr-compliant -userdir=<隔离 profile>` |
| profile | `Z:\\ck3_mod_rewrite\\_runtime\\formal-baseline-20260903-0928\\profile` |
| bridge / injector | 未加载 |
| mod / mod-content | 不存在 |
| 存档加载 | 未执行 |

## 结果

- 进程窗口标题为 `Crusader Kings III`，分辨率 `2560×1440`。
- 屏幕实证显示完整 CK3 中文主菜单（单人、继续游戏、新游戏、载入游戏等），不是只创建进程或停在启动器。
- `logs/debug.log` 明确记录：
  - `[09:32:01] Setting idler 'Frontend' with NO init options`
  - `[09:32:01] Total startup duration: 125.720343 seconds`
- 使用正常 `WM_CLOSE` 关闭窗口；日志记录 `[09:34:15] Quit: Quit event from os`，进程随后消失。
- 没有生成 crash dump 或 exception 文件；本次 `error.log` 为 0 字节。
- 初始监控脚本在启动后自身表达式报错，未保存 `Popen.ExitCode`；因此回执不伪造数值退出码，使用 Frontend + clean WM_CLOSE + 无 crash 文件作为退出证据。

## 可复核工件

- 截图：`Z:\\ck3_mod_rewrite\\_runtime\\formal-baseline-20260903-0928\\desktop-09-33.png`
- 运行目录：`Z:\\ck3_mod_rewrite\\_runtime\\formal-baseline-20260903-0928\\`
- CK3 debug 日志：`Z:\\ck3_mod_rewrite\\_runtime\\formal-baseline-20260903-0928\\profile\\logs\\debug.log`
- CK3 system 日志：`Z:\\ck3_mod_rewrite\\_runtime\\formal-baseline-20260903-0928\\profile\\logs\\system.log`
- 预检身份：`Z:\\ck3_mod_rewrite\\_runtime\\formal-baseline-20260903-0928\\preflight.json`

## 结论与边界

这次 GREEN 排除了“CK3 原始 EXE 完全无法启动”以及“必须由 mod/bridge 才能到 Frontend”的说法。它没有排除自动化链的启动上下文、bridge 生命周期、存档加载或生产 mod 投影问题；下一次工程动作应针对这些差异做一次受控 A/B，而不是继续重复裸 CK3 启动。
