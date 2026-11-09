# P187：保留结果计数的长度标量替换，有限正常DATA源码接受

Root已接受本单元有限正常decoded、nonnull Bytes域的源码／Code等价：只把保留结果队列两处长度用防御getter改为已经采用的Bytes.byteLength。**本轮没有任何Test、JUnit、benchmark或完整workload**，范围在首次VM前已固定；分支命中、真实结果尺寸／频率、实际allocation／CPU／wall与caller收益均 **UNPROVEN／NOT_HELD**。没有用旧P181来源假设冒性能绿样，也不把本单元当10秒目标通过。

本次正式源码切点离线软件仍actual360，尚未采用该候选；后到软件候选及Root实际采用另账。不授JVM装载、body热更、Runtime、Game、P100、GET、账本、SAVE；零新增确认保存日不报有限秒／日。P188单叶原型只留隔离D目录，未混入本次Git。

## 仅两处counter RHS

[NativeGameTransport.java](../../java/ck3-control/native-transport/src/main/java/org/xar/ck3/control/nativebridge/NativeGameTransport.java)基底152664B／`242e6379fbe84e6811b69040678a9ef4b74cea794c76a3bcb828e089fa820d67`，与actual P171已闭编译输入及本次授权47d0正式叶整字节相同。新152660B／`6a794c8db6a23abf3f4e6c52e60a47be8d138532d871e1d319f6138aac266a22`；仅1783与1790物理行的 `result.packet().value().length` 改 `result.packet().byteLength()`，行数与其它source字节全部保留，整叶inverse精确恢复基底。

retain原有packetIdentity独立copy／hash、sentRequestIds与originalResponses、重复request的独立完整Arrays.equals、预算predicate、terminalFailure文字、lateResults.add和retainedResultBytes递增原序保持。removeRetained仍先执行原lateResults.remove predicate，再在true时减计数；其它outbound／HELLO／received／evidence的value().length不改。没有新local、field、type、helper、API、cache或raw+typed平台；NativeGuard／parser／hash／oldencode、captureFreshSnapshot、HELLO、execute／poll／collect、fresh READ、UNKNOWN与P171既有字段／Fingerprint／close行为均原字节保留。

现有NativeWire.Bytes为final record，构造器own clone、value()防御clone，P174已采用的byteLength为读取private数组length的6B纯标量。数组长度不随内容变化，因此无hash／provider只读前提，不把原packet／比较副本移出其角色或保存第二份原件。NativeWire.decode原guard后构造Bytes及CommandResult，正常私有队列保持该对象；public CommandResult record自身没有nullcheck，任意伪nullpacket／私态／反射／Unsafe不纳正常decoded域，不能宣称帮助性NPE全文或全部Throwable等价。

原retain计数前和remove成功后各去一次长度getter分配／OOME机会；资源失败或UNKNOWN时序变化不被静态值等价掩盖。既有标量只给长度，不给有效帧、ACK、来源、Guard或命令权限。

## 一次实际typing及全部方法Code核验

唯一新1TU26编译真实0accepted、CLOSE **2026-11-09T13:07:24.058144Z**、fenced／released；没有重编旧SDK／Test。25个nested SHA与P171旧件完全相同；Top122993B／`5e375e5f39d138cb7bc203c33bd8e31ca70915a870e3f84ccaf167cceba98b84`，旧ABI、fields、声明、MethodParameters与Nests保持，无结构增量，但不据此补授实际热载。

实际122方法中仅retain／remove两处标量操作发生预期语义差异：retain Code279→278，remove31→30与必要ifeq offset30→29；原value调用PC202／22在新体改为byteLength，原计数和控制顺序保。其余 **120方法normalized Code／resolved CP operands／constants／完整bootstrap args／exception table／controlflow相同**，其中 **93 raw Code SHA同，27仅CP索引重排**；不能误写全部raw相同。常量池3370→3373仅新增byteLength UTF8、NameAndType、Methodref三symbol，旧字符串／数字／bootstrap保持。Root还直接核实际classfile／hex／SHA与两操作inverse，Native65条引用pin全部通过。

本单元以已有P174 Bytes6B／API历史和本次normal DATA值操作／actual Code等价为依据，不假造一次功能调用。现有 EventOptionLocatorDiagnosticsTest完整helper涉及后继PlanningReadGuard、execute与AckReceived，已按原约束排除；未裁剪当新fixture、伪造ACK／outbound custody／Guard，未换完整case或benchmark填命中。drainLateResults只是copy／clear／计数归零，不经过removeRetained，不能拿它冒remove正例。合法tiny完整selector、真实remove与大结果fixture仍NOT_HELD。

## 全费用与预算

唯一编译actor **7.598461s**、operator **9.980979s**仅资源子窗。Native首次已持artifact **12:54:46.836739Z → CLOSE757.221405s → qualification1196.387477s**；owner SourceReady **12:55:27.023490Z → CLOSE717.034654s → qualification1156.200726s**是另一已知较窄窗口，不相加。更早真实只读／来源准备起点 **UNKNOWN，不记0**，全部source、排除fixture、资源／审阅／调度等待、资格与Git费用保留。

保留原0VM准备错误与派生更正：writer01 raw-index核验拒绝、02更正；Root Git blob walker错误；Native误指P174资格文件名后纠正。这些都不是Java RED或第二次编译，不因typing通过抹掉等待。准备metadata旧快照922679B与Root接受时 **951845B**静态快照分别保留，后者在4MiB内，classfiles／所有tmp／日志／错误件都按原分类计；瞬时连续硬峰值仍UNKNOWN，不据逻辑静态数授Java heap peak。

可核原件：`R/P187-FINAL-LIMITED-SCALAR-COUNTER-SOURCE-ACCEPTANCE01.json`，4868B／`4b69bde281ef5bbdaae13fc54f3e2563da287a26695cba698be451343dd1a011`；`N/p187-retained-result-length-prod01/QUALIFIED-P187-TYPING26-ALLMETHOD-INVERSE-ALLCOST01.json`，27155B／`813acc18d5b3f9eb77cd9e037cd6797ea2b1293554563510686f96ad194b928e`；同根全部Code证据95497B／`cfa96e846c9ec2e4528cb1006c05c98fe14550d64313104edc6fe08253cb0b50`；`J/construction-retained-result-length187/candidate01-owner/SOURCE-READY01.json`，3546B／c346187f…，wholeinverse12685B／dbbcef71…。N／R／J为隔离证据根。

正常exact4只发表本生产叶与unit／daily／weekly，原Test、Guard、其它Source、AGENTS、CI、pom不改。不恢复旧PARK分支，不把source接受、编译、Git、后到软件基线及Runtime混账；P188及持续性能主线独立继续，不因本次交付结束。
