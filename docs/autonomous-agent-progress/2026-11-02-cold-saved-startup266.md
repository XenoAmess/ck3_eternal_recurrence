# 266 冷 Saved 启动离线分析

结论：259 的 240.8044782 秒仍是日志未细分的墙钟区间，现有材料不能给它分配 CPU、磁盘、锁或 Native RPC 占比。当前正式源码可证明一个更窄的重复工作：一次 retained 校验返回的同一个 `SavedMaterial.current.savedDriver()` 在 Store 和 Root 两层各编码一次。下一 267 可仅在这两叶之间传递本次已生成的编码结果，保留两个独立基线比较和全部实际重验。无需假设两个基线相等，不改 `DriverStateSnapshot.Complete`，不新增全局缓存。

本单元仅写 `D:/ck3-state/resume91-root/cold-startup266`。没有改正式源码、S/MB、运行配置，没有编译、Java/JVM 启动、Game/Native 查询、进程采样、PE、部署、界面或录像操作。用户手动游玩边界继续有效。

## 材料与版本

- 运行材料仅取 `runtime-doc259-user-stop/DELIVERY259.json` 导航的冻结 FACTS、10391B stdout、START/END 小原件；复制及 SHA 在 `SOURCE-INPUT266.json`。
- 当前分析源码冻结自 `D:/r64d/java/ck3-control`，当时正式 HEAD `91460afde8384d5c116cedb79d22baac2e7623b0`。39 个具名完整源码的路径、长度、SHA 均在同一 manifest。没有读当前账本或大 SAVE、Driver、SEM 内容。
- 261 的 `eb0338e4f4ee26b8d0ad3bf31ca276d478724a16` 是后到的私有 live token；264 的 `7d3aacec652f614b1e96f898a78d3a4ab689bcc7` 是 Store 内 fixed-side 编码的 lazy getter。这两项仅正式发表，不证明装入旧 259 或有实测收益。
- 正式入口名是 `RootLoadedSavedResumeMain250`。它解释当前源码调用关系；本单元未证明其逐字等于实际 259 的 loaded CLI source，不把后到代码反投到旧运行。

## 冻结时间线

| 标记 | UTC | 与前一标记间隔 |
|---|---|---:|
| START | 18:55:04.882106 | — |
| SOURCE_QUALIFIED | 18:55:37.7408252 | 32.8587192 s |
| ACTUAL_ATTACHMENT | 18:55:39.8328621 | 2.0920369 s |
| LOADED_CUSTODY_QUALIFIED | 18:55:40.8500706 | 1.0172085 s |
| SAVED_ENTRY_ADOPTED | 18:59:41.6545488 | 240.8044782 s |
| LOOP_START | 18:59:41.6555439 | 0.0009951 s |

FACTS 冻结总值为 276.773437 s；逐文本时间戳差为 276.7734379 s，精度区别不形成新的测量。没有中间子阶段时间戳。`runOperationPhase` 52–54 只是计算 deadline 并同步调用 `operation.run`，本身不 sleep、起线程或等待 timeout；不能把多个配置时限求和解释实耗。

## 当前正式控制流

以下是 custody 后至返回 Running 的完整主控制顺序。域子系统内部仅列实际委托名称；未逐个读取所有业务域实现，不为那些叶分配时间或声称已完成全图性能审计。

1. `RootLoadedSavedResumeMain250.run` 93–95：emit custody → `newPrepared.openRetainedLoadedSaved(...)` → **额外** `running.core().writer().locked(same -> same.head())`。随后才 emit adopted/LOOP。因此 240.804s 不等于单个 `openRetainedLoadedSaved` 实耗。
2. `RootOrdinaryRuntimeAssembly.Prepared.openRetainedLoadedSaved` 460–489：实际 custody/Game 检查、既有 source 绑定、adoptAttached、managed lifecycle 绑定、awaitHello/原 hello、实际 business source、`catalogs.install`、`RootJavaSavedBootstrap.reopenLoaded`、`Core.adoptRetainedSaved`，然后 `Opened.finishConfirmedSaved`。
3. `RootJavaSavedBootstrap.reopenLoaded` 330–407：先 source 当前资格和 custody；新 writer 内查询真实 Saved marker/canonical edge、完整 suffix/历史来源；执行**两次独立 fresh READ**及前后关系；归档真实 ACK/raw；再次检查 source/custody；最后 canonical 来源与 opening/当前 native revision、实际 physical-origin qualification、原件 Pins/suffix，构造私有 RetainedSaved，并执行完整 `retained.requireCurrent`。失败仍 close physical proof、保 suppressed。这里的两 READ 和前后复核有不同角色，不能凭“同文件”删除后半段。
4. `Core.adoptRetainedSaved` 与 `DriverBootstrap.adoptRetainedSaved` 1266–1371：完整私有 current 资格、raw/session/Game/transport、实际 fullDriver/facts/manifest/native 原件读取与 SHA、Known/Driver 一致性；按真实 suffix 重放 READ；验证 replay Pins；新 repository/producer/authority/held observation；bindRetainedSaved、真实第二 READ 的 frozen join，以及 original history basis。`fullDriverReference` 是本新 writer 保存的初始 Driver，后续 READ 可将它推进为 Driver1；不能拿旧 saved Driver 或初始 Driver0 代替当前 replay 结果。
5. `Opened.finishConfirmedSaved` 727–758：第一次独立 `retained.requireRetained`；真实 consumed batch ID/next sequence；selector/configuration；`Core.finishConfirmedSaved`；`session.install`；**最后**另一个 retained 复核；当前正式版本才再 `promoteSavedLive`。
6. `Core.finishConfirmedSaved` 517–531：单独 writer scope 的 actual retained 验证、catalog/Game/source 对应，进入 `finishObserved`。
7. `Core.finishObserved` 1589–1697：bind physical Driver、stage/save、readiness.initial、reconciliation/source-history、dispatcher/offline、`Staged.finish`。Saved 分支在 1659–1669 再验证；如有 consumed batch，用真实 SEM 记录 Saved read-only recovery；初始化 Saved 域、持久 planning、retain batch IDs，最后才 mint 私有 live completion。
8. `RootInstalledCatalog.initializeConfirmedSaved` 459–489：actual private proof；FreshCampaignContext；governance continuation、construction 条件导入、finance、prisoner definitions、governance/跨局、offline、Army retained/首次导入分支、remaining.afterInitialEntry。`initializePersistentPlanning` 562–640 校验真实 Driver/capability/base domains，再初始化 capability/planning；Saved READ suffix 分支在 replay/publish 前后重复 proof，**中间有 publication，不能按同 head 消掉后验**。
9. `RootApplicationSession.install`：安装 Host/controller 后仍执行 `prepareTransportContinuity`。后者返回前不能认定安装成功。当前正式的 live token 只在这些步骤及最终 retained 检查成功后激活，激活本身还先运行原 campaign proof；不重提 261 的热路径设计。

上述多个 writer scope 是先后调用或明确 borrowed/readOnlyFrom 角色，不能统称“多个嵌套可重入锁”。Writer thread-local/owner 与 readOnlyFrom 的 outer suspend/resume、源 writer lease 都必须保留；没有锁等待测量。没有依据把 240s 归因成四个 60s RPC。

## 必须保留的边界

- `RootJavaSavedBootstrap.RetainedSaved.requireCurrent` 650–658 是 startup current/suffix/deadline 角色；`requireRetained` 660–677 是允许后到合法恢复/导入后继续保原件的角色。两者不能互换或将 precommit current 在恢复提交后重调。
- `ConfirmedSource.requireRetained(activeNewSame)` 133–144 通过真实 old writer `readOnlyFrom`，在现有 bounded historical read scope 内执行完整旧来源校验。该 scope 不是普通 Head.documents 的完整图闭包，也不是全局“已验证”许可。
- `RequalifiedConfirmed.requireRetained` 286–306 仍检查实际旧 source Session/head、confirmation Pin/完整 edge/存续 saved branch、原 material FileWitness、proof/original head/checkpoint digest 和完整 Driver。
- `loadRetainedOriginal` 311–343 仍执行实际 manifest observe/read/verify、原历史 state/cycle proof、CheckpointCommitVerifier、头与 session 后验。Source 的固定对象不可变，不表示路径中的实际原件永远没有被替换。
- paired CAS 保护只覆盖其实际取得的 payload+commit OS lease 与 bounded custody；直接 CheckpointFiles、writer Pins、current physical/Game/custody 等旁路读取照旧。预算 fallback、例外、关闭失败不允许输出成功值。不得据同 head 或旧成功缓存整个 qualification。
- 域安装、归档、READ/capability publication、恢复 commit、transport 安装前后的检验保留。没有源证支持合并这些阶段的全部资格。

## 267 最小候选：本次 fresh 编码结果传递

唯一建议的生产写域是：

1. `application/src/main/java/org/xar/ck3/control/application/checkpoint/SavedAttachmentSourceStore.java` 的 `RequalifiedConfirmed.requireRetained`。
2. `local-service/src/main/java/org/xar/ck3/control/service/root/RootJavaSavedBootstrap.java` 的 **两个 retained overload**，不改 requireCurrent、cold/private issuer 或其它调用者。

精确旧链：

| 顺序 | Store / Root 当前行为 |
|---|---|
| 1 | Root 进入自己的 writer/readOnlyFrom 与现有 historical scope |
| 2 | Store 校验旧 source Session/head、confirmation、saved branch，完整 `loadRetainedOriginal` |
| 3 | Store 299–303 按原顺序检查 pair、witness、session、proof、original head、两个 digest |
| 4 | Store 304：对**本次返回的 current.savedDriver**执行一次 fresh `encode()`，随后才取 264 fixed-side A lazy getter并比较 A |
| 5 | Store 返回这个 `current` SavedMaterial |
| 6 | Root 113–116 或 138–141：先 session、pair；通过后对**同一个 current.savedDriver**再 `encode()`，比较 Root 私有 fixed-side B |
| 7 | 返回 current.savedDriver；scope/old-writer/outer Session 的原关闭和后验照旧 |

这里的 fresh 指“本次实际重验返回的旧 Saved material”，**不是新 world 的当前 Driver1**。A 是 RequalifiedConfirmed 固定 material 的编码，B 是 Root ConfirmedSource 固定 material 的编码；不需要也不允许用“它们应该相同”删除任一比较。

可实施合同是 prospective，尚无新 ABI、生产源码或验证绿：Store 创建私有构造的不透明即时结果，包含已验证 material 和第4步已生成的私有 fresh 编码，仅提供 `material()` 与 `matchesDriverEncoding(expected)` 一类名义访问。不能返回 byte[]，不能为传递而 clone 大数组，不能把它存到全局/跨调用缓存，也不能让它成为 permission/source issuer。Root 先在原位置校验 session/pair，再使用不透明结果比较 B。旧 `requireRetained` 返回 SavedMaterial 的 ABI 和语义保留，可委托同一实际校验路径后取 material。

异常和求值顺序要求：

- 所有现有实际读取、hash、FileID、Pin、head、physical、scope 和当前资格仍逐次执行。
- 第3步任一条件失败时不提前编码 current，也不触发 fixed A getter。current fresh encode 仍先于 A getter；A getter失败/encode失败不产生成功结果。
- 只有 A 比较和全部 Store 校验成功后才构造/交付即时结果；Root 元数据失败时仍不调用 B 比较。
- B 比较留在原 Root metadata guard 之后，不提前、不取消、不改为 A==B 或 Complete.equals。
- 无新 callback、Writer/IO/Core/Host 调用或锁；保 readOnlyFrom/历史 scope 的 failure/suppressed/cleanup 行为，未成功关闭仍不得返 T。
- 此结果仅是本次已验证 DATA。其 getter/matches 不等于重新要求 current，也不许未来调用跳过当前原件验证。

静态收益范围仅为：每次成功走到 Root B 比较的 retained 调用，同一个 current Driver 的 fresh 编码从2次变1次；A/B两次比较均保留。失败于 A 前仍与原先一样不做 Root B 工作。没有减少任何实际原件 I/O 的主张，没有次数总量/命中率/墙钟收益承诺。当前正式 `Opened.finishConfirmedSaved` 729/757 与未激活前 `activateSavedLive` 477–490 仍明确可达此链；这些是后到正式源证，不是实际259调用计数。

immutable 依据来自当前 `DriverStateSnapshot` 15–51：sealed Slot；Value 构造规范化/持有封闭字节，json accessor clone；Complete 对 history List.copyOf，Session/HistoryEntry/Value 组成固定 record；encode 新建 JSON 树并返回新数组。此证据只支持复用**刚生成且未外泄的一份编码**，不支持把完整 Driver record 改成全局/public encoding cache。

## 三角色 HTTP 全文审阅与采用

三份请求均固定三消息、实际完整当前源码、max_tokens6000、唯一输出目录，均 HTTP200 / stop / 0retry，cached tokens 均 null。证据保留在各角色 `http-r1/{REQUEST.json,EVENTS.jsonl,ATTEMPT1-CONTENT.txt}`，没有 R2 或重新洗绿。

| 角色 | POST_BEGIN UTC | total / TTFT | reported prompt+completion | 等级 |
|---|---|---|---|---|
| flow | 20:20:33.953586 | 88.806786 / 72.201983 s | 229473+1730 | 部分重复链/日志盲点经 owner 独立核实；whole结论不采 |
| store | 20:20:33.952348 | 92.238694 / 46.172292 s | 134101+2348 | 指出初始 requalify→requireCurrent 重复方向；全部省读/许可建议拒，owner另证窄编码候选 |
| counter | 20:20:33.953254 | 92.544301 / 55.330880 s | 191833+2060 | 部分身份/cleanup反例独立核实；错误方法/264/261/全局编码建议拒 |

具体未采用：flow 将顺序 scope 称嵌套、把进程启动/前置 config 读取混进 custody 后区间，省略安装及额外 writer.head；F2把 `requireSavedHistorical` 的完整实际读取说成已经 decode，与601行只读并弃结果不符。store 的行号大量不对，反复以“immutable所以missing_proof=None”建议省实际读；SaveWithDriver 传播已存在于当前 CheckpointCommitVerifier，不再作为新修复。`readExact` 只是实际 read，不是它所说的自动 JSON parse。counter F8混淆264 fixed-side getter和current-side，F9错误声称261激活后不跳旧 historical campaign proof；F12建议 Complete全局编码缓存，不采用。F6的 completeAdmission 命名也未核成实际方法，不引用它做精确链。

Owner 候选是两个独立原条件保留前提下的 fresh 结果传递，不采用模型“文件不可变所以可跳验证”的授权推理。输入缺失成本也保留：各角色是不同真实闭包，flow未提供Archive/Writer具体实现，故其相应I/O/锁未知不能追认为已读；本次 owner 通过其它角色提供的同一冻结实际实现核对。域子系统所有 leaf 内部未展开，未做未知推断。

## 下一步和保留项

267 由 Root 交 M5 独占这两叶的 D 私有候选和真实模型实现。266 不改生产源码，不运行 Java 或现场见证。新接口和公开名义类型必须在 M5 实际源码冻结后才能作为消费者事实；本分析只交合同和旧链。

以下保留原样：两 fresh READ；pre/post source/current/retained；所有 physical/Pin/hash/FileID/head；恢复与域发布前后 proof；既有261 token和264 lazy；Store/Archive provider scopes。完整 old Saved proof 的跨Session缓存、批量跳 domain proof、并行 writer读取和以旧 head 许可新Game均无安全源证，不实施。

若以后用户另行允许性能见证，需要独立子阶段时间和真实 I/O/CPU 才能解释240.804s；本单元不发新采样、不把诊断作为恢复或用户手动游戏的门。

主动工作时界：首实际 clock 为20:16:57 UTC（秒级，之前未知不倒填）；源码准备到三POST约216.95秒。模型区间约92.55秒，三段重叠，不能相加成owner等待。Owner在请求期间继续读源并随后全文审三个结果；没有显式idle sleep/等待资源窗口。工具启动HTTP后返回所需约10秒属于工具墙钟，主动CPU时间没有测量，不能把全部elapsed写成owner CPU。最终封包UTC与实际调度耗时见现有 `ACTIVITY266.json`。

## 发布时补记：实际调度窗口

首次观察 clock 20:16:57Z（秒级）到封包 20:31:48.064068Z，完整调度墙钟为 891.064068 秒。准备约 216.95 秒；三 HTTP 的并行窗口为 92.545056 秒，三次 HTTP 请求各自耗时之和为 273.5897802 秒，后两项不能相加到前者。owner 在请求期间继续读源；主动准备/审阅工时与 CPU 时间未连续计量，保持未知，不声称净节省。此补记依据执行机器 ACTIVITY266.json，不修改原冻结分析。
