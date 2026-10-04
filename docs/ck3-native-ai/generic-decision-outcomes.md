# 通用决议确认：事件窗口与窗口关闭

2026-10-05 新增，适用 CK3 1.20.0.3，EXE SHA-256 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。

《礼与道》的议案、签署和撤回需要反复执行普通决议。原接口的确认后置条件限定为白绮窗口，不能用于这些决议。本次新增独立通用接口，保留原接口及其既有回执格式。

Gameplay MCP：`ck3_confirm_ingame_decision_outcome_v1(decision_key, expected_outcome, expected_revision, expected_event_definition_key=None)`。冻结 profile 提供对应的 `ck3_confirm_profile_decision_outcome_v1`，以及打开决议、查询指定决议、选择指定决议三项接口。profile 仍使用既有九字段结构；功能开关属于 DLL 编译及实际能力发现。

| 预期结果 | 调用参数 | 独立读回 |
| --- | --- | --- |
| 打开事件 | `expected_outcome="event_window"`，完整 `namespace.numeric_id` | 当前事件实例、完整定义、玩家 root、日期及实际帧绑定 |
| 关闭详情 | `expected_outcome="decision_closed"`，事件参数为 `None` | 完整 stock `decision_detail` 树中 `decisiondetail_view` 的实际隐藏状态 |

关闭分支的管道请求将 `None` 编码为空字符串。既有共享字符串解析器拒绝空字符串，故新增 route-local 解析，保持共享解析器不变。编译测试实际链接 `protocol.cpp`，覆盖两种请求及缺失、null、重复、嵌套等错误输入。

确认前需要真实选中的决议定义与玩家详情 owner，无当前事件或待答互动。原生 provider 使用现有 stock ConfirmReceiver 和原 dispatcher，仅调用一次。ACK 表示已经尝试调用，仍需 Python 的独立读回；未知结果保留 claim，不能通过换 revision、重连或换确认接口重试。

成功决议可能隐藏自己的列表行。关闭后必须直接读取完整 GUI 树，不能把按 key 查询失败所返回的默认布尔值当作窗口已关闭。原始树没有玩家、PID、revision 字段，使用外层前后实际 control frame 绑定；缺树、截断或仍可见均不证明关闭。

当前事件 provider 按实例匹配已物化的数据，未证明哪个事件位于画面最前。接口因此始终返回 `front_event_verified=false` 和 `event_option_selection_authorized=false`。选事件选项仍需当次单事件存档与可见语义证据，R6 中 SDK active 与画面前台不同的记录继续保留。

成功的 UI 读回始终返回 `business_effects_verified=false` 和 `full_product_acceptance_credit=false`。费用、信仰、礼仪、签名、宗教领袖及其他结果由实际存档分别验收。公开 revision 可以因 checkpoint 或重连增长，不能作为某个业务周期已经完成的证据。

DLL 新开关 `XAR_CK3_ENABLE_INGAME_DECISION_OUTCOME_PRIVATE_V1` 默认关闭，依赖 item-action 开关。验收构建另启用既有 MODEL、START、DECISIONS_OPEN、ITEM_ACTION 开关，实际新 HELLO 必须包含决议操作、事件查询、GUI 树及 frontend identity 能力。编译成功不能代替 HELLO。

本轮主树 40 项决议/旧接口回归和 18 项 profile 测试通过；作者另完成完整 DLL 编译、25 项源码检查、7 项负向编译检查及 128 组旧回执字节比对。当前状态为 static-ready，尚未注入游戏。详见[本轮集成记录](../li-yu-dao/acceptance/2026-10-05-generic-decision-integration/README.md)。下一步从最终集成 HEAD 构建，再在新隔离实机 attempt 验证。
