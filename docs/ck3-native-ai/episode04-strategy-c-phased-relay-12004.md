# 第4期 C：同 S0 的分阶段执行接线

[phased_relay.py](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/strategy_c/phased_relay.py)把既有 C state/next adapter 与 Root 文件 relay接起来。`--help`、导入及`prepare`仅离线读源码/JSON；只有 Root 显式调用一个live stage才会向既有request helper提交请求。本工作包只做准备和两个合成接线例，没有调用SDK、游戏、桌面、EXE构建或录制，没有把C正式对照标为完成。

离线执行机器 `machine_id=desktop-3fevhd2-1c74096080`，冻结源码 `dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb`。当前准备包为 `high-parallel-C-stages-a03`，时间及源SHA见 `SOURCE-INTAKE.actual.json` 和 `DELIVERY.actual.json`。所有部署、Steam离线、进程资格及容量必须按实际目标机器重读；本组合器的现有Root admission仍限定这台机器及普通Robert来源，不能据代码可导入外推其他机器实机已通过。

## 已有 runner 与最小改动

开始前已找到并核对现有 `r12-r13-root-helper-a02/locked_routes_root.py`，以及 `filming-delta-a03/locked_routes_dcda.py`（28677B，SHA `39195635236da76a547a4fbca4dc4e06406da4b83c28453994c32b3d3ed26133`）。实际R13入口是项目外置根的 `r13_stage_a06.py` 和 `r13_requests_a06.py`，不在filming子目录。另有仓库的[同T0 control binder](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/bind_common_t0_control_runner.py)。这些入口各有原用途，未另造SDK连接器。

C组合器复用旧Root helper原有的进程/创建时间、source/context/proof绑定、response-local完整Driver引用、once claim、原响应读回、普通frame读取及dcda `coherent_stop_core/strength_at`。只有私有ledger名称通过已限定的单个AST常量改为`strategy-c-phased-a03`；source、当前assets名和Root实际请求预算显式配置，不继承旧512MiB作新容量授权。请求方法与游戏动作实现不改写。

逐日推进仍沿用R12/R13的“Arm→一次Resume→只读等待暂停→status→新同帧core”的顺序，并调用现有production native sentinel normalize/Arm/stop validators。C按自己的合同采用`speed5 / terminal-a-0 / exact_one_day`，每次target严格为原date+24；不会拿R13 speed3多日burst伪造C一日记录。累计generation与一日来源再由既有C `observe`检查。

准备包保留这些小型依赖的精确字节副本和pins；它们是来源复用，不是本次重新运行旧资格。替换来源先重新审阅和更新pins，不使用目录latest或静默换成不同helper。

## S0与候选：先冻结，再正式独立冷载

Root本轮指明的候选S0来自R0175最终静止状态：Province1036、date53146320。这个信息属于Root提供的该机器历史来源；本worker没有读取其存档或进程。正式A/B/C仍须另行取得冻结合同中的普通共同checkpoint、其native保存回执及完整baseline。不能从R13已经锁定或改道后的局面直接开C臂。

`probe-via`只在draft pilot case从S0读取完整队列及调用方具名有序候选（最多8个）的fresh native previews，不推进日期、不提交Move，也不自动冻结plan。结果复用已有`choose_draft_via`；只证明当前第一段可预览，via→共同目标仍等实际到via时的新原生preview。pilot结果确定后，Root先冻结exact waypoint顺序、共同目标、同S0、完整cohort/统帅/loaded features和停止政策，再为正式C独立正常冷载同一份S0。正式case拒绝更换plan pin或把pilot过程当新臂已执行。

`admit`会对照实际prepared receipt中的`checkpoint.source.save` bytes/SHA与冻结普通S0，要求plan冻结早于当前cold started time、actual source/DLL相符，并将当前完整endpoint与冻结baseline逐项比较，再调用既有C `start`。没有C专用修正Halt、换统帅或重设日期。若S0实际仍有route，保留拒绝；应在正式实验前统一重冻一个合格静止S0，不能只对C停军后说三臂同起点。

## 明确的阶段与一次动作

```text
<verified-python-with-jsonschema> -B -X utf8 <package>/tree/promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/strategy_c/phased_relay.py prepare --bundle BUNDLE.actual.json --output PREPARE.new.json
<same-python> -B -X utf8 <entry> admit --bundle BUNDLE.actual.json --attempt C-admit-a01
<same-python> -B -X utf8 <entry> move-once --bundle BUNDLE.actual.json --attempt C-leg00-move-a01
<same-python> -B -X utf8 <entry> path-after --bundle BUNDLE.actual.json --attempt C-leg00-path-a01
<same-python> -B -X utf8 <entry> advance --bundle BUNDLE.actual.json --attempt C-leg00-days-a01 --max-days 7
<same-python> -B -X utf8 <entry> report --bundle BUNDLE.actual.json --attempt C-report-a01
```

一个调用只运行一个stage，Root按结果决定下一步；同一case禁止并行stage。`move-once`先保存pending state，再由现有Root action helper保存该leg专属once claim并最多提交一次typed Move。新目标必须是冻结顺序中的下一项，fresh preview必须同帧；失败/超时也不删除claim重发。

`path-after`先读该leg原请求的实际响应，再独立读取同日较新native frame、预期完整route及整军DATA，才转marching。ACK不是path-after，route生效也不是到站。

`advance`每次明确1–30日批上限，同时始终受共同T0+90日绝对上限约束。每个完整日保存原Arm/status pins、独立后态、完整DATA及C state。到中转点后立即结束该批，让Root审阅并另显式调用下一段`move-once`；不会自动跳段。原cohort及全部strategy Army人数、逐records缺口按既有C完整性门处理，缺DATA不补0，effective/prepared不冒充physical。到站仍是`(最后未到,首次已到]`且exact tick为null；不会把旧`(75,77]`写成精确日。

当真实第90日未到才是预算截尾；主动stop、modal、战争/身份变化、测量失格等保留原诊断，不冒充旅行失败或D90。普通陌生事件交还Root已有原生策略采集、选择与离线分析流程；组合器不会点GUI或制造事件结果。

## 结果未知与可收口恢复

Move结果未知时只运行`path-after`读原响应及新当前帧；若原响应仍pending/rejected，不能提交第二次Move。状态文件采用exclusive-create，state index仅在本case追加明确pin，不按mtime挑latest。

真实日可能已经完成，但其后普通core查询或状态提交失败。此时使用：

```text
<same-python> -B -X utf8 <entry> recover-day --bundle BUNDLE.actual.json --attempt C-day-recovery-a01 --day-start-raw <original-start>
```

它要求原day claim和原Resume的正面原响应，读取原Arm、fresh只读status及当前同日独立完整core，再执行现有native stop验证和C `observe`，**不重发Arm或Resume**。当前日期不是原start+24、generation/身份不符或DATA不完整时拒收，保留原证据。Arm已提交但从未形成Resume claim的更早中断，不由该方法猜测resume；Root先查看确切原Arm/status并通过已有explicit cancel/正常会话恢复流程处理，不能删claim重造同一日。

## 缺字段的具体施工入口

随包`BUNDLE.UNBOUND.json`故意没有当前C runtime。离线`prepare`输出`NEEDS_ROOT_BINDINGS`和每个缺字段的`construction_entrance`，返回2；它不是可批准的live绑定或永久unknown待办。

| 缺输入 | 现有补观测/准备入口 |
| --- | --- |
| 普通同S0、plan/baseline、loaded save SHA | Root正常保存/prepare回执与[正式比较合同](episode04-comparison-contract-12004.md)，只核小元数据，禁止改opaque存档 |
| 当前context/proof/source/DLL、cold开始时间 | 新正常分配与已有runtime身份probe，实际PID/create-time/generation/actor/episode及部署来源回执 |
| Whole DATA/ordinary core | 现有`ck3_take_snapshot`→scoped `ck3_query_army_strengths(profile=ordinary_core_v1)`，取该响应精确引用的完整Driver文件 |
| 当前统帅 | 现有`ck3_query_army_commander_candidates_v1`，同帧`army_commander_candidates.current_commander`和完整CArmy/date witness |
| 统帅actual absent | 原R10 endpoint仍要求integer；当前组合器明确拒绝并保留absent。共享endpoint/C基线若要支持absent，需以原typed query status显式扩展比较，不能写0 |
| actual loaded features | 当前run实际preflight/playset/features JSON的source pin+pointer；不复用其他进程或凭源码置true |
| 单个record缺失/partial | 修复该actual query的DATA捕获/发布，再取得新同帧完整查询；不能用摘要或旧帧拼补 |
| Runtime容量 | Root为未来C scene批准实际请求/响应/ledger预算与原deadline；child准备配额不等于新scene获准 |

该worker没有更改上述共享消费者以追认局部ready。`READINESS_GAP`会指出确切失败口，补齐后继续原case允许的只读阶段；已提交动作仍不重发。

本轮仅执行三个新合成接线compound，使用既有Root `action/claim/action_original`方法和真实C guards，注入合成请求后端及native validator接口替身；第三例验证UNBOUND的具名施工入口及拒读opaque文件。证明的是新阶段接线、一次提交、路径独立后态、日记录传递和原响应恢复；不授实际native时钟/实机、完整ABC、费用、动态镜头或影片资格。原10/13测试未重跑。测试源码、输出及复用helper均保存在具名外置准备包；入仓候选仅共享entry与本文，不把外置包的其他依赖文件整体复制进仓库。可移机复算需随包保留精确小型复用源并重绑bundle路径/pins；当前Root机器的live admission限制仍须显式适配和重新资格，不能静默继承。

本准备包≤1MiB，计入Root已分配active32MiB及metadata17池，容量来源`continuation-r13-a06/CAPACITY-ACCEPTED.actual-a01.json`；原复核截止2026-10-16T07:45:01.597Z不延长。不在本轮启动任何未来C scene或执行重型写入。
