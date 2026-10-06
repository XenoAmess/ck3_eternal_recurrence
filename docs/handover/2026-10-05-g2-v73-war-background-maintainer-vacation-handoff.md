# G2 v73战争与后台研究：维护者休假交接（2026-10-05）

> 最新本机权限（2026-10-06T09:18:05+08:00）：用户要求这台Z机器不启动CK3，继续后台研究；其他机器照旧。下文旧游戏授权与PID均为历史。本机最新保存h9586/5996日，新g82修复仅static-ready，完整恢复材料与本页末尾增量保持可查。


> 后续授权更新：接手用户要求“不要开启ck3，我自己要玩。你先只做后台能做的”。当前以 [后台接手施工](2026-10-05-g2-background-successor.md) 为准；本页下述 CK3/界面恢复授权是交接时历史，不代表接手阶段可以操作游戏。

**接手先读本页。用户已重新允许本机使用CK3与界面；无需为解除先前用户游玩暂停再询问。自动任务最后实测并保存到5035天，R0046已正常退出。本次仅整理并提交交接，没有重新启动/attach/输入/查询游戏，也没有构建或运行候选。**

实际整理登记时间：2026-10-05T18:41:11+08:00（Asia/Shanghai），这是登记时间，不倒填用户发言时间。完整目标仍是原普通Robert战役的长期自动游玩，战争/战斗研究与有用功能交付并行；不是把本轮八份research当作终极目标完成。

## 1. 最新授权和执行原则

- 最新用户原话：**“你现在可以使用ck3和界面了。用吧。我去休息了。”** 随后要求本维护者休假、由同事接手并把交接放入docs。此前“用户自行玩数小时，直到下次明确授权前不操作实机”的暂停已被这句授权解除。[旧用户游玩交接](2026-10-05-ck3-user-session-and-autoplayer-resume.md)保留历史并已加当前授权说明。
- 战争、战斗及宗教全面开放。用户10-03勒令撤销任何非战约束，规则与prompt清理已完成；不得恢复nonwar-only/war OFF或借旧交接停止战争。历史OFF和零动作仍只表示当时事实。
- 维持尽可能高的**有用并发**、尽可能少占窗口。用户资源为8个M和最多64个并行槽。本轮8个owner、按必要性各1–2条小文件子线已收口；接手可按表中互不冲突工作包重新铺开。一个执行者持有本机游戏、SDK与源码整合，多个后台owner消费各自缓存/投影；不为填槽派生重复审计。
- MCP-first，状态由原生查询与独立后置确认；ACK不等于操作成功。原生树先于counter-policy，exact-build绑定；不要因观测缺口循环说unknown，按下表明确入口补读口。单台机器CK3启动排他，保持Steam离线、最少前台操作；正常检查仍按当前AGENTS与本机operator合同执行，不新增门禁或重复已验收检查。
- **Robert Character29829原普通战役是唯一测试入口**。不换fixture、新人物或新开局来赚进度；游戏日、战争胜利、primitive/loop/complete分别记账。当前授权不改变玩家限定、版本绑定与实际证据要求。

## 2. 源码、运行冻结与证据入口

| 用途 | 确切入口与状态 |
| --- | --- |
| 主仓与用户现场 | `Z:/ck3_mod_rewrite`；原现场有用户/其他任务改动，本轮没有清理或覆盖它 |
| 本维护者整合树 | `Z:/g38`；本交接及知识/报告由该隔离树提交、普通push到origin/master；接手先fetch/rebase最新master |
| 最后运行冻结源码 | **`Z:/g78`，HEAD `d22e9a1cd3fb1062f6c66282f044daafa016718a`**；native与Python同冻结，不在此直接改实现或文档 |
| 游戏exact build | CK3 **1.20.0.3 / Steam25652598**；EXE SHA-256 **`94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`**；文件名里的12002不能替代实际ABI绑定 |
| 原生研究冻结EXE副本 | `Z:/ck3_mod_rewrite/artifacts/migrations/2026-10-02/installed-build/binaries/ck3.exe`；复用已有pin，不重扫或重新hash整EXE |
| 最后runtime | **v73**；`Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/runtime-preparation/v73`；DLL/injector在`binaries-v73` |
| 历史环境哈希 | `20ba8b4f1c4e99c6575a0029adf17ea4cae5e492a5a516fc7fc3b234768a7cbf`；新恢复另绑定当次实际输入，不能投影旧环境为当前 |
| 隔离普通战役state | `Z:/ck3_mod_rewrite_process_assets/g2-robert-mainline-12003-v73-20261005/state`；与用户普通游玩现场分开，不把用户玩过的天数记到自动任务 |
| 运行/停止证据 | `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261005/ROOT-CK3-USER-RESERVED-RELEASE.json`；该文件的旧授权暂停已解除，正常STOP/关闭事实仍有效 |
| 历史部署链 | v73下`ROOT-ACTUAL-V73-DEPLOYMENT-DELIVERY.json`、`rebind-cold/ROOT-DEPLOYMENT-RECEIPT.json`、`ADOPTED-V73-RUNTIME-FREEZE.json`、`RUNTIME-INPUT-BINDING.json` |
| 本轮后台交付根 | `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261005/background-user-session-round02`；八包详见[小包索引](2026-10-05-g2-v73-handoff-packets/index.json) |

最后实际run：**`xenoamess-full-tower-eb9d2c1186--eternal-recurrence--R0046`**（旧别名R46），execution `d78a26cc-923a-411e-bfda-35221beec816`，历史PID104164、managed47337。北京时间 **2026-10-05 15:22:48** 已观测CLOSED0，最后SDK83619也是CLOSED0 GREEN。历史部署receipt早先的ACTIVE/PID/pipe/public revision均已过时，不可当作当前会话。没有要继续poll的SDK或构建session，也没有待交给同事的本轮实机锁。

v73全量strict64四target `/W4 /WX` **GREEN，86.837956秒**，579 TUs、576 unique、1137输入；exact源码官方CI **37269932921 SUCCESS**。直接复用这一次证据。本轮只改docs并保全小包，不再次构建、编译或运行旧测试；新的代码整合应验证新增路径一次，并按实际冷载结果更新资格。

## 3. 最后正常保存与真实战况

累计 **5035/36524正常保存日（约13.79%）**，resume1882，10-05增377；G2 **5/8**、NW2 **2/4**、自然继承0。此计数是冻结历史，交接过程新增游戏日0，不是整体项目完成百分比。

| 保存 | raw date | 大小 | SHA-256 |
| --- | --- | --- | --- |
| 最后六个正常游戏日的whole-save **h9048** | 53265168 | 99036288 B | `9354912f261fca203aeda8e0cedaef6c5b579c210444556faefc590233db783d` |
| 末零日查询后的normal-save **h9052** | 53265168 | 99036288 B | `e0a7fb224723c62296a60ce6683c7b7f2e7614a6d6536e6a3ab8cbf2a5840cec` |

两保存同日；h9052查询不多算四天。恢复优先基于最新正常h9052，与last whole h9048分别保全。episode历史 `native-29829-2bc2d599f7f9`。不要直接重跑仍锚定**h8938**的旧v73 prepare/recovery packet；它是已执行部署过程，不是新的恢复指令。v73 `root-results/v73-current8938-01/ordinary-rebind-01-argv.json`可帮助理解既有agent入口和state绑定，执行前生成面向当次保存/版本/revision的正式输入，勿照抄旧endpoint。

冻结时470已由Robert占领，围城结束；**War117440524 active，分数38**，还没有全战争胜利或结算。三自军同帧无Combat/retreat：

| public CUnit ID | 最后状态 | 当前兵力 | 有效未完成事项 |
| --- | --- | --- | --- |
| 主军301989997 | moving，在470，route `[3717,3711]` | 2407/3873 | 首边getter20.84832h，不是完整route ETA |
| 器械268435481 | moving，在3717，route `[3711]` | 8/11；mangonel7/10 tier2 | 当前边146.66664h；尚未实测抵达3711或贡献K |
| 守军184549452 | sieging，在3711 | 2883/3000 | 3711围城继续，尚未占领 |

3711 siege：work **24279868/55000000 =44.145%**，remaining30720132，ETA319是估计；B2883/G500/F6/M85800/**K0**/D96432，breach0/CanStartAssault false。器械军同省还须完整native参围资格；原生源码没有必须先合军的条件，不能把未到场包装成强化。

独立军力查询末帧native140/public2/raw53265168/queryseq5：主/器械stock300、月+20、attr0；守stock81.81820、月−4.54545、attr.01、lossbudget28。主/器械六日分别净增360/+1，守净−29；旧prepared全0已过时，当前主28/器械1/守0/敌127。预算28不能解释净−29，端点变化不还原逐项损失/到账日。

远方敌方Combat **369098771 @4893**，main day16、未finalized、winner−1；敌2846/4702，实际新defender16777766 owner32313已attached，234881391@735不在参与集合；resolved advantage+3、width1342。只读实际敌battle transition可以查该战；enemy control因ownership被拒的旧RED保留。没有完整Entry/未来battle/MC/胜率信用。

既有有限loop包括470攻占、主/器械正常移动及此前玩家防御胜利/首都2619解围，证据不可重复赚取：见 [470捕获与调动](../ck3-native-ai/episode03-assault-capture470-stage3711-1.20.0.3.md)、[强攻完成日](../ck3-native-ai/siege-assault470-capture-live-loop-12003-2026-10-05.md)。**玩家首都是2619/县2142；2640只是县2115头衔首府**，旧误标签已纠正。

## 4. 八条后台研究：已知结论、最短施工和边界

本轮八包均为 **research**。所有实现/纯计算/reference候选都在外置目录或压缩交接小包，**未应用生产源码、未编译/测试/导入/执行，未授static-ready或新live**。源知识已分别入库；不能仅因source-closed就升级功能资格。

| 工作包与知识入口 | 已闭合及接手下一步 |
| --- | --- |
| [完整路线ETA](../ck3-native-ai/army-current-movement-progress-observer-12003.md)，`movement-eta/ROOT-DELIVERY.json` | `ReadCommittedRouteTimeline`已有完整route provider；在日期舍入前保留signed Q100000 prefix durations及final remaining，挂既有行军query。active base0，24AADA0已减current progress，不再扣一次。contact wrapper要求非空完整敌军集合，不能当通用无敌军ETA。 |
| [器械到场参围](../ck3-native-ai/siege-efficiency-inputs-12003.md)，`siege-engine-arrival/ROOT-DELIVERY.json` | M/K/D遍历实际Province CUnit occurrences，完整资格`2C16690`已闭合，独立eligible军可贡献，无leadArmy等值/必须合军；K/M每调用现算，无额外刷新动作。最小增量为occurrence/public Unit/nativeArmy/eligible bool/qualified ArRg IDs，复用库存与K/M/D。 |
| [chunk数值补员](../ck3-native-ai/army-regiment-replenishment-raised-reserve-12003.md)，`replenishment-numeric/ROOT-DELIVERY.json` | q按chunk maximum×prepared，与缺额封顶后整数trunc0；不是whole regiment cap。现有字段足够，保留32/64位原生算术、有效状态和native0/true。外置纯候选未运行，未知真实F不报数、不预测下月。 |
| [损耗分配](../ck3-native-ai/army-attrition-soldier-writeback-12003.md)，`attrition-loss-model/ROOT-DELIVERY.json` | Supply先分配、siege+raid再使用post-supply current，stored order/资格/剩余budget和total/IMUL低32/IDIV trunc0已闭合。候选只给writer requests；`2657EA0..2657F0E`最终setter仍未闭，不能说已算最终兵数。 |
| [首次接战人物构造](../ck3-native-ai/battle-first-contact-person-preparation-frontier-12003.md)，`battle-entry/ROOT-DELIVERY.json` | `291C255→24DFB70`88B只读AL谓词闭合；Army120!=-1时比较第二object174，true才合provider1640权重100000。补同query `current_context_source_inputs.pre_291e210_1640`及两registry bindings，按291D1D0→1640→A→B正确源阶段组合；current final不能当baseline。 |
| [实际战场geography](../ck3-native-ai/combat-simulation-inputs.md)，`battle-terrain/ROOT-DELIVERY.json` | Combat6B8→strict Province10→247E590→terrain key18/Qwidth60；retained6F8 adjacency、6FE holding同leaf发布。复用可达transition(fullCombatID, revision)，owned control复制采样、不改权限/新增MCP；native DTO/serializer sections及三路径Python候选齐。 |
| [盟友拒绝诊断](../ck3-native-ai/call-ally-blocked-submit-diagnostic-consumer-12003.md)，`call-ally-reason/ROOT-DELIVERY.json` | 现有query已给C88/firstfailed/报价/战争关系，typed Python拒绝时丢失这些。单文件候选将有效CanSend=false返回rejected+完整selected terms，不发送命令/不产生ACK；unknown保留原异常。接手按当前调用方与一个受影响case验证一次。 |
| [普通holy-order hire](../ck3-native-ai/religion-holy-order-hire-command-construction-12003.md)，`holy-order-hire/ROOT-DELIVERY.json` | 真实inline ctor、0x30 owned clone、8B owning pointer、flags0x0E、SubmitCommandCopy已闭合，报价/CanHire/CanAfford/兵数query现成。接普通typed provider与注册，不调用带camera的UI callback。实际employer、资源扣款、public CUnitID后置仍待实现和live。 |

必要文件的原件路径、哈希、候选修改路径在 [22份小包索引](2026-10-05-g2-v73-handoff-packets/index.json)；只压缩小型receipt/合同/候选，没有游戏EXE/DLL、真实存档或大录像。原始来源、失败attempt与历史树全保留。

Entry还有确切断点：post-A/B `291C2B3→291C2FE`、`291C32C`、`291C334→28B6200`来源列表；changed-stage receiver/held-title/qualifier与七组counts关联；辅助scratch430/438与后续构造；Entry实际`28BFC70→2C06B00` context尚未证明等同model+10，以及首次接战caller身份。R46的21个空current-prefix叶只是已观测为空，不能补成完整人物、Entry或刷新/flush/reset。

地形另有边界：现v2只支持ctor0/null entry，holding实时按显式defender首军owner predicate取值。要重建retained constructor，还需明确retained holding/provenance；只接受非零kind不够。raw0不证明旧initiator/native_defender，不能把远方敌战retained geometry当下一次玩家入省的几何。

用户占用期间只对必要的已知RVA做冻结副本窄读：siege资格三个功能体合计887B、Entry总访问204B、holy clone130B/总访问906B。它们口径不同，不相加冒充统一总I/O；没有全EXE扫描/hash、完整构建或实机操作。Terrain末次lookup引号错误导致文本范围扩张，已立即Ctrl-C并保全`SOURCE-LOOKUP-RED.json`，该输出未用于结论。早期predicate RVA漏前导2已在读取前改为24DFB70，没有读取错址4DFB70。

## 5. 接手后的优先顺序与并行拓扑

1. **先恢复可见游戏推进。** 已有用户授权，接手核本机operator/当前owner并按现行Steam离线规则处理，然后在唯一实机执行线恢复原Robert普通保存。不要对用户游玩后的当前屏幕直接发历史命令。Fresh核actor29829、episode、raw date、War117、三军位置/route/Combat和公共revision；旧public2、PID、endpoint、h8938 packet均不可复用。
2. **利用现有能力闭合3711阶段。** 按fresh route进行正常OODA和保存；抵达后用既有occupation/army strengths验K/M/D/B/G、兵力与占领状态。独立eligible军可参围，先观察再决定是否有玩法理由合军。CanStartAssault/报价/支付用当帧native输入；source证明不要求合军不代表已经抵达。及时推进War117结果与独立结算，不为完整forecast研究阻塞已经可执行的玩法。
3. **并行补最有价值的观察/动作缺口。** Root sole source/Git integrator；背景owner分别做ETA、siege membership、actual geography、C88 consumer、holy hire及Entry/补员/损耗。前四项直接改善当前围城/战斗决策；holy hire须当前真实合法、有兵力价值候选；Entry是forecast依赖，保留精确断点持续补齐。独立文件/夹具按包所有权派子线，测试只由唯一owner消费一次。
4. **新源码用新冻结/资格，旧证据复用。** 在最新master整合外置候选，不改g78；需要新native binary时正常保存并退出旧run后构建、绑定exact source/EXE、分配新run，静态与paused读回资格分层记录。纯Python真实故障修复按AGENTS保留同进程热重试，不仅为Python变更重启。
5. **持续报告并按结果校准。** 每个包给Root提交完成项、为何必要、测试/RED、artifact/commit、readiness与remaining。日/周文字更新，不制作未请求的日/周视频；月报完整能力视频规则继续执行。没有未来artifact不报未来日数、战斗胜率或complete。

接手阅读顺序：本页 → [统一进度入口](../autonomous-agent-progress/README.md) → [完整目标/路线图](../autonomous-agent-progress/goal-and-roadmap.md)与[整代blocker账本](../autonomous-agent-progress/one-generation-blocker-ledger.md) → 当前专题与小包 → [operator MCP](../operator-mcp.md)、[测试流程](../testing-workflow.md)。进度大文档早期的“当前”段是历史，最新5035增量在后部；以本页截点和新的实际读回为准。最早[v32宗教休假交接](2026-10-03-g2-religion-v32-maintainer-vacation-handoff.md)仍是朝圣/改宗等未闭能力的输入账本，先检查最新注册库存再施工；不凭旧包假定已完成，也不因旧约束停宗教/战争。

## 6. 磁盘分支：已删除与未授权删除

用户明确“删除这个修复备份”已执行完成：唯一目标 **`C:/Users/xenoa/.codex/repair-backups/repair-20260922-032924`**，2026-10-05北京时间17:09:44删除后目录不存在，exit0；实际C盘释放 **84.739GiB**，当时可用 **162.047GiB**。证据 `Z:/ck3_mod_rewrite_process_assets/disk-space-inventory-20261005/repair-backup-deletion.json`。这不是待办，勿再删除、再跑清理或恢复旧授权问题。

同目录`report.md`、`cleanup-list.json`是此前C/Z盘扫描快照；数值不是现在实时空间。初步可再生成缓存候选45.602GiB，其中C36.932/Z8.670；shader11.688需等CK3退出，未清。**`zg361`历史研究约109.868GiB仍保留，没有整删授权**，包含三六一mod历史实机原件/未提交现场/录像，现有周报及测试仍引用；2.928GiB纯编译中间物是Z8.670的子集，不可叠加。详见`historical-zg361-followup.md`；没有权限将“可清候选”当成已获Apply授权。

## 7. 交付、状态与同事接手提示

本次将剩余四份native知识入库、封存八包关键receipt/候选、更新当前用户授权、进度入口及10-05/W41滚动报告，按项目规则提交并普通push。此前本轮已推送知识：C88 `d608b9af`、ETA `9ac0161d`、attrition `8524be62`、补员 `b4747184`；原非战撤销、历史live和前轮研究不重复验收。最新本页提交可由 `git log -1 -- docs/handover/2026-10-05-g2-v73-war-background-maintainer-vacation-handoff.md`取得，发布回执在外置`ROOT-VACATION-HANDOVER-20261005-PUBLISHED.json`。

本次文档验证仅 `git diff --check`及小包建立时的内容哈希；没有将文档检查写成代码测试/CI/live。原失败attempt继续保全；push并发时仅fetch/rebase/普通push，禁止force或merge。当前任务只是休假交接完成，原长期自动玩家目标、战争结算、完整person/Entry/forecast和自然继承仍未完成。后续同事可按最新授权直接继续工作。

## Actual watch declaration, raising and V2 observation (2026-10-06T08:12:53+08:00)

实际R0048/source715原Robert现 **5996/36524日，h9579**；78日增量为32+33+13，resume961/cumulative2843、natural0、G2 5/8、NW2 2/4。Watch-aware宣战一次，经独立后态确认 **War100663329**，title2132/objectives2606/2608；已有planner正常召集，当前军218104048已集结1833/2367兵在2619，未提交移动/未本战获胜。真实物理存档SHAc8f6e3e68cfadf8bbf46e7c9fb30ced282b19fb409f37325d28c488b659a4f7f/104792693B已保留。当前实际blocker为V3未advertised导致general-battle query空step；814现有V2同帧 available/input_observation_ready=true，完整MC/phase仍false。下一项正在接线已有bounded generic模型的明确V2消费者，同时Rule43实采六QWORD48B地址支持后台三段source研究。参见 [实际h9579字段](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/watch-raise-v2-h9579-report/ACTUAL-CUTOFF.json)、[watch原生树与实际宣战](Z:/gb0/docs/ck3-native-ai/player-war-entry-faction-watch-scope-12003.md)、[814实际V2](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/814-war100663329-combat-v2.json)。previous exact297c7630 CI37391070890 SUCCESS421s/job409s只复用终态；其旧h9543/5918截止与本次分开。本报告新增tests/builds/CI查询0，Root继续，不授fullperson/Entry/forecast/自然继承/完整战斗或complete。

## Local background work and first production fault qualification (2026-10-06T09:18:05+08:00)

**本机CK3由用户自行游玩，仅后台；其他机器保留原安排。** 原战役最新正常h9586/**5996日**、natural0；新游戏日/动作/部署0。最新保存与完整driver已留，十条输入只做文件保全。两个native实证故障最小修复在新g82/ecc15d1cfdcae9d8497cdc847af8a61be264837d一次formal四runtime+两fixture严格64编译GREEN（116.98222s、586TUs/581unique/1238inputs/0复用），FIRST新Ct **2/2 GREEN**，static-ready，未实机恢复。V2 consumer与outer路由FIRST各1/1 GREEN；fresh人物新基线FIRST1/1 GREEN，均保留完整Entry/phase/live缺口。Rule43真实154B来自三组各自绑定帧，不合成wholetruth；当前source累计850B。原844 AV/845 bit512/850拒绝与R0048stop（SDK0、CK3exit1/cleanup proven）全部保留。

参见[本包资格](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/battle-terminal-mailbox-failure-01/strict02/ROOT-FIRST-QUALIFICATION.json)、[h9586十条输入](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/runtime-upgrade-plan/source-pair-h9586-background-only/FINAL-SOURCE-PAIR.json)与[Oct6滚动日报](../autonomous-agent-progress/daily/2026-10-06.md)。下一项只读caller identity census、associated refill组合及phase候选Rite输入继续后台施工；不启动本机CK3、不重跑旧证据、不授完整forecast/war loop/自然继承/complete。新publication的commit/push与精确CI由外置回执追加，旧f990 CI终态直接复用。
