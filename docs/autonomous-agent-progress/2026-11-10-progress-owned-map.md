# P199：progress 三个固定元数据更新共用局部 Map

Root 已接受正常 DATA 的有限源码、完整实际 Code 和原缓存单用例回归；没有把原用例扩写成目标三键独立 oracle，也未接受 GC、实际分配或速度结论。

本单元只把 ConstructionMaterialReducer.reduce(Input) 第 200 行的三个固定 with 更新改为局部 owned Map 的三次 put 和最终 Obj。正常 immutable DATA 的值、键序、叶引用、首个 RHS 顺序及相邻 Guard 由源码和实际 Code 独立核验；原缓存 coldCompletion 用例另作有限功能回归。没有 allocation、JIT、CPUwall、生产频率或性能测量。

排除两边共有的 199 初始 progress 构造，旧三个 with 对应 6 次浅 Map 构造、3 个 Obj，新实现对应局部 Map 加最终 Obj 防御副本的 2 次 Map、1 个 Obj。**这只是源码/callee 构造代数，不是实际分配计数、N² 修复或耗时收益。** P196 已接受的 201+ retainedMembers/19-key 更新不变，也不重复算作本次新节省。

## 一行原型与原求值顺序

[ConstructionMaterialReducer.java](../../java/ck3-control/application/src/main/java/org/xar/ck3/control/application/planning/finance/ConstructionMaterialReducer.java) 基底为 31654B、`e49f126945f7e81831642bce3cf80fb3ccf33f948b01e73ba4723cdb015e905e`，新源为 31842B、`6572adfb459416a950cdf816d9cf22f063a9cab1d1e8b00d19674ce3cd124ee0`。304 行保持，仅一个物理行 200 不同；整叶 inverse 恢复基底，199 以前和 201+ 全部原字节保留。正式 parent8d478353 已发表 P198，但本 Reducer 叶仍是 P196 受测原件。

199 仍按原 matchingActive 分支生成本次初始 progress，原 progress helper 不展开、不重写。200 的词法 block 先完整执行原 frame.get("snapshot_id") 并保存为 Value，再取 progress.members() 创建 owned LinkedHashMap。按原序 put snapshot_id、以原 new IntegerValue(revision) put native_revision、以原 new IntegerValue(date) put date_raw，最后 progress=new Obj(map)。第一份值允许原有 null，不加 guessed requireNonNull；Obj.with/构造器原行为本就允许 null Value。

三键互异，覆盖已有键不改变位置，新键按原序追加；原初始成员与 Value 叶引用保持。旧中间 Obj 不作为任何后续 RHS 的输入，也未在最终 retainedMembers 收录前外泄。frame、prior 和原子树不变，最终 Obj 仍拥有自己的 Map 防御副本。无 helper、field、API、type、跨调用 cache、raw+typed bridge、decoder、issuer 或来源许可增量；其余 Guard、融资、parser、hash、oldencode、完整原 P196 nineteen-key 链和 219+ 收入分支原样。

词法 block 仅约束新局部变量的源码可见范围，不授 JVM slot、GC、释放时机或 live heap。实际 Code 后到才核局部槽。删除中间分配/OOME 点、改变 map growth 和对象存活期，不授恶意 Map、私态、Unsafe 或所有 Throwable/资源失败时序等价。

## 首次生产编译与完整实际 Code

current366 的旧 Reducer6 实际来自 P196，whole 编源 31654/e49f 与正式基底相同；旧 Top38540/a0a68c01…。沿实际 release21 无显式 -g/-parameters profile，只编必要生产 1TU6。首次唯一编译 exit0 accepted、CLOSE **2026-11-09T18:29:02.350101Z**，terminal 后 fenced 释放；5 个 nested class 逐 SHA 与旧相同，新 Top38574B、`e3fc50224e73ebbed749d172f727479fadf3ae87435ce11b15512ef7679047ae`。API、fields、声明/flags、签名、参数、SourceFile、Nests 和 InnerClasses 保持，没有新增结构，但不据此授实机热更。

39 个方法中只有 reduce(Input) 目标变化；其余 **38 个 normalized Code、resolved CP、分支/异常表相同，其中 36 个 raw Code 相同、2 个 CP 索引重排**。CP 均为 1239 entries，完整 symbol multiset、字面量和 bootstrap handles/args 相同。目标 Code3761→3795B，max_locals49、max_stack10 均保持；不把 normalized 相同写成全部 raw 相同。

原 line200 区域 PC2660..2708 对应新2660..2742，三 RHS 分别逐指令比同，新旧完整区域按精确容器指令枚举，没有未解释部分。原首 get2670→新2665，先 store snapshot Value42，再于 PC2670 创建 Map43；三 put 为2691/2709/2727，final Obj2731、ctor2737、赋值 progress41 于2740。原 199 前与 201+ 所有解析后指令、字段/常量、分支目标和异常表独立逆为同。

实际 slot42 在 block 内保存 snapshot 值、slot43 保存局部 Map；201+ 的 retainedMembers42/oldUnavailable43 分别于 PC2754/2767 复用原槽。后续每次 load 均在对应原新值写入之后，shared local operands 原样。原 199 初始 progress 与最终 progress 仍是 slot41。**槽复用已观测，不等于 block 结束立即 GC 或对象不再存活。** Native 和 owner 的独立 classfile 解析结论相同，没有启动额外 JVM/Graph 平台。

## 原 Test2 缓存，只运行一个原用例

本轮不新增或重编任何 Test。使用 P196 实际已资格的 ConstructionMaterialReducerTest34636B、`dd7c4f8158b71d0249a61e7fa6a633b38696c28d6ad88a46af4c73945b09a329` 和编译依赖 helper ConstructionCoordinatorPendingTest10734B、`1488c0f283c7837ab1e3280d78f209fa3c7183b1362b65af704fe668f9b5fd24`；原源分别 29553/33148ddb…、5230/c1a1b123… 未改。旧 P196 Test2 typing-prefix 资格与旧真实 1P XML 是独立历史件，均保留，不把 typing0 当 JUnit 已跑，也不把旧 1P 当本次新运行。

Run368 的 first origins 为 cached Test2 在前、新 Reducer6 第二，其后 actual366 原有输入；八类及原 prerequisite 来源已核，CFG 只有 prod、junit 两阶段。仅选择 `ConstructionMaterialReducerTest#coldCompletionRetainsTheOriginalActionAndAllowsANewWorkerCounterNamespace`，主类其余12个及 helper3个 Test 均不运行；没有新 fixture、Guard/ACK/issuer、setup target、warmup、benchmark、JFR 或完整 APPLIED workload。

原 public reduce(byte[])→decode→reduce(Input) 的同一 inline DATA 走 cold completed/not_active 路径，三引擎合计 **1P、0F、0E、0skip**。真实 Jupiter XML 在 `N/p199-progress-map-regression01/reports-junit`；Root 消息曾把目录误写 junit01，后已依 CFG/POST 更正，原错误消息保留，没有复制报告或重跑 Java。testcase **2.608s**、Jupiter suite **2.643s**，BEGIN18:36:50.676009Z→CLOSE **18:36:57.757198Z**，exit0 accepted、输入不变并 fenced 释放；这些是功能时长，不是性能窗口。

原独立 oracle 仅包含 P19619 键中的五项：completion_status、completion_observed_date_raw、post_proof_epoch、start_receipt、observed_player_monthly_gold_income_raw；另验 MATERIAL_UPDATED、candidate/pre_proof_epoch、post_cash_v2 缺失和 originalBody 的完整 ledger encode/decode 往返。该例自然经过 200，但**没有对 progress 的 snapshot_id/native_revision/date_raw 增加独立值/键序/sameRef 断言，也没有 active progress helper 覆盖**；这些新目标等价由 Source/actual Code 负责，不扩写原用例 oracle。

## 全费用、预算与边界

生产 actor5.9696835s/operator7.2900001s，缓存 JUnit5.4601310s/7.1748562s，合计 **11.4298145s/14.4648563s** 只是两阶段资源子窗。最早具名 Planning checkpoint **2026-11-09T18:07:55.621081Z→末 CLOSE1742.136117s→final qualification1890.748478s**；SourceReady18:12:25.237747Z→1472.519451s/1621.131812s；Native 前检18:19:32.869601Z→1044.887597s/1193.499958s 为内窗，不相加。更早实际研究开始 UNKNOWN，不记0；UTC 时间对应北京时间11月10日。

method-object 形状、actor literal AST 和 raw-index 过强断言三项 0VM 原件与费用保留；后者明确按 resolved CP/branch offset 解释，不放宽语义标准或声称 raw 全同。Root 报告路径笔误保留。准备、wholeinverse、source/Code peer、actual366重绑、授权、调度、等待、qualification 与 Git 全部计入，不删失败/错误窗口；本轮两 JVM 各第一次唯一，没有源码/class/profile 更改后重跑。

旧 P196 cached dependency 的原三 actor17.8663413s/operator21.4041723s 及其准备等待原件继续保留，既不抹成缓存零成本，也不当作本轮新 Test 重编重复累计。Native final 之前三 roots metadata1146705B/67 文件，后到 final/budget/summary 切点 **1168077B/70 文件**，均在4MiB内；tmp、owned DLL 和 business fixture 为0，不证明进程级 JNI 未加载或 hard/heap peak。实际分配、CPUwall、生产频率/调用数、GC、端到端收益均未测。

可核：`N/p199-progress-map-prod01/QUALIFIED-P199-PROD6-CACHED2-SOLE1P-ALL2COST-FINAL01.json`18966B、`a8ab1e67a85203009422a2c939efa96f25193985fdac12ef436ddcdc28ac29aa`；同根 Code91092B、`e2a2cbe0fdcfee33f6c7bef81517f3c8a1cc369b863151ed22d95a1d3922db79`；budget1421B、`77e588cf1747a8f93af868a1e2288777b2ff27d96b7a09a44f20dafa38b674b6`。regression01 Jupiter XML45466B、`c7621a2c821237e97cc234e14752a85e9e754c9e84cc9e335fa49a9cf71ef3fc`；owner actual Code14237B、`b44c24a7b2a3a1fa29405f04e3208a85c1b12fc4059b49afb7c0a7e876c27561`，solecase5457B、`ae45d66d206f1431e9cf14b21c90149996523178b8dafeca1df4572ae4099612`。N/J/R 是 Native、Java 交付及 Root 隔离证据根，来源与原件保留。

exact4 只本生产 Reducer 叶与 unit/daily11-10/W46，原 Test2、Obj、P200/其它生产源、AGENTS、CI、pom 和运行文件均不变。本源码切点实际离线软件 current366，后到 candidate367/Root 软件采用另账，不能预填 adopted；没有 Runtime、Game、GET、P100、SAVE 或10秒目标通过。零新增确认保存日，秒/新增保存日 null，持续目标不因交付结束。

Root 最终接受：`R/P199-LIMITED-PROGRESS3-SOURCE-CODE-CACHED1P-ACCEPT01.json`8159B、`3baf4e0d3c64e8cf2f0c42a72c34cade45ed2182466486404e6293e4b73995c4`。SOURCE/Code、单功能回归、Git 与后到实际软件367采用分别记账。
