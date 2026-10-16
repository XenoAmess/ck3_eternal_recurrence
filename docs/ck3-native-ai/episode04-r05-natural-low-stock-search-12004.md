# R05：有界自然低库存检索与下一场选择

编制机器 `machine_id=desktop-3fevhd2-1c74096080`；2026-10-16 UTC 离线检索，具体读回时间和小原件 SHA 见同包 `QUALIFIED-SMALL.actual.json`。本页没有游戏/SDK/桌面操作、EXE读取、构建、存档读取或新业务信用。目标知识为 1.20.0.4 / Steam25734779 / EXE `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；这是已有 source pin，不是本次重新核验安装或运行。

**本次没有找到可直接加载、已经实测 stock<10 且负 rate、至少20名合格兵的普通 checkpoint。** 可以优先准备的替代场景是同一 Robert 的 **R180 普通2645存档 → 重新读候选 → 一次合法低容量换将**。它避免从 R189 围城位置重新依赖当前不可用的 route preview；仍须正常耗补给，不是一个短饥饿窗口的现成正例。

## 检索范围及拒收

限定 `git ls-files` 中 `docs/ck3-native-ai/` 与 episode04 promo 的小型 JSON：1762项元数据中，1675份单文件≤131072B、共20,983,019B进入 JSON 解析。先检 exact stock/raw 字段，再独立检查 decimal-string 和 supply/stock 子对象的形状；没有遍历外置巨目录、存档、ledger、全局军队历史或 EXE。完整逐文件元数据在压缩的 `TRACKED-METADATA.zip`，两个脚本与小结果保留，可复核范围而不重导出。

exact raw 检索没有匹配；形状检索17份命中全是非库存或合成例：supply usage/limit、byte更新标志、overwritten计数、monthly rate、panel126/100、原始源码行号，以及 `illustrations_only` / `arithmetic_example`。**零 rate、stock0 算例、state threshold0.5 均不是实机低库存。** 此结论只覆盖明确列出的集合，不声称所有机器/所有历史存档都不存在低库存。

| 已有来源 | 可用事实 | 本次资格 |
| --- | --- | --- |
| R176 `saved-r0176-supplies.literal-a01.json`，同机器 exact4 | date53146632：Army18为300；93/94/95均为100，各250人 | 全部不低于10；93后续combat不能当当前对照。 |
| R180 normal save + day5，后续R181 a04 | 同机器 Robert actor31254 / Army18(native18)，date53147592，2645 regular1、route完整空、无combat/retreat；R181同日期实测 stock300/cap300/rate−175438，1184兵 | 合法准备基线；没有低库存或实际 starvation debit。 |
| R189 commander 原件 | 同机器 Army18/native18/owner31254，date53149080，native3/pub4；完整14名候选 | 生产 normalizer 接受；10名 actual CanAssign=true且条件cap100。不是已经换将或 stock100。 |
| R0172/173旧专题，exact1.20.0.3 | 历史actor33388/Main0 stock116.51751→110.37716，随后106.13988；分出子军100 | 均不低于10；`machine_id: unknown`，旧.3不能授本机.4可用性、actor许可或业务资格。 |
| common-T0 R0173 exact4普通对照 | actor31254 Army18 stock300，承诺登船路线 | 非低库存；不得把其它原件的stock拼入这个save。 |

前三行数值均有小 JSON 原件路径/bytes/SHA，见 `QUALIFIED-SMALL.actual.json.source_pins`；旧.3是排除性历史知识，不能当新候选。没有发现可直接替代的、已获当前剧情身份许可的其它actor低库存存档。无需为此换成William或把旧33388 runtime ID搬进新PID。

## 最少动作的具体选择

由Root选择是否在下一场加载现有 **R180正常存档**，而非改变当前R189录像/闭场。小回执保存于：

`C:/ck3-e04-resume-20261015-a01/live12004-logistics-next-a09-a01/arrival-closure-a01/NORMAL-SAVE.actual.json`

其原件 SHA `d17aa2bd77d706f7017ca512deb812b0cd0ed60aa529a1dfcdab627397c82e1d`。记录的save为72,973,969B、SHA `e4cac633d1b27ecaa063ecf6a8ae7f31ac8b9ca99edf1fb8517ec4d2844e4892`。本次仅 stat 该回执的确切save路径，文件仍存在且大小相同；**没有重核其当前内容SHA**。加载前按既有managed input绑定核原件身份，不能把stat当内容验收。R180历史runtime PID16736/create134365825176284454/episode native-31254-75ef9942b4cf；新场须重新绑定PID/episode，不沿用历史进程。

R180从2635到2645已有实际5个exact自然日的正常Move与保存链，本次替代直接加载抵达后的普通save，所需新Move为 **0**。在该同actor准备场景：

1. `ck3_take_snapshot`取新暂停F；确认Robert身份、Army18真实FullID、实际位置2645、ordinary陆军及无combat/retreat/gathering。不能强搬旧revision，snapshot缺失布尔不补false。
2. 同新revision取 `ck3_query_army_strengths(army_ids=[18], profile="observed_history_full_v1", expected_revision=F.revision)`，并取 `ck3_query_army_commander_candidates_v1(army_id=18, expected_revision=F.revision)`。Root已有同F完整query可复用，不额外导出全history。核完整DATA/21团物理槽、真实eligible人数、当前stock/cap/rate、effective fraction及loaded表、grace/all30原pointer桶、各journal可用/安装/epoch/read_complete和latest fence。
3. 只从**新场实际** `available && final_eligibility_observable && can_assign` 且exact4 conditional-cap leaf正常化通过的候选中选容量较低的一名。R189历史10名为 `32236,34975,37244,37702,35899,34232,36445,33946,45458,45464`；它们是fresh查询线索，不能直接当下场ID白名单。至多一次 `ck3_assign_army_commander_v1(army_id=18, commander_character_id=<fresh候选>, expected_revision=<fresh F>)`，由Root决定执行。
4. 换将后立即fresh snapshot并同Army重新读stock/cap/rate、current commander、Province loss operands/M、loaded supply表、合格兵数、admission及fences。**换将ACK或candidate capacity100不等于stock已变成100。** 若当前rate≥0、有效fraction为0、合格兵不足、桶/parent捕获缺失，则停止这个准备lane；不启动一次无望30日等待。若真的有更负rate，再用现有 `successful_supply_occurrences_to_zero_12004`重算；最多两次目标preview只用于Root另有fresh合法路径时选site，本方案无需preview/Move。
5. 准备期按真实成功callback数记录stock耗损，遇rate/cap/roster/身份变化立即重算，不能为保留预测忽略补给恢复。达到**自然stock<10**时正常保存新的checkpoint，才开启短R05镜头窗口。若库存已低到下一次真实负rate可归零，保存前低库存、同callback before/after零值、writer当场stock0及complete unique physical debit>0；复用现有parent join与实际loss classifier，不用Army总数净变代替扣兵。

公共入口实际签名见 `mcp_server.py:2658/3017/3030/3042`；条件容量严格消费见 `army_commander_conditional_capacity.py`；调度与零值选择见 `army_zero_stock_clock_12004.py`。本页不新增hook、平台或SDK请求协议。

## 耗时条件：这是准备路线，不是短期正例保证

复用当前生产算术函数，以R181实际 S=30000000 / C=30000000 / r=−175438 为输入：

| 条件保持不变 | 第一次成功后的stock | 首次严格stock<10 | 首次stock0 |
| --- | --- | --- | --- |
| 实测300容量和rate保持 | 298.24562 | 第166次成功updater | 第172次成功updater |
| **反事实**：换将后实际容量100，rate仍为−175438 | 100 | 第53次成功updater | 第59次成功updater |

第二行先按 `min(cap,max(0,stock+rate))` 经一次成功更新钳到100；没有“换将马上减200库存”的假想动作。两行均是**成功原pointer occurrence数，不是天数**；admission、桶重复/变化、正rate、补员/战争和事件均会改变实际进度。当前未取得更快negative target的fresh preview，不把source min/max或旧2602条件值授为新场实际。这个成本明确排除了“从300盲等30天就是饥饿实验”。

因此下一场优先级为：有真实保存的自然低库存输入就用它；目前没有，则用R180已在负rate位置的同Robert普通save做一次fresh低cap准备。若Root不安排长期正常战役耗补给，本轮应转其它仍可获得的实机任务；R05等自然战局出现合格低stock再采，不能以换actor、强改save或把source算例当自然库存跳过成本。

## 审查和存储边界

新实际验证只有一次对R189具名小原件运行现有production normalizer（PASS）及现有零值算术函数，旧fixture未重跑。本包原始检索metadata曾临时输出237672B，超过本lane96KiB文件预算；发现后对**该具名派生文件**压缩并逐字节校验zip副本后移除原派生，事实记录在 `MATCHES.actual.json`，没有碰其它lane或主树。最终包按≤96KiB封存，48小时复核派生检索材料、30天复核新小原件摘要，canonical知识不因派生到期而丢来源pin。

研究总信用仍 **6/14**、业务 **4/11**、qualified dynamic **0/11**；没有新增R05闭合、人工完整观看或影片信用。
