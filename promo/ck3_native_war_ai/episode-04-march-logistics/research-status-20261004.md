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
