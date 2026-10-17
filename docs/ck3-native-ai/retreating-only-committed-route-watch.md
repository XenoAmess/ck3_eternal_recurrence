# 敌军全部撤退时的既有路线单日观察

`machine_id: xenoamess-full-tower-eb9d2c1186`。P39 的 AUTO55 在军队已有完整安全路线、全部已发布敌军都明确撤退时，仍因接敌 horizon 的敌军 scope 为空而返回 `native_war_active_route_contact_horizon_unsupported`。空 scope 不是现有 Native horizon API 的合法参数，不能为继续推进伪造一份 contact-free 证明。

普通规划器现仅在这个分支尝试既有 `life-advance-one-day`：地图暂停、无当前事件或交互、无已知独占弹窗；唯一受控本军属于当前活着的玩家、正在移动且不在战斗或撤退；完整非空路线与目标、现有 active move intent 相符，原被动路线审计为 safe；每场战争的已发布敌军都必须明确 `retreating is True`、`in_combat is False`，且至少实际观察到一支敌军。未知撤退状态、空敌军列表、unsafe 路线或缺少单日能力继续拒绝。

该计划只观察已经提交的路线，不重发军令；`contact_free_proven`、`movement_resubmitted`、`offensive_combat_permission`、`war_or_material_credit` 都为 false。下一日仍需重读军队、战斗与敌军。既有主动攻击强度准入不因本分支改变。

公共实现只修改 `_choose_one_life_turn_core` 的这个空 scope 分支，新增纯资格函数；其余旧函数 AST 逐一相同，新函数 AST 与已审 SDK 候选一致。便携夹具保留真实 SEM56、CAP2、AUTO55 plan 和 17 条已完成 AUTO 的 command-row 投影，不宣称这是完整 Driver 历史。普通 chooser 的旧行为通过禁用新增 helper 作对照；21 个变形否例明确属于离线测试。连同相邻“敌军已在其他战斗”回归，本地 4 项、35 个子例通过，CI 复用既有战争策略检查入口，没有新 Native 构建或现场调用。

## 已发生的实机边界

[小型原件投影与精确来源](research/p41-retreating-only-committed-route/P41-ACTUAL-QUALIFICATION.json)保存 P41 AUTO13／MET14：正确的新 phase，raw `53201808→53201832`、单日、Native clock generation1、完成一 tick、deadline 截停、overshoot0、独立暂停读回；planning public2／Native19 与后态 public5／Native22 分别保留。这个既有单日时钟实际采用 speed5，不是实验性的 route-horizon speed5，也不产生 contact-free、战果或资源信用。

原 P39 故障及零动作清理保留。P40 首启另因 audience 指针已经存在，Windows `pending.rename` 在发请求前失败；[该次失败投影](research/p41-retreating-only-committed-route/P40-AUDIENCE-COLLISION-PROJECTION.json)明确保留 queue1／app0、非正常闭场、零新 RPC，不能改写成两端正常退出或游戏动作失败。公共 audience 绑定 API 已采用显式受管写者及 replace 边界，不复制场次 queue 脚本作为通用实现。

P41 在同 Game51028、同录像下接入，原单日结果配对结算后，Root 的 `d0ef55eb…` 续接证明为 window7 建立新基线 `53201832`。Root 本次交接截点回报该窗口已连续约44日；战争33554541仍在进行，尚未胜利。旧窗口失败与这一天启动资格不累加为连续稳定成绩。连续稳定30年第一，之后低于1秒／日、再0.5秒／日，均未宣称达成。

2026-10-17 后补：上段是最初44日的历史截点。窗口7后来在786日因 AUTO1731 的玩家决策暂停边界校验失败，SEM1732实际观察到6日变化与待处理交互；原结果不重放。新的[自行暂停读回窄修复](natural-player-decision-pause-boundary.md)与部分推进恢复分开记录，不把该窗口写成仍持续运行。
