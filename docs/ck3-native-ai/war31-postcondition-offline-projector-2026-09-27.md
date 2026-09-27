# WAR31 离线战后观测投影与证据边界（2026-09-27）

本投影只读已有原生 rich snapshot 和 `surrender-war-16777231` 的 typed 返回，不启动 CK3，也不提交战争动作。入口为 `ck3_autonomous_player/tools/project_war31_postcondition.py`，核心纯函数在同目录 `war31_postcondition_contract.py`。它绑定 WarID **16777231**、目标 title **2128**、玩家角色 **29829**、对手角色 **30097**，拒绝不同角色、重复 WarID、错位 episode 和 action 结果。

## 输入与计算

对战前、动作后各提供一次完整 `ck3_take_snapshot` 的 JSON 对象：

```text
<verified-python> ck3_autonomous_player/tools/project_war31_postcondition.py --before <before.json> --after <after.json> --action-result <typed-action-result.json> --output <new-report.json>
```

`--next-turn <snapshot.json>` 可追加后续日期的新原生快照；`--recovery <snapshot.json> --recovery-source-save <post-action-save.ck3> --recovery-restored-save <restored-save.ck3>` 可追加独立重载回读。命令逐字节计算所有 JSON 输入的 SHA-256；恢复配对的两个存档由命令直接流式计算 SHA-256，不信任手写哈希。输出用独占新建，拒绝覆盖旧报告。

| 域 | 现有原生证据 | 投影原则 |
| --- | --- | --- |
| 战争仍在 | `active_wars` 中精确 WarID，连同防守方、主战方及对手身份 | 完整列表中缺 WarID 才是 `false`；列表缺失/损坏为 `unavailable`。 |
| 动作提交 | typed 返回 `step/accepted/status/war_termination_result`，绑定 episode、战前/后 snapshot ID 和日期；本战防守方投降的 outcome 为 `attacker_victory` | `submitted_pending` 与 `applied` 分开；ACK 不能代替战争消失的原生回读。 |
| 玩家金币、威望 | `played_character_gold/prestige.raw`，固定 `scale=100000` | 保留正负原始整数；两端均可见时才算 `after-before`，真实零与缺失严格分开。 |
| 下一回合 | 另一次同 episode、日期严格前进的原生快照 | 单独检查旧 WarID 是否仍缺席；战后即刻回读不能冒充下一回合。 |
| 恢复 | 两份实际存档同 SHA-256，恢复后原生快照 | 比较 episode、日期、旧 WarID 状态和已有玩家资源；不拿保存前的 action ACK 当恢复后证据。 |
| 头衔、封臣、停战、全部资源 | 现有 rich snapshot 无 title 2128 的精确 holder/liege/vassal 集合、持久 truce、piety、对手有符号资源 | 输出 `unavailable` 和原因；绝不把它们填为 0、空集合或“没有变更”。 |

报告 `gates` 对每项给独立布尔量；`material_outcome_complete` 只有全部独立门禁成立才会为真。目前后三个原生字段缺口会使它保持 `false`，这是刻意的，不表示动作失败或零损失。脚本不会把 R0221 的可投降只读判定、结算预览或 `war_termination_result.status=applied` 当作 title/资源/truce 的实测结论。

## 原生缺口与后续读数

现有 `native_driver.py` 的 rich snapshot 直接载有 `active_wars`、玩家金币和威望；`campaign_root_context` 的玩家持有头衔分区及直属有地封臣列表也不能单独证明 title **2128** 终局 holder、该 holder 的领主或它的封臣关系。`raiktor_actual_truce_expiry` 是另一战例的定向私有读数，不能套到 WAR31。后续若补原生查询，须采集战前/后/恢复后的同一 title ID holder、holder 的直接领主及有地封臣、双方有符号资源，以及两个角色定向持久 truce 及到期日；各读数须绑定相应原生 revision/episode/date 和 DLL/EXE 身份，然后才能扩展投影，不能仅把新字段塞进本报告。

另一个执行边界：当前 typed `surrender-war-<id>` 在 `native_driver.py` 仅由 `_emergency_surrender_readiness` 广告/执行，而该分支要求玩家为**进攻方**。R0221 WAR31 是**防守方**。用户本次单次授权并不自动使现有驱动器支持此步；正式实机需要先完成精确防守方 typed 门禁及受管复验，不能绕过驱动器直接调用原生写入。

本工具的合成测试：`<verified-python> ck3_autonomous_player/tests/unit/test_war31_postcondition_contract.py`。测试覆盖零与缺失、有符号差分、ACK 与原生战争状态冲突、下一回合与配对恢复、错角色及不匹配存档。它们只验证投影合同，不是 WAR31 实机结算证据。
