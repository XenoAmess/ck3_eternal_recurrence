# P171：保留上次语义表示，限定软件源码采用

本次只在 NativeGameTransport 内保留上次 canonical Obj 对应的 JsonNode，免去后继接收时对同一不可变 previous 再次转换。Root 已批准限定的软件分配优化源码采用；正式源码、已编软件类图、Runtime 装载和游戏保存分别记账。本记录切点软件基线仍为 current351，后继 352 必须另有正式 SHA、manifest 和 Root 软件采用回执；没有 Runtime、Quarkus 热载、整体游玩提速或新增 SAVE 信用。

## 源码、生命周期与实际来源

受管 NativeGameTransport.java 基底 152346B／`0f69cceb214f4f959cc5f50fdadca73bf6baf431dec6b7914454fc303b50b1f7` 与 source307 整叶逐字相同，候选 152664B／`242e6379fbe84e6811b69040678a9ef4b74cea794c76a3bcb828e089fa820d67` 仅五个物理行变化、三段 diff，原 1952 行数保持。新增两个 private 字段 ownerCanonicalObj／derivedJsonNode，单槽保存既有 Obj 身份与本次新建的表示，不是 Guard、权限、接收结果或跨对象值缓存。完整叶逆向证明恢复原件；整个历史 C0 的编译源码谱系仍 UNPROVEN，已持的是精确 source307／formal 和定点实际方法域，不能扩大为整个 C0 来源已知。

当前 semantic 的 toNode 始终先在原位置执行；previous 非 null 且 owner 身份相同、node 非 null 才复用 previous 表示，否则在原第二次转换位置走原 toNode。Fingerprint 每次仍原样调用，uint64、原包、token、map、错误与所有检查顺序不改。槽只在原 semantic 成功赋值之后更新，close 原 finally 开头清两个新字段，原 endpoint.close／disconnection 和旧字段顺序保持。Guard、parser、hash、oldencode、Fingerprint 等原算法体逐字不变。

这依赖同一固定 DriverJson、默认 factory、Fingerprint 与软件定义；没有自动源码 epoch 失效能力，未来改变定义需要明确清槽或新实例。**两个新增字段是结构变化，不能据本次验收称 body-only Quarkus 热替换可行。** JsonNode 容器私有且不外泄，等价仅限标准不可变 canonical 生产域；不授恶意可变数值、Unsafe、定义热变更或 OOME 等价。Node 会跨下一次 decode 存活，分配下降不能直接推峰值／GC／内存安全收益。

## 必要编译与真实接收验证

第一次生产编译 1TU26 实际 exit0，但默认离线 javac 缺旧 MethodParameters／调试属性，保为 typing 事实并未采用。独立 prod02 对同一源码加 `-g -parameters` 后再首编 1TU26，25 个 nested 逐 SHA 与旧 C0 全同；26 类共 283 个方法的 MethodParameters presence／name／flags 保持（136 个有该属性），旧 API、字段与 Nests 闭合，仅新增两个字段。不能将第一次绿色编译的元数据缺口擦除，也不把两次生产编译说成只一次。

测量源 Test02 31411B／`af34a107ff53021a66ebe10bbd58aba6e44a9a3667631d4c7803a7787bc3fa41`，必要新 1TU6、sole JUnit 1P／0F／0E／0skip，Jupiter 整 run 为 4.984s，指定 testcase 为 **4.961s**。原先消息与 owner 初件把 4.984 标为 case 的标签另件勘误，实际 XML／raw 均不变。测试精确字节放 `tools/performance/retained-semantic171/RetainedSemantic171Test.java`，依赖显式外置根及 current351 父 CP，不进入默认 Maven 自动测试；没有改 pom、隐式 skip 或生产接口。

两侧各 own 完整 NativeGameTransport26，父 Endpoint／Api／DriverJson／Assembler／DTO 共享。Test 同 runtimepackage 使用现有包内软件 Endpoint／Api，child 用 public ctor；不是全 public 入口，也没有反射私有缓存、计数器或 issuer。byte[] cursor 一次最多一包，实际 Endpoint guard／Peek／ReadFile／严格 decode 保持，没有真实 Win32 pipe 创建、Game、命令写入或模型 HTTP。

原件来自实际 P164 receipt 的 native_evidence：完整 framed STATE **3400700B**／`4084dcb52ed1ecafadf7fbe6fd11998ff2ed2c06fd22ac077025e519044e4e5d`，native:2／revision2／date53144328，含 opaque_unconsumed_extension **3400000 字符**。性能输入直接逐包重放原字节，不 parse/reencode 冒精确原件，不据该人工 opaque 规模外推自然频率或扩大 N。

固定首 8ABBA32、每侧16次，两侧各持久一个 transport；setup 仅 HELLO，没有 STATE／observe 目标暖机。每次调用真实 `observe(Instant)`，不用可复用 retained 的 duration 重载或 currentSnapshot。32 行均实际 ReadFile53次、3400700B、guard60次；全部 target／post 通过，新的 actual frame 身份、完整 raw Obj／原包／state SHA、canonical SHA、公有 revision2、接收事件 order2…17、token 绑定与原件哈希均核同。相同 DATA 不可当成同次接收，旧 token 对下一 frame 拒绝、对原相同 frame 接受。绝对系统 UTC 与随机 custodyUUID 仅侧内检查，不伪造两侧字面相等。

功能另有20次 observe，共 **52次**（A26／B26）、6次 HELLO-only setup、10功能行、6次公开 close：first／equal／change／A-B-A／合法 wire 的 date 拒收／后继恢复／nativeRevision 回归／secondHELLO／关闭后拒收与无额外读取通过，完整异常类和消息等价。私有 owner-miss／node-null、槽清零本身、uint64 overflow、fixed-clock 回归只保 Source／Code 证明，不冒实际命中；实际 nativeRevision 回归满足公路回归验证。

## 全部首32结果与反向

| 指标／每调用 | A | B | 限定观察 |
| --- | ---: | ---: | --- |
| 分配均值 | 149427024.5 B | 138506401 B | −7.3083% |
| 分配中位 | 149903408 B | 138506080 B | −11397328 B／−7.6031%；8配对全降 |
| observe wall 均值 | 50.6902 ms | 39.51035 ms | −22.0552%，冷首影响 |
| observe wall 中位 | 38.67785 ms | 36.43135 ms | −5.8082%；5好3差 |
| 线程 CPU 中位 | 31.25 ms | 31.25 ms | 15.625ms量化，不授比例因果 |
| 含准备／后验的 row 中位 | 75.4979 ms | 66.4035 ms | −12.0459%，不替 target |

三组反向必须保留：cycle1／2／5 的两调用 wall 合计 B−A 为 **＋2.9261／＋15.7600／＋8.4181ms**。首 A wall187.9957ms、B55.1043ms及全部 outlier 均保，不将均值下降全归机制。首 A 分配142304024B反而低于后继约149.9M，不能套用“冷首额外分配”解释。CPU 本次两侧没有零值，累计 A531.25／B468.75ms仅描述，配对5低／1平／2高；CPU收益比率 UNKNOWN，不能以粗量化授稳健 CPU 提速。

Root 根据全部功能、8/8分配下降及当前完整 observe 时间分布未见明显 material 倒退，批准有限源码采用；不是任意均值为绿即可采用，也不承诺每一组输入获益。没有加暖机、重采样、删首行、放大 N、第二次测量、JFR 或 fullcase 刷样本。A-first 固定顺序、同 JVM／父 codec／JIT 共享及 post 转换预热偏差全部保留。

## 完整费用、heap 与保留

setup 至首目标 1.9693913s；32目标 wall 合计1.4432088s、enclosing合计2.5784165s、packet准备合计0.0085428s，功能0.0466553s。逐行原 packet clone／offer 与 raw／typed／canonical／SHA／身份／heap 后验均在 target 外、enclosing 和全 case 内；before-report4.6095068s不含报告序列化、写出和JUnit尾部，不能把差值全叫纯序列化。

共享 heap 在32前32,334,480B、后221,256,680B；GC总次数2→75、总时长25→261ms，committed389,283,840B。它包含双侧持久实例、完整共享 raw oracle／原包及 post 转换，不能按侧归因缓存峰值或把73次GC归给某一侧；没有强制 GC，post采样不是peak／OOME证明。Native metadata 3,189,303B＜4MiB，实际 JNA273408B计入；外置原packet不复制进metadata。

Root最早具名只读切点 **02:24:13.729861Z→末CLOSE03:46:34.456085Z＝4940.726224s**；这是已知切点，不是研究真正始点，与P170并行不能相加。Native较窄切点02:39:39.041117Z→末CLOSE4015.414968s／qual03:49:27.259820Z＝4188.218703s；Root同锚到该qual5113.529959s，更早UNKNOWN非0。四VM actor合30.6589439s／operator合42.2004731s仅资源子窗，不替全部研究、源码、等待或结算费用。

保留 prod01 元数据缺口、prod02 首发 controllerQ caption机械串替换的0VM准入纠正、准备期路径误读、Test01关闭消息疑虑经真实terminal前置撤回，以及Test02只修三scope cleanup对primary异常的suppression。Test01从未编／跑，首32没有重试。所有实际输出、旧CFG／SourceReady、原source、delta、XML、报告与费用原件保；外部报告 CREATE_NEW≤256KiB、NEVER保留，失败会保partial与首错。

## 具名原件

- `N/p171-retained-semantic-test01/reports-component/p171-retained-semantic-public-observe-fixed32.json`：65802B／`9442555ee986097523dc964fefc6c15b84b340040de7eec5c3cb974d20f2ac98`。
- 同目录 `QUALIFIED-P171-FIRST32-PUBLICOBSERVE-ALLFUNCTIONAL-COST01.json`：62421B／`24e8f8b87f18811bbc1e2da7502934bdc31c08db7f896aee065e7b65ed9d63a8`，Native131独立refs；Root153次引用／131独立原件实核。
- `N/p171-retained-semantic-prod02/QUALIFIED-P171-PROFILE02-26-METADATA-CLOSED01.json`：72571B／`f9db04378e42893348bb0bfd2686f7fb2b8921261a57b5031714956ebc976f13`。
- `R/P171-ACTUAL-FIRST32-52ORIGINS-FUNCTIONAL-AND-LIMITED-SOURCE-ACCEPTANCE01.json`：14267B／`20f13b783b1517d310492e7a777da223dc22f13d74107190b2ce66a044db9f97`。
- `J/construction-retained-semantic171/OWNER-ACTUAL-FIRST32-SOFTWARE-REVIEW01.json`：10286B／`6b1d51c3a405031e33924014268b8ee12a83f69ef9e6d8e66c7401dd33b255e7`；4.984整run／4.961case标签澄清另件，原数值未改。

N、R、J分别为本机Native、Root、Java证据根；只作具名离线来源，不发放 Runtime 或 P100 同链准入。零新增确认保存日，不报有限秒／日，也不把旧世界累计保存日混入分母。P165／166／167／170与token分支旧PARK继续保持。
