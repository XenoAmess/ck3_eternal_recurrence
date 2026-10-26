# Java 自动玩家、G2 与原生研究：60 并发续行

machine_id: `xenoamess-full-tower-eb9d2c1186`。记录日期为北京时间 2026-10-26；本文引用的执行时间使用 UTC。当前用户已明确恢复任务，并将并发目标提高到 60；随后要求持续监控、自动调度，开发依赖受限时提高相关原生机制研究并发。

## 当前推进与调度

Root 已建立 60 个独立岗位。实际运行数会随阶段完成变化，累计派发数不作为实时并发。监控先后观察到 42/18、45/15、35/25 的 running/completed，均为 0 error；这些观察没有达到 60 个有效运行岗位。单一调度者逐项补位赶不上短任务收口，Root 随后将岗位分成互斥的 20/20/17 三组，由 native_protocol_identity、readiness、g2_acceptance 分别监控与补派；三个监控岗位另计，共 60 个 worker。每组按 20 秒周期检查，按 60 秒汇报实数。阶段交付后的后继优先修具体生产缺口，依赖受限时研究尚未闭合的原生 candidate、caller、writer 或失效时机。不得将等待、重复核对或已完成岗位算作有效生产。

新源码与运行输出分别位于 D 盘 background/state 根。F78 允许本轮 32 MiB 完整源码峰值；各岗位原帽为 512 KiB，Root 后续从总额内 guard 调拨 auto_loop 增至 768 KiB。Native、SDK、B64、tools 的实际运行分别绑定新的有限卡，暂停前旧卡没有复活。所有旧磁盘 holds 保留，关闭逻辑槽不产生物理释放信用。新文档完整预算 32 KiB。

## 已实际运行的结果

| 范围 | 已观察结果 | 范围边界 |
| --- | --- | --- |
| SDK quote59 | compile02、forecast01、独立 coldread01 均 exit0、Job0、三 MATCH；16:00:19Z 安全闭场，整轮 573.141316 秒 | 仅 FORECAST；不授 SharedQuote、Prepared、sourceIntent 或 Game 资格 |
| B64 | 原 prepare01 不重跑；新 review、batch、collector 成功，3 窗 CODE51/META16 共 67 B，3 attempts、UNKNOWN=0；16:05:52Z 闭场 | raw 已交 M6；采集成功不证明词法、业务单位或游戏效果。闭场 121.498536 秒，超过原 120 秒报价的差额保留 |
| Native helper | 严格 javac 成功；rebind01 因 UTC 表示不满足末尾 Z 合同 RED，rebind02 用同一截止的规范表示成功 | 不延长原整轮截止，不重跑成功 SOURCE/ENV/person 回归 |
| Native Person10 | execute01 实际 configure RED，内层 exit124、Job0；输出目录增长时 allocation 观察的两次 size 读取不同，触发 NativeFactsChangedException | 非 C++ 编译失败；未继续 Ninja。旧输出及 INTENT/失败终态保留，正在修共享可变输出观察路径，冻结 R6 不热改 |

SDK 闭场原件：`D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume60/sdk_execution/SDK-QUOTE59-RESUME60-CLOSE01.json`。B64 闭场原件：同根 `b64_execution/B64-RESUME60-CLOSURE01.json`。Native 新整轮固定为 2026-10-25T15:54:09.110706Z 至 21:14:09.110706Z，失败诊断不重置时钟。

## Java 候选与整图

Council held-read 的 Coordinator、EO、NGT、native port、ordinary policy、archive 及真实 fixture 已分别封候选。NG pending 的真实 codec 必填 step，测试缺字段由 owner 生成独立后继；EO source map 缺 owner 也由后继纠正。新增 callback-only 生命周期限制与现有延后 History 消费冲突，Root 已撤该额外限制，保留原延后合同。

接收链候选覆盖真实 occurrence、HELLO/semantic chronology、真实断链末态、driver latestState、Legacy fixed-clock ABA；保存恢复服务补 snapshot_id 校验。M7 普通恢复入口已接 Natural admission，并以真实选图的 Catalog85 为基线保留 warm evidence。最终退休与下一继承回归仍需要正式整图运行。

正式 release 已有 Java pure projection/受管 Git CLI/共享 manifest 候选，LS 已接原唯一 Guard 的正式有界载荷分支。尚无实际 Git clean/tag、Java quote、发布产物或业务通过。

其他实际候选包括：高位 CUnit ID 保持 BigInteger；战斗状态读取与原 producer 的 OR 语义对齐；WAR_EXIT 提前返回仍消费 M5；历史事件选项拒绝 0 并接受 01；普通 null goal 在恢复准入后的首次鲜观测初始化；月度现金共享合同覆盖 owner、war、单位、scale 与 scope；Halt 失败进入原唯一历史路径。以上源码封存和词法/哈希检查均不能替代 Java 类型检查、编译、JUnit、完整 CI 或 SDK continuation。

Host 持续合并明确 sealed successors，检查 ABI、真实来源及完整峰值。H4 从未物化，H5 尚未冻结；不先编译已知不闭合 H4，也不按 mtime 选叶。SDK minimum 后继必须使用最终 GoalCodec，不能沿用旧 11387 B 或中间 13962 B 版本。

## 新知识的实际边界

- B64 的 51 B 仍未覆盖 numeric callable 的完整分支和返回，不能据此实现猜测 codec，也不能把 raw32 命名为 fullID/token。
- actual4 CampaignRoot 月收入是 gross；当前通道的 owned 账本承诺不能外推原生全部负债。缓存 writer/cadence 必须沿较新来源继续核对。
- 原生路线 ETA 混合当前速率与首边 Unit190 缓存，不能按统帅速度比例缩放全 ETA；及时到场保持独立资格。
- 事件 current getter 返回筛选投影；current ID 改变本身不证明旧对象销毁。选择命令使用捕获的 full ID，仍需闭合实际 erase、分配与序列化 caller。
- 原生婚姻 outer pool 展开后才逐 full-ID 评分，另有 fallback，不能直接充当玩家完整候选索引。
- 玩家改信通知、单选信件、配偶建议与后续家族改信是不同阶段；ACK 或窗口消失不能证明全部效果。
- 存档继承的历史 MATCHED 样本预测距死亡边界 3121 日，不能当临终 fresh；已有 title-holder 查询可以复用，缺的是最终实际 Root 帧的调用、原件捕获与 M3 消费。

完整原件、源码后继与来源 SHA 位于 `D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume60/<owner>/`。已持原件优先复用；必要新源码读取采用明确范围、来源身份和完整资源预算。未运行的项目继续保留 NOT_RUN。新 Java 游戏日、SAVE→restore→NEXT 完成数及 G2 完整实机验收仍为 0、0、0/8。


### 实际更新 2026-10-25T17:15:29.296054+00:00

machine_id: xenoamess-full-tower-eb9d2c1186。Root已冷读工具四阶段报告（9807 B，SHA256 5f28b2366bdf65a992101b6419c2d7aad3256c5a13d22641a0cc0e4eaf34700a）与闭场02（3957 B，SHA256 c90d4572c1530291184febee851417df263d6b74e03e5bb4c7f34781ed10f82a）。Full35严格编译、原R真实adoption、C16严格编译和完整8/8测试实际通过，初次7/1失败原件保留；仅释放逻辑slot2，所有存储hold保留。不授S40、Host或Game资格。

H5唯一Input已实际封存447357 B，SHA256 ee6636a2d85e92033dd5ee9a8a5f2cc712d6b446f933177758b2dd44db38c7de，Root冷读一致；含当前必修ReadContract STATUS_ONLY及原postKnown API，不加入下一批M0/cold/其他新域。已授权slot4在Battle闭场后实际metadata组装与Plan，2040秒原完整窗口，物化/编译须先审实际Plan。R successor默认Maven已实际运行，尚未完整通过。

调度整改：A/B/C三智能体专职监控20/20/17名，暂停自产长研究，完成或报错立即实际followup并复查running，不把派发数当运行数；目标60名工作智能体（含三监控），瞬时完成与补派仍如实计数。F82–84只有限增额与32MiB源额度内部调拨，没有删除或虚报释放。小源新批限479 B/4reads，尚未执行；Native全轮原截止保持不变。


### 实际更新 2026-10-25T17:51:50.257652+00:00

machine_id: xenoamess-full-tower-eb9d2c1186。新 R 已完成默认 Maven 133 suites / 960 tests，0 failure/error/skip；独立 Own39 全量读回和 Source38 两个实际 JUnit（包括 hostname 513 个真实输入）均通过，9 个受管阶段及内层进程均有实际终态/Job0，原 maven01 参数拒绝保留。Root 冷读六个 runtime、阶段终态与全部 133 份原 Maven XML 并重汇 960 项，签发 resume60/sdk_execution/R-ROOT-ADOPTION60.json（4300 B，SHA256 f22d4a14ae1eddd900fed8b14e1414924b0eef80fe152041c5db5a88d9ab1158）。仅采用完整工具载体；不授 Native ENV、S40、Host、SDK、Game 或保存接续资格。

H5 原 Input 的四个裸 owner 在实际 Assembly 中被拒绝；原件保留，正式 InputR2 447376 B / 9d61ca774573084eb81fbd0afe547b401f17c280ad2223a92681ed8bcb9276c9 仅修 owner 元数据，选源字节不变。真实 Assembly/Plan 已通过；Plan 5544309 B / c03983ee22724e3e1158cece56f90192e24f9f4a707426877200f9eefa7b4f23。物化与独立审计均已通过，源 native 含父目录 98404488 B，22 个负例及 manifest/native snapshot roundtrip 通过。原 17:21:04→17:55:04 整轮没有足够完整编译窗口，按 SOURCE/AUDIT PASS、COMPILE NOT_RUN、OVERALL INCOMPLETE 关闭；后续独立 1500 秒 CompileOnly scope 保留原累计墙钟，不能将两段合成原 2040 秒内完成。typed 实际 attempt lease仍由 capacity沿现成生产者产生。

并发持续由三专职调度维持 A20+B20+C17+三调度=60。Root 独立 list 曾实测全部运行，随后三组多次 fresh 复验；完成与 capacity-error 同 agent 实际 followup，不切换模型。F86将常规60源根累计帽统一1MiB，总源包64MiB，新增D hold32MiB；旧占用不重置、22Z不延，source不外推执行权。warcore明确纠正旧512KiB页预算低估，不追认过去通过；新源写依 F86。所有原证据与存储hold继续保留。

Native 在正式新R上5个原helper/source严格编译已实际通过，正在原 whole02 内重新生成 SOURCE/ENV；不热替换旧R消费者。有限原生取源C65实际三窗109 B已闭场，后继C66四窗296 B仅获新资金、等slot2真正空闲后执行。combat四窗479 B多次被准备参数/输出预算拒绝，至本更新尚无业务进程或EXE读取；原失败完整保留，F88独立D执行2MiB明确补足，不能借F86 source-only冒执行预算。

新Java游戏推进、保存日和G2完整实机仍为0；所有NEXT cohort源码候选均保留NOT_COMPILED/NOT_RUN边界。


### 实际更新 2026-10-25T18:37:47.650990+00:00

machine_id: xenoamess-full-tower-eb9d2c1186。本节为最新状态；上文较早状态保留为过程记录。Root fresh list 独立读到 60 worker 全部 running（另有 Root）；A/B/C 仍以不超过 10 秒的实际监控、真实 followup 与复查维持 20/20/17+3。正常数值的消息现聚合为每 180 秒一次，原 bounded state 每 60 秒保留实际点；下降、错误或关键实际结果立即报告。

H5 独立 CompileOnly 实际 RED：FormalReleaseGit.CaptureFailure 缺 serialVersionUID，-Werror 将 serial warning 升级为失败。实际 root/child 已结束、Job0、输入/运行时三 MATCH；reactor 两个成功、一个失败、32 个跳过，不能称其余模块编译通过。旧 H5/c01 原件保留。最小后继 H5R3 只改变 Git.java 的 55 B UID，Input/Plan 仍完整选图 5704 targets、34 modules，含 87 retirement。整轮固定 18:20:36.080261Z→19:20:36.080261Z；F92 独立新 512 MiB hold，不拿旧 hold 假装空闲。物化01 实际超时，5704 个副本已复制但最终 Actual 未产生，按 RED 记录，不手写 Actual。Root 已授权回收仅此可重建失败副本，保留 inventory/copyproof/终态/回收清单后 fresh h5r3b。实际回收采用一次 shutil.rmtree，虽然事先逐件核对与无链接检查，但未按通用策略单批≤1000文件执行；明确记录该偏差，不追认分批合规。后续回收必须遵循精确清单/≤1000批次。新物化不得重置整轮，后继 Audit/Compile 必须消费真实 PASS 并保留充分时长。

Native 在新已采纳 R 上真实 SOURCE、ENV 和 CMake 输出增长回归均 PASS。Person configure 首次 root exit0 但 Job 未在300秒内清空，真实 RED；0/37 EXE、0/39 runs，不继续 Ninja。第一次独立 typedMSVC configure 在 prelaunch image 分块读期间反复 whole census，尚未创建子 Job 即耗时；精确核 root birth/argv 并暂停后确认无 descendants，再仅终止该 root，保留 INTERRUPTED，无不存在的 Job0 资格。第二次缩到真实 mutable research root，预先扣除保留常量输出，固定 18:31:58.953543Z→18:36:58.953543Z 的300秒包括全部准备。实际在18:36:11结束，CMake child13.9524943秒、exit0/noStop/Job0、三 MATCH、typedMSVC NATURAL_DRAIN，forced_cleanup=[]。约252.5秒完整阶段仍如实包含昂贵准备。Native 当前完整 SOURCE 后核与真实缓存封包后进入 fresh Person4500；整轮截止仍次日00:45:15.912008Z，不热改 runtime。

工具整链修复：实际 H5 manifest2168457 B 超过旧 C16 1 MiB 限制，最小候选08改用现有8 MiB严格边界，严格编译/原8/新增3测试真实通过；真 outer 随后 RED，实际 Plan5791 raw selections 与 Audit 正式 resolve后5704 selections比较错误。候选09改为 resolved selections 严格等值，不放松其余来源。原1200秒/独立32 MiB scope内 fresh 重编、完整8/3及实际 Plan/Manifest重验均 PASS，真 projectExisting 外层实际PASS20.1999秒、Job0/三MATCH。该次投影仍含旧 Git 失败源，仅证明生产整链修复，不授 S ready；最终 S 须消费 H5R3 实际合格源码与审计。

C65、C66、C67 已实际闭场；最近 C67 两窗100 B（CODE96/META4）2 attempts、UNKNOWN0、完整durable结果、Job0/三 MATCH，closing43.035168秒，30 MiB磁盘 hold 全保留，仅归还 slot2。Root 已选新 batch02 的正式10精确读取7267 B，原 mapper/冻结EXE/R6，不加窗口；执行新 D8 MiB（含 TMP2）/Z139264 B 经 fresh finance 后方可起固定900秒整轮。源预算总64 MiB内，F93 Auto+64 KiB、当前 M5 必要线程修复另+128 KiB均为内部guard重分配，期限仍22Z；执行预算与source不得互代。

首次实机的剩余硬前置：H5R3实际Java宿主编译与必要运行产物；Native完整构建/回归与独立生产构建；最终S/SDK真实四软件夹具及完整必要验收；Java PROFILE_STAGING实际载荷和运行配置、目标机器版本与新鲜后台Steam离线准入。旧dist实际不符合manifest，不能复用；PROFILE recipe不是actual input。软件通过后方进入罗贝尔1066短场：真实观察→决策→原生后态→日期推进→普通SAVE→restore/NEXT。NEXT全域候选和全部研究不是当前55 B修复图的隐藏前置，但必须另行验收。当前新增实机天数/SAVE接续/G2完整实机仍为0/0/0/8。

## 2026-10-26 度假最终停工补注

用户要求收尾并写交接；60个子智能体全部completed、0 running、0 error，三路调度停止补位。此处completed只指岗位收尾。Host H5R4最终编译30成功/1失败/4跳过，6个测试编译错误；JUnit未运行，SERVICE未产出。工具R实际133 suites/960 tests通过；Native两次4 GiB Person失败、8 GiB重试未启动；S为0 JVM/NOT_RUN。首次实机新增天数/SAVE接续/G2完整验收仍0/0/0/8。

本文较早的活动队列、H5R3及S/SDK前置描述被[最终交接](../handover/2026-10-26-java-g2-resume60-r4-vacation-final-handoff.md)和[来源索引](../handover/2026-10-26-java-g2-resume60-r4-vacation-final-source-index.json)取代。全部WIP/原件/holds保留，释放额度0，期限不延长；必须用户明确恢复，不自动继续。machine_id: xenoamess-full-tower-eb9d2c1186；补注为实际停工后的记录，不倒填已举行会议。
