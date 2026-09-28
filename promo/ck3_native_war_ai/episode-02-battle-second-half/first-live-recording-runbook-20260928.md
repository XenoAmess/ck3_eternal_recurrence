# E2-02/03 首次追击补录：受管操作 runbook

**状态：待屏幕交接；本 runbook 尚未执行实拍。** 按主任务队列等 R0271、R0266 依次释放 `ck3-screen`，由本任务 `promo-episode02-capture-20260928` 领取后执行。所有下列命令使用 `cmd` 和显式 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`；`<...>` 均须替换为当次新路径。当前 no-launch 证据见[源档预检](pursuit-capture-preflight-20260928.md)，录制器见 [`record_bounded_gameplay.py`](record_bounded_gameplay.py)。

## 0. 冻结源、版本和画面目标（不占屏）

1. 再查 [xar-promo 最新正式 Release](https://github.com/XenoAmess/xar_promo_toolchain/releases/latest)、wheel SHA 与本次解释器 `-m xar_promo --version`、`start-run --help`、`preserve --help`。2026-09-28 当前是 `v0.2.1`、wheel SHA `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`；若更新先同步 requirements 与解释器，再开新 run。以 `D:/w/e2/promo/ck3_native_war_ai/episode-02-battle-second-half/project/promo-project.json` 的**当次精确 bytes** `start-run --run-id <NEW_E2_02_03_RUN_ID> --run-directory <NEW_EXTERNAL_XAR_RUN>`；当前只读 SHA `B00B4EA61EC2240ED1CBF718F654137F5ABED3953E1E3BF7F204CC38332F2778` 仅作今日基线。保存 CLI version/help、requirements、ProjectConfig snapshot 与 run manifest 身份；后续 config 改动只影响下一 run。
2. 再对 `episode01-full-edge-attempt-004/trace-d27-immutable.ck3` 与 `ck3-output/interactive-requests-responses/trace-d27-save.json` 算 SHA，应分别为 `F085D8ABB89A354FA1004DBE8800505BC952AA8A68C0EA21AAB788F9875FEEB3` 和 `5198123BD71842624A3FB933492F78C3BB11C65D2DED634E3965FDC79B90A012`。**F085 是 004 运行内生成的第 27 日 checkpoint，不是 004 的冷载源**；004 真正从 attempt-002 `45CCE7E9A7E505C878F661333DE30D6B459DA638259A9E99990A226CE564245F` 冷载。新 E2-02/03 从 F085 冷载属于另一 source pair，来源卡须如实写这层差异。CK3 EXE 应为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；预检配对的 `cwb2` DLL/injector 分别为 `EB643577E0DE6214582A667B3C6C52DB712CA75E46374BECB9DB5C36204F67E7`、`CE8A20C7B25A697058AB69B03629D6B7655BB2935AD147DF1E84895A826BF247`。若任何一项变化，先对**新配对**建独立无启动 preflight；旧 READY 回执不能借用。
3. 新轨不得把旧 004 的 72/72、69/69、三日伤亡、终局以及 085/024 的 `-50` 数值无标注配在新画面。首批镜头定位为**新回放的上下文和终局画面**：每一天以本 run 的原生 snapshot/control/terminal 回执与 raw/mark 绑定；若后续计算卡仍用 004/085/024 原始数字，就在画面上清楚标“历史研究 attempt / 独立回放”，并以来源卡隔开。E2-09 的 `-50` 面板须等其新配对 live 自己证实；这条 E2-02/03 不给它签核。

创建原生 run 的命令形状如下；`--run-directory` 指向新的外置目录，而非旧 TTS/视频 attempt：

```text
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe -m xar_promo start-run D:\w\e2\promo\ck3_native_war_ai\episode-02-battle-second-half\project\promo-project.json --run-id <NEW_E2_02_03_RUN_ID> --run-directory <NEW_EXTERNAL_XAR_RUN>
```

## 1. 屏幕交接、分辨率与 Steam 离线

1. 接到主代理的释放通知后，再 `poll --ack`、`list` 任务总线，确认 R0271/R0266 都没有 `ck3-screen:acquired`；领取本任务独占，并仅在此后运行 `tools/desktop_steam_offline_recovery.py inspect`。若仍有 CK3/FFmpeg 或他人屏幕占用，继续等待，不运行 `capture_session.py`。屏幕资源取得、释放均用总线 `status` 记录。

```text
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe D:\workspace\.codex-task-bus\bin\codex_task_bus.py poll --task promo-episode02-capture-20260928 --ack
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe D:\workspace\.codex-task-bus\bin\codex_task_bus.py list
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe D:\workspace\.codex-task-bus\bin\codex_task_bus.py status --task promo-episode02-capture-20260928 --state running --repo D:\w\video_capture_prep --resource ck3-screen:acquired --summary "E2-02/03 managed capture owns screen"
```

`status --resource` 只在 `list` 确认空闲且主代理已交接后执行；期间每 15 分钟 `heartbeat --task promo-episode02-capture-20260928`。
2. 当前只读 Win32 模式报告 `D:/workspace/ck3_native_war_ai_promo_work/episode02-display-mode-probe-20260928-a01/modes.json` SHA `F0F3370BA8129872FC86C8461B39DC744B95E3E5A47C60C1E4AB3FD150821D28`：桌面现为 **1024×768**，原生驱动列出 **1920×1080**；R0004 CK3 为窗口化 **1280×720**，当前桌面可能裁掉右侧。获屏且 CK3 已关闭后，先重新只读执行 [`inspect_display_modes.py`](inspect_display_modes.py)。若远程桌面稳定，可用 Windows 原生显示模式设置切到 1920×1080，保留变更前模式与原图，立即核实真实 GDI、`pyautogui.size()`、新截图和 ToDesk 画面；失败则恢复原模式。**任何显示模式变化之后重做 Steam 新鲜画面与下方几何检查**。若不能升分辨率，可拍的下限是整个 CK3 窗口/全部必要 HUD 真正落在当前桌面内；只按实际低分辨率登记 raw，成片插值不称原生 1080p/1440p。窗口或战报被裁切就停录，记录 RED。
3. 在新外置 `<OFFLINE_ATTEMPT>` 中运行 `tools/desktop_steam_offline_recovery.py recover --task-id promo-episode02-capture-20260928 --output-dir <OFFLINE_ATTEMPT>`。如有 stale/黑屏按[桌面恢复合同](../../../docs/ck3-native-ai/desktop-steam-offline-recovery-2026-09-27.md)处理，不把窗口边缘变化当 Steam 离线。直接打开 **原尺寸** `probe-N/steam-moved.png`，审阅当前“离线模式”、画面/时钟新鲜度；未看到就停。审阅后 120 秒内运行下列收据写入器，显式人工见证是前提：

```text
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\episode-02-battle-second-half\write_reviewed_offline_receipt.py --freshness-receipt <OFFLINE_ATTEMPT>\probe-N\steam-frame-freshness.json --output <OFFLINE_ATTEMPT>\reviewed-steam-offline.json --reviewer video_capture_prep --i-reviewed-current-offline-ui
```

## 2. 单个受管 CK3 与先行几何片

再次 `poll --ack`、确认屏幕归属与离线回执后，在**全新** `<LIVE_ATTEMPT>` 运行下式。`--frontend-timeout 900` 给前端 900 秒、检查点地图门 1800 秒：本机 R0002 首 turn 约 912 秒、R0003 900 秒地图门曾超时、R0004 使用 1500 秒。总外层 wall 应覆盖两段等待、后续 3600 秒 interactive、清场余量；短等待 RED 只说明启动时限不足，不判源素材失败。`capture_session.py` 的上限已在本工作包扩到 1500 秒；启动前必须确认此补丁已在执行工作树。

```text
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe -B promo\ck3_native_war_ai\integration\capture_session.py --game-dir C:\SteamLibrary\steamapps\common\CRUSAD~1 --bridge-dll D:\workspace\cwb2\xar_ck3_bridge.dll --bridge-injector D:\workspace\cwb2\xar_ck3_bridge_injector.exe --state-dir <LIVE_ATTEMPT>\ck3-state --output-dir <LIVE_ATTEMPT>\ck3-output --pipe-name \\.\pipe\<NEW_UNIQUE_E2_02_03_PIPE> --checkpoint-save D:\workspace\ck3_native_war_ai_promo_work\episode01-full-edge-attempt-004\trace-d27-immutable.ck3 --checkpoint-receipt D:\workspace\ck3_native_war_ai_promo_work\episode01-full-edge-attempt-004\ck3-output\interactive-requests-responses\trace-d27-save.json --frontend-timeout 900 --interactive-seconds 3600 --steam-offline-receipt <OFFLINE_ATTEMPT>\reviewed-steam-offline.json --capture
```

单独保留此命令会话；不传 `--record-debug-desktop`。等 `<LIVE_ATTEMPT>/ck3-output/native-start-readback.json` 明确 `postcondition_verified=true`、source save/receipt SHA 相符、玩家 `29829`、第 27 日 `date_raw=53146872`，再审游戏窗口在真实桌面内完整可见；仅 `map_ready` 不代表 HUD 好拍。窗口聚焦/面板动作优先现有 typed MCP/UIA，鼠标兜底遵守原图尺寸、当前 `pyautogui.size()`、预览内容矩形和 `tools/desktop_coordinate_map.py --receipt`；键盘焦点与英文布局另验。

先按[源档预检文档的几何命令](pursuit-capture-preflight-20260928.md#一个正式-recorder-与时间锚点)录独立 2 秒 `geometry-e2-02-03-a01`。其 `geometry-admission.json` 要显示 GDI=`pyautogui.size()`；`recorder-final.json` 要是 `ENCODED_UNREVIEWED`，`native_desktop_size_match=true`、`first_frame_size_match=true`，且首帧实际分辨率、截图与完整 CK3 窗口相符。几何片永久保留，不充当剧情 clean span。失败即停，在下一次新 attempt 重做，不裁切、不循环、不通过后期放大伪装。

## 3. 600 秒连续 raw 与逐日 mark

几何片过门后按[600 秒 `record` 命令](pursuit-capture-preflight-20260928.md#一个正式-recorder-与时间锚点)启动 `<LIVE_ATTEMPT>/recording-e2-02-03-a01`，此命令会话一直运行到自动封口。另一个命令会话按下面顺序逐步执行；`pursuit_live_step.py advance` **只有**前一 `observe`、同日原生 control 和原始 screenshot mark 齐全且该 FFmpeg 仍运行才会推进日期。若分叉，helper 写源绑定/日期/阶段回执后 typed stop；不强改脚本让旧数值“继续吻合”。

| 日 | 先 `observe` 并拍实物 | 随后 mark `kind` 与 control 文件 | 再 `advance` |
| --- | --- | --- | --- |
| 27 | 主阶段、地图/战斗面板、玩家 ArmyID 18 | `d27-paused`，`e2-d27-control.json`，`date_raw=53146872` | 27→28 |
| 28 | 追击第 0 日，双方军队/面板 | `d28-pursuit`，`e2-d28-control.json`，`53146896` | 28→29 |
| 29 | 追击第 1 日 | `d29-pursuit`，`e2-d29-control.json`，`53146920` | 29→30 |
| 30 | 追击第 2 日 | `d30-pursuit`，`e2-d30-control.json`，`53146944` | 30→31 |
| 31 | 追击第 3 日；旧 100 秒 raw 缺此段 | `d31-pursuit`，`e2-d31-control.json`，`53146968` | 31→32 |
| 32 | 正常终局、玩家败退、战争面板；旧 raw 缺此段 | `d32-terminal`，`e2-d32-terminal.json`，`53146992` | 不推进 |

每行命令的真实参数示例（以第 28 日为例；当前 run 如分叉必须停用旧值）：

```text
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\episode-02-battle-second-half\pursuit_live_step.py observe --session-output <LIVE_ATTEMPT>\ck3-output --day 28
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\episode-02-battle-second-half\record_bounded_gameplay.py mark --workdir <LIVE_ATTEMPT>\recording-e2-02-03-a01 --kind d28-pursuit --date-raw 53146896 --combat-id 16777218 --war-id 4 --control <LIVE_ATTEMPT>\ck3-output\interactive-requests-responses\e2-d28-control.json --capture-screenshot --note new_replay_context_not_old_004_numeric_card
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\episode-02-battle-second-half\pursuit_live_step.py advance --session-output <LIVE_ATTEMPT>\ck3-output --day 28 --recorder-workdir <LIVE_ATTEMPT>\recording-e2-02-03-a01
```

第 32 日用 `observe --day 32` 后 `mark --kind d32-terminal --control ...\e2-d32-terminal.json`；再留战报/战争面板的可读尾段。每个 mark 的时间是近似墙钟，不是媒体 PTS；确保原始 UI 可见、没有弹窗遮挡。若新同 run 的 WarID 4 战分、终局 winner/retreat 与历史不同，就只讲本次可读事实，旧 `-50` 和结果板退回历史标记。此 helper 不读取或证明 004 的逐团 72/72 parity；正式计算卡必须另以本次原生逐团回执重算并审计，未完成则以历史研究板呈现。

## 4. 封口、冻结、释放

1. 等 600 秒 recorder 自行退出，保存 `recorder-intent/start/end/final.json`、`marks.jsonl`、FFmpeg stdout/stderr、raw、完整 `ffprobe.json`、逐 stream 首末 PTS 与每帧原件；检查 `ffmpeg_exit_code=0`、probe 成功、尺寸门。中断、异常、短片和 partial 均保留为 RED，不复用同目录。**`ENCODED_UNREVIEWED` 不等于 clean span**：随后逐帧核 PTS 单调/断档、HUD/日期/CombatID/面板可见性和一倍速原速审片，才能出新 clean span。
2. Recorder 封口后运行 `pursuit_live_step.py finish --session-output <LIVE_ATTEMPT>\ck3-output --day <LAST_OBSERVED_DAY>`，等待受管 `capture_session.py` 退出，保存 `capture-report.json` 或 `entry-failure.json`、`session-result.json`、MCP 请求/响应、`operator-steps`、截图、游戏日志及原始 state/profile。受管报告即便仍为 `raw_video:null`，也不覆盖外部 recorder 的 raw 身份；adapter bundle 必须另建、只读校验。

```text
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\episode-02-battle-second-half\pursuit_live_step.py finish --session-output <LIVE_ATTEMPT>\ck3-output --day 32
```

若在分叉处提前停止，将 `32` 换成最后一次实际 `observe` 日；已写过 `finish` 请求不得重发。
3. 在新的外置 `<CLOSURE_DIR>` 用 [`freeze_capture_attempt.py`](freeze_capture_attempt.py) 对本次 live attempt、离线取证目录、源档与真实回执逐文件哈希；它要求受管报告或 failure 已写出、ProjectConfig snapshot 与 RunManifest 匹配，拒绝读写中变化的文件。`INDEXED_UNREVIEWED` 只证明冻结索引，不证明画面合格。其命令及随后最少两条 `xar-promo preserve` 命令如下；更多逐日回执、geometry、FFmpeg stderr、脚本和报告按唯一 artifact-id 顺序保全，外置原件始终保留：

```text
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\episode-02-battle-second-half\freeze_capture_attempt.py --attempt-root <LIVE_ATTEMPT> --offline-attempt <OFFLINE_ATTEMPT> --source-save D:\workspace\ck3_native_war_ai_promo_work\episode01-full-edge-attempt-004\trace-d27-immutable.ck3 --source-receipt D:\workspace\ck3_native_war_ai_promo_work\episode01-full-edge-attempt-004\ck3-output\interactive-requests-responses\trace-d27-save.json --run-manifest <NEW_EXTERNAL_XAR_RUN>\run-manifest.json --recorder-workdir <LIVE_ATTEMPT>\recording-e2-02-03-a01 --output <CLOSURE_DIR>\asset-index.json
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe -m xar_promo preserve --run-manifest <NEW_EXTERNAL_XAR_RUN>\run-manifest.json --artifact-id e2-02-03-raw --collection raw --role capture <LIVE_ATTEMPT>\recording-e2-02-03-a01\raw\e2-pursuit-d27-d32.mkv
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe -m xar_promo preserve --run-manifest <NEW_EXTERNAL_XAR_RUN>\run-manifest.json --artifact-id e2-02-03-closure-index --collection derived --role report <CLOSURE_DIR>\asset-index.json
```

补完整 `report.json`/timeline/evidence-index/clean-frame-gates 后才调用 CK3 adapter 只读验证；没有真实 clean span 不得宣称成片可用。
4. 冻结本次外置目录和 SHA 后释放 `ck3-screen`，在任务总线更新 status 并通知主代理；后续 E2-09/E2-04/05 按队列独立获取屏幕。若显示模式曾调整，结束前按屏幕交接约定恢复并核对真实尺寸，再以新鲜图确认 Steam 仍离线。
