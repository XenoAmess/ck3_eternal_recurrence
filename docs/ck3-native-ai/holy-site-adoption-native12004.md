# HolySite 原版采用详情与一次确认

这是[圣地只读专题](holy-site-native12004.md)的后续候选实现。研究机器为 `machine_id: 4-8e1c2f1861`，函数来源缓存观察于 `2026-10-17T08:31:53Z`，集成记录更新于 `2026-10-17T08:51:02Z`；来源为 exact4 EXE 的有限函数缓存与独立审查回执。目标 EXE SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。native 编译、fixture 和 live 资格分别记录，不能由源码成立推断实机已执行。

生产路线仍使用同一游玩智能体：`ck3_open_holy_site_window_v1` → 独立 `ck3_query_ingame_ui_window_v1(window_kind="holy_site")` → `ck3_open_holy_site_adoption_decision_v1` → `ck3_query_player_holy_site_adoption_detail_v1` → 符合普通原生条件时 `ck3_confirm_holy_site_adoption_decision_v1` → 独立查询 Faith、资源与站点后验。每一步绑定新鲜 revision；最终确认不可重试结果未知的调用。

隐藏 `adopt_holy_site_decision` 的原版入口携带 `selected_item`，不会保证出现在普通 keyed 决议列表。既有 `ingame_decision_item_v1.cpp` 对实际可见决议行的 guard 保持原样。新入口只在实际 HolySite 窗口目标一致、Adopt 原生可见、Regular/Eminent 两种替代动作均不可见时，查找唯一有效可见且启用的原版双回调按钮；再逐层回读路径、上下文和完整 callback descriptor，调用现有原版 shortcut dispatcher。它只打开详情，不能证明采用合法或完成。

详情通过既有 religion mailbox 的 owner 线程读取，原生 step 为 `query-player-holy-site-adoption-detail-v1`，在基础 player/context 后直接返回。独立 MCP CLI optin 为 `--private-holy-site-adoption-detail-query`；公共 case 的 `required_mcp_tools` 和 `opt_in_read_only_mcp_tools` 均列入 `ck3_query_player_holy_site_adoption_detail_v1`。默认关闭，复用既有 `XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1`，没有新增游戏 ABI 开关。

| 实际 producer / consumer | 采用详情的证据与约束 |
|---|---|
| handler `+0x1B8` / detail `+0xA0` | `DecisionDetailView` primary vtable `0x455D4F8`、RTTI type `0x5795050`，且回指同一 handler；root `+0x60` 的渲染可见性另行读取 |
| detail `+0xD0` / definition | 原生字符串 key 必须是 `adopt_holy_site_decision`；definition vtable `0x48BD150`、RTTI `0x5586B90` 与 magic `0x4744624F` |
| detail `+0xD8/+0xDC` | actor 必须同时等于 GetPlayer frame 和 `0x54DBC00` 当前 actor；普通决议 option 必须为 `-1` |
| detail `+0x248` | `SelectScopeController` vtable `0x45A08F0`、RTTI `0x5802AC0`，回指 detail 和 handler；拥有的非多态参数 context 为 `+0x18` |
| controller `+0x20/+0x38` | 0x40-byte 候选条目的实际 selected index 和 selected 标记；不能把默认第一项当作请求目标 |
| context `+0x28` | 24-byte 字典条目，以实际动态 token `0x5D4C2EC` 唯一找到 `selected_item` |
| 原版 Scope | kind=23、flags=0、64-bit payload 必须为请求完整 uint32 HolySite ID 的零扩展；参数与实际选中条目同时匹配，再查 storage generation；不比较未初始化 padding `+4..7` |
| `0x1471140` → `0x1471C10` | 原版 detail `CanConfirm`，读取两次且完整控制器/参数快照稳定；明确区分 true、false、unavailable |
| `0x1471150` / `0x856050` | 原版确认 tooltip 返回的 32-byte CString，复制后配对调用原生析构；成本报价仍为 unknown，不能由文本伪造结构化成本 |
| `0x1471190` | 单次原版 Confirm；内部再次判断 CanConfirm 并构造原版命令。专口不自行构造游戏命令或直接添加 HolySite |

一个影响合法性的原生边界是 `bypass_requirements`。`0x288D630` 在基本 actor/选择器检查后，可通过 `0xA75D00` settings singleton 的 `+0x10` 字节，对人类玩家提前返回 true，跳过普通条件和成本检查。这不是 `debug_mode` 的推断。候选只观察该字节，不更改它；未读到或非零时，`native_can_confirm` 可以保持真实引擎返回值，但 `normal_requirements_can_confirm` 必须为 null。最终确认要求实际读到零，并在调用前重新读取 detail、参数、目标、actor、原生判定及此开关。

确认专口使用现有 UI owner/TLS、paused map、snapshot、modal 和 GUI context 守卫，再要求实际 `decisiondetail_view` 可见启用且 root/handler 与详情一致。调用前设置 `native_dispatch_attempted`，异常或 ACK 不能抵消已消耗的尝试。原版确认可能清除 `+0xD0/+0x248` 并关闭窗口；窗口消失只证明界面变化，必须另查 Faith 关联、资源及同一站点 ID 才能记录采用后验。

外置证据根为 `C:/workspace/ck3-faith-and-power-20261017/episode01/native-candidate/`。来源原包：`gui-source/adopt-decision-detail-native-source.json`、`gui-source/decision-detail-safety-boundaries.json`、`gui-source/ADOPTION-DETAIL-INDEPENDENT-REVIEW.json`；reader 校验其中九个 loaded-code pins。独立审查未执行 EXE 或游戏。Python 聚焦测试目前通过 2 项真实 MCP schema/严格入参测试、1 项公共四 permission 独立 optin 测试及既有 70 项 UI 回归；native fixture、编译与 live 仍待单独回执。
