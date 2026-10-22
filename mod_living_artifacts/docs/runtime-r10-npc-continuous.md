# R10：NPC 连续培养保存点记录

R10 原场次结果为 **BLOCKED**，实际推进 **47 个自然日**、接纳 **4 份保存点观察**。四候选初始绑定和两名 NPC 的存档装备转换通过，成长、训练与喂养尚未通过。表中状态只证明各保存点，不能作为当前原生状态或保存点之间持续装备的证明。

- `machine_id`：`pc-20260924rtuf-f11af23c08`；本次身份命令实际读回工具 chunk `9d5ec4`。
- `run_id`：`pc-20260924rtuf-f11af23c08--living-artifacts--R0010`；冻结执行树 `c13` / `abcfefeda3f2d140a80b6c161e15f9215c859938`。
- 准备与 keeper：`living-npc-a13`；公开入口原 session `74600`，分配原 session `42192`，均由 Root 保有并负责最终实际等待。
- 此次汇总观察时间：`2026-10-22T14:58:28.687502+00:00`；已接纳保存点数量：`4`。
- 精确 envelope、原存档来源、帧身份与每项标记原值见[保存点来源索引](evidence/r10-saved-checkpoint-summary.json)。

这里只读取已经产出的 observation JSON，经真实 `NpcSavedObservation.parse` 校验闭合字段、内部一致性与保留来源 pin；没有重新执行完整存档投影，也没有发送游戏动作。初值完整只表示保存的验收输入齐备，四候选角色的资格与最终结论仍由原 case 独立决定。

| 保存点 / 存档日期 | 健康角色 / 角色 ID | 目标 ID / 存档装备 slot | L / 本级 XP / growth sequence | 训练标记 / 喂养印记 | 材料状态 |
| --- | --- | --- | --- | --- | --- |
| 01 / 1066.9.15 | landed / 36893 | 402 / 空 | 1 / 0 / 0 | 缺失 / 缺失 | common=owned；masterwork=owned；famed=owned；illustrious=owned |
| 01 / 1066.9.15 | baron / 45602 | 407 / 空 | 1 / 0 / 0 | 缺失 / 缺失 | common=owned；masterwork=owned；famed=owned；illustrious=owned |
| 01 / 1066.9.15 | courtier / 37986 | 412 / 空 | 1 / 0 / 0 | 缺失 / 缺失 | common=owned；masterwork=owned；famed=owned；illustrious=owned |
| 02 / 1066.9.16 | landed / 36893 | 402 / 空 | 1 / 0 / 0 | 缺失 / 缺失 | common=owned；masterwork=owned；famed=owned；illustrious=owned |
| 02 / 1066.9.16 | baron / 45602 | 407 / 空 | 1 / 0 / 0 | 缺失 / 缺失 | common=owned；masterwork=owned；famed=owned；illustrious=owned |
| 02 / 1066.9.16 | courtier / 37986 | 412 / 空 | 1 / 0 / 0 | 缺失 / 缺失 | common=owned；masterwork=owned；famed=owned；illustrious=owned |
| 03 / 1066.10.1 | landed / 36893 | 402 / weapon | 1 / 0 / 0 | 缺失 / 缺失 | common=owned；masterwork=owned；famed=owned；illustrious=owned |
| 03 / 1066.10.1 | baron / 45602 | 407 / 空 | 1 / 0 / 0 | 缺失 / 缺失 | common=owned；masterwork=owned；famed=owned；illustrious=owned |
| 03 / 1066.10.1 | courtier / 37986 | 412 / 空 | 1 / 0 / 0 | 缺失 / 缺失 | common=owned；masterwork=owned；famed=owned；illustrious=owned |
| 04 / 1066.11.1 | landed / 36893 | 402 / weapon | 1 / 0 / 0 | 缺失 / 缺失 | common=owned；masterwork=owned；famed=owned；illustrious=owned |
| 04 / 1066.11.1 | baron / 45602 | 407 / weapon | 1 / 0 / 0 | 缺失 / 缺失 | common=owned；masterwork=owned；famed=owned；illustrious=owned |
| 04 / 1066.11.1 | courtier / 37986 | 412 / 空 | 1 / 0 / 0 | 缺失 / 缺失 | common=owned；masterwork=owned；famed=owned；illustrious=owned |

“空”表示该保存点没有目标装备 slot；“缺失”表示字段不存在，不把它改写为显式 0 或已触发。材料 `gone`、`owner_changed` 与引用缺失分别保留，单凭消失不能认定已喂养。整数值按既有 Q100000 消费者解码，原始标记及引用类型保留在源 JSON。

额外检查了四份 observation 中三名健康角色的 `xalw_monthly_chain`、`xalw_last_owner_month`、`xalw_ai_review_queued` 与 `xalw_training_cooldown`：全部缺失，不能改写为显式 0。各保存点的原始 presence/value 均在索引 `owner_monthly_ai_variables` 中单独保存。

日志只读复核于 `2026-10-22T14:44:05.080284+00:00`：完整抓取 262 行、91 个 header，连同续行 stack 筛出 28 个含 `xalw` 的记录，均为启动静态“set but never used”警告；含 `xalw` 的运行时或未分类记录数为 0。原始抓取与分类回执另存外置目录并绑定于来源索引；首次抓取没有先前字节 baseline，不能写成“新增错误 0”或证明月度链已执行。

原最终 case 结果已出现，精确原结果投影与来源 pin 见 JSON；本表自身不授予业务通过。

原结果 `status=BLOCKED`，`actual_natural_days=47`，`actual_saved_observations=4`，预算计入公开调用 `194`；`case_contract_qualified=False`、`business_pass=False`、`product_release_pass=False`，保持原值。

| 原检查 ID | 原结果 | 原原因 |
| --- | --- | --- |
| NPC-BIND-landed | PASS |  |
| NPC-BIND-baron | PASS |  |
| NPC-BIND-courtier | PASS |  |
| NPC-BIND-fragile | PASS |  |
| NPC-EQUIP-landed | PASS |  |
| NPC-GROW-landed | BLOCKED | No retained same-owner equipped Oct1-to-Nov1 settled growth increase |
| NPC-TRAIN-landed | BLOCKED | No new exclusive training marker with growth evidence |
| NPC-FEED-landed | BLOCKED | Disappearance/owner change alone cannot prove feeding; require new exclusive feed imprint and growth |
| NPC-EQUIP-baron | PASS |  |
| NPC-GROW-baron | BLOCKED | No retained same-owner equipped Oct1-to-Nov1 settled growth increase |
| NPC-TRAIN-baron | BLOCKED | No new exclusive training marker with growth evidence |
| NPC-FEED-baron | BLOCKED | Disappearance/owner change alone cannot prove feeding; require new exclusive feed imprint and growth |
| NPC-EQUIP-courtier | BLOCKED | No initial-unequipped to actual saved equipped transition; existing equipment is not a new action |
| NPC-GROW-courtier | BLOCKED | No retained same-owner equipped Oct1-to-Nov1 settled growth increase |
| NPC-TRAIN-courtier | BLOCKED | No new exclusive training marker with growth evidence |
| NPC-FEED-courtier | BLOCKED | Disappearance/owner change alone cannot prove feeding; require new exclusive feed imprint and growth |

本场正常闭场已完成，业务 BLOCKED 原值不变。`normal-close-result.json` 记录保留 OS 句柄退出码 `0`、原生退出码 `0`、`cleanup_proven=true`、`host_error=null`、`normal_close_qualified=true`；原生完成于 `2026-10-22T15:01:06.951288Z`。原 host 的原始 `Popen.wait()` 也实际返回 `0`。退出后最终观察明确为 `not_applicable` 且 `alive_or_business_credit=false`。

Root 等待原公开 run session `74600` 实际返回 `0`（工具 chunk `064054`），随后于 `15:01:58.138517Z` 写入 cooperative STOP，文本分别记录实际 host/public 退出码。原 allocate session `42192` 也实际等待返回 `0`（chunk `147e2c`）；keeper 原回执保留 `last_sequence=495`、`thread_exited=true`、`failure=null` 与 `screen_released=false`。之后独立 CAS 释放回执为序号 `496`、`state=done`、`resources=[]`，不能把 keeper 自身回执误写为已释放屏幕。

后台 Steam 离线探测于 `2026-10-22T15:02:19.789838Z` 读回 `status=offline / offline_mode=true`。同日 `15:02:19.620978Z` 的统一存储闭场检查记录 `deletions=0`；只覆盖本次账本范围，不声称自动回收或重型写入准入。

场中婚姻 interaction 实例 `16777231` 依既有策略执行 `reject`。原动作步骤 `root-r10-interaction-reject-01`、独立后验 `root-r10-interaction-post-01` 与 Root 续行回应分别保留来源；原实例独立确认已消失，续行成功。此项只证明通知处理和推进续行，不能充作 NPC 培养通过。

闭场后重新只读抓取本场 error.log：原 `14:44:05.080284Z` 抓取是当前文件的完整前缀，后续追加 547 字节，其中新含 `xalw` 的 header 记录 0 条；闭场全日志含 `xalw` 的运行时或未分类记录 0 条。新增原始字节另行保留，未覆盖首次抓取；这些结果仍不表示缺失的月度 AI 链已执行。原 case 写入早于退出，保留的 `normal_close_pending=true` 没有回写；以上闭场事实由独立原始证据说明。

所有闭场来源 pin、实际等待工具来源与环境观察时间见本场 JSON 索引。收口阶段只追加这些记录，没有重新投影完整存档、重跑保存解析或发送游戏动作。上场消费者修复及其限制见 [R9 记录](runtime-r9-npc-consumer-block-and-normal-close.md)。本场不授予产品发布通过。
