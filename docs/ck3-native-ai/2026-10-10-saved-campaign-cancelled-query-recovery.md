# Saved-campaign启动查询的有限恢复

R0050公共I4实机在启动恢复阶段失败：`ck3_query_campaign_root_context_v1`的native回执为
`timeout_cancelled_before_execution`，executor及最终结果未产生。原host的观察记录在query之后
才追加，因此失败的实际提交帧未保全；最后一条pump2不能代替提交帧。
[原始RED及实际闭场](../li-yu-dao/acceptance/2026-10-10-i4-natural-startup-r50/REPORT.md)
保持不变，尚未执行I4业务动作。

本次只修改共享host的`wait_for_saved_campaign`及一个新专项测试文件。每次root查询前先写入
实际提交帧、revision和attempt状态，异常时保留原错误。仅完整、精确的campaign/wait回执
证明查询已在执行器进入前取消时，允许一次恢复：重新取得两个稳定的暂停owner帧，pump必须
大于失败提交帧，PID、连接代次、角色、日期、local player及owner一致，再发一次只读查询。
执行已开始、回执不完整或未知、第二次失败仍直接终止。返回值仍须通过原完整root来源、
当前角色/日期/revision及启动事件合同，不给予产品验收信用。

root和snapshot等待均受原readiness deadline约束，成功返回前也检查原截止；不增加等待预算。
这修复了host的失败取证和有限恢复缺口，应用主线程为什么未进入执行器仍UNKNOWN。
Source09/O9及历史attempt不改写；后继真实启动需要使用包含此修正的新冻结运行时，源码
检查不能替代新的冷启动或I4初始/最终SAVE及自然日期推进。

新增8项专项检查调用实际host等待函数及原frame/root validator，只替换异步MCP I/O。
覆盖完整取消回执恢复、旧pump/原deadline、未知或已执行回执、第二次取消、身份改变、
错误root、in-flight截止与首次查询成功。`open_kaishek`预验为not-applicable：这是通用host的
异步取消与时限语义，不执行或模拟CK3脚本业务。

实际两路径采用命令退出0，保留MAIN host原UTF-8无BOM及LF换行；随后对采用后的MAIN执行唯一一次
专项命令，退出0，`Ran 8 tests in 0.564s / OK`。[原始采用、测试及精确来源索引](acceptance/2026-10-10-saved-campaign-cancelled-query-recovery/INDEX.json)
同时保留首次外置AST准备因BOM失败的事实及修正来源，不把候选AST通过冒充测试通过。

当前仅STATIC_READY，不授新的实机通过。正式B4/B5/C3/I4仍未完成，一期仍75%工作量估计 /
NOT_GREEN。本次没有native编译、游戏启动或重型写入预约；旧缓存、存档及原失败证据保持
既有有限期限。

14:20 UTC的[单次精确CI观察](acceptance/2026-10-10-saved-campaign-cancelled-query-recovery/ci-1420/REPORT.actual.json)
记录：失败证据提交`7a735081f`的Official/Linear均success；修复提交`3f8cae002`的Linear
success、Official仍in_progress。两者LYD均未触发，不能算LYD验收通过，也不外推其他HEAD。

14:23 UTC勘误：上述ci-1420两份原件首次提交被Git规范化CRLF，ROOT未处理add警告就继续
提交。现已从同一原件恢复并补该目录`* -text`，显式renormalize后逐份比较staged blob，均与
原size/SHA相等。[原错误与修正回执](acceptance/2026-10-10-saved-campaign-cancelled-query-recovery/ci-1420/BYTE-CORRECTION.actual.json)
保留先前发布commit及两组字节摘要；CI观察、源码和测试结果未变。

14:30 UTC：[Source10后继候选及ROOT审阅](acceptance/2026-10-10-saved-campaign-cancelled-query-recovery/successor-source-only/ROOT-REVIEW.actual.json)
已保全。producer固定Source09父树及已发布3f8两条Python投影，继承O9四项GUI的build-ready /
live-false声明；compiled native与MCP注册源码保持原冻结。预计源码逻辑141,079,473 B，写入
上界192MiB，须在下一独立4GiB预约中显式计入。此时尚未创建Source10/O10或tag，未运行producer。
host签名及source_core改变使旧v2seed不匹配；不绕过key或从R0050失败追认normal-close seed。

14:48 UTC追加：[Source10实际冻结和新CASE2公共准备](acceptance/2026-10-10-saved-campaign-cancelled-query-recovery/successor-source10-actual/INDEX.actual.json)命令均退出0，Source10 archive commit为`b9d179bc74b69e7fc92cd82499622d224a1ab93e`。只投影已发布的host/test两路径，7905项继承复制，无native构建或硬链接。独立预约002包含192MiB源码上界；此时预约仍OPEN，prepare/plan/preflight不代替实机启动或业务通过。旧CASE1已经消费，不再分配；原输入与71文件production相同，新CASE2单独保存状态。
