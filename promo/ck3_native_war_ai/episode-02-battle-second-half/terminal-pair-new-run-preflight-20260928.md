# E2-09 新配对终局轨：无屏幕预检与下次窗口步骤

2026-09-28。目标是让**下一次**受管窗口从第 27 日冻结档取得同一新 run 的终局原生 writer 数字、战场/战争 UI 和原速 raw，再决定 E2-09 能否展示精确算式。本文件和随附三个脚本均未启动 CK3、未读桌面、未占用 R0271 屏幕。此前 `024` 研究回执仍是历史研究来源；其旧 DLL 的精确字节已不在原路径，**不得把旧动态数值、旧 UI 或旧脚本启动结果充作新回放证据**。

## 已核对的源档与二进制

| 对象 | 本次静态核对 | 准入含义 |
| --- | --- | --- |
| 第 27 日 immutable save | `episode01-full-edge-attempt-004/trace-d27-immutable.ck3`，52,871,423 bytes，SHA-256 `F085D8ABB89A354FA1004DBE8800505BC952AA8A68C0EA21AAB788F9875FEEB3` | 与原 `trace-d27-save.json` 所证保存字节、日期 raw `53146872`、角色 `29829` 一致；源回执 SHA `5198123BD71842624A3FB933492F78C3BB11C65D2DED634E3965FDC79B90A012`。不得改旧存档。 |
| CK3 游戏 EXE | 1.19.0.6 当前 `ck3.exe` SHA `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` | 与 `capture_session.py` 的精确构建 pin 一致。 |
| `024` 启动 sidecar | `launch-argv.json` SHA `DBB646A76ABCBE565300AF2E363FCE8BA5C6ED6CDF82D050AE495F4799C6A3F9`，记录旧 DLL SHA `5FA16EABCD2FD77730E96F11A3C030401EA14B58926E6504007008533B6929DE` | 同一路径现已是另一组字节，旧 `start.py`/`launch-argv.json` 不能重放为 024 的精确环境。 |
| 当前候选 DLL / injector | `episode01-denominator-build-007/` 当前 DLL SHA `FCAFBA2A73E1EEF1E2651ADD40F71CE66B9FE16E4E61BD014DBA65C9965AEBD8`，injector SHA `3773042110D9E207FD02E00BF5376A033E71B70433B6B650088550A522B581C5` | 两者为 x64 PE，DLL 含 checkpoint 读图所需三个静态能力字符串；**静态检查不证明**新的分母钩子会在 writer 现场产生八桶。 |

[无屏幕静态脚本](prepare_terminal_pair_static.py)已写出**新的、不可覆盖**回执 `D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-pair-static-20260928-a03.json`，SHA-256 `F986701CF66B396AF1737B1D714717FDE7B6293B62FF9CE00CD9275939FC70C0`，状态 `STATIC_GREEN_FOR_NEW_NO_LAUNCH_PREFLIGHT_ONLY`。它冻结了主 worktree 的 `capture_session.py` 精确字节（与独立分支同 SHA）、候选二进制和两个不同输出根的 `argv` 数组；a01/a02 静态回执原样保留。主仓已验证解释器 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe` 为 Python 3.14.7，`mcp 2.0.0`、`pywin32 312`、`Pillow 12.3.0`、`psutil 7.2.2` 均可用，ffmpeg/ffprobe 可定位。

## 下一个独占屏幕窗口的顺序

1. **先领窗口，再做受管入口。** 等 R0271 释放 `ck3-screen:acquired`，确认没有其他 CK3/录像占用。下一次受管实机前按仓库 AGENTS 取得并**直接审阅新的 Steam 离线画面**；旧 `024` 的 2026-09-26 离线截图不够。若远程画面疑似冻结，先走恢复与窗口位移取证；所有鼠标兜底使用 `desktop_coordinate_map.py --receipt`，键盘输入遵守英文布局/焦点门。
2. **独立 no-launch 门。** 使用[阶段调用器](invoke_terminal_pair_stage.py)配 a03 静态回执执行 `--stage no-launch --execute`；它把 `capture_session.py` 的 `--capture` 排除在 argv 外，输出只写新 `episode02-terminal-pair-20260928-a03-preflight/`。要求 `preflight.json` 的 `result=READY_FOR_BOUNDED_LIVE_ATTEMPT`、`ck3_started=false`、候选 DLL/injector、源档和 EXE SHA 与静态回执逐项一致。这个入口会拒绝当前仍有 CK3 进程的环境；不要在 R0271 占屏时试跑。若 RED，保留该 attempt，另选 a04 根目录，不覆盖。
3. **正式有界采集。** 在新鲜离线回执已审阅、屏幕租约仍独占后，阶段调用器 `--stage live --offline-receipt <本次回执> --execute` 才会给 `capture_session.py` 显式 `--capture`。它使用独立 `...-a03-live/` 的新 userdir/pipe，复制冻结 save 而不改源文件；`hold=30`、`frontend-timeout=360`、热服务 `interactive=1200` 秒、恢复上限 `300` 秒。启动后核对加载的暂停日期、角色、CombatID `16777218`、WarID `4`、ProvinceID `2633` 及双方军队；若身份或日期变了，停止推进并保全 RED。
4. **另录真正的游戏 raw。** `capture_session.py` 的可选 debug 桌面录像含启动流程、默认也不生成可剪 clean span；它不能代替本步。在墨西拿居中且战斗 UI 可见后，另起 append-only FFmpeg 原速桌面录制，保存启动 UTC/monotonic、命令、stderr 和 raw SHA；在第 27 日战斗/WarID 面板先留前态。镜头需包含第 28–31 日原生日期与追击战报、第 32 日普通终局 winner/败军退出旧 CombatID，以及同一新 run 的 WarID `4` 面板前后；录完按 PTS 标 clean span、审每段头尾的画面可见性。录制进程**只录**，不能同时运行会自行推进日期的 `capture_battle_with_hotspot.py`，避免双重 life-advance。当前[新轨驱动器](drive_terminal_pair_live.py)本身不录视频。
5. **一日一命令，保留当次 writer。** 在 raw 已开始、日期与 UI 锚点已留后，运行驱动器 `--execute`。它只连接本次 `capture_session` 的 hot service：第 27–31 日每次取 snapshot、control，再以当前 revision 执行一次 `life-advance`；第 32 日起查询 `ck3_query_battle_terminal_transition_v1`，最迟第 36 日或 900 秒停。每个请求/响应保持独立文件与 SHA，另存 UTC/monotonic mark；新终局若非 `normal_result`、writer 未 `recorded`、八桶/倍率/分子不全或 WarID 改变，驱动器以 RED 保全，**不把旧 024 数值填空**。它不执行旧 `024/start.py` 或旧 `024/run.py`。
6. **新数值核算与画面配对。** 只有新 driver `status=new-run-native-writer-inputs-captured-not-yet-projected` 时，[只读投影器](project_terminal_pair_numbers.py)才逐字节核对同一新 run 的每日 snapshot/control/advance 和 terminal 响应 SHA，按 native hard-loss、八桶分母、整数比例、加载的 CB 倍率和 `5,000,000` Q100000 单场 cap 复算 row 与战争攻方符号。GREEN 只叫 `numeric-parity-green-footage-and-voice-unverified`；还须检验 raw SHA、camera/WarID/date 的 clean PTS、UI 前后、人工 1× 阅读。将原始媒体、sidecar、失败尝试和核算报告按新视频 run 的 append-only manifest 保全。若新 run 的数值恰巧等于旧 024，也必须更新来源卡到**新 run**；若不同，先改 E2-09 数据 JSON/SVG、旁白相关数字并另起正式配音 run。不能从战争总分 UI 差分倒推出本场 writer 分子或八桶。

以下命令只列入口；先以实际路径替换尖括号占位符。**本次未执行任何 `--execute` 或 CK3 录制命令**。路径中的 a03 是已冻结候选，若下一窗口候选字节变化或 a03 任一目标目录已有 attempt，应运行静态脚本创建 a04，而非覆盖。

```cmd
tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\episode-02-battle-second-half\invoke_terminal_pair_stage.py --static-receipt D:\workspace\ck3_native_war_ai_promo_work\episode02-terminal-pair-static-20260928-a03.json --stage no-launch --execute
tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\episode-02-battle-second-half\invoke_terminal_pair_stage.py --static-receipt D:\workspace\ck3_native_war_ai_promo_work\episode02-terminal-pair-static-20260928-a03.json --stage live --offline-receipt <本次新鲜离线回执> --execute
tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\episode-02-battle-second-half\drive_terminal_pair_live.py --static-receipt D:\workspace\ck3_native_war_ai_promo_work\episode02-terminal-pair-static-20260928-a03.json --run-root D:\workspace\ck3_native_war_ai_promo_work\episode02-terminal-pair-20260928-a03-live --execute
tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\episode-02-battle-second-half\project_terminal_pair_numbers.py --static-receipt D:\workspace\ck3_native_war_ai_promo_work\episode02-terminal-pair-static-20260928-a03.json --driver-result D:\workspace\ck3_native_war_ai_promo_work\episode02-terminal-pair-20260928-a03-live\terminal-pair-driver-result.json --output D:\workspace\ck3_native_war_ai_promo_work\episode02-terminal-pair-20260928-a03-live\terminal-pair-numbers.json
```

当前可复核的**无屏幕**检查是静态回执 GREEN、驱动器默认 plan-only 回读、四个新脚本 `py_compile`。`capture_session` 的真正 no-launch preflight、runtime denominator hook、原速 raw 与新整数对拍全是下次独占窗口的待验门，不能从本次静态 GREEN 推断。

原速录制命令形状沿用现有 `capture_battle_with_hotspot.py` 的 `gdigrab`、30 fps、无鼠标光标和 H.264 CRF 18 参数；它需要在另一进程运行，先保全实际 argv 与启动时钟，再由操作方在终局 UI 停留结束后向 FFmpeg stdin 发送 `q` 并保存 stderr、退出码、ffprobe 和 SHA：

```cmd
ffmpeg -n -hide_banner -loglevel warning -f gdigrab -framerate 30 -draw_mouse 0 -i desktop -c:v libx264 -preset ultrafast -crf 18 -pix_fmt yuv420p -an D:\workspace\ck3_native_war_ai_promo_work\episode02-terminal-pair-20260928-a03-live\e2-09-raw.mkv
```

这条命令本身只产生 raw，**不会**生成 adapter 合格的 clean span；须再以当次 request/response 时间戳、录像 PTS 和画面可见身份逐段编证据索引。
