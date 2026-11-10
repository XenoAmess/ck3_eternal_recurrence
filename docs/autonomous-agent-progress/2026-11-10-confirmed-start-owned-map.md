# P209：confirmedStart 的局部收据 Map，以源码、Code 与原单例回归验收

仅将 `ConstructionMaterialReducer.confirmedStart` 的253–255三个物理行改为局部owned Map：从intent.original成员复制一次，按原effect迭代序跳过candidate并put，其后按原序取两项diagnostic Value、put，再构造最终Obj receipt。原304行、240–252与256–270全部Guard/校验以及其余源码字节保持；无新API、字段、类型、helper、cache、raw/typed桥或新Test。

原exact12-key Guard使合法effect有11个非candidate更新，随后两项诊断，共13个with。排除原intent容器，26浅Map/13Obj→2Map/1Obj仅为源码/既有Obj定义的构造代数，不是本轮实测分配、自然调用次数、尺寸或性能。保留原完整candidate值/引用和未知扩展成员；覆盖已有键不移动位置，新增键依原序append，所有Value引用与输入不变。Obj允许null Value，不添加非空检查；正常闭合immutable DATA等价不授OOME、分配时序、恶意反射私态或全部异常等价。

实际唯一1TU编译6类exit0；Top38678B / `eabe244d004998064102c3e91bfd7a45b473ddba11b27e0eaeafccf34f9f2fc2`，五nested原SHA保持，major65/API/fields/参数/Nests/raw CP及完整BSM/literals原样。39个方法中其余38个完整raw Code及attrs相同。目标1086→1108B，原[436,559)→新[436,581)全region逐项核：effect iterator/candidate跳过/getKey/getValue顺序保持，put531/550/566，最终Obj ctor576/store receipt4于579，原256+随后执行。区外399指令/29分支和436B prefix/527B suffix原样，所有frame/player/proof/wallet/codec校验保留。

新增map5/iterator6/entry7仅在局部块；旧iterator5/entry6只在对应loop映射。map5后被原candidate store912覆盖，先于load928/1067/1072；6/7无区外引用。maxlocals7→8、maxstack12不变，按实际定义核对而非global mask；源码block或实际槽复用不授GC/即时释放/堆占用提速。

复用P196原qualified Test2，**零Test重编**，仅首次选择原 `verifiedStartMergesTheFullOriginalCandidateAndRejectsAnObservedDifferentSelection`（源码87–96）。公开Codec.intent(originalReceipt)+原12字段effect/snapshot，正例完整原candidate结构相等（含原钱包/成本扩展），改building_type_id为12的负例抛原IllegalArgumentException。三engine XML合计唯一 **1P/0F/0E/0skip**，case **1.783s**、Jupiter suite **1.808s**；其它selector/helper测试未运行。Run373实际前8来源为缓存2+新生产6，原source/cache pins、provider ABI和输入未变后验独立核。此前typing切点selectedpass NOT_HELD原件保留，首次真实通过另记。

该oracle没有独立覆盖11个effect字段、两诊断键的全部值/键序/ref/input不变或所有Guard失败优先级；这些正常DATA等价由独立源码/actualCode证明承担，不冒完整功能穷举。本轮无新fixture/benchmark/完整APPLIED/JFR/额外样本；case wall不是性能测量，[P207固定cold组件结果](2026-11-10-material-reducer-measurement.md)也不授本方法收益。

两个实际JVM均exit0 accepted、terminal/fencedreleased，最后CLOSE **2026-11-10T00:10:19.807280Z**。actor合 **9.608418400050141s**、operator合 **12.355588699923828s**只为嵌套子窗，不相加或替代完整准备。Planning具名 **2026-11-09T23:51:44.558660Z→CLOSE1115.248620s→final1320.931236s**；SourceReady→781.037109/986.719725s为内窗，更早真实begin UNKNOWN，不记0。准备、编译、Code/peer审阅、原缓存资格成本、授权、全部等待/错误、最终资格与Git保留，重叠单元窗口不相加。

Native count-shape/pretty JSON写前cap/路径错误、Root actor比较/canonical API及owner只读路径/inline打印、首次XML checker路径分隔符假差异均保留原件，仅修checker而不改源码/类/标准或重跑Java；缺单项精确费用则NOT_HELD。旧预算快照1113119B/66files，加预算1127B和final23059B后三根 **1137305B/68files**在4MiB内。tmp/owned DLL/磁盘fixture0不授process-wide JNI未载或硬瞬时峰值。两child OS lifetime peak WS145092608/152850432B、pagefile155144192/273989632B仅各自进程OS值，不是Java heap峰值或候选收益。

源32374B / `15073b53050ddedf541d54f48346e9a590c0572ba502adc9212af7a9d4273e2b`；早Ready固定formal8a08/软件371，后到P207 facts-only67775未改Reducer基底32232/30ffc，不轮换历史。原件：`J/construction-confirmed-start-map209/candidate01-owner/SOURCE-READY01.json`2610B / `307a2cc7811df0da21ed383636a3d5b0b0dfc39ed6bbc7030748d5d553105fb8`；owner actual39 proof32750B / `8abb6bf7d9d26e035e7e48e4db385ec68b440dcd8f695fc780066aaef230e6c6`，首selector proof8849B / `36c4ccfdb4affb968798cb014691e2217700fa146e1a4f57c7b3a0a9eb201cb2`，均在同unit的owner-review01。

`N/p209-confirmed-start-regression01/reports-junit/TEST-junit-jupiter.xml`45915B / `2d1e7dbf20e5607840a0bac1b9518cc73710ec323a88e54cf2651fa31dd4a9de`；`N/p209-confirmed-start-prod01/QUALIFIED-P209-PROD6-CACHED2-FIRSTVERIFIED1P-ALL2COST-FINAL01.json`23059B / `bdc8bc11e52d111a613ad07a1fa9008067233a6c3ef17254a42453c600ea17af`。Root actualCode3653B / `7cf6211349a6c617970130e2cefdc38003557860d5c82165bde0a2d6b727f129`及首1P2482B / `d7aa756e6789aa05c671fa3560b91d6b6e1865417d6725f2a0250636186e2ff2`独核；J/N/R沿用隔离证据根。

本次exact4仅该生产叶+新unit/daily11-10/W46，旧Test/Obj/Guard/parser/hash/oldencode不变；接受范围是正常DATA源码/实际Code等价与有限原功能回归。软件切点371，未来372候选及后到Root实际离线采用另账，不预填采用或JVM装载。无Runtime/Game/GET/P100/账本/UNKNOWN动作、SAVE或10秒达标，新增确认保存日0、秒/日null；主目标持续。
