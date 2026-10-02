# 冻结桌面与 Steam 离线预检／恢复

`tools/desktop_steam_offline_recovery.py` 提供独立于 CK3 启动的 Windows 预检。`inspect` 只读 ToDesk 服务、CK3 进程、唯一 Steam 窗口及任务总线屏幕占用；`recover` 在取得本任务的 `ck3-screen:acquired` 后，复用 `steam_offline_fresh_frame.py` 将 Steam 窗口水平移动 20 像素、采集移动前后桌面图并复位窗口。画面随真实窗口移动而变化，才报告 `fresh_frame_needs_offline_visual_review`。它从不切换 Steam 在线状态，也不启动 CK3。

使用已验证有 `psutil`、`pywin32`、`pyautogui` 和 Pillow 的项目 Python；每次 `recover` 必须给全新的仓库外 `--output-dir`：

```text
<verified-python> tools/desktop_steam_offline_recovery.py inspect
py D:\workspace\.codex-task-bus\bin\codex_task_bus.py status --task <本任务ID> --state running --resource ck3-screen:acquired --repo <本工作树>
<verified-python> tools/desktop_steam_offline_recovery.py recover --task-id <本任务ID> --output-dir <全新外置目录>
```

Steam 不在前台时，可在本任务独占屏幕期间加 `--bring-steam-forward`；脚本按窗口句柄置前、验证前台身份，并在取证后尽量恢复原前台窗口，不使用桌面点击。`recover` 拒绝活跃的其他屏幕占用、运行中的 CK3、非唯一 Steam 窗口及未知／转换中的 ToDesk 服务状态。任务总线的过期记录仅在其登记 PID 也已消失时不再算活跃占用。每次真正操作前及重试前再次检查租约和 CK3 进程。

2026-09-28 本机重启后的首个恢复 attempt 发现 Steam 窗口处于最小化状态：仅用 `SW_SHOW` 无法保证恢复成可采集的窗口，随后 `SetForegroundWindow` 抛出底层 pywin32 异常。工具现在对最小化窗口使用 `SW_RESTORE`，并把置前失败转换成明确的恢复错误，保留该 attempt，不绕开新鲜画面门禁。聚焦测试覆盖最小化恢复和置前拒绝。随后的全新恢复 attempt 取得原始 1024×768 画面 `D:/ck3-research-artifacts/war31-h2743-20260928/steam-offline-post-reboot-02/probe-1/steam-moved.png`，SHA-256 `795BA96C21DCF730506531E1A5728F162C52EF8C56EDF7B1985878D8B0C217B1`，人工确认左下“离线模式”及更新后的任务栏时间。H2743 新 `attempt-04` 只读实机结束后另取 `steam-offline-post-army-01/probe-1/steam-moved.png`，SHA-256 `6F6F046346EC1E3E10A2BFF1837AE78C4946072121CD6A5416960B359B433C32`，再次人工确认离线。

088 前检揭示 Windows 的 `SetForegroundWindow` 可能异步生效：同次调用立刻读前台曾误报失败，随后只读 `inspect` 已看见 Steam 在前台。工具现在最多等待两秒确认目标 HWND，仍未确认则拒绝采集；相应模拟时序测试已覆盖。该次保留失败的 004/005 attempt，再以全新 006 attempt 取得移动窗口的新鲜帧，人工看到左下“离线模式”，未改 Steam 模式，也未重启 ToDesk。

ToDesk 服务若已停止，`recover` 会尝试启动。若服务正在运行，默认**绝不重启**。只有第一次窗口移动取证明确报出 `desktop capture did not respond to live Steam movement`，且调用者显式传 `--restart-running-todesk-on-stale`、屏幕租约仍独占、CK3 仍未运行、常见 FFmpeg/OBS 录制进程均不存在时，才尝试停止并启动 ToDesk，然后取第二次新鲜帧。录制进程存在时报告 `restart_blocked` 并保留该 attempt；仍须人工核查其他会话是否使用画面。这一步可能短暂中断远程桌面。不要用该参数处理单纯的网页黑屏、旧截图或未验证的远端画面卡顿。

2026-09-28 H2743 复验发现一项误报：窗口真实移动使边缘像素变化，但底下的桌面仍冻结，右侧任务栏时钟在约一小时后仍为 01:32，Steam 区域变黑。此时不允许把 `moving_edge_changed=true` 当作离线确认。若已人工审阅一张至少两分钟前、同分辨率且时钟可见的原图，可给 `recover` 加 `--stale-clock-reference <那张原图> --stale-clock-rect LEFT TOP RIGHT BOTTOM`；矩形是原始桌面像素中的**时钟区域**，不是预览缩放坐标，必须完整处于移动后 Steam 窗口外。工具对比新旧时钟区域的亮色字形；Steam 移动可能改变任务栏背景色，故不对比原始 RGB。字形仍完全相同便保留 `probe-N/steam-frame-stale.json` 并走明确 stale 分支；未传这组参数时保持旧的边缘位移检查。该检查只是否决疑似冻结帧，不识别离线模式，也不能用随意静止区域代替时钟。选区需人工核实确有时钟且原图年龄超过两分钟；新图仍须人工审阅离线标识。仅在独占屏幕、无 CK3／录制／其他屏幕占用的门禁下，才能同时传显式 ToDesk 重启参数。

H2743 `attempt-05` 启动前再次遇到此问题：原始 `1024×768` 截图 `steam-offline-01/probe-1/steam-moved.png`（SHA-256 `635754066BBF9B0F12E1A8DDADBF6D56F11E2B8E1084B8BDAB4F205BC63689D8`）虽显示 Steam 左下“离线模式”，但任务栏时钟停在 03:13，且与实际时间不符。第一次时钟复验因矩形碰到移动后的 Steam 窗口，被工具拒绝；保留 `steam-stale-recovery-02` 错误回执。第二次使用实际图像中的 `985,645,1022,708` 矩形，参考图年龄约 231 秒，字形像素完全不变，窗口移动也未使桌面采集响应；`steam-stale-recovery-03/probe-1/steam-frame-stale.json` 保存了 RED。工具仅在确认无 CK3 和录制进程、独占屏幕后尝试重启 ToDesk 服务，但 `sc stop ToDesk_Service` 返回错误码 5；未取得新鲜离线画面，未启动 CK3，屏幕租约已释放。此时只能等桌面会话恢复后重新取证，不能复用旧图。

H2825 再次出现“窗口边缘能移动、Steam 内容区全黑、两次完整截图哈希相同”的情形。`recover --stale-frame-reference <至少 120 秒前的 steam-frame-freshness.json> --restart-running-todesk-on-stale` 现在会核对同一 Steam HWND、桌面尺寸和移动后窗口矩形；若两次移动后截图的字节数及 SHA-256 完全相同，就保存 `steam-frame-stale.json` 并进入原有的独占屏幕、无 CK3、无录制进程的 ToDesk 重启门禁。它仍不判定 Steam 是否离线。H2825 `attempt-05/steam-offline-03` 的重复帧检查确证 RED，服务停止再次被错误码 5 拒绝；随后一次在同一桌面临时显示当秒随机挑战码的两张原始截图产生不同像素，操作人目视确认第二张中当前挑战码与 Steam 左下“离线模式”，才继续只读 CK3 启动。挑战窗不点击 Steam、不改变客户端状态，完整截图和回执保存在该 attempt 外置目录。

挑战窗沿用上述先例，仅用于 stale 后的**启动前显示层取证**。执行前按既有预检及[屏幕租约合同](../codex-task-bus.md)确认独占、无 CK3／录制／其他屏幕占用；不得作为活跃 CK3 会话的通用输入捷径。
自有瞬态窗只显示两次当秒 UTC 与不同 nonce，不点击 Steam、不改模式。分别保存两次实际请求显示的 UTC/nonce 及两张未裁切、未合成的完整原始桌面图，各绑定 bytes、SHA-256 与采集时间；审阅时间另记，失败旧图和回执保持。
操作人须直接在第二张原图读回当次 nonce，并直接审阅同图 Steam 的“离线模式”；挑战窗或两图 SHA 不同都不能自动判定 offline，也不能单独证明 Steam 内容区或后端状态新鲜。
当前挑战只证明采集响应本次显示变化；已有窗口／背景 stale 和冻结时钟事实仍保留，不称时钟已更新或整层桌面已恢复。无法读回当前 nonce 或看清离线标识时，启动前离线证据仍未闭合。

每次 attempt 保留 `events.jsonl`、`recovery.json` 和 `probe-1/`（有重试则再建 `probe-2/`）。`recovery.json` 的 `fresh_frame.receipt_path` 指向成功的新鲜帧回执，`fresh_frame.image_identity` 给出截图路径、字节数和 SHA-256；原回执 `probe-N/steam-frame-freshness.json` 的 `moved_identity` 也保存同一身份。`outcome` 只表达桌面响应性；`steam_offline_status_observed` 永远为 `null`。**操作人必须亲自审阅本次新截图**中的 Steam 离线标识，才可把它当作离线实证；黑屏、服务运行、旧图 hash、窗口移动成功都不单独证明离线。必要时还须查当前账号是否被其他机器占用，再按项目的 CK3 启动门禁继续。

2026-09-27 本机静态／实测证据：历史 `ck3-xqol-phase2-20260910` 屏幕记录已过期约 16 天，登记 PID 2696 不存在；CK3 与常见录屏进程不在运行。取得新独占租约后，`D:\workspace\ck3_native_war_ai_promo_work\steam-offline-recovery-20260927-002\recovery.json` 报 `fresh_frame_needs_offline_visual_review`，`probe-1/steam-frame-freshness.json` 中 `moving_edge_changed=true`，`moved_identity.sha256=205DAEA6748C6A2508C9DB02F113D9525F4FC6ADFF8737221AE6DE04349CC9D6`；原始 Steam 窗口矩形 `[0,0,962,768]` 经 `[20,0,982,768]` 后已复位。人工查看同次 `steam-moved.png`，Steam 左下显示“离线模式”。ToDesk 服务 PID 4792 始终运行，未触发重启，未启动 CK3。

聚焦静态测试：`<verified-python> tools/test_desktop_steam_offline_recovery.py`。它覆盖其他任务占用时拒绝操作、失活占用的 PID 复核、新鲜帧不重启服务、录制中拒绝重启、显式 stale 分支才重启及失败时尽力恢复服务。此工具验证本机桌面采集响应，不检测另一台远端查看器是否正在显示最新帧；远端仍卡住时需在远端另取当前画面作独立核验。

## 2026-10-03 Workshop 发布后的正常退出与离线恢复实证

More Tenets Slots(XA) v10 发布完成后，屏幕独占 root 多次点击官方菜单“进入离线模式”，未出现确认窗口或状态变化。随后正常执行 Exit Steam，客户端曾提示等待 CK3 关闭；当时实际 CK3 进程为 0，本机另有 7 个旧 CK3 CrashReporter，均已核对父进程不存在。Steam 随后正常退出。root 按每个报告窗口的原生 Cancel 按钮发送 `BM_CLICK` 关闭这 7 个窗口，未上传报告；每组 7 或 8 个既有 crash 文件的 SHA-256 前后全部不变。

重新打开 Steam 时保留 `-cef-disable-gpu`，再用官方菜单进入离线，约 8 秒后的新原图明确显示“离线模式”。本次窗口水平位置从 40 移至 80 时画面实时变化，随后审阅新图，CK3 仍为 0。该位移是当次画面响应证据，坐标不是后续通用默认值。最终 `steam-offline-verification.json` 于 `2026-10-02T22:29:12Z` 记录 PASS，审阅 PNG SHA-256 为 `ae469ee6cfa4529bd6dabc46462ced4e1681b479a0be4c51a2e559117b2c264a`。具体收据和原图留在独立项目的 [v10 发布报告](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/master/docs/workshop/publication-v10.md)，这里不复制完整进程命令行、上传 URL、机器路径或产物。

这次闭环验证的是“正常退出、取消已核对的本机孤儿报告窗口、重新打开、官方菜单切换、鲜图读回”的组合路径，没有隔离 A/B，不能认定 CrashReporter 是菜单无反应的单一根因。操作没有注销账号、接管远端游戏、启动 CK3或结束其他游戏。后续遇到相同现象时仍先核对当前进程、报告窗口归属和屏幕占用；本文没有新增自动离线 MCP，也没有将上述桌面取证工具扩为模式控制工具。框架作者仅记录 root 提供的实证，没有执行此次 Steam 或桌面操作。
