# CK3 家徽 VFS 挂载顺序 MCP 合同

> 状态：R28 exact 1.19.0.6 原生 MCP GREEN。默认关闭的 caller-local observer 已通过显式
> `ck3_get_bridge_diagnostics` 返回完整 DLC/mod 挂载顺序；仍不等同于逐资源 winner 证明。

## 目的

R24/R25 已证明两个预登记的 `replace_path` 隐藏假设均不成立，但 framebuffer 只能说明资源最终可见，不能说明启动期间实际发布了哪些
VFS mount。为避免继续用日志文本、截图或猜测替代结构化证据，开发桥把私有只读的
`vfs_mount_lifecycle_observer_v1` 与 caller-local `physfs_mounted_data_observer_v1` 接入现有
`ck3_get_bridge_diagnostics` MCP 诊断路径。

该能力仅用于开发验收。正式 GitHub Pages 家徽编辑器不启动、不连接 CK3，也不依赖 MCP、本机服务或该 observer。

## 返回合同

诊断对象 `private_observers.vfs_mount_lifecycle_observer_v1` 保留原有 64 槽摘要。R28 优先读取
`private_observers.physfs_mounted_data_observer_v1`：

- 固定 `128` 槽、每个路径最多 `256` bytes；
- `call_count`、`success_count`、`failure_count` 和 `slot_overwrite_count` 明确区分调用、结果与覆盖；
- `rows` 按 post-call `ordinal` 升序，包含 thread、raw result、完整性标志和路径；
- exact executable SHA-256、唯一 `Mounted Data` literal xref、direct CALL 与 publisher target 全部冻结在 ABI/source contract。

旧 observer 仍提供：

- `publisher_slot_count`：本次快照中稳定读取的发布槽数量，范围 `0..64`；
- `publishers`：按 `ordinal` 升序排列的有界数组；
- 每行保留 `ordinal`、entry/return sequence 与 thread、`raw_result`、`raw_rcx`、`backend`、`insert_mode`、`return_seen`、
  路径预览以及 manager 前后摘要。

两个 observer 的读取端都对每槽的发布序号做前后双读，遇到并发覆盖或不稳定行便跳过，不返回撕裂记录。observer 默认
`OFF`，保持 `private_build=true`、`read_only=true`、`public_capability=false`，也不注册任何可写 action。

## 证据边界

可据此证明：某个受控启动会话中，observer 捕获到的挂载发布顺序、返回状态和有界路径摘要。

不可据此证明：

- 任意逻辑资源路径的最终 winner；
- `replace_path`、definition merge 或 CoA registry 的最终语义；
- 未被 observer hook 覆盖的 DLC、archive 或其他装载路径不存在；
- 正式网页需要或允许连接本机 CK3。

因此即使后续取得完整挂载顺序，也只能提升“挂载来源/顺序”证据。单文件来源仍需有界的 VFS resolve 或 CoA registry provenance；
在能力闭合前，浏览器 asset pack 继续只接受显式、SHA-256 绑定的 winner receipt。

## R26 勘误：失败来自过早快照

R26 在 Steam 离线、exact `1.19.0.6` 会话中启用了两个有序目录 mod。官方 MCP capability 回应中的 bridge diagnostics
证明 observer 四个 hook 全部安装且无 failure flag，但只返回 `clausewitz`、`jomini`、`game` 和隔离 profile 四个根 publisher。
同会话 CK3 debug log 则在 `virtualfilesystem_physfs.cpp:813` 明确记录 29 个 DLC 和两个测试 mod 的 `Mounted Data`。

R27 改为 MCP capability ready 后轮询，旧 observer 随后稳定返回 35 条：三个 engine 根、隔离 profile、29 个 DLC 和两个 fixture。
因此 R26 的“hook 覆盖不足”根因结论已被后续同构实验证伪；真实原因是当时只在挂载早期取了一次快照。R26 的原始回执仍保留，
但不再用于描述 observer 最终覆盖能力。详见 [R26 勘误](coat-of-arms-fit-artifacts/vfs-mount-order-native-r26/README.md) 与
[R27 过渡回执](coat-of-arms-fit-artifacts/vfs-mount-order-native-r27/README.md)。

## R28 原生结果：显式 MCP 路径 GREEN

R28 使用相同两个有序目录 mod，在 Steam 离线下通过显式 `ck3_get_bridge_diagnostics` 轮询四次，8.908 秒内取得稳定结果：

- caller-local observer：34 次调用、34 次成功、0 失败、0 覆写；
- 三个 engine 根之后依次是 29 个 DLC，再是 `coa_vfs_replace_earlier`、`coa_vfs_replace_later`，fixture ordinal 为 33、34；
- 旧 observer 同场为 35/35，唯一额外项是隔离 profile 根，两个 fixture ordinal 为 34、35；
- 全部行 ordinal 严格递增、返回完整，observer 保持 private/read-only 且未成为 capability/action；
- 受管进程树、watchdog 和共享槽位均完成清理。

checked-in 报告 SHA-256 为 `17FA7AFABD23C3EEAF79D346897DDC6984BE75E582F05A06067CD07E44B22093`，见
[vfs-mount-order-native-r28](coat-of-arms-fit-artifacts/vfs-mount-order-native-r28/README.md)。该结果证明受控会话的挂载顺序，
但仍不宣称 `replace_path`、definition merge 或任意逻辑路径 winner。后续 R29/R30 已在这个完整回执之上补出 direct-DDS
字节投影 MCP；它提升了单文件来源证据，但依然不冒充引擎内部 resolver/registry。见
[direct-DDS 来源投影 MCP](ck3-coat-of-arms-vfs-resource-provenance-mcp.md)。

## 已通过门禁

```text
C:\xb\coa-wp1-v2-final\xar_ck3_vfs_mount_lifecycle_observer_v1_test.exe
ck3_autonomous_player\native_bridge\build-fresh-20260915T110015Z-612b586b\Release\xar_ck3_physfs_mounted_data_observer_v1_test.exe
call C:\PROGRA~1\MICROS~1\18\COMMUN~1\Common7\Tools\VsDevCmd.bat -arch=x64 -host_arch=x64 && C:\PROGRA~1\MICROS~1\18\COMMUN~1\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe --build C:\xb\coa-wp1-v2-final --config Release --target xar_ck3_bridge --parallel 2
set PYTHONPATH=ck3_autonomous_player\src&& tools\.venv\Scripts\python.exe -m unittest ck3_autonomous_player.tests.unit.test_vfs_mount_lifecycle_observer_integration -v
tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\test_vfs_mount_lifecycle_observer_v1_source_contract.py --root . --ck3-executable C:\SteamLibrary\steamapps\common\CRUSAD~1\binaries\ck3.exe
tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\test_physfs_mounted_data_observer_v1_source_contract.py --root . --ck3-executable C:\SteamLibrary\steamapps\common\CRUSAD~1\binaries\ck3.exe
```

结果为：两个 native observer test 均退出码 `0`、启用 successor 的完整 `xar_ck3_bridge.dll` 编译链接成功、Python runner 与
diagnostics integration 合计 `21/21`、两个 source contract 均为 `GREEN_STATIC`。最终原生范围以 R28 的显式 MCP GREEN 为准。
