# Campaign root 查询拒绝后的快照同步

2026-10-12：源码实现，尚未编译或部署。当前运行仍为 Native85 / SDK86；本条不是实机验收。

普通冷恢复的继承人订婚结果查询先调用 campaign-root 原语。该原语的 preflight 要求请求 native revision 匹配、worker revision 非零、previous snapshot 存在、当前读取成功且完整 DTO 与 previous 相同。原实现发现完整 DTO 改变时返回 `state_changed`，早分派路径没有发布已读的新 DTO；SDK 的普通 snapshot API 只读取缓存，不能靠它补上这次同步。

此次改动保留全部五项谓词、短路读取顺序和原拒绝结果。仅在实际 1.20.0.4 campaign query 已成功读取、完整 DTO 改变时，暂存 owned observed snapshot；先发送原失败响应，再通过现有 snapshot publisher 发布这份 DTO。实际 WorkerAdapter 的读取是 observer cache 复制，owner 仍可复用同日期/暂停状态的 250ms 缓存；这里不强制 owning-thread 新采样，也不能将 published DTO 称为新的完整实机采样。publisher 不再次读取，保持正常去重、revision 更新及 checkpoint 处理；没有业务操作、重发或人为 revision bump。不可读、revision 错配及其他 query 不进入此同步分支。

失败响应增加至多 4 KiB 的 `campaign_root_preflight_failure_v1`：实际失败 stage、请求/worker revision、五项布尔谓词、read_attempted，以及现成 cached/observed scalar 摘要和不同字段名。超出预算时省略摘要，仍不能输出完整 snapshot。SDK 的 `ck3_auto_turn` 只对 type/protocol/request ID 精确匹配且 `ok=false` 的原生拒绝，投影实际发送 step/request ID/revision 和这个有限诊断；保留原错误文本及 construction 诊断优先分支。不同字段 CSV 和摘要整条保留或整条省略；SDK 发生任何裁切/省略都明确标记 `projection_truncated`，非法 thin 必需字段仅标记 `thin_schema_invalid`，不生成貌似合法的空谓词。诊断不消费 pending，不授予重试许可。

原始 R101 响应 `820-r0101-native85-ordinary-after-read-stop-chunk01-000005-normal.json` 仅有 `native gameplay step failed: state_changed`，没有原生 request 身份；不能追认为 campaign-root full-changed 已实证，也不能据此判定婚姻业务失败。其后 860 是新鲜 core frame，870 是 SDK 缓存 snapshot；两者都不能补证旧请求的五项 preflight 值。原 RED 保留，累计已保存普通日仍为 6082，M7 自然跨代次数仍为 0。

来源候选位于当前获准源工作包的 `sdk86-candidates/native-root-context-diagnostic01/` 与 `native-rejection-candidate01/`；原准入和复核期限不续。部署时须将共享 child DTO 的三项实际 production TU 一起重编，保留对象各自的真实 source pins；混合对象的全局 native source head 继续为 null。没有执行测试、fixture、FIRST 或功能复验。

## 2026-10-16：两种已发生的只读版本竞态

`machine_id=xenoamess-full-tower-eb9d2c1186`；下面是新证据，不追认上文历史运行。
罗贝尔长局 P14 AUTO20 在原生根查询读取前被拒绝：`preflight_revision_changed`，
request native370、worker371、`read_attempted=false`，五项谓词分别为 false/true/true/false/false。
P17 AUTO109 则发生于 Service 的 `query_campaign_root_context_v1`，公共 revision64/65
不符；源码确认该检查在 `execute_step` 之前，因此不存在这条失败查询的 native request ID。
两次原会话均通过外置精确只读恢复继续，没有重放原 AUTO。

公共 `readonly_planning_retry_v1` 现在把这两个具体类别接入已有一次 fresh planning 预算。
原生类别必须保留完整实际 request/result 身份与读取前诊断；Service 本地检查改用既有
`PreSubmissionRevisionMismatchError` 子类，只有精确 campaign-root 文本且 current > expected
才纳入此分支。任意裸 `BridgeUnavailableError` 同文案不会被接受。重新调用整个只读规划
流程取得新 snapshot，不重用旧 planning view，不重放 `auto_turn` 或动作执行；嵌套调用仍
共用一次预算。timeout、业务 step 和无法证明读取前拒绝的错误继续保留原失败。

9 项定向测试及 25 个子测试通过，包含实际 Service 本地检查未调用 execute，以及现有
规划 wrapper 的一次重规划。P14 原件诊断与 P17 原件文本分别适配通过；P14 测试使用由
实际诊断重建的 envelope，明确不是原始 native packet。公共修复尚未部署到活跃 P18 SDK。
这不授任何游戏日、动作、战争胜利或完整 30 年信用。

本机原件索引为 `continuation42-cold-prep/p14-responses/0020-1-result.json`、
`p17-responses/0109-1-result.json` 和
`ROOT-P14-P17-PUBLIC-READONLY-RETRY-VERIFICATION.json`；源摘要保存在最后一份小回执。
按通用存储策略于 2026-10-23 复核最小证据。本轮未改 Native DLL、运行 SDK 或 Game；
Python 预检/重规划逻辑不适用 `open_kaishek` 的游戏脚本语义预验。
