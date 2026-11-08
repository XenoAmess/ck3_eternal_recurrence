# P147：scoped Reader 同次复用私有 packet，保留状态路径代价

Reader 的公开 scoped assembly 在原首次 nativeFrame 位置调用已有 private captured factory，持有私有 framed 副本和首次解析 envelope。原 replayFacts／实际Driver严格解码顺序保持；随后 Assembler 新包内入口复用这个闭合 carrier。完整 projection 仍在 try 外，只有原 identity尾在原 catch 内：早期 projection错误直接抛，晚期身份缺口仍为 Incomplete。Reader finally及原state helper的幂等clear覆盖成功／失败，不暴露DOM、raw+typedpair、回调或新trusted flag，不跨调用缓存。

两叶逆向逐字恢复此前正式源码；旧capture／fallback／公共API其余body、Complete的独立self-replay、P143counter／P144guard、所有fresh hash／parser／oldencode／Guard算法保留。新增一个包内方法、0新生产类型；此结构变化不授Runtime热载。

代价没有省略：增加已有holder和整个framed数组克隆，首次packet树活到Driver解码之后。私有state helper恒解析state，替代旧public compact前缀／精确编码命中快路。减少packet重复parse不等同所有输入净CPU或heap改善，必须看compact与pretty各自结果。模型未参与，0 HTTP。

## 实际功能和类型边界

生产2TU／10类首次编译0，Driver3未编；新独立Test1TU／5类通过，功能1P与唯一固定64组件1P跨2JUnit闭合，无旧Test／helper增编或默认Replay／Applied／Main／JFR运行。

新功能实际调用公有scoped Reader，分别以null与真正parent finalLoader严格decoder，旧A绝不经parentLoader.load冒充旧Reader。验证decimal词法与只读原件；public producer构造的paused冲突保持直接原IllegalArgumentException，playedactor74／Driver73保原Incomplete原因；badDriver fresh验证失败类别／消息一致。B端真正publicLoader读取manifest→native→driver，driver回调变更借用native数组仍不影响原先私有copy；P4公有producer、OriginalProjection present及原Complete self-replay实际通过。清carrier由完整源码finally证明，没有私有mint、反射观察hook或新接口。

A的Reader4→Assembler6→Driver3来自三个原root，同child有效13类；后一个物理9类root中的旧Asm被前者遮蔽。B为新Reader4＋Asm6及原Driver3 parent。反射签名使用各自Assembler类，结果通过各自公开getter比identity／source／session／evidence／time／完整semantic bytes和order／binding值；不跨loader recordequals、parentcast或把重建ObservedFrame当同一对象。

## 预锁两输入、全部64调用

compact先、pretty后，每输入8轮ABBA＝32次（16A／16B），总64，0额外target warmup。所有冷样本和较慢尾部均保留，不混未知自然hitrate。时间单位ms、分配单位B：

| 输入／侧／指标 | n | 总计 | 均值 | 中位数 | min | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| compact/A wall ms | 16 | 842.0539 | 52.62836875 | 44.08835 | 39.1269 | 157.6066 |
| compact/A CPU ms | 16 | 656.25 | 41.015625 | 31.25 | 15.625 | 156.25 |
| compact/A allocation B | 16 | 1523792728 | 95237045.5 | 95031816 | 95031248 | 98308744 |
| compact/B wall ms | 16 | 729.7359 | 45.60849375 | 41.1047 | 33.4478 | 101.3228 |
| compact/B CPU ms | 16 | 453.125 | 28.3203125 | 31.25 | 15.625 | 46.875 |
| compact/B allocation B | 16 | 1520697160 | 95043572.5 | 95029280 | 95027496 | 95252520 |
| pretty/A wall ms | 16 | 831.1066 | 51.9441625 | 48.91015 | 40.0684 | 98.9824 |
| pretty/A CPU ms | 16 | 531.25 | 33.203125 | 31.25 | 15.625 | 62.5 |
| pretty/A allocation B | 16 | 1899710880 | 118731930 | 118731512 | 118731504 | 118732736 |
| pretty/B wall ms | 16 | 734.8323 | 45.92701875 | 39.49795 | 30.3726 | 129.7546 |
| pretty/B CPU ms | 16 | 390.625 | 24.4140625 | 31.25 | 0 | 46.875 |
| pretty/B allocation B | 16 | 1520467328 | 95029208 | 95029164 | 95028200 | 95031296 |

每轮两次A／B求和的预声明配对如下，保留全部八轮；不作独立性或显著性推断：

| 输入／B−A指标 | 负／零／正 | 八轮合计 | 均值 | 中位数 | min | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| compact wall ms | 6/0/2 | -112.318 | -14.03975 | -13.6063 | -88.9368 | 59.8315 |
| compact CPU ms | 5/2/1 | -203.125 | -25.390625 | -15.625 | -140.625 | 15.625 |
| compact allocation B | 7/0/1 | -3095568 | -386946 | -7536 | -3057776 | 6360 |
| pretty wall ms | 6/0/2 | -96.2743 | -12.0342875 | -24.9962 | -58.4517 | 70.0841 |
| pretty CPU ms | 6/1/1 | -140.625 | -17.578125 | -15.625 | -46.875 | 15.625 |
| pretty allocation B | 8/0/0 | -379243552 | -47405444 | -47405904 | -47406608 | -47403560 |

pretty分配均值118731930→95029208B，少23702722B，八轮配对全负。compact均值95237045.5→95043572.5B仅少193473B，配对中位数−7536B／7负1正，且首A冷分配驱动均值，不授相同大额机制。compact近持平不能包装为两输入通用20%改善；累计分配不是peak／live heap。

两输入wall配对均6负2正，累计compact842.0539→729.7359ms、pretty831.1066→734.8323ms，为有限组件观察。CPU配对compact5负2零1正、pretty6负1零1正，四组CPU中位数皆31.25ms；pretty B有两个0量化值，不称零成本。pretty B最慢129.7546ms高于A最慢98.9824ms，尾部回退不隐藏。Root采用软件改动，以pretty分配稳定下降及完整语义闭合为依据，不授稳健因果CPU／latency、worker或10秒目标。

## 偏差、完整窗口与资格

parent B与fixture／postwriter共享factory／代码，A独立child；同一parent严格Driver decoder、共享JDK／Jackson／normalizer及不同JIT／GC历史保留。pretty继承前32次compact调用的预热，输入次序预先锁定；不得取较好输入推广自然频率。目标bracket是公开scoped Reader；公开Loader三次DATA回调另在功能验，不冒物理IO／wholeverify速度。

旧13／parent初始化311.457／1.9759ms，来源／反射准备16.4602ms，setup2.241992秒；目标wall总3.1377287秒、含observer/post的row累计3.7700567秒，summary/report前方法6.0226525秒。差额不独归serialization／GC。

生产编译actor／outer7.0130334／8.2289245秒，Test6.3540384／7.7927099秒；功能5.7200111／7.1046893秒（case2.863），组件9.1372724／10.6247633秒（case6.483）。功能／组件child stderr303／302B保留，outer0另记。actor含父记录／验证，不称纯child wall；phase actor合28.2243553秒、outer合33.751087秒，不替完整窗。

首生产operator→末component operator1241.072072秒；生产BEGIN `14:55:31.802204Z`→末CLOSE `15:16:11.915994Z`为1240.11379秒；更早CandidateReady1486.675964秒、TestReady428.605465秒分别记录，准备／审阅／等待全部计入。不追加样本或重跑挑绿，三root聚合元数据1645625B＜4MiB。P141历史整体PARTIAL预算失败仍只作线索，P146公开projection实验不能替代本次scoped Reader路径。

本单0 saved，软件源码／编测／Git与当前软件class图、Runtime实际装载／行为／SAVE分层；无head47／P100或实机速度准入。下一P148先读当前profile合同，不把本单发表当全局完成。

- [Root采用与有限输入观察](D:/ck3-state/resume91-root/post-vacation-20261107/P147-CLOSED-PACKET-SOFTWARE-ADOPTION-AND-LIMITED-INPUT-TIMING01.json)：4935B／`e3524a32a975dfb95350d27e7123327d5ab47d898ba13c52ceafc10c5fded018`。
- [Native完整资格](D:/ck3-state/resume91-native-integration/p147-reader-packet-test01/QUALIFIED-P147-PUBLIC-SCOPED-READER-FUNCTIONAL-AND-FIXED64-SOFTWARE01.json)：68752B／`96196f8846c10e4c5929565a65a7a038149271b7c263ae73d6281985d4f91ab7`；[全部64行](D:/ck3-state/resume91-native-integration/p147-reader-packet-test01/tmp-component/junit-4851232223778860176/p147-scoped-reader-fixed64.json)：155644B／`80ea0a955b3167289be31ba37ba31657c1891c8e166b2dd68987b732a01c0dcb`。
- [Owner全64独核](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-reader-packet147/P147-OWNER-ALL64-ACTUAL-REVIEW01.json)：21528B／`a5d8b1185b40b59e9c6e5c51d8e3810dbf37a93e995fb26ac6fbeebaa0677f13`；[正式同字节采用](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-reader-packet147/FORMAL-ADOPTED-AFTER-ACTUAL01.json)。
