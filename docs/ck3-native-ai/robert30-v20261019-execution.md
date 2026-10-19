# 罗贝尔三十年 v20261019：新局执行记录

用户在2026-10-19明确要求：后续评分结算片改为15秒，旧片不改；复盘首局并写入智能体；随后从1066重开罗贝尔三十年v20261019；继续性能优化及高并发G2研究。这一指令解除旧交接的“暂不开下一局”。

**当前指针（2026-10-19T04:35:29Z现场边界，04:48Z汇总）**：`machine_id: xenoamess-full-tower-eb9d2c1186`，新局已推进61实际日、74个完整周期；AUTO194只读月检完成，第二次决策发布失败，pending75/next195。最新正常SAVE仍是第30日，不能据此恢复后宣称保留61日。当前业务SDK为`063531c4`、Game214568/原birth、Native25；Native26已构建并完成离线检查，尚未加载。以下较早时点均保留为历史快照。

用户追加要求以长期性能和实际游玩效果为优先，不追逐单次执行速度。阶段目标仍为≤1秒/实际游戏日、0.5秒为后继目标；完整运行账须包含查询、规划、持久化、中断及修复间隔。短连续窗口12日/5.978826秒只能定位潜力；已闭累计38日/3075.207607秒为80.926516秒/日，未达标，不能重置起点隐藏维护成本。来源见[墙钟账](evidence/robert-v20261019-closed-wall-ledger03.json)和[长期增长分析](robert-v20261019-long-term-growth-2026-10-19.md)。长期效果另核领土、财政与军费、战争后果和继承，不用完成动作数代替运营成绩。

执行机器为 `machine_id: xenoamess-full-tower-eb9d2c1186`，本轮由 `tools/ck3_live_run_id.py machine` 实际读回；本节记录时间 `2026-10-19T02:07:20Z`（clock工具）。此时仍处于新局启动准备，**新Game、首次1066存档、普通推进均尚未发生**。后继运行事实另追加，不倒填本节。

## 已交付源码与复盘

已实际普通推送的公共源为 `d90d5e79ac7d22b3376ca70f3fccebd3faef516f`（本地b417f430经fetch/rebase后的身份）。[首局复盘](robert-first30-lessons-2026-10-19.md)区分已确认的AUTO193授独立、知识/定义ID绑定错误、主线修复未证明冻结场采用、陈旧held缓存和缺失运营采样；不把统治县10→2全部归因于一个窗口。

版本化[经验目录](../../tools/g2_saved_campaign/robert_first30_lessons_v1.json)及[实际采用复验](../../tools/g2_saved_campaign/qualify_robert_first30_lessons.py)让新SDK与已审固定源码逐叶比对，再由实际loader核新state中的民粹知识跨ID复用。它不是游戏业务通过证明。公共[评分入口](campaign-score-presentation-v1.md)现为450帧/30fps/15秒，全部九章保留；旧60秒评分片、首局09成片及无声素材未改动。[月度日历叶](campaign-score-monthly-cadence-v1.md)使用CK3固定365日/raw24，计划1066.9.15→1096.9.15；实际截止接线和完整评分输入仍须分别验证，纯叶不授准点能力。

## 并行研究及采用边界

| 包 | 已完成内容 | 此刻边界 |
| --- | --- | --- |
| M0 | [反抗领主战争白和政治代价来源](g2-m0-research-2026-10-19.md) | 原合同complete保留；不改投降倾向，不当作本局已发生处罚。 |
| M1 | [fresh direct县与realm未知分离](g2-m1-research-2026-10-19.md) | additive turn bundle，未知不能误报空集；不是完整realm失地跟踪器。 |
| M2 | [98条知识携带及旧批事件闭合](g2-m2-research-2026-10-19.md) | 新state仍需实际迁入；7条exact-only保留限制。 |
| M3 | [resident继承P51采用与期待时差](g2-m3-research-2026-10-19.md) | 软件组合已验，实际新运行采用和自然继承待观察。 |
| M4 | [合法贷款决议门槛/十槽费用源码](g2-m4-research-2026-10-19.md) | C++未编译/部署，完整本金债务及到账unknown、资金信用0。 |
| M5 | [非主导宗主战争风险覆盖缺口](g2-m5-research-2026-10-19.md) | 无新采购权限；目标命中不等于必失地。 |
| M6 | [generation0观察修复及完整采用闭包](g2-m6-research-2026-10-19.md) | 真实新增具名收益→自然有用终态→普通消费仍缺。 |
| M7 | [新Game冷恢复后的resolved义务缺口](g2-m7-research-2026-10-19.md) | 后继限定lineage源码继续研究，不迁pending/UNKNOWN；更多seed/government未补。 |

G2原定义仍为M0–M7，**6/8**。六个原完成项不重开验收；M6/M7为剩余重点，研究与录制/游戏成绩分列。

Python首批性能优化把派系历史查找从全量收集改为惰性逆序，16种旧新路径等价、新增3例通过；8853行最近4行命中的局部测量0.519→0.041毫秒，miss路径略慢。原战争测试一个宣战断言在旧新helper均失败，未为测试改变策略。第二批大combat过期帧前置拒绝候选此刻尚未提交/冻结，不能计入当前新SDK。

Native [四条临时JSON字符串边优化](knight-json-streaming-performance-2026-10-19.md)只有固定源全文守恒验证，未编译/部署，不能称实机提速。新局计划复用已资格Native25；最终DLL/EXE与广告仍由本次实际启动核对。

## 新局准备与容量

唯一现场owner为runtime准备线程。旧screen声明已按精确CAS退休，旧Game51028退出1及旧异常闭场原样保留；新租约由既有keeper维护，不复活旧PID。用户再次明确确认Steam离线。runtime已在新外置attempt取得窗口位移与亲审离线图（2026-10-19T01:57:13Z），没有切Steam在线、重启ToDesk或操作个人OBS；这只是该时点准备事实，不替代未来必要的新鲜检查。

业务SDK已按公共d90d5e79的canonical Git对象冻结1420叶、58,720,484 B；为满足真实environment/runtime消费者一致性，另建同commit的clean sparse host，保留旧host与第一次freeze历史。候选根为 `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01`，实际运行/profile仍待安装。旧P51会构造退役蓝窗且要求overlay HWND，因此当前正在将新录制入口、relay ACK与门禁迁到现有无窗口decision-text publisher；禁止只换标题或伪造旧HWND。

[本机新容量摘要](evidence/robert30-v20261019-capacity-summary01.json)记录新的64GiB首阶段峰值与24小时复核，截止 `2026-10-20T01:48:56.993837Z`，并行小研究256MiB包含在总额中。全部其它预留621,808,745,452 B与首局OUT146,027,527,160 B继续保守计入，未把旧例外、删除epoch或free当新授权。旧媒体三个派生候选仅列计划、没有删除。C/Z重型写入未准入；小型必要配置及源码记录与重型资格分开。

下一步沿既有清洁开局入口完成真实Host/App/Queue/Native/EXE绑定、知识迁入与一次采用复验、无旧蓝窗录制、原生frontend选择1066 Robert及初始SAVE；普通推进前落实同一次native sentinel arm的日期截止。当前尚不报告开局或任何新游戏日。

## 02:26后继：新Game进程已启动，游戏日尚未推进

同一 `machine_id: xenoamess-full-tower-eb9d2c1186`。runtime owner于2026-10-19T02:26:24Z取得新启动回执：Game PID214568、birth FILETIME134368503807325674，新profile/0 mod/无旧SAVE，Native25 DLL仍为 `a1448baa860a88826cbb9ae50ab67c93506560f2772c0515e4ef51e934002f40`，新pipe `\\.\pipe\xar-g2-robert30-v20261019-campaign01`。注入子进程exit0、tree-gone；主Game句柄由原supervisor持有。实际来源为外置新场的 `ROOT-ACTUAL-GAME-LAUNCH.json`，记录路径由后继完整运行清单固定。此刻MainMenu尚待录制放置/实际像素准入，App/Queue尚未启动，不能计1066角色、初始SAVE或新游戏日。

新SDK/state对固定reference的实际经验资格attempt02已PASS（23202 B/SHA `f25b10da60b545f52fbb2a0ba70d7a46caf13475b4e1fc54c73b5d236f26d147`），含已审民粹知识cold-ID绑定。attempt01因经验目录把 `bridge/native_driver.py` 误写为根路径而FAIL；该数据错误已精确修正，原失败保留，不能把它写成SDK缺失。三个真实newSDK清洁frontend软件合同已通过；早前fixture旧schema/换行溢出及旧import优先级问题保留其诊断，未放松生产门禁。

日期截止公共实际driver/executor/Protocol软件组合已完成5项，覆盖单Arm多日、Plan/target一致、Sway内部规划旁路、route窄收尾和终点不再resume；新Native25运行tuple真实采用仍待首批结果。后继combat过期帧优化22种等价与4项回归通过，4MB合成输入0.5333→0.0020秒，不能外推整局。原生JSON优化现有9组C++字节/SHA一致验证；109.28→108.02毫秒的计时区间重叠，不认定可靠提速。EXE登记不可用已保真实回执，实际采用经授权的独立Python/DLL离线备选，没有更改Native25/系统设置。

M7后继源码已补完成resolved台账与精确checkpoint的新Game谱系：原证明精确保全后才能退役，pending/UNKNOWN不迁移，原 `_checked` 不放宽；普通AUTO零新增查询，仅resolved SAVE多一次真实小帧。软件消费者组合及旧进程不可观察分支分别定向验证，当前不计新实机/G2完成信用。全部后继源码将一次合批冻结后再启动App/Queue，不热换正在运行的App。

## 02:36后继：最终业务冻结完成，录制首试正常清理

同一 `machine_id: xenoamess-full-tower-eb9d2c1186`，观察时间2026-10-19T02:36:06Z。后继源码已实际推送为 `dc4b7d56787ac769c809d1ab0d7b6057be2377e6`，业务SDK采用src02共1423个Python文件、58,769,189 B；保留Host/Game的d90d5e79身份。实际采用目录与独立Git对象reference进行经验资格attempt03，PASS，回执22,718 B，SHA `5eefe8e98d70908d80edaa77493ea0396b728ab7c367116aa9f89e3458720743`。此前失败和通过回执均保留。

来源固定在同一外置根 `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep`：`robert30-v20261019-campaign01/runtime/ROOT-FINAL-SDK-FREEZE-P37.json`（399,506 B，SHA `db68e72afa3ef6e562af656ad0b341471e4ee63f52e011405ff3ba3b22912c95`）、`p51-fresh1066-v20261019-prepare01/PRE-APP-SOURCE-ADOPTED05.json`（3,398 B，SHA `3d00b102c9389f49fc23484b5368d823a444f8cd700f4723792a5ee7dbe16ee5`）及该准备目录的 `LESSONS-QUALIFICATION03.json`。M7只提取小型相关pins，未复制完整inventory或读取活Driver。

专用portable OBS配置范围已获得实际存储追加准入，计入原64GiB而非新增预算；个人OBS及二进制不写。来源 `D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/STORAGE-ADMISSION-OBS-SCOPE01.json`（7,573 B，SHA `e951f2eeba0afdb153a613290f70c876c147a951ac9cd4c654d9139a7cda4179`）。02:33:26Z小型容量观察为D可用891,818,803,200 B，距既有guard 73,498,543,132 B；不是新的全卷预算。

录制首attempt的自有OBS PID181812抢焦点，实际foreground由Steam HWND52505028变成该OBS HWND83305260，触发原守卫；worker随后正常OBS exit0并确认inputs_unbound，失败MKV仅约13KB。Game与decision-text publisher保留，未恢复或操作用户窗口。此刻仍为MainMenu、App/Queue未启动；修正仅在唯一runtime owner处进行，尚无1066角色、基线SAVE或新游戏日信用。

## 02:47后继：录制阻点与并行后继

同一 `machine_id: xenoamess-full-tower-eb9d2c1186`。第二次录制启动 `a30b0a91-c277-49ca-a984-1269e809166b` 的自有OBS PID2396仍触发原foreground守卫，已正常OBS0/unbound；新增诊断将变化定位到 `Qt653QWindowIcon` 隐藏主窗，而非首次向导。显式tray/SW_SHOWMINNOACTIVE没有解决实际故障。AGENTS.md:503明确要求最小化且不抢焦点，因此未采用隐藏自有窗占foreground的放宽方案。下一候选复用已有AppView路径，将retained-generation唯一自有OBS主窗移至Game所在Desktop1，不激活、不切桌面、不恢复用户窗口；原最终foreground守卫继续执行。来源为runtime的失败attempt与 `p51-obs-owned-desktop-review01` 四项合成资格，后者不代表实际移动成功。Game与publisher保持，仍MainMenu/App未起。

首失败worker的原请求实际有PID250672/birth134368507483354329；08诊断曾误读为未留birth，后继已更正。其当前进程不存在不等于历史exit0，历史exitcode保持unknown。存储追加范围仅按精确request tuple、当前absence/空端口/未armed未started/OBS正常退出及无写占用核验许可专用配置归档和新profile，不扩大64GiB或删除媒体。

[M1月度来源映射](g2-m1-monthly-observation-source-map-2026-10-19.md)确认当前普通月度数值仍只有gold；已有cash-v2尚未进入同帧MET，不能把AUTO前态财务移到动作后月点。[M5参与战争事实后继](g2-m5-participating-war-threats-2026-10-19.md)确认普通战术已有all-participant敌军覆盖，并给出未接消费者的去重关系投影；CB及双方主将已有query DTO，剩余重点是后果消费者与未发布宗主战争范围，不新增采购/投降权限。

WAL实验恢复修复及98项知识实际迁入观察已在 `b000c9a623eec88a48c95a2f8e2ad72eaf59198e` 推送。[隔离资格](evidence/driver-wal-qualification-2026-10-19.json)保全144行全部字段，JSON键顺序差异及首失败不隐去，计时缺失保null。实验仍default-off，不修改当前src02；后继性能源审计发现只读query本已有延后持久化，不能将所有零日回合都归因于完整写入。研究与现场并行，不把未采用候选、软件测试或等待自然证据计为G2完成；仍6/8。

## 03:44后继：真实T0、18日与阶段性能目标

同一 `machine_id: xenoamess-full-tower-eb9d2c1186`，本节汇总截至2026-10-19T03:44Z的唯一runtime owner及已封存小回执。用户明确将阶段性能目标调整为**≤1秒/实际游戏日**，0.5秒保留为后继目标。10950日分别对应3小时2分30秒、1小时31分15秒；以端到端墙钟除实际日期差计，零日规划/查询、持久化及运行中恢复间隔均保留，启动/录制准备另列。

03:02:45Z真实原生frontend选择1066 Robert，03:04:29Z SEM确认actor31254、episode `native-31254-6271ac8cd441`、raw53144328/1066.9.15、paused/map_ready；03:05:39Z首次SAVE成功。保护的T0为外置运行根 `robert30-v20261019-campaign01/runtime/baselines/robert-v20261019-T0-1066-09-15.ck3`，68,936,116 B，SHA `381e832bb3122b1c544d5bcd505eb86b4d40456a4d37969bcf208714d0aa88f4`。终点raw53407128固定10950日。来源与实际SDK/Native/首SAVE pins见[M7真实新局证据](evidence/g2-m7-v20261019-fresh-campaign-zero-day-2026-10-19.json)。[M1离线T0投影](g2-m1-robert-v20261019-T0-baseline.md)实际一次SAVE解析得到realm10县、直接地理county2、direct holding4、house174/dynasty174、宗族8县、现金257金；Native domain size/limit及E/M/H仍unknown，不把旧局数值挪用。

03:25:33.905006Z新录制UUID `9222b897-e0d6-42d5-9062-55f8e2c58317`实际启动；专用OBS留原Desktop2最小化，未移动AppView、未切桌面，前后foreground保持Steam HWND52505028。实际map/HUD审阅通过，无旧蓝窗或影片标题。[无移动录制证据](evidence/p51-obs-no-move-recording-2026-10-19.json)保留此前失败；02:47提出的AppView候选后经实际验证会切桌面，已弃用，不追认成功。

普通完整规划已实际推进18日，当前47个settled cycles、pending48/auto_verified。AUTO109及MET110均已完成，故障发生在将MET110写入 `CURRENT-INPUT.json` 时的WinError5。原P37B Queue231428实际exit1、App258172实际exit0，owner退出1，`normal=false`；Game214568、Native25、OBS141536及publisher273652保留。来源为准备根 `SDK-METADATA-ROTATION-REQUEST31.json`、`MET110-TEXT-PUBLICATION-RECOVERED32.json`及运行根 `ROOT-P37B-OWNER-CLOSED.json`。M0将原552B不可变投影重新发布获得真实TEXT_PUBLISHED，0新AUTO/MET/RPC；[小回执](evidence/p51-current-input-replace-retry-2026-10-19.json)区分这次replace成功与未实际触发的重试。必要SDK-only维护保留原47/48状态，仅一次消费原MET110，之后从新sequence继续，不重发游戏动作；[软件组合资格](evidence/met110-warm-resume-software-qualification01.json)通过，现场暖恢复尚待实际读回。

[已闭墙钟账](evidence/robert-v20261019-closed-wall-ledger01.json)首FULL11为61.535486秒/10实际日，即6.1535486秒/日；从首AUTO9至FULL11闭合含零日首批和48.413089秒间隔为110.445645秒，即11.0445645秒/日。此后开放批和修复间隔尚未闭合，不能据此报告全局平均。AUTO50的8日耗3.000531秒，AUTO74仅2日却耗30.314162秒；后者原生event已出现而新date-only predicate漏接，导致无效等待。已修复为复用原完整早停条件；[同输入软件复现](campaign-clock-throughput-2026-10-19.md)保留同6命令/同实际2日/同cancel、无重resume。集成测试40项及75子测试通过；首次Root测试缺PYTHONPATH导致collection失败，正确环境后通过，不隐藏首次失败。未以软件计时认定已达到1秒/日。

同批Python候选还包括[有界JSON编码](driver-bounded-json-encoding-2026-10-19.md)、[等价历史尾扫与规划分层计时](planner-battle-tail-lookup-2026-10-19.md)、combat V3仅复制待修改的两层容器及完整递归重验、[owner响应单次编码](robert-v20261019-harness-performance.md)。各自资格保留字节、顺序、拒绝与隔离行为；局部CPU收益不换算为实际秒/日。本次维护不更换Native25，WAL仍default-off。

[M6首次真实Start](g2-m6-first-natural-start-2026-10-19.md)已确认fullSchemeID2/generation0及随后8日普通推进，尚未观察first gain或自然terminal。精确Native25的1.20.0.4外层非战路由白名单遗漏completion-termination常量，虽然handler/serializer已链接，实际入口仍unsupported；本次SDK维护仅关闭该不支持的optional query flag，保留Start、completion、opinion及完整普通/战争规划。后继Native补gate单独验证，不热换当前Game。M7真实新局不等于cold或自然继承，G2仍6/8。

## 04:48后继：连续稳定性与运营反馈合批

同一`machine_id: xenoamess-full-tower-eb9d2c1186`。原MET110已一次消费，同PID暖接续通过，不重发AUTO109。其后117暖开场锚、130 Crown pending字段、143多callback和147目标日暂停发布先后暴露执行链缺口；[恢复源清单](evidence/c3-recovery-source-ready-manifest01.json)与[157–160实际采用](evidence/c3-clean160-actual-adoption-readback01.json)保留原错误、有限修复和业务完成范围。160采用后正常推进16完整周期，累计74周期/61日；194再次因旧publisher同parent固定文件名碰撞中断，尚未采用永久ordinal修复，不能把source-ready当运行已修好。

194冻结来源为外置`D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-auto194-source-review01/META.json`，10,433B，SHA`6cf39a4277e95cf660840e2728c201fc779497cc0b16c237c03a99f06cc0d1aa`，观察时间`2026-10-19T04:35:29.426190Z`。existing Sway2/gen0在native98/raw53145792完成只读月检，pending为空、下次raw53146512；未新Start，普通fallback第二before-submit失败且未dispatch。只结算这个只读前缀，不重194、不计完整AUTO75。最新正常SAVE142仍raw53145048/第30日；精确清理后由原owner正常保存61日，再用实际SAVE响应构造续行输入，不能信旧累计state中的checkpoint字段。

下一次正常维护一次采用[多callback发布修复](evidence/p51-auto143-subdecisions-2026-10-19.json)、[目标日原生暂停等待](evidence/campaign-clock-target-pause-publication-2026-10-19.json)、[Crown完整来源上下文](crown-pending-publication-context-contract-2026-10-19.md)、[月界财政/root采集](g2-m1-monthly-met-production-2026-10-19.md)和[新root使旧继承预期失效](ordinary-succession-operations-feedback-2026-10-19.md)。后两项不增加普通非月界查询；月界两次Native捕获分列，不能标成同一capture。Crown提升不被当作分割继承的未经证明补救。领土与宗族低频反馈继续复用正常checkpoint，缺失链不能按确定失地计。

[Native26构建](native26-performance-build-2026-10-19.md)完成121/121对象、612 archive payload和离线JSON/CB/M6检查，DLL SHA`eaee4443f083ae5055232b908fdb5c6555aa75084801fd24654224b090032184`。当前仍Native25；actor gate默认关闭，四族历史耗时不能当当前收益。[M7具体cold方案](g2-m7-native26-cold-plan-2026-10-19.md)要求新SDK/新publisher精确绑定、最新SAVE/Driver/Sway侧车、实际新Game birth及新鲜Steam离线画面；旧receipt和captureEpoch保原来源，不重Start。M6仍无自然正收益/终态，M7无本次cold或自然继承完成信用，G2仍6/8。

并发调整：runtime维持唯一现场owner；M0封存194并交永久发布修复；harness处理精确只读清理与下一bootstrap元数据；Native构建已闭场。M1继续补领土成员完整性，M3完成fresh-root失效接缝，M4继续军费借款本金getter，M5审主动割地后果消费，M6等自然生命周期，M7准备真实cold；Python性能线审自然持久化增长，存储线按统一策略低频监测。已有研究闭场，不重跑旧矩阵填并发。现有WAL仍关闭；完整Driver重写的成本随history增长，先记录自然屏障/候选连续段，再决定是否启用既有增量机制，不新造框架。
