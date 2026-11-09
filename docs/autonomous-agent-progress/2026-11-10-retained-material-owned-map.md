# P201：retained material 两个固定更新共用局部 Map

本单元只合并 ConstructionMaterialReducer.reduce(Input) 第159行的两个 with：首个 IntegerValue(date) 完整求值后才复制 prior.members，按原序更新检查日期与既有 observation，最终构造 retained Obj。正常 immutable DATA 的键序、值、叶引用、输入不变及全部 Guard 由源码和实际 Code 独立证明；原 missingProjection 方法首次实际运行另提供有限功能证据。没有实际 allocation、CPUwall、GC、频率或端到端速度测量。

排除共有的 prior 和154–158 observation 构造，旧两with对应4次浅Map构造、2个Obj，新实现对应局部Map和最终Obj防御副本的2次Map、1个Obj。**只是源码/callee构造代数，不是实测分配、N²修复或吞吐收益。** P196/P199/P200其它修改原字节保持，不重复计成本次节省。

## 唯一159差分与原数据顺序

[ConstructionMaterialReducer.java](../../java/ck3-control/application/src/main/java/org/xar/ck3/control/application/planning/finance/ConstructionMaterialReducer.java) 基底为正式7f07890c的31996B、`80cd00d59c054e10942ac7ef3482cc18d0ae76012bb474be68eefced3dd95762`，新源32232B、`30ffc0fc3b2305997f92898c07a9e0c9d43169f2b7c60a670c0ef91f9d4694a7`。304行、仅159一个物理行不同，wholeinverse恢复基底。93 pending-empty、96–100原回执检查、全部material source/frame/quote校验、151 applied及postcondition_verified检查、154–158 observation、160return和所有其它源码原样；119与200两个已接受block也原样。

159保留原作用域Obj retained声明，用无条件局部block先执行原new IntegerValue(date)，保存为Value retainedCheckDate，然后才访问prior.members并创建owned LinkedHashMap。先put completion_last_check_date_raw，再把**同一个既有observation引用**put到material_observation_unavailable_v1，最后retained=new Obj(map)。不重建、重解析或拷贝observation，不增加null/权限/Guard检查。原Obj.with/构造器允许null Value，新put不猜测添加requireNonNull。

Map只取原prior，不换ledger/frame/source或另造来源。已有键覆盖保位置，缺失键按原序追加；其余子Value引用不变，prior和input不被修改。最终Obj仍拥有防御副本；160原replace、两个Optional.of(retained)和Reduced构造仍接同一个最终retained及原observation。无API、field、type、helper、cache、raw+typed/decoder bridge、issuer或来源许可。

这只是软件DATA reducer：原pending和已验证回执检查保留，未触碰任何现场账本、Game/Native动作、UNKNOWN重投、旧deadline刷新、同链诊断、P100或repair许可。inline测试DATA中的applied/postcondition字段也不证明真实世界动作或授权。删除中间分配/OOME点、改变map growth及存活期，不授Unsafe/反射/恶意Map/私态或全部Throwable/资源失败时序等价。源码block不是JVM槽或GC证明。

## 实际六类与全部39方法

旧actual368 Reducer6为P200完整产物，whole编源31996/80cd与正式基底相同，旧Top38605/675b157d…。本轮只必要生产1TU6，沿实际release21无显式-g/-parameters profile；首次唯一编译exit0 accepted、CLOSE **2026-11-09T19:27:29.057433Z**并fenced释放。五个nested class逐SHA旧同，新Top38636B、`e7048959e86b07de1ce89a96ba2157cba00a111b7bc1904c5593ee506f32a38d`。API、fields、声明/flags、签名、参数、SourceFile、Nests及InnerClasses保持；不据此授实际热更。

39方法仅reduce(Input)变化，**其它38方法raw Code及normalized Code全部相同**，不是套用前单元CP重排计数。CP均1239 entries，完整resolved symbol multiset、字面量和bootstrap handles/args相同。目标Code3826→3857B、max_locals49/max_stack10保持；caller Code变长不代表实测更慢或更快，旧with的callee构造代数另证。

原159区域[1915,1942)对应新[1915,1973)，完整Integerdate RHS [1920,1929)→[1915,1924)与第二aload observation33 [1935,1937)→[1956,1958)逐指令相同。新date Value35先于Map36创建；Map1926取prior5.members1932，put1947/1958，final Obj1962/ctor1968/store retained34于1971。两个旧新目标区域全指令精确枚举，无进入区域内部的外部jump。

所有外部1641条指令、119个branch的resolved CP/字段/常量/调用、locals、控制流和exception table保持，93/99/151 Guard、154–158 observation和160return均包含其中。160原调用及observation33/retained34引用完整同，立即areturn2003前不读取临时35/36；另一条路径跳过本块。source119区域保持，progress200的82B区域[2691,2773)→[2722,2804)也独立核同。临时槽实际行为与源码scope分别记账，不作GC、heap peak或立即释放证明；owner只复用既有class reader解析，没有新Java/Graph平台。

## 首次真实missingProjection，仅原断言

原完整Test2缓存保持：ConstructionMaterialReducerTest34636B、`dd7c4f8158b71d0249a61e7fa6a633b38696c28d6ad88a46af4c73945b09a329`和helper10734B、`1488c0f283c7837ab1e3280d78f209fa3c7183b1362b65af704fe668f9b5fd24`，源29553/33148ddb…与5230/c1a1b123…未改。本轮Test编译0、无新fixture、Guard/ACK/issuer、private反射、warmup、benchmark、JFR或完整APPLIED workload。旧typing资格、旧coldCompletion1P与本次新selector分别保原，不转移绿证据。

只运行既有 `ConstructionMaterialReducerTest#missingProjectionRetainsPriorMaterialAndItsNewReadOnlyLeaseWithoutGrantingNewCredit`（原57–68），主类其它12个和helper3个JUnit方法不运行。public reduce(byte[])使用原input(ledger(),query(900,75,false,false))；原ledger的pending空且applied/verified，没有active/completed匹配，900晚于原post date100，不走restored路径。固定输入与不变Code支持到159的路径推断，不是插桩计数或真实权限。

Run370 first origins为缓存Test2在前、新Reducer6第二、随后actual368原tail，八类及原prerequisite/ConsumerABI核过。报告路径从实际POST取 `N/p201-unavailable-map-regression01/reports-junit`。三引擎合计唯一 **1P/0F/0E/0skip**，case **2.143s**、Jupiter suite **2.175s**；BEGIN19:37:07.888289Z→CLOSE **2026-11-09T19:37:14.337637Z**，exit0 accepted、inputs unchanged并fenced释放。该selector原Ready的actualpass NOT_HELD历史切点保留，本次实际通过是后到件；不是cold1P借授。

独立原oracle只有：PRIOR_MATERIAL_RETAINED disposition；原post_proof_epoch/post_date_raw保留；unavailable marker为Obj，其business_submission=false、native_submit_calls=0、retry_not_before_date_raw=1620；对result.originalBody公开编码/解码后，applied.observed.dateRaw为900。**这不是完整ledger往返相等断言**，也没有裸completion_last_check_date_raw的直接值、两键迭代序、observation sameRef、完整input/receipt identity或全部material分支oracle；decoded observeddate900仅为间接语义检查。两RHS/order/ownership/Guard等价由Source/actual Code负责。功能时长不与旧cold或别的JVM相减称性能。

## 全费用、原件与范围

生产actor5.5777299s/operator6.8915254s，首次新selector JUnit4.8117509s/6.5484784s，合计 **10.3894808s/13.4400038s**仅两资源子窗。最早具名Planning checkpoint **2026-11-09T19:05:20.959623Z→末CLOSE1913.378014s→final qualification2212.109666s**；Owner SourceReady19:12:04.356047Z→1509.981590s/1808.713242s；Native前检19:18:45.486685Z→1108.850952s/1407.582604s；production首artifact19:24:09.510025Z→784.827612s/1083.559264s。均是重叠内窗，不相加；更早实际研究起点UNKNOWN，不记0，北京时间均11月10日。

旧controller caption误配0VM错误0.281967s、最终writer alias误配0.2769503s及其修正原件保留；候选source/class/profile未轮换，没有Java失败重跑。准备、finiteplan、代码与peer审阅、授权、调度、等待、qualification和Git不删除；两JVM各第一次唯一。旧P196缓存原三actor17.8663413s/op21.4041723s及全准备费用独立引用，不抹成零成本或重复算成本轮Test编译。

Native final前metadata1140238B/65文件；后到final/budget/summary静态切点 **1163487B/68文件**在4MiB内，tmp、owned DLL及business fixture为0，不证明process-wide JNI未加载、hard/heap peak或GC。实际allocation、JIT、CPUwall、频率/调用数及端到端收益未测。

可核：`N/p201-unavailable-map-prod01/QUALIFIED-P201-PROD6-CACHED2-FIRSTMISSING1P-ALL2COST-FINAL01.json`20809B、`4bd7f96a8fef2113e0490cf29344fb6122a3610dab288395d5b169104e57bcb7`；同根Code79427B、`841eadc6bd440597e55e69bbb31f71a9740a4dd1ef33735de203c48081fe9f32`；budget1441B、`70e4c89fbdc4fef008a331d893a9b39fd80a6a7688ed93a1b6e149ff3f6694b8`。真实Jupiter XML45680B、`c36f4b16146dfa3cab0ced7d361d17626034165dd0ef87aafc90d046a43c5518`；owner独立Code14697B、`901b3a23bb7db9f3fc94ae90cad26d7cebac3ba42f7b61a6b4baa9d86ba26905`及首次solecase5991B、`b9b261e83ca8d37751a0b292892c4513d226c9656f316edfce7a17574932b4d8`。N/J/R为Native、Java交付及Root隔离证据根，原件和来源保持。

P202只读两点另账：reducer125–143的tuple target已一次计算，active/completed为不同数据，保各自校验；另一个codec重复处理若要省须动冻结validator或引入新DOM/raw桥，均不实施。firstseen/PARTIAL缺行不等0hit或成本0，未硬凑小常量或tinywith新单元，不借旧PARK。纯只读结果不增加正式文件或停止主线。

exact4只本Reducer叶+unit/daily11-10/W46；原Test2、Obj、其它生产源、AGENTS、CI、pom及运行文件不变。本源码切点actual软件current368，future369与Root后到采用另账，不预填adopted；无Runtime/Game/GET/P100/SAVE或10秒目标信用。零新增确认保存日，秒/新增保存日null，持续目标不因单元发表完成。

Root limited source acceptance: `R/P201-LIMITED-RETAINED2-CODE-FIRSTMISSING1P-ACCEPT01.json`10694B / `9462594408a7cf6c5dc0835cb0047c29f0d7c25532f663206eeac7b66af77d67`. Normal DATA/source/full Code/first selected missingProjection1P only; software369 adoption separate, no Runtime or performance qualification.
