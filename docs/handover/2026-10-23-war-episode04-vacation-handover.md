# 第四集战争机制视频：2026-10-23 度假交接

> machine_id: `desktop-3fevhd2-1c74096080`。本地日期为北京时间2026-10-23；除特别注明，本文使用UTC（北京时间=UTC+8）。本次收尾按用户“温和地收尾手上的每件事，然后编写交接文档到docs”执行。承接[上一份交接](2026-10-22-war-episode04-vacation-handover.md)，最新机器可读状态见[本次闭场JSON](evidence/2026-10-23-war-episode04-vacation-closeout.actual.json)。不同机器只能复用代码与知识，不能继承安装、离线、容量或实机资格。

## 当前结果

- **正式动态主题10/11（90.9%），剩余R05自然低补给实体减员因果证据。** 这是机制主题比例，不能作为整片完成率。R08计数建立在已接受的有限“同次净入账中的军费抵扣”证据上，不代表独立军费付款、付款人或完整周期均已验收。
- **新版47段派生视频实际生成0/47。** 全47段安全字幕配方及实际执行器已经冻结并通过源码检查；R05正证尚缺，未运行新版逐段编码、合片或新版全片验收。
- 现有23:58.667黄色47段审核片仍是旧版，未被新R08内容或R05替换。OneDrive审核片、全部原始录制、图卡、配音继续保留。整片人工1×听看和用户签收仍未完成。
- 已停止新Game、SDK、录制、回收与发布。**最后RunID仍为R0243；新SceneB没有分配RunID，没有启动Game、SDK或Film，没有普通推进或新Save。**
- 先前45项来源文档已完成正常非强推及当时远端读回；后续R0241新证据、R0242/R0243修复、新47段源与本次交接尚未作为新成果全部提交/推送。不要把外置冻结源等同于已入库。

当前可看片：[OneDrive黄色审核片](C:/Users/1/OneDrive/CK3-War-AI-20260923/CK3-Episode04-Mechanics-Yellow-Review-20261022-a01.mp4)，43160帧/30fps、72484128B，SHA `822963261dad6abdf63c42c66efb13de24f77a04f74e45a987ca0ada18d8792f`。已有CFAPI客户端同步记录属10-22T08:11Z历史，未在本次收尾重做云网页下载或声称新的远端SHA。

## 现场与关闭状态

下表均属于本机 `desktop-3fevhd2-1c74096080`。Root于20:03–20:08重新只读核对机器身份、进程、counter、Git和保留文件；原现场owner于20:04补查。最终容量观察时间以文末实际快照为准。

| 对象 | 实际状态 |
| --- | --- |
| canonical RunID counter | `last_sequence=243`，`last_run_id=desktop-3fevhd2-1c74096080--vanilla--R0243`；原更新时间19:01:26.862083Z。a252从未提交。 |
| CK3 / FFmpeg / 新SceneB host与SDK | 现场owner及Root只读查询均无匹配进程；本任务owned Popen为0。未强杀其他程序。 |
| 新SceneB临时Steam屏幕占用 | 原owner、keeper、release均原wait0；**CAS8303，done/resources=[]**。owner原工具session2119已wait0。 |
| Steam离线 | 最后新鲜四原图采集19:57Z，Root直接看见“离线模式”及Steam窗口x0→20→0变化。nonce被更新通知部分遮挡，仅直接看到455→889尾部变化；完整字符串来自报告，未声称整串均可见。托盘陈旧时钟未作新鲜度证明。未切在线，下次实机必须新取。 |
| 新SceneB元数据 | a02全链已冻结、停写；prepare/plan/preflight、1736源Pin/53公共调用方的首次claim拒绝、host首次Savecopy拒绝均实际通过；未越过首claim启动游戏。 |
| 旧R0243 | public原wait2、host0、Game0、keeper0、allocator0；正常GUI退出，保存勾选已取消。release CLI原等待未持久化为null、supervisor原等待null，均保留，不补成0。实际后续总线读回CAS8300 done/resources=[]。 |
| Git临时HTTPS guard | 原timer/子进程已于17:59正常恢复，原wait0；config 12174B / `a4a0343ee9360e1786e6fb71c352c9678d254968b9b75b8537a48ed8d2bb2262`，lock不存在。无遗留恢复定时器或CI watch。 |
| Root/CAP/源码scope | 各作者和未用预留按实际闭账释放；本次只留下两份docs的有限写入与最后关闭回执，最终零预留见独立final。 |

关闭入口：

- [Root现场与C银行关闭](C:/ck3-e04-resume-20261022-b01/root-phase9/VACATION-ROOT-LOCAL-STATE-AND-C-BANK-CLOSED.actual-a01.json)，2288B / `aa257c77bd96e52c57898168bd3aaed392caf6ca0ff8939c338cad12acc914a9`。
- [SceneB Steam关闭](C:/ck3-e04-resume-20261022-b01/r05-progress-b01/steam-prelaunch-a01/CLOSED.actual-a01.json)，2508B / `f83198db22da8e4d33e986d63c0ee68a0acc613848945d82cc4fceff157fba7b`。
- [旧R0243 owner关闭](C:/ck3-e04-resume-20261022-b01/r05-progress-a01/live-ops-a02/R0243-OWNER-CLOSED.actual-a01.json)，5683B / `c73965a854ca0027fd8231767165ae4143391d23a2b16493157421fbf2506eb4`。

## R08已取得什么

[R0241有限镜头接受回执](C:/ck3-e04-resume-20261022-b01/r08-film-qa-a01/ROOT-R0241-R08-SHOT-ACCEPTANCE.actual-a01.json)已将正式主题9/11更新到10/11。角色31254，自然日期53146872→53146896（1066-12-30→12-31），原父实例中a=384653、b=0、c=273262、d=0，scale=100000；净额111391完整入账，钱包25455910→25567301。

这证明**军费分量2.73262金币参与同次净额计算，净加1.11391金币**。没有单独军费wallet debit；payer、cadence均未取得，recurring_payment_observed=false。原full_R08_qualified、business_pass、opportunity_complete仍为false。不得改写成完整“实际军费付款卡通过”，也不得再次从净额中扣军费。

原始连续录制：

- [raw.mkv](C:/ck3-e04-resume-20261022-b01/r08-settlement-a01/camera-raw-a01/r08-postload-a01/raw.mkv)：29175414B，SHA `2093104a5ba12db634617efe9ffaa7c12563559847bf994fb7394b08787a0de1`。
- 1280×720、30fps、1332帧、44.4秒、无音轨。完整解码和PTS/DTS通过；Root实际抽审45个contact格及7张全分辨率帧，未声称逐帧人工看完。
- 接受源区间[120,1110)，当前编辑选区[180,1051)，871帧。精确原生事件到编码PTS仍为null，不把可见金币变化帧当成精确事件时刻。
- N06-05/N06-08两段新配音及F13新图卡已经实际生成，已进入最终47段配方；新派生MP4未生成。旧两段专用字幕源曾有分页边界问题，后继统一47段安全分页源已经替代，恢复应以final47 a04为准。

## R05为何还没闭合

R0243实际进入了暂停地图，实际EXE/DLL身份通过并完成MCP初始化。随后普通推进前，Selection层和普通适配器重复调用会创建唯一文件的readiness等待，触发 `FileExistsError: readiness-window.json`。**本场普通新增游戏日、AUTO、Film、新业务Save均0**，不是低补给阴性实验。游戏已正常退出，没有热续现场。

就绪后继现已修好并冻结：由真实Selection→原CaseClient构造/单次wait_hold→新适配器→原CapacityPort/RemotePort/Frame/ProgressScope走到首业务动作前拒绝。单次readiness、错帧/错绑定、Save finally、未知Save不重试、原正常关闭路径均保留；4文件strict、三组真实调用链冷验及隔离导入原wait均0。源码检查替换的是明确测试接缝，未发真实Game/SDK动作。R0242的CallToolResult注册/SDK返回类型问题此前也已修复，R0243进图已实际越过该初始化问题，不必重做旧矩阵。

后继SceneB仅完成a02材料化和一次新的Steam离线检查，随后因用户度假取消；其20Z源码窗口、21Z前瞻Game用途均不能跨假期热续。a10是未消费的用途/预算方案，**没有完整有效Game执行财务卡，没有新RunID，没有普通推进授权**。

R05正式阳性仍必须同时具有：

1. 自然、未篡改局面的补给writer入场值0≤stock_raw<1000000，scale100000，即实际补给低于10。
2. 同次callback→调用父实例→对应补给writer→正向物理扣兵的可核链路；没有环覆盖/缺口、身份或成员变化等歧义。
3. 真正连续Film和完整HUD，实际原生回执及正常关闭；净兵数下降、enable ACK、人工stock=0不能替代。
4. 没有候选为NOT_PRESENT，缺输入为UNKNOWN，不把null当0。普通规划器必须保留真实战争、外交、建设等全部能力；遇陌生弹窗按原生采集→第一显示合法项→读回→离线补规则处理。

全局512条环不保证一天不覆盖；若覆盖仍保留UNKNOWN，不能用净差分补证。

## 恢复输入与冻结源

全量文件Pin见闭场JSON，以下是少量主入口。外置根前缀为 `C:/ck3-e04-resume-20261022-b01`；这些源可读，旧作用已停写。

| 用途 | 当前入口 |
| --- | --- |
| 普通恢复Save | [R0241 canonical](<C:/ck3-e04-resume-20261022-b01/r08-settlement-a01/state-a03/profile/save games/xar_checkpoint.ck3>)，71743357B / `e8e4a89d1ff5dbea0738a1e0d84e68e3c723aa5af8b3783f70356789e36c6b1f`，Native FileID128十进制字符串`281474979304802`。角色31254、日期53146896；不是one-life资格。 |
| 原完整普通推进源 | [progress-source SOURCE-FREEZE](C:/ck3-e04-resume-20261022-b01/r05/progress-source-a01/SOURCE-FREEZE.actual-a01.json)，17171B / `e40f27fcc081f5f1b886e7952905a97a81ccad30472b4eeb919760987448918b`。 |
| MCP初始化修复 | [registration integration](C:/ck3-e04-resume-20261022-b01/r05-mcp-registration-fix-a01/RUNTIME-INTEGRATION.actual-a01.json)，13138B / `b8b92347253ae3d7b0571853545b2a8ae2bea78537e4e98bfcd9f1f55646b35e`。 |
| 单次就绪及SceneB Film接线 | [ready-once integration](C:/ck3-e04-resume-20261022-b01/r05-ready-once-source-a01/RUNTIME-INTEGRATION.actual-a01.json)，19626B / `fb6e0fb903eba7930b107f2f3c546726ac8c66922f85b9cfb24c9430dc33bae4`；[freeze](C:/ck3-e04-resume-20261022-b01/r05-ready-once-source-a01/SOURCE-FREEZE.actual-a01.json)，6786B / `7c28c1abb6c824718f2e78a2979ee69fc0eab063018966acfd08f32d1255eb09`。 |
| 最后准备基线，未开局 | [a02 FINAL-FREEZE-AND-CLOSED](C:/ck3-e04-resume-20261022-b01/r05-ready-once-runtime-a02/FINAL-FREEZE-AND-CLOSED.actual-a01.json)，7493B / `f0914d6b1d94e701efc9a04cffd905dcd31445359b62a15b78f55b10443e7e20`。runtime、prepared、source-index及COMMANDS都由它绑定。 |
| 最终47段配方 | [final47 a04 freeze](C:/ck3-e04-resume-20261022-b01/final47-source-a01/a04/SOURCE-FREEZE.actual.json)，14738B / `ec15ee5a4afb60d6401ddcdd3de8484b4f4e9cc11328b024f948db80da24ea1f`。 |
| 实际47段执行器源码 | [executor a02 freeze](C:/ck3-e04-resume-20261022-b01/final47-executor-source-a01/a02/SOURCE-FREEZE.actual.json)，15117B / `c24e8c0150d9e31a104f46a77e5243ee71ce2c32eaa6a63c44fe8a3dc06fa982`；[Root源码复核](C:/ck3-e04-resume-20261022-b01/root-phase9/ROOT-FINAL47-EXECUTOR-SOURCE-REVIEW.actual-a01.json)。 |
| 真正R05接受合同 | [R05-ACCEPTANCE-CONTRACT.source.json](C:/ck3-e04-resume-20261022-b01/final47-source-a01/a04/R05-ACCEPTANCE-CONTRACT.source.json)。当前只有合同，**没有实际R05接受回执**。 |

R0243当时实际游戏为CK3 1.20.0.4/build25734779，EXE101040248B，SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；加载DLL14397440B，SHA `062b2ae3639c230d2ca4552d5de67c9536605b1fbda2045c040d3fd6f25ca746`。原Game PID33292、created FILETIME字符串`134371694124720351`。这些是该场当时的读回，不证明未来安装或另一台机器。

### 成片下一步

47段中46段分页边界及1段行内断行需要更新，所以要**实际重编码全部47段**，不能只替换R08两段后保留44段旧烧录字幕。已验证共同中文分页232页，≤32字/1370px/两行，保留语义句时序。44段的原片、图卡、旁白输入保持既有配方，派生视频全部新产；N05-01保留最终配音与K17，不回退到旧baseline。

executor已实现独立实际媒体卡→真实R05接受→CompleteRecipe47→逐段一次编码/实际解码计数→新root内work/CAS双名硬链接→真实47段timeline→一次concat/remux→整片解码计数和实际元数据消费。8组纯检查及3文件strict原wait0；Root独立核68个Pin并审关键代码。**没有启动Native Job、FFmpeg或ffprobe，不是媒体产物验收。**

将来只有Game正常闭场、真实R05通过、独立Root媒体用途和CAP实际媒体卡均齐全，才能调用 `produce_final47.py execute CARD SHA256`。实际媒体卡schema为 `xar.capacity.final47-media-execution-admission.v1`；逐字段合同见executor README。冻结源内source-check旧截止已过，不能用旧源码检查卡重新写源。最终仍须实际PTS/音轨/字幕/画面复核、人工1×、OneDrive本地哈希及客户端同步核验和用户签收。

R05镜头接受schema为 `xar.e04.final47.r05-shot-acceptance.v1`，严格19字段；business_result须是真实同machine/run且business_qualified=true的Root因果结果，原native Window不能直接替代。raw身份使用retained_sha256及mtime_ns/st_dev/st_ino规范十进制字符串，不加shot_review别名。

## 存储闭场与未执行回收

统一使用[通用策略](../storage-retention-policy.md)及[参数v1.0.0](../storage-retention-policy.json)。C配额449025409024B没有提高；当次24个原生系统文件实际分配量下界仅支持保守扣除512MiB，另保留4GiB增长与32MiB不确定性，未删除/修改系统文件。该限时复核不授权度假后自动复用。

| 本轮代表操作 | 已发生的实际结果 |
| --- | --- |
| R0243重建shadercache | 精确3856件，164765152B实际回收；Root逐项确认缺席、保留目录及源Pin。原cache已不可读，不造同名替代证据。 |
| R0243恢复输入副本 | 精确1件，71745536B实际回收。R0241 canonical同句柄完整SHA/Native身份后验仍一致；删除的是重复恢复副本。 |
| R0243三份冻结JSONL无损NTFS压缩 | 105218048→46657536B，**实际节省58560512B**。原路径、内容SHA和FileID保留；各一次FSCTL+Flush，真实时间/属性差异已记录，未手工还原时间。不是删除证据，未额外从配额再扣一次。 |
| D Git MIDX一次标准回收 | 实际净释放816656384B；保留全部唯一对象/126 packs/178567 OIDs/38 promisor。已完成，不再expire/gc/repack或手删pack。 |
| 旧47段cue CAS及1份whole CAS | **实际删除0，48件全部仍在且attrs33。** 145133568B仅是候选量，不能计为已释放。OneDrive审核片不在候选中。 |

readonly48的计划和Root精确审查已经形成，但旧普通入口正确拒绝READONLY|ARCHIVE=33。后继仅提出新有限范围的FileDispositionInfoEx/DELETE|IGNORE_READONLY_ATTRIBUTE单次处理，未准新control、未调用Native。最后新producer严格类型检查原wait1、3项类型错误（ref重复定义、Handles缺kernel属性、except变量error作用域），已停止，不为度假继续修。新控制根 `r0243-readonly-oldmedia-recovery-a01` 未建立。旧计划20Z仅保留作定义，未来执行必须修复窄边界、重新核现有输入/永久资产索引和目标身份，并取得新预算/Root精确复核，不能直接重放原批准。

- [48件精确计划](C:/ck3-e04-resume-20261022-b01/r0243-derived-and-old-video-recovery-a01/OLD47-AND-FULL-EXACT-PLAN.actual-a01.json)：28637B / `97d8d5a213a6440c7651672e03f61014440547ba911f22b39b1376463b332991`。
- [重建及当前输入资格](C:/ck3-e04-resume-20261022-b01/r0243-derived-and-old-video-recovery-a01/OLD47-AND-FULL-REBUILD-QUALIFICATION.actual-a01.json)：79631B / `258a0e66fc601221f529f5e594e4a300584095b93831164d95b5ccb426ba6522`。203份原片/图卡/配音/字幕/来源及永久索引已核；93个新渲染输入路径不消费旧MP4。
- 精确候选来自 `r22-mechanics-render-a01/native`、`r22-n05-weight-explainer-a01/native` 和 `r22-mechanics-full-a01/attempt-a02/native`；Root用途a01曾把cue父目录写窄，a02已纠正并绑定48精确行，无扩大删除范围。

闭场fresh快照：[实际关闭写卡及held快照](C:/ck3-e04-resume-20261022-b01/capacity/r05-phase2100-control-a01/VACATION-CLOSEOUT-AND-TWO-DOCS-ADMISSION.actual-a01.json)（2026-10-22T20:12:20.764199+00:00）。

| 卷 | 实读空闲B | 同次预算结果 |
| --- | ---: | --- |
| C | 67040788480 | 有限配额下余量+1140535296B；包含最后C64KiB关闭预留，未证明完整项目精确占用。 |
| D | 22495764480 | 策略floor余量+885563392B；包含docs96KiB及同一ledger最终CAS峰1MiB。 |

14个旧作用的未用预留已释放，不是物理删除。此刻仅CAP有限关闭尾段及两份docs/最后ledger CAS仍活动；完整Game池没有准入。

本文及闭场JSON保存文档写入前的真实held快照；最后零预留/零作者以 [VACATION-ALL-WORK-CLOSED.actual-a01.json](C:/ck3-e04-resume-20261022-b01/capacity/r05-phase2100-control-a01/VACATION-ALL-WORK-CLOSED.actual-a01.json) 的实际回执和最后ledger CAS为准。两份docs先固定Pin，再由capacity独立核验并释放其D96KiB、既有ledger原子CAS峰及最后小型C关闭预算；不预填文件自身或最终回执SHA，避免自哈希循环。除了必要收尾，无后续回收任务或自动续跑。

## Git与发布边界

- D主仓仍detached `bc63851081462413d0cc6ebe62e37490707ee6a9`。原tracked树clean；原10-22交接两件保留。本次只新增这份10-23交接及JSON，未提交/推送，也未切分支。
- 唯一发布W：`C:/ck3-e04-resume-20261020-a01/r06-resume-a02/integration-worktree`，master `ca58a620c3a6fac67ad814ba346931920ca656ed`，本次收尾Root完整status为空；无rebase、无index.lock、无guard/CI watch在途。之前本地origin曾观察领先32提交，这是历史本地观察，不是本次fresh远端结果。
- 先前45项文档正常非强推到d347683f…并当时读回；后续W更新与CI记录保留。新R08/R05/47段外置成果尚待新的来源包/最小入库，不将它们复制覆盖D运行树后继续旧场。
- CI不能宣称全绿。ca58保留的Official run39794617729为failure（共享acceptance的SimpleNamespace/case_imports fixture错误，9项组内1 error）；watch传输错误与服务端结论分开。后续上游修复和其他CI观察不能追认本机冻结源已通过。恢复后按实际新HEAD最小复核，不为文档重跑全仓/实机矩阵。

## 保留与恢复顺序

下次用途复核 **2026-10-24T10:00Z**；必要输入限期保护至 **2026-10-29T10:00Z**，R08接受回执已有更晚16:30保护的按原件保留。到期重新判断用途，不自动续期，也不自动删除。只保护实际必要Save、R08 raw、当前审核片、最终图卡/声音/配方、冻结源与代表性失败/关闭证据，不保护整棵外置目录。永久单资产、5项Workshop本地禁回装和唯一DACL恢复备份仍按独立长期指令执行。

恢复时：

1. 读本交接/JSON/独立final；重新核machine_id、统一策略及双卷空间。**不要复用20Z/21Z一次卡、purpose、RunID或旧待件循环。** 所有本次作者已停止，没有可热续的Game。
2. 先从现有黄色审核片做人工完整听看，记录具体内容问题；无需为看片启动CK3。保留当前OneDrive原件，尚无新版成片或新的云端下载SHA/B站发布。
3. 需要R05实机时，新独立用途/窗口/有限source与runtime/prepared/Scope；复用已通过的registration/ready-once逻辑。Film源含SceneB常量，换scene时仅作明确来源绑定后继，旧冻结根不改。完整公开prepare/plan/preflight和首claim/首Savecopy边界通过后，再新鲜Steam原图、唯一allocate、实际财务卡和≤30秒紧邻run的原生离线probe。
4. 上次1200MiB方案为profile640/driver304/Other224/物理不确定32，30实际日/256 AUTO/1 Film；它未获本次完整Game资金，不是下一轮自动额度。启动前必须覆盖完整1800秒就绪和1050秒正常关闭；每次AUTO/scout仍按原Native容量guard，不事后抬帽。第一次PRESENT才唯一Film，UNKNOWN继续合法普通规划，不能许诺下一场必有阳性。
5. 得到自然低补给真实扣兵链、实际连续raw和正常闭场后，Root出真实business_result及19字段镜头接受回执，才将10/11改11/11。随后独立媒体卡运行全47段实际编码和QA；最终签收另列。
6. Game完全关闭后再让发布owner以新预算fresh核W/远端，正常整合价值来源、非强推、读回及恰当CI。保留已有本地提交、旧失败和未知wait，不重拷旧包或手工Git回收。

恢复后的首个实机节点是“真实一场结果、连续录制及正常关闭”；自然候选与因果覆盖尚不确定，不按源码完成比例承诺十几分钟闭题。
