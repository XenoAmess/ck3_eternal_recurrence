# CK3 家徽 VFS 挂载顺序 MCP 合同

> 状态：静态与单元门禁通过；exact 1.19.0.6 原生会话回读待 R26。

## 目的

R24/R25 已证明两个预登记的 `replace_path` 隐藏假设均不成立，但 framebuffer 只能说明资源最终可见，不能说明启动期间实际发布了哪些
VFS mount。为避免继续用日志文本、截图或猜测替代结构化证据，开发桥把已有的私有只读
`vfs_mount_lifecycle_observer_v1` 接入现有 `ck3_get_bridge_diagnostics` MCP 诊断路径。

该能力仅用于开发验收。正式 GitHub Pages 家徽编辑器不启动、不连接 CK3，也不依赖 MCP、本机服务或该 observer。

## 返回合同

诊断对象 `private_observers.vfs_mount_lifecycle_observer_v1` 保留原有摘要，并新增：

- `publisher_slot_count`：本次快照中稳定读取的发布槽数量，范围 `0..64`；
- `publishers`：按 `ordinal` 升序排列的有界数组；
- 每行保留 `ordinal`、entry/return sequence 与 thread、`raw_result`、`raw_rcx`、`backend`、`insert_mode`、`return_seen`、
  路径预览以及 manager 前后摘要。

原生状态仍使用固定 64 槽；读取端对每槽的发布序号做前后双读，遇到并发覆盖或不稳定行便跳过，不返回撕裂记录。observer 默认
`OFF`，保持 `private_build=true`、`read_only=true`、`public_capability=false`，也不注册任何可写 action。

## 证据边界

可据此证明：某个受控启动会话中，observer 捕获到的挂载发布顺序、返回状态和有界路径摘要。

不可据此证明：

- 任意逻辑资源路径的最终 winner；
- `replace_path`、definition merge 或 CoA registry 的最终语义；
- 未被 observer hook 覆盖的 DLC、archive 或其他装载路径不存在；
- 正式网页需要或允许连接本机 CK3。

因此 R26 即使取得完整挂载顺序，也只能提升“挂载来源/顺序”证据。单文件来源仍需有界的 VFS resolve 或 CoA registry provenance；
在能力闭合前，浏览器 asset pack 继续只接受显式、SHA-256 绑定的 winner receipt。

## 已通过门禁

```text
C:\xb\coa-wp1-v2-final\xar_ck3_vfs_mount_lifecycle_observer_v1_test.exe
call C:\PROGRA~1\MICROS~1\18\COMMUN~1\Common7\Tools\VsDevCmd.bat -arch=x64 -host_arch=x64 && C:\PROGRA~1\MICROS~1\18\COMMUN~1\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe --build C:\xb\coa-wp1-v2-final --config Release --target xar_ck3_bridge --parallel 2
set PYTHONPATH=ck3_autonomous_player\src&& tools\.venv\Scripts\python.exe -m unittest ck3_autonomous_player.tests.unit.test_vfs_mount_lifecycle_observer_integration -v
tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\test_vfs_mount_lifecycle_observer_v1_source_contract.py --root . --ck3-executable C:\SteamLibrary\steamapps\common\CRUSAD~1\binaries\ck3.exe
```

结果分别为：native test 退出码 `0`、完整 `xar_ck3_bridge.dll` 目标 `118/118` 编译链接成功、Python `3/3` 通过、source contract
`GREEN_STATIC`。这些结果尚不等于 R26 原生回读通过。
