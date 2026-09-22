# CASE-R：Robert 同暂停帧的两目标原生战争估值

记录日期：2026-09-23（Asia/Shanghai）。**本次已取得真实原生读回：玩家 Robert 的当前合法宣战候选，以及两个目标的原生战略军力评估。** 这是一段 production query 的实机结果，不是自然 AI 宣战，也没有执行宣战或发生战斗。对应的[冻结操作单与观测计划](war-film-robert-mcp-shot-runbook-2026-09-23.md)保持原样；本文记录其实际结果和偏差。

## 运行与同帧身份

实机编号为 `desktop-3fevhd2-1c74096080--vanilla--R0004`。所有外置相对路径均以 `D:/workspace/ck3_war_film_research_20260923/` 为根：

| 项目 | 本次读回 |
| --- | --- |
| 游戏 | CK3 `1.19.0.6`，EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| 加载 profile | `capture-live-live-r4c/profile-source.json`，`enabled_mods=[]`，使用独立 userdir 与正式 native bridge |
| 玩家 | Robert，`actor_character_id=29829`，与真实前端开局及 snapshot 读回一致 |
| 游戏进程与连接 | bridge PID `31108`，`connection_generation=1` |
| 观测 snapshot | `snapshot_id=native:5`，**public revision=6**，`native_revision=5` |
| 日期与 episode | `date_raw=53144328`，`episode_run_id=native-29829-21f647c6639a` |
| 地图状态 | `paused=true`，`map_ready=true` |
| 查询前存档 | `robert-input-case-r1/day-zero.ck3`，50,502,569 bytes，SHA-256 `a450f37ff62ea0375b9ae2f6549aa5a14baa9940fc57fa6f97f912f1c76447f8` |

存档在观测窗口前物化，随后重新读取 S0；上述绑定见 `004-post-save-snapshot.json`、`009/010` 查询回包及 `011-case-end-snapshot.json`。`009/010` 的 `snapshot_revision=5` 是 native revision，MCP 请求使用的 `expected_revision=6` 是 public revision，不能互换。

## 实际调用与候选恢复

`ck3_query_declarable_wars(expected_revision=6)` 的第一次调用在 Python 层超时，原 `006-declarable.json` RED 保留。协调者后来在同一 driver 中发现原请求 `step-199-52e31f1268cd` 已有成功回包；核对原绑定后一次性恢复公开缓存，**没有重复提交 native 候选查询**。`008-after-reconcile.json` 通过官方 MCP snapshot 读回 `query_sequence=1`、9 条声明行、7 个不同原始目标。

恢复证据为 `robert-input-case-r1-readback/late-declaration-cache-readonly-r1.json` 与 `late-declaration-reconcile-r1.json`，对应 dispatch 也已保留。详见[超时与迟到结果说明](war-film-declaration-query-late-result-2026-09-23.md)。这次是临时同 driver 恢复；之后新增的正式 collection 工具不在本次 live 结果中。

随后只发起两次单目标请求，均返回 `status=available`，readiness 各项及 `ready=true`：

| 回包 | 实际 MCP 请求 | query_sequence | 回执 UTC 时刻 |
| --- | --- | --- | --- |
| `009-assessment-one.json` | `ck3_query_war_entry_assessments(target_character_ids=[31899], expected_revision=6)` | 1 | `2026-09-22T21:18:52.459090Z` |
| `010-assessment-two.json` | `ck3_query_war_entry_assessments(target_character_ids=[31549], expected_revision=6)` | 2 | `2026-09-22T21:18:53.085003Z` |
| `011-case-end-snapshot.json` | `ck3_take_snapshot` | 候选缓存 1；最新 assessment 2 | `2026-09-22T21:19:10.016950Z` |

请求的目标都来自本帧 `declarable_war`，并非任意手填 NPC。两次 assessment 绑定同一暂停 snapshot，末次 snapshot 仍为上述日期、角色、revision 与 episode。末次公开 assessment 缓存只保留第二次结果；第一次以独立 `009` 回包保全，不能宣称一个 snapshot 同时发布了两条 assessment。

## 两个目标的实际数值

`power`、`distance` 和 `ratio` 的协议 scale 都是 **100000**。下表“换算值”仅为原始整数除以 100000，军力不是士兵人数，ratio 不是概率。ratio 直接使用原生 `actual_power_ratio_raw`；不以浮点重算取代原生值。数值含义与来源边界见[宣战专题的 production 单目标合同](war-declaration.md#query-war-entry-assessments-v1-production-单目标只读契约)。

| 字段 | 案例 A raw | A 换算值 | 案例 B raw | B 换算值 |
| --- | ---: | ---: | ---: | ---: |
| `distance_raw` | 62200000 | 622 | 0 | 0 |
| `actor_power_base_raw` | 3786000000 | 37860 | 3786000000 | 37860 |
| `actor_network_contribution_raw` | 0 | 0 | 0 | 0 |
| `actor_power_total_raw` | 3786000000 | 37860 | 3786000000 | 37860 |
| `target_power_base_raw` | 10718000000 | 107180 | 1334000000 | 13340 |
| `target_network_contribution_raw` | 0 | 0 | 0 | 0 |
| `target_pre_adjustment_total_raw` | 10718000000 | 107180 | 1334000000 | 13340 |
| `target_adjustment_delta_raw` | 0 | 0 | 0 | 0 |
| `target_power_total_raw` | 10718000000 | 107180 | 1334000000 | 13340 |
| `actual_power_ratio_raw` | 283095 | **2.83095** | 35235 | **0.35235** |

身份、AI entry 和 flags 是离散整数，不按 Q100000 缩放：

| 字段 | 案例 A | 案例 B |
| --- | ---: | ---: |
| `target_character_id` | **31899** | **31549** |
| `effective_target_character_id` | **37169** | **31549** |
| `target_ai_context_actor_entry_raw` | 0 | 0 |
| `actor_ai_context_target_entry_raw` | 0 | 0 |
| `native_flags_raw` | 29 | 157 |

这里能直接展示三个事实：

1. **声明对象与有效防守方可以不同。** 本次 `31899 → 37169`，而 `31549 → 31549`。本文不凭 ID 猜人物名称，也不凭重定向单独推断全部政治关系。
2. **同一个 actor 的军力总值保持 37860，目标评估明显不同。** 原生 ratio 的方向是 `target final / actor total`；A 返回 2.83095，B 返回 0.35235。它们表示本评估器中的战略军力比较，不表示 283.095% 或 35.235% 的胜率。
3. **本次网络增量和目标调整增量均为零。** 这证明的是这两个查询的输出，不证明人物没有盟友、任何盟友都不参战，或所有战争都无关系网络作用。`distance=0` 也不能单独解释为地理重合、接壤或零行军时间。

provenance 同时返回 `assessment_rva=0x1878A00`、`network_collector_rva=0x1879850`、`fixed_point_scale=100000`。兼容字段 `power_leaf=CCharacter+0x1B8->+0x308` 不能被扩大为“两侧 base 都直接读取此叶”；现行合同中 actor base 来自权威 State16 builder，target/network decomposition 才对应该叶。本次不重新定义既有 ABI。

## 录像、时间关系与本轮结束

独立 HUD 后录像是 `robert-input-case-r1/gameplay.mkv`：2560×1440、H.264、时长 120 秒、288,043,189 bytes，SHA-256 `131ae9958a81a5a4d8c3b883f3ff6cfa1a2cc7e0e1242c48bcbcb8ae4820b6d0`。`recording-precondition.json` 记录 owner 已观察到实际 HUD，`recording-result.json` 记录录制/探测退出码 0、全程前台窗口为 CK3，clean-span 审阅仍 pending。

录像完成回执为 `2026-09-22T21:10:51.952544Z`，早于 `009/010` 的约 21:18:52Z 查询。它们绑定的是**同一未推进的暂停游戏帧**，不是录像帧与查询的同步采集。可以将地图作为同现场背景，并明示数值为随后查询的读回；不能剪成“这段录像同步捕获 AI 正在选择目标”，也不能据此标记 `frame_synchronous_query_proven=true`。

逐帧时间审计 `robert-case-r-frame-timing-r1/frame-timestamps.json` 发现：

- 媒体头的 `r_frame_rate` 和 `avg_frame_rate` 虽均为 `30/1`，实际只有 **1077 个解码帧**，不是 120 秒 CFR30 所需的 3600 帧。
- 实际首末 PTS 为 0 / 119.967 秒，平均帧间隔约 0.11149 秒，间隔从约 0.033 到 0.200 秒；按 1077/120 计算约 **8.975 fps**，属于当前审计所见的 VFR 时间线。
- 因此旧 raw **不能按当前连续零起点 CFR30 合同直接导入**。它必须永久保留；如后续制作需转换，应另产派生文件、保留来源与时间映射，再独立验证。当前没有因此取得 clean-span、人工 1× 审阅或 signoff。

启动至结束的 debug 录像另为 `capture-live-live-r4c/raw-desktop.mkv`，5,063,562,376 bytes，SHA-256 `D5521691ACD9B8C05DF36BB9A0C0BFD461F239405D58AFCFAD0F001DF3F378B3`。它与 HUD 后录像分开保全，不能把启动全程自动标成可用净片段。

`interactive-requests-responses/service-ended.json` 记录服务于 **`2026-09-22T21:33:03.184276Z` 按预算正常结束**（北京时间 2026-09-23 05:33:03）。随后 `session-result.json` 为 `ok=true`、`exit_reason=stop`、`restart_count=0`，受管清理 `tree_gone=true`、`cleanup_proven=true`、最终 CK3 进程清单为空；这是预算收尾，不是游戏自然退出或宣战查询再次失败。`capture-report.json` 完成时间为 21:33:06.830646Z，状态仍是 `RAW_CAPTURE_COMPLETE_PENDING_VISUAL_REVIEW`。

## 可核验材料与结论范围

汇总入口为 `robert-input-case-r1-readback/result.json`（`READBACK_CONFIRMED`）。它记录所有读回副本的精确 bytes/SHA，保留超时及恢复链。关键原始回包：

| 文件（位于 `robert-input-case-r1-readback/`） | bytes | SHA-256 |
| --- | ---: | --- |
| `009-assessment-one.json` | 13353 | `7ba46fc01e705f45a64e9479b0575ded6d3c8419cda4e065e08b2e78aa711a6e` |
| `010-assessment-two.json` | 13343 | `a89e114d3c7220b4e6aa6351e9c6826ca719da73b25891d2538c5b7b93de6e21` |
| `011-case-end-snapshot.json` | 80277 | `08a798d1648125e5cc3e740e8e8897ee83fc5b1545a4868b11fe1042c6d97825` |

本案例支持影片 W1 的一个具体读回展示：玩家当前合法对象、原始目标到有效防守方的解析，以及原生战略军力比较。它**没有**观测 NPC 自然宣战、全候选评分和 `.9max/top5/加权随机` 选择，也没有展示军队行动、求援、撤退或和平因果链。9 条合法行不是 AI 自然选择的候选池证据；两条 assessment 不是全池排序，也不是 strongest/weakest 结论。真实读取已有了，完整战争影片与逐机制因果案例仍未完成。
