# 2026-09-30 非战争维护者休假交接

> 本文按用户完成手上事项、停止新工作并交接的要求，在R0407实际终态后写成。root于2026-09-30 10:02:05 UTC确认wrapper已退出0。文档源码基线fb32a5ca52aa51324abb0583c551223d4b8fcfd5；实际source7eb/profileba885/native-origin-debe分别记账，最新现场沿实际证据/live source核实。

## 用户最新范围与接手规则

- 仓库导航已通过exact master树定位：[状态投影 current-state.json](../project-state/current-state.json)、[G2要求JSON](../autonomous-agent-progress/g2-requirements-v1.json)、[G2要求与执行索引](../autonomous-agent-progress/g2-requirements-and-execution.md)。状态投影只指向live source，不能替代现场身份；本文不改这些文件。
- 本次仅收口既有 **BA5 候选、3 paused query、婚配动作 OFF、日期推进 OFF**，随后交付文档；没有后续婚配动作、日期推进或新 cold 包。下文“下一步”留给接手者，不表示本执行者已启动。
- 非战争仍以 LIFE → ECON → FAMILY 为常规优先级，JOINT 并行；本轮婚约 application 观测缺口曾升为 P0，已由 R0407 窄关闭。战争公式、路线与模型维护留给战争维护者，本执行者只消费 master 已交付接口。不扩宗教策略或全矩阵。
- **用户已明确撤销检查别人机器 CK3 的要求**：不要询问或检查另一台战争机器。沿本机现有 owner、受管进程、冻结制品和正式实例队列操作；不得根据本文旧状态抢占本机实例。
- CK3 默认最小化，只有必要加载/视觉验收/输入阶段短时显示；等待代码、CI或外部结果时最小化。当前身份、owner、RED、心跳与窗口状态以实际 live source 和终态回执为准，不由 PID 存活或旧报告推断。
- 所有新源码/temp/cache/build/日志在实际可写非 C 盘，进程级 TEMP/TMP 与所需工具缓存一并绑定，不改 HOME/USERPROFILE。根 `Z:\ck3_mod_rewrite` 是历史脏现场，不能 reset、全量 stash/clean 或覆盖。

## 真实主线、能力与版本

| 项目 | 收尾前已验证事实 |
| --- | --- |
| G2 | **3/8**：M0/M1/M3 complete，M2/M4 in progress，M5–M7 not started；定义、分母与通过条件不改。 |
| Robert | 1066 Robert 及合法继承主线，持久 **3,153/36,524游戏日**，raw **53220000**；百年 **0/1**、首整局 **0/1**、独立种子 **0/2**。不计旧 Murchad、H3928 活动研究、h90 派生或 replay。 |
| R0404 / R0405 | R0404 正式 typed move +1日；R0405 新PID恢复原 target2614/route/moving，无重复move，12/12 turn再推进2日。3日已计入3153，不再累计。原军队在2610，未把 moving 写成抵达或围攻。 |
| R0406 | PID36192/创建20260930082304.628169+000，actual **d1aea174/profile95eb/DLL28**，h4013输入真实cold_checkpoint/active_resumed，**3/3 query、0 gameplay、0日期**。最小化背景心跳2921→3284、mailbox8→18、native3→4证明真实执行。 |
| R0406历史输入 | **h4019/raw53220000**、save **AC52…0C6E**、final driver **770F1C92…95522**；Guy ED022D20…8C689。输入h4013已cold恢复，该h4019输入在R0407已实际cold恢复；最新h4025输出资格另记，不物理强配或手改driver。 |
| BA5最后候选 | official pair/no-launch一次PASS，PAIRING-READY BB3AB71C…8B5AB、official report02E6350C…4A493；source7eb2785、actual selected runtime ba885d0f3d511da62cedcf9ffef1c864ab89cf60、新DLL BA5。输入h4019合法冻结，没有手改driver；未传 `--private-family-marriage-formal-trial`，两个新consumer allow=false，原7opts/Guy query-only保持。 |

**最后R0407已完成：3/3正式query、0 gameplay/typed婚配动作、0日期。** allocator09:48:26.441013 UTC/execution4e52abb7-cf2e-416a-a64c-5d24bd7d957f，CK3 PID193704/创建20260930094836.427197+000、native-session146376/root唯一owner，once-owned最小化true/window1。新PID实际cold_checkpoint/active_resumed合法恢复h4019/actor29829/episode native-29829-2bc2d599f7f9；心跳2638→3008、mailbox0→8→14→19、native3→4，六次before/after日期均53220000，paused date0符合后台合同。

- 当前婚约actionability **available/reason=null**，闭合至 **production-live private observation primitive**：38822↔38718双向同帧；双方adult measure14、threshold16、is_adult=false、ready_to_marry=false；**final_legality_sampled=true表示采样发生，complete_can_send=false**。actor29829/recipient32897、AIraw1600000/answerraw0为query结果，十signedcost实际全0、effective-matrilineal=false、predicted outcome_if_accepted=betrothal、value **not_ready**。没有婚姻兑现/接受/联盟，两formal consumer仍OFF。
- Guy age3 pending/materialfalse/outboxactive，turn2checkpoint后turn3真实query消费且无重提；LIFE财富focus XPraw71250000/unused0/used7同帧、0新focus/perk。原R0406 unavailable失败保留；原P0观测RED只窄关闭，M4/M5与日期/战争资格不提升。
- strictcleanup/shutdown/treegone/proven/driverclosed/root无本机game/operator均PASS，owner/CK3control释放，当前本机无CK3或操作owner；watchdog_start仅不可变证据。本执行者功能/验收worker全部收口，无后续修复、动作、日期/cold包，仅本交接文档CI/集成/登记源码清理在途。

R0406 的 LIFE 同帧focus/XP/progress正式投影已达到窄 **production-live private observation primitive**：初native3/public4→末turn3 native4/public5、同raw53220000/actor29829，wealthfocus/stewardship XPtotal/within **raw71250000**、xp_per_level1000、unused **0**/used **7**。教育martial5且已有有效focus，不切focus或重复花点；旧centralization receipt/date53215920不是新perk。合法同actor/focus的raw53219928开局68125000→53220000读回71250000，是已计主线3日内 **+3125000raw** 的区间观察，不做每日估计、独占focus因果或新增日期累计；本轮3 query前后XP一致。M4两年及全perk门没有因此完成。

## 非战争实际边界与当前阻点

| 包 | 已可复用的能力 / 未闭合边界 |
| --- | --- |
| NW-LIFE | 开局/继承focus gate、有效focus保持、native revision机会刷新、pending独立receipt与下一turn消费路径已存在；本轮trigger源码追踪未找到新确定漏消费。#759补focusless低阶军事教育最小分支，#767补同帧XP正式report投影；当前0点正常no-op。没有新focus/perk提交或新perk收益。 |
| NW-ECON | 复用既有私有建设typed提交/receipt/恢复资格。当前farm_estates_01成本180金、authored月收入0.70是**只读机会**；warfuturecost/sharedcashcommitment缺项仍null，战时hold。无新扣款、开工、完工或实得收益；不要为完整ROI无限延后独立合法和平建设。 |
| NW-FAMILY | Guy38988→37909/recipient34332，age3/cutoff7、pending/material_result=false/outbound active；query ACK的accepted=true不是婚配接受。R0406历史turn2 checkpoint native4/h4019后turn3正式query，无重提。首继承人38822↔38718双向同帧betrothal/no-newproposal，未转婚或形成新联盟。 |
| 当前婚约观测 | R0406真实 **current_betrothal_application_main_unavailable/null**保留历史失败；#782修复未注册executors68/69后，**R0407实际available**且adult/final采样/完整CanSend/answer/十cost/lineality均读回。14<16、CanSend=false/not_ready为合法负结果，原P0观测RED窄关闭；未开正式婚配消费者，动作闭环仍待正常合法场景。 |
| NW-JOINT | m5 selector/dispatch/shortlist已存在；复用真实value与同帧资源承诺，pending婚配角色资源保留一次。缺战争现金/长期义务输入不能填零；候选数量、selected_step或ACK不代替正式消费。本轮无新联合资源typed动作。 |
| NW-ACTIVITY | R0403 counter1077→1555、同fingerprint的旧误判已窄关闭；opinion=-100、未selected、join负/arrival晚/CanStart=false保持hold。requested1但普通auto attempted/successful0/0、turns[]；无Invite/Start/下一普通turn/日期。H3928研究不替Robert。 |
| Prisoner / Faction / Council / Event | R0404/R0405/R0406 prisoner首帧完整count0是该帧真实空场景，旧ransom7金不重计。faction gift正式consumer/receipt/cold路径源码追踪未见新漏接，旧空recipient不代表当前；Council仍需自然阳性。0110已有同日county/legitimacy观察接线，当前组合CE1私有flag OFF、无新自然事件物质/下一turn/cold证据。无阳性不挂等待worker或新开专题长跑。 |

## 最新保存与下一恢复

R0407 turn2正式checkpoint **h4025/raw53220000/actor29829**，turn3query随后消费；最新full driver保留完整尾部。Robert仍 **3153/36524日**、G2/长期门不变。**h4019输入已实际新PID恢复，以下h4025输出未再次cold-tested**，下一次须由officialprepare/rebind判save/full driver/profile/ledgers兼容，不截尾或手改。

| 资产 | 完整路径 / SHA-256 |
| --- | --- |
| 最新save | `D:\nw-family-ba5-official-20260930\state\profile\save games\xar_checkpoint.ck3`；**6CB205C638F2945278DFE21DC26F3B3201D422E8BF6D39A3986D34335D190042** |
| 最新full driver | `D:\nw-family-ba5-official-20260930\state\native-session\driver-state.json`；**E9DA6761899A617344B39405D492A8F18C5E651C878436F75AD37615AF37F93E** |
| Guy pending | `D:\nw-family-ba5-official-20260930\state\player-child-default-formal-v1.json`；**7C36F5D77424F585629670D5304E5AFF7C265634A71B633BCE07CDB54185B9E5** |
| 首继承人ledger | `D:\nw-family-ba5-official-20260930\state\first-heir-marriage-formal-v1.json`；**6F007805A9CC5B602858AF9A670F2A6A591EE269E19C6301239422FFBEEAE0B3** |
| Prisoner ledger | `D:\nw-family-ba5-official-20260930\state\player-prisoner-ransom-formal-v1.json`；**D60736FB035B6E77D9F71641AD76B2006FB975CC1187C77CC2FB0BA91BAA115F** |

最新state/profile为 `D:\nw-family-ba5-official-20260930\state`；官配READY与freeze仍描述历史h4019输入，最新h4025输出以实际pins为准。正式report/operator-receipt在 `D:\ck3-nw-family-current-pair-ba5-candidate-20260930\operator-runs\family-current-pair-ba5-paused-query-3turn-1`，root终态证明为候选根 `FORMAL-TURN-SUMMARY.json`。复用已执行的严格wrapper本机zero断言，无额外WMI；本候选taskbus completed seq392/resources[]/next_step空，仅关闭这次在途验收。

## 战争消费与日期hold

- #762仅去除生产消费者多defender的残留单军条件，模型未改。实际R0404–R0405消费已交付有界路线：短步move与contact-safe advance；没有完整EU数值投影、远处2630 siege接战或全面战争资格，`COMBAT_ENTRY_EU_ACTIVATION_ENABLED=false`没有擅自翻开。
- **H3937 generic episodewide hold** 的scope/owner/certifier/date-release接口尚未定位，最新source仅按episode阻止同episode日期/move。任务总线已登记war-contact378、cash379、current-pair380及协调waiting382；没有改他们状态或永久hold，没有宣称owner已回复。screen release不等于date release，六项原始安全读口仍未实读0/6。
- 这是实际主线日期阻点，不影响paused query或独立源码推进；正常短步旧cfb日期证据不自动解除新hold。先沿已授权任务总线取得原责任人的精确frame/接口与release证明，再由正式合同恢复目标，不重建战争模型或以unknown永久停掉全部非战争包。

- 启动前root安全fetch已核上游 **fb32a5ca52aa51324abb0583c551223d4b8fcfd5**：新actor army-role私有query default-OFF及R0368 helpers，四共享native diff没有68/69改，Python0变化，本次3 paused query不调用新warstep。一次影响记录 `D:\ck3_task_tmp\nonwar-ba5-freeze-upstream-impact-20260930.json`；首shellquote失败未写、随后apply_patch记录成功，这是metadata失败而非游戏RED。冻结制品没有为这项无关增量重建或热换。

## 已交付源码与报告

| 交付 | 范围与状态 |
| --- | --- |
| #774 / #775 | resource query、action native **SOURCE_DONE**：exact官方CI与登记临时源码清理通过；私有入口默认关闭。源码资格不等于本次真实婚配/资源材料或动作成功。 |
| #777 / #778 | 兑现betrothal正式consumer与entry **SOURCE_DONE**；保留typed fulfill mode、同ledger pending、只有实际marriage判物质结果、cold mode/lineality/checkpoint fence。全consumer未在当前query-only候选开启，无新婚姻资格。 |
| #781 | R0406短两报告已合入 **c079cf76d1478206a03987864eb75e37026dc0dc**；exact官方master pushCI **36695427845 SUCCESS**，两blob与author2c43一致，remote/local refs、D源码clone/.git/index全部清理。回执 `D:\ck3_task_tmp\nonwar-r0406-report-cleanup-20260930.json`，SHA **6C6B36C5951D796D56AA3B91ACFB0867F0CD1420FE4121E2E0D531EB843EAB11**。 |
| #782 | executors68/69注册修复 **SOURCE_DONE**，master **7eb2785c8ffb8c3d3fcd9057bdd00f7b20cc7b31** /官方CI **36695436024 SUCCESS**；bounddebe remote/local/sourceclone已清理。`D:\nw-family-current-pair-app-main-20260930\CLEANUP-RECEIPT.json` SHA **60B7DFC53393128DCFFB7D5CEA80035C84B4879AB156C2F2C5D6F766148A7495**；BA5 DLL/index/ADMISSION、Debug/Release2+2与原R0406失败证据保留。 |
| 本交接 | 仅此文件及必要日报/周报，独立D源码，等待最后实际边界后commit/rebase/push。本文自身final SHA/官方CI/cleanup从真实后续receipt报告，**不预填future DONE**。 |

此阶段未新增公共MCP/协议破坏性变化；私有字段/default-OFF入口沿既有版本/schema消费，测试与source、fixture、no-launch、paused查询、typed动作、后置、下一turn、cold恢复分账。Git只rebase、普通push；协调者是唯一master写者。旧根脏现场和外部运行资产不随临时源码清理。

## 必须保留的资产与已知清理受阻

- **BA5运行依赖源码必须保留**：`D:\nw-family-current-pair-ba5-runtime-20260930\source`，source commit **7eb2785c8ffb8c3d3fcd9057bdd00f7b20cc7b31**、actual profile-selected revision **ba885d0f3d511da62cedcf9ffef1c864ab89cf60**、runtime fingerprint **866d01442eeb0c04040a9c3af7d85fbbcdb501b4ed6d0d77e458167c693eb48d**。它直接供official operator/profile和后续冷恢复使用，**不是已清理的#782临时实施源码clone**。
- BA5候选根为 `D:\ck3-nw-family-current-pair-ba5-candidate-20260930`，冻结索引 `CANDIDATE-FREEZE.json`，正式实际输出 `operator-runs\family-current-pair-ba5-paused-query-3turn-1`；官配根/state为 `D:\nw-family-ba5-official-20260930\state`，`D:\nw-family-ba5-official-20260930\PAIRING-READY.json`保留。冻结前的not_started/false字段是历史metadata阶段，后续真实identity/operator/终态单独证明，原索引不改写。
- Native origin **debe5d1d214e03d898565998c8bce6248f8d4786** 与runtime/master分别记：DLL `D:\ck3-nw-family-current-pair-ba5-candidate-20260930\release\xar_ck3_bridge.dll` SHA-256 **BA5E63CD18CD00B3C932D7AF37D91C22BE5275F7D5E6D03A9FAECB2148AC1055**；injector SHA-256 **5A43D73133E0BC200206666D58D7B888A03F578B6351C200F3F5A29BE8B25647**。provenance同release下 `NATIVE-BUILD-INDEX.json`，SHA **86B55FA14802D11DAA7AF0B788B68C64E3AF7A8AF71730B7C5AC64338FB106DA**；它引用的native实施source已清理，不沿旧路径重建或冒称仍存在。
- Exact EXE为 **1.19.0.6-steam23530548**，SHA-256 **2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86**，路径 `Z:\ck3_mod_rewrite_process_assets\ck3-frozen-1.19.0.6-steam23530548-20260922\game\binaries\ck3.exe`；沿官方no-launch/native provenance复用，未为交接重hash或重跑检查。版本/ABI改变必须另做匹配迁移。
- **single-use RUN wrapper已消费**：`D:\ck3-nw-family-current-pair-ba5-candidate-20260930\RUN-FAMILY-CURRENT-PAIR-BA5.py`，冻结SHA **A9BAC1B90CD15B153A6491BEBFC3B5718E4F4228CB85C540862188D3D3BBC771**，历史root exec78213。本文件不是通用可重跑启动器。下一次恢复沿仓库[官方配对/恢复入口](../../tools/g2_preview_operator.py)和最新合法save/driver的official prepare/rebind；重新冻结匹配候选并用当前owner/持久分配器，不直接复用历史run_output或编新命令。
- **PRV008本机ZIP实际可读**，SHA-256 **B9952E544C78D51F650FCBF252D2DE81B1E005B0EA5081880AEE9FDECC2BD9F3**。资格仅actor31853/episode native-31853-af642d76cb41、普通封建有界路径、mod/xar_autoplayer.mod、ordinary_campaign_succession/xar_off、未自然继承；不广告任意存档、无限无人值守、整局或双种子。其他机器实际获取未测，不把本机路径当跨机下载成功。
- 保留 `Z:\ck3_mod_rewrite\.task-tmp\PRV008-FROZEN-EARLY-PAIR` 与 `Z:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-ca852d1-20260922\release`。启动/停止/状态/cold命令只读 `Z:\ck3_mod_rewrite_process_assets\g2-preview-prv008-frozen-path-live-20260922\START-HERE.txt` 和 `QUALIFICATION.json`，不编造命令，不覆盖冻结版本。
- Robert原始/派生pair、Guy/firstheir/prisoner ledger、run identities、candidate freeze/profile/DLL/injector、R0401/R0406失败与各独立薄层，以及战争原始/派生pair都保留。最新输入/输出资格必须由官方prepare判定；目录叫.task-tmp不等于可删除。
- 三项历史工具策略拒绝 **#715/#726/#738** 仍为已知未清理边界，原因及登记owner沿原receipt，不换工具绕过或重试；本次报告包和#782已完成的清理不覆盖这些拒绝。源码branch/worktree已交付即按exact tip+CI清理，但运行依赖先解除，证据/制品独立保留。

## 下一维护者的最小接手顺序

1. 读本交接最后实际BA5段、[09-30日报](../autonomous-agent-progress/daily/2026-09-30.md)、[W40周报](../autonomous-agent-progress/weekly/2026-W40.md)、[G2要求JSON](../autonomous-agent-progress/g2-requirements-v1.json)及[状态投影](../project-state/current-state.json)指向的live source。fresh fetch master并核exact SHA；只核本包依赖，不重审全仓或重做已完成gate。
2. 核本机owner/受管进程、窗口与官方freeze；**不查别人机器**。Robert继续最新合法配对，由official restore判profile/save/driver兼容，不把新master热换进旧live/DLL，也不固定下一轮编号。
3. 复用已通过BA5私有current-betrothal观测，不重做registration修复。当前双方14<16/CanSend=false/not_ready与Guy pending，保持负结果不重发；只在正常游玩状态改变、原生完整CanSend与价值成立后沿既有formal trial/default-OFF合同提交，再证实际婚姻、下一turn及规定cold恢复。首继承人沿具体关系/提案权限，不借玩家本人权限。
4. LIFE有有效focus/0点继续正常策略；新角色首帧或真实点数及时评估。ECON独立合法和平建设按原成本/储备/收益先做一项，战时未知预算只约束相关比较；JOINT资源只预留一次。自然事件/议会/派系仅沿正常机会采集。
5. 对主线date/move先取得H3937原owner/certifier接口和精确release证明；战争问题留原维护者，非战争缺口独立修复。每次交付按真实观测→策略/合法价值→typed动作→独立后置→下一turn→规定checkpoint/cold恢复，exactmaster官方CI后立即清临时源码。

## 实际证据入口

- [R0406终态](D:/nw-robert-nonwar-postcondition-review-20260930/R0406-FAMILY-LIFE-ACTUAL-TERMINAL.json)，SHA **D1234F2495880B1EEE3BADC8531A362AAD834321D93D60DFF32D87E2B51082B8**；[R0406正式消费者与后台进展](D:/nw-robert-nonwar-postcondition-review-20260930/R0406-FORMAL-CONSUMER-DETAILS.json)，SHA **ECB5E0849F04626B55B17681C2A4DA0AC70A3080A4A515D1570A21961828508B**。
- [R0405冷恢复终态](D:/nw-robert-nonwar-postcondition-review-20260930/R0405-COLD-ACTUAL-TERMINAL.json)，SHA **249656C3597DA71E4F32F5A57EE74C72A3287741AC31A3AE713797F5AB2AEB18**；[物质后置/下一turn](D:/nw-robert-nonwar-postcondition-review-20260930/R0405-COLD-MATERIAL-POST.json)，SHA **908CCAE488484EF0C8F7FADA3E295CEA0340A9C6CF28551C492C09B7A6E9C42D**。大report和driver由唯一reader薄抽，不集体解析/hash。
- [BA5官配](D:/nw-family-ba5-official-20260930/PAIRING-READY.json) SHA **BB3AB71C00A76A7D2794C596333976D0660CEF7B2E5CDB82499AD7465708B5AB** / official no-launch **02E6350CDDBAE9AE3A9168CD969FB34ECB89F3628ADBE6EC6C0784DF7294A493**仅为官配阶段。
- [R0407实际薄终态](D:/nw-robert-nonwar-postcondition-review-20260930/R0407-BA5-CURRENT-PAIR-ACTUAL-TERMINAL.json)，SHA **F50D938ABCB27F526A072EB58465925794F759DB4BD5BB4EDBAE5AF167F0B00A**；[最后字段/保存/清理完整pins](D:/nw-robert-nonwar-postcondition-review-20260930/R0407-BA5-HANDOFF-PINS.json)，SHA **633E32C46019B7A42414DD07FA3B864C2E76983EDB8EE9C6BF96519C7C9FCE39**。唯一reader从既有薄层投影，未重读大report/driver或重新hash。
