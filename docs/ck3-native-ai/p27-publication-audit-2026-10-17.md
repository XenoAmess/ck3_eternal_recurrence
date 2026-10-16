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
