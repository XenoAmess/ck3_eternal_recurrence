# P205：P198 六形状比较为有效 mixed，不授广泛速度

冻结协议的真实结果是 **allocation_support=true、latency_support=false、bounded_micro_support=false**。这是有效混合数据，不是失败重跑理由；不补N/热身、不换输入/门、不自动回滚或改写[已接受的P198](2026-11-10-financing-snapshot-owned-map.md)。本提交只发表事实，生产源码与测量harness均不变。

A为P190原financingSnapshot完整12类，B为P198已接受12类；使用固定历史P198 CPP365加新harness输出前缀366，非物理current371集成比较。两个必要test-only TU首次编译为6类，再仅运行一次Main；本轮没有JUnit engine/selector (existing JUnit Assertions library retained)、旧Test/SDK/生产重编、完整业务case、JFR或utility JVM。相同六份immutable Obj输入/独立literal expected及旧完整key/ref/input不变oracle经公开同package Function caller调用，未反射私有目标、造Guard/ACK或引入生产接口。

顺序固定none/actor/gold/wars/diagnostics/all，cycle旋转形状、每形状ABBA。4×6×ABBA×256热身为96行/24576次；8×6×ABBA×1024测量为192行/196608次，总288行/221184次。每个结果在预分配1024槽中保留至完整POST检查，再在target外清空；target为Function.apply+arraystore及循环。全部原始端点、顺序、实际completed/checked、输入标记和计数通过。每侧13、共26仅指明确file-backed named Finance12+相同Caller定义，实际loader/CodeSource与磁盘前后SHA通过；不是hidden/JDK/Consumer lambda总类数或OS HANDLE/defineClass bytes认证。

下表为**测量批次归一到每调用**的结果，不是生产单次延迟或自然频率。每例每侧16行，配对为8组，signed delta=(B1+B2−A1−A2)/2048；全部48组和8个人工等权cycle原件保留。

| 形状 | 分配A→B（B/调用） | target均值A→B（ns/调用） | target中位A→B（ns/调用） | 配对好/差 | 时间门 |
|---|---:|---:|---:|---:|---|
| none | 1016→1016 | 460.302734→275.079346 | 151.269531→155.615234 | 5/3 | false |
| actor | 1992→1992 | 319.824219→496.520996 | 204.980469→206.884766 | 2/6 | false |
| gold | 1992→1992 | 6353.308105→235.815430 | 227.050781→231.884766 | 3/5 | false |
| wars | 2080→2080 | 214.843750→251.055908 | 208.056641→213.574219 | 5/3 | false |
| diagnostics | 1928→1928 | 317.492676→215.411377 | 214.990234→212.451172 | 5/3 | true |
| all | 9744→6264 | 7961.126709→878.509521 | 1144.189453→776.904297 | 7/1 | true |

all四outer更新形状的8组均少3480B/调用（−35.714286%），其余五形状8组均相等。人工六例等权平均分配3125.333333→2545.333333B/调用（−580B/−18.558020%），不代表生产role分布。时间门逐例要求B均值及中位不劣、paired中位≤0、至少4组严格好；none中位+2.872821%，actor均值+55.248092%/paired中位+3.759766ns，gold中位+2.129032%/paired+1.635742ns，wars均值+16.855114%/中位+2.651960%，这些反向均保留。

人工aggregate target均值2604.483032→392.065430ns（−84.946516%），但pooled median218.212891→219.189453ns（+0.447527%），故aggregate时间门也不通过。大的绿色均值不删、不归因机制：measured A119/all target107.0475ms，A124/gold100.548ms；B117/all target0.9249ms而enclosing125.4817ms，均保。all仍有逆向cycle6 +62.207031ns/调用；人工aggregate后两cycle逆向。包含原完整POST的outer人工均值3108.204142→3635.049438ns（+16.950151%）、中位496.386719→511.718750ns（+3.088727%），不冒整体worker加速。warm首A0/none target11.4018ms、outer62.2097ms及warm A40/B41大值全留；固定warmup不证明稳态JIT。

allocation/CPU实际supported+enabled，前/后/cleanup三份state相同，未启用或fallback。192个measured CPU端点差中187个为0，其余5个均15.625ms；A/B target原CPU总和46.875/31.25ms仅量化描述，不报比例或因果提速。全共享JVM heap used11823672→35040248B、Copy GC20次/35ms是整段观察，不是每variant live/peak或GC归因；expected/assert构造与POST开销均在target外、whole内。

首次compile和唯一Main均exit0 accepted、fencedreleased；最后CLOSE **2026-11-09T22:19:26.136922Z**。两actor合计 **7.8860659s**、operator **9.4831747s**仅子窗。Plan **2026-11-09T21:02:33.875722Z→CLOSE4612.261200s→final4985.013455s**；Source02→2982.671989/3355.424244s为内窗，不相加。更早实际起点UNKNOWN、不记0。Main setup416.4632ms、warm含POST474.7119ms、measure含POST663.1086ms、报告物化83.4522ms/写1.0127ms/stdout11.0313ms另列，receipt写/启动退出由parent窗口包含，不能叠加减除。所有Source01→02 loader/counter失败记录修正、静态cap/编号/路径/ldc宽度/展示截断纠正、准备、Code/peer审、授权、等待和Git保原，非Java失败追绿；owner pretty JSON写前cap拒收仅以紧凑空白保存同字段/同门，不改raw或测量。

Native四根final metadata **1457642B/103files**在4MiB内；tmp/owned DLL/fixture0不授process-wide JNI未载或hard/heap peak。原success report223173B与finish699B均CREATE_NEW/原cap内，cleanup先于报告，两phase HANDLE/租约真实释放；无新增Source采用、回滚、Runtime/Game/GET/P100/SAVE或10s达标。本切点offline371保持，零新增确认保存日、秒/新增保存日null。

原件：`N/p205-financing-measure-test01/reports-component/financing-measure205-report.json`223173B、`36736a625967c0698892f38b444bbce15e7c820955943caccdce8487bbe3186b`；同根final16064B、`0e25251d37148a425b610022b28fb6966ab06d482314d6711f11fb2ecaced22a`；`R/P205-VALID-MIXED-MEASUREMENT-FACTS-ACCEPT01.json`11528B、`6d5a34f6e7edb580737f8ba9fd96207e0ab808d88343b6ceb450cd91d0fd76af`。Root Fraction独算8693B、`6c98e41321ef563ffe490ecf549f6b6d3903f19eb238e285859061981b139eff`；后到owner `J/construction-financing-measure205/owner-review01/ACTUAL-ALL288-SIX-CASES-EXACT-PAIRS-MIXED-OWNER-REVIEW01.json`20785B、`8c61149f724a977448f3d3b8689bd86569a49444a3d1c97a8a4dee16a51004b1`，不回填此前pending切点。N/J/R是原隔离证据根。

exact3只新unit+daily11-10/W46；不发表harness、生产或P206。后继可行性只读另账，目标持续，未以本单元交付宣告完成。
