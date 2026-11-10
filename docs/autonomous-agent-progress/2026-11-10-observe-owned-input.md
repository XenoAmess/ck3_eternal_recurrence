# P216：observe 内部借用已拥有 Input 字节，只有 Code 资格

本轮仅改 OrdinaryWarPriority.java 102、103 两个表达式，290行及其它源字节保持：首 RHS 为 record(parseFull(input == null ? input.snapshot() : input.snapshot))，次 RHS 为 StrictJson.parse(input.nullableCampaignRoot, StrictJson.EXPLICIT_MAX_BYTES)。整叶逆变换恢复 P214 正式源码24432B／a9a9b3f4…；候选24463B／SHA256 02c492594c99efff2992209343aa05f6782adc58cf8ee67f5bc9465c2602f724。

Input 仍为 final record，公开构造器仍独立 clone 两个非空数组，公开 getters 仍返回 clone；finance 及所有其它调用原样。正常构造的 Input 私有 final 字节数组没有外部可变别名，本次仅在同调用、同家族内部交给原只读解析消费者，不新增 API、字段、type、carrier、cache 或授权来源。Root 有界核了 StrictJson 四个实际程序及原 FullJsonTree parse/read/fresh-factory：借用数组不改写、保存或返回原始别名，原 parser/validation/预算/Guard/hash/oldencode 算法完全未动；未把有限程序证据扩成全旧 C0 编源谱系。

首项特意保留 null 分支的原 snapshot() 调用，避免 bare getfield 改变 helpful-NPE 方法语义；snapshot 解析及 record 成功后才读取 root 字段。该边界由源码与实际 Code 证明，没有执行 null 负例或观察实际 NPE 文本。删除两处丢弃的 getter clone 同时去掉相应 OOME 点，不宣称资源失败、恶意反射/Unsafe/私态或所有 Throwable 等价，也不把字节码少 clone 直接换算成实际分配、CPU/wall 或频率收益。

唯一生产1TU4编译实际 exit0／accepted／CLOSE fencedreleased，没有 Test/JUnit1P/benchmark/fullcase。Top30189B／a07b1dfd6ebd4cbc29570a7feb5b2f3b4e9fb30a9142d08664148ec2a3162ae0；Input、Observation、FinanceRequest 三份 class 与 P214 binaryexact。Top 的另外45个完整程序（2raw／43resolvedCP）加 nested27个程序共 other72 保持，API/fields/参数/Nests/BSM41及旧 literals 相同。

observe 1970→1982B，maxstack5/maxlocals34 不变；null 路径在PC5仍 invoke 原 Input.snapshot()，非空路径PC12读 snapshot 字段，PC23读 root 字段；parseFull15→record18→StrictJson.parse28 的原解析顺序完整保留。其余全部指令、分支与局部槽逐项映射；唯一 LDC18→19 扩宽为 old659/new670 的同一个 survival reason 字符串。CP只新增两个 fieldref、两个 NameAndType 和 StackMap 合并所需 Class[B，没有新命名产物或 API；finance 的原 getter 调用PC4/18仍在，未误称旧 getter 符号删除。

MethodParameters 仍 input/flags0，LVT slot0/input 覆盖整个方法，source line102与其余行号、所有 LVT/LVTT 区间均精确映射。53个原 StackMap frame 完整保留映射，仅新增PC11空 stack及PC15 byte[]合并 frame。没有 global opcode/local/ordinal/String mask，也不授运行时热替换能力。原 Chooser Guard/ACK/replay/ledger case 整体排除，未裁剪或造 fixture；P215 的组件通过及收益没有迁作本候选的功能或性能验收。

单 JVM actor9.23418979998678s／operator10.441490800003521s只是嵌套子窗。SourceReady→末 CLOSE9687.526186s／Native final10775.283772s；Root source accept→9742.520550／10830.278136s；AUTH→BEGIN64.383180s，CLOSE→final1087.757586s全部保留，更早真实 begin UNKNOWN，不作0或剔除长等待。所有源码/Code/审阅/准备/Root与Native错误及等待保留，owner inline 的 elseNone 语法错误工具0.1654305s只改空格，后纯Python auditor一次成功0.2154652s；确切 process耗时未持，不是 Java 重跑。Git成本在发表回执续记。

Native 两根及固定外件14405B合计415370B，小于原4MiB；tmp文件0。owned DLL文件为0不等 process-wide JNI 未加载，磁盘快照不是 JVM堆/机器峰值。原件不覆盖，所有成本与资格保各自真实切点。

证据根 N=D:/ck3-state/resume91-native-integration，J=D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108。N/p216-observe-input-prod01/actual/prod/OUTPUTS.json21045B／21b75ed3…，Native final15101B／ebb2f8b5fb117a656d3a9c740c4433b497d0f80386b467c462fd53d54c9f1166；owner完整 peer30489B／31a4cc6d…位于 J/construction-observe-input216/owner-review01，源码/inverse/Ready保在同单元 candidate01-owner。

正常发表仅生产单叶、本记录、日记和周记；不改其它源/Test/CI/pom/AGENTS。实际 OFFLINE375 继续保持，正式源码发表不等编译产物采用、装载、Runtime/GET/P100/SAVE。后继 P217 是独立新 Main、复用旧 Caller 的固定测量，须具名接线与另行授权，不能原样复用 P215 固定旧 roots/pins 的 Main。当前收益仍 NOT_HELD，新增确认保存日0、秒/新增保存日 null、十秒目标未达，主任务继续。
