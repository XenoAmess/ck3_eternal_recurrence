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
