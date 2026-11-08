# 同次完整 semantic verify 复用稳定 Native body（P139）

Root 采用本次改动为软件 allocation 优化，不授 CPU、延迟、峰值／存活堆、Runtime 或10秒目标通过。真实完整 verify 组件中两次 B 分配都低于最小 A；wall均值反向、B1慢于两次 A 的原值全部保留。Owner-original，模型 NONE、0 HTTP。

原 `NativeSemanticEvidenceVerifier.verify` 先读 semantic、Native packet、stamp、Driver，再解析 semantic／stamp，随后首次解析 Native body。canonical 分支的晚期 Reader 在 manifest 回调后又复制并解析同一 packet body。原件由回调借用，后续回调可能改数组，不能直接复用早期 Obj，也不能只在复制 body 后比较借用数组：A→B（复制）→A 会错误复用 A 而旧 parser 消费 B。

两叶改动把原首次 LE32 require→`Arrays.copyOfRange`→原 `DriverJson.object` 机械搬入 byte-only producer，调用仍在原首次解析位置；不提前到 Native 读取点，不加 RawJson／UTF8／schema或额外预算限制。新 `NativeBodyStage` 的 private ctor 只由该 producer 用同一份私有 body 和其解析产物构造，public只给完整 immutable Obj及close，无 raw getter、任意 raw+Obj 注入、DOM、callback、Session、authority或跨调用cache。

晚期 Reader 仍先原 manifest／framing／fresh SHA，再做原 bodycopy；只有两份稳定私有 body 逐字相同才取已有 Obj，否则执行原 parser。两边原 LE长度规则保留，等长 body与合法 LE长度也确定完整 framed bytes相同；这只证明 DATA解析可复用，不替代原件资格。所有 envelope／stateToken／state SHA／RawJson／frame／Driver／head和最终输出检查保持，旧公开入口null候选行为、`NativePacketInput`／`NativeFrameInput`及其原路径整块不改。parser/hash/encoder/Guard算法不改。

stage 同锁访问和幂等不抛出close，只丢 body／Obj引用，不清零数组；canonical 晚期 Reader消费成功或失败后立即close，外层finally覆盖此前检查／回调失败，非canonical在原state检查后close。返回的immutable Obj不因close破坏。两个原 body副本均保留，没有新增整份clone；代价是一个小stage对象、O(n)memcmp、同步和跨回调延长body／Obj存活，不能将累计分配降低解释为live／peak heap降低。

候选 B 两 TU首次编译0／6类（Reader4＋Verifier2，新stage1）；另在隔离输出首次编译精确 d56 旧源码 A 两 TU／5类。当前旧C build307 Verifier的编译源码谱系仍 UNPROVEN，A只是 source-qualified d56 Reader3／Verifier2，不是当前C二进制等同或完整历史CP。三份正式源码均在软件取舍后才按实测相同字节采用，没有为发表再编译。

必要修改旧366测试一 TU／4类首次编译0，原Replay缓存和实际compiled15完整10类复用。六个不同方法、三个JUnit JVM全部通过，计1新组件方法＋5既有affected；无支持@Test：

- 功能四方法：扩展原366两项，保v3/v4、wide、distinct Driver／原读取计数／marker IOException／head drift／Driver借数组变异原断言；补stage精度／负零／exponent／Unicode／顺序、caller隔离、null／closed／不同body和同值异wire回退、资源清理；stamp／Driver回调改Native证明捕获未前移，manifest回调改Native证明fresh hash仍先行，并对照七组多故障先后。另复用实际P4缺失/null/retained及v3重播两项。私有字段／predicate反射只读DATA，不mint构造器或许可；Verifier-local全路径释放由exact finally源证与公开stage close测试共同支持，不伪称运行时取出了私有local。
- 真正归档 Applied15 一项：case109.723／suite109.754秒；软件210/240秒，原业务120秒不改、不刷新。
- 唯一完整verify测量一项：case3.566／suite3.607秒，四行全部completed／post checks成立。

组件只用单一 v4 large pretty-originals 场景，含3,400,000 ASCII opaque字符，Native packet3,400,439 B、semantic3,401,306 B；map-backed DATA回调每次仍真实clone原件，read-only Head不授writer权限。A精确旧五类同child，B当前parent；两边对应ArtifactReader都同样Proxy／反射构造，计入setup，目标均通过相同parent SemanticVerifier接口调用。保每次 semantic→Native→stamp→Driver→manifest五个ref／SHA顺序、完整VerifiedSemantic record／frame／time、head和输入SHA一致。它是完整生产verify调用组件，仍不是物理IO、whole worker、Game或当前C旧binaryAB。

| 行 | 入口 | wall ms | 当前线程 CPU ms | 当前线程 allocation B |
| --- | --- | ---: | ---: | ---: |
| 0 | A | 278.5574 | 156.250 | 584,534,632 |
| 1 | B | 208.8606 | 125.000 | 560,338,008 |
| 2 | B | 328.9980 | 171.875 | 560,330,024 |
| 3 | A | 246.3592 | 140.625 | 584,013,656 |

固定A/B/B/A、每入口两样本、0 target warmup，不删除firstA或慢B1。均值分配584,274,144→560,334,016 B（少23,940,128 B／−4.09741356%）；后A与两B分别差23,675,648／23,683,632 B，首A另有520,976 B冷差、B0另有7,984 B，均值不全归单一源码机制。wall均值262.4583→268.9293 ms（+2.46553452%），B1慢于两A；CPU均值同148.4375 ms，15.625ms粗粒度。两者均不授收益，累计分配也不等于进程CPU或峰值内存。

旧／parent Reader+Verifier显式Class.forName(load/link/dependency init)为265.3638／0.8348 ms，Proxy、fixture、loader均在setup；setup2.0802054秒，beforeReport3.2014358秒，全post／close／报告也留在完整JUnit／actor中。单一混合JVM的OS峰值不能分配到A/B，更不能当每variant live heap测量。没有额外目标预热或后继重跑。

| 必要阶段 | recording actor 秒 | outer 秒 |
| --- | ---: | ---: |
| 候选B生产2TU6类 | 5.4587593 | 6.2616733 |
| d56旧A生产2TU5类 | 4.9476487 | 5.7413859 |
| 修改的Test1TU4类 | 6.2001395 | 7.0999798 |
| 功能四方法 | 4.8265764 | 5.9135359 |
| public Applied15 | 111.8515617 | 112.7010114 |
| 完整verify组件 | 5.4835988 | 6.3413884 |

actor含父 recorder 校验，不是完整child wall；outer另一窗口也不与其子区间相加。首B生产BEGIN11:54:47.632748Z→末close12:17:49.737866Z为1382.105118秒，CandidateReady→末close1682.078093秒，含D测试准备／审核／两源码族和Test首次编译／全部验证／等待。首Ready前源码准备另存。两个实际生产typing、Testtyping与三JUnit均0、accepted、无timeout且close资源释放。

child stderr不是outer wrapper stderr：functional602 B、Applied7879 B、component301 B原件全保。前后为CleanupMode.NEVER保目录信息，Applied还含HISTORICAL_CAS_METRICS／ACTION提交与append阶段记录；outer stderr为0不能写成child stderr0。首TestDraft01有owner自查的局部变量重名和非真正同值wire向量，Draft02在首次编译前独立修正并保01；0Java重试，不冒模型或生产失败。该单位无HTTP／新JFR／Main重编或现场操作。

源／逆向／草稿／软件后正式采用回执在 `D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-semantic-native139`。正式 [Reader](../../java/ck3-control/application/src/main/java/org/xar/ck3/control/application/driver/DriverObservationEvidenceReader.java) 为27535 B／`b005429ced7a22617def171c23c2626fecbee34a5a2f6fe2394d86eedde6df03`，[Verifier](../../java/ck3-control/application/src/main/java/org/xar/ck3/control/application/readiness/NativeSemanticEvidenceVerifier.java) 为19813 B／`5f44b32590726ff8926d36e5778261573920e89f489f6ed02ebbd512fca651d8`，[测试](../../java/ck3-control/application/src/test/java/org/xar/ck3/control/application/driver/SemanticDriverReuse366Test.java) 为34502 B／`0ec9de6abb410460b0d7b5e0e11ad4d55efbd7f79143dc218630314f09740019`。Native最终资格88703 B／`251d29a2914b0008bd2a1dc0a973804855fbc19c7181280224c64767b52e6c7e`，原report7823 B／`7d984a3cc3943173159738cdf6afcf6e4639f068c1b42caee87cb76bca3a021f`；owner复核19058 B／`02d34d4ac0bca5aa475ec0a05821d89401953a2f55e93bd7c745930b0c32df32`，Root allocation-only决定7179 B／`4dd20db5ac94a27d8ca83b225343b4f62ba1c5b9da80f65726e3cb8f6c085821`。

P139仅软件分配采用。P100／UNKNOWN／原账本／deadline／Guard及Runtime唯一owner边界不变，不授新stage／布局热载、head47、保存日或实际agent速度。后到P140有限原件核对得before／after Driver facts各7207 B，不含3.4M opaque；Root决定暂不实施manifest stage，不把大Native body成本冒作小manifest收益。下一采用后独立采样先准备具名方案，不以本发表结束持续主线。
