# P55：未获接战授权时继续路段评审与被动守备

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-18；精确 UTC、源码及不可变输入 SHA 见[资格记录](evidence/p55-siege-route-public-2026-10-18.json)。本次公共基线 `cf75d38a5055e2dc0f1fb40a7159c041dd61e525`，仅离线源码与组件验证；不修改当前 R3、Native25、SDK48、冻结包或录制现场。

## 实际问题与改动

R2 AUTO265（源 UTC 2026-10-17T21:07:08Z–21:07:53Z，native10292/public83/raw53358576）原普通方案为追击 `167772577 → 2619`。旧围城研究入口用双敌 V2 的 `research_only` 结果替换了它，导致已有 general ingress 的安全首路点评审没有运行。实际完整路线为 `8755 → 2622 → 2623 → 2619`；到 2622 要四天，H1 只证明当时一天的路线接触情况，不能证明四天安全。

新共享消费者把这类原追击方案交回现有 general ingress，仅允许已有的路线查询、完整敌军 H1 查询、首路点预览、首路点 H1 与首路点移动阶段。实际 AUTO259/261 的同帧结果及 Native 原有动态 action-step 派生函数回放后，下一步是 `preview-move-army-167772577-to-2622`。后续预览和 H1 仍须实际获得，不能直接返回原 2619 行军。最终敌人接触仍走原有预测及接战门禁。

原普通规划器若已经选中合法驻守目标，则复用 Driver 的 `_battle_sentinel_stationary_objective_hold_state`，保持原本最多七天的 typed hold。它不是“无接战”保证：敌方可以主动发起战斗，Native 在 daily tick 后发现 combat transition 并暂停；第一天可能已发生战斗与伤亡。完整己方驻军、目标、战争、围城、强攻及窗口检查在执行前仍会重复，停下后重读战争与目标状态。战争分数和占领不是该 Native 哨兵的逐日触发项，仍可能有最多七天的观察延迟。

公共基线没有 SDK48 后来的额外 CArmy 后置守卫。本次新增的移动与七天驻守出口因此局部要求同帧 `ordinary_core_v1`、唯一玩家行、有效真实 Native CArmy；缺失、陈旧或重复时选择已有 army-strength query。该局部资格不等于补齐整个公共规划器的 SDK48 守卫。原 H3937、Service typed-step 准入及 Native 执行检查继续运行。

## 多战争兵力与实际展示缺口

实际 R2 AUTO257 的小型兵力回执已记录：己军 1357；2619 两敌为 438+117=555；另一场己方主导战争 `134217796` 的敌军 `285213101` 为 4228/max4242。R3 AUTO17/19/29/33 的 `primary_war_hostile_union_v1` 已去重为三敌 4783、己军 1357，并标明 shared-force deficit；不存在将全部敌军错算成 555 的统计缺口。

当前 R3 私有展示只挑选最高现金风险的保地战，因此 reason 显示了 1357/555，遗漏了全场范围。公共 mercenary consumer 的新版 reason 分别展示优先保地战兵力与全部己方主导战争敌军去重合计，并明确未来增援、抵达和胜率未知。具体战争查询与行军优先；上述真实回合的 `quiet=False`，尚未进入市场查询条件，不是采购模型因 1357>555 而忽略第二场战争。旧 AUTO400 的 172 金报价不作为当前报价。

## 验证与边界

- 公共 war/finance/profile/P52/P55：43 tests、35 subtests 通过；包含实际原 siege ingress、原 general 路点评审、全 choose 后处理、Service selected-step 准入及全三敌范围；不是仅测试一个无人调用 helper。
- 原 Native stationary-objective-hold 回归：3 tests、8 subtests 通过。新增 FakeEndpoint 生产链证明原七天驻守在敌方引发 combat transition 后一天停止，且 post-stop `invalidated` 保留真实含义；无 move、无新增攻击授权。
- 实际 AUTO265/SEM266 前缀、AUTO257/259/261 小回执与 R3 AUTO29 摘入可移植 fixture。SEM266 后续大型 cache 没有被读入，缺失字段不当作观测为空。compact strength 的角色与战争成员关系显式从同帧 SEM 连接；测试相对 history index、重建的旧 pursuit 字典及未来首路点回复均明确标注。
- `git diff --check` 通过。首次新增 Native fixture 错把 sentinel 的冻结 combat watch count 当作结束时战斗数量，严格原校验如实拒绝；仅修正测试夹具，未放宽生产校验。

不宣称已经解围、已经胜利、四天无接敌、battle model 已校准，亦不增加 M6/M7 验收分数。多军 V2 模型与实际战斗校准继续独立进行，不能由本次非攻击续行外推完成。
