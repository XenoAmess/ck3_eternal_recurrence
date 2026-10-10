# 2026-10-10：当前机器自行重建公共运行时

用户确认 `C:/workspace/ck3-upgrade-20261008` 不存在，并要求不依赖它。本次从本机已跟踪源码构建、固定一份供全部产品共用的 manifest，没有等待该目录，也没有回退产品专属 host/native。历史缺件和失败报告保留。

本机 CK3 为 1.20.0.4，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。正式入口仍为 `tools/ck3_mod_acceptance.py` 的六种模式。

28项实际输入、输出、索引和生产器已逐字节归档：[INDEX](acceptance/2026-10-10-local-common-runtime-rebuild/INDEX.actual.json)、[归档复验](acceptance/2026-10-10-local-common-runtime-rebuild/ARCHIVE-VALIDATION.actual.json)。完整源码 ZIP 和二进制保留外置，仓库保存它们的字节/SHA。

## 实际构建与共享源码

第一次冻结 Source01 `5e2f65740a28dd5df34ffa59862a47030048a1b3` 的构建失败于 MSVC C2712；[共享修复](2026-10-10-religious-title-seh-compile.md)将纯 SEH 调用与含 RAII 的逻辑分开。Source01、失败日志和输入保留。

Source02 `af20455212ed75000ba6136b3be308a9288cb06e` 在 `C:/csr2`，实际 build 在 `C:/cbr2`，公共 DLL/injector 编译链接返回0。特性开关从本机已知真实基线取得并加入公共 frontend rules；完整定义、编译工具和索引位于外置证据，不据此宣称所有产品能力已通过。

| 产物 | 字节 | SHA-256 |
| --- | ---: | --- |
| `xar_ck3_bridge.dll` | 9459712 | `390506e486f5b19e298070523360d420de255a7811b5e79a5b279d5f9331dbbe` |
| `xar_ck3_bridge_injector.exe` | 39936 | `2e22a985ba3166ce50ca1732901f0bac0629e8ff0f068de73330fdd5d09c86a8` |

Source03 `13d063c81ff706d8bc3f9a8bf81f60c283338042` 在 `C:/csr3`，增加[固定保存中已有事件的只读启动检查](2026-10-10-saved-startup-event-admission.md)。与 Source02 全文件比较共有6项变化；native_bridge 下只有 host `.py` 改变，所有其他 native 目录文件逐字节相同。因此沿用已编译 Source02 产物，保留两份完整 source/native 索引和实际比较，不宣称重新编译 Source03。共同运行时固定这些显式输入，不随其他 master 工作包自动改版。

`C:/workspace/ck3-common-runtime/20261010-002/manifest.json` 的 SHA 为 `275bd7bdb8b44e72340e4fb77cc238f43a50dabd532d64f93916d3d0380be51c`；本机映射 `runtime.local.json` 的 SHA 为 `36e880a0784458fd54c3740c0cf69fcccb66cc3e1ca87a82571dba852482660f`。公共 host、source、DLL/injector、Python imports、launcher、队列、keeper 和已安装 task-bus 均绑定精确字节。能力表只授 source/build-ready，`actual_live_qualified=false`。

## 首次本机准入与事务对照输入

[首次本机 bootstrap](../ck3-mod-acceptance-first-machine-bootstrap.md)实际 bundle 已固定。真实只读检查通过：绑定当前 OS MachineGuid 派生 machine ID、canonical ID 历史、八份 R38 原始闭场证据、归档 INDEX、当前实际 bus list 和 durable 4188→4189 释放链。没有借此将 R38 追认为公共运行时或完整事务对照。该检查未分配 ID、创建 ledger 或领取屏幕。

《礼与道》新增 `transaction-only-control` 产品 case，只有 fixture/data/adapter；host/native 选择仍在全局 manifest。正式71文件与原固定 `06159b964d859d30f2f07f4b183284df7d6dac47` 的正式 staging 逐字节相同，诊断覆盖6文件单独挂载。外置 seed 是原 R34 D2a，91711686字节、SHA `a6db85e38ba0648eca4b7e835c79d867b96ca26099698f4d4ee5269b818d822c`。actor/root31254、date_raw53144712、原事件121均固定；真实 typed saved scope 名是 `new_title`，title18373。

四份配置中 `pdx_settings.txt`、`tutorial.txt` 使用 R38 原字节；旧现场和当前 Windows Documents CK3 目录均没有两份 presets。新 fixture 明确创建两份零字节“无自定义预设”输入并保存来源说明，不伪称历史复制，不改变存档及其中的游戏规则。seed 留在外置输入路径，准备 profile 的 saves/logs/run 保持空。

新 case 仍使用既有公共预算 command300/readiness400/timeout2100/hold900/poll0.5；没有延长旧 held 会话。只选择原 D2b 选项一次，以真实终点事件、完整有序45人缓存、resolve 后持久化数值标记、未授封18373和七个政治头衔完整 AST 为证。此对照不授正式 I3b/C3/I4 或整体验收通过。

## 已知边界

构建原始回执的 Defender hook 为 `disabled`：冻结源码没有主仓 Git-local opt-in。随后从已成功构建的真实 CMake codemodel 仅登记新增 injector 精确路径；实际管理员 WMI Add 返回常规故障，读回仍缺该路径，终态 `settings_failed`。未重新 build，DLL/injector 字节保持固定。原 disabled、dry-run仅需CMake glob regeneration的保守停止和实际失败回执分别保留；不能外推旧238路径或称新路径已永久排除。

`af2045521` 的 Official CI 失败于新增无害子进程测试缺少可选 `psutil`；[原失败及修复证据](acceptance/2026-10-10-shared-local-launch-static-dependency/REPORT.md)保留。修复只隔离可选创建时间查询，真实 Popen/wait/退出码7检查仍执行。Linear 通过，LiYu 未触发；不把未触发写为通过。

公共 `prepare` 实际 exit0，完整 profile 为84文件（79项 mod/outer 加四配置、dlc_load），seed未写进 profile。公共 `preflight` 实际 exit0，状态 `READY_FOR_EXISTING_REVIEWED_LAUNCH`；包括安装游戏 SHA、共同 host CLI、固定保存、startup handler/data、adapter 和 native pins。[12项准备和预检原件](acceptance/2026-10-10-local-common-runtime-rebuild/PREPARE-PREFLIGHT.actual.json)另行归档，前28项历史归档不覆盖。原未准备 `plan` 的6项 unbound 阻点及 exit2 也保留，不改写旧结果。

截至此版记录，公共运行时为 **BUILD_READY / LIVE_NOT_RUN**。新实机仍需当次实际无占用检查、唯一 ID/屏幕租约及新鲜 Steam 离线原图亲审；不能由 manifest、bootstrap 或 preflight 推导 live GREEN。事务对照和正式 I3b/C3/I4/整体验收未通过。

## 04:07 CST 后续：R39 已实际启动，启动检查 RED，现场已释放

上节 `LIVE_NOT_RUN` 保留为启动前记录。本次公共入口已实际分配并启动 `bf-202609141645-5434332d4d--li-yu-dao--R0039`；owner checkout 固定为 `00b88fc4df0b8b4cea8b15ff85de8f244825a329`，仍消费上述同一全局 manifest 和 Source03。首次本机 bootstrap 已消耗，后继不得重复 bootstrap 或清理 machine admission ledger。

公共 `run` 实际 exit2；host 的固定存档检查在原400秒 readiness 预算内超时，最终原生报告 RED。146份观察均未取得就绪地图、玩家角色和当前事件；日期53144712及暂停状态存在，query mailbox 在工作，但 `map_ready=false`、`played_character=null`、`local_player_id=0`、`active_event=null`。原守卫逐件只读重放与保存的 `frame=null` 一致，尚未进入 campaign-root 查询或产品启动 handler。`steps=[]`，事务选项、业务保存及天数推进均为0；不能据此判断事务或继承缓存的业务结果，底层未提供完整快照的原因继续排查。公共 `verify` 实际 exit2，保持原失败，未制造成功 case 记录。

host 原 Popen wait 返回1，CK3 受管退出码为1；native job active0、进程树消失、三路最终清点均空、控制文件清空，managed session/thread/cleanup 已结束。这证明失败现场清理，不授正常退出0。最终新鲜1920×1080原图亲审 Steam“离线模式”，原桌面1024×768×32@60实际恢复；keeper 原父句柄退出0、线程已结束，CAS4221→4222实际 done/resources=[]。首次释放因缺少 CLI SHA pin 被拒，补全精确 pin 后释放成功；两份原始回执均保留。[R39 原始证据及诊断](2026-10-10-r39-shared-runtime-startup-red.md)另包归档。

精确 `00b88fc4d` 的 Official CI 已到失败终态，原因是既有 allocation 测试的模拟 `ids` 缺少新机器绑定接口 `MACHINE_ENV`；Linear 通过，Li Yu Dao 未触发。该 CI 夹具修复与原生快照只读诊断并行，生产 allocator 的机器绑定、原现场闭场和唯一 ID 守卫保持。正式 I3b/C3/I4 与一期仍 **NOT_GREEN**，上一工作量估计不因构建、闭场或 CI 修复上调。

## 下一场启动预算与已完成 CI 夹具修复

实际日志精度为1秒。R38启动后185.147秒记录Load Save、228.147秒 powerful vassals、331.147秒 In Game、417.147秒 Setup completion。R39原进程创建后对应前两阶段为240.764及299.764秒，在401.928秒结束前没有后两项。R38是历史独立launch再attach，没有保存同类startup budget字段，不能追认为旧400秒通过。R39的400来自新case复制通用LiYu配置，不是业务谓词。两轮日志及精确来源行已纳入R39原件归档。

仅未来新场的 `transaction-only-control` startup readiness 改为600秒：以实际R38完成417.147秒、R39前半段额外71.617秒为依据，约489秒历史参考加约110秒余量。command300、timeout2100、hold900、poll0.5、终点60秒及正常退出reserve90均保持，host/native、seed、正式71文件、六项overlay与业务谓词不变。这不保证加载成功，也不延长已结束R39或追改其RED；未来必须全新profile和ID，常规前驱闭场准入。

[CI窄修](2026-10-10-common-allocator-ci-fixture.md)已完成，34项相关回归通过：adapters9、bootstrap10、entry15；生产allocator/ID工具逐字节不变。旧00b88fc4d失败保留，后继精确CI需另取实际终态。

## 05:00 CST：R40 仍启动 RED，600秒没有解决加载问题

普通fetch/rebase后的 `598d4855b1a5e7678fa2253e5664acb991c0c825` 已实际推送，接入远端失败启动清理更新后54项相关回归通过。该精确提交 Official Runner CI 37988052013 和 Linear 37988052148 均实际success；Li Yu Dao未触发，单独保留。[原始CI及本地回归证据](acceptance/2026-10-10-exact-598d4855b-ci-and-rebase-tests/REPORT.md)含190项原件；本地旧回执没有独立HEAD字段，不补造其绑定。

新profile公共prepare/preflight均exit0，常规R39闭场准入实际分配 `bf-202609141645-5434332d4d--li-yu-dao--R0040`，未重复bootstrap。固定原seed、正式71文件和六项overlay、同一公共host/native，readiness600。run/verify实际exit2，host再次在原始本轮预算内超时，steps=[]。413份观察中前363份map_ready=false，后50份已map_ready=true/local_player1/actor31254/date53144712/event121，但后50份准入帧的pump_epoch均27770，未通过第二独立owner帧推进守卫，campaign-root查询和产品handler仍未进入。日志进入InitPostRead和缓存重算，04:51:05到powerful vassals，至04:56:15结束无In Game/setup completion，error.log仍0字节；日志缺完成行不能覆盖原生已map_ready的事实。此结果证明本次600秒预算没有完成准入，不增加或重跑业务动作。[R40永久记录](2026-10-10-r40-shared-runtime-startup-red.md)保留全部实际输入和失败。

原host/CK3退出码均1，managed session/thread/job/tree/最终空清点及控制文件清理完成，normal0未取得。新鲜Steam原图亲审离线、原1024×768桌面恢复；keeper原父句柄退出0/thread joined，CAS4234→4235实际done/resources=[]。当前无游戏和屏幕占用。下一步核两帧绑定、采样/更新链及实际启动路径，不再次仅增加预算；尚无已验证的底层修复。正式I3b/C3/I4与一期仍NOT_GREEN，工作量估计75%保持。


## 2026-10-10 07:31 CST：Source04已交付，R41未到延后注入点

共享默认OFF的same-PID加载后单次注入修正已主线rebase并普通推送为6a3affdb87f03f01bdc9f4dc43aeff15960200db；接远端关闭流程后48项相关回归PASS。固定Source04为919bae0f42def04e6398eb2de4b4afe20dcfc106，单父13d063c81只应用作者1d4468fc五路径Python增量，原生目录仅host Python变化，其余逐文件一致后复用cbr2；新全局manifest 20261010-003显式启用该策略，仍共用600秒绝对deadline及严格两帧/身份/事件守卫。[共享修正及133项证据](2026-10-10-shared-delayed-injection-source04.md)保留作者测试、独立599→600剩余预算probe和冻结边界。冻结export生命周期8PASS，整入口suite因未导出workshop/products.json报ERROR，原件保留；新增globalflag单测1PASS及host help0，正式prepare/preflight0，不修改冻结树追认。

R41实际run/verify2，714次startup观察均未连接/native帧0/steps0；600秒内无Setup completion，因此原策略没有注入，未进入事务对照或任何业务，也没有业务SAVE/day。日志最后强力封臣初始化，error.log0B；此结果未验证延后注入后的效果，不判定早期注入就是根因。原host Popen1；runtime原安全失败异常源链执行清理，但launch没有返回SessionHandle，host session.report=null且cleanup_ok=false，原游戏exit/Jobcount结构化回执缺失，均保留而不称normal0。新的独立进程清点CK3/录制/host/watchdog空、控制文件空；最终新鲜Steam原图7:01离线亲审、桌面恢复1024×768、keeper原allocate Popen0/thread joined，CAS4276→4277实际释放。[R41报告](2026-10-10-r41-shared-runtime-startup-red.md)保存真实边界。

精确6a3 Official37995375811 FAILURE、Linear37995375808 success、LiYu NOT_TRIGGERED。实际失败为旧AST隔离测试漏传生产host已声明的supervisor，6项同NameError；外置一行namespace fixture修正使原6项PASS，等待闭场后独立入库与新精确CI，不能追认6a3成功。当前并行：CI窄修、R41证据归档、root共享报告线性发布、engine加载路径只读诊断；不再仅增加预算或重复bootstrap。缺失ck3-upgrade-20261008不再是依赖。正式I3b/C3/I4及一期仍NOT_GREEN，75%仅工作量估计，不承诺未经实机依据的一期完成日期。


## 2026-10-10 08:07 CST：本机Source05与R42单变量对照准备

R41失败证据与failed-launch前驱分配修正已通过rebase普通推送至0c0e36e21164d55cd9f47d2d8ab9ae7a5cbf3f63。它保留原cleanup_ok=false、session.report=null及原CK3/Job退出未知；新分支只允许已安全结束、当前进程和控制文件为空且原keeper/CAS已释放的失败启动作为后继，不授normal0或业务信用。原八项边界测试PASS；远端整合后26项关闭/审核/poll测试及一项initial-plan-failure测试PASS。最初组合调用漏传--host-source退出2，分开按正式CLI执行后通过，原失败保留。

Source05固定为27644fdc18e693990e43794af62ebf13db523aef，单父Source04 919bae0f4，只应用作者3704561725e583d9c9fc10f4c47c1523bb1d9643相对其父0c0e36e的五路径Python增量。共享-debug_mode默认关闭，由单一manifest显式启用；同PID/Job、一次loadsave、600秒绝对deadline、加载完成后注入及严格native守卫不变。主仓相关93项首跑有一旧测试mtime失败，固定测试marker时间后14项PASS，另79项原PASS；不把首跑写成全绿。冻结Source05另14项生命周期、4项global路由及host help通过。全native目录仅host Python变化，C++/CMake输入逐文件相同后复用原Source02的cbr2产物，没有声称编译当前master全部native功能。

本机新全局runtime为C:/workspace/ck3-common-runtime/20261010-004/runtime.local.json；R42冷输入prepare/preflight已实际0，71正式文件+6 overlay、原91MB seed与预算保持。缺失C:/workspace/ck3-upgrade-20261008不再是任何依赖。精确0c0e Official38006953109 FAILURE、Linear38006953137 SUCCESS、LiYu NOT_TRIGGERED；实际错误是一个Workshop cache测试缺失审核上下文context_path，测试夹具窄修与证据独立交付，不改生产resolver或追认旧head成功。

当前R42尚未分配/启动，后续先完成上述夹具修复的普通发布，再获取当次新鲜Steam离线图与独占现场执行唯一debug变量对照。归档可在外置目录与实机等待并行，冻结现场期间不改跟踪文件。正式I3b/C3/I4及一期仍NOT_GREEN，75%仅工作量估计，未新增实机业务PASS；启动窗口仍最多600秒，产品完成日期待能力恢复后的实际业务结果。


## 2026-10-10 08:41 CST：R42调试单变量仍RED，现场已释放

Source05/debug公共修正、缓存测试夹具及准备记录已普通推送b0e5119ccc023e99509f2d33001f7a9372cd436b；该精确提交Official38007787292与Linear38007787307均SUCCESS，共享acceptance步骤也有原jobs实际success，LiYu工作流未触发，不计通过。[Source05永久证据](../ck3-native-ai/2026-10-10-shared-saved-debug-source05.md)中的未实机状态是冻结当时事实；本段记录随后R42真实结果。

R42沿previous-shared-failed-launch分支实际分配，未重复bootstrap；正式71+overlay6和4项配置逐文件与R41一致，seed/budgets/baseline/actor/date相同，规范化路径后唯一argv差异为-debug_mode。实际CK3 PID9988原进程命令行确有此参数和一次-loadsave。run退出2（00:11:11.944Z→00:21:16.034Z），host原Popen1，native报告00:21:29.148Z终态RED：1022次startup均disconnected/native帧0/steps0，600秒内无Setup completion，故没有注入或业务动作、SAVE/day。日志最后08:16:21强力封臣初始化，error.log0B；单独debug未解决加载阻点，不把该最后一行当成已定位函数根因。

原cleanup_ok=false/session.report=null及原CreateProcess句柄/Job关闭结构化回执缺失继续保留。独立只读观察句柄在游戏仍活着时用raw GetProcessTimes FILETIME核同PID（相差-2tick），实际观察CK3于00:21:28.739Z退出1；它不是原CreateProcess句柄或typed normal0。首次PyWin32 datetime精度断言失败保留，002改用raw FILETIME成功；后到的三次进程活动采样均NoSuchProcess，无CPU/IO数值，不回填0或据此判断死锁。

最终当前CK3/录制/控制文件空、Steam新原图8:37离线亲审、桌面恢复原1024×768，keeper joined且原allocate Popen0；CAS4302→4303已释放，verify仍退出2。Source05归档、R42归档和exact CI记录并行落地；后续先核已有STATE中的活动事件/marker与夹具定义，不能凭源码推测改存档或恢复全部额外夹具。缺失ck3-upgrade-20261008仍非依赖。I3b/C3/I4及一期NOT_GREEN，75%仅工作量估计，无新增业务PASS，不承诺未经实机支持的完成日期。


## 2026-10-10 10:39 CST：R43 活动观察、实际闭场与未来 R44 单预算比较

精确 `a967a41d178d5a7e080415e5f2376b58a70b0f60` 的 Official CI `38016435851`、Linear `38016435827` 均实际 SUCCESS；共享 acceptance 与 Python-only 步骤也有实际 success。Li Yu Dao 工作流 NOT_TRIGGERED，不计通过。原 `6baf0b73e` 的历史报告措辞检查失败继续保留；修后本机完整检查 exit0，生产运行时和校验器未因该文案修正改变。实际 CI 原件位于 `C:/workspace/ck3_lyd_runtime_20261004/r43-exact-a967a41d1-ci-20261010-001`，terminal evidence SHA-256 `65854e54528702656d587fb02af02053ea11bcc28c5f415a23fd35aa62bc9805`。

R43 使用原 Source05、71 正式文件、6 overlay、四项配置和固定 D2a seed，原 readiness600；公共 run/verify 均 exit2，host 原 Popen1、native frames0/steps0。未到 Setup completion，未注入、未进 handler、业务选项/SAVE/day 均0。独立只读观察取得20次采样，19个 CPU 区间均非零；最后一次约573.100秒时 CPU 仍约440.164%（单核100%口径）、RSS约5.87GiB、可用内存约17.86GB，累计 CPU 增量4732.859秒、读取5869441508字节。窗口19次均可见且未最小化，前台均为 Steam；不推断前台状态造成加载延迟。最后日志为 powerful vassals 初始化，不把日志行当作已定位阻塞函数。

独立观察句柄以 raw FILETIME 核对创建身份，在02:30:33.579721Z实际取得 CK3 exit1；它不是原 CreateProcess 句柄，原 cleanup_ok=false/session.report=null、原 Job 最终计数及原游戏退出回执缺失仍保留。最后573秒采样到退出的28.857秒无活动采样，不外推 CPU 状态。当前进程/控制文件清点为空，最终新鲜 Steam 原图10:31亲审离线，桌面恢复1024×768；keeper 原 allocate Popen0/thread joined，FINAL sequence4324，原 CAS 释放回执实际 done/resources=[] sequence4327。[R43 原始观察与闭场归档](2026-10-10-r43-observed-startup-red.md)独立保全。

缓存元数据只读比较证明 R38 自己的3740个 shadercache 文件也都在本轮启动之后创建/修改；原 materializer 只复制三项普通配置，没有复制 profile cache。原报告把三项误写四项的错误和追加更正均保留。不据此认定公共冷 profile 为根因，也不复制缓存或恢复额外52文件。已保存活动事件是 `.20`，marker 在此阶段缺失符合脚本顺序；没有修改存档或 marker。

下一场 R44 仅将本产品此 case 的未来 readiness600→900秒，保持 Source05、单次 loadsave、同PID/Job、加载后注入、一个绝对 deadline、原 native 守卫及所有业务输入。command300/timeout2100/hold900/poll0.5、终点60秒和退出reserve90保持；这次活动证据支持有界耗时比较，不保证成功，不延长或改写 R43 原600秒失败。外置观察器上限可延至1200秒，以覆盖新预算后的实际退出，仍只读且不改变游戏 deadline。新 profile、ID和常规前驱闭场准入必须重新取得。

并行工作：R43 证据包收尾；root 调整未来预算并更新公共准备；独立线程只读核对 R44 固定输入及观察器派生。没有新增无关能力。正式事务对照、I3b/C3/I4与一期仍 **NOT_GREEN**，75%仅工作量估计，无新增业务PASS。下一时间节点是本轮线性发布后一次最长900秒的启动检查；能否进入业务及一期完成日期仍取决于真实结果。缺失 `C:/workspace/ck3-upgrade-20261008` 不再是依赖。


## 2026-10-10 11:04 CST：R44 原900秒仍未完成加载，已实际清场

R43归档与未来900秒预算已通过无冲突rebase、远端新增的独立宗教日志验证测试PASS后普通推送为 `97d16f9b1f3c91887549c987291c2435087e1025`。该精确提交 Official `38018072981`、Linear `38018072962` 均实际SUCCESS，共享acceptance和Python-only步骤也成功；LiYu NOT_TRIGGERED不计通过。51组查询及两完整日志归档在 `C:/workspace/ck3_lyd_runtime_20261004/r44-exact-97d16f9b1-ci-20261010-001`，包括TLS超时原件与恢复后的真实终态，terminal evidence SHA-256 `0a09745ea78ea7bd209cc6603bb79ffe4f67606183a11101e89a88b2228878c3`。没有dispatch或重复本机全套测试。

新 C6公共prepare/preflight均实际exit0，常规 R43 failed-launch 前驱/CAS4327准入分配 `bf-202609141645-5434332d4d--li-yu-dao--R0044`；未重复bootstrap。实际冻结输入只读对照确认，规范化运行路径/执行ID后唯一调用参数差异为readiness600→900；正式71+overlay6、4配置、原seed/actor/date、Source05/EXE/DLL/injector、typed handler、45有序缓存/政治7 AST、终点60/退出reserve90保持。全量provenance另包含rebase接入的无关XQOL adapter pin变化，不能声称全部来源仅改registry；两个outer descriptor仅profile路径不同。对照位于 `C:/workspace/ck3_lyd_runtime_20261004/r44-actual-frozen-input-comparison-20261010-001`。

公共run实际 `02:47:16.746746Z→03:02:21.541348Z exit2`，verify仍exit2。原host Popen于03:02:39.080492Z实际返回1。native终态RED，原900秒内没有Setup completion，所以未注入、native frames0/steps0，handler及业务选项/SAVE/day均0。不能据此授事务对照或正式业务信用，也不把powerful vassals最后日志行当作已定位阻塞函数。[R44原件及闭场报告](2026-10-10-r44-900s-startup-red.md)单独保全。

30次只读样本中，9个完整CPU区间处于600秒之后；最后约873.873秒仍CPU347.81%（单核100%口径）、read+26331485B/write+3770124B，RSS7894478848B、127线程。独立只读句柄以raw FILETIME核身份，03:02:38.247809Z、elapsed902.849849秒实际取得CK3 exit1；最后活动样本至退出约28.977秒不外推。29次SDL观测全部visible且未最小化，本场前台自然为游戏，与R43前台Steam不同；没有向游戏发送focus/输入，不认预算或前台因果。CPU活动也不能排除局部死锁。原cleanup_ok=false/session.report=null、原CreateProcess退出及Job最终count未知保持，不补造normal0。

当前CK3/case进程及控制文件清点为空，最终新鲜原图11:02 Steam离线亲审，桌面恢复1024×768；keeper原allocate Popen0/thread joined，原FINAL sequence4339，实际CAS4339→4340释放done/resources=[]。当前现场已释放，允许主树写入。本轮900秒已失败，下一步不再仅增加加载预算：本机已找到WPR/xperf，先只读核现有trace、可用CLI和权限，准备有界CPU热点/模块RVA观察以定位加载消耗；未开始新trace或新游戏，不改变系统设置或占用他人trace。

并行调整：R44原件紧凑归档、只读CPU采样工具准备、root进度与线性发布收尾；CI和固定输入对照已完成。正式I3b/C3/I4与一期仍 **NOT_GREEN**，75%仅工作量估计，无新增业务通过项。下一节点是加载热点观察方案的本机可执行性确认，之后才安排新实机；一期完成日期仍无可靠依据。缺失 `C:/workspace/ck3-upgrade-20261008` 继续不是依赖。
