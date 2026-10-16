# R10 下一轮：一个新冻结 T0，三次独立 A/B/C 冷载

本页供战争四期视频与智能体开发共同使用，只收敛现有合同和入口，不新增执行器。**R182 的围城 checkpoint 当前只能证明普通战役续行；它可以成为下一轮准备的候选输入，不能直接算新 ABC T0，也不能算 A/B/C 任一正式臂。** R10 新版三臂结果仍为 **0/3**；模板、schema、`--help`、合成测试和来源文档不增加此分子。

离线审阅机器 `machine_id: desktop-3fevhd2-1c74096080`；观察时间 `2026-10-16T10:03:00Z`（本轮文件审阅时点）；Git 阅读基线 `20c7319b6964c80fa419540cf4e30852feff4810`。本轮稳定 ID 由 `tools/ck3_live_run_id.py machine` 实际读回；本页不重授游戏版本、Steam 离线、进程、权限或容量资格。现场事实引用各自原机器和原时间，不以本次读文档的时间刷新。

## R182 能保留什么，怎样才能成为新起点

[R182 原始归纳](episode04-r182-march-and-county-p-12004.md)记录同机 PID14392/gen1/episode `native-31254-8e3d88fb82cc`，从 R181 正常 checkpoint 接续；结束日期 raw53147928、actor31254、Army18 在2635、`sieging`、完整空路线。正常保存为73,446,058 bytes，SHA-256 `af291da7e2af3b8b0870dc3aa21291b55452a78e08a241994ba6358411c7c96b`。这些不是本轮重读大存档所得；实际可用性、当前保存、位置和主体仍由下一场重新读回。后续 [R183](episode04-r183-window-capture-12004.md)也是这条普通谱系的续行，没有为 ABC 冻结新的 T0。

R182 未绑定同一暂停帧的 agreed commander、全部 DATA、钱包、实际战争目标和三条合法策略；原片未授 clean，县边 P 为 false，军队端点净兵数相同也未授实际扣兵。不能把这些缺项从其他场的数字拼入。2635 已是该保存点的当前位置，不能为了得到零日抵达，把它直接当作新的比较目的地。

最短准备是正常加载保留输入，取得一个新的、无待处理弹窗的暂停帧 F，审阅真实对立战争目标、驻地、统帅和路径。`sieging` 本身并不被 ready-T0 消费者禁止；但三臂必须冻结相同起始围城/敌情，且目的地与策略必须有实际可回答的问题。若缺少两处可用休整点或合法替代路径，先做有界 pilot，再统一冻结新的普通 S0；不要只在 B/C 开始前改起点。

准备场可以续行。**正式三臂必须在计划冻结后，分别正常冷载同一 S0 SHA，从 day0 重新取本臂 T0 读数。** 准备场保存后直接跑 A，只能算准备续行，不能冒充第一条独立冷载。重启脚本、换 attempt、同进程 reload 或沿用旧 reader 身份均不能替代三次独立正常冷载。

## 最小冻结字段：已有消费者逐项取，缺什么补什么

权威意图仍是[导演案](../../promo/ck3_native_war_ai/episode-04-march-logistics/director-plan.md)、[同起点比较合同](episode04-comparison-contract-12004.md)与现有 [PLAN 模板](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/PLAN.template.UNBOUND.json)。下表是它们的准备顺序，不是第二套 schema。

| 冻结对象 | 最小实际字段与来源 | 拒收边界 |
| --- | --- | --- |
| 版本与实现 | `build.version=1.20.0.4`、Steam build25734779、实际 EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`、批准的 `source_head/native_dll_sha256`；实际构建、部署和运行来源 | 旧 DLL/另一机器版本记录不能代替本次运行绑定；三臂不得中途换 source/DLL |
| 普通保存 S0 | `normal_save.kind/bytes/sha256/save_receipt/normal_origin_proof`，每个小证据 pin 为精确 `path/bytes/sha256`；正常 native 保存回执 | 不编辑 opaque 存档、不用 fixture Start、不覆盖旧恢复点；只引用哈希而文件不可读时不是可加载输入 |
| 一个暂停 F | `t0_raw`、living actor、war/player side、public/native revision、snapshot ID、native epoch；当前 Army owner/control、public CUnit 与 signed native CArmy 映射、位置、状态、完整空 route | `map_ready=false`、moving/embarked/gathering、combat/retreat、pending event/interaction、未知控制权或不完整 route 不授 T0 |
| 完整军队 | `original_regiment_ids`、完整 scale1 ArRg current/max 和求和、所有 DATA/record/backlink、各军 stock/cap raw 与 scale100000、同帧 typed current commander、实际 loaded features | compact MCP summary、partial/unavailable/shadow、缺 DATA/缺团、把 absent commander 写0均拒收；Character 空 DATA 1/1按既有角色规则另列 |
| 战争与现金 | fresh 完整 occupation collection、实际对立目标 `goal_province_id`、当前钱包 raw/scale、战争集合；军事目标选择的理由 | 相机中心、旧伦敦目标、另一场 actor ID、当前月率不能代替实际目标、钱包或实付 |
| 策略与时限 | 下面三策略；`arrival_states/report_days/event_policy/wall_budget_seconds_per_arm`；90自然日、每自然日 raw24；`follow_after_arrival_to_day90/post_arrival_policy`；`compare_fees`及先决资格 pins | 不在看完结果后改休整阈值、将领、路线、费用列或到达后政策；wall budget须按 pilot 实测，不把270日估为固定几分钟 |

直接复用 [ready-T0 组合器](../../ck3_autonomous_player/src/xar_autoplayer/bridge/episode04_ready_t0_12004.py) 的 `ready_t0_readonly_requests_12004` 与 `evaluate_episode04_ready_t0_12004`：已有 snapshot F→full strengths（`observed_history_full_v1`、两个 `observed_prepared`）→typed commander→private cash→canonical war occupation→末尾独立 snapshot。函数只生成/检查输入；Root才执行真实查询。各结果按 queried snapshot/revision/native revision绑定 F；旧 cash wire缺 epoch 时依靠 Root 真实生命周期回执，不伪造字段。

`military_t0_frame_ready=true`仍不是整卡完成。Root还须明确采用当前统帅、目的地及周边陆/海/休整点与真实 previews，并正常保存一次，绑定同日/actor/episode与 `ordinary_campaign_succession/xar_off`。`normal_t0_saved`只核实际回执；保存是否已完成与精确原件可读性需材料回执证明。读数换帧则重取相关只读输入；未知保存结果只读原响应，不重提交保存。

## A/B/C 必须在正式前固定的行为

| 臂 | 事前冻结 | 逐阶段实际后验 |
| --- | --- | --- |
| A `whole-direct` | 同整军直达共同目标的真实完整 preview；整军与统帅政策 | 一次 Move后独立同日更新帧确认 target/完整route；逐日实际到场，不用 ACK/ETA授抵达 |
| B `split-rest-merge` | R09微实验来源；两处已有实际 stock增长证据的驻点；`minimum_stock_raw/maximum_deficit/maximum_rest_days`；会合省份、merge destination方向、commander policy | split后完整队列守恒与真实 child；各军实际驻定才起算休整。stock和缺额同时达标，或到最长驻留即退出。未恢复也是结果。会合后 fresh packet→一次 merge→独立 survivor/消失child/真实统帅/DATA/库存cap；再去共同目标 |
| C `whole-via` | 有序 `waypoint_province_ids`、第一段 fresh合法preview；同整军、共同目标与停止政策 | 每到一个真实中转点结束本批，Root审阅下一段当前合法preview再一次 Move；记录中转点真实日期，不用远终点或预览first edge冒充到站 |

现有 [R09 selected93](episode04-r09-selected93-micro-actual-12004.md)只授一方向的物理 DATA/角色/统帅后验，R09全卡仍缺反向 merge、stock/cap/weights和动态镜头。不能因代码可导入就写 `B_microexperiment qualified`。Army18若被选作正式军队，选中93的来源只按其真实适用范围复用；未证明的主体效果不能直接迁移。

“同起点”不要求未来世界每帧相同：保留普通事件、敌军行为和随机分歧；它们是各策略的真实后果。共同 S0 的相同 bytes/SHA是输入冻结，不等于已证明 PRNG 全程逐帧复现。不改 seed、不筛掉不利事件、不在结果差时重开取最好一次。陌生事件按当前 AGENTS先采原生 ID/实际选项，选第一显示项后继续；交互通知按原生左侧语义，保存 ACK和原窗口消失后验，批后离线补知识。

## 三次 live 身份与三份 reader 输入互不接续

每臂独立分配 `run_id/case_id/attempt`，保存 `ARM.runtime` 的 `machine_id/started_at_utc/pid/process_create_time_100ns/connection_generation/episode/player_character_id/source_head/native_dll_sha256/source_proof`。`started_at_utc`必须晚于计划冻结；`loaded_save_sha256`三者相同。PID可能被系统复用，比较器以 machine+PID+create-time+episode区分，不能只看PID；gen1可在三次冷载各自出现，不代表同一 journal。

ready-T0 `source_binding`中的对应创建时间键实际为 `process_creation_filetime_100ns`；ARM模板键为 `process_create_time_100ns`。按各自已有合同写真实值，不混用拼写或改造native wire。历史actor31254与Army18只作候选，必须逐臂读回，不由历史人物1128推算。

每臂 `cold_start`以自己的 snapshot、response-local完整 Driver引用、typed commander/features source pin重新读回；观测投影必须与冻结 baseline完全一致（actor/war、队列/DATA、各军位置route、stock/cap、钱包、统帅、loaded features）。旧 F的 episode/revision不能搬成新 cold F。不同进程的 observer epoch/sequence不得相减或拼接；每臂独立 admission、起始 fence、retained完整性和终点。

只读消费者使用本臂小证据根与显式 pins。公共证据可单份引用，原件不复制三遍；不得让 A 的“latest”、cache或source pin静默落到B/C。重复使用只限相同、完整、身份与frame/fence已证明相等的输入。日期或revision数字恰好相同不足以跨stage免新读。[当前 runtime预算](episode04-r10-runtime-total-budget-12004.md)已经指出完整 fence vector尚未发布。

三臂 live 仍由 Root独占 CK3/SDK/桌面串行执行；并发用于源码研究、独立证据读取、叙事和审计。离线worker不得同时操作同一场或并行提交stage。

## 停止线与可输出的差分

每臂共同绝对截止 `D_end=T0+90×24`；每天用已有 exact sentinel保存 date-only `terminal-a-0`、speed5、一次tick、target=start+24、overshoot0、真实generation/暂停来源和独立暂停snapshot。batch或脚本重启不重置90日。unknown Move/Arm/Resume保留once claim，只读原请求/原响应/新后态；禁止删除claim后重发。A/B/C当前阶段代码分别负责自己的恢复入口，不能拿另一臂的状态续跑。

| 结果层 | 合格输出 | 停止/降格线 |
| --- | --- | --- |
| 抵达与耗时 | current=共同目标、冻结允许状态、完整空route、target=null；`(最后未到,首次已到]`宽≤1日，日快照扫描确认首次 | 第38日主动停是STOP，不是D90截尾。只有实际90日仍未到才budget-censored。死亡、战争终止、接敌等分别记录竞争终点/世界事件；身份失配、越步、缺日或丢日志为measurement，不伪造完整比较 |
| 人数与损耗 | 原始cohort current/max、全部strategyArmy current/max分列；physical debit、physical ADD分别由完整自然应用链授资格 | 净兵差只叫net cohort change；补员、角色1/1、分合军和战斗不能混称损耗。缺团/unknown/shadow不补0，原队列无法绑定时停止完整比较；源derived预算或loss fraction不等于实际扣兵 |
| 补给 | 各军各自实际stock/cap、scale与日期；B实际退出原因 | 不把分军库存相加/平均成整军库存；getter正值不等于恢复发生；最长驻留未恢复不能重启策略 |
| 费用 | 独立合格boarding、maintenance应用账，other income/expense与钱包对账；`Δwallet=income−otherExpense−boarding−maintenance` | `compare_fees=true`而R07/R08资格或应用账不齐，计划/费用比较hold。unknown保持null；空records不是零费用，当前月率/NET不是实付。完整expenses已含军费时不再扣一次 |
| 横向结果/评分 | 各臂到场表呈真实不同观察日；共同日期表只用三臂均有的预注册同日读数；条件性权衡 | 不以A第X日和C第Y日当同日效果，不从到场总费用推纯费率。现有工具 `winner=None`，不输出通用最优或事后加权分数；若未来引入评分，权重/门槛须先冻结，当前没有该实现或结果 |
| D90 | 事前冻结到场后 `hold-arrival-position-until-day90`并实际继续至90日；保留首次到场不变 | 未采用/未执行到场后政策则D90为null，不能用到场数值代填。A/B/C已有显式common-horizon阶段不等于它们已经跑过 |

费用资格不足不禁止智能体依据当前状态做合法行军；但不能偷改 `compare_fees`以把缺失的正式比较说成完成。可输出 observations-only及具体unknown，正式结果范围另经事前决定。物理总账不合格时，现有比较器会保留观察事实并拒授 `controlled_comparison_records_eligible`，不是把缺证据默认为0。

## 显式新场绑定候选（本轮源码整改）

[共用pure guard与小JSON loader](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/runtime_binding.py)新增 `xar.e04.live-operation-binding.v1`。R09、A和B入口新增 `--live-binding PATH --live-binding-sha256 SHA`，两者必须同时提供；C bundle使用精确 `live_binding:{path,bytes,sha256}` pin。无新binding保留历史有限合同，过期不能启动新live。旧存档、配置、原证据和pure策略消费者均不改写。

manifest必填：`operation_id/created_at_utc/machine_id/run_id/run_sequence/source_head/scene_root/deadline_utc`、`runtime:{pid,process_create_time_100ns,generation,actor,episode}`、`normal_save_sha256/max_runtime_total_bytes`、`capacity_admission:{path,bytes,sha256}`、`guard_sha256`。不提供默认机名、旧run或新期限。创建时间不能在未来；当前必须严格早于deadline，窗口最长7日。Root执行入口另外实际调用稳定机器ID工具；机器不匹配拒绝。

capacity必须是Root实际adopted的有界JSON，`admitted=true`、`policy_version=1.0.0`、`root_atomic_adoption_required=false`、`root_adopted_at_utc`；同machine/source/run/scene，`source_binding.new_clean_integrated_source_head`相同，review时刻严格等于manifest deadline，driver ceiling覆盖显式runtime总量且aggregate覆盖driver。pure guard兼容`new_scene_aggregate_bytes`或`aggregate_scene_ceiling_bytes`，同现必须相等；现有RuntimeTotal meter仍使用前者规范字段，未来Root准入应输出该规范字段，不能据别名通过pure gate就称所有meter已可消费。

每次请求前重新检查binding/capacity精确bytes/SHA和期限，仍独立核PID/create-time；同case不能更换operation pin或把旧case领成新场。R09新场meter同时计请求/响应、case及完整native-session sidecars，并预留下一response与该次完整Driver结果；A/B继续复用既有RuntimeTotal meter。实际共享卷空间与原子预留由Root做，guard不制造新的容量授权。

**截至2026-10-16 10:45Z的历史C新binding仅提供离线准备，provider返回`NO_GO_LEGACY_LOCKED_CONSTRUCTOR`并拒绝live。** 所选历史locked constructor仍含literal旧机器/资产限制，本轮未通过AST、`__new__`或动态重写绕过它；下一轮须正常参数化并验收该constructor才能启用。其余新guard/入口测试只用synthetic JSON、fake metadata/transport，没有新游戏日、SDK或录像；不能算ABC 3/3。A原本已有独立constructor覆写，此次只在该既有入口加资格检查，没有改冻结base源码。

2026-10-16T10:45:49Z，同机离线回归：新guard/入口边界12项、A stages5项、B stages9项、B CLI→真实Root admission的synthetic绑定5项、C既有显式绑定6项、R09合同7项，共**44项通过**；`git diff --check`通过。使用`tools/.venv/Scripts/python.exe -B -X utf8`，未调用SDK、桌面、CK3或构建。B旧full-packet测试补齐实际Evidence、bounded load与显式单军scope；旧期限正向fixture固定在其历史时间，生产旧期限没有被延长。源仍待Root最终审阅/提交/构建，不能据此声称部署或新场通过。

## 复用入口与当前有限期限

本轮在上述机器的 `tools/.venv/Scripts/python.exe -B -X utf8`下实际执行下列四个 `--help`，均exit0，只读导入，没有live参数或请求：

```text
promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/strategy_a_stages.py --help
promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/strategy_b_stages.py --help
promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/strategy_c/phased_relay.py --help
promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/r10_compare.py --help
```

真实stage名：A为`baseline / Move-once / Move-post / advance / post`及显式`advance-common-horizon`；B为`baseline / split-once / post-split / rest / merge-once / post-merge / route`及common-horizon/recovery；C为`prepare / probe-via / admit / move-once / path-after / advance / recover-day / report`及common-horizon/recovery。B普通阶段不推进时间或发Move；交还Root已有route/exact-day通路。大小写和参数以各入口真实help为准，不能虚构统一 `run-abc` 命令。

**这些有限relay不因新增源码就获得新ABC现场资格。** 整改前阅读点中[A入口](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/strategy_a_stages.py)第57–59行、[C入口](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/strategy_c/phased_relay.py)第140/172行绑定`2026-10-16T07:45:01.597Z`；本次审阅已过期。整改后无新binding仍保留这个旧限制；source/run/module参数不自动延长现场授权。有新binding的A/R09/B依照上一节的实际Root有界输入逐项重验；C当前接线修正见下节，旧legacy provider仍拒绝。未来操作必须重新取得当场期限、source和容量资格，不修改旧场或旧approval。pure消费者、字段语义、一次动作和阶段顺序可复用。

准备好真实小证据后，继续使用已有只读核验命令：

```text
<verified-python> -B promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/r10_compare.py check-plan PLAN.frozen.json --evidence-root SMALL_EVIDENCE_ROOT --output CHECK.new.json
<verified-python> -B promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/r10_compare.py compare RESULTS.json --plan PLAN.frozen.json --evidence-root SMALL_EVIDENCE_ROOT --output COMPARE.new.json
```

`r10_compare.py:279/291/336/352/391`分别是paused frame、完整endpoint、plan、逐日clock和三臂比较的现有检查。结果固定 `live_execution_performed=false / research_card_closed=false / human_media_review_performed=false`；`controlled_comparison_records_eligible`只验供应记录一致性，不证明来源真实性、所有策略动作或因果账真实性。影片还需[R10逐句动态映射](../../promo/ck3_native_war_ai/episode-04-march-logistics/review02/r10-claim-result-shot-map.json)的同场raw/时码、合格clean、声音、完整机器审计、实际人审与交付，各自结算。

容量与期限按[统一策略](../storage-retention-policy.md)和[参数1.0.0](../storage-retention-policy.json)在任务开始、重写入前、闭场检查；旧512MiB默认不是本轮容量准入，超过默认需exact Root admission，16/32MiB单文件与总量是两项限制。普通full样本曾约9.66MB，270日不能套一个小场额度；先pilot估算真实请求、完整sidecar、profile/保存和媒体峰值，再协调所有并发预留。当前活跃S0、正式计划和未解决问题最小证据限期保护；不可变输入单份引用，过期可重建导出按策略回收。本文为≤24KiB的record，180日复核归纳，不新设raw永久保留或续期。

## 正常 C constructor 已接线（2026-10-16 后续）

机器 `desktop-3fevhd2-1c74096080`。新增具名 [operation_root_relay.py](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/strategy_c/operation_root_relay.py)，provider正常import后调用完整constructor；不改旧 frozen 源码、不跳过constructor、不用AST重写其执行类。plan冻结必须早于独立cold start，prepared正常S0、machine/run/PID/create/gen/episode、source/DLL及实际Root容量逐项核对。无live binding或legacy API仍拒绝。

根据R184实际`state-a02`与run根日志修正了两处使用问题：从精确prepared.state_dir定位native-session/完整Driver原件；计量整个run（含mcp-calls.jsonl）、实际native-session和case ledger，路径去重并在请求前预留。新增14项仓库内离线回归覆盖这些实际问题及正常provider接线，旧C套件42项与共享12项一并复核；全为synthetic IO/transport/process metadata，没有新SDK或ABC成绩。正式 **0/3**、新T0与三次独立冷载要求均不变。
