# R9：NPC 存档消费者阻断与正常闭场

R9 的 NPC 业务验收结果为 **BLOCKED，新增自然日 0，AI 实机未通过**。场次后来完成了普通游戏界面退出，保留进程句柄确认 CK3 OS 退出码 0，原生报告确认退出码 0 与清理完成，原 host 和公开入口也各自实际退出 0。这些退出结果不能抵扣 NPC 装备、喂养或成长验收。

- `machine_id`：`pc-20260924rtuf-f11af23c08`；2026-10-22 重新运行 `tools/ck3_live_run_id.py machine` 核对。
- `run_id`：`pc-20260924rtuf-f11af23c08--living-artifacts--R0009`。
- 冻结执行树：外置 `runtime/c12`，提交 `3a7b1c1dda1eaf33dc8625fa1835c9ab1f766114`；场次内没有热改该树。
- 业务结果观察于 `2026-10-22T13:41:12.169307Z`；原生退出完成于 `14:10:46.618384Z`；闭场后台离线复核于 `14:12:57.385699Z`。日期均为 2026-10-22，时间均为 UTC。
- 外置证据根目录：`D:/workspace/ck3-living-artifacts-20261022`。精确路径、字节数、SHA-256 和观察范围见[本场来源索引](evidence/r9-observation-index.json)。该记录只证明上述机器和时刻。

原场次为何没有取得 NPC 业务结果

正常地图、角色绑定与第一份存档生产已完成。`checkpoint-readback-01-root-result.json` 为 `completed`，绑定游戏 PID `2008`、连接世代 `1`、玩家 `31254`、原生日期 `53144328`，保存了原存档、严格解码结果及解码器来源。实际原存档为 70,955,418 字节，解码结果为 104,301,635 字节。因此，业务结果中的 `actual_saved_observations=0` 表示消费者未接纳一份 NPC 观察，不能写成“没有保存”或“解码器未成功”。

随后真实消费者在 `NPC-BIND-landed` 拒绝：`Exact saved character reference required: NPC owner landed`。引擎实际将角色引用序列化为 `type=char`，旧消费者和手写夹具却使用了 `character`。原结果保留 `status=BLOCKED`、预算计入的公开调用数 `2`、`actual_natural_days=0`、`current_native_npc_equipment=false`、`business_pass=false` 和 `product_release_pass=false`。原结果写入时的 `normal_close_pending=true` 也原样保留；退出由后来独立生成的闭场证据说明，没有回写旧业务结果。

离线修复取得的结果

消费者修复已入主线提交 `de99f4d38c6693feb0f0a081efac36a8e9b1991f`（rebase 前为 `00588760b`）。共享角色引用解码按实际 `char` 标签、缺省 flag 与规范十进制身份读取，观察器、候选角色绑定及 JSON 消费者保持同一合同；引擎发出的数据没有改写。与选定目标、基线和 NPC 库存无关的无角色所有者世界神器可跳过；选中的既存无角色所有者神器仍明确拒绝，不能推断为已消失或已喂养。

离线重读原场次的 Root 回应时，未修改的统一存档来源校验通过，修复后的消费者从原始完整解码存档读出了三名健康 NPC 的完整初始输入与四个候选角色绑定。旧消费者的原始拒绝也得到复现。真实记录节选保存为[约 67 KB 回归夹具](../tools/fixtures/r9_npc_saved_reference_excerpts.json)：叶节点来自 R9，外层存档文本包装明确为手写；它不代表重放完整世界或推进了游戏。历史测试回执记录 CRLF 原字节 67,258 字节，当前 Git 工作树为 LF 的 66,954 字节；将当前换行编码为 CRLF 后精确匹配历史 SHA-256。两份原字节 pin 在来源索引中分别记录，历史回执未改写。

[修复回执](evidence/r9-npc-reference-consumer-repair.json)记录了实际执行的两完整 NPC 测试模块 28 项、完整产品发现测试 165 项，以及当时全部 39 个产品 Python 文件的 strict 检查，均退出 0；这些检查未在本次文档整理中重复运行。其范围是历史文件重新解析及离线回归，**不是新场次 AI 实机通过**，也没有把 R9 的自然日从 0 改大。

本次额外核验了当前 LF 夹具、当前 Git blob 与下一冻结执行树 `c13` 的原字节完全一致。原完整存档及解码存档仍可读取且来源 pin 匹配；从原完整解码存档重新抽取的 41 个变量/库存叶段、21 个神器叶块与夹具逐项精确相等，夹具 JSON 往返也相等。针对这份当前 LF 输入，实际执行了“真实 R9 引用→观察器→JSON 消费者”和“真实引用节选→producer→公开 Root→两 NPC 消费者”两个现有回归，结果 `2 tests / 0.873s / exit 0`。该窄范围复核没有重跑完整 165 项，也没有发送游戏动作。

旧提取目录实际仅保留 `project.py`、`result.json` 与 `selected-projection.ck3`，没有识别到独立保存的旧 CRLF JSON 原件；旧工作副本已随 Git 重放变为 LF。本次没有重建同名“旧原件”，来源索引明确保留历史 raw pin、当前 raw pin 及此次复核回执。

正常退出与资源释放

| 独立层次 | 实际证据与结论 |
| --- | --- |
| 普通退出界面 | Root 直接查看退出确认图并经正常 GUI 退出；这份人工审阅自身没有声称 OS/native 已退出。 |
| CK3 OS 后态 | 原先保留的同步/查询句柄确认 PID `2008` 已结束，退出码 `0`。 |
| 原生后态 | 原生 `process_exit_code=0`，`tree_gone=true`、`cleanup_proven=true`，原生完成时间 `14:10:46.618384Z`。 |
| host | 原 host PID `9376` 的原始 `Popen.wait()` 返回 `0`，记录于 `14:10:50.199607Z`。`native-report.json` 的 host 状态为 `GREEN`，`cleanup_ok=true`。 |
| 公开入口 | Root 对原 session `73737` 的实际等待返回 `0`；该事实另记入 cooperative STOP 文本，不以新的包装命令退出码代替。 |
| 退出后采样 | `snapshot_final`、`diagnostics_final` 和 `final_observation` 为 `not_applicable / finished_native_process_exit_zero_cleanup_proven`，`alive_or_business_credit=false`，没有最终采样错误。 |
| keeper | 原 session `96839` 实际退出 `0`；回执 `last_sequence=476`、`thread_exited=true`、`failure=null`。keeper 回执自身的 `screen_released=false` 保留。 |
| 屏幕资源 | 随后的 Root CAS 释放回执序号 `477`、`state=done`、`resources=[]`，时间 `14:12:56.681464Z`。 |
| Steam | 后台探测 `status=offline`、`offline_mode=true`，观察时间 `14:12:57.385699Z`。 |
| 存储闭场 | `14:13:28.406552Z` 的统一策略检查记录 `deletions=0`；只覆盖账本列出的资产组，不表示自动回收器已部署或重型写入已获准。 |

R9 的 host 步骤均成功；本场不能单独证明 R8 那种已有失败行的退出分支已在新实机覆盖，也不能证明原生 V2 退出提交在本场实际调用。这里的正常关闭资格仅来自本场各层原始退出与清理证据。

下一次实机仍须完成的范围

修复后的 NPC 消费者需要进入新的冻结场次，以实际自然推进、独立存档和原生读回验证 NPC 获取、装备、培养及材料消耗。R9 不给这些业务记 PASS。管理页的喂养预览、取消不消耗、正常成长显示及镇压 tooltip 也须按新的管理界面复验安排验证；旧 [R8 实测及显示缺陷](runtime-r8-continuous-growth-and-feeding.md)仍保留其原结论。后续入口见[喂养预览操作卡](feeding-preview-runbook.md)与[最小发布验收范围](minimum-release-acceptance.md)；它们是待执行范围，不是本场通过记录。

本场 `product_release_pass=false`，没有由这份记录宣告发布完成。
