# Java / G2 resume91 休假交接（2026-11-07）

机器：`xenoamess-full-tower-eb9d2c1186`；时间统一为 UTC，本地时区 Asia/Shanghai。配套阅读[源码与证据索引](2026-11-07-java-g2-resume91-vacation-handoff-source-index.json)及[Native 收尾](../native-handoff-2026-11-07-vacation.md)。本交接替代 11 月 4 日文档作为最新入口；旧文档、失败回执和原件保留，不改写。

## 最新指令与实际收尾

用户最新明确：“你要去度假了。输出交接文档到docs.” 当前停止新增实现、编测、本地模型派发、业务 worker、Game/Native live 查询、动作、采样、录制、部署、装载及 GET。只整理已有结果和完成本交接的正常 Git 发表。此前自由使用 CK3 与持续执行的授权保留为历史，不能据此在本次休假期间自动续行。恢复须有用户后到的明确续行指令。

本轮收尾前，各已知工作岗均已 completed，M6 为 provider error；没有运行中的业务岗。本次未发新 STOP、未启动或终止 Game、keeper、Java 或模型请求。**最后业务 Java 已在此前退出，不把本次文档指令说成一次新的成功停止。**

| 范围 | 最后具名事实及边界 |
| --- | --- |
| 自动游玩 Java | PID24536 于 2026-11-06T20:42:09.517668Z 真实 exit4；此后没有新的已登记业务 Java START |
| Runtime 登记 | 2026-11-07T04:42 的有限检查内，已知 build/deploy/recovery 无 BEGIN 未配 END；不代表全机器或其他 owner 的状态 |
| Game / keeper | 04:42:43.690923Z / .691143Z，固定两个 PID 的 OS 身份与出生时间匹配且存活；不是新 Game 状态查询，也不是发文时再次核实 |
| Native | P101 编译和 DATA、P102 基准均已结束；资源槽 LIGHT1/LIGHT2/HEAVY 为 null，无该工作包未闭 JVM |
| Git / 源码 | 两个最新独立单元已于约05:02正常推送；本交接只新增文档，不部署候选 |
| 本地模型 | 没有新增 HTTP；已知源码工作岗已结束。不推断整个模型服务或其他机器的队列为空 |

保留 Game 与 keeper；不为交接触发 SAVE、查询世界、补跑基准或启动恢复。停止请求、进程退出、资源释放和历史 OS 存活核验是不同证据。

## 自动游玩为什么没有恢复

当前运行故障仍未解决：上一次 Sway（拉拢角色）动作处理出现 `integer outside contract range`。父动作已经登记一个子动作，但原执行结果没有完整子动作回执；不能从登记记录推断已派发、未派发或成功。因此调度器要求保留每个原子回执的一致性检查拒绝恢复，原动作维持 UNKNOWN。

| 项目 | 冻结事实 |
| --- | --- |
| Game | PID102152，birth FILETIME `134384631867107774` |
| keeper | PID35300，birth `134384631396059561` |
| 当前 profile / transport session | `resume91_m7_saved1475_20261106T182247Z` |
| 原业务 episode | `resume91_after_user_20261105_01`；与新 transport session 不是同一身份字段 |
| 当前账本 | head47 / repair_required / BATCH_INTERRUPTED |
| 原父动作 | parent46 / COMPOSITE_UNKNOWN / UNRESOLVED；registered child1，原 Run.child=null |
| 原控制期限 | 2026-11-06T21:06:53.1953352Z，已自然过期；保持原值 |
| 当前恢复准入 | NOT_HELD；未启动新 worker，没有新的保存信用 |

已有 target READ 返回 available/legal/can_send，只证明该次目标只读观察，不证明后续动作派发或结果。异常的实际首个字段及完整派发边界仍未被确证。不要把异常文案、缺 ACK、登记顺序或冷读替代原动作的执行/未执行证明。

P100 是这次 UNKNOWN 原因诊断工作包的编号，不是性能百分位。M6 的该诊断任务在 11 月 6 日约21:29被平台返回“possible cybersecurity risk”。这是诊断受到平台限制，不是已确认 CK3 存在安全漏洞。原拒绝保留；本轮没有改述、重投、换岗或由 Root 接续同一被拒诊断链。后继不得用其他独立软件单元绕过该拒绝或取得实际恢复准入。

## 已完成：源码、软件资格、实际运行分别记账

### P101：恢复入口的独立软件资格

生产与测试源码已正式发表 `b51bbb9eb7c2cb7459cc8b99daed5cfb4f2cf55b`。它区分原 Driver episode 与新 transport session，保留旧 readonly 模式空动作检查及新模式的来源/身份检查，不回落到 observed initial。七字段 schema 为 `xar.java-loaded-saved-original-recovery-request/v1`。

本轮七个明确正式 TU 编译 exit0，14.4602343 秒、新88 class；复用此前三个完整 SourceFile 家族46 class，组合134 class 的 API、双向 nests 及 private token 构造器检查闭合。没有删除范围外检查或全树编译。此前六 TU RED 与46部分产物的历史原样保留，不能追认为旧 attempt 通过。

只复用两个已有测试 class，对独立 episode/session 身份及严格 schema 的两个 DATA 方法实际取得 2P /0F/0E/0skip，exit0，5.3743913秒；04:56:08.692151Z 资源释放。**没有执行 Root/SavedLive 图、构造实际私有许可、Native 或 head47 恢复。** 这些通过不能解除 registered child1 的原门。

新资格记录正式提交 `a52ac0cfa14a4f968ec0627c2d0ef8f616e32788`，见[正式 Saved 基线](../autonomous-agent-progress/2026-11-07-formal-saved-baseline-qualification.md)。

### P102：减少同调用重复编码，并完成一次组件测量

生产优化已提交 `be44e4bb7d41331ea9aca121068c1da3536db298`：在同一次严格验证中复用合格 saved Driver 原字节，目标 saved.encode 从两次变一次。只接受固定 decoded 同一对象、非 retained、actor 精确匹配及不超过8MiB等条件；一次消费、finally 清理。外部/retained/不同身份/过大/重复消费走原编码。combined.encode、物理读/hash/ACK/保存校验/lease/current/head 顺序和原 encoder/parser 保持。

此前必要生产与独立测试已通过，本轮仅新编一个手动 benchmark TU，未重新编译生产。单 JVM、CPU1、128MiB、45秒预算；固定1475 Driver与Pair，ABAB再BABA，每模式4个测量样本、另8个预热，全部保留；无强制GC、删慢样本或速度断言。

| 样本（毫秒） | A：原第二次 saved 编码 | B：同调用复用 |
| --- | ---: | ---: |
| 1 | 199.2963 | 187.1938 |
| 2 | 244.8050 | 133.3509 |
| 3 | 192.9580 | 154.8705 |
| 4 | 182.6569 | 147.2337 |
| 均值 | 204.92905 | 155.662225 |

描述性均值差49.266825ms，约24.04%。两模式使用相同测量缓冲生命周期；这不是旧生产二进制、完整 checkpoint 管线或稳态统计对照。全部16次编码 marker 与原 Driver SHA 一致。main 5.2752572秒，managed 进程窗口5.8603287秒，含设置/读取/解码/预热的单独记录保留；VM uptime 不能拿来精确扣除启动。04:52:18.644190Z 已释放资源。

benchmark、分析器、21条原始记录和事实文档已提交 `a7007b1b088eb78c7088f3140c1e62fa40178c60`。见[完整测量](../autonomous-agent-progress/2026-11-07-checkpoint-encoding-component-measurement.md)。**尚未运行采用，不能授整局提速、新增保存日或10秒目标通过。**

P097 正式重复读取优化 `5b18edbcec6ff40eabbdbab7b301bcf453095a77` 也有独立软件通过；已发布候选不等于活跃路线命中或端到端收益。不得为这些候选重启健康 Game。

## 游戏进展与性能口径

最后具名 SAVE_CONFIRMED 为1475，2026-11-06T15:49:08.1922044Z，date_raw53168040、actor31254、C56。对应 Pair 来自旧 Game117900，native1009/public905；不能将这套历史 Pair 身份冒充当前 Game102152 的实时观察。

保存文件83015547B / `333979275a1e808be2cb58e0ac818f98c0e95121e68426a8789bd5cd23a714c3`；Driver5255697B / `092b7df37ab70b5d28981b1c681fbf96cc1e58f0029706bab15fd741adc705f4`。这些是历史已核原件身份，本次不为文档重读大存档。

- 1323起点 2026-11-06T10:54:22.3482445Z →1475：17685.8439599秒/38新增确认保存日＝465.4169463秒/日，是旧封闭切点。
- 同一起点延长到2026-11-07T03:33:45.264918Z：59962.9166735秒/38日＝1577.9714914秒/日；含失败、恢复、研究与跨 turn 等待。
- 1475之后到该切点：42277.0727136秒，新增确认保存日0，秒/日为 null；不能拿旧38日做这个零保存尾窗的分母。
- 03:33之后的交接发文时当前全程秒/日未重算；上述数字不冒充发文实时值。本轮新确认保存日0。

10秒/新增 SAVE_CONFIRMED 游戏日目标未达到。不扩大批步、降低保存/校验频率、剔除失败等待或拿累计历史保存日伪达标。未新增确认保存不等于已证明不存在用户手玩或其他全局活动。

## 功能缺口与接手顺序

G2 最后完整验收仍为6/8；自然 M6 scheme/activity 完整链与 M7 保存、继承、多场景终验未闭。P098 曾实际消除超大 Sway 模型输入，生产请求200且 SELECT/ACCEPT；这不等于自然 Sway Start 成功、终态收益或整个 M6 通过。本地模型既有正式运行期用途，也有离线源码辅助；本次休假不发新请求。

1. **当前只读交接，不自动运行。** 先读本总交接、JSON索引、Native交接；旧11月4日 stopped/BOOTSTRAP 现场不得覆盖本次 head47。
2. 后到明确续行后，唯一 Runtime owner 核实实际 Game、birth、keeper、world/continuity、原账本和 stop 状态；历史 PID 或04:42存活不能外推未来。
3. 先确认允许的故障处理路径。保留 P100 拒绝与当前准入不成立的事实，不用 P101 编译/两个 DATA 通过启动 CLI。不得补写、删除或重排子回执，伪造零写入证明，放宽 Guard，重放原 UNKNOWN，刷新旧 deadline，或清账本。
4. 恢复准入真实成立后，沿既有 Quarkus Dev 架构进行唯一受控采用；源码、编译、实际装载、LOOP、行为、SAVE 逐层验收。没有新 launch 命令或可盲跑脚本在本交接中获授权。
5. 原局正常游玩与P0功能/性能优先；候选采用后检验路线命中和新增保存的完整墙钟。G2/M6/M7按真实自然场景验收，不用软件绿代替。
6. 所有权保持：Runtime 独占 live/Game/keeper/账本/worker/装载/GET；Java负责正式源码与Git；Native负责必要离线编测；Models负责既有模型运营。本机地址记录为 `http://192.168.1.11:8080/v1`、qwen38-coder；休假不探活、不自动回退地址或重投任务。

## 文件与 Git 注意

本交接整理时 `D:/r64d` 的 HEAD 为 a7007b1b088eb78c7088f3140c1e62fa40178c60，**detached且干净**；它不能再按“master开发工作树”模板直接改写。不要为了交接移动冻结HEAD、改租约或重启Game。正式发表由Java owner在允许的隔离目录处理；Z工作树大量既有修改保持，不reset/stash/全量stage。本文不把某个工作树或旧owner名字的存在视为仍在执行。

索引给出有限原件路径、bytes和SHA；它是导航，不发放运行许可。原11月4日交接和索引保留。当前目标未完成；本次是用户要求的休假暂停。
