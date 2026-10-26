# Java 全能力迁移、G2 八专题与 56 并发：R4 度假交接

用户于 2026-10-25 要求提高并发，随后明确要求“你要去度假了，生成交接文档到 docs”。本文件是本轮接续入口。机器为 `xenoamess-full-tower-eb9d2c1186`；主目录 `Z:/ck3_mod_rewrite`。时间均为 UTC，北京时间加 8 小时。最终观察时间、文件长度、完整 SHA-256 和各执行者收口证据见配套 [精确来源索引](2026-10-25-java-g2-resume56-r4-vacation-source-index.json)。

## 接手先看这几项

1. **长期目标未完成。** 完整迁移 Python 自动游玩能力到 Java + Maven + Quarkus，然后以 Java 从 1066 罗贝尔完整普通规划继续实机；持续完成 G2 的 8 个 M，并落入 Java。实际新 Java 游玩、保存日和 SAVE→restore→NEXT 都为 0；G2 完整实机验收为 **0/8**。没有可靠总能力分母，不能把源码/文件比例写成迁移百分比。
2. **已按度假指令停止新增业务执行。** 子执行者在安全边界收口；不能因旧卡尚未到时就自动继续。源候选与运行证据保留，未完成的接口方案明确记为未实现。Native 最后 person 回归已实际 5/5 PASS、0skip、Job0；Native/B64/SDK/CB 四执行槽均已取得各自关闭依据，Root 已解除逻辑占用，磁盘 hold 保留。不能从外层工具成功推断 Job 已结束。
3. **R 工具载体真正通过；S、Host 全图、完整 CI、SDK 真装配和游戏没有通过。** R 的 957 个测试不能替代整个自动玩家；H4 未物化，H5 未冻结、未物化。不要先编译已知 ABI 不闭合的 H4，再复制一轮 H5。
4. **48 个独立源码任务确实已派发。** 本轮按原 56 owner 分工扩并发，已完成无缺口任务自然退出，多个实际缺口已有 Java 候选。不能把累计派发 48、已完成、等待或模型容量错误，算作当前 56 个有效生产者。
5. **不改主树既有工作、不复活旧身份。** HEAD 为 `4a999f3ef5aa6770345832ed6a3ed47602c3c4f4`；本轮收口前主树有大量既有 dirty/untracked，staged diff 为空。未 commit/push/reset/stash/clean/merge。交接两件新文档是本次明确要求的新增输出。

## 路径、机器与执行约束

| 简写 | 本机实际根 |
| --- | --- |
| `J` | `D:/codex-ck3-demos/2026-10-22-java-phase1` |
| `R3` | `J/scratch/resume-current-20261024-r3` |
| `TEAM` | `D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025` |
| `SOURCES` | `TEAM/sources` |
| `SC` | `TEAM/source-bank-controls` |
| `H` | `J/build/resume-current-20261024-r3/source_graph-complete31/plan/H` |
| `TEST` | `D:/ck3-state/ck3-java-g2-r4-tests` |
| `RSTATE` | `D:/ck3-state/ck3-java-tools-r-r4-20261025` |
| `SSTATE` | `D:/ck3-state/ck3-java-tools-s-r4-20261025` |
| `I` | `TEAM/integration-controls/sdk-plan-inputs32` |
| 待生成的 Host canonical repo | `D:/codex-ck3-demos/2026-10-25-java-g2-complete31-r4` |

- 先阅读项目 `AGENTS.md`、[通用存储策略](../storage-retention-policy.md)、其 JSON 参数和 [C→D 迁移报告](../storage-migration-report-2026-10-25.md)。R3 的 [度假交接](2026-10-24-java-g2-resume56-r3-vacation-handoff.md) 与 [来源索引](2026-10-24-java-g2-resume56-r3-vacation-source-index.json) 保留原始导航；定向读取自己 owner 和必要依赖，不重新扫描全证据树。
- **禁止 PowerShell。** 工具环境默认 shell 虽是 PowerShell，实际命令须显式使用 `C:/cygwin64/bin/bash.exe`、`login=false`。Windows 工具用 `python.exe`；裸 `python` 可能走 Cygwin，产生不同的机器 ID fallback，不能把它当成本机身份变化。
- 本机身份通过 `python.exe tools/ck3_live_run_id.py machine` 重新取得。Java 21，命令行默认 `mvn` 最低 3.10.0；本轮实际默认为 3.10.0，Java 为 21.0.10，安装位置是观察事实，生产命令不得锁绝对 Maven 路径。
- 大型工作树、构建在 D；状态、场次、TMP 在 D。显式传 `--state-dir`、`--userdir`、输出根。不得新建 C 实体大目录、改全局 TEMP/LOCALAPPDATA，D 不足不得退回 C。D 为机械盘，本次迁移不是性能改进。
- 新生产、编排、CI 模块用 Java；Quarkus 作宿主，领域模块不各启服务。不新增 Python 平行业务。既有 Python 用于原生产 oracle、操作与兼容回归，不作为新生产入口。
- Game 动作和账本保持唯一权威；UNKNOWN 不重放。Steam 保持离线，启动前走后台原生新鲜离线探针；不截图、不抢焦点、不切在线、不使用 OCR/鼠标替代原生接口、不恢复退役蓝色面板。
- 本轮原 M1 oracle 工具曾对 `zhongguo_scoreboard_state_contract.py` 做同字节写入：18067 B、原 SHA `afe199408d36dfc28980e3588e1832aa27715a3a90572ae7200bbbd6a935d9bd`，内容一致但时间/原生身份改变。不得恢复 mtime 或沿旧 guard 追认身份；保留事件并重新取真实 guard。Git index 在 status/同字节写过程中也刷新过，不能声称二进制未变；staged 内容仍为空。

## 已取得的真实验证

| 范围 | 实际结果及限制 |
| --- | --- |
| R 通用 Tools 载体 | 默认 Maven 132 suites、957 tests，failure/error/skipped 均 0；完整 Own39、Source38 实际 2 项 JUnit 通过，全部 Job 0。Root 独立冷读 build/Own/6 runtime 匹配。只授通用 Tools、SourceGraph、原生共享命令 2048 范围。 |
| R 完整耗时 | 从 11:36:03.712777 到 13:18:58.925070，共 6175.212293 秒，包含等待、原 Own36 角色不匹配失败、真实 consumer 升级和闭场。不能只拿成功子进程耗时报告效率。 |
| Accounting42 | 原 17 项全通过；真实 narrow DACL fixture 修复，不放松生产守卫。 |
| M5 wire | 真实 18 wire→32 Java/runner→原 3 项 JUnit 通过；仅软件范围，不是游戏验收。 |
| RF61 / RF62 | 原 45 测试、prepare 与 148 census 通过。RF62 420 META 字节、35 次读取、36 次比较；独立 public verifyComplete 在新 600 秒窗口通过。旧 900 秒闭场失败保留。 |
| A63 | 仅新 CODE15/META4 的实际采集 3 child 通过，95 新 refs 匹配；715.31 秒整轮通过，真实闭场约 213 秒大于原关闭预估，不隐去。numeric15 只是 prologue/fallthrough，normalize 仍有原生缺口。 |
| M1 PURE66 | 11 个 normalizer 主体严格编译通过。完整 1270 oracle（115 成功、1155 错误）+90 早期错误+7 Java 方法尚未跑实际 JUnit。 |
| FH4 | decoder16 严格编译与原 5 项 JUnit 实际通过；研究软件范围，精确 CRT/runtime base/input 仍 UNKNOWN。 |
| CB timeout44 | strict 69 classes 与原 2 项 JUnit 通过。共享服务显式允许 3600 秒、CLI 默认 900；JNA fixture 真实修复，未运行完整 CI。 |
| Native10 | SOURCE 5520 文件物化与实际 ENV 已通过；不能替代 configure/Ninja、39 runs、C++→Java、REGISTER、profile 或 Game。最后 person regression 实际 5/5 PASS、0skip、Job0；尚未采纳到后继运行时，关闭证据见索引。 |

R 交付原件为 `RSTATE/controls/input01/R-ACCEPTED-DELIVERY01.json`，17186 B，SHA `fc7a6e54c39becf0a5cd6c0565f648bf6d7f19d04018b3aac23c3c1c22a6b0ba`。实际 build 为 `J/logs/build-java-tools-r-r4.json`，170091 B，SHA `a94c04db04d3e9ebf982dc846f0ddae0e7234b8f0cb2da6e5dfad382dac20c4f`。完整原件引用均在索引。

**R adoption adapter 尚未生成。** `Full35CompileOnly.requireAdapterMetadata` 要求 `qualified_whole_build_receipt_ref`、`qualified_own_archive_actual_ref`、`complete_runtime`。R wrapper 前两键不满足，不能把 wrapper 直接塞入该合同。下一轮用实际 R build、实际 Own 和同 6 runtime 生成明确限域的 typed adoption metadata，并让现有 qualifier 检验；不手写通过或冒称 CI/S40 资格。

## H4、H5 与 S 的精确断点

H4 原件 `H/SOURCE08-COMPLETE-INPUT31H4.json` 为 414020 B，SHA `37e97889c9b7d8f286d7d2d655c4bb069a2bf4f78f9c1c4e9cb294cfbbeeb326`；5632 targets、58 owners、155 layers、87 moves、34 modules/35 projects，Tools 306 targets。H4 从未物化/JVM。原 source 含 canonical 父目录占 97619968 B/95 MiB，snapshot 100495360 B/96 MiB，完整 prepare 4190208 B/4 MiB，接近原帽。

H5 由 `host_graph_current` 在 RAM 定向合并本轮候选；不是已冻结包。初批 22 maps/62 refs、1727033 源码字节冷读匹配，计算 5645 targets，含父 source 97828864 B 仍低于 95 MiB；snapshot 100704256 B 已比原 96 MiB **超 40960 B**，不能切掉原 overhead/reserve 来假装合规。最终候选表/未到件/实际是否保存 draft 见索引 Host 收口。

- canonical Tools projection 必须在真正 H5 `repo/java/ck3-control/build-tools` 上生成零 payload 的 existing-source-map，原 source/destination pins 双向绑定真实 Plan/Audit/NativeSnapshot。不能复制另一棵 10 MiB S tree 后，把 pins 冒称 canonical；ControlCi 要求 Tools 与实际 sourceManifest/pins 一致。
- 最终投影 production 是 `canonical_tools_projection46/IntegratedToolsSuccessor16.java`，54636 B；测试 winner 是 **48**，`canonical_tools_projection48/IntegratedToolsSuccessor16Test.java`，43124 B。47 是保留的中间后继，不能按 mtime 取错。46+48 的精确 delta refs 在索引。
- H4 军队 ABI 不闭合：旧 decoder 六参/Selection 三参与新版 Service 七参、Capture、Native/Driver generation、deferred/failure 混用，PairedQuotes/Routes/Reconciliation/PublicWire tests 也受影响。`w56_native_army` 已做现成 cohort 整组接线，结合 window_failures03、Military14、Launcher22、CommandOrigins29、NativeProtocol29/commander28；不能只补一个 decoder。最终 23 target join 与已有旧测试调用适配见索引，尚未编译。
- 同时纳现成婚姻 LS `R3/family_ordinary/marriage_fault20/SOURCE-DELTA20.json` 与 NT `R3/m1_research/marriage_fault41/SOURCE-DELTA41.json`。两原件重新冷读匹配，本轮不重复复制，Java/JUnit 尚未运行。
- Source40 的 Own consumer 明确要求 40 roles，含 `SOFTWARE_FIXTURE_INPUTS`；R 的 Own39 不给新 S 授权。正式完整外部 Own40 为 38123 B/SHA `91548c5d7ad132e903383f7251b508770d246871abc69aba37d1dac3b0ba0d51`。
- S 未开始：**0 JVM、0 业务 child、没有 source/build payload、没有执行 run terminal**。state 最后观察 45056 B，只有 controls；三份实际 quote 已封，但 future 5100 秒、whole6300提案未执行/未采用。5100 秒含 strict addon120+完整 C16 test120+Maven3600+Own180/240+post120 等，不能删项塞进不足剩余时间。
- F75 的 funded 起点 14:29:11.120202、终点 16:04:11.120202/5700 秒包含准备等待，不能恢复时重置钟；16:14:11/6300 是后来尚未采用提案。下一轮重新核整个已冻结 H5、全部 hold、足额整轮时间和资源，再发新实际有限执行卡。

## 扩并发的产物与尚未落地部分

实际 grant 为 `TEAM/parallel56/WAVE56-SOURCE-GRANT01.json`，5545 B，SHA `cc71c31078576c10d3614b956aeb62ac5c6ab203978dab910b0fcd56553b0629`；48 owner 各 512 KiB，合 24 MiB，另 control64 KiB，source-only 至 22Z，不授 JVM/EXE/Game。任务定义在同目录 `TASKS.json` 与 `BRIEF.md`。配套索引列每个已封 map、实际 Java refs、PARTIAL 和零改动任务。

已封且有实际代码的主要范围：

| owner | 实际变化；全部新 Java 编译/JUnit 仍 NOT_RUN |
| --- | --- |
| auto_loop | 批后分析入队失败不再覆盖原退出码、超时或 planner 终态；原 Controller 扩 5 回归。 |
| construction / finance_ordinary | 战时建设月度预算入 intent→material→ledger；Gift 锁内复验消费封存最低储备而非默认 10M。 |
| driver_history / driver_snapshot / campaign_goals | legacy null/missing 日期保留 Python advisory；普通初始 goal；profile3 正确归一验证与旧 cache 回投保护；真实 create→Driver→focus 回归。 |
| ledger_writer | 真实已提交事件先查重，再恢复 snapshot/index；新请求仍在唯一锁内执行业务 authority/reducer。 |
| known_interactions | retained UNKNOWN 校验当前 actor，保留前任原件；Facade→serde→左侧拒绝/确认通道回归。 |
| native_transport_core | 普通部分报文 IO/中断保留真实字节、原 cause 与 TERMINAL，避免把旧 HELLO 当本次故障。只有已封01；02 未实现。 |
| launcher_refresh | 启动日志测量失败时保真实 injector terminal；薄 PROFILE 路由验证真实 Host 部署后调原 LS61 三阶段，沿用唯一 issuer/Guard，不另造物理 writer。 |
| lifecycle / battle_advance | 军队失败接唯一历史 writer；Halt 日期时序；最终 status 后新事件/战争边界消费；resume 前重验实际最新 speed。 |
| root_assembly / reference_main | 计划 SAVE 接回 RootSession 原保存链；Resume Inputs 在真实 Main/Core 生命周期内消费，不预造绑定。 |
| sway_ordinary | 分段持久化、Start 早期基线、generation0/首次收益/自然终态/Following；采用正式 selected_files map02，不是只有 files 的旧01。 |
| m3_research / m5_research | GoalCodec 矛盾分区/flags/date 消费；M5 普通政策真实消费非主导战争 UNASSESSED 风险，不把无来源项当已评估。 |
| combat_phase | 原 CONTROL 结果进入唯一 cache writer、11 槽、普通 phase/terminal/comparison 与 public64 serde；保 route27/commander28 roles，6 Java/5 回归。 |

以下是**明确未完成的实际缺口，不能从“已对齐接口”推成可执行 winner**：

1. **Council 技术失败延期**：action 6 叶以 `SOURCE-PARTIAL01.json` 保留；native governance 3 叶为 partial；governance 普通政策 map01 已封，但依赖前两者与 transport。`scope.deferReadOnly(...)` 尚未实现。实际 Unknown mailbox 会 poison，且可能禁止 after guard 需要的 nested READ。必须取得真实 held source scope 的 after，不能偷用 before、伪成功、清 UNKNOWN/assignment 或放松业务提交守卫。producer→port→policy 集成测试尚未落齐/未跑。整组待完成，H5 不得只收政策绿化。
2. **receive-bound public revision**：transport 的 `acceptedSnapshotRevision(frame)` / `latestAcceptedSnapshotRevision()` 只完成接口讨论，producer 与差分回归未实现，driver_snapshot 没有02。已封01的 cache guard 不证明 Python ingest 计数等价。
3. **M7 跨新 Game FINALIZED 退休**：NS/M7 两执行者均 0 新 Java/0 新测试，仍是原 `public_cold38`。已定位复用 `context.requireRestoredOrigin(...)` / `RestoreCheckpointService.requireReboundOrigin`，绑定 paired SAVE、前后 owner/actor/run/goal 和真实 restored/current pending clear，才能退休并继续下一继承。UNKNOWN/nonFINALIZED 不退休；不得删历史。下一次需 actual FINALIZED→pairedSAVE→新Game RestoreBinding→pendingprobe空→next continuation 的生产链回归。
4. **正式 Java release producer**：未实现，只有 `reference_main/formal_release35/HANDOVER-PARTIAL35.json`。原 Python 是 allowlist→acceptance 剥离/descriptor registry 投影→实际 staging→format2 SHA/size manifest；Java 已有共享 manifest 消费者和 LS61 PROFILE 物理 writer，不能再写一套无资金 writer。缺原 canonical compatibility registry（当前 `ck3_workshop_mcp/src/ck3_workshop_mcp/compatibility_tags.py` 不存在）、真实 clean/tag `v1.0.2` identity；当前主树 dirty 不能伪造。LS61 的原 profile asset1.5MiB/64files/3dirs/single1MiB 帽不能冒称可容完整 production tree。须同 Guard 的有界正式 payload/manifest 分支真实报价再生产。

已有等价实现、定向核对后零增量退出的 owner 不要为了凑56反复派相同任务。主要包括 command_origins、combat_contract、dynamic_capabilities、effect_observers、event_registry、forecast_kernel、military_ordinary、prisoners、public_mcp、readiness、recovery_junction、save_restore、route_contact、warcore、M0/M1/M2/M4；family/native_family 复用现成婚姻成果；life_advance 的 speed 缺口交 battle_advance 同一实现。

## Native10、B64、SDK 的接续要求

**Native10** 由 `migration_census` 唯一持运行 handles。source15/16、Memory44、financial73/75/76 和完整 11670 秒窗口原件仍保留；原 whole 13:50:41→17:05:11，不授新轮。

- 29 选源、5520 domain/62149511 logical、37 targets/39 runs，5 lobby wire；已保 Native09 bridge/CMake 三处修复。
- SOURCE actual 6851898 B/SHA `66e99288adc56004f640a77f74ed0056cf34e4b3157f43a54cd5a6e508a57aa7`；ENV actual 3693590 B/SHA `adebe6a653345a52cfac6f896b42d569de480513554d26082b4b4a4c5f191b79`。ENV 原四探针 exit0/Job0。
- 真实 person10 问题为 Optional explicit null 缺 codec，原消费校验也拒 managed heap/UTF8/implicit-none 新 argv。修入共享 pair+原 producer→consumer 回归，source28/fix02 原件保留，不改 R/27。最后 person10-regression02 已消费真实终态：5/5 PASS、0skip、exit0/stopnull/Job0。2生产源与2测试源严格 javac 通过，修复尚未被后继 Host/runtime 或持久 CI 采纳；不能称 R 已热修。精确修复选源与回归终态见索引。
- 度假通知时仅 `person10-regression02` 在途，随后自然完成，session35047 已消费并关闭；15个调用终态已收，14个实际起 child 均 Job0、另1个prechild拒绝。configure/Ninja/39 runs/C++→Java/正式 production/REGISTER/profile 都 NOT_RUN。不得把运行请求 ACK 当编译/登记成功。

**B64** 由唯一 `forecast_envelope` 接任；旧 `forecast_current` 曾模型容量错误，已非运行 owner，禁止双 collector。prepare 在 14:27 真通过且未重复；最后恢复卡只 carry 成功 prepare。停止时没有 Auth12、没有新 issuer/batch/capture，尚无 B64 raw 可给 M6 解码。

- 只允许 selected03 的 3 窗：CODE51、META12+4，共 67 B；不重复 A63 旧 19 B，不做 normalize/M3。
- 请求 1194 B/SHA `544ed70428ce84e71ae3916d6e6b16f0b908eb95504a4de027eefd047fc5dab1`；prepare terminal 246875 B/SHA `e0a08b97017e080e2a0a2c694e352811a3a93ef51443a1363daefdfdb4fcaceb`，outer0/child0/stopnull/Job0/三 MATCH/stderr0。
- 旧 900 秒及 14:36:38→14:51:38 remainder 卡都只是历史有限窗口。接手查 retained actual terminal 与空 capture，再新准入剩余真实链；成功不重跑，UNKNOWN 不重放。真实 raw 到件才唤醒 M6。

**SDK58/59** 四包合同及独立 Reader 已封，SourceIntent 原35/36未改，DataReview39/minRequest37 真实存在，目标数据到 26 日08Z、最低源码数273。真正 SharedQuote、1717 sourceIntent prepare、metadata/runtime 装配仍没执行。

- quote59 只编 full Assembly+Producer+Reader→forecast7 metadata→独立 cold read。FORECAST 不能写成实际 SharedQuote/正式包。
- 唯一 compile01 实际 RED：child1/stopnull/Job0/前后及 runtime 三 MATCH。缺的是 K 旧运行图没带 **H4 已有 ProjectStoragePolicy**，并非需要改58/59业务或放宽 storage guard。加入该真实 prototype 源闭合编译。
- 最新已发残余卡03为 14:40:22→15:00:22/1200 秒，但仅 standing03 metadata，**compile02 未创建/未启动，forecast/coldread NOT_RUN**。已停、无在途 child。卡与全 closed refs 在索引，恢复不能自动续。
- `I` 完整 future 3792896/3801088 B，仅剩8192 B，勿塞大新回执。源码 views128MiB、delta204589569、service future upper640MiB、CI artifact1GiB 都是范围各异的报价，不能当已测实际占用。

## 财务、容量与保留

最后 F76 加本次新交接文件 Z 盘256KiB预约：R3 holds **7171235840 B**/Root ceiling12GiB（12884901888）；D holds269153665916、required359347979132；Z holds6070996992、required49020669952。14:49:38Z 原生卷身份、4096簇及全额配额检查 PASS；无删除信用。Root ceiling 到26日08Z只是上限/复核，旧 scope、卡、source22Z不自动续期。

- F76 Host455MiB，controls24/plan16/prepare6；source95/compile336/snapshot96 未改。snapshot 的新超额待真实 amendment，不能拿 metadata 增额替代。
- 本轮 net-new source 32MiB 包含前轮增量与48任务grant；F76时该额度余额4517888 B。全部历史及新增 source 授权合计102408192 B，与本轮增额不是同一分母。reference formal source cap2MiB、source-only22Z。SC 控制区已紧，原wave64KiB控制预算也紧，不在旧根追加一轮大索引；本交接放用户明确要求的 docs。
- M44真实内存：总内层16GiB+outer1GiB，最多4 slots；full CI 单slot最高12GiB，其余一般≤4GiB；每个 child 前 fresh RAM 和 commit 各至少32GiB，保留12GiB+512MiB；m2唯一 writer，Ninja总4。记账许可不等于当前 free，必须重新探测。
- 原 Native09 已 materialize 的96MiB受保护；仅未花1408MiB预约取消。R 原位52MiB有限保留，只取消未花42MiB，无删除和精确物理释放信用。testpool/旧24MiB/SDK12MiB仍占账，Job0不释放磁盘hold。
- 本轮最后 Root 可用容量探针：C193678426112、D641296265216、Z134475812864 B，仅为当时快照；机器已核。容量与 quota、并发预约、系统预留同时检查；不按目录名/mtime直接删，不保留过期资产到无限期。原件有 review/用途，按统一策略复核。
- 新4slot闭场事实、最后实际文件/ref、无子进程的范围见索引。不要写“所有进程已停”来代替逐项证据。

## 接手的执行顺序与时间口径

1. 读本文件与索引 final live/partial，再核机器、默认mvn、实际路径、容量/期限和相关 retained Job terminal。先定向对齐正在收口的原件，未知请求不重放。主树既有工作保留。
2. 直接处理已经定位的共享缺口：Council真实 after/transport、receive revision、M7 retirement、正式 Java release；并复用 Army/婚姻及已封源码。可独立源码并行，不为单一Maven锁让所有owner等候，也不再给等价范围派重复核查。
3. 完成唯一 H5 正式选源，解决全部 producer/consumer ABI 与 snapshot 容量，冻结后一次物化。R typed adoption metadata 尚需补。canonical Tools projection46+48 先实际严格编译/完整测试，再真实 source map；S 完整默认 Maven、完整Own40、Source38 原两JUnit不能省。
4. Native10 从真实成功终态继续，修共用 serde/consumer 后执行剩余原流程；B64 成功 prepare复用，实际67B到件后解码；SDK补真实缺源后执行完整forecast/coldread。这几路与Java源码互不等待，但各自要新实际整轮准入。
5. 用实际 Host deployment/正式 release 运行原 finite PROFILE/启动绑定，取得 Runtime/SDK 真实输入。完整 CI 11阶段需要物理 Game、Core、Pending、Resume 原场景；五软件 G2 provider不产生真实Core/Prepared/ReadInputs，软件9项不能替代11项。
6. 完整普通规划实机从1066罗贝尔开始，确认实际动作后态、新游戏日和保存/恢复/下一阶段；陌生事件原生采集后第一显示项续行，批后离线规则补齐与下一批并行；战争资金/雇佣/贷款/退款仍按原有合法原生观测守卫。

时间只报依赖与整轮预算：S未来5100秒约85分钟（未启动），Native旧整轮11670秒约3小时14分，完整CI合同最低31000秒约8小时37分、最高43200秒；这些不是三段可直接相加的预计交付时间，重用与并行须按真实链判断。当前有未实现和未编译阻塞，**不承诺首次 CK3 实机日期**。下一次有效节点是 H5冻结/物化、S真完整终态、Native剩余链、SDK真实forecast，之后才能据实际失败率给实机时间范围。

本轮没有把48份任务或新回执量当智能/效率，未测完整新增游戏日，不报告秒/日提升。历史进展文档和总线只是各时点记录，本交接与其精确来源索引优先；若后到关闭证据改变状态，以索引所列实际原件为准，不追改旧失败。
