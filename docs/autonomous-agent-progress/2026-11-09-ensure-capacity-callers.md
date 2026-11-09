# P185：定点补取41条已记录caller链，无新的业务源码候选

P182已知41个AbstractStringBuilder.ensureCapacityInternal叶Execution样本，但旧有界top输出的96条链没有任何一条含该方法，不能把83key PARTIAL应用轴拼成同一样本caller。P185只对**同一份成功P182 raw**运行一次新的定点JFR工具，不新profile、不扩业务采样。唯一工具真实0accepted、CLOSE、fenced／released；完整EOF后保留全部41条匹配的原recorded前缀，支持两叶有限源码核查，结论 **NO_CANDIDATE**。工具通过不等于业务性能优化、Runtime或SAVE。

## 小工具与严格原件边界

[P185EnsureCapacityCallers.java](../../tools/performance/ensure-capacity-callers185/P185EnsureCapacityCallers.java)为受测原字节 **14801B**／`4d8850add3ab3c5121b4f88fd0966215fc9d7a85bc4f56728740e1e0333f9225`。它是独立纯JDK源模式工具，只用jdk.jfr.consumer、1TU／唯一top声明，源码编译含在唯一工具JVM内部；AppCP0，无第三方、SDK、反射、新平台或缓存，没有持久compiled class cache授信。仅显式tools/performance入口，不进入默认Maven编测，不修改原Tool02、旧报告、生产算法、Test、AGENTS、CI或pom。

工具只接受固定成功raw `N/p182-current-integration-profile01/raw/current-integration182.jfr`，**8340560B**／`442632bf590a2c79bc473dbb7f2d0ddc8e9e81ff9ad56dada7159790d3fe1d0f`；输入真实路径、大小、前后SHA与mtime核同。它不读P152失败raw、不写原件，不接触Runtime／Game／P100。前后SHA／属性一致不等于持有同一OS文件HANDLE身份，输出明确retained_OS_handle_identity_proof=false。

过滤精确为 `jdk.ExecutionSample`，原frame0的class `java.lang.AbstractStringBuilder`、方法 `ensureCapacityInternal`、descriptor **`(I)V`**；descriptor取自P182实际method277，不猜。sampledThread必须为原事件真实RecordedThread，stack必须实际存在，绝不用eventThread替代。保事件原timestamp／ordinal、thread ID与名称／virtual、原state／类型、isTruncated，以及每帧class JFR ID／class／method／descriptor／line／BCI／frame type／isJava／hidden。固定列数组配完整frame_columns，保顺序而不复制字段名；null／负line等unknown显式留，不补根、不替换成完整逻辑链。

上限为64样本×64 recorded帧、每metadata字符串4096字符、event类型128、输出 **1048576B**。任何cap超界均失败，绝不截断为成功；41与完整类型分区只在EOF后核对，不据41提前停或过滤差异。输出existing-parent／CREATE_NEW，拒覆盖；失败stderr与可能部分新文件保留为失败原件，不删除、重写或冒completed。Main timer不含pre-main源编译、报告序列化／write／stdout／exit，Native另计完整进程及准备费用。

## 实际EOF与全41链

实际输出 `N/p185-ensure-capacity-callers-tool01/derived/P185-ENSURE-CAPACITY-CALLERS.json` 为 **729900B**／`f718f0b33e208459c425549e5ef711c7d51b7f8491a6f93d91c10d75852af116`，在1MiB帽内。fullEOF **26253** 事件与P182原报告全部12个实际发生类型逐项相同；Execution752、Native4325、Allocation19817等类型总和匹配。这不是总共只有12个启用设置的宣称，也不消除P182原53缺栈、64截断或PARTIAL应用轴限制。

41匹配sampledThread均真实且missing=0，**41×64=2624帧**全原序保留；全部原isTruncated=true，**474个负line是原unknown**，没有补成源位置。事件条数、目标样本数都不是方法调用次数、CPU秒或自然频率；FQName／JFR class ID不是运行时class SHA或完整源码来源。

按离leaf最近的实际org.xar帧独立聚合：

| 最近org.xar caller | 原line／BCI | 匹配记录样本 |
| --- | --- | ---: |
| FullJsonTree.read | 81／208 | 25 |
| NativeWire.parse | 195／57 | 9 |
| RawJson.validate | 81／93 | 6 |
| DriverJson.write | 213／251 | 1 |

25条通过Jackson TextBuffer.contentsAsString／ReaderBasedJsonParser.getText建JSON文本节点；9条通过UTF8解析与ObjectMapper.readTree；6条getText交原Unicode校验；最后1条为StringBuffer／StringWriter／WriterBasedJsonGenerator实际编码。均未出现类似P163成功路径丢弃完整record.toString的诊断构造，不借P163旧链或旧96链补caller。

## 两叶核查与历史class来源

严格只读两个源码叶：FullJsonTree.read81是 `factory.textNode(parser.getText())`，实际消费JSON字符串；RawJson.validate81是 `unicode(parser.getText())`，其高低surrogate检查依赖真实字符。它们属于冻结parser／Unicode验证，不是无用成功诊断，不能删校验或引入新carrier／cache来省。另两组NativeWire.parse与DriverJson.write已在原parser／oldencode冻结体范围，直接排除，没有扩读第三、第四leaf。结论仅本定点窗口NO_CANDIDATE，不证明全程序不存在eager诊断或其成本为0。

按**原P182 actual357／workload CP358**定点首origin并重新核SHA，而非用后到current360类代替：FullJsonTree在index41、C0 contracts root，10891B／9be504f1…；RawJson在index72、C0 application root，7035B／cbc94538…，是P183新增API之前的旧类；NativeWire在index4的P174 root，DriverJson在index10的P143 root。selected实际Code薄核进一步确认FullJsonTree private read Code276B，JsonParser.getText调用PC208／233；RawJson.validate Code124B，getText PC93。此调用点与recorded BCI一致，不授whole C0 compiler-source绑定、原flags或JFR动态loaded class SHA。

## 全部费用与保留错误

唯一source-mode工具actor **2.8342768s**、operator phase **3.4573392s**、whole operator **3.6968572s**仅子窗，包含内部源编译而不含全部研究准备。较早已持Java SourceReady **12:01:54.546393Z → CLOSE 2138.752256s → qualification 2282.151374s**；Native首次artifact **12:34:52.812391Z → CLOSE160.486258s → qual303.885376s**是较窄历史窗口，两窗不相加；更早实际开始UNKNOWN而非0。CLOSE为 **2026-11-09T12:37:33.298649Z**。

所有源编写、合同、字段核验、配置别名、资源／调度／Root审阅与等待、解析／报告写入／退出、资格和Git费用保留。Owner最初PowerShell rg参数误解析导致cwd只读扫描，工具约1.4s，输出截断；没有引用无关结果，随后只以Python读精确Tool02单叶，错误原件1056B／790bc9d2…保留，不伪造未持有的完整local stdout。Native后置两叶预检另有0VM inline quoting与fullSHA誊写assert错误，原01／派生02／错误件都保，非Java RED或再次JVM。

Native qualification时最终静态metadata **1655780B**、derived729900B在原4MiB／1MiB范围；后到selected-Code与0VM错误薄件追加后Native报告metadata1675541B，旧快照保当时事实，不覆盖。它们是逻辑静态观察，不是连续瞬时硬峰值或Java heap peak；原P182 raw仍外部只读保管，未重分类／删除其它tmp或旧原件。没有新profile、旧业务／Main／SDK／Test编译、HTTP、Game、GET、P100、Runtime或SAVE；当前离线软件360不因工具Git变化，零新增保存日不报有限秒／日。

可核原件：`Q/QUALIFIED-P185-ONE-TOOL-EOF41-RECORDED-CALLERS01.json`，15938B／`ad41d2cdedfaa50c06a9ca7175c51ec4c5ae8414e5577900d81a23478a0f8a7f`；`Q/ACTUAL-TWO-LEAF-READ-VALIDATE-CALLPOINTS01.json`，13282B／`367ab0b9c369b05e0833cdb5966878502d5a818a2875621e0e3581a14065db62`；`R/P185-ACTUAL-EOF41-ALL64FRAMES-NEARESTCALLERS-INDEPENDENT01.json`，2409B／`b74b6ce10861a38ff0e46ad17335788e115709260b4b6f762a527b20388d23c6`；`J/construction-ensure-capacity-callers185/OWNER-ACTUAL-41-CALLER-SOURCE-REVIEW01.json`，10345B／`9243a3dd86d08bec68646b68c39397cbead61017314815f16034bb2127fb3e6d`。Q为N/p185-ensure-capacity-callers-tool01，N／R／J为隔离证据根。

本次只发表该独立工具源与unit／daily／weekly，不改生产／旧工具／旧报告／Test或Guard算法。P186独立两叶只读及后继性能主线分别继续，不以本记录或NO结论冒目标完成。
