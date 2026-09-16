# CK3 CoA VFS mount-order native R27（过渡 GREEN）

R27 是采样时序修复后的首个 exact `1.19.0.6` 原生运行。它证明旧
`vfs_mount_lifecycle_observer_v1` 并非只覆盖四个根：轮询等待挂载稳定后，共捕获 35/35 个成功 publisher，包含隔离 profile、29 个 DLC，
以及按 `dlc_load.json` 顺序出现的 `coa_vfs_replace_earlier`、`coa_vfs_replace_later`。

本轮新 `physfs_mounted_data_observer_v1` 已安装，并存在于 bridge 原始 heartbeat；但 Python explicit diagnostics whitelist 尚未转发它，
所以验收器选择旧 observer。该缺口随后修复并由 R28 闭合。R27 是定位 R26 过早采样与发现 whitelist 缺口的过渡证据，不是最终合同。

- interaction：受管 typed MCP；无 OCR、键鼠或屏幕坐标
- Steam：全程离线
- elapsed：12.398 秒
- cleanup：进程树消失、watchdog 缺席、共享槽位释放
- checked-in report：`1098881` bytes，SHA-256 `DF712BFE878BDF1134C78D7780A486465AF1A290526AF0372504C76E24168A1C`
- bridge DLL：`3230720` bytes，SHA-256 `972092940989B6122FFFC5A1AFA8D8EB76660208B4C8BCF86F4333AB2EF90A9E`

机器可读结果见 [summary.json](summary.json)，完整调用与清理回执见 [report.json](report.json)。后继证据为
[R28](../vfs-mount-order-native-r28/README.md)。
