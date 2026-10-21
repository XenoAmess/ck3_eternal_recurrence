# 全新机器的第一次公共验收分配

2026-10-22。为活武器开发在全新执行机部署公共验收环境时发现：现有 `--first-machine-bootstrap` 仅接收真实 legacy 场次的闭场资料，没有“从未分配过实机编号”的入口。公共 allocator 现支持 `ck3-mod-acceptance-fresh-machine-bootstrap-v1`，仍使用同一 CLI 参数、机器 admission 锁、canonical ID allocator 与 keeper，不建立产品私有启动器。

新 schema 明确声明没有前场：`previous_session_closed=false`、`previous_screen_released=false`、`previous_normal_exit_claimed=false`。它不是正常退出证明。分配时读取当前 OS 机器绑定、canonical 历史、任务总线和进程；任何旧编号、失败的 admission intent、既有共享分配或屏幕占用都拒绝新机路线。bootstrap 同时固定共同 runtime mapping/manifest 的路径、大小和 SHA。首次分配成功后，启动器再核唯一的机器 admission `000001` 与真实 canonical live 记录；第二场必须走正常前驱闭场链。

实现是 [共享合同](../../tools/ck3_mod_acceptance_fresh_machine_bootstrap.py)、[allocator](../../tools/ck3_mod_acceptance_allocate.py) 和 [launcher](../../tools/ck3_mod_acceptance_launcher.py)。[回归](../../tools/test_ck3_mod_acceptance_fresh_machine_bootstrap.py)使用临时机器命名空间执行真实编号生产与消费往返，覆盖错机器、漂移 pin、bool/float 序号、旧记录、假前驱、在用进程、屏幕占用及第二次分配拒绝；没有启动游戏或授予业务 PASS。原 legacy bootstrap 规则保持。

本次验证机器 `machine_id: pc-20260924rtuf-f11af23c08`，观察时间 2026-10-21T19:52Z，来源为本次工具执行与外置 `D:/workspace/ck3-living-artifacts-20261022/environment/`。新增 12 项回归、既有 legacy 10 项、launcher 10 项、helper 闭包 18 项通过；新合同、测试及 helper 类型文件通过实际严格 mypy。allocator/launcher 的历史未标注部分未据此宣称整体严格类型通过。游戏实际初始化和业务验收另记。

同日补充：首次启动前可能需要修复安装或维护Steam。已有屏幕历史只有在逐项提交 `maintenance_closures` 原件pin，证明原始登记就声明 `maintenance-only:no-game-start`、从未分配canonical实机编号、维护前后CK3双源清单为空、任务实际释放并保持该释放头时，才可作为纯维护epoch放行。两份清单及动作结果各自必须有匹配的machine_id和有序UTC时间；不拿外层机器字段推认原件所属机器。当前屏幕占用、原件漂移、缺少声明和真实游戏历史仍拒绝，旧legacy规则不变。增量回归累计15项通过，新合同及测试仍通过严格mypy。

第二次补充：对早于上述原件字段合同的纯维护记录，另有显式`maintenance-screen-declaration-v1`。它保留`raw_observation_identity=unknown`及原件pin，只证明该屏幕epoch事前声明维护且已真实释放，不使用身份未核的旧清单证明同机、旧游戏退出或过去的进程状态。声明自身有当前machine_id/UTC；首次游戏分配仍只依赖当前OS身份、无canonical/shared实机历史、当前进程及资源守卫和原子首次编号。它不降级严格原件闭场schema，也不能用于普通第二场或绕过在用CK3。累计16项回归与修改文件严格类型检查通过。

第三次补充：首次分配的当前进程守卫同时读取所绑定共同源码的tasklist、Toolhelp和psutil清单，使用严格的`FreshCurrentProcessObservation`字段合同拒绝缺失、错类型、非空或来源不可用。这是分配当时的新鲜观测，不授予历史维护记录退出信用。累计17项回归通过；本次增量的合同、helper与测试通过严格mypy。legacy allocator以同一`--check-untyped-defs`参数对基线和当前各检查一次，均为64项既有问题，归一化增量为空，未声称整个allocator通过严格类型检查。当前机器及实际命令证据见外置`environment/allocator-type-scope/result.json`。

2026-10-22补充：首次分配在canonical ID产生之前，可能已写入机器和profile intent后抛出未知内建mod key异常。现在先验证`runtime_mod_key`与`external_mod`，任何新unknown key均在消耗intent前拒绝；已存在的此类失败仅支持显式`allocate --retire-pre-identity REQUEST --first-machine-bootstrap PROPOSAL`。其余五种公共模式拒绝退役参数，不增加私有runner。

`create_pre_identity_request()`冻结原command/空stdout/原traceback、带机器与时间的后续Root工具观察、实际原terminal tool event、原机器intent、原profile ledger intent、原ID源码与products registry。运行时要求九份原件pin精确，原源码确实不认识该key，stderr恰为该源码的unknown-key终态，唯一原tool返回exit1并绑定同operation/stderr。Root后续观察不是历史HANDLE wait；request、退役marker均不证明游戏正常退出。缺少原terminal、bool代替exit整数、错机器、原件漂移、原异常不符、任何allocation结果或keeper/已玩profile均拒绝。

制作新proposal时，`create_bootstrap(..., pending_pre_identity_retirement=Path(REQUEST))`只校验原件并容许准备，不能自行退役。公共allocate在当前双源CK3、psutil runtime/controller及durable bus空守卫通过后，持原`chain.lock`排他追加`000001/retired-pre-identity.json`；保留原`intent.json`与`single-use-ledger/allocation-intent.json`。随后仍在同canonical namespace登记`000002`，使用`single-use-ledger/pre-identity-epoch-000002/`新ledger，经原canonical allocator申请真实首`R0001`。退役marker明确`canonical_id_allocated=false / normal_exit_proven=false / business_pass=false`；任何已有canonical ID或第二个未解决intent均不能借此重置。launch再次复核000001退役原件、000002实际分配及唯一canonical记录，正常前驱与legacy守卫不变。

本机`machine_id: pc-20260924rtuf-f11af23c08`的2026-10-21T20:40Z真实失败原件保留于外置`environment/public-operations/20261021T204017894355Z-allocate/`。原terminal在20:40:21.019Z返回exit1，未产生canonical ID/keeper/game；后续原件校验成功不表示已退役或已验收。新增[五项回归](../../tools/test_ck3_mod_acceptance_pre_identity.py)使用真实失败allocator子进程及真实ID生产者，覆盖000001→退役→000002/首R0001→JSON往返launch消费、保留原字节和拒绝边界；没有运行游戏。
