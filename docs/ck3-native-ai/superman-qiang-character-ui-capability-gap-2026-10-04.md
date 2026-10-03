# 《超人强》角色查看入口的 MCP 缺口与官方 UI 验收路线

2026-10-04 对《超人强》R0006 已加载组合做只读盘点。结论：当前 MCP 注册的角色窗口工具不能在这一 DLL 上调用；既有能力没有按稳定 key 发起自定义 character interaction，也没有事件正文或特质 tooltip 文本读回。此次没有操作桌面、Steam 或 CK3，没有修改模组或验收 runner，没有执行未验证的旧版地址。

## 当次冻结身份与证据

| 对象 | 当次身份 |
| --- | --- |
| 游戏 | CK3 1.20.0.3 / Steam build 25652598 |
| EXE SHA-256 | `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6` |
| SDK 部署 | `D:/sxad-freeze-20261004`，源提交 `f643b32e6146dce73f77fedfefd8471da59fb04f` |
| 已加载 DLL SHA-256 | `ad3bbb4e7bc19f2737bba10c468d26cabcae4058c6c2ae4f3b8675e95c5b8518` |
| R0006 MCP tool list | 141 个注册工具；155,491 字节；SHA-256 `b9af59f1b7909dd1f1ee2032e9b253eed860c941db5190a9e3abb70de6f3213d` |
| R0006 原生 capability 回执 | 41,141 字节；SHA-256 `6f062d8f467145a3f514735ab912021be27124270904e2633efba4a7351de6d4` |

tool list 和 capability 回执位于 `D:/ck3-experience-drain-feasibility-20261004/desktop-3fevhd2-1c74096080--superman-qiang--R0006/`，分别为 `mcp-tools.json` 与 `receipts/0001-ck3_get_capabilities-response.json`。盘点结果与冻结源码逐文件 SHA 保存在 `D:/ck3-experience-drain-feasibility-20261004/superman-character-ui-gap-a02/inventory.json`。最初 a01 因 SDK 部署不含历史 docs 而未完成归档，其输入和失败记录仍保留；a02 将旧版文档按主仓历史参考另行绑定。

## 已存在的能力与实际边界

| 能力 | 查得的合同与本次限制 |
| --- | --- |
| `ck3_open_character_window_v1` | tool list 注册存在，但已加载 DLL 没有 `game.command.navigate-ingame-ui-v1`。 |
| `ck3_query_ingame_ui_window_v1(window_kind="character")` | 注册 schema 接受 `character`；历史合同会返回 `character_window` 的最多 512 节点 census，但本 DLL 没有 `game.command.query-ingame-ui-window-v1`。 |
| `ck3_inspect_gui_window_tree_v1` | 枚举只有 `decisions`、`decision_detail`、`courtier`、`vivhite_courtier`；结果明确 `rendered_text_available=false`、`tooltip_state_available=false`、`business_model_available=false`。 |
| `ck3_query_current_event_window_context_v1` | 本 DLL 有对应 capability；返回 event key、root、saved scopes、option `resolved_name` 等，可核验 `sxad.1` 及 `sxad_view_subject`。现有字段集合没有事件标题／正文文本。 |
| Generic character-interaction proposal binder | [既有专题](character-interaction-proposal-native-binder.md)明确它是 **1.19.0.6 static-ready/private/unwired**，不能作为 1.20.0.3 的可执行入口。 |

冻结 [`service.py`](../../ck3_autonomous_player/src/xar_autoplayer/bridge/service.py) 的 `_typed_ingame_ui_v1`（9474–9476 行）在 driver 派发前检查上述 capability；缺失时抛 `UnsupportedStepError("capability_not_available: typed UI has no desktop fallback")`。R0006 未真正调用 open/query；这里记录的是**真实原生 capability 缺席及对应拒绝源码**，没有伪造一份 live 拒绝回执。下一次受管验收可保存调用产生的原始拒绝结果，不能因为工具名在 list 中就绕过 capability 门。

[`ingame_ui_contract.py`](../../ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_ui_contract.py) 仍将结果绑定到 1.19.0.6 的 backend、版本与 EXE SHA；[`ingame_ui_navigation_v1.cpp`](../../ck3_autonomous_player/native_bridge/src/ingame_ui_navigation_v1.cpp) 使用该旧版固定 storage、view handler、`DefaultOnCharacterClick` 与窗口 RTTI 地址。当前 1.20.0.3 adapter 只恢复了已经迁移的有限 frontend 与 named-window census 能力，没有宣告这组 ingame routes。禁止直接执行其未闭合的旧地址。

## 为什么单独扩一个枚举不足以闭合

已有 [`DispatchFixedGuiWidgetNativeV1`](../../ck3_autonomous_player/native_bridge/src/zhongguo_scoreboard_action_v1.cpp) 可在原生 GUI 所属线程上对经过身份、callback、可见及 modal 门验证的固定 widget 执行 `ShortcutActivate`。它没有公开“按交互 key 取当前菜单业务行并派发”的接口，也没有 rendered text 查询。

当次原版 `gui/interaction_menu_window.gui` 使用 `CharacterInteractionMenuWindow.GetCategoryItems`；`gui/interaction_templates.gui` 中重复的普通 button 执行 `InteractionItem.OnClick`，名称文字来自 `InteractionItem.GetName`。只增加 `character`／`interaction_menu` census 范围，仍无法将某个重复 button 绑定到 `sxad_view_experience_interaction` 的 actor、recipient 与完整 Can Send 语义。通过位置或 child path 猜业务身份不构成 typed capability。

当前 1.20 的婚姻／赎金实现已有 context construction、refresh/finalize、Can Send 与 send-command 原语，可作为未来通用 interaction provider 的基础；它们尚未提供自定义 key 的 preview/query/action 合同及事件正文 readback。完成这些合同需要新 native 实现、main-thread mailbox、schema/driver/service/MCP 接线及新 DLL 实机证据，不能由 Python 薄包装或一个菜单枚举补齐。因此本次不扩大 native 施工，不改变冻结游戏组合。

## 本次可执行的官方 UI 降级

此路线以明确的 MCP capability 缺口和未验证 1.20 ABI 为依据，沿用[已审阅桌面动作边界](reviewed-desktop-semantic-action-mcp.md)与[坐标换算合同](../desktop-coordinate-mapping.md)。屏幕执行者继续持有当次独占租约，并使用本次新鲜 Steam 离线证据；本文作者不执行这些动作。

1. 用独立 save 解析取得目标成年非玩家角色的完整 ID、姓名、当前经验、六项属性修正及模组变量；夹具中的成年角色以 `create_character = { employer = root ... }` 创建，可在玩家 Court 列表选择。实际 ID 必须取自本次存档，不能复用 R0006 的 `65904`。
2. 通过原生游戏 Court／角色页面找到并打开目标，对其肖像右键进入原版角色交互菜单，再选择友好类的“查看性经验”。原版肖像 `DefaultOnCharacterRightClick(Character.GetID)` 与 `InteractionItem.OnClick` 是这条正常玩家入口；出现原生确认窗时正常发送。禁止用夹具 `trigger_event` 替代此步骤。
3. 每个鼠标点击或 hover 都先保存并审阅原始桌面截图，读取文件真实尺寸与当时桌面尺寸，通过 `tools/desktop_coordinate_map.py` 提供真实预览内容矩形及 `--receipt`。该工具支持 `--button right`／`left`；不得套用历史固定倍率。只读 trait hover 使用它的 move 路径。
4. 交互后取新的 MCP snapshot 与 `ck3_query_current_event_window_context_v1`，核验 event definition key 为 `sxad.1`、root 为当前玩家、saved scope `sxad_view_subject` 为目标的完整 ID。这些是独立原生业务读回，鼠标 ACK 或画面变化不能替代。
5. 直接审阅该真实事件原图中的目标姓名与经验数字；特质 hover 原图也应显示当前目标的值。将视觉读到的数字与独立 save 中该角色的 `sxad_sex_experience` 对照；未初始化时应显示 0。这里是 UI 呈现验收，机制判断继续采用脚本断言／save 数据，不能用 OCR 推测机制。
6. 查看前后经验、六项修正、已记录计数与双方身份保持一致；正常关闭窗口后再保存／重载并复核。每次点击、原图、MCP 业务读回和 save 数值均绑定到同次 run，保留失败过程。

L3 只有以上真实入口和读回闭合后才能记为 GREEN。工坊媒体使用另一次纯模组正常玩家流程的干净实机截图，保留原图 SHA、裁切来源与公开回读；夹具事件截图和宣传封面不代替这张产品实机图。

## R0007 的真实 capability 拒绝

后续 R0007 屏幕执行者在取得新鲜 snapshot revision 后，真正调用 `ck3_query_ingame_ui_window_v1`。原始 MCP 回执 `D:/ck3-experience-drain-feasibility-20261004/desktop-3fevhd2-1c74096080--superman-qiang--R0007/receipts/0053-810-character-window-response.json` 为 340 字节，SHA-256 `babc86fbf8b643133e905ae728e536989b99b12e40ce7c81f039122e7453316f`，`is_error=true`，正文明确 `capability_not_available: typed UI has no desktop fallback`。该证据补齐了上文 R0006 仅有 capability 缺席与拒绝源码的边界。较早请求的旧 revision 拒绝另行保留，不能把它称作能力缺失。

只读核对记录保存在 `C:/ck3-superman-qiang-20261004/r7-ui-gap-evidence-a01/record.json`。屏幕执行者随后开始正常角色肖像菜单入口；在它交付完整事件身份、目标 saved scope、实际经验文本和存档对照前，此文不宣称 UI 已 GREEN。本文作者仅读取回执并记录 SHA，没有进行桌面或游戏操作。
