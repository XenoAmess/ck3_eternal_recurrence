# P150：同次 packet 与不可变 state 双重绑定

Root最终采用本单为限定的软件DATA复用：两种实际输入均有稳定分配下降，组件wall只作有限观察，不授稳健CPU／worker／Runtime或10秒目标通过。使用现有私有 NativePacketInput 的同次来源关系，整包匹配、非null的实际 RawJson 引用相同、包内 state 为标准不可变 Obj 三条件同时成立，才复用 Reader 已解析的 state。整包不匹配即使state引用相同也走旧解析；null／cleared／不同引用／非Obj同样保留原parse→packet.state object→equals及错误序。公共originalNativeState逐字P147，未带入P149抽取helper。

Reader仅新增一个private RawJson引用、package boolean身份查询，并在原clear丢引用；原holder wholeframe clone→RawJson校验→ObservedFrame clone顺序保持，成功frame后才由Reader直接绑定actual.state。stateToken原parser字节边界和全包strict parse证明其为同次完整子树，实际RawJson／ObservedFrame方法体的不变性独立核实。无public raw+typed接受路、Session或跨调用cache；所有fresh custody/hash、Guard、parser／writer／oldencode、identity异常边界和Complete自重播保留。新增field影响布局，不授Runtime热替换；减少分配会改变OOME机会，不承诺VMError／peak不变。

生产首次2TU10、Test首次1TU5均0closed；两个新方法各JUnit1P，功能case2.809秒、组件case6.296秒。功能沿真实公有scoped null／strictnominal／earlythrow／lateIncomplete／借用数组回调／P4，保Unicode词法、integer-0与公共state错误优先级。三门私有miss仅sourceproof，没有mint／反射私有issuer，不伪称全部私有路径已实际覆盖。Reader／Assembler仅首编，Driver／SDK／Main及旧Test0编或补跑，0新profile／HTTP；功能／组件child stderr310／309B原件保留，不当成outer0B。

测量事前固定compact后pretty、每输入8轮ABBA＝32调用（16A16B）、总64、0额外warmup。A为P147shared10＋P143Driver3两root同child13，B为新Reader4＋Asm6和同Driver3 parent，own类型／来源／适配对称。所有原件SHA、semantic、member order、binding及64行post通过，全部冷／慢样本保留。

| 分输入，各16次A／B | compact A→B | pretty A→B |
|---|---:|---:|
| wall均值ms | 52.9579875→36.2110000 | 47.8202500→35.9874875 |
| wall中位ms | 45.52065→34.72185 | 40.35825→31.21285 |
| 8轮wall配对负／零／正 | 8／0／0 | 7／0／1 |
| allocation均值B | 95,235,247.5→67,938,652 | 95,029,231.5→67,927,779.5 |
| allocation中位B | 95,028,972→67,927,800 | 95,029,400→67,927,896 |
| 8轮allocation配对负／零／正 | 8／0／0 | 8／0／0 |
| 当前线程CPU累计ms | 500→421.875 | 515.625→437.5 |
| CPU中位ms | 31.25→31.25 | 31.25→31.25 |

分配后段每两调用约少54.203MB，符合省一次state防御副本／重复parse及树物化；均值的冷A／B0额外开销不全归机制。wall只属本有限组件观察，pretty cycle6 B−A＋58.0914ms与B单行105.1231ms保留；compact也有B55.8877ms慢于邻A53.9114ms。CPU15.625ms粒度、compact A两次0量化、配对方向混合，不授稳健CPU／每调用更快。parentB与fixture／postwriter共享状态、独立factory/JIT／GC、pretty继承前32调用的偏差均保留。自然频率未知，不将两输入混成headline；累计allocation不是peak／live heap。

setup2.405007秒，初始化old13为339.6004ms、parent3.2708ms、source／reflection18.7777ms；组件before-report5.8286513秒。四phase actor合29.6999304秒／outer合35.3651374秒，不代整体。首prodoperator→lastCLOSE738.400620秒，至原qualification899.975008秒；Native preflight16:51:47.149687Z→lastCLOSE926.135104秒／至qual1087.709492秒。更早Root D授权16:45:23.714940Z→lastCLOSE1309.569851秒／至qual1471.144239秒才覆盖其前等待，此前契约审等准备仍UNKNOWN，不记0。最后close后161.574388秒资格整理与所有准备／等待全计，精确child lifetime未持久化exit FILETIME，UNKNOWN。纯metadata曾误判额外private ctor、查不存在JUnit OUTPUTS，以及历史AGENTS误读造成等待，原件保留，均0Java失败／0重测。三根最终元数据1,568,280B低于4MiB；P141旧预算失败不改写。

P149仍为不采纳的独立负结果；本单既未重测它，也不替换其样本，不能将两次独立JVM数据冒成paired A/B。正式Reader27976／Assembler34549／Test29237均按实际编测原字节采用；软件class graph由Native另做0VM导航，不等于实际装载。源码、有限软件、正式Git和实际Runtime／Game／SAVE各按真实回执分别记账，新field布局不授热替换，0新增确认保存日，不授head47／P100或10秒目标通过。P151 normalizer角色缩减另只读PARK，不由此扩大本单。

原件：[全部64行](D:/ck3-state/resume91-native-integration/p150-state-identity-test01/tmp-component/junit-7647392324573161876/p150-scoped-reader-state-identity-fixed64.json)（155,908B，SHA256 `d824ddd6c86a5d7441f3c4036501564e205b05de8e70d2778c9b2638cf7f911d`）；[Native最终资格](D:/ck3-state/resume91-native-integration/p150-state-identity-test01/QUALIFIED-P150-STATE-IDENTITY-FUNCTIONAL-AND-FIXED64-SOFTWARE01.json)（48,193B，`f770a69c8edf6850d0444f6b3fb092302b1a5062ee217b6343c7899ffb30ccaa`）；[Root限定软件采用](D:/ck3-state/resume91-root/post-vacation-20261107/P150-CLOSED-STATE-SOFTWARE-ADOPTION-AND-LIMITED-INPUT-PERFORMANCE01.json)（5,621B，`8ed2bb3649a1db4fdc5d24c964edf77c9bca681686d553c81914daed33c4f591`）；[候选源及整叶逆证明](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-state-identity150/candidate01-owner/CANDIDATE-SOURCE-READY01.json)；[owner独立64行判断](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-state-identity150/P150-OWNER-ALL64-SOFTWARE-ADOPTION-RECOMMENDATION01.json)；[独立采用审](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-state-identity150/read-only-adoption-review01/REVIEW.json)。
