# R12：NPC 连续培养保存点记录

原 NPC case 结果为 **PASS**，实际推进 **47 个自然日**，取得 **4 份保存观察**。各项判定保留原 case 结果，见下表；本汇总不另授业务或发布资格。

- `machine_id`：`pc-20260924rtuf-f11af23c08`；本次实际身份命令 chunk `2b0e7a`。
- `run_id`：`pc-20260924rtuf-f11af23c08--living-artifacts--R0012`；冻结执行树 `c15` / `e00c7a73aeb393c16cade4ae5e0e289f47417ad7`，keeper `living-npc-a16`。
- 原 host PID `1524`、原保存帧 game PID `11180`；本次汇总时间 `2026-10-22T17:19:31.562881+00:00`。
- 精确四份 envelope、保存原件/melted 来源、帧、变量原编码、逐保存差异及最终原结果见[来源索引](evidence/r12-saved-checkpoint-summary.json)。

复用 R10 汇总脚本的 `role_row` 和共享 `NpcSavedObservation.parse`，仅解析已经产出的四份小型 JSON，没有重读完整存档，没有发送游戏动作。数据是各保存日期的历史状态，不证明当前原生装备状态，也不证明两保存点之间一直装备。

| 保存点 / 存档日期 | 健康角色 / 角色 ID | 目标 ID / 存档装备 slot | L / 本级 XP / growth sequence | 训练标记 / 喂养印记 | 材料状态 |
| --- | --- | --- | --- | --- | --- |
| 01 / 1066.9.15 | landed / 34967 | 402 / 空 | 1 / 0 / 0 | 缺失 / 缺失 | common=owned；masterwork=owned；famed=owned；illustrious=owned |
| 01 / 1066.9.15 | baron / 45576 | 407 / 空 | 1 / 0 / 0 | 缺失 / 缺失 | common=owned；masterwork=owned；famed=owned；illustrious=owned |
| 01 / 1066.9.15 | courtier / 53351 | 412 / 空 | 1 / 0 / 0 | 缺失 / 缺失 | common=owned；masterwork=owned；famed=owned；illustrious=owned |
| 02 / 1066.9.16 | landed / 34967 | 402 / weapon | 5 / 0 / 4 | 存在 / 存在 | common=gone；masterwork=gone；famed=gone；illustrious=owned |
| 02 / 1066.9.16 | baron / 45576 | 407 / weapon | 4 / 205 / 3 | 存在 / 存在 | common=gone；masterwork=gone；famed=gone；illustrious=owned |
| 02 / 1066.9.16 | courtier / 53351 | 412 / weapon | 4 / 205 / 3 | 存在 / 存在 | common=gone；masterwork=gone；famed=gone；illustrious=owned |
| 03 / 1066.10.1 | landed / 34967 | 402 / weapon | 5 / 8 / 4 | 存在 / 存在 | common=gone；masterwork=gone；famed=gone；illustrious=owned |
| 03 / 1066.10.1 | baron / 45576 | 407 / weapon | 4 / 213 / 3 | 存在 / 存在 | common=gone；masterwork=gone；famed=gone；illustrious=owned |
| 03 / 1066.10.1 | courtier / 53351 | 412 / weapon | 4 / 213 / 3 | 存在 / 存在 | common=gone；masterwork=gone；famed=gone；illustrious=owned |
| 04 / 1066.11.1 | landed / 34967 | 402 / weapon | 5 / 16 / 4 | 存在 / 存在 | common=gone；masterwork=gone；famed=gone；illustrious=owned |
| 04 / 1066.11.1 | baron / 45576 | 407 / weapon | 4 / 221 / 3 | 存在 / 存在 | common=gone；masterwork=gone；famed=gone；illustrious=owned |
| 04 / 1066.11.1 | courtier / 53351 | 412 / weapon | 4 / 221 / 3 | 存在 / 存在 | common=gone；masterwork=gone；famed=gone；illustrious=owned |

“空”表示该保存点没有目标装备 slot；字段缺失与显式 0 分别保留。材料 `gone`、`owner_changed` 与引用缺失保持区别。喂养与训练检查来自原 case 对部署生产动作独占写入链、初值缺标记、后续新标记及经验增加的联合判定，不能单凭材料消失认定喂养。培养检查的范围是同角色、同物品在 10 月 1 日和 11 月 1 日保存中的装备与结算经验增加。

| 原检查 ID | 原结果 | 原原因 |
| --- | --- | --- |
| NPC-BIND-landed | PASS |  |
| NPC-BIND-baron | PASS |  |
| NPC-BIND-courtier | PASS |  |
| NPC-BIND-fragile | PASS |  |
| NPC-EQUIP-landed | PASS |  |
| NPC-GROW-landed | PASS |  |
| NPC-TRAIN-landed | PASS |  |
| NPC-FEED-landed | PASS |  |
| NPC-EQUIP-baron | PASS |  |
| NPC-GROW-baron | PASS |  |
| NPC-TRAIN-baron | PASS |  |
| NPC-FEED-baron | PASS |  |
| NPC-EQUIP-courtier | PASS |  |
| NPC-GROW-courtier | PASS |  |
| NPC-TRAIN-courtier | PASS |  |
| NPC-FEED-courtier | PASS |  |

原顶层字段保持 `case_contract_qualified=True`、`business_pass=False`、`product_release_pass=False`。本场不为实际健康/诅咒差值、秘密、真实训练费用、持续装备或当前原生 NPC 装备授予额外信用。

Root 已完成本场正常 GUI Quit。原 retained handle 读到游戏 OS exit0，原 native `process_exit_code=0` 且 cleanup/tree gone、job final=0；最终 native 报告 `GREEN` 于 `2026-10-22T17:25:11.208389+00:00` 完成。原 host wait0 与公开 run wait0 分别留有实际 Popen 回执，后者原 tool session `69514` / wait chunk `75d7d6`。keeper 于 `17:30:46.459485Z` 协作停止，last sequence=540、原 allocate session `75760` 实际 wait0（chunk `4df4ba`）；CAS seq541、done、resources=[]。后台 Steam 于 `17:31:16.743209Z` 实际 offline，闭场存储检查0删除。以上均绑定本场原回执和 machine_id，详细事实及图像/动作来源见同一索引。原业务结果中的 `normal_close_pending=true` 作为当时字段原样保留，后续闭场事实单独追加。

本场婚姻通知实际实例为 `16777344`、date_raw `53145312`，actor/recipient 为 `32569/31254`、secondary 为 `37107/38924`；命中既有 `arrange-marriage-reject-only-v1` 来源审查规则。原生拒绝于 `17:14:15.092034Z` 返回 `rejected`；独立 `root-r12-interaction-post-01` 于 `17:14:33.957002Z` 读到 pending=null。上下文、单次动作及后态各自来源均保留，未复用 R10 实例，未新增陌生事件。

完整 `error.log` 为 **7668 B、34 行/34 条 header、17 种精确签名**：24 条 NPC 夹具未使用变量、4 条产品辅助未使用变量、2 条 `historical_artifact` used-never-set，共30条静态诊断；另有3条 formatter 错误和1条原版 AI `activity_coronation` 创建诊断。未报告 error0，也未将4条非静态诊断当作已归因的产品失败。完整34条原文、类别、签名计数与原件 SHA 在索引 `complete_error_log_audit`。

3条 formatter 原 tag 为 `weak` + 控制字节 `08 15` + `positive_value`；索引保留第31—33行的原始 hex 及前后行。正式 staging、实际部署与当前生成的各9份 localization 文件逐字节一致，全文均未命中 `weak`、`positive_value` 或此混合坏 tag，产品脚本中的 `weak` 命中仅为原版弱宣称标识和注释，并非格式 tag；`feast.txt:38` 的 `ai_activity_coronation_check=yes` 与原版同一行完全相同（两文件各自 SHA 已保留，不声称全文相同）。因此没有定位到产品直接写出的坏 tag，缺少 key/stack 的日志仍不能排除动态取值或引擎运行拼接；当前没有已建立的产品专属复现路径。加冕项保留为原生 AI 外部诊断，不推断活武器导致或完全无间接影响。

独立只读 `root-r12-campaign-root-health-readonly-a01` 于 `16:54:14.819699Z` 实际完成，工具 `ck3_query_campaign_root_context_v1` 返回 available/accepted=true；玩家31254、date_raw53144328，health=`466160/100000`（`4.6616`），`player_health_ready=true`、`same_frame_ready=true`。原生构建来源为 CK3 1.20.0.4 / EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。只证明本场 c15 的基本玩家 health getter 可读；没有前后健康对照、没有诅咒干预，**不构成 curseDelta、NPC健康或重诅咒效果通过**。

脆弱角色本场仅验收真实候选绑定；三健康角色的保存观察不能外推到脆弱角色的培养、健康、秘密或费用。此次只补读现有文件，没有重测已绿业务，没有操作游戏/屏幕/MCP，没有修改运行时或发布状态。
