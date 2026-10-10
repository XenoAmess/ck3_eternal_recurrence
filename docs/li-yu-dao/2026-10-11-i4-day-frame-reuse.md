# 2026-10-11 I4 每日推进后帧复用

在 R53 正常退出、原 host/keeper 等待完成及 CAS 释放后，采用公共 I4 adapter 的每日帧复用。原场仍为业务 RED，一期保持 **75% / NOT_GREEN**。本改动没有重跑 R53，也没有实际提速或自然到期通过的结论。

每日观察直接使用原始 `advance_day` row 的 `after_snapshot`，完整执行 `CaseClient.validate_frame`、暂停状态、事件、PID、连接世代、玩家及日期检查，并严格要求它与原 `result.after` 的正整数 `native_revision` 相同。显式模型查询的 public revision 取这份实际帧；观察前再次验证。首次观察保留原 `snapshot()`。三项原生查询、两次观察 plan、自然日完整性、事件拒绝、366 日上限、SAVE 及原 900/8400/7200 秒预算保持。

每日公共提交数预计从 4 降到 3。R53 原始第一日的[实际帧投影](acceptance/2026-10-11-i4-day-frame-reuse/one-day-selected-frame.actual.json)显示 `result.after` 和 host `after_snapshot` 的所选身份字段一致，public/native revision 均为 8；这是该样本的资格证据，后继每一天仍须独立检查，不能假定暂停时 native revision 总不变。

原先把三个观察合到一次 plan、让 host 自动补最后 revision 的方案被拒绝：Source11 在 `fresh_revision=False` 时不会补缺省 `expected_revision`。实际采用的改动继续显式传入两次模型查询的 revision。

Root 审阅后在外部 namespace 执行新 6 项与现有 20 项测试，实际 exit 0、26 项通过；[原始命令与日志索引](acceptance/2026-10-11-i4-day-frame-reuse/INDEX.actual.json)保留 exact bytes。采用后的 adapter SHA-256 为 `59d7c74e919898573d6f8270b6a61c16326e44787c6f6c193365c994fc9039f3`，与已测候选逐字节相同，新测试接入正式 CI。测试涵盖旧 public revision、失败/未完整推进、事件、缺失 post-step frame、native revision 漂移及实际帧身份守卫。

R53 第 28 天的 `pipe_completion_keyed_query_binding_changed` 是原生查询内部完成检查的拒绝。本改动不放宽 `available` 或 `frame_verified`，也不重放失败查询，不能据测试通过声称该拒绝已经修复。
