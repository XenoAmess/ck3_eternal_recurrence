# R0266 H3911：正式只读查询与军费缓存同会话诊断计划

状态：**无启动计划；尚无本机 #449 formal query 或军费 Q100000 实值。**R0266 五项战争现金、期限及未来风险假设继续为 `null`，M5 建设支付门关闭。本计划只为下一次独立外置 attempt 固定可执行边界；H3911 可能已非来源最新帧，取得历史诊断也不能回填更新的 M5 帧。

## 冻结输入与已知失败

| 输入 | 必须逐字节核验的身份 |
| --- | --- |
| H3911 冻结来源 | 玩家 CharacterID 29829、episode `native-29829-2bc2d599f7f9`、WarID 16777231、date raw 53219928；save `5EFB3B3CF3EE7368C6C12D4C984B4A0366AA8A971409165016E3DC24725A4746`、source driver `DE09EA8B3648FAE89F90E5459991BC66AE52154971948DB39C353D05EEAAEE33`；family/ransom sidecars 及 DLL/injector 以 [接收清单](r0266-h3911-formal-query-receiver-plan-2026-09-28.md)的六件 SHA 为准。六件接收回执 `D:/ck3-research-artifacts/war-intake-20260928/r0321-h3911-matched-pair-001/receipt.json` SHA `25B832ED62BC6C75081B353BA1CFA018892AE357C6BAD7099F8C32E6C312C174`，只证明 transfer 6/6。 |
| 可执行代码 | 当前 #449 head `dc436f03b196c97213b57fe5393eb59a085eefba` 只是起点；若加入同会话诊断接点，冻结新 commit 和逐文件源 SHA。CK3 EXE 必须为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。来源 DLL `C71F6A5DFE8D23374B5B73F9DFA18AD9455CFF087D36EC93D2D29F7F610E8786`、injector `F9F2472C5969A248E7942AC79CC17A03CFDDA24C7FF79E78DA810A66A0E30C15` 的接收端 ABI/二进制只读路径仍须单独审计；磁盘 SHA 不是进程内代码页哈希。 |
| 既有 RED | 独立 R0321 H3911 **forecast receiver** attempt-2 虽通过本机 prepare/rebind/no-launch，却在 CK3 启动后 50 次 readiness snapshot 都未见 available native map；未完成查询，清理后 PIDs 为空。来源 `WAR/M5-WAR-CASH-20260928/RECEIVER-R0321-H3911-ATTEMPT2-RESULT-v1.json` SHA `C03B5C52EFD4B3269FD5C58DBA85CA4A06EC97CC77D51B86679C2E2542B9CBFD`。该 RED 不是 #449 的 formal-query attempt，也不证明零费用。 |
| 来源补证 | R0326 小回件 SHA `1820D49D4E6CD85017AA06BED8B78DCDC5CA30EC2FC1155FBB30F134122FA5A8` 只保留 compact paused before/after；planner 选中 `query-war-termination-options-16777231`，**未派发该查询**。原始 war request/envelope、军费 getter、缓存 epoch、费用报价、完整 treasury scale/原始 snapshot 均缺。来源的选中步骤不替代本机 #449 新 run。 |

## 会话前的硬门

1. 屏幕资源必须由现任执行者显式释放，CK3/recorder PID 清零；接收端领取 `ck3-screen:acquired` 后按项目合同取得当次新鲜 Steam 离线画面。禁止仅凭来源报告或旧截图启动。新建与 forecast attempt-2 分离的外置 attempt/profile，不覆盖任何旧原件。
2. 对六件本机不可变副本重新逐 SHA，核 exact EXE/DLL/injector/source commit，按本分支代码重新官方 `prepare-profile`、以**来源原始 driver 的管道**执行 `rebind-ordinary-seed-v1`、再对接收端派生 driver 执行 `native-one-generation-preflight`。保存原始与派生 driver 两个不同 SHA、family/ransom sidecars、argv/stdout/stderr、no-launch 报告；任一身份或 ABI 不合格即停在无启动阶段。另复核 forecast attempt-2 的 native-map readiness RED 原因，不把 readiness 超时当现金零。
3. 冻结一 turn 受管命令、正式 selected-query receipt 路径、最少 1800 秒 readiness 与至多 3900 秒总会话上限。CLI 必须以此 checkout 当次 `--help` 读回；任何启动参数变化都用新 attempt。二进制审计要明确 exact DLL 对此 WarID 查询的已编译入口、无 gameplay submit 路径及退出清理，不以来源源码哈希代替已加载模块审计。

## 同一 PID 中的最短读取顺序

现有 `native_auto_run.py` 在 `service.auto_turn()` 后于正式查询路径拿 `after_snapshot` 并构造 candidate receipt，随后清理会话；它**没有**一个把 GUI 采样保持在同一暂停 PID 的受管接点。若要同时诊断军费，须先新增显式 opt-in、只读、失败隔离的 `post_formal_query_passive_sample` 接点，位置在 `after_snapshot`/formal query 校验之后、cleanup 之前；保全采样前后的完整原生 snapshot，而不是在进程清理后另启存档并拼接。接点不得调用 `GetGoldExpensesBreakdown`、`MilitaryView.GetGoldMilitaryExpenses` 或 `GetAllRaisedGoldMilitaryExpenses`，不得写 CK3 内存、推进日期或提交行动。未实现并静态复核此接点时，正式查询 attempt 只能给 query receipt，不能承诺同会话军费。

1. 先读 `paused=true`、`map_ready=true`、唯一 WarID、玩家/episode、snapshot ID、public/native revision、date raw、Q100000 treasury 和 PID/创建 FILETIME，并记录现役 EXE/DLL 的实际进程模块路径与磁盘文件 SHA。原始值与复核值均保全；不能把四份 driver/outer 国库投影描述成四次独立原生内存读取。
2. **实际** `service.auto_turn()` 必须选中 exact `query-war-termination-options-16777231` 与 typed `read_only_query`。在 `before_submit` 门拒绝 null、move、raise、mercenary 及 query 参数不符；保全真正发送的 protocol v1 request、相同 request ID 的 `command_result` envelope、query sequence、WarID、native result、提交计数。R0326 的未派发文本不满足本项。
3. 查询后复核相同暂停六字段/国库、同一 PID/创建时间、零 gameplay submit、零日期推进。仅当此正式查询链完整时才保全外置 `formal-selected-query-receipt.json`；两项批准 registry 目前均为空，所以即使 receipt candidate 通过，也不发布 `immediate_war_action_cost_raw=0`。
4. 在**同一进程仍暂停**时运行 [顶栏有界双读](../../ck3_autonomous_player/native_bridge/research/war_cash_topbar_bounded_sample.py)：精确 global→idler→handler→topbar owner/vtable/back-pointer、每次 ≤64 KiB RPM、行名称/raw/scale、玩家 ID；同一原生帧前后再查。新渲染 epoch 诊断额外只读全局 RVA `0x576CC68` 指针、对象 `+0x180` tick、RVA `0x570D8D0` 间隔及顶栏 `+0xF88` 标记。自然 GUI 刷新与可见费用需由屏幕拥有者按桌面证据合同取得；标记写在刷新调用**前**，tick 差或双读稳定均不能单独证明缓存完成或属于 native revision。
5. 当前军费只能在顶栏费用行树中识别真正互斥的军费项，并与原生独立军费计算结果/可见值交叉核对。全军征召满员预测值要在同一 PID 找到唯一玩家 `CMilitaryView`、完整角色句柄、自然刷新后 Q100000 `view+0x740/+0x748` 及 GUI 值；无 view 或刷新证明就单独记 `missing`。不要把六个可能嵌套的军费行相加，也不要把顶栏总支出当战争军费。
6. 再读完整原生帧、国库、WarID、PID/创建时间、提交数和清理状态。所有原始 request/envelope/snapshot/GUI bytes 与机器回执按精确 SHA 放外置新 attempt；独立核后才给同帧诊断。即便两个**月费率**被读到，已扣现金、待办承诺、selected move 的即时价、未来上界/风险、Robert 版本化最低储备和期限仍未知，不能开放 M5 支出。

## 下一步需要的独立来源

- **军费缓存新鲜度**：GUI 自然刷新完成的可核原生/屏幕证据、渲染 tick 与 native revision 的关系、唯一玩家 view owner；现有 marker 只表明刷新曾被排期。若无法证明，保留 `monthly_military_rate_missing`，不填战时现金。
- **实际扣款和未来上界**：游戏金币扣款的精确日期/次数、当前与满员军费组成、舰队/上船、补员、雇佣/续约、兵力/费率变化的有源覆盖。一个月率不能按 horizon/30 当短期现金上界；一日窗口也可能遇完整月账期。欠任何上界时 `future_war_cost_upper_raw` 与 risk 保持 null。
- **动作与政策**：owner 侧完整 pending/committed 账本，选定 typed action、army/route/target/preview/报价同帧严格绑定；Robert 战时 liquidity floor 的发布 owner、ID/version、金额、用途、有效期。来源明确没有已发布政策；建设 200 金 floor 与 AI war chest 均不能借用。

本计划预计占屏和受管清理约 35–65 分钟；只有 screen owner 释放、no-launch 与二进制静态门 GREEN、同会话诊断接点完成后才排队。任何步骤 RED 留新 attempt，不重用其部分现金读数到另一帧。

# Optional passive topbar diagnostic hook

The formal one-turn runner now accepts `--formal-war-query-passive-topbar`
only together with its fresh `--formal-war-query-receipt-dir` and source
commit. The option defaults off. After the selected termination-options
query passes its normal after-snapshot check, and before managed cleanup, the
runner calls the exact checked-in topbar sampler in a child Python process.
It opens the same PID with query/read access, uses `ReadProcessMemory` only,
and allows at most 64 KiB per pass across two bounded passes. On a reached
attempt, the raw sampler file and `passive-topbar-diagnostic.json` use exclusive creation in that attempt
directory; a second attempt cannot overwrite them. The diagnostic verifies
the sampler's PID, process creation time, exact EXE disk hash, intent receipt
hash, read budget and six-field frame after a second runner postcheck. A
changed frame or PID invalidates the original formal query candidate.

Every path remains `RED_diagnostic_only` for cash: the topbar cache may be
stale even when two reads match, and its expense rows do not establish a
war-only monthly debit, a selected action price, a cash settlement cadence,
or an upper bound. Sampler errors are recorded as typed RED observations and
do not replace the native query result. The existing five cash fields and
horizon remain null. No H3911 live sample has been taken with this option.
