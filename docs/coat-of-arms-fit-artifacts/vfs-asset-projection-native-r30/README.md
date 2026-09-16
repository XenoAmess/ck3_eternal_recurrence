# VFS direct-DDS projection R30（原生 MCP）

R30 在 Steam 离线、CK3 `1.19.0.6` exact build 下，由正式受管 runner 通过官方 MCP 实际调用 `ck3_project_coat_of_arms_vfs_asset_winner_v1` 四次。运行结束后 CK3 进程树、watchdog 和共享槽位均已释放。

## 原生门禁

- 总 MCP 调用：9；遗漏：0；四个投影调用全部 `is_error=false`。
- caller-local mount observer：34 calls / 34 successes / 0 failures / 0 overwrites。
- 四条预声明路径全部恰好返回一次，winner 均绑定 asset bytes、SHA-256 和同一 mount-receipt SHA-256。
- `pattern_solid.dds` 同时存在于 base ordinal 3 与 later-mod ordinal 34，投影 winner 为 ordinal 34。
- Steam `WantsOfflineMode=1`；受管清理 `cleanup_proven=true`；最终 CK3 inventory 为空。
- 完整报告 bytes：`1,134,964`。
- 完整报告 SHA-256：`AA21DA1D45CB5DB3D2048A1EEE7DE3EF368DA9FFA5A1C3EC09442CEA1F4181C4`。

精简且机器可读的 winner、源码文件哈希、binary 哈希和门禁见 [`summary.json`](summary.json)；完整官方 MCP 返回保存在 [`report.json`](report.json)。`.gitattributes` 将完整报告标为 binary，以免 checkout 换行规范化破坏回执哈希。

## 证据边界

本轮提升的是“从真实完整挂载回执，对 direct DDS 做可复现、源字节可审计的 winner 投影”。工具没有调用 CK3 内部 resolver，也没有观察 CoA resource registration；`replace_path` 和 definition merge 没有在投影中执行。因此：

- 可以给开发期 asset-pack builder 生成更可信、可追溯的 direct-DDS 来源候选；
- 不能把本结果写成引擎对任意资源类型的最终 resolve 证明；
- R24/R25 的原生 framebuffer 反例仍有效：已注册资源不会因为后载 `replace_path` 就自动等同于 missing；
- 正式网页仍只消费导入的 pack/receipt，不运行 CK3、MCP 或本机扫描。

## 执行命令

```text
set PYTHONPATH=ck3_autonomous_player\src&& tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\run_frontend_gui_route_v1_live_acceptance.py --source-profile D:\ck3_coa_vfs_replace_path_r25_source --state-dir D:\ck3_coa_vfs_asset_projection_r30_live --game-dir C:\SteamLibrary\steamapps\common\CRUSAD~1 --bridge-pipe \\.\pipe\xar_ck3_coa_vfs_asset_projection_r30 --bridge-dll C:\xb\coa-vfs-r27\xar_ck3_bridge.dll --bridge-injector C:\xb\coa-vfs-r27\xar_ck3_bridge_injector.exe --timeout 120 --vfs-mount-order-diagnostics --vfs-mount-order-diagnostics-only --vfs-asset-projection-path gfx/coat_of_arms/patterns/pattern_checkers_06.dds --vfs-asset-projection-path gfx/coat_of_arms/patterns/pattern_xar_vfs_replaced_earlier.dds --vfs-asset-projection-path gfx/coat_of_arms/patterns/pattern_solid.dds --vfs-asset-projection-path gfx/coat_of_arms/patterns/pattern_xar_vfs_replace_later.dds --output D:\ck3_coa_vfs_asset_projection_r30_live_report.json

tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\summarize_coat_of_arms_vfs_asset_projection.py --report docs\coat-of-arms-fit-artifacts\vfs-asset-projection-native-r30\report.json --repository . --output docs\coat-of-arms-fit-artifacts\vfs-asset-projection-native-r30\summary.json
```
