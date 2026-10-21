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
