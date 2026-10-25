# House → Dynasty 原版链接修复（2026-10-25）

2026-10-25T02:55:27Z实际补记（`machine_id: desktop-3fevhd2-1c74096080`）：R0013使用18de31e4源码后，创建+1及+2日各61名实际原生信徒的独立保存均为Rite150→House12760→Dyn12156，且Dyn12156反向绑定Rite150；未改信后代65825保持Rite6／House174／Dyn174。两日名单与保存逐人核对，没有等待周期修复补过失败成员。该结果覆盖这两个实际观察日期，不外推所有内部callback瞬间；完整核心仍未通过。详见[R0013](acceptance/R0013-2026-10-25.json)。以下为R7及原修复时的历史记录。

观察机器：`machine_id: desktop-3fevhd2-1c74096080`。取证时间：2026-10-25 00:54 北京时间（2026-10-24 16:54 UTC）。实际 CK3 为 1.20.0.4，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本记录只说明 R7 真实失败与最小源码修复，新场引擎语义验收待执行。

R7 原件为 `C:/ck3-dynastic-esotericism-20261024/common-runtime-a07/runs/desktop-3fevhd2-1c74096080--dynastic-esotericism--R0007`，角色 31254、PID 18964。创建已独立观察到 Rite 150/Faith 13。随后 `des_acceptance_capture_created_decision` 的唯一 confirm 在 `2026-10-24T16:42:31Z` 被 native 以 `fixed_visible_confirm_receiver_unqualified` 拒绝：`receiver_qualified=false`、`dispatch_invoked=false`、`native_call_completed=false`。SDK 将这次原生提交前拒绝报成 `malformed generic decision dispatch acknowledgement`；原 claim 仍为 `claimed_result_unknown_no_retry`，后续 Save 没有执行。没有重放，也不授予 R7 业务或正常闭场成功。

同一运行的 `attempt-a10/state/profile/logs/error.log:340636` 起有原始调用栈：

```text
Event target link 'dynasty' did not get a matching scope type. Expected 'character', but got 'dynasty_house'
common/scripted_triggers/des_dynastic_triggers.txt:6 (des_has_binding_trigger)
common/scripted_triggers/des_dynastic_triggers.txt:11 (des_has_active_binding_trigger)
common/decisions/des_acceptance_decisions.txt:13 (des_acceptance_capture_created_decision:is_valid)
```

House 的原版链接是 `house_dynasty`。本机原版 `game/common/scripted_triggers/10_tgp_house_relation_triggers.txt:39` 使用 `house_dynasty = scope:house_2_temp.house_dynasty`（文件 SHA-256 `fece4a169f347f37eb29256a52a586a2ec0e735bae09a3717912bf33fc2efde4`）；`game/common/script_values/tgp_values.txt:566-567` 同样使用该链接（SHA-256 `a6ae6df5afe8c18831cf0fca33b0e191b7371751738d257d64d5c8d38f72f9de`）。

修复仅把产品 `des_dynastic_triggers.txt:6` 与 `des_binding_effects.txt:64-67` 的四处 `var:des_join_house.dynasty` 改为 `var:des_join_house.house_dynasty`。仍要求真实 House、真实 Dynasty、Rite ↔ Dynasty 双向绑定和同一 Rite；Character 的 `dynasty` 语义保持原样。fixture 的作用域及 House 判定由独立修复包处理。此次没有修改 SDK、native 或冻结的 R7 图。

原版 `window_decisions_detail.gui:215` 把确认按钮 enabled 绑定到 `DecisionDetailView.CanConfirm`；native 的 `ConfirmReceiver` 跳过不可见或禁用按钮。上述 `is_valid` 错误提供了真实产品拒绝原因，但失败时按钮树没有落盘，不能声称已直接观察到具体 receiver 子条件。成功的原输入决议在同一 R7、同一 DLL 上也曾返回 `named_parameter_count=1`，随后正常确认并关闭；它发生于打开信仰窗口之前。因此非空参数数量不能解释这次差异，关闭信仰窗口不能修复已证实的产品脚本错误。

完整 Java `clean verify` 和 producer → manifest → ZIP 闭环应确认新源码确实进入新图；这些构建检查不代替引擎验收，不增设镜像字符串断言冒充语义测试。新 R8 应重新创建并保存，核 Rite/House/Dynasty 实际身份、双向变量、原生合法确认及实际后态；错误 House 所属 Dynasty 仍须拒绝。R7 旧图与失败原件保持不变。

精确原件 pin、wire 行号/行 SHA、原 claim、原错误栈、改前源和改后 diff 位于 `C:/ck3-dynastic-esotericism-20261024/R7-capture-confirm-diagnosis-a01/`，入口为 `FINAL.actual.json`。这些小型证据只证明本次诊断与源码修复；不外推完整矩阵通过或发布资格。
