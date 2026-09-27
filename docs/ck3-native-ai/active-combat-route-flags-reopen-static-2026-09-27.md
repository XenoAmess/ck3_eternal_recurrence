# 主阶段败方撤退标志与追击重开：静态核

对象为 CK3 1.19.0.6 `ck3.exe`，SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。本页补充 [战斗终局控制流](active-combat-terminal-controlflow-static-2026-09-27.md)、[战中撤退](active-combat-retreat.md) 和 [增援加入](battle-reinforcement-and-join.md) 的输入时点。证据仅为 exact-build 离线指令，**没有新实机结果**。

## 谁写、谁读、何时改变

| 状态 | 原版 writer | 当前读取边 | 续算含义 |
|---|---|---|---|
| `CCombatSide+0xC0` disallow retreat | `CSetCombatSideDisallowRetreat` execute `0x2EB46F0`：`0x1977600` 求 bool，`0x2EB472E` 写 byte | `0x2308250` 选中传入 Army 所属 side，在 `0x23082CE` 读；winner 路径 `0x230A0DD` 调同一 validator | 败方也能被禁止 route；不能固定 false |
| `+0xC1` allow early | `CSetCombatSideAllowEarlyRetreat` execute `0x2EB4740`，`0x2EB477E` 写 | validator `0x2308434` 读；绕开严格 `elapsed>14` 日数门 | day gate 以 `BattleResult+0x2C` 原生 baseline 计，而不是随便用 phase day |
| `+0xC2` skip pursuit | `CSetCombatSideSkipPursuit` execute `0x2EB4790`，`0x2EB47CE` 写 | winner transition `0x230A26F`、pursuit tick `0x230A2DF` 读 | **败方** skip=true 会同步跳过追击伤害；它不是撤退合法性门 |

三位 writer 都可由加载的 script effect 改写，不是战斗创建时永久冻结的常量。`0x230A010` 已记录 winner 后，从**败方** side 的第一支 stored Army 取身份，才调 `0x2308250`；不能把玩家所选 CUnit 的 side flags 套到败方，也不能把一侧的 landless 限制套到另一侧。`BattleControlSnapshot` 目前仅为 selected CUnit 所在 side 输出 `side_flags` 与同一 Army 的 legality；它没有一次双侧 first-Army route census。因此当前 production snapshot 不足以直接构造完整的主阶段续算输入。

`0x23040A0` 的加入路径先写 incoming Army backlink；若旧 phase=2，`0x230423C` 把 phase 改 main/1 且 phase-day 清零，`0x2304247` 把 winner 写 `-1`；再调用两次 `0x23CB840` 重算 side totals，必要时调用 `0x2305580` 更新战宽。已核查的这个 wrapper 局部没有将 `+0xC0/C1/C2` 统一清零的直接写入；但下游加入 helper 或脚本 effect 的后续影响未由这个局部锚点排除，所以新主阶段必须重新取得同帧 flags、first stored Army、date gate，而不能延用旧 pursuit snapshot。若该日还有 main event，写标志的 effect 可能发生在下一次 `0x230A010` 前；没有原生边界 trace 时不得假定前一暂停帧的标志必然仍有效。

## 最小可实现的只读输入合同

对一个 generation-valid CombatID、同一 paused native revision 和 exact date，按双方**原生 stored Army 顺序**分别发布：first stored public CUnitID / native CArmyID、`+0xC0/C1/C2` 三个 bool、该 first Army owner 的 landless-gate 结果、BattleResult `+0x2C` baseline 与换算的 `elapsed_whole_days`。同时携带 phase/day、winner/forced、双方有序兵团 ledger 和当前日期。两个 side 必须通过 combat→side→Army→CUnit 的 full-ID/backlink 同帧复核；任一失败返回 unavailable，不以 0/false 填空。复用现有 selected-side `ReadBattleControlSnapshotSample` 的只读字段链，但要作为**双侧**记录，不能对一侧查询结果作镜像。快照只能保证本帧；若未来模拟加载效果/增援，则在其生效边界更新这些输入或标为未知。

## 已做的镜像修复和边界

`research_envelope.py` 的 `ActiveMainResumeState` 现在要求 `side_0_route/side_1_route: ActiveRouteSideState`，各自验证首支 public CUnitID 与该侧 frozen army 顺序一致，并拒绝缺失/非布尔 flags。确定 winner 后，它**只选败方** route state，将原生 elapsed 加本次继续推进的 main 天数，传给已存在的 `transition_after_winner_is_known`；skip flag 同样取败方。这是研究 kernel 的输入语义修复，测试夹具是 synthetic，**不是** production producer 已完成或整场胜率已 native parity。开战前 research envelope 仍用明确的 phase-events-disabled/no-voluntary-retreat 条件假设，缺少两侧 live route state，不能把该条件分布写成原版无条件结果。

复核命令：

```text
tools/.venv/Scripts/python.exe ck3_autonomous_player/native_bridge/research/verify_combat_route_flags_reopen.py --exe <CK3 1.19.0.6 ck3.exe> --expected ck3_autonomous_player/native_bridge/research/fixtures/combat_route_flags_reopen_1_19_0_6.json
```

核验器绑定 EXE 哈希与 19 处 writer、validator、winner 和 join/reopen 的确切指令，不证明所有间接 caller 或日内全局调度顺序。剩余 live matrix：败方标志分别为 true/false 时的 winner→phase/date/伤亡结果；追击增援重开后同 CombatID 双侧 flags 是否变化；以及脚本 effect 改写发生在 main 日内哪个结算边界。期间仍应把模型标识为条件研究，不抬高 production fidelity gate。
