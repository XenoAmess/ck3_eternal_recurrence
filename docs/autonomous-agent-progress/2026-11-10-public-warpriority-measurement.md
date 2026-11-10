# P215：公开 Input→observe→toJson 的固定组件比较

本轮仅测同一原始归档输入上的公开组件：两次 byte[] 读取及 cast、new Input、observe、toJson、返回 byte[] 的数组存储。A 为 P211 完整四类，B 为 P214 完整四类，只有私有 Observation 构造器的两次 deepCopy 不同；两侧共用 P212 BudgetObservations 和原 BudgetJson。冻结的是 P214 CONFIG 中的 historical374，A 是该环境下的旧四类对照，不是完整历史 P211 环境，也不是当前 OFFLINE375 的整体测量。

原 sources 方法只改资源 Class owner，选定首个 available Source20／triplet145／metadata146／war0，不换输入。完整 snapshot/root 各 canonical 一次，实际 2664／636B；同一个 Object[2] 和两份 byte[] 引用供 A/B 使用，逐行前后及最终核对完整 byte backup、长度和 SHA。两个 child 各严格自载 Caller、四类 family、两个 helper，共 14 个具名来源、11 个物理文件、8 种 SHA；parent BudgetJson oracle 为同物理文件的第三个独立定义。该名单不是 hidden/JDK 生成类总数，磁盘前后 pin 与 loader/CodeSource 也不是 OS HANDLE 或实际 defineClass 字节证明。

完整 WarPriority 原始 golden 未持有。每个输出先解析完整 object、核 schema 与 war0，再用原 parent BudgetJson.equal 验证完整的政治 SUBSET；通过后，首 A 的完整 bytes/tree/递归键序才建立 NEW 差分观察 baseline。2304 个输出全部逐项比较，该 baseline 为 3076B／SHA256 ce873a3d7cd548ea668c0fefc40e494f50f257c7d0fdb2ffdfab00f1836a9fcf。它不是旧 Test 的完整公开输出 oracle、独立政策正确性证明或权限；两侧可能共有既存缺陷。原 Chooser 的 Guard/ACK/replay/ledger helper 整体未使用或裁剪。

首次两 TU 编译实际七类，唯一测量 Main 与编译均 exit0／accepted／CLOSE fencedreleased；未重编旧 SDK/Test，未追加测量。固定 48 行、2304 次：4ABBA×16 为 16 行256次 warmup，8ABBA×64 为32行2048次 measured，各侧1024次，最多保留64个返回数组。归一化分母64，八组 signed 配对分母128；setup、POST、输入检查和清理位于 target 外、enclosing 与整轮成本内。未强迫 Observation 逃逸，JIT 可自然消除本消费者不使用的工作。

| 每调用指标 | A | B | 变化 |
| --- | ---: | ---: | ---: |
| allocation mean，B | 112964.5234375 | 98080.546875 | −13.175797% |
| allocation median，B | 112867.0625 | 98128 | −13.058781% |
| target mean，ns | 321177.34375 | 236227.734375 | −26.449440% |
| target median，ns | 106223.4375 | 76278.125 | −28.190871% |
| enclosing median，ns | 150825.78125 | 89265.625 | −40.815407% |
| POST median，ns | 13842.96875 | 14600 | +5.468706% |

全部原始端点、48行顺序/调用/POST/输入/origin/counter/清理/finish SHA 通过独立复核。Root、Native 与 owner 分别用完整32行 measured 原值计算；冻结 allocation／latency／combined 门均 true：八组 allocation 全负，target 6好2反、paired median −42392.96875ns。paired allocation median −14736B 与两侧 median 差 −14739.0625B 分列。enclosing 配对6好2反，但 POST 配对仅2好6反、paired median +1797.265625ns；不把 POST 的反向结果藏在总均值里。

cycle2、7 的 target 配对反向 +111691.40625／+1850.78125ns 保留。warm A0 target157.0138ms、measured A16 target98.6313ms、B18 target67.0656ms、A23 target64.9953ms，以及 A36 target8.4296ms／enclosing90.89ms 等完整冷值与 outlier 未删；不把大均值下降说成稳定机制或整体提速。CPU measured26/32、warm12/16为零；measured A/B 总31.25/62.5ms是量化观察，比例与因果比均 null。heap/GC 仅共享 JVM 观察，不是 per-variant 活跃量、峰值或 GC 因果。

两 JVM actor 合9.305304000037722s、operator 合11.066403100034222s仅嵌套子窗，不能相加或替代整轮。Plan→末 CLOSE2514.176283s／Native final2796.381047s；完整 SourceReady→1778.440634／2060.645398s；AUTH→BEGIN17.969091s。更早 begin UNKNOWN，不作0。所有源码生成、Code/算术审阅、准备、等待及0VM错误均计入；包括 owner 读取越界0.1745838s、块提取误断言0.1897635s、metadata 标签 checker0.2011521s和路径分隔符比较0.1904117s的工具子窗，确切 process 耗时未持。原错误/脚本保留，纠正只改审阅器，无 Java 重跑或标准放宽；Root 后到 tmp 空目录/文件误判0.2085686s另件保留。Git 成本在发表回执继续记账。

Native final 写后四根 metadata 快照1105714B／91文件，小于原4MiB；tmp/DLL文件及 fixture 磁盘副本为0，不等 JVM 内存为0或 process-wide JNI 未加载。后到 owner raw/error append 不回填旧 final 中 peer pending 的真实切点。

证据根 N 为 D:/ck3-state/resume91-native-integration，J 为 D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108。原件为 N/p215-public-warpriority-measure-test01/reports-component/public-warpriority-measure215-report.json（89448B／SHA256 5b29906c2ecd457f21dd60dc255a97fdad865e667795e64099eb6834d25a05e7）；同根 Native final 36023B／a77aefef10217af4bf12343f0745de02eedb4788081f6fdfccbf31d7e6123d44。owner actualCode 53678B／877d7761…、全行 Fraction18634B／cdd16a56…及后到成本一致性2787B／b0d10413…均留在 J/construction-public-warpriority-measure215/owner-review01。

本次只发表本单元、日记和周记，不发布 harness 或改变生产、baseline、CI/pom/AGENTS；OFFLINE375 保持。结论限于这个固定公开消费者，不能授自然规模/频率、count/sourceSnapshot、端到端、Runtime/GET/P100/SAVE 或十秒/新增保存日达标。新增确认保存日0，秒/新增保存日为 null；主任务继续。
