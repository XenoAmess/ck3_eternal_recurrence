# 冻结桌面与 Steam 离线预检／恢复

`tools/desktop_steam_offline_recovery.py` 提供独立于 CK3 启动的 Windows 预检。`inspect` 只读 ToDesk 服务、CK3 进程、唯一 Steam 窗口及任务总线屏幕占用；`recover` 在取得本任务的 `ck3-screen:acquired` 后，复用 `steam_offline_fresh_frame.py` 将 Steam 窗口水平移动 20 像素、采集移动前后桌面图并复位窗口。画面随真实窗口移动而变化，才报告 `fresh_frame_needs_offline_visual_review`。它从不切换 Steam 在线状态，也不启动 CK3。

使用已验证有 `psutil`、`pywin32`、`pyautogui` 和 Pillow 的项目 Python；每次 `recover` 必须给全新的仓库外 `--output-dir`：

```text
<verified-python> tools/desktop_steam_offline_recovery.py inspect
py D:\workspace\.codex-task-bus\bin\codex_task_bus.py status --task <本任务ID> --state running --resource ck3-screen:acquired --repo <本工作树>
<verified-python> tools/desktop_steam_offline_recovery.py recover --task-id <本任务ID> --output-dir <全新外置目录>
```

Steam 不在前台时，可在本任务独占屏幕期间加 `--bring-steam-forward`；脚本按窗口句柄置前、验证前台身份，并在取证后尽量恢复原前台窗口，不使用桌面点击。`recover` 拒绝活跃的其他屏幕占用、运行中的 CK3、非唯一 Steam 窗口及未知／转换中的 ToDesk 服务状态。任务总线的过期记录仅在其登记 PID 也已消失时不再算活跃占用。每次真正操作前及重试前再次检查租约和 CK3 进程。

ToDesk 服务若已停止，`recover` 会尝试启动。若服务正在运行，默认**绝不重启**。只有第一次窗口移动取证明确报出 `desktop capture did not respond to live Steam movement`，且调用者显式传 `--restart-running-todesk-on-stale`、屏幕租约仍独占、CK3 仍未运行、常见 FFmpeg/OBS 录制进程均不存在时，才尝试停止并启动 ToDesk，然后取第二次新鲜帧。录制进程存在时报告 `restart_blocked` 并保留该 attempt；仍须人工核查其他会话是否使用画面。这一步可能短暂中断远程桌面。不要用该参数处理单纯的网页黑屏、旧截图或未验证的远端画面卡顿。

每次 attempt 保留 `events.jsonl`、`recovery.json` 和 `probe-1/`（有重试则再建 `probe-2/`）。`recovery.json` 的 `fresh_frame.receipt_path` 指向成功的新鲜帧回执，`fresh_frame.image_identity` 给出截图路径、字节数和 SHA-256；原回执 `probe-N/steam-frame-freshness.json` 的 `moved_identity` 也保存同一身份。`outcome` 只表达桌面响应性；`steam_offline_status_observed` 永远为 `null`。**操作人必须亲自审阅本次新截图**中的 Steam 离线标识，才可把它当作离线实证；黑屏、服务运行、旧图 hash、窗口移动成功都不单独证明离线。必要时还须查当前账号是否被其他机器占用，再按项目的 CK3 启动门禁继续。

2026-09-27 本机静态／实测证据：历史 `ck3-xqol-phase2-20260910` 屏幕记录已过期约 16 天，登记 PID 2696 不存在；CK3 与常见录屏进程不在运行。取得新独占租约后，`D:\workspace\ck3_native_war_ai_promo_work\steam-offline-recovery-20260927-002\recovery.json` 报 `fresh_frame_needs_offline_visual_review`，`probe-1/steam-frame-freshness.json` 中 `moving_edge_changed=true`，`moved_identity.sha256=205DAEA6748C6A2508C9DB02F113D9525F4FC6ADFF8737221AE6DE04349CC9D6`；原始 Steam 窗口矩形 `[0,0,962,768]` 经 `[20,0,982,768]` 后已复位。人工查看同次 `steam-moved.png`，Steam 左下显示“离线模式”。ToDesk 服务 PID 4792 始终运行，未触发重启，未启动 CK3。

聚焦静态测试：`<verified-python> tools/test_desktop_steam_offline_recovery.py`。它覆盖其他任务占用时拒绝操作、失活占用的 PID 复核、新鲜帧不重启服务、录制中拒绝重启、显式 stale 分支才重启及失败时尽力恢复服务。此工具验证本机桌面采集响应，不检测另一台远端查看器是否正在显示最新帧；远端仍卡住时需在远端另取当前画面作独立核验。
