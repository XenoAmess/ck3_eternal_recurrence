# 施工状态

2026-11-18，machine_id: 4-8e1c2f1861。

## 当前状态（R0012 收束后）

第十二场`R0012/a90`实际装载当前`71575e8f`的Q18 DLL，进入已归档1.21基线。首次关联只读请求在8秒期限排队超时并确认撤收，随后在同一owner实际完成新帧后取得`native:2/public3`与`native:3/public4`；角色31254、日期53144328、暂停状态均核实。GUI查询实际执行并在0.207秒返回`gui_global_tree_budget_exhausted`，没有控件或按钮效果。该错误目前还合并了深度、节点数、子指针读取、重复及环等失败，不能仅据名字认定节点数量超限。[本场真实原件](../../docs/maintenance/evidence/2026-11-19-financial-markets-machine4-r0012.json)。

本场首次实测新版公共队列的正常退出链：query取得Core上下文，一次confirm获得真实requested ACK，随后retained process observer独立确认同一PID/出生身份退出码0；managed session亦为Game0、Job0、treegone，Host原wait0。正常退出不代表业务通过：公共run仍为wait2/627.981849秒，case尚未完成且原自动关场报告进程已退出，两项错误保留。显式finish-hold后正常停止keeper，原keeper exit0；21:40:15Z CAS15314→15315释放资源。金融动作、新增日、金融SAVE仍为零，当前继续修控件定位及完整市场业务验收。

同步远端后Q18在同一Native缓存实际重建受影响目标并通过，耗时100.631971秒；新DLL SHA256为`4892f522b6f5db9ad26c9ca992230b1f0e64d15a2e7b33976ba5a5c9bf78ada4`。受影响EXE的7次补充执行通过，耗时54.691909秒；相同字节的旧程序按原件另行复用。远端GUI磁盘身份改动涉及的9项检查及新helper完整strict通过，旧队列39项未重复执行；公共链消费绑定当前源码。原Q17与重放前提交身份保留历史，不将其重标为本场实际产物。

## R0011 收束记录

第十一场`R0011/a89`实际装载Q16后进入原存档，先后取得`native:2/public3`及`native:3/public4`的独立完整状态，日期53144328、角色31254、暂停；持久1024未复现。第一条GUI查询完成了Semantic前置读取，随后因固定许可表没有GUI执行器而返回unavailable，没有执行按钮。实际前后计数为3→4，不能把这一次Semantic完成记作GUI执行。[本场证据](../../docs/maintenance/evidence/2026-11-19-financial-markets-machine4-r0011.json)。

20:47:12Z实际保存132,739,080字节，SHA256 `d58e7f82bf607ff1cb2957f19e8d0263dd1f1e852e63de3801e502800a2e4a66`；20:49:41Z外置独立物理归档原wait0，复制前后身份、大小和SHA均核实。保存为1.21.0／格式19／1066.9.15，仅有51个原版故事，尚无金融exchange或账户，保留missing/incomplete而非金融认证。原生回执只证明提交；物理事实由SDK落盘指纹及后续只读归档独立确认。额外one-life身份回执仍为unconfirmed，现行全新profile冷载不消费该旧身份门。

正常退出query又在claim/publish前被公共工具的旧1.20能力门拒绝。未热改冻结场；一次既有session stop于20:53:10Z确认，Game exit1、Job0/treegone及清理均核实。21:00:04Z，Game已清理后采用源码使旧keeper因checkout变化结束，原entry_error及keeper exit1保留，不能借allocation父wait0称keeper通过。公共run原wait2/1677.831873秒；Host按原hold期限结束，原wait0。21:10:22Z实际CAS15305→15307释放资源，过期claim保持waiting/unresolved_red。没有金融动作、新增游戏日或正常Quit信用。

已修复并单独提交Native固定GUI／事件执行器登记，保留原四角色并按既有能力追加两槽，不放宽版本、Full、动作或期限保护。Q17在同一缓存实际构建通过（105.066644秒），补充7次实际执行通过（54.580884秒），不变程序的既有通过另行引用；新六槽回归亦接入原默认CTest链。Q17的DLL为`c3dce988b6caed4f9edb8da6c8de800bc3694ef8eb14c7336d95a7022085667e`，尚未装载后继场。

公共退出队列按精确版本选择既有1.21／1.20能力，并从冻结索引核验、私有加载原SDK五叶。首稿37项通过未覆盖独立CLI缺包，保留为被替代历史；最终完整两模块39/39通过，包含无ambient SDK的真实干净子进程入口、来源破坏拒绝、严格类型检查与编译。后继以已归档的1.21基线准备开市、付费发行和真实交易，整Mod仍未验收完成。

## 第十场与只读漂移修复（20:24 UTC）

第十场`R0010/a88`在初始只读Core请求后触发持久`1024 post_execution_drift`。后续owner回调持续完成，但共同观察器在读取前拒绝，旧`root_type_mismatch`只是未刷新的诊断。原请求为`core-frame-2-65fdb43a253b`；周围心跳日期变化支持载入过渡，但未记录执行器精确before/after stamp，不能认定具体哪一比较项失败。本场没有Fresh请求、金融动作、新增日或SAVE。[完整原件](../../docs/maintenance/evidence/2026-11-19-financial-markets-machine4-r0010.json)。

通过现有session lifecycle队列发送一次stop，原受管流程实际收树：公共run原wait2/833.375284秒，Host1、Game1、Job0/treegone、cleanup通过，keeper原wait0；20:07:10Z实际CAS15291→15292释放。失败退出不计正常Quit或业务通过。

已采用三叶Native窄修：只有精确Florin已登记只读Core回调正常返回、after stamp可读且同pump/线程/TLS稳定时，过期结果仍拒绝、本ticket仍失败并重置连续证明，但不新增永久故障。控制回调、旧版本、执行失败、不可读边界、TLS漂移及已有故障保持原保护；不清旧flag、不重放旧请求。13个边界场景已加入现有mailbox夹具，尚待同缓存Q16实际编译执行。

共同Host同时采用精确永久故障的及时失败分支，先核本场实际single-CLI启动与HELLO/心跳身份，保存原诊断后走原清理；只有从无Full或业务的同一专用异常才跳过不可能的最终读取。两个完整NoGame消费者单次35/35通过、原wait0/10.020023秒；两处旧调用序列断言首次失败原件保留，未改生产调用来迎合测试。

上一轮发布序号修复的Q15已实际构建通过（105.157011秒），受影响两个EXE的三次执行通过（18.474095秒），基线按真实依赖复用；DLL为`59b69fcdf66bdd4e32ff2216798473550a92a7896593a2a2bfdf40cf5606b472`。R0010在更早的启动保护处失败，尚未验证该递增行为的实机结果。下一场继续金融业务验收，不以这些软件结果替代成交、物理保存或整Mod通过。

## 第九场与发布序号修复（19:42 UTC）

第九场`R0009/a87`已实际通过取消恢复路径：原read3在8秒内明确取消、撤收且未执行；随后同一进程、连接、owner及TLS有自然完成进展，Host发出独立read4。19:31:55Z，Native实际写出关联Full并ACK成功，但仍为初始的`native:1/revision1`，SDK正确拒绝非递增发布身份。公共run原wait2/400.159142秒，Host1、Game1、Job0/treegone及keeper原wait0已核，19:37:32Z实际CAS15281→15282释放。零金融动作、零新增日、零SAVE。[原件摘要](../../docs/maintenance/evidence/2026-11-19-financial-markets-machine4-r0009.json)。

已采用Native窄修：每次强制关联读取都选择新的发布序号，状态帧成功写入后才提交；普通去重、世界状态及SDK后来版本检查保留。两个现有生产body夹具同步并增加连续相同状态读取、写失败和溢出边界；尚待同缓存Q15实际编译与执行，源码采用不授实机通过。R0009另有一次有限PSS及16帧元数据回溯，样本处于普通界面update任务等待；上下文与后取栈非原子，未取得heap任务身份，不能称死锁或Native/Fresh正在执行。

## 第八场与取消恢复修复（19:15 UTC）

第八场`R0008/a86`已实际装载完成帧就绪修复：先拒绝载入对象，再等待真实完成帧，随后成功完成两遍Full读取。18:41:33Z首份完整快照可用，紧接的唯一Fresh请求仍在8秒原期限内排队超时：submit0/wait4/reclaim0，pump18799未推进，32次wake发送成功。公共run原wait2/403.366303秒；Host1、Game1、Job0/treegone和keeper原wait0均确认，18:43:58Z实际释放资源。零金融动作、零新增日、零SAVE，不能称业务通过。[实际原件摘要](../../docs/maintenance/evidence/2026-11-19-financial-markets-machine4-r0008.json)。

Q13实际受影响测试及新增就绪夹具通过；Q14在最终`c136e1c534d99ca52a08fd9cd14324a1d453c149`下同缓存no-work，19个不变基线原件复用，DLL为`c95fe73d4d7b28f0ab0ab4906037c12e82e0ea960318a44c08d34d794e08f7be`。正常同步造成Q13非祖先的首次运行包拒绝保留；改用实际当前提交Q14后公共builder成功。没有重标Q13来源或伪造worktree绑定。

已采用共享启动消费者对“已确认取消并撤收的排队只读请求”的窄修。旧请求、8秒期限和原错误保留；新请求必须等待同一进程、连接、owner、TLS及游戏上下文的真实后续完成进展，原1800秒readiness期限不重置。两处暂忙竞态单独处理：已撤收的旧读取保留证明，尚未创建或发送的新读取通过独立SDK回执继续等待；不释放UNKNOWN读取或业务动作。最终15项NoGame组合测试通过，新的合同模块strict通过；只覆盖软件生产路径，不授予游戏业务信用。正在准备下一场实际装载与验证。

R0008引擎日志18:38:03Z的564391字节快照已独立核对：156条金融诊断均为静态变量警告，78个符号逐项关联源码，未确认金融语法或scope阻断。其余3124条不能统称无害：包含812条旧建筑字段拒读、1078条缺少key、468条宗族名字替换、410条文化引用失败等。原版1.21中实际存在`czech/slovien`定义，不能据错误认定缺DLC；旧建筑经济状态是否重建、具体损失多少仍未知。断言后日志继续不等于完整恢复，此结论只覆盖该保留快照，不能称全日志或实际业务健康。[兼容诊断与精确来源](../../docs/maintenance/evidence/2026-11-19-financial-markets-machine4-r0008-compat.json)。

## 第七场与就绪检查修复

云端独立分支真实run [44359949157](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/44359949157)已通过：共享存档库10项、金融246项，29个JUnit suite逐例核对，0failure/error/skip；源码validator与候选allowlist均196文件。仓库路径修复已正常接到远端并推送`89e5e07f43b3009dd75c67112baf9f358bb1130b`；金融生产字节及工具与该云场完全相同。前三次云端失败均保留。

第七场`R0007/a85`用于取证，仍在启动FreshFull原8秒期限失败，零业务动作/新增日/SAVE。两次有限OS线程诊断实际成功并释放PSS；第二次前已确认37843ms无新的Peek/Poll进入，RIP在`NtYieldExecution`，原生候选地址涉及Core取玩家与Full观察。只保留owner上下文及有限栈，未clone全内存、未输入或抢焦点。原Game失败exit1/Job0/treegone、原Host和keeper wait已核，17:36:35Z资源释放。[原件摘要](../../docs/maintenance/evidence/2026-11-19-financial-markets-machine4-r0007.json)。

精确PE展开元数据的16帧有限回溯已完成，并逐个核对调用指令及链式展开：该采样在UI初始化任务等待链中。raw栈中的Native候选地址位于游戏函数局部栈区，不能当作当前观察器调用帧。上下文与后续有限栈读取非原子，结论只适用于保留的这次样本；发布的heartbeat也不能独立证明当前是否有观察器在运行。

已采用窄修复：Full业务读取在既有owner/TLS资格之后，先检查精确UI对象图和应用已完成帧计数。第一次合格对象图只记录基线，同一图实际完成后续帧才允许调用游戏getter；切换、对象缺失、身份变化、计数回退或回绕均重新验证。独立Core读取保持原合同。冻结候选及9项精确PE校验经独立静态审阅未发现阻断缺陷；私有adapter的owner/reset分支尚只有静态审阅，不能借Full夹具授予执行信用。

18:19:19Z，Q12实际生产增编和链接成功，随后被旧构建范围合同拒绝，原操作wait1/108.352729秒、零finite执行。合同现显式增加该生产源，实际生产TU为793，两个受影响Full夹具分别由7/10增加到8/11；flags及19基线目标不变。同缓存继续资格，不将清单修复或编译成功当作实际Fresh成功或金融业务信用。

## 第六场与前序云端失败

第六场`R0006/a84`已实际装载Q11及196文件产品profile，主窗口最小化、非置顶、非前台。17:05:40Z普通Full可用后，唯一强制读取仍在8秒原期限失败：32次thread wake成功，owner的Peek/Poll进入与完成计数均不变，active=0，executor未开始。新SDL hook确实已安装，但未覆盖该等待窗口；不再把单纯“换到更上层hook”假定为足够。原场已失败exit1/Job0/treegone，Host与keeper原wait均确认，17:07:27Z资源实际释放。零金融动作、零新增日、零SAVE；正在根据自然事件长间隔及SDL等待/唤醒链继续最小修复。

金融源码已以`a79244d1feb6dda1ebbcb8ba250fc9ac7132955b`正常推送。正式云端CI44350459844在运行测试前缺少共享save-core依赖；独立分支补安装后，44353909542已完成共享库安装和金融57main编译，但Quarkus测试生成另有依赖解析失败。两次RED原件保留，正在独立修复，不能把本机246项通过称为云端通过。完整真实记录见[共同验收记录](../../docs/maintenance/2026-11-18-machine4-financial-acceptance-control.md)。

第三次云端44356563069的新增诊断确认：共享安装与金融外层解析器使用C盘本地仓库，测试生成器另建的解析器却使用D盘同名路径；原始日志和失败保留。下一步修正这个实际分歧。只读SDL分析尚未证明游戏长间隔进入其等待函数，因此未盲加新hook。新隔离场拟采集实际owner线程等待证据；公共prepare及prepared plan通过，首次allocate因三份未提交记录文档被干净anchor规则拒绝，未启动Game、未占新资源。

## 截至16:41 UTC的集成记录

新增四包已按独立补丁合并：有限资金回兑、所选期货合约真实盘口、章程确认目标固定及退市静止状态的冗余写入优化。显式运行清单为196文件；各包说明见[回兑](coin-redemption.md)、[期货盘口](futures-selected-contract-book.md)及[章程确认](charter-target-confirmation.md)。回兑只用发行账户真实预存现金，成功交付后记用途和永久收据，不制造现货成交量或价格样本。

16:32:32Z首次统一完整验证实际失败：239项、2 failure、1 error、0skip，原wait1/38.5113165秒。三个集成问题分别为新盘口刷新缺少旧AI测试的显式UI端口、优化测试默认引用当前源码而非旧基线、OTC界面冻结对比未排除新增回兑面板。原JUnit保存在`task/software-13-financial-utility-full01-FAILED`，没有改判。已从Git固定8份原生产源码及来源SHA，保留原严格优化差异断言；另外两处只补明确端口和新面板扩展。16:38:43Z受影响三类24项全部通过、0skip，原wait0/19.876317秒，`operations/MVN-financial-utility-fixtures01`。完整后继验证、回兑SAVE审计接线与实机仍在继续。

共同Native的Q10已实际通过：同缓存生产构建wait0/72.733934秒，19基线中实际重验4个受影响目标、复用15个相同原件，附加10次调用全部通过。自然SDL事件边界修复已编入DLL，尚未取得新场装载或主线程读取成功信用。最终金融提交后仍须按干净源码完成公共资格绑定和运行包，不能用Q10软件结果声称第五场已修复。

16:41:04.570428Z统一完整后继`mvn verify`实际wait0/39.423229秒：246项全部通过、0skip，Quarkus默认入口打包成功；`operations/MVN-financial-utility-full02` stdout9460bytes/SHA `f5e68585752e524bf8822071359c407177807f348fb1153b8d6193284c2c1cd9`，JUnit保全`task/software-14-financial-utility-full02`。其中7项新增回兑SAVE审计与原2项共同通过；两类新实体已进入真实两遍reader/来源资源与JSON输出，核预算、当前余额、历史复用、永久ID/收据链和七日冷却，不把预算重复加成现金。仍保持`financialCertified=false`，没有真实1.21金融SAVE或冷载信用。

## 截至15:51 UTC的准备记录

第五场`R0005/a83`实际收到32次发送成功的后台唤醒，但owner pump仍停在19058，唯一新完整读取在8秒后明确失败。错误及原始诊断已完整经过公共接口保留；本场失败exit1、Job0、tree gone，原Host/keeper退出及CAS释放均已确认。没有金融动作、推进日或SAVE。正在修实际主线程服务边界，不延长旧请求或恢复前台；失败不计整Mod通过。原件见[共同验收记录](../../docs/maintenance/2026-11-18-machine4-financial-acceptance-control.md)。

已采用五包集成：AI用实际私人金币准备有限期货保证金、共用到期系列与存续义务日结环、正常市场OTC入口、退市币的保守AI议价，以及两份观察公式修复。运行文件174项；旧空合约的一次迁移保留ID并进入发现索引，不进入日结环。具体规则见[集成说明](financial-product-integration-2026-11-18.md)。

15:50:20Z，统一版本完整`mvn verify`实际wait0/39.056779秒：200项通过、0失败、0跳过，Quarkus默认入口打包成功；原件`operations/MVN-financial-integrated-full01`，stdout8386bytes/SHA `d1c282f406b6db3fff62fc805fe2b9b9d61ca1ba1264ef6847f09a2f46437329`。包含新增14项AI期货、9项日结、3项OTC界面、8项AI议价及6项观察公式测试。此前23组standalone仅属这些生产脚本子集的独立执行，不叠加成223项。统一版本尚未装载游戏，实际用途、真实交易、SAVE、冷载与规模仍待验收。

## 截至14:22 UTC的准备记录

第三场 `R0003/a81` 实际载入原存档，13:50:32Z 获得精确 1.21 Full：玩家31254、存活、地图就绪、暂停、日期53144328、金币255。暂停且语义不变时，普通 snapshot 持续返回同一 `native:1`，原启动守卫要求两份递增 Full，遂在原1800秒期限失败。公共 run 原 wait2/1805.433秒，Host原wait1；受管失败清理为CK3 exit1、Job0、tree gone，不能称正常退出。keeper原wait0后，14:16:03Z CAS `15224→15225` 释放。本场没有业务动作、游戏日或SAVE。

已采用独立 `ck3_take_fresh_full_snapshot_v1`：复用原DLL的关联只读查询，核实际ACK、read_request_id、完整原包、递增revision及相同PID/连接。普通snapshot与运行中的推进观察不变。新10项组合含12种异常刺激通过，受影响Saved14及旧版2项另行通过；实际capability3项通过。金融七个saved case均声明此工具，未重编Native或伪造新帧。

AI付费宣传关注队列和真实本金认购修复已采用，受同一个总日预算约束；满额AI发行在原注册币遍历及时完成，保留玩家手动完成及不同继承项目的pending。详见[AI运行合同](ai-attention-runtime.md)。原生产品现在有160个运行文件；真实自然募集、队列保存和交易仍待新场验证。

14:20:42Z，采用共享流式SAVE审计及AI修复后的完整金融工具`mvn verify`实际wait0/34.793秒：160项通过、0skip，56个主源码和20个测试源码实际编译，Quarkus默认入口打包成功。此前共享save-core的10项通过并install。本轮SAVE两项JUnit复用52个合成断言，不能当真实存档认证；命名审计入口、真实1.21编码与冷载仍须实测。原件见`operations/MVN-save-core-audit01`及`operations/MVN-financial-ai-save-full01`。

## 截至13:37 UTC的准备记录

第二场 `R0002/a80` 已实际创建 CK3 并注入 Q05 DLL，连接实际返回精确 Florin HELLO。Saved startup 遗留的 `.4` 守卫立即拒绝新身份；后续 300 秒为 finally 的收尾 snapshot 等待，并非正常启动等待。原受管环境失败清理为 CK3 exit 1、Job 0、tree gone，不能计正常退出。keeper 与原 allocate wait 0 后，CAS `15207→15208` 实际释放；没有业务动作、游戏日或 SAVE 通过。完整因果及原件见[共同验收记录](../../docs/maintenance/2026-11-18-machine4-financial-acceptance-control.md)。

本场加载日志还暴露了真实脚本解析问题。关场后已采用保持原公式的数值比较修复、意见衰减期限修复、正数扣款 API 与无用交互 AI 调度声明修复，尚待新场重载及真实金额对账。Saved 启动按精确版本识别，Florin 等待实际 owner 与两份递增的完整帧，旧版保留原分支；Core 的 partial/unavailable 消费同时按实际 HELLO 绑定，不能跨版本混用。

13:13:58Z，完整金融工具 `mvn verify` 实际返回 0：143 项通过、0 skip，49 个主源码和 16 个测试源码实际编译，Quarkus 打包成功，原进程总墙钟 34.064 秒。包含六个后续验收 profile 的生成、衍生品关联账户/合约/债权、继承观察基线防覆盖及保守容量边界；这些 profile 只生成观察器，不注入生产资金或资产。六场均已接入公共准备入口，尚无对应游戏业务信用。JUnit 原件保全在 `C:/workspace/ck3-market-task-20261118/software-10-financial-full01`，原进程回执见 `operations/MVN-financial-followup-full01/ORIGINAL-WAIT.actual.json`。当前正在完成共同 Host/Core 联合检查并准备新场，未把软件通过当成交易、保存或整个 Mod 通过。

共同 Host/Core 的当前组合 26 项及 Core strict 已通过。同根运行包绑定另暴露原 Q05 无 `observed_at_utc` 与旧 reader 假设不一致；最小读取兼容修复的 9 项已通过，保留原 Q 与原构建时间，不伪造资格时间。新包继续复用未变 Native，下一场仍须实际验证 loaded Full、钱包与保存。

源码复核另确认 AI 募资可达性缺口：35,586 个角色在默认每日512候选下约70日才轮转一次，长于30日募资期；广告只影响最多8人，AI登记后尚未主动本人认购。正在独立准备有界关注队列及真实本金认购修复，仍受同一总日预算、随机选择、外部认购比例与真实现金约束；此修复尚未采用或实机验证，不能称 AI 市场已验收。

## 截至 12:27 UTC 的准备记录

共同 Florin 运行包 `runtime-core03` 已实际组装成功；Q05 使用同一 Native 编译缓存，未重编 C++。正式 DLL SHA-256 为 `2716d740cb145eae319cf7776fe4f0a46b5c325b6196026d0541a5eed292836c`。共享单日推进和完整角色 ID 消费修复已提交推送，但仍未取得游戏运行行为信用。

首场 `R0001/a79` 的 prepare、已准备 plan 和 preflight 通过。公共 run 的 Host 在创建 Game 之前，被 Saved inventory 守卫拒绝：观察包仍含 `xfma_start.txt` 新开局钩子。原失败和 profile 保留，keeper/原 allocate 正常退出，CAS 已释放；游戏日和 SAVE 均为零。

最小观察器修复已移除该钩子的输出，继续只通过正常 GUI arm。实际 Java emitter 到公共 Saved inventory 和 Host 复制的新增组合回归通过，受影响 8 项通过；完整金融工具随后 `mvn verify` 130 项通过、0 skip，Quarkus 打包成功。新的实际场次仍待执行。完整事实、路径与时间见[共同验收记录](../../docs/maintenance/2026-11-18-machine4-financial-acceptance-control.md)。

## 截至 11:07 UTC 的施工记录

用户明确要求继续做完完整产品。A0是历史原型，不是本任务的交还终点；下文A0通过与失败保留原范围。当前正在把完整现货、发行主体、期货、价格来源、债务新闻和自定义市场界面接入同一原生账册。共同接口见[运行合同](runtime-contract.md)，没有以Java参考计算替代游戏实现。

新增游戏规则提供2,048／4,096／8,192种活跃币容量、AI每日128／512／1,024个候选和独立新增风险开关。默认4,096币、512个AI候选；扩展档仍属实验配置。关闭新增风险不会删除旧持仓、债务或结算义务。

09:43:53 UTC，首轮增量Maven实际47项全部通过：原现货26、原子账册批次3、发行9、退市生命周期7和新增界面引用/窗口注册构建检查2。42个main源与7个test源编译，Java21，15.344秒。09:44:42 UTC，债务8、危机策略3和世界新闻4共15项另行全部通过，11.873秒。这两轮是软件结果；完整期货、原生脚本、GUI和压力场次仍需后继实际验证。

09:34:38 UTC，本机Steam11.23.65.88通过新精确Native配置实际读回离线（同进程/模块、两次离线byte=1、tray状态4）。[共享修复与来源](../../docs/maintenance/2026-11-18-machine4-steam-native-offline-1123.md)已提交推送。旧08:43探针不可用的事实不改写。新版1.21的普通事件选项后台提交仍在迁移，实机业务尚未开始；不借用1.20地址，也不恢复游戏前台。

10:09:02 UTC，完整工具验证126/126通过，Maven20.251秒；涵盖现货与原子账册、发行与真实出资认购、退市、期货、价格来源、债务危机新闻及验收夹具。后续修复了强平余单错误留簿、旧开仓价越当前风险带的问题，10:25:10 UTC期货15项和验收夹具6项共21/21通过，30.789秒。153个runtime文件的BOM检查通过。以上均为软件或静态结果。

公共后台GUI消费者实际35项通过、1个旧1.20夹具缺失跳过；新增1.21跨语言原件链另10项通过。原生债务和期货公式已依据CK3 `max`为上限、`min`为下限修正，仍待引擎金额验证。共享DLL在同一缓存中构建完成，19项独立基线程序及CTest全部通过；首次基线链接失败保留，修复只涉及测试目标生产body隔离。DLL尚未装载。

10:28完整金融工具验证128项中127项通过、1项因新增互动未及时列入运行清单失败；补齐清单后7项构建合同独立重跑全部通过，不记作一次完整128项绿。10:33共同Java控制链31项通过。10:55静态CLI校验155个运行文件、209个effect及每语言468个本地化键通过。现货已补上真实有资买盘深度，退市读取上一完整日的合格交易量；期货新增永久合约号和仓位号。A0交易入口永久关闭，历史资产仍供一次性迁移。

11:07:17 UTC，最终完整金融工具`mvn -f mod_financial_markets/tools/pom.xml verify`实际128/128通过、0跳过，28.190秒；复用已有编译缓存，main/test均无重编，Quarkus重新打包成功。原失败仍保留。该轮包含最新155文件清单及本地化；这是完整工具软件验收，不是游戏引擎或整Mod业务验收。

新增1.21 Native配置合同由真实CMake File API绑定791个生产TU及19个测试目标，25项消费者测试通过。实际DLL SHA-256为`22da249e8de425ad605693d062cd691e7b2dd3a334f21a7a090fc98e06111b4e`。完整正式资格还需最终干净提交后的预冻结、同缓存no-work构建及结束复验；首轮dirty编译不补造预冻结。

共同运行包最近可信基线仍为1.20，正在补齐实际1.21安装身份迁移输入；不能把旧manifest换hash当成运行兼容。共同Python五组194项通过，既有巡礼只读/执行数据消费三组115项通过，均不授金融游戏行为通过。

首场采用隔离旧原版存档，夹具只提供正常按钮启动的只读观察，不生成币、金币或订单。实际开市、付款、同日买卖与物理SAVE需要由生产GUI完成并独立对账；本轮完整产品实机仍为NOT_RUN。共享启动、每日推进和正常退出的1.21消费链正在补齐。

本轮完整任务预留峰3GiB、增长上界6GiB，10:27:51 UTC C盘可用74,326,544,384字节，容量与当日配额均通过；未清理资料。执行机器仍为4-8e1c2f1861。

## A0 历史交付边界

已开始 A0 原型。一个 Mod，共用金融底座，现货与期货作为内部模块维护。阶段范围、退出标准和性能预算见 [实现计划](implementation-plan.md)，具体用例见 [测试验收](test-and-acceptance-plan.md)。

Java 参考账本已实现稳定账户/币/受益人 ID、有限供应发行及增发、真实费用金库、100 枚一手、整数分、价格时间优先、部分成交、原订单累计手续费、冻结与撤单、关联受益人自成交拒绝、跨币共享资金和失败整笔回滚。日序可以同日幂等推进，但尚无期货日清算。该核心是开发参考，不是游戏运行时，也未证明 CK3 性能。

发行资金参考计算已加入：微型R20需要6金费用或限制，剩余14金；标准R200需要55金费用或限制，剩余145金。费用、维护预存、履约保证金和做市资本分别记账。实际认购、滚动融资上限、风险服务准入仍需生产接线。

14个游戏文件已落地：收费发行、有限双向报价/买卖、每日AI候选、持仓故事和托管候选、玩家决议/互动/回执、中英本地化。首包保护值为32个累计登记身份，并非最终容量。详见[A0原生说明与来源](a0-runtime-notes.md)。完整订单簿尚未接入游戏；合格继承管理入口、全世界公平发现和存档寿命仍待补。

## 已有软件结果

2026-11-18 08:46:16 UTC：

~~~text
mvn -f mod_financial_markets/tools/pom.xml -Dtest=FinancialMarketTest test
~~~

26 tests，0 failure / 0 error / 0 skipped，JUnit 0.426s，Maven 27.844s，exit0。包含确定性随机资金/币守恒序列、先成交外部订单后遇自成交的全笔回滚、跨币余额不能重复冻结。Java release21，-Xlint:all -Werror 编译通过。软件结果不授游戏交易或存档通过。

08:58:55 UTC 新增执行：mvn -f mod_financial_markets/tools/pom.xml -Dtest=ListingFundingTest,PoolQuoteTest test，9项全部通过，Maven14.594s，exit0。两档发行资金分类及A0有理数池报价/双边手续费、最小成交拒绝和溢出边界通过；这是独立计算模型，不证明原生脚本精度。

09:02:17 UTC 执行 mvn -f mod_financial_markets/tools/pom.xml -Dtest=BuildContractTest verify：新增5项构建合同测试全部通过，Maven15.765s，exit0；Quarkus augmentation 1758ms，工具打包完成。含BOM/未定义effect/未列入runtime文件/本地化不一致/路径逃逸/输出覆盖/清单SHA等边界验证。

本轮共40个不同软件用例全部通过。随后对最终报价作用域修订文件运行Quarkus CLI validate：14文件、11个effect、每语言26键，exit0。两个native文件的修订仅有静态信用；事件上下文、引擎语义和业务仍NOT_RUN。GitHub新增 financial-markets-static 工作流执行完整软件验证，不调用游戏。

显式清单见[运行文件清单](../runtime-files.json)，候选工具输出content/与独立manifest.json，排除tools、docs和验收数据。外置候选与实际文件SHA保留在 C:/workspace/ck3-market-task-20261118/candidate-a0-01；这不是已发布包或实机通过凭据。

源码568d763833679612bd493aad20b1a60779c856a4的候选14文件已实际构建成功。首次官方[CI 44272883501](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/44272883501)在Windows checkout阶段因历史promo长路径失败，未运行任何测试；失败不改判。后继补齐与既有工作流一致的core.longpaths环境配置，重新触发官方CI，金融代码和14个runtime文件未改动。

后续审阅将native本金/费用公式调整为先转分再做除法和费率，减少固定点中间截断风险，数学预期不变。此变更尚无引擎精度信用；新候选使用外置 candidate-a0-02，保留01原输入，不覆盖历史包。最终CI及外置manifest绑定实际后继源码。

## 实机状态

本机此前已更新到 CK3 1.21.0 / build26622941，见 [本机更新记录](../../docs/maintenance/2026-11-18-machine4-ck3-update-and-market-design.md)。本轮 08:43 UTC 进程只读检查未见 CK3，未启动游戏、注入或恢复旧自动游玩。

08:43:20.845669Z 公共 steam_offline_state_probe.py 实际 exit2：status=unavailable，reason=cdp_not_enabled，native_provider_unavailable=invalid_input，owned_debugger_candidates=0。原件：C:/workspace/ck3-market-task-20261118/implementation-steam-offline-probe-01.json。该结果不能证明当前在线，也不能作为可启动凭据；本产品尚无1.21共同后台业务场次和公共adapter资格，实机状态为 NOT_RUN / prerequisite BLOCKED。

不通过抢前台或复用1.20 DLL绕过。第一场先做金额精度、故事实体/死亡托管、保存冷载及日历合同，再扩大到百币和完整每日委托簿。

## 后续未完成

1. 修复第五场证实的暂停owner不服务问题，再按公共入口准备新的隔离场次；Native只对实际变化重新构建和验证，未变目标保留原资格来源。
2. 实机验证金币精度、正常GUI付费发行、同日现货买卖、AI资金、物理SAVE与冷载，保留真实失败。
3. 扩大到已实现的发行主体、宣传操盘、认购、期货多空杠杆/债务、退市、继承和20种剧情及全球新闻；六个后继场次已具备软件验证的观察包和公共准备定义，实机尚未执行。

4096/8192尚未压测，不是已支持容量；尚未 Workshop 首发。

## 工程与资源

默认 Maven 实测3.10.0，Java25.0.4.1，编译目标21。源码及增量构建/候选包峰值预留256MiB，08:43 UTC C盘可用74,891,210,752字节；完整旧库存加512MiB保守增长上界仍低于当日有效配额，未删除旧资料。原件及容量保护按通用存储策略复核，不将历史构建永久保留为默认。

跨产品可复用的是整数资金/资产守恒用例和清单打包合同。当前金融策略专属于本产品；工具留在tools内部，公共实机入口直接复用，不另建host/DLL/启动器。未来有第二个消费者时再提取稳定Java模块，避免在接口未验证前扩散原型。
