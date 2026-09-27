# 现役战斗续算：同帧原生观察回执 v1（2026-09-27）

## 交付与边界

CK3 `1.19.0.6` 的既有 `query-battle-control-snapshot-v1-N` 在 application-main 线程对同一个已暂停 `CombatID` 做双采样，并对外层世界快照做前后相等检查。现在同一 `command_result.result` 额外携带 `active_combat_resume_inputs_v1`。它由**同一个已经稳定的 `BattleControlSnapshot`**序列化，不发起第二次 v3 查询，也不修改 CK3 状态。既有 `battle_control_snapshot` 字段和 ABI 不变，旧 DLL 的客户端仍可继续读取旧字段。

新回执固定 `status=unavailable`、`input_observation_ready=false`、`unavailable_reason=same_frame_resume_operands_incomplete`。这是有意的：当前只能证明部分现役状态来自同一 application-main，不能把它转成 [`ActiveMainResumeState`](active-main-combat-resume-kernel-2026-09-27.md) 或宣布“继续打”的胜率。已有战前 v3 的首次接战操作数不参与这个回执，也不能由客户端拿来补空。

## 字段合同

`source` 精确回写父 `battle_control_snapshot` 的六个值：`snapshot_revision`、`observed_date_raw`、`subject_public_cunit_id`、`subject_native_carmy_id`、`combat_id`、`province_id`。父子任一值不等时，下游必须拒绝。外层 mailbox 仍执行 expected revision、暂停地图、可控 CUnit、双采样、世界前后核对及完成时再读快照；新回执在同一成功帧内才出现。已有失败路径保持错误帧，不输出伪造的 unavailable 观察。

`observed` 从同一原生战斗帧复制 `phase/phase_day`、撤退基线计算的 `elapsed_whole_days`、原始 `roll_cadence_counter`、`final_combat_width`、两侧当前 roll、当前选中将领（无将领为 `null`）、有序 public CUnit ID 列表和 levy/MAA entry 数量。详细 entry 的身份、当前 fighting/soft/hard 状态、当前有效 damage/toughness/pursuit/screen、side 总量及其核对仍在父 `battle_control_snapshot`。这里的 cadence 是**原始值**；回执不擅自归一化。硬伤不可得的非主战 entry 在父字段继续以 `unavailable` 呈现，不能被改写为零。

`missing_required_domains` 明列尚无完整同帧续算来源的玩家 coalition 映射、选中将领**下一次** roll bounds、现役反制 class/stack/context、下一日非 roll 优势来源，以及骑士参与和动态 entry 转换。后续即使补了其中一项，必须逐项验证来源与日界刷新，再在新版本合同中讨论 `available`；不能直接删掉数组条目提高状态。

## 聚焦验证与下一步

原生 mailbox 测试用完整 BattleControl 合成帧核对回执的六项身份、当前主战状态、`null` 将领、数组顺序、entry 计数、非空缺域与 unavailable 状态；无效 `CombatID` 的帧不能生成回执。原版战斗快照的旧序列化回归保持不变。完整 `xar_ck3_bridge` 构建验证 result frame 引用新序列化函数并成功链接。该测试仅证源码/ABI 及合成帧，不是 CK3 实机同帧验收。Steam 离线画面新鲜度门当前为 RED，本轮未启动 CK3。

下一步要从同一个 `ReadBattleControlSnapshotSample` 路径补原版现役反制、将领 roll bounds、非 roll 优势来源、骑士与未来参加者边界，并在完整真实暂停帧对拍日界结果；达到这些条件前，智能体只使用已验证的战前整场预测和战中撤退合法性/安全目标，不把本回执交给续算内核生产决策。
