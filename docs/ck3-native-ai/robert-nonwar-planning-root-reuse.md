# Robert 普通回合：同帧 root 观测复用

2026-10-02。当前 exact build 为 CK3 Steam 1.20.0.3，EXE SHA-256 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。本专题只减少普通 nonwar 规划的重复读取，时间策略、战争字段、原生动作与提交后验证保持现有语义。

## 必要性与实证

`artifacts/g2-maintainer-2026-10-02/resume-12003/m7-robert/finite-normal-7day-actual-01` 的三轮正式运行，每轮第 2、6、7 个只读查询均为 `query-campaign-root-context-v1`。每组三份完整 `campaign_root_context` 相等，包含 council、held-title partition、readiness 与 provenance；仅外层请求 token 和递增 query sequence 不同。

| 回合 | public revision | native revision | date_raw | actor | root query_sequence |
| --- | --- | --- | --- | --- | --- |
| 1 | 2 | 16 | 53220096 | 29829 | 12 / 13 / 14 |
| 2 | 5 | 19 | 53220120 | 29829 | 15 / 16 / 17 |
| 3 | 9 | 23 | 53220240 | 29829 | 18 / 19 / 20 |

真实批次 Python 源为 `production-source-c0f53e9b`；当前生产接线分析基线为 `production-source-716acfec`，两者不得混称。完整 raw 请求/回包及逐组相等证明见外置 `m7-robert/nonwar-query-cost-01/wire-repeat-proof.json`，调用链见同目录 `source-chain-readout.md`。实际 planning 合计 80.471090 秒、dispatch/verification 5.099678 秒、外部 JSON 0.075965 秒；没有逐查询计时，不能据此宣称具体节省秒数。

## 已有决策与读取树

```mermaid
flowchart TD
  A[paused ordinary nonwar planner] --> B[succession preparation: fresh root query]
  B --> C[successful full result recorded in native command history]
  C --> D[choose existing ordinary action and time horizon]
  D --> E[government and council final gates: fresh domain queries]
  E --> F[council holder observation: root result]
  F --> G[current primary heir relationship: fresh native query]
  G --> H[existing fixed-pair value: adult hold or typed action]
  H --> I[formal submit and postcondition verification]
  I --> J[next turn: fresh succession/root observation]
  C -. same paused public/native frame .-> F
  C -. same paused public/native frame .-> G
  C -. static-ready: same-frame incumbent .-> K[consume applied Chancellor persistence]
  K -. next natural live validation pending .-> F
  H -. future unobserved business outcomes: unknown .-> U[actual later reply / event]
```

第一份真实 root 读取保留：原生查询同时刷新当前 primary-heir 观测。仅将该完整 result 显式传给本轮 council planning 与 current-first-heir relationship 的绑定部分；relationship 和 council final-gate 查询继续真实读取。完整 result 来自规划已有的成功 history，保留首个原始 query_sequence，不使用缺少 query_sequence 的 driver 缓存重建结果。

若 snapshot_id、public/native revision、日期或 actor 变化，消费者走原有 fresh root 调用。可选参数只在 `plan_nonwar_turn` 本次调用内传递，不落盘，不建立全局缓存。实际 council receipt reader、直接公开/私有 relationship 查询、family fresh-frame retry 与下一回合仍走 fresh 读取。计划的普通 1/7/30-day 策略不变。

## 交付状态

最小接线首先达到 **static-ready**。五个生产 Python 文件仅新增规划范围的可选 `campaign_root_result` 参数与同帧完整 result 选择；`service.plan_nonwar_turn` 从已有成功 history 取出完整结果，议会与继承人消费者显式接收，帧不相符时沿用原调用。

一次 focused 测试文件 `ck3_autonomous_player/tests/unit/test_nonwar_planning_root_reuse.py` **5 passed in 1.06s**：真实 service → council → family consumer → NativeDriver wrapper → relationship transport 函数链将根读取 **3 → 1**；council final gates 与 relationship 仍各查询一次。完整计划相等，仅 relationship 的原始 root provenance sequence 从第三份 `103` 变为首份 `101`。succession retained bundle、议会持任/任务、14/14 的非成人 hold、已观测负 gold cost 材料均保持。另覆盖 revision/date 变化后的 fresh fallback、默认直接查询 fresh，以及实际赋职 receipt 的独立 root 读取。

测试读取使用既有 1.20.0.2 council DTO 与 current-pair negative fixture，并在离线环境构造 frame/endpoint；上述是真实 Python 生产函数接线验证，不是新 1.20.0.3 游戏回包或性能测量。首次调用因独立 harness 未设置 `PYTHONPATH=src` 而在收集阶段 RED，未运行测试体；该 receipt/output 保留为 `FOCUSED-TEST-RECEIPT-attempt01.json` / `focused-test-output-attempt01.txt`，补标准环境后同文件 GREEN，未跑旧 suite 或 L0。

原始重复证明支持三回合 root 读取总数从 9 降至 3、全部规划查询从 24 降至 18；这是待实机确认的计数预期。新 runtime 必须由协调者提交/推送、冻结 Python 源并重启 MCP 后，在下一轮正式普通回合核验实际请求数与 planning timer。native 无改动，无需重编。

该静态工作包本身不增加游戏天数、G2 credit 或可玩能力 readiness。完整 history、真实状态、提交/回退与 goal 路径均未改动。

## 公开 412 的单回合实机验证

`m7-robert/planning-reuse-412-actual-01` 已 **CLOSED GREEN**。运行 Python 为公开 `41291bf2315f11b6748affce318e1e456a6f8918`，执行前 native prepared/binary 的源版本标记仍为 `716acfecc6c487e2b48942c6a6030c8b7012e5d5`（该 raw plan 未提供 DLL 哈希）；运行使用新 state v19。冻结 execution plan 中的 `live_executed=false` 是执行前元数据，真实资格来自本次 CLOSED raw 请求、回包与正式结果，不回写那份执行前 plan。

本批次 target 7 天在 **一个正式回合**就达到，实际 date_raw `53220456 → 53220624`（7 天），执行后 native revision 8，最终 paused，无 modal 或新 Sway start。只观察一个回合，不声称完成了新的三回合样本。罗贝尔累计耐久天数为 3179，本次迭代累计 26 新日；这 7 天属于协调者实际运行，文件分析自身不加天数或 G2 credit。

| 实际 planning 请求 | 旧同类回合 | 公开 412 回合 |
| --- | ---: | ---: |
| campaign root | 3 | 1 |
| Sway target | 1 | 1 |
| government adapter | 1 | 1 |
| council final gates | 1 | 1 |
| council status | 1 | 1 |
| current first-heir relationship | 1 | 1 |
| 合计 | 8 | 6 |

唯一 root 是第 2 个 planning 请求：expected/returned native revision 5、public revision 2、date_raw 53220456、actor 29829、原始 query_sequence **2**。government 的 revision/date/actor、council source frame、family 的 `root_query_sequence=2` / native revision 5 / primary heir 38822，以及 proposal frame 均与首份观测绑定。另五类业务观测仍真实读取，没有减少为缓存数据。

正式 plan 消费的材料保持完整：goal 仍为 `dynasty_continuity`，政府为 feudal，44 个 core-supported features 与 readiness 为 true；Steward 43706、skill 14，14 个 native candidates 中 11 个合法，`NO_CHANGE`、Collect Taxes 持任与 following consumption 保留。38822 ↔ 38718 双向关系已验证，双方成年量度仍为 14、阈值 16，实际选择 held，再按既有 7-day horizon、speed 5 执行 `life-advance`。本回合没有业务动作的新 receipt，因此动作后独立 fresh 分支仍以已通过的 focused 测试为证，不扩大该分支的实机覆盖。

实测本回合 planning **20.101028 秒**，旧三回合 planning 均值 **26.823697 秒**；前者低 25.0624%，仅作不同日期、进程与样本数下的观测对比，不能归因为受控的单项提速。新 dispatch/verification 为 **1.317485 秒**，整批外部 JSON 为 **0.019963 秒**。root 请求 **3 → 1** 和总请求 **8 → 6** 是本次原始包直接证明的生产收益。1/7/30 策略未改，30-day 仍未由本批次观测。

有限 external capture 为 turn 184706 B 加两份 snapshot 49169 B，共 **233875 B**；history 在这些外部 snapshot 继续明确 omitted，而保存的 checkpoint history index 与完整 driver history 都是 **4081**。完整 save/driver bytes 与 SHA 由协调者关闭时计算并写入不可变 result，分析者未读取当前 live state。

本范围升级为 **production-live loop：普通规划中复用首份 root 观测**，对应真实“观察 → 决策 → life-advance → 验证/保存”。G2 整局目标与其他能力边界不变。一次 closed-file readout 位于 `m7-robert/planning-reuse-412-live-readout-01/`：`wire-live-proof.json`、`context-timers-proof.json` 与 `capture-history-proof.json`；后续自然新帧继续正常主线，不为额外样本重复实机。

## v24：Chancellor 持任核对复用与规划耗时

`m7-robert/normal30-after-finalread-recovered-82c-v24-actual-01` 的 16 个正式普通回合已 CLOSED。冻结 Python 为 `production-source-82c03174`。正式 service 合计 **438.775308 秒**，其中提交前 planning **419.075478 秒，占 95.5103%**；dispatch/verification 为 19.675587 秒。外置 JSON 写入合计 0.873864 秒，与阶段计时重叠；16 次外部 Sway 预查询未计入 formal service，因此这些数值不是约九分钟进程全程的完整分解，也不能归因于最小化执行或某个 native wait。

每轮 root 已只读一次。Chancellor 与 Steward 的两份 final-gates 查询针对不同职务，status 分别消耗各自 pending 操作。本次可减少的是既有 Chancellor 赋职的持任核对：**16/16** 同帧 root 的 incumbent、applied 人选与 Chancellor terminal 查询的 incumbent 都为 **43696**，日期与 native revision 匹配；消费函数只使用额外查询的 incumbent。单叶补丁删除这组异职务的 final-gates/status 请求，直接使用既有 root holder；Steward 完整候选与合法性 quote、同职务核对及动作后的独立 receipt 验证保留，既有 root 帧绑定和 fresh fallback 原样使用。

新增既有测试文件的一个 focused case，真实 production consumer → driver wrapper → pending/status transport 的离线 wire 请求 **4 → 2**，Steward 完整计划、quote、决策和 Chancellor 消费结果相等，既有 typed 提交行为保持。第一次因独立测试目录缺少 frozen tools import 路径而在收集阶段 **harness RED**，尚未进入用例；receipt 保留，补路径后同一个用例 **1 passed in 3.56s**。最终测试文件只另同步旧 cold-query 计数断言，已通过的 focused case 字节未变，未重跑旧 suite。这是 **static-ready**，端点回包仍为 fixture 输入。按本批次预计每轮读取请求 **9 → 7**（16 轮 144 → 112；planning 请求 128 → 96），尚无节省秒数或实机提速百分比的 claim；等待新冻结 Python attach 后下一轮自然普通游玩确认。日期 1/7/30 策略、native DLL、窗口行为与完整 history 持久化保持现有实现。

完整计时、16/16 比较、两路径 patch/pins、首次 harness RED 与 focused GREEN 索引见 `artifacts/g2-maintainer-2026-10-02/resume-12003/performance-v24-normal16/ROOT-DELIVERY.json`（SHA-256 `7372273681087f2f659ccec1197a4f6271329df66dae7c2979f4f84956349458`）。本分析与静态补丁不另加 Robert 天数、政府资格或 G2 credit。
