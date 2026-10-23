# Java / G2 继续执行记录（2026-10-23）

承接 [休假交接](2026-10-23-java-g2-stabilization-vacation-handoff.md)。用户已明确恢复执行，并追加要求维持56条智能体迁移子任务，G2八个M全部基于Java继续研究、同时继续原版AI挖掘和智能体优化。2026-10-22T23:00Z后已实际登记56个独立子任务；研发并发与受资源约束的JVM/Maven/实机调度分别管理，不把等待数或源码量作为完成成绩。

`machine_id: xenoamess-full-tower-eb9d2c1186`。本轮重新执行 `tools/ck3_live_run_id.py machine`；命令行默认 `mvn -version` 实读3.10.0、Maven home `C:/apache-maven`、JDK21.0.10。这些安装路径仅记录本机观察，不作为执行规范。`J=D:/codex-ck3-demos/2026-10-22-java-phase1`，`N=J/scratch/resume-current-20261023`。旧撤回卡不复活；新SOURCE02与Runtime01有效期至2026-10-23T00:30Z，原4GiB包内登记，其他任务预留继续保留。未启动新Game，未读取实际Driver/SAVE正文。

## 已验证并纳入本提交的修复

原生产者窗口包含独立的 `stable_source_identity`，共享Java `MandatoryChoiceCodec` 曾将它作为未知字段拒绝，使四个真实UIRecovery/SourceReviewedMandatoryPlanner向量变成 `query_malformed`。现在共享record和codec明确保存该可选对象；它与 `source_identity` 各自保留缺失、null和空对象语义，序列化回环保持原内容，字段不授予选择、重放或业务后态资格。新增默认JUnit覆盖独立字段、类型拒绝、完整回环和零动作信用，沿现有event-policy Maven/CI路线执行。

本机完整选定M2图重新严格编译168源，产生505class后封装唯一新JAR；随后标准JUnit运行原37类，加必要边界回归共450/450通过，0失败/跳过/中断。三步outer0/child0/Job0，所有输入pre/post及runtime MATCH。原444/5与本轮失败证据均保留。本提交只采用主线已有event-policy的三个文件；完整M2图、wrapper、SDK和真实HTTP仍需后续完整图采用与验收，不能将450测试外推为主线已部署全部M2。

资格：`N/g2-m2/M2-QUALIFIED01.json`，27400 B，SHA256 `3572101a6ce6d8cfae4e7004ecbfa5f3078797c82aec66d56f17eb2ce52da55f`。完整JUnit终态：`J/build/resume-current-20261023/g2-m2/m2_repair/junit-full01/terminal.json`，188728 B，SHA256 `8b33a9a0de92229d38e365df831b9e47947fdd5ce30231645a59b133f7f6ec5d`。summary为3551 B / `a017bef640f3673b57f86e9fc4559d78722788283082f74bcd347e78066df30f`。

## 同轮已完成的软件证据，尚未据此声称采用

- tools27同37源在新窗口完整Maven验证140/14，0失败/跳过/错误；outer0、Maven0、Job0、双source MATCH。`J/logs/build-java-tools27-window03.json` 为26097 B / `85e0a68fe260e5c63ab6af621ef0d754011c13d9dae541a8cf2373036eb6ee26`。新整包reader真实通过，完整六件闭包不混类；shared caller09严格编译、长路径、timeout124/Job0、输入漂移未起child和精确Python调用通过。
- M0机械兼容类型修复通过严格Java编译、90原消费者、58次Java往返及证书回环、legacy5次Java调用、实际生成shadow的整模块strict/strict-equality mypy。资格 `N/g2-m0/M0-CURRENT-QUALIFIED02.json` 为11035 B / `06fc580e7874f4eecddeb693d984cf6b1af484e9fd7b3f856764252c1009bcad`；不外推未改R旧模块、完整Maven/HTTP/SDK。
- Java29 source03正式独审真实通过：1524文件、9替换/3新增、29子模块/30reactor、29负例及严格回环；outer0/child0/Job0。`N/source03_audit/DELIVERY01.json` 为6990 B / `fb4a235ed0ebe997e708c7e4b6e54b02ab8be84c63e07732b04930f3b9e61ae0`。随后capture03实际RED：outer1/Maven1/Job0，双source MATCH，20child SUCCESS、3FAIL、6SKIP及parent SUCCESS；90.1909169s，峰624517120B，tests NOT_RUN、无部署/编译manifest。原件 `J/logs/build-java29capture03.json` 为949696 B / `9d54eb7a4068bff6b6916fc6689226cc6728917e919be56dac329f470454b577`。三项测试源码合同修复候选已定位，原source03不热改，进入新完整图统一采用与验证。
- M7真实34源严格编译、33/33标准JUnit、gov215/goal88/calendar15报告与13份原producer HTTP fixture已交宿主。`N/g2_m7_java/QUALIFIED-DELIVERY01.json` 为6423 B / `0b59fbcdbf47693eec63d0a5dda88f8b2c6a3764f7f4e1459d7fc2de63325b98`。新sharedwire与调度后继不由旧结果追认。
- M4增编及3/3标准JUnit、四份实际原producer HTTP字节导出通过；`N/g2_m4_java/DELIVERY01.json` 为16689 B / `b66c5cba032a2d9e89720fb1037d86eaf6d635d8e3148eb2b1991a7dd3dc9bf7`。完整Maven、同宿主HTTP与SDK另验。

## 正在推进

完整Java29 capture、缺失军事/融资原始fixture、合并后的tools/Host/SDK完整资格、同一Quarkus宿主八域HTTP、现有Python消费者与独立SDK continuation均按实际新图继续。原版AI八方向与缓存、索引、生命周期、计量优化各自保留来源绑定和采用边界；研究候选不得计为实机能力或秒/日提升。

保存前沿仍沿交接5628/10950日，当前新增保存日0；UNKNOWN动作不重放，原T0不重置。本文是滚动执行记录，非任务完成或实机恢复授权。当前必要源/原始失败保留按通用策略限期复核；compact记录180日复核，不默认为永久保存。

用户07:19北京时间询问百分比与实机时间。本次报告按明确分母区分：本轮M0/M2两阻塞2/2关闭；八M基础Java实现/实测覆盖8/8；新统一宿主八域整链0/8；本轮Java新实机保存0；原有G2历史能力6/8。首轮Java实机目标北京时间09:00–10:00，08:00前收敛首个整合包，08:00–09:00执行完整软件/SDK链与恢复预演，08:30按实际结果更新预计开测时间。此为计划而非已取得启动、恢复或业务资格。

## 09:00 进度与实际阻塞补记

`machine_id: xenoamess-full-tower-eb9d2c1186`。以下为本轮已读回的本机软件结果及随后补记，覆盖上段已错过的计划节点；观察时间与后续状态以原始回执为准。56个研发子任务已按实际依赖收敛为14条端到端工作链，已完成的叶任务按真实缺口再唤醒，不以等待或重复运行充并发。

- 新tools88/source04完整Maven实际通过293项测试、34套件，零失败/错误/跳过，Root outer0、Maven0、Job0、双source MATCH。`J/logs/build-java-tools88-firstcut04.json` 为56361 B / `089b26b85f55708c9630d198c76a00223bfec3e679beef921563adf4135304e8`。新JAR自身读回通过，并实际验证旧source03回执可作为历史构建证据，过期旧租约仍拒绝授予本轮执行权；不是通过重建未改源码来续期。
- Plan09实际选定1931文件、26039106 logical B、30子模块/31项目。修复五个共享来源后补入漏选的原M2三项HTTP测试；这些HTTP测试尚未执行。完整新宿主八域HTTP仍0/8。
- 首次整图复制真实RED：1931文件和1198目录被共享ordinary walker合计3129项，误与2304文件上限比较。外层/child退出1、Job0、输入与runtime MATCH；实际native含目录guard34815432 B，低于36MiB。失败源根与空metadata保留，没有补写原复制前见证或伪造actual receipt。修复必须落到共享扫描器，分别控制文件数及有限目录遍历；旧1536文件合同不放宽。
- M0三个完整兼容模块及continuity两个完整模块已通过带2004项完整来源清单的严格静态检查。完整transport两模块另查出14个真实类型错误，修复使用独立后继，随后whole static与53项功能回归通过；原首切源码保留。完整55项适配测试、实际宿主和完整SDK仍另验。

本轮口头百分比仅按用户要求的明确分母汇报：两项初始阻塞2/2；八M基础Java软件证据8/8；tools04测试293/293；完整宿主八域HTTP0/8；新增实机保存日0。G2权威JSON的历史6/8状态未据软件成绩改写。

首轮Java实机目标已调整为北京时间10:00–11:00争取窗口，尚非确定开测时刻；先争取Java地图回执的实机纵向验证。完整SDK、真实Native接续、原writer锁内reducer和业务后态未通过前，不报告已恢复自动游玩。2026-10-23T00:46:10.419426Z后台Steam probe实际为offline/true，回执`J/logs/STEAM-OFFLINE-JAVA-PREFLIGHT01.json`；正式启动前仍须重新取证，不复用此旧观察。

当前SOURCE/Runtime新窗口至2026-10-23T02:30Z，原4GiB包内重分且新增take0。tools88依赖完整G2的CI入口，不能只覆盖现有主线9子模块后声称可以发布；完整新图验收后再整体采用。原失败、旧计划和时间记录保留，当前必要输入按通用存储策略限期复核。
