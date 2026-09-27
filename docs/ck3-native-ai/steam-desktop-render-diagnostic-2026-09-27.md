# Steam 离线 UI 取证阻点：桌面与 CEF 渲染诊断

截至 2026-09-27 01:46 UTC，076/079 的 Steam 启动前门仍是 **environment RED**。本轮只读诊断表明，桌面采集管线能够取得新内容，但当前 Steam 主窗口内容为黑色，任务栏时钟也停留在 `4:06`；因此不能从这些帧人工确认**当前** Steam 离线状态。没有启动 CK3、切换 Steam 模式、重启 Steam/Explorer/DWM 或改变显示设置。此结论不改动 076/079 及以前实机 attempt 的原始身份与业务结果。

原始图像、脚本和 JSON 回执均在外置目录 `D:/workspace/ck3_native_war_ai_promo_work/desktop-capture-freeze-static-20260927/`，以下文件名均相对于该目录。当前 Steam 主窗口为 HWND `198194`、`steamwebhelper.exe` PID `5820`，进程创建时间 `2026-09-26T07:14:02.195467Z`；诊断结束时窗口矩形和前台焦点已恢复。

| 观察 | 原始回执 | 能确认的边界 |
| --- | --- | --- |
| 会话/显示 | `environment-inventory.json`、`display-monitor-inventory.json`：活动 console session 1、`Default` desktop，DWM composition 开启，桌面 `1024×768`，Display1 为 NVIDIA GeForce RTX 3060 Laptop GPU、60 Hz；WMI 只报“默认显示器”，没有枚举出 monitor child。 | 当前显示拓扑已冻结；不能据此断定物理显示器断开或驱动失效。 |
| GDI 系列 | `capture-compare.json`：`pyautogui`、PIL ImageGrab、Win32 BitBlt 的 1024×768 像素相同；`ffmpeg gdigrab` 图也可见黑色 Steam 窗和 `4:06`。`ddagrab` 限时等待未取得帧，安全停止。 | 单一截图库缓存不是充分解释；`ddagrab` 没有可用结果，不能把超时解释为黑帧或设备错误。 |
| 新鲜合成层 | `overlay-response-test.json`：短命 270×76 时间戳窗口从 `09:36:39` 变为 `09:36:40`，两张原图 SHA-256 分别为 `CE83B6E444676529BDD8835EE04FBDA75A83EC1B3153203EA3B2C422D2F69872` 与 `F74AFC745B85D17A53467276241DBE80740B5A3C5BC3A9EF611C613DD60CAC21`；销毁后原图回到此前 SHA `46AC6B166815DF44E7CEE04AD677E04953ED3D8C6FA18A1C9827BBF2D5BC18E1`，Steam 矩形与焦点恢复。 | 桌面能够合成并采到**新**窗口内容；不能把整个 compositor 或所有截图路径称为冻结。新窗口的时间戳不证明既有 Steam 内容新鲜。 |
| 独立 Windows Graphics Capture | `wgc-window-default-border-receipt.json`：Steam HWND 单帧 `962×768`，PNG SHA-256 `9A30B47D0E7715F3E6F6B68E55FADCDFD456615A72D2B7B2431DA9B3D9A38CA7`；`wgc-monitor-index1-default-border-receipt.json`：显示器单帧 `1024×768`，PNG SHA-256 `EDDA90E03832C16685D22E1A0C57756CCDECD3A5A8A0A833BD37421EB1637B38`。人工查看：前者 Steam 内容全黑，后者 Steam 区全黑、任务栏时钟仍为 `4:06`。 | WGC 也只能取到当前呈现的黑色 Steam 表面，无法从中识别在线/离线；这不是 GDI 专有故障。单帧不证明黑表面从何时开始或哪一个组件导致。 |
| Steam 进程/事件 | `webhelper-roles-health.json`：主/browser PID `5820`、GPU PID `19048`、两个 renderer PID `19888`/`22328` 仍运行，有线程和句柄；HWND 的 `WM_NULL` 响应且非 Win32 hung。`render-log-inventory.json` 中 `webhelper_gpu.txt` 最后写于本次 Steam 启动、无 `device_lost` 文本命中；`webhelper.txt` 后续有记录。`display-event-inventory*.json` 的可读 System/Application 范围未见同期显示驱动/DWM 错误；DxgKrnl 细分频道查询权限不足。 | 存活、消息响应、没有匹配日志都不足以证明 CEF/GPU 正常渲染；也没有足够证据归因于显卡驱动。 |
| 可恢复重绘 | 076 原 `steam-printwindow-diagnostic/`、`steam-restore-diagnostic/` 及本轮 `steam-width-refresh-test.json`：`PrintWindow` 成功码但画面黑；移动/`RedrawWindow`、最小化→恢复/`DwmFlush`、真实宽度 `962→1000→962` 均未恢复 Steam 文本，操作后矩形、前台焦点恢复。 | 这些有限、可恢复的表面刷新未打通离线 UI 门；不再重复同类操作。 |

本轮定位到的是**既有窗口内容异常**：新建 overlay 可更新，Steam CEF 主窗口保持黑色，Explorer 时钟显示也未随系统时间前进。Steam 与 Explorer 是否共享同一故障根因、CEF GPU/renderer 是否停滞、默认显示器拓扑是否参与成因，均仍未知。Steam 同次启动日志的 `Start offline - 1`、配置 `WantsOfflineMode=1` 及 loopback 网络观察只证明离线意图/间接状态，不能补成实时 UI 签核；见 [Steam 运行时离线证明边界](steam-offline-runtime-proof-boundary.md)。

下一步应先恢复**可读、可证明新鲜**的 Steam UI，再按 [Steam 帧新鲜度合同](steam-offline-frame-freshness.md) 生成新的 HWND/PID/create-time 绑定原图、人工读取“离线模式”，最后才重做相应 attempt 的源档/EXE/DLL/任务总线/前次清场门禁。当前会话没有找到可安全自动执行且有效的进一步表面刷新。重启 Steam webhelper 或整个 Steam、切换硬件加速、重启 Explorer/DWM、重置显示驱动或改显示拓扑，可能改变离线状态、丢失窗口/会话或影响其他进程；必须先确认没有 CK3/录制占用、保存现状，并为 Steam 模式和窗口重新建立完整门禁，不能把这些操作当作本轮已验证修复。若需本机协助，应由能看到实际桌面的人检查显示连接与 Steam 客户端是否能交互并确认离线文字；如须重启客户端，恢复后的证据必须视为**新进程/新会话**，不得继承旧截图的证明力。
