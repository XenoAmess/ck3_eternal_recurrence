# 全新机器的第一次公共验收分配

2026-10-22。为活武器开发在全新执行机部署公共验收环境时发现：现有 `--first-machine-bootstrap` 仅接收真实 legacy 场次的闭场资料，没有“从未分配过实机编号”的入口。公共 allocator 现支持 `ck3-mod-acceptance-fresh-machine-bootstrap-v1`，仍使用同一 CLI 参数、机器 admission 锁、canonical ID allocator 与 keeper，不建立产品私有启动器。

新 schema 明确声明没有前场：`previous_session_closed=false`、`previous_screen_released=false`、`previous_normal_exit_claimed=false`。它不是正常退出证明。分配时读取当前 OS 机器绑定、canonical 历史、任务总线和进程；任何旧编号、失败的 admission intent、既有共享分配或屏幕占用都拒绝新机路线。bootstrap 同时固定共同 runtime mapping/manifest 的路径、大小和 SHA。首次分配成功后，启动器再核唯一的机器 admission `000001` 与真实 canonical live 记录；第二场必须走正常前驱闭场链。

实现是 [共享合同](../../tools/ck3_mod_acceptance_fresh_machine_bootstrap.py)、[allocator](../../tools/ck3_mod_acceptance_allocate.py) 和 [launcher](../../tools/ck3_mod_acceptance_launcher.py)。[回归](../../tools/test_ck3_mod_acceptance_fresh_machine_bootstrap.py)使用临时机器命名空间执行真实编号生产与消费往返，覆盖错机器、漂移 pin、bool/float 序号、旧记录、假前驱、在用进程、屏幕占用及第二次分配拒绝；没有启动游戏或授予业务 PASS。原 legacy bootstrap 规则保持。

本次验证机器 `machine_id: pc-20260924rtuf-f11af23c08`，观察时间 2026-10-21T19:52Z，来源为本次工具执行与外置 `D:/workspace/ck3-living-artifacts-20261022/environment/`。新增 12 项回归、既有 legacy 10 项、launcher 10 项、helper 闭包 18 项通过；新合同、测试及 helper 类型文件通过实际严格 mypy。allocator/launcher 的历史未标注部分未据此宣称整体严格类型通过。游戏实际初始化和业务验收另记。

同日补充：首次启动前可能需要修复安装或维护Steam。已有屏幕历史只有在逐项提交 `maintenance_closures` 原件pin，证明原始登记就声明 `maintenance-only:no-game-start`、从未分配canonical实机编号、维护前后CK3双源清单为空、任务实际释放并保持该释放头时，才可作为纯维护epoch放行。两份清单及动作结果各自必须有匹配的machine_id和有序UTC时间；不拿外层机器字段推认原件所属机器。当前屏幕占用、原件漂移、缺少声明和真实游戏历史仍拒绝，旧legacy规则不变。增量回归累计15项通过，新合同及测试仍通过严格mypy。

第二次补充：对早于上述原件字段合同的纯维护记录，另有显式`maintenance-screen-declaration-v1`。它保留`raw_observation_identity=unknown`及原件pin，只证明该屏幕epoch事前声明维护且已真实释放，不使用身份未核的旧清单证明同机、旧游戏退出或过去的进程状态。声明自身有当前machine_id/UTC；首次游戏分配仍只依赖当前OS身份、无canonical/shared实机历史、当前进程及资源守卫和原子首次编号。它不降级严格原件闭场schema，也不能用于普通第二场或绕过在用CK3。累计16项回归与修改文件严格类型检查通过。
