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

## Associated refill current and phase input source continuation (2026-10-06T09:26:17+08:00)

仅后台继续：associated refill物理ADD一次、DATA按occurrence刷新current/max的新生产字段首次1/1 GREEN，bounded static-ready，actual仍false/null；完整月度、真实兵力变化未完成。phase adopted Rite参数最小source树/Mermaid已交，仍research，optional V2叶与人物identity census正在施工，不授完整V3/forecast/live。新game/nativebuild/旧tests0，原h9586/5996日/natural0不变。[FIRST](Z:/ck3_mod_rewrite_process_assets/g2-background-round6-20261006/associated-refill-current-assembly/FIRST-PYTHON-CASE-RECEIPT.json)、[phase原生入口](../ck3-native-ai/combat-phase-readonly-input-frontier-12003.md)。

## Three readonly observer FIRST qualification and source continuation (2026-10-06T10:29:11+08:00)

三个可达生产叶（current/old/pair模型身份、phase adopted Rite参数、Province补给contributors）完成 g85@01d98c73ca42b91b5e39c827e32a07b1afe51479 fresh native编译及FIRST3Ct 3/3 GREEN，新actualwire4/5/4首次生产消费GREEN；**bounded static-ready**，未live/部署。两个compiler/link RED保留，实际fix后通过；无旧tests重跑。warmonger Core membership与land resupply新叶正在实现，person2921350/2921020数值source闭合、observer/emitter尚待施工。用户自行重启解决Steam环境继承造成的启动失败；Root无再次游戏/Steam/SDK操作。Z新worktree空间不足已缩减Root两树、编译转C盘。原h9586/5996日/natural0、G2 5/8/NW2 2/4不变。[资格证据](Z:/ck3_mod_rewrite_process_assets/g2-background-round6-20261006/readonly-observer-batch/root-publication/ROOT-FIRST-QUALIFICATION.json)、[源树入口](../ck3-native-ai/combat-phase-warmonger-predicate-12003.md)。

## Land resupply and warmonger FIRST qualification; actual isolated CI repair (2026-10-06T10:59:32+08:00)

g86@75e9d648dac75f941cc338a0d410f930570fa1fb四runtime+两新fixtures native121.607099s/FIRST2Ct2/2 GREEN；新resupply4wire、warmonger7samples/67checks首次生产消费GREEN，两current叶 **static-ready**，未live/部署/fullrate/fullphase。实际359e CI漏collector依赖已复现并最小修复，一次必要isolate route检查GREEN，其它旧测试不重复。phase敌方Faith方向与实际Side token/class source闭合，46552B有界metadata定位未中iterator/resolver，下一compiled registration入口明确，仍research。人物两numerical producers/native17wire待集中资格、full-rate source继续。本机CK3/Steam/SDK/input0，其他机器安排照旧，冻结agent h9586/5996/natural0不变。[资格证据](Z:/ck3_mod_rewrite_process_assets/g2-background-round8-20261006/current-land-resupply-observer/root-resupply-warmonger-publication/ROOT-FIRST-QUALIFICATION.json)、[继续source入口](../ck3-native-ai/phase-enemy-participant-faith-conditional-12003.md)。

## Person following stages and full land rate FIRST qualification (2026-10-06T11:24:15+08:00)

g87@5c33040bbc28864fa76106e719fa61fae30258ab FIRST native三新Ct3/3、人物17wires/4条件stage/204checks、full-land-rate5wires均GREEN；两人物阶段与同context完整陆军rate为限定static-ready，实际Rule43/阶段关联/月度/Entry/live仍未完成。[人物树](../ck3-native-ai/battle-person-stage-chain-12003.md)、[补给率](../ck3-native-ai/army-land-supply-rate-inputs-12003.md)、[Root资格](Z:/ck3_mod_rewrite_process_assets/g2-background-round9-20261006/person-full-rate-root-publication/root-publication/ROOT-FIRST-QUALIFICATION.json)。registry/name source13627B闭合，敌方iterator/resolver继续；狂战士五输入最小源码接点已确认并开始V2施工。上一323445bc官方CI37406839068 SUCCESS。本机game/Steam/SDK/input0，其他机器授权照旧；冻结agent h9586/5996/natural0不变。

## Berserker inputs, cold person projection and joined refill service (2026-10-06T11:49:59+08:00)

g88@a71cbc85e80c4c5c85531733596303fa3dd305cd FIRST native/Ct1/1、新berserker9samples/95checks/9stockAST GREEN；新leaf限定static-ready，Core/context wrapper synthetic，wholephase/live不升级。cold normal-return pure1case和joined refillservice1case首次GREEN；[cold模型](../ck3-native-ai/battle-person-cold-tier-projection-12003.md)、[月度组装源入口](../ck3-native-ai/army-monthly-supply-stock-assembly-inputs-12003.md)、[Root资格](Z:/ck3_mod_rewrite_process_assets/g2-background-round11-20261006/berserker-cold-join-root/root-publication/ROOT-FIRST-QUALIFICATION.json)。kind11 ctor/decoder source9094B闭合，compiled enemy/list与Rule43 context继续；月度pure assembly正在施工。上一16f官方CI SUCCESS434s。本机game/Steam/SDK/input0，冻结agent h9586/5996/natural0不变；其他机器授权照旧。

## Selected refill monthly assembly and Rule43 root source (2026-10-06T12:00:46+08:00)

选定补员→derived DATA/current/max/flags0123→full-land-rate→stock/SJR→四轮扣兵→caller的production service条件组装 **FIRST1/1 GREEN**（四variants，0.024s/outer3.2408652s），预算18/41/12、首writer current90验证真正消费refilled frame；[月度树与边界](../ck3-native-ai/army-monthly-supply-stock-assembly-inputs-12003.md)。限定bounded static-ready，actual/full regular/full monthly false/null。Rule43 actual kind4 producer及expected22565B0完整leaf source闭合，newEXE I/O91B/unique credit0；[根验证器与实际观测入口](../ck3-native-ai/battle-person-rule43-character-root-validator-12003.md)，loaded descriptor/current witnesses/finalpredicate未升级。上一c19官方CI SUCCESS419s，本包0native/旧测试重跑/本机game或Steam/SDK；冻结h9586/5996/natural0未变。继续actual manager preparation、compiled enemy/list factory和berserker chance source。

## Actual refill/assault order and phase input implementation frontiers (2026-10-06T12:23:40+08:00)

source确认primaryArmyManager2A540/secondary2A548、重复full7q-buffer补员→最后Armyrefresh及每日active-assault table loss；[真实顺序](../ck3-native-ai/army-monthly-manager-prepared-stage-inputs-12003.md)，selected固定模型仍只限定static-ready。observed-prepared scoped有序observer/kernel、[Rule43同query整合](../ck3-native-ai/battle-person-rule43-integrated-current-query-12003.md)、berserker18新增traits等chance输入和fleet固定context observed-rate模式正在隔离C树施工；没有以null/metadata冒充功能。compiledenemy/list缺实际factorypin，0newread且停止弱定位扩张。本批source/plan均research，0Root native/旧测试/本机game或Steam/SDK；冻结h9586/5996/natural0不变。上一b991官方CI SUCCESS406s。实际fullregular/fullmonthly、全person/Entry/phase/自然继承未完成。

## Same-query chance and Rule43 FIRST qualification; fleet monthly composition (2026-10-06T12:45:55+08:00)

g89-fix02@aff6d9f2首次strict native GREEN119.043374s/FIRST2Ct2/2；同query狂战士chance **10samples/90checks** 与Rule43 **8cases** 首次生产消费GREEN，限定static-ready；[chance树](../ck3-native-ai/combat-phase-berserker-chance-inputs-12003.md)、[Rule43树](../ck3-native-ai/battle-person-rule43-integrated-current-query-12003.md)、[Root回执](Z:/ck3_mod_rewrite_process_assets/g2-background-round16-20261006/phase-chance-rule43-batch/root-publication/ROOT-FIRST-QUALIFICATION.json)。fleet固定context月度service FIRST1/5variants GREEN。配置误列inlinehelper cpp的strict01 RED保留，未运行fixture；旧tests/wires本地重复0。scoped ordered core23097990 Python FIRST1 GREEN但native待g90，B/pointerfix和fresh fixedchunk0输入继续施工。上一d84官方CI SUCCESS418s。本机game/Steam/SDK/input0，冻结h9586/5996/natural0不变；其他机器授权照旧。实际fullmonthly、wholeperson/Entry/phase/forecast、自然继承与complete未完成。

## Ordered core and siege current FIRST native qualification (2026-10-06T13:08:17+08:00)

g90-fix02@62f39655 native GREEN121.900624s、FIRST2Ct2/2、ordered core **5新wires/5 GREEN**、B/pointerfix **5新wires/5 GREEN**；[有序树](../ck3-native-ai/army-ordered-regular-refill-projection-plan-12003.md)、[围城B树](../ck3-native-ai/army-province-besieging-current-12003.md)、[Root回执](Z:/ck3_mod_rewrite_process_assets/g2-background-round17-20261006/ordered-core-assault-batch/root-publication/ROOT-FIRST-QUALIFICATION.json)。重复80→90→100、DATA200；独立selectedB352→381、强攻预算8→9实际消费derivedphysical且无第二ADD。限定static-ready、不同入口scope不混；missing与0分开。corefixture缺第五serializer参数的strict01 RED保留，Root最小修复后首次Ct/wires通过，旧测试本地重跑0。下一ordered→B刷新语义组合、freshchunk0 candidate932/native6、dailyassaulttable输入继续；上一58e官方CI SUCCESS255s。无本机game/Steam/SDK/input/部署，新日0，冻结h9586/5996/natural0不变，其他机器照旧；actual/fullmonthly/fullwar/自然继承/complete未完成。

## Fixed chunk0 preparation FIRST qualification and actual CI compatibility fix (2026-10-06T13:22:37+08:00)

固定chunk0准备同查询输入：g91@51d14f31 fresh native GREEN116.223264s、FIRST新Ct1/1、首次六个compiled wires6/6 GREEN；ordinary10000/permission false0/negative−123/合法0/partial/empty分支均经production contract/service。限定static-ready，不写148，[原生树](../ck3-native-ai/army-fixed-chunk0-preparation-inputs-12003.md)、[Root回执](Z:/ck3_mod_rewrite_process_assets/g2-background-round18-20261006/fixed-chunk0-root/root-publication/ROOT-FIRST-QUALIFICATION.json)。上一f1a官方CI FAILURE155s由ArmyBindings聚合前缀变化造成；b9367e30将新增成员移尾，一次必要corrected route检查GREEN21.6291008s，原RED保留，旧新资格未重复。显式prepare→core、[真实refresh ordered→B](../ck3-native-ai/army-ordered-refill-besieging-assault-composition-12003.md)、[当前daily-assault分组](../ck3-native-ai/army-daily-assault-active-table-placement-12003.md)继续实施；后两者source-plan已采用、尚为research。仅后台，新game/Steam/SDK/pipe/输入/部署/日0，冻结h9586/5996/natural0不变，其他机器照旧。actual/fullmonthly/live/complete未完成。

## Explicit preparation to ordered current/max FIRST production-query composition (2026-10-06T13:40:46+08:00)

[显式准备组装](../ck3-native-ai/army-explicit-preparation-scoped-core-assembly-12003.md)增加MCP可选模式 `fixed_chunk0_prepare`，共享ordered core只执行一次，再刷新subject DATA/current-max。FIRST新compound1/1 GREEN、六次真实registered dispatch、1.042s/3.0493282s；重复80→90→100/两DATA200、合法0负值/缺权限不借old148均验证。限定static-ready条件输入组装，0新native build/旧test/wire/EXE/live；[首次收据](Z:/ck3_mod_rewrite_process_assets/g2-background-round16-20261006/explicit-prepare-scoped-core/first01/FIRST-COMPOUND-RECEIPT.json)。上一3b0官方CI SUCCESS299s/static296s，[终态](Z:/ck3_mod_rewrite_process_assets/g2-background-round18-20261006/fixed-chunk0-root/root-publication/CI-3b0b0290/FINAL-CI-RESULT.json)，原f1失败保留。日常强攻表新native9与真实refresh ordered→B继续；本机游戏及用户现场不动，新日0，冻结h9586/5996/natural0不变，其他机器照旧。实际write/fullmonthly/live/complete尚未完成。

## Current daily assault groups and ordered besieging refill FIRST compiled qualification (2026-10-06T14:17:02+08:00)

[当前daily表](../ck3-native-ai/army-daily-assault-active-table-placement-12003.md)与[ordered-B组装](../ck3-native-ai/army-ordered-refill-besieging-assault-composition-12003.md)有限static-ready：immutable g92/ae7819df full首次GREEN120.59862s、595TU/590unique/1306inputs、generated0/reuse0、65ON50OFF；新Ct2/2GREEN。两项零场景 harness RED保留，最小输出flag/三个假ID修正、单fixture重编译复用原runtime后，FIRST真实整帧service **table9/164checks** 与 **ordered7** 均GREEN（0.5269947s/0.5344395s）。[9帧](Z:/ck3_mod_rewrite_process_assets/g2-background-20261006/daily-assault-active-table-2aa2030/implementation/FIXTURE-ID-FIX-COMPILED-SERVICE-RESULT.json)、[7帧](Z:/ck3_mod_rewrite_process_assets/g2-background-round17-20261006/ordered-core-assault-composition/FIRST-NATIVE-WIRES-QUALIFICATION-repaired-output.json)、[分开源码的修正收据](C:/codex-ck3-background/ordered-assault-table-batch/fixture-output-repair01/CORRECTED-FIXTURE-CTESTS.json)。物理顺序/重复/fullDWORD、局部分母[200,30,0]及B800/80 versus held640/64成立；actual/fullmonthly/future placement/live未计。当前daily-loss新compound1/1GREEN、native新6待统一资格，[损失输入](../ck3-native-ai/army-current-daily-assault-loss-inputs-12003.md)；[实际freshB范围](../ck3-native-ai/army-ordered-besieging-fresh-preparation-scope-plan-12003.md)实现继续。上一12fd官方CI SUCCESS427/static423，[终态](Z:/ck3_mod_rewrite_process_assets/g2-background-round19-20261006/explicit-prepare-core-root-publication/root-publication/CI-12fdc06f/FINAL-CI-RESULT.json)。本机游戏操作与新日0、h9586/5996/natural0维持，其他机器照旧。

## Current daily assault sequential loss FIRST compiled qualification (2026-10-06T14:35:14+08:00)

[当前daily-loss](../ck3-native-ai/army-current-daily-assault-loss-inputs-12003.md)有限static-ready：g93/1f45a362 full首次GREEN128.750114s，605TU/590unique/1310inputs，65ON50OFF/generated0/reuse0；原新Ct缺endcontrol RED与service旧ID字段RED均保留。两个fixture-only最小修正后复用原producer，新Ct1/1GREEN/NEW6；此前失败6个实际字节场景完整service必要重试 **GREEN6/12checks/1.6269146s**，[收据](Z:/ck3_mod_rewrite_process_assets/g2-background-round16-20261006/current-daily-assault-loss-numeric-plan/implementation/compiled-consumer-attempt02/CONSUMER-FIRST-RECEIPT.json)、[修正双来源](C:/codex-ck3-background/current-daily-loss-batch/fixture-output-repair02/CORRECTED-NEW-CTEST.json)。原生预算116/58与顺序条件116/25、B252/targetcached20/physical10分开，actual/fullmonthly/live未计。actualfreshB scope新模式和[physical stage接口](../ck3-native-ai/army-ordered-besieging-physical-stage-interface-12003.md)待FIRST，源树[队列/release](../ck3-native-ai/army-daily-assault-queue-release-12003.md)与futureplacement继续。上一fdc官方CI SUCCESS439/static436，[终态](Z:/ck3_mod_rewrite_process_assets/g2-background-round20-20261006/ordered-assault-table-root/root-publication/CI-fdcbd9c5/FINAL-CI-RESULT.json)。本机游戏操作、新日0，冻结h9586/5996/natural0不变；其他机器照旧。

## Actual ordered-B fresh preparation FIRST compiled qualification (2026-10-06T14:59:49+08:00)

[实际ordered-B准备查询](../ck3-native-ai/army-ordered-besieging-fixed-chunk0-preparation-inputs-12003.md)有限static-ready：g94/cc453409首次fullGREEN123.705205s，599TU/591unique/1315inputs、65ON50OFF/generated0/reuse0；FIRST新Ct1/1GREEN、[七个完整MCP实际字节场景](Z:/ck3_mod_rewrite_process_assets/g2-background-round18-20261006/fresh-ordered-b-preparation/NATIVE-ROOT-DELIVERY.json)FIRST GREEN7/7，核心一次/adapter ADD0，B640→800/预算64→80。缺输入保留partial，旧RED和冻结NOT_RUN保留。队列pre-release FIRST完整service1/1GREEN；[canonical release源码](../ck3-native-ai/army-daily-assault-queue-release-12003.md)闭合到HeapFree，条件释放后态另包施工。[实际allocator匹配的futureplacement](../ck3-native-ai/army-daily-assault-future-placement-12003.md)候选FIRST纯service GREEN，六新native待g95；完整roster/admission为下一观测主线。上一637官方CI SUCCESS303/static299，[收据](Z:/ck3_mod_rewrite_process_assets/g2-background-round21-20261006/current-daily-loss-root/root-publication/CI-637ac0a9/FINAL-CI-RESULT.json)。本机游戏操作、新日0，h9586/5996/natural0保留；actual/fullmonthly/live未增加。

## Actual daily assault allocator witness FIRST compiled qualification (2026-10-06T15:08:44+08:00)

[实际allocator witness与有限放置](../ck3-native-ai/army-daily-assault-future-placement-12003.md)compiled static-ready：g95/f2cd130e首次fullGREEN118.89139s、594TU/591unique/1316inputs/65ON50OFF/generated0/reuse0；FIRST新Ct1/1GREEN，[六新全帧完整service与显式conditional prefix](Z:/ck3_mod_rewrite_process_assets/g2-background-20261006/daily-assault-future-placement/g95-first-compiled-service01/FIRST-COMPILED-SERVICE-RESULT.json)FIRST GREEN。正常匹配的slot1→2搬迁保留重复，缺witness/mismatch保留独立current与hit/directempty资格；不称明日状态。下一项实际原primary roster/admission query与[条件release原始header输入](../ck3-native-ai/army-daily-assault-queue-release-12003.md)继续。本机游戏操作、新日0，h9586/5996/natural0保留，actual/fullmonthly/live未增加。[上一11ab7145官方CI37426962332终态SUCCESS](Z:/ck3_mod_rewrite_process_assets/g2-background-round22-20261006/fresh-ordered-b-root/root-publication/CI-11ab7145/FINAL-CI-RESULT.json)，与native资格分别计账；本次exact新HEAD官方L0由唯一observer另记。

## Current assault conditional normal-return release FIRST qualification (2026-10-06T15:41:21+08:00)

[actual raw header与条件release](../ck3-native-ai/army-daily-assault-queue-release-12003.md)有限compiled static-ready：g96/c981首次fullGREEN121.693152s，594TU/591unique/1317inputs/65ON50OFF/gen0/reuse0、FIRST新Ct1/1GREEN。新strict拒native reason=null的零投影RED保留；只修Python并[冻结service cc33fc55](Z:/ck3_mod_rewrite_process_assets/g2-background-round24-20261006/daily-release-root/IMMUTABLE-SERVICE-REASON-FIX.json)，producer未改，必要首例retry+五首次全GREEN6/6，[字节资格](Z:/ck3_mod_rewrite_process_assets/g2-background-round18-20261006/current-daily-assault-normal-return-release/compiled-consumer-necessary-retry02/CONSUMER-FIRST-RECEIPT.json)。normal-return null保留、nonnull canonical清零，count驱动control清理，独立table/header/pending资格保留。旧fixture source-only correction不计runtime。[generalcollision309B源码与纯extension](../ck3-native-ai/army-daily-assault-carried-collision-12003.md)FIRST新完整service1方法/6subcases GREEN，两次非空重复值交换+hit/empty完成count6，[独立收据](Z:/ck3_mod_rewrite_process_assets/g2-background-round20-20261006/daily-assault-carried-collision/first-new-service-compound01/RECEIPT.json)，无native重编/旧case重跑。下一[当前roster/admission](../ck3-native-ai/army-daily-assault-roster-admission-12003.md)observer与实际first-removal输入继续；上一aff官方CI SUCCESS463/static458，[收据](Z:/ck3_mod_rewrite_process_assets/g2-background-round23-20261006/daily-placement-root/root-publication/CI-aff08f99/FINAL-CI-RESULT.json)。本机游戏操作、新日0；h9586/5996/natural0保留，actual/fullmonthly/live未增加。

## Pre-date mutating pending-list source closure and first-removal input plan (2026-10-06T16:01:33+08:00)

[前置pending mutator原生树](../ck3-native-ai/army-pre-date-roster-pending-update-12003.md)source闭合：2A92320保留旧列表并追加actual ArRg10，subject Contract B9/persistent13C/War按需选择，最终count与Army44比较；重复Army改变removal append与admission skip。2299uniqueB/duplicate0，FIRST source全GREEN，[收据](Z:/ck3_mod_rewrite_process_assets/g2-background-round21-20261006/pre-date-army-roster-dispatch/ROOT-DELIVERY.json)，两次bus CLI RED不计source失败。current standalone admission独立；下一raw observer+纯模型施工，零新test/native/live。[current/derived首次removal context](../ck3-native-ai/army-current-assault-first-removal-context-12003.md)计划已采用，[交付](Z:/ck3_mod_rewrite_process_assets/g2-background-round19-20261006/current-assault-removal-reference-context/ROOT-DELIVERY.json)，借qualified原始queue与六列表/B0，仅补actual14、第二次helper和physical bucket。7e官方CI SUCCESS454/static451，[终态](Z:/ck3_mod_rewrite_process_assets/g2-background-round24-20261006/daily-release-root/root-publication/CI-7e621c24/FINAL-CI-RESULT.json)。h9586/5996/natural0及全部已冻结资格保持；本机操作和新增日0，actual/fullmonthly/live未增加。该记录是实际追加时刻的施工更新，不倒填早会。

## Current standalone roster admission compiled qualification and preceding dated-append source (2026-10-06T16:26:07+08:00)

[current完整原始名册与standalone准入](../ck3-native-ai/army-daily-assault-roster-admission-12003.md)有限compiled static-ready，FIRST新九wholewire完整serviceGREEN9/307，[收据](Z:/ck3_mod_rewrite_process_assets/g2-background-20261006/daily-assault-roster-admission/compiled-service-first01/RECEIPT.json)；七ready/twopartial，重复/fallback/knownArmy-nullArRg/合法空/legacyqueue实际复用保留。g97首次full fixtureunsigned断言RED123.89342s，[原记录](C:/codex-ck3-background/roster-admission-batch/strict01/BUILD-RESULT.json)；生产da887不改，四runtime复用对象completionGREEN2.681649s/593TU590unique1320inputs/65ON50OFF，fixture1df仅1TU修正后FIRST新CtGREEN9wire，[分来源](C:/codex-ck3-background/roster-admission-batch/fixture-repair01/FIXTURE-ONLY-BUILD-RECEIPT.json)。这些wire的currenttableabsent，不计compiledplacement/fullfuture/live。[前置dated158 append source](../ck3-native-ai/army-pre-date-tomorrow-context-preparation-12003.md)560B缓存复用，新读取/hash0，[交付](Z:/ck3_mod_rewrite_process_assets/g2-background-20261006/pre-date-tomorrow-context-preparation/ROOT-DELIVERY.json)，不改roster50/removal68/pending130；实际tomorrow operand与按需date observer继续。043官方CI SUCCESS502/static498，[终态](Z:/ck3_mod_rewrite_process_assets/g2-background-round25-20261006/roster-admission-root/source-publication/CI-04369827/FINAL-CI-RESULT.json)。本机操作/新日0，h9586/5996/natural0与所有旧资格保持；该记录是实际追加更新，非倒填早会。

## Current first-removal qualification and pre-date observation progress (2026-10-06T17:14:56+08:00)

[当前首轮清理](../ck3-native-ai/army-current-assault-first-removal-context-12003.md)达到有限 compiled static-ready：g98首次full GREEN126.984656s；新夹具 Strength 数据 RED0wire保留，只编修正 CPP，原 producer177a/includes/service与fixture9e49分开记录。FIRST六个新wholewire完整service GREEN6/17checks/2.7709512s，[回执](Z:/ck3_mod_rewrite_process_assets/g2-background-round19-20261006/current-assault-removal-reference-context/compiled-consumer-first01/CONSUMER-FIRST-RECEIPT.json)，actual/future drain/live均未提升。[pending完整服务](../ck3-native-ai/army-current-pre-date-pending-update-inputs-12003.md)新11场景 GREEN2.7556847s，[资格](Z:/ck3_mod_rewrite_process_assets/g2-background-round22-20261006/current-pre-date-pending-update/FIRST-SERVICE-QUALIFICATION.json)；FIRST实际native8-wire完整服务GREEN8，保留首次消费者断言RED并仅重试未通过的6场景。g99首次full RED117.416104s仅pending夹具unsigned断言，生产复用completion GREEN2.939789s/595TU592unique1333inputs/65ON50OFF，[记录](C:/codex-ck3-background/pre-date-inputs-batch/runtime-completion01/REPORT-FIELDS.json)；dated新Ct GREEN1/五wire，FIRST实际消费GREEN5。[dated](../ck3-native-ai/army-pre-date-tomorrow-context-preparation-12003.md)原生clock+24U/signed wrap接线完成；新Python夹具必要修正后source compound GREEN1/六querycases，原RED保留。[Character-prefix树](../ck3-native-ai/army-pre-date-character-prefix-and-post-admission-callback-12003.md)source-only采用，24DF精确metadata160B+body669B的树/写账本已采用，下一项补rawArRg40以解锁独立24/28数值刷新；后续flag/callback仍分列。9c官方CI SUCCESS453/static449，[终态](Z:/ck3_mod_rewrite_process_assets/g2-background-round25-20261006/roster-admission-root/qualification-publication/CI-9c85009c/FINAL-CI-RESULT.json)。本机操作/新增游戏日0，h9586/5996/natural0不变；这是实际追加进度，非倒填早会。

## Isolated CI link correction and source-bound mapper/commander seams (2026-10-06T17:33:21+08:00)

97192b20官方CI RED127/static125，缺新collectorTU导致isolatedroute LNK2019，[终态](Z:/ck3_mod_rewrite_process_assets/g2-background-round27-20261006/pre-date-root/g98-pre-date-publication/CI-97192b20/FINAL-CI-RESULT.json)。Root仅补实际直接编译列表/header，必要同14TU link GREEN33.4633789s/fixture0.1356856s，[验证](C:/codex-ck3-background/pre-date-inputs-batch/isolated-route-link-fix01/NECESSARY-LINK-FIX-VERIFICATION.json)；CMake/runtime及19wire资格不重跑，新官方CI另记。[后续动态buffer/mapper](../ck3-native-ai/army-later-removal-drain-stage-inputs-12003.md)source已采用，247code+220metadata一次、无neighbor/hash，kind1/4与count0/negative、signedcount>0 fallback分支闭合，[交付](Z:/ck3_mod_rewrite_process_assets/g2-background-round20-20261006/later-removal-drain-stage-plan/mapper-2a977a0/ROOT-DELIVERY.json)。[Character前缀计划](../ck3-native-ai/army-pre-date-character-validation-and-commander-inputs-12003.md)以现有F/T/F真实predicate补观测，Unit174先读，failure80不阻断admission，[计划](Z:/ck3_mod_rewrite_process_assets/g2-background-20261006/pre-date-character-validation-commander-inputs/ROOT-DELIVERY.json)；只读实现进行中，无compiled/live。numeric24/28、pendingnewkey及byte20/30source继续。本机操作/新增day0，h9586/5996/natural0保持；实际追加记录不倒填早会。

## Current numeric refresh service and exact flag/growth source (2026-10-06T17:46:44+08:00)

dfab3f7d官方CI37443785470 SUCCESS284s，[终态](Z:/ck3_mod_rewrite_process_assets/g2-background-round27-20261006/pre-date-root/ci-link-fix-publication/CI-dfab3f7d/FINAL-CI-RESULT.json)，首次lookup已terminal，static独立时间未观测不补猜。原971LNK RED/最小link修复/19wholewire资格分账不重放。[numeric24/28新输入](../ck3-native-ai/army-current-post-admission-refresh-inputs-12003.md)真实hooks820d已接入；完整immutable Service FIRST1method/4queries GREEN0.014s/process3.6116393s，[收据](Z:/ck3_mod_rewrite_process_assets/g2-background-20261006/current-post-admission-refresh-inputs/first-source-service01/FIRST-SERVICE-COMPOUND-RECEIPT.json)，9compiled新wires尚未运行，actualrefresh/nextrepeat/fullcallback/live不计。[实际20/30 source](../ck3-native-ai/army-refresh-two-byte-flags-12003.md)采用e7db，809actual/803credited code+184metadata，六padding与locator/decoder RED保留，[交付](Z:/ck3_mod_rewrite_process_assets/g2-background-20261006/army-refresh-two-byte-flags-source/ROOT-DELIVERY.json)；真实20tail24E3FE0与30Army1D8+160 condition待补。同query [pendingcarry/growth](../ck3-native-ai/army-current-pending-new-key-carry-growth-12003.md)StageA307uniqueB/dup0、普通wrapper/continuation有限前沿已记录，[收据](Z:/ck3_mod_rewrite_process_assets/g2-background-round23-20261006/current-pending-new-key-source/ROOT-STAGE-A-DELIVERY.json)，StageB只有限source。Character前缀/wholecandidate mapper施工中，Root计划一次新formal batch。本机操作/day0，5996/natural0保持；真实追加非早会倒填。

## g100 three current-input families: compiled25 FIRST GREEN (2026-10-06T18:25:38+08:00)

fdcf官方CI37445325155 SUCCESS476/static473，[终态](Z:/ck3_mod_rewrite_process_assets/g2-background-round28-20261006/refresh-root/source-refresh-publication/CI-fdcf9118/FINAL-CI-RESULT.json)。Rootb044 fullRED130.251976s为mapperinc在namespace外的实际接线错误，source/log保留；仅include919修正后551f完整freshfullGREEN126.056244s、597TU/594unique/1347inputs/gen0/65ON50OFF，[构建](C:/codex-ck3-background/refresh-prefix-mapper-batch/strict02-production-namespace/BUILD-RESULT.json)，[FIRST仅3新Ct](C:/codex-ck3-background/refresh-prefix-mapper-batch/strict02-production-namespace/FIRST-THREE-NEW-CTESTS.json) GREEN0.6709783s。三family25新wholeStrength真实strict→Service→pure **9numeric+8prefix+8mapper全GREEN**：[numeric](Z:/ck3_mod_rewrite_process_assets/g2-background-20261006/current-post-admission-refresh-inputs/COMPILED-QUALIFIED-ROOT-DELIVERY.json)独立24/28/repeats/fallback；[prefix](Z:/ck3_mod_rewrite_process_assets/g2-background-20261006/pre-date-character-prefix-observer/QUALIFICATION-DELIVERY.json)真实按需6/5/4、validfallbackactualCharacterID/重复skip转换；[mapper](Z:/ck3_mod_rewrite_process_assets/g2-background-round21-20261006/current-candidate-detachment-mapper/FINAL-QUALIFIED-ROOT-DELIVERY.json)9raw/7physical/4signedcounts、fallbackstate4、183checks。已过source4/5和mapper10场不重放；mapper仅新夹具Nullable构造修复后7未跑场续GREEN，原RED保留。三个当前输入static-ready，actualeffect/future/fullcallback/monthly/livefalse。[pendinggrowth源](../ck3-native-ai/army-current-pending-new-key-carry-growth-12003.md)1788uniqueB闭合及九文件实现已授权；[20tail/30condition源](../ck3-native-ai/army-refresh-tail-and-condition-verdict-inputs-12003.md)531B增量落盘，实际30 current-verdict新family准备，28B2820/B02D10/2633FF0实际叶cache-first继续。本机操作/day0、5996/natural0保持；无部署/rebind，真实追加非早会倒填。
