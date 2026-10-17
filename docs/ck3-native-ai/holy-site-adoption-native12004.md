# HolySite 原版采用详情与一次确认

这是[圣地只读专题](holy-site-native12004.md)的后续实现，当前资格为 **生产源码编译、原生离线夹具与实际 MCP 消费通过；live pending**。研究机器为 `machine_id: 4-8e1c2f1861`，函数来源缓存观察于 `2026-10-17T08:31:53Z`，资格汇总更新于 `2026-10-17T09:23:06Z`；来源为 exact4 EXE 的有限函数缓存、独立审查与下列实际回执。目标 EXE SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。离线通过不能推断实机已执行。

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

外置证据根为 `C:/workspace/ck3-faith-and-power-20261017/episode01/native-candidate/`。来源原包：`gui-source/adopt-decision-detail-native-source.json`、`gui-source/decision-detail-safety-boundaries.json`、`gui-source/ADOPTION-DETAIL-INDEPENDENT-REVIEW.json`、`gui-source/CONFIRM-INTEGRATION-REVIEW.json`；reader 校验其中九个 loaded-code pins。两项独立审查均无阻塞发现，未执行 EXE 或游戏。

## 实际离线资格与边界

以下均为机器 `4-8e1c2f1861` 的本轮回执，精确观察时间位于各原包。Python 使用主树 `tools/.venv/Scripts/python.exe`，没有连接游戏或桌面。

- 原生 detail fixture 实际 36 checks PASS；生产 reader 和完整 `command_result` serializer 生成六份回包。覆盖原生 true、false、bypass 开启、bypass 不可读、参数高位错配、默认第一项与目标不同，以及拒绝后不调用 Confirm、合法时一次回调、字符串复制与析构配对。
- 生产 `create_server`、NativeDriver、normalizer 与真实 MCP ClientSession `list_tools/call_tool` 两项测试 PASS，保存六个原包调用与一个 foreign-build 负例，共七份返回。严格输入拒绝发生在 native I/O 前；未把测试包的错误 build 改成有效包。
- 主树合入并行 service 变更后，在 `ad3dcbe7b2a897720777e8791cfcff4f6e9c1891` 重新消费同六份回包，两项测试、七份返回再次 PASS。记录了实际加载模块的主树路径和七个相关文件的前后 SHA；没有重复执行原生夹具。
- 最终导航 fixture 在 a08 实际 exit0，保留全部断言；生成生产 serializer 的拒绝结果体。随后主树 `201606305bfb2f8ec4f4730e20d751c8ce68e288` 经真实 Service → Driver → MCP 开窗工具消费该结果体，保持 `available=false`、`native_dispatch_attempted=false` 与原拒绝原因。
- Python 另有两项新工具 schema/严格入参检查、一项公共四 permission 独立 optin、既有 70 项 UI 回归及一项原生树 root 合同通过。

**这些输入是显式合成的。** C++ fixture 使用自有内存布局、模拟 code/RTTI 读取以及测试 CanConfirm、Confirm、settings、tooltip、析构回调；没有调用原版游戏函数。详情包由实际编译的生产 reader/serializer 产生，Python 未预计算业务 DTO。Python endpoint、hello 和 paused snapshot 也是合成输入：actor `0x03000004`、HolySite `0x81000002`、native revision `701`、capture epoch `17`、date_raw `53175816`。这些数值不能用作任何真实存档的身份或帧。

导航拒绝结果体的 actor `29829`、native revision `3`、epoch `14`、date_raw `53146848` 同样是夹具帧。该消费单独使用显式合成的外层 `command_result`，其原生结果体不改写；它证明拒绝诊断可被现有动作通道消费，不能证明原版 Open 已调用、窗口已显示或采用已完成。

| 外置原件（相对于上述证据根） | SHA-256 |
|---|---|
| `adoption-native-mcp-qualification-a05.json`，隔离源码首次实际消费 | `5ac96cce1ea8b9550bc878c11f734461b18a5f7d297ae0ae9d69347df975e0d7` |
| `adoption-main-mcp-qualification-a07.json`，最新主树七份返回 | `0ff2be9e5c4c367d817e5ad40bcf35496d6de25b57b743b9d2adbbf5b13a1295` |
| `nav-denied-main-mcp-qualification-a09.json`，主树真实动作通道拒绝消费 | `1cdb06bf71763bdb60b607af1817ba0a98ec83071e80fe0a8b4e5fa52d605e01` |
| detail fixture EXE，位于 `../runtime/adoption-candidate-a03/build/` | `fadbbde9f2aa2e83d4226ee932e217173582fbebfdd908b79572d48befcabc46` |
| navigation fixture EXE，同一 build 根 | `4b532e6bfae952c0fb3abcfd39eee6c998b9083658c6cf06348d8c5a0e1c595c` |
| `../runtime/adoption-candidate-a03/a08/navigation-wire/holy-site-denied.json` | `50230cb628eddcef2ff67aa26bb83312c1ac4c8b45997ced4038c9299bbe7383` |
| `research-plan-adoption-a09.json`，十个证据文件检查通过 | `fe1ae126a623374fc8f92ea3f3610bf0bb53df5859a0422b47ae2bdecce886f7` |

六份 detail 原件位于 `../runtime/adoption-candidate-a03/normal-exit-increment/adoption-detail-wire/`，逐文件 SHA 在两份 MCP 回执中。研究计划的 `check --for-observation` 只证明记录结构与文件完整性：五条静态边、一条业务后验未知边、零条 live-confirmed，采用 live case 仍 pending。

初次构建及导航夹具的 RED 均保留：新增 Snapshot 命名空间错误、目标 UTF-8 选项、旧测试源依赖/投影函数签名与已合法 enum2 的过时负例均已修复。未删除断言；测试的无关 war binder 若被误调用会 assert/abort，不能返回假 owner。a03 的 `/UNDEBUG` 是显式编译约束，源码此前已有 `#undef NDEBUG`，不能据此声称此前断言全被关闭。生产 HolySite 业务源码在这些测试修复中未变。冻结原件与后续 delta 分开保存，详情原生/MCP 已通过部分未因无关修复重复重验。

下一层只由实际游戏回执补齐：真实窗口可见且选中目标、原版详情参数与普通 CanConfirm、一次原版 Confirm，以及独立的 Faith 关联和资源后验。当前不能把工具注册、源码、夹具 true、ACK 或窗口消失写成采用成功。

## R0002 实机入口缺口与修复候选

`machine_id: 4-8e1c2f1861`；实际观察 `2026-10-17T09:35:51Z–09:36:07Z`，离线诊断 `09:37:26Z`。来源为同机 run `4-8e1c2f1861--faith-and-power--R0002` 的 `root-native-receipts/` 原包，生产源码 `201606305bfb2f8ec4f4730e20d751c8ce68e288`。以下是新增实机边界，不改变上文夹具的合成性质。

- HolySite 窗口实际可见，当前完整 ID 为 `32`；actor `15893`、暂停、date_raw `51394920`。采用入口的原生可见判断为 true，Regular/Eminent 为 false。
- 单次打开采用详情请求在 dispatch 前返回 `adoption_entry_receiver_not_unique`，`native_dispatch_attempted=false`。随后详情读取返回 `adoption_detail_definition_unavailable_or_different`，两个 CanConfirm 字段均为 null。未调用 Confirm，未观察到采用效果。
- 563 个实际控件中，精确匹配 `OpenGameViewData→Close` 双回调的四行均位于原生标准点击选出的 `fallback` 组；其中仅 `1/3/1/3/4/0` 及其祖先实际可见且 enabled。旧 Signature 强制 `primary_group`，因此错误排除了唯一 receiver。此次错误不是 native 合法性拒绝，也不是控件禁用。
- 原版 `0x3AA0D20→0x3A9FA30` 的 mode0 标准点击在 primary 无回调时执行 fallback；现有 producer/dispatcher 已支持该语义。候选修复 `002c9cfb93f0e299540eafcbfa9215a45c6dab6e` 只移除 primary 限制，仍保留完整有序双回调匹配、唯一性、可见/禁用/模态准入与两次读取的 group 稳定性，并增加对应断言。它尚未获得本轮原生增量及新实机资格，不能热换当前 DLL。

原版 `window_decisions.gui:384–417` 用 `DecisionTypeWithParams.IsPossibleForPlayer` 控制灰图、灰标题及红叉；它没有把该条件绑定为按钮 enabled。灰色外观不应被智能体转换为已观测的 detail CanConfirm=false。修复入口后，优先继续原版 dispatcher，再由现有详情查询读取真实 `selected_item`、普通条件开关、CanConfirm 和完整原生 Confirm tooltip；未知结果不得重放动作。

| 外置原件（上述 root-native-receipts） | SHA-256 |
|---|---|
| `r2-nadjaf-tree-a01.json` | `dccf0a6aa00b7b516ddce345430a65968b1959bf951f8a9f09f4f1a592c3a8ff` |
| `r2-open-adoption-a01.json` | `652f1c38ea3f256dbaee282d4da4f726f4ae8d1ef3f5fb2b77416a17973a4420` |
| `r2-adoption-detail-a01.json` | `731115d1ba3d4cc5cb76389ac2b1448ce55a869cdc6c3bf458612b096fa85af8` |
| `r2-adoption-tree-a01.json` | `0bf0e74073cddf9502823efedc6d5e9ed8e7cc36e9593cd451b877b33b239ecf` |

离线来源绑定位于上述 native-candidate 根的 `r2-adoption-entry-diagnostic-a01.json`、`gui-source/fallback-and-params-tooltip-source.json` 与 `adoption-fallback-fix-a11.json`。最后一份不可变两文件 freeze 的 SHA-256 为 `9fe755d757d7f6920549350d672cad01037ef1e37103fc37189c9bf4166cdfb3`。缓存中原版 `IsPossibleForPlayer` 与 `GetCommandDescForPlayer` 的只读 ABI 也已另行闭合；它们是候选预览，不替代实际详情的最终许可。
