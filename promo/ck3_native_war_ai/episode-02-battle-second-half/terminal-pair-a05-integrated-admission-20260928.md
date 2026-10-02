# E2-09 a05：集成入口字节的静态准入

2026-09-28，只读检查 `D:/w/e2` 集成工作树的 `promo/ck3_native_war_ai/integration/capture_session.py`，SHA-256 `D62555C435E23A1057ACD0FF0C4EB834F1E52A4089E9702A1B5FB3A1D996F48A`。该入口的 frontend 参数上限是 **1500 秒**，本次选择 **900 秒**；其 checkpoint map 公式为 `2 × frontend`。独立脚本不再要求入口上限的字面值恰好是 900，而验证上限至少容纳所选预算，并把实际入口上限写进回执。a04 绑定 `D:/w/ett` 的不同入口字节，不能代替 a05。

外置 append-only [a05 静态回执](D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-pair-static-20260928-a05.json) SHA-256 `9A98CE3CA00A3EAC6049DE0722D43C95390635660809C5EAB9EEF7F5B4139ECD`；[a05 准入回执](D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-pair-admission-20260928-a05.json) SHA-256 `DB9C23ECF5633704090D97CDFAF5A61DE30913C71D25F442ACA5957908B01935`。前者状态仅为 `STATIC_GREEN_FOR_NEW_NO_LAUNCH_PREFLIGHT_ONLY`，后者为 `STATIC_READY_SCREEN_AND_RUNTIME_PENDING`。两者都声明未启动 CK3、未接触桌面、未验证运行时分母钩子。入口文件再次变动须用新 attempt 重新生成，不能改写 a05。

| 预算或身份 | a05 冻结值 |
| --- | ---: |
| frontend 入口允许上限 / 本次选择 | 1500 / **900 秒** |
| checkpoint map 等待 | **1800 秒** |
| interactive hot service / recovery | **2400 / 600 秒** |
| outer native session | **5220 秒**（`3×900 + 30 hold + max(600, 2400) + 90`） |
| 逐日驱动 | **1800 秒**，最迟第 **36** 日 |
| 第 27 日原存档 / 保存回执 SHA-256 | `F085D8ABB89A354FA1004DBE8800505BC952AA8A68C0EA21AAB788F9875FEEB3` / `5198123BD71842624A3FB933492F78C3BB11C65D2DED634E3965FDC79B90A012` |
| CK3 EXE / 本次候选 DLL / injector SHA-256 | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` / `FCAFBA2A73E1EEF1E2651ADD40F71CE66B9FE16E4E61BD014DBA65C9965AEBD8` / `3773042110D9E207FD02E00BF5376A033E71B70433B6B650088550A522B581C5` |
| 源帧标识 | date raw `53146872`，actor `29829`，CombatID `16777218`，WarID `4`，ProvinceID `2633` |

## 下一屏幕窗口的最短链

1. **R0271 释放屏幕后**取得 `ck3-screen:acquired`；获取并直接审阅本次新鲜 Steam 离线画面，保存回执。若入口 SHA 与表中不符，停止并另建 append-only 静态回执。
2. 以 a05 静态回执调用 [阶段调用器](invoke_terminal_pair_stage.py) `--stage no-launch --execute`。读取新 `...a05-preflight/` 的 `preflight.json`，必须是 `READY_FOR_BOUNDED_LIVE_ATTEMPT`、`ck3_started=false`，并逐项核 save、DLL、injector、EXE、入口 SHA。no-launch 不带 `--capture`，不能将它当作实机录制。
3. 以同一 a05 和新鲜离线回执运行 `--stage live --execute`，进入隔离的 `...a05-live/`。稳定暂停后核源日期、actor、CombatID、WarID、ProvinceID；先拍墨西拿战斗和 WarID `4` 战分面板前态。**第一次**推进日期前启动独立 30 fps 原始录像，保存 recorder argv、start clock、stderr 和原始 PTS；不得并行启动其他会推进日期的驱动。
4. 对同一 live root 调 [有界驱动](drive_terminal_pair_live.py) `--execute`，每日只执行一次 life-advance，保存原生 snapshot/control 与请求响应 SHA、UTC/monotonic mark。第 32 日起观察 `normal_result` writer，最迟第 36 日或 1800 秒停。终局后拍 winner、败军退出旧 CombatID 及 WarID `4` 面板后态，再结束录像并做 probe/SHA。
5. [整数投影器](project_terminal_pair_numbers.py)只用**该新 run**逐日响应核分子、八桶分母、已加载 CB 倍率、50 单场 cap、row 和战争攻方符号。还须对上同轨 raw clean PTS、前后 WarID `4` UI、attempt/日期来源卡，经人工 1× 完整审阅，才允许 E2-09 写入精确数字。旧 024 DLL SHA `5FA16EABCD2FD77730E96F11A3C030401EA14B58926E6504007008533B6929DE` 的动态数值不能移作 a05 证据。

本次只运行静态身份脚本、阶段调用器与逐日驱动的 **plan-only**、脚本语法编译；未运行 `--execute`、no-launch 实例、CK3、raw recorder、writer 或 UI 校验。
