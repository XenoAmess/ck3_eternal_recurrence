# R40 公共运行时冷载启动 RED（2026-10-10）

`bf-202609141645-5434332d4d--li-yu-dao--R0040` 的 600 秒 readiness 实际仍超时，公共 `run` / 首次只读 `verify` 均退出 2；host 原始父句柄与受管 CK3 均退出 1，**normal exit 0 未证明**。原 report `steps=[]`，未进入产品业务，未执行选项、提交或保存。不能把准备/预检成功、地图候选帧出现或进程清理成功记为 case 验收通过。

本轮固定 checkout `598d4855b1a5e7678fa2253e5664acb991c0c825`，继续使用本机 Source03 `C:/csr3` 与 Source02 native `C:/cbr2`；host、DLL、injector pin 均与 R39 相同。独立 case 为 `lyd-transaction-control-20261010-002`，`prepare` / `preflight` / `allocate` 的实际退出均为 0。输入 provenance 保留相同 R34 D2a checkpoint、正式产品和 overlay，仅使用新 state 目录；冻结 argv 实际为 `--readiness-timeout 600`。本轮从 R39 的 `previous-shared-managed-session` regular closure 准入，没有重复使用 first-machine bootstrap。

R40 的最终门禁与 [R39](2026-10-10-r39-shared-runtime-startup-red.md) 不同。只读原件复核共 413 次 saved observations：前 363 次 `map_ready=false`；后 50 次出现非空 admission candidate，`map_ready=true`、local player 1、alive actor 31254、date 53144712、active event instance 121。它们不是事件定义、根身份或 typed options 全部通过的证明：50 个 frame 的 `pump_epoch` 均为 27770，未满足“同一 owner 的第二个相等帧且 pump 严格推进”条件，因此 campaign-root query、binding 和 startup handler 均未到达，未取得完整事件准入 proof。

原 wire 只有两份 state snapshots。后段 heartbeat sequence 2244→2394 仍递增，但 mailbox pump 停留在 27770，observer 完成时间也未继续变化。已有游戏日志进入读档后，未记录 `In Game` 或 setup completion；后段有效 map/actor/event candidate 本身不能替代日志的 loading completion 证据。只读诊断提出“注入时序可能影响进度”的待验证假说，但 R38 与 R40 还存在 DLL 和 debug CLI 等差别，不能据此断言因果或底层错误。

公共 case 保留 `TimeoutError: Original case readiness budget elapsed`，host 最终保留 saved-campaign exact identity/root/event-policy readiness 超时。只读 `verify` 原文为 `NOT_RUN_OR_PRESERVED_FAILURE`、`normal_close=null`，case/qualified/business/product pass 均为 false。不会增加预算重跑，R39 的原 400 秒失败也不改写。默认关闭的延后单次注入对照属于后续独立工作，本报告没有把它记为已执行或成功。

| 实际闭场项 | 结果 |
| --- | --- |
| host 原始 `Popen.wait()` / CK3 | 分别退出 1 / 1，未推断 normal 0 |
| 受管清理 | `tree_gone=true`、`cleanup_proven=true`，job 最终活动数 0 |
| 最终进程 / 控制文件 | CK3 清单为空；指定四项控制文件 absent |
| keeper 原父句柄 / join | 退出 0，thread exited，不替代 CK3 退出证明 |
| Steam / 桌面 | 位移后的原图可见 2026-10-10 4:56 及“离线模式”；显示恢复 1024×768 |
| release-command-001 | 带精确 CLI pin，实际退出 0，CAS 4234→4235，resources=[] |

首次外置观察脚本 001 因未完成 report 的空值访问报错；原脚本及 002 的空值修正、003 的精简派生全部保留。该次错误没有独立保存的实际 stdout/stderr 原件，本包不补造失败日志。显示、人工 nonce 审阅、闭场及 successor-inputs 的作者脚本与 derivation pin 一并封存；它们不新增本轮业务动作。后续新 run 须使用 R40 regular closure，并按新尝试的准入规则重新核验。

[RAW-EVIDENCE.zip](acceptance/2026-10-10-r40-shared-runtime-startup-red/RAW-EVIDENCE.zip) 保留 run 全部 140 文件、keeper 全部 69 文件、16 份 profile 日志、30 份 case 准备/预检/分配/输入及来源文件、诊断包、作者脚本与实际机器准入记录，共 280 项、8854584 字节，SHA-256 `ca834f64c4c3cc4d8d68cc2c3608351dd996ffbbc84e7d00994ce06dafe5e1ec`。原始 PNG 未改；91711686 字节的存档正文不入包，仅 pin SHA-256 `a6db85e38ba0648eca4b7e835c79d867b96ca26099698f4d4ee5269b818d822c`。不重复封装 R39 整包；54 项相关测试及 exact CI 见 [独立证据索引](acceptance/2026-10-10-exact-598d4855b-ci-and-rebase-tests/INDEX.json)。

[INDEX](acceptance/2026-10-10-r40-shared-runtime-startup-red/INDEX.json) 固定每项实际来源、大小与 SHA；[FACTS](acceptance/2026-10-10-r40-shared-runtime-startup-red/FACTS.actual.json) 摘录退出与释放事实；[VALIDATION](acceptance/2026-10-10-r40-shared-runtime-startup-red/VALIDATION.actual.json) 已核 ZIP 成员/CRC、全部归档及原件 SHA、诊断 INDEX pins、命令 stdout/stderr 和脚本派生 pins。[producer](acceptance/2026-10-10-r40-shared-runtime-startup-red/package_evidence.py) 只封存既有文件。证据一致不等于业务通过。
