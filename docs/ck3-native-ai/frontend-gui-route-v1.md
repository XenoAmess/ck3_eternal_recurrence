# CK3 frontend GUI route MCP v1

状态：`production-live primitive`
适配目标：CK3 `1.19.0.6`，EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`

## 目的与边界

该 primitive 用于补齐开局前无法取得 gameplay snapshot 时的语义导航。它读取 CK3 当前 GUI owner tree，并只允许编译期固定动作：
从主菜单激活原版 `new_game_button`；在书签页激活 `pick_any_character_button`；在 lobby 激活原版“随机可玩角色”按钮；
最后激活编译期冻结的默认角色设计器子路径。它不截图、不做 OCR，不发送鼠标或键盘事件，也不接受调用方提供的 native pointer、
控件名、子路径或回调地址。

首版只闭合：

```text
main_menu --activate-frontend-new-game-v1--> bookmarks
bookmarks --activate-frontend-pick-any-character-v1--> lobby
lobby --activate-frontend-select-random-playable-v1--> ready lobby
lobby --activate-frontend-ruler-designer-v1--> ruler_designer
ruler_designer --activate-frontend-coat-of-arms-designer-v1--> coat_of_arms_designer
```

上述五段均为 `production-live primitive`。最后一段由 live native tree 与原版 GUI 源码固定目标，并由官方 MCP 的独立
route/page 后置条件完成实机闭合；上层 Finish 仍不在当前闭环内。

## MCP 合同

```text
ck3_query_frontend_gui_route_v1()
ck3_inspect_frontend_gui_tree_v1()
ck3_inspect_frontend_coat_of_arms_tree_v1()
ck3_inspect_frontend_coat_of_arms_pattern_grid_v1()
ck3_activate_frontend_new_game_v1()
ck3_activate_frontend_pick_any_character_v1()
ck3_activate_frontend_prepare_custom_ruler_v1()
ck3_activate_frontend_ruler_designer_v1()
ck3_activate_frontend_coat_of_arms_designer_v1()
ck3_activate_frontend_coat_of_arms_custom_mode_v1()
ck3_commit_frontend_dynasty_coat_of_arms_v1()
```

对应 bridge capability/step：

```text
game.command.query-frontend-gui-route-v1
query-frontend-gui-route-v1

game.command.inspect-frontend-gui-tree-v1
inspect-frontend-gui-tree-v1

game.command.inspect-frontend-coat-of-arms-tree-v1
inspect-frontend-coat-of-arms-tree-v1

game.command.inspect-frontend-coat-of-arms-pattern-grid-v1
inspect-frontend-coat-of-arms-pattern-grid-v1

game.command.activate-frontend-new-game-v1
activate-frontend-new-game-v1

game.command.activate-frontend-pick-any-character-v1
activate-frontend-pick-any-character-v1

game.command.activate-frontend-select-random-playable-v1
activate-frontend-select-random-playable-v1

game.command.activate-frontend-ruler-designer-v1
activate-frontend-ruler-designer-v1

game.command.activate-frontend-coat-of-arms-designer-v1
activate-frontend-coat-of-arms-designer-v1

game.command.activate-frontend-coat-of-arms-custom-mode-v1
activate-frontend-coat-of-arms-custom-mode-v1

game.command.commit-frontend-dynasty-coat-of-arms-v1
commit-frontend-dynasty-coat-of-arms-v1
```

路由枚举为 `unavailable`、`main_menu`、`bookmarks`、`lobby`、`ruler_designer`、`coat_of_arms_designer`。动作分别要求
`main_menu → bookmarks`、`bookmarks → lobby`、`lobby → ruler_designer` 与 `ruler_designer → coat_of_arms_designer`；原生调用只返回 `acknowledged_verification_pending`。driver 必须另行轮询 route，
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
| `game/gui/multiplayer_lobby.gui` | 31,100 | `DA5CFBBC695FE480E814EA6580A811B7719AB08E5A0359FBBB9EC98934425F17` | `JominiLobbyViewButton`；`onclick = [SetRandomPlayableObserverCharacter]`；live 相对路径 `4/0/1/0/1` |
| `game/gui/multiplayer_types.gui` | 56,911 | `93912D008D2362955470E7F42029280C41E3E316E28D8D1055EE09DFBE8BC3A3` | ruler-selection root `lobbyview`；后续设计器入口调用 `TryStartRulerDesigning` |
| `game/gui/window_ruler_designer.gui` | 118,240 | `C5761FD395E0C3D7FDF320DDE41DA900928F0A2EB217524E25348CCCC07ABDC9` | root `ruler_designer`；`dynasty_house` 编辑按钮调用 `OpenDynastyCoatOfArmsDesigner`；page `coat_of_arms_page` |
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

CoA 另有两个更窄的零输入只读入口。`ck3_inspect_frontend_coat_of_arms_tree_v1()` 仅允许当前 route 为
`coat_of_arms_designer`，并从固定 `ruler_designer` 解析可见、enabled 的 `coat_of_arms_page`。
`ck3_inspect_frontend_coat_of_arms_pattern_grid_v1()` 再把 root 收窄到背景页无名网格：固定完整 child path 为
`0/2/0/3/0/2/1/1/2/0/0/0/0`，且四个有名祖先必须依次匹配
`coat_of_arms_page → background_panel → patterns → patterns_scrollbox`。调用方仍不能提供 root、path、pointer 或 limit。
其结果使用有界广度优先遍历，Python 合同要求根报告的全部直接子项 `0..N-1` 均实际出现在结果中；深层节点仍可因 512 行上限
标记 `truncated=true`。该固定网格入口当前为 `mcp-static-ready / live=false`：原生完整构建与 `127/127` CTest、Python
contract/service/native-driver/official-MCP、Quarkus REST 和 Vue API 回归已通过，但尚未用新工具取得受管 CK3 实机结果。

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
2. 从固定 root 重新解析 target：两个旧动作使用固定名称；随机选角动作只取 `lobbyview` 下编译期路径 `4/0/1/0/1`；设计器动作只取 `lobbyview` 下编译期路径 `3/0/2/3`；CoA 动作只取 `ruler_designer` 下编译期路径 `0/0/0/0/0/0/0/3/1/0/1`；
3. 有名控件必须精确匹配 runtime name；三个固定路径按钮必须保持空名；所有 target 都必须 visible/enabled；
4. target GUI context、button vtable slot、callback group 与 modal admission 通过现有 exact-build 原生 dispatcher；
5. 调用 `CPdxGuiShortcutManager`；该返回值只算 ACK；
6. Python driver 独立查询并观察对应的 `bookmarks`、`lobby`、`ruler_designer` 或 `coat_of_arms_designer`，才能报告 verified；准备动作先从 inspector
   证明 `4/0/1/0/1` 可操作，执行选角后再独立证明 `3/0/2/3` 已 enabled。

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

最初的 2026-09-14 静态实现错误地把“选择书签人物”与 `Pick Any` 串联。三份受管 attempt 均保持 Steam offline、
零 OCR/键盘/鼠标且 cleanup GREEN，但不能证明进入角色设计器：`mcp-frontend-route-ruler-designer-live1.json`
（96,248 bytes，SHA-256 `CDCCD36EDEA3A385D0A2EFC77D58672FFD647ED1ECD97EBF515362C451E3C92E`）进入了未选角色 lobby；
`live2`（95,247 bytes，SHA-256 `01FFD5832D6BF0E04F81D0A7F32AA9CBD79E4BCC96F0C11AA88722321E3FDEAF`）与
`live3`（95,232 bytes，SHA-256 `F2C616951292D6631819FB1EFD7E9AD71103559F7158D3B11EC1582205DA6636`）都由
application-main executor fail closed。原版源码解释了这个分叉：书签人物卡设置 `GameSetup.SetSelectedCharacter` 后应走该页
`GameSetup.StartGame`，而 `pick_any_character_button` 走 `GameSetup.OnCustomStart` 打开自由选择 lobby；这两条不是可串联的状态延续。

替代实现使用同一份 `live8` 原生 tree 中已经观察到的 lobby 按钮：相对路径 `4/0/1/0/1` 为空名、visible/enabled，
相邻 `4/0/1/0/0` 是不可见的找头衔入口，`4/0/1/0/2` 是观察者模式；原版 `multiplayer_lobby.gui:1131`
把目标精确绑定到 `SetRandomPlayableObserverCharacter`。零输入 `ck3_activate_frontend_prepare_custom_ruler_v1()` 现先进入 lobby，
验证并激活这一个固定目标，再由 inspector 证明默认设计器按钮 `3/0/2/3` 已 enabled；
`ck3_activate_frontend_ruler_designer_v1()` 仍只允许激活 `3/0/2/3`，且独立观察 `ruler_designer` 后才返回 verified。
调用方不能注入名称、路径、地址或输入事件。

替代包的 Release 编译链接、Python contract/service/native-driver/official-MCP 聚焦测试及 CTest `106/106` 均 GREEN；
当前 DLL 为 2,701,312 bytes，SHA-256 `5573805A227AE86683FD7C846B8E4BA621F60CF10725067ADC55D1055A24456C`。
首次全量 CTest 因旧构建缓存把 `XAR_CK3_EXECUTABLE_PATH` 指向仓库内不存在的忽略路径而产生 9 项 environment RED；重新配置为
exact 安装 EXE 后同一套测试为 `106 passed / 0 failed`，因此前者不是能力 RED。`open_kaishek` 无 frontend GUI/CoA domain，
本包预验证为 `not-applicable`。

2026-09-14 的 `mcp-frontend-route-ruler-designer-live4.json` 已把随机选角与进入角色设计器提升为
`production-live primitive`（911,495 bytes，SHA-256 `23F752FF7FF37A5354BD35DE92777EFDA746225DC4FDE980A1FD6DA064666CAE`）。
官方 MCP 全链检查均为 true，Steam offline；共享 CK3 启动锁与状态锁覆盖启动至 cleanup，PID 4848 与 watchdog 均已回收。
其 `ruler_designer` scoped tree 固定观察到 `dynasty_house` 路径 `0/0/0/0/0/0/0/3`，其内容行
`0/0/0/0/0/0/0/3/1/0` 可见、enabled 且恰有两个子项。原版 `window_ruler_designer.gui:514-548` 证明第二个子项
就是调用 `OpenDynastyCoatOfArmsDesigner` 并设置 `coat_of_arms_customization_open='dynasty'` 的编辑按钮。

据此新增的零输入 `ck3_activate_frontend_coat_of_arms_designer_v1()` 只允许上述固定 leaf，且必须独立观察 route
`coat_of_arms_designer` 与可见 `coat_of_arms_page` 才返回 verified。rebase 到 exact `master` 后的 Release DLL 为
2,702,848 bytes，SHA-256 `973B9EB1A4BAA926811CD06237A8B8173CC4459C7F9140221AFD45242E537095`；Python 普通/优化模式各 `11/11`、runner
普通/优化模式各 `2/2`，原生套件为首次 100/106 加修正后失败六项 6/6，即等价 `106/106`。

最终受管实机 `mcp-frontend-route-coa-page-live5.json` 已将这段提升为 `production-live primitive`（1,185,843 bytes，
SHA-256 `6BE30B3C356CCE22D279FD1906BAFE6474451D7FFCB5EF2229E5B538A0106103`，源码 commit
`c3f074a8f8f6717dd0a40f23b796c6d8a2d23881`）。官方 MCP 依次完成五段 route，最终独立观察到可见、enabled 的
`coat_of_arms_page`（路径 `0/2`）、`dynasty_detail_input`（`0/2/0/0`）与 `dynasty_finish_button`（`0/2/1/1`）；
所有 ACK、route/postcondition、native backend 与零 OCR/键盘/鼠标检查均为 true。Steam 保持离线，共享锁释放和受管 cleanup
均为 GREEN，PID 19424 与 watchdog 已回收。该证据只证明进入原生家徽页，不证明上层角色设计器 Finish 或纹章持久化。

后续语法扩展不再需要另写桌面导航链。runner 现提供 opt-in `--syntax-matrix`：先复用同一官方 MCP route，再读取 checked-in
`coat_of_arms_syntax_matrix_v1.json` 的 15 个固定 ASCII 载荷，在同一 designer 依次采集 detect、可选 apply 与 native
Copy/export。两项既有 `mcp-applied` 用例是回归门，八项边缘用例只要求完整记录 apply 或 apply-failed，五项已知拒绝用例要求
`not_detected` 且 Copy 前后源码哈希不变。矩阵文件 SHA-256 为
`ADFBB02A097A5B13452743761D693A78FBB988570DEE3A80A5EFEC764F6BA13F`；普通/优化合同测试各 `4/4`。该 runner 尚未在 CK3
执行，状态仅为 `mcp-static-ready / live=false`，不改变第 5 节既有语法结论。
