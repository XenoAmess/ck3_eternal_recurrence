# P115：大输入保存阶段去除重复纯DATA构造

本地2026-11-08，实际UTC00:16—00:35。P114完整warm消费者数据表明保存阶段仍为285.83275ms／395,396,252B中位；本次仅删除large preserve中丢弃结果的ObservedRequest.fromFullMaterial(full)语句。

full ObservedRequest为final类，factory先clone完整raw，再从同一owned字节解码，private pair构造只由该factory调用，original()返回clone。保存时拿到的large raw已通过相同纯DATA校验，再构造一个丢弃的typed对象不读取时间、Native、Session或原件。oldsmall public构造器decode后才clone，存在调用者并发改源数组的理论窗口；因此small分支原new ObservedRequest(full)重验逐字保留。array长度不变，成功small对象不能进入large分支。

所有真实Session／withSession、DriverJson.object(full)、RawJson.fullMaterial、物理CAS保存与loadFullMaterial、len／SHA／每byte读回、manifest financing副本、cold resolve重建、fresh Q2及Guard保持。未新增cache、类型、API、storage cap或权限。当前formal9358B／SHA256 8f3cc5b990feca7d0ec1ee0d82e3494b107b42dfd983c65bfff6b336b7af111d；旧9410B／026b6453…原件保留，实际diff仅删一行。

真实模型POST00:16:16.851522Z、stop00:16:21.906688Z，total5055.228ms／有效TTFT1529.8693ms／prompt9658／output519，cached未报告。literal edit原样采用；large不可变raw及small边界的最终证明另由owner／reviewer核实际构造、clone与别名，模型文字不授来源权限。必要1生产TU首次exit0／3class，4.0177273秒，00:27:10.563221Z关闭。此前Native复用phase别名误写在claim／JVM／BEGIN前修正，不是Java或模型RED。

新增2个同writer DATA方法首次1TestTU编译0／4.8627683秒，同JVM2P／0F／0E／0skip；child10.1716732秒、operator10.9133714秒、console8164ms，00:32:39.625360Z关闭。覆盖full factory后调用者及getter数组修改、实际preserve两次与原ref／完整读回、新Archive冷读、canonical command融资header不一致、缺件与外部同字节路径拒绝、恢复原件后成功、小输入inline及其旧canonical合同、head不变。只复用两个qualified纯quote／command DATA builder，未运行旧@Test或反射私有权限夹具。cold binding delegate是明确spy，只证明实际源检查先于委托，不冒充Native verifier正向或canonical action membership。

测量复用P114成功的同一个Main03字节、绝对shared-cas／DATA／EXPECTED、Q1／Q2、source及全部hash。无新PREP，无A冷B热；原RootDataset是6831978B的显式139-history DATA重建，非实机FullSnapshot。双方均保P114缓存，所以内部合法report.label仍为B0／B1：外部逻辑A0→B0旧Source、B0→B0新Source、B1→B1新Source、A1→B1旧Source。raw report不改标签，真实variant由Source三class family、first origin及完整ordered classpath确定，不能从内部label臆测A／B。

固定四JVM各2warm4measure，同CPU1／384MiB／90秒；全部8warm和16measure保留，24call cache=true／CAS已存在，输出markers逐次等原EXPECTED，whole等不重叠phase之和。每次仍真实获取／释放writer、mutable preserve命中核验、physical完整重读、header／frame检查、distinct固定DATA Q2对象与sameQuote、实际包内intent／canonical body；手组args明确DATA适配，不称Policy.evaluate／revalidate、Native fresh READ、完整SEM准入或owning publication。新allocation card每进程另记，原source／ledger／anchor／lock／store／payload／commit身份保持，不称整个文件系统完全相同。

| 指标 | P114成功基线A | P115 B |
| --- | ---: | ---: |
| whole墙钟均值 | 913.822675ms | 705.3617625ms |
| whole墙钟中位数 | 861.3643ms | 694.91825ms |
| whole主线程CPU中位数 | 390.625ms | 328.125ms |
| whole allocated均值 | 1,216,925,041B | 1,041,739,137B |
| whole allocated中位数 | 1,216,926,060B | 1,041,740,136B |
| preserve阶段墙钟中位数 | 287.222ms | 147.72655ms |
| preserve阶段allocated中位数 | 395,396,252B | 220,210,304B |

此样本whole均值减22.81%、中位减19.32%、主线程分配均值减14.40%；actor均值12.16565385→11.32841445秒，约减6.88%，不是整个公开生产方法或新增保存日指标。四actor合计46.9881366秒；文件BEGIN00:34:18.141494Z至A1关闭00:35:08.240640Z为50.099146秒，operator总窗口50.553755秒包含其边界开销。所有准备、配置纠正、编译、验证和间隔另存，未forceGC、删慢样本或只摘getter片段。不同单元的A不是同一基线，不把P114／P115百分比简单相加。

证据根D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-preserve115；Native为p115-preserve-prod01／02、p115-preserve-custody-test01、p115-consumer-execution01，原A0／B0／B1／A1.json完整保留。最终QUALIFIED-P115-PRESERVE-AND-CONSUMER-DATA01.json为38145B／SHA256 9f943260b7ae30b43639f0e54999ab11e3ce2ebc14f0f3413070993f20839a78；ALL-P115-FIXED-ABBA-SAMPLES01.json为392596B／f0585319d83d71d45491bf6ba0ef34de0dfb235f38b4526e59c5b8bf1f55b891；身份索引6593B／b1d294378ce9ac84986b1a73003c04d466e2e3a8f3731eb16c49827f3c8844af。Root逐读24call及actual／close的独立审阅另存P115-ABBA-ACTUAL-DATA-REVIEW01.json。

P114后到Native总窗按operator BEGIN口径为191.163224秒，先前本文所引用的文件BEGIN口径190.727833秒从00:10:18.254808Z起，均到A1实际关闭，原件不改；从首次失败PREP到A1关闭473.568004秒包含修源等待。二者不是实际游戏日速度。

P115仍未Runtime采用，无新SAVE或10秒目标通过。下一大phase是resolve约207.40115ms／338,378,552B；融资header exact wrapper也只作为P116待测方案：必须保原token、null-presence、oldsmall及合法raw header>262K的旧accepted set，有限retention超界回原fullparse，新增序列化和临时分配全部计入，不能为cache扩全局cap／改codec。持续任务继续，不在本次发表处停工。
