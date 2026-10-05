# 2026-10-05 G2 后台接手施工

## 本轮交付结果（2026-10-05T19:48:26+08:00）

八个实现包均完成有限static-ready验收，源码整合 `4733655173e65be99c9ffaafbe2d9275940df4d6`；五项原生CTest、生产bridge编译及新增compiled-wire消费链GREEN。两项功能source研究额外闭合。新增实机/游戏日0，下一步仍只可做后台；本页末尾逐包列出真实验收、RED修复、剩余项和Git发布。DLL是默认离线构建，不是已部署runtime；用户原现场、交接树与v73冻结保持保全。

实际接手登记时间：2026-10-05T19:14:19+08:00（Asia/Shanghai）。本页接续 [v73 休假交接](2026-10-05-g2-v73-war-background-maintainer-vacation-handoff.md)，记录后续执行，不改写交接时的事实。

用户本次明确要求：“注意，不要开启ck3，我自己要玩。你先只做后台能做的。”并允许最多 64 并发。**当前只进行离线源码、测试、编译、文档和 Git 交付；游戏及界面由用户使用，实机推进等待用户后续授权。**旧交接中允许恢复游戏的指令仅代表当时授权。没有启动、注入、连接、查询或操作 CK3，也不更改用户游戏配置、存档、工坊缓存或 Steam。

源码基线为 `origin/master` 的 `3f2025ca8cfac4e298210925ca0e472025ae5d51`。Root 使用独立 detached 工作树 `Z:/gb0`；八条实现线分别使用 `Z:/gb1`–`Z:/gb8`，隔离共享 bridge 文件的并行编辑。原仓库用户现场、`Z:/g38` 交接树和 `Z:/g78` v73 冻结树保持保全。工作树登记在外置 `Z:/ck3_mod_rewrite_process_assets/g2-background-20261005/lanes.json`，构建与报告回执也写入该外置根。

## 本轮工作包与验收

| 工作包 | 交付目标 | 离线验收及后续边界 |
| --- | --- | --- |
| 完整路线 ETA | 在现有行军查询发布 signed Q100000 prefix durations 与最终 remaining；不重复减 current progress | 新路径 fixture/序列化与 consumer 验证；实际抵达、paused readback 待实机 |
| 独立器械军参围资格 | 发布实际省份 CUnit occurrences、原生 Army、完整 eligibility 和合格 regiments | 复用已闭 native 资格树；K/M/D 实际变化及器械抵达待实机 |
| chunk 数值补员 | 接入现有军力字段的整数算术 consumer，区分合法零与缺失 | chunk cap、截断及已有输入路径测试；不预测未知 F 或下月到账 |
| 损耗分配 | 发布按 stored order 的 supply、siege/raid writer requests 与可计算边界 | 精确算术和 missing-input 用例；未闭最终 setter，不能称最终兵损 |
| 首次接战人物输入 | 补 source-closed `pre_291e210_1640` 与两 registry bindings | DTO、源阶段和消费路径；完整 Entry/人物构造仍部分完成 |
| 实际战场 geography | 通过现有 battle transition/control 发布 terrain、width、retained crossing/holding | 原查询权限和三路径保持一致；不将 retained geometry 当未来接战输入 |
| 盟友拒绝原因 | 原生 CanSend=false 返回 typed rejected 和完整 selected terms | 一个受影响调用用例，零 command/ACK；unknown 保留原异常 |
| 普通 holy order hire | 接入 source-closed 普通 typed provider、dispatch、MCP | 构造/注册/序列化离线测试；雇主、扣款、public CUnit 后态与 live 待验 |

本轮按必要性开八个并行 owner；64 是上限，不是必须占满的目标。Root 唯一源码/Git 整合者，并集中验证新增 native 目标；本机构建采用低优先级、有限编译并发，避免与用户游戏争抢资源。每包一次与风险相称的验证，复用交接中的研究和旧构建证据，不重复旧实机或全 EXE 扫描。

`open_kaishek` 预验：本轮工作对象为 exact-build 原生内存 DTO、序列化、typed consumer 与 native command 布局，不属于 CK3 脚本 parser/finite-runtime 可覆盖语义；记为 `not-applicable`，使用相应离线 fixture。实际失败 attempt 原样保留，测试通过只记 `static-ready` 或局部静态资格，没有真实 paused artifact 不增加 live 信用。

历史日账维持 **5035/36524 正常保存日、resume1882、10-05 +377、G2 5/8、NW2 2/4、自然继承0**。末 whole h9048 和零日 normal h9052 同为 raw53265168；用户自己的游戏进度不计入自动任务。本轮新增自动游戏日为 0，War117 的实际结算、3711 攻占、完整战斗 forecast 和原战役长期目标仍未完成。

结果、测试及提交随每包交付追加在下方，并同步至当天日报和 W41 周报。


### BG-1 盟友拒绝 consumer 完成（2026-10-05 后台接手）

完成：已观测 CanSend=false 经 registered MCP → service → driver 返回 typed rejected，完整保留 C88、first-failed、报价和战争关系；零提交、无 command ACK，unknown 继续原异常。解决旧 helper 丢弃已采样拒绝原因的真实消费缺口。源提交 e2ef3c8d，Root 线性采用 99329688；本报告随该包普通 push。

验证：`python Z:/ck3_mod_rewrite_process_assets/g2-background-20261005/call-ally-diagnostics-gb7/run_validation.py` 两个聚焦用例一次 GREEN，1.576 秒；diff check GREEN。回执与原日志位于同目录 ROOT-DELIVERY.json / VALIDATION.json / validation.log，未重跑旧测试。Readiness 为 Python consumer static-ready，仍无新 live、邀请/参战/扣款或游戏日信用；5035 历史日账不变。下一步为其他后台包整合；动态 C88 和真实邀请独立后态等待用户实机授权。

并行拓扑追加：在八个实现 owner 之外，新增两条仅消费缓存/冻结窄窗口的功能研究，分别闭合最终兵损 setter2657EA0..2657F0E 和 Entry post-A/B291C2B3..291C334。必要性是这两个已知原生输入缺口仍阻碍完整数值/接战消费；不重复已闭树，不接触运行游戏。Root 合并其知识和报告，原实现不等待研究结果。


### BG-2 chunk 数值补员 consumer 完成

完成：现有 `query_army_strengths` 新增 `same_input_replenishment_v1`，按真实 full-DATA operands 计算条件 chunk 请求；chunk maximum×prepared、64位乘法、trunc0、缺额封顶、qualified native0和重复identity alias均保留。解决已有字段尚无数值消费的缺口，不聚合alias或猜未知 F。源提交21e0093c；Root线性采用并随报告普通push。

验证一次：`py ck3_autonomous_player/tests/unit/test_replenishment_numeric.py --artifacts Z:/ck3_mod_rewrite_process_assets/g2-background-replenishment-20261005`，5个聚焦用例GREEN，覆盖现有service消费、算术/截断、合法q0、missing F、alias/conflict和coverage。diff check GREEN；回执同目录 ROOT-DELIVERY.json / offline-validation.json。Readiness为数值consumer static-ready；没有新native构建、game/pipe/UI/Steam操作、paused artifact或新增游戏日。真实下一步是用户授权后fresh query；冻结R46的精确F缺失，不报真实F或下一月到账。历史5035日账与未闭战争/自然继承不变。


### BG-2 损耗请求 consumer 与两项原生施工输入收口

完成：生产军力查询新增 `loss_allocation_requests_v1`；按stored order保留supply preferred/residual → siege+raid preferred/residual四阶段、preferred初始overflow、signed32低位IMUL与IDIV trunc0。当前supply budget0时消费现有regiment/预算；正supply仍明确缺per-ArRg2A956D0和真实post-supply current，不从requested amounts虚构实际写回。源提交b110ee79，Root43306c28采用；service冲突已保留补员与损耗两独立输出，整合查询复核待最终组合。一次6例离线GREEN，回执 `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261005/background-successor-attrition/focused-test-receipt.json`；同目录ROOT-DELIVERY与DAY-WEEK-FIELDS。Readiness仅writer requests static-ready，applied_loss_ready=false/null。

功能研究增量：冻结EXE110B完整setter叶2657EA0..2657F0E已经source-closed；先直接写chunk+4=EDX，普通newCurrent<maximum不再clamp/舍入/访问state+18；特殊满额路径按原始owner谓词清空max/current。复用pin并仅读400B PE映射，无wholehash/扫描/callee扩张。source与狭读receipt位于 `Z:/ck3_mod_rewrite_process_assets/g2-background-20261005/attrition-setter-research/`，ROOT-DELIVERY SHA d784dd25e9c051d2b649d26fb488c8ae4ef4ecafd53944fdbaaf00fd1aa0286b；canonical已随b110ee79更新。叶语义闭合不等于writer2634880 admission、DATA分布及每阶段实际current已建模，不能称实际损兵。

另一项Entry source研究闭合post-A/B三个贡献族：291C2FE guarded+630、291C32C carrier+40、28B6200返回Character1C0 carrier+200或inline54E7270 header，caller按真实stored order合source+D8。新读121B code+48B pdata，复用cached caller；字段/顺序/Mermaid与精确遗留已入canonical，源receipt与合同在 `Z:/ck3_mod_rewrite_process_assets/g2-background-20261005/entry-next-stage-research/`。资格research、尚未observer实现；下一入口为该optional后段、changed-stage list writers及291C371余段/actualEntry上下文，当前final不能当prestage baseline。两研究原失败命令attempt均保全，记录检查不算semantic测试。

本包新增game/SDK/attach/query/UI/Steam/stop/native-build/game日全部0；历史5035日账不变。下一步完成整体native新路径验证并普通push，真实paused及最终loss/Entry资格等待用户授权后另验；完整战役和战争结算仍未完成。

### BG最终离线交付：八包static-ready，实机保持停用（2026-10-05T19:48:26+08:00）

完成：完整路线ETA、独立器械军成员资格、chunk补员数值、四阶段损耗requests、首次接战pre1640、实际战场geography、盟友拒绝diagnostics、普通holy-order hire八包均已接入现有生产路径并完成相称离线验证。交付目的分别是消除已知字段/consumer/typed动作缺口；不新增策略猜测或第二套MCP。Root整合源码 `4733655173e65be99c9ffaafbe2d9275940df4d6`，采用提交如下，Git publication与旧R46运行源分开。

| 本轮后续包 | 实际实现及Root采用 | 新离线验收 | 资格与遗留 |
| --- | --- | --- | --- |
| 全路线ETA | 8eaee61a→c170ed08；保留native prefix Q100000，首段progress不再二减 | native四场景GREEN；compiled producer registered MCP 4cases/24checks GREEN | static-ready；真实paused路线和实际抵达待验 |
| 参围成员 | fcc756e5→9a7bc93b；Province CUnit occurrences、CArmy/ArRg身份及完整资格 | lane Python3GREEN；native成员reader/serializer GREEN | static-ready；器械到场与真实K/M/D贡献待验 |
| 接战pre1640 | 9e13ef39→5aca2c89；两registry bindings、源阶段/short circuit/missing独立 | lane Python16GREEN；nativeprestage GREEN | 该observer static-ready；post-A/B仅research、完整Entry partial |
| 当前geography | 392a290b→975bb5b1；terrain、signed width、retained crossing/holding及原查询镜像 | lane Python5GREEN；native GREEN；compiled producer消费3/3GREEN | static-ready；未来constructor/MC/win odds未完成 |
| 普通holy hire | 6ebccc54→4dfadd9e；mode3 typedprovider、executor/dispatch/MCP及原生资格 | native8samples GREEN；registered MCP1case/51checks GREEN | static-ready；雇主/扣款/CUnit后态和loop待验 |

公共构建：Release、`/WX`、jobs4、低优先级，生产`xar_ck3_bridge`与五个focused目标已GREEN；新增五项CTest一次5/5GREEN（wrapper0.798秒）。`native-attempt-01` actual C3889 occurrence equality与`native-attempt-02` geography fixture LNK2019按最小范围修复，失败log/receipt原样保留；后一次incremental build GREEN4.746秒，不把增量耗时冒充clean build。CMake接线ccb158c7、equalitye8c47c98、link47336551保全真实触发/修复。纯consumer此前2/5/6例结果直接复用；service真实cherry-pick冲突保留补员与损耗两输出，Root仅新增2例组合验证GREEN，不重跑算术。

外置总冻结 [OFFLINE-FREEZE.json](Z:/ck3_mod_rewrite_process_assets/g2-background-20261005/OFFLINE-FREEZE.json) 绑定源码、实际flags、DLL/producer/receiptSHA。DLL5613056B、SHA `96a56408cc7dd00dbca3cc20bbccf837feaa39af77ad017000f8575e45c3a4b8`；构建/CTest/组合consumer原log同根。路线compiled回执在movement-compiled-consumer，geography在battle-terrain-consumer-replay，holy在g2-holy-order-hire-offline-20261005/registered-mcp。五个canonical原生专题均追加最新资格，两项source研究已先入库；所有owner结果已同步本日日报/W41周报，文本报告无需视频。

限制：本次只构建默认离线目标，未采用v73实际runtime capability flags，宗教private query仍OFF；不作为直接可部署v74。未来获准实机时须采用所需flags、另冻candidate并fresh读actor/episode/war/army/revision。Git-local Defender opt-in未设置，build hookdisabled，未登记或声称新增EXE排除，也未弹出系统确认。未执行runtime prepare/stage/launch、CK3/SDK/attach/query/pipe/UI/Steam/profile/缓存/存档操作，新live与游戏日0。沿用历史5035/36524、resume1882、Oct5+377、G2 5/8、NW2 2/4、自然0、h9052/raw53265168；旧wholeh9048保全。用户游玩不计自动任务。实际3711攻占、War117结算、完整损耗/Entry/forecast及自然继承仍未完成。

对照19:14后续计划：BG-1四项离线交付完成；BG-2三项有限实现与验收完成（applied loss/full Entry不在本包完成边界）；BG-3普通动作链离线完成；BG-4知识/日周同步完成，普通push随本次收口执行并以实际回执记录。计划外完成final setter叶和post-A/B三贡献族source研究、两处实际编译修复及组合service校验。无提前午夜/周末收口；新实机不属于当前授权，等待后续明确恢复。已推送441c8df5的官方CI37302333309 success仅绑定该旧head，本次整合exactCI另记，不借旧GREEN。


### 后台包实际主线发布（2026-10-05T19:52:26+08:00）

普通fast-forward push已成功发布 [`f8625cb2`](https://github.com/XenoAmess/ck3_eternal_recurrence/commit/f8625cb262cb09dd0ce4cceb66cd7e2c483627ac)。期间另一机器提交a3a0cadf，Root保留其Main GUI修复及R17/R18日报，先fetch再线性rebase；只发生独立日报append冲突，两侧全文保全。`git diff --quiet 4733655173e65be99c9ffaafbe2d9275940df4d6 f8625cb262cb09dd0ce4cceb66cd7e2c483627ac -- ck3_autonomous_player` exit0，已验证自动玩家源码逐字节相同，复用本轮离线结果，不重跑。实际Root采用提交由原rebase前编号对应到：ETA4289373c、pre1640536570d5、holy7e7e5674、lossb16a290a、成员7a1abd42、source/frontier2944aaae、geography0d784483、fixture5b7e1282、equalityae72e842、link9dd50766；上段旧编号为当时的采用事实。映射与actual push回执在 `Z:/ck3_mod_rewrite_process_assets/g2-background-20261005/PUBLICATION-RECEIPT.json`。

整合源码exact官方CI [37305495479](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37305495479) 登记时in_progress，不提前称GREEN；本发布记录为docs-only追加，随即普通push，最终exact CI终态保存到同根ROOT-FINAL-DELIVERY.json。BG-4提交/推送已实际完成。所有CK3/SDK/界面/Steam操作和新增自动游戏日仍0；日/周仍滚动。


### 第二批后台施工已启动（实际登记 2026-10-05T20:28:07+08:00）

用户再次明确继续所有能后台执行的任务，CK3由用户自行使用、不得启动。上一轮八包是阶段性交付，不能据此声称后台任务耗尽。本次重新扫描P0/P1、测试/CI、知识同步与后续能力依赖，继续六条确有原生缺口的功能线，Root串行整合和集中新路径native验证。源码base3e2737b5909616cd2ab301da59352250410bafb8；原用户树、g38/g78和第一批产物保持保全。

| 工作包/优先级 | Owner树 | 可交付项与一次离线验收 | 依赖和完成边界 |
| --- | --- | --- | --- |
| R2-1 P0 post-A/B observer | Z:/gb9 | source-closed guarded630、carrier40、orderedD8接现有context query/DTO/consumer；原生三叶fixture与必要消费验证 | 复用已闭contract、真实顺序/短路/inline54E7270，完整Entry与live仍分开 |
| R2-2 P0 actualEntry context | Z:/gbr2 | 28BFC70→2C06B00来源/首次caller闭合；输入可读时直接补同query observer | narrow cached/source证据先行，不把current final当prestage |
| R2-3 P0 supply eligibility | Z:/gbr3 | 逐ArRg2A956D0现成军力口及loss consumer依赖 | 正供给request真实资格缺口；不虚构post-supply current |
| R2-4 P0 loss writer inputs | Z:/gbr4 | 2634880 admission、DATA/special原始字段与可完整计算的同输入chunk写回 | 已闭setter复用；完整应用与真实净人数分开，source先于实现 |
| R2-5 P1 retained geometry | Z:/gbr5 | 已观测6F8/6FE和明确provenance进入retained constructor diagnostics消费 | 对实际当前combat的独立诊断；不补造历史entry/initiator或未来接战 |
| R2-6 P1 holy-order release | Z:/gbr6 | 普通release原生树及可闭合typed command/provider/MCP | 不猜hire mode、不用Disband冒充release；提交ACK不升格employer/CUnit后态 |

六owner已经启动；需要进一步source叶时以实际依赖补小线，不为64上限填槽或派安全审计。Root唯一source/Git integrator；owner在各自clean detached树记录测试、why、RED、artifact、commit、readiness和精确剩余，共享canonical/daily/weekly由Root合并。知识先落盘再施工，新native统一jobs4低优先级编译；每包验证完成即普通push，不等其它包或实机。open_kaishek对本轮ABI/DTO/native命令不覆盖，记not-applicable；有CK3脚本语义时再按实际子集预验。无旧测试重跑、无全EXE扫描/hash、无新策略猜测或理论安全机制。

本次不执行CK3/SDK/attach/query/realpipe/UI/Steam/gameprocess/profile/save/cache/runtime prepare/stage/launch。新增自动游戏日与live0；5035/36524、resume1882、Oct5+377、G2 5/8、NW2 2/4、自然0和h9052/raw53265168仍为历史冻结。日/周保持滚动，此计划实际晚间登记，不倒填00:00。工作树登记与checkout回执在Z:/ck3_mod_rewrite_process_assets/g2-background-round2-20261005/lanes.json；第一批实际CI37305747276 GREEN直接复用。


### 第二批并行调整：增加两条人物后段施工（2026-10-05T20:36:18+08:00）

重扫原生依赖后，post-A/B与actualEntry实现之外，已知291C371后段和scratch430/438/changed-stage census仍阻碍完整人物构造。增加R2-7 P1 later suffix（Z:/gbr7）及R2-8 P1 scratch/census（Z:/gbr8），source基线5ed6267a（与前六包只有计划docs差异）。两owner先复用缓存/source闭合必要贡献与身份，再将可独立解锁的只读输入接入同query；Root合并共享专题及日报/周报，不创建额外端点或安全审计。当前八owner+Root并行，所有CK3操作与新增日0；next gate为source树/精确readrecipe，闭合后实现和一次离线验收。工作树登记suffix-lanes.json在第二批外置根。


### R2-5 retained几何消费完成

R2-5 retained constructor geometry消费已完成，实际采用时间2026-10-05T20:40:17+08:00。生产现有transition/control service新增独立retained_constructor_geometry_v1及immutable typed simulation输入：支持原生kind0/1/2/3→none/strait/river/large_river，复制stored side0/1 order、owned side+70身份，直接以retained6FE决定holdingF10。Source先行闭合RulesF70+8kind/FA0+8kind及F10选择；这里是规则slot输入，不发明effect数值、advantage、原initiator/entry，也未扩v2未来grammar或削弱owned权限。解决已发布原始几何尚未被构造诊断消费、非零kind不能被现成v2使用的具体缺口。

源1668f551，Root采用82c114b8，8个文件；一次新Python聚焦4/4GREEN（test0.019秒、process3.106秒）实际使用第一批compiled production wire原字节及明确kind/holding变体，覆盖source-frame/roles、零/false/signed width、unavailable、旧shape及immutable输入。没有native改动/构建或旧测试重跑，diff checkGREEN。回执Z:/ck3_mod_rewrite_process_assets/g2-background-round2-20261005/retained-geometry/ROOT-DELIVERY.json；SOURCE-TREE.md/CANONICAL-APPEND.md同根，canonical与Mermaid已采用。资格static-ready独立diagnostic，真正效果数值/统帅exclusion/scale/初始context/roster与历史initiator/entry仍未闭，实际pausedadoption等待用户。

Root立即提交普通push此独立包，同时其它七线继续；新game/SDK/realpipe/UI/Steam/process/profile/save/cache操作、游戏日/live/MC信用均0，5035历史冻结不變，日报/W41持续滚动。第一批默认DLL已在source47336551-default-offline-binary按字节归档，不覆盖旧资格；后续新native会使用已存v73能力flags进行纯离线CMake联编，不执行任何runtime prepare/stage/launch。


### R2-3/R2-4损耗输入已实现，集中native验证中

实际采用2026-10-05T20:45:16+08:00：R2-3供给资格源f850fcbf→Root326c40c1、R2-4写回源61e5059a→Rootf5d0c607已整合。Source-first完整只读2A956D0和2634880分别闭合，现成regiment_strengths发布前者bool/reason，fullDATA父行发布native_loss_writer_skipped、每record发布chunk_army_regiment_id。既有严格generation读取和DATA关联已经证明特殊setter的association−1清零域不可达，因此不用虚构owner/flags，能独立释放当前关联chunk回放。

正供给分配现能计算initial preferred请求；同阶段chunk projection按原生Q100000、两轮、别名/顺序、state3物理零及负数量修复转移、角色skip/parentzero处理，不擅加clamp。两个owner各一次新Python focused case GREEN；gbr4首次importpath harnessRED已保留。两新增native targets由Root集中低优先级jobs4编译，尚未在本段抢记native GREEN。源码/读取、Python测试、日志和SHA回执在第二批根supply-eligibility与loss-writer-inputs；两canonical/Mermaid已采用。

Root正在联编生产bridge与两新增native目标，采用已存v73 capability flags（纯离线CMake，不prepare/stage/deploy/launch游戏），第一批默认DLL已单独归档。gbr3继续一条依赖整合：只把initial supplypreferred、供给budget0时的initial siegepreferred请求送入对应同阶段DATA回放；实际post-supply/postpreferred current缺失仍不制造后态。applied_loss_ready与整月应用信用继续false；新游戏/SDK/realpipe/UI/Steam/profile/save/cache/game日均0，5035历史冻结保持。其余人物/holy施工继续，并非后台任务耗尽。


### C/D 原生验证与同输入扣兵 consumer 已交付

实际收口时间：2026-10-05T21:00:25+08:00。C/D 新增生产 reader 与完整 bridge 在 v73 capability flags 下完成纯离线 MSVC /WX 构建；没有 runtime prepare/stage/deploy。原生 source 为 `9b270104`，`native-loss-03.json` 记录增量构建 GREEN（5.65 秒），不是 clean/full build 时长。两个新增 native fixture 各实际执行一次 GREEN：`xar_ck3_12003_loss_writer_inputs`（0.13 秒）与 `xar_ck3_12003_supply_loss_eligibility`（0.10 秒）。首份 CTest 命令把 supply target 名误当 test 名，实际仅运行 writer 1/1；随后仅补跑遗漏的 supply test 1/1，没有重跑 writer。两实际日志分别为 `native-loss-ctest-01.log`、`native-supply-ctest-01.log`。

保留两个真实 build RED：`native-loss-01` 的新 fixture UTF-8 在 CP936 下产生 C4819→C2220；`native-loss-02` 的 narrow diagnostic Unicode minus 产生 C4566→C2220。Root 只补 fixture UTF-8 BOM、将该诊断改为 ASCII minus（`61cbc345`、`9b270104`），没有改 production 运算、放宽 /WX 或更改系统编码；第三 attempt GREEN。原始失败日志和回执不覆盖。

依赖整合源 `352ebd69` → Root `f0c4aa69`，一次新增生产 service 的 C+D 内存 integration case GREEN（1.69 秒进程）。现有 loss request 已返回 `same_input_conditional_chunk_writeback_v1`，只回放当前 initial supply preferred，或 supply budget=0 的 initial siege/raid preferred；residual 与 post-supply 后段不借用旧 DATA。条件 physical chunk 结果与真正 post-stage/current/整月扣兵分列，`actual_loss=false`、`actual_post_stage_current=null`、原 `applied_loss_ready=false` 保持。专题及 Mermaid 已同步，不增加完整月度/live 信用。

证据根：`Z:/ck3_mod_rewrite_process_assets/g2-background-round2-20261005/`，C/D source 与 conditional-integration ROOT-DELIVERY 各自保留。Readiness 为 static-ready（生产路径 fake-memory fixture 与同输入条件运算），非新 paused/live。新 CK3 启动、连接、SDK/真实 pipe、窗口/Steam、profile/save/cache/runtime 操作与游戏日均0；历史5035天不变。人物后缀、actual knight context、holy-order 查询及后续 scratch 仍在推进，不能据此声称后台工作耗尽。


### 人物来源/上下文/scratch 与 holy-order 当前战争资格继续交付

实际整合时间：2026-10-05T21:05:12+08:00。四份人物 source-first 后台包已接入现成只读查询：post-A/B 三族源 `1bb9c2cf` → `0c5e0959`；actual knight effectiveness Character context `0b2e1d69` → `122d1eb7` 及 native fixture child `f105f5b0` → `9a92c24e`；later caller-direct 两族 `977de946` → `273faa52`（随后修复merge）与额外 source closure `2d567cd7` → `623182ba`；辅助 scratch 两公式 `73e8f3f1` → `8f4c84ed`。原生 tree/Mermaid 已并入第一接触人物专题，actual knight 独立专题已合入；各 producer/normalizer 保留独立 optional 字段，旧 wire 兼容。

owner 已分别只执行新 Python cases：post-A/B16 GREEN、knight context1 GREEN、later direct11 GREEN、scratch1 GREEN。Root 不重复这些旧测试，新增四个 production-reader/serializer fake-memory targets 正在集中编译，native GREEN 尚待独立日志。post-A/B 与 later direct 共用 DTO/collector/normalizer 的冲突均保留双方。Root 临时 conflict regex 的 DOTALL 末标记贪婪误吞了尾部，diffstat 当场识别；从双方原始提交与共同基线重新三方合并，`5b329bfc`、`5ae64bd8` 恢复后完整增量恰为 owner 880 insertions，无其他删除。错误态未build/test/game，外置 `direct-merge-repair-complete/REPAIR-RECEIPT.json` 保留实际修复。

holy-order recall/release 源 `f3afac55` → `d89590fd` 已入独立生命周期专题；依赖直接261C120 source 的独立 current-war eligibility `5c3b14f4` → `bf76e19f` 已实现，允许已雇佣/can_hire=false 时仍读取当前战争资格与 native reasons，native fixture/MCP genuine wire 验证待集中执行。该字段不是 release action、war-end trigger 或持久雇佣合法性。manager 入边/多战争解雇仍 unknown，明确source入口而不猜动作。

后续后台已继续：同一人物2949010九cachebyte输入/计算（新EXE read0）及291F0A0四族helper只读选择/贡献（复用2BFB4C0、窄查3F90910）。不是后台工作耗尽。全部 source/fixture/read/consumer receipt 位于第二批根对应目录，readiness 仍static-ready/native pending，无新 paused/live、完整人物/Entry/forecast/战争loop信用；5035历史保存天不变。CK3启动/连接/SDK/真实pipe、UI/Steam、profile/save/cache/runtime preparation/stage/deploy全部0。


### 五项新增观测原生验证与28份真实fixture字节消费已通过

实际验收收口时间：2026-10-05T21:12:06+08:00。整合 source `96e4c6a688d95dc326db4cd3b7cd25961e3c40c6` 在 adopted v73 capability flags 下 MSVC `/WX`、jobs4 below-normal 纯离线 bridge + 5新增targets构建 GREEN（152.98 秒、362增量步骤），`native-person-holy-01.json/.log` 保留。只运行5个新增 CTests，一次 **5/5 GREEN**（总0.73 秒）：post-A/B、knight effectiveness context、later direct、auxiliary scratch、holy-order current-war eligibility。旧C/D及旧Python cases未重跑。

真实生产reader/serializer输出随后各消费一次，合计28份：post-A/B8（ordered requests `[5,1,1,3,0,null,null,null]`）；knight4（缺诊断仍保留真实scalar/stats）；later-direct7（duplicates、fullgeneration fallback、negative count/missing/false分开）；auxiliary scratch6（真实准备/复制结果分列、native-noop、missing threshold）；holy-order3通过注册MCP consumer 48checks。无synthetic replacement，生产normalizer/module从Z:/gb0导入；十三份later/scratch在 `later-scratch-genuine-wire-integration.json`，其他各lane native-wire-integration/VALIDATION-RECEIPT保留wire、consumer与projection pins。新native+consumer资格均为 **static-ready**，不是live，也没有完整人物、changed-stage、Entry预测或release action信用。

qualified DLL已归档 `source96e4c6a6-person-holy-qualified-binaries/xar_ck3_bridge.dll`：9,691,648 bytes，SHA `ce030baa45956ffac50b43e3b1337b6b06c8407e9a38fe2ab110382d0c51ca41`，同档案保留5fixture EXE、实际JSON、CMakeCache与编译result。未注入或deploy。上一已推送loss milestone `02d187b2cf7df41393affe840992d26f2b715691` 官方CI `37313580089` SUCCESS；对应[CI日志](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37313580089)不能外推新commit已过CI。

下一后台工作仍在做：已交付九cachebyte child源待Root采用/独立native验证；291F0A0 helper四族观测、2633340 conditional raised refresh及retained selected Rules真实effect值正在 source-first施工。这些都针对当前功能输入缺口，不派生理论安全审计，不用无paused状态当停止理由。新CK3启动/连接/SDK/真实pipe、UI/Steam、profile/save/cache/runtimeprepare/stage/deploy与游戏日全部0；历史5035保存日与R0046停点不变。日/周保持rolling，不倒填早会，不把幕后源码测试记成production-live。


### 九项人物缓存与条件军团refresh继续交付

实际续行采用时间：2026-10-05T21:16:05+08:00。九cachebyte source `2306c381` → Root `da9aa3fa`：2949010必须读取scratch258真实model+78 aggregate，不用earlier owner/fallback选中的context；exact nine键表、两个magic guard、选中definition九U16与FFFF skip、wrap64→truncQ100000→signedlow32→[-100,100]均保留。current signed bytes与pure calculated结果分列，新增EXE读取0。一份新生产normalizer→kernel case GREEN（1.10秒），八个newnative reader/serializer samples待Root集中验证；旧auxiliary6实际wire已消费过一次，不能再重复包装为新测试。

2633340 source `e18adfad` → Root `3496fa3f` 已交付：复用缓存1952B函数，不新增native字段/编译。纯conditional raised current/max已接入原writer与initial preferred consumer，每DATA occurrence含重复别名均计入signed32 wrap，state3/current0用max，Character独立refresh1/1但writer skip实际不调用refresh。一个新focused case GREEN（-B -O）；旧C/D不重跑，actual post-stage/current仍null，整月applied ready仍false。证据分别在第二批/person-nine-cache-byte与 `Z:/ck3_mod_rewrite_process_assets/g2-background-round3-20261005/raised-refresh/`，专题/source树/Mermaid均同步。

四项后续施工为九cachebyte原生验收、helper291F0A0四族同query观测、retained selected Rules实际effect读取、conditional raised refresh（本项已完成static-ready）。前三项依赖source闭合/当前raw观测，验收用各新focused native与真实serializer字节消费，Root独占jobs4 below-normal编译；不增理论门禁、不重复旧通过测试。完整人物/changed-stage/Entry、月度真实后态和release trigger仍未完成；无paused或用户正在玩不阻止这些具体后台源码工作。游戏/SDK/真实pipe/UI/Steam/profile/save/cache/runtime部署与新增日数0，历史5035不变。


### 九byte standalone native与8份真实wire通过

实际收口时间：2026-10-05T21:25:57+08:00。newnine standalone target在 source `f16c12b7e50fb50da899655ef295993ecbe55cf5` 下 `/WX`、jobs4 below-normal离线构建 GREEN（9.66秒）；唯一新增 CTest一次1/1 GREEN（0.13秒），产出8份production-reader/serializer样本。随后只消费这8份，生产normalizer→purekernel30checks一次GREEN；旧auxiliary6重跑/读入0。真实wire SHA `2033c0fd780383e1cfcdc086097388021d5f8dc9118a8887b68af3217ce5fe50`，RESULT SHA `7691730f786587e50fb05531d60e5a921808ba478f3870f4252676e251035f50`；外置第二批/person-nine-cache-byte/ROOT-COMPILED-WIRE-DELIVERY与资格附录保全。

native fixture EXE544,256 bytes/SHA `939093571954aae848c768b62dfa52050f50dd74cdf3d958977d5d9b70ddf5bb`、actual wire、CMakeCache/result已归档 `sourcef16c12b7-nine-fixture/`。本次只build新target，完整DLL仍为已封存source96e4c6a6，不能把standalone target当新source整DLL联编。Root下一次合并helper/Rules后集中build完整bridge；九byte旧native与消费者不重跑，除非新变更改变此路径。

资格为standalone native+consumer static-ready，真实当前cache、计算值、earlier fallback-selected context分列，完整人物/Entry/未来forecast/live均未授信。其他后台仍实际进行：helper四族与retained选中Rules effect实现待交付、四pass conditional army losssource账本、first-contact实际Province/admission、七groupcensussource。新增EXE读量/游戏日/CK3连接/SDK/pipe/UI/Steam/profile/save/cache/runtime部署全部0，5035历史冻结保持。


### Helper四族与真正loaded Rules effect已实现，下一合批原生验证

实际采用时间：2026-10-05T21:32:33+08:00。Helper源 `d30e01eb` → Root `12574a6b` 接入同查询四族observables/有序贡献：present1C8及真实manager路径四族可ready；absentrecipient/lazy未初始化明确partial，另外三族保留独立价值，不调用initializer。新Python11/11一次GREEN（1.07秒），新native target/CTest含7wire samples待Root联编。CMake冲突仅手工合并独立test blocks，source增量1227行与owner一致，没有之前temporaryregex尾部丢失。

Rules源 `7c8d410f` → Root `df3307ec` 发布同frame真正loaded F70/FA0/F10 effect keys与signed wholepoint，points_scale1；source getter8FC3E0复用phaseeffect DB与原phase decoder（其body不变，仅提为inline共享）。独立只读leaf不会把offset当value、null/invalid adjacency当0point或current slot当历史已append。holding倍率、commander exclusion与完整advantage仍缺。新Python4/4一次GREEN；new CTest `xar_ck3_12003_retained_rule_effects` 用现current-state target的new-only mode，7新frames待验。

Root下一次集中MSVC /WX build完整bridge及helper/current-state两个targets，包含已经standalone通过的九byte代码；只执行上述两新增CTest与各自真实JSON消费，不重跑旧九byte/auxiliary/post-A/B cases。证据第二批/person-later-suffix/HELPER-*与retained-geometry/loaded-effects，专题/Mermaid同步；native资格本段保持pending，不能抢记GREEN。

同时继续实际source任务：四pass条件损耗已闭合262BE30 scratch返回路径，不改必需eligibility/admission/tier/current；first-contact per-Army Province与returnedCombat双方refresh阶段已区分；七group current rawcensus/actualmodel-owner关联已从缓存source找到独立施工入口，gbr8先完成source树再实现下一child。它们皆不写stage-startbaseline、不冒充完整Entry/fullmonthly actual，也没有任何CK3/SDK/pipe/UI/Steam/profile/save/cache/runtime部署或新增游戏日，5035冻结不变。


### Helper/Rules合批原生与四pass条件损耗交付

实际收口时间：2026-10-05T21:45:29+08:00。source `52391be52ac520e077eb3131f9bb9e638651a978` 完整bridge（含九byte/helper/Rules）与helper/current-state targets严格 `/WX`、jobs4 below-normal纯离线联编 GREEN（156.12秒、349增量步骤）；两项新增only CTests一次2/2 GREEN（Rules0.13秒、helper0.11秒）。真实producer新输出各消费一次：helper7/7（0.043秒，四族顺序/重复/单位weight，partial的独立族保持可用）；loaded Rules7/7（normalizer→service→immutable adapter0.00217秒），生产import为Z:/gb0。旧post-A/B/aux/nine/原current-state tests不重跑。整个第二轮共10项新增native CTests各通过一次、50份新人物/holy/Rules真实fixture输出消费通过；这个计数不包含第一轮5 tests，也不冒充game fixture-live。

Rules第一次external import harness RED消费0帧：同目录inspect.py遮蔽stdlib inspect，导致dataclasses导入失败；仅修外置脚本import path后首次实际消费7帧GREEN。`NATIVE-WIRE-REPLAY-ATTEMPT-01-RED.json`保留，不改production代码。helper与Rules各自receipt/资格字段在第二批/person-later-suffix和retained-geometry/loaded-effects。source523完整DLL已归档 `source52391be5-helper-rules-qualified-binaries/xar_ck3_bridge.dll`：9,738,752bytes，SHA `6cd956645577e5b45cf772fa02dc0f4a718075179b7abaf4ec6692b6ef542c05`，同档保全actual14wire与native EXEs/CMakeCache/result，未stage/deploy/inject。

条件损耗sequence源 `93550a97` → Root `ce24cbca` 已采用，无native变更。新same_input_conditional_loss_sequence_v1按四pass即时重读derived current、writer+2633340刷新、DATA物理别名重载，分别报告最终ArRg current/max、唯一physical变化；一份新生产service case一次GREEN（3.37秒）。黄金fixture totals6→8→2→9、budgets8→2→7→5、finalcurrent[0,3,2,1]，aggregate12→6与uniquephysical−7分列，不改原query。必要262BE30源码helper只写caller80B scratch及已闭合只读子查询，新增660code+512mapping+216pdata bytes=1388B，不扩大modifier树。actual_loss=false、actualpoststage=null、appliedready=false保持；资格为当前显式输入下loss current/max子系统static-ready，非fullmonthly/未来budget/live。

first-contact Province/admission源码包已同步独立专题：24E0EB0实际Army+124 CUnit+20 Province，2C16770原Unit gate，首次行参与byte98A，与建Combat后效果/统帅更新→双方2651070刷新/Combat+6B8分开。新EXE403B，无新tests/代码字段；旧query已有validatedcurrentProvince/admission，不重复新增字段。不同target的firstinitstat可施工入口与完整newcontact后段未知保持research。

七grouprawcensus/actual model-owner关联正在继续source-first实现，旧counts字段保持；stage-start baseline不会由currentfinal伪造。Root下一编译只验证此新增路径，以上通过结果复用。游戏仍由用户使用：CK3启动/连接/SDK/真实pipe/UI/Steam、profile/save/cache/runtimeprepare/stage/deploy与新增游戏日全部0；5035/36524、G2 5/8、NW2 2/4、natural0保持历史冻结。日报/周报滚动，默认正常commit+push。


### 当前七组 Title census 原生与消费者验收完成

实际收口时间：2026-10-05T22:06:41+08:00。Source-first当前raw Title census/model-owner关联源e46db613→Rootd2d2d341已接入既有只读查询；完整bridge和newtarget离线 `/WX`、jobs4 below-normal build GREEN148.40秒（native-census-02）。新夹具fix65415a63→Root12a9caf2仅改fake-memory test：query稳定性连续双采样，每帧Provider重置government序列，累计两次Provider/正常10次government；scratch扩到290补query已有custody288读取。生产代码与旧Python用例不改不重跑，整DLL无需因test-only变化重编。新target单独重建GREEN5.89秒；新CTest一次修复后1/1 GREEN0.07秒（总0.11）。

真实生产reader/serializer新JSON22497B，SHA25b7d129abbf535873f88ac935ee1cbf7c5a09c1d4af71982d54bc6951dfd13f；十份输出只消费一次，Z:/gb0 authoritative normalizer→pure seven-group kernel 45checks GREEN。compiled-wire-02/RESULT.json14563B，SHAd6174b5efc5544706f09979a072c24bb77e2fdd1e8a411abee491920244b3fc6。旧aux/nine/其他已通过样本0重跑。Raw census独立ready，outside-tier原值留存但七计数partial；头衔重复/顺序/fallback、实际actor/model-owner关联与短路source读取保留，不拿旧汇总或当前final代阶段baseline。

首次native-census-01因Root错误DLL target名无compile执行；native-census-ctest-01因夹具未模拟第二帧throw穿过noexcept而RED0xc0000409，输出0bytes。Root随后consumer也在byte0 JSONDecodeError，实际消费0份。原失败与empty wire均保留person-changed-stage-census/native-attempt-01-red/RESULT.json和owner ROOT-FIXTURE-FIX-DELIVERY.json；最小fixture修复后才首次实际消费十份GREEN，不能改写失败。新增路径共11项不同native CTests已通过、60份新真实fixture输出已消费通过，资格为static-ready，非game fixture-live。

整DLL归档source12a9caf2-census-qualified-binaries/xar_ck3_bridge.dll：9748992bytes，SHAce472bc34028dc675d9f5c47cf10f6ff65f082387bd93e0be8ebde115277f44a；编译production source为d2d2d341，fixture source为12a9caf2。同档案保留newEXE/wire/cache/result/consumer pins及source差异只有此test的证据，未stage/deploy/inject。前一已推送fc628dca官方CI37319699503 SUCCESS，归档tag archive/g2-background-20261005-round2-pre-rebase保全原编译源；新publication的实际SHA/CI另记，不借上一CI结果。

三条后台依赖继续source-first推进：291F550/291F940人物剩余helper，291C0D0 model10真实reset/显式起始状态，以及月度初始供给/围城/劫掠预算。阶段baseline、实际changed-stage receiver/operands、完整人物/Entry/fullmonthly/forecast仍未完成；无新paused/live或战争loop信用。CK3启动/连接/SDK/realpipe/UI/Steam/profile/save/cache/runtimeprepare/stage/deploy与新增游戏日0；历史5035/36524、G2 5/8、NW2 2/4、natural0保持。日/周rolling，后台工作未耗尽。



### 显式人物阶段基线与前缀连接交付

实际采用时间：2026-10-05T22:28:23+08:00。source e68ef8922a535ea188d80654e0f09a309755c295→Root497319d0已合入，source账本/Mermaid先封存并同步frontier。既有materialized prefix保留completed-empty-reset API，新增明确post_291C010_pre_prefix logical baseline；支持weighted0但aggregate非空的实际保留分支，依原生base/common/actual-selected→291D1D0 selected/groups顺序复用共享fold，返回pre291C204和post291D1D0/pre291C209两个有界context。必要23033BC空目标非unit-Q scale已闭合；firstcopy重复keys/FFFF与nonempty merge的FFFF skip分开。不自动将current-final当historical prior或声称cleanup实际执行。

唯一新增production normalizer→assembler→既有six-skill kernel integration一次1/1 GREEN，结果保留aggregate为[9,6,6,6,8,9]、显式新reset清空为[9,6,6,6,8,7]；首group2Q空目标、大数分解与prowess raw80006→cap120已覆盖，缺失baseline和错误current-final stage仍partial，原当前prowess8与输入不变。旧tests、native builds和游戏操作0。本包资格为有界logical stage static-ready，不是完整人物/Entry、native parity、physical allocator/storage、历史stage观测或live。

交付及日周fields保存在第二批actual-entry-context/person-stage-baseline/ROOT-DELIVERY.json、OCT5-W41-FIELDS.json；focused-attempt-01/RESULT.json保留实际测试。新必要EXE code231B、一次可避免的cleanup重复读取29B按实际历史保留计成本而不给新研究信用，总260B；wrong plan CLI和Windows wildcard harness失败已保留纠正，没有capability RED。完整专题：[explicit person stage baseline](../ck3-native-ai/battle-person-stage-baseline-12003.md)。下一实际连接是post291D1D0→preA1640/A/D460/B/DED0/DCE0和已闭后缀，各helper输出逐stage续fold，未知与合法空分开。

两条原生observer包继续施工：291F550/291F940 ordered source与monthly post-updater budget，source均已闭合并同步native专题，尚不抢记其native/consumer GREEN。前一census提交74f60838的官方CI37322176165/37322176711已SUCCESS，11个新增native tests和60份新真实fixture consumer资格仍保持，未重复运行。各包完成即普通commit/push；后台入口没有耗尽。CK3/SDK/realpipe/UI/Steam/profile/save/cache/runtime prepare/stage/deploy与新增游戏日0，游戏留给用户，历史5035/36524、G2 5/8、NW2 2/4、natural0保持；日报/周报rolling不倒填午夜收口。



### 后台三个功能包完成：人物后缀、显式阶段基线、月度预算

实际采用时间：2026-10-05T23:06:01+08:00。逐项核对22:02实际追加计划：291F550/291F940 source/observer/consumer包完成；explicit baseline/prefix/291D1D0包完成（此前497319d0/8b01a769）；monthly post-updater budget包完成。没有倒填00:00计划，本日/本周报告仍为rolling。这些包解决当前人物贡献与扣兵预算所缺的可施工输入，依原生source账本/Mermaid先封存再实现。

人物同查询新增`later_helpers_291f550_291f940`，保留550政府/文化direct/mapped和940每个outer的direct→inner原生顺序、FullQWORD membership、firstFullID mapping与重复项。3份新原生序列化输出一次走生产normalizer/emitter GREEN，完整11条、partial独立7条、known skip/zero span1条；未使用的lazy default未初始化不影响已选有效PC，实际选中未初始化default保持partial，未调用initializer。source子提交e3dc8920、实现cb57a5a3→Root69a36e5b、fixture修复c28d683a→Root64bb7db9。一个新Python case1/1 GREEN1.56s，不重复旧case。

月度同查询新增`monthly_loss_budget_inputs_v1`，采集admission、loaded vectors、fleet/date、实际commander/Province ordinal；新条件kernel先计算post-stock，再按source选table/modifier，最后独立取整siege/raid，对已提供tier/DATA的复制frame连接既有四轮writer/refresh。新Python生产service case验证current budget0/原序列final12保持，derived budget1/条件final11成立。7份新原生生产serializer输出一次走实际service/normalizer/kernel GREEN0.034064s，供给预算为4/0/6/0/0/0/null，siege与raid各1保持。该新native fixture未绑定旧tier/DATA，预算ready不冒充nested sequence ready；Python新增case单独验证这些现有输入的连接。实现0e64b517→8620dbc9；7bf52472→e6b4219d移除与loaded table无关的regiment数量限制，仅保留source非正count与实际读失败。

中央native-final-frontiers-01 /WX初次harness RED144.2888s为helper fixture的optional<uint32_t>==signed0引发C4389/C2220；原receipt/log已保留，最小修复为0U，未改生产helper。source64bb7db9054fc155839c7c30528405c6b8f4addd必要增量完整DLL+两新target GREEN8.350974s（此值不是clean build耗时）；两项新CTest首次2/2 GREEN，helper0.14s、budget0.09s，总0.49s。随后仅消费新增3+7份wire，没有重跑此前passed路径。本次后续累计13项不同新增native CTests、70份新actual production fixture JSON消费GREEN，旧资格直接复用；原stage baseline新integration也已1/1 GREEN。8b01a769的Official Runner CI37325149320已SUCCESS。

完整DLL9807360B，SHA256`72a070cddb334f875a391d3f9dc48c25df559ccd897925751f4abb83bb424c54`。两个新fixture EXE、10份原生wire、CMakeCache、native-msvc-result、初次RED/后续GREEN与两consumer receipt已归档到`Z:/ck3_mod_rewrite_process_assets/g2-background-round2-20261005/source64bb7db9-final-frontiers-qualified-binaries/`，索引HASHES-AND-QUALIFICATION.json。构建使用只读已保存v73 115 feature flags、/WX、jobs4 below-normal，是普通离线编译；没有runtime prepare/stage/deploy。归档首次metadata的Windows separator assertion失败保留在索引，使用Path.parts恢复既有拷贝，没有重跑编译、测试或消费者。

最终资格为各有界查询/纯kernel的static-ready。actual_loss=false、actual_post_stage_current=null、full_monthly_applied_loss_ready=false，人物whole-source仍partial。接续后台入口明确保留：earlier absent1C8→2BFAC30、caller291C467以后、post291D1D0逐stage接到已闭A/B/后缀并关联actualEntry、其他monthly effects；实际post-updater/post-writer读取与整套paused/live验收继续等用户结束占用。无需以缺少实机停止这些source/model施工，也没有宣称后台工作耗尽。

game/SDK/realpipe/UI/Steam/profile/save/cache/runtime部署操作0、新增游戏日0。Z机器历史R0046关闭、v73 h9052/raw53265168与5035/36524、G2 5/8、NW2 2/4、natural0保持；其他机器单独授权的日报记录保留，不外推本机live。相关实现与本次专题/报告一起普通commit/push到master；最终发布SHA、archive tag和CI回执保存于外置FINAL-PUBLICATION.json。

专题：[人物阶段基线](../ck3-native-ai/battle-person-stage-baseline-12003.md)、[人物后缀与frontier](../ck3-native-ai/battle-first-contact-person-preparation-frontier-12003.md)、[月度budget/writer](../ck3-native-ai/army-attrition-soldier-writeback-12003.md)。最终子包资格：第二批person-later-suffix/remaining-two-helper/FINAL-QUALIFICATION.json SHA97eece0edbdfc89ee1b4881611a33e4c94cdc9fc4bbd51580372e1627caa53aa；第三批monthly-budget-source/ROOT-DELIVERY.json SHAbc88d0aad351fef88342cf1f76e5f82bf1108b815c03a34e2cbca4c5ad0b93ba。日周fields已分别由工作包代理封存，由Root合并，没有漏报。


### 持续后台续行：剩余人物阶段、月度效果及宗教战争生命周期

实际续行登记：2026-10-05T23:18:50+08:00。用户要求不停工；R4-1..7已分别在gbs1..7启动人物tail/absent recipient/阶段组合、月度war-side及尾段、retained advantage、holy-order lifecycle和first-contact最终刷新。此时仅为in-progress source/implementation，不抢记其测试、live或完成；原13新native/70wire已通过资格复用。上一published614440b9的CI37330465560已SUCCESS。Root中央整合和相称新路径编译，计划及owner详见日/周会后追加；下一交付是各source树/真实inputs和最小功能模型，不以用户占用为停工理由。实际游戏操作/新增日0，历史5035/36524及R0046停点不变。跨午夜按真实时间闭Oct5与召开Oct6早会，不提前或倒填。


### 显式阶段到六技能、辅助和九项缓存的纯连接已交付

实际交付登记：2026-10-05T23:35:04+08:00。Root source-first专题在23:28:25封存后实现新专属cache-stage projector，复用已通过的sixskill、2948DF0/F00和2949010 kernels，不改其代码。显式skill/auxiliary context与scratch258 model aggregate分别提供stage/queriedactor/provenance，不将AE0 fallback context默认当nine model78，也不借current final作为stage起点；其他原生scalar/selector/guard operands按提供值固定。

唯一新增production normalizer→两explicit context→三组cache kernel integration一次1/1 GREEN0.306495s。sixskill[1,2,3,4,5,6]、辅助[270,-13]、nine[2,-3,0,0,12,0,0,0,0]均可实际计算；缺某stage只使该family partial，另一family保留；differentactor不提供queried actor stage，nullscratch保持source noop。当前prepared[999,-888]/copied[777,-666]/ninebytes[7×9]独立保留，输入不变。原kernels/oldtests重跑0、native编译/新EXE读取0、游戏操作/新增日0；该Python手工fixture不是新C++ production wire，不增加原13newnative/70wire计数。

资格为有界conditional numeric static-ready，未生成context、历史stage、physical storage、真实copy/write、full native callback或Entry/live。它直接消费stagechain已验证frontier的明确context，余下构造段仍由R4-1..3继续补真实fields并续fold。没有因第一项交付而停止本批后台任务。专题[显式缓存投影](../ck3-native-ai/battle-person-stage-cache-projection-12003.md)，源码module`battle_person_stage_cache_projection_12003.py`及一个新case随本次commit/push；回执`Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/cache-stage-projection/attempt01.json`，SHA5dafed929b5be5cba5b22e0e299b213df43d03d6ce4f7a3118252c0f0d5535a8。

同时Root已采用person-tail source-only8557f9a7→b1adea76并将SOURCE-TREE-INITIAL/Mermaid同步frontier：政府870/A30和weighted630 raw weights/order独立闭合，初始source新EXE0；实现/新native资格仍pending，intervening unknown没有当empty。其他six owners/Entry第七owner继续source/model施工，Oct5日周rolling；本机R0046/h9052/raw53265168与5035/36524等live冻结不变。


### 首次接触纯刷新与不同省份初始输入连接继续交付

实际采用时间：2026-10-05T23:49:36+08:00。first-contact-final-preparation包494ae01c→Rootc6a0bd1c、a66f1348→Rootb9db5ca1已合入。新专属纯模型使用显式selected Character stage C1..C9与独立linked knight prowess，按exact2C06B00/2C4D680/2C06D30算六值，再按side0→side1、levy→MAA依2651070写入派生Entry六cache；quantity/header不变。ordinary/MAA缺明确endstage getter tuple时partial，不用currentfinal当pre-effect。2C4D680 slowMAX/Q与general numeric helper的MIN/Q分解分开，旧helper不改。

两个新增focused case各通过一次（final primitive0.3682s、initial adapter0.2343s）。第一次final fixture缺MAA counter census在normalizer处harness RED，已保留，仅修fixture后首次成功；旧case/原生compile/新EXE读取/游戏操作0。初始adapter同省复用旧effective_stats；异省只消费initialization_context_stats且sourceProvince必须是actualArmycurrentProvince，缺/错source不拿targettuple补。Root已分配R4-8 replenishment Z:/gbs8补同CombatInputs query这项真实readonly依赖，equalcase不另读getter；这项计划按当前真实追加，不倒填23:18七包或00:00早会。

本次资格为named-stage knight公式、显式六cache refresh及initialstage adapter的有界static-ready；完整人物构造、outer commander/effects/accolade assembly、未来contact/Entry/forecast/live仍未完成。工作继续，R4-3补prefix连续阶段，R4-1补真实trait/tail与absentbranch输入，R4-5 sourceholding/exclusion已合入且新standalone native target/WX首次GREEN10.9545s、新CTest1/1 GREEN0.14s，但9wire消费者此记录时pending、整DLL未就新native源重编（旧完整DLL64bb资格保持）。

证据：本轮first-contact-final-preparation/ROOT-DELIVERY.json、OCT5-W41-FIELDS.json、focused-attempt01 RED与focused-attempt02-fixture-census GREEN、focused-initial-attempt01 GREEN；[首次接触最终stat专题](../ck3-native-ai/battle-first-contact-final-stat-refresh-12003.md)。source-only absentrecipient a0f4d53a→Rootfc749b36（source5,029B、puremodule尚待统一person包新case）和retained source182eb841→69016947 /nativecandidate ab7ab1f1→db015fe8分别保留其research/candidate或独立验证边界，未抢记全人物ready。游戏及新增日0，本机5035/36524等历史freeze保持；Oct5/本周仍rolling，跨日正常收口后续行。

### 实际跨日后台续行（2026-10-06T00:03:36+08:00）

Oct5正式日报收口并立即建立Oct6早会/日报，W41继续滚动；没有为等待全部功能包推迟形式收口。R4-5新standalone1CTest/9wire一次GREEN使第二批后续累计14/79；完整DLL仍64bb源。R4-7pure/adapter完成；09be453a monthly、aba4cdb6 holyorder、53e1675b initialstats和db8a1742 guard等待中央采用/新native资格，人物trait/tail及stagechain继续。详见Oct5最终对照/Oct6新会，各后续firstqualification按Oct6真实时间记。用户仍独占CK3，本机游戏与新自动日0，不把00:00环境更新当恢复实机授权。

## Oct6 central native and production integration completed (2026-10-06T00:21:35+08:00)

Integrated source **89cb683dbed31bad3bc0c008ea525faf1db08db0**: fullDLL plus four newtarget ordinary offline compilation first successful GREEN. Initial native-round4-core-01 harnessRED172.1268s came from two newfixture integer narrowing/signed comparison warnings under/WX; only fixture native-width constants and missing outputdir setup changed. Necessary incremental core-02GREEN9.400365s is not a clean-build duration. Savedv73 115flags, jobs4 below-normal, no runtimeprepare/stage/deploy.

Four distinct new CTests ran once, **4/4GREEN** total0.51s: holy-order0.09s, initialstats0.09s, personfiveleaves0.13s, monthlycaller0.09s. Earlier14passed checks reused, so second-batch subsequent cumulative **18 different new native CTests**; first-batch5 separate. This batch produces **36 new JSON files /39 scenarios** (person26 + monthly6 + initial3 + one holycollection of4). Earlier79outputs remain separate; serializer projection metadata is not a wire. All actual new producer bytes passed production consumers once. Person consumer firstharnessRED after6 successes used wrong helper field path; minimal consumer correction resumed only20 failed/unexecuted, never repeated6 passed.

| Package / morning item | Observable benefit and qualification | Readiness / remaining |
|---|---|---|
| D1 coherentpersonfiveleaf/absent | Actualtrait classifier+291B690 interleaving,275/2530 independentinputs,rawgov/weighted rows,rank/gather and cachedabsent insert-or-assign; calculatedscalar1300000 now releases existing manager_range PC777. NewfocusedPython1/1 plus26 actualwireGREEN. | Independently useful static-ready source primitives; required2922070/conference/provider/qualifier/list/tail and uncached440 remain. |
| D2 pre467 stagechain | productionnormalizer/traitcontract→orderedexplicitpostD1D0 stages→sixskill; unique newcaseGREEN0.015s, boundedprowess40 vs missingtraitfrontier14. | Boundedlogicalstatic-ready; tail continuation remains active and no currentfinal substituted for historicalprior. |
| D3 monthlycaller | SixactualwireGREEN0.0291802s throughsameproductionservice; war-side orderedcounters andpostwriterzero-strength rawIDqueue independentcalculations. True datecell originsourceclosed separately. | Static-ready same-input model; actualpost/loss/fullmonthlyfalse/null. Nextdailytransfer/removal input pkg inprogress. |
| D4 holyorderlifecycle | One nativeJSON/4samples, registeredMCP4/103GREEN at00:14:46; player service retention/combatdelay/release-queue readable independently of hire/resource terms. | Static-ready readonly; next ordinaryactive releasecommandsource-first, no employer/publicUnit actualremoval/live. |
| D5 initialstats | Threeactualwire→productionadapterGREEN at00:16:20; actual-currentProvince unequals targetcorrect, equalreuse, partialindependent. | Static-ready boundedinitialgettercache; ordinary/MAA changedstage formula construction next. |
| D6 nextspecificinputs | gbs5 storedCombat effectledger sourcefirstd46b27c3 + code12fd84e8/newPython1case4branchesGREEN, nativepending; gbs3 uncachedsourcebf98a57f adopted andnextkernel active. | Source/necessaryPython only untilnewproducerqualification; fulladvantage/Entryunfinished. |
| D7 reports/Git | Oct5formalclosure/Oct6realmeeting established00:03:36; 6dd863a8 normalpush preservedremoteC55 machine reports. Current compiled89cb fix/source followed thispublishedhead; next normalpublish pending. | Day/weekrolling, CIfornewheadpending. |

FullDLL **10034688B**, SHA256 **d10649a986f21b19e3ff86ae0586665542dd4b66e7f1a082cd86f337d9a3941b**. Fivebinaries,36wire files,literalserializer projection,CMakeCache/native-msvcresult,savedflags,firstRED/success/newCTest and consumerreceipts are archived in `Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/source89cb683d-core-native-artifacts/`; HASHES-AND-NATIVE-QUALIFICATION.json preservesinitialconsumerpending, FINAL-PRODUCTION-QUALIFICATION.json sealsactualsuccess. Earlierretainedstandalone sourceDB/9wire archive preservedseparately. No qualification is moved to a later sourcehead.

Prior REDs and current archiveglobharness4!=3 (includedprojectionmetadata) are preserved; corrected metadata filtering does not rerun build/CTest/consumer. Historicallive5035/36524/resume1882/G2 5/8/NW2 2/4/natural0 remains, todaynewautomaticdays0, allCK3/SDK/realpipe/UI/Steam/realprofile/save/cache/runtime ops0. Root is continuing functionalnextpackages, not stopping after thisbatch. Readiness never advanced to fullperson/Entry/forecast/monthly/productionlive merely by ACK or schema.

Evidence: `person-tail/FINAL-QUALIFICATION.json`, `FINAL-DAY-WEEK-FIELDS-20261006.json`; `monthly-caller-effects/ROOT-DELIVERY.json`, `DAY-WEEK-QUALIFICATION-2026-10-06.json`; `holy-order-lifecycle/VALIDATION-RECEIPT.json`; `first-contact-initial-stats/NEW-NATIVE-WIRE-CONSUMER-OCT6.json`; `person-stage-chain/REPORT-FIELDS.final.json`. Eachactualowner persistedday/weektest/artifact/commit/remainingfields andRoot mergedthemhere. Normalcommit/pushcontinues; nochecksduplicated.

## Stored combat contributions and daily queue inputs qualified (2026-10-06T00:48:39+08:00)

Two more boundedbackground packages completed: ordered actual Combat16B retainedsource ledger/base/resolved query and initial dailyArmyIDqueue transfer/first eligiblecall model. Source/Mermaid was frozen before implementation; parent14file packages12fd84e8 andcdf09eff adopted Root621bcf3f/52252a53. Unique newPython cases passedonce (stored4subcases0.002s, queue0.003s), no oldcase re-run.

Exact compiledsource **9d3461e4fe31c57d04824c331edda54d7a2fd8c2**, fullDLL+twonewtargets GREEN7.598313s necessaryincremental after actualharnessRED171.6032096s atf89fad9b. Newstoredfixture had undeclaredTransitionWire; c32 minimalfix uses existingrealproductionserializer/revision2. No kernel/provider change; no consumer used failedbatch. Firsttwo newCTests **2/2GREEN** total0.29s (stored0.13,queue0.08), previouspassedchecksnotrepeated. Subsequentnative cumulative **20 distinct newCTests**, firstbatch5separate.

Eight newactualproducerJSONfiles consumedonce productionpath: stored **4/4GREEN0.0014874s**, queue **4/4GREEN0.0335567s**. Storedledger preserves actualrow+8individualsignedamounts, key/order/zero/negative/empty/partial andowned/foreign; independentconsumeronly applies native side sign. It never recomputes retainedhistory fromloadedcurrenteffect40 or invents cross-sideclamporder. Queue copies observedorderedIDs tologicaltemporaryvector/source[] and selects firstnativeeligible request afterinitialinvalidprefix; selectedindices1/none/none/0. Laterduplicate occurrences needpost-callslots/virtualeffects and staypartial. It neverclaimsactualdrain, destruction, fullmonthly or historicalnativewrites.

FullDLL **10052608B**, SHA256 **adcc52861fd7c430ef66572b0270ee1641b47084fe1af711fc6bec44fc5e4398**, ordinaryoffline savedv73 115flags/jobs4 below-normal/WX. Threebinaries,eightwire,CMakeCache/native-msvcresult,firstRED/necessaryGREEN/newCTest andtwo consumers archived in `Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/source9d3461e4-next-effects-native-artifacts/`. HASHES-AND-NATIVE-QUALIFICATION preservesinitialpending; FINAL-PRODUCTION-QUALIFICATION sealsbothconsumersGREEN. Prior89cb fullDLL/36file39scenario and DB retained1/9archives remainvalidfor exactoldsources.

The nextordinarydamage pureprimitive e7566a48→Rootf89fad9b has one newcase1/1GREEN0.003s; fiveexactgetter sourcebodies nowclosed byowner. Fullsix/nativeproviderchild e0b30346 andperson16wire2922070+conference children754edac6/7066d25f awaitcentraladoption/qualification, no prematureGREEN. Stagechild4d365afb one newthrough2922530caseGREEN0.010sawaitsadoption; earlier pre467/275casesnotrerun. It reachesboundedpre291C4E2/prowess19 when realoptional helperinputsprovided, demandedBA0failureholds275/prow11 andlater2530 independentoutputs. These currentnewstage tests are synthetic source-shapedPython, not nativewire/live.

Rootnormalpublished **f89fad9bb7a7721676126ddb01929cbadda3cc31** with89cbarchive tag andOct6records; newfix/qualifiedsource9d ordinarypush next. Exact-headCIqueriesforf89/6dd failedTLS handshake once, qualificationpending; prior614CI SUCCESS is notassignedtonewheads. No CI failurecause guessed or passedchecksretried.

Currentreadiness boundedquery/puremodelstatic-ready. Wholeperson/Entry/advantage/forecast/fullmonthly/release/livenotcomplete. UserexclusiveCK3 continues; game/SDK/realpipe/UI/Steam/profiles/save/cache/runtimeprepare/stage/deploy andnewautomaticdays0. Historical5035/36524,resume1882,G2 5/8,NW2 2/4,natural0remain. Day/week rolling, furtherconcreteperson/ordinary/MAA/uncached/holyArmyrefs anddynamicadvantage packagescontinue; no backgroundexhaustion claim.

Ownerfieldsmerged: `monthly-caller-effects/queue-consumer-source/IMPLEMENTATION-DELIVERY.json` SHA87d994bb15070bd864a34c6f5e3fe169f37780001c9db071510161abaeed3de6; `retained-advantage/next-constructor-inputs/implementation/ROOT-DELIVERY.json` SHA47a789505a92553821ed38bf09aec7eb388cd940a4263550f772817ff62bfd7d. Nextqueue source2A98200 actualnewread897B laterfoundalreadycached; cost/cachemiss retained, no furtherclosedbodyreread; no newfunctionalcreditfromduplicatecapture.

## 人物后段、普通部队六属性与圣骑士团关联完成后台验证（2026-10-06T01:22:10+08:00）

完成四个有界输入工作包：人物2922070与conference四族、cache440=0无缓存recipient、普通部队完整六属性、玩家雇佣圣骑士团Regi→CArmy→Combat关联。原生树/Mermaid及最小查询方案先于实现冻结；通过这些实际输入继续解除人物/Entry和军队后置验证缺口。

Exact compiled source **3fb869c751d9050caffa790716a332ca71238c1a**。首次集中编译harness RED179.2425943s：新增conference夹具漏声明头；一处真实include修复ed483d93→3fb869c7后，必要增量fullDLL+三个新增target **GREEN8.0160481s**。首次新增CTest **3/3 GREEN，0.39s**（person0.11、ordinary0.09、holy0.09）；既有通过项未重跑。后续集中批次累计 **23个不同新增native CTests**，最早独立5项仍另记。

**35份新增生产JSON／38个场景**通过实际生产路径：人物helper/conference16份一次GREEN0.2159496s；无缓存11份一次GREEN75checks/process0.27675s；ordinary7份GREEN；holy1份含4samples、registered MCP83checks一次GREEN。普通部队consumer首次用请求索引代替实际完整ProvinceID而RED，保留原attempt，修正请求后仅重试失败direct帧，另外6帧首次执行；不是observer故障，没有为此重编译或改生产模型。其余旧wire/测试重跑0。

无缓存scalar660000解锁同query旧manager-range实际PC777；缓存未初始化支路仍partial。Conference精确四族请求，后两族独立；2922070保留DFS、稳定full-ID顺序、去重/跳过ordinal和BA0独立缺失。纯阶段链分别已在新增case推进至post2922530_pre291C4E2、post291F260_pre291C558（prowess19／30），但291F260使用held-current same-query operands，不能冒充重建过程中新model权重。新model配对构造/旧owner复制的source-only timing及provider返回边纠正另包待采用。

Ordinary观测真实selected Character／aggregate与加载五base，独立current或显式人物stage计算six FinalEntryStatInput；MAA的实际baseline、culture、linked accolade、selector/environment源和完整Entry继续施工。圣骑士团关联保留真实rawID、重复/顺序/合法fallback及独立nullable状态，为已有army_strengths提供native_carmy_id连接；普通玩家release命令receiver/factory未闭合，不以内部manager写入代替玩家动作。

Full DLL **10212352B**, SHA256 **f57170c41d82224b75abe34ecd4d96699b36989ba09e185b1c423bca5e5b9700**。普通离线MSVC /WX、savedv73 115flags、jobs4/below-normal。四binary、35wire、serializer投影metadata、cache/msvc与RED/GREEN/首次CTest共49文件先封存，随后十份owner receipts/fields合并到 FINAL-PRODUCTION-QUALIFICATION。路径 `Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/source3fb869c7-person-ordinary-association-native-artifacts/`；tag `archive/g2-background-20261006-person-ordinary-association-qualified` 固定该编译source。owner原始child7066/33d7/b580/e0b3/7cf3、stage4d36/7674/59dc均已Root采用。

新helper/conference source读取5962B（4330+1632），此前prefix6672独立；无缓存lane累计19849B含旧cache来源，不再重复加5029。普通getter累计4185code+324pdata；holy关联实现新增EXE读取0，command locator历史成本单列。成本及失败attempt均保留，未全EXE扫描/重hash。

上一已推送 **a3dbad213f06c91874d39e43e3d493dcbd81aff2** 的 [Official Runner CI37345080742](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37345080742) 已于17:17UTC查询确认SUCCESS；本批新提交CI另记，不能借用旧head成功。

当前readiness为有界 **static-ready**。本机5035/36524、resume1882、G2 5/8、NW2 2/4、自然终态0不变。新增游戏日、CK3启动/attach/SDK/realpipe/UI/Steam/真实profile/save/cache、runtime prepare/stage/deploy均0。完整person/Entry/forecast/fullmonthly及真实release loop未完成。

继续下一批：first-removal cleanup1cf7623f、新current direct258A470 advantage63ca/ef3；MAA arithmetic a4及其actual getter inputs；person signed-provider、qualifier与政府stage；动态优势具体分量和普通release receiver source。Oct6日报／W41滚动，不因本批交付停止；Root按默认正常commit+push发布并保留协作者共享报告。

## First-removal cleanup and current direct advantage qualified（2026-10-06T01:51:56+08:00）

首个 manager-removal 阶段与当前 Combat direct dynamic advantage 两个有界后台包完成生产路径验证。Exact compiled source **c7b1b2c0548bf6a34b2bcdf6c149d9c555756c71**：首次 full DLL＋两个新增 target **GREEN 192.3092681s**；首次新增 CTest **2/2 GREEN，total 0.39s**（cleanup 0.10s、dynamic 0.22s，完成于 2026-10-05 17:32:42 UTC／上海 01:32:42）。后续集中批次累计 **25 个不同新增 native CTests**；最早独立 5 项仍另记。此次只执行新增首次测试，既有通过项与旧 wire 重跑 0。

八份新增生产 JSON 一次通过：first-removal **4/4 GREEN，处理 0.0377004s／进程 2.7869819s**；dynamic direct **4/4 GREEN，处理 0.0013369s／进程 0.5929727s**。首阶段保留 manager50 的稳定首次删除、30 bucket 按实际第二 lookup pointer 清理、其他 swap-tail／16B record 的各自语义，只投影条件后状态；不声称实际清理、销毁、损失或完整 monthly lifecycle。动态口保留每侧 independently nullable 的真实 direct258A470 输出与 stored6C8／710，以 wrap64(base＋side0−side1) 得到同帧当前结果；current／stored 不一致是数据，合法零值、缺单侧输出、owned copy 独立保留。不刷新 native state，不调用 mutating258B510，不把当前缓存当历史构造或未来预测。

两项 consumer 均曾在导入阶段 harness RED，实际 wire reads／case runs 均 0：Root sparse checkout 漏了已跟踪的 `ck3_workshop_mcp`。Root 仅恢复该 exact package，源码与 HEAD 没有变化，随后才首次读取八份新 wire；RED 回执保留，不归因于 capability，也未改模型或使用 stub。首阶段 qualification 文档 child **80cd6d4e** 已采用；dynamic 的 source63ca8f5b／实现ef3eea0f 及本次 QUALIFICATION-APPEND 同步权威专题。

Full DLL **10228736B**，SHA-256 **97c9975feeaa9734476523df4dd1b363bf3828a151fbc6c1b80511c050513c94**，普通离线 saved-v73 115 flags／jobs4／below-normal／MSVC /WX。17 份原生 binary、wire、cache、MSVC、build／CTest 文件已封存在 [sourcec7b1b2c0 archive](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/sourcec7b1b2c0-cleanup-current-dynamic-native-artifacts/HASHES-AND-NATIVE-QUALIFICATION.json)；原始 pending 索引保留，本次追加 owner receipts／fields、import RED 与 [FINAL-PRODUCTION-QUALIFICATION](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/sourcec7b1b2c0-cleanup-current-dynamic-native-artifacts/FINAL-PRODUCTION-QUALIFICATION.json)。复用已封存 DLL 哈希，没有重编译、重跑测试、重读旧 wire 或重复计算 DLL 哈希。

实际 [CI37348249239](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37348249239) 在白绮旧人工 descriptor 缺 supported_version 处产生 20 个 error／12 个失败方法，属于 fixture harness RED。已修复白绮、牛来、体验优化和 independent 四处同因夹具；保留唯一 supported_version／tags 与所有生产检查。**31 个选定失败／未执行方法一次 GREEN**（12＋5＋5＋9），白绮原先通过的 6 方法重跑 0，生产 renderer／registry／真实 descriptor 未改。child **122b51d2** 已采用为 Root **c33336d0bfe8d2472c09e6e40d3698e25e04876f**；下一正式 CI 随实际新发布另记，不能借用旧 head SUCCESS。上一公开 head 为 **c63cbbcf9695b8a36fc5a56a59c9a4db8206cd91**，本次报告追加时本地 head 为 **aef3051a89def5da8d595f5ddec616dc4a56f976**；Root 随后正常 commit＋push，发布回执另记。

readiness 为有界 **static-ready**，完整 person／Entry、未来 forecast、full monthly 和普通 release loop 继续 partial。此次后台资格的游戏操作／新增游戏日均 **0**；既有 Z 历史 5035／36524、resume1882、G2 5/8、NW2 2/4、自然终态 0 是新授权前基线。用户最新明确授权“你现在可以使用这台机器的ck3了，我要去睡觉了。你继续执行任务。”，因此 Root 可开启新的 fresh resume；这项授权不新增 live 能力或验收事实，后续真实推进、paused artifact、日期、结果和清场分别记录。所有子代理继续后台工作，Root 独占实机操作及串行 Git 集成。

继续具体输入：first-removal 后续 Domain predicate／count 与 allocator callbacks，当前优势独立 components／opposite raw88／89，人物 signed-provider／qualifier／政府 stages、MAA baseline／linked／selector 输入和普通玩家 release receiver。边界与成本沿 owner 原始 fields 保留：dynamic source close 560 code＋368 mapping bytes，consumer 新 EXE 读取 0；首阶段历史重复 cache miss 如实保留且不重复计功能信用。首阶段：[qualification](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/monthly-caller-effects/queue-consumer-source/first-removal-stage-ledger/QUALIFICATION-DELIVERY.json)、[日报／周报字段](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/monthly-caller-effects/queue-consumer-source/first-removal-stage-ledger/DAY-WEEK-QUALIFICATION-2026-10-06.json)。动态优势：[交付](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/retained-advantage/actual-dynamic-getter/ROOT-DELIVERY.json)、[日报／周报字段](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/retained-advantage/actual-dynamic-getter/DAY-WEEK-FIELDS.json)。CI 修复：[完整回执](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/release-fixture-ci-fix/ROOT-DELIVERY.json)。

## Five native input packages and R0047 runtime cutoffs recorded（2026-10-06T02:44:46+08:00）

五个新增 native target 的有界输入包完成首次集中资格：exact source **47ecd200e6ef72d46c4d58e1ed7378a76aebae21**，full DLL＋五 target **首次 GREEN 195.8294221s**，首次 CTest **5/5 GREEN，2.75s**，2026-10-05 18:16:47 UTC／上海 02:16:47 完成。后续集中批次累计 **30 个不同新增 native CTests**，最早独立 5 项另记。**52 个新生产样本一次 GREEN**：provider6＋qualifier18／172 checks＋list14／130 checks、MAA5、components4、Domain5；MAA 的 SERIALIZER-PROJECTION 是 metadata，不计第 53 个样本。此批 native／consumer 无新 RED，既有通过检查／旧 wire 重跑 0。

人物 provider 各支路重新汇合 government／qualifier／FB10；qualifier 保留先 predicate 后 ID／dedup、每 definition 独立结果；list 保留 fullID 顺序／重复／sentinel／空值／真实 fallback 与非零 scripted scope 缺口。新增真实 normalizer 有界 stage 到 **postList2530DD0_pre291C7A7／prowess51**；缺行前缀50可独立保留，但 operands 是 held-current same-query，不是 evolving fresh-stage 输入。MAA 从实际 class／culture／aggregate／linked／selector／environment 输入产生六属性，不把最终 tuple 当 baseline；components 保留真实 commander／side 分量、zero／fallback／partial／owned；Domain5 的有序条件输出保留非零8count、wrap、alias和真实效果未观测边界。完整 person／Entry／未来 forecast、late helper／monthly 和普通 release 均未完成。Root 先采用 MAA **befce052**、list stage **8dbed4fd**；本脚本仅追加尚未采用的 owner qualification，保留各源／实现 pending 历史。[person38 final／fields](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/person-tail/FINAL-PROVIDER-QUALIFIER-LIST-QUALIFICATION.json); [qualifier18](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/person-tail/qualifier-28bc0d0-source/COMPILED-QUALIFICATION.json); [list14](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/person-tail/list-predicate-2530dd0-source/COMPILED-QUALIFICATION.json); [MAA5](Z:/ck3_mod_rewrite_process_assets/g2-background-round5-20261006/ordinary-maa-stat-inputs/ROOT-MAA-FINAL-QUALIFICATION.json); [components4](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/retained-advantage/actual-dynamic-getter/group-decomposition/implementation/ROOT-DELIVERY.json); [Domain5](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/monthly-caller-effects/queue-consumer-source/first-removal-stage-ledger/later-manager-removal-stage/domain-predicate-count-source/QUALIFICATION-DELIVERY.json)。

Full DLL **10349568B**，SHA-256 **05fd8939b2d922b4710e8bbb70716ae46b31aaf0f58f836833d489f2cb40e556**；普通 offline saved-v73 flags／MSVC /WX／jobs4／below-normal。65 份原始 native 文件已封存，原 pending 索引不改，新增 owner receipts／fields 与 frozen runtime bindings 汇总到 [FINAL-PRODUCTION-QUALIFICATION](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/source47ecd200-person-maa-domain-components-native-artifacts/FINAL-PRODUCTION-QUALIFICATION.json)。复用原 DLL／wire 哈希，不重编译、重测、重播或重新验证包。[此前 Official Runner CI37352493393](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37352493393) 已 SUCCESS，仅对应 **845128c761d2393071db864ac85b0724710a6740**；新 source47／当前追加 head **a090d8df1aec580a62a1c16b619c94ea7d04ca09**／后续发布 CI 不借此授予 SUCCESS。

用户重新授权此 Z 机器使用 CK3后，Root 恢复 fresh Operator／**R0047**，official no-launch preflight exit0，Robert **29829** 原普通战役／原 episode／v73，自正常 **h9052／raw53265168** 开始。九天里程碑截面 **raw53265384／h9067**，实际新增 **9日**，累计 **5044/36524**：三支原军 **268435481／184549452／301989997** 均独立在3711、route空／sieging，未合并；实际 K176100／tier2，B5298／G500／F6、D299100／ETA99，work **25428292/55000000**，occupation=False，War117分数38。030只记录当时 checkpoint SHA **64d68a5dbae804e2376af22d648fdf155d63f0b447f531596992d200a33945e7**；本脚本不读取后来被覆盖的实际 save。这里的 5044 是明确里程碑截止，不能当随后运行的最新计数。

同一条原战役完成 event29／option1 一次，Root 实际 API1；旧 instance29 消失／postcondition_verified，真实前后宗教查询 fulfillment **500000→1000000**，Rite **152→152**／Faith **23→23** 保持。这是观察→决策→动作→独立状态／效果回读的有界 production-live loop，不以 ACK 代替效果；不新增完整宗教、整战胜利、自然终态或完整 campaign 信用。

九天截面之后发生真实 controller 故障：050从 **53265384** 请求 **7日／speed5**，实际走 **13日**到 **53265696**，paused=True。因此截至 frozen050／051／052 是独立 **22日增量／5057/36524** 截面，不只计请求7，也不把超推进抹成 GREEN。该帧 breach=1／CanAssault=True，occupation=False；本报告不声明已执行 assault。Root 停止该 controller 并保留失败，051已保存 raw53265696／h9071、SHA **9f28ad3344b7e8c2247f9e83fa469ec1ba65cb16148490c8837b3dcb44bbaf5e**，052独立确认 paused=True。现有绕行是 **life-advance-one-day／speed1**；实证最小修复已另行分派，尚无修复／新验收 SUCCESS 声明。[nine-day checkpoint030](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/030-movement-checkpoint.json); [arrival strengths040](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/040-arrival-strengths.json); [occupation041](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/041-arrival-war-occupation.json); [paused arrival042](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/042-arrival-paused-snapshot.json); [fulfillment023](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/023-rite-growth-before.json); [event29 action024](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/024-rite-growth-select1.json); [fulfillment025](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/025-rite-growth-after.json); [post-event026](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/026-after-event29-snapshot.json); [overshoot050](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/050-siege-slice-01.json); [saved051](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/051-post-overshoot-checkpoint.json); [paused052](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/052-post-overshoot-paused-snapshot.json); [retained h9088 checkpoint060](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/060-siege-checkpoint.json); [retained paused070](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/070-single-day-block-paused-snapshot.json); [retained strengths071](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/071-single-day-block-strengths.json); [retained occupation072](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/072-single-day-block-occupation.json)。

整体 readiness 仍 **partial production-live loop**；此次52样本包自身是 **static-ready**，没有把 R0047 的实机 credit 转给新 source47 callbacks。G2 5/8、NW2 2/4、natural0、完整目标36524未达和百分比不宣称完成的边界保留。下一步优先用已授权的正常 Robert 观察／操作推进当前围城与独立后置结果，同时继续具体人物 C7A7／C8AE／nonzero15C、MAA outer changed stage、raw88／89、Domain point-store／late caller和玩家 release receiver。日报／W41持续滚动，Root独占实机及 Git 集成；脚本按此刻实际追加时间记录，不倒填午夜早会、不覆盖历史。Root随后正常 commit＋push，实际发布回执另记。

保留的后续单日截面：既有 speed1／life-advance-one-day 绕行060连续 **16次各 elapsed1／GREEN**，原 R0047／PID69432／connection_generation1／episode不变；至 **raw53266080／h9088** 累计实际新增 **38日／5073/36524**。这是已保留的里程碑，Root随后继续运行，因此不是当前最新计数。独立保存 [h9088 retained files](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/checkpoints/h9088-siege-single-day-16) 记录 **99239594B／SHA 132fbcf2fab9f8aab1e848b93154df09e4e621fdaebca6cfd637412129ab897b**；本脚本只复用receipt，不读或重哈希save。

070／071／072 paused回读：3711 work **34589892/55000000**（62.890%），B5246／G500／F6，Root实读 D298050／K175050／tier2／ETA69；breach=1／CanAssault=True、occupation=False／assault_in_progress=False，未执行assault。三军士兵 **8／2855／2383**、supply raw **29545455／7727275／29545455**；相对040到达截面，guard184549452减28、main301989997减24、engine268435481不变。这里保留普通士兵损失的实际观察，不凭两帧归因为单一原生路径；新Domain／components47静态包的资格不因此升级。060每步raw起止／实际日／speed／paused已逐项进入最终seal。

新 scope 变体 **265ba48→c6273217** 首个新增生产policy／registry回放 **1/1 GREEN，0.172s**，旧case重跑0；原七scope合同保留，原生0／API1推荐未改。该帧九名九型来自 **022 native18/public19**，authored option_count3来自相邻真实 **010 native17/public18**，同event29／actor／raw的相邻观察不合并为同一revision。SOURCE-QUERY-PLAN02区分实际9scope和authoring count3；opaque payload不作为选native0的额外输入。新识别合同仅 **static-ready**，Root023→024→025→026独立fulfillment／旧instance消失仍是实机效果证据，不记作这项新策略的live验收。[scopevariant delivery](Z:/ck3_mod_rewrite_process_assets/g2-background-round5-20261006/rite-growth-observed-scope/ROOT-DELIVERY.json); [first newcase1/1](Z:/ck3_mod_rewrite_process_assets/g2-background-round5-20261006/rite-growth-observed-scope/new-case-01.json); [scope sourceplan02](Z:/ck3_mod_rewrite_process_assets/g2-background-round5-20261006/rite-growth-observed-scope/SOURCE-QUERY-PLAN-02.json); [adjacent authored count010](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/010-movement-day-04.json); [nine typed scopes022](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/022-event29-context-after-save.json)。

另外采用的 **19290243→1025eae3** 文档和 **0e76→6b098171** opposite输入源码各自保留独立状态；后者尚未native资格，**不并入47批次52个已qualified样本**。此处单日绕行的实机结果与随后另行采用的87e33 cadence修复／静态case分开，不声明后者已获实机资格。

## Gated and opposite inputs qualified; retained3711 occupation cutoff（2026-10-06T03:15:33+08:00）

最新集中资格 source **93ee1bd6504b0a15db69d54f0fdf86bcd34eec5e**：24份 native 文件既有pins复用，**13个新增实际wire一次GREEN**（gated9／119 checks，opposite4）。首个 source540d5a16 build01 **RED 185.9697s** 是 `/WX C4244` 夹具 `optional<uint8_t>` int literal；Root仅把夹具字面值写成精确uint8_t，生产逻辑不改。source93ee build02必要增量 **GREEN8.85209s**，首次新增 CTests **2/2，total1.72s／wall1.7496s**。gated consumer0.0109802s，opposite0.0173485s／process0.4823549s，无新增 consumer RED；原通过test／wire重跑0。gated staged-format RED及build01真实失败保留。[gated9／119](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/person-tail/gated-temporary-tail-source/FINAL-GATED-QUALIFICATION.json); [gated fields](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/person-tail/gated-temporary-tail-source/FINAL-GATED-OCT6-W41-FIELDS.json); [opposite4](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/retained-advantage/actual-dynamic-getter/group-decomposition/nested-19F-inputs/implementation/ROOT-DELIVERY.json); [opposite consumer](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/retained-advantage/actual-dynamic-getter/group-decomposition/nested-19F-inputs/implementation/NATIVE-WIRE-CONSUMER.json); [opposite fields](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/retained-advantage/actual-dynamic-getter/group-decomposition/nested-19F-inputs/implementation/DAY-WEEK-FIELDS.json)。

新增 raw tree-first literal／knownzero current observer、fresh clamp/rank、内部prefix及恰好两次outer temporary贡献、独立currentA20／relatedBE0请求，只授 **static-ready**；命名非空dynamic tree／fresh历史stage／完整person与Entry仍partial。Opposite raw flag membership和retained amount sum有首次native producer→production normalizer资格，own19F **a507→5722** 仍待native、**不计入这13样本**。另有真实 normalizer stage **10474ec→abdaed8e**，保留首个harness assertion RED，新增case修正后 **1/1 GREEN0.018s**，skills **[6, 6, 6, 6, 6, 58]**／frontier **postGatedTemporaryAndList_pre291C9D8**，fullperson／Entry false；当时测试只修field-based missing diagnostic的断言，生产逻辑不改。[gated pure stage／preserved RED／new GREEN](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/person-stage-chain/GATED-ROOT-DELIVERY.json)。gated／opposite canonical资格已在 adopted commits中，不重复追加；原始pending及失败历史保留。后续集中批次累计 **32个不同新增native CTests**，最早独立5项另记。

Root原 R0047／PID69432／generation1／Robert29829／episode不变，保留 paused **raw53267544／h9159** 截止，正常5035基线以来 **99实际新日／5134/36524**。组成是初始9日＋050请求7实际13日（原故障不抹去）＋精确单日060×16、080×5、100×1、120×9、140×16、160×16、180×14。此为retained里程碑，不是随后运行的最新状态。保存 **99775465B／SHA b8beb9f39d5d896ec5f94bcc3ecd7d99cdc1ea99d41fdca793445491020c1837**，脚本不读或重哈希save。

190与191独立回读确认 **3711 occupied、occupier29829、F6／G25／B0／siege null**；三个target county的五处holding已occupied。193 War117440524实际分数 **64**（battle0／imprison0／occupation64／ticking0），duration **678日**，CB **raiktor_conquest_cb**；victory.available=False，战争未结束。194 terms.status=unsupported，reason=casus_belli_not_claim_cb：实际CB不是claim_cb，既有claim专用terms不授该conquest条款readiness。192三军实际士兵 **8／2799／1173**，当前attrition raw均0；数量变化不归因为唯一损失路径。[paused190](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/190-near-complete-siege-snapshot.json); [independent occupation191](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/191-occupied-war-targets.json); [strengths192](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/192-post-siege-strengths.json); [termination193](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/193-war117-termination-options.json); [terms194](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/194-war117-terms.json); [retained h9159](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/checkpoints/h9159-3711-occupied/checkpoint-receipt.json)。

这是围城→占领→独立状态／终战条件观察的 **partial production-live loop**；不授新source93 callbacks实机资格，不写整战胜利、完整OODA／Entry／forecast／monthly／release或complete。G2 **5/8**、NW2 **2/4**、natural **0** 保留。后续Root正在执行473移动计划／新210，已观察473 F4／G404，supply limit4562、route3712→472→3709→473；main的210移动已accepted并回读moving public279，raw仍53267544，guard／engine当时待执行。该新revision属于190截面后的工作，不预记到达、未来围城或胜利。

此前 [Official Runner CI37358348460](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37358348460) SUCCESS **仅对应a684cab20a170702a3899854f11735ff4e9fe07e**，复用[实际CI回执](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/CI-a684cab2-observation/FINAL-CI-RESULT.json)；source93／当前437ce380921c0d8c474fa23a7885fcac5855c37b／后续发布head不借用其SUCCESS。全部owner字段与冻结实机receipt汇总到[最终qualification seal](Z:/ck3_mod_rewrite_process_assets/g2-background-round4-20261005/source93ee1bd6-gated-and-opposite-native-artifacts/FINAL-PRODUCTION-QUALIFICATION.json)，复用24原始pins、不重编译／重测／重放／新CI。按真实追加时间记录，Root随后正常commit＋push；发布回执另记。
