# C3 AUTO147 Native 截止证明的分类

machine_id: `xenoamess-full-tower-eb9d2c1186`。2026-10-19 的实际来源为原 AUTO147、冻结 src03（`063531c4b2bc64f52b80a78b8a2b8e9f55112964`）、score15 的 Native 源审及本页资格。Game PID214568/birth134368503807325674；其他机器不能沿用此现场资格。

AUTO147 实际将 raw53145048 推进至53145240，共8日。Native Arm/Status 同 generation6、target、speed5、零军队/战斗，Status 证明8 ticks、零 overshoot、唯一 date_deadline、pause wrapper 与 paused，最终返回 paused map_hud。其间冗余 `pause-map` 返回 `accepted:false/status:rejected/error:CK3 map state is unavailable`。旧 classifier 要求每个 action accepted，因该拒绝阻止日期观察结算。

[纯邻接叶](../../tools/g2_saved_campaign/campaign_deadline_clock_credit_v1.py)保留旧 clock 的 outer/source/date 要求，使用冻结 SDK 的 `_validate_tactical_daily_sentinel_arm` 与 `_validate_tactical_daily_sentinel_stop`，额外要求精确 target、flags1/唯一 date_deadline、零 overshoot、同 generation、实际暂停 map、固定 C3 owner/connection、完整 campaign deadline 以及 action 与 summary 深等。仅四动作 Arm/resume/该唯一冗余 pause/Status 顺序可进入拒绝诊断分支；任何关键动作未知或失败、异样拒绝及多动作均拒绝。

原 action 不删改，失败 pause 原样进入 `rejected_redundant_pause_action`，`rejected_pause_command_succeeded:false`。授予8日日期观察，`primitive_accepted:false/business_success_inferred:false/replay_allowed:false`，仍要求原 paired MET。不能把 Native 自动暂停说成该 pause 命令成功，不能重发147。

[producer](../../tools/g2_saved_campaign/prepare_campaign_deadline_clock_classifier_v1.py)保留所有旧 classifier AST，仅改旧 clock 函数名并追加分流；tokenize 只删除真正的整行注释以满足既有256KiB上限。无 Native clock 时直接走旧函数；全部 accepted 的 clock 也走完整旧路径。邻接叶精确 SHA 写入 classifier，旧 route/battle 邻接依赖保持原路径。

[147软件资格](evidence/c3-native-deadline147-classifier-qualification01.json)复现旧拒绝，完整 dispatcher 消费实际147，不改原回执，通过12个必要负例及原117/130回归。Crown130回归 fixture 来自保留 response 的 pending 字段，不冒称旧 mutable sidecar 仍存在。[实际正常正例资格](evidence/c3-native-deadline147-actual-accepted-regression01.json)进一步用原122的8日和126的4日月界响应，确认 allaccepted 的完整旧新 dispatcher 结果逐项相同，0新 RPC。

早期 review03 只覆盖147的拒绝诊断分支，遗漏原正常 allaccepted 的兼容分流。runtime 已在收到更正前采用它，以148安装、149原件重消费成功（0新 MCP/Native，原动作不重放），随后150仅结算原147；58完整周期、实际38日。后继使用 review05/v2 邻接名保留已采用 v1 原件，正常 allaccepted 回归通过后再放行新 AUTO。review05 的最终 candidate 为260311B、SHA256 `d47350282ad422978bac99653aa5757a5d72d6af10fb690e615592a3ff825991`；邻接 `root_campaign_deadline_clock_credit_v2.py` 为9160B、SHA256 `102a2b94f742e14c9f9fb3fbbad14b3c21cf2e1a9ac7626e8ddce5d82fcbc883`。本页不把待采用 v2 的软件资格写成实际采用。

src03 Native driver SHA256 为 `27cad6e04f885d98cd438535dcae905831b619deb5c1232a2f5d7ea0bcc966de`，Arm 定义29149–29203，Stop29206–29266。score15 已独立核验原147与调用顺序，公共 producer 的后继修复独立合批，不热换本次冻结 SDK。

这是实际日期与暂停证明的合同修复，不证明达到1秒/游戏日。所有维护、分类恢复与门禁墙钟仍归实际运行总耗时，不能拿8日动作耗时单独替代整场日吞吐。review/source 及原147是当前恢复输入，维护验收后7日复核保留理由并按统一存储策略回收过期派生副本。
