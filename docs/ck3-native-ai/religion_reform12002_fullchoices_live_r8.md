# CK3 1.20.0.2 全实际草案 Doctrine：R8 暂停实机观测

2026-10-01 21:30（Asia/Shanghai）root 执行的 R8 readonly preview，已使 [全 slot Doctrine provider](religion_reform12002_fullchoices_provider.md) 取得 **production-live primitive**：真实当前草案29个slot、94个source rows全部最终选择门可观测，其中49行 `final_selectable=true`，`doctrine_gates_complete=true`。本篇只读取冻结的成功 packet 和 root 摘要；记录者没有访问游戏、UI或pipe，也没有重跑fixture。

## 本轮真实证据

成功 [官方 MCP packet](Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/targeted-sdk-r8/r8-draft-three-readonly-20261001T133028Z/003-ck3_query_player_religion_draft_doctrine_choices_v1.json)，SHA-256 `d73f7cf3d710a523e4b0ec9210730fd0a2115c1125c057acdb06f6bba8af7dce`，是 `ck3_query_player_religion_draft_doctrine_choices_v1` 实际结构化结果，非手编JSON或命令ACK。root [暂停预览摘要](Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/live-run-08/actual-r8-preview-summary.json) 绑定PID **93880**；[root截图](Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/live-run-08/gui/20261001T133027288606Z.png) 作为原始视觉证据引用，本篇未重新检查截图。

| 输入／结果 | 实际观测 |
| --- | --- |
| exact build / EXE SHA | 1.20.0.2 / `AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D` |
| 玩家完整ID / source RiteID | `29829` / `152` |
| paused frame raw / capture epoch | `53169360` / `26972` |
| snapshot / native revision | `native:2` / `2` |
| available / draft observed / status | `true` / `true` / `observed` |
| readonly / packet isError | `true` / `false` |
| all actual slots / source rows | `29` / `94` |
| final selectable / duplicate excluded | `49` / `0` |
| Doctrine gates complete | `true` |

结果 scope 是 `actual_current_draft_selected_slot_group_sources`，schema `ck3_12002_current_draft_full_doctrine_choices_v1`。它证明当前真实创建草案的所有实际 Doctrine slot source已经过重复排除、shown/nativeCanPick及knowledge/prophet最终选择门，可用于当前草案决策；无需以每个分组是否打开来决定能否观测。原生输入闭合见 [stock/exact树](religion_reform12002_fullchoices.md)，不是从全局 registry推断所有 Faith 的通用合法选项。

本帧 duplicate excluded为0，因此本轮实机没有新增非零重复排除覆盖；该分支只复用已交付四slot／十五source实际C++ fixture。49个true行是最终观测结果，不代表已经选择任一选项、具有足够创建资源、名称有效或已经完成创建。

## 保留失败与能力边界

root交接报告首轮 [13:27:02 UTC attempt目录](Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/targeted-sdk-r8/r8-draft-three-readonly-20261001T132702Z) 因草案窗口隐藏，未进入有效preview；该harness失败保留。本篇按root交接记录该原因，没有读取首轮packet或重新运行它，也没有把隐藏窗口当作本能力失败。随后13:30:28 UTC的上述成功packet才是本篇资格证据。

本包仅升级 **Doctrine readonly observation primitive**。没有选择、提交、创建／改革动作或费用扣除结果，没有完整观察→决策→操作→验证循环，不能写作 production-live loop、complete或新增G2完成项。摘要仍为 `all_three_live_ready=false`；Doctrine通过不覆盖独立Tenet查询或创建事务。MCP结果当前 `advertised=false` 也不等于能力不存在：本轮已由真实官方查询执行并返回冻结结构化结果，发布策略由中央owner维护。

后续由root/中央owner使用已有暂停证据继续集成并推进必要的创建草案决策、合法选项动作与独立后置验证。本篇没有改动原七份provider源、旧历史tree、SDK、共享接线、测试或游戏状态；doc-only source SHA和日报／周报字段见 `Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-reform\fullchoices\live-r8-doc-delivery-result.json`。commit/push由root统一收口，本worker不执行Git。
