# 天朝二期双宣传片导演方案

## 唯一现行状态入口

当前 P1/P2/T1/T2、稳定 RED 索引与 Git/CK3 live-source 口径只从机器生成的
[`docs/project-state/current-state.json`](../project-state/current-state.json) 读取；P2 各固定分母和两条 cut 的独立节点只从
[`p2-stage-ledger.json`](p2-stage-ledger.json) 读取。生成输入、校验命令和三轴结果合同见
[`docs/project-state/README.md`](../project-state/README.md)。

本文件承担导演方案、合同和历史证据导航。下文所有带日期、轮次或“截至”字样的状态均为历史快照，即使旧段落保留“当前”“下一步”措辞，也不得覆盖上述机器投影；历史内容不删除，以便继续核验原始 artifact。

## T0-P1 验收合同与 R504 历史收口（2026-09-10 owner revision）

P1 现在只由产品关键链、代表性高风险路径和真实 encountered RED 决定。以下九项必须全部 GREEN：

1. 当前 B1 配额重建修复取得 production-live 后置；
2. `zg361comp.1` 的 AF5 选择 authored `42` / native `41`，并由独立 provider 证明 portfolio 进入终态；
3. 玩家作为 Central owner 的 stage `9/11` 分别取得 `zg361cl.390` 与真实 Workforce provider terminal（正常 close 或合法 N/A close）；独立的玩家 manager-subject 路线以 `zg361mg.120` 取得 stage `10` F-case terminal，不要求 `.361` 宪章/制度债事件或其跨周期后续；
4. 从一个代表性终态生成 save，执行一次真正 cold restore，并回读相同终态；
5. 覆盖完整 gameplay 时间窗的 error scan 为 GREEN；
6. managed cleanup 为 GREEN；
7. 与待签收字节 SHA-256 完全相同的最终候选通过完整 L0。

这里的 stage `9/10/11` 分别计三项，因此机器门共有九个布尔检查。`tools/run_zhongguo_acceptance.py` 仍在 artifact 中保留旧
`7 action + 4 observation`、source registry、第三次 `.356`、三周期和全树 definition 统计，但它们现在明确是
`NON_BLOCKING` coverage。缺少任意这些 coverage cell 不会把 P1 变 RED。`8/8` clean footage 和两条成片只属于 P2；P1
签收前 P2 继续硬锁定，既不能以 footage 缺失阻塞 P1，也不得提前检查/更新宣传工具或制作视频。

下文在 2026-09-10 以前形成的 `source 3/4`、第三次 `.356`、三周期、`7+4 exact` 与 `footage 0/8` “P1 剩余”表述均作为
历史计划和 coverage 快照保留；其 P1 阻塞语义已被本节 supersede，不得再据此推导当前签收结论。

正式入口 `tools/run_zhongguo_acceptance.py --phase2-live-batch --phase2-p1-evidence-manifest <json>` 默认只做当前
paused candidate 的 manifest/seed 绑定并判定上述九项，不再依次跑旧 Incident/B2/manager/scoreboard/Workforce/promotion
全矩阵。证据 JSON 必须保存现有 provider/receipt 内容；cold restore 项必须包含真实 save/restore receipt、两个不同 PID、
各自有效且与当前帧一致的进程内 generation，以及 B1、AF5、Central、Workforce 的 identity/state/receipt 前后回读。旧矩阵只有显式增加
`--phase2-legacy-full-tree-coverage` 才运行，结果只记 `NON_BLOCKING` coverage。九项以外的问题照常记录和处理真实 RED，
但不能扩大 P1 blocker；因此 P1 判定没有“还差一个历史 cell”之类的隐含口径。显式 legacy 诊断命令本身仍可因其
coverage 失败返回 RED，但该诊断 RED 不回写、不改变独立的 P1 九项判定。

截至 2026-09-12 R504 收口，现行候选 P1 为 **`9/9 = 100% / GREEN`**：B1、AF5、Central stage 9/10/11、代表性终态 cold restore、完整 gameplay
时间窗 error scan、managed cleanup 与候选 L0 全部 READY。Stage 10 在 36 游戏日后真实到达 `zg361mg.120`，同帧原生 provider 证明玩家经理/直属上级绑定和 F `state=5 / active=false`；旧 action 的 aggregate-readiness RED 已按 Stage 10 专用合同离线提取，原 RED 保持不变。Stage 11 与 cold restore 的 exact-build 证据、两 PID 生命周期、process-local generation 合同和 cleanup RED 修复见
[`r476-r480-stage11-and-cold-restore-2026-09-12.md`](r476-r480-stage11-and-cold-restore-2026-09-12.md)。权威中间账本为
`Z:\ck3_mod_rewrite\_runtime\p1-critical-path-assembler\pending-assembly-status.json`，状态 ledger SHA-256 为 `08AA89BC...E0F2`；最终 manifest `C8879E16...E1A5` 经当前 runner 独立判为九项全真，gate 为 `309750CB...57D6`。这只是九项门禁的完成比例，不换算为
T0 产品总完成度。P1 已签收；P2 只能按“检查宣传工具版本 → rebase 更新远端 master → 验证更新 → 制作并发布最终视频”的顺序推进。R390 Stage 9 冻结记录的真实选择与当前候选的 23 文件逐字节
资格核对，以及 R432 硬上限、R433 零游戏日诊断见
[`r432-r433-bounded-stage9-intake-2026-09-11.md`](r432-r433-bounded-stage9-intake-2026-09-11.md)。证据整理不重开 CK3。

P2 前三步已在 2026-09-12 完成：宣传工具 fresh fetch 后从 `57c42fca` 更新到 `adb52f44`，normal/optimized
各 268 tests（2 skipped）GREEN；根仓 143 个提交无冲突 rebase 到远端新增 11 个提交之上，并将
`origin/master` 线性快进到 `77bd8e42`。更新后的现行 runner 再验 P1 仍为 9/9 GREEN。机器回执与边界见
[`p2-toolchain-master-update-2026-09-12.md`](p2-toolchain-master-update-2026-09-12.md)。下一步只盘点八段正式 clean footage，缺哪段补哪段。

R538/R539 的首个正式捕获通过前两段，但第三段在动作前返回
`owner_filter_mismatch`。该 RED 证明 P2 编排仍错误依赖旧 seed 的 AI-owned B1，
而现行产品与 P1 Stage 10 已使用玩家限定的真实玩家经理公示路线。捕获合同现改为
hash-bound Stage 10 v7 source restore：玩家经理 `27181`、直属上级 `36354`，
从 checkpoint `50B713F2...C7E4` 有界推进到 `zg361mg.120`，由同帧 F
`state=5 / active=false` 证明业务终态并把事件保留到 clean hold。失败 take 不计数，
P2 仍为 `0/8`；证据与修复见
[`r538-r539-stale-ai-manager-capture-contract-red-2026-09-12.md`](r538-r539-stale-ai-manager-capture-contract-red-2026-09-12.md)。

R584–R588 的连续 take 在前四段通过后，于 HC 来源从成熟 `.356` 推进到 `.360` 途中遇到原版
`ep3_story_cycle_admin_eunuch.8030`，按多选未知事件规则保留 RED 并完整清理，P2 仍为 `0/8`。既有共享原版事件注册表本已包含该事件的 2/3/4 按钮合同；本次补入 exact-build 调用链与 R588 现场，并让 P2 等待门在全部保存域和 native 映射严格吻合时选择最小影响的 authored D/native 3。未知或漂移事件仍在选择前 RED。代码提交、证据哈希、轮次处置和下一次 R589 边界见
[`r584-r588-eunuch-8030-red-and-contract-recovery-2026-09-13.md`](r584-r588-eunuch-8030-red-and-contract-recovery-2026-09-13.md)。

R467 的 `no_bounded_ai_direct_manager` 现已结合 `380af02` 之后的生产调用链确认为真实 reachability RED：AI 年度 B1 已按玩家限定停止，但旧 Stage10 仍要求 AI 经理或其 AI 上级持有 `review_serial`。最小修复改为玩家经理真实 B1 公示后调度 `.90`，由直属上级作为 owner/root 打开玩家 F/AK，并用独立 evaluation cycle 保持 strict lag；Stage10 与 opener 同时拒绝 AI subject。定向双模式测试与本地静态解析 GREEN，尚待新轮次 R481 单次有界实机到达 `.120`，所以 P1 仍为 8/9、P2 仍锁定。见 [R480 后 Stage10 玩家公示可达性修复](r480-stage10-player-publication-reachability-fix-2026-09-12.md)。
R434/R439 的零游戏日 selector 只排除了 R432/R159 作为 B3 focused 路线的 AI manager/direct subordinate source，不能判定玩家可见的 Stage 10 `.120` 路线；其中 R439 重复了 09 月 07 日已有的 R159 结论，是一次可避免的验证。R435 只排除 R432 的 Stage 11 terminal 资格；R437 又证明 R398 输入存档本身并未停在 `.242`，因此在零游戏日、零事件输入处停止，没有把 source 误读扩成第二次长跑。两种 Stage 10 角色拓扑、验收 runner 纠正、不重跑边界与下一项 source 要求见
[`r434-r439-bounded-source-checks-and-stage10-route-correction-2026-09-11.md`](r434-r439-bounded-source-checks-and-stage10-route-correction-2026-09-11.md)。P1 仍为 `6/9`。

Stage 10 action/operator 已同步改为真实玩家 B1 公示路线：从非独立的天朝玩家经理存档调用 review-now，在同一 120 游戏日
绝对截止内等待 `.120`，不再依赖 `.390`、AI manager selector 或玩家切换。R482 在业务动作前确认旧 v2 receipt 错放了
内部含五组玩家记录的 `SAV0101`；实机为 `played_character=null`、mailbox 未安装，按 300 秒 readiness 门 RED 后立即清理，
没有重跑。v3 receipt 现同时要求离线单玩家结构及 hash-bound 的 MCP 原生保存/live campaign-root 证明。action normal/`-O`
各 `5/5`、operator 各 `4/4` GREEN，状态仍为 `static-ready / live pending`，P1 为 `8/9`。公共 Operator MCP 1.1 不变，
目标自有 receipt 语义需在本次根仓提交后同步 open_kaishek。完整合同与 R482 证据见
[`stage10-player-subject-bounded-action-cell-2026-09-11.md`](stage10-player-subject-bounded-action-cell-2026-09-11.md)。

R482 后的下一步来源构造已实现为独立受管 operator：从已实机准入的 R159 单玩家 checkpoint 恢复，原生切换到目标玩家经理
`29037`，同帧复核 campaign root 后以 MCP 原生保存；控制面只有 `status / capture-source / cleanup`，不允许 retry。离线 topology、
既有 live qualification 与 checkpoint provenance 三者必须 hash 一致。该工作包只生成 v3 admission 所需来源，不计作 Stage 10
`.120` 验收；接口与聚焦验证见同一 [Stage 10 action cell 专题](stage10-player-subject-bounded-action-cell-2026-09-11.md)。

R483/R484 首次 source-capture 启动的 loader/native 链全部 GREEN，但继承的 worker 错用 AF5 基类 validator，目标字段在 action 前丢失并保留 harness RED。玩家切换、保存和时间推进均未发生；两轮已清理。最小修复让 worker 显式调用 source-specific validator，并增加分派回归测试；下次只允许用递增新轮次执行。见 [R483/R484 分派 RED](r483-r484-stage10-source-capture-dispatch-red-2026-09-12.md)。

R485/R486 已生成合格的 production-live 单玩家来源：玩家从 `32904` 原生切换到经理 `29037`，同帧确认 `29037 -> 32904`、tier 4、celestial 与 `zg361_on` 后保存；日期未推进。新 checkpoint SHA-256 为 `C11AFCF4...21BFA`，离线复核 single-player ready。两轮 cleanup GREEN 并已终止。该来源只解除 v3 admission 前置，P1 仍为 `8/9`；见 [R485/R486 来源捕获 GREEN](r485-r486-stage10-player-source-capture-green-2026-09-12.md)。

R466/R467 随后从距 `.390` 仅 2 游戏日的 production 存档执行了一次有界资格尝试。R467 在真实 `.390` 帧返回
`no_bounded_ai_direct_manager`，所以该来源的 Stage 10 用途永久淘汰。Stage 11 随后因恢复推进时 paused revision 已变化而返回
`snapshot changed or is not ready`；首帧缺少 owner/portfolio/case 绑定是 D+2 pump 前的预期状态，不能据此淘汰 Stage 11 来源。
runner 已把这条 exact-build 文本纳入现有四次上限的只读 rebind，normal/optimized 各 `14/14` GREEN；Stage 11 仍为
`NOT_EVALUATED`，可从原始近边界输入短程续跑。运行在 10 游戏日上限内停止，cleanup GREEN，P1 仍为 `6/9`。启动前还修复了
Operator worker 首次后台导入 `numpy/cv2` 时无响应的问题；这是 Python Operator 生命周期修复，未修改公共 MCP 或游戏资产。
证据见 [`r466-r467-stage10-near-source-rejection-2026-09-12.md`](r466-r467-stage10-near-source-rejection-2026-09-12.md)。

R408–R414 的终端 lineage 换轨、五玩家 `SAV0102` 两次 native-readiness RED、离线 normalization 的证据边界以及
R375 单玩家 checkpoint 的有效准入，见
[`r408-r414-lineage-intake-and-multiplayer-red-2026-09-11.md`](r408-r414-lineage-intake-and-multiplayer-red-2026-09-11.md)。

## 现行 effect 文件边界（2026-09-05）

单文件过大现按强制缺陷处理，不再讨论是否拆分或等待性能触发。canonical source 已退役 mechanism、B1 runtime 与 core 的四类旧聚合 owner，改为 `186 + 12 + 4` 个用途分片；当前全树 `626 files / 3721 effects / maximum 10 / >20=0 / exceptions=0`。后续 production 与 CK3 验收只允许使用拆分布局，详见
[`phase2-effect-file-boundary-audit-2026-09-04.md`](phase2-effect-file-boundary-audit-2026-09-04.md)。

测试与验收用例的统一执行索引见
[`phase2-acceptance-case-index.md`](phase2-acceptance-case-index.md)；361 项批次权威定义仍以
`mod_zhongguo_style/docs/361-phase2-full-implementation-program.md` 为准。

## Source registry 与 T0 历史快照（2026-09-10；P1 门语义已 superseded）

本节记录当时 canonical source registry 的 `3/4` coverage 快照：promotion/compensation、projects/metrics 与
incidents/operations 已有真实 paused source checkpoint，当时尚无 `capture_cross_cycle_endgame`。R303/R313 以下段落保留各自
历史增量；R326 已把 incidents/operations 纳入 schema-v3 多分支联合前缀。source `4/4` 已不再是 P1 硬门。

该时点 T0 账本为 `50%`、canonical stage `8/11`；这是历史进度快照，不是现行 gate 算法。`strict 4/361` 与
`definitions 106/626` 是非阻塞发现 backlog，不是 P1 完成门，也不得换算为剩余工作百分比。P1 未签收前最终宣传片
T0-P2 继续硬锁定。

共享原版事件资产本包为 `165 contracts / 165 analysis / 15 observation keys`，production runtime 为 `304`；冻结迁移基线
`156 + 8 = 164` 与 embedded bucket `79` 不变，`.1101` 是其后新增记录。R372 已在同一
PID 热恢复 TGP0001；此前 stress RED 的真实根因是提交阶段重新按 base contract 解析，而不是 reload 未生效，两个最小补丁
提交为 `039a509`、`e6ab3d4`。长跑随后同 PID 热恢复 `epidemic_events.1064` instance `867` 并验证 advance，继续推进到
`epidemic_events.5009` instance `871` 的第二次合法交付；R374 随后将 `natural_disaster.7031` authored3/native2 同 PID drain 并验证 instance `978` advance，
其选择前 RED observation 仍保留。R374 随后又将 `ep3_story_cycle_admin_eunuch.1001` authored2/native1 与
`tribute_mission.1005` authored6/native5 同 PID drain，并分别验证 instances `988`、`1007` advance；三条动作前 RED
observation 继续保留。产品私有 `zg361p2c.2` 第三次跨周期 summary 已由 commit `2ba288b` 改为有限产品窗口内可重复，
R374 在同 PID 选择 authored1/native0 并验证 instance `1035 -> null`；上游 typed-RED cycle 仍按失败保留。随后 drain
`zg361.40` #1036 与 `epidemic_events.5009` #1037。新的原版 `vassal_interaction.0040` #1038 可移植合同已由
commit `eeea8a6` 推送并通过 Official Runner；R374 在 PID `51852` / generation `1` 原位选择 authored1/native0，
验证 instance `1038 -> null`，成为第九条 production-live primitive。随后 `debate_event.5110` #1039 亦安全 drain；
原版 `trait_specific.4001` #1040 的 exact-build yearly caller、直接/下游效果边界和实见三 scope shape 已由 commit
`75a611e` 迁移并通过 Official Runner run `34398909398` / job `102625565721`。R374 同 PID/generation 选择
authored2/native1，验证 instance `1040 -> null`、revision `1670 -> 1671`，成为第十条 production-live primitive；
随后 #1041--#1045 安全 drain。原版 `death_management.1007` #1046 park7 的严格无 killer
shape 为 `new_memory`/`dead_character`/`deceased_character_stress` 三 scope，唯一 authored1/native0 的完整直接效果为
基础压力 20。该形状已由 commit `c666335` 按 rebase-only 推送；Official Runner run `34401932801` / job
`102635654978` completed/success。R374 保持 PID `51852` / generation `1`，选择 authored1/native0，验证 instance
`1046 -> null`、snapshot `native:1779 -> native:1780`、revision `1780 -> 1781`、postcondition GREEN，成为第十一条
production-live primitive。随后 `.0010` #1047 authored2/native1、`.5110` #1048 authored2/native1、`.1100` #1049
authored1/native0 均安全 drain。

park8 的原版 `faction_demand.2001` #1050 动作前为 date `53595360`、player/root `32904`、snapshot
`native:1847`、revision `1848`，五个 scope；native0 与 native2 enabled，native1 shown/disabled，selection 未尝试且
无需进程重启。最小共享修复选择 authored3/native2 的拒绝路线，并增加通用 disabled-native 合同以区分“呈现但不可用”
与真正的 shape mismatch；动作前 deadline `53635896`，尚余 `1689` game days。park8 report / driver-state / hot-recovery
SHA-256 为 `AC7EF0A37844A7F0B252917DAB0922B77721F0CAE6FB2A7416BC0F4420BCF9CA` /
`FDFD7C0B2AB7DF6DC936B9FC01D611F1F5425BA6E571CBB74942BF08A68A9F28` /
`89B4F2F8F6ADD2243C0CAD803766EB6B82491D0EF8E3C3BCCC6B55E5BC41B561`。`.2001` 的双模式静态验收与实际 MCP
查询 GREEN，T2 判定 open_kaishek `NO-CODE-CHANGE`；package commit
`3bb5169ca2b81701a8ea49e9d842de36f39fd87b` 已按 rebase-only push，Official Runner run `34404896747` / job
`102645406781` 约 4 分 26 秒 completed/success、失败步骤为空。R374 在原 PID `51852` / generation `1` 原位选择
authored3/native2，instance `1050 -> null`、snapshot `native:1847 -> native:1848`、revision `1848 -> 1849`、
postcondition GREEN，成为第十二条 production-live primitive。

当前长跑在新的 `faction_demand.1101` #1055 park9 选择前 RED 暂停：date `53607792`、player/root `32904`、
snapshot `native:2057`、revision `2058`，四个 scope；native0/native1 均 shown/enabled、非 fallback/cancel，
selection 未尝试且无需进程重启。四个 scope 为 `faction` faction/raw25、`peasant_county` landed_title/raw5、
`peasant_leader` character `33633057`/raw4 与 `new_title` landed_title/raw5。exact-build 可重复合同选择
authored1/native0；eligible 月检普通约 50 个月、高不满加成约 7 个月，另有 90 eligible days 上界，不是 daily pulse。
接受仍有 legitimacy、top-liege 县控制/十年 modifier 等代价，但避免拒绝立即开战；宗教只作附带边界。deadline
`53635896`，尚余 `1171` game days。park9 report /
driver-state / hot-recovery SHA-256 为 `BA39B64ACC3224E8F1F5D5C04719A04106430D7F2F2551DEC52CCEC514FC3AA6` /
`78C84C846ED9D2F05AF153EC9302C4C3A85C645FD0B33316CD212B10E342C494` /
`4E3B59B3EB6328939D2008BD2DD4138546C0224F76D62297D19415138DF577E6`。代码/双模式测试和实际 MCP list/call
已 GREEN，T2 为 `NO-CODE-CHANGE`；Python normal/`-O` 各 `42/42`、open_kaishek `3/3` GREEN。仅
commit/rebase/push 与同 PID live retry 尚待；live 仍为 12、non-live 为 153。该增量不改变 T0、stage、source 或 P2 门。

R303 已在 CK3 `1.19.0.6` 的真实 paused frame 完成 projects/metrics provider 后置条件：owner `32904`、subject
`30938`、cycle/case `4/2`，CP #026 contribution receipt `1` / revision `3` / value `1` 被 P3 #229 metrics revision
`2`、dictionary `metric_dictionary_subject_v1` 明确回链。report 位于
`Z:\ck3_mod_rewrite\_runtime\p2r303projectsmetrics\report.json`，SHA-256 为
`926BBD25076F69205B8AAA7CCC366AB470227BCBE174017B7E86C282862D7B01`。这是 private candidate 的 live GREEN；默认
CK3 adapter 仍不广告该 capability，`production_live_ready=false` 不变。

R313 随后从真实 `zg361cp.26` Route A lineage 捕获 schema-2 projects source checkpoint。provider 在 owner 仍为当前玩家时
以显式 subject 读到 `checkpoint_state=cp26_ready_p3_absent`，再由 native set-player 在同一 raw date `53246712` 把玩家切至
subject 并原生保存；checkpoint 为 `89,548,228` bytes，SHA-256
`72FB7D0F04C8B584555C35AC87313A5581FA8610344F72ABA4758904BC4C433B`。R313 report SHA-256 为
`9225D94ABCA8E47AFF0D2CBB3BE51785E28F5C0781F412F4B1D917B13046E76F`，projects registry SHA-256 为
`7F80326DA8B0EBBBCEE26DE21E2A55A6F74AAE989D567F9B8909BD1F7B3190DE`；cleanup GREEN，原始 source checkpoint 未改变。

以上是 R313 时点的历史 `2/4` 基线：当时 promotion `1/1`、projects `1/1`，two-of-four artifact SHA-256 为
`8128750541EE7683EAB5CAD83CFDAF11FCCE47F8017019E3B5541A76F1AD603A`。registry checkpoint 是取证输入，不是成片素材；
当前已由 R326 推进至 `3/4`；缺少 cross-cycle/endgame source 只影响 coverage，不再阻塞 P1。该时点真实 footage 为
`0/8`、两条 MP4 为 `0/2`；它们属于仍被硬锁定的 P2。

这里是天朝二期两条正式宣传片路线的权威导演文档入口。用户已明确要求：**两个版本都保留、都制作、都分别交付成片。**二者不存在“主方案/废案”或“长版/短版”的从属关系。

## 当前实机门（2026-09-04 12:49）

最新 canonical candidate 已在 CK3 `1.19.0.6` 的 r20 实机保持 seed `ready`：252-file / 12,104,708-byte r8 product
完成 loader、暂停 checkpoint 与 cleanup；candidate contract SHA-256 为
`FD055093617AA78858BB47F6F9F2BE4AA2E1B66ED4CABE4983B5418C6C99B7E7`，checkpoint SHA-256 为
`96D1919D569E6F3EA115BF21882B0F4372246812B1E1F630F3AED44968D49335`。loader scan GREEN / `matches=0`，quiet window
`16.232 s`。这解除的是修复后 seed 生成门，不是 8/8 素材门。

focused r22 的 outer、cell、scenario 与 matrix 已全部 GREEN：three arms / four exact restores / final baseline、4 restarts / 5 unique
PIDs、cleanup/driver/locks 与 source/product/runtime immutability 均通过，readiness 为 `production-live primitive`，因此
**B2 focused gate COMPLETE**。r21 的 5,607 条静态 liveness 行仍保留为 nonblocking evidence，并未删除。该结论不等于全
Phase2 或 T0 完成；outer report SHA-256 为 `6FC744BA4C5D6BA905A41A0E91EF870452A378DA3431DCBFB537C31AA3533F47`，artifact 位于
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-b2-r22-20260904-123400\focused-live`。真实 footage 仍为 `0/8`，两条 MP4 均未生成。
r22 loader scan GREEN、0 matches，没有 loader performance RED，不触发额外拆分。B2 首用 RED、修复、跨进程事件身份与 r20–r22 证据见
[`b2-first-use-loader-and-seed-evidence-2026-09-04.md`](b2-first-use-loader-and-seed-evidence-2026-09-04.md)。

seed-entry 的加载根因也已纠正：仅做用途拆分的 r2/r3 仍 RED；移除
`zg361_workforce_appointment_fact_seal_and_publish_effect` 的直接自递归后，诊断候选及 production r4/r5 连续 GREEN。
因此“文件过大”不是本次已证明根因；B2+ 仍严格执行用途分片（目标 1–10、原则不超过 20），用于闭包选择、维护与后续
加载性能 A/B。r9 新增层为 72 个 effect 文件 / 314 definitions，单片最大 10，无超限例外。
当前 canonical 全树与 live product 的逐文件分类、四个 pre-B2 owner 的理由、精确哈希和实机覆盖边界见
[`phase2-effect-file-boundary-audit-2026-09-04.md`](phase2-effect-file-boundary-audit-2026-09-04.md)。

B3 manager 首次真实启动已执行，但在 `310.617 s` 因累计投影漏选 central dispatch provider 而 RED；CK3 实际报告
`record_stage` / `record_red` Unknown effect，递归静态 closure 还闭合到同 provider 的 `mark_lane_busy` / `schedule_pump`。
cleanup GREEN。这是 material/call-graph closure RED，不是文件大小因果证据，所以当前不触发 size A/B。`ce458af` 的全产品
边界审计仍为 427 files / 3,718 effects / max non-legacy 10 / 0 target miss / 0 violations。证据哈希与后续判定规则见
[`b3-manager-first-live-startup-red-2026-09-04.md`](b3-manager-first-live-startup-red-2026-09-04.md)。

## 两条正式路线

| 版本 | 权威导演稿 | 叙事主角 | 目标时长 |
|---|---|---|---:|
| 人物版 | [`phase2-character-director-treatment.md`](phase2-character-director-treatment.md) | 一名真实历史官员贯穿绩效季，以个人遭遇带观众进入制度 | 约 `09:30`，允许 `08:00–12:00` |
| 制度群像版 | [`phase2-institution-director-treatment.md`](phase2-institution-director-treatment.md) | 制度及多人组织网络，追踪一个 C 如何被生产、批准和跨周期记账 | 约 `09:40`，允许 `08:00–12:00` |

两版的配置、authoring ledger、cut/run/artifact/output ID 与制作命令统一维护在
[`phase2-dual-cut-production.md`](phase2-dual-cut-production.md)。

## 双片交付登记（2026-09-03 继续执行）

本轮分别生成的人物版与制度群像版制作包见
[dual-video-production-packet-2026-09-03.md](dual-video-production-packet-2026-09-03.md)。

两条路线都是正式交付物，不互相替代：

- 人物版：[`phase2-character-director-treatment.md`](phase2-character-director-treatment.md) → `zhongguo-361-phase2-character-led.mp4`
- 制度群像版：[`phase2-institution-director-treatment.md`](phase2-institution-director-treatment.md) → `zhongguo-361-phase2-institution-led.mp4`

两套配置、authoring claims、审片计划和独立输出路径均已落盘。宣传工具已在可写 fresh clone
固定到 `origin/main` 的 `57c42fca13ea459432c1caf76e069a1fbccf602c`，并通过二期 builder 的 26 项测试；
正式 TTS/渲染仍必须等待 8/8 段真实 CK3 clean spans。当前两份 MP4 尚未生成，历史启动阻塞和可核验日志见
[`live-startup-blocker-2026-09-03.md`](live-startup-blocker-2026-09-03.md)。

最新一次双版本前置复核见
[`promo-preflight-audit-2026-09-03.md`](promo-preflight-audit-2026-09-03.md)，两份 runbook 位于
`_runtime/phase2-preflight-audit-20260903-0930/`，均诚实停在 `RED / footage_pending`。

`docs/` 保存两版的导演稿、生产合同、审片模板和状态索引；大体积 MP4 按项目约定落在外部
`artifacts/demos/YYYY-MM-DD/`（并在本页登记路径、时长、编码和 SHA-256），不把成片二进制塞进 Git。

## 交付进度（2026-09-09）

| 工作包 | 当前进度 | 下一项 | 预计时间点 |
|---|---|---|---|
| 二期产品代码与发布树 | 该表形成时为 T0 `50%`、stage `8/11`；source registry `3/4` 仅作 coverage | 先闭合 B1 live、AF5 `42/41` terminal 与 stage 9–11；再做一次代表性终态 cold restore、error scan、cleanup 和最终候选 L0 | 以九项现行硬门为准；source `4/4`、全树计数和素材不参与 P1 判定 |
| Canonical source registry | promotion、projects/metrics、incidents/operations 各 `1/1`；合计 `3/4 incomplete` | 可在非冲突资源下继续补 `capture_cross_cycle_endgame`，但不得占用关键链或延后 P1 | 非阻塞 coverage；不计作 footage，也不再是 P1 前置 |
| 人物版最终片 | 导演稿、独立配置、authoring ledger、审片模板已完成；真实 footage `0/8`，尚无 MP4 | 取得 8 段 clean spans → 具名 source review → fresh-update promo tool → TTS/build/review/export | 素材齐备后再估；候选制作约 45–90 分钟，另加两轮真人审阅 |
| 制度群像版最终片 | 导演稿、独立配置、独立回切编排、authoring ledger、审片模板已完成；真实 footage `0/8`，尚无 MP4 | 同上，但独立生成旁白、候选、审阅和导出 | 素材齐备后再估；候选制作约 45–90 分钟，另加两轮真人审阅 |
| 宣传工具 | 历史 fresh clone 曾冻结于 `57c42fca13ea459432c1caf76e069a1fbccf602c`；这只是历史准备证据，不算当前 P2 前置完成 | T0-P1 通过后才允许重新检查版本、rebase/pull 到远端 main 并验证，再把 fresh checkout 注入 builder | T0-P2 当前硬锁定，尚未进入本轮更新门 |
| G2 / open_kaishek | 历史暂停已解除；default-production truce duration 已完成 paused same-frame 双查询并晋级 `production-live read-only primitive`，但 expiry/loss/decision/action 与 `GEN-034` 仍未就绪 | 继续补 actual expiry 与 proven war-bound loss 的只读观测；不得由 1825 天推导 expiry | 已完成本次 live 槽；后续仍需新的冻结候选与独占槽 |

这里的“尚无 MP4”是刻意保留的事实状态，不是漏写路径：没有真实八段 CK3 素材、具名审阅和 fresh tool receipt 时，制作器会 fail-closed，不生成占位宣传片。

## 启动恢复基线（2026-09-03；后续增量见下文）

有效 profile 的最新对照已改变启动判断：显式非空 disposable `-userdir`、完整 `pdx_settings.txt/account/dlc` 与 warm DX11 cache 下，无 Mod 裸跑 42.253 秒到达 `Frontend`；当前 Release bridge 54.634 秒、RBX guard candidate 45.582 秒也都到达 `Frontend`，并以 `WM_CLOSE`、exit `0`、cleanup proven 收尾。早先缺 profile 资产的 direct probe 仍可在 `ck3+0x1DABD89` 崩溃，但不能再据此宣称 CK3 本体完全打不开。剩余 RED 是 Phase2 broad/workforce 依赖闭包与事件本地化 fan-out；event-locaug 虽出现窗口和 `frontend_main.gui`，但未完成 history load。对应 crash dump、session cleanup 和 relay 日志保存在
`Z:\\ck3_mod_rewrite\\_runtime\\phase2-seed-20260903\\`，这些运行均没有产生满足合同的可入片游戏素材，当前 footage 仍是 `0/8`；详细分层见
[`manual-vs-automated-launch-diagnosis-2026-09-03.md`](manual-vs-automated-launch-diagnosis-2026-09-03.md)。

宣传工具已在可写 fresh clone `Z:\\ck3_mod_rewrite\\_runtime\\promo-tool-fresh-20260903` 更新并核对到 `origin/main`（`57c42fca13ea459432c1caf76e069a1fbccf602c`）。等 provider/业务门闭合并取得八段素材后，仍会分别完成两版 TTS、字幕、候选、人工审阅、导出和独立哈希记录。

实机启动复现、解锁条件和诚实 ETA 见 [`live-startup-blocker-2026-09-03.md`](live-startup-blocker-2026-09-03.md)。

最新 A/B 结果：冷/不完整 profile 的 `-noWorkshop` 以及 `--userdir=<isolated path>` 探针仍在同一 `ck3+0x1DABD89` 崩溃；复用完整有效 profile 后裸跑、当前 bridge、RBX guard 均 GREEN。Steam `-applaunch` 入口仅是 no-launch harness 结果。详细回执见 [`live-startup-probe-no-workshop-2026-09-03.md`](live-startup-probe-no-workshop-2026-09-03.md) 与 [`ck3-startup-recovery-live-evidence-2026-09-03.md`](ck3-startup-recovery-live-evidence-2026-09-03.md)。

两版的独立审片入口为：

- 人物版：[`review/character-led-review-plan.md`](review/character-led-review-plan.md)
- 制度群像版：[`review/institution-led-review-plan.md`](review/institution-led-review-plan.md)

每个入口都包含第一轮原始素材/声明审阅和第二轮最终候选片审阅模板；模板不是通过回执，只有绑定真实媒体字节并完成全长 `1×` 审阅后才能签核。

## 共同素材与独立交付

两版共享同一套真实二期证据基础：十个 canonical authoring chapters，其中开场/结尾为双语生成卡，中间为八个真实 CK3 clean spans。共享 source span 是为了避免重复制造游戏事实，不代表两版是同一条视频。

两版必须分别拥有并验收：

- 独立的项目配置、剪辑时间线、中文旁白和中英双语字幕；
- 独立候选视频、媒体探测结果和 SHA-256；
- 独立 claims audit 与两轮 1× 完整人工审阅/sign-off；
- 独立导出记录；若外部发布，还要分别保存明确发布回执。

任何一版通过或发布，都不能替另一版自动签核。人物版不得用蒙太奇伪造同一人物因果；制度版不得把不同角色、案件或周期伪装成一条连续游戏内因果。共同的实机事实、authoring/claim 边界、有效 footage intake、媒体门禁和真实证据要求继续生效。

## 路径与同步规则

本目录中的两份 treatment 是导演内容的 **canonical authority**。`mod_zhongguo_style/promo/` 下保留同名入口文件，仅用于兼容原有浏览路径并指向这里；不得在两个目录分别维护两份正文。后续导演修改只编辑本目录的权威稿。

项目配置、authoring claim matrix、capture contract、媒体构建和 readiness 状态仍由各自原有文件负责。导演稿只定义叙事与拍摄方案，不会自行把 `planned`、`static-ready` 或候选素材提升为 live、complete、exported 或 published。

## 历史 seed preflight 回执（2026-09-03 06:51；已被 r9 supersede）

以 clean freeze `165b47742fd05ff3713b8be4452711002328d57d`、source ZIP SHA-256
`77aa3e30f1c20763576dbeea71b1c7451cfd63a15fb53a46fc58a373d72338e8`、guard-on bridge 和同步
open_kaishek `981c79388a07e447b18f8e4472a16fd65e28c083` 重新执行 `--preflight-only`：结果 `GREEN / preflight-ready`，source/archive、依赖、projection、bridge 和静态测试均 GREEN，`ck3_launch_attempted=false`；该历史时点的 seed 合同仍为 `blocked_seed_generation_required`。回执位于
`_runtime/phase2-seed-20260903/artifacts-preflight-current-03/preflight.json`，SHA-256
`9057F967CFE97036AD4E3918C2640892371EBB006BBADDE18EE36DA7A4CABE2E`。这确认后续实机采集入口可直接复用，但不等同于 live 或视频完成。

### 30 分钟完整投影轮次（已结束；monolith control）

`formal-phase2-full-exact-1800-20260903` 已完成并封存。该轮实际挂载的是未拆分 monolith（264 files / 15,937,535 bytes），不是目标 exact A+B 树；report SHA-256 为 `241254233107098CF5F385F1C4472D94CA3E1C8D93D6CFFF869A8C38C0F7A79A`。结果为 `timeout`，最后停在 `Total of : 881`，未到 `Frontend`/history，`error.log=0`，CK3 exit `1`，cleanup 已证明。因此本轮只能作为非拆分 control，不能用来判定 split 功能 GREEN。

随后 B7 workforce stub 的 300 秒轮次仍在 `Total of : 881` 停止，Frontend/history 均为 false，结论保持 RED。7200 秒续测已取消，不再创建 `formal-phase2-full-exact-7200-20260903`。当前改按 [`phase2-incremental-startup-batch-plan-2026-09-03.md`](phase2-incremental-startup-batch-plan-2026-09-03.md) 推进；第 1 批 `core-current` 已实际启动，并于 15:04:20 同时到达 `Frontend` 与 `End loading of history`。该批启动层为 `STARTUP_GREEN`，但整体报告仍为 RED：observer coverage 只报 `heartbeat_not_observed`，`error.log` 同时记录 projection-missing symbols（含 `Unknown effect`/trigger 等）。因此当前分类是 `STARTUP_GREEN / PARSER-或-PROJECTION_RED`，不是完整功能 GREEN。旧 `4ff` preflight 的 `ck3_launch_attempted=false` 仍只算启动前配套 RED，不计作 CK3 启动失败。

### B1 effect 拆分最新实机边界

未改写的 58-file、单 effect full B1 仍只有一次 `1205.343 s` pre-menu RED。随后 all-stub（255.113 s）、left-real（180.403 s）、right-real（178.968 s）、event-root closure（181.360 s）、excluded-A（193.588 s）、excluded-B（184.817 s）以及 all-but-76（保留 77 个真 block 中的 76 个，171.228 s）均取得 full-entry GREEN。

进一步的 `balanced-files` 候选没有 stub，保留全部 77 个定义且逐 block 正文字节与原始 effect 一致，只把单文件拆成两份；它为 59 files / 7,858,264 B，两份 effect 分别为 255,134 B 与 240,709 B，并在 180.396 s 取得 full-entry GREEN。在该诊断时点，拆文件已是可实施候选但尚不能唯一证明根因，也不能把原始未改写 full B1 改写为 GREEN。后续 seed-entry r2/r3 与 no-self-call 对照已将更大候选的实际故障定位为 direct effect recursion；canonical seed 也已由 r9 提升为 ready。素材门仍未通过，真实 footage 保持 `0/8`，两条 MP4 仍不存在。

本段记录的 open_kaishek 单文件 parser smoke 仍只属于当时的离线结果，不能作为 B1 语义或 CK3 native/runtime 证据。其“G2 暂停”状态已被 2026-09-04 的 default-production live GREEN supersede；最新边界见下方 G2 增量。

### 正式 B1 generator split 与 r3 验收

正式生成器已将 B1 effect 物化为两个文件，分别包含 `41 + 36` 个定义；候选为 **59 files / 7,858,254 B**，全部定义按顺序重组后的正文与原始单文件 **exact**。formal tree SHA-256 为 `9EED00504E1AAF34F352B440CFB4DFEBF3BB1206966457834727A81BAB4FC50A`。

r1/r2 均在约 0.3 秒因 probe game-path 配置错误结束，`ck3_started=false`，只保留为 harness/config RED，不计作内容失败。修正后的 r3 用时 **245.770 s**，8/8 entry gates、3 个 game-state markers、material error 0 与 cleanup 全部 GREEN。B1 checkpoint 因而晋级为 **startup/full-entry production-candidate GREEN**。

该 B1 晋级本身不覆盖 delayed-path、seed、生产 OODA 或 footage；后续 r9 已独立关闭 canonical seed 门，但 provider/OODA
与素材仍未完成。真实素材为 `0/8`，两条 MP4 未生成。原始未拆分单文件 full B1 的唯一 1205.343 秒 RED 继续保留；
B1 拆分仍是有效布局，而 seed-entry 对照已把本次更大候选的已定位根因收敛为 direct self-recursion。这里的 `G2 paused` 是当时调度状态，已被下方 2026-09-04 live 增量 supersede。

### G2 default-production truce duration live 增量（2026-09-04）

唯一 fresh default-production 双查询已在 exact CK3 `1.19.0.6` 上 GREEN：artifact 为
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-production-leaf-1941c56-20260904\live-production-leaf-dual-query-r1`，
report SHA-256 为
`AD6EEF83DCCA07C3AE280F01CADE6BBD0C1912FF0E086D797604D5F06C99F7C2`，耗时
151.766 秒。两次 public terms query 在同一 paused frame 上均返回 `evaluated_days=1825`，无 mutation、无时间推进，cleanup 后 CK3/injector 进程数为 0。该结果只把 truce duration 晋级为
`production-live read-only primitive`；actual expiry、proven war-bound loss、decision/action、automatic surrender 与
`GEN-034` 均保持 false/unresolved。紧凑证据见
[`evaluated-days-production-live-r1-green.json`](../../artifacts/g2/2026-09-04/evaluated-days-production-live-r1-green.json)。

### B2 generator 用途分片（2026-09-04）

B2 的 `253,920 B / 152-effect` 旧单体已由 generator 替换为 25 个用途分片；152/152 个顶层正文逐 block 字节一致，每片
`1–9` 个、合计 `250,551 B`，清单 SHA-256 为
`06274A5E0D89EF97C19EF3C099E8AEF946C4153BC78C065EC260806D27F67FAB`。broad/release 均包含全部分片且不含旧单体；
该分片工作包交付时仅为文件布局 `static-ready`；后续 r2 full-entry 结果见下节。完整映射与限制见
[`361-b2-runtime-spec.md`](../../mod_zhongguo_style/docs/361-b2-runtime-spec.md)。

Workforce 的 `4,636,271 B / 324-effect` 旧单体也已由 generator 替换为 76 个用途分片，324/324 顶层 block 逐字节一致，
每片 `1–10` 个且没有超限例外。B2 所需的 40 个 Workforce effect 恰好映射到 16 个完整分片（341,602 B，
extra=0、missing=0）；全量分片清单 SHA-256 为
`E5DD22CEF71D60E069884A27BE924234B4FAD42490AEF2B52B966AFD95585858`。该 owner 分片的独立交付状态为静态就绪；组合 live 见下节。

Workforce 的 `168,729 B / 149-event` 旧 event 单体（SHA-256
`637F65CC72C176E6E19BE982F41B203DC326047939B79A80E5E43D3A9D361EF7`）现也已按用途拆为 35 片，合计 `175,403 B`；
每片 `1–7` 个 event，最小 `349 B`、最大 `16,842 B`，数量分布为 `{1:2, 2:7, 3:5, 4:4, 5:4, 6:9, 7:4}`，
无超过 20 的例外。manifest SHA-256 为
`1E1EEE665105139653BC3D00B092522A41C97FE16164E27ACBDB6FC0C967F8DA`；B2 的 19 个 Workforce event 是其中 7 个完整分片的
精确并集，extra=0、missing=0，不再由旧单体的约 210 个 effect 引用拉回几乎全图。generator `--check` 当前覆盖 120 个输出；
Workforce 主测试 116/116、`test_zg361*` 1265/1265、`test_gen_361*` 107/107、visual/projection 8/8、release 9/9 与
`validate_local.py` 均 GREEN。可复现 release `--check` 为 413 files，manifest `E68E89F3…60B4`、ZIP `4A7C7995…1E67`；
该分片工作包的独立交付状态为静态就绪，组合 live 见下节。

权威固定点仍为 `71 effects / 28 events`，旧 `68/24` 漏扫了 `EVENT = <id>` 参数 ABI。不能把旧的 P2/P3
startup/projection RED 或 stub 候选冒充正式 B2。

### B2 无 stub production closure r2（2026-09-04）

fresh 候选位于 `_runtime/phase2-b2-production-closure-20260904-r2`，由冻结 B1 的 59 文件加 60 个 overlay 文件组成，
共 **119 files / 8,891,635 B**。静态物化与重放先通过 `GREEN_STATIC`；随后 exact 同树已完成 CK3 full-entry GREEN。候选包含 B2 的 25 个
effect 分片 / 152 effects（单片 `1–9`）；Workforce 依赖恰好是 16 个完整 effect 分片 / 40 effects 和 7 个完整 event
分片 / 19 events。三 root 依赖固定点为 71 effects / 28 events，全部 selected events 为 51；没有 legacy monolith、stub、
duplicate、missing callable 或 missing event。

文件边界门覆盖 **B2 起新增的 60-file overlay**：其中 44 个 effect 文件 / 218 definitions，最大为 probation owner 的 15，
且只有它超过 10；overlay 中超过 20 为 0。119-file 整树另继承冻结 B1 的 5 个 grandfathered 超 20 effect 文件：B1
part1=41、part2=36、case_kernel=229、`zg361_effects`=26、`generated_mechanism`=1449。它们不是 B2 新增，且已有
B1 full-entry 证据；因此不得把口径写成“整棵 119-file 候选超过 20 为 0”。绑定哈希如下：

- source tree：`F3B36DFDBE74827FF373B06C7C621D1EC72AA15E575F5ABBF1186E636C625184`
- formal tree：`3DD3DA79F11EC892DF72024E25EE985ACAB26E21FD4C1281C35E5DEB0642C4D3`
- file-list：`6C3FE72E3FBB3E1AB6543BEE9226F24203D1063951999AAF6BD7E9053B7533FF`
- projection：`2C8F0979113F75866191C3AE10C699F3801D83AEF91ADCFD9C4B526B469EAE28`
- contract：`F5BC105C1C3EF8E55E82053F61D3B453E6B92A7E0AE224EDECBD072B6EF49180`

r1 仅作为被 fresh r2 取代的静态 artifact 保留。exact r2 full-entry artifact 位于
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-b2-no-stub-full-entry-20260904-r1`：用时 164.781 秒，8 个入口门、3 条
game-state marker、exact mount、material errors 0、`cleanup.ck3_running_after=false` 全部 GREEN。`report.json` SHA-256 为
`4DAAD3649E4FC37373EF2B95F9DE24FB15D23E1319403F37A89228E4B44674F1`，`complete_entry_map.png` SHA-256 为
`F867A24AE1267BA032BC8CDB2EE623A966FF8E7ED1AE9ED78251B115958F875C`。本轮没有加载性能 RED，所以不做文件边界 A/B。
该时点曾计划直接复用同一 exact tree 进入 seed/paused-native；随后 no-launch seed preflight 证明固定 fixture 还会调用
Incident 与 Workforce 入口，故该计划已被下节的新证据取代。full-entry 不替代 delayed-path 或生产功能验收。

### Incident/X 用途分片与 full-entry（2026-09-04）

Incident 旧 aggregate effect 为 `700,085 B / 124 effects`，旧 aggregate event 为 `8,573 B / 54 events`；它们现在只作为
generator 内存 parity reference。正式输出按用途拆为 27 个 effect 分片与 12 个 event 分片，124/124 与 54/54 顶层 block
逐字节一致，历史 aggregate SHA-256 分别为
`0C228FAABB5F6B7DCDABFD32A071CA82F0C1EF15C08AB0BD07C25AF3A467DACD` /
`49577D5475FBF6B22006021F4FADED2A248C7E193840A283FB043F7AAAC0E091`。所有分片最多 `7` 个定义，无超过 10/20 的例外。

X production closure 精确选择 11 个 effect 分片和 4 个 event 分片，承载 47 个 Incident effects / 20 个 events；连同冻结
case-kernel 后固定点为 `60 effects / 20 events / 6 triggers`，没有 Y/Z 定义夹带。exact 候选位于
`_runtime/phase2-incident-x-production-closure-20260904-r3`，共 **135 files / 9,158,442 B**；source/formal/file-list SHA-256 为
`ACC693206AAA03AEEDFB829911778275ED4D4F2EEF31CF4DCE6DE7D46F34BF3E` /
`AF8F0DECE9477FDD60B6C96D0E09A27BFC9E55CEED40A9804B70ACB986D57A2D` /
`045F56D78FB036CDF69225912F9B046673FCD528E99A69571363133A65EA2262`；projection SHA-256 为
`CF379F38DA8C471DDCCDB6522D7E0864098596737862B5E2A703AECA94E40CB7`。

首次 live attempt `phase2-incident-x-full-entry-20260904-r1` 在 `0.338 s` 因默认 worktree 游戏路径不存在而 harness RED；
CK3 未启动，report SHA-256 为 `1CF7A2B014D8BBD9F39C6D1423B2E39BB5B7BCDBA21D1505CD4CECB7F5DFDC51`。r2 显式设置
`XAR_CK3_EXE` / `XAR_CK3_GAME_DIR` 后，在 exact CK3 `1.19.0.6`、EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 上以 **188.303 秒** full-entry GREEN：8/8
entry gates、3/3 markers、exact mount、`material_error_lines=[]` 与 cleanup 全部通过。artifact 为
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-incident-x-full-entry-20260904-r2`；report/map SHA-256 为
`1D41298B8987AA473304AE70FC53628639DE7700BBE5A9D7484A6BF76F566FE2` /
`F75097D9C20B610F81CA60837DF879865E26866F65AC76E7D40C1DF300C34B2A`。没有加载性能 RED，因此未做追加 A/B。

用途分片与 closure 工具已由 `df77ed636c51c51f99f534d8efbb559b94c639d2` 提交并推送。该 GREEN 只覆盖 Incident/X
入口层；在该历史时点，fixed seed fixture 仍要求 Workforce 的 `zg361_we_open_portfolio_effect`。此前 callable/event-only 扫描的五-root
`2034 effects / 578 events` 与 Workforce root `385 effects / 161 events` 漏掉 court-position definition 的
`on_court_position_*` native callbacks，现已被 supersede。callbacks 对五-root union 净增 `8 effects / 2 events`；单独遍历
Workforce root 时还会从 role-failure 继续进入 probation publish，另拉入 `4 effects` 与 `zg361wpf.1`。
`zg361_we_open_portfolio_effect` 的完整闭包为
`397 effects / 164 events / 6 triggers / 0 values / 2 court-position definitions`；五个 product roots 在 candidate 内的完整
materialized closure 为 `2042 effects / 580 events / 6 triggers / 0 values / 2 court-position definitions`。Workforce root 与
Incident/X r3 provider 的交集为 `83 effects / 22 events / 6 triggers`，故相对 r3 的增量仍为
`314 effects / 142 events / 0 triggers / 0 values / 2 court-position definitions`，新增 loc 为 `28 keys / 5 files`。最终
overlay/candidate 文件数在该阶段尚待 renderer；后续已冻结为 249-file product。Manager 43-effect owner 增量仍为 0，
不在闭包内。原定“物化 Workforce → full-entry → seed”路线已由 r9 完成；当前下一项是 product-only focused
B2/provider。footage 仍为 `0/8`，两份 MP4 均未生成。
## R418 零幸存者 B1 liveness RED（2026-09-11）

R418 在同一 PID 内解除全部已知原版事件阻断后跑满固定 `10190` 天产品窗，B1 仍为 active/state `7`，
roster/processing 均为 `0`，无 pending、reopen 或隔级回调；Central 与 PP 始终不可达。该结果禁止继续延长观察窗。
实机证据、根因和只在玩家请求边界运行的无奖励/无发布退役恢复见
[r418-b1-zero-survivor-liveness-red-2026-09-11.md](r418-b1-zero-survivor-liveness-red-2026-09-11.md)。
R430 已用 fresh production tree 在 148 游戏日内证明 cycle `8/8` 退役为 `state=8 / inactive`，且无奖励、无发布，B1
零幸存者永久卡死升级为 `production-live primitive`。本收据不单独证明新周期 publication；后续只做 P1 evidence assembly，
不重复同 checkpoint 长跑。详见上述专题的 R430 小节。

## R468/R469 Stage 11 短验收

R468/R469 验证了 `f14220f` 的只读快照重绑修复，但同一来源到 10 游戏日绝对截止仍未建立 Stage 11 owner/case/portfolio 身份，现已永久淘汰该输入的 Stage 11 用途。P1 保持 `6/9`，P2 继续锁定。详见 [R468/R469 Stage 11 短验收与来源淘汰](r468-r469-stage11-source-disqualification-2026-09-12.md)。

## R487/R488 Stage 10 固定尾链边界 RED 与修正

R487/R488 首次正式动作在旧 30 游戏日绝对边界保留 RED：11 次观测均为 B1 active，Central/PP 均未开启，`.120` 未出现。冻结 save 的通用离线队列检查确认来源已经位于 B1 `D+299`，下一事件 `zg361b1.102` 在次日；此后产品还要执行 `.103 +30d`、公共合账、经理公示回调和五级 F 票据。因此该失败来自验收边界短于固定产品尾链，不是新的 mod 玩法缺陷。

现行 action 上限修为 45 游戏日；source receipt 升为 v4，同时绑定 R488 live B1 初态、exact checkpoint 的 `.102 +1d` 队列和固定尾链说明。修复只做聚焦 normal/optimized 测试 `10/10`，不扩成长期 runner。当前两轮均已终止，CK3 与 Operator MCP 为零；P1 仍为 `8/9`，P2 仍锁定。完整证据见 [R487/R488 Stage 10 边界 RED 与修正](r487-r488-stage10-bound-red-and-correction-2026-09-12.md)。

## R489/R490 Stage 10 校准尾链边界 RED 与 v5 修正

R490 的唯一 gameplay 实例通过 loader/native/exact-mount/error 门后，在 45 日绝对上限保留 RED；16 次观测均为 B1 active，`.120` 未出现。live 日志已经记录有效共同上级合账并进入 pending/reopen，且没有 manager-calibration stale，因此这不是新 mod bug。冻结 source 的 `m142=1 / m143=1` 使保守最迟路径从 D+299 延伸到 D+403：31 日 pending watchdog、30 日 reopen、`.90 +1d` 和五张逐日 F 票据都必须计入。

现行 action 上限为 120 日，receipt 为 v5，同时 hash 绑定 R488 的 30 日 RED、R490 的 45 日 RED 和 `.102 +1d` 队列；104 日源码上界之外只有 16 日调度余量。聚焦测试通过后只执行一次新轮次，不恢复 400 日完整 B1，也不允许原位 retry。R489/R490 均已终止，CK3/Operator MCP/端口 `12441` 为零；P1 仍为 `8/9`，P2 仍锁定。详见 [R489/R490 校准尾链 RED 与修正](r489-r490-stage10-calibration-tail-red-and-correction-2026-09-12.md)。

## R491/R492 Stage 10 外来 roster 产品 RED 与修复

R492 的唯一 gameplay 实例在 120 日内完成 40 次观测，已出现 7 次 publication 和 10 次 final-callback compaction failure，仍保持 B1 active、Central/PP false。这证明失败来自产品状态机，而非观察窗不足。冻结 source 的经理 `29037` 持久 subject 列表有 29 个存活引用，只有 6 个属于当前 `29037/17/17` exact tuple；其余 23 个已属于经理 `29628` 的 case `19/19`。旧 prune 只按存活过滤，使 subject 与 processing 域永久分裂。

最小修复让 subject 和 processing 两个列表统一按 owner、subject、cycle、case、active、roster exact tuple 清理，缺字段 fail closed。B1 runtime normal/optimized 各 `76/76` GREEN，没有额外 CK3 长跑。R491/R492 均已终止，CK3/Operator MCP/端口 `12442` 为零；P1 仍为 `8/9`，P2 继续锁定。旧 v5 receipt 已失效；路径无关的 `ck3_character_scope_offline_v1` 报告和 v6 receipt 已生成并通过生产 validator，下一步只执行一次新轮次复验。详见 [R491/R492 外来 roster RED 与修复](r491-r492-stage10-foreign-roster-red-and-fix-2026-09-12.md)。

## R493/R494 Stage 10 原版强制退休来源 RED

R494 在修复后产品树与 v6 receipt 上通过全部启动门，并在 source 后第 88 个游戏日遇到原版 `ep3_interactions_events.0630`。该事件唯一按钮本身执行 governor resignation/title transfer；现有通用合同正确保持暂停、没有选择并返回 `SCENARIO_INVALID`。失效前有 29 次观测、7 次 publication 与 1 次 compaction failure，但官职与 roster 即将被原版改变，故 `.120` 产品结果为 `NOT_EVALUATED`，不能判定 B1 修复成败。

该来源已永久淘汰，禁止重试、延时或绕过事件。R493/R494 均已终止，CK3/Operator MCP/端口 `12443` 为零；P1 保持 `8/9`，P2 继续锁定。下一步仅离线筛选新的 active B1 玩家经理候选，通过准入后再做一次有界来源捕获。完整证据见 [R493/R494 原版强制退休来源 RED](r493-r494-stage10-governor-retirement-source-red-2026-09-12.md)。

## R494 替代 Stage 10 来源离线筛选

R494 的 `1068.1.1` 自动存档仍是 single-player READY，且已运行 exact-roster 修复。新的通用 `ck3_character_scope_discovery_offline_v1` 在其中找到 18 个 B1 root；11 个候选的 subject/processing/exact 域完全一致。下一次 source-capture 选 `27181 -> 36354`：其 case `5/5` 有 5 个 state-7 exact subject，五个 `.122` 都在 30 天后，且域内不含会在 23 天后被已知 `.0630` 移除的 `29037`。拓扑中的直属有地封臣总数为 7，不能与 5 个 exact B1 对象混写。

该选择已通过新的 `managed-autosave` 无启动准入：凭据统一绑定来源 activation、loader GREEN、场景 RED、checkpoint-bound topology/discovery/queue，定向普通/优化测试各 `5/5`。它仍须零时间推进完成 exact-build 玩家切换、campaign-root 复核和 MCP 原生保存后才能签发新 receipt。原版退休 law 5 对所有 governor 都满足年龄触发，因此不声称候选免疫后续事件。P1 仍为 `8/9`，P2 继续锁定。证据与一次性消费层边界见 [R494 替代来源筛选](r494-alternate-stage10-source-screening-2026-09-12.md)。

## R495/R496 Stage 10 ?????? GREEN

R495 ??????R496 ???? gameplay ????????????? `27181`??????? `36354`?tier 4?????? `zg361_on`??? `date_raw=53155680` ???????? MCP ?? checkpoint `50B713F2...C7E4`??? topology??? exact B1 subject/processing ??? `.122 +30d` ?????????

Stage 10 operator ??? v6????????? checkpoint ? v7 receipt `B687CC04...FFBA`?focused normal/optimized ? `4/4` GREEN????? R496 ???? R495 ????????????????P1 ?? `8/9`?P2 ??????????????? 120 ?????? product attempt?????? [R495/R496 ?????? GREEN](r495-r496-stage10-managed-source-capture-green-2026-09-12.md)?

R498 在 Stage 10 source 后第二个游戏日保留新的原版事件 RED `stress_threshold.1011`；B1 仍 active 且 `.120`
尚未评估，所以这不是 B1 产品结论。exact-build 定义与一级压力池调用链已闭合，R498 现场精确呈现 native `0/1/5`，
共享合同选择只改变玩家压力的 authored6/native5，避免 rakish/妓院、reclusive/关系损伤和信仰路线。选择前 artifact
SHA-256 为 `B51B8960...F392F`；合同现场回放 `18/18` GREEN，相关 normal/optimized 测试均为
`59 passed, 82 subtests passed`。本包为 Python-only；当前轮次 R498 保持暂停，提交推送后原位热恢复，不重启、不重发
一次性 `run-stage10`。P1 保持 `8/9`，P2 保持 `LOCKED`。完整记录：[R497/R498 `.1011` RED 与合同补丁](r497-r498-stress-threshold-1011-red-and-contract-2026-09-12.md)。

提交/兼容同步期间，R498 达到 activation 的 1200 秒托管上限；session report 为
`exit_reason=timeout / elapsed=1206.428s / restart_count=0`。canonical/managed cleanup
`A93FB075...12DD7C` / `F90F824D...E03EB` 均为 GREEN，最终 CK3 清单为空。没有重发 `run-stage10`。
当前轮次 R498 与旧轮次 R497 均已终止；下一次启动为 R499 warmup / R500 gameplay，仍受同一 120 游戏日绝对边界约束。
P1 保持 `8/9`，P2 继续硬锁定。

R500 已实机通过 `.1011` 的 authored6/native5 选择并继续推进 13 日，随后在新的原版诗歌互动事件
`trait_specific_interactions.0011` 保留 RED；`.120` 仍未评估。exact-build 定义、调用链与选项 effects 已冻结，
最小通用合同选择 authored2/native1，避免随机外交决斗及拒绝导致的关系恶化/潜在宿敌。冻结 frame 生产解析器
`26/26` GREEN，normal/optimized 聚焦测试均为 `50 passed, 147 subtests passed` 加独立 `8 passed`。
P1 保持 `8/9`，P2 继续硬锁定。完整记录：[R499/R500 诗歌事件 RED 与合同](r499-r500-trait-specific-interactions-0011-red-and-contract-2026-09-12.md)。

- [R501/R502 travel completion RED and reusable contract](r501-r502-travel-completion-1000-red-and-contract-2026-09-12.md) records the exact-build `travel_completion_event.1000` single-rendered-option boundary, the R502 pre-selection RED, and the campaign-neutral authored1/native0 contract.
- [Stage 10 same-process Python contract resume](stage10-python-contract-hot-resume-2026-09-12.md) defines the `retry-stage10` control, unchanged native-session admission, retained 120-day deadline, and no-reselection boundary.
- [R503/R504 Stage 10 provider-readiness RED](r503-r504-stage10-provider-readiness-red-and-fix-2026-09-12.md) records the real `.120` arrival, terminal F case, over-broad aggregate provider gate, and focused same-process correction.
- [P2 30 日有界跨周期来源 operator](p2-endgame-source-bounded-operator-2026-09-12.md) freezes the current-product route from the R366 Stage 11 near checkpoint to the first real `zg361we.356`, then reuses the canonical same-frame capture and 4/4 registry builder. Static focused checks are GREEN; live capture is pending.
- [R558-R563 campaign-root schema and G2 leaf RED](r558-r563-campaign-root-schema-and-g2-leaf-red-2026-09-13.md) records the stale-DLL schema mismatch, the current-build `direct_landed_vassals_unavailable` collapse, cleanup evidence, and the narrow hash-bound Stage 10 source attestation.
- [R564-R567 promotion paused-wait RED](r564-r567-promotion-paused-wait-red-2026-09-13.md) records the three-span failed take, the obsolete `.147 → comp.1` orchestration edge, and the bounded real `.147 → .148` P2 correction. AF5 remains an independent accepted P1 gate.
- [R568-R571 PP successor live and close RED](r568-r571-pp-successor-live-and-close-red-2026-09-13.md) proves the real `.147 → .148` edge production-live, preserves the three-option `.148` finalizer RED, and records the focused bound-option close correction.
- [R572-R575 PP close GREEN and scoreboard snapshot RED](r572-r575-pp-close-green-scoreboard-snapshot-red-2026-09-13.md) proves the explicit `.148` option-1 close production-live and records the bounded retry for the transient post-close scoreboard snapshot.
- [R576-R579 static scoreboard drain RED and scope correction](r576-r579-static-scoreboard-drain-red-and-scope-correction-2026-09-13.md) records 20 unchanged paused-frame query results, removes the ineffective retry, and limits product-event drain to the event instance that can affect the captured span.
- [R580-R583 four-span GREEN and HC source correction](r580-r583-four-span-green-hc-source-red-and-correction-2026-09-13.md) records the failed take, closes the owner/subject reachability root cause, and replaces passive HC waiting with the registered mature `.356 -> .360B -> .361` product path plus provider-backed typed transition.
- [R589-R593 four-span take and Central summary recovery](r589-r593-four-span-take-and-central-summary-recovery-2026-09-13.md) records the live `.8030` authored4/native3 closure, the fail-closed `zg361p2c.2` RED, and the narrow reuse of the existing Central 1/0 contract while generic single-option clearing stays disabled.
- [R594-R603 reviewed product interruption recovery](r594-r603-reviewed-product-interrupt-recovery-2026-09-13.md) records two further four-span takes, production-live GREEN for `zg361p2c.2` and `zg361.40`, the next fail-closed `zg361.1` annual-summary frame, and the two exact-key P2 allowlist additions.
- [R604-R608 `epidemic_events.1060` scope-variant recovery](r604-r608-epidemic-1060-scope-variant-recovery-2026-09-13.md) records the third four-span take, the exact-build religious-minority-only `faith_to_blame: faith` projection, and the narrow shared-contract variant added while the final-video lock remains active.
- [R609-R613 `zg361.5` elimination-interrupt recovery](r609-r613-elimination-interrupt-recovery-2026-09-13.md) records base-projection production-live GREEN for `epidemic_events.1060`, the next fail-closed player-liege elimination card, and the exact-key reuse of its existing authored3/native2 manager contract.
- [R614-R618 native pause-race recovery](r614-r618-native-pause-race-recovery-2026-09-13.md) records four clean spans followed by a harness RED where an accepted native `already_paused` ACK was rejected before the event-definition query. The focused fix accepts that idempotent success while retaining the existing paused-state, event, date, character and revision stability gates.
- [R619-R623 Career HC chain recovery](r619-r623-career-hc-chain-recovery-2026-09-13.md) records the next four clean spans, strict live replay of the `zg361ch.950` frame, and reuse of the complete reviewed Career HC timeline registry in the P2 product route. The failed take remains uncounted and the final-video lock remains active.
