# Stage 10 玩家 subject 有界 action cell（2026-09-11，2026-09-12 修订）

## 现行状态

当前为 **`product fix static-ready / live pending`**。R492 后 P1 为 **`8/9 = 88.9%`**，唯一待验收项是玩家可见的
`zg361mg.120`；P2 最终宣传视频继续 `LOCKED`。本页早期记载的“从 `.390` 选择 AI manager 再切换玩家”路线已被
R467 的实机 RED 与 `58e8cc9` 的生产修复取代，不能再用于启动准入。

## 现行产品路线

B1 是玩家限定系统。玩家本人作为有直属上级的天朝经理完成真实 B1 公示后，产品幂等调度 `zg361mg.90`；该隐藏事件
把直属上级作为 owner/root，并在玩家 manager 身上打开 F/AK。随后逐日 ticket 到达玩家可见的 `zg361mg.120`。
F/AK 使用 owner-local 独立 evaluation cycle，值为玩家 B1 `review_serial + 1`，保持 source 严格早于 evaluation，且不伪造
AI 上级参加过 B1。Stage10 与公共 opener 都拒绝 AI subject。

这条路线不需要 `.390`、manager selector 或 `set_player_character_v1`。R467 证明旧路线依赖已经没有正式生产者的 AI
`review_serial`；继续搜索 selector-positive 存档只会重复验证同一个已知缺陷。

## 单次执行合同

[`zg361_phase2_stage10_player_subject_action_cell.py`](../../tools/zg361_phase2_stage10_player_subject_action_cell.py)
从 paused、map-ready、产品-only 且已经停在 B1 D+299 的玩家经理存档执行一次最多 120 游戏日的验收：

1. exact-build `campaign-root-context-v1` 必须确认当前玩家与 activation 的 CharacterID 一致、存活、非独立、公爵及以上、
   `government_is_celestial` 且游戏规则含 `zg361_on`；直属上级必须与准入收据一致。
2. 保存原始 source checkpoint，不做角色切换、fixture 或控制台输入。
3. 复用共享 promotion-source navigator 消费已经活跃的 B1 固定尾链，不新开 B1；在同一个绝对 120 日截止内暂停于 `.120`。
4. `.120` root 必须是当前玩家 manager；saved scopes 必须回指收据中的直属上级 owner 与当前玩家 subject。
5. manager-governance provider 必须证明同一 F case 已 `state=5 / active=false`，随后才保存 terminal、确认事件并输出
   `p1_acceptance_evidence.central_stage_10_terminal`。事件 ACK 不作为业务后置条件。

任一身份、事件、lineage、期限或 provider 条件失败即保存 RED 并停车；action cell 不拥有进程生命周期，也不提供原地 retry。

## 启动前 source admission

受管 operator 的 v5 输入已被 R492 证实绑定旧产品树和错误的“仅余时间边界”前提，因此永久失效。下一次只接受 `zg361_stage10_player_publication_source_v6`；除 v5 的来源约束外，还绑定 R492 产品 RED、外来 roster exact-tuple 证据和修复后产品树。收据必须绑定：

- `SAV0101`、CK3 `1.19.0.6`、产品树 SHA-256，以及 checkpoint 的绝对路径、大小和 SHA-256；
- 离线玩家数必须为 `1`，唯一 `played_character` 和 `currently_played_characters` 都必须精确绑定目标 manager；
- 离线读到的玩家 manager、不同的直属上级、至少一名直属有地封臣、公爵及以上和 `celestial_government`；
- 一份 hash-verified 的 `zg361_stage10_player_source_capture_v1` 实机证明，确认同一 checkpoint 由 MCP 原生保存，且
  source 帧 paused/map-ready、玩家/上级/爵位/政府均与离线收据一致；
- `offline_topology_observed=true`、`offline_single_player_observed=true`，且 fixture、console、selection 均未使用。
- R488 live 初始进度证明 `B1=true / Central=false / PP=false / review-now=false`，以及同一个 exact checkpoint 内
  玩家经理 `zg361b1.102` 距当前日期恰好 1 日的离线队列证明。

离线字段只负责避免把明显不合格的存档送进 CK3；运行后的 campaign-root MCP 才是权威准入，任何不一致都会在首次保存或
游戏输入前 RED。operator 复用 AF5 的 frozen-input admission、唯一 CK3 生命周期与 managed cleanup，只暴露
`status / run-stage10 / cleanup`，成功时归档玩家经理 source 与 `.120` terminal。

## 当前候选源与通用资产边界

R481/R482 已淘汰原用户存档 `autosave.ck3`：`112339684` bytes，SHA-256
`80030146765A960EABAA1E38E90FF88CDEB8FBBBB2442E30E695FDFBFD64687D`。离线解析显示玩家 `37884`、直属上级
`61334`、直属有地封臣 `[57858, 16817470, 43060]`，但进一步检查确认它含五组玩家记录；实机也恢复为
`played_character=null`，所以不能作为产品来源。解析使用仓库外 Rakaly CLI 0.8.19：
ZIP SHA-256 `343E2C33869B1EC82E4AB018D1BB6936CC68B63146F99F426939F4D76106710D`，EXE SHA-256
`E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D`。

R482 的详情和 v3 admission 见
[`r481-r482-stage10-multiplayer-source-red-2026-09-12.md`](r481-r482-stage10-multiplayer-source-red-2026-09-12.md)。
下一份 source 必须从已 live-admitted 的单玩家 lineage 由 MCP 原生保存；离线扫描逻辑先迁为通用、路径无关工具。

## 聚焦验证

- action cell：normal / optimized 各 `5/5` GREEN；覆盖成功、独立玩家拒绝、非天朝拒绝、错误 terminal 和 provider 未闭合。
- operator：normal / optimized 各 `4/4` GREEN；覆盖目标角色透传、双 checkpoint 归档、单玩家/live provenance/拓扑/树/checkpoint 绑定和归档失败保留产品 GREEN。
- 两个实现与两个测试通过 `py_compile`；`git diff --check` GREEN。

本包没有为这一小改动运行全量测试或启动 CK3。公共 Operator MCP 1.1 的 control、schema、DLL 和传输协议没有变化；目标自有
activation/receipt 语义改变，需在根仓提交后同步 open_kaishek 兼容说明。

## 单玩家来源捕获执行器

[`zg361_stage10_player_source_capture_operator_job.py`](../../tools/zg361_stage10_player_source_capture_operator_job.py)
把“从已准入单玩家存档切换到合格玩家经理并原生保存”收成独立工作包。它只暴露
`status / capture-source / cleanup`，不提供 retry；每次 activation 只能启动一次受管生命周期。

启动前必须同时通过三份 hash 绑定输入：通用离线 topology 报告、既有 exact-build live qualification、原生 checkpoint
provenance。运行后依次执行：确认来源玩家与 campaign root、调用通用 `set-player-character-v1` 切换目标经理、重新确认目标经理
直属上级/公爵级以上/celestial/`zg361_on`、在游戏时间不前进的条件下调用 MCP 原生保存。成功结果为
`zg361_stage10_player_source_capture_v1`，并归档独立 checkpoint；任何身份、日期、进程、连接代次或来源哈希漂移都保留 RED。

当前冻结输入为已实机准入的 R159 单玩家 checkpoint，来源玩家/owner 为 `32904`，目标玩家经理为 `29037`。离线候选只负责
避免无效启动；新轮次中的 campaign-root 与保存结果仍由 exact-build MCP 权威确认。聚焦测试在 normal/optimized 下各
`4/4` GREEN，另通过 `py_compile` 与 `git diff --check`。

R483/R484 已证明 loader/native 来源本身可恢复，但首次 worker 错用 AF5 基类 validator，在 action 前丢失目标字段并保留 harness RED；没有玩家切换、保存或时间推进。最小修复改由 worker 调用本模块 validator，R483/R484 已完成 GREEN cleanup，不能原地 retry。证据见 [R483/R484 分派 RED](r483-r484-stage10-source-capture-dispatch-red-2026-09-12.md)。

修复后的 R485/R486 已签发 `zg361_stage10_player_source_capture_v1`：目标 `29037 -> 32904`、`date_raw=53154120`、MCP 原生保存、零时间推进。checkpoint SHA-256 为 `C11AFCF4...21BFA`，离线结构为唯一玩家 `29037`；详见 [R485/R486 来源捕获 GREEN](r485-r486-stage10-player-source-capture-green-2026-09-12.md)。

R487/R488 随后证明该来源实际位于 B1 D+299：`.102` 在次日，后续固定尾链至少还包含 `.103 +30d`、公共合账、公示回调和五级 F 票据。30 日边界因此属于 harness RED。现行 v4 receipt 绑定 live 初始状态与离线队列，上限只修正为 45 日，不回放完整 400 日 B1；详见 [R487/R488 边界 RED 与修正](r487-r488-stage10-bound-red-and-correction-2026-09-12.md)。

## R489/R490 的 104 日校准尾链修正

R490 在 45 日上限前已经记录有效的共同上级合账和 pending/reopen 入口，随后仍保持 B1 active。冻结 source 的玩家经理 `29037` 实际为 `m142=1 / m143=1`；产品允许 31 日 pending watchdog 和 30 日 post-seal reopen。结合 `.102/.103`、最迟 D+335 合账、D+336 校准入口、`.90 +1d` 与五张逐日 F 票据，`.120` 的保守最迟点为 D+403，即 D+299 source 后 104 日。

现行 120 日 action 上限只在该 104 日源码可达尾链外保留 16 日调度余量。v5 receipt 同时绑定 R488 的 30 日 RED、R490 的 45 日 RED、`.102 +1d` exact-save 队列和 104/120 日合同；任一 hash、角色、日期、初态或边界不一致都在启动前 RED。R490 没有暴露新的 mod 产品故障，旧 45 日充分性结论已被本节取代。完整证据见 [R489/R490 校准尾链 RED 与修正](r489-r490-stage10-calibration-tail-red-and-correction-2026-09-12.md)。

## R491/R492 的外来 roster 污染修复

R492 在完整 120 日边界内完成 40 次观测，日志已出现 7 次 season publication 和 10 次 final-callback compaction failure，B1 却始终 active，Central/PP 也始终未开启。这是产品 RED，不能继续解释为观察窗不足。

冻结 source 中，玩家经理 `29037` 的 `zg361_b1_subjects` 有 29 个存活引用，但只有 6 个属于当前 `owner=29037 / cycle=17 / case=17 / active=1 / roster=1`；其余 23 个已经属于经理 `29628` 的 case `19/19`。旧 prune 只检查 `is_alive`，而 processing 构造按 exact tuple 取 6 个，导致最终数量等式永远不可能成立。

最小修复让 subject 与 processing 两个持久列表都按当前经理的 owner、subject、cycle、case、active、roster exact tuple 清理，字段不可读时 fail closed。B1 runtime normal/optimized 各 `76/76` GREEN；未启动额外 CK3，也未扩大成长跑。v6 receipt `E363D5EE...ACF8` 已绑定通用角色域报告 `74BF50BB...B328` 与修复后产品树 `C428C42B...B5DC` 并通过无启动 validator。下一步只跑一次新轮次。完整证据见 [R491/R492 外来 roster RED 与修复](r491-r492-stage10-foreign-roster-red-and-fix-2026-09-12.md)。
