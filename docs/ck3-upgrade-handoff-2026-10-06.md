# CK3 1.20 维护交接：2026-10-06

## 2026-10-07 用户新指令：缓存验收只核文件与实际加载

本仓库全部 mod 的现在及后续发布使用 [缓存验收新规则](workshop-cache-acceptance.md)：Steam 实际下载文件与正式构建一致，CK3 实际加载这份缓存，即完成缓存验收；不再重复缓存业务、事件、按钮或数值检查，不要求新开战役或进入地图。发布前源码验收继续保留。此规则覆盖下方旧段落、归档操作卡中的“代表业务 cell”“缓存字节及业务实机”等门槛，历史失败不改为业务 PASS。

CCC 1.0.1 已有真实下载的 strict22 一致性回执，并在本机 .4 的 R0014 实际加载该 Steam 缓存，正常 GUI 退出、独立 OS0/native0、清理及 CAS5358 已完成。按新规则收口至其 [永久 changelog](release-changelogs/celestial-commerce-corruption/1.0.1.md) 和 [发布证据](release-evidence/celestial-commerce-corruption/1.0.1.json)；不再启动 CCC 缓存业务复验。R14 点击前的旧模板定位失败保留为当时记录。下方 5/10、CCC pending 和未实机等状态是较早时间的历史截止；最新发布闭环以永久记录实际提交推送为准。后续顺序为 QOL、RMTM、TED、361；具体礼仪仍在全部维护之后。

## 2026-10-07 续办增量（2026-10-07 13:58:13 Asia/Shanghai）

当前用户要求先更新本机 CK3，再同步本机仓库，随后继续全部十产品迁移，保持有意义的高并发。**Step1 本机更新、Step2 仓库同步均已完成；当前正式发布闭环仍为 5/10。** 本段是接手入口；下方10月6日停办、旧版本与旧现场段落保留为当时历史。

本机实际安装为 **CK3 1.20.0.4 / Steam build25734779**，EXE 101040248 B，SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本机 manifest 的下载与 staging 剩余均为0，非零总计是已完成的累计值；[只读安装及队列分类](C:/workspace/ck3-upgrade-20261007/current-install-readonly-resource-01/CURRENT-LOCAL-INSTALL-QUEUE-CLASSIFICATION-02.json)保留边界。root 已一次查验[Steam官方当前 Update1.20.0.4 公告](https://store.steampowered.com/oldnews/?appgroupname=crusader+kings+iii&appids=1158310&enddate=1793516400&feed=steam_community_announcements&headlines=0)，正文将1.20.1列为active development，与本机实际安装吻合。06/08下载过渡原图保留为历史，不能单独证明当前公开客户端版本，也不能以08倒推当时已在线；在线fresh菜单在16。Step1依据官方公告、actual manifest/full installed/剩余0和最终离线亲审。最终 root 于05:47:43 UTC亲审[recovery19原图](C:/workspace/ck3-upgrade-20261007/resume-root-02/steam-final-offline-recovery-19/probe-1/steam-moved.png)为离线，[亲审回执](C:/workspace/ck3-upgrade-20261007/resume-root-02/root-steam-final-offline-review-01.json)已保存，期间未在线启动CK3。

publisher keeper 已真实停止：最后sequence5238、actual session44334 exit0、thread_exited=true；[闭合回执](C:/workspace/ck3-upgrade-20261007/publisher-release-root-01/publisher-screen-closure-receipt-01.json)记录CAS5239/done/resources=[]与当时空进程盘点。root 已从`38b0a986`同步至新origin/master `7d412003f`，CCC永久事实增量随后rebase为`6281813f23b9dbd3e749f933de2bdb2e0dc5d1a4`并普通push成功。发布状态沿用已入库[CCC changelog](release-changelogs/celestial-commerce-corruption/1.0.1.md)及[release evidence](release-evidence/celestial-commerce-corruption/1.0.1.json)：**PUBLISHED_CACHE_ACCEPTANCE_PENDING**；不重发SDK/HTTP，不计6/10。

### 当前续办入口与并发拓扑

| lane / owner | 直接消费入口 | 剩余实际交付 |
| --- | --- | --- |
| 本机共享 .4 native / rules / Python host，各独立owner并行备料 | [本机构建冻结](C:/workspace/ck3-upgrade-20261007/local12004-runtime-build-01/source-snapshot-01.json)、[rules候选packet02](C:/workspace/ck3-upgrade-20261007/ccc-frontend-rules04-candidate-01/FRONTEND-RULES12004-SOURCE-CANDIDATE-PACKET-02.json)、[host产品选择addendum02](C:/workspace/ck3-upgrade-20261007/shared12004-python-host-01/ROOT-HOST33-PRODUCT-SELECTION-ADDENDUM-02.md) | 提交实际 .4 final source-index、DLL/injector及构建回执，绑定各caller；构建输入38b0冻结与当前仓库628提交分列，不以新HEAD重新解释旧输入。当前备料/静态结果不授 .4 实机信用。 |
| CCC，root现场 | 已入库永久记录及上述 .4 host/rules入口 | 已发布缓存的本机 .4 实际业务与正常GUI/OS0验收尚未完成；.3 R0011的真实source业务/正常退出信用保持其版本范围。 |
| QOL，独立caller备料owner | [same-live连续消费卡02](C:/workspace/ck3-upgrade-20261007/qol12004-continuous-prepare-01/ROOT-CONSUME-QOL-SAME-LIVE-02.md)及host产品选择addendum02 | 保留原defense/任命/百万分/宗教slider/自然pending/正常退出合同；使用QOL专属Source09 host33或PAM private host，不用generic H81替代。真实GUI缺项仍由root亲审当前原图，prepared不等于业务通过。 |
| RMTM / TED，独立caller备料owner | [.4消费卡02](C:/workspace/ck3-upgrade-20261007/rmtm-ted12004-prepare-agent-01/ROOT-CONSUME-PENDING-01.md) | 四个新冷profile和连续caller已备料；最终shared binding及实际分配/实机仍待。接续原RMTM14日/core与50/51阈值、TED core Save/Load及UI Send，原预算不变。 |

root 是本机 Steam、桌面、Start、实际游戏与屏幕CAS的唯一操作者；上述源码、host、产品caller与文档lane可同时准备，真实CK3场依旧顺序执行。最终绑定完成后消费已有连续入口，不临场重造平台或重跑无变化检查。QOL/RMTM/TED三产品正式metadata的`.4`增量由`remaining12004_metadata`施工，版本号保持既定值；各产品owner同步新cold profiles，完成后按实际pins绑定，当前只记准备。本机新 **.4 实机仍为 NONE/NOT_RUN**，旧f150 DLL、旧.3通过和静态测试不授新版本资格。远端 **Z机器 R63全原ON范围的实际信用原样保留**，以其owner的current-scope回执为准，不能记成本机实机。

其余未闭环仍为CCC、QOL、RMTM、TED、361；达到原门槛的产品按既有授权逐个发布并恢复离线。361仍最后，廷臣具体礼仪在全部维护完成后处理。已完成五产品和Compatible Version专项100%保持原信用，所有旧RED、raw、冻结输入、DRAFT历史永久保留。

用户于2026-10-06要求：“平稳结束手上每件任务，不要再开启新的任务，然后编写交接文档到docs，提交推送。”本执行者已停止新增场景、清理操作、源码施工和发布。本文是本机最新交接，优先于[10月2日交接](ck3-upgrade-handoff-2026-10-02.md)中的续跑安排。旧记录、失败attempt、原片和冻结输入继续保留。

## 接手摘要

- 正式发布闭环完成 **5/10（50%）**：白绮、自动建造、肃清曼荼罗、牛来、永恒轮回主版。分母是本次全产品迁移清单的十个玩家产品，不含其他机器新增产品，也不是准备完成率。
- Compatible Version专项 **100%**：本轮八个已有公开条目已补标并精确回读；14个builder使用统一映射。361仍声明1.19，不能提前赋予1.20兼容信用。
- 其余五个产品未完成本轮发布：经商贪腐、体验优化、重整河山、驱策朝贡国、天朝361。经商贪腐核心脚本已验，剩余生产UI被真实磁盘不足阻断，没有完整可上传结果。
- 本机没有本轮CK3、验收器、watchdog、keeper或上传进程；最新屏幕释放为 **a77 / CAS4212 / done / resources=[]**。全部团队子线程停止，`main_localization`的服务端容量错误没有重启。
- NVIDIA 793,353,272 B缓存删除入口、H81写错误诊断补丁保持候选状态，未执行／未合回／未实机。首先处理实际空间压力，再补经商贪腐剩余UI；不直接复用已消费的R0004 profile。
- 之前ETA不再有效。下一位接手后按环境恢复、剩余业务通过、单产品发布、fresh cache验收、永久记录推送报告实际节点，本次不承诺下一产品完成时刻。

## 用户要求

优先级：**白绮第一、自动建造第二、其他mod随后、天朝特色361制最后**（用户称“天朝365”对应仓库361制）。前两项已完成，不重跑。恢复执行后保持有意义的高并行；允许root加64个子线程，但本机CK3、桌面和Steam上传只有一个实际操作者，不为填满槽位制造工作。

用户已授权达到门槛的产品逐个上线，每个产品立即发布并恢复Steam离线，不等全部产品。“不要开启CK3，我自己要玩”针对另一台机器，用户已明确不约束本机；本机仍遵守离线与共享账号占用合同。本次收尾指令生效后，本执行者不自动继续未完成产品。

低优先级功能已登记到[产品任务清单](product-technical-roadmap.md)：白绮和主版创建廷臣时，选择信仰之外增加具体礼仪选择；**全部mod的1.20翻新维护完成后才做**，不扩入当前发布门槛。

本项目的 Windows 命令仅用 cmd.exe 或 Python；只用fetch/rebase/普通push，禁止merge/force-push。所有过程资产永久保留，原日志、聊天历史、存档、失败场和构建输入不能作为垃圾删除。

## 已完成发布

| 产品 | 版本 / Workshop ID | 永久依据 |
| --- | --- | --- |
| 白绮独立版 | 1.0.2 / 3787304042 | [changelog](release-changelogs/vivhite-courtier/1.0.2.md)，单独及双加载顺序、业务、完整Notes、fresh27、离线和master闭环；原回调超时保留，以公开和下载独立确认 |
| 自动升级建筑 | 4.0.3 / 3800124956 | [changelog](release-changelogs/auto-upgrade-buildings/4.0.3.md)、[证据](release-evidence/auto-upgrade-buildings/4.0.3.json)，核心/继承、六图标专项、Notes、fresh17、无ID重建、离线和master闭环 |
| 肃清曼荼罗 | 1.0.1 / 3797711947 | [changelog](release-changelogs/remove-mandala/1.0.1.md)、[证据](release-evidence/remove-mandala/1.0.1.json)，.3实机、Notes、fresh15和永久记录完成 |
| 牛来 | 1.0.3 / 3790635143 | [changelog](release-changelogs/ox-here/1.0.3.md)，生产拒绝/招募及原12标记通过，Notes、fresh22、离线和永久记录完成；harness frontend查询RED保留 |
| 永恒轮回主版 | 1.0.2 / 3784706360 | [changelog](release-changelogs/eternal-recurrence/1.0.2.md)、[实机范围](ck3-1.20.0.3-eternal-recurrence-readiness-2026-10-05.md)，Writer/Reader/Creator、R20无嗣八值和正常退出、Notes、fresh86、离线和永久记录完成 |

完成仅覆盖各changelog明列范围，不等于所有GUI hover、其他mod组合、旧存档或多人均通过。旧DRAFT/RED段落仍是历史，以前面的实际发布增量为准。

Compatible Version规范见[workshop-compatible-version.md](workshop-compatible-version.md)，实施提交`f8bbcb849`。统一表映射1.20→`1.20 'Crozier'`，未知minor在发布前拒绝。builder和native从实际staging派生标签，保留其他标签原字符串和顺序，包括`Balance `末尾空格。[元数据修订](workshop-metadata-revisions/)保留八项匿名sidebar/tags和Notes未变证据，无需再补标。

## 现场、工具和资源

仓库：`C:/workspace/ck3_eternal_recurrence`。解释器：`tools/.venv/Scripts/python.exe`，已核Python3.14.7。实际游戏：Steam **CK3 1.20.0.3 / build25652598**；EXE SHA-256 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`；安装`C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III`。

本机实际总线为`C:/workspace/.codex-task-bus/bin/codex_task_bus.py`，旧指南D盘路径不适用。**09:47:05 UTC / 17:47:05北京时间**的[进程盘点](handover/2026-10-06-ck3-upgrade-handoff-artifacts/actual-local-shutdown-inventory.json)为空；C盘空闲 **3,592,962,048 B（约3.35GiB）**，这是停机后快照，不是故障瞬时余量。

[R4闭场回执](handover/2026-10-06-ck3-upgrade-handoff-artifacts/ccc-r4-red-and-cleanup.json)证明game16840/harness14404/watchdog21768原身份gone，job0/treegone/cleanup、control files全absent；keeper7339实际exit0，末seq4211后完成[CAS4212](handover/2026-10-06-ck3-upgrade-handoff-artifacts/ccc-r4-screen-release.json)。Native退出1保留，不写正常GUI退出0。

总线没有活跃`ck3-screen:acquired`声明。九条属于本轮的旧root/白绮/361普通任务补写done/resources=[]，[实际闭合索引](handover/2026-10-06-ck3-upgrade-handoff-artifacts/actual-nine-old-owned-task-closures.json)记录seq4214–4222；这是执行收尾，不授361实机通过。历史已退休屏幕waiting/RED继续保留，不修改其他机器任务。integration任务`ck3-upgrade-maintenance-integration-20261006`在本次push后写done释放自己的origin/master；最终回执存于`C06/root-vacation-handoff-20261006-01/`。

最后亲审的Steam离线原图是R4启动前，操作者`/root/ccc_ui18_foreground`检查recovery/challenge2，nonce `cd0206b1c1c6`。此后没有切在线、重启Steam或发布；**下一场仍要新的离线审阅**，不能复用旧截图。本次未改分辨率，接手读取真实桌面尺寸，禁止套用旧倍率。

本文别名C03/C04/C05/C06分别为`C:/workspace/ck3-upgrade-20261003`、`20261004`、`20261005`、`20261006`这四个完整绝对目录，不是工作树下的相对C06。外置raw、运行树和failed attempt永久保留。

## 真实NoSpace阻塞

CCC R2和R4实际出现`OSError: [Errno 28] No space left on device`。现在没有新冷场、Steam重启、pagefile设置修改或系统重启。

- 已执行NVIDIA unpack470叶约2.939GiB及此前pip/build/cache清理，以[清理记录](maintenance/c-disk-cleanup-2026-10-04.md)和原回执为准，不重复计数。
- 最近61份已闭合文本无损NTFS压缩，新增API尺寸差 **1,310,679,095 B（1.221GiB）**，完整SHA/身份/时间不变。四份旧聊天逻辑7.58GB仅贡献233,180,644 B API差，不能说释放7GB。过程资产删除0。
- C05/live和R3目录默认压缩已设置，操作释放0；R4新run目录/control/零字节probe已实际读回继承压缩属性，但仍NoSpace，不能把设置成功当环境解决。C04/live已有设置，C06/live不存在且未创建。
- [09:20:45内存/pagefile快照](handover/2026-10-06-ck3-upgrade-handoff-artifacts/nospace-memory-and-pagefile-snapshot.json)：RAM34,259,685,376 B，空闲16,342,523,904 B；CommitTotal22,682,312,704 B，CommitLimit39,359,959,040 B；系统管理pagefile当前5,100,273,664 B。CommitPeak42,016,415,744 B是Windows启动以来峰值，不能隔离为CK3峰值。R3运行中pagefile曾从5,100,273,664增到8,371,859,456 B，同期C空闲337,387,520 B；全部空间下降因果未知。
- [09:22:01 Steam private内存](handover/2026-10-06-ck3-upgrade-handoff-artifacts/nospace-steam-private-memory-snapshot.json)：webhelper2900 private3,392,278,528 B，webhelper16360 private294,674,432 B，steam17200 private664,498,176 B。仅三者约4.35GB private；RSS有共享页，不能累加RSS当可释放commit。正常重启Steam、降低背景commit是尚未实施的处理方向，没有回收信用。
- NVIDIA App有单叶793,353,272 B（0.739GiB）OTA下载616.92，安装驱动仍581.80；这是较新未消费下载，不是已安装后残留。[计划](handover/2026-10-06-ck3-upgrade-handoff-artifacts/nvidia-cache-exact-plan-NOT-EXECUTED.json)及[未执行脚本原件](handover/2026-10-06-ck3-upgrade-handoff-artifacts/nvidia-cache-delete-NOT-EXECUTED.py.txt)已归档，原入口`C06/delete_exact1_nvidia_retained_download_cache_03.py`。只允许计划内一个绝对叶、完整身份/时间/独占DELETE/无安装器guard；本轮未发执行指令，未删父目录或DriverStore。接手选用时重核当时身份与占用。
- WU Download仅17.27MiB，pending UNKNOWN、UsoSvc/MoUsoCoreWorker活跃，保留；旧浏览器/pip196叶仅11.75MiB，Temp近期用途不明，未扩扫。有限检查不能写成“全C无其他可释放空间”。

接手先观察实际磁盘、系统commit与处理收益，再新profile启动；不要只看启动前约4GB空闲重复冷试。系统设置或重启需基于实际数据准备具体操作，不盲目限制pagefile。原日志、存档、失败场和游戏安装树不作垃圾删除。

## 经商贪腐1.0.1：下一前台

维护目标 **3804807463**，上游3596263413禁止上传。[专题](ck3-1.20.0.2-celestial-commerce-corruption-compatibility-2026-10-01.md)保留R2、R3并追加R4。本轮未生成新正式tag、上传或公开条目。

R3/a76：Source10在D1 actor29959实际root available/ready，D2 xccc.1001 ROOT29959/instance2/native authored index3可见且enabled，一次tool option4选择`.d`并读回eventgone；D3唯一24h后 **原11标记各一次、两FAIL族0**，第四档特质和税率0.50实测。期限自动Native1闭合，没有剩余生产UI或正常OS0信用。不要再重跑这11项来拖延剩余业务。

R4/a77：D0/D1/D2通过，实际86对rules应用已证实；`.d` accepted/eventgone，D3 advance完成UTC09:05:52.545882，下一D3 frame/root未记录。UTC09:05:55.565978 Errno28，完整清理。仍待真实生产决议“定夺贪墨之策”→“翻开账册”的 **GUI Confirm**、新事件`.f`撤销、四档traits全消失、原tooltip三年冷却、正常GUI退出0。冷却只读实际Confirm日期+3年，不新增推进三年门槛；White专用MCP Confirm不能替代CCC动作。

R4 error EOF17893B，SHA `5c63d83cec0a8eb5e3a42cd295d257adc17935b367795af9a058240890e6beac`；60个[E]块中2个fixture `xca_effects.txt:12`未用初始化变量，其余指向原版court_scene/null character。strictBaseline UNKNOWN，不写全部noise或零错误。

[写入诊断](handover/2026-10-06-ck3-upgrade-handoff-artifacts/ccc-r4-write-diagnostic-candidate.json)把最窄代码路径缩至最后成功advance的`finally self.write → run.write → write_atomic_report`，逻辑sink为该场native-report.json的UUIDpartial原子写入。没有原traceback/filename，open/write/flush/fsync/close/replace子操作和瞬时空间峰值仍UNKNOWN；这是控制流推断，不是捕获的失败栈。

[候选patch](handover/2026-10-06-ck3-upgrade-handoff-artifacts/ccc-write-error-context-NOT-APPLIED.patch)和[完整候选字节](handover/2026-10-06-ck3-upgrade-handoff-artifacts/ccc-runtime-harness-NOT-APPLIED.py.txt)仅外置H81候选：给实际OSError附sink/operation/phase/laststep/原栈并重抛同一异常，不新增write、不吞错、不retry，不改业务/预算；旧atomic Permission retries保持。[九项有限in-memory writefaults](handover/2026-10-06-ck3-upgrade-handoff-artifacts/ccc-nine-writefaults-receipt.json)PASS；未合回master、未实机，Source10和旧场输入没动。采用时先审小patch、再冻结新输入，不能重写旧R4为GREEN。

R4原树`C05/live/4-8e1c2f1861--celestial-commerce-corruption--R0004`；inputs-08、operation18卡和已消费计划只作历史。UI19/profile09/new aNN未分配或准备。

Source10：新2638文件树仅两个stock大写key override，其余2636与Source09相同；一次fresh358objects/361edges成功，DLL5,565,440 B/SHA `f150c4cf1aa8a121ab44ab41d3052b0b7db6729644a7958bd53156abf682d754`。[冻结包](handover/2026-10-06-ck3-upgrade-handoff-artifacts/source10-build-only-packet.json)绑定producer/consumer/runtime。R3实际root读取通过，但title16958具体raw key没在薄证据中，不能反推R2必由大小写造成。其他产品已qualified Source09继续复用，无需统一重编译。

### 正式发布入口

[最短发布卡](handover/2026-10-06-ck3-upgrade-handoff-artifacts/ccc-formal-release-card.md)及[包](handover/2026-10-06-ck3-upgrade-handoff-artifacts/ccc-formal-release-packet.json)已准备。剩余业务与正常退出通过后，源码master/tag `celestial-commerce-corruption-v1.0.1`、正式22文件builder、目标3804807463上传、完整Notes匿名exact、fresh22 **及代表业务cell实机**、无ID重建、离线、永久changelog/master推送依次完成。候选git_tag=null不能替代正式tag，EResult1不能替代Notes，cache字节不能替代规定业务验收。

Notes：`workshop/change_notes/celestial-commerce-corruption/1.0.1.txt`，1708B/1244字符/17行/SHA `2d74578e9feca3dac77e2efca4791c8cb90c469ad8145b6586d244e3302e0ae3`。拟用`C06/ccc-workshop-publish-1.0.1-01`尚未使用；上一公开tag `celestial-commerce-corruption-v1.0.0`/commit `dc91dc1f0a1abd733d274382833a0ab9b3cdb51f`。实际CLI、匿名核对、cache profile和原合同已在卡中，不再搭发布平台。

## 其他待办入口

### 体验优化1.1.1 / 3798133925

R17/a73 D5为19/23、ZQAREL FAIL2；实际tributary=YES/forced=NO/primary_defender=YES/is_participant=YES。不能写从未参战，也不能仅凭参战归因mod召集。最终六步未执行，业务FAIL；正常GUI OS0、完整清理、CAS4095和离线已取得。[专题](xqol-1.20.0.3-defense-maintenance-2026-10-05.md)保留原结果。

下一防御cold18用[最终卡09](handover/2026-10-06-ck3-upgrade-handoff-artifacts/qol-defense-cold18-card.md)，唯一index `C06/xqol-defense-cold18-agent-01/package-index-ready-02.json`，65020B/SHA `0ae1ada437ce4e8bebcca43aed49ed61dd8e471ca3b8b6929a8c0a7e59ed898a`；旧01被validator拒绝，禁用。candidate03只改fixture资格，真实stock obedience effect与actual target/档位检查后正常断盟；原23标记+最终6/max33天/once/失败门禁、生产27和Source09不变，**READY/NOT_RUN**。

防御后用[原直接续行卡](handover/2026-10-06-ck3-upgrade-handoff-artifacts/qol-post-defense-direct-card.md)的天朝任命/slider/宗教自然链、[ordinary async38](handover/2026-10-06-ck3-upgrade-handoff-artifacts/qol-async-entry-card.md)。[新五场总路由卡](handover/2026-10-06-ck3-upgrade-handoff-artifacts/qol-post-defense-followup-card.md)已经补齐原缺输入：

| 场 | 准备范围 | 未验边界 |
| --- | --- | --- |
| 行政、贤能各一 | [政府卡](handover/2026-10-06-ck3-upgrade-handoff-artifacts/qol-government-entry-card.md)，各37文件，prod27/Source09，真实e_byzantium/e_goryeo holder | actual government/root、法、候选、任命、tooltip；白名单已master b2c5合回，冷场未跑 |
| PAM正03、负02 | [双入口卡03](handover/2026-10-06-ck3-upgrade-handoff-artifacts/qol-pam-two-entry-card.md)，各39文件/35步/最多12天，D0实际SP=0后D1唯一自然派发 | 正SP0→10→13、负0→0；piety同步原断言。既有public `player_legitimacy_v1` raw可读，不能再称不存在；同步合法性因果仍GAP，不能仅用总前后差授信用 |
| 赎金 | [最终卡02](handover/2026-10-06-ck3-upgrade-handoff-artifacts/qol-ransom-entry-card.md)，38文件，两真实AI自付全额/一金币自然流程 | 原回调释放/quote/transfer/piety及必需markers；卡01遗漏marker已作为历史保留，不直接调用callback |

五场均READY/NOT_RUN，无allocation/game/UI，无新ABI/DLL。nonself/shared wallet、完整秘密家族矩阵、未具现有能力的归因等仍GAP，不扩为全排列研究。用实际最新lease和当次reviewer，prepared档位或源码常数不是游戏结果。

### 重整河山0.4.1 / 3798404599

R3/a74三阶段宋存在/h_china=true，但character_situation=false/top_group=ABSENT；fixture_vassal_tree_prepared FAIL一次、core RED。正常GUI OS0、全部gone、CAS4115闭合。

[operation10卡](handover/2026-10-06-ck3-upgrade-handoff-artifacts/rmtm-operation10-card.md)：完整stock situation真实hegemon on_join插入6行就绪后派发，6项有限用例通过；初始化根因UNKNOWN、实际callback NOT_RUN。生产36、业务/UI/14天/400秒不变，必须配[SHARED05 controller补卡](handover/2026-10-06-ck3-upgrade-handoff-artifacts/rmtm-shared05-controller-card.md)，不用旧07/09同bug controller。核心realm/personal land/9部长/两annex取消/继承36markers先闭场，再独立50/51阈值，不延长原预算。

完整Notes3376B/2374字符/22行/SHA `10eb22a29829a2726cbe529d11ac806369448e4bdf2419c902a5a6d4959019f4`，旧20行仅历史，无0.4.1正式发布信用。

### 驱策朝贡国1.0.1 / 3801490405

R6/a72 D2暂停失败；真实玩家34422→34440死亡边界、war4保留，投降后果/关系停战、save-load和三项UI未完成。正常GUI OS0、清理、CAS4079完成。

[operation11卡](handover/2026-10-06-ck3-upgrade-handoff-artifacts/ted-operation11-card.md)为下一入口：Source09/H81、生产16、actual rules、400秒、core13/save-load/三项UI不变。controller05修caller pause expected None/SDK真实revision pin、SHA大小写、paused heartbeat去重、speed settled和实际paused读回；旧迟到失败/预算保留，不重跑纯检查。Notes1584字符/17行/SHA `057028c6439cdac695db4184798f9217a34774678b203ebd28085e2fd3c408b9`为未发布草稿。旧formatter精确caller/root cause UNKNOWN，按实际投降前后增量判断，不以路径来源代替因果。

### 天朝特色361制：最后

本轮完整实机与发布尚未取得，[专题](ck3-1.20.0.2-zhongguo-compatibility-2026-10-01.md)和`C04/361-parallel-startup-03/`保留。规则停止、文案review绑定RED不能被旧1.19/.2覆盖；兼容仍1.19。本次仅结束旧输入准备任务释放资源；其他四个待发布产品完成后才处理，不提前宣传或调整优先级。

## 已推送主线工作包

| 提交 | 内容 | 已有验证 |
| --- | --- | --- |
| `41508ddfe9435c1bf47fa87588965e9ba7ae9d0a` | stock key case最小修复、回归、文档 | master25测试PASS；既有native6组/serializer/Python normal与-O各40；CI37430392108 SUCCESS |
| `5bc98dfd43714e0ef5ecf37be4f8a5363b8e8717` | CCC R2失败、61文件压缩和日报 | ordinary push/remote exact；CI37434738325 SUCCESS；fetch TLS失败和两resume错误保留 |
| `b2c5ec6ab25d14c3500b989a007a42549987e93e` | 政府白名单与actual loader回归、CCC R3、目录压缩事实、日报 | 22针对性测试PASS（3.709s）；CI37439420655 SUCCESS，09:03:55 UTC完成 |

这些包已结束，CI不重复查询。冻结Source09/10和旧工具不随master变更追认修改。交接起点working tree clean，local落后其他机器24提交，已正常fetch/rebase到 `dfab3f7d96e3df50a65df7af6f207e0de842bd03`，无merge，不重跑其他机器研究。最终交接commit与ordinary push/远端exact回执存`C06/root-vacation-handoff-20261006-01/actual-handoff-pushed-closeout.json`，不在本文虚构自身尚未生成的commit。

## 接手顺序

1. 阅读本页、[AGENTS](../AGENTS.md)、产品专题和[归档索引](handover/2026-10-06-ck3-upgrade-handoff-artifacts/index.json)。26份原件字节/SHA保持；卡中绝对runtime路径仍依赖这台机器，Git副本不代替完整profile、原录像或存档。
2. 用户恢复执行后盘点本机进程、总线owner、C空闲和系统commit，先处理真实空间问题。正常Steam重启/精确缓存删除均未实施；旧截图、nonce和lease不能复用。
3. 如采用H81诊断候选，审小patch并复用已有9项回执，冻结新的source/runtime/profile绑定；业务、预算、DLL和已消费场保持，避免重逆向/重全矩阵。
4. CCC优先补剩余生产UI与正常退出；后台复用QOL18、RMTM10、TED11已备输入。新场使用new aNN/run、新nonce、实际操作者reviewer、新鲜Steam离线审阅。
5. 规则以实际86pair应用为准，不用旧85精确数卡死。MCP/native读取状态真值；必要GUI走现有语义/UI Automation或原截图坐标映射，不用OCR猜状态。点击必须原图/真实尺寸/receipt，键盘必须LANGID0409和目标焦点。
6. 单产品source PASS后立刻完成正式tag/build、上传、匿名完整Notes、规定cache字节及业务实机、pristine无ID重建、第一时间离线、永久changelog/master推送。remote_file_id仅用户外层.mod，源码树不能直接上传。
7. 闭场核原PID/create-time、真实Native/OS退出码、job0/treegone/inventory空/controls absent/watchdog gone；keeper实际退出后以原末seq单次CAS释放，绑定当前CLI SHA大写。不事后补finish_hold制造正常退出，不用ACK代替业务结果。
8. 361最后，具体礼仪选择在全部维护之后。重复已有测试、重读大帧、全盘宽扫或无需求的平台建设不是接手第一步。

本次只收尾和交接；未来步骤都是接手清单，尚未发生。

### 2026-10-07续办：R23/R7实际失败与正常闭场

QOL R0023/a96实际D5 forced_flag NO、19/23项到达、2条FAIL；新增观测有missing BOM告警及同event priority0冲突，ZQD22CALLBACK=0，未取得定义执行证据，回调资格仍UNKNOWN（[薄诊断](C:/workspace/ck3-upgrade-20261007/qol12004-continuous-prepare-01/R23-initialization-definition-readonly17-01/ROOT-R23-D5-OBSERVATION-NOT-EXECUTED-DIAGNOSIS17-01.md)）；不据BOM告警推断整个fixture未执行。实际正常GUI/retained OS0/native0、keeper89392 exit0、CAS5616 done，旧FAIL/raw保留，不授业务PASS。

RMTM R0007/a97 operation12实际natural chaos observer1、D2dispatch PASS1，D3完成14日中的3日后paused/event NULL；chaos/ministry/loyal/defection/released/path/budget各PASS1，首FAIL `later_dynasty_single_heir_law_and_heir_ready`只知law+current_heir组合未过、尚不区分。无READY/DONE、业务未验收；[薄闭场](C:/workspace/ck3-upgrade-20261007/rmtm-r0007-closure-readonly-resource-01/R0007-BUSINESS-FAIL-NORMAL-EXIT-CLOSURE-01.json)确认正常GUI/retained OS0/native0/host thread cleanup，keeper40317实际0→CAS5669 done（14:15:35.893868 UTC），host GREEN仅生命周期。当前QOL R24/a98已分配seq5670、正常bootstrap中，未判结论。正式仍6/10（60%）；全部及未来产品沿用[永久缓存规则](workshop-cache-acceptance.md)：真实Steam下载文件exact formal+CK3实际mounted/load，发布前源码业务验收保留。

### 2026-10-07续办：R24回调实际执行与TED R7到期闭场

QOL R24/a98自然xqol.101 priority1的BEGIN/END已实际执行，BOM错误消失、error0 B；D5 forced=no、19/23项到达、2FAIL，helper观测0，不能据target invalid归因，helper/回调资格仍UNKNOWN（[薄诊断](C:/workspace/ck3-upgrade-20261007/qol12004-continuous-prepare-01/R24-initialization-definition-readonly18-01/ROOT-R24-ACTUAL-CALLBACK-DIAGNOSIS18-01.md)）。实际正常GUI/retained OS0/native0，keeper1503 exit0→CAS5687，原业务FAIL保留。新RMTM op13 R8/a100仅启动准备、只读分辨law/heir，非修复，未判结论。

TED R7/a99原13项各1、FAIL0，真实GUI Surrender及defender保留县已亲审；Save/Load、truce未完成。原hold于15:42:24 UTC到期，close02守卫拒绝且未发送Quit；[薄闭场](C:/workspace/ck3-upgrade-20261007/ted-r0007-expired-closure-readonly-resource-01/TED-R0007-HOLD-EXPIRED-CLOSURE-01.json)为native stop/退出码NULL、shutdown CK3 exit1、job1→0/treegone/cleanup，非normal0，host GREEN不授业务PASS。keeper91610实际exit0、last5772→CAS5773 done；结束error1260 B与before exact一致/delta0，14条文本格式错误尚未归属。用户最新允许本机CK3、临时禁令已撤销，G2后台源码研究继续；批次仍6/10（60%），全部及未来产品的永久缓存两项规则与发布前源码业务要求保持，旧失败/raw不改。

### 2026-10-08续办：RMTM R8法条失败与最小生产候选

RMTM R8/a100 D3原FAIL1已缩窄为law FALSE/current_heir TRUE（primary18371/heir37989/root34422/date53144400/paused），Root原图宋领地“仅男性 / 长子继承”；[实际薄包](C:/workspace/ck3-upgrade-20261007/rmtm-r0008-law-fail-readonly-resource-01/RMTM-R0008-LAW-FALSE-HEIR-TRUE-NORMAL0-BOUND-01.json)证明正常GUI/retained OS0/native0/job0/thread cleanup、keeper64291实际0/last5797→CAS5798 done，业务FAIL保留。生产finalize/set_primary后唯一8行缺法guard幂等补single_heir已由Root应用，早期grant/resolve保留、engine清法UNKNOWN、候选未实机，原36合同/14days不改；[当前适配专题](reclaim-the-motherland-ck3-1.20.0.3-readiness-2026-10-05.md)接续。QOL R25/a101新graph18已启动、未判；G2外置新API源码8+2测试已有，native未build/live未资格；批次仍6/10（60%），全部及未来产品缓存永久两项规则与发布前源码业务验收保持，不写未来发布成功。
