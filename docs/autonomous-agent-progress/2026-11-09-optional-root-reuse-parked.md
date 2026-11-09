# P165：ROOT 局部解析复用功能通过，时间反向，默认PARK

候选只动 ConstructionDomainLifecycle 的480／483／489／490四行：原 ROOT contract.decode 严格验证完整帧与独立token，CASH decode仍先于原ROOT消费位；正常token≤262144时用同call Packet.originalResult 的不可变Obj做status／类型／Optional.equals观察，超界在原490调用原parser。CASH段、全部物理读取／identity／hash／Guard／parser／encoder体保持，无新类型、字段、API、helper或跨调用cache。ROOT normalized result不能代替originalResult；CASH的后续encode有键序风险，本单没有复用它。Obj跨CASH解码延寿风险保留，不能授峰值降低。

实际生产首次1TU8 exit0／accepted／CLOSE，候选50,080B／`0f19eb772f60a1991037495e90df81c9732b78bf00fb003ec31e0732454c3dd5`可整叶逆回P133原49,913B。字段／公开与protected声明／Nests相同，private synthetic lambda$verifyOptionalMaterial$5新增Obj捕获参数，不能声称所有方法声明相同或可Runtime热载。旧／新 fallback 都在line490。

Test03首次编译真实1个符号错误：reverse返回Value却直接访问members；0classes、0JUnit，stderr433B（GB18030）与CLOSE保留，不算功能失败。必要Test04只加已知Obj的安全cast，逆回03整叶一致；只重做仍未成功的同1TestTU4，不重编生产8或旧绿。编测前保留01／02／03三稿：02修正receipt拒绝阶段、成功row端点与Unicode功能表示，03把fixture owner改为实际73；均不是执行重试。Test04实际首次有效4类及唯一JUnit1P0skip，stderr288B原件保留；共4个实际phase（含03 RED），无额外profile／fullcase／补样本。

实际测试原字节34,384B／`c489723e7bdfec479bf66c0edc7b79bb31f934177869e805ca44f0c261bed787`仅D保留。A旧P1338、B新8分别child隔离，parent FinanceReadContracts／Input／回执共享。只反射实际private纯DATA verifier，不构造Prepared／Session／writer资格，也不以未观察的ledger／query字段替代完整material／previewImport验证。没有候选软件的完整public case或Runtime通过。

原ROOT资源1,781B是多行；原模型compact token为1,409B，递归反键序＋pretty／既有字符Unicode转义token为1,836B，typed模型相同，帧1,500B／包1,504B相同，全部实际SHA与首轮前预测一致。两个输入各8ABBA（16A16B）共64，0setup目标调用／0额外warmup；所有端点、成功void、原件SHA及input后验通过。固定非随机顺序、共享parent初始化／JIT、首冷与后暖行全部保留，不合并未知自然频率。

| 输入 | allocation mean A→B（B/call） | allocation median A→B | wall mean A→B（ms） | wall median A→B（ms） | 8配对 wall B−A |
|---|---:|---:|---:|---:|---|
| compact | 302,968→102,728 | 118,016→97,680 | 5.53833125→6.31953125 | 1.92785→2.60155 | 2负6正 |
| 反键序pretty／escape | 119,789→98,926.5 | 119,824→98,864 | 3.0691→6.59295625 | 1.7893→1.76385 | 5负3正 |

两形态allocation8/8配对下降；compact后段118,016→97,680B、约少20,336B是真实小机制。首A3,071,208B／56.5348ms，首B162,104B，compact均值−66.0928%受冷首支配，不能全归删除解析；pretty分配均值−17.4160%仍保。compact wall均值＋14.1053%、中位＋34.9457%、6/8更慢；pretty均值＋114.8173%而中位−1.4223%，B最大57.3481ms高于A18.5716ms，两次大B慢尖峰保留。CPU全部中位0；compact A14/16、B16/16为0，pretty双方全0，15.625ms量化不授−100%CPU或零成本。

之后14真实private调用case／28次目标调用、2独立public ROOTdecoder oracle、2constructor拒绝均通过。262145 token先被真实64MiB ROOT decoder接受，再于原262144消费界抛同类／全文相同动态错误，包含lambda$verifyOptionalMaterial$5:490；坏CASH先于该窄界报错。合法legacy county缺capital经真实public normalizer增加显式null，originalResult与normalized result确实不同，候选仍保原始语义。ROOT反键序、无ROOT、unavailable、错误contract／step／protocol／独立token及缺失token都保原错误；重复JSON在RawJson ctor拒、nativeOk=false在PlanningReadReceipt ctor拒，均明确0private目标调用，不冒新增分支覆盖。

保留报告36,089B／`928a5380d3887422d6094ba7ab0a658ecbb42d1b6d3454cca0e0928ed132d756`，NEVER＋CREATE_NEW；全64端点和16类实际SHA已独核。setup0.2920231s、功能0.1260635s、before-report0.8389371s不含写报告与JUnit／VM尾部。四actor合20.9063515s／operator合25.07121s仅资源子窗；Native最早已知artifact `2026-11-08T23:20:53.001689Z` 至末CLOSE2370.158314s、至资格2806.719147s，包括所有失败、修正、准备、冷启动、等待与后处理，更早Root／实现研究UNKNOWN，不记0。四根metadata1,735,691B＜4MiB，原433B错误和288B后继stderr不删，预算通过不等parent瞬态heap峰值证明。

Root最终默认PARK：分配条件收益保留，两个输入的时间反向不支持当前延迟目标；不改lambda样式再刷样本。生产和Test留D，正式业务／软件current351不变，无回滚（从未采用P165）。本次只unit／daily11-09／W46三事实docs；0新增SAVE，不报有限秒／保存日，不授整体CPU／worker／Runtime／10秒目标。P164事实、P163限定采用及所有旧PARK／失败不改写。P166另沿更大payload同调用值比较研究，不以文档延迟后继工作。

原件：[Native最终资格](D:/ck3-state/resume91-native-integration/p165-root-reuse-test02/QUALIFIED-P165-TEST04-FIRST64-FUNCTIONAL-ALL-FAILURE-COSTS01.json)（79,988B／`4cda2517f252b081c238def6ab1adec52fbcbb72f8869882e6ff7caf98d981cd`）；[全部64原数](D:/ck3-state/resume91-native-integration/p165-root-reuse-test02/tmp-junit/junit-4499539799001968975/p165-optional-root-reuse-fixed64.json)；[Root完整独核与PARK](D:/ck3-state/resume91-root/post-vacation-20261107/P165-ACTUAL-FIRST64-ALLPOST-16CLASSES-FUNCTIONAL-AND-PARK01.json)（20,075B／`8d0bf8643ca0e4c88f695d2b39ad9482c1fc618ad61bbab36dbf5459ad37f473`）；[owner独算](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-next165/OWNER-ACTUAL-FIXED64-AND-PERFORMANCE-ADVICE01.json)。
