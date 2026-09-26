# R067：同帧交互查询闭环与三支军队共同接战

本页记录 CK3 `1.19.0.6` 的独立实机复验。它从 [064 的第 41 天交互阻断存档](war-contact-attempt-064-pending-history-2026-09-27.md)继续，验证生产规划器能消费一次原生类型化查询的**命令历史写回**，解除阻断并观察到三支目标军队进入同一战斗。它是本地 WarID `4` 的接触夹具；[战争请求 R0244](../autonomous-agent-progress/coordination/war-requests/README.md) 的原始 WarID `48`、ArmyID `16777237` 对 `16777417` 尚未由此验证，不得将请求标为 passed。

## 输入、会话与结果

- 独立原始目录：`D:/workspace/ck3_native_war_ai_promo_work/episode01-losing-side-contact-attempt-067/`。输入 `pending-blocker-immutable.ck3` SHA-256 `55FFD6033DC9910A0A1A32BDD05DAA904D10641AB2BF7D6F6ACF779D80A31ECF`；原生 EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。会话使用空 mod 列表和独立 `-userdir`，Steam 离线，正式 CK3 PID `19868`。Bridge hello 宣告 `game.command.query-pending-character-interaction-context-v1`；初始快照 SHA-256 `ADA8A04E11A81695D197D56A77E62AF288D1EB14B76FDA3EF450AAE107E8BA11`。
- `contact-summary.json` SHA-256 `51B73BB9B583683A958221139F96A0E0565F1D42FC5DC97E3E48D374A7502CFE`，`outcome=OBSERVED`、`status=three_cunits_common_combat`、`combat_id=2`、`army_ids=[18,32,33]`。逐日原始 `contact-observations.jsonl` SHA-256 `6AEE7BFBF96AD8B888FCE801C99C5D485AC189FF2A16282DBA0B528D63BAEA14`。这证明这一场本地复验中的同场接战，不证明胜负、撤退重入或其他存档的路线会相同。
- 外置只读逐项断言 `audit_067.py` 通过，独立 `evidence-audit.json` SHA-256 `8557E032511B18751904747A38B7B97389B75FC7706D7F781BC17996D336EDBB`，明确记录 `PASS_LOCAL_FIXTURE_ONLY` 和 `r0244_original_war48_verified=false`；审计脚本及输出留在同一外置目录，不把该状态扩写为 R0244 通过。
- 相对第 20 天的独立存档 `day20-after-blocker-immutable.ck3` SHA-256 `37381CD02CDDEAC1682EEC131933D303F83FD8F996AEB5C082860318637ED30C`，`date_raw=53145984`。三军共同接战时的 `common-combat-immutable.ck3` SHA-256 `26CD41E098F60EE3349BC9ABDC422066DCC7DB52EABAE341EEE49501522FEC6E`，`date_raw=53146128`。两个存档均在外置目录独立保留。

## 同一暂停帧的查询、历史与重规划

交互 instance `33554522` 在 `date_raw=53145504` 阻断推进。玩家 CharacterID `29829`、发送者 `32522`。查询前后快照均为 `snapshot_id=native:3`、公开 `revision=4`、原生 `native_revision=3`，且 `paused=true`。下表 SHA-256 对应原始 `ck3-output/interactive-requests-responses/` 文件的**整文件字节**，不是重排后的 JSON。

| 阶段 | 文件 | SHA-256 | 关键读回 |
| --- | --- | --- | --- |
| 前置规划 | `001-pending-plan-before.json` | `C15905048DDF50233E1E7AADE05CF94DB9C88AB64B057537BAE44B67620D4287` | phase `pending_war_interaction_query`，选 `query-pending-character-interaction-context-v1` |
| 查询前快照 | `001-pending-before-query.json` | `07A63E073EEA9784FBE015F442B9DF5D2AA8E14A8FD4BE264BE83480BC52EDE8` | 同帧，`native_command_history` 长度 `0` |
| 通过 `ck3_execute_step` 的查询 | `001-pending-recorded-query.json` | `ED42430A74C16FEDAD95F109B6445A57FF10394F208F7A9964F9D30AB5993A6C` | `accepted=true`、`status=available`、`snapshot_revision=3`；类型 `arrange_marriage_interaction`，instance 准确匹配，原生 reject `allowed=true` |
| 查询后快照 | `001-pending-after-query.json` | `2DF73F9E30EAA967C1A2D5F8186CF4FD8E99D6380D22AAAED6123AD824EA4C71` | 仍同帧；历史长度由 `0` 到 `1`，唯一新项是该 query，`ok=true` |
| 后置重规划 | `001-pending-plan-after.json` | `2165B0B3F63C1B0EA22559363682A0F1D45133BC2D25190AE8E7C5A6FBA4B310` | phase `pending_arrange_marriage_reject_only`，选 `reject-pending-character-interaction`，`pending_interaction_id=33554522` |
| 原生回复 | `001-pending-reject.json` | `362A401FE2944BFE5AA2DCD9EF0F1CAE1568F69FEA33CA3207BF744483186FB1` | `accepted=true`、`status=submitted`、`interaction_result.status=rejected` |
| 回复后快照 | `001-pending-after-reply.json` | `3D7033F4660535629C5DD153A389EEB8F49F7155E3BABC1BBAE8DCC99A2F56F0` | 同一 `date_raw=53145504`，变为 `native:4`/`revision=5`/`native_revision=4`，pending 消失，历史末项为已接受的 reject |

这条链路实机闭合了 064 留下的“查询已返回，但规划器命令历史没有查询”的缺口。此例的 reject 是规划器明确标为 `degraded_blocker_removal` 的允许动作：婚姻特殊载荷、交换条件及效果预览仍不透明，`semantic_decision_ready=false`，因此**不能**解读为原生 AI 婚姻答复偏好或完整语义最优决策。观察器仅在后置规划选中 reject、原生 legality 允许且同帧身份吻合时提交；本次只回复一次。

## 三军共同 CombatID 的原生双重读回

随后每天只推进一个原生游戏日。相对第 `26` 天 `date_raw=53146128` 的快照为 `native:84`、公开 `revision=85`、原生 `native_revision=84`；WarID `4` 仍活跃。`contact-observations.jsonl` 同帧列出玩家 ArmyID `18`、`32`、`33` 的 `combat_id=2`。下列三次只读 `query-battle-control-snapshot-v1` 再次分别绑定到同一帧：

| 玩家 CUnit | 原始回执 SHA-256 | 原生关键字段 |
| --- | --- | --- |
| `18` | `B84232ED68652B6CA2C7CBB6E0684AB4B73E6F2BA6CF6A12BC6C86CEDE2AEB33` | `selected_owner_character_id=29829`，`combat_id=2`，side `1`，ProvinceID `2633` |
| `32` | `B76241F0C1D022BB95B6E17CCB2F8D0496F1ED05F19A755D9F75A5AB58802C41` | 同上 |
| `33` | `BA6FB19F00A386A6C18F7A2E01C2FDF91FFCE1EBF07B9F0130BB1D3FE76A3813` | 同上 |

三份原生控制查询的 `queried_snapshot_id=native:84`、`queried_revision=85`、`queried_native_revision=84`、`snapshot_revision=84` 一致；同侧 `affected_public_cunit_ids_in_stored_order=[32,33,18]`。前一日已有 ArmyID `32`、`33` 与敌侧 ArmyID `16777218` 交战；第 26 天 ArmyID `18` 加入同一 CombatID。这里的 `18/32/33` 是玩家 CUnit/Army ID，不是兵种名或兵数。

## 环境与范围审计

`ck3-output/session-result.json` SHA-256 `DB2B20396DCCCEE19D568E004624DDC64B4CC94431A2F4901EDD6765810B855D`：`shutdown.cleanup_proven=true`、`shutdown.job_active_processes_final=0`，`tasklist+toolhelp32` 两路最终 CK3 清单为空。`ck3-output/capture-report.json` SHA-256 `C5A4F2EB1125F28E29ECD0B4E8EAD8B70D61176812B3754FB2212ED395E5F894`：`environment_session_complete=true`；独立 `cleanup-check.json` SHA-256 `3AD51D1E6F5CF05502F00E848AEF23BAB990B6CD63F6D4F0DAA26EFC35EFB995`：`cleanup_ok=true`。结束后进程清单无 `ck3.exe`，任务总线 `ck3-losing-side-contact-067-20260927` 为 `done/resources=[]`。

Steam 结束截图 `steam-postflight-moved.png` SHA-256 `AD57D778137C5138539B9D90CE457D0684218D34B549EEFA2FC8B5F0037523D5`，窗口底部可见“离线模式”；通过实时 Steam HWND 从 x=0 移至 x=30 并复位证明此次桌面像素更新。任务栏时钟画面仍旧，**没有**用其时间证明新鲜度。截图收据 `steam-postflight-receipt.json` SHA-256 `BCBF11AD8606D0C7139382298CC557CF60498053303D3843930B9542651D126D`，人工视觉复核附录 SHA-256 `5858A9F675A039C970283782DD89DEA190D1ECB783B93746363C9B76A6D78560`。

本次结果可用来继续验证本地三支军队在真实战斗中的增援、撤退与终局读写，但该存档仅冻结了**接战时刻**，不能把其后尚未运行的事件或胜率拟合写成已证实。R0244 消费方仍须在其原始 WarID `48` 存档复验其路线接触与策略动作。
