# G2-M5 五候选联合选择：当前不能安全提交

此页是 `master@f75423623a1f873859db0042277eb7b3ed9b41ad` 的离线预检，不是新策略、实机动作或能力广告。冻结 CK3 `1.19.0.6`，EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。原生决策依据仍为[婚姻/联盟树](marriage-and-alliance.md)、[宣战树](war-declaration.md)和[战争入口策略](player-war-entry-policy.md)；具体缺字段账本见 [R0082 审计](m5-r0082-joint-selector-field-gap-2026-09-22.md)。

R0082 [只读报告](<Z:/ck3_mod_rewrite_process_assets/g2-m5-observed-heir-legality-65c84ed-20260922/live-R0082/report.json>) SHA-256 `040319A17FC5AA636A1A84E26BAD74C0D450DD7CD6609FC00FF8E4AFDA4BFD28`，逐行 [结果](<Z:/ck3_mod_rewrite_process_assets/g2-m5-observed-heir-legality-65c84ed-20260922/live-R0082/observed-first-heir-legality.json>) SHA-256 `D7C3FE9BC820983BE6E747A2415DCDDC69F4FD5A10E88D65DC4543759A8B698A`：同一 paused native revision `3`、玩家 `29829`、首继承人 `38822`，657 个互异候选都通过 complete Can Send 和接收方原生最终答复。该结果的 `native_rank` 全为 `null`；五个前列 ID `16778038, 16778252, 16778632, 16778730, 16778737` 仅用于定位冻结 fixture，不是排名或策略常量。R0082 没有动作，也不证明当前存档仍有这五个候选。

| 所需输入 | 当前边界 | 下一项可施工只读入口 |
| --- | --- | --- |
| 同帧五个不同合法婚配候选 | R0082 私有合法性查询已实机；尚未公开注册，且只含身份/原生答复，不含效用 | 从当前 public campaign-root 绑定玩家及首继承人，在同一 native revision 动态取五个不同 `native_legal_candidates`；不足五个就如实返回不足，不复制旧 ID |
| 候选婚配/联盟及长期承诺 | `marriage_candidate_alliance_projection_v1` exact-build 私有核静态就绪，但 CMake 默认 OFF、未接 application-main 或 paused live；`possible_alliance_pairs`/`would_attempt_if_accepted` 不是成立的联盟或承诺价格 | 将现有 `query-first-heir-candidate-alliance-projection-v1-private` 接到已验证合法的五角色 context，并同帧附 `marriage_native_outcome_classifier_v1`；读取候选实际 pair、婚姻/订婚、lineality、已有/潜在联盟，再补最小只读承诺期限/取消代价，字段不可读返回 typed unavailable |
| 战争与共用预算 | 可读取当前 gold/income、已有 WarID/army 和部分单目标战略军力；自愿盟友到场、未来补给/耗损、宣战总成本及白和/投降退出价尚未形成同帧候选结果 | 对一个当前合法 declaration 绑定完整 participant/ally 最终判定、现役补给与目标路线、有限成本和退出后果；复用既有 exact-build prewar source/ABI，不把 power ratio 当胜率 |
| 联合机会成本 | `joint_candidate_ledger.py` 输入为另一套最多八条 *ranked* 婚配 schema，不能吞 R0082 的 unranked 行；它正确返回 `joint_selection_ready=false`、`selected_step=null` | 上述观测通过后，再以同一版本目标、现金保留、盟友/长期义务及多战争占用设最小确定性阈值，比较五个真实候选与“现在等待”；仅提交一个 typed 动作 |

最小冻结 fixture 入口是 R0082 的 `dev3b_r639.ck3`，SHA-256 `9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63`，配上述逐行结果、exact EXE 和版本绑定 native DLL；若重新实机观察，必须由唯一 CK3 owner 分配新轮次，使用同版本 paused snapshot 而非跨帧拼接。潜在联盟私有传输现有 schema 为 `xar.ck3.first-heir-candidate-alliance-projection.v1`，normal/`-O` 静态测试不替代真实 paused 五行读回。未来通用 MCP 可命名 `ck3_query_first_heir_candidate_alliance_projection_v1`，但只有同帧 available/unavailable/RED 和下游消费门闭合后才注册/广告；目前不注册、不改 G2-M5 状态。
