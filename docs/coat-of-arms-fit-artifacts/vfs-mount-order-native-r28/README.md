# CK3 CoA VFS mount-order native R28（显式 MCP GREEN）

R28 是 `physfs_mounted_data_observer_v1` 的最终原生验收回执。exact `1.19.0.6`、Steam 离线会话通过官方 Python MCP client 显式调用
`ck3_get_bridge_diagnostics`；不使用 OCR、键鼠或屏幕坐标。

## 结果

- 轮询 4 次后在 8.908 秒内稳定；所有预登记检查通过。
- caller-local observer 捕获 34 次调用：34 成功、0 失败、0 槽覆盖。
- 顺序为 3 个 engine 根、29 个 DLC、两个 fixture；fixture ordinal 为 33、34，`earlier` 在 `later` 之前。
- 旧 lifecycle observer 的 A/B 快照为 35/35，额外的一行是隔离 profile 根；fixture ordinal 为 34、35。
- private/read-only/default-OFF 条件保持，observer 未进入公开 capability 或 action。
- 退出时 Job Object active process 为 0，CK3 进程树消失、watchdog 缺席、控制文件清除。

这证明受控会话的 mount order 和每次 publisher 返回结果。它不证明单个 CoA 路径最终来自哪个 source，也不把 `replace_path`、definition
merge 或 registry lookup 推断为已闭合；这些仍需要独立的有界 VFS resolve/CoA registry provenance。

## 可追溯性

- checked-in report：`1174238` bytes，SHA-256 `17FA7AFABD23C3EEAF79D346897DDC6984BE75E582F05A06067CD07E44B22093`
- live source base：`62afdb91b62f42c1207fa84b856b0da5c7b09e31` 加捕获时工作树；实际运行字节以 bridge DLL SHA-256 为准
- CK3 executable：SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- bridge DLL：`3230720` bytes，SHA-256 `972092940989B6122FFFC5A1AFA8D8EB76660208B4C8BCF86F4333AB2EF90A9E`
- observer binding：CALL RVA `0x3B5CE1D` → publisher `0x3BE18C0`；`Mounted Data` literal RVA `0x4556E50`

机器可读摘要见 [summary.json](summary.json)，完整 MCP 请求、原始 diagnostics、Steam 状态和清理回执见 [report.json](report.json)。

## 复现

```text
set PYTHONPATH=ck3_autonomous_player\src&& tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\run_frontend_gui_route_v1_live_acceptance.py --source-profile D:\ck3_coa_vfs_replace_path_r25_source --state-dir D:\ck3_coa_vfs_mount_order_r28_live --game-dir C:\SteamLibrary\steamapps\common\CRUSAD~1 --bridge-pipe \\.\pipe\xar_ck3_coa_vfs_mount_order_r28 --bridge-dll C:\xb\coa-vfs-r27\xar_ck3_bridge.dll --bridge-injector C:\xb\coa-vfs-r27\xar_ck3_bridge_injector.exe --timeout 120 --vfs-mount-order-diagnostics --vfs-mount-order-diagnostics-only --output D:\ck3_coa_vfs_mount_order_r28_live_report.json
```
