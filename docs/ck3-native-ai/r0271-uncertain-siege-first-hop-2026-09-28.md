# R0271：围城未来参战集合未明时的首路点续行（2026-09-28）

## 冻结输入与边界

[R0271 正式失败摘录](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-R0271-SIEGE-PARTITION-20260928.r0271-blocker-excerpt.json)来自失败报告 SHA-256 `A5C5D21266D7ACFDC2CDD4C619B2846DE100BFF7F4CAD1E261DC116B880790CD`。阻断帧为 `native:30`、public revision `31`、native revision `30`、raw `53219160`、WarID `16777231`。玩家军 `83886367` 在 `2610`，到围城目标 `2629` 的当前路线预计 raw `53220216` 到达；敌围城军 `50331920` 已在 `2629`，场外敌军 `83886484` 在 `3719`，其当前路线预计 raw `53219928` 到达目标，**早于玩家 288 raw ticks（12 游戏日）**。两军都必须留在全敌接触名册内。

这组当前命令的 ETA 不能证明敌军 `83886484` 未来一定参战，也不能证明它会缺席；AI 命令、围城和战况可变。原 `offsite_hostile_may_join_by_target_entry` 阻断对**目标处的未来单次遭遇**是正确的。不能用只含 `50331920` 的 V3 输入批准接战，也不能把尚在 `3719` 的军队假装成当前固定守军。当前没有可据此声称的整场胜率、围城最终结果或终战净收益。

## 可恢复首路点

生产规划器仅在这个精确阻断理由出现、目标路线至少还有两个路点、目标路线的下一日全敌接触查询 `one_day_contact_free=true` 且 `conflicts=[]` 时，转入**不依赖战斗预测的探索路径**：

1. 原生预览从 `2610` 到首路点 `2614`，要求返回的完整路线恰为 `[2614]`。
2. 针对首路点重新查询包含 `50331920`、`83886484` 的同帧全敌接触；要求下一日无接触、无冲突，并核两次接触查询的逐军当前位置一致。缺读、位置矛盾或变化都停止。
3. 只有上述条件全部成立且 typed `move-army-83886367-to-2614` 可用，才提交该**首路点行军命令**。输出保留 `participant_scope_unresolved`、`active_attack_allowed=false` 和原始阻断理由；从未把目标 `2629` 的行军或战斗授权给该分支。

`2614` 的当前预计到达时间 raw `53219328` 距阻断帧 7 游戏日，而原生接触证明仅覆盖下一日。因此首路点命令**不是七日安全承诺**。命令后，既有受管 moving 路径在每个新的暂停帧重新取得完整敌军路线接触查询；缺当前帧证明或有接触会阻断下一次推进。`native_driver.py` 的 active-route 时域将每次推进限为 1 游戏日，并在执行前重验当前 revision 的证明。旧查询随日期或 native revision 变化失效。到达首路点后，规划器须重新识别围城、敌军位置、路线、现金和退战选项，再决定下一个动作；在到达前也不得把未来参战集合当成已知。这里的风险预算只覆盖逐日**即时接触**，不量化因行军而发生的围城损失、军费或远期战斗结果。

## 验证与剩余工作

聚焦测试以 Git 保存的 R0271 路线、ArmyID、日期和 ETA 重放规划器查询链，并反证首路点冲突、下一日接触不安全、过期读数及敌军位置不一致不会得到行军命令。普通和 `-O` 模式均通过；既有 `test_committed_route_requires_fresh_daily_horizon_even_when_sentinel_live` 核下一帧必须重新查询。测试中的完整战争帧和个别兵团实力是合成夹具，不能当作原生 R0271 实机复验。

当前独立 worktree 没有相对 `.venv`；静态复验显式使用主 worktree 的 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`（Python `3.14.7`），依赖 probe 为 pytest `9.1.1`、NumPy `2.5.2`、Pillow `12.3.0`，并以 `PYTHONPATH=D:/w/r0271/ck3_autonomous_player/src` 指向本 worktree 源码。`test_combat_provisional_defense_canary.py` 普通与 `-O` 各 8 项通过；上述既有 moving 路线回归 1 项通过；`tools/validate_python_only.py` 为 `PYTHON-ONLY GREEN`。`-O` 模式 pytest 会对自身断言改写发出一条警告，测试主体使用 `unittest` 断言，结果仍为 8 通过。

H3388 精确 source pair 与候选 DLL/injector 已由固定 OneDrive `WAR/R0271-H3388` 接收并逐字节核验，接收回执 SHA-256 为 `A5FAA910E25ADD1D9002C1C239440C2EB6ADEC729156EB3A1D68520E6F65974D`。不得将 H3446 存档与失败后已变异的 R0271 driver 强行配对。R0271 原失败仍保持 RED；以下接收机回放属于独立新 run，不改写该失败。

接收机 R0002 从精确 H3388 pair 以受管 Steam 离线、官方 no-launch prepare/rebind/preflight 完成 36/36 turns、无 blocker；旧阻断帧 raw `53219160` 选出目标 `2629` 的全敌接触查询和首路点 `2614` 的精确路线预览。该 run 停在预览，未提交移动。其 33 件冻结原件 manifest SHA-256 为 `E854315B472A837BB3C2FF28DD6CBCAA67B9D673A1BD0D1E601BA70CCD72B0A7`；[R0002 正式验证](../autonomous-agent-progress/coordination/war-requests/verifications/WAR-ROBERT-R0271-SIEGE-PARTITION-20260928.r0002-partial.json)保留每个检查点哈希。R0001 的 300 秒就绪超时和 R0003 的 900 秒就绪超时均为零回合环境 RED，不得当作算法结果；R0001 profile logs 曾被下一次运行覆盖，证据缺口已如实登记。

从 R0002 冻结终点建立的独立 R0004 在 12/12 turns 里继续：同帧全敌首路点查询 `3445` 的时域为 raw `53219160` 至 `53219184`，敌军名册 `[50331920,83886484]`，`one_day_contact_free=true` 且 `conflicts=[]`。随后 `3446` 的 typed `move-army-83886367-to-2614` 得到 `submitted`，正式 turn 10 的后置帧为 `native:4`、revision `5`、raw `53219160`、`war_action.status=moving`；`3449` 在该后置帧重新读到两支敌军的一日 contact-free 查询。R0004 以 checkpoint `3D8E689641ED299DFE5921ADF2952CDE6BC9439F7F8AE6B7334061EACC5D0F5F` 和 driver `3D5C7AC0E1E0705D84E5DAAA0BBC5FE263394A055C8D9570889F9084615A96D0` 结束，29 件冻结 manifest SHA-256 为 `F6D6DA5B9288B42ABE369F44FA3616B5FBFF808E4A20F77361A2B179898A0627`。这证明命令提交且后置状态为行军中，尚未证明游戏日期推进或跨日新证据。未来围城参战集合仍未知，不能把 `submitted` 写成已抵达 `2614` 或允许进攻 `2629`。

再从 R0004 冻结终点建立的独立 R0005 在 24/24 turns 里，依次从 raw `53219160` 推进到 `53219184`、`53219208`、`53219232`、`53219256`、`53219280`、`53219304`。每次仅推进 24 raw ticks，且各自先在当前新帧重读 `[50331920,83886484]` 两支敌军的原生接触查询。关键反复用例为：历史 `3456` 的 raw `53219160` 证明只允许 `3457` 推进至 `53219184`；在新的 raw `53219184` 帧，`3460` 重新查询得到时域终点 `53219208`、`one_day_contact_free=true`、`conflicts=[]`，才允许 `3461` 第二次推进。后续同样六次查询、六次推进，正式报告均无 blocker。末检查点为 raw `53219304`、save SHA-256 `8A00FEF601F722BF5028563AF4A1E7680D8E6EF25C3C019CB260D6C9DBA3D2EC`、driver SHA-256 `EBD733F5919A6DEA26FD66F4A34679E6889E67D4E24FD431E69099CC341C6B18`；29 件冻结 manifest SHA-256 `429ECA005996563F14AB2E94CBB1E6AB8108CFBB048F2A09503DA61EC3941DD9`。[R0004/R0005 正式验证](../autonomous-agent-progress/coordination/war-requests/verifications/WAR-ROBERT-R0271-SIEGE-PARTITION-20260928.r0004-r0005-recoverable.json)记录每次 run 的报告、回执、来源与冻结哈希。

R0005 结束时距首路点当前预计到达 raw `53219328` 仍有 24 ticks。实机结论是**遇到未来围城参战集合不明时，可以安全合同内提交首路点行军，并逐日以新鲜全敌证据恢复推进**。仍未证明实际到达 `2614`、目标 `2629` 的未来参战集合、最终战斗、围城胜负或终战代价。下一日及之后的推进依旧要重新取得当前帧证明，不能把这六天的成功外推成剩余路线安全。

## 后续 R0321：不同帧上的战斗预测门槛

固定 OneDrive/WAR 收到的 [R0321 来源机通知](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-R0321-COMBAT-FORECAST-20260928.source-notice.json)共 5,777 字节，接收机核得 SHA-256 `6CCA6BE7CD31828F662271C9FF0B58E9C7D48081A587C9D5833DA9A7C2D6DD20`，且通知引用的前序 R0319 哈希匹配。来源机称 R0321 正式续跑在 turn 27、h3911/raw `53219928`、`native:23`/public `24`/native revision `23` 再度停在规划阶段。此时两支敌军 `50331920`、`83886484` 均列入目标 `2629` 守军，参战分区状态为 `available`；但 V3 输入读取虽获接受，合格预测生产者为 `producer_unavailable`，研究性预测为 `same_frame_encounter_scope_mismatch`。`selected_step=null`、`active_attack_allowed=false`，来源机没有提交攻击。

这是**较新帧上的不同阻断**，不能倒写成旧 R0271 raw `53219160` 已证明目标参战集合。仓库静态核查发现研究性 `_provisional_defense_research_assessment` 要求 `len(defender_army_ids)==1`，对 R0321 的两支守军已足以触发范围不符；正式 `COMBAT_ENTRY_EU_ACTIVATION_ENABLED` 仍为 `False`。去掉研究用单守军条件不会自行产生合格胜率、模型精度证据或预期效用授权。完整 388,302 字节正式报告、同帧 V3/分区原始行、H3911 合格配对及准确度试验带尚未被接收机取得；来源通知也写明 `recovery_qualified_for_receiver=false`。详见 [R0321 新请求](../autonomous-agent-progress/coordination/war-requests/requests/WAR-ROBERT-R0321-COMBAT-FORECAST-20260928.json)和 [R0271 后续元数据审计](../autonomous-agent-progress/coordination/war-requests/verifications/WAR-ROBERT-R0271-SIEGE-PARTITION-20260928.r0321-metadata-audit.json)。

随后 `master` 的 `32c0dd370` 将 H3911/raw `53219928` 列为最新持久检查点，并记录来源机独立候选 `2eb9cb952` 已对冻结 save、driver 与 sidecar 完成正式配对、rebind 和 no-launch；其 `current-state.source.json` 为 132,004 字节，SHA-256 `76B21C3F6E41A79AA9B919594CCE9EC7B28F2BD027391E973578ED1BE7419507`。这项**较晚的来源机配对资格**更正了旧通知的恢复资格字段；接收机仍未取得 H3911 资产或完成本机 no-launch/冷恢复，也没有新的预测合格或正式续跑。[Git 审计](../autonomous-agent-progress/coordination/war-requests/verifications/WAR-ROBERT-R0271-SIEGE-PARTITION-20260928.r0321-metadata-audit.json)和固定 WAR 的追加勘误保留了两份按时间顺序的证据。

之后固定 WAR 传来了 388,302 字节的 R0321 正式报告（SHA-256 `7A7774C59DA6099B0A1FFD650AB21A29407BD8B22B1056C7B6F5053251A5CF30`）与三份小型来源配对证明，接收机按 manifest 逐字节核验。报告显示 27 次尝试中前 26 次成功，阻断 turn 27 仍未提交动作。raw `53219928` 的两支敌军都在 `2629`；全敌路线查询只证明到 raw `53219952` 的一日无接敌，而路线首路点 `2614` 当前 ETA 是 raw `53220096`。不能将这一天的证明外推到首路点到达。报告的 V3 结果只是 `accepted/available` 的查询外壳，`monte_carlo_ready=false`、`planner_usable=false`；当时完整 `combat_simulation_inputs` 原始对象仍位于未传输的 H3911 source driver。报告另在同帧列出战时联合预算所缺的七项战争金额/政策字段。精确 JSON 指针和抽取值见 [正式报告摘录](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-R0321-COMBAT-FORECAST-20260928.formal-report-excerpt.json)。随后已在 WAR 请求只读原始 V3 有界摘录；本段不授权行军、接敌或退战。

其后来源机从冻结 driver 的 `/command_history/3919` 只读抽取了 2,080,166 字节的完整命令行与 V3 输入对象，接收机核得 SHA-256 `865EA7B7AC1B4A680E2BE3A1D84012C67CF9550474075E4A917EFE043CCCDD51`。该行与正式报告的查询外壳在命令、`accepted/status`、`native:23`、public/native revision 和 `query_sequence=1` 七个字段相同；原行没有 `request`、前后帧、`episode_run_id` 或 `connection_generation`，不能凭这七项替代完整会话绑定。V3 输入列出我军 `83886367`、目标处两支守军及假想入口 `2630`，`input_observation_ready=true`；其 `contract_stage=production_exact_132_refs` 仅描述输入引用阶段。四项战斗转移/事件域和三项 phase-event 保真门仍缺，`monte_carlo_ready=false`、`transition_fidelity_gate=false`、`planner_usable=false`、`active_attack_allowed=false`。原始 46 MB 父 driver 未传，因此来源机所称摘录与父行语义全等尚未在接收机独立复核。[V3 接收摘要](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-R0321-COMBAT-FORECAST-20260928.v3-receiver-summary.json)保留字段与哈希边界；目前依旧没有可用战斗胜率、模型精度或预期效用授权。

为后续接收机匹配复验和同帧现金查询，固定 WAR 另发六件精确资产请求 `WAR/M5-WAR-CASH-20260928/RECEIVER-REQUEST-R0321-H3911-MATCHED-PAIR-v1.json`（SHA-256 `1C82BD10B526179AE1AEC4CF8F8A452190089D5204DF031212B501371601769F`）：H3911 冻结 save、原始 driver、两份 sidecar，以及 R0321 实际运行 DLL/injector；不索取来源机重绑后 96 MB driver 或旧 H3860 配对。发出请求时，来源 ACK、清单、文件复制与接收机逐字节校验尚待完成。即使传输成功，仍须新的本机官方 rebind/no-launch 和独立正式候选；任何工件到达都不能视为 R0321 预测 RED 关闭。

随后六件共 `128,617,719` 字节已按来源 manifest 在接收机独立校验 SHA 并外置不可变复制；完整原始 driver 的 `/command_history/3919` 与先前 V3 摘录的 `/command_row` 深度 JSON 相等，包含整个 `combat_simulation_inputs` 对象。这只关闭摘录对父行的语义保真缺口。接收机 H3911 attempt-2 的本地重绑与 no-launch preflight 成功，原存档字节未变；随后另起的 CK3 只读 native session 在 50 次 readiness 查询后仍未得到地图原生状态，结束于 `ExceptionGroup`，没有完成任何战争查询或提交游戏动作。原始回执和 SHA 见 [attempt-2 接收响应](../autonomous-agent-progress/coordination/war-requests/responses/WAR-ROBERT-R0321-H3911-RECEIVER-ATTEMPT2-20260928.json)。所以 R0321 双守军预测仍 RED，当前没有同帧战时现金读数或接敌授权；更晚的 H3911 也不改写原 R0271 turn36 的历史 RED。

H3911 attempt-3 在新接收机代码下再次通过 no-launch 重绑与预检；live 冷载日志出现 postread/vassals，MCP 初始化返回，但首次 `ck3_take_snapshot` 在 120 秒有界等待后超时，未留下快照响应或 `readiness-001`。原始 `failure.json` 只记录 `ExceptionGroup`，不能据此断言更底层的超时原因；退出回执证明进程清理和来源工件未变。详情见 [attempt-3 接收响应](../autonomous-agent-progress/coordination/war-requests/responses/WAR-ROBERT-R0321-H3911-RECEIVER-ATTEMPT3-20260929.json)。另有 R0329 来源通知称 Emma 婚配提议仍待答复，且未推进日期；[接收依赖回件](../autonomous-agent-progress/coordination/war-requests/responses/WAR-ROBERT-R0329-EMMA-WAR-DEPENDENCY-ATTEMPT3-20260929.json)记录当前没有已入 master 的合格战争预测或安全路线版本及兼容字段。她的答复与婚配尚无接收机原生回读，不能为等待答复而手动越过战争规划器推进日期。
