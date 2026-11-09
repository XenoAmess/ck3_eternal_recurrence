# P204：peacetime/material 元数据局部Map的有限源码与Code接受

Root接受正常immutable DATA的两处容器变换、首次typing及实际Code证明。本轮**0 Test、0 JUnit、0 fullcase、0 benchmark**；两目标的独立positive oracle、动态命中、成员数M/频率、实际allocation/JIT、CPUwall、GC和收益仍未持证，不以P182 PARTIAL采样或旧case补授。

[OrdinaryConstructionCollector.java](../../java/ck3-control/application/src/main/java/org/xar/ck3/control/application/planning/finance/OrdinaryConstructionCollector.java) 以正式359cb4的P203源30471B、`f530fc823a91abc064f96ce0d91865318c46c7fd220e592b268eaf380688e82c`为基底，新源30884B、`e00dafb74682191e683d945887ea4570986aba89c07ed2000bc2530b9efcf903`。只peacetime195–196和material250–251四物理行，326行/wholeinverse及3完整RHS×2均保持；P203 privatequote及其余源码原字节不动。

每处分别先完成new Text(frame.snapshotId())，再copy本次normalized.members到私有LinkedHashMap，按原序put queried_snapshot_id、以原IntegerValue(frame.revision()) put queried_revision、以原IntegerValue(frame.identity().nativeRevision()) put queried_native_revision，最后new Obj。覆盖键保原位置，新键原序追加，保留Value引用/输入及最终owned copy；没有共享builder/helper/API/field/type/cache/bridge/nullguard。material原normalized不新增赋值，完整Obj构造仍先于Optional.of；未知CASH仍empty。ROOT/CASH/CONSTRUCTION读取顺序、Known条件、normalize/parse、peacetime encode/decodeCash/ObservedCash、全部fresh ending checks/Guard/catches以及parser/hash/oldencode均保持。

每个实际进入的三with链由6浅Map/3Obj变为2Map/1Obj，仅为源/callee构造代数。两条不同路径不合成实测节省；大字符串/子树仍为引用，不是深拷贝3.4M或N²。Obj原null行为保留；删除中间allocation/OOME、map-growth及资源/liveness时序不授所有Throwable、恶意私态或资源失败等价。

沿P203真实release21无显式-g/-parameters profile，唯一生产1TU22首次compile exit0 accepted，CLOSE **2026-11-09T20:40:46.380967Z** fencedreleased。Top40110B、`287b06afd6188a7e552426ae8f4c9a6d26d469e4998aaad8368bb3b8de31f910`；21nested逐SHA旧同，API/fields/params/Nests不变。other23含P203 privatequote的normalized Code/CP/BSM/literals全同，**20raw同、3CP编号重排**，CP1063完整符号不变。

peacetime666→700B，[525,586)→[525,620)完整RHS/构造区逐指令核验；区外278指令、9branches、4catch ranges/handlers同。material703→737B，[278,337)→[278,371)同样完整枚举；区外293指令、5branches、4catch同，Obj ctor368→Optional.of371→cash5 store374。peacetime临时15/16无区外访问；material临时12由原finalized store662覆写再load674、13无区外访问。所有区外local operands保留，未全局mask槽/分支；这些事实不证明立即GC。Native与owner复用现有class reader纯Python解析，无Java/新Graph平台或新fixture。

actor **5.2753081s**、operator **6.7460604s**仅唯一compile子窗。SourceReady **2026-11-09T20:27:16.201296Z→CLOSE810.179671s→final1227.699798s**；Native首锚→371.265174/788.785301s，production首artifact→116.750860/534.270987s为内窗，不相加。更早scout/协调起点UNKNOWN、不记0；准备、Source/Code审阅、授权、等待、qualification和Git全部保留。Native旧attrs字段映射0.3039353s、template Ready文件名查找0.1853383s两项0VM错误原件保；owner显示截断后分段重读、首次包路径误猜及CLOSE→实际MANAGED-CLOSE pin路径纠正也保原script01/纠正件，不是Java失败、重编或标准放宽。

Root后到预算切点 **699976B/63files**在4MiB内，先前预算切点保原；tmp/DLL/fixture0不证明process-wide JNI未加载或heap/hard peak。Root接受时owner actualCode仍IN_PROGRESS，后到独立13285B证明和2240B一致性件已完成；Native原final空peer数组不改写。源码、typing/Code-only、Git和后到软件采用分层，本切点actual软件**current370**，future371不预填；无Runtime/Game/GET/P100/SAVE或10s目标信用，新增确认保存日0、秒/新增保存日null。

可核：`R/P204-LIMITED-TWO-METADATA-SOURCE-ACTUALCODE-ACCEPT01.json`5344B、`5dab36f1382bb081f4e5d8863f5b30ca705cd800087b414c358be3009008a248`；`N/p204-cash-metadata-prod01/QUALIFIED-P204-PROD22-STATIC25CODE-SINGLECOST-FINAL01.json`12479B、`c3adccd7bfdbacb89d17f6a36d3e3a7f2d01707c35ab1fcfaffd25c1edebabd1`；同根Code109170B、`233b101a5fd243d0b87c8ac995b61990ced8cd56109698212e61dfbd68d438b1`；owner `J/construction-cash-metadata204/owner-review01/ACTUAL25-TWO-CASH3-RHS-REGIONS-AND-CATCHES-INDEPENDENT01.json`13285B、`4c81b6a302efdca11ca5b6073d7b001cdbaeb75bcfb26fc9d11cac5e8d4b6094`，一致性2240B、`ad6584e267652a862918fe38b273c7a2048fb6eeb38cb09092ebf71981dd2fab`。N/J/R为Native、Java交付与Root隔离证据根。

exact4仅本生产叶+unit/daily11-10/W46，不含Test、Obj、其它源、P205、AGENTS、CI、pom或运行文件。后继P205仅另账测量可行性研究，持续目标未完成。
