# SDK35 静止军队停钟消费与修复状态

机器：`xenoamess-full-tower-eb9d2c1186`。这是有限源码／小回执归档，
不是30年完成报告。[精确来源](SOURCE-PINS.json)保留原字节 SHA、公开源码规范换行 SHA、
原失败及后续纠正；视频、截图正文、Driver、SAVE和完整场次分类器不入此包。

## 静止军队的一日结果

Native22 实际 AUTO22 在2604返回可用零跳 horizon、完整敌军时间线和精确停钟：
raw53483040→53483064、tick1、overshoot0、paused。
旧55b消费者只认 moving phase，FULL21因而误拒，原失败没有被改写或删除。
Root同SDK安装25、重消费26，FULL27／MET28只结算原一天一次，未重发时钟。
随后普通FULL37／AUTO38又实际推进到53483088，SEM40／MET41匹配Native7／public8、
12457周期。[实际安装代际](stationary/ROOT-P35-CLASSIFIER-EPOCH02-PIN.json)
与[正式原队列回放](stationary/ACTUAL22-QUEUE-TESTS.json)分开保留。

公共[结果消费者](../../../../tools/g2_saved_campaign/route_contact_exact_day_outcome.py)
新增精确 `native_war_stationary_contact_horizon_progress` 分支，要求同帧我军 regular／sieging、
无移动目标／路线、非战斗／非撤退；原生 complete empty timeline 必须经正式 SDK normalizer。
完整 hostile scope、Native revision、四个原动作、精确一日和独立配对 METRICS要求不变。
既有moving／合法弹窗结果的信用不变，只授日期观察，不授UI／军事业务或战果信用。
空Python路线本身不构成零跳证明。

便携测试用完成原22的精简完整消费输入、原1／19的必要生产租约，直接调用公共
`_fresh_route_contact_advance_proofs`；公共与Native序号不同，三种错误租约拒绝。
另保25否例、四种明确stationary姿态及原AUTO50 moving popup回归，共50项通过。
它们没有扮演公共queue；原正式 AST loader／reconsume／full_loop／persist回放单独归档。
未来不可避免接敌的speed1消费者是独立候选，本包不从stationary实机结果外推其资格。

## 停止原因与恢复状态

用户要求：错误导致停止时显示简短原因和“正在修复中”；实际恢复后显示修复说明和
“已恢复推进”。Root亲自审阅两态Desktop1画面，消息到期后恢复正常实际决策；
原overlay／Game／OBS未重启，状态工具不提交游戏动作或增加业务信用。
[实际像素审阅](repair/ROOT-REPAIR-STATUS-PIXEL-VERIFIED01.json)绑定原install25、
实际FULL37和freshSEM40。此实证针对冻结v1 relay，不能证明所有异常来源均已实机触发。

公共入口是参数化的
[runtime_repair_status_v2_all_stops](../../../../tools/g2_saved_campaign/runtime_repair_status_v2_all_stops.py)。
它复用v1状态合同、按NEXT数值序号增量读取，不反复glob整个响应目录；
同一父FULL迟到、跨9999序号也能观察。只读取实际两SDK PID／出生／EXE元数据并持有
只读进程句柄，观察退出而不枚举或重启进程。录制等待只有配对实际停止证据才显示
游戏推进暂停；队列异常在pending已清后、feeder typed blocked等来源有离线用例。
公共版本改成仓库正常相对import，并复用现有share-delete有界读取；未修改冻结0b88／d6f7／ef39。

该工具消费现有saved-campaign目录合同：Game launch、recording request／job、
指定SDK prefix的requests／responses／queue、NEXT、精确SDK pair及feeder状态。
路径与SDK prefix由调用方提供，不固定盘符、场次UUID或PID。示例：

```text
python -B -m tools.g2_saved_campaign.runtime_repair_status_v2_all_stops --session <session-root> --sdk-prefix <p-number> watch
```

该命令不由本次提交自动启动。单一watch由既有writer lock约束；
`repairing --halt ... --reason ...`记录实际停止，`applied --evidence ... --message ...`记录修复回执。
只有修复之后成功FULL确有新日期推进，加fresh同Game／actor／episode暂停SEM，才能发布恢复。
原失败动作已经推进的日期在重消费时不算新恢复证据。恢复横幅30秒使用单调TTL，
随后重显原实际决策投影，不重放动作。

[专用schema renderer](../../../../tools/g2_saved_campaign/runtime_repair_overlay_view.py)
是供未来overlay接入的纯API，当前实机仍使用已验收legacy relay。
v2增加的SDK／feeder／summary异常覆盖及专用renderer只有离线测试，
不宣称全部公共host已接入或全部未来错误已覆盖。
状态及共享读取定向命令25项／8子例通过，零Game／OBS／桌面调用。

## CI 与当前边界

第九公开 `4f71b101` 的
[Official38997913853](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38997913853)
与Linear38997913841均实际success；原终态回执附在本目录。
本包截点新窗口31尚未准入，Root继续独占现场操作；
旧窗口27／28／29／30的1824／31／3／58日失败记录保持，不能累加成达标。
目标仍是连续30年稳定第一，再低于1秒／游戏日，最后0.5秒／日，均未完成。
WAL、路线速度5和异步全片hash关闭验收不能由本包推定已实机通过。
