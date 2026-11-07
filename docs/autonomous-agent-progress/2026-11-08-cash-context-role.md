# P110：现金角色覆盖producer和原件验证的SDK入口

Collector.cashContext过去把完整snapshot/root送入Gift、ConstructionCash、Focus/Political的原64KiB SDK lane。两个真实入口现在共用 `OrdinaryFinanceCollector.projectCashContext`：producer构造后投影；FinanceEvidenceArchive在全部原件核验之后、最终cash SDK判断之前使用同入口。跨finance/effects包需要该现有类上的纯静态方法，无新类、控制权、parser或预算变化。

snapshot只选21个声明顶层键，diagnostics只选connected/PID/gen；全部业务容器、route/strength/war termination/opaque CB均完整保留。root选14个完整子树，特别保留后继Construction intent读取的 `player_monthly_gold_income`。source/frame、cash候选、spending、market、market_source_frame、mercenary ledger及其余outer字段不裁，missing/null/错误shape保持；完整request/SEM/Packet/root/docs仍在原owner处。

这是角色表示，**不是无损归档**。Focus raw echo/currentRoot内部表示可以变，最终政治profile、FocusedWar和现金Decision须相同。新Construction args中的ordinary_cash_request参与新actionId/bodyhash，表示变化仅作用于后继新规划；已发行命令/原hash/UNKNOWN绝不改写或重投。NativeQuote原starting/ending全文和原限额不动。

## 模型与必要编测

模型真实一次200/stop，UTC19:43:09.695→19:43:24.906，TTFT6317.99ms、total15211.43ms、prompt48676/output1449、cached=null。语义core partial采用；owner修正Obj.get返回Value却赋Obj的编译错误，并合并不必要私有别名。首次准备路径把ConstructionDomainLifecycle放错module，在0POST前改正并另记，不算模型错误。原件：`D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/cash-context-role110/model01`。

两生产TU一次green，exit0/16class/6.2508452秒，19:46:29.272151Z close，未重编codec/Guard。唯一新Test首次因owner复合var声明javac RED，exit1/0class/0JUnit/1.4117572秒，原件保留；只拆两声明，第二次TestTU exit0/1class/4.8047895秒。仅五个新方法5P/0F/0E/0skip，7.3256083秒，19:58:50.157231Z实际close。最终Test15931B/SHA `88e66f4288e3eed60f4068988eff948ef2da79a7ea38aa78b1f55a5ba1a41e41`；此前消息抄size15930不是原件尺寸，不回写历史。

## 新DATA证明的范围

- 32Gift：全部typed Request、Decision及原expected；31ConstructionCash：context/quotes/cost/kind/procurement等和完整Decision，其中3个正例实际进入Focus分支。
- 18Focus：FocusedWar及expected全输出，同每个原war ordinal比较政治profile bytes/qualified/status/reason，共20个profile；role echo只对其实际提供的role bytes一致，不与完整历史原输入冒称相同。
- publiccashContext保原held snapshot/root/market/ledger等对象与字节。Driver139末个原ROOT的income raw584686/scale100000及actor/native/date绑定完整保留；这证明实际Lifecycle收入消费者所需子树，未执行真实intent或授其资格。
- 新snapshot64411B仍小于64KiB，而完整cash65897B越门的SDK正例通过同共享入口；错误scalar/null/missing保持。139行历史是未消费的大扩展DATA，原SDK full输入仍拒，角色判定与原小输入相同。

实际最大role：Gift2277B、ConstructionCash5805B、Focus3999B。POM只引用3个现有原向量资源；81＝32+31+18，不把同一31case压缩原件的别名算额外样本。未测Runtime/端到端性能、Native回执或保存日收益。

Archive caller已做实际源码/编译核验，**完整FinanceEvidenceArchive.verify编排尚未实测**；不把共享helper/SDK绿冒作全Archive绿。该项明确并入紧接P111的public软件fixture bind→verify→originalRequest集成。v2 inline PlanningRequest仍有独立1MiB边界；不得裁归档全文或升旧cap绕过。P111使用既有64MiB FullMaterial CAS保全独立原bytes引用，旧v2规则原样保留。整个Construction其它quote层也不授通过。

最终证据：`D:/ck3-state/resume91-native-integration/p110-cash-context-test02/QUALIFIED-P110-SHARED-CASH-CONTEXT-ROLE.json`（16769B，SHA `6d1d096af86c9f8b6914b712f260186248402da8c14a18bc78917c29375b498e`），含原RED、两生产源、末Test/JUnit和关闭回执。原UNKNOWN/P100/Guard及冻结工作树保持；新增确认保存日0，持续目标仍active。
