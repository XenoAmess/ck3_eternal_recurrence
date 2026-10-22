# R13：四档喂养预览、同场续行与正常退出

机器为 `pc-20260924rtuf-f11af23c08`，场次为 `pc-20260924rtuf-f11af23c08--living-artifacts--R0013`。本记录从 2026-10-22 UTC 的原始场次文件只读提取，精确观察时间、路径和 SHA-256 见[机器可读摘要](evidence/r13-feeding-preview-and-close.json)。没有重新执行业务或解析完整存档。

原 `case-output/living-artifacts-preview-result.json` 保留 **BLOCKED**，原因是独立库存查询未确认 GUI 可见性；17:48:26Z 的原 host 步骤 `xalw-core-0004` 被实际来源守卫拒绝。随后保持原 CK3 PID `7108`、出生时间 `1792690850.5543785` 和 connection generation `1`，通过已有[同场库存续行](preview-inventory-continuation.md)入口继续。`case-continuation-a01/preview-inventory-continuation-result.json` 于 **18:50:21Z** 记录本次续行 **PASS**；它不覆盖原 BLOCKED，也不授予整个产品发布通过。

原冻结运行时来自 c16，`frozen-argv.json` 绑定 `shared-source-a7bc6ebe6` 和 `runtime/c16`；续行单独声明了主仓 `preview_acceptance_adapter.py` 的实际源码 SHA `44fe45060f87ac37631fbfc79575fab7113ddd03be07484c8342e446c947517a`。这是保持游戏加载字节不变的 Python 续行，不能把后来的 c17 源码身份追记为本场原始运行时。

本场累计 **87 次计预算调用、5 个真实保存观察、0 个自然日**。玩家 `31254` 的活武器 `402` 在 `1066.9.15` 完成普通、大师级、名作级、卓越级四种材料的预览和喂养；日期在五个保存点保持相同。

| 保存点 | 已确认喂养 | 等级 / XP / 成长序号 | 尚存材料稀有度 |
|---|---|---|---|
| 01 | 初始 | 1 / 92 / 0 | common、masterwork、famed、illustrious |
| 02 | 普通，80 XP | 2 / 72 / 1 | masterwork、famed、illustrious |
| 03 | 大师级，200 XP | 3 / 72 / 2 | famed、illustrious |
| 04 | 名作级，500 XP | 4 / 272 / 3 | illustrious |
| 05 | 卓越级，1200 XP | 6 / 572 / 5 | 无 |

五次确认页均有 Root 直接查看原始 PNG、相应 capture、原生事件记录和独立 Root response。事件实例依次为 `3、5、7、9、11`；界面基础经验与本次经验依次均为 **80、80、200、500、1200**，材料名分别显示普通、普通、大师级、名作级、卓越级。摘要逐项绑定五份原图及其审阅记录；本记录没有 OCR，也没有编辑或另生成图片。

第一次普通材料确认页选择了“保留材料”。独立取消前后库存查询保留材料 `403`，随后回到管理事件；再次打开普通材料确认页后才正式喂养。取消后的 XP 没有独立的原生动态变量查询，原结果只把它纳入第一次喂养后的精确存档 XP 核对，不能扩大为单独的取消 XP 原生读回。四次喂养后的保存观察分别只剩三、二、一、零档材料，目标活武器始终存在；02–05 的独立原生读回均确认装备状态为 true。最终共鸣 `20`、耐久 `75.00000`、pending `0`。等级和 XP 来自真实保存观察，并结合独立原生 owner/equipment 读回，不能称为当前帧原生神器变量查询。

本场 `error.log` 读回为 **5350 B、24 条记录**，均归类为静态诊断；本模组运行时错误 `0`、未归类记录 `0`。此范围是本场实际打开的管理和喂养预览流程，不代表全部脚本和玩法已运行，也不抵扣 NPC、镇压到期、阈值、诅咒或冷加载验收。

19:03:46Z 的 Root 正常 GUI 退出记录绑定原图、未勾选自动保存和实际 Quit 操作。原持有进程句柄读回 **OS exit 0**；native 于 **19:03:59Z** 结束，`process_exit_code=0`、`cleanup_proven=true`、进程树与控制文件清除，原 `CaseClient` 的 `normal_close_qualified=true`。

退出结果仍须分层：原 host 进程实际等待 **exit 1**，`native-report.json` 的总体状态仍为 **RED**，唯一失败步骤仍是此前的 `xalw-core-0004` 库存打开来源拒绝。其最终观察为 `not_applicable / finished_native_process_exit_zero_cleanup_proven`，`host_error=null`、`failure_preserved=true`；没有新增的退出后 snapshot 故障。该 host 终态中的 `normal_close_qualified=false` 与原 `CaseClient` 的正常退出资格分开保留。外层 public 原进程实际等待 **exit 0**，不将它替换成 host GREEN。

Keeper 于 **19:04:52Z** 结束，原父进程实际等待 `0`、线程退出且无 failure；随后屏幕任务在 CAS 序号 `574` 进入 `done / resources=[]`。后台 Steam 回执于 **19:05:55Z** 确认本机 `offline / offline_mode=true`。

旧 `_runtime/living_service_checkpoints.py` 服务仍指向原 `case-output`、max `5`，未随续行自动结束。19:06:37Z 枚举确认 CK3 已无进程且原 public 已实际退出；再次核完整 argv、出生时间、父子关系及无活动 producer 子进程后，只显式停止这项只读 scheduler。实际 scheduler PID `12396` 的 Windows 等待返回 `15`，launcher PID `10556` 的等待没有取得退出码；Root 随后对原工具 session `73931` 实际等待也返回 **15**（chunk `344a57`）。两进程均已消失；这属于本任务只读服务显式终止，不能记为 OS0，也没有终止游戏、host 或 keeper。

本轮并行工作调整按 [AGENTS.md 第 533 行](../../AGENTS.md#自动游玩-agent价值优先与安全边界)补记于此：当天现有根日报没有活武器任务段落，故不改其他机器的 Java 日报。R13 续行与闭场记录完成，原失败保留；独立 c17 的 timer a21、curse a22 已实际执行 plan → prepare → preflight，六步均 exit `0`，固定来源分别读回 `151 / 162` 项，尚未 allocate/run。下一门槛是 Root 绑定真实前场身份后开展代表业务场，cold 仍等待真实 timer renewed checkpoint 来源。

Root 另在并行隔离整合 Java CI 的最小夹具修复，并由现有 storage 工作包进行人工时效复核；本记录不替这些工作声明 CI 或容量通过。R14 已由 Root 分配为本机 `R0014`，本次交接时等待新的 storage 操作卡正式启动，尚无 R14 业务结果。没有因等候 R13 闭场而重跑已通过检查或扩展验收范围。本包只新增本说明和专属摘要，由 Root 与 Java 工作包协调后统一提交；没有发布产品。
