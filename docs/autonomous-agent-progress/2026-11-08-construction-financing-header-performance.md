# P116：完整融资头部的精确可选缓存

P116只在full ObservedRequest构造时，从同一份FullJsonTree原树编码单字段融资wrapper，并在large preserve中使用该精确副本。完整原文／同writer物理归档、读回、长度／SHA／逐byte核验和cold重新解码保持。该软件单元不授Runtime采用、动作许可、SAVE或10秒／保存日目标通过。上个正式单元为[P115](2026-11-08-construction-preserve-performance.md)，本次基线为其真实成功B，不累加两轮百分比。

源码仅两叶：OrdinaryWartimeConstructionCodec新增private owned byte[]与Optional clone getter，旧public small构造始终无缓存；financing=null保留present wrapper-null，不能等同cache miss。ConstructionOriginalSource.preserve只在large分支lazy选择小wrapper解析，缺缓存仍执行原完整DriverJson解析；oldsmall重验、resolve／resolveCommand完整物理重新加载和当前header绑定均未裁减。SDK标准化输出会改变1.00／-0.0／1e+0等原token，因此未复用SdkProjectionJson或typed融资再编码，也未用32深的OpportunityJson解析wrapper；旧DriverJson64域保持。

真实模型于01:02前的00:46:41.382413Z开始、00:46:57.688172Z结束，单POST200／stop，总16.3057455秒、有效内容TTFT1.9834396秒、13594prompt／2442output、cached tokens=null。只partial-core采用；owner拒绝catch(Exception)吞错、修Obj／Value类型及缺import，改用既有StrictJson.object和私有owned数组。初方案按64MiB编码派生wrapper会新增合法原输入拒收，后继owner改为已有FullJsonTree.MAXIMUM_DRIVER_BYTES的256MiB派生额度；原raw／parse仍64MiB、永久retention仍262144B，没有扩大原输入、旧parser、命令或Guard预算。编码先分配后筛选，超大header确实产生临时数组，全部成本保留。

## 有限正确性与反例

生产01两TU／5class先typing通过，production02仅修改Codec一TU／2class；Source三class复用。新Test首编因owner漏obj helper static import而javac RED，0JUnit；修正后四普通方法3P／1E。该E的完整XML定位为既有NativeConstructionEffects.expected→Candidate.decode→EffectJson.object→OpportunityJson32，不能把其整动作构造域当64。最终仅修失败方法：deep40原输入与所有精度／顺序／clone断言保持，走Source.preserve→Source.resolve的真实64深完整原件／header核验；撤去该深输入的动作准入声称，生产Guard／EffectJson与旧helper不改。浅层canonical command、frame／原件绑定由已过的另外三个方法保留。

五个unique新方法的通过来自Test02三个原P、Test03失败方法单独1P、Test03独立大case1P，跨三个JUnit JVM，非同JVM5P；原RED／1E不覆盖。覆盖原token／高精度／负零／指数、原成员顺序、escaped字符串／非BMP、40深、caller／getter数组变异、两实例、full small present／oldsmall empty／null present，以及真实same-writer CAS保存／cold加载、坏当前header、缺payload、同字节外部alias拒绝。归档delegate spy只证明source先验，不冒充Native verifier正向或Root权限。

合法大header反例实测：3000个127B零指数原token使exact融资385906B，而既有标准化融资仅13906B；full输入398479B仍由factory接受，缓存empty，preserve fallback及canonical cold header核验通过。独立近上限case直接构造67108863B原raw，含6000个literal UTF-8 emoji；实测派生wrapper67150800B，既有SDK融资25931B，新factory成功／cache empty／完整raw逐byte同。该case不要求巨大manifest可通过旧1MiB动作边界。其单JVM1CPU／Xmx1024MiB／90秒，actor5.5578267秒；owned OS峰working set1090727936B、pagefile1153990656B，均不是heap实占值。其临时编码和高峰内存如实保留，不混入普通性能cohort。普通方法使用384MiB／90秒。

## 同一warm CAS完整DATA对照

复用P114 Main03的26020B／SHA256 6660ee3c3ecf375b620eaeb63b5355c1b8cb3763dbe8e9cffbeaa0111ddd1da0，无Main增编、新PREP或dataset刷新。原6831978B input／Q2、固定绝对CAS、source／ref、DATA／EXPECTED保持。四独立JVM各2warm＋4measure，CPU1／384MiB／90秒，全部8warm／16measure和失败／慢样本保留；实际only target class族切换，A0=A1、B0=B1，所有24call cached=true／warm=true／marker=原EXPECTED，whole等于disjoint阶段之和。getter marker来自共同P114 exact结果路径，P116新header路径由当前源／独立测试确认，未捏造新Main marker。

logical A0／B0／B1／A1与实际raw标签B0／B0／B1／B1显式映射，raw不改写，真variant由first-origin／完整class族SHA和ordered CP区分。各进程新增software allocation card单记；原head／anchor／lock／store／payload／commit身份保持，不声称整个文件系统字节相同。

| 指标 | P115成功基线A | P116 B |
| --- | ---: | ---: |
| whole墙钟均值 | 730.0337375ms | 631.3798ms |
| whole墙钟中位数 | 722.61945ms | 622.43395ms |
| whole主线程CPU均值 | 341.796875ms | 306.640625ms |
| whole allocated均值 | 1,041,765,402B | 945,644,769B |
| whole allocated中位数 | 1,041,763,556B | 945,644,780B |
| preserve墙钟中位数 | 152.06015ms | 86.4378ms |
| preserve allocated中位数 | 220,210,336B | 124,024,624B |

此样本whole均值减13.51%、中位减13.86%、分配均值减9.23%；actor均值11.2068362→10.53680915秒，约减5.98%。新增wrapper成本并未藏掉：construct分配中位175186200→175216264B，resolve338381912→338408564B，Q2 175227488→175257552B。construct均耗114.5833125→114.8331625ms，intent均耗107.3128125→107.4850125ms，均未更快；未改Q2样本墙钟反而更低，不能把全部whole差额都因果归给融资cache。所有factory／冷重新解码、CAS读回、clone／比较、writer获取释放、setup／main／process／outer均计入或另存。

ABBA含阶段间隔总窗口47.112489秒；从首生产BEGIN至末close739.117687秒包含纠错、测试、审阅及等待。二者不同于只取16个timed样本，也不等于公开Policy或实机游戏日耗时。Main执行的是实际factory／compose、DATA args组装、真实同writer preserve／cold resolve、固定DATA Q2比较和包内pure intent，不是实际Policy.evaluate／revalidate、Native fresh READ、完整SEM准入或owning publication。

业务证据根D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-financing-header116。Native最终QUALIFIED-P116-HEADER-AND-CONSUMER-DATA01.json为67246B／c4e58eaa32a9657089a21aff08de5b5e0f6e3d101d727ec6f1a0d983c223af7c；全样本395511B／a26e5f9c8b0148f633fe6d4327d6b92173ad8c71b2b36c079ab69b19776ad300；fixed identity6593B／0fc52656dffe8e8daca604a0ff066af7f81bbe3009b109cb05c139be0e64499b。Root独核全部24call、96具名origin pins及最终145pins，原错误与机械metadata修正另留。

P116无新增保存日或Runtime收益。B resolve中位203.6795ms仍为大phase；pure intent中位78.0845ms／114651120B。后继P117仅准备同一NativeQuote exact结果在intent的受限复用：保现有query编码，并须逐byte等于该quote.original才用cache，否则原finalizer。该下一候选仍须独立验证和同输入完整测量，持续目标继续。
