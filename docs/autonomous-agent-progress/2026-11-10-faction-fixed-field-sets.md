# P220：派系赠礼策略复用三组固定字段集合

FactionGiftPolicy.choose 每条 observation 原本在三个字段检查循环中构造固定 Set.of(7/7/3)。本单元把原三个表达式及字面参数顺序移到 JSON 初始化之后的三个 private static final Set<String>，循环仍各自获取 iterator，原检查、Reason、分支和执行顺序不变。其余 parser、Guard、候选选择、比较、编码与持久化程序逐字保留；整叶机械逆变换恢复正式基底。源码19591B/340218b7…→19878B/2125a8d5…，324→328行。

正常私有解析对象域中，三个 Set 的元素与构造参数顺序相同；限定于已核 JDK21 SetN 布局和同 VM 的 salt/迭代方向，保留原字段检查顺序，没有改成 array、排序、索引或缓存 observation。源码代数仅为每条完整到达的 observation 最多三次 SetN 及其六个引用数组构造转为类初始化一次；iterator 和检查仍执行。这是静态工作消除，未量测实际分配、JIT 消除、CPU/wall 或自然频率。原 golden 只有0–2条 observation，实际 caller 源码每次一条；256只是上界，不能用来放大收益。

代价是三个图常驻，并把构造工作前移到首次类初始化，包括仅 encode/decode 首次使用时；冷启动、OOME/ExceptionInInitializerError、资源和异常时机不作全域等价声明。新增三个私有字段也不是仅 body 的热重定义资格。

唯一生产1TU3编译实际0并 CLOSE fenced/released。实际43个程序中其余41个完整 resolved Code、分支、异常表、参数和 BSM 保持；choose 的三段 Set 构造改为 getstatic，clinit 在原 JSON 完整前缀后按原组序追加三表达式。公开 API 不变，字段精确新增3个，CP新增9项，5项 BSM 完整相同。原 default LNT/SourceFile、无普通 LVT/MethodParameters 的形态保持，record mandatory 参数照旧。全部97条 choose 行表按已声明+8/+6/+4逐项映射，嵌套行表+4。LDC 宽度按原符号和逻辑 PC 精确核：other41内6处、choose保留段13处、原clinit前缀21处，17个搬移字面中13处宽度差；没有用全局 mask 或要求调试行已变的 nested raw SHA 相同。

随后必要的原 Test1TU1 编译及唯一原全类 JUnit 均实际0/CLOSE。三 engine XML 合计 **70通过、0失败/错误/跳过**：原63个 factory 案例和7个静态方法，没有裁剪、包装、新 fixture 或追加 benchmark。原 Python unbounded-integer 案例的既有 signed32 适配及完整 expected JSON、模型恢复、稳定编码、输入 JSON-domain roundtrip 均保留。逐个动态 [i] 的完整 unique-id/display 层级对应原资源 cases[i−1].name；XML 文档不要求按索引排列。Test源11985B CRLF 规范化后与Git11788B整叶相同，原资源115155B/04e92400…字节相同且本次 CP 首资源命中在379；actual Test16718B/ab3e905f…及新生产三类来源均核。70例是原软件功能资格，不代表三处自然频率、全域性能或 Runtime。

三次实际 JVM 仅生产编译、原 Test 编译、原全类 JUnit；actor合13.990347699960694秒、operator合19.24296899989713秒是嵌套子窗，不能相加或代替整轮。具名 Plan→末 CLOSE2774.475391秒→final2999.570000秒，SourceReady→CLOSE2287.300990秒→final2512.395599秒；更早真实开始 UNKNOWN。准备、来源/Code/XML审阅、失败纠正与全部等待都在全窗口中保留。Native final 写后四 metadata 根1365181B（后到 Root70件后1367425B），tmp/ownedDLL文件0，不代表连续峰值、Java堆或全进程JNI为0。

原0VM错误均保原件：稀疏路径读取、97条LNT误当首行、raw catch PC与逻辑PC、旧clinit末return行表、actor/controller函数位置判断，以及owner把包含LNT的Code属性当raw同、14总行项误当13前缀。owner两次Code checker工具窗0.2205739/0.2242984秒，XML来源诊断误迭代attrs字典工具窗约0.4秒，精确进程耗时 NOT_HELD；只修读法/统计与已声明精确映射，没有改源码、实际类、测试、比较标准或重跑Java。后到owner70与Git成本另件记录，不倒填旧final peer pending切点。

主要原件（J=D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108，N=D:/ck3-state/resume91-native-integration，R=D:/ck3-state/resume91-root/post-vacation-20261107）：

- J/construction-faction-fixed-sets220/candidate01-owner/SOURCE-READY01.json，3342B/00c86a9f…；whole inverse4000B/b852c07b…。owner actual43独审19885B/21d9efec…，原70独审24462B/5ee9df39…。
- N/p220-faction-fixed-sets-junit01/QUALIFIED-P220-SOURCE-ACTUAL43-ORIGINAL70-ALL3COST-FINAL01.json，34681B/4b0c5eb4…；Jupiter XML81953B/906af0b2…、原资源115155B/04e92400…。原producer证据只按其既有元数据和测试断言保留，不冒当前Game采样。
- R/P220-ALL3COST-SOURCE-AND-ORIGINAL70-DELIVERY-INDEPENDENT-ACCEPT01.json，1975B/689975eb…；后到root/owner审阅原件与旧final历史分别保存。

本次正常 exact4 仅生产单叶、本文、daily 和 W46，原 Test/resource/tools/CI/AGENTS/pom 不改。发表时当前仍是独立选定的 OFFLINE377；候选编译、源码发表、新离线输入选择、实际装载、Runtime 与 SAVE 分账。没有 benchmark、整局/自然频率提速或新增确认保存日，秒/新增保存日无新有效数字，10秒目标未授；主目标继续。
