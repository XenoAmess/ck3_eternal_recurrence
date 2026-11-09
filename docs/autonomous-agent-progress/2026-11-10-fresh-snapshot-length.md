# P195：fresh snapshot解析前的长度getter改为既有标量

Root接受有限正常decoded、nonnull immutable Bytes域的源码／实际Code等价：只去掉captureFreshSnapshot里**第二个仅取length、随后丢弃的防御副本**。本轮只有唯一1TU26编译和静态资格，**Test／benchmark／完整workload为0**；真实caller命中、packet尺寸／频率、实际allocation／CPU／wall或端到端收益均NOT_HELD／UNPROVEN，不拿既有标量组件测试冒这个新caller的运行通过。

本单元SourceReady及编译发生UTC11-09 16点后，对应Asia/Shanghai **2026-11-10凌晨**，因此写本日记录；所有证据UTC切点保持。正式发表切点实际离线软件仍current363，后到candidate364及Root实际软件采用另账。不授JVM装载、body热更、Runtime、Game、GET、P100、账本、SAVE或10秒目标；零新增确认保存日，秒／新增保存日为null。

## 一个operand，原首副本与全部验证保留

[NativeGameTransport.java](../../java/ck3-control/native-transport/src/main/java/org/xar/ck3/control/nativebridge/NativeGameTransport.java)基底152660B／`6a794c8db6a23abf3f4e6c52e60a47be8d138532d871e1d319f6138aac266a22`，是已采用P187正式叶；新152658B／`ebc20b2e0d380358e2c34f60fba8dbde395957a9015192317d0e2dbbd9b5b728`。只改966同一物理行中Arrays.copyOfRange的第二个长度operand：received.packet().value().length→received.packet().byteLength()，整叶inverse精确恢复基底、总行数不变。

pendingFreshSnapshot为null的早返回不动；第一个received.packet().value()仍原位置产生原防御copy，offset4不动；第二operand才读同一immutable Bytes长度。原Arrays.copyOfRange、NativeWire.parse、object、read_request_id marker、匹配／重复帧检查、capture赋值、session与chronology顺序逐字保留。HELLO、其它小包、Guard、execute／poll／collect、fresh READ、UNKNOWN、此前P171字段／Fingerprint及P187计数均不变，无新local、field、type、helper、API、cache、bridge或issuer；parser／Unicode／hash／oldencode及NativeGuard算法未改。

现有NativeWire.Bytes是final owning record，构造器和value()都防御clone，P174已有byteLength()为6B直接private数组length。数组长度不随内容变化；只用长度，不复用哈希后可变内容，不加provider只读或新检查前提。正常非null decoded DATA下与第二clone.length相等。原首clone失败位置保持，但删除了第二clone／OOME机会，**不授全部Throwable／OOME／资源失败时序或恶意私态等价**；标量本身不给有效帧、fresh发生、来源或权限证明。

## 唯一typing与全部122方法资格

当前旧Transport实际来自P187完整26族，P195沿真实release21、-g、-parameters profile；新编译0accepted，BEGIN **2026-11-09T16:06:49.159216Z**，CLOSE **16:07:00.565891Z**、retained HANDLE终态后fenced／released。未编旧SDK、Test或Main，没有任何后继测试／profile。

25个nested与旧SHA逐件相同，仅Top122992B／`24f94d9c8c1293e2ea09e78c60fcb394137616c49524876e88eaa06232ce95b9`变化（旧122993B／5e375e5f…）。旧API、fields、方法声明、decoded MethodParameters与Nests保持，无结构增量，但不补授实际body热载。

122方法中仅captureFreshSnapshot Code201→200B：首Bytes.value PC16保持，旧第二value PC24改既有scalar并删旧PC27 arraylength；range／parse／marker和必要offset归一inverse通过。其它 **121方法normalized Code／resolved CP operands／constants／控制流／exception table／完整bootstrap相同，其中61 raw Code SHA同、60只CP索引重排**，不能写全部raw相同。CP symbol multiset及bootstrap均保持，byteLength原已用于P187计数，不新增symbol或算法。Native资格65个引用pin已重hash，Root另核含资格本件的66个独立原件。

NativeFreshFullStateReadTest的现成public软件路径source可能自然经过该caller，但本轮其compiled／run qualified回执NOT_HELD；未为补命中裁剪／新造Guard、ACK或largefixture，也未追加selector、benchmark、完整case。P171／P172普通observe样本与P174 public scalar历史均按各自原边界保留，不变成captureFreshSnapshot动态命中证据。

## 所有费用与原件

唯一编译actor **11.0707384s**、operator **14.1906162s**仅资源子窗。owner SourceReady **2026-11-09T16:01:10.638381Z → CLOSE349.92751s → qualification518.628572s**；Native CFG首持artifact **16:04:33.364568Z → CLOSE147.201323s → qualification315.902385s**为其内窗，不相加。Native preflight文件mtime15:59:27.605229只是文件切点，不是精确研究开始。更早只读／来源／P193边界研究起点UNKNOWN，不记0，准备／审阅／调度等待、资格与Git费用保留。

Root两次0VM list-schema assertion错误及更正均保存：把26行list误比integer26、把空CP新增／删除symbol list误比integer0；物理pinwalk无mismatch，不是Java RED，不导致重编。Native资格前metadata **843826B**静态快照保持，qualification后871084B、summary1988B后为 **873072B**，在原4MiB内，所有tmp／classfiles／日志／原件保留；瞬时连续硬峰值UNKNOWN，不把逻辑静态数当Java heap peak。

可核：`R/P195-LIMITED-NORMALDATA-CODE-ONLY-SOURCE-ACCEPT01.json`3872B／`9c90f115eaec4bda557b4b16c77a661914456f2b759984b7d0d607971a692736`；`N/p195-fresh-snapshot-length-prod01/QUALIFIED-P195-TYPING26-ALL122-INVERSE-ALLCOST01.json`27258B／`72a920dacdaf2635e6139f0d8f124299ded238bdc2d562a24e0f7268970003c7`；同根全部Code84805B／`2a6110a423d3b9ac4752df2d85a2e87b40ad72c5be3388adecc78d3e6b7f25c6`；`J/construction-fresh-snapshot-length195/candidate01-owner/SOURCE-READY01.json`2837B／b6e3fadc…，wholeinverse3872B／51f7a734…。N／R／J为隔离Native、Root和Java交付证据根。

exact4仅该生产叶、本unit、新daily11-10及原W46追加；旧11-09记录、所有Test、P196原型、其它Source、AGENTS、CI、pom与运行文件不动。源码、typing、Git、后到离线软件采用与Runtime／SAVE继续分账，P196独立D原型不作本单元通过条件，持续目标未完成。
