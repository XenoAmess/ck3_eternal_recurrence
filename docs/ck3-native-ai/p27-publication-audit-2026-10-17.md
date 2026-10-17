# P27 外置成果入库核对与补齐

北京时间2026-10-17，证据时间使用UTC；机器 `xenoamess-full-tower-eb9d2c1186`。
本轮起点为公开 `3aef8584`。此前 SDK 正式能力已提交，但每场冻结 harness 的
可复用部分和性能候选没有同步完成抽取、测试及入库；这是本次补齐的交付缺口。
外置大视频、SAVE、Driver和完整trace继续按存储策略维护，只保留小型来源索引。

本轮前已经公开的成果：

| 成果 | 已有提交／入口 |
| --- | --- |
| 原版 CB 候选缩减、同帧 shadow | `d645eef2`，[专题](declaration-candidate-provider-12004.md) |
| battle typed-failure unavailable、按日观察与冷却 | `896f9c4c`，`bridge/battle_reader_watch_v1.py`及公共结果分类器 |
| 六类18树162技能、实际类别点数、独立回执和资源目录 | `ec88bd3f`；原生serializer原字节修复`7cae4561`，[专题](all-lifestyle-frontier-v3-2026-10-16.md) |
| same-day路线否决、非leader首都资格、被动观察、可选时钟诊断 | `b4cdaf52`，[路线专题](route-contact-readonly-unavailable-2026-10-16.md)、[时钟专题](exact-clock-observation-timing-v1.md) |
| Native21／SDK27加载、D盘录制与实际窗口中断 | `3aef8584`，[交接](../handover/2026-10-17-p27-native21-continuation.md) |

`b4cdaf52`的Official38932847485与Linear38932847553均已成功；这不替代新代码的验证。

本轮补入以下可复用代码及测试。每个项目保留独立状态，不能把“已入库”改写为“已实机验收”。

| 补入成果 | 仓库入口 | 资格和状态 |
| --- | --- | --- |
| 家庭查询复用当帧CampaignRoot | `current_first_heir_relationship_private_transport.py`及Driver cache的query_sequence | 核snapshot/public及native revision/date/actor/PID/connection全相同，旧帧仍独立查询；没有省略关系查询 |
| battle reader unavailable时的exact-one-day速度5 | `bridge/battle_reader_exact_clock_speed_v1.py`及Driver窄分支 | 仅已选择的孤立、我方、无移动／撤退的现有战斗观察，完整Native clock能力、明确无模态、无强攻；原+24日截止与暂停后验不变，无预测、撤退或主动攻击授权 |
| 敌军已在另一战斗的普通等待 | `_general_battle_forecast_ingress`窄分支 | 我军确为我方静止、非战斗／撤退、完整空路线，原追击目标已combat且原生单日能力齐备，才观察一日；不新下移动、不声明接敌安全或胜负 |
| Windows共享删除读取及恢复前置 | [shared_harness_reads.py](../../tools/g2_saved_campaign/shared_harness_reads.py) | 进程显式选择；READ/WRITE/DELETE共享，只对访问／共享／锁竞争最多六次、共0.31秒退避；JSON、schema、身份错误不吞。无HALT时不先读正在替换的累计状态 |
| 只读revision竞态及继承观察资格 | [readonly_precondition_portable_v1.py](../../tools/g2_saved_campaign/readonly_precondition_portable_v1.py) | 原件、上一METRICS、无before-submit plan、reviewed来源pins和driver-mode由调用方注入；不发动作、清pending或给信用。原场次registry的`handler(row)`不能直接加载这个参数化模块 |
| 原有继承恢复完整最小配方 | [候选patch](../../tools/g2_saved_campaign/patches/p27-readonly-successor-handoff.patch)及相邻JSON | 保留两叶完整增量，generation模块名只作模板；复用已存在handoff和材料SAVE验证，未部署、未有新死亡实机验收 |
| Driver WAL | [实验目录](../../ck3_autonomous_player/experimental/driver_state_wal_v1/README.md) | helper、Driver与cold-reader配对patch、故障／集成测试保留；正式SDK没有启用hook，默认关闭，尚未实机A/B |
| 原生battle子状态诊断 | [实验目录](../../ck3_autonomous_player/experimental/battle_reader_diagnostic_v1/README.md) | 原Native patch182cf32a和SDK兼容patch完整保留；未编译、未加载，不混入Native21 release |

家庭与battle焦点实际通过18项测试、16项子测试；加现有相关guard及关系transport回归，
本轮公共生产／harness范围通过81项、40项子测试。敌军已在另一战斗的新分支包含
实际AUTO3771／SEM3772投影、14个拒绝变体及真实公共chooser包装链。
Native／进程边界均使用fake，
真实响应仅提供小型只读projection。共享读取的7项包含本机Windows文件读取；
可移植revision／继承资格的2项覆盖来源改变、已提交计划、死亡／no-heir、错误episode、
Game／birth及title reconciliation等拒绝分支。Linux分支没有冒称在本机运行。

原场次actual375只读恢复已经有独立外置回执；新的公共参数化实现仅有离线资格和原件回放。
继承配方需要调用已有正式handoff、保留zero-credit失败边界并独立验证真实successor SAVE，
不能因为观察到角色改变就重放旧AUTO。共享helper不自动修改公共所有runner，也不会在import时
全局改Path；调用者须在隔离解释器使用显式上下文，退出会恢复。

WAL采用sealed-v3 base与有序校验journal，旧reader明确拒绝；同PID hot replay与SAVE／close
完整v2 barrier、closed-owner及两份hash绑定的外部materializer必须配套。
原27cad28e候选逐日仍重读／hash大基线，旧route-advance资格也未覆盖实际步名；本次
修订实验代码、完整配对patch和测试已入库，外置最终包pin为`b8dbf887…`。
该版在已hash的sealed base上核file identity／size／时间戳，
稳态append只stat，身份改变即拒绝；cold恢复仍完整核hash，不拿stat当恢复证明。
实验目录6项测试、6项子测试在公共源码临时副本上通过，覆盖严格路由条件、缺journal／
破损／乱序、材料SAVE、正常close完整barrier和closed materializer。
旧sealed样本的字节估算及离线33.5MB读取基准不是真实P27 A/B，不能写成已达到0.5秒／日。
独立审稿曾发现口头11/11与初版manifest的0/11矛盾：真实原件`final_screen=map_hud`，
初版错误要求None且微型夹具漏该字段。现在显式要求真实map_hud并保留字段，11份不可变
route原件资格重演通过；这只是存储资格，不是11次真实WAL写入或端到端提速。
实验patch不进入构建或运行入口，不因本次入库自动修改任何冻结SDK／DLL。

外置来源以`continuation42-cold-prep/`为相对根：家庭`p27-family-hotpath-audit01`
patch`ca1901c7…`；battle`native21-cold-generation03/p27-clock-profile-audit01`
Driverdiff`5f1520b3…`／helper`2d162fd3…`；共享runtime`ef5166e3…`、实际安装回执
`ROOT-P27-SHARED-HARNESS-READ-EPOCH01.json`；revision handler`6d70937d…`；
继承原配方`a58ee550…`。原件身份不由公共文件的换行归一化反向改写。
完整SHA与实验／正式状态见[小型来源索引](evidence/p27-publication-source-index-2026-10-17.json)。

指令给出时窗口23曾连续运行至少467日；随后17:57:01UTC的小状态实际记录
window23 `repair_required`、767日、raw53432280／10575周期。Root继续独占现场修复与游玩，
本次收口没有Game、SDK、Native或OBS调用。最近五批260.352秒／49日，即5.31331秒／日，
是Root交接引用的具名批次结果，不是整场平均；0.5秒／日和连续30年目标均未达到。

Root后续SDK28Rev2 attempt01在SEM／请求前因constructor的route5与既有
`configure_stationary_objective_hold_research_speed`要求route3冲突而停止。
这是已知配置边界，不是Game动作失败或Source测试失败；后续使用未启动的新attempt
按既有route3资格准备，不能为赶速度删除原守卫。本次公开提交不等待该现场重试。

本机Z工作树另有版本差异：Root只读核对其本地master落后远端185提交。
W是本轮公开提交checkout；Z未同步和外置成果确有漏交是两个已核事实，不能混作
“远端没有源码”。同步前已核Z clean、目标约51MB、受影响旧叶无共享hardlink、
无merge hook；当前SDK取D盘独立冻结源码，Game模组也挂D盘profile副本。
公开push后只作Z常规fast-forward；实际结果单独记录，不改变任何冻结运行树。

## 第二批归档与实际 SDK28 修复截点

第一批 `79055bb2` 已实际推送；Z 的 `master` 已常规 fast-forward 至同一提交，
工作树 clean。同步前逐一核过受影响旧叶没有共享 hardlink，当前 Game 模组与
SDK 仍取 D 盘独立冻结树。外置同步回执 SHA-256 为
`c136309a8e05306505f4f2bacef106b271d0b6659a052b4573323b99fc03d9ec`；
这次 Git 同步没有改运行配置、游戏存档或录像。

第二批补入的[接敌范围纯校验](../../tools/g2_saved_campaign/route_contact_exact_day_war_scope_v1.py)
仅排除原生明确 `retreating is True` 的敌军，缺字段或未知仍计入；public CUnit ID0仍合法。
实际 AUTO79 已按原生哨兵准确推进一日，但旧外置分类器错误要求把11支撤退敌军
也纳入接敌 scope。原始 clock／frame／paused 资格保持，完整窄 patch 和实际小投影
一并保存；不会复制236KB场次分类器到正式 SDK。

[可选研究预检恢复](../../tools/g2_saved_campaign/zero_rpc_optional_research.py)只资格化
已审查的 compare 配置 ValueError，要求原件、source-mode 原字节 SHA、冻结源码、
same-Game出生、独立暂停 SEM 和无提交标记均绑定。它只通过宿主回调提交本地 metadata，
计数不变、HALT最后清除，失败不重试、不伪造成功；没有 MCP、原动作重放或继承操作。
[runner 前置](../../tools/g2_saved_campaign/runner_preflight.py)要求首个真实 FULL 已发布才可
attach，并让故障身份包含内容 SHA／帧／计数。两个公共 API 及原最小研究配方已保存，
不因此宣称所有公共 runner 已接入。以上新增范围通过22项测试、22项子测试。

实际 SDK28Rev2 attempt02 沿既有 route3 配置热接同一 Game6068；FULL9先推进6日。
Root 随后在同 SDK 安装81／重消费82，FULL83只结算原 AUTO79 的一日，累计10610周期、
raw53432448；SEM85／METRICS86独立绑定同暂停帧。恢复 proof SHA-256 为
`c819433c8220c9b3341dd3d7d594da65ed0b7acf9aade92d1038bc4aee65fe12`。
没有为这个分类错误重启 SDK、重放 AUTO79 或追加业务信用。

窗口24因首 FULL 未先发布而失败0日，原事实保留。窗口25从 raw53432448重新起算，
FULL87曾成功推进13日；随后 Root 在2026-10-16T18:57:27Z报告 FULL516／AUTO541
以 `native_war_active_route_contact_horizon_unavailable` 再次阻塞，窗口25失败76日。
当前只记录这个失败截点，不把历史 running、旧767日或修复期间日期算进新窗口。
Game、Native21与D盘原录像由 Root 保持，下一修复另行验收。

当前优先级为连续30年稳定推进，其次先达到平均1秒／游戏日，再追求0.5秒／日。
三个目标均未验收；最近具名五批仍为260.352秒／49日，即5.31331秒／日。
WAL SDK29候选仍未部署、默认关闭；源码和离线资格不能替代实机收益。

## 冻结运行源码与公开源码逐叶核对

不能只核本轮点名的几项补丁。[完整差异目录](research/sdk28-public-source-delta-20261017/README.txt)
将实际 SDK28Rev2 freeze／source-mode绑定的1317叶与公开`79055bb2`比较，
所有实际原字节SHA及大小均吻合。联合1358路径中，1261原字节相同、5只换行不同、
45代码不同、6仅在实际运行源码、41仅在较新的公共源码；sparse checkout未检出的
16个Workshop模块使用Git blob比对，没有误报为缺失。

相对原运行基线`00a70009`，97个原字节差异分为67项公共已前进、13项运行overlay、
12项双方分叉或各自新增、5项换行。六个actual-only叶的完整create-file增量、
所有代码差异的完整窄patch以及97个hashguarded无损recipe均已入库，另有
[逐项分类](research/sdk28-public-source-delta-20261017/EXPERIMENT-CLASSIFICATION.json)。
其中正式来源、运行适配和研究入口分列；source inclusion／静态可达不等于实机运行。
仍需逐项评审的overlay已保全完整源码，未盲目覆盖公共M6等后续成果。

公共目录共105文件／2,400,223字节；没有复制57MB SDK树、Driver、SAVE、录像或trace。
只使用公开Git对象与recipe，在内存中准确重建1317叶／全部97差异通过，
不读取实际SDK或写回源码；wrong-base／wrong-target在优化Python中同样拒绝。
这是可重建研究档案，整patch反向应用会删除较新的公共能力，不能当生产升级方案。
原件metadata与recipe保留精确字节，来源索引记录其delivery pin。

## 第三批：已有陆军路线的不可用时间线出口

实际AUTO537／SEM542留下完整13敌军horizon不可用证据，AUTO541的旧负缓存没有
续行出口，导致上文窗口25失败76日。第三批仅把SDK30已定向验证的Strategy／Driver
必要hunk移到公共源码；原公共后续能力、Native、冻结SDK和现场均不覆盖。
同帧完整敌范围、精确原错误及我方已有陆军路线满足时先尝试原生Halt；只在独立
suffix后验，或精确原生提交前validator拒绝加unchanged-route后验后，进入既有
精确单日风险观察。Halt ACK仍pending，拒绝是零提交／零业务和日期信用，
未知错误不吞、不重放移动，也不改1.5准入。

公共生产imports新增8项／16子测试，连同既有相邻route／Halt守卫31项／23子测试通过；
外置组合SDK30生产方法32项另有pin。真实完整原件留D盘，小型projection与合成
validator／partial变体的边界明确。实际SDK30是否推进、存活或改善性能仍需Root实机
回执，不能由这次提交推定。详见[路线专题](route-contact-readonly-unavailable-2026-10-16.md)。

其后Root实际同Game热接SDK30，FULL3完成8日／30回合，到10862周期和raw53434464。
AUTO14的Halt ACK仍pending；SEM16独立读回只剩首边[5966]，原停军后验仍false，
后续完整h13查询恢复available并正常单日续行。原件14／16小投影已加公共第9项测试，
验证真实suffix与pending边界；不是实际validator拒绝或Halt后仍unavailable的验证。
独立SEM65／METRICS66及恢复proof`85137494…`打开窗口26，Root报告13日running前缀。
旧窗口25失败76日保留；源码与前缀均不授30年、速度目标、接敌安全或战果成功。
Game6068／Native21／OBS278060及原D盘录制未重启，WAL未启用。

第三批同时保存[可移植Halt结果分类](../../tools/g2_saved_campaign/land_route_halt_outcome.py)
和完整历史窄patch；帧绑定须由已审核调用方注入，拒绝回执零action／business／date信用。
公共CUnit0正例是兼容校正，未改已部署de0077；公共所有runner的接入不在本次验收内。
最终生产source、pure classifier和相邻既有守卫合计41项／43子测试通过。

## 窗口26后来失败与移动结果不确定

此前13日running是历史前缀。AUTO417在2026-10-16T19:39:07.549296Z返回
`CK3 move-army state is unavailable`，window26在72日后失败；原request
`step-440-2c2de938e06a`／move402653503→5980／expectedNative3207保留。
独立SEM418同paused日raw53436192、Native3208／public257已看到目标5980和
完整[5983,5981,5980]，并非可以安全重试的纯读取或无动作错误。
原命令结果未知和独立意图观察必须分开；不得重发原移动、伪造ACK、标为零动作清除，
也不凭路线存在授到达、接敌安全或战果信用。Root正准备可重复自动reconcile，
待最终源码／fixture一批入库，本条不冒称已恢复。

原生`SubmitMoveArmy`把缺bindings／ReadCurrent／构造失败与submit_copy=false
合成unavailable；`SubmitCommandCopyCompat`再把clone前unavailable与queue已调用后
rejected压成false，bridge只发同一句错误。原始417没有阶段诊断，不能从错误串
判断实际走了哪个分支。阶段归因仍unknown，既有后验足以禁止重发。
Root已关闭SDK30（queue1／app0），Game和原录像未重启，WAL关闭。

Root核算正常段AUTO68 start2026-10-16T19:32:00.731840Z至AUTO415
end19:38:45.227582Z：404.495742秒／72日＝5.6179964167秒／日。
明确排除417耗22.271467秒的失败和后续停机，不是full-campaign平均。
旧P28 4.671秒／日保留为历史段；稳定30年优先，再先低于1秒／日、后0.5秒／日，
目前仍未达标。

同段已完成回执的离线阶段审计另见外置`p31-current-siege-performance01/`
（FINDINGS SHA`9e14a6a9…`／MANIFEST SHA`58d3b9e5…`）：69次Army查询总157.882秒，
其中pipe发送／等待92.351秒、普通规划59.539秒，Python行normalization仅0.0428秒。
68次围城单日调用总188.143秒，life阶段143.378秒**内含**完整state持久化48.676秒，
普通规划42.557秒。这些嵌套／重叠阶段不能相加；pipe wall也不等于Native CPU。
compact回执不能证明private-scalar AB已启用。既有private scalar仍读完整53–55军scope，
普通requested IDs在全读后才筛选；不能把它说成安全subset或宣称节省90秒。
本期只有一次preview，未证preview-first可替代完整兵力／接敌守卫，本批不部署该研究候选。

## 第四批：移动 ACK 未知与源链验收

公共 Driver 已窄合 SDK31 的“原生报错后独立读回路线”修复，保留原始失败包与未知 ACK，
不把已见路线改写成确定未提交，也不重发原命令。纯分类器与3.6KB实际字段投影已入本批，
详见[完整小增量与测试边界](research/move-unknown-ack-sdk31/README.md)。
真实 Service→Driver→primitive wire 的9个新用例及既有移动回归共26项、22个子用例通过；
规划公共序号256与 Native3207分别核验。旧等序号/Hybrid 三项 GREEN 明确 superseded。

第三批 `c535719b` 的[官方 CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38956954264)
已实际 success。SDK31首次实际推进3日后又遇外置 route-window 分类遗漏；控制16/17仅安装分类器并重消费
原 AUTO14，FULL18/MET19结算原3日到11039cycles/raw53436264，无原 clock 重放，Game/SDK/OBS没有再重启。
随后 FULL20 已发布；此时间点尚未开启窗口27，不能写成已稳定完成30年。新 route-window 修复另包收口。
## 第五批：路线窗口分类与可选 UI 负缓存

route-window实际原14已在同SDK重消费结算3日，无clock重放；公共自含callback提取与实际完整原件、13KB投影
输出一致。SDK32的Service／overview／results三叶窄hunks及便携测试一并收口，保留读取失败ID和unknown；
results首次query失败仍是明确未完成项，不宣称absent或close成功。[完整研究patch与边界](research/sdk31-route-window-sdk32-ui-defer/README.md)。
新16项及已有窗口优先级回归共25项通过；第四d8dca28e的Official38962991406和Linear38962991499均success。

后续现场实际：SDK31 FULL83已推进5日后又因AUTO104负缓存阻塞；SEM105为raw53436696／Native3266／public59。
CTRL106仅本地clearNoAction，0MCP／0credit／0replay，保持11079cycles；SDK31随后queue/app真实0/0退出，
watchdog精确stop不冒称normal exit。resume01从未attach，不能补造窗口27在SDK31稳定running。

Root在2026-10-16T20:55:46Z报告SDK32已实际热接：FULL3成功12日，SEM64／MET65配对后先发FULL66再挂runner2752，
窗口27从53436984开始，当前具名截点11158cycles／raw53437440，累计19日；proof SHA `be270b5572b8b2d7712374a45dc860c46846762b2bdd7e1f4aa2c57520c050cc`。
同Game6068／Native21／OBS278060、Desktop1及原f333录像持续，watchdog232328健康；无Native新build、WAL或peace实验。
这证明启动和19日推进，不证明UI首次失败分支已实机触发，更不等于30年稳定或两级速度目标完成。

后续Root 21:02:10Z具名截点已达窗口27的302日／11323cycles／raw53444232，watchdog健康，无新阻塞。
20:58:32.782396Z至21:02:10.187353Z，两次完成队列样本覆盖192日／217.404957秒≈1.132318秒／日，
包含该连续段排队与规划，排除前面的战争／人工修复，非全campaign平均。SDK33首次results失败候选保持离线，
未打断SDK32；本批共享CI定向命令52项／36子用例及Python-only检查通过。

## 第六批：results 首次只读竞争的非致命观察

第五批 `18393cce` Official38967170365／Linear38967169970 均已 success。后续两叶最小修复仅消费 results query
精确 pre-owner `state_changed`，保留完整失败包／ID／租约和 unknown，可继续普通规划；不会关闭窗口或重放原请求。
12项新真实 Service／NativeDriver 测试与相关回归共25项通过。独立正式队列 AST／check_after／full_loop／持久化
回放保持零日期／业务／close信用、TURN2454B；[完整增量与复核](research/war-results-first-read-state-changed/README.md)。

本候选未部署，当前 SDK32 连续运行未被打断；不以离线回放宣称实机首次失败分支已验收。
稳定30年优先，其后<1秒／日、再0.5秒／日，均未达；已有302日具名样本与1.132318秒／日段仍按历史范围保留。

## 第六批 CI 完成后的真实失败边界

第六 `7e1cf70f` Official38972872688及Linear38972872670均已success。后续SDK32窗口27在AUTO2086
`native_war_no_alternate_player_held_county`无动作阻塞：raw53436984→53480760，共1824游戏日；
该窗口失败，不能将此前具名正常段续算成30年达标。SEM2087独立确认paused、public2464／Native5729／actor39979；
CTRL2088保持12076cycles，0MCP／0业务信用／无原动作重放。SDK32随后真实正常0/0退出，Game／OBS保留。
原失败包、fresh帧、零RPC清理和owner退出的精确出处纳入source-index；SDK33及撤离候选此时仅准备、未launch。

## 单县防守候选的公共收口

三源叶只增加同帧完整直辖封臣首都的Native预览种子及现有能力路由，保持实际移动的原版exact／full-hostile守卫。
五项无外置盘依赖的公共生产链回放及相关回归共26项、2子用例GREEN，原public2464与Native5729分别绑定。
164KB实际投影保留必要举兵和第一次独立读回，不复制完整history；synthetic deferred记录只证明规划退路，不当作实际移动。
[最小源包与验收限制](research/sdk32-defender-refuge/README.md)。本次公开不改D盘冻结源，AUTO wire／安全撤离／后续稳定待现场证明。
[两份有限报告](research/sdk32-peace-and-cb-offline/README.md)只保存小原件与pins；CB loader02旧失败与新静态闭合并列，
和平1.041361秒／日含3SAVE不当作整场均速，不将研究上限计为实际提速。

提交前Root另交SDK33实机链：preview16→horizon19→move22→SEM24→clock29/fresh31/32真实成功并后来到达2604，
[精确小原件](research/sdk32-defender-refuge/ROOT-P33-ACTUAL-DEPARTURE-CHAIN.json) SHA64228d8e…保全。同Game／OBS保持。
但FULL178／AUTO191在`native_war_counterpolicy_hold`再阻塞，窗口28失败31日／raw53481528／12157cycles；
出发修复已实机，抵达后驻守／再次撤离仍待SDK34，不能宣称全面稳定或拼接旧1824日达标。

## 第八批：抵达生命周期、真实启动基线与事件中断

公共两叶窄合SDK34 FINAL02，新增抵达直辖封臣首都／返回己方首都后的原生零跳和下一预览生命周期；8项便携回放直接使用公共Driver能力与实际精简历史，安全／不安全后续原生输出明确合成。实际移动仍需完整原版资格，未把空路线当安全证明。

第六首次results读错分类的旧独立正式夹具误给八字段当前frame，已复现真实六字段startup后的拒绝并纠正；当前规划源／raw Native包／lease／Game八字段仍严格，启动只绑定actor／episode及日期下界。新12项连同旧12项通过，正式queue AST／持久化另保10否例。旧GREEN原件保留并标superseded，不再冒充真实baseline验收。

AUTO50实际一天＋event110的消费者只放宽合法暂停弹窗读回，完整clock、敌军、四动作与METRICS后验不变。公共函数、真实完成包投影、16否例和UI形状测试23项／10子例通过；不会给事件选择或战争信用。Root同SDK52/53/54只安装／重消费／结算原一天，随后真实选择event110并完成异步原版离线分析，来源注册已发布。精确出处及未知边界见[有限归档](research/sdk34-refuge-and-readback/README.md)。

最新Root截点窗口29失败3日，修复后的30又失败58日／12448cycles／raw53483040，根因当前原生零跳不可用与替代路径危险；不再写仍running30。新Native22未部署，本批不混入新DLL或WAL。连续30年稳定优先，再<1秒／日、0.5秒／日，均未达。第七d173f601 Official38990144747／Linear38990144789均success。

## 第九批：零跳与采集释放的有限闭合

第八41846f49已push／Z同步，Official38994392765与Linear38994392772均success。后续Root已报告Native22冷载新Game263980、同raw53483040和12448周期无回退；旧30失败58日不改，新31尚无准入。公共只移21行原生零跳与既有fixture，并实际MSVC compile/run通过，保留后来9行movement cutoff，不复制DLL或334头全manifest。新测试EXE精确Defender登记实际仍admin-required/no Add，未记生效信用。

录制218.234秒延迟与21.23GB仅由小元数据推导，旧90秒失败／Game强退与迟到OBS正常关闭并列。主仓CK3录制适配器先release／capture_closed再后台SHA，保留公共主窗口GetParent守卫；公共只读reader和真实producer实接验证媒体SHA仍未完成时采集已关闭。独立宣传工具链未被vendoring，R4私有shutdown原小patch单列研究，不假称所有public host已接入。

两个modal消费者公共4producer／48否例与CUnit0真producer通过，明确使用正式SDK验证器、无UI业务信用；旧runtime整canonical不搬。WAL报告已在第八入库，不重复实现；速度5报告保留default off／35不采用／未来2748重基边界。所有精确来源与测试见[第九有限归档](research/sdk35-zero-hop-and-capture-close/README.md)，无视频、Driver、SAVE正文读取或复制。

提交前Root另交实际Native22零跳和clock一天成功原22，raw53483040→53483064／tick1／paused／overshoot0；地图＋overlay首帧和watchdog均已实际准入。旧55b随后因stationary phase遗漏拒绝结算，FULL21失败、同SDK纯分类修复中；不把物理一天推进写成新窗口31已开启或主流程已恢复，也不重发原时钟。

## 第十批：stationary 消费与停止／恢复提示

第九4f71b101的Official38997913853／Linear38997913841均已实际success。其后Root在同SDK安装25、仅重消费26，FULL27／MET28结算原22的一天；普通FULL37／AUTO38再真实推进到53483088，SEM40／MET41匹配Native7／public8和12457周期。旧FULL21误拒仍保留，修复未重启Game／SDK／OBS，也未重放原时钟。

公共stationary分支严格要求原生完整空路线、同帧合法姿态／完整hostile与精确clock；50项实际投影／生产租约／旧moving popup回归通过。新停止原因／修复状态工具参数化入库：v1两态画面经Root亲审，v2增量读、SDK／feeder／summary等新增异常来源只作离线资格，25项／8子例通过。不把安装ACK或原失败动作日期的重消费当作“已恢复推进”，须另有真实新日历FULL和fresh匹配暂停SEM。[有限源包与边界](research/sdk35-stationary-and-repair-status/README.md)。

本批截点窗口31未开，不将两次一天观察当作30年完成；稳定30年第一，随后<1秒／日、0.5秒／日，均未达。未来不可避speed1消费者与WAL／速度5研究分离，不因提示功能或stationary实证外推其生产验收。

## 第十一批：暂停读取、不可避接敌与已结算恢复提示

第十 `20ae0155` Official39000024458／Linear39000024440均已success；之后外部 `4f3b6c4f` 的Official39001084726亦独立success。其晚到录制暂停证据刷新守卫保留。公共新增精确 campaign-root 暂停边界纯资格函数与实际247小原件；Native分支在读准入／TrySubmit之前，业务、超时或未知错误不匹配。Root实际249只生成SEM250，12550周期／原日期不变，0业务／不重放，后续FULL251成功23日。

不可避接敌消费者保留完整敌军、同帧租约及速度1／+24／tick1／overshoot0／paused，未把未知路线改成contact-free。实际130为predicted_only；实际170才是active_combat_observed，FULL149只是成功15日批汇总。原件与18否例及旧moving／stationary回归经过公共消费函数；日期以外业务／UI／战果信用皆零，不绕过1.5主动攻击门槛。

修复提示v4细化真实Native错误，v5从已结算TURN、成功AUTO、配对MET及精确存活SDK双进程身份证明恢复，不等待整批FULL。10.7KB投影保留实际252／253／12551的必要字段与原SHA，waiting-state／最小loop／活句柄边界明确合成。公共导入改用实例方法，不修改v4模块全局函数；v1两态像素实证不外推为v4／v5全来源实机验收。[完整有限归档与源链](research/sdk35-readonly-and-settled-status/README.md)不含250KB canonical、4MB原夹具、媒体、Driver或SAVE正文。

窗口31随后在AUTO349 counterpolicy_hold失败，raw53484480→53484768仅12日／12597周期，SDK35正常0/0退出；不把先前6日前缀写成持续running。Root随后以83745edd准入窗口32／SDK36，基线53484792／12603周期；04:36:34Z报告63日／12813周期／53486304、runner76027及采集健康，同Game263980／OBS56104／原42cd录像不变。近期45秒小样本约2.58秒／日，非整场均速。失败窗口不拼接；连续30年稳定第一，再<1秒／日、0.5秒／日，均未达。

Army146／148只证明同帧比较和use配置，未来AUTO选用及收益仍需指标。等待段默认头尾各2秒、中段快进最多4秒；通用EDL归独立promo仓，CK3绑定／正式启动metadata收集另批接入，不复制通用engine进主仓。render-plan目前仅估算，真实PTS映射与像素复验后才可授最终编码资格，本批未读取或编码活动媒体。

## 第十二批：跨 SDK 提示、当前故障去重与默认停顿元数据

第十一1af385fc Official39003837013及Linear39003836974实际success。SDK36 transfer保留原349停止时间／source binding，新19／20已结算推进才恢复；当前readonly1876／SEM1877仅识别修复已应用，按小TURN顺序找到真实首正向1911／1912，不读零日期大AUTO。专用4MiB／2MiB上限与普通core1MiB分开，公开正常import不覆盖v5全局函数。旧watcher32513 exit1及误报4b／0c撤回保留；最新当前pending／feeder／terminal原故障去重守卫一起收口，不把历史HALT误当新停顿，也不称全部异常已验。

Root较新报告SDK36窗口32已383日，旧31仍失败12日；当前Game／SDK／录像不由本包切换。稳定30年第一，再<1秒／日、0.5秒／日，均未达。Family仅修未定义child-focus submit_step，技术负缓存完整窄包仍研究未部署。

纯EDL在独立promo12ecaf98／正式v0.3.0发布，275项正常及275项-O通过、Release39005285835 success；wheel真实SHA f59c4b62…核验后主仓同步精确依赖。主仓仅CK3 adapter／collector／默认2/2/4 policy和future actual-started hook：一个hidden metadata child，cleanup写自有STOP，错误不请求停止录像。CURRENT先不可变快照；撤回误报没有等待编辑，不覆盖真实已闭区间。当前私有provider／collector未改；最终PTS／素材／mapping／像素绑定尚需独立合格入口，旧不完整render candidate只保研究，0encode／无成片信用。[第十二有限源包](research/sdk36-status-and-stall-edl/README.md)。

用户随后明确干净重开1066罗贝尔、重录／重跑，至少主菜单起录，公开视频《罗贝尔的三十年》伪一镜到底；阻塞中段<5秒、默认4秒并保留原因／修复。旧carry37取消（未现场drain），Source37／缓存／focus-present仅源码复用，新局天数／战果／Driver／goal零继承，旧945日等不能转记。新局和成片未由此文档或离线测试完成；正式hook不要求已有地图／actor，实际主菜单录制资格另记。第12修改CI入口174项／91子例及loader1项实际通过；最终PTS与像素校准渲染归独立promo，当前D2和D视频不限长合同保持。

## 干净原版新局：继承binder小包

SDK37 CLEAN03的无XAR ordinary-no-pact合同窄移植到公共binder，保持None与xar_off区别；实际profile空清单、固定日志审阅、环境SHA和Game代字段缺失／unknown／篡改均拒。公共M7两个旧off硬门共同识别精确新六字段合同，无SDK导入依赖或第二queue。31项／24子例在正式公共入口通过，public6／Native42、原回执不重放与同owner保留；fake传输不授自然死亡／SAVE实机信用。新局启动与录制仍由Root实际准入，不承接旧局成绩。[来源与边界](research/sdk37-verified-vanilla-lifecycle/README.md)。

## 第十四小包：停顿身份与实际私有调用者

第12 b25c96f2／Official39007487520、第13 be658a4e／Official39009194515及各Linear均success。旧EDL collector35452 exit1已证，不能称持续healthy；缺序号误用None为legacy AUTO身份。公共adapter仅两hunk，正int＋同已知SDK代才fallback，其他按incident ID，真歧义拒绝，13项／11子例通过。保原6区间及false标签的历史事实，不将其当最终有效等待；通用promo0.3未改、无编码或媒体正文读取。

私有automatic_handoff的04f798窄delta已补存，normalize／Native／PID／actor／episode／分封／零重放守卫保留，实际不import公共M7。另附M6 host-death通知与M7 Tribal市场／authority的三份静态缺口，均无新API／实机信用、G2仍6/8。[有限来源索引](research/sdk37-edl-incident-identity/README.md)。新局从主菜单起录、旧成绩／状态零继承；稳定30年第一，速度后续<1再0.5，均未达。
