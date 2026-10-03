# R0007：账本机制实机与查看窗口 RED

本轮整体为 **RED，不可发布**。41 项实际执行完毕，原始日志为 **39 PASS、2 FAIL、0 未执行**；独立真实存档证明存活测试角色的六项基础属性均未改动，成对净账本与永久 modifier 符号、数量、保存的倍率相符。两个日志 FAIL 均来自夹具把诺曼文化下的勇武减益抵消错误当成显示数值必减 1。另有明确产品错误：正常查看入口打开的记录事件没有显示经验和属性数字，游戏日志直接报告本地化 data chain 解析错误。旧日志与 FAIL 标记保持原样。

## 运行身份与输入

- Run ID：`desktop-3fevhd2-1c74096080--superman-qiang--R0007`。
- Execution ID：`63c8382d-e86b-43cf-8a93-b882b2f64794`。
- CK3 PID：`10824`；游戏 HWND：`4064130`；玩家完整角色 ID：`31254`。
- 证据根目录：`D:/ck3-experience-drain-feasibility-20261004/desktop-3fevhd2-1c74096080--superman-qiang--R0007/`。
- 游戏：Steam CK3 **1.20.0.3**，build **25652598**，EXE SHA-256 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。
- 正式生产输入：A0003 的 **22 文件** staging；来源 commit `599af8da0008fd77f30347f7d3a7b2faef33a852`；manifest SHA-256 `0272aa21327336f95b199b36dfca90286c1a7818aab4f679143c601c5f1c17ef`。完整文件级 SHA、大小及来源保存在 `production.manifest.json`。
- 外置夹具：`fixture-a11`，manifest SHA-256 `be18c42e47f6347425f110545323a028f8322138de7a50fd6de3e1b22324116e`，与生产 staging 分开加载，未混入正式包。
- Python：已验证主工作树 `tools/.venv/Scripts/python.exe` **3.14.7**；MCP **2.0.0**；SDK clean detached 来源 `f643b32e6146dce73f77fedfefd8471da59fb04f`，1027 个 Python 文件的精确输入 SHA 清单保存在 `sdk-python-input-hashes.json`。
- Native DLL SHA-256 `ad3bbb4e7bc19f2737bba10c468d26cabcae4058c6c2ae4f3b8675e95c5b8518`，DLL 的真实历史编译来源按外置构建收据记录，不用 A0003 产品 commit 冒充。当前 injector SHA-256 `d332d1a4bb3524ddce5a73b6150449d9b29b21aff8c9fae61333b088796ffa7f`。

Steam 保持离线，启动前实际审阅 `offline-a11/steam-menu-frame-a02/screen.png`：当次菜单显示“上线…”且客户端显示“离线模式”，内部菜单及内容确实重新绘制；新像素 SHA-256 `be19a50f3ca7bc7858ee18636130a96f0cfc24564bfe156041151891845f5237`。先前任务栏旧时钟与一次错误扩展名导致的截图回执失败仍在 `offline-a11/visual-review.json` 中如实保留，未把旧时钟时间改写为新时间。

## 独立存档结果

原生普通 Robert 开局后，夹具通过原版 `on_game_start_after_lobby` 排程；每 8 项在案例边界跨 1 天打断递归。所有 41 项与一次 END 标记实际出现，随后暂停。保存时游戏日期为 `53144544`。

首次原生保存请求确实提交，但 SDK 等待文件完成的 deadline 超时；没有重复提交该请求。文件随后稳定完成，经大小与 mtime 稳定检查复制到 `save-readback-a03/checkpoint.ck3`，其 **69,277,042 字节**、SHA-256 `4f578f301ba046c0736a5000f0396a6b536fce180f258f720edb1b8619b6f947`。原错误响应和提交请求一起保留。真实 Rakaly **0.8.19** melt 输出 SHA-256 `d7f56d11656698476cca533eb39defc88ccef17e857e6b9069eb75b73f60a948`。

`save-readback-a03/fixture-readback-v3.json` SHA-256 为 `ba0f4b664efc88d7f65bb75b0f6476016bacd90dede245b9ef06f46559a1a2b1`。解析器直接读取 `skill` 数组，顺序固定为外交、军事、管理、谋略、学识、勇武；负 fixed5 变量按有符号 64 位整数解码。实际存档中的 modifier 倍率字段是 `multiplier`，默认 1 可以省略；核对使用保存原始字段，不从账本变量反推倍率。

| 强制技能 helper | 接收者 / 来源者完整 ID | 最终双方基础数组 | 接收者 / 来源者净账本 |
| --- | --- | --- | --- |
| 外交 | 65853 / 65854 | 均 `[10,10,10,10,10,10]` | `[1,0,0,0,0,0]` / `[-1,0,0,0,0,0]` |
| 军事 | 65856 / 65857 | 均 `[10,10,10,10,10,10]` | `[0,1,0,0,0,0]` / `[0,-1,0,0,0,0]` |
| 管理 | 65859 / 65860 | 均 `[10,10,10,10,10,10]` | `[0,0,1,0,0,0]` / `[0,0,-1,0,0,0]` |
| 谋略 | 65862 / 65863 | 均 `[10,10,10,10,10,10]` | `[0,0,0,1,0,0]` / `[0,0,0,-1,0,0]` |
| 学识 | 65865 / 65866 | 均 `[10,10,10,10,10,10]` | `[0,0,0,0,1,0]` / `[0,0,0,0,-1,0]` |
| 勇武 | 65868 / 65869 | 均 `[10,10,10,10,10,10]` | `[0,0,0,0,0,1]` / `[0,0,0,0,0,-1]` |

这六组的 modifier 均为唯一、正确符号、倍率 1；其他五技能面板即时读回成对 ±1。勇武实际为接收者 **12→13**、来源者 **12→12**。来源者保存的基础勇武仍为 10，loss modifier 与账本 -1 均存在。

R7 存档实际文化 ID **73** 对应 Norman，带 `ethos_bellicose` 的勇武 +2 和 `tradition_chanson_de_geste` 的 `negate_prowess_penalty_add=5`。原版与只读 native 链证据保存在 `prowess-cultural-rule-runtime-a01/`。因此来源者 -1 的显示减益被原版文化抵消；随机赢家案例恰好抽中勇武，导致同样的夹具面板断言 FAIL。该诊断没有把旧日志改成 PASS，也没有把原版文化效果当成生产 modifier 无效的证据。下一夹具须单独验证耗尽抵消额度后的可见扣点，并保留当前原版抵消场景。

独立存档还核对了基础 0 加正修正、接收者面板 0、双方 -0.5 外交百分比修正、全六项不可转移、同日两次、玩家/AI、AI/AI、16/17 岁、匿名计数、原版性行为记忆与压力、经验 99/100/101、百万与安全极限、账本正负增长、过零、翻转及 ±1,000,000 边界。40 个案例的 base/ledger/modifier gate 成功；死亡来源者的 role flag 被原版清除，当前独立 gate 明确记录 1 项定位不足。未用其他 40 项替代死者数组验收。

## 正常入口与只读查看

实际 MCP character window query 返回 `capability_not_available`，收据见 `receipts/0053-810-character-window-response.json`；采用已记录的[官方 UI 降级路线](../../docs/ck3-native-ai/superman-qiang-character-ui-capability-gap-2026-10-04.md)。执行者先确认本轮 HWND 与前台，然后从原始 **1024×768** 截图按坐标换算工具回执执行：玩家肖像右键 → “查看性经验” → 正常确认。没有用夹具直接触发事件代替入口。

MCP 独立 current event context 确证 **`sxad.1`、instance 1、root 31254、`sxad_view_subject` 31254**。原图 `ui-evidence-a02/06-screen.png` SHA-256 `12724e4e780e2aa1ce38ab769cdf3dea545569bbe455449e8ff400f229424f00` 只显示规则段落，经验和六技能、净修正行均未显示。日志在 `05:20:37` 对 14 个 `scope:sxad_view_subject...` 本地化表达式产生 **42 条 type/promote/convert 错误**，另有 `Data error in loc string 'sxad.1.desc'`。这是明确产品 UI RED，需要修正生成器中的 data chain 后重新实机。

随后正常打开玩家角色窗，鼠标 hover“性经验”图标，原图 `ui-evidence-a02/07-screen.png` SHA-256 `d83407ad3017a65aafc6098066adc3a7d5f83d018916e242e3842a6292a452d1` 清楚显示 **“启用后累计性经验：1001 次”**，与实际存档一致。这是玩家特质 hover 的局部成功，不能代替非玩家查看和百万值 UI 验收。

正常查看前后各取得一次独立真实存档；第二次提交也保留原生 consumer deadline 错误，随后只归档确实变新的完成文件。查看后 `save-readback-a05/checkpoint.ck3` SHA-256 `610bd944306e7924d41392d07590360fb5204f0a6c9d3ac29631fc79ea5f36e2`，melt SHA-256 `d90cd2b80ef449b7f55f23d850b498aae3b5ea1d5eb2b05d8d2b1dbe1b940c93`。新永久解析工具 [inspect_save_readback.py](../tools/inspect_save_readback.py) 的实际输出 SHA-256 `0fd9e51f0cf1c3d532ee6cd916ed390c14fca1c575edd4f9cccc6bb493a1d31f`。

同一暂停日期下，对 **81 个真实角色**逐一比较经验及全部 `sxad_` 变量、六项基础数组、生产 modifier 的 key 和实际保存倍率，**0 项变化**。比较和 UI 原图、日志精确字节一起保存在 `ui-evidence-a02/report.json`。该比较证明本次查看没有修改这些字段，不声明引擎完全没有使用 RNG。

## 夹具与证据限制

查看前矩阵阶段日志有 **25 条死来源者 65944 的变量 scope 错误**（18 set、7 has）及同时间 **14 条 formatter 错误**。运行代理保全原始字节并定位：25 个 primary location 全部为 `sxat` 夹具，未出现生产 `sxad` 调用；见 `log-attribution-runtime-a01/`。下一夹具仅在存活角色上采样变量，死亡前在 root 保存 typed donor 引用，用真实存档独立定位死者基础数组。14 条 formatter 是否随夹具修复消失须以新运行验证。

旧 v2 保存解析报告因负 fixed5 当无符号数、漏读 `multiplier` 而出现错误 gate；旧文件完整保留，纠正后的 v3/v4 输出使用新文件名，没有覆盖旧报告。一次尾部 16 项输出曾被误报成 41 PASS，已即时纠正；正式口径始终按完整日志与存档 **39/2/0**。

本轮未完成真实存档重载、修正后详情数字、非玩家详情、百万值 hover 和无夹具正式玩法 media。所有夹具画面只作开发证据，**不得充当 Workshop 首发实机图片**。下一轮使用新 run ID 与冻结后的新 staging；本轮历史证据保持原样。
