# 第4期研究总账：行军、补给与损耗

2026-10-04。用户已授权开始高并发研究与拍摄。本总账汇总首批并行工作包，沿用[导演案](director-plan.md)与[交接](../../../docs/handover/2026-10-04-war-episode04-march-logistics.md)的20–40分钟交付范围，编辑目标30–35分钟。**机制文件研究、最小观测增量及拍摄配方已有新成果；本期主案尚待新实机可行性核对，A/B/C出发档尚未冻结，正式录像尚未取得。**

游戏身份重新核对为 CK3 **1.20.0.3 / Steam25652598**；当前安装 EXE SHA-256 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。本包读取源码最终快照为 `f8530f4aeb64735dbeae4831f3bc6c315276bb88`；后续运行必须绑定真正加载的源码、DLL与输入，不能把该阅读快照自动当作部署事实。

原始报告与小型收据的真实路径、字节数、SHA-256及证据等级见[evidence/candidate-index.json](evidence/candidate-index.json)。该索引列出10个工作面、34个首批小型证据入口；不重新哈希大原片、不修改原存档、不创建同名历史替代件。原生主题可复用的结论仍回链其专题，Robert历史帧及第3期William录像保留原主体和日期。

## 首批成果分层

| 包 | 静态、源码或旧能力复用 | 本次离线执行 | 本期新实读与录像仍缺 |
| --- | --- | --- | --- |
| P0-TERM | 107个简中/英文key，26份stock文件与GUI入口；“补给容量”可区分“当地补给上限”，月补给、月损耗和月补员费用分开 | 214条原始本地化行及来源SHA复核通过；没有GUI getter执行 | 11项真实tooltip镜头：补给、容量、当地上限、月变化、损耗、补员、停止和锁定；截图未采 |
| P0-SUPPLY | [真实双时钟及先后](../../../docs/ck3-native-ai/army-monthly-update-order-12003.md)已有主线原语；本次补齐集结结束写`Army+190`宽限anchor，`+188`为成功补给更新时间，stock宽限30日 | 本包为exact EXE切片/注册槽位研究。`army_update_clock_v1`已在当前主线，源复用包未新增实现或重跑旧测试 | 实际bucket、stored D、loaded宽限、anchor与成功日期的同帧读数；同军跨真正更新前后的补给与容量截断录像 |
| P0-LOSS | 补给、劫掠、围攻分别产生整数损失预算，实际兵团/record/chunk写回链已静态闭合；行军损失有独立入口 | 指令字节位置核验；没有原生游戏函数执行 | 逐团人数前后、实际结算输入及排除补员/战斗/集结/分合军的窗口；特殊state与行军modifier最终值仍有范围限制 |
| P0-SPLIT | exact半拆复制当前补给及两个anchor，搬移完整兵团ID、重新选新军统帅；[合军继承](../../../docs/ck3-native-ai/army-meeting-merge-supply-inheritance-12003.md)规则复用 | 新有界静态span；没有实际拆军/合军 | 前后两军Army/CUnit/兵团身份、各军补给/容量/统帅；同省占用与离开后的真实当地负担；合军前后值及源军消失 |
| P0-MOVE | 原版`CHaltUnitsCommand`已定位；严格`progress > loaded cutoff`才锁定，stock为0.5；未锁定清路线、锁定保留当前路段并去后缀为静态预测 | candidate02真实submit代码配合mock native constructor/validator/queue fixture通过；Python grammar/advertisement通过。未执行原游戏allocator/executor | 停止、改道、锁定前后连续录像；同军完整路径/目标/驻地/进度后读；原生预期日期与实际到达独立核对 |
| P0-REFILL | 最小`regiment_strengths`数组复用现Strength成员循环，公开每团FullID/current/max/scale1；既有首record补员入口和两项bool原样保留 | 生产reader→serializer→normalizer的8条wire及10项Python契约测试通过；无首record团亦可保留完整actual人数 | 新DLL下完整逐团数组实读；补给恢复与人数两项真实转移。全部persistent records和整军净月补兵预测仍未宣称完整 |

这些等级互不替代。静态确认给出机制与施工入口；fixture证明特定代码在冻结输入下的行为；旧production-live能力只支持其原证据主体；第4期具体数字必须由本期同身份、同日期窗口的原生实读和连续画面支撑。

**调度不是仍待从零研究的缺口。** Regular补员为原生日历月首；补给/损耗由daily callback的stored D无符号模30及实际ArmyManager bucket选择。集结结束宽限、上下文资格和实际dispatch仍控制是否成功更新；正月贡献不保证次月首或“第31天”一定增加。读`+188`成功日期可区分容量满而实际成功clamp与根本未成功执行，不能仅看补给是否变化。使用[当前补给与损耗](../../../docs/ck3-native-ai/army-current-supply-capacity-attrition-12003.md)的现getter，避免重复建设。

**源集成与部署分开记。** `b148719256a92b1d0fe014f9f62f659e44f0d105`已有clock观察；`c30d6b1bcee72c2d7aa40270bd18311a427572d1`为逐团人数增量；`f8530f4aeb64735dbeae4831f3bc6c315276bb88`为Halt增量。本批文件研究不含实机信用，f853对应官方CI失败。原生3目标、16并行构建随后留下`native-build-a02/root-result.json`返回0及`native-msvc-result.json status=built`，其`game_contacted=false`；构建不能替代CI、部署或新实读，最终修复与运行收据由Root另行保存。

## 主案候选与冻结边界

| 候选 | 真实存档与SHA-256 | 已核对身份与边界 |
| --- | --- | --- |
| Jan11已登陆，首个冷载候选 | `C:/ck3-war-episode03-expansion-20261003-a01/checkpoints/checkpoint-landed-a01.ck3`；72,222,213字节；`d94be518cc52fefb62d896de8fabc8bd560f49674925049dab863cef77a1e14b` | 历史William33388、date_raw53147160、War1。Army0已到Lewes1506并围攻，第二军16777220仍在海上；并非全军已经合并的出发档 |
| Jan1海上，替代候选 | `D:/ck3-war-episode03-20261002-a01/vanilla-state-carmy-zero-a05/profile/save games/autosave_1.ck3`；71,837,528字节；`17d98cd24f955dd951be14965502c8ba49856ad8524371430348cd60ecd098c1` | 历史date_raw53146920；可作渡海背景，不能预先声称海上能够分兵或休整 |

两份存档均由主案包各做一次完整SHA核对，匹配冻结源且stat稳定。大raw只核存在与尺寸，未重新完整读哈希。上述日期/Army/围城数属于原冻结报告，新冷载后再次核原生状态与HUD；本期尚未取得新补给压力、当地占用、完整编成或统帅读数。William是否含大量“不使用补给”的特殊部队也要从新提示读实际数量。

先检查Jan11的真实状态和loaded content；若采用全军方案，让第二军依冻结规则正常登陆、正常合军并独立读回，随后新保存第4期append-only出发checkpoint。候选目的地London1527与西/东waypoint都要由新preview验证。**A/B/C最终出发存档SHA、合法路线、休整条件、费用边界与停止条件仍待冻结**；主案包的90%/30日/90日建议只是实验候选，没有作为已经执行或最佳策略记账。

## 预计拍摄字段与采样点

每个需要解释状态的暂停点保留原始packet与各自revision/date：

- 运行身份：exact build/EXE、源码/DLL、run/session/generation、加载mod/DLC feature manifest、出发存档SHA；人物、战争与全部己军FullID。
- 军队身份与位置：public CUnitID、native CArmyID、commander、province、state、combat/siege/gathering、完整stored route与目标；逐团FullID/current/max及数组覆盖情况。
- 后勤原始量：当前补给、容量、当前月贡献、损耗raw/scale；当地原生上限、占用/来军负担；同省分兵不自动把总负担减半。
- 时钟：stored D、selected phase、pointer-match的actual bucket、`+188`成功更新时间、`+190`集结anchor、loaded宽限、当前日期。以actual membership观察，不以ArmyID模30替代。
- 行军：当前路段Q100000进度、剩余duration、loaded lock cutoff、下令前预期到达、当前ETA、停止/改道后完整route、真正到达省份/状态。
- 补员：actual逐团人数与可用的first-record persistent/chunk身份、两项原生bool和fraction各自保存；不要AND或聚合为未经验证的整军预测。
- 财务：全玩家金币余额、NET/current-vs-all-raised维护率、实际事件与单次登船支付前后。净余额差、当前费率、实际支付分列；缺流水时不称累计行军军费。
- 画面：当次原始截图尺寸/SHA、连续raw SHA/PTS、动作marks与clean span，保持同帧人物/军队/日期来源。game ACK、录制ACK与SDK-ready不充当结果画面。

采样点为出发、实际分合军前后、路线下令与生效后、停止/锁定边界、实际补给/兵数跳变、登船或财务事件、真正抵达，以及三个回放的共同游戏日期。三臂分别新userdir/pipe/run，来自同一新增冻结出发档；随机事件及敌军行为差异原样保留。

[费用当前量专题](../../../docs/ck3-native-ai/war-cash-current-resources-12003.md)已有同帧production-live原语，可直接复用，不能把Robert值叠到William。现query未给区间军费流水或逐笔登船支付；1.19登船quote仅为历史研究线索。需要精确支付主张时补紧邻真实支付归因，否则只报该回放净余额变化和当前月维护。

## 六项最小门槛

这是既有六个P0进入本期核心口播的证据门槛，不扩成新的平台或全量枚举要求；全部目前仍缺本期画面，静态/fixture进展见上表。

| 门槛 | 最少必须闭合 | 当前剩余 |
| --- | --- | --- |
| G-TERM | 当前简中原生tooltip与单位，key/GUI入口/截图同主体绑定，英文副字幕按key核对 | 11项待拍；容量与当地上限分主体，损耗与地图伤亡分场景 |
| G-SUPPLY | 同Army更新前后补给/容量/monthly raw、真正dispatch与loaded资格，至少一个可解释的实际变化或成功clamp | 部署现clock并采当前边界；没有成功日期时不把零变化解释成clamp |
| G-LOSS | 完整actual逐团前后与当前输入，连续窗口排除或单列战斗/补员/集结/编成/事件 | 新因果窗口未拍；排不净时只记净兵员变化，静态预算不当死亡实测 |
| G-SPLIT | 同日真实拆分、两侧完整兵团集合/补给/容量/统帅及后置；移动、会合和合并分别记录 | 新实机未执行；数值合军算例缺native权重时不由public总人数补造 |
| G-MOVE | 未锁定Halt、锁定保留当前路段且去后缀、改道和实际到达的独立后读与连续镜头 | Halt CI修复/部署/新实读；单一剩余路段拒绝不记作provider失败 |
| G-REFILL | 当前补给与完整actual人数各自前后，展示可观察的不同变化；若声称补员原因另绑定其执行/对照 | 新逐团数组实读与变化镜头；全persistent record和全军预测保留质量缺口，不阻核心区别说明 |

实际开机前仍遵守唯一屏幕租约、当次新鲜Steam离线、真实加载输入和正式run身份。Root已直接审过challenge-a03的新nonce及“离线模式”，但原背景时钟stale/Steam内容黑区仍记录边界，不能写成桌面全面恢复；上线前重新取得新鲜证据。辅助runner的`life-advance`必须核实际raw增量，出现非24增量保留RED而不伪装每日样本。

## 并行拓扑、后续与报告口径

本轮拆出术语、补给时钟、损耗、分合军、移动、补员、主案、费用、capture和环境工作面；CK3/SDK/录制由Root单协调者串行。clock确认已有主线原语后停止重复实现，切换为源码复用及paired-JSON解释配方；逐团人数与Halt为当前拍摄缺口的最小增量。原片、失败候选、环境RED、编译输出及历史输入保留。

本批`open_kaishek`步骤逐项判为not-applicable：处理compiled native ABI、stock GUI/localization和进程/SDK包装，没有该parser/finite runtime可替代的执行语义；各包保存实际理由和可取得的commit/profile，未凭不存在的历史盘位制造模型或CK3 RED。

本批并行文件研究线程新增SDK查询0、新游戏日0、新录像0；这些是文件包统计，Root之后的运行另列，不合并历史Robert或第3期数据。M1研究与案例工作正在推进，M2尚无A/B/C媒体验收，M3–M5未新增完成信用。**不设完成百分比：当前包没有正式加权分母，静态链和fixture不能换算成已拍摄或视频完成比例。** 下一步为CI修复与严格运行输入冻结、当前主案冷载读回、六项P0实拍、同档A/B/C，随后冻结全文与音频。

工具链最新正式版已在当次查询核验为v0.2.1，wheel SHA `f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621`，主venv Python3.14.7的实际版本/help已有收据；新run仍遵守届时最新正式Release规则。当前没有影片、人工1×完整signoff或OneDrive交付信用。

## 当前小型回执位置

下列为本机真实绝对路径，作为证据定位文字；所有仓库超链接保持相对路径。完整SHA在[evidence索引](evidence/candidate-index.json)。

- `D:/ck3-war-episode04-research-20261004-a01/{terms,supply-clock,split-merge,move-control,refill,case-selection,costs,capture-runner}/`：各并行包，目录不当作完整验收结果。
- `C:/ck3-war-episode04-research-20261004-a01/{loss-cause,refill/implementation-a01,move-control/focused01,supply-timing}/`：当前切片、offline fixture和现clock复用收据。
- `C:/ck3-war-episode04-research-20261004-a01/native-build-a02/{root-result.json,native-msvc-result.json}`：f853原生3目标16并行构建收据，无游戏接触。
- `C:/ck3-war-episode04-research-20261004-a01/steam-offline-root-review-a01.json`：challenge-a03直接审图及仍有的画面边界。
- `C:/ck3-war-episode04-research-20261004-a01/toolchain-check-a01/completion.json`：当次最新wheel、SHA与CLI验证。

本文件与索引的入库、push及exact SHA官方CI由Root独立收口；本候选组装包没有操作Git ref，也未声称本身已提交。


## Root运行追加（2026-10-04）

原生三目标严格构建完成；f853隔离测试失败为既有clock依赖遗漏，补齐其translation unit后本机原fixture通过。正式CI修复尚待本次提交复核。Root随后分配 `desktop-3fevhd2-1c74096080--vanilla--R0161`，在独立 `state-main-case-a01` 加载精确Jan11源存档。SDK于14:28:31UTC初始化；14:30:39首次地图snapshot尚不可用，保留loading原始错误，未推进游戏或录制。运行入口 `C:/ck3-war-episode04-research-20261004-a01/native-live-main-case-a01/`；这段初始化不为六项P0增加完成信用。


## R0161实际研究与首段原片（2026-10-04 15:23 UTC追加）

本节更新前文初始阶段状态，保留其当时事实。Root已在独立vanilla profile完成本期首次实机；人物William33388，CK3 1.20.0.3、冻结source f853及DLL完整SHA绑定，[证据索引](evidence/r0161-index.json)保存原始packet路径/尺寸/SHA。正式CI依赖修复fe3247e已在[run37209736858](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37209736858)通过。

| 工作面 | 本次新增实际结果 | 仍缺 |
| --- | --- | --- |
| REFILL | 两支可用军27条actual逐团人数，SUM与原生整军5660/5660、1086/1087一致；缺首record仍保留actual人数 | 实际恢复补给与实际补员变化窗口 |
| MOVE | Army0下令London后有完整四跳route；未锁定Halt后独立snapshot确认同省、route complete_empty、target null | 锁定停止、改道及实际抵达；非县战争目标1513的preview接口未受理，不能用失败作路线结论 |
| SPLIT | 同日实际拆成2540/3120人；13团disjoint完整union且每团人数未变；同省1506原生usage仍5660/limit3680 | 分省、实际统帅读回、会合与真实合并后态 |
| SUPPLY | 新public170/native161复制原+188/+190，实际manager bucket11；主军bucket0 | 新军+6日、主军+25日仅为条件dispatch预测，实际成功更新时间变化未见 |
| TERM | 当前ArmyUI真实调用返回capability_not_available，已定位最小当前版本SelectUnit/GetArmy/GUI可见性ABI并施工 | 面板和11项tooltip拍摄 |
| 费用 | 合法CUnit0被Python拒绝的真实错误已定位并修复；两项回归及9项focused suite通过 | 新绑定runtime的William NET/current/all-raised实读；原失败body=null |

原片 `C:/ck3-war-episode04-research-20261004-a01/recordings/main-case-mechanics-a01/raw.mkv` 为2,514,097,740字节、SHA `4fd4af5ba5a2dcfc50e00a7e49885cc1b6bbeeabe03b4690888abc5ac6d40cd6`。录制实际26:26.500、1920×1080/30fps；正常结束exit0、Job进程树空。完整47,595帧及packet的媒体探测均通过，时间戳严格递增；这段包含暂停研究和机制操作，尚未划定clean spans，也未做1×人工成片审阅。原片时长不等于正式影片完成。

本轮游戏日增量0，A/B/C共同出发档仍未冻结。下一独立attempt先补Army-only原生面板接口及费用新读，再以真实日期边界采供给/损耗，并等海上军自然到达、正常合军后冻结三臂共同checkpoint。B必须记录新军统帅与容量变化；不得把当前6746计划人数当将来合并实际人数。

15:14 UTC受管SDK已退出，CK3/录制进程树空，原1024×768显示模式已恢复；15:16:49新nonce画面直接确认Steam“离线模式”，15:17:29 CAS释放屏幕。原Robert战役、第3期原始存档和失败attempt均保留。原生UI实现、独立日采样方案、ABC共同起点准备与媒体验证并行推进；只在新live环节重新取得排他屏幕。全文/TTS、正式成片、人工签核和交付均未新增完成信用。


## 2026-10-05：R0162 实验与录像增量

本期第二个受管冷载使用原始检查点7f766a68…（实际完整SHA见索引），运行Python dba795、DLL编译2db29c且native C++字节相同，exact CK3 1.20.0.3/25652598。费用/普通省typed移动/拆军已实际读回，Army0合法fullID保持。+5进度0.60时，两次Halt均只保留first edge1513，中间改目标1526也保留当前段。+6 child supply82.99737→74.22545，自己的+188 stamp更新，兵员3120→3089；+9 main实际到1513/空route，stock/stamp未变但人数2540→2413。两类扣兵的具体源链与端点推断见[新专题](../../../docs/ck3-native-ai/army-episode04-periodic-and-county-arrival-loss-r0162.md)，不得统称饥饿或死亡。

原版Army面板在后续regular1案例实际可见；Root审图2413、0%、82/100下降。初始sieging3时的hidden、首次加载map未ready、旧public版本拒绝与首次读取partial-JSON消费者竞争均保全，不转GREEN。最后一次短脉冲pause收到`CK3 map state is unavailable`；首cleanup snapshot证实仍在运行。Root处理延迟造成采样空窗，独立紧急pause最后证实raw53149272（初始+88日）。最后有效连续样本仅raw53147688（+22日），不能声称整个30日控制计划通过、已观察第25日主军结算或用最终端点填补空窗。旧+6/+9配对证据保持各自已核scope。暂停恢复正在最小MCP接口线研究，不用桌面兜底。

第二原片2474390796B/SHA d2e1c49ee21aafc52af16559e951581f255d403fbff42b629577708cddfe3c41，实际28:29.666、1920×1080/30fps、H264/yuv420p/无音频，51290帧与packet完整解码/时间戳PASS。此为含暂停研究及失控后段的原片；加上第一原片26:26.500也不等于30分钟成片或可用动态镜头时长。SDK线程/keeper/CK3/recorder均已退出，Job树空、显示恢复1024×768，fresh Steam离线原图审阅后CAS释放屏幕seq4436。

证据见[本期R0162小索引](evidence/r0162-index.json)。仍未完成：十一项真实概念tooltip、正补给恢复与兵员补充区别案例、actual合军供给/容量截断、同档A/B/C出发与三完整回放、累计支付/路线代价、全文/TTS/成片/人工1×签核/指定最终MP4交付。主军当前month−5，不能先许诺休整恢复；B地点需actual正恢复条件。提示框候选只有static/offline，GUI epoch与实机文本像素信用另取。


范围校正：same-province preview-main-current-1513-a02 为 accepted=false/statusdeferred、move_mode_unavailable，没有当前 province_supply；+9在1513的当前limit/usage及underlimit仍待证。Jan11 ordinary target1513 limit2880/usage0只属于早先帧，不外推后续。可说stock82.99737/month−5/attr0，不能以此生成“当前低于上限仍不恢复”的单变量反例；另案验证友方资格与实际正恢复。第三军16777220在+15净−10另存，全军变化不止两次。


## 2026-10-05 下一次GUI-only冷载准备

R0162 postovershoot保存已真实物化：74405700 bytes，SHA-256 `208a52733662769c9675cef11ebd53c1520fc8d2efb2c6bd6ef2bc6e3b53d73d`，actor33388/date53149272。它仅作提示框画面观察，不能作为A/B/C共同起点或弥补+23至+88的观测空窗。原保存使用真实 `ck3_execute_step` 的 `save-checkpoint`；bootstrap现在兼容该调用与既有 `ck3_save_checkpoint`，仍检查saved状态、原profile路径、bytes/SHA、actor/date、pure vanilla lifecycle与exact build。保存DTO不携带paused；另以独立paused snapshot绑定，重载后还要新读paused/alive/noevent。

最小兼容patch及15项offline fixture PASS保存在 `C:/ck3-war-episode04-research-20261004-a01/capture-next-r0163-plan-a01/bootstrap-save-compat-a01/`，patch SHA-256 `083a47f00f1fb6d3f0a2a9667b37437ae2069d9e8e82747050ad484f162e0e1d`。此包只改变保存receipt准入；没有执行游戏、SDK或屏幕动作。


## R0163：暂停GUI提示框尝试与第三原片（2026-10-05T02:36:56+08:00 资料编制）

本轮是GUI-only受管冷载，人物William33388、exact1.20.0.3，Python冻结dbab/native-build-a05（编译36a，DLL5,234,688B/SHA63f30d…56fd）。加载的74,405,700B、SHA208a5273…d73d保存输入对应R0162最终+88日端点；即使名为episode04_frozen_start，也没有A/B/C共同起点资格。初/末snapshot及语义样本date_raw53149272、paused=true，实际新增游戏日0，不能再次加88日。完整身份与回包SHA见[R0163索引](evidence/r0163-index.json)。

Supply与attrition各一次hover只得到acknowledged_verification_pending；随后query均为tooltip_active_stack_unreadable_or_out_of_bounds，active_count=null、active_stack_read=false，leave均为tooltip_leave_requires_hover_receipt_or_observed_root。Root直接审过对应截图，只有Army77/100与0%标签、Lewes地图tooltip，未见Armytooltip。原始ACK不等于已读取或已呈现提示框；现有证据不能证明地图提示覆盖了Army提示。实际栈cap/count仍未知，TERM与十一项概念tooltip没有新增闭合信用。

第三原片843,481,703B/SHA a34a780ac5b5c949f9b97d060d4ef0c7e20b04ff63e095cd56c45b33381dc68d；565.233秒、1920×1080/30fps/H264/yuv420p/无音频。完整16,957帧与packet时序自动媒体PASS（报告9361B/SHA733ec8e1…42f41，索引8135B/SHA7ae57c19…7c06）；只授该原片媒体资格，不授TERM、clean spans、成片时长、人工1×签核或影片完成比例。原录制finish收据的media_probe_pending保留为当时状态。

Root误调用stop-session产生Unknown tool，原错误保留；正确stop随后成功，bootstrap独立证实SDK/keeper线程退出、CK3和recorder树空。1024×768显示恢复，Root直接审阅新的Steam离线图，CAS4491实际done/resources[]。CAS之后heartbeat参数被parser拒绝不改写CAS成功；本脚本过程输出保全。实际bootstrap位于native-live-army-tooltip-r0163-a01/bootstrap-result.json，launch-gui同名路径缺失不是SDK/游戏失败。

后续修正只处理cap误拒绝并提供实际cap/count诊断，尚属static-only、未新live。下一轮独立绑定真实栈/当前root/文本刷新与像素；不要按旧ACK补造Tooltip成功。正补给恢复、补员、actual合军、同档A/B/C、全文/TTS及成片/交付仍按原缺口推进。[Army UI专题](../../../docs/ck3-native-ai/army-ui-selection-window-12003.md)保持R0162已验范围和R0163失败各自身份，不覆盖历史。


## 2026-10-05 R0164 收口：正补给实际闭合，整数补员仍待证

这是对上文历史pending切点的追加更新。[本期R0164索引](evidence/r0164-index.json)绑定exact1.20.0.3、fea65ebb/a06、原始7f Jan11及新episode native-33388-18dbe3e6ac0a。实际暂停初末raw53147160→53147520，共15新游戏日；与Robert长期控制loop、第3期及R0162空窗不合并信用。

正式positive-pair-a05实证：同一CArmy16777220第14→15日仍在2174行军（route[2327,2325]），补给291.22808→300/capacity300，current monthly+15.61404；+188成功更新日期53146800→53147520。净增8.77192符合当前容量截断。完整14个actual兵团人数向量及24条raised records前后相等，总1086/1087、53仍9/10；当前补员权限true及比例不当整数补员正例。当前全roster为[0,16777220]；独立post只请求Sea subject，未冒充sampler全roster。详细边界回链[补给专题](../../../docs/ck3-native-ai/army-current-supply-capacity-attrition-12003.md)与[补员专题](../../../docs/ck3-native-ai/army-regiment-replenishment-raised-reserve-12003.md)。

day15独立preview的current2174 limit4960/usage1086与target2325 limit3840/usage0各保留role；target未抵达值不能当抵达后用量。将领27357在day15再读，day14未独立再读；CArmy+0xC0 raw flag没有由Strength DTO发布，capacity300不能反推flag。

Root直接审阅四张精确PNG：末帧面板1086人、补给300/300、HUD1067Jan26；补给和损耗尝试仍显示Argentan地图tooltip，实际query=source_null（cap1/count1/hovernull/index0）。这是实际失败状态，hover ACK不代文字/像素；十一术语门槛继续pending。

原片1327000997B/SHAba74579ca20d996bb9b78774c229223fc147638503b9327cbd3189212d0bdc01正常finish exit0/Job0，900秒1920×1080/30fps，完整27000帧及27000包时戳严格递增，前后SHA稳定，媒体审计PASS。Root PNG authority SHA938e5f27be4f9dff0dc8e08a7d3ef59a904d3eeb9433f687f3570b44b06c1ed3与raw时码绑定为null；不以UTC推测覆盖stock增长画面，0自动clean spans、0全片1×审阅/approval。第二次recording-start被one-recorder合同拒绝，未启动第二段，publication退出0不代业务成功。

actual day15 save72775729B/SHA2255db3e442650afac51e4e5d75bea7ed9864a90e3b4d1d96de243ef6dd7257f、同SHA immutable seed及保存前后paused/map_ready身份保全。SDK线程退出、CK3/recorder Job空、屏幕资源CAS释放，Root直接审阅新的Steam离线关闭图并恢复1024×768；这些为R0164历史收口证据。后续独立R0165只续余15日、总end53147880，实际证据另记，不是A/B/C。

仍需十一tooltip、实际整数补员、actual merge、同档A/B/C三回放、累计支付/路线代价与全文/TTS/成片/1×签核/指定视频交付。本例闭合库存恢复与人数未增长的区别，不清空这些门槛。权威总账没有正式加权分母，研究完成百分比保持null；900秒素材不能换算研究或影片完成百分比。


## 2026-10-05 费用口径勘误：旧月 NET 实为月总收入

**本节纠正前文费用口径，原始事实和历史文字保留：旧 `.3` `player_monthly_net_income` 只读 `2BCA960`，实际是月总收入。** [费用原生专题追加勘误](../../../docs/ck3-native-ai/war-cash-current-resources-12003.md) 逐项说明初始 “already net” 合同、Robert `+3.57546` 与 R0162 William `+4.69417` 三处旧解释。R0164 Jan11 的 `469417` 同为收入侧，不能标为已扣全部支出的 NET；各帧金币余额、current/all-raised 维护保留其原先已验范围。旧原始 payload/录像/文档历史均不重写。

Exact1.20.0.3 静态原版 HUD 链为 `28BFDA0` 返回 ExpenseContextCharacter，`2BCA960` 收入与 secondary 输出，`2BCB180` 完整支出（包含军事，按原版 false/nil 参数），再做 signed income−expenses；缓存净额 getter无除30。原版显示月口径有 GUI/本地化和实际 writer 证明；没有同帧完整支出采样，不能用 HUD `+0.2`/`+0.3` 与旧收入的数学拟合建立每日率或跨日期的精确对账。

最小 source 候选保留现有 NET 字段，增加 gross/total 可审输入和 exact `.3` 语义标记 `ck3-1.20.0.3-native-income-minus-total-expenses-v2`；失败与 signed overflow 为 null/明确原因，合法零仍是0。无标记历史 packet 不取得新 NET 信用。当前只完成外置生产 reader/serializer/fake-bindings 严格构建、六份实际 wire 的注册 in-memory MCP合同、8项 Python合同和 focused CMake/CTest；源码集成、新 DLL、实际暂停净值读取仍由Root另验。提醒前新路径 test EXE 运行缺少 Defender 排除回读的流程缺口已记录，之后停跑并交精确 CMake target 待登记；没有自行提权或扩大排除范围。

R0165 使用旧 a06继续独立兵员采样时，只消费已确认金币余额，旧 NET 禁止用于费用计算。P0-TERM11、同档 A/B/C、登船实际付款 ledger、累计行军代价、影片/TTS/完整人工签核与交付仍按各自证据闭合；本次静态费用修正不提升这些门禁或影片完成百分比。净额、维护月率与实付流水必须分开：只在新的 true-NET 字段已验时说明军事支出已包含，不能再扣军费一次。


## 2026-10-05 R0165 收口：实际整数补员与四项术语PNG

本节更新前文历史pending，保留所有原始append和费用勘误。[R0165索引](evidence/r0165-index.json)绑定fea65ebb/a06、William33388、新episode native-33388-c6f1ef2b4089/PID19360/connection1，由actual day15来源SHA2255独立冷载，paused初末raw53147520→53147664，真实新增6日；原Jan11计划共21日，总end53147880不变、尚余9日，未完成整30日，也不是A/B/C。

P03严格相邻004→005（原+20→+21日、native23/public24→native25/public26）取得整数补员正例：同Sea完整14个actual团仅53 current9→10/max10，全军1086→1087/max1087，其余13团current/max不变。全24physical records已核，只有目标人数/effective增长，但23条prepared刷新，不能称所有records不变或23团增长。独立完整玩家postread再次同native25/public26/date53147664重合人数及records；最终保存后全玩家[0,16777220]三读同native26/public27/raw53147664、paused/map_ready。Sea仍2327/moving7/route[2325]，不是抵达2325后休整；stock/cap300/300、month15.61404及+188日期53147520在这个补员窗口均未变。

结合R0164“补给回到容量而人数未增”，现在本期已实际观察补给与兵员两项独立变化。两次run及边界必须分别标注；整数正例不等于整军净月补员公式、完整恢复策略或损耗因果验收。actual +21 save72936215B/SHA3c841cbc7585989c2334392697608a600907dc2fd615f992a59b7d55abee5bb0、同SHAimmutable seed与新外置checkpoint均保全，保存前后暂停身份和复制receipt绑定。

P0-TERM当前原图覆盖TERM-01/02/05/07，共4/11：补给300/300、当地1086/4960、+15/月及实际breakdown；损耗零值0%/0月与Army0围攻1%/−56月；当前移动3天/Feb4；停止移动H。Root直接审阅原始PNG及五个实际encoded中心（107.167、195.3、1617.767、1705.6、1744.767秒）。平分只有警告PNG，合并部分与其他六项整项未完成，完整剩余为TERM03/04/06/08/09/10/11；平分PNG超过actualraw范围不绑定，当前移动日期不当实际抵达。

30分钟raw2949921171B/SHA6ee0a20cb16b46c74902fc281b107c451205a49584b354db74a846ae3bd13f31正常finish exit0/Job0，全metadata/54000frames/54000packets及strict decode均PASS、零时间戳缺失/相等/回退、零解码错误、1920×1080/30fps/无音频。媒体报告SHA0712dc942341f6fc94e0b13a46955f4966082204cab31b7e32ca9f5fc15a7f5b只授机器媒体条件，Root五帧authority只授这五帧；clean_spans_certified、完整人工1×及film signoff均false，原PNGraw时码保持null。两次typed tooltip cache的hoverdifferent/topbound/locked1拒绝继续保留，不被像素成功盖过。

关闭流程保留一次Unknown tool:stop-session失败，再由实际stop工具请求收口。launcher返回0，SDK与keeper退出；CK3实际exit_code=1，Job0/tree_gone/cleanup_proven=true，不能改写成CK3 exit0。屏幕CAS已done、资源空，1024×768与Steam原rect已恢复，Root直接审阅新离线footer及01:35:11/nonce5d56a225c5e5关闭图。

费用新source ffc29已有income−total expenses修正，但本轮运行a06旧NET仍实际月收入，禁止作净额计算；只消费已确认余额。新的DLL与exact true-NET实读、实际支付ledger仍另验。剩余核心包括七项完整术语、actual merge、同档A/B/C共同出发档与三回放、路线与费用边界、连续可用镜头、全文/TTS/成片/完整人工审阅及指定视频交付。

当前调度粗估为整体约30%、研究约70%，术语PNG4/11约36%、ABC0/3、影片制作0；这是Root向用户说明的规划估算，**正式研究加权完成比例及分母仍为null**，不由素材分钟数推出。Oct5（Asia/Shanghai）12:00–15:00补研究、18:00–22:00拍A/B/C、Oct6下午/晚间Review01是目标，尚非完成事实或保证。
