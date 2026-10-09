# R39 公共运行时冷载启动 RED（2026-10-10）

`bf-202609141645-5434332d4d--li-yu-dao--R0039` 实际在启动 readiness 阶段超时，未进入 `transaction-only-control` 业务。公共 `run` 退出 2，保存 `TimeoutError: Original case readiness budget elapsed`；host 的原始父句柄退出 1，受管 CK3 退出 1。清理已证明，**normal exit 0 未证明**，本轮不增加 case、业务或公共运行时实机资格。

本轮固定 checkout 为 `00b88fc4df0b8b4cea8b15ff85de8f244825a329`，host 使用本机 Source03 `C:/csr3`；native 使用已成功构建的 Source02 / `C:/cbr2`。构建来源与固定二进制见 [本机公共运行时重建](2026-10-10-local-common-runtime-rebuild.md)。没有依赖不存在的 `C:/workspace/ck3-upgrade-20261008`。

冷载目标是固定 R34 D2a checkpoint，显式 startup contract 预期 `lyd_factory_diag.20`、instance 121、root/actor 31254、date 53144712、native option indices `[0]`。本次只允许先观察并准入已有事件。原 readiness 预算为 400 秒；实际 native report 的 `steps=[]`，typed executor 请求执行数为 0，未发生选项、产品查询、提交或保存业务动作。原失败、case-once 和全部输入快照保留，未重放已提交步骤。

只读复核得到 146 条 observations：均 `map_ready=false`、`local_player_id=0`、played character / active event 为 NULL，host 在首个地图/身份 guard 拒绝，未到 campaign-root query 或 startup handler。observer 的完成时间实际递增，读取可用；不支持把相同帧值解释为采集停止或 owner/commit 阻断。固定 `.4` core 的 readiness 条件涉及 `GetLocalPlayer` 非 NULL 与 `signed32(player+0x70)>=0`，原回执没有分别记录这两个操作数，具体原因仍为 UNKNOWN。

已有游戏日志证明进入 Load Save / InitPostRead，最后到 `Setup powerful vassals`，未记录 `In Game` 或 setup completion，`error.log` 为 0 字节。历史 R38 在相同阶段之后才完成。时序补包记录了 R38 launch→completion 417.147 秒，以及 R39 到 powerful-vassals 299.764 秒、原 deadline 401.928 秒；这支持后续单独评估 readiness 预算，不证明加时必成功，也不确定底层错误。Root 计划仅下一场使用 600 秒 readiness；本报告没有记录任何已发生的 R40。

| 实际闭场项 | 结果 |
| --- | --- |
| host 原始 `Popen.wait()` | 退出 1，未推断 CK3 normal 0 |
| 受管 CK3 | 退出 1；job 最终活动数 0，`tree_gone=true`、`cleanup_proven=true` |
| 最终 CK3 清单 / 控制文件 | 清单为空；四项控制文件均 absent |
| keeper 原父句柄 / join | 退出 0，thread exited；不替代 host 或 CK3 退出证明 |
| Steam / 屏幕 | 位移后原图可见“离线模式”；原显示恢复为 1024×768 |
| screen release 001 | 退出 3；缺 bus CLI SHA pin，`CAS_CONFLICT`，未释放 |
| screen release 002 | 带精确 pin，退出 0；CAS 4221→4222，resources=[] |

闭场后的首次只读公共 `verify` 实际退出 2，原文 `NOT_RUN_OR_PRESERVED_FAILURE`，`normal_close=null`，case/qualified/business/product pass 均为 false。没有补造 case result。本机 first-machine bootstrap 已绑定并消耗于 R39；后续须使用新 run 及 regular closure 准入，并保留本轮 exit 1 的事实。

外置原件是 `C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0039`、`keepers/20261010-a01` 和该 case 的 `state/profile/logs`。[RAW-EVIDENCE.zip](acceptance/2026-10-10-r39-shared-runtime-startup-red/RAW-EVIDENCE.zip) 含 run 全部 160 文件、keeper 全部 189 文件、16 份 profile 日志、原始 PNG、三个诊断包及作者脚本、实际机器准入记录和封存 producer，共 420 项、9303974 字节，SHA-256 `4b0bc61802a4d2946476d424c986a97d361413d23a51a694d00a3536e42ac707`。不含存档正文；`restored_campaign.ck3` 91711686 字节，SHA-256 `a6db85e38ba0648eca4b7e835c79d867b96ca26099698f4d4ee5269b818d822c`，仅 pin。

[INDEX](acceptance/2026-10-10-r39-shared-runtime-startup-red/INDEX.json) 固定每项来源、大小、SHA；[FACTS](acceptance/2026-10-10-r39-shared-runtime-startup-red/FACTS.actual.json) 摘录实际终态；[VALIDATION](acceptance/2026-10-10-r39-shared-runtime-startup-red/VALIDATION.actual.json) 证明 ZIP 成员/CRC、全部原件与解包 SHA、诊断原 INDEX pins 和目录文件数复验通过。[producer](acceptance/2026-10-10-r39-shared-runtime-startup-red/package_evidence.py) 只封存既有文件，不启动或修改运行时。证据一致不等于业务通过。
