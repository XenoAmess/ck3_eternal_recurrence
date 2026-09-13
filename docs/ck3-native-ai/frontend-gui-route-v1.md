# CK3 frontend GUI route MCP v1

状态：`mcp-static-ready / live=false`
适配目标：CK3 `1.19.0.6`，EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`

## 目的与边界

该 primitive 用于补齐开局前无法取得 gameplay snapshot 时的语义导航。它读取 CK3 当前 GUI owner tree，并只允许一个固定动作：
从主菜单激活原版 `new_game_button`。它不截图、不做 OCR，不发送鼠标或键盘事件，也不接受调用方提供的 native pointer、
控件名或回调地址。

首版只闭合：

```text
main_menu --activate-frontend-new-game-v1--> bookmarks
```

bookmarks → ruler designer → coat-of-arms designer 目前只支持路由观察，尚无动作 primitive。上层 Finish 也不在 v1 范围内。

## MCP 合同

```text
ck3_query_frontend_gui_route_v1()
ck3_activate_frontend_new_game_v1()
```

对应 bridge capability/step：

```text
game.command.query-frontend-gui-route-v1
query-frontend-gui-route-v1

game.command.activate-frontend-new-game-v1
activate-frontend-new-game-v1
```

路由枚举为 `unavailable`、`main_menu`、`bookmarks`、`ruler_designer`、`coat_of_arms_designer`。动作要求 before route 为
`main_menu`；原生调用只返回 `acknowledged_verification_pending`。driver 必须另行轮询 route，并且仅在 after route 为
`bookmarks` 时返回：

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
| `game/gui/frontend_bookmarks.gui` | 111,993 | `C853B48F42A5A3B84208B2FC570C02F5FCB5DA217133553C6A5B70B7F8F0F267` | root `frontend_bookmarks`；后续候选 `pick_any_character_button` |
| `game/gui/window_ruler_designer.gui` | 118,240 | `C5761FD395E0C3D7FDF320DDE41DA900928F0A2EB217524E25348CCCC07ABDC9` | root `ruler_designer`；page `coat_of_arms_page` |
| `game/gui/shared/coa_designer.gui` | 56,297 | `2F3B863A7FEA692D630825052426CCC674403D096C37DD470E63C923D2D356EC` | CoA designer 结构来源；v1 不从文件文本执行动作 |

运行时不会根据这些磁盘文本猜页面；DLL 每次都从当前 GUI owner 重新解析固定 root/descendant，读取 runtime name、vtable、
visibility 和 enabled 状态。route priority 为 `coat_of_arms_designer > ruler_designer > bookmarks > main_menu > unavailable`。

## application-main 与 gameplay 隔离

旧 mailbox 只在连续两个“暂停、Jomini state 和 game state 均有效”的 SDL pump 后允许局内 typed executor。前端没有这些对象，
因此 v1 另建 application-main ownership proof：连续两个 pump 必须具有相同的当前线程、TLS initialized 地址、TLS context 和
main-thread marker。只有固定 `ExecuteFrontendGuiRouteMailboxV1` 可使用这条门禁；原有 gameplay executor 仍要求完整 paused
proof。

`main_thread_query_mailbox_v1.ready` 保留旧的 paused-gameplay 含义，新增诊断为
`application_main_observed` 与 `owner_verified_pump_epochs`，防止消费者把“主菜单可查”误写成“局内命令可用”。

## 动作验证

`new_game_button` 动作按以下顺序 fail closed：

1. 当前 route 必须是 `main_menu`；
2. 从 `mainmenu_panel_bottom` 重新解析 `new_game_button`；
3. runtime name 精确匹配且控件 visible/enabled；
4. target GUI context、button vtable slot、callback group 与 modal admission 通过现有 exact-build 原生 dispatcher；
5. 调用 `CPdxGuiShortcutManager`；该返回值只算 ACK；
6. Python driver 独立查询并观察 `bookmarks`，才能报告 verified。

## 验收状态与下一步

- fresh MSVC build 已生成 DLL；
- 原生 fixture 覆盖“无 Jomini/game state 时 frontend executor 可用、gameplay executor 仍拒绝”；
- Python contract/service/native-driver/MCP closed-schema 测试覆盖 route、ACK 与独立 postcondition；
- 当前尚未重启 CK3，因此 `live=false`；
- `open_kaishek` 没有 frontend GUI/CoA domain，本包预验证为 `not-applicable`。

下一次 live 只需用 MCP 完成 `query(main_menu) → activate → query(bookmarks)`。若该首片 GREEN，再按相同固定 allowlist 方法补
`pick_any_character_button` 之后的 ruler selection、ruler designer 与 CoA 页动作；禁止以鼠标链代替缺失 primitive。
