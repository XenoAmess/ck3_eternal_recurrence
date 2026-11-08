# P114：同一完整报价对象复用精确 finalized bytes

本地2026-11-08；源码与新cache测试完成于UTC11月7日，完整DATA测量于UTC11月8日。P113成功的软件链作为基线；当前持续目标仍active，无Runtime装载、实际游戏日或10秒／新增保存日通过信用。

full NativeQuote构造时已经通过既有finalizeObservation(sdkBytes)生成选中结果，Policy随后从同一对象的完整raw再次投影、解码和finalize。现在仅full factory的SELECTED且满足既有Economy输出上限的对象保留首次精确byte[]，getter返回防御clone；旧public small构造器和未选中对象保持空，Policy149用同一对象的getter或lazy原fallback。其余消费者，包括Loaded INTENT、MATERIAL及Q2后继计算，未接缓存。未使用selected().original()的经济codec重编码结果替代原bytes，未新增静态／跨调用／Session缓存。

不可变来源为full factory先clone、单raw确定性推导、private pair构造和original()防御clone；构造出的封闭typed图没有能写回owned raw的公开别名。新字段增加少量对象存活内存，收益必须计入所有新对象和完整消费者成本。source／guard、物理CAS发布及重读、长度／SHA／逐byte、fresh独立对象、旧codec／parser／cap／命令hash均保留。新增getter及字段尚无Runtime结构采用资格。

真实模型请求于23:36:36.891818Z POST、23:36:52.304673Z stop，total15411.7106ms、有效内容TTFT3587.8828ms、prompt25752／output2045，cached未报告。候选错误地让旧small构造器也缓存，超出既定scope；仅核心思路部分采用，owner保留先前独立审阅D稿的full-only实现，不能称原样模型采用。两个生产TU首次exit0、16class，5.1504935秒，23:41:09.092925Z资源关闭。

新增CacheTest仅1TU首次编译0、四新方法同JVM4P，child5.0055077秒、outer5.7498147秒，23:49:23.389008Z关闭。实际existing finalizer对高精度opaque world／成员顺序的输出逐byte一致，caller数组／getter数组修改不能污染缓存，两个实例隔离，oldsmall及unselected保持空／原fallback。部分1.00／-0.0／1e+0由既有finalizer规范化，oracle是该原输出；完整original仍保输入词法。未借此重跑旧schema套件或授Policy.evaluate／CAS行为。

测量执行的是真实factory、compose、fixed finalizer或同对象cache、同writer mutable Source.preserve／完整CAS读回、resolveCommand／header与frame核对、全新固定DATA Q2对象与sameQuote、包内Lifecycle.intent及canonical body。args／新DATA command的组装明确是适配器，未运行完整Policy.evaluate／revalidate、Native fresh READ、完整物理SEM准入或owning publication。prototype原命令只作为过期DATA描述符，字节不改、不执行、不刷新原deadline；新DATA actionId由新args／CAS ref自然生成。

数据从Applied15成功软件原件6828384B派生：仅把两个未消费3.4MB字符串换成已qualified Driver1475前139行，其余成员保留；不是原完整FullSnapshot或实机授权。Q1为6831978B，SHA256 fe413956e14af2487bbec3b900e7ef6f08e653fc405ad5b71466eaa9e2cb9cdd；固定Q2只改请求nonce／单调probe，SHA256 a5a09c41abe1a73a358e986f241774f4cb3b9a19d85e2b70f7678a71237661be。small控制只移除两个大字符串，28318B。source、input、CAS ref、args、command／actionId、result及body的全部标量／hash markers逐次匹配成功PREP。

一次A-PREP在新独立SOFTWARE目录建立mutable writer／store和durable原件；四JVM重开同一绝对Layout、source和CAS，不把A首次创建与B热读混比。每个进程的software allocation card不同，在计时外另记；不称整个文件系统字节相同。每次实际preserve即使命中已有CAS仍走requireWrite和publication／全bytes核验，每次resolve仍物理load，未用readOnly或缓存值替代。首次publish的1.6968599秒／1,330,318,352B分配仅是PREP观测，不计入热cohort提速。

固定顺序A0／B0／B1／A1，各2warm＋4measure，同CPU1／384MiB／90秒，8warm及16measure全部保留，未forceGC或剔除慢样本。实际A来自P113成功两family16class，B来自本次新两TU；同一个Main class按实际API存在选择cache调用，反射与clone成本算入B。large每call A未用cache／B实际用了cache，CAS事先存在，markers同PREP。whole墙钟等于全部不重叠phase之和，包含writer获取和释放。

| 指标 | A | B |
| --- | ---: | ---: |
| whole墙钟中位数 | 951.43385ms | 862.08805ms |
| whole墙钟均值 | 947.99135ms | 907.3915375ms |
| whole主线程CPU中位数 | 406.25ms | 390.625ms |
| whole主线程allocated中位数 | 1,284,099,924B | 1,216,949,556B |
| 提取＋metadata source阶段中位墙钟 | 35.51285ms | 0.40635ms |
| 同提取阶段allocated中位数 | 67,173,528B | 23,128B |

本样本观察到whole中位墙钟减9.39%、均值减4.28%、主线程分配减5.23%；未把提取阶段约99%的缩减外推整个软件链。未改Q2 phase的B中位146.2695ms大于A的114.88235ms，原样保留，不把全部wall变化归因缓存。actor两进程均值A12.21972205秒／B11.86151175秒，约减2.93%；完整main、setup、process／outer与OS峰值另列。主线程分配不是全JVM分配，Windows CPU计时粒度也不作额外精度推断；112秒公开方法与实际游戏日不在这个分母。

准备时Main02唯一实错是small原插入序bytes对比经过ActionCodec canonical args的旧inline表示。旧入口本来用OpportunityJson.encode(supplied)后旧构造器，Main03对small按该准确合同取expected；large全文仍原first.raw==loaded.raw逐byte。旧data01目录、PREP child1／5.9625245秒及部分trace漏报原件保留，未开始ABBA；Main03用新data02根，两个PREP trace放finally，后继首次成功后才执行固定四进程。仅必要changed Main TU，未重编生产或重跑4P。所有准备、失败及最终运行耗时分别保留。

原始证据在D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-immutable-result114和D:/ck3-state/resume91-native-integration/p114-exact-result-prod01、p114-cache-data-test01、p114-consumer-data01／02。成功raw为p114-consumer-data02/benchmark-data/{A0,B0,B1,A1}.json；Root独立审阅P114-ABBA-ACTUAL-DATA-REVIEW01.json记录24call、route、phase总和与实际回执。shared-cas／DATA.json／EXPECTED.json及allocation card、前后身份索引随Native原件保留，无重复测量填数字。

下一实测大phase是B preserve中位285.83275ms／395,396,252B，其次resolve205.6186ms／338,381,868B。P115已准备真实模型候选，只针对large preserve丢弃的重复full factory，保留small重验及所有物理CAS／header／Guard；待独立SourceReady与有意义数据校验后继续同边界测量。本次正常发表不结束持续性能工作。

完整墙钟另记：四进程ABBA从BEGIN 00:10:18.254808Z到A1关闭00:13:28.982641Z共190.727833秒，包含间隔与等待；四actor合计48.16246760007925秒。data02成功PREP actor8.6686718秒（main-before-output6.2205335秒）、data01失败PREP5.9625245秒及两次必要Main编译、源码准备和审阅均分账保留，不从上述窗口剔除来宣称端到端达标。
