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
