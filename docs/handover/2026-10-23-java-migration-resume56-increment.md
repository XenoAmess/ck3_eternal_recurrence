# Java 稳定化续行增量（2026-10-23）

本轮承接 [休假交接](2026-10-23-java-migration-stabilization-vacation-handoff.md)，依据用户“阅读交接文档，继续执行任务”及随后恢复56并发的指令继续施工。休假停止调度是历史边界，不再据其停止新工作；冻结来源、未知动作不重放、独立审批和存储准入要求仍适用。

`machine_id: xenoamess-full-tower-eb9d2c1186`。北京时间2026-10-23，本文时间均为UTC。`J = D:/codex-ck3-demos/2026-10-22-java-phase1`。本轮先分配56个子线程按模块工作；分配数、当时运行数及重型进程并发分别记账，不把完成线程计为运行并发。

## 新鲜机器、容量与来源

- 原生Windows Python及Java共享机器身份读取一致，默认命令行 Maven 为3.10.0，Java为21.0.10。观察到的 Maven home 仅是该时本机事实，后续命令继续使用默认 `mvn`。
- Cygwin 的裸 `python` 是POSIX解释器，缺machine-id后退回hostname摘要，产生不同ID `xenoamess-full-tower-cbe08df9e8`。它不具备Windows MachineGuid身份资格；本轮机器准入明确使用已核原生Windows解释器或现有 `WindowsJobProcess.currentMachineId()`，不按截断的COMPUTERNAME推断。
- 新准入原件：`J/logs/RESUME56-CAPACITY-RELEASE01.json`。19:52:42Z，J加六外源原生allocation与目录guard合1,505,615,320 B，全部0error/0reparse；原两financial heads精确MATCH。原D4GiB、scratch512MiB、Z32MiB同池，新增take=0。source8MiB及新源快照29MiB+metadata2MiB均计入原池。
- 新窗口至21:52:17.501144300Z，不修改旧20Z卡。`RESUME56-PARALLEL-AMENDMENT03.json` 在20:01:19Z新鲜核验后分别准入static07 1.5GiB、物化256MiB、tools25 Maven2GiB加outer384MiB，合4.125GiB；Maven仍唯一writer。各链必须消费真实退出码、超时及终态Job0。
- Z工作树保留原有未提交成果，不reset/clean或全树add。既有发布隔离树为 `J/scratch/java-publish01`；先前8282d8da3包已进入远端祖先，不能重复发布或将旧Z ahead/behind解释为未交付。

## 完整34文件实际回归

新执行真实RED：41 parent为40 PASS、1 FAIL；subtests为6 PASS、5 FAIL，skip0。compile PASS、内外Job0、来源前后MATCH，峰1,110,646,784 B低于1.5GiB。

单一入口 `J/artifacts/coldwarm-resume34-01/TERMINAL-INDEX01.json`，SHA256 `af28198289765fd748445bf432e181b98c82c1d3e2612fc92fca6f6d25b7cc1c`。原actual不改；初版summary把聚合6失败误写为parent失败，索引明确纠正parent/subtest两层，不能借统计修正改写业务RED。

唯一parent失败是soldier夹具错误要求11字段核心缓存保存全部raw扩展；真实query结果仍保留raw。修复进入 `static_callback_soldiers` 唯一外置候选，保留result原raw断言并对缓存精确key集合与值校验，不改Python生产算法。

七份既有RED测试夹具已各自生成外置强类型候选，尚未整体采用；`ci_static07` 顺序执行完整模块Python3.13 strict检查。首个MCP模块从旧17错误缩为1个真实RED，已交原owner补正；其余实际结果待续写。后继运行覆盖34核心加MCP watch、Holy reinforcement两整文件，明确共36文件，不以局部测试或AST代替。

## Java29源图与后继边界

原partial保持1451文件/prefix545不变。独审863次显式引用、595个文件全部bytes/SHA MATCH；剩153原阶段加33 extras的严格链仅发现0546重复CODEX section。最小规范化按preimage位置重排原hunks 1、2、3、5、4并合单节，保留原post `19980 B / a2483d1c02c42c70b258e08d3b51b87f09d7c93b32219fcc9fe33e51bad36afd`，不放宽patcher。

新执行根为 `D:/codex-ck3-demos/2026-10-23-java29-source02`，不能写原partial。先独立copy及fresh pinned snapshot，再续行153+33与Java19四源。1521文件/18,758,300 B只是静态投影；真实物化、native identity/linkCount、严格SourceManifest、编译与capture仍需分别记录实际结果。

最终图相对Java19有六个有意overlay：四项29模块图配置、StrictJson新增child数值profile、DeadlineTransport领域拒绝。即便恢复四源和tools24 src30全匹配，也不能称整个Java19闭包逐字节相同或继承实机资格。

本轮发现的事件after缺失/null混淆、interaction错误布尔token分类、Budget身份及int溢出、measurement读取后时效/身份复验、stock probe重编码opaque浮点等问题，各在新外置Java后继候选处理；旧698 pre/post及原golden保持不变。候选源码、实际回归通过和生产接管分开记账。Owner V3与sharedwire仍须统一字段权威、完整闭包绑定、真实HTTP与所有消费者验收；不能仅凭字段/SHA形状放行。

## 尚无新实机成绩

本轮未签发真实Driver/SAVE新票、未启动SDK恢复或Game。head240、repair_required、pending5190及AUTO11558未知仍为交接中的历史事实，未追认为当前新观测。保存成绩仍5628/10950日，本轮新增游戏日0。

团队历史Driver正文检索聚合仍UNKNOWN。另有子域一次cmd引号错误造成普通仓库bridge/tests宽文本检索，其可能读取正文次数/字节同样UNKNOWN；不能以其他只读子域0外推团队0。新检索限定显式源码/候选文件，原运行态Driver/SAVE不纳入普通FileRef或广域搜索。

本文是进行中的结果增量，不表示全29、全部消费者、SDK恢复或实机通过。后续真实终态将追加到同一工作包。
