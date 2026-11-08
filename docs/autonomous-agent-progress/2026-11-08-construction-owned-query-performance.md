# P120：仅在私有查询路径省去重复快照

本次保留公有 Node 工厂的完整快照合同，只让 full ObservedRequest 内部已经私有的 query 树直接生成封闭 DATA token。必要 3SDK TU／18class、新三个方法及受影响旧 full139 方法均通过。同 Main03、同物理 DATA／warm CAS 的固定 ABBA 中，whole 墙钟均值 596.6199625→534.74935ms（-10.37%）、中位 573.6067→536.43795ms（-6.48%），主线程累计分配均值 762065993→711314495B（-6.66%）。这是本次有限 DATA cohort 的观察，不与前轮百分比相加，不替代实际 Policy／Native／持续 worker 或保存日验收；P117／118原有墙钟未改善的结论保留。

## 私有所有权与最窄源码

P119 的同一固定 query 有 33993 个 object、14716 个 array、207949 个 key；结构计数说明公有 snapshot 会重建多少容器，不是分配大小或方法耗时证据。现有 full factory 先检查原 64MiB，再 clone caller bytes、FullJsonTree.parse 私有原文；queryNode 只在该调用栈内，未外传。parser 每个容器新建，前段 selection 只返回 enum／String，后段 cash／finance 由独立字节解码。角色 projector 对原树只读，目的角色／diag／hello 均新建。原树无外部可变 alias，后续 DATA 对象也不持 DOM。

三处既有 SDK 源仅 26add／2del：

- Codec 新 nested package-private static final OwnedQueryProjection，private constructor 只在该唯一 full factory 的私有 query callsite 调用；先原 FullJsonTree.encode(query,64MiB)，再同一 private projector 的 262144B SDK 投影，private final raw／SDK 数组、getter clone、无 DOM。没有 package／public 任意 Node 到 token 工厂。
- QueryCodec 新 role-only DATA facade 只返回 SDK byte[]，委托唯一既有 private projector；明确 caller 在同步调用期间保持树稳定，不验证完整原文、不创建公有 carrier、不授 source／Native 权限。
- NativeQuote 新包内入口只接受该不可外造 token，消费 clone getters 后进入原 private(raw,sdk)；不开放任意 raw＋SDK／typed pair。

公有 deriveFullMaterialQuery、其标准节点 snapshot／carrier／13拒绝域、旧 public byte 入口、NativeQuote 私有 pair 及全部融资代码体保持。反向撤销四个声明的 edit 可逐 byte 恢复原三源；没有复制字段白名单，也没有改 contracts／FullJsonTree／Guard／应用层物理读取。query 派生仍 64MiB，SDK仍262144B，不能借融资的256MiB编码 lease。外部 mutable Node 仍走 P118公有强 snapshot；内部 token 本身只是 DATA 所有权，不是原件或 Runtime 许可。

真实模型使用六份完整当前源78927B，含 StrictJson 实际声明，强 owner 指导任务6977B；一次 POST 于02:31:59.962279Z开始，200／stop／DONE，12.7207579s、TTFT2.5647585s，19104prompt／1720output、cached=null。核心采用，非 literal 整包：模型一个 Codec outer 补丁 anchor 多四空格、原文零匹配，owner 仅 dedent 为唯一匹配，并澄清 facade 的稳定树／无原文权限注释。原答复保留，未为机械修正重 HTTP 或编无效 anchor 稿。

## 实际验证与预算域

Native 仅编必要三生产 TU，一次0／18class／5.8923103s，新增 Codec$OwnedQueryProjection 一类。新 Test 仅1TU一次0／4.182332s；两个普通方法在同JVM2P0F0E（actor4.1838954s／XMLsuite2.279s），actual fullouter 大case独立1P0F0E（actor6.5138347s／XMLsuite4.368s），新3unique跨两个JUnit JVM。原P118 full139仅该受影响方法另JVM1P、未重编其Test，不算newunique；不是同JVM4P。无其它旧绿重跑，本单Java编测和Native metadata gate均无RED。

旧139受影响方法保留原query／SDK参考的字节对照；新普通方法通过实际 full factory，对旧 public byte 参考的原query、exact finalizer／opaque高精度、selected和whole typed结果一致；caller raw／getter数组变异、两个 proof epoch 不同实例不串用。token／private pair 只查 API modifier、字段类型及实际输出，不反射 mint token、Guard 或 detached 许可。另把后置 cash_input 故意设错，先触发 consumed SDK262K 同类同消息异常，并定位到 OwnedQueryProjection 栈，保原顺序。

独立大case把 literal query 嵌进真实完整 outer 原wire：outer67108863B、query literal67098833B，实际 query 重编码67146833B。旧 standalone byte query 可selected，旧 public derived64拒绝，新 actual Observed full 路径也在 OwnedQueryProjection 原64MiB编码处拒绝；不是只测公有Node，也不是把旧byte域和derived域等同。测试256MiB encode仅量出膨胀大小，生产query预算没变，不要求巨型manifest或动作准入。该case CPU1／Xmx1024MiB／90s，owned OS峰 working set1062567936B／pagefile1153273856B，均不是heap实占，完整临时raw／clone成本另存，不混进主要性能cohort。

## 原Main、原DATA的固定ABBA

A为实际P118当前B17完整SDK族，B为新18；公有carrier双方都有，OwnedToken只在B声明first-origin。P117共同Lifecycle／Source／Policy、Main03原binary、6831978B input／Q2／source／绝对CAS／EXPECTED完全沿用，无Main重编、PREP或DATA deadline刷新。newTest不进入Main CP，没有P119 GC flags或诊断重跑。logical A0／B0／B1／A1对应raw B0／B0／B1／B1，raw不改写，真实variant由完整family hash／first-origin／ordered CP核定；cached=true仍是共同P114路线标记，不假称新token命中计数。

四独立JVM，各2warm＋4measure，CPU1／Xmx384MiB／90s。全部8warm／16measure、所有24call及慢样本保留，无forceGC／过滤或重跑挑绿。每call marker等于原EXPECTED、warm CAS／cache均true，whole等于11个disjoint phase的wall／CPU／main-thread allocation之和；不支持的计数原样null。每进程新allocation card单列，原head／anchor／lock／store／payload／commit身份保持，不声称全文件系统逐byte相同。

| 指标 | P118 B17基线A | P120 B18 |
| --- | ---: | ---: |
| whole墙钟均值 | 596.6199625ms | 534.74935ms |
| whole墙钟中位数 | 573.6067ms | 536.43795ms |
| whole墙钟样本标准差 | 76.8383514ms | 57.8273945ms |
| whole墙钟最小／最大 | 528.4788／749.735ms | 472.2734／606.9453ms |
| whole当前线程CPU均值 | 267.578125ms | 240.234375ms |
| whole allocated均值 | 762065993B | 711314495B |
| whole allocated中位数 | 762065896B | 711314416B |
| actor均值 | 10.76688055s | 10.4887232s |
| 序列化前main均值 | 8.29276565s | 7.9671396s |
| setup均值 | 2.09244445s | 2.03089755s |

construct／resolve／Q2分配均值分别131852467→114953491、295047878→278142100、131893616→114994640B，各约减少16.90MB；它们墙钟均值97.20405→94.59835、206.63655→192.3909625、102.9785→65.6563625ms。未改preserve反向70.06805→76.5136375ms，args12.007375→13.015375ms；未改intent95.3914375→81.1021625ms的波动也保留，不把所有phase差异都当作该局部方法因果。P119已说明冷单CPU下编译线程与GC成本存在，本次不改JIT／GC参数或warmup，不据这些数据授持续worker稳态收益。

四actor合42.511207499891秒；ABBA从02:42:07.520148Z至A1close02:42:54.292778Z，46.77263s含phase间隔。首生产BEGIN02:36:24.953023Z至末close为389.339755s，包含必要编测、准备和等待；此前模型12.7207579s及所有权研究／源准备另存，不把389秒冒称从最初研究开始，后到文档也不混入抽样分母。所有raw／setup／main／process／outer／OS峰保留，未引入同JVM wrapper的额外cohort。

业务根 D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-owned-query120。
Native最终QUALIFIED-P120-OWNED-QUERY-AND-CONSUMER-DATA01.json49301B／f85c9bcb30d50019530c6c198700e44777e342b4725e03e252bf9a0b9ba6eb1f；
全样本412626B／cf12a6b37f8cc22c27ba0e9cba10a683e93bf1d3f7eec9f87e5b9066a35f1969；
identity6593B／bd9ef1fd84220441e458ff4ee0bd951af12fda585fb0ed7c0d62eb72ff789bce。
Root独核24raw／phase sums／close的proof112172B／804b834813c86fdb6eba7c0304e5eaec25c776f587ceda49336ee8f0976c1a49；Java独立只读raw复核17797B／e60a039e5736656175389cb4a37350a8108bfb1ec2f33f0e64b0c0bce30fa72b另存，原件不改。

本次限域保留，18类软件通过不授新类Runtime可载；没有部署、Native动作或新增确认保存日。后继先D-only准备未改Main03的固定三pass复用wrapper合同，若另获有限执行将另记cohort及全部18call／冷启动／新cards／失败停止，不替换本primary ABBA或选择后pass冒提速。
