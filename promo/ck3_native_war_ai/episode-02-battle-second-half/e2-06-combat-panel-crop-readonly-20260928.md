# E2-06：1920×1080 战斗面板下沿取材门

2026-09-28 只读核验。未触碰当前 CK3、桌面模式、游戏设置或 recorder。本文只安排**新镜头**的取材；旧 raw、截图、marks、RED 与受管会话原样保留。

## 已在本机看到的事实

- `D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-06-d11-live-20260928-a01/screens-battle-cleared-a01/desktop.png` 是 1920×1080 原始桌面截图，SHA-256 `1D382F8F0093F8983B2685FC01E6D8C14EFFECE22FC243E621BAB9578633739A`；战斗窗在底部打开，但下部超出画面。先前 `screens-pregeometry-a01/desktop.png` SHA `77DA73D5244EDFB0EBD260D5688A48E465B8B44F32751E887424C6E22BA8B311` 和相机居中后的 `screens-postcamera-a01/desktop.png` SHA `D03866245EF9DE16C2E3B68CE9188AF5664146DBDF9F9945AB77EA8C874F25F4` 证明地图机位已改善，不能解决面板下沿。
- 同一隔离 profile 的 `ck3-state/profile/pdx_settings.txt` 本轮只读 SHA-256 `10C7728EE668E4E7F59C57ECFBDDB4C6EE75230D386B08D7157DB6760E1EE79F`：`GUI.scale` 为 `1.3`；`display_mode=fullscreen`，`windowed_resolution=1920x1080`。历史截图显示实际 raw 几何为 1920×1080，设置文件中的分辨率值不能单独替代媒体探测。
- CK3 原版 `game/gui/window_combat.gui` 开头把 `combat_window` 定成 `size={875 330}`、`parentanchor=bottom|hcenter`、`movable=no`，全文无 `scroll` 或 `collapse` 控件。因此拖动或滚动**整个战斗窗**不是已证可用的修复。原版 `jomini/settings_layout.txt` 第 56–64 行将 `GUI.scale` 放在 Interface/界面页；`game/gui/settings/setting_types.gui` 第 142–146 行显示保存按钮调用 `JominiSettingsWindow.SaveAndClose`，第 108、197–199 行分别暴露全局和逐项重启提示。设置元数据中的 **该项是否需重启**没有在这些文本中给出，必须由实际 UI 提示和改后图判定。
- `inspect_display_modes.py` 的旧只读 `modes.json` 列出 2560×1440、32 bpp、60 Hz；这是驱动候选，**没有证明当前远程桌面切换稳定，也没有证明 CK3 在该模式可完整显示面板**。

## 屏幕占用最短的执行顺序

1. 若本次 600 秒 raw 已开始，先按原设定自然封口，保留它的原 bytes/SHA 与 PTS 报告。不要在同一 raw 中途更改 GUI 比例或桌面模式，也不要把该片中缺失的下沿用裁切、后期放大或计算卡伪作可见实机 UI。此 raw 可按实际可见部分单独审；需要完整战斗窗的镜头另开 attempt。
2. 在仍暂停且**尚未开新的 recorder**时，可由当前屏幕持有者经游戏原生设置页查看 **Interface/界面 → GUI scale/界面比例**，注意该行 `*` 和重启提示。若允许当场保存，选 `1.0`，执行 **Save and Close**，再读取本次隔离 profile 里的实际 `GUI.scale`，拍一张新的原始桌面图，人工核战斗窗顶部、所需下部字段、日期、战斗身份与战争 UI 均完整可见。原版 CK3 没有已核可调用的本项 MCP/UIA 语义操作；若使用鼠标，按桌面原图尺寸、`pyautogui.size()`、预览内容矩形和 `desktop_coordinate_map.py --receipt` 操作。只有配置读回与**新像素**共同证明生效后才可在**新录制 attempt**开始下一 raw。
3. 若该项标需要重启、保存后仍见 1.3、或 1.0 仍裁切，就结束当前受管会话并保全它。下一独立 attempt 使用同一精确来源存档/回执、独立 state/profile/output/pipe；启动前在其新 profile 设置待验 1.0，或在**无 CK3/recorder 且独占屏幕**时试驱动列出的 2560×1440@60。显示模式改变后重新取真实 GDI、`pyautogui.size()`、原图及窗口完整性，重新挑战新鲜 Steam“离线模式”；新 2 秒几何片必须全帧解码匹配，再凭实际游戏截图确认面板全见，才开 600 秒正式 raw。若任一门失败，保留 RED 并恢复已记录的桌面模式。

`GUI.scale=1.0` 与 2560×1440 是**待实机验的取材候选**。新截图之前，不把它们写成已经解决裁切。改比例或分辨率不改变原生战争/战斗数据，但会改变画面字节、像素坐标和媒体身份；新 raw 必须有独立 attempt、配置、几何与审阅回执。
