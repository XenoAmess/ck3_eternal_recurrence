# 通用产品验收的自然日与事件交接

R26 实际故障发生于 `machine_id: desktop-3fevhd2-1c74096080`，2026-10-23 18:24:30 UTC；2026-10-23 18:46 UTC 复核来源。该场保持 RED，不能把下面的离线回归计作实机通过。

通用适配器直接投递旧 `advance_day`，没有 `allow_event_boundary`，绕过了现有 `CaseClient.advance_day`。到达一天目标后，事件在暂停读回时出现；冻结 host 没有为该旧分支设置 `allowed_event_instance`。32 项诊断只有第 9 项“出现事件但没有获准实例”失败，其余 31 项未失败；没有证据将原因归为暂停预算耗尽或真实 owner 帧不完整。[实际诊断与原生 wire 摘录](../tools/testdata/generic_product_day_boundary/r26-pause-admission.actual.json)保留失败计划、原始条件、观测值、来源 SHA 和 wire 行号，没有伪造完整失败后帧。

普通推进改接已有公共 `advance_day(days=1, allow_event_boundary=True, allow_actor_change=配置值)`。它按实际能力选择原生 `life-advance-one-day` 或既有事件边界分支；保持一次投递、一天上限、完整暂停帧、相同进程/连接/角色与精确 build 守卫。未知结果不回退或重投。`actor_transition_days` 指定的序号继续保留旧 `wait_for_played_character_change` 参数；冻结 host 的旧 `advance` 读取此字段，而其事件边界分支不读取。此次只验证参数保存，没有新增角色切换实机资格。

事件与角色交互通知分别交给 Root 按原生上下文处理，适配器不猜选项。Root ACK 后重新读回，要求旧原生 `instance_id` 消失；同日出现不同实例时继续交接。每次交接使用独立递增序号，避免同一天多个窗口重复使用检查点。通知没有合法原生动作或后验不足时保留诊断，不把 ACK 当作已关闭。

正整数实例要求来自当前原生通道：`native_driver.py:21822` 的事件上下文查询要求 1..2³¹−1，原生 `ck3_12002_event_window_context.cpp:1033` 拒绝不大于零的实例；通知沿用 `PendingNotificationV1.parse` 的 minimum=1。通用观察层允许零，不等于当前原生交接动作支持零；本修复没有扩大其资格。

[回归测试](../tools/test_generic_product_day_boundary.py)运行实际公共客户端、投影器和通用适配器，替换传输及 Root IO；覆盖零小时边界、同日连续实例、通知分流、未消失窗口、错误 owner/build/日期/暂停、错误 ID 类型及未知结果。原生单日响应 envelope 与 wire 到公共帧的元数据投影明确是测试构造；R26 没有产生这样的成功响应。

冻结来源 SHA-256：

- adapter：`8327f1e295a050b62d542f37d27c0ff34c8376598bbb6c8ce95bc2a8b402e5d2`
- public client：`dfc100e133aa686ad64c906959de6e65052a8eb82e86889f48483a736af17b6d`
- host `registration_host.py`：`776fc23d6a0d7913df96e1799ae25b5021db99b76fb943802171bac6f85c808f`
- native-day projection：`c6b5e4fec8bdb9895a9e73506d56d748417af7c6403c07ed2863ab1d55d2ee54`

host/SDK/客户端与完整帧守卫均未因本修复放宽。新接线仍须另场实机确认。
