# H2825 精确原件的本机接收与无启动配对（2026-09-28）

[H2825 跨机请求](../autonomous-agent-progress/coordination/war-requests/requests/WAR-ROBERT-H2825-SIEGE-PARTITION-20260928.json)指定 OneDrive 根目录 `WAR-ROBERT-H2825-R0265-2026-09-28` 的六个原件。本机最初只在 OneDrive 客户端数据库中见到该目录元数据，选择同步未包含它。通过客户端“选择文件夹”读回 21 个顶层复选框后，只把目标项从 0 改为 1，另 20 项保持原样，并使用 UIA `submitButton.Invoke` 提交。目录随后出现且恰好包含请求列出的六个文件。本次没有选择或主动打开其他 OneDrive 文件夹；选择同步及按需下载不能证明客户端绝对没有其他后台流量。

本机只读哈希与复制脚本保存在仓库外 `D:/workspace/ck3_native_war_ai_promo_work/h2825_verify_onedrive_exact_six.py`。它先核对目录名集合，再只打开六个精确路径，以 `xb` 写入不可变复制目录 `D:/ck3-research-artifacts/war31-h2825-20260928/source-verified-01/`，逐项重新哈希。`transfer-receipt.json` 的 SHA-256 是 **`634A68470E3B0A576D338CD991F6C12EA4447C915F38145B86FCE962E6E15E26`**；六文件总字节数 **110,503,425**。

| 原件 | 本机与请求一致的 SHA-256 |
| --- | --- |
| `xar_checkpoint.ck3` | `231513D308A7D62D2F9CBF354D872C9F15FF1FB2B24B2CCAFF2480CF5E14B13D` |
| `driver-state.json` | `B8E50A281AFB9A5DAA7AC1ED55DD68C4305816302B71B14EDF79F1060177D872` |
| `first-heir-marriage-formal-v1.json` | `E642B45C8FF830148A2DED2D2B107CDD30C81F7E8FB2D3D4938CCEA81D744AF8` |
| `xar_ck3_bridge.dll` | `A520BCB688ED921E8DA7410D8426E2FE443135F3F0CECBA928791CCBA0243245` |
| `r0265-formal-report.txt` | `B990E9F9E0F3E83B2412F86D9AE491820A0A5AA7EA6B83A028F7DF5A5B77E95B` |
| `TRANSFER-README.txt` | `4358EB5F90B66167C554390A167FF738392E7AF58519E12B114D39FE3BA8927C` |

源 driver 的 episode 为 `native-29829-2bc2d599f7f9`，角色 `29829`，冻结检查点历史索引 `2825`、日期 raw `53217624`、存档 SHA 与请求相符。其 `command_history` 有 2828 条，末尾三条是检查点之后的只读命令；不能把历史长度误当检查点索引。家庭 sidecar 为同一 episode 的已解决订婚且无 pending。

外置 `D:/ck3-research-artifacts/war31-h2825-20260928/attempt-01/` 使用官方 `prepare-profile --xar-enabled xar_off`、`rebind-ordinary-seed-v1` 和 `native-one-generation-preflight` 建立独立状态，三步均通过，预检 `ready`、进程清单为空。派生 driver SHA-256 **`C4958192D27FF32ACA77414D8D6381CD6FEAB52B9EEB640EF1ABF9C1473F2A29`**，rebind 回执 SHA-256 **`D0549CDA3AA872FAD78C10EF389D328BCA23F667BE6F4E4E81102E17230E5F4E`**，预检报告 SHA-256 **`57A2119DB844C848958584335599217653F593BA8E8D2DB86861ECA0ECF48933`**。这只证明精确输入与无启动配对就绪；没有启动 CK3、推进日期、执行投降或验证 H2825 围城规划器的实机结果。

后续实机必须先取得**新鲜** Steam 离线画面，使用此配对及请求中的精确 DLL，并在全新 attempt 中记录同帧战争行、路线位置和规划结果。2026-09-28 05:03（北京时间）的桌面恢复尝试仍报告 `stale_or_unavailable`，且未取得新鲜离线画面，因此本次无启动配对不得被写成实机通过。
