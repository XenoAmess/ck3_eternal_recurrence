# E2-09 a04：长冷启动的新配对终局轨准入

2026-09-28，屏幕前静态修订。a03 的 `frontend-timeout=360` 对同事回报的本机约 **912 秒**冷启动不足；a03 静态回执与[原流程](terminal-pair-new-run-preflight-20260928.md)保留为历史。本次**只**增新的 a04 静态/准入回执并放宽[受管入口](../integration/capture_session.py)的 frontend 上限；未执行 `--capture`、任何 no-launch 实例、Steam/CK3、桌面录制或高负载测试。

## a04 冻结条件

| 边界 | a04 值 | 依据/限制 |
| --- | ---: | --- |
| frontend 单阶段 | **900 秒** | `capture_session.py` 参数上限从 600 扩至 900；`NativeHeadlessGameplayDriver` 与 `native_session` 只要求正数，未发现内部 600 秒硬限。 |
| checkpoint map 等待 | **1800 秒** | 现有入口 `wait_checkpoint_map(timeout_seconds=2 * args.frontend_timeout)`；由 900 秒 frontend 精确推导，不单独改加载器。 |
| interactive hot service | **2400 秒** | 地图就绪后留给相机/战斗与 WarID `4` 面板、原速录像、逐日采集及清场。 |
| recovery / outer session | **600 / 5220 秒** | outer 为 `3×900 + 30 hold + max(600,2400) + 90`。限时扩大不是成功保证；超时仍保留 RED。 |
| 逐日驱动 | **1800 秒、最迟第 36 日** | 热服务应在地图就绪后再启动驱动。每次只推进一个原生日；旧 `024` 动态数值不进入判定。 |

外置 a04 静态回执 `D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-pair-static-20260928-a04.json` SHA-256 `B41F8E443A0D49EFE15ED3E3054D5DC16E8579E37221048EF27C537A65DA2D80`，状态 `STATIC_GREEN_FOR_NEW_NO_LAUNCH_PREFLIGHT_ONLY`。a04 准入回执 `D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-pair-admission-20260928-a04.json` SHA-256 `D06ABEA1FFEBD7C5608CDFD9AFE2563C68056572FC3EAD7980589180CF31032E`，状态 `STATIC_READY_SCREEN_AND_RUNTIME_PENDING`。后者明确 writer、战分面板、raw PTS 与人工 1× 的待验门，不是任何实机通过回执。

静态脚本逐字节复核第 27 日 save SHA `F085D8ABB89A354FA1004DBE8800505BC952AA8A68C0EA21AAB788F9875FEEB3`、原保存回执 SHA `5198123BD71842624A3FB933492F78C3BB11C65D2DED634E3965FDC79B90A012`、CK3 EXE SHA `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`、当前 DLL `FCAFBA2A73E1EEF1E2651ADD40F71CE66B9FE16E4E61BD014DBA65C9965AEBD8` 与 injector `3773042110D9E207FD02E00BF5376A033E71B70433B6B650088550A522B581C5`。原 `024` sidecar 记录的是旧 DLL `5FA16EABCD2FD77730E96F11A3C030401EA14B58926E6504007008533B6929DE`，当前路径不同 SHA；这证明**旧环境不可精确重启**，不否定旧 024 研究回执的历史身份，却禁止把其数值作为新录像的同轨证据。新 DLL 的分母钩子是否运行、八桶是否完整，仍只可在新 writer 回执中判。

## 下一次独占屏幕窗口：最短动作链

1. **R0271 释放屏幕后**领取 `ck3-screen:acquired`；取得、直接审阅并保存本次新鲜 Steam 离线画面。确认无其他 CK3/录制，疑似 stale 时按仓库恢复流程取窗口位移证据。
2. 用 a04 静态回执运行[阶段调用器](invoke_terminal_pair_stage.py)的 `--stage no-launch --execute`。它使用新 `...a04-preflight/`，**无 `--capture`**；检查 `preflight.json` 的 `READY_FOR_BOUNDED_LIVE_ATTEMPT`、`ck3_started=false` 和精确 save/DLL/injector/EXE，并用 `command.json` 与 a04 静态回执核 900/1800/2400 预算。RED 保留并另开 a05，不改写 a04。
3. 用同一 a04 及**新鲜离线回执**运行 `--stage live --execute`，让受管 `capture_session.py` 在新 `...a04-live/` 冷启动。等稳定暂停地图：回读日期 raw `53146872`、actor `29829`、CombatID `16777218`、WarID `4`、ProvinceID `2633`；在 WarID `4` 面板及墨西拿战斗面板先录前态。独立 FFmpeg raw recorder 需在**第一次** life-advance 前开始，并保存 start clock、argv、stderr；不能同时跑会自行推进日期的 `capture_battle_with_hotspot.py`。
4. 运行[有界逐日驱动](drive_terminal_pair_live.py) `--execute`。它记录每日 snapshot/control/一次 life-advance 的原始请求响应 SHA、UTC/monotonic mark；第 32 日起等待 `normal_result` writer，最迟第 36 日或 1800 秒。期间原速录完整日期变化；终局后继续录 winner、败军退出旧 CombatID、WarID `4` **同一新 run** 面板后态，再正常结束 raw 并 probe/SHA。若新 run 提前分叉或 writer 无分母/倍率/row，保留 RED，不补旧 024 数值。
5. [整数投影器](project_terminal_pair_numbers.py)只读当次新回执，逐日核 SHA、分子、八桶、CB 倍率、50 单场 cap、row 和战争攻方符号。只有数字 GREEN、同轨 raw clean PTS、前后 WarID UI、可见 attempt/日期来源卡及 1× 完整人工审阅均通过，才允许 E2-09 上屏。战争面板总分并不等于该 battle row；从 UI 的 `-50` 倒推 writer 输入无效。数值若不同，重建 E2-09 JSON/SVG、旁白和正式配音；即使数值相同，也必须把来源身份换成新 run。

入口命令沿用[前版的四阶段写法](terminal-pair-new-run-preflight-20260928.md)，但把所有 `a03` **替换成 `a04`**，且本次静态回执路径为 `episode02-terminal-pair-static-20260928-a04.json`。这份 a04 回执绑定 `D:/w/ett` 工作树内本次修订的 `capture_session.py` 字节；若 cherry-pick 后该工作树不再存在，应从集成后的精确文件重新生成 **a05**，不要改 a04 或偷偷换路径。

**本次验证**：a04 静态生成成功；四个 E2-09 脚本和受管入口通过 `py_compile`；阶段调用器、逐日驱动默认 plan-only 只读返回 a04 计划。真正 no-launch、实机启动、raw、writer、战分 UI 和新数字对拍仍为未执行。
