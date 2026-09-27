# H2743 精确原件的本机 OneDrive 接收（2026-09-28）

跨机[资产通知](../autonomous-agent-progress/coordination/war-requests/requests/WAR-ROBERT-H2743-ASSETS-20260928.json)指向 OneDrive 根下 `WAR-ROBERT-H2743-2026-09-28`。本机 `C:/Users/1/OneDrive/` 起初未投影该目录。在 OneDrive 桌面客户端“选择文件夹”中读取 19 个顶层复选框：只将目标由 0 改成 1，另 18 项状态逐一不变；UIA 语义 `Toggle` 和 `submitButton.Invoke` 后目标目录出现。该动作没有开启其他 OneDrive 文件夹的同步。

目录下恰好四个文件；本机只读哈希与复制脚本没有进入仓库，保存在 `D:/workspace/ck3_native_war_ai_promo_work/h2743_verify_onedrive_exact_four.py`。脚本在读取内容前核验文件名集合，随后只读取这四个精确路径并以 `xb` 方式复制到 `D:/ck3-research-artifacts/war31-h2743-20260928/source-verified-01/`，没有打开其他 OneDrive 文件。外置 `transfer-receipt.json` SHA-256 为 **`DE10DAC715DE2AA976FABF7220BE8A9F2C3449594F83A19497F9A461BE529AAF`**，四文件总字节数 `109,573,552`。

| 文件 | 本机 SHA-256 |
| --- | --- |
| `xar_checkpoint.ck3` | `A5012030DA500A4352EF79D1EA10269D45DD5D19DAC508E22DD835663A5106E9` |
| `driver-state.json` | `F31460BAA126BAED289CBA20A6FEFF59AAF6EF87BA3B29943C892236B6D15069` |
| `first-heir-marriage-formal-v1.json` | `12D7B2B006E409DB69F7F442107B01B5D38D8C589A7F494B24519094024B5724` |
| `xar_ck3_bridge.dll` | `8C3A9523D14DEDB6C44AC04F748BFC9D086E983B2A973A956CBADD21F07A8A5C` |

四项均与跨机通知和原请求的冻结 SHA 一致，复制品也各自再次哈希相等。这个回执只证明输入已到本机；没有进行正式配对、启动 CK3、当前帧退战查询或任何游戏动作。源目录仍保持客户端管理，后续研究使用外置不可变复制品。Files On-Demand 和选择同步只约束本次选择范围，不能把“未主动读取其他路径”夸成系统层绝对禁止所有后台流量。

## 本机无启动配对

外置 `D:/ck3-research-artifacts/war31-h2743-20260928/attempt-01/` 以这四项精确哈希创建新独立状态。原 driver 的 2743 项历史、最后 `save-checkpoint`、日期 `53217264`、角色 `29829` 与 episode `native-29829-2bc2d599f7f9` 和存档哈希吻合；家庭 sidecar 是同一 episode 的已解决订婚，没有待提交动作。新状态保留 sidecar 原字节，官方 `prepare-profile --xar-enabled xar_off`、`rebind-ordinary-seed-v1` 和 `native-one-generation-preflight` 均通过；派生 driver SHA-256 `DE008FD0E58C86897F419188787109A04391A44A245A25F2E7BD8AE670D6B614`，rebind 回执 SHA-256 `AFD5C716FADE80B960E8B7441B5DA053479259EFDD82D4D44F0D68A6AB0843D3`，READY 预检报告 SHA-256 `45272A42440DB742C485B4E243A59FB0660BBDC2C12C7ED4C4262BA3C5102B44`。本步骤未启动 CK3，未查询停战选项，也未执行任何游戏动作。

随后以本机屏幕任务租约运行 `desktop_steam_offline_recovery.py recover`，取得 `steam-offline-01/probe-1/steam-moved.png`，SHA-256 `14332285E7B6DC48AB1B66F88601B3D763A1541AEC25BA22B70A89BD557985CF`。窗口位移产生新像素；人工审阅该图左下角确为“离线模式”。预检还记录当时无 CK3、无录制进程，ToDesk 服务运行，未重启服务或切换 Steam 模式。这是启动前门禁证据，不是 H2743 原生结果。
