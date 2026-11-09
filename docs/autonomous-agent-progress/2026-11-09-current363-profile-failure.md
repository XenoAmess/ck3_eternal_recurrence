# P192：current363首次完整profile在原deadline处失败，保留原件且不重试

当前离线软件363的首次唯一完整APPLIED／JFC软件case真实 **0P／1F／0E／0skip**，没有通过本次fresh profile验收。testcase **145.481s**、Jupiter suite **145.505s**，实际exit1、timeout=false、原HANDLE终态后fenced／released，所有slot释放。**Utility为0，失败raw永不解码／重试**；不改heap、settings、业务120s deadline、输入、oracle或旧P153缓存，也不拿本次失败归因P190等某个已接受源码。

这是离线软件失败记录，不是Game／Runtime操作或SAVE。current363既有有限源码／软件资格仍保留，未自动切回旧组合；源码接受、软件基线、此次完整case失败、Git、Runtime与保存分别记账。零新增确认保存日，秒／新增保存日为null，持续性能目标未完成。

## 精确失败层及原范围

原cached P153 ConstructionFullProduction113Test#fullFuturePlanRunsActualIntentEffectColdVerifierAndFullMaterialPublication，source38984B／`815f2d214d823af324f1034f35ea286c9a98573b0c3c43d1dbbfcc195dec72f8`及其10个class原样复用。工作负载使用实际363有序classpath／166项critical来源及原named输入，输入POST不变；没有任何生产、旧Test、Main、SDK或Tool编译，没有暖机、额外case或补采。完整来源pin不是动态loaded ClassSHA或全C0源码授信。

失败位于原Test182的MaterialAvailable断言，实际返回 **OrdinaryConstructionCollector.MaterialMissing**，原懒reason为：

`current material observation rejected: caller readiness deadline expired before any native query`

reason_chars=96、reason_truncated=false。原material_deadline与command_deadline同为 **2026-11-09T15:40:42.100940700Z**，failure_utc为 **15:40:47.202134400Z**。原断言未改；完整type／message／stack与XML原件保留。此准确说明读材料时触发caller readiness的查询前deadline层，**不等于已找到为何前序耗尽时间的唯一根因**，也不证明某生产源码造成性能回退。

原软件case此前已经经过选择command、执行与若干原件／history／outcome检查，但最终完整case是1F，不能把前缀成功写成整体1P。保留首次失败，不延长／刷新旧deadline、不新建命令、不伪造ACK／Guard／UNKNOWN许可，不弱化物理读取、hash、回读或解析验证。

## 失败raw与未知采样范围

保留原raw **9074310B／`ed4a016ac2eaf508b2d8a0cf18de18fe7c8110ed85c6f49ada50ad09b8ed15cf`**。Native只持四字节JFR magic `464c5200`及有限文件尺寸／SHA；没有读取header完整chunk、事件EOF或调用轴。Tool／utility JVM数为0，derived为0。事件数、settings实际生效、DataLoss、stack截断／缺失、allocation权重、应用轴覆盖全部 **UNKNOWN**，不能从旧P182成功报告、83partial轴或P185堆栈拼补本次结果。失败raw只按原件保全，不作为后继工具输入；旧P152失败raw也不触碰。

保留的raw／JFR repository采样峰值各9074310B在原12MiB／20MiB帽内，derived0在8MiB帽内，metadata采样峰值1163940B在4MiB内；原sampler coverage_errors=0只描述该软预算观察。final metadata **1503934B**（最终capacity文件前1502969B＋该文件965B），guarded fixture **31393527B／333文件**在原64MiB内。JNA、其它tmp／classfiles／日志／错误件仍计metadata，没有移动分类以规避cap；采样峰值与保留静态逻辑数都不授连续硬峰值。

## 全部资源费用

唯一workload actor **150.2998753s**、phase operator **151.9049364s**、whole operator **152.0494197s**仅子窗。最早已持source checkpoint **2026-11-09T15:28:02.794632Z → 最后CLOSE765.854215s → qualification937.000176s**；CFG checkpoint15:34:26.508362Z到CLOSE382.140485s是内窗，不相加。更早真实研究起点UNKNOWN，不记0；source-only准备、旧schema 0VM错误、更正、软件采用等待、审阅／授权／调度、冷启动、observer、JFR dump、失败及tail全部保留，后继源码调查／文稿／Git费用继续另记，不能拿150s冒整任务成本。

原owned child HANDLE lifetime149.5979127s；kernel CPU57.09375s、user CPU31.578125s是该实际子进程OS记录，whole parent CPU仍UNKNOWN。observer自身thread CPU15.25s、scan elapsed26.567432s与子进程墙钟重叠，不能减掉或相加；最大观测gap0.4053781s亦不补齐未见区间。OS peak working set **567459840B**、pagefile **575180800B**不是Java heap peak，更不是候选程序全局内存／CPU归因。未新增OS／模块／Game查询补缺口。

## P193：仅现有日志及源调用链收束

后继只读调查使用原Test和已保留的14条业务at_utc、7条单调诊断行，不解码raw、不再运行JVM。Test97创建PlanningRequest的120s deadline，130检查command沿用；177–180的materialRequest仍使用同一command.deadline。创建后有evaluate、原件resolve、execute、history发布与coverage、冷verifier和outcome同步等阶段；每个阶段保持原Guard／来源职责。

现有事件#7末初始导入 **15:38:40.7131083Z** 到#8 INTENT域导入 **15:39:29.5073013Z** 的相邻最大间隔 **48.7941930s**，不是某方法self耗时。之后#9 INTENT_DURABLE15:39:32.2239649、#10 SUBMITTING15:39:36.9073882、#11 ACK15:39:44.1288056、#12 SETTLED／APPLIED持久15:40:01.6942148、#13 history15:40:10.9918176、#14 outcome域15:40:19.5707442。receipt observed15:39:44.8893385与持久事件另账。

#14到原deadline剩 **22.5301965s**，到failure为 **27.6313902s**，failure晚于deadline **5.1011937s**。没有细粒度日志将该区间拆成方法耗时，mtime、业务UTC与单调日志域也不能混作同一精确调用钟；observer费用不被从失败墙钟剔除。

源码优先核Test172 synchronizeOutcome→173独立domain.read→177新currentOwned→181材料registered read：Life.read每次真实session.readDomain、一次canonicalBody decode及requireRetained；canonical比对received与surviving-chain新lookup的actual两份独立编码；原verifyArchived不返回可复用typed结果，不能通过新桥或跳验证省掉后续load；新的currentOwned与后继材料查询分属关闭后的独立观察scope。没有找到可直接删除的同call不可变大对象重复纯计算，**BOUNDED_NO_DIRECT_CANDIDATE**，不是全算法不可能或成本0。两次模块路径猜错的0VM只读错误与更正／未采用输出另留D原件，不当作Java RED或本次deadline故障原因；没有新Source、Test、CFG、VM或HTTP。后续独立候选不混本facts包。

可核原件：`N/p192-current-integration-profile01/QUALIFIED-P192-FAILED-WORKLOAD-UTILITY0-THIN01.json`9215B／`1c7034e15ea7da6da6a04c6af38c1c1a1e43b5408976206802701894ad2615ca`；完整失败7348B／`224d8c4d7e1a95612c304216fc7dd3af5823de275f35204e4395772fe0296c40`；Jupiter XML47743B／`72a8417d2df69868ce3bad9a8d10207180af0cec25673fa0e5ed8421401a4df1`；`R/P192-FAILED-THIN-FINAL-INDEPENDENT01.json`871B／`66b0a41458f9bf44f56d691ea6bf73c417684316e0c1b2014275744762765814`。Root核19个独立原件及真实1F／utility0／释放；`R/P193-EXISTING-TIMELINE-AND-UNOBSERVED-GAPS-INDEPENDENT01.json`1290B／`94bf00a790bea225cc4f492142e73783442085b126fc0ff36ab2b0996fc1261e`独核现有时间线；`J/construction-material-deadline193/read-only01/RESULT01.json`3941B／a7bec7a5…及source-index4527B／23831aad…。N／R／J为隔离证据根，本文不声称新读取raw或完整CPU／来源资格。

exact3只新增本unit并追加事件发生日11-09的daily／W46，旧正文保持；无Source／Test／Tool／AGENTS／CI／pom／运行文件变更。后到本地日期跨11-10不改原失败事件日期。继续性能主线，不把失败结算或文档发表当完成。
