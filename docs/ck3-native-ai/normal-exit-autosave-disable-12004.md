# 原版退出自动保存关闭动作（CK3 1.20.0.4）

本能力扩展已有 `normal-exit-map-v1`，供受管验收在原版退出确认页关闭退出自动保存。来自 More Tenets Slots 两次实际收尾未赶上原 900 秒 hold 的需求；产品场次记录归独立仓库的 `docs/native-runtime-r17-r18-lifecycle-2026-10-15.md`，不将本次框架离线资格当成该产品实机通过。

## 固定动作与读回

`ck3_query_normal_exit_context_v1` 在可支持的原版确认页增加 `native_observation.exit_autosave`：`state_available`、`control_visible`、`control_enabled`、`should_save`、`disable_claimed`、`dispatch_invoked`、`postcondition_observed`。前三项与 `should_save` 是当前观察；查询本身不派发动作。旧 DLL 的无此字段结果仍可用于原有退出阶段，但不能用于新动作。

对最新 query 返回的 revision 和签名调用原有 `ck3_request_normal_exit_v1`，`action="disable_exit_autosave"`。不新增 widget、地址、路径或布尔设置参数。目标固定为 `false`：

- 原版状态已为 false：只读确认，返回 `autosave_disabled`，不调用 ToggleShouldSave。
- 原版状态为 true：在原有 owner、暂停地图、进程身份、源码清单及新鲜签名校验后，单次调用官方 ToggleShouldSave，并重新读取实际状态。只有实际 false 才返回 `autosave_disabled`。
- 控件隐藏、不可用、状态未知或签名之后状态变化：不调用切换。Ironman 的原版保存规则不在该动作范围。
- 调用或后读结果未知：独立 lifetime claim 保留，不重发切换。新鲜 query、revision 或 reconnect 不清除 claim。原有三个退出阶段的 claim 保持独立。

动作不确认退出，不调用 OnDesktop。后续退出前须重新 query 并使用新签名。`autosave_verified` 仍为 false：关闭复选框的读回不证明存档完整性或进程正常退出。

## 精确原版绑定

[源码合同](../../ck3_autonomous_player/native_bridge/research/fixtures/normal_exit_autosave_12004_source_contract.json) 绑定 EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518` 和原版 `gui/window_resign_confirmation.gui`。沿已有 .4 ingame idler/cast/handler 链定位 `handler+0x1F8` 的 `CResignConfirmationWindow`，核主 vtable、GUI root 与 handler 回指，再观察固定 `save_checkbox` 的实际可见状态。

原版注册关系为 `ShouldSave → 0x12F78D0 → 0x12F70E0`、`ToggleShouldSave → 0x12F7910 → 0x12F76B0`、`IsShowSave → 0x12F7970 → 0x12F7100`。getter 分别读取 window `+0xC8`、`+0xC9`，官方 Toggle 同时修改原版偏好。provider 校验 getter/toggle 指令前缀；上下文签名加入对象身份、当前保存状态、控件状态和独立 consumed claim。它复用完整原版 GUI 源码清单验证，不提供泛化 widget 点击。

既有 .3 退出支持保留；新增自动保存动作仅有精确 .4 绑定。未启用既有 normal-exit private feature 时仍不可用。

## 验证与交付范围

新增 native 离线夹具覆盖 true→false、已经 false 的幂等读回、未知/隐藏/禁用/签名后状态变化、切换失败及后读失败的 claim 保留，并实际调用 production parser/serializer。Python 定向回归覆盖已有退出流程、新动作前置校验、未知动作不重发、失败资格不升级和两套官方 MCP SDK 的闭合 action schema。

本机外置构建和实际资格回执统一放在 `C:/workspace/ck3-common-runtime/normal-exit-autosave-20261015-001/`，旧 `C:/csr12`、`C:/cbr3`、runtime001…004 和前两场失败证据保留原字节。后继 DLL 必须递归复用原宗教对象链，并按真实 header 依赖重编本次影响的 TU。离线构建、离线夹具、Defender 登记结果和将来的实机结果分别记录；离线通过不宣称真实回调、退出 OS0 或产品业务已验收。
