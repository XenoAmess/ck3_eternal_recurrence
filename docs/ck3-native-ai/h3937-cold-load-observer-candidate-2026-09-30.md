# H3937 冷载只读观测候选（2026-09-30）

## 已冻结的 a11 RED

本候选从 `f96dc005422e87ab7748909c0d71f02a63935e49` 分支施工，不修改 a11、a10 或更早的任何实机素材。a11 的 [outer 报告](D:/ck3-research-artifacts/war-h3937-combined-live-20260929/attempt-11/outer-report.json) SHA-256 为 `5197B0CB85EDFBC11BE7DB0348B3221F31D4E8E6CEDE8A3513457D9ECF2653F3`：1800 秒没有 native paused semantic frame，六项目标查询为 0，游戏动作和日期授权均为 0。90 次 [20 秒采样](D:/ck3-research-artifacts/war-h3937-combined-live-20260929/attempt-11/readiness-progress-series.json) SHA-256 为 `AA265A64D2429DCE37BF92B4CF785D84D58F1E1DC26C126668E7B9C4DE41265D`；倒数一分钟 shader 文件数仍增加 163，pump epoch 仍增长。它们只说明冷载活动，不能证明存档被接受。

a11 [末截图原件](D:/ck3-research-artifacts/war-h3937-combined-live-20260929/attempt-11/readiness-timeout-desktop.png)为 0 字节，SHA-256 `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`；[失败回执](D:/ck3-research-artifacts/war-h3937-combined-live-20260929/attempt-11/timeout-visual-review-failure.json) SHA-256 为 `533E72168504A56A6CA38191CF53B78EFE7D1377C93EEC43C0BED5BFB5DAA357`。不存在 a11 末画面的视觉直审，不能套用 a10 的启动画面。a11 `debug.log` 为 328,533 字节，末行 `[23:44:58][D][history.cpp:1350]: Start loading of history`，文件 mtime 为 15:44:58 UTC；1800 秒门约在 15:44:40 UTC 结束。这行发生于超时后的受管宽限期，只能说明该时段仍写出日志，不能推断 1800 秒门内语义就绪或确认最终停点。

## 默认关闭的轻量观测

`collect_h3937_combined_paused_war_scope_once(..., cold_load_observation_dir=None)` 默认不建立观测目录、不调用采屏器。显式启用时要求同一全新输出目录、现有 20 秒 stall watchdog 和每次采屏前可回读的独占屏幕租约。观测器从 native capabilities 的 `bridge_pid` 取得 PID，以 Windows 进程句柄读取实际 EXE、创建时间、CPU user/kernel 时间及 I/O 读写次数和字节；PID 或创建时间改变时立即拒绝继续该候选。窗口只枚举同 PID 可见 HWND，每个 HWND 最多进行一次 100 ms 的只读 `WM_NULL` 响应探测，不点击、不发游戏命令。

每 20 秒的样本单独 `open("x")` 留存。原始桌面截图由独立隐藏子进程异步执行，每 120 秒最多一次，最多 15 次，每张最多 16 MiB，合计最多 240 MiB。每张先写唯一 `.pending.png`；独立 wall-clock timer 在 12 秒期限对精确子进程句柄 kill/wait，不依赖 readiness 轮询。即使下次轮询或清场才发现退出码 0，只要观测已逾期就保留 pending 并记 RED。定稿前再核同一 PID、创建时间、EXE 和屏幕租约；取消 timer 后 bounded join，确认其回调不再并发改写结果。随后核 PNG、大小和 SHA，才把 pending 改名为定稿 `.png`。超时、0 字节、无效 PNG、租约或身份丢失均保留 partial 与 RED 回执，不伪造画面或覆盖历史；若 helper 或 watchdog 不能退出，清场门为 RED。采屏不会阻塞 native readiness 轮询。报告中的帧保持 `CAPTURED_UNREVIEWED`，必须另行直接审阅原图才可陈述屏幕内容。CPU、I/O、窗口响应、截图和 shader cache 均只是诊断信号，native semantic paused frame 仍是六项只读查询的唯一入口。

旧 `h3937_combined_once_enable.py` 明确绑定 a11 的 no-launch、GO、screen attempt 和 R3945，其输出已被消耗。本候选不得用该入口重启 a11；未来若进入实机，需独立新 one-shot、外置 state/output/GO、live run ID 和完整准入。

## 精确存档文件读取与门

本增量不启用 WPR/ETW，也不声称观察到了 `xar_checkpoint.ck3` 的 open/read。未来若要用 File I/O trace，须在无 CK3、无 OBS/录制、无人占屏且无已有 ETW 会话时，先做**无启动探针**：确认 WPR 可用版本与权限、当前全局 session 清单、可用磁盘空间、trace profile 事件范围、输出字节与时长上限、停止和异常清理回读。实际 trace 还需新的独立候选及授权、自己的 source/target hash 和 GO；H2743 受管 live 期间不启动任何全局 trace。即使追到目标文件 open/read，也只证明尝试读取，不能证明解析成功、存档身份或 map-ready。

`open_kaishek` 对 Win32 CK3 PID、窗口消息与真实桌面采集不可适用；确定性部分由纯函数/假进程离线单测覆盖。先前 a11 前的适用性回执为 [v2](D:/ck3-research-artifacts/war-h3937-combined-no-launch-20260929/prepared-attempt-10-v2/open-kaishek-applicability-v2.json)，SHA-256 `5727915DAADE8434AD22390A4C010A731BF99450290696484F9D144787FEBBC6`。本候选没有执行新的 CK3 验收。

本 worktree 未创建相对 `.venv`；离线测试明确使用主 worktree 的 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`，版本 Python 3.14.7，Pillow、pytest、pywin32 可导入。首版提交 `c756f0a078ad60e7a0c19833812647cc1b624d94` 的独立静审为 **RED**：原实现没有独立 12 秒 deadline，且定稿前未复核进程身份；该提交保留为历史，不用于 no-launch/live。修正候选的 `test_h3937_cold_load_observer.py` 13/13（含晚完成、实际 timer 无轮询 kill/reap、起拍/定稿身份漂移和并发清场正负例）、`test_h3937_combined_paused_war_scope_run.py` 10/10、`test_h3937_combined_once_enable.py` 41/41，普通和 `-O` 均通过。独立读取当前 Python 自身 PID 的 Windows CPU/I/O API 和零窗口结果成功；这不是 CK3 进程测试，也没有桌面采集。新精确源码 HEAD、官方 CI、独立复审和官方 no-launch 仍须按下一节完成。

## 下一次准入

先冻结精确源码 HEAD 并独立静审、通过聚焦正负单测及官方 CI。待 H2743 正式清场且 CK3/OBS/FFmpeg 进程为零后，对新 HEAD 和新脚本 SHA 运行官方无启动预检，并复核原始 source pair 与新隔离 profile 哈希。实机需另分配新 ID、正确 `D:/workspace/.codex-task-bus` 排他屏幕租约、当次窗口位移原始 Steam 截图及亲自目视“离线模式”、新鲜 GO。只允许同暂停帧只读；日期、移动、攻击、投降、花费和其他游戏动作均继续禁用。任一门 RED 时保留新 attempt，不能原地重试、延长超时或复用 a11 cache。
