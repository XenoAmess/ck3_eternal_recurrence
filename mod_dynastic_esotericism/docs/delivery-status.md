# 制作与发布状态

观察 2026-10-25T15:41Z（`machine_id: desktop-3fevhd2-1c74096080`）：用户恢复任务并追加两项独立信仰／同名礼仪、礼仪名称与纹章、建族后实际创建／改革者担任最终族长的要求；已确认新信仰归基督教大类。需求／测试版本2先落盘，0.2.0 候选实现及九语文案、用户图标已形成。两个预置纹章使用精确图标；任意自创礼仪原生无法直接复制图标时，按用户随后授权只随机生成一次宗族纹章并给默认 House 使用。尚未新开实机，未更新 Workshop。

首轮 a20 默认 Maven 3.10.0、JDK25.0.4.1 实际构建运行24项测试，23通过／1失败／0跳过；唯一失败为新独立 Python AST 检查片段的 Windows 引号传递，已修复并单独核实际 Java textblock 生成后的语法，完整重跑待执行。原失败日志／原 Popen 结果位于 `C:/ck3-dynastic-esotericism-20261024/resume-builder-a20/`，未覆写。当前30文件开发包／51文件九语包为候选清单，不是已验收的新发布。新core仍须以R0016正常managed closure接续并另行取得存储与SCREEN资格，旧运行与冻结图不改。

观察2026-10-25T13:30:38.536581Z（machine_id: desktop-3fevhd2-1c74096080）：按用户最新“先发布，再继续本地验证”指令，0.1.0初始公开测试版已发布到[Steam创意工坊3826991345](https://steamcommunity.com/sharedfiles/filedetails/?id=3826991345)。CreateItem与SubmitItemUpdate均实际EResult1，公共API读回公开状态、标题、完整说明、AppID与三个标签一致；更新日志网页HTTP429尚待补查，缓存下载/加载验收未执行。后台原生回执已确认恢复Steam离线。R0015签署核心前四阶段，保留+2日全员保存缺口；Root在同一revision重复打开已打开的决策菜单，被SDK正确拒绝，业务失败及闭场原件保留。后续先修复继承输入夹具和操作顺序，再继续长期、继承、cold/old验证；修复并验证后更新同一条目。完整业务未通过。见[首发实际记录](acceptance/first-publication-2026-10-25.json)、[R0015](acceptance/R0015-2026-10-25.json)。

观察2026-10-25T02:55:27Z（machine_id: `desktop-3fevhd2-1c74096080`）：R0013实际通过核心前两阶段；创建后+1、+2日各61名原生信徒均由保存独立核为House12760→Dyn12156，未改信后代仍为House174→Dyn174。原族长交接给真实旧家族成员后建族，以及singleton生成并保留真实同礼仪成年创始人，两条分支均取得实际保存后态。正式创建、取消无副作用、两个教义的创建／编辑显示也通过。第三阶段尚缺合法囚犯的处决／驱逐选项预览，Root如实返回INCOMPLETE，没有提交不支持的监禁动作。Game0、host0、public2、keeper／allocator0、SCREEN8892，normal-close=true仅生命周期，完整核心仍未通过。当前总体约62%，完整矩阵、seed／cold／old和Workshop尚未完成。见[R0013实际证据](acceptance/R0013-2026-10-25.json)。下列较早观察保留其历史范围。

观察2026-10-25T00:03:25.441948+00:00（machine_id: `desktop-3fevhd2-1c74096080`）：R0012已完成typed原生退出与资源闭场，业务0/6；原失败和autosave=false保留。e703产品静态CI40143646790实际success。新候选统一canonical source index并显式保历史只读兼容；原请求者优先卸任、singleton生成真实NPC，以及stock家庭转换同callback共享同步均纳入新源码。18文件开发包／25文件九语清单已同步，完整回归、a15工具／a16新包／runtimea12和全部实机矩阵仍在执行，不能拿旧产物抵扣。当前总体约60%，seed/cold/old与Workshop尚未完成。以下为各观察时间的历史记录。

观察2026-10-24T22:20Z（北京时间06:20），machine_id: `desktop-3fevhd2-1c74096080`：R0010真实创建与独立completion通过，原取消前后Rite／House／资源／无绑定保持；+1原生63成员与保存选择完全相等，其中六名实际仍在旧Dyn174，其余不同House不能直接当作不同Dyn。+2前已有新事件，Root漏先处理，guard9正确拒绝，日期仍+1，+2查询和保存未执行；这不是SDK读取故障，不改共享守卫。另实际加载报告新NPC create_character缺必填gender；最小源码修正仅增加 gender_female_chance=50，有exact原版用例和grammar原exit0，新图加载／NPC仍待验证。详见[R0010原件摘要](acceptance/R0010-2026-10-25.json)。

原生同handle Game退出0、host1/public2、keeper及原allocator0，SCREEN8830释放；公共verify实际2、业务及normal-close资格仍false，autosave=false。两次误用参数／finish intent均在分派前拒绝，修正后仅有一次真实各阶段动作，旧回执保留。整体约60%，完整核心、seed/cold/old及发布未完成。下一节点06:35启动修正版、07:45–08:15汇报核心实际结果，依赖真实资格与后态。

后继采用原a11/S11冻结SDK／host和原a13 fixture（13文件／14pins），不更改已冻结图；新main11生产源单行改动须由未改a13 Java工具重新validate/build/verify，生成新正式包／manifest／ZIP，再公共prepare到全新a19并核manifest=staging=profile。旧S11三文档合同仍明确属于原来源，新操作更正与head边界另存，不冒认同一源；只改CK3脚本无需重编译未变Java/SDK。容量新10-profile scope与关Game后的系统预留正在重验，未沿用旧1185页文件消费授新启动。

2026-10-24T21:40Z（北京时间10月25日05:40），machine_id: `desktop-3fevhd2-1c74096080`：用户确定先交接旧House族长，仍无合法founder时生成真实同礼仪创始人物。最终隔离候选2e7b8bf完整默认Maven原会话94612退出0，16项无失败／错误／跳过；实际生产链validate/build/fixture/verify均0，15JAR资源、17开发包／ZIP、13fixture及14pins一致。新runtime a11与prepared a18正在生成，尚未启动新场。原R0009公共verify实际退出2，normalclose仅生命周期true，phase1六断言接受、phase2 FAIL不变；seed/cold/old及发布均未完成，总体约60%。新两cell只经stock factory输入，+2独立保存核真实交接、NPC及Root身份，不给旗标业务信用。详见[机制及实际构建](2026-10-25-house-head-handover.md)。

容量已实际原子准入r1184/storage72，原6GiB执行池覆盖9个profile与新a18/a29，构建／源／运行准备峰值504MiB包含两份135MiB源、Git32MiB、runtime42MiB、builders48MiB和共享未来test/temp112MiB；C build/test总额仍512MiB，D未来仅2MiB小元数据，D Git28MiB未激活。原20GiB安全、C16GiB/D128MiB系统未来预留和2026-10-25T07:30Z期限不变，没有物理回收或延时。 authority `C:/ck3-dynastic-esotericism-20261024/capacity/NINE-POOL6-C-BUILDERS48-TEMP112-PEAK504-D2-ADMISSION-r1184.actual.json`，SHA `293ae0c11a47ad65e12f5a5b0114f9c3b843eb3bcf2424f8f05c45b8b8c706d6`；每次重型操作另做新鲜实际检查。05:50启动为计划，07:10–07:40汇报核心实际结果；发布依赖核心、cold与旧档通过。

本次用户指令：依次完成需求文档、测试方案、编码、测试验收、发布。开始时间 2026-10-24；本机 `machine_id: desktop-3fevhd2-1c74096080`。

| 阶段 | 当前事实 | 依据 |
| --- | --- | --- |
| 需求 | 已制定版本 1 | [requirements.md](requirements.md) |
| 测试方案 | 已制定版本 1，尚未授予测试通过 | [test-plan.md](test-plan.md) |
| 编码 | 18de31e4源码的交接／singleton真实NPC及家庭转换同步已在R0013取得实际后态；现有囚犯预览通道与测试输入仍须补齐 | [R0013](acceptance/R0013-2026-10-25.json)、[测试方案](test-plan.md) |
| 测试验收 | R0013核心2/6阶段通过，全体61人两日核对与两种建族分支通过；第三阶段未完整验收，核心整体INCOMPLETE。seed/cold/old未完成 | [R0013实际范围](acceptance/R0013-2026-10-25.json) |
| 发布 | 0.1.0初始公开测试版已发布，Workshop ID 3826991345；继续本地验证，缓存与完整业务未通过 | [首发实际范围](acceptance/first-publication-2026-10-25.json) |

2026-10-24T21:15Z补记（北京时间05:15，machine_id: `desktop-3fevhd2-1c74096080`）：用户提出卸任家族族长再建新宗族。已核 exact .4 原版 `set_house_head` 会同步重算 Dynast；窄生产候选优先已有合格真实信徒，无人时才让另一存活同旧House人物接任，并在实际双重离任守卫后建族。旧House只有本人时仍未解决，不默认新建NPC，等待用户对该边界的选择。见[原版来源、影响和待验边界](2026-10-25-house-head-handover.md)。新S11候选61b4b05不改SDK/native，完整默认Maven16项0失败/错误/跳过及15资源、17文件开发包/ZIP/13文件fixture实际生产链通过，回执 `C:/ck3-dynastic-esotericism-20261024/resume-builder-a12/SUMMARY.actual.json`，SHA `b0977cbc628e5c2c9021774fe48c706e7846ab1f15baaa3db8da06bf1b181076`。当前新增交接路径尚未实机，不能从构建或研究追认通过；下一图准备还将检查能否以真实输入触发fallback。R0009公共verify已实际退出2，case_acceptance_pass及qualified_boundary_pass为false，原normal_close=true仅生命周期继续保留。

2026-10-24T20:49Z更新（北京时间10月25日04:49，machine_id: `desktop-3fevhd2-1c74096080`）：R0009已通过创建／取消／费用／真实绑定的第一phase，六项断言只计该phase。创建日47名成员全部已进入House12760/Dyn12156；次日新增13人仍在旧House，其中六人明确仍属Dyn174，原全量检查FAIL，原错误与保存保留。首批43人的原版转换标记在下一日期才出现，新增13人当时尚无标记；exact .4调用链与逐人对照支持排队时序调查，不足以追认产品正确。下一图仅把fixture检查由+1改+2日，保留全量守卫与REQ-05同次同步要求，分别在两日读取原生名单和保存。中英fixture的方括号标题前缀另改为普通文字，解决其被当作data function解释的真实日志错误。候选b8c7fc3的完整默认Maven16项、15项JAR资源、17文件开发包／ZIP／清单消费者、13文件core fixture／14项生产来源均通过；实机尚未复验。实际包回执 `C:/ck3-dynastic-esotericism-20261024/resume-builder-a11/SUMMARY.actual.json`，SHA-256 `b0acbc24f97e4da377a35aebe6686336e2fe7b84dae5b5176bfc53f358430114`。

R0009原生正常退出Game0、host0、public2、keeper/allocator0，SCREEN8808释放；原normal-close=true只证明生命周期，autosave=false及业务RED保留。共享后继消费者实际返回`previous-shared-managed-session`，不使用failed-host bundle。总体仍约60%，完整核心未通过；单一信徒恰为原House族长时的合法建族方案另待明确，不能从本场多人成功外推。计划05:00汇报，下一轮预计05:10进入实机、06:30–07:00形成核心结果；冷载／旧档与发布随后进行，具体完成时间取决于原失败及sole-head边界的解决。

当前容量r1181/storage69已原子采纳，C盘main11集成与S11冻结SDK来源使用原512MiB构建额度内490MiB峰值方案；D盘仅2MiB有限元数据，Git写未激活，用户原脏文件和原HEAD3c均保留。旧D28MiB是未激活后续阶段，不作已消费或物理回收。Game退出后同FileID pagefile实际回baseline，系统原16GiB未来预留已恢复、consumed归零；所有新启动仍须另核scope与新鲜容量。证据 `C:/ck3-dynastic-esotericism-20261024/capacity/R1181-ROOT-CAS-COMMITTED-a33.actual.json`。以下旧场次及容量按各自观察时间保留。

2026-10-24T19:46Z更新（北京时间10月25日03:46，machine_id: `desktop-3fevhd2-1c74096080`）：R0008已正常结束，Game原保留句柄观察退出0、host1、public2、keeper0，SCREEN8784释放。原宿主因Root将只读工具名误写为缺少`_v1`的名称而停止业务，后续业务请求被门禁拒绝；没有执行创建或迁移，也不增加核心通过数。启动日志另发现继承夹具把变量当日期字面量解析，原错误保留于`C:/ck3-dynastic-esotericism-20261024/R8-heir-date-guard-fix-a01/CANDIDATE.actual.json`。修复改用原版同构的数值天数比较，保留缺变量拒绝和至少一日要求；主线cff81b3已推送并回读。新隔离候选0c54184的完整Maven原会话55072退出0，16项测试无失败、错误或跳过，15资源打包后的生产者到消费者核验和新实机仍在继续。当前总体约60%，核心0/6，seed/cold/old与发布均未完成。

最新容量为r1178/storage66：`C:/ck3-dynastic-esotericism-20261024/capacity/EIGHT-POOL6-D28-SCOPE-A17-ADMISSION-r1178.actual.json`，SHA-256 `3183055c901d0f5eac9acff8a5c578e9716d75a76724e47f5aaf6857b7e4babf`。八个累计Game profile共用原6GiB池，旧a16保留、新core为a17/keeper-a28；build/test仍512MiB、D未来仍28MiB、安全预留与2026-10-25T07:30Z期限不变。运行中同FileID的pagefile实配新增曾消费9,250,131,968B系统增长预留，关场后实际回退，因此已恢复原16GiB未来预留、consumed归零，未提高原总额。重型写入和新启动仍执行新鲜检查；以下旧容量与场次记录按原观察时间保留。

截至2026-10-24T18:46:46Z（北京时间10月25日02:46），总体约60%是规划估计；核心0/6、cold/seed/old未完成，Workshop未创建。R0007已原生退出，Game原Popen0、host1、public2、keeper0，SCREEN8743释放；资源终态不授业务通过。后继s08/common-runtime-a08已冻结，公共plan/prepare实际通过；尚未分配或启动R0008，保留a07原件。

2026-10-24T19:21:47Z更新：a08实际allocate在分配ID前退出2，真实Java运行包生产者漏出成员查询的构建证据，未启动Game或keeper。实际Java生产者补一行既有工具登记，原14项编译开关与来源守卫不变；完整Maven16项通过，新增到既有JUnit内的真实Java产物→公共预检正负链已执行。新S09以1df冻结SDK为基线，只接入同一主线Java修复，执行提交为25e7e5；a09真实Java运行包、plan/prepare和实际产物公共预检均通过，仍不授live或业务资格。新core state为a16、keeper为a27，旧a08/a12原件不改。详细[失败、修复与实际生成回执](acceptance/runtime-members-capability-2026-10-25.json)。核心0/6、总体约60%及未发布结论不变，04:00继续汇报实际阶段。

工具链已在以上机器原位升级默认 Maven 3.9.16→3.10.0，PATH与原配置保留；实际来源和读回见[环境回执](evidence/environment-maven-2026-10-24.json)。当前容量依据为机器绑定的 `C:/ck3-dynastic-esotericism-20261024/capacity/SEVEN-POOL6-D28-SCOPE-A16-ADMISSION-r1176.actual.json`（SHA-256 `275e150776a773ed50e5e2c78d829c9665891fd82848d56be54be4a305072ae7`）：七个实际Game profile共用6GiB执行池，另保留a11及a12未启动的旧准备材料；build/test512MiB，D剩余未来28MiB，硬期限2026-10-25T07:30Z。core/seed/cold/old新state分别为a16/a13/a14/a15；本次仅补正未Game旧a12与新a16/a27的scope，预算未增加。已实际checkout的旧incoming不再重复列为未来写入，仍保留两份临时index、objects和bus预算，来源32对象已计实际占用，没有冒充物理回收。C池、系统增长与安全预留均未减少。重型写入及启动前仍须实际新鲜检查；旧4GiB/32MiB记录只作历史。这些资格不代表游戏业务已通过。

当前软件增量：共享目的消费者从原合同顶层消费既有 `allow_actor_change`，真实producer→JSON→host loader→实际driver回归10/10，preserved3/3、offline-TTL6/6及7完整模块strict通过；同一原生成员查询已接通公共只读路由，完整产品CI step六条命令32项退出0。该许可只允许观察合同声明的actor变化，PID/generation/pipe、单调日期与原400日预算继续生效；实际继承和新礼仪领袖仍须原生与保存证据。完整共享91条命令退出0，其中一项HoF原生wire测试缺真实输入，明确NOT_EXECUTED。cold/warm完整30条命令已顺序全部退出0，包含独立Python进程SDK continuation；其中第23条的可选真实小WAL诊断缺输入，明确NOT_EXECUTED，不计全测试零跳过。已修正既有测试合同、两处局部类型推断及其两个来源指纹消费者，并恢复远端已发布的精确Source32历史标签。此前失败保留，不冒充一次无失败执行，也不授实机业务通过。

云端06d2358的产品和线性历史CI已success；Official实际Java两轮各633项通过后，完整parity因缺少真实fixture-production request拒绝，后续step未执行。已保留来源调查与原RED，没有伪造请求、放松guard或报告全仓绿色。以下按观察时间保留历史进展。

截至2026-10-24T09:02Z，首轮候选已完成最终离线准备：Java／Quarkus构建10项测试全部通过，17文件清单及既有清单消费者一致；启用14项所需能力的原生DLL已生成，三个原生测试在受管构建目录实际通过并取得SYSTEM精确路径登记回执。早先空EXE尾钩失败、外置来源登记拒绝及UAC取消仍保留为原始事实，没有将其标成成功。

SDK的19项礼仪回归及4项共享服务绑定回归通过；真实运行解释器离线注册220个工具，所需旧工具全部保留，与新接口使用同一个实际服务。冷加载完整CI命令组和严格检查的准确范围见[离线类型检查](acceptance/offline-types-2026-10-24.json)，旧大模块的遗留错误未被冒充为全绿。以上均为离线结果，实际游戏尚未启动，宗族迁移、犯罪理由、赦免、自然出生、存档恢复等业务继续等待原版界面与原生后态验收。正式发布状态仍为NOT_PUBLISHED。

2026-10-24T09:12Z 补记：首次固定提交56d5627的产品CI和SDK CI均已实际success，见[云端回执](acceptance/hosted-ci-2026-10-24.json)。固定提交换行与旧工作树打包资源不一致曾被生成器拒绝；已从该干净提交重建，10/10及15资源精确比对通过。公共plan与prepare已通过；第一次allocate在分配ID前因新产品不在共享canonical key表而退出1，未启动游戏，正在修复该登记项。原始失败保存在C盘任务证据根，不能从这些准备结果推导业务或发布完成。

2026-10-24T09:59Z 实机更新：R0001已真实启动，发现不可玩角色教学错误与共享推进scope缺失，尚未完成任何GUI业务phase，结果RED；原版GUI正常退出0、原始宿主退出1、公共run退出2、原生清理通过、keeper退出0、CAS8596释放。详见[R0001不可覆盖的失败记录](acceptance/R0001-2026-10-24.json)。源码修复正在准备，不能把静态或闭场通过改写成业务通过。

2026-10-24T10:22Z 修复准备：仅对原版可玩角色传授选项知识，全员归族与犯罪规则不缩减。修改的5个脚本增量语法解析通过，CK3 1.20.0.4语义profile仍不受离线工具支持，见[解析回执](acceptance/playable-knowledge-parser-2026-10-24.json)。九语发布构建合同14项测试通过，当前真实源仍是中英开发包，尚未写入七语正式译文，见[构建准备](acceptance/release-localization-builder-2026-10-24.json)。两者均不授予新实机或发布通过。

2026-10-24T10:57:55.767374+00:00 后继入口准备完成：原正常退出profile接线的完整7组测试33项及修改范围严格检查通过，见[实际回执](acceptance/managed-exit-wiring-2026-10-24.json)；最终干净候选480ea的Java构建14/14、17文件包和13文件夹具回读通过。新common-runtime-a04已生成，公共plan／prepare实际退出0；尚未启动R0002，业务与发布仍未通过。专项最初两次测试夹具报告写入竞态已修复，原RED保留，生产代码字节未改变。

2026-10-24T11:18:01.579044+00:00 启动前更新：R0002未启动宿主或CK3，实际public run因离线凭据超过冻结守卫的30秒窗口而退出2；keeper合作退出0，CAS8607已释放，见[R0002原件摘要](acceptance/R0002-2026-10-24.json)。业务为NOT_RUN，不存在Game退出码。原先60秒的口头说法已按pinned源码纠正。2afe的[产品CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40088035978)及[SDK CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40088035992)实际成功；[cold CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40088036030)在232套件中出现1失败和1错误，均为新profile必填检查误阻旧v1/v2只读验证。正在恢复历史读取与实际launch检查的正确边界，并补既有unrun消费者的真实pre-intent拒绝闭场路径。后继完整相关回归和新冻结场次尚未通过。

2026-10-24T12:38Z 恢复执行：机器身份重新核验为 `desktop-3fevhd2-1c74096080`，实际 EXE SHA 与 1.20.0.4/build25734779 基线一致，后台 Steam 新观察为 offline；无 CK3 进程。任务容量已从关闭状态重新原子准入到 r1158/storage46，期限2026-10-25T07:30Z。R0003 的公共 verify 实际退出2，case/gui/business/release均未通过；其真实原生同handle退出0与资源闭场消费者通过只授资源结束，原业务RED及normal-close=false保留。见[R0003摘要](acceptance/R0003-2026-10-24.json)。四个fixture修正与新等待规则已形成3592360干净候选，正在重新Maven构建；共享正常闭场typed路由和完整回归仍在施工。尚未分配下一场或发布Workshop。

2026-10-24T12:43Z 离线增量完成：新干净候选Java构建15项JUnit通过，15打包资源、17文件正式开发包/ZIP和13文件core fixture逐字节一致；已线性rebase并推送master b4a58ed38。R0001旧GUI和R0003真实typed原件均通过共享资源消费者，资源22项、同CI step余13+12及历史20项通过，strict仅覆盖8个完整实际定义与实际分派。详见[恢复构建与typed闭场](acceptance/resumed-fixture-and-typed-closure-2026-10-24.json)。不授业务或正常闭场通过，原R3 RED不变；下一场所需无错误typed正常闭场仍在完整共享CI验证中。

2026-10-24T13:19Z 共享正常关闭软件路径完成：新增独立typed路由，实际保留原handle精确FILETIME，校验原fact/close/once claim与冻结profile/source inventory；GUI review仍为null，autosave完整性资格仍false。正常关闭原组40项及7个完整新增顶层定义strict通过。原共享CI step全部91条命令均已真实执行并取得0，期间环境依赖和旧fixture/source兼容失败分次修复，原RED保留；不将它们写成一次无失败执行或实机通过。尚待全新runtime、R0004实际业务与正常退出验收。

完整命令及修复出处见[typed正常闭场与91条共享CI](acceptance/typed-normal-close-and-full-shared-ci-2026-10-24.json)。Windows短TEMP修复后的5c6cc产品CI已实际success，远端runner机器ID未采集；不外推为本机游戏通过。

2026-10-24 R0004 实际增量（machine_id: `desktop-3fevhd2-1c74096080`）：a06 实机发现夹具整句宏日志被引擎拆成未知 effect，完整业务保持 RED。原生 UI 已观察默认“无”、两项教义可选及五名称字段读回；原最终 Can 仍因缺少原版教士傀儡前置而拒绝，未提交创建，已取消草案。原 SDK 同保留句柄退出0、host 原 Popen0、public run2、keeper 原 Popen0，SCREEN8661已释放；完整 normal-close 因共享消费者误将同一 Windows 路径的斜杠表示判为不同来源而失败。见[R0004原件摘要](acceptance/R0004-2026-10-24.json)。

后继已修路径比较合同，并用真实 inventory producer 到 SDK/消费者回归覆盖；正常关闭原四模块42项、原共享CI整组91条命令在一次顺序执行中全部退出0，7个完整修改定义 strict 通过。夹具改用静态日志、保留原完整正负谓词，准备真实原版教士关系前置并提供独立读回；这些软件结果不追认R0004。新干净Java构建、新runtime和后继实机仍待完成。旧867bcd4的Product CI成功，但Official CI另有scope测试导入路径RED，不能称全仓CI通过。实际出处见[后继软件与容量记录](acceptance/R0004-followup-2026-10-24.json)。
