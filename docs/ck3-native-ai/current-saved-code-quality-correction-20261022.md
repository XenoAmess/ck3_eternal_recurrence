# 自动游玩代码与门禁整改（2026-10-22）

本次自查由用户要求触发。`machine_id: xenoamess-full-tower-eb9d2c1186`；实际调查与整改开始于 `2026-10-21T19:53Z`，以下现场截点为 `20:01Z`。源代码基线 `5605487f8d189ba229b49360fa6455e9af7c34f0`。这是当前问题和修复的记录，不能据此授予整局稳定、智能或性能通过。

## 判断

这几天的实现包含可复用的原生查询、完整规划、持久化、身份校验和录制能力，也积累了明显的应急债。后者已经影响交付：不同入口分别准备材料，运行时依赖人工接线；部分门禁检查了构造、字段和来源，却没有执行即将失败的真实状态转换。代码量、强类型检查和局部门禁通过，都没有证明生产入口能完成第一批。

协调者也存在质量问题：多次手工拼装入口、猜测 DTO 字段、复制旧操作片段，制造了额外故障。继续增加 attempt 专用脚本会扩大接线成本。后续修复应进入共享生产实现；场次只保留数据、证据和身份绑定。

## 已确认的问题

| 问题 | 可复现实证 | 当前整改与验收要求 |
| --- | --- | --- |
| 只读资格漏验真实接续 | feeder `--qualify` 在安装 transition 和 attach 前返回；N37 资格为绿，实际首批因 predecessor 不同失败，业务调用为零 | 资格返回前调用实际 reducer 预演；写入仍在原 writer 锁内核验 predecessor。测试必须执行真实 reducer |
| 恢复输入继承过期账本 | basis 冻结 sequence225，实际事件226、227、228已有连续提交；当前 head228 为 `repair_required` | 共享只读事件链视图验证 snapshot、events、source-index 和 exact-next 缺席；新接续显式绑定新 head，保留旧输入来源，不能改旧证据或放宽 equality |
| 队列守卫安装标记可被继承 | 安装 Base 后，Child 覆盖 call/check_before，再安装会因继承 marker 提前返回；重复安装不同 runtime 仍粘旧路径 | 验证类本地标记、实际方法及 runtime 绑定；实际调用回归必须证明 Child 仍经过守卫，换 root 明确拒绝 |
| 录制启动交接存在保管缺口 | launch 后解析坏 request 抛错，尚未进入 retain/HOLD；旧测试只检查异常和一次启动 | 在 metadata 交接前保留真实 worker custody；异常路径仍能保管并等待原 worker，不能用坏 PID/birth 伪造身份或再次启动 |
| 自有子进程环境不完整 | helper 忽略 `sys.path` 的空项，未将父进程 cwd 实化；换子进程 cwd 后依赖消失 | 统一启动器实化空项，使用真实独立子进程验证导入，明确参数和返回类型 |
| 生产准备依赖测试模块 | public prepare 导入历史 replay runner，测试依赖未完整进入生产来源闭包 | 将真实 runner 提取到生产模块；生产和测试消费同一实现，保留原历史来源与失败样本 |

当前源码还存在按行号、源码字符串生成入口及多处 epoch 分派的债务。整改应逐步迁移到明确的类型和函数边界；本轮不以无关的大重写阻塞已复现故障的修复，也不把这些债务标成已消除。

## 本轮交付顺序

1. 并行修复共享接续预验、队列守卫、子进程环境和 worker 保管；按文件所有权隔离修改。
2. 用真实生产函数测试失败路径，覆盖缺字段、错类型、序列化往返与 qualify 后 head 前移；对实际修改范围运行 strict 类型检查。测试数量与 skip 必须明确。
3. 将新执行用例接入 CI；静态通过只授软件资格。随后通过正式 warm-forward 入口接续现存 Game，不能改冻结 N37、跳 attach、重置窗口或直接提交 FULL。
4. 工作包验证后立即按仓库规则提交、rebase、普通推送。以实际第一批结果、原生后态和完整耗时评价运行改善；失败继续保留，不能仅凭回执文字宣布整体稳定。

## 现场与能力边界

`20:01Z` 时 N37 Game PID105532 保持暂停，实际日期1082-02-09；当前账本 head228 尚未接续该 Game。N37 已失败 feeder 的任务已注销，不能重放原 launcher。首 FULL11389 尚未提交，本轮新增天数为零。现场来源为 `runtime-a37/CURRENT-SAVED-FEEDER-STATUS.json`、`ROOT-CONTINUITY-WINDOW.json` 及其事件226–228；原失败、未知请求10565/11386、T0、window2全部保留。

累计仍为5622/10950日，G2仍6/8；M6自然终态闭环、M7广度未完成。已有完整计时样本488.0427秒/186日＝2.62388555秒/日，1秒/日未达标；没有 Source32 成功首 FULL 的信用。代码质量改善、策略能力改善和端到端性能改善分别按实际证据记录。

软件整改使用统一存储策略，Root于 `20:00Z` 左右手工准入有限的软件范围，复核期限21:00Z；原受管现场期限20:30Z并未因此延长。小型准入来源：`current-saved-software-quality-remediation01/ROOT-QUALITY-SOFTWARE-SCOPE01.json`（3397字节，SHA-256 `f2af071123637f13ea2755676311d77b876628cacc83a3aeb19e8377808ad07b`）。不增加财务 take/refund，不重复读取 Driver/SAVE 正文。

后续在此追加实际修复、测试和提交结果；以上开始截点不得回写成最终成功。

## 第一批已交付：守卫绑定与自有子进程环境

实际交付观察 `2026-10-21T20:05Z`，机器同上。提交 `60f0fd81` 已普通推送 `master`，其父为并发同步后的 `86a5e795`。生产代码和直接测试共四叶：

- 队列安装器以类本地记录绑定实际 wrapper、原方法和 runtime；对子类覆盖重新安装守卫，同一类的 runtime 变更或安装后方法替换明确拒绝。实际3项回归通过、0跳过；两完整修改模块 strict/equality、explicit package、silent imports 检查通过。
- 自有 Python 启动器将空搜索项实化为父进程 cwd，补齐公共返回类型和 base image 的字符串校验。整个直接测试模块5项通过、0跳过，包含改变子进程 cwd 后导入实际项目，以及原精确 PID/出生时间/依赖来源检查。两修改叶的 strict/equality 检查通过；新 CI silent imports 覆盖另行实际核验。

这批修复解决已复现的两类失败，未修改冻结现场，也不提供整局稳定、决策提升或1秒/日信用。CI 接线与接续修复继续推进。此次 Python 调度、导入与账本边界检查不包含 CK3 脚本语义，`open_kaishek: not-applicable`；不为形式重复 CK3 机制预验。

## 第二批实际验证与首批结果

机器同上，实际观察截至 `2026-10-21T20:24Z`。共享只读 continuity 视图及真实 reducer 预验已经实现：Prepared 前消费真实 canonical head，feeder `--qualify` 返回前执行实际转换，正式写入在原账本锁内重验来源、前态和结果。原快照、缺 index、滞后 snapshot 和旧 predecessor 不会因此被写成 ready。新控制器显式绑定独立 Task、源码、旧失败和真实 head；复用原 ordinary main/callbacks，不改冻结 N37、不重置 T0/window/unknown，也不重放旧请求。

生产 replay 已从测试模块迁出，SDK 三份纯源码显式绑定，原历史 JSON 按精确字节进入运行闭包。提取期间完整测试实际暴露了隐式依赖及错误 fixture source ref，修正后原完整模块24项、0跳过通过。关键门禁9+3+1＝13项实际执行、0跳过；受影响 TypedCold 9项通过。CI 中相同16个类型检查入口联合 strict/equality 通过；启动器空 `PYTHONPATH` 的窄语义后继另以5项及两全文 strict/silent 验证。worker保管20项通过，另有真实普通子进程和线程/HOLD/日志三重失败的独立审查。capture 新增7个声明仅有本机严格检查，未宣称旧 capture 整文件通过或该提取范围已有持久 CI。

本机正式新控制器两次实际只读资格均退出0；第二次绑定冻结原失败副本，以免 ordinary.status 后续覆盖原件。`20:22:13Z` 独立 Task 启动，真实账本完成228→229接续，新增天数/周期信用均为零。**首 FULL11389 随后仍失败**：`20:23:29.567919Z` 原响应记录 SDK error，AUTO11404 报 `exact-day native clock did not stop the map`；7个周期已结算，5145→5152，但日期 raw53279256 不变，新增0日，第5153周期未结算。原 resume 与两次清理 pause 的提交不能证明停表成功，禁止重放。

该失败的15条RPC区间合计67.2186472秒，AUTO11404占40.9467705秒；小回执缺完整FULL起点，不能将RPC合计当作完整批墙钟或计算秒/日。5622/10950日、G2 6/8和1秒/日未达标不变。前置接续缺陷已被本次实机越过，原生时钟失败成为下一项实际调查；不能据此宣布整体稳定或性能目标完成。

远端 `60f0fd81` 的 [Official CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39667282093/job/119455543136) 实际失败：并发收到的 fresh-machine launcher 更新后，静态 launcher/gate 来源配对 registry 未同步，3个 LauncherProtocolTests 拒绝该组合。本地已复现，正在保留旧配对与 crossed/unknown 拒绝语义的前提下补齐新配对；未以本地绿覆盖远端失败。

本机原件在 `current-saved-software-quality-remediation01`：第二次资格stdout 19,860B/SHA-256 `e29e814fb3909986ce5960f0abd51d263bda05f1163094fd7ac73518b247d318`，独立Task位于 `forward-feeder-task02`；FULL响应1389B/SHA-256 `079550f0dd3520cbe3eed772222c18ac7fe8d8b82cc495afc1df375c8cdbf643`，AUTO11404为8779B/SHA-256 `8bf918106465ade704032d0aae72462c427414c567af15b65e5bee4b9a57b84b`。通用 future-cold basis 的 metadata-forward 尚未实现，当前只是正式 same-live-epoch pre-FULL forward，边界不得扩大。

`20:25:20Z`，CI来源配对修复已完成本地实际验证：保留原两组，只新增已核对的静态新配对；6项协议测试、0跳过，registry/测试/共享类型三完整模块严格检查通过。没有动态信任任意当前源码哈希，远端新提交CI仍须单列实际结果。

原生失败的只读分析进一步确认：同一Game/connection持续返回心跳，曾采到未暂停状态，但日期不变；owner/observer更新有长间歇，仍出现少量pump。因此不能断言完全死锁，也不能把mailbox15不变归因为时间命令未消费。Source32当前journal状态明确是 `unavailable_current_sdk_binding_pending`，下一施工应将现有 current-SDK binding compositor 接入新冻结图以获得逐命令诊断；不能热改N37或重放原11404。

原正式forward Task实际child0/bootstrap0/Job0闭合，业务结果仍为FULL失败；两种结果分别记账。Root已发原supervisor正常闭场请求，SDK/录制/Game实际退出结果待原回执，不提前称正常退出。

## 闭场及通用恢复修复

`machine_id: xenoamess-full-tower-eb9d2c1186`；观察截至 `2026-10-21T20:42Z`。原现场已经闭场：SDK queue/application 实际退出码为1/0，录制 engine/publisher 为0/0；原 owner 发送一次 WM_CLOSE 后，Game 未正常退出，最终由原 Job 清理，Game 退出码1。原 supervisor、display 和 forward 三个任务均已读回 Job0 并注销，屏幕资源以8103→8104完成释放，R0024记为 `completed-red`。不得把任务闭合或录制停止解释为业务成功或游戏正常退出。原 `ROOT-ACTUAL-GAME-EXIT-C23.json`、`ROOT-SUPERVISOR-SDK-PROCESSES-EXITED-C23.json` 与 `ROOT-RECORDING-SHUTDOWN-C23.json` 保留失败原义。

闭场小清单 `ROOT-A37-QUALITY-CLOSEOUT01.json`（4328B，SHA-256 `b08385c47956a17e5fda6f38339ed630e5db9e08b596c354e0d490dba9392f6c`）与后续媒体路径勘误 `ROOT-A37-MEDIA-STAT-CORRECTION01.json`（1695B，SHA-256 `dd4e73e4d4081d9df9bf248b4ca6cee7c4337d853e041676f5d399f25a8d1748`）位于同一质量工作包。实际 MKV 在 recordings 的 SID 同名兄弟文件，stat长度1,848,708,374B；没有读取或重新散列媒体正文，也没有获得完整媒体质量验收。原错误空目录观察保留，使用追加勘误，不能改写为当时已找到。关键证据于2026-10-23复核用途，继续保留须按统一策略重新说明，不能永久积压。

通用 `current_saved_basis_v1` 已增加明确版本的 metadata-forward DTO、解析器、builder及独立qualification；owner四个既有入口均消费同一合同。它只接续已经证明的业务状态：重新验证原资格、不可变事件链、T0/window、未知请求和 Driver/SAVE 身份，绑定保留的精确新head，零新增信用、零动作重放。业务从5145变到5152的场景明确拒绝，必须另有真实业务依据，不能靠调整ledger数字继续。

独立审查实际构造了“内容及SHA不变、FileID改变”的反例，暴露首次实现仅解析身份但未比较stat。已将不可变anchor/event/index的读取前后身份检查补回共享实现；只有合法前移的历史canonical快照按来源记录处理。实际RAM回归14项、0跳过，修复后新增身份反例另实际重验；basis、owner、continuity和测试四个完整模块 strict/equality/explicit/silent 检查通过。独立读回无本轮剩余阻断。没有修改任何冻结运行目录，未再次读取Driver或SAVE正文。

这次仍新增了约30KB的合同与回归，并没有完成架构清债：basis已约197KB，历史链验证存在重复，四处分派仍需收敛。后续应把历史链与当前head验证的共同部分抽成共享实现；不能直接复用要求“当前canonical”的校验器而破坏合法历史回放。本轮修复已经落在公共模块，场次不再新增另一套恢复脚本。

`20:43:48.945440Z` 原后台 Steam probe 再次实际返回 `offline/true`：同一机器，PID165096、出生FILETIME字符串`134362593935766296`、版本10.96.30.42及当前SteamUI来源绑定均稳定；新回执 `STEAM-OFFLINE-CLOSEOUT01.json` 为2480B，SHA-256 `7aa751a536a36e441c481491dc067c9a3a1cebca7c5c3db2605f302e68867d0b`。没有截图、激活、移动窗口或抢焦点，也没有切换Steam模式。该观察只证明此时本机离线，不是后续启动时可永久复用的准入。

## Native32生成接线与持久门禁

本包修复的是诊断链的来源接线，还没有修复原生时钟或取得实机journal通过。旧适配器只更新Entry和Queue，漏更新Outer的两项external pin；原10项测试未调用这条三消费者接线。已改为具名的Entry/Queue/Outer返回类型，实际保留另外24项pin与Outer剩余AST，并覆盖错误来源、歧义和UTF-8边界。完整13项、0跳过，两个完整模块strict通过；实际N37材料的三文件RAM回归也已执行。新独占夹具实测峰值1,394,144B，清理后Root确认ABSENT；旧DLL、4TU和Source31历史资格未改。

公共Plan升级为v2、Quote为v3，新增必填的显式null或三份ExactRef合同。非null只能接受原历史binding权威、当前SDK BASE/anchor及机器ID一致的确定性重组结果；不接受任意当前哈希或把运行目录同字节副本追认为原来源。Entry/Queue/Outer在原固定点封包前一起接线，binding单独作为数据输出；全部依赖显式进入来源闭包，canonical入口仍为8，完整闭包上限按新增依赖收敛到66。null保留原先可用的普通FULL路径，不把诊断缺口变成全场阻断。

`2026-10-21T20:47Z`、机器同上：与持久CI相同的18个完整模块联合strict/equality/explicit/silent/no-cache检查通过；关键runner发现并执行21项、0跳过，包括continuity11、Prepared3、真实独立SDK子进程1和Native32公共合同/生产者6。Plan/Quote更新后的原完整preflight模块又实际执行24项、0跳过，31.278秒，夹具峰值557,056B并清理。两套fixture均由Root再次stat确认ABSENT。新增13项native适配器及6项公共生产者测试已接入CI，Hosted fixture显式使用runner临时根并拒绝跳过；不是本机默认D盘路径。

真实完整compose曾调用原业务验证器，旧N37 Plan因 `closed Driver identity` 被拒绝：现场运行后该Driver已变化，目前没有新的5152业务资格，不能改stat或metadata-forward绕过这项真实准入。后续RAM封图模型若使用历史stat，只能计软件生成集成；必须明确其测试替身，不能授予当前机器、物理部署或运行资格。

Root另把上述真实转换预验、全消费者封图、失败退出码传播、CI零跳过和证据分层要求写入AGENTS.md。这是持续的编码规范；不能用新增规范条数代替实际测试。`20:48:13Z`唯一watcher确认 `9421d65f` 的 [Official CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39670436802/job/119466574874)仍在执行，尚未到strict步骤40；Linear历史检查已成功。此处不宣称远端整套CI通过。

`20:49:02Z`同机器实际RAM封图模型通过：使用原材料、Source32引用和当前14份生产源码，仅Driver.stat两次返回历史basis记录的身份，其余read/stat真实；审计记录Driver/SAVE正文尝试0、所有写尝试0。原compose实际输出165文件/3,618,719B，8个canonical和66个closure条目的最终SHA全部逐一匹配实际输出，Quote v3往返通过，未来物理根仍ABSENT。模型依赖当前机器保留的旧材料分类器，因此仅记一次软件集成，不冒充便携CI、当前业务资格或物理部署。可重复的便携覆盖是上列6项生产者用例；真实过期Driver的拒绝仍保留。

## 2026-10-22恢复施工：补真实消费者及当前业务证据

`machine_id: xenoamess-full-tower-eb9d2c1186`，实际观察截至 `2026-10-22T02:05Z`。用户恢复任务后，Root重新核机器、统一策略、ALL431/SHORT626及实际容量；旧21:00软件准入没有自动续用。新有限软件范围到03:00，来源 `current-saved-a38-recovery-prep01/ROOT-SOFTWARE-SCOPE0300-01.json`（3215B，SHA-256 `c3e76784aeab271ea65b3626330889307f1a6370ee575f39932c2dd3a92ed7c7`）。当前仍未启动新Game。

`05b28a55` 的 [Official CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39673812993/job/119478320935) 已真实失败：步骤95的Workshop缓存测试固定要求14项，而正式清单已有15项；步骤40严格类型及20/21/23/47/48/56/69均成功，Linear成功。已将测试改为核canonical与独立验收目录的完整集合、唯一性及各产品身份，保留未发布产品null ID拒绝和原预算断言。原失败真实复现，恢复本checkout缺少的跟踪依赖后，完整13项实际通过、0跳过；修改方法strict范围无诊断，整叶历史56项诊断未称全绿。

新的前置独审发现上一轮漏验：真实材料entry62、external26、canonical8；新增三份Python与binding使完整图66，但继承Outer构造器仍硬限64。上轮只核封包与SHA，不能证明该构造器可运行，撤回其“完整消费者无阻断”范围。修复进入公共renderer，canonical8保持；真实继承构造器旧65/66拒绝、新65/66通过、67拒绝，原哈希、外部26项、缓存来源和入口缺失负例继续拒绝。最终20项回归通过、0跳过；Root将新5项接入持久CI，并再次实际执行5/5，夹具峰值125952B、清理为ABSENT。普通源码仍限1MiB，原响应另有显式2MiB能力，不以提高全局上限遮盖接口差异。

Q38实际Source32 thin reader已经执行其真实源码资格函数通过（02:00前、0.183秒），保留历史Source31/DLL资格的独立含义；不是运行态Native通过。旧5152业务缺口正用共享settled-prefix合同补齐：7个周期的明确查询/婚姻冷读回与末尾真实失败advance分别记录，不能按primitive计数或query前缀认定无效果。唯一Driver取证已完成42841812B/`34ef7a19baad919b4ca7d05a8c29b5a8d58f612b671b75cbc2b24caad8206eae`，同held HANDLE下拒新WRITE/DELETE、前后FileID及mtime稳定，body/hash/parse各1；SAVE正文/哈希0。14条原始post-checkpoint history保留在有界压缩opaque中，末尾unknown不归入只读或成功。恢复包及真实完整消费验证尚在施工，不提前授予当前业务资格。

另一个前置接线缺口是旧launcher硬传2GiB artifact cap，与本轮1920MiB联合封套中的artifact净帽不符。正在通过显式Typed Plan/Quote字段同步生产者、实际argv、绑定与测试，禁止手改生成图。媒体保持continuous既有合同与画质；本轮423MiB媒体及20分钟边界由Root实际监控、到界请求原owner闭场，不能宣称旧continuous worker已自动实施这些新子帽。新版Full为32018B并已通过原四消费者数据校验，仍不能替代Game执行准入。

`2026-10-22T02:21Z` 同机器增量：Plan v3／Quote v4 的必填整数 `artifact_cap_bytes` 已接到实际 launcher argv，错类型、越界、两端不等及旧 wire 均拒绝，原 reply reserve 保持。完整 preflight 24项、关键联合34项实际通过，均0跳过；联合18个完整模块 strict/equality/explicit-package/silent-import 检查通过，18份来源前后SHA相等。关键34项来源回执为 `current-saved-a38-recovery-prep01/ROOT-MANDATORY34-QUALIFICATION01.json`（1954B，SHA-256 `9303c8c81ccf3a71ebab35231ee72f2e72327efb0d139ea9d6bdcf0d7a7da5ef`）。联合类型检查使用本机实际 Source32 依赖；不把它混写成远端CI结果。

恢复合同现显式区分 native observation、formal ledger readback 和 returned SDK error；实际失败 history 的五字段形态及原 CLI／subprocess 两种 Task 闭场运输格式均进入共享解析，不能删字段或虚构退出码。7个原结算周期到5152、再接至保留head230的完整RAM包已通过原四入口，物理发布重读仍待完成。没有重读Driver/SAVE正文，没有重放11404，也没有新Game或新增游戏日。basis继续增大至约215KB，历史分派和重复验证的架构债仍在，未宣称清债完成。

## A38实际失败：录制父目录没有进入准备合同

同机器，实际观察 `2026-10-22T02:39Z`：恢复包物理重读和公共 Prepared 已通过，完整 supervisor `main` 两次实际运行到首个 ADMITTED 写入前，随后按同一顺序执行器检查退出码并注册／启动。Game177352实际出生 `134371098919795565`，原注入器退出0；Desktop1放置2560×1440、用户Desktop2与焦点不变。上述“完整”仅指 Game 准入前缀，**没有覆盖录制的实际启动调用**，不能外推为整条运行链通过。

Root随后漏建 `runtime-a38/recordings` 父目录，而公共 prepare 当时也未物化／校验它。真实 display 在 capture `launch_recording:440 → root.mkdir()` 抛 `FileNotFoundError [WinError 3]`，尚未写job或创建worker／OBS；actor的finally等待publisher又使异常延后显示。这是新的前置验收缺口，不能归因为OBS慢启动，也不能用补目录抹掉原失败。原stderr1324B（CP936），SHA-256 `15fcdac3d9dce9d912456cf3b526a351c6f1542db7dbabe98648ec49035ab170`。

原supervisor已正常收到Root停止请求并闭场：publisher实际退出0，Game的WM_CLOSE未获正常退出，原Job最终清理为exit1；两Task均child1／Job0并注销，screen8117释放。SDK与录制worker均未启动，未增加ordinary或游戏日信用；R0025记completed-red。小型闭场证据为 `current-saved-a38-recovery-prep01/ROOT-A38-ACTUAL-CLOSEOUT01.json`（3498B，SHA-256 `78ed104c37446342a59252556ab97300b1134e0a64f062f6d7e4849ca9811e1f`）。03:00前同一有限范围正把录制父目录的物化、引用绑定与真实文件系统反例补入公共prepare；冻结A38不修改，新图另行验收。现有recording-only恢复合同要求真实旧worker／OBS／SID，不能拿虚构旧证据用于这次worker创建前失败。

`02:44:24Z` 同机器：公共prepare已按批准根物化录制父目录，核对quote中profile的精确引用与路径，拒绝文件、非空旧SID、重解析点及错误父路径；Prepared发布前再验目录身份。完整28项（原24＋新增4）实际通过、0跳过，夹具峰557056B且最终ABSENT；两修改全文联合strict/equality/explicit/silent通过。首次新增测试暴露缺parse_json导入，首次严格检查暴露test经core重导出，两项均实际修复，不掩去中间RED。独立窄审无剩余P0/P1。最终core130497B／`6c0243d0cde729c3429dbe5145975e8cfd7c62b3d602aa8755447a1f80b947dc`，test82152B／`1fd0cbb028d6fe968033d2b1543c54fb065bf4c7a74da4ffdfb20f8a12c7f8ff`；尚不能据此宣称录制或首FULL实机通过。

## N39首批实际推进成功，闭场仍失败

`machine_id: xenoamess-full-tower-eb9d2c1186`；观察截至 `2026-10-22T03:10Z`。共享录制目录修复已随 `4900a522` 普通推送。新图N39实际启动Game259436、加载当前检查点并开始受管录制；首个不可变原始游戏帧和合成帧均为2560×1440，Root直接审看地图及1082-02-09日期，未见旧蓝窗或影片标题。Steam准入和闭场状态均由后台原生probe确认，无截图或焦点操作。

首FULL11407实际成功：30周期，5152→5182，日期raw53279256→53279400，即1082-02-09→1082-02-15，新增6日，累计 **5628/10950日**。T0、window2、创始人31254和当前角色40526保持；10565、11386、11404的历史未知请求不重放。FULL响应2204B，SHA-256 `a21abc31859d57ed5f9acc54d580d7e7935a877cc65b2aac9ab7ce0901ccd736`。完整批墙钟41.4099253秒，**6.9016542秒/日**；60条RPC合计30.6211233秒，另10.7888020秒尚未归因。该样本不能证明比旧186日样本更快，1秒/日仍未达标，G2仍6/8、M6/M7未完成。

SEM11468之后的SAVE11469实际于03:00:16.065768Z至03:00:20.995600Z完成，返回saved、overwrite_confirmed=true；新SAVE117661285B，SHA-256 `c52326604ce1d6aefc493c1bc5d088e26600b001a59978a93ca951b383440ca9`，history_index5944。Driver只获得 `WRITE_REPLACE_RETURNED_NOT_FSYNC`，不能称已fsync。当前raw累计状态仍保留旧维护检查点11372，必须由公共maintenance projector生成新seed；不能改写原raw，或把旧Q38资格当作当前文件身份。

实际闭场：SDK queue/application均exit0，录制engine及publisher正常退出；媒体stat395613446B，probe为2560×1440／30fps、658.333秒。没有重读媒体正文、重散列或最终媒体质量验收。原supervisor03:00:56.641Z提交一次WM_CLOSE，未获得正常退出，03:01:31.609Z由原Job清理Game为exit1；不是整场GREEN。三Task实际Job0并注销，screen137以8124释放，R0026记 `completed-red`。闭场清单 `current-saved-a39-runtime-prep01/ROOT-A39-ACTUAL-CLOSEOUT01.json` 为8704B，SHA-256 `0cb09179555d075cf85e46f501db15808511fff858898d530ca44aae3f1e23a2`。

Root还有一项调度错误：feeder已于03:00:00.181Z按期限停止，但手工SAVE于03:00:15提交、Root STOP于03:00:50写入，晚于03:00业务范围。保存成功事实和超期事实同时保留，不能用清理宽限追认新业务准入，亦不能声称旧continuous worker自动执行了媒体子帽或Root截止守卫。后继修复进入共享请求准入，并覆盖permit之后、真正MCP调用之前再次到期的反例。

03:08:14.792367Z后台probe再次返回offline/true：Steam PID165096／出生FILETIME字符串`134362593935766296`、10.96.30.42及当前SteamUI来源保持。此观察不能作为后续启动的永久准入。新的03:45有限软件范围来自 `ROOT-SOFTWARE-SCOPE0345-01.json`（8762B／`141b6ecda3aec3ae485847d14d95cc329a38e414943f2d442e3baa78cf47f8b1`），没有续用旧03:00票据，不授权新Game、SDK或录制。当前并行施工是共享截止守卫、通用settled-progress闭场合同及首批分段计量；均未提前授予完成信用。

## 本轮共享整改终验

同机器，实际验证截至 `2026-10-22T03:43Z`：新维护seed及正常settled-progress闭场已通过实际Source32 checkpoint validator、cold inputs和prepared SDK消费者。basis10372B／`71d9f017624daab0dfc6a02f05739ffe45361c3e2a29f51d576ce09c2a7b50c3`，资格2147B／`fdf2683744e030a3db0d287cc987b8ad9a2297137069f7245109c97db8c8454aa`。Driver实际物理读一次，原SDK对SAVE散列一次，全部读锁和取证进程已释放。婚约sidecar已按当前原字节另存，未沿用不相同的历史副本。

Root按持久CI同一选择器实际执行 **57项关键回归＋34项完整preflight，全部通过、0跳过**；完整20模块联合strict/equality/explicit/silent通过，最后源码pin稳定。面板及资格表另3完整模块按相同严格口径通过。关键回执1409B／`7536ff67dfb5f31644cd0e715c9219e4bd88625d35c4c78a34867b48ca764be1`，最终联合类型回执6182B／`d31204dea96a6abcfcb7316528869e3abb0b98aac34102a48c25f18452a24486`，均在Q39。首次57项中的新组合夹具使用0字节Python源，被真实正长度来源解析器拒绝；已仅修该用例为合法非空stub并同步SHA，再全量重跑通过，未放宽生产守卫。首次类型工具进程缺checker搜索路径也已明确纠正，没有把工具启动失败称作检查通过。

新cold使用Planv4／Quotev5，必填 `renderer_override_ref` 明确区分null与ExactRef。非null会在继承图中核双旧body／旧Outer tuple一致，再同步两份新body及唯一external项，其余25项和最终封包保持。当前材料的真实RAM compose输出165叶／3649995B，双21038B渲染器、external26、canonical8、closure66以及165份最终len／SHA全部逐项通过；null完整compose也通过。便携永久覆盖包括真实intake→继承构造器、来源及缓存拒绝；145份历史材料的完整compose仍是本机集成，不冒成便携CI。旧到期Full未因此获得执行资格，新A40仍未物化或启动。

首批分段计时builder、真实保存显示、推进中文行动及相应强制零跳过回归均接入持久CI；新图Gate还须实际调用计时builder。此前远端exact4900的Official只有部分步骤观察，不能用本机终验补写远端全绿。连续Game正常退出、1秒/日、G2剩余两项和30年长局仍未完成。完整当前恢复与继续步骤见[Source32／N39交接](../handover/2026-10-22-robert-source32-n39-quality-handoff.md)。
