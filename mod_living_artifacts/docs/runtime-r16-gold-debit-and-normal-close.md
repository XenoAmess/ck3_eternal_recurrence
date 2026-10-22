# R16：金币扣款复验与正常闭场

`machine_id: pc-20260924rtuf-f11af23c08`，记录时间 2026-10-22T23:22:21Z。EXT 为 `D:/workspace/ck3-living-artifacts-20261022`。本场复用已冻结 c18 `5b1408fb3cc7b359eb5a43342861e8a521ab9d28`，不热改源码、SDK、Prepared 或原结果；经公共入口启动的 run 为 `pc-20260924rtuf-f11af23c08--living-artifacts--R0016`。

## 阈值业务结果

原 `case-output/living-artifacts-threshold-result.json` 实际记录 **PASS：47 自然日、257 次计预算调用、7 次真实保存、8 项全部 PASS**，`original_action_unknown=false`。八项为自动 L11、诅咒/饥渴投影、训练经验与钱包、训练压力、压制钱包/90 日期限、压制压力、装备持久化及跨月停级。

保存与同日原生读回一致：

| 检查点 | 状态 | 金币 | 威望 | 压力 |
| --- | --- | ---: | ---: | ---: |
| 03：训练后 | 1066.10.1，L11/XP25，装备中 | 743 | 2350 | 25 |
| 04：首次压制后 | 同日，期限389453、chain1、timer sequence1 | 668 | 2300 | 33 |
| 05：卸下 | 同日，L11/XP25 | 668 | 2300 | 33 |
| 06：重装 | 同日，L11/XP25 | 668 | 2300 | 33 |

实际首次扣除 **75 金**，卸下与重装不重复扣款。`xalw-core-0033.actual-results.json` 还保留原生事件付款前后 Q100000 钱包 `74300000 → 66800000`、`postcondition_verified=true` 和原管理事件消失。最后 07 为1066.11.1、装备中、L11/XP25、成长序号1；压制期间跨月未继续成长。第七次只读 Save producer 于 **2026-10-22T22:51:01.027452Z** wait0，保存服务原工具 session24370 实际退出0（chunk `62893a`），未发游戏动作。

库存入口使用既有 GUI 回调：一次有坐标回执的库存打开，延迟原图确认五件宝物与未装备的 ★402，随后由适配器原生装备并独立读回 `equipped=true`。没有重放 R15 那次不受支持的通用库存查询。原预意图拒绝仍保留在步骤记录中。

## 同进程安抚扣款补验

原七保存用例结束后，在同一暂停 PID6552、actor31254、date_raw53145456、generation1 内，经原生决策入口和实际事件选项选择安抚一次。指引显示的原生 `ARTIFACT,402` 链接绑定同一目标；管理事件的安抚为 native index8、实际显示 index2，未硬编码显示位置。

原生付款回执与独立新快照均为 Q100000 `67620051 → 65120051`，即 **扣25金**；压力33→41。原事件实例6消失，新快照 `active_event=null`、`pending_character_interaction=null`，日期/角色/PID/generation不变。没有第八次 Save、额外自然日、重复提交或喂养信用；该补验不授365日持续时间或保存持久化信用。

完整九步与来源见 `EXT/environment/r16-appease-a01/result.json`，SHA-256 `b7795843aa9c16b9a9f23d0eb6e36a3c77d5499c54dc62629caf683ef9d96ad0`。三个通知处理调用与九个安抚调用分别留证，不混入原257次用例计数，也不据此报告性能提升。

## 通知处理与离线补齐

第41日出现实例33554473的 `arrange_marriage_interaction`：sender32569、recipient31254、secondary actor37107、secondary recipient38924。冻结策略识别为已有婚姻拒绝专用规则，实际原生拒绝合法；只提交一次拒绝，再由独立快照核对同日原窗口消失后续行。

离线核对了当前原版交互/事件定义及通用、婚姻 GUI 的来源 SHA，均匹配已有持久知识，分类 `ALREADY_REVIEWED_EXISTING_SPECIALIST_REJECT_ONLY`，未新增平行策略。保留 opaque 条款等语义缺口，不授婚姻结果或脚本物质效果信用。回执 `EXT/environment/r16-interaction-offline-analysis-a01.json`，SHA `0ec8b86b75748bc0f451de166b23a2e7b10d46c9b9e839e61bdc5170b92b6b17`。

## 闭场与公开校验边界

Root 直接审阅退出确认框的自动保存为空框，经统一坐标工具正常“退出到桌面”。原图 `EXT/media/20261022T231859729826Z-r16-quit-confirm-a01.png`，最终 canonical sidecar `EXT/media/r16-final-quit-desktop-a01.png.json`；`normal-quit-root-result.json` SHA `bc189f084b328f33daaa309c38cdf161b7ca998d166fc51f45ab4feea376d121`。

保留句柄 signaled/OS exit0，原生会话于23:19:29.360312Z实际 process_exit0；job/tree/control 清理完成，`normal_close_qualified=true`。原 host wait1/native-report RED 保留，原因范围是既有库存打开的预意图拒绝；`error=null`。原 public run `20261022T220034919427Z-run` 实际 wait0，原 keeper/allocate wait0；CAS669→670、done/resources=[]，回执 `EXT/environment/r16-screen-resource-close-a01/release.stdout.json`。没有强杀游戏。

23:22:21.284152Z后台 probe 确认 Steam offline/true，PID8580、出生FILETIME `134371126587222837`、版本11.15.70.27；下一场须重新观察。

原 c18 公共 verify `20261022T232146985347Z-verify` 于23:25:35.031784Z实际退出2：八项业务仍全部 PASS，正常退出为真，但旧 threshold v1 没有 `gui_contract_qualified`，公共消费者要求它为真。这个历史失败保留。

共享生产路径已修入显式 v2 字段与精确旧生产者来源派生。修复后的原主线消费者 `51cd2b381` 通过公共 verify `20261022T233045639938Z-verify` 于23:34:28.949156Z实际退出0，`case_acceptance_pass=true`、`qualified_boundary_pass=true`。它实际调用原 c18 adapter 重读七份保存、重算八项，再校验原 Prepared、frozen 表、runtime/products 和正常闭场；新增输出附强类型版本化来源，未改原结果。原结果596058 B、SHA `1e3463456492d42d8af89f2dab59a161c0320669447911de3661f8f6eccbb0e8`，验证后仍一致。core/NPC 的明确 GUI 延期范围不提权。

随后正常 rebase 并发主线，修复为 `793fc987511404e3e711701c7796f88e6c2515b7`；仅合并共享类型与 codec 导入。合并后另开 `20261022T233543541031Z-verify` 重新验证原证据，原工具22022实际退出0，完成时间23:39:26.377599Z；8项、GUI、case acceptance、qualified boundary及正常闭场均通过。合并后的消费者78502 B、SHA `63bc317410400f874e107f3ffe8eaec4c007ec9f5f0766d1d309ffbb276c1a62`，原结果 Pin 再次不变。两次新验收均完整重算，不沿用前一消费者的来源 Pin；合并前后离线测试与实机资格分别记录。

本场通过的是上述八项实际阈值检查和一次安抚扣款；结果中的 `business_pass=false`、`product_release_pass=false` 保留。计时、诅咒和冷加载仍须代表实测，尚未发布工坊物品。
