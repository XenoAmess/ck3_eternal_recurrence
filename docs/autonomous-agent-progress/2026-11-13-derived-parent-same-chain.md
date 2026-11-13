# Derived 父回执同链相邻校验（软件候选）

实际Action闭窗采样中，Journal.historical经RootDerivedChildAuthority.verifyArchived→NativeRecordedEvidenceVerifier.guard/verify为76个Execution／88个Native样本的一个caller组；这不是全量wall或CPU。Source72B只针对该真实callee中133加载parent后、134／135相邻两次membership验证，不改140 lookup与148 preceding之间的authority callbacks，未外推整个76组都可优化。

Root保留原顺序：先load原parent，再第一次完整canonical chain校验；仅实际final NativeArchive、同原owner／writer Session／active HistoricalReads，以及两state的sequence／machine／canonical action head相同，才有资格复用。第一完整读取的全部CAS依赖须实际held，新鲜metadata／lease守卫在复用前后照跑。第二次仍真实重开选中ActionRecord，保第二top检查与两次完整receipt编码比较。不同头／opaque／无custody原第二full照跑；未知公共Archive的router原load＋两次full逐字保。没有公开trusted AST／flag或跨调用head相同缓存。

正常Submitting存在源码路径：Coordinator214先INTENT、216在新head重新guard，Derived110记录该头且119核unchanged，253 appendSubmitting，Journal122 preview在124 commit前。因此两头可以在这个阶段相同；归档后重放常不同则走旧路。这是source potential，未据此报实际hitrate。已有Source70 Store依赖捕获／fresh检查、DPP及Runtime桥作为显式coherent候选依赖，当前未实际采用，不把未部署类型冒成活跃能力。

actual两TU19类首次0，owner24单Test3类＋原qualified Fixture37／Helper2复用，整2首次2P/0FES。真实writer/coordinator建立多record链，经实际Root包级router与NativeArchive同头clone、未知Proxy两full、不同头／无custody、第二head fresh failure、parent加载优先与后继合法调用均验证。formal只移两处delta并逆恢复规范化原BASE，保Archive既有diagnostics/historicalBorrow/provenance差异；正式两TU19独立0，同Test／Fixture／Helper独立整2首次全P，23:41:59.002401Z释放。完整Installed RootContext许可／Native动作不是该DATA测试资格。

原平衡日志的小fixture中typed-same-head为30次publication entry、plain-same-head55；两者均15个acquired物料、peak36751B、fallback/opaque/bounds/validation失败0。同材料输入与未知full route已有真实断言，不是镜像计数。**这不是总IO或提速**：依赖前后freshLease检查不进入publication counter，可能抵消收益；不同头的同数值也不授快路。该软件发表切点的原日志只有秒级Logger，完整高精度per-scope wall尚未持有，JUnit／actor总时包含setup和多scope不能倒算。受控ABBA完整scope测量另行小资源报价，软件发表不等它，健康worker不据这小计数冷启。

Source72首两次真实模型输出分别8000／12000 tokens到length，整件UNUSED、未读半稿、不拼接，未作语义／编译失败结论，0model hunk；共191078输入／20000输出tokens、124.0768093秒HTTP，无第三请求。owner/helper先试三个negative/fixture loop，但不覆盖本次正常Action热路，未编／未采用；最终只选择这个正常Derived切片，生产两叶由owner/helper实现。

来源根 `D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/life-postcondition-p0-20261112-01/action-canonical-history-source72`：helper-owner03/SOURCE-READY72B.json（10283B／0d9e0448…）、SOURCE-READY72B-FORMAL.json（4211B／e819e9fe…）保完整source／BASE／cohort pins。actualNative137327B／86f7f61f…与Root30907B／0fdc5fe3…；正式Native142460B／a2f4c671…与Root30560B／84f2b00e…。原Fixture119729B／8960d52a…与Helper16482B／3bd4e423…直接复用，不重新编译或冒frozen旧版本。

Native根 `D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01` 的action-canonical72B-compile01／whole2-junit01和formal-compile01／formal-whole2-junit01保存ACTUAL／XML／POST输入未变／CLOSE。SOURCE72B-ACTUAL-FORMAL-WHOLE2-WALL-LIMITS-AND-200JVM-FINAL01.json（11513B／8661e2c9…）保双变体与wall缺失界限，EXISTING-ROUTER-CAS-METRICS01保原七scope分组，没有另跑诊断counter。

本次未Runtime采用，不改变当前正常游戏、动作、Deadline或Guard。未来classloader／完整cohort采用、实际同头held条件、包含freshguards的完整wall与新增SAVE各另验；不因软件通过、发布或55→30而授10秒目标。

后到一次有限完整作用域测量已实际执行，未做重投或按结果扩样本。owner26冻结12103B测试复用同一真实writer／coordinator fixture和同一个actual NativeArchive；A走新router，B逐字执行原loadParent及两次requireHistoricalReceipt三行，不使用Proxy。System.nanoTime从writer.locked之前到archive.inSession、HistoricalReadScope及全部freshguard、custody、decoder／lock关闭之后；结果相等、原账本不变和受控Native计数检查在计时外，关闭期间既有日志成本仍计入。配置CPU1／Xmx192、child240秒，实际唯一JUnit首1P，actor28.6639459秒、outer30.2661293秒。

初始自然链实际为N4，计时外经原合法UNKNOWN追加3条后为N7，没有强造预测的N3／N6。每个cut保留warm A、B各1，再ABBA×4的16次测量，总36行全部返回同值。原fixture建立15.7633205秒、追加5.6799173秒另记；准备、编译和managed outer不冒充目标scope速度。每个variant／cut均8次measure，完整原序与warmup均保留，无阈值、调参、样本删除或第二次测量运行。

| 自然链记录数 | A中位数ms | 原三行B中位数ms | A合计ms／8次 | B合计ms／8次 |
| --- | ---: | ---: | ---: | ---: |
| 4 | 51.68515 | 44.62965 | 409.0070 | 369.2817 |
| 7 | 66.84125 | 71.40570 | 544.5179 | 596.6426 |

N4四个ABBA round中新路径3慢1快，N7为3快1慢；没有稳定收益结论。N4首warm A151.3814ms／B52.7783ms及N7 warm A81.4360ms／B92.6497ms全部保留，不宣称稳态JIT。A仍需第一次O(N)完整walk与trace，新增前后O(D)依赖fresh验证；B在相同HistoricalReads内也已有lease及command cache，第二walk不是第二次冷磁盘获取。这个同command的小链不能代表真实异command长链，55→30 publication也不等于总metadata／IO下降。当前不为70／72B冷启健康worker，不授Runtime命中、总体Action提速、保存日速度或10秒目标。

冻结测量源：`D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/life-postcondition-p0-20261112-01/action-canonical-history-perf-owner26/draft01/DerivedParent72BFullScopeTimingTest.java`（12103B／`804b1bd67279b870b655f21ff97158f830ed2b0942aeef0f1d0759a2602b6b03`）。Native原件为同Native根action-canonical72B-fullscope-perf-junit01／actual／prod的ACTUAL、POST、MANAGED-CLOSE及stdout.bin（8617B／`9628b6fdd8907bbdcac39a226907088074a9acff35e10e0e1438455907a105ab`），00:00:54.111403Z已释放。独立模型测量review一次完整stop，误把warmup计入measure index而建议18；实际代码warm后重置index并恰16，已源核拒收，0代码／测量改动，未设为实验门。
