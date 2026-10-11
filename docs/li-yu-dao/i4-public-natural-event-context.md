# I4 自然事件上下文观测

2026-10-11：`i4-natural-event-context` 已接入公共入口；新增 4 项纯模拟测试于 02:11:29 UTC 返回 0。实际 prepare、准入、启动、事件观测和正常闭场尚未执行，业务信用为零。R56 原 strict case 的事件拒绝及 RED 保留。

本 case 沿原0240真实无HoF输入，复用原产品/profile、原 metadata、初始决议 disabled 和 fresh initial SAVE 的冷却存在/Faith/Rite/headless 校验。自然推进最多90实际日，预算仍为 readiness900、hold7200、total8400秒，不续期、不重试。首次活动事件时保留完整暂停身份帧，取得 fresh 帧后只调用现有 typed event context 查询，保存真实 instance、definition、root、options、原始结果与精确引用，然后正常返回 shared GUI Quit。事件选择和学派选择均为0。

被事件打断的区间只计真实自然小时，不冒充完整24小时日；90日未遇事件明确为 `NO_EVENT_OBSERVED`。typed 效果指标不完整，本 case 不选择选项、不证明到期、fresh365、cold reload、I3b、C3或完整I4。未知事件的后续政策须依实际 definition 源码另行制定。共享正常关闭仍须独立取得真实证据。

源码入口：[adapter](../../tools/ck3_mod_acceptance_cases/lyd_i4_natural_event_context_adapter.py)、[case合同](../../tools/ck3_mod_acceptance_cases/lyd_i4_natural_event_context.json)、[新增测试](../../tools/test_lyd_i4_natural_event_context.py)。旧 strict case 未改变。

prepare 继承接点仅做源码核实：新 adapter 先校验新case/config，再只为原prepare投影旧case/config。产品profile helper不消费case/config ID；公共 `Selection.prepare` 仍以新case ID及新adapter/config pins生成prepared-case。旧natural adapter及其sidecar为明确依赖，未发现此接点的实际阻断；这不等于prepare已运行。

4项测试只覆盖：首个真实格式typed边界和零选择、完整日守卫及错误时长拒绝、90日无事件、跨owner查询拒绝且不重发。原始小回执见[索引](acceptance/2026-10-11-i4-natural-event-context-static/INDEX.actual.json)，fixture通过不得写成实机事件或正式I4通过。
