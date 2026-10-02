# 罗贝尔 G2 接续 prompt

配套[当前现状与行动计划](2026-10-02-g2-robert-current-state-action-plan.md)记录 2026-10-02 晚间 v19 cold 与随后首批 actual 收口基线。这份文本可以直接复制给协调者；工作包 prompt 用于其并行代理。若已有更晚 ROOT actual 回执，继承最新真实日期、PID、配对与来源，保留本文基线作为历史，不回滚。

## 协调者总 prompt

```text
继续 Z:/ck3_mod_rewrite 的 G2 自动游玩与 CK3 最新 Steam 版本迁移工作。先读 AGENTS.md、docs/handover/2026-10-02-g2-robert-current-state-action-plan.md、docs/ck3-native-ai/README.md 和 docs/autonomous-agent-progress/g2-requirements-v1.json，按最新用户指令与 AGENTS 执行；旧 handover/README 的历史权限与数值不覆盖最新授权。

用户已经释放 CK3，Steam 离线，授权继续实机且要求高并发。当前唯一测试入口是罗贝尔 actor29829，原 episode native-29829-2bc2d599f7f9，ordinary_campaign_succession/xar_off，typed goal dynasty_continuity。保持原 campaign 及自然 successor，不创建 Murchad/rogue/Clan/Tribal/新 seed，不用 fixture 冒充实机。全程最小化/后台，不抢占 CK3/Steam/其它窗口焦点，不用物理输入。通用宗教暂缓，战争研究停止，WAR_CASH/PREWAR OFF；可消费已有 war/army 状态作为非战争与时间策略的依赖。

执行身份与现有资源：
- canonical delivery worktree：Z:/ck3_mod_rewrite/.task-tmp/g2dlv。原 root dirty workspace 保留，不 reset/stash/clean/force。
- Python：Z:/ck3_mod_rewrite/tools/.venv/Scripts/python.exe。使用 Python 与 cmd.exe（login:false）。命令结构化传参，避免复杂 shell 拼接。
- HERE：Z:/ck3_mod_rewrite/artifacts/g2-maintainer-2026-10-02/resume-12003。
- 当前 v19 source/native：716acfecc6c487e2b48942c6a6030c8b7012e5d5；runtime HERE/production-source-716acfec。
- 下一Python候选已发布：41291bf2315f11b6748affce318e1e456a6f8918；runtime HERE/production-source-41291bf2，freeze HERE/robert-planning-root-reuse-source-freeze.json，static-ready/未正式attach/未live。ROOT已生成HERE/MCP-ROBERT-PLANNING-REUSE-41291bf2-PLAN.json，file-only/live_executed=false。当前live MCP依然716；native/environment继续716，不能将412误记为当前DLL来源。
- 新 v19 state：Z:/ck3_mod_rewrite_process_assets/g2-robert-mainline-12003-v19-20261002/state。
- 当前 ROOT packet：HERE/m7-robert/robert-mainline-v19-716acfec-current-review-01/ROOT-PACKET.json。
- 当前 MCP plan：同目录 MCP-CURRENT-CANDIDATE-PLAN.json。
- Pipe：\\.\pipe\xar-g2-robert-1066-seed-66f926d。
- 已运行 managed game：PID70968 / HWND4333808 / 最小化。ROOT managed exec session11164 属当前会话句柄，跨会话不能假定还能使用。
- 最新 actual cold：同目录 actual-candidate-cold-goal-01/result.json GREEN，date_raw53220456，full history4076/save anchor4075，same goal/five ledgers/source prefix。最新 save SHA dd4d3f772147778e7308a85f0e09336b491f00ad4f6e067e1d11564dfb5d23ec。
- 已完成官方 prepare/verify/stage九streams/rebind/preflight/new-PID paused cold。当前已有游戏，不重跑已闭合这些步骤，不另启第二游戏。仅用实际 endpoint 定位现有 PID，若有更新则服从较晚 actual 回执。
- v19 DLL SHA677d2e195ee55e8000f3a6313353aa64cb843f8bda2f3e0dbec150b07dde2a8a；manifest SHA b4a6b8eb51fc5d4dd5184f2c223cb0d5472995c6a190bbc2a4865372d8827447。
- runtime/native source 与文档 HEAD 分开记录。716acfec 官方 CI37006646983 SUCCESS20:31:28，只代表静态资格。不要为其重复触发 CI/旧测试。

已经闭合的生产窄循环直接复用：CA1一次207prestige、生效/材料/next/cold；Steward32716skill11→43706skill14且Collect Taxes保留、材料/next/cold。不要重发法律或任命。
Sway原 full134217986/gen8 target34333；v19 newPID cold四查询已GREEN/native3，exactjoin/CanContinue=true/chance55%，三ringsseq0/rows0/nogap，外部cursor已切新70968。19/353、opinion-10和两modifier合法absent只属旧v16/PID101084/native28同日期warm实际；新completion无progress/opinion，不称新DLL实读这些值。无terminal/收益，不重发Start、不重复cold4。
Guy38988↔37909/recipient34332原提议：旧两个properconsumer child subject_changed RED保留；本次v19唯一properconsumer已GREEN/native4，child合法/双边物质关系合法absent，receipt pending/materialfalse/cold_absent_relation_unresolvedtrue，outboundabsent且id/age/cutoff全null，正常ledger已更新lastchecked→70968/native4、resolvednull。acceptedtrue只说明query成功。当前没有subject错误可修，缺口是原提议终态/原因不可观测；不得从日期/outbound消失推断拒绝或timeout，不重发、不替换pending，不阻断其它OODA。
第一继承人38822↔38718双向订婚、双方14/threshold16，complete CanSend=false，无成人婚姻/联盟。
Feast 尚无Start/扣款/full activity ID/terminal；旧Stages不能冒充cold后当前planner。v19finance006 actualavailable：maxmaintenance588600/Q100000=5.886gold/月，政策18个月分配105.948gold+原200floor=305.948gold；未fresh quote/currentwallet/currentownedcommitments，不借旧1206.59426gold填。当前provider完整budget调用尚未actual。construction只有Robert自己的公共资源与war/armyhold，没有private keyed baseline；不得引用Murchad type572/tuple。
v19派系005完整targetingvector当前只有liberty50331692，power32.455/threshold80/discontent0/month-3/dangerousfalse/watch，countyrows/exposures合法空；原populist188已不在当前vector，没有2111/2115新getter实际值。不能追空getter、称county非空primitive完成或据消失认M4干预收益。
首批实际证据：HERE/m7-robert/actual-v19-sway-county-finance-01/result.json GREEN；HERE/m4-sway/robert-v19-cold-70968-01/REPORT-FIELDS.json；HERE/m4-sway/robert-county-material-dto-01/V19-ACTUAL-REPORT-FIELDS.json；HERE/m6-feast/robert-budget-finance-01/actual-v19-readiness-01/ACTUAL-V19-FINANCE-READOUT.json；HERE/m5-family/robert-Guy-v19-actual-diagnostic-01/REPORT-FIELDS.json。直接复用，不再次读取以证明相同结论。
G2保持4/8（历史M0/M1/M3/M5），NW保持1/4。机器合同禁止overall百分比。Robert历史3153+本轮19=3172/36524，8.69%只表示持久日目标占比；不要把本轮材料扩为新的M5、整体M4/M6/M7或迁移全域完成。

现在按照以下顺序继续：
1. 复用已运行的v19paused会话与正式MCPmain/load_driver/sessionfactory。ROOT唯一拥有实际Game/window/process/SDK/pipe/state/Git；所有子代理只离线研究、写独占源/专题、读冻结artifact并返回patch/字段。
2. 复用已GREEN的Sway cold四查询、派系/finance两查询、Guy原properconsumer。原scheme按普通回合接续，phase/material/terminal或停机归档时读retained增量；不每turn重读所有六口。当前county合法空不追新getter实机资格。
3. Feast使用Robert wrapper和本次source provider重新fresh guest/location/Stage5/CanStart/cost/currentwallet/shared commitments，传actualfresh campaign rootfinance。维护费口是明确18个月分配，不是未来上界；保留200floor与pendingcommitment一次。全部门槛成立则唯一Start，独立扣款/activity identity，继续自然活动到terminal/material/next/所需cold；hold时明确依赖并做其它工作。
4. 同ROOT SDK owner以现有capture_baseline(service.driver, Path(new_external_out))读取Robert自己的首次private keyed建设材料，不开第二SDK/driver、不重复收入facade、不放开war/army新支出hold。
5. 并行Family包研究原Guyproposal最终结果/原因的现有原生入口；针对本次receiptpending/outboundabsent/关系absent的实际观测缺口，交最小只读capability或consumer接续。旧subject_changed没有当前错误可修；不加理论门禁，不重发、不按19日猜拒绝/timeout、不把此包挡在全部nonwar回合之前。
6. 恢复现有正式nonwar planner/service，沿原1/7/30时间策略与finite外置记录器持续回合并保存完整paired checkpoint。自然M2/Sway/成年/继承出现时按原registry与typed动作闭合观察→决策→操作→独立验证→next→规定cold。没有自然实例不要制造。
7. planning-only root去重候选已发布41291bf2/static-ready，五项focused生产链GREEN约1.06s：root3→1/plan material相同，stale fallback与receiptfresh通过。专题docs/ck3-native-ai/robert-nonwar-planning-root-reuse.md，字段HERE/m7-robert/nonwar-query-cost-01/REPORT-FIELDS.json。ROOT先用现成HERE/MCP-ROBERT-PLANNING-REUSE-41291bf2-PLAN.json，将412 Python正规attach现有716prepared environment/native/PID70968；下一normalfinite runner的--mcp-plan使用这个文件，再做一轮actual query数量/plan/同类回合计时对照。分别绑定Python/native身份，native无需重编/重启，不rebind旧env来伪装新来源，既有focused检查不重复。旧3turn planner80.471s，同paused三份root相同。仅同计划过程复用；跨动作/时间/独立验证仍fresh。当前未attach/live，新plan仍file-only，不预报收益。finite记录器已actual882MB→608KB，99.931%减少，完整history保留；无需重复其旧测试。
8. 持续把真实结果、失败attempt、source/native/文档commit、测试、artifact与遗留项交专职日报/周报owner合并。完成工作包默认普通git commit+git push，不另问许可。机器合同只有原整项门槛过门才改；需求JSON若真的改只运行对应validator一次。

并发策略：利用64槽位处理独立有价值模块，native使用--parallel64；M0/M1/M3历史complete不为占槽重审。先给每包写输入、输出、独占路径、依赖与一次验收。把M4拆construction/council/county response，把M6拆Feast/Sway，把M7拆timeperf/nativebuild/reports；getter/DTO/Pythonconsumer可在互不写同文件时并行。桥接总文件bridge.cpp/CMake、共享driver/service与报告只有一个owner，其它人交patch/字段。Game/pipe/Git顺序执行。idle/completed agent接续用followup_task。

每60秒内有进展时简短汇报新事实与下一门槛；只对同一结论做一次相称验证。复用原ABI/L0/fixture/成功业务证据，禁止重复广审计。工程ETA用T0范围，自然事件/Sway成功/成年/死亡不承诺墙钟时间。用户新状态问题或文档请求作为当前任务 steering，完成其交付后仍保留主线。
```

## 通用并行工作包模板

下面模板复制后填入实际任务和独占路径。64 并发是资源上限；每包应解锁一个明确结果，不能用重复审计占槽。

```text
你负责工作包 {包名}，服务当前罗贝尔G2下一实际门槛。ROOT sole Game/window/Steam/process/SDK/pipe/state/Git owner；你不启动/停止游戏，不调用live SDK/pipe，不写现场profile/save/driver/ledger，不提交推送，不改其它owner文件。

先读AGENTS和对应native专题，复用exact-build 1.20.0.3/Steam25652598 EXE94b55397...02a6已有证据。当前actor29829/episode native-29829-2bc2d599f7f9，ordinary/xar_off/goal dynasty_continuity。通用宗教暂缓、战争研究停止、唯一Robert入口保持。
唯一允许写入：{独占canonical文件清单}、{新外部artifact目录}。
给定实际输入：{冻结artifact/明确源码commit/完整字段}。
这次要交付：{具体结果与能解锁的业务}。
只做一次必要focused验证：{验收方式}。已有证明不重跑。缺实际字段时准备现成ROOT读取配置并说明参数，不猜值、不新开理论门禁，不把source/fixture/ACK算live。
共享bridge.cpp/CMake/driver/service改动只交最小patch给指定owner；按真实实际故障缩范围，不全文件覆盖public源。不要复制其它ruler材料。
完成返回：结果/原因；实际字段与时间/PID身份；source与文件SHA；验证与artifact路径；资格research/static-ready/primitive/loop/complete；未完成依赖；可合并日报周报字段；建议ROOT下一唯一操作。缺输入时尽快回报，让其它独立包继续。
```

## 八个 M 的工作 prompt

### M0：已闭合历史退出，保持原证明

```text
G2-M0 complete，战争研究停止。本轮只复用原三出口/材料/next/cold证据，不重开native战争树、prewar、WAR_CASH或退出矩阵。只有ROOT指出直接影响当前使用的实际故障才分析其最小非研究修复。没有新故障则无需派新代理，也不要为了64并发制造审计。
```

### M1：县领与 finance 新观测口的实际交付

```text
读ROOT新v19县领/finance冻结包，绑定actual actor/date/PID/source716acfec。负责解释同一公共MCP返回的county_title/capital/holder、int32scale1 opinion、int64Q100000 native final join score、CanAddCounty/queued/threshold，以及campaign root maintenance值。区分合法0/false/null与读取失败，不扩religion模型。县领派系188的县2111/2115不是人物Sway/gift目标。
当前v19 actual005只有liberty50331692/watch，countyrows/exposures合法空，原188不在当前完整vector。当前判读已完成直接复用，newgetters非空尚待自然实例，无getterRED、无当前威胁、无干预收益可归因；不为了补资格重复query或造county。
独占docs/ck3-native-ai/county-faction-material-12003.md及指定新判读artifact；finance专题由Feast owner写，向其传actual字段。若新生产DTO/consumer有真实错误才最小修复。字段缺失确实阻断实际决策时继续最小exact observation；合法空不等于缺口或阻点。
```

### M2：自然事件的精确接续

```text
按现有stock/exact registry与native树准备Robert自然事件consumer。ROOT给真实paused modal后，读本次full instance、可见native/authored option mapping、scope和材料定义；修实际出现的精确分支，交ROOT唯一typed选择与独立验证配置。不触发事件，不开另一seed，不把definition option_count当可见多选数。
独占ROOT指定event专题与独立consumer文件；共享driver/service只patch。M2原门槛三个自然事件且两个多选、独立material及正式续跑，不能降低。无自然实例则交已有确定性执行准备与明确等待条件，不编造live。
```

### M3：真实 successor 与目标连续性

```text
复用历史M3 complete，不重新跑旧继承矩阵。分析Robert最新完整pair中的实际succession prediction和typed dynasty_continuity，保持原actor/campaign语义。等ROOT真实自然死亡包时，逐title比较预测与真实分配、player successor identity、原goal继承及正常下一回合。
独占docs/ck3-native-ai/robert-1066-ordinary-seed.md与新对照artifact。禁止控制台die、强制继承、改goal/ledger/state或新ruler入口。只有本轮真实自然继承、材料与接续可增加本轮证明；当前new-PID cold已GREEN直接复用。
```

### M4：治理三个独立子包

```text
M4按原同一两游戏年窗口闭合建设、合法Council调整、真实封臣/派系干预。Steward43706skill14/CollectTaxes的材料/next/cold已完成，不重发。
建设owner：独占ck3-1.20.0.2-construction.md，准备同ROOT driver现有capture_baseline；读Robert自己的keyed tuple/cost/active/completed/收入，不复制Murchad type572。war/army支出hold保持，新private baseline不代表开工。
Council owner：独占角色专题，复用原树，用当前合法候选与已证明命名skill查询解释真实增益；默认NO_CHANGE或只建议有实际价值任命，不为覆盖角色降级。共享动作模块单owner。
县领response owner：独占county response专题/独立策略模块，先依据新actual县领输入落原生树再交最小可验证response。身份是县而非人物，不直接套gift/Sway；宗教专用模型不扩。
三个owner互不写同文件。ROOT唯一实机动作。每包给出实际输入、可执行或held原因、一次必要验证及对两年窗口的贡献，不因query或fixture更新M4完成数。
```

### M5：Guy 原结果与未成年履约

```text
独占docs/ck3-native-ai/ck3-1.20.0.2-family.md及新Guy最终结果原生入口/最小接续包。v19 properconsumer已GREEN/native4/date53220456，原pending38988↔37909/recipient34332不变，statuspending/materialfalse/cold_absent_relation_unresolvedtrue/outboundabsent/双边关系合法absent。正常ledger更新lastchecked→70968/native4、resolvednull。旧两次subject_changed RED保留，当前没有此错误可修，不重复诊断/read来证明已GREEN。
先按原生调用链研究原proposal最终结果/原因现有查询能否补；缺失确实让原response无法消费时交最小只读bridge/consumer接续、一次focused覆盖与ROOT真实验收配置。不依赖elapsed days或outbound消失判拒绝/timeout，不移除现校验、不扩schema/WAL/安全协议、不重发proposal/重排候选。该包并行，不阻断其它业务回合。bridge.cpp只patch由ROOT集成。
第一继承38822↔38718双方14/阈值16，保持minor hold；真实成年后才比较最终CanSend与履约材料。历史M5成人完成保留，Robert此支路不自动增加whole credit。不给联盟/回复deadline/时间推进推断材料。
```

### M6：Feast 与 Sway 分开完成业务

```text
Feast owner独占docs/ck3-native-ai/ck3-1.20.0.3-robert-feast-finance.md及ROOT指定activity模块/新判读包。v19 actual finance已available，5.886gold/月×18=105.948分配+200floor=305.948，未计currentcommitments/quote/wallet。复用该观测，重新fresh Robert actor/episode guest/location/CanStart/cost/currentwallet/managedledgers并用现provider一次完整budget；合法预算成立交ROOT唯一Start。跟踪actualfull ID、扣款、stock事件/terminal、物质结果、next与所需cold，不能借旧wallet/Stage5或ACK代替结果。
Sway owner独占ck3-1.20.0.2-sway-state.md及新rings判读包。原full134217986/gen8,target34333；new70968cold4已GREEN/native3/chance55/ringsseq0rows0nogap。19/353/opinion-10/modifier合法absent只属旧v16同日期warm，不称新DLL实读。复用cold4，沿正常回合；phase/material/terminal或prestop时才增量拉取retained。保持唯一原Start，真实终态与独立opinion/modifier变化才证明收益；合法absence不是成功0收益。
CA1窄loop已完成复用。M6原scheme/囚犯或制度/非宗教决议或法律/完整活动四门保持。
```

### M7：普通循环、性能、构建与报告

```text
Time/performance owner独占docs/ck3-native-ai/robert-normal-time-and-capture-cost.md及robert-nonwar-planning-root-reuse.md，已有planning候选五项focused生产链GREEN/静态root3→1/plan material相同/stale fallback和receiptfresh通过。候选已发布41291bf2315f11b6748affce318e1e456a6f8918/static-ready，待ROOT以现成MCP-ROBERT-PLANNING-REUSE-41291bf2-PLAN.json将412 Python正规attach现有716env/native，并做一轮actual对照。不重复focused检查、不为Python重编/重启native；当前live仍716，分别记两身份。finite capture已真实882MB→608KB、99.931%，15实际日保存，不改1/7/30。实际query数量/plan/计时由ROOT采集，再只读判读；跨动作/时间/材料验证仍fresh，未live不报运行收益。
Native build owner只负责ROOT指定新candidate artifact/cache，strict/W4WX/jobs64，正确绑定实际source/header/objects；v19只重编1TU+485复用的事实不能写全编。只有真实新native变更才build，保留RED，ROOT官方prepare/rebind/adopt及实际new-PID paused。
Requirements/report owner唯一编辑当日/当周报告与中央索引；他人提交字段。G2 4/8，NW1/4，Robert3172/36524（8.69%仅持久日），源/构建/窄loop不增加原整项。记录actual artifact、FAILED attempts、提交推送、门槛与下一依赖，原档4031只归档。
ROOT持有现有game/SDK/state/Git持续nonwar有限批次与完整pair，natural successor延续原goal，不开其它seed/government。M7广矩阵仍in_progress，本轮current goal cold/next已closed复用。
```

## 每轮交付回报模板

```text
工作包：
实际截点：Asia/Shanghai时间、actor/episode、PID、date_raw/source/native
完成结果与可见游戏价值：
资格：research/static-ready/fixture-live/production-live primitive/production-live loop/complete
实际动作：action/full ID、是否唯一提交；只读则0动作
独立后置与next/cold：实际字段、已过门/未出现/RED
验证：仅本次必要检查，复用旧证明注明入口
artifact与SHA/source文件：
保留失败attempt与真实原因：
持久新增日与最新完整pair：不计未保存推进
G2/NW分母与本包贡献：禁止整体百分比/越级credit
剩余依赖、ROOT下一唯一操作、T0工程ETA与自然不可承诺项：
日报周报合并字段与commit/push：由ROOT/指定report owner写
```

阶段结束默认提交推送已完成包，主线继续。当前 v19 已后台 paused，实际查询与正常循环已经获得授权，继续执行；若后续用户重新占用 CK3 或改变窗口权限，按届时明确指令调整。需要窗口的阻点必须说明具体必要步骤及对应限制，同时继续其它独立后台工作。
