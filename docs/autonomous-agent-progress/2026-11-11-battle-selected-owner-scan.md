# P224：选中owner损失行的完整扫描复用

本单元仅改BattleRetreatPolicy.assess原200–206行：将List.copyOf已持有的owner loss行经stream/filter/toList构造匹配列表，再用size/getFirst的接线，换成原顺序完整foreach、int匹配数和唯一匹配行引用。源14990B/7fd3b92b…变15123B/988c668e…，270→276行；唯一hunk逆换后与正式72a140a7的整文件bytes完全相同，其余imports、记录/构造器、helper和后续政策原文保留，没有索引、缓存、helper、字段或新类型。

循环不提前break。每行仍先取得row.ownerCharacterId再取得observed.selectedOwnerCharacterId，均为final record的int getter；同一列表顺序完整评估原谓词。匹配数为0或大于1时仍先返回原query，不读hard；恰一条时才按原null短路、第二次hard getter/signum、第三次取得hard、调用预算getter/compareTo的顺序继续。List.copyOf及原校验不动，OwnerDelta字段引用不被外提或重建，公有BigInteger的signum/compareTo回调顺序保持。多匹配时局部引用覆盖不影响count先拒绝；计数不超过List的int大小。后续phase/preview、策略返回及所有Guard/parser/hash/oldencode不扩大或删减。

实际唯一生产TU编译成功，得到完整22类。旧170个Code程序变169：只删除原17B private synthetic lambda$assess$0；21个嵌套类整份binary相同，其他168个完整程序/字段/公共API/Nests与结构保持。BSM4→3仅移除old1的原filter闭包，保留项逐descriptor/内容映射；CP548→532，精确30项移除/14项新增只服务stream视图到iterator/count/row接线及局部调试名，没有业务String/数值/Field变化。

目标assess737→741B，maxstack11不变、maxlocals14→15。313条保留指令的完整符号、操作数、分支与局部slot逐一核对，原14条去除、新23条加入；循环整个初始化/hasNext/next/cast/原谓词/计数/回边均核验，无早退。保留指令old388的load在new394，但进入原388的分支必须指向new388初始化，明确使用两张map，不作全局mask。唯一LDC缩宽为old515→new520、19→18，仍是同一within-caller-budget字面。

hard getter原437/453/479对应new458/466/484，null/signum及预算比较顺序相同。iterator slot10只在循环使用，new487先存hard后489读取；row slot11只在循环使用，new506先存boolean后508读取。全部LVT端点/类型、被删ownRows泛型局部、新三个具名局部及展开后的27个旧StackMap frame和3个新loop frame均精确核对。新scan源行明确记录，old207之后源码行+6；不把调试PC、栈迹、GC、临时对象寿命或OOM时序说成逐字相同。删除方法的shape变化也不构成旧类body-only热重定义资格。

必要的原Test只首次增编1TU/1类，再唯一完整JUnit：32个原golden动态向量和5个静态测试实际37通过、0失败/错误/跳过，suite2.304秒。原Test9298B/07d5470a…及resource107656B/SHA1351a9dce0f3dce0619dc13bf65b66c9c74dd30f03691930a0cec410b8c59613未改、未复制、未裁剪；逐factory[i]完整UID/display核对原cases[i−1].name，不要求XML文档顺序。case19 duplicate_owner_rows、20 missing_selected_owner、21 null_selected_loss、22 negative_selected_loss覆盖核心拒绝路径，完整向量保留模型roundtrip和encoded Decision全expected；原5个类型/缺失/身份/preview/非授权输出断言全部保留。没有新增镜像测试、fake fixture或实际动作/Native/账本调用；原37不冒全输入域穷举或性能测量。

本轮仅三个软件JVM：生产编译、必要原Test编译、原完整JUnit，均exit0、契约接收及CLOSE fenced/released。actor合12.225419200025499秒嵌在operator合15.147572800051421秒内，不能相加或代替整轮。SourceReady05:22:01.416932Z→JUnit CLOSE05:35:55.159247Z为833.742315秒，至final05:45:46.144144Z为1424.727212秒。Plan05:29:11.475504Z是晚于SourceReady的封件，其到CLOSE403.683743秒/到final994.668640秒不是初始begin或许可；更早真实开始UNKNOWN。所有准备、模型辅助审阅、编译、Code/XML核验和等待都保留，正式发表成本后到另记。

Source、owner Code和XML核验首次成功。planning classreader偏移、Root误猜PATCH.diff文件名、Root把保留行map误作loop入口branch map的0VM错误保原；本岗后来读final误用lowercase close而实际键为CLOSE，写证明前KeyError，仅改元数据读取，工具窗0.1728636秒及未知process耗时不计为0。Root另一次final reader误把bool/dict当scalar也保原；没有源码、class、原Test、次数或准入标准调参。final六根1263347B<4MiB，包括独立planning根；三处tmp各一个空目录、regular files/bytes为0，外部Root181746B完整语义原件只pin不复制，不授内存峰值或process-wide JNI为0。

主要原件（J=D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-battle-owner-scan224，Q=D:/ck3-state/resume91-native-integration/p224-battle-owner-scan-junit01）：

- J/candidate01-owner/SOURCE-READY01.json：3308B/8c8e0c3a…；新源15123B/988c668e…及唯一wholeinverse patch。
- J/owner-review01/ACTUAL22-168OTHER-313RETAINED-FULLSCAN-OWNER01.json：26025B/0695ba66…，直接实际22/169Code独核；原Source/Test/Codec的分层来源不冒全SDK编译谱系。
- Q/reports-junit/TEST-junit-jupiter.xml：65709B/9f9be3dd…；J/owner-review01/ORIGINAL37-FIRST-FULLCLASS-XML-OWNER01.json：17811B/13181506…，actual0/完整37+UID与原资源对应。
- Q/FINAL-P224-SOURCE-CODE-ORIGINAL37-ALL3COST01.json：20660B/19f838e6…；J/owner-review01/FINAL-ALLREFS-THREEACTUALS-ALLWINDOWS-CONSISTENCY01.json：1400B/1242954c…，fresh48唯一pins、三actual/CLOSE及24个完整UTC窗口。

正常exact4只发表唯一BattleRetreatPolicy叶、本单元及daily11-11/W46追加。原Test/资源、其他生产源码、tools、CI、pom、AGENTS、运行source307不动；软件发表、未来OFFLINE380候选/实际选择和Runtime装载分账。本轮没有benchmark、自然规模/频率或实际allocation/latency收益证据，不借P223微秒结果；不授P100/Sway诊断、Game/Runtime准入或新增保存。newSAVE0、秒/新增保存日为null，10秒目标未通过，主目标继续。
