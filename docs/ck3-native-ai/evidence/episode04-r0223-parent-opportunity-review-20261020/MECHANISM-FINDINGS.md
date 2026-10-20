# R0223：先证明角色结算机会，再追 c/d writer

machine_id: `desktop-3fevhd2-1c74096080`。离线复核日：2026-10-20，15:44–16:15Z 有限 metadata scope。执行源：`bc63851081462413d0cc6ebe62e37490707ee6a9`；实际 `machine` CLI 与 tracked clean 读回见 [来源索引](SOURCE-AND-SMALL-FACTS.actual.json)。本包没有新游戏、SDK、DR、query、consumer/selector 执行、EXE 读取或构建；只读 R0223 已有小原件和精确源码。原始失败/零样本结果不改。

**结论：R0223 没有留存 c/d 写入，不能判定 c/d producer 不存在。最缺的事实是：目标角色 33388 是否在这个实际一天里进入过角色结算父函数 `28F7840`，以及进入时真正使用哪个 context。下次只做这个入口机会实验；不要重复相同 Mar31 S0 月界。** 当前方案未实现、未冷资格、未实机，不授 R08/full/business/ABC 信用。

## 1. 实际事实与来源

原件根 `L`：`C:/ck3-e04-resume-20261020-a01/r08-scene-a02/driver-runs/desktop-3fevhd2-1c74096080--vanilla--R0223/case-output`。以下都是该场，不复用旧 R204/R213 运行资格。

| 实际读回 | 数值/边界 | 原件/JSON pointer |
|---|---|---|
| 所有者 | PID32336/create134369836483832557/gen1；actor33388/localplayer1；ordinary/null episode | `r08-writer-control/C-D-WRITERS.actual.json#/Root_binding` |
| 绑定对象 | Character2176289642448；context2176345091488；GameState2175668561792；window1/epoch1 | 同上 `admission_owner_binding` |
| 一天 | raw53149056→53149080，absolute389544→389545；实际 clock start/target 达成、completed_tick_count1、overshoot0、pause observed | `r08-1615-a01-day-once.actual-results.json`；小摘要见 timing projection |
| 玩家军队 | 一条 native controllable army_id0/owner33388/province2170；route complete/empty、无战斗/撤退；soldiers=null、army_strengths=[] | before/independent-after common-view `/body/player_armies`。不能把未观测兵数当 0 |
| 当前军费 rate | before386622→after310621 raw/month；all-raised484950 是替代场景；personal treasury63760699 不变 | cash-before/after `/body/military_expenses` 与 `current_treasury` |
| 四原始字段 | initial/before/after a=b=c=d=0；context 前后相同、capture_complete/context_stable/actor_identity_stable/same_frame_ready=true，failed_reads0 | cash `/body/current_raw_context_v1` |
| 两条实际 trap | offset2C0/2C8，各0→0，same-value write；post-PC28A645B/28A6466；thread36552/gen1，c/d0条，unknown0条 | `watch/ACTUAL-WRITERS.json#/qualified_writers` |
| watcher 闭场 | timeout；2 hits/128 上限、restore/detach/cleanup_complete 真；thread admission complete；full_window_all_writes_covered=false | 同上 `/terminal` |

`C-D-WRITERS.actual.json`：4581B，SHA256 `f6c1cf99033da0df2816c4e08446d90c892d08a9c2ca0d2efe3401abbd5cee17`。
`ACTUAL-WRITERS.json`：7681B，SHA256 `a2a0619e1ca5b22f0f76d45ae90e7d49c1f1d916964f3a7e61b3f3d2fc7e9d24`。
其他原件完整 pins 见 [packet projection](PACKETS-PROJECTION.compact-a02.actual.json) 与 [timing projection](TIMING-CASH-READBACK.compact-a02.actual.json)；没有复制完整 active_wars/大 native-report。

**必须区分两种 journal。** payment `records=[]`、retained0、latest0；但 cash-after 的 `natural_journal_status.retained_records=2`，`natural_parent_returns` 实际留有两次 original_called/returned=true：pre-date `2A99DA0`、thread36552、entry/return absolute389544；post-date `2A9A570`、thread15464、absolute389545。它们是军队自然阶段父调用，不是 `28F7840` 角色结算调用。不能写成“所有父 journal 均为零”。原完整两条小 record 已保存在来源索引的 `natural_after`。

时序：observer claim15:36:00.154740Z；READY15:36:00.333295Z/armed108；day claim15:36:07.336432Z；真实公共 day operation15:36:10.258635Z–15:36:20.843452Z；最终消费15:36:33.517652Z。30s debug deadline 在 attach/preflight 后进入 loop 前设置。协议顺序支持 observer 先 ready 后一天推进，不支持“实际一天开始太晚、完全没覆盖”的解释。原 raw 缺 observer start/end QPC 与频率，不能将 hit QPC 与 date/native event 强行拼成全窗口完备证据；源码也固定输出 full_window_all_writes_covered=false。

## 2. 源码能解释的范围

`ck3_12003_war_cash_current_reader.cpp` SHA256 `1126fb936eeb9b5beb67e5935452af17983121562011c2c90ddb9f4c9aaf921b`，190–249 行：Gold→MonthlyFlow→CurrentMaintenance→AllRaised→raw context，同一个 played Character；raw helper 从 Character+1C0 实际读取四个字段，前后身份再核，没有制造 callback。MonthlyFlow 的 expense_context_character 可解析另一角色，但 raw/current getter 参数仍为 played actor。因此“Python 复用了旧 cash 回复/四槽自动选成上级领主”不符合这些已读实现。**底层四字段自身是何种缓存及刷新机会仍未知，query fresh 不等于底层数据刚由 producer 生成。** 顺序 getter 也不是同次结算因果 join。

已有完整 caller 源证明 `28A645B/28A6466` 对应 `28A63E0` 内 secondary+18/+20→context+2C0/+2C8 copy；本轮 post-PC 可复用该静态知识，不能改写原 consumer 的 source_unknown，更不能升级为 c/d writer。128 上限只用了2，不是被 a/b 耗尽；无 c/d 样本的主要缺口不是配额抢占。

**当前 payment 安装表核实**：`war_payment_runtime_12004.cpp` 的 kDescriptions 只有 transition`24E8DB0`、gateway`28B9950`、personalADD`285EE40`、personalSUB`285EED0`、landSUB`285EFF0`；条件 RAW4 getter 第六项`28B9490`。枚举在 `war_payment_runtime_12004.hpp`。**没有 `28F7840` 入口 hook，也没有“角色结算父 invocation 次数”DTO。**

`war_payment_passive_12004.cpp` 148–186 行：先 Ready/retain_actor/Permit，再入钱包 callback；仅 personalADD 且原 caller=`28A6D7C` 时建立 `generic_wallet_context`，取四原字段和 stack-based generic parent trace。`parent_transition/gateway` 是24E8DB0/28B9950的 TLS 链，`natural_parent_metadata` 是军队自然阶段 scope。callback records0 因而不能区分：角色父函数没被调度、已调度但没走 ADD、retention 排除、或其他未留存的调用路径。字段名里有 parent 不代表已观测角色结算入口。

旧完整 source 已证角色 parent`28F7840` 正常路径先 call`28A6D10`（call28F7934），再到 expense-context/current-maintenance getters；后面的 getter 不能倒因果为更早同 invocation 的 settlement 输入。任务`290DC00/290FD20` 的 selected index 不是日期；constructor/enqueue/calendar 仍未闭。

## 3. 仍未知且真正缺少的字段

1. **目标实际被选中吗**：`28F7840` 原入口 RDX 是否是本窗口 actor33388、原 R8D selected index、原 RCX inline context、真实 caller。当前钱包零 records 没有这些事实。
2. **入口使用哪个 context**：实际 RDX+1C0 是否等于同场 fresh paused before 的 context。当前四槽只绑定一个 context；端点稳定不能排除一天中临时切换后恢复。
3. **有效维护资格**：现有 army endpoint 证明拥有可控军队、rate positive；未提供这支军队/付款方进入角色结算任务的实际 membership/eligibility 或计费 cadence。rate>0 不是付费、producer 或该日选中的证明。
4. **更精确的时钟**：现有 raw 没 start/end QPC，a/b hits 不能与 natural callbacks 用不同 clock 数值直接 join。新样本应在同一原生 clock 内给机会边界，不从线程相同推同 invocation。

R213 历史同 actor 有 c310999/rate386622，但相隔约27 raw days、不同进程/窗口/对象；只能证明历史可见过非零 c。不能要求当前必有同值、以旧 pointer 或旧 rate 重新授资格。

## 4. 下一场只选一项：目标角色父入口机会观测

选择 **新、default-OFF 的 `28F7840` 执行 DR 入口观测**。这是从原入口捕获实际机器参数的专用小模式，不是执行结算、不改内存数值、不新增 detour/返回 ABI 假设。先回答“被调度了吗/用哪个对象”；暂不构造收费或 c/d writer 断言。

源锚已有：`acceptance/2026-10-16-r0174-maintenance-source/PARENT-HOOK-SOURCE-ANCHOR.contract-a01.json`，原16B prefix `488bc453554881ec980000004c8970e0`，SHA256 `d44f03f2855791f5fb4ee339dc21b28917e981d419df5cb4f1ecb89ba20aa517`。原合同状态明确为 SOURCE_ANCHOR_ONLY_NO_IMPLEMENTATION_OR_ABI_QUALIFICATION。此入口 RCX=task+70 inline context、RDX=selected Character、R8D=raw index；只保存实际参数，不凭减70制造同实例 job。

最小实现/资格缺口：已有 a08 四槽 observer 没执行模式；正在外置的3F90A6F exec 候选也固定另一个源地址。需一个独立命名的 parent-entry 模式、目标角色筛选/foreign计数、typed 小结果和对应真实冷例（实际入口/错 anchor/错 owner/原 DR 已占用/线程代际/清理）。明确构建/两 EXE/SYSTEM/exec fixture qualification 后，绑定新源码及普通 null-owner，才能进入公开同 CaseClient 的一次有限准备/执行链。**当前没有可直接添加到旧 a08 argv 的合法开关；不将此方案称为已可运行。** 不重造 launcher 或一般观测平台。

建议有限数据合同（施工预算，不是原生已有字段）：一个 fresh owned no-load window；最多30s、一个原生 exact day、累计128 exec stops、最多8个目标入口详细记录；foreign只计数，不导出角色全集。每个目标记录保留 process/create/gen/window/epoch、thread/generation、实际 RIP==28F7840、原 RCX/RDX/R8/R9/RSP、[原RSP] caller、Character+18/+1C0 双读/失败状态、原四字段、原生 event/日期；start/end 也保同 clock。第一条目标记录已足以完成“至少一次被选中”判断；预算/线程覆盖不足时 negative 必须标 incomplete。执行源暂停/恢复与原 DR 还原必须沿独立资格合同，未知 attach/动作不重投。

这项低成本执行DR方案的主要限制是 foreign 入口也会停机：128 次可能早于 actor33388 进入而耗尽，真实数组顺序未知，不能把 a/b copy 时 RBX2242 当作结算 index。故首要成功条件是**取得目标一次真实入口**，不是取得“目标永远不被调度”的阴性结论。若 Root 要求一日目标负结果具更完整的机会覆盖，应先改用默认OFF、内部target-filtered的原生入口计数/记录方案并独立资格（旧16B提案可作为来源，仍需ABI/原调用一次/回滚冷验）；它是替换实现，不能与本次DR或dispatch方案叠加现场。本包不擅自切换或实现该较高成本路线。

基线只在 Root核正常 Save 原件后选择 **R0223 成功一天之后的正常后继**，以新进程 fresh query 的实际 raw date 为 start、target=start+24；不复用旧 PID/context/Q/scope，也不再次从同 Mar31 S0 重放。场前公开 snapshot/cash/自然阶段/付款 ON 读回和 exact day、独立 after cash、OFF/clear、verified Save/normalclose可复用现同client公共能力；新 observer 入口需显式受限接线，不能绕过现 admission argv 精确校验。

| 一次新实验的结果 | 能得出的结论 | 不能得出的结论 |
|---|---|---|
| 有其他 parent entry，目标0，未到上限/覆盖诊断完整 | 本有限窗口未留目标入口；优先追目标 selection/eligibility | 该角色永久不结算/零军费/固定 cadence |
| 目标入口>0，入口context与新before不同 | 旧固定context watcher可能未盯到实际结算对象；取得真实入口对象 | 可以复用跨进程旧context或自动改盯点 |
| 目标入口>0，同context，c/d入口为0 | 确实获得一次“已调度且输入为0”的机会；下一应找该机会之前 producer | 本次收费0、c/d writer不存在、军费已解释 |
| 目标入口>0，同context，c/d入口非0 | 已定位非零输入的时间/对象边界 | 已定位写指令或与NET同 invocation |
| 全局0、达到128或覆盖不完整 | 保留有界负结果/诊断，停止这一场 | 自动反复开相同存档等待阳性 |

比较后暂不选的两项：`--capture-known-copy-caller` 可补 a/b copy caller，但不是目标结算机会，而且当前公共 prepare/controller精确 argv 不允许手加；`3F90A6F` 可读真实dispatch vptr+10 target和原参数，但 generic first job 未知，不能筛33388或连 payer/calendar，其 target ABI/参数调整仍未知。两者都不应同时加进下一现场。

完整源码文件 SHA256/行号锚点在来源索引。当前结论仍是 `NO_QUALIFIED_C_D_TRAP_RETAINED`；R08军事已付/同NET/payer/cadence均未闭，B0/2与正式主题计数不变。
