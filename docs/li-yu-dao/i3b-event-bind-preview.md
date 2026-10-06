# I3b 事件上下文绑定与决议预览

R14 HEAD19 的原始日志在构建决议 tooltip/description 时重复报告 `lyd_i3b_bind_event_effect` 对尚未设置的 serial、nonce、phase 的读取。第一段发生于选择 begin 决议详情后、实际 confirm 前；第二段发生于已取消章程、只保留 serial/nonce 的同类详情预览。日志的预览标记及未确认时的真实工具状态支持这一分类。真实 B1/B2 保存读回与预览错误分别记录；错误不自动推翻实执状态，也不替未完成的章程结果授信。

生成器在绑定 numeric saved scopes 前增加三个 `has_variable` 条件，仅在完整已有轮次上读取值。它不为预览创建假 serial/nonce/phase，不加零默认，不改变 begin 的初始化、授权、收费、名册、关闭逻辑或事件 ID。有效业务轮次三字段已存在，绑定值与旧版本相同；不完整状态不绑定 numeric scopes。

`tools/test_i3b_event_bind_present.py` 使用已保存 R14 B0、取消基线、两轮 B1 的精确字段子集，检查旧版本 undefined-read 负例、候选完整轮次数值、只移除新增守卫后整个 setup AST 与旧源相同，以及生成器生成的正式字节。模型只检查 authored effect 条件与取值，不能证明 CK3 renderer 的 effect-if 预览行为。

既有 `test_c3_i3b_preview_scope.py` 只评估 trigger 里的 optional-target 守卫；它不执行 setup effect，也不模拟 CK3 renderer。此修复不得声称沿用该历史通过结果已消除实际预览刷屏。候选本身尚未实机，须关闭旧会话、审核并合入、生成新生产包，下一次冷启动选择 begin 详情时保全 fresh 日志、真实未确认状态与之后 B1/B2。使用 has_variable 守卫在引擎中确实停止 unset 读取仍待该实证；失败则永久保留新 attempt，不热换当前加载源码。
