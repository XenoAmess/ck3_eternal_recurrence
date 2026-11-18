# 本机 Steam 11.23 的后台离线观测修复

`machine_id: 4-8e1c2f1861`；来源核对与验证日期：2026-11-18。此修复只解除公共验收入口的离线状态观测阻塞，金融 Mod 的 CK3 业务验收仍未完成。

08:43:20Z 的公共探针返回 `unavailable / cdp_not_enabled`，附 `native_provider_unavailable=invalid_input`。真实客户端为 `11.23.65.88`，而原 Native registry 仅登记 10.96、11.12、11.15，故在读取状态前即被版本预筛拒绝。该结果保留，不解释为在线或账号状态。

本机 `SteamUI.dll` 为 **19,675,800 bytes**、SHA-256 **`2dfb0a5d50dd90667549cc7d413c7bfb0794c9af4ebaf08bf1cf7d938a11ea93`**，PE image size 为 19,959,808。离线反汇编确认：

- `0x661b0c` 的 producer 以 `bIsOfflineMode` 输出 `0x11ca0d7` 的字节。
- 唯一调用点 `0x6d8daf` 把 `0x11c9f50` 交给 `0x619840`，getter 写 `+0x187`，恰为同一字节。
- `0x660484` 检查同一字节并向托盘 setter 传状态 4；跳表该分支使用 `public/steam_offline` 与 `#Steam_Tooltip_Offline`。
- 当前托盘 manager pointer 为 `0x11c8328`，成员偏移为 **`0x160`**；此前版本的 `0x154` 不适用。六处精确代码锚点与完整图像身份一起登记，不用宽泛模式匹配准入。

`steam_offline_state_contract.py` 的 wire parser 接受 registry 已登记偏移；公共 gate 继续要求版本、实际图像大小/SHA、producer、manager 与偏移属于**同一个 exact profile**。没有变更 schema、采样方法或 gate 的资格条件。

实际离线回归结果如下；这五组共有 **62 个不同测试**，无 CK3 启动。其中原 CI 的后台 Steam／fixture／GUI step 四条命令共 55 项，另单独运行 Native provider 7 项。

| 真实命令（均 `python -m unittest discover -s tools -p <文件>`） | 结果 |
| --- | --- |
| `test_steam_offline_native_profiles.py` | 11 通过 |
| `test_steam_offline_native_provider_v1.py` | 7 通过 |
| `test_steam_offline_state_probe.py` | 21 通过 |
| `test_fixture_engine_prepare.py` | 3 通过 |
| `test_ck3_mod_acceptance_gui.py` | 20 通过 |

首轮 profile 测试曾因 wire parser 固定 `340` 失败；随后曾把通用 wire 形状校验误作 exact source admission，导致既有通用序列化 fixture 失败。最终恢复形状与准入的职责边界，原形状 fixture 未修改；新增锚点数据流联通及新旧偏移互换拒绝回归均通过。

Root 于 **09:34:38.707105Z** 运行公共探针，实际观察同一 Steam PID `22864`／birth `134394574701311395`。结果为 `offline / native_current_user_byte`，两次 backing byte 均为 1、托盘状态均为 4；前后进程、加载模块、文件身份与代码锚点保持一致。没有启用 CDP、重启或操作 Steam UI。

小原件保存在 `C:/workspace/ck3-market-task-20261118/`：`steam-1123-offline-exact-profile-candidate.json`（SHA-256 `39041fe8fbaf9ef98294f00907d6aa0ffa68b978ee3e1fac1a1295cdd73ea80b`）、`continued-steam-offline-probe-01.json`（SHA-256 `e80b708ff64807e6f080dad7e67f834d3a42cc876f9664c739e49addb708f055`）。该观察只代表原时点的有意离线模式；后续启动重新取新鲜公共回执，不复用旧 nonce 或以本记录代替准入。
