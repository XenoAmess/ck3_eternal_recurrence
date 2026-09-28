# E2-02/03 第 27 日源档补录：无启动预检与录制命令

2026-09-28，R0271 独占 CK3 屏幕期间完成。**此文件只冻结候选和下一次操作；未启动 CK3、未录制新 raw、未生成 clean span。** E2-02/03 优先于 E2-01 上下文镜头。

## 冻结的候选与真实回执

| 项 | 精确来源 | 本次独立复核 |
| --- | --- | --- |
| 第 27 日源档 | `D:/workspace/ck3_native_war_ai_promo_work/episode01-full-edge-attempt-004/trace-d27-immutable.ck3` | 52,871,423 bytes，SHA-256 `F085D8ABB89A354FA1004DBE8800505BC952AA8A68C0EA21AAB788F9875FEEB3` |
| 真正的保存回执 | 同 attempt 的 `ck3-output/interactive-requests-responses/trace-d27-save.json` | 13,401 bytes，SHA-256 `5198123BD71842624A3FB933492F78C3BB11C65D2DED634E3965FDC79B90A012`；`body.checkpoint.status=saved`、size/SHA 与源档一致，`date_raw=53146872`、角色 `29829`，原版 `enabled_mods=[]`、`xar_off`。 |
| 战斗身份回读 | 同 attempt 的 `trace-d27-before-control.json` | 当日仍为 main 阶段，`CombatID=16777218`、墨西拿省份 `2633`、玩家军 `18`；第 28 日 `term-d28-control.json` 才显示 pursuit、phase day 0。不能把第 27 日源档描述成已在追击阶段。 |
| CK3 1.19.0.6 EXE | `C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe` | 95,206,008 bytes，SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。 |
| bridge DLL | `D:/workspace/cwb2/xar_ck3_bridge.dll` | 3,301,888 bytes，SHA-256 `EB643577E0DE6214582A667B3C6C52DB712CA75E46374BECB9DB5C36204F67E7`。 |
| injector | `D:/workspace/cwb2/xar_ck3_bridge_injector.exe` | 39,936 bytes，SHA-256 `CE8A20C7B25A697058AB69B03629D6B7655BB2935AD147DF1E84895A826BF247`。 |

第 27 日档可从真实保存回执加载，但新加载会成为**新独立回放**。即使 CombatID 相同，也要逐日重新取控制报告、逐团值和画面；004 既有追击三日零差数字不能直接配新回放。旧 `gameplay-messina-pursuit-to-terminal.mkv` 虽名为 `to-terminal`，实测 100 秒、抽帧只到第 30 日，不能代替第 31–32 日或新回放的完整录像。

## 本次 no-launch 回执

使用主工作树已验证解释器 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`，对上述**成对**源档/真实保存回执执行 `capture_session.py`，没有传 `--capture`。新外置目录是 `D:/workspace/ck3_native_war_ai_promo_work/episode02-pursuit-e2-02-03-preflight-20260928-a01/`，不复用任何旧 RED attempt。结果：`READY_FOR_BOUNDED_LIVE_ATTEMPT`、`ck3_started=false`、`runtime_capabilities_verified=false`；当前没有 CK3/recorder PID 的只读清单也写在回执内。它是环境与源档校验，**不是游戏加载成功或 Steam 离线画面证据**。

| 文件 | SHA-256 |
| --- | --- |
| `ck3-output/command.json` | `965E238A87AD5C477E3C9D3EF99D1D77C74D7A1F213D0DC19033EBE742E142A2` |
| `ck3-output/preflight.json` | `7974A660680C21AB3419BF054748B3F26CE3161862A66778185C18F9DE34E741` |
| `ck3-output/static-capability-strings.json` | `EAE2678D3C73F4A0E77A86C74587F9DE4C3201B9741A0297C3606B2224639054` |

## 下一次 live attempt：先获屏，再启动

1. 同步战争任务队列，等 R0271 释放 `ck3-screen`，领取独占并核查没有 CK3/录制进程。按 `AGENTS.md` 用当次实时窗口变化和新截图审阅 Steam **离线模式**，保存新的 UI 回执。若画面 stale、黑屏或状态不明，先走桌面恢复和新鲜度门；不能复用今天的 no-launch 回执或历史离线截图。
2. 再次核查上述源档、真实保存回执、EXE、DLL、injector 的 bytes/SHA；在**全新的** `episode02-pursuit-e2-02-03-live-...` 目录调用下列受管入口。`--capture` 才启动游戏；保持 `--record-debug-desktop` 缺席，让一个单独 recorder 拍正式原速画面。`<NEW...>` 与 `<FRESH...>` 由当次真实值替换，不能把预检目录重用成 live。

```text
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe -B promo\ck3_native_war_ai\integration\capture_session.py --game-dir C:\SteamLibrary\steamapps\common\CRUSAD~1 --bridge-dll D:\workspace\cwb2\xar_ck3_bridge.dll --bridge-injector D:\workspace\cwb2\xar_ck3_bridge_injector.exe --state-dir <NEW_LIVE_ATTEMPT>\ck3-state --output-dir <NEW_LIVE_ATTEMPT>\ck3-output --pipe-name \\.\pipe\<NEW_UNIQUE_E2_PURSUIT_PIPE> --checkpoint-save D:\workspace\ck3_native_war_ai_promo_work\episode01-full-edge-attempt-004\trace-d27-immutable.ck3 --checkpoint-receipt D:\workspace\ck3_native_war_ai_promo_work\episode01-full-edge-attempt-004\ck3-output\interactive-requests-responses\trace-d27-save.json --interactive-seconds 3600 --steam-offline-receipt <FRESH_REVIEWED_OFFLINE_RECEIPT> --capture
```

3. 加载后等受管入口稳定确认 actor `29829`、date `53146872`、CombatID `16777218`、WarID `4`，再对战场居中、打开面板并保存原始画面；不能凭 native `map_ready` 推断 HUD 已可拍。第 27 日先拍主阶段前态；第 28、29、30、31 日每个暂停边界取原生控制/逐团读数、带来源的原始截图与录制 mark；第 32 日拍正常终局、败退和战争面板前后。任何日期/事件轨迹分叉即以本次 run 的新值重算算式与旁白。

## 一个正式 recorder 与时间锚点

受管 session **不**负责正式 gameplay raw。它的 `--record-debug-desktop` 只覆盖启动故障，不能代替这个 recorder。游戏已加载且屏幕归属仍有效时，使用 Python `subprocess.Popen` 启动以下单个 FFmpeg argv，`CREATE_NO_WINDOW`，并在 live attempt 保存完整 argv、启动 UTC、`time.monotonic_ns()`、PID、stdout/stderr 路径与进程结束码；所有输出路径为全新文件，FFmpeg `-n` 拒绝覆盖。旧 100 秒上限漏了后两日，本轮给 600 秒窗口，终局后继续保留原始尾段；实际够不够由最终画面和 PTS 判定。

```text
ffmpeg -nostdin -n -hide_banner -loglevel warning -f gdigrab -framerate 30 -draw_mouse 0 -i desktop -t 600 -c:v libx264 -preset ultrafast -crf 18 -pix_fmt yuv420p -an <NEW_LIVE_ATTEMPT>\raw\e2-pursuit-d27-d32.mkv
```

时间锚点采用**追加写入** `marks.jsonl`：每条记录 `kind`（recorder-start、d27-paused、d28-pursuit、d29、d30、d31、d32-terminal、recorder-end）、UTC、monotonic ns、相对 recorder-start 的近似墙钟秒数、原生日期/phase/CombatID/WarID、该次控制回执与截图的 bytes/SHA。截图本身也保全。mark 的墙钟秒数**不是视频 PTS**；录制启动、编码器和桌面采样会有偏移。实际媒体封口后运行下列 ffprobe 读取完整 decoded frame PTS（将 stdout/stderr、argv、退出码保全到新文件），并通过逐帧可见 HUD 与 mark 对齐，再给每一段 clean span 的**实际 PTS 起止**、可见性审核和来源身份。第 31 日、终局若仍不可见，该 span 为 RED，不借静帧或文件名补洞。

```text
ffprobe -v error -select_streams v:0 -show_streams -show_format -show_frames -of json <NEW_LIVE_ATTEMPT>\raw\e2-pursuit-d27-d32.mkv
```

最后把 raw、完整 probe、marks、原生控制与截图、检查点/构建身份、每个 clean span 及其逐 PTS 审核保存为新 capture bundle；调用当前正式 `xar_promo.adapters.ck3.load_capture_bundle` 只读验证。录制进程退出且媒体完整解码之前，不能登记完整镜头。机器验证不代替 1× 人工审片。当前既有 source save、真实 checkpoint 回执与本机 DLL/injector 均齐，尚无来源机配对文件缺口，不向 `OneDrive/WAR` 写空请求。
