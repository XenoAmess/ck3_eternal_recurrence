# 考核榜 named-widget MCP action 单元

状态：**static-ready / live RED**。本单元已经实现 allowlisted 动作合同、
ACK schema、Python admission/post-query verifier、C++ admission/dispatch primitive
和专属 native fixture；尚未接共享 mailbox/driver/service/MCP，也没有启动 CK3。
OCR、屏幕坐标、任意 widget 名和任意变量读写均不在这条路径里。

## 1. 固定动作面

能力名冻结为 `game.command.activate-zhongguo-scoreboard-v1`，step 为
`activate-zhongguo-scoreboard-v1`。动作只允许：

| action | provider-owned 真实目标 | 后置 |
|---|---|---|
| `open` | 当前关闭态唯一可见的 managed/received/system 入口 | modal 打开；对应 list page 唯一可见 |
| `switch-managed` | `zg361_scoreboard_tab_managed` | managed list page 唯一可见 |
| `switch-received` | `zg361_scoreboard_tab_received` | received list page 唯一可见 |
| `switch-system` | `zg361_scoreboard_tab_system` | system list page 唯一可见 |
| `close` | `zg361_scoreboard_header_close` | modal 与三个 page 全部不可见 |
| `reopen` | 当前关闭态唯一可见的入口 | modal 打开；对应 list page 唯一可见 |

`open/reopen` 不让 caller 提交目标名字：provider 从同一 paused query 中三选一，
若零个或多个入口有效可见则拒绝。managed 切页还要求 materialized managed ACL，
received 切页要求 received-self surface；不能按爵位猜权限。

## 2. 固定 state/action identity

只读 `zhongguo_scoreboard_state_v1` 的固定实例从 9 个扩为 15 个：原有
window/toggle/modal/panel、三个入口、backdrop/header close，加上三个页签目标和
三个 list-page 后置 witness。新增 GUI identity 为：

- `zg361_scoreboard_tab_managed`、`zg361_scoreboard_tab_received`、
  `zg361_scoreboard_tab_system`；
- `zg361_scoreboard_page_managed`、`zg361_scoreboard_page_received`、
  `zg361_scoreboard_page_system`。

这些只是名字与既有 exists/local/effective-visibility ABI 的扩展；没有据此猜
enabled、focus、modal-stack、rect、scroll 或 callback ABI。当前只读 provider 仍把
enabled 返回 `enabled_state_abi_not_frozen`，所以生产 action 必然在 dispatch 前
fail closed。

## 3. 请求与 ACK

请求绑定以下字段：

- `request_nonce`、allowlisted `action`；
- `expected_revision`、`expected_native_revision`、
  `expected_connection_generation`；
- `expected_player_character_id`；
- `expected_window_instance_pointer`；
- `expected_target_instance_pointer` 与
  `expected_target_vtable_pointer`。

请求没有 `widget_name`、角色 scope、坐标、变量名或 callback 地址。instance/vtable
只是在同一 paused query 内使用的短期 identity，不能跨 revision 或重连复用。

dispatch 被 executor 接受后只能返回
`acknowledged_verification_pending`。ACK 回显 exact source/target binding，并冻结：

- 最小后置 public/native revision（均为 source + 1）；
- modal 应当打开还是关闭；
- 预期 active outer tab；
- 是否必须回到 list；
- 必须保持的 scoreboard-window instance。

ACK 的 `postcondition_verified` 永远是 `false`。它不能因为 native callback 返回
true 就写成 GUI 成功。

## 4. 独立 post-query

PASS 只能由另一个 nonce 的只读查询给出，并同时满足：

1. public 与 native revision 都至少增长 1；
2. connection generation、player、date、window instance 未变；
3. modal effective visibility 与动作一致；
4. 打开/切页/重开后，预期 page witness 恰好一个有效可见；
5. 关闭后三个 page witness 全部不可见。

关闭时隐藏页面无法证明 `detail_tab=facts`；本单元不把该不可观察状态冒充已
验证。重开后的 list-page witness可以证明已经退出 detail view。若今后必须单独
证明隐藏的 facts selection，应先补 typed 观测口，不能靠 ACK 或 GUI 定义推断。

## 5. fail-closed 矩阵

在调用 executor 之前拒绝：非法 action/nonce、revision 溢出、public/native
revision 不匹配、connection/player/date 重绑、非 paused/player/same-frame、固定
实例集合不完整、window/target instance 或 vtable 重绑、目标不存在/不可见、
enabled 不可读、disabled、managed/received ACL 拒绝、modal 开关状态不适合该
动作，以及 production dispatch 尚未接通。fixture 断言所有这些拒绝路径的
dispatch 计数为 0。

## 6. 已有静态证据

- Python action contract：normal 与 `python -O` 各 8 项 GREEN；
- 扩展后的 scoreboard state contract/MCP fixture：normal 与 `python -O` 各
  11 项 GREEN；
- fresh MSVC `/std:c++20 /W4 /WX /O2` action fixture：编译与执行 exit 0；
- fresh MSVC `/std:c++20 /W4 /WX /O2 /DNOMINMAX` 15-widget state fixture：
  编译与执行 exit 0；
- 证据目录：
  `Z:\ck3_mod_rewrite_process_assets\zg361-scoreboard-action-native-fixture-20260901`。

以上都是 static/fixture 证据，不是 production-live。

## 7. 后续精确 wiring patch（本轮不碰共享文件）

等 Workforce/G2 释放共享路径后，按以下最小补丁接线：

1. 冻结 effective-enabled exact-build ABI；让 state provider 对 7 个动作目标返回
   typed enabled，保留其他未冻结字段 unavailable。
2. 取得 dispatcher → PushButton callback 的 paused trace，证明 upstream admission、
   onclick identity、modal stack/top receiver；禁止直接调用当前候选 RVA。
3. 增加 scoreboard 专属 canonical state revision；它只随 open/tab/list/detail 等
   规范状态改变，不拿 query sequence 冒充 revision。
4. 为 action 增加独立 mailbox request/ACK slot；不得覆盖现有第 18 槽只读查询，
   也不得与 Workforce 当前第 21 槽冲突。
5. 在 `game_contract.hpp`/adapter/bridge、`native_driver.py`、`service.py` 和
   `mcp_server.py` 只做上述 capability 的窄注册；public 参数严格等于本合同。
6. runner 流程固定为 source query → action ACK → later-pump query；保存 raw
   request/ACK/post response 和 cleanup。先合批 open、三切页、close、reopen，再做
   managed/received-only ACL 角色矩阵。

## 8. 当前 exact-build blocker

- `enabled` 的完整 effective 语义尚未冻结；
- callback candidate 与真实 onclick/upstream admission 尚未闭合；
- `filter_mouse=all` 到 modal stack/top receiver 的运行语义尚未闭合；
- scoreboard canonical revision 尚不存在；
- 15 个固定实例（尤其 6 个新 tab/page identity）尚无当前 SHA paused artifact；
- 共享 mailbox/provider/MCP 尚未接线；
- 无真实 action ACK + later-query artifact。

任一 blocker 未解决前，`full_widget_gate_ready=false`、
`production_live_ready=false`，正式 phase2 runner 的 scoreboard action cell 继续 RED。
