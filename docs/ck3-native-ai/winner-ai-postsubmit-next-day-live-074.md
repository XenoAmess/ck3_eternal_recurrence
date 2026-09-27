# 1.19.0.6 胜方 AI 后备派令：次日仍未见位移

本页是 [072 终局后备提交](winner-ai-terminal-reentry-live-072.md) 的独立后续样本，
不是同一游戏进程或终局后 checkpoint 的延续。074 从同一原始 047 种子重新受管回放，
原版 EXE SHA-256 为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，
默认关闭、仅本次显式开启的私有观察器 DLL SHA-256 为
`E8FB321D985880EC3079E2BBC9406663457C2F790445751CEDDDE522F0412ED6`。
run ID：`desktop-3fevhd2-1c74096080--vanilla--R0066`。

074 在第 26 日的终局同帧完整匹配 072：CombatID `16777218`、WarID `4`、
胜方 CUnit `16777231`、`normal_result` sequence `5`；builder 对该 CUnit 的
返回 `+8=0/+9=0`（unhandled），内部主提交 `0` 次；外层 `0x1872611`
后备提交 `1` 次，目标 Province `2639`，原生队列返回 `accepted=true`。
第 25 日私有目标已经是 `2639`，公开路线为空；第 26 日路线为 `[2639]`。

| 观察时刻 | 原生日期 | 当前省份 | 公开/私有路线 | 目标省份 | 军队状态 | 新提交 |
| --- | ---: | ---: | --- | ---: | --- | ---: |
| 第 26 日终局暂停帧 | `53146992` | `2633` | `[2639]` / `[2639]` | `2639` | `sieging`、非战斗、非撤退 | 后备 `1` 次，入队接受 |
| 第 27 日自然推进后的暂停帧 | `53147016` | `2633` | `[2639]` / `[2639]` | `2639` | `sieging`、非战斗、非撤退 | 新 builder `0`、新 submit `0` |

第 27 日的原生位置**没有变化**，也没有到达目标 `2639`。公开快照和私有 CUnit
回读对位置、路线、目标一致；观察器 `failure_flags=0`，次日重复暂停快照稳定。
因此本样本只能确证“后备命令入队后一天仍显示原目标与路线，未见位移”。
它既不能证明命令已经进入 `CMoveArmyCommand` 的 apply，也不能证明命令未执行：
路线可能延续第 25 日之前的目标，移动可能受围攻或行军时间制约。一次队列 ACK
和次日非空路线都不是执行完成证据。

## 原始字段可见性与下一次取证

074 的第 27 日原始 `winner_army` row 只有 `current_province_id`、
`move_target_province_id`、`route_province_ids`、`army_state` 等公开字段，
**没有 ETA、MovePath 进度或 command apply 事件**。私有终局观察器只记录 builder
与 `0x973E00` 提交；其次日计数不变，不能反推已入队命令后来是否 apply。
`native_command_history` 是桥接器的查询/日更命令历史，本案第 26/27 日没有
`move` 项；它不是原版 AI 内部队列日志，不能拿这个“没有”判定原版 AI 没执行。

已存在的 `route_contact_horizon_v1` 可读**可控玩家军队**已提交 MovePath 的
`subject_route.arrival_date_raws`，但当前 mailbox 在
`route_contact_horizon_v1_mailbox.cpp:171-176` 要求 subject 出现在
`snapshot.player_armies` 且 `controllable=true`。本案胜方 AI 军队
`controllable=false`，不能把该正式查询直接套到它身上或把其他军队的 ETA
当作它的 ETA。下一次独立回放应先以只读私有方式有界核定该 CUnit 的原生
MovePath/首跳 ETA 可否安全回读；若仍无 ETA，就逐日读相同 CUnit 的原生位置、
路线与目标，以实际位置变化或路线消失/目标改变作观察终点，并设置有限天数上限。
即使位置改变，也需独立关联队列 apply，不能仅凭时间顺序归因给本次后备命令。

## 证据与可复核投影

外置不可覆盖目录：
`D:/workspace/ck3_native_war_ai_promo_work/episode01-winner-ai-postsubmit-movement-attempt-074/`。
冻结源档 SHA-256 为
`9B51A2FB20C7F931CF4E9F2A33F1E7598F517C4E793CE0CEFCFEF48C0D65BD2F`。
`audit-result.json` SHA-256
`234F9B863D4A813C2688BBC637E1EA13BD7ED9D261901A130A8185D751271DFA`，
31/31 项 GREEN；原始第 26/27 日暂停快照、终局查询、私有回读、每日 JSONL、
`probe-summary.json`、启动冻结、Steam 离线新鲜帧和受管清场均留在该目录。
`session-result.json` SHA-256
`797B90957FAC588CC12CAA4D264C9D66A30C1F71A65F506107B7DC4B26EE4032`；
capture exit 0、`cleanup_proven=true`、job 活跃进程 `0`，任务总线 CK3 资源已释放。

下一次有限日数回放的冻结设计见
[`winner-ai-postsubmit-076/plan.json`](research-plans/winner-ai-postsubmit-076/plan.json)：
在第 26 日先复核同一终局与后备接受，再最多自然推进 30 日，以原生位置变化、
目标/路线失效或经单独验证的原生首跳 ETA 为观察门；计划通过离线结构和证据
哈希校验，不代表 076 已实机执行。

给智能体消费的[冻结向量](research/winner-ai-postsubmit-next-day-074.json)
把 `post_queue_movement_executed` 保持为 `null`，不把单样本写成通用 AI 派令规则。
只读投影器同时校验外置原始响应 SHA、每日观察、终局对齐、DLL/EXE/源档身份、
31 项审计和清场：

```text
<verified-python> tools/project_winner_ai_postsubmit_next_day_074.py --attempt D:/workspace/ck3_native_war_ai_promo_work/episode01-winner-ai-postsubmit-movement-attempt-074
```
