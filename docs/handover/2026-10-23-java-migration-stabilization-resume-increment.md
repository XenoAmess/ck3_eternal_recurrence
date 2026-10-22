# Java迁移稳定化：跨日接续增量

观察截止：2026-10-22T16:44:57Z / 北京时间2026-10-23 00:44:57。machine_id: `xenoamess-full-tower-eb9d2c1186`。Root于16:44:19Z实际运行 `tools/ck3_live_run_id.py machine`，exit0读回该ID；来源为Root的实际tool观察反馈，没有杜撰独立receipt文件。

本文接续[10月22日15:09Z休假交接](2026-10-22-java-migration-stabilization-vacation-handoff.md)，原交接及旧失败保持历史。范围是正在进行的Java迁移稳定落地，未开新迁移；[日报](../autonomous-agent-progress/daily/2026-10-23.md)、[补录早会](../autonomous-agent-progress/meetings/daily/2026-10-23.md)与[小证据索引](../ck3-native-ai/evidence/java-migration-stabilization-resume-20261023.json)分别记录计划、结果和来源。

## 已变化的软件证据

| 项目 | 本次真实结果 | 信用边界 |
|---|---|---|
| java15完整注册图 | 1888项：1794 PASS、44 failure、50 error、0 skip；exit1/Job0；source与compiled-source均MATCH | 全图仍RED，不是acceptedBuildPASS或全部迁移完成 |
| wave2-runtime | 325/325 PASS；ClockReaderTest28项含7个真实canonical Python接收场景通过 | java14原7项failure保留；本次仅软件接收链，不等于Game恢复 |
| wave2-military | 754项中660 PASS、44F/50E，18个RED suite | mandatory producer goldens及Commander/HolyHire整数JSON节点断言仍待收口 |
| CI05完整cold step | 前5条通过；第6条 historical core源码_pin默认135168B拒绝143253B；exit1/Job0、source MATCH | 独立SDK第8条未达；不能拿局部或另一组通过补齐 |
| CI05的27文件组 | 227 PASS、91 subtests PASS、0 skip；独立完整命令exit0 | 仅该组，不能替cold/warm整step或SDK continuation |
| CI06 | 16:42:49Z小索引为RUNNING，session15945；compile/prepare PASS；仅core源码metadata pin调用窄设262144B | 尚无终态；D消费者后继patch当时未采用，不提前授验收 |
| tools21 | 实际build PASS/Job0/双source MATCH；Root已普通FF推送 `ee8d0787b14f038d020e1f9a92b39c600c1d3012` | 精确提交Official39815396090 RUNNING、Linear39815396065 SUCCESS；不称hosted全绿 |

java15构建终态16:36:24.593869600Z、JUnit观察16:36:58.775928900Z。构建用默认命令`mvn`，该机实报3.10.0；home只是带时间事实，不成为后继命令绑定。当前D-only候选、未注册wave2/wave3、源码Ready和采样PASS均分层记录。SDK supplemental只证明其精确范围；旧12381B shared fixture whole-module仍24 errors，13238B类型候选尚未采用/执行，不能写整模块全绿。

## 实际并行与资源槽

16:44:57Z紧接实际`list_agents`快照：**56个running子线程**，排除Root、6 completed、2 interrupted。其逐名清单在小索引；不是累计已创建数，也不是OS进程数。新增deadline_custody、progress_sync和native_fixture_execution只服务已开始的具体缺口；军事movement等完成叶从active排除。

源码工作保持互不冲突的有限并行。实际重资源由build/ci/storage独占调度：java15已Job0；CI06占1.5GiB CI槽；storage回报capture0，CI占用时最多1 capture。tools22首入口在Maven前因nested source/work-root guard拒绝，没有Maven child；其02后继当时仅RESERVED，未收到RUNNING证据。槽位状态按各owner小回执更新，不由56线程外推测试、采样或游戏并发。Git由Root唯一操作。

## 游戏与下一门槛

Game仍closed；AUTO11558结果UNKNOWN、不重放。canonical240为repair_required，pending5190 auto_unsettled、NEXT11559保持；旧未知10565/11386/11404不重发。保存仍5628/10950日，本次新增0，G2仍6/8；稳定30年、1秒/日及0.5秒/日未达。软件回归不补原FULL、SEM、SAVE或正常退出信用。

1. 收口既有共享生产链和mandatory golden，采用前核preimage/source pins；实际producer→全部consumer及序列化回归通过后再记接管。
2. 消费CI06真实退出、超时、Job及source终态；完整对应step和独立SDK continuation都必须执行。后继接线或fixture变化须对其最终版本完整验收，不借CI05局部通过。
3. runtime、完整CI和临时交易资格齐后，按原交接申请新nonce/期限SDK有限单读，全部Maven/CI/capture先停；同一JVM测量权威、真实reducer与原writer锁内事务不得被绿色JSON替代。临时交易、canonical提交、warm、attach、首FULL和成功SAVE分门验收。
4. 新受管Game前另取新鲜后台Steam offline回执。保原pending/T0/window/NEXT及冻结SDK，不热改，不silent fallback。新增保存日与完整墙钟到齐后才评价推进与速度。
5. 精确ee8提交的hosted终态由Root继续读取；旧commit失败保留，不能外推新提交。

本次进展代理仅做必要小文件读取与D文本候选，Z写入0、构建/测试/游戏执行0、真实Driver/SAVE正文读取0。D根`J/scratch/progress-resume01`的256KiB allocated+目录guard额度由storage纳入Root40MiB同池，20:00Z止、无新take；只保存小patch/索引，不重复厚manifest或旧原件。

## 01:19实际补录：CI08终态与读取范围事故

machine_id: `xenoamess-full-tower-eb9d2c1186`；实际补录2026-10-22T17:19:41Z / 北京时间01:19:41。本文00:44原观察与16:44拓扑保持历史，不把后续结果倒写进原截点。小来源与SHA见[本次证据索引](../ck3-native-ai/evidence/java-migration-ci08-read-scope-increment-20261023.json)。

| 后续运行 | 真实结果 | 尚未授予的信用 |
|---|---|---|
| CI06 | RED/exit1/Job0/source MATCH；第6条65项通过，第7条95项运行、5个子场景error；27文件227 PASS/91 subtests PASS | fixture的两方法投影缺真实requestloop；独立SDK未达 |
| CI07 | 16:49:35.799166300Z因容量遍历碰到已消失junit后代而abort124/Job0；4/30完成，source postcheck未完成 | 未执行SDK与27文件，不用后继成功补写 |
| CI08 | 17:04:43Z：30/30完整命令实际执行、CMD exit0；SDK第8条独立进程PASS、fixture-before-import；95 closure PASS、27文件227+91/0skip，source MATCH；outer465.9443484秒/Job0 | command23真实small-WAL诊断缺XAR_WAL_DIAGNOSTIC_ACTUAL_WAL及SHA环境而skip1，严格总态仍RED/outer exit1；不是全部用例通过，也未采用D endpoint |

Root已定位42506B真实small-WAL原件，补验仍待实际执行；本代理只消费小回执，不读取或切片原件。D cold/Prepared/warm/live endpoint图、typed monthly fixture整模块、军事34文件并集及SDK sentinel/endpoint、finance静态比较仍须各自最终source范围验收。

### 读取范围事故必须带入后续恢复

17:09:45Z `WAL-SEARCH-INCIDENT01.json`记录：查找时误对已知campaign根的*.json作过宽内容rg，随后停止。可能打开真实Driver；具体路径、次数、字节以及SAVE读取次数UNKNOWN。无输出不能作0读证明，事故不授SDK测量、恢复或协议单读资格。17:11:33Z补注已撤销整CI团队/整轮正文0读的总口径；旧0只适用于对应受控CI08命令和相应代理明确的时段，不能外推。后续新签读票须带入该UNKNOWN非资格读取事实，不能靠重读或hash追认。原回执保留；本进展代理本次实际Driver/SAVE正文读取仍为0。

### 百分比与条件时间表

以下来自Root本轮向用户报告的口径，非本代理新增模块验收：首29项的软件验证16/29≈55%；java15实际1794/1888≈95%；runtime325/325，tools54/54。模块、测试项与生产接管分母不同，不能汇成“全部迁移95%”或实机恢复百分比。军事44F/50E、Game closed、UNKNOWN11558不重放、保存5628日与G2 6/8均保持。

| 北京时间2026-10-23 | 条件目标 | 继续条件 |
|---|---|---|
| 01:30 | 恢复代码与新CI结果 | 最终源码、真实退出和未执行项均有证据 |
| 02:30 | 首29项集成 | 真实producer到全部consumer、注册图及完整所需检查完成 |
| 03:00–04:00 | 有限SDK恢复 | 新nonce/期限、有效容量、所需槽全停；UNKNOWN不重放；测量/reducer/原writer锁内重验分门 |
| 04:00–06:00 | 本轮目标收口 | 前门已满足，使用届时有效期限/容量；原20:00Z额度不自动延至更晚 |

时间表是条件目标，不是保证，也不以赶点跳过真实资格、warm/attach/FULL/SAVE或未知结果守卫。成功SAVE前新增保存日仍为0；不因纯软件结果评价游戏速度。

### 02采用失败与03真实检查门槛

Root已将01 `git apply --cached`入publisher索引；对02的真实`--cached --check`在README.md:1及weekly/2026-W43.md:1失败，02未应用，原02保留。先前纯文本顺序PASS不能代替Git采用检查。03只读publisher的真实`git show :目标`重制，未修改index或工作树；须以针对当前index的真实只读`git apply --cached --check` exit0及交付回执为采用门槛，由Root实际apply。
