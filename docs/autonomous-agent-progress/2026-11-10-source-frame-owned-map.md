# P200：source frame 两个固定字段共用局部 Map

Root 已接受正常DATA的有限源码、完整实际Code和原缓存coldCompletion单用例回归；不把回归扩成新source两字段oracle、GC或性能结论。

本单元仅合并 ConstructionMaterialReducer.reduce(Input) 第119行的两个 with：先完整构造原 pid Value，再复制 frame.members，按原序更新 bridge_pid 与 bridge_creation_date，最后构造 source Obj。正常 immutable DATA 的值、键序、引用、输入不变与所有相邻校验由源码和实际 Code 独立证明；原缓存单用例另作有限回归。没有实际 allocation、CPUwall、GC、生产频率或端到端性能测量。

排除共有的 frame 物化，两个 with 对应 4 次浅 Map 构造、2 个 Obj，新局部 Map 与最终 Obj 的防御副本对应 2 次 Map、1 个 Obj。只是源码/callee 构造代数，不是实测分配、N²、热点、吞吐或速度结论。P196/P199 已接受的后续两个 Map 单元原字节保持，不再重复计作新节省。

## 只改119，所有输入校验和RHS原序保留

[ConstructionMaterialReducer.java](../../java/ck3-control/application/src/main/java/org/xar/ck3/control/application/planning/finance/ConstructionMaterialReducer.java) 基底为 P199 正式 e23dd438 的31842B、`6572adfb459416a950cdf816d9cf22f063a9cab1d1e8b00d19674ce3cd124ee0`，新源31996B、`80cd00d59c054e10942ac7ef3482cc18d0ae76012bb474be68eefced3dd95762`。304行保持，只119一物理行差异；whole inverse恢复基底，117/118及全部120+、特别P199新200 progress block全字节相同。

原111 frame/snapshot取得、112–115身份和快照漂移校验不动；117 integer+positive(pid)、118 text+birth非空检查仍完整先执行。119声明原作用域的 Obj source，在无条件词法 block 中先执行完整原 new IntegerValue(pid)，保存为 Value sourcePid，之后才访问 frame.members() 并创建局部 LinkedHashMap。先 put bridge_pid，随后执行原 new Text(birth) 并 put bridge_creation_date，最终 source=new Obj(map)。两个 RHS 不重复、不跳过、不前移到校验之前。

Map 从实际 frame 的成员复制，不换 snapshot/prior 或新来源。覆写既有键保持原位置，缺失键按原序追加；其它 Value 叶引用不变，输入/frame不被修改，最终 Obj 仍拥有防御 Map 副本。source 的原消费者不变。Obj原定义允许 null Value，不额外猜测或加 requireNonNull；没有 helper、API、field、type、cache、raw+typed/decoder bridge、issuer、权限、Guard、parser、hash 或 oldencode 增量。

词法 block 仅限定源码局部名作用域，不预授 actual slots/max_locals、GC或临时对象立刻释放。删除中间 Obj/Map 分配改变 OOME、map growth和资源失败时序，不授恶意 Map、反射/Unsafe/私态或所有 Throwable 等价。

## 实际39方法与完整目标区域

旧 actual367 Reducer6 为 P199 首编产物，whole编源31842/6572与正式基底相同；旧Top38574/e3fc5022…。旧 SourceReady 在 owner收到后到367消息前封存了366切点，随后只追加 actual367 来源，不覆盖旧件或轮换候选。Native current367前检和Root采用分别为独立证据。

本轮只必要生产1TU6，沿旧实际release21无显式-g/-parameters profile；首次唯一编译 exit0 accepted、CLOSE **2026-11-09T18:56:27.503557Z** 并fenced释放。五个nested class逐SHA旧同，新Top38605B、`675b157d5b966976b6374e0e142843f2830b3ee9c77a9673e3ce346d53d81e00`。原API、fields、声明/flags、签名、参数、SourceFile、Nests和InnerClasses保持；没有新增结构不等于实际JVM重定义已验。

39方法中只有reduce(Input)变化；其余 **38方法normalized Code、resolved CP、分支/异常表保持，其中22 raw Code相同、16 CP索引重排**。CP均1239 entries，完整symbol multiset、字面量及bootstrap handles/args相同。目标3795→3826B，max_locals49/max_stack10相同。没有把normalized相同称作raw全同，也没有给全局slot/branch mask豁免。

old119区域PC609..643对应new609..674，两完整RHS分别逐指令比较；整个旧、新区域均精确枚举，所有区域外1623条指令/119 branch的resolved字段、常量、locals、调用、分支目标和exception table保持。原pid Integer RHS [614,623)→[609,618)，先store15再new Map620；frame.members为626，首put641。Text(birth) [629,638)→[650,659)，位于首put之后；第二put659、final Obj663/ctor669/store source14于672。新Map是私有副本，不改变原frame。

原117/118与全部120+独立核同，P199 progress完整82B区域[2660,2742)→[2691,2773)也单列归一相同。source仍slot14；临时pid Value15/map16随后由原date688/revision704写入覆写，每次后续load均在原新定义之后。**这些实际slot复用不授GC、heap peak或对象释放时机。** Native和owner均只解析classfile，owner未启动Java或新Graph平台。

## 只复用原Test2，只运行原coldCompletion

本轮Test编译0，没有新增Test、fixture、Guard/ACK/issuer、warmup、benchmark、JFR或完整APPLIED case。原P196 qualified cache的ConstructionMaterialReducerTest34636B、`dd7c4f8158b71d0249a61e7fa6a633b38696c28d6ad88a46af4c73945b09a329`与helper10734B、`1488c0f283c7837ab1e3280d78f209fa3c7183b1362b65af704fe668f9b5fd24`保持；原源29553/33148ddb…及5230/c1a1b123…未改。旧Test2 typing资格与独立旧1P XML继续分别记账，不把typing0当已跑JUnit或把旧绿当本次通过。

Run369首根cached Test2、第二根新Reducer6、其后actual367原tail，八类及原prerequisite/Consumer ABI核过；CFG仅prod、junit。唯一选择 `ConstructionMaterialReducerTest#coldCompletionRetainsTheOriginalActionAndAllowsANewWorkerCounterNamespace`，主类其它12个和helper3个不运行。原public reduce(byte[])→decode→reduce(Input)使用同一inline软件DATA，不构造真实来源或权限。

报告路径只从实际CFG/POST取：`N/p200-source-frame-map-regression01/reports-junit`。三引擎合计 **1P/0F/0E/0skip**，其它两engine0tests；testcase **2.085s**、Jupiter suite **2.112s**。BEGIN **2026-11-09T19:02:38.502743Z**→CLOSE **19:02:44.852093Z**，exit0 accepted、inputs unchanged并fenced释放。这只是功能时长，不与P199/P196不同JVM时长相减称加速。

原case只独立断言P19619键中的completion_status、completion_observed_date_raw、post_proof_epoch、start_receipt、observed_player_monthly_gold_income_raw五项；另MATERIAL_UPDATED、candidate/pre_proof_epoch、post_cash_v2缺失及完整originalBody ledger encode/decode往返。它自然经过119，但**没有source_frame的bridge_pid/bridge_creation_date值、键序、sameRef独立oracle或全部material分支覆盖**；也不借此补授P199 progress三键/active helper覆盖。两RHS及所有权/外部Guard等价的依据是Source/actual Code。

## 全费用与范围

生产actor5.8472113s/operator7.0821594s；cachedJUnit4.8395849s/6.4561153s，两阶段合计 **10.6867962s/13.5382747s** 仅资源子窗。最早具名Planning checkpoint **2026-11-09T18:35:16.665523Z→末CLOSE1648.186570s→final qualification1732.237391s**。Owner SourceReady18:45:47.789027Z→1017.063066s/1101.113887s；Native前检18:48:44.188213Z→840.663880s/924.714701s是内窗，不相加。更早实际开始UNKNOWN，不记0；北京时间均为11月10日。

OwnerReady的base字段误读0VM错误0.2691546s及首次调用之前的preparer标签draft修正原件保留；没有候选源码/class/flags变化或Java失败重跑。准备、source/inverse、actual367重绑、双peer Code、授权、调度、等待、qualification及Git全部保；两阶段各第一次唯一JVM。旧P196缓存依赖原三actor17.8663413s/op21.4041723s及其全费用继续单独引用，不抹成缓存0成本，也不重复计成本轮新Test编译。

Native final前metadata1151391B/65文件，后到final/budget/summary静态切点 **1173185B/68文件** 在原4MiB内；tmp、owned DLL及business fixture均0，不证明process-wide JNI未加载、hard peak、heap peak或GC。allocation/JIT/CPUwall/生产频率/真实调用数/端到端收益未测。

可核：`N/p200-source-frame-map-prod01/QUALIFIED-P200-PROD6-CACHED2-SOLE1P-ALL2COST-FINAL01.json`19365B、`0581eb76f0560745aca7f656366eec9d52fc5ab9babb74dc32fb2bc1820582c7`；同根Code105664B、`9e9c61b7e8976afcf268d40ef2c6487bcfa5f0bcda642224763a34815537c63f`；budget1437B、`3c439027dc5f3f8274f225a3ebb03bd33fc9cf6b18b2c6dc6bae1e0826f49a63`。真实Jupiter XML45561B、`9fc587860ebc4efc04d4d37c323c64c098a120581e659f2848aff6c0eb711b64`；owner独立Code14144B、`cc71a106d510589af9e8e7aa062ca25a0aa6820fa90e9b0618467e457ec42732`、solecase5536B、`efec8a4aceef7c63fe3ffb5d95eb6297d0cb668a24c659e630b7739a86265e53`。N/J/R为Native、Java交付及Root隔离证据根，原件及来源保持。

exact4仅本Reducer叶+unit/daily11-10/W46，原Test2、Obj、P201/其它源码、AGENTS、CI、pom及运行文件不变。本正式源码切点actual离线软件current367，后到candidate368/Root实际采用另账，不提前填adopted；没有Runtime/Game/GET/P100/SAVE或10秒目标信用。零新增确认保存日，秒/新增保存日null，持续目标未完成。

Root 最终接受：`R/P200-LIMITED-SOURCE2-CODE-CACHED1P-ACCEPT01.json`7643B、`9c5ac10de0054557cf2474371da2c26d8ead46ef79e74f0c8e17b9c127580ab6`。源码、Code、功能、Git、后到actual368与Runtime/SAVE保持分层。
