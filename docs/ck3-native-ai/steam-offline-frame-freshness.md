# CK3 实机前的 Steam 离线画面新鲜度

2026-09-27 的 065/067 连续实机尝试发现：`pyautogui.screenshot()` 在 06:34 与 06:50 两次保存了 SHA-256 均为 `96F83530559B8659E486A4CA00E266BBD7BA8F22B72DF4DB3B1FE658D07B1235` 的桌面图，图内任务栏时钟始终显示 `4:06`。文件修改时间、新 `observed_at` 或图中曾经出现“离线模式”，都不能单独证明后一张图是当前画面。065 的旧离线门因此记为**新鲜度未独立确认**，其原生实机回执仍按原始 bytes 保存，不因预检缺口而改写。

067 启动前先保留旧图，然后用当前 Steam HWND `198194`、进程 `steamwebhelper.exe` 的 Win32 窗口矩形确认窗口位置，执行一次可恢复的 `x=0→20→0` 位移。位移期间原生桌面截图 SHA-256 为 `795B38F3E6429B1EBB3DCA03EE78F43863A0760FE1EC3C22F8EEF38D6C06ACC5`，窗口边沿确实随之平移，底栏仍可见“离线模式”；窗口原位恢复。067 的新收据绑定这张图、窗口身份、位移前后矩形与当前时间，旧截图留在独立 attempt 中作为失败新鲜度证据。此方法证明桌面捕获对**当前窗口动作**作出了响应，不把冻结的任务栏时钟称为已更新，也不单凭像素证明 Steam 后端连接状态。

以后在受管 CK3 实机前，使用 [`steam_offline_fresh_frame.py`](../../tools/steam_offline_fresh_frame.py) 于**没有 CK3 进程**且 Steam 窗口在前台时取得新图和 `steam-frame-freshness.json`：

```text
<verified-python> tools/steam_offline_fresh_frame.py --output-dir <new-empty-attempt-directory>
```

工具要求目录已存在且目标文件均不存在，唯一可见 Steam 窗口完全位于桌面内，向左或右有 20 像素安全空间。它先保存基线图，移动当前 HWND、核对新矩形和桌面真实宽高、保存新图，再在 `finally` 恢复原矩形；若新旧哈希相同、移动侧边沿像素无变化、屏幕尺寸变化或恢复失败，报错而不产出成功收据。输出的 `offline_status_observed` 固定为 `null`：执行者仍需直接审阅**新图**上的 Steam 状态，再单独记录离线结论；不得让脚本凭“画面有过离线字样”自动签核。整个过程不点击桌面坐标，也不启动游戏。

该工具在无 CK3 的同机环境完成一次实际复跑，生成前图 SHA `96F835...B1235`、移动图 SHA `795B38...6ACC5`，Steam 矩形 `0,0,962,768→20,0,982,768→0,0,962,768`，桌面 `1024×768`；过程资产在外置 `D:/workspace/ck3_native_war_ai_promo_work/steam-fresh-helper-smoke-068/`。后续机器若窗口无法唯一识别、无法安全位移或图像不响应，应把离线预检记为未证明，并排查环境；不能复用旧图和旧收据。
