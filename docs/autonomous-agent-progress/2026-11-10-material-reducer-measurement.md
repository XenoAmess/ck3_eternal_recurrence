# P207：固定原 coldCompletion 的组合组件测量通过预设门

唯一固定输入的真实结果为 **allocation_support=true、latency_support=true、bounded_micro_support=true**；Root、Native、owner 从全部原始行以精确 Fraction 独立重算一致。支持的是这一原 DATA 输入上完整 public `ConstructionMaterialReducer.reduce(byte[])` 的有限组合比较；本次只发表三份事实文档，生产源码、harness、软件371及 Runtime/SAVE 均不变。

A复用P113完整Reducer6，B复用已接受P201完整Reducer6，五nested字节相同；共同历史CPP368加新harness前缀，不是物理current371整体集成比较。此MATERIAL_UPDATED路径包含P196的19-key、P199的progress与P200的source更新，不经过P201 retained159，也不分摊单patch因果收益。首次2TU编译实际7类，再仅运行一次Main；没有旧Test/SDK/生产重编、JUnit engine/selector、JFR或P205复测，existing JUnit Assertions library用于POST。

原coldCompletion输入/helper闭包及完整POST机械保留：query(date820,75,false,true)，检查MATERIAL_UPDATED、receipt存在/completed、date820、pre5/post2、原start_receipt、完整candidate、Nil income、null post_cash_v2，以及完整originalBody经Ledger codec往返相等。公开test-only Function caller直接调用public reduce；POST-only View只经三个cached PUBLIC child accessor取值并校验真实class/loader/type，Enum.name转parent公开Disposition，不进入target或充当生产来源。无私目标反射、Guard/ACK、现场账本或新许可。

输入只在setup编码一次，同一物理byte[]用于两侧；fresh wire为2875B，SHA `d7fc30b9c2d8321ecaff424d302881e346b567032f9be6249d84cd16bee8e5fd`，各批前后和最终与独立backup逐byte/SHA相同。此SHA是本次setup实际记录，历史raw artifact pin仍NOT_HELD。每侧Reducer6+相同Caller共7个explicit named定义，两侧14条/13个物理文件的磁盘前后pin、loader/CodeSource通过；不是hidden/JDK总类数或OS HANDLE/defineClass bytes认证。

协议未变：4轮ABBA×4调用=16 warm行/64次；8轮ABBA×16=32 measured行/512次，总48行/576次。固定16槽保留每批结果，端点后对每个结果执行完整原POST，再清空；target为Function.apply+arraystore/循环。全部48行的顺序、整数端点/差值、completed/checked、输入身份、counter前后/cleanup及finish绑定报告SHA通过，无额外target warmup、补N、调门或重试。

下表均为measured批次归一到**每调用**，不是自然生产频率或单请求延迟。

| 指标 | A均值→B均值 | 均值变化 | A中位→B中位 | 中位变化 |
|---|---:|---:|---:|---:|
| allocation（B/调用） | 357841.78125→296858.21875 | −17.042046% | 357984→296976 | −61008B / −17.042102% |
| target（ns/调用） | 1195153.515625→629995.3125 | −47.287499% | 570756.25→470578.125 | −17.551823% |
| enclosing含POST（ns/调用） | 1446405.859375→999218.75 | −30.917125% | 688137.5→648718.75 | −5.728325% |

全部8组signed delta=(B1+B2−A1−A2)/32如下，负数为B较少。这里配对每call的中位与两侧各自中位之差分开：target paired中位−244900ns，allocation paired中位−60989B。

| cycle | allocation差（B/调用） | target差（μs/调用） | enclosing差（μs/调用） |
|---|---:|---:|---:|
| 0 | −61240.25 | −2856.5 | −3211.903125 |
| 1 | −61051.25 | +13.45625 | +233.746875 |
| 2 | −60988 | −962.415625 | −1204.503125 |
| 3 | −60986 | −162.43125 | +2.103125 |
| 4 | −60804 | −378.434375 | −555.228125 |
| 5 | −60990 | −327.36875 | +976.23125 |
| 6 | −60801 | +186.7125 | +217.34375 |
| 7 | −61008 | −34.284375 | −35.2875 |

分配8组严格下降，mean/median均严格下降；target mean/median不劣、paired中位≤0且6好2差，满足首Java前冻结门。enclosing仍4好4差，不冒整体worker无退化。反向cycle1/6两批总差分别+0.4306/+5.9748ms；所有冷/异常值保留：warm首A0 target581.381ms/outer612.370ms、B2 target193.7356ms，measured A19 target125.1781ms/outer133.4226ms，B37 target34.8391ms而outer79.1367ms。绿色均值不归因JIT/GC或每个源码改动；固定warmup不证明稳态。

allocation/CPU实际supported+enabled，三份state保持，未启用、切换或fallback。32个measured CPU差中24个为0，其余为15.625ms量化（A另有31.25ms）；A/B总93.75/46.875ms只描述原值，比例null，不授CPU因果。共享JVM heap used52414680→8956792B、Copy GC累计1/4ms→7/17ms，只是整段观察，不是variant live/heap peak或GC归因。

两个实际JVM均exit0 accepted、fencedreleased，最后CLOSE **2026-11-09T23:43:35.051720Z**。actor合 **14.313145700027235s**、operator合 **16.236534500028938s**仅嵌套子窗，不相加或替代完整准备。Plan **2026-11-09T23:03:22.354556Z→CLOSE2412.697164s→final2823.493976s**；Source02→997.268746/1408.065558s是内窗，更早真实begin UNKNOWN，不记0。Main setup2020.5666ms、warm含POST1123.9349ms、measure含POST626.1591ms、cleanup0.1335ms；报告物化30.2639ms/写0.9029ms/stdout8.9878ms另列，parent还含启动、receipt写和退出，不能重复加总。两child OS lifetime peak WS154181632/144658432B、pagefile158953472/271892480B不是Java heap peak。

Source01 metadata methodref真实问题在首Java前改为Source02，仅两literal，原件保留；Native静态writer语法、路径/分隔符和owner regex/norm参数错误均保原，不是Java失败重跑。单项错误精确费用未持则NOT_HELD，不填0；全部源码准备、Code/peer核验、授权、等待、报告、最终资格及本次Git保留于具名窗口。Native预算旧快照1052561B/87files，计入预算1528B与final33986B后四根 **1088075B/89files**，在4MiB内；tmp/owned DLL/磁盘fixture0不授process-wide JNI未载或瞬时硬峰值，2875B输入仅内存构造。

原报告 `N/p207-material-measure-test01/reports-component/material-measure207-report.json`71091B / `aadc74dc98595e6e701320f5252afe4426a8ed149b860016577ea6e9fde770a8`，finish694B绑定同SHA；同根final33986B / `a5cdfb840e288136da41cae08035af04951e999090e496af42310b5a1d987fd4`。owner `J/construction-material-measure207/owner-review01/ACTUAL-ALL48-EXACT-PAIRS-INPUT-ORIGINS-AND-GATES-OWNER-REVIEW01.json`11457B / `7ae5ae718276be4f1566fb761021af52e4b402c72b41f877e99c0e9c3aa6f2e9`；Root全行独算6406B / `76fcc5ab5ec200333ce994d52f4456474953a1572078f5680b51edc7aa29e494`，final事实接受3663B / `afeb5590658b7c2a7925489c2fe18dff4e3ca8320aead6cac1fcc7151a5c183b`。N/J/R沿用隔离证据根，所有原始行和错误件不改。

本次证据不授其他输入/全路径、P201159、单patch归因、自然尺寸频率、整体软件或生产吞吐、Runtime/Game/GET/P100/SAVE；没有新源码采用、rollback或自动重测。offline371保持，零新增确认保存日，秒/新增保存日null，10秒/SAVE目标未达。exact3只新unit+daily11-10/W46；主目标持续，后继候选另行审阅。
