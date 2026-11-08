# P142：同次 packet SHA／长度校验共用私有副本

`DriverObservationEvidenceReader.bindDecodedDriver` 原先为 SHA 取得一次 `ObservedFrame.originalPacket()` 防御副本，紧接着又只为 `.length` 克隆同一个不可变 packet。现在仅在原 SHA 参数求值位置把该副本存入局部变量，下一长度条件使用同一副本。读取没有提前，原 `&&` 短路、字段类型／错误消息、fresh SHA、framing、解析、回调、Guard 和公开 API 保持；无新增字段或类型。模型未参与，owner-original，0 HTTP。

线索来自 P141 实际 recorded-prefix chain12295；P141 后处理超出元数据预算，整体仍为 `PARTIAL_BUDGET_FAILURE`，不因本单成功改写。P142 使用独立有界原件，写前预算检查通过。

## 必要验证与完整 verify 组件

生产首次必要 Reader 1TU／4类通过；修改既有366 Test 1TU／4类通过。功能四方法与唯一完整 verify 组件共五个受影响既有方法，跨两个 JUnit JVM 全 P，newunique=0。保留366原回调变异／解析顺序、stage null／closed／不同 body、wide／distinct Driver 和 Replay v3／v4 oracle；新增早期失败、坏 SHA 字段类型与坏 bytes 右项的短路对照。不重编 Verifier／SDK／Main，不重复昂贵 Applied，不新录制 JFR。

组件 A 是已经采用的 cc/P139 六类，包括 NativeBodyStage，与其 Verifier 同 child loader；B 仅使用新 Reader4、复用同一 Verifier2。双方均对应 ArtifactReader Proxy 加同 parent SemanticVerifier interface，初始化／fixture／loader 单列 setup；不是 d56 旧五类，也不把 P139 stage 的收益混入本单。使用同一 v4 大原件、完整五次 DATA callback 和实际 verify，逐行核对读取 ref／SHA 顺序、完整 VerifiedSemantic、head 与输入 SHA。它是内存 DATA 回调组件，不是物理 IO、worker 或 Game 测量。

固定 A/B/B/A，无 target warmup；全部原值如下：

| 行 | wall ms | 当前线程 CPU ms | 当前线程累计分配 B |
| --- | ---: | ---: | ---: |
| A0 | 257.6360 | 171.875 | 560848400 |
| B0 | 170.6086 | 140.625 | 556938096 |
| B1 | 213.7405 | 156.250 | 556930112 |
| A1 | 183.6070 | 109.375 | 560318232 |

分配均值560583316→556934104B，少3649212B（0.65096693%），两 B 都低于最小 A。以末 A 为基准，两 B 分别少3380136／3388120B，符合移除一次大 packet clone 的机制；首 A 额外530168B、B0额外7984B，不能把全部均值差归因这一行。累计分配减少不等于 peak／live heap 降低。

wall 均值220.6215→192.17455ms（−12.894%）只是这四行描述，B1 比末 A 慢。CPU 均值140.625→148.4375ms（+5.5556%），15.625ms量化且每侧仅两个样本，不授 CPU 或稳健延迟改善。Root 决定仅采用软件 allocation 优化，不为更绿数字重跑。

## 完整成本与资格范围

setup2.0009124秒，包括旧侧／parent类初始化274.9302／0.8874ms；组件报告物化前2.8894127秒。测试编译 actor／outer为5.9222407／6.7248404秒；功能 JUnit为5.1252242／5.9747982秒，组件为5.2353633／6.0940422秒。actor含父记录／资格验证，不称完整 child wall；功能／组件 child stderr分别628／313B保留，不以 outer stderr0替代。另有生产编译 actor4.2381325／outer5.0430972秒。

首生产 BEGIN `12:55:27.287054Z` 到末组件 CLOSE `13:05:19.711443Z` 为592.424389秒；候选 Ready 到末 CLOSE 为787.042409秒，准备、审阅、编译、等待全部计入。全部进程实际0／accepted／closed、资源释放；无额外软件 JVM 挑样本。

源码／软件编测／发表与 Runtime 分层：本单0 saved，不授实际热载、head47／P100、实机速度、自然调用频率或10秒／新增确认保存日目标。下一 P143 仅另单元 D 候选，研究保留完整 writer 遍历而取消仅用于预算检查的大数组物化，不作为本单发表前置。

## 原件

- [Root 采用决定](D:/ck3-state/resume91-root/post-vacation-20261107/P142-PACKET-LENGTH-PRIVATE-CLONE-ALLOCATION-SOFTWARE-ADOPTION01.json)：5776B／`5f5d478be9ee311403c48f1c7c68942bbf0b186def52721a80ab83db299ed102`。
- [Native 完整资格](D:/ck3-state/resume91-native-integration/p142-native-packet-length-test01/QUALIFIED-P142-FIVE-METHOD-SOFTWARE-AND-FULL-VERIFY-COMPONENT01.json)：97161B／`4dcc9f4987ef0734deada1d1877a57fa950c77aad806913c8a0ed8a9d035b3c7`；[四行原报告](D:/ck3-state/resume91-native-integration/p142-native-packet-length-test01/tmp-component/junit-11050898452802733925/p142-semantic-packet-length-component.json)：8130B／`3a9c5cf11e2e812ffc6ae42c9f9dfa1810b01eed043cfbdefdb26b52aa2f74e7`。
- [Owner 原件复核](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-native-packet-length142/P142-OWNER-ACTUAL-REVIEW01.json)与[同字节正式采用回执](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-native-packet-length142/FORMAL-ADOPTED-AFTER-ACTUAL01.json)。历史 cc Test 已另存 immutable 副本，原 Ready 的正式路径只表示捕获时来源，不声称发表后仍是不变基底。
