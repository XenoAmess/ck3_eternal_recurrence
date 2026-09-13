# CK3 frontend GUI route MCP v1

状态：`production-live primitive`
适配目标：CK3 `1.19.0.6`，EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`

## 目的与边界

该 primitive 用于补齐开局前无法取得 gameplay snapshot 时的语义导航。它读取 CK3 当前 GUI owner tree，并只允许编译期固定动作：
从主菜单激活原版 `new_game_button`；在书签页选择广度优先遇到的第一个可见、可用 `bookmark_character_selection_button`，
再激活 `pick_any_character_button`；最后在 lobby 激活编译期冻结的默认角色设计器子路径。它不截图、不做 OCR，不发送鼠标或键盘事件，也不接受调用方提供的 native pointer、
控件名、子路径或回调地址。

首版只闭合：

```text
main_menu --activate-frontend-new-game-v1--> bookmarks
bookmarks --select-first-bookmark-character + pick-any--> lobby
lobby --activate-frontend-ruler-designer-v1--> ruler_designer
```

前两段均为 `production-live primitive`；新增的固定选角和 `lobby → ruler_designer` 已为 `mcp-static-ready / live=false`。
`ruler_designer → coat_of_arms_designer` 及上层 Finish 仍不在当前闭环内。

## MCP 合同

```text
ck3_query_frontend_gui_route_v1()
ck3_inspect_frontend_gui_tree_v1()
ck3_activate_frontend_new_game_v1()
ck3_activate_frontend_pick_any_character_v1()
ck3_activate_frontend_prepare_custom_ruler_v1()
ck3_activate_frontend_ruler_designer_v1()
```

对应 bridge capability/step：

```text
game.command.query-frontend-gui-route-v1
query-frontend-gui-route-v1

game.command.inspect-frontend-gui-tree-v1
inspect-frontend-gui-tree-v1

game.command.activate-frontend-new-game-v1
activate-frontend-new-game-v1

game.command.activate-frontend-pick-any-character-v1
activate-frontend-pick-any-character-v1

game.command.activate-frontend-select-first-bookmark-character-v1
activate-frontend-select-first-bookmark-character-v1

game.command.activate-frontend-ruler-designer-v1
activate-frontend-ruler-designer-v1
```

路由枚举为 `unavailable`、`main_menu`、`bookmarks`、`lobby`、`ruler_designer`、`coat_of_arms_designer`。动作分别要求
`main_menu → bookmarks`、`bookmarks → lobby` 与 `lobby → ruler_designer`；原生调用只返回 `acknowledged_verification_pending`。driver 必须另行轮询 route，
只有目标 route 被独立观察到才返回：

```json
{
  "schema": "ck3-frontend-gui-action-v1",
  "status": "verified",
  "input_backend": "native_gui_semantic_activation",
  "uses_ocr": false,
  "uses_keyboard": false,
  "uses_mouse": false,
  "postcondition_verified": true
}
```

## 原版 GUI 身份

本机 exact 安装的输入文件：

| 文件 | bytes | SHA-256 | v1 使用的固定身份 |
|---|---:|---|---|
| `game/gui/frontend_main.gui` | 48,636 | `F75D4EF3DEB22C15195B71A54624D3054879FDE046F30A761A19212E6D7EA614` | root `mainmenu_panel_bottom`；button `new_game_button`；`onclick = [FrontEndMainView.OnNewGame]`；shortcut `menu_1` |
| `game/gui/frontend_bookmarks.gui` | 111,993 | `C853B48F42A5A3B84208B2FC570C02F5FCB5DA217133553C6A5B70B7F8F0F267` | root `frontend_bookmarks`；button `pick_any_character_button`；动画结束调用 `GameSetup.OnCustomStart` |
| `game/gui/multiplayer_types.gui` | 56,911 | `93912D008D2362955470E7F42029280C41E3E316E28D8D1055EE09DFBE8BC3A3` | ruler-selection root `lobbyview`；后续设计器入口调用 `TryStartRulerDesigning` |
| `game/gui/window_ruler_designer.gui` | 118,240 | `C5761FD395E0C3D7FDF320DDE41DA900928F0A2EB217524E25348CCCC07ABDC9` | root `ruler_designer`；page `coat_of_arms_page` |
| `game/gui/shared/coa_designer.gui` | 56,297 | `2F3B863A7FEA692D630825052426CCC674403D096C37DD470E63C923D2D356EC` | CoA designer 结构来源；v1 不从文件文本执行动作 |

运行时不会根据这些磁盘文本猜页面；DLL 每次都从当前 GUI owner 重新解析固定 root/descendant，读取 runtime name、vtable、
visibility 和 enabled 状态。route priority 为 `coat_of_arms_designer > ruler_designer > lobby > bookmarks > main_menu > unavailable`。

当固定 route 返回 `unavailable` 时，零输入 `ck3_inspect_frontend_gui_tree_v1()` 可在同一 application-main mailbox 上对当前 GUI
owner 做只读广度枚举。它最多返回 512 个节点的 runtime name、深度、effective visibility、enabled；遍历上限为 4,096
节点、深度 64，达到任一上限即标记 `truncated=true`。调用方不能提供控件名、地址、遍历上限或回调；该工具只用于以原生
结构化证据识别缺失页面，不执行控件，也不读取屏幕。

route 可识别时，inspector 会自动把固定 route root 作为 `scope_root_name` 并枚举其子树；route 不可识别时才回退全局 root。
每行包含相对 root 的只读 `child_path`、runtime name（允许空，覆盖原版无名控件）、child count 和模块相对 vtable RVA，仍不暴露
可回传的绝对 native pointer。该扩展用于确定 `lobbyview` 内无显式 name 的原版设计器按钮结构，不能由 MCP 调用方选择任意 root。

## application-main 与 gameplay 隔离

旧 mailbox 只在连续两个“暂停、Jomini state 和 game state 均有效”的 SDL pump 后允许局内 typed executor。前端没有这些对象，
因此 v1 另建 application-main ownership proof：连续两个 pump 必须具有相同的当前线程、TLS initialized 地址、TLS context 和
main-thread marker。只有固定 `ExecuteFrontendGuiRouteMailboxV1` 可使用这条门禁；原有 gameplay executor 仍要求完整 paused
proof。

`main_thread_query_mailbox_v1.ready` 保留旧的 paused-gameplay 含义，新增诊断为
`application_main_observed` 与 `owner_verified_pump_epochs`，防止消费者把“主菜单可查”误写成“局内命令可用”。

## 动作验证

固定按钮动作按以下顺序 fail closed：

1. 当前 route 必须与动作匹配：`main_menu`、`bookmarks` 或 `lobby`；
2. 从固定 root 重新解析 target：两个旧动作使用固定名称；选角动作只取 `frontend_bookmarks` 下第一个可见、可用的固定名称；设计器动作只取 `lobbyview` 下编译期路径 `3/0/2/3`；
3. 有名控件必须精确匹配 runtime name；无名设计器控件必须保持空名；所有 target 都必须 visible/enabled；
4. target GUI context、button vtable slot、callback group 与 modal admission 通过现有 exact-build 原生 dispatcher；
5. 调用 `CPdxGuiShortcutManager`；该返回值只算 ACK；
6. Python driver 独立查询并观察对应的 `bookmarks`、`lobby` 或 `ruler_designer`，才能报告 verified；准备动作还必须从 inspector 独立证明 `3/0/2/3` 已 enabled。

## 验收状态与下一步

- fresh MSVC build 已生成 DLL；
- 原生 fixture 覆盖“无 Jomini/game state 时 frontend executor 可用、gameplay executor 仍拒绝”；
- Python contract/service/native-driver/MCP closed-schema 测试覆盖 route、ACK 与独立 postcondition；
- 2026-09-13 的受管 CK3 `1.19.0.6` 验收通过：官方 MCP SDK 先返回 `main_menu`，固定原生动作 ACK 后由独立查询返回 `bookmarks`；
- 十项闭环检查均为 true，包括 `postcondition_verified`、原生语义 backend，以及 `uses_ocr=false`、`uses_keyboard=false`、`uses_mouse=false`；
- artifact 为 `artifacts/coa-clipboard-probe-2026-09-08/mcp-frontend-route-live3.json`，408,936 bytes，SHA-256 `1EBBFA6052967E02F2C929CDD11A76A312B75F85487E9B65DE0158CA7C14DDD5`；源码 commit `84e1f5f139ef4d299fe7635f44f01144083ac8e0`，DLL SHA-256 `8FE08D0FE6E2793866CB6C3164472CB1CAC10BD05A45B1996FCB321537A515F0`；
- Steam 全程离线；`cleanup_proven=true`、`tree_gone=true`，验收后没有残留 CK3 进程；
- `open_kaishek` 没有 frontend GUI/CoA domain，本包预验证为 `not-applicable`。
- `activate-frontend-pick-any-character-v1` 已通过 Release 编译、adapter registry、mailbox/source-contract 与官方 MCP closed-schema 测试，状态为 `mcp-static-ready / live=false`。
- 首次 live attempt 已保留为 `mcp-frontend-route-lobby-live1.json`（94,811 bytes，SHA-256 `B8A98F66B942B785629FED6255E276E313CB8E5870DF809D64A05D6A36039763`）。原生动作已令 Bookmarks 进入加载，但加载期 application-main GUI pump 暂停，单次 route command 超时，结果为 RED；`cleanup_proven=true`，不是能力 GREEN。
- driver 现在以独立的 120 秒 frontend transition deadline 重试暂时超时/拒绝的 route 查询；每次查询仍由原生邮箱自己 fail closed，只有最终观察到目标 route 才报告 verified。聚焦测试包含“暂时不可用 → unavailable → lobby”的恢复向量。
- 第二次 live attempt `mcp-frontend-route-lobby-live2.json`（94,795 bytes，SHA-256 `87650AC340C0049B3279816DE1D49DE14C9CCC79027BD0DCD158CBFEAD24C9D8`）证明加载后 CK3 已开始发布 gameplay snapshot；route transport 此时误复用 CoA 专用的 `snapshot=false` frontend binding，因而被 Python 侧拒绝。GUI route 现改用独立 exact-bridge binding：同一 PID、连接代次、adapter、build hash 与 capability 必须成立，但允许 pregame lobby 同时存在 snapshot。该 attempt 同样是 RED 且 cleanup GREEN。
- 一次仅完成 runner 参数检查的 setup RED 保留为 `mcp-frontend-route-lobby-live3.json`（690 bytes，SHA-256 `ACAE42ADE9A86954CFA872471BA337819195B426A2F4187EEC77D72C05B8D967`）；Steam 路径写错，在启动 CK3 前即停止，不属于能力 attempt。
- 第三次真实 attempt `mcp-frontend-route-lobby-live4.json`（94,822 bytes，SHA-256 `7F7180A929095C2D24416AE0B1F20C2741F47AB63DFD810C1820F00034C839C0`）在修正 binding 后持续取得结构化 route 响应，但加载完成后的 route 始终为 `unavailable`，120 秒后按合同 RED。游戏日志证明已进入 `In Game` idler，说明源码推定的 `lobbyview` 身份尚未被 runtime 证实；cleanup 与 Steam offline 均为 GREEN。
- 因此新增上述有界只读 GUI tree inspector，Release DLL 编译链接、mailbox source-contract 与 Python contract/service/official-MCP `7/7` 均 GREEN，状态为 `mcp-static-ready / live=false`。它是为这次可复现 route-identity 缺口补齐的 MCP 观测功能，不是 OCR 或桌面自动化替代品。
- `live5` 是另一份启动前 setup RED：管道名缺少 `\\.\pipe\` 前缀，未启动 CK3；artifact 为 1,667 bytes，SHA-256 `F6827D482FACBF642167B1B5E768957C37E9CAB957A024BE8250003B9E0B8EAC`。
- `mcp-frontend-route-lobby-live6.json`（352,192 bytes，SHA-256 `E0E8FF03AD61C71F4A9E52613FF27D5056502FF3579B961DF4E2134AE1B4675F`）的 inspector 以 native structured data 直接观察到可见、enabled 的 `lobbyview` 位于全局 root 深度 2；旧 fixed-name resolver 却返回 `unavailable`。根因是 resolver 的 4,096 节点深度优先预算被同层大型局内窗口的深子树先耗尽。固定名称解析现改为同上限的广度优先，优先覆盖浅层 top-level 身份；不扩大节点、深度、名称或动作边界。该 attempt 的 Steam offline 与 cleanup 均为 GREEN，但动作因旧 resolver 仍报告 RED。
- 修复后的 `mcp-frontend-route-lobby-live7.json` 为 GREEN（353,637 bytes，SHA-256 `FBD86144D7EFA066E9839AD5B729A58EB57EFF631AA6C2BA2ECD32458347FCE9`）。官方 MCP 完成 `bookmarks → lobby`，action ACK、独立 route 后置条件、零 OCR/键盘/鼠标、tree inspector、Steam offline 与受管 cleanup 全部通过；源码 commit `294b2afe3b2a67d693ef369c5f1aa56732610402`，DLL SHA-256 `ACD88796BD90715167AFF3409CC9008404837B84ED887B534C246BB746D89EC7`。第二段由 `mcp-static-ready` 提升为 `production-live primitive`，inspector 同步取得首份 live native tree evidence。

`mcp-frontend-route-lobby-live8.json` 完成聚焦 inspector 的受管实机验收（491,326 bytes，SHA-256 `46D167D73C65C51DDD736BBC494AFCA18003E0D5B8BE3606F461D543ACEA073B`）。报告中的 `scope_root_name=lobbyview`、`widget_count=512`、`truncated=true`；Steam offline、`cleanup_proven=true` 与 `tree_gone=true`。原版 `JominiLobbyViewPreparation` 对照表明相对路径 `3/0/2/3` 是 `TryStartRulerDesigning(Character.Self, 'default')` 的无名按钮；样本中该按钮可见但 disabled，同时 `tab_character_unselected` 可见，直接证明下一动作还必须先建立一个有效的 selected playable，不能把 disabled 控件 ACK 当作设计器已打开。源码 commit `9e0687649c22c0f3a96bcd5ac19c11da2e003136`，DLL SHA-256 `6D0917BE5451BC2109581D30C464213B82D7AEFCA709667E72C8BC9C63866A0E`。

2026-09-14 的静态包已补齐上述两个缺口：零输入 `ck3_activate_frontend_prepare_custom_ruler_v1()` 在书签页选择第一个可见、可用的固定名称角色卡，再调用既有 Pick Any，并以 lobby inspector 证明默认设计器按钮已经 enabled；零输入 `ck3_activate_frontend_ruler_designer_v1()` 只允许激活编译期冻结的 `lobbyview/3/0/2/3`，且独立观察 `ruler_designer` 后才返回 verified。调用方不能注入名称、路径、地址或输入事件。

静态验收为 fresh Release `549/549`、CTest `106/106`、Python contract/service/native-driver/official-MCP `7/7`；候选 DLL SHA-256 `38BDED238B182542C27BFCD860FB848EE9DEAD79F71E26998C9FDE8179DDA591`。`open_kaishek` 无 frontend GUI/CoA domain，本包预验证为 `not-applicable`。两项新增动作当前仍为 `mcp-static-ready / live=false`；下一步只用该 MCP 链做一次受管 CK3 实机验收并采样 `ruler_designer` 原生 tree，再补 CoA 页固定动作，禁止以鼠标链代替。
