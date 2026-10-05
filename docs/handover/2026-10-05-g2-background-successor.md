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
