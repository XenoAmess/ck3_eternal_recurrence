# H2825 三名囚犯的战争扣留值：原版来源与读口边界

对应 [WAR-PRISONER-RETENTION-H2825](../autonomous-agent-progress/coordination/war-requests/requests/WAR-PRISONER-RETENTION-H2825-20260928.json)。本页只冻结原版条件及当前已证实的输入，不将缺少的战争绑定写成零。原版身份为 CK3 `1.19.0.6-steam23530548`，EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。

## 原版的两条不同释放路径

- `game/common/scripted_effects/00_war_effects.txt` SHA-256 `A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D`，第 1607–1656 行：`release_prisoners_of_war_effect` 遍历两侧参战者作 jailer；释放被其关押的对方 primary，及该 primary 的 primary title 继承顺位前 3 名。这是具体的 `jailer → full CharacterID` 配对，不能从一名囚犯只是战时被关押推断。现有 [战争终局文档](war-termination.md)对另一历史帧曾完成精确枚举；其空配对不能移植到 H2825。
- `game/common/casus_belli_types/05_fp3_wars.txt` SHA-256 `234DEC6EAEE859A6CF95D8D0BC66247CB22D74C69358806CA3C75E75C33C2AE9`，第 1015–1175 行：`fp3_free_house_member_cb` 的开战前提要求防守方关押主攻方 House 的人；胜利时释放防守方关押的全部同 House 囚犯（1122–1127）；当防守方再无同 House 囚犯，CB 的 `should_invalidate` 成立（1166–1174）。这是不同于一般 PoW 前三继承人的 **House 范围**；不能混作一份释放列表。
- `game/common/character_interactions/00_prison_interactions.txt` SHA-256 `3E05C94CDCE4D42CCE8256D2D79CD78FEB1C9D5B79DAA64AA8243AA0C658F22B`，第 4880–4916 行：释放某个有 House 的囚犯时，若任一当前战争使用 `fp3_free_house_member_cb`、actor 是该战 defender，且 primary attacker 的 House 等于囚犯 House，则对那场匹配战争的 primary attacker 加 `major_prestige_gain`、primary defender 加 `major_prestige_loss`。这两个是脚本 value，不是当前帧已计算的整数；也不能把 `random_character_war` 当作多个匹配战争逐一累加。
- `game/common/character_interactions/00_war.txt` 的投降、无条件和平、胜利交互另有 `fp3_free_house_member_cb` 专用分支：它们跳过通用 `release_prisoners_of_war_effect`。所以对于 FP3 战争，即使通用配对输入图中存在候选，也不能把候选写成实际终战释放；消费端明确返回 `not_applicable_cb`。

## H2825 已确认与未确认

H2825 同一暂停帧为 `native:3` / native revision `3` / `date_raw=53217624`，WarID `16777231`，玩家 `29829` 为 defender。私有囚犯集合读回三名 full CharacterID：`34486` 的 House `2370`，`44484` 与 `47028` 的 House 为 `null`；他们都由玩家关押，无条件释放 preview 合法且自动接受。这些证据见 [正式报告](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-H2825-SIEGE-PARTITION-20260928.r0265-formal-report.json)及[本机同源只读复验](h2825-readonly-partition-live-2026-09-28.md)。`null` 仅是本次 House reader 的结果，不赋予人物其他未知关系的否定值。

本机独立 attempt `D:\ck3-research-artifacts\war31-h2825-20260928\attempt-04\live-plan-readonly-04` 的 `query-01-payload.json` SHA-256 `4FA460AC977EF9C25C2FAAE5E41630CB146A2903D03860B110CF28B2D721F4BD`，由正式规划器先选 `query-war-termination-options-16777231` 后在同一 `native:3`、native revision `3`、日期 `53217624` 只读得到：`active_casus_belli_identity={database_index:17, canonical_key:individual_county_de_jure_cb}`，玩家为 defender、主战分 `-24`。因此对**这场 WarID**，三名囚犯的 FP3 释放威望分支均是 `not_applicable_cb`，优先依据精确 CB 而非只看囚犯 House。此结论不自动适用于玩家可能参与的其他战争；本帧 public active wars 只列此一场。

主攻方 House、赎金和其他扣留价值仍未读得。下文 attempt-05 单独取得该战争的主攻方 full CharacterID、双方参与者、两侧 primary title 前三继承人和通用 PoW 配对输入图；attempt-08 才完成三名囚犯、配对图和终战选项的同次暂停帧 join。所有 attempt 均未提交囚犯或战争动作。

## 可交付的只读接口合同

为每个请求 `WarID + jailer full CharacterID + prisoner full CharacterID` 发布以下字段，并把它们绑定到同一 `snapshot_id`、public/native revision、日期、EXE/DLL SHA：

1. 当前战争 `CB canonical key`、主攻/主守 full CharacterID、双方 participant full CharacterID 集合及来源；任一项读不到即 `unavailable`，不能代填空数组。
2. `generic_pow_exit_release`: 依据第 1607–1656 行，在两侧 primary 与前三顺位继承人、实际 jailer relation 全部可读时，给出 `matched_pair` 或 `not_in_pairs` 和精确 `jailer/prisoner/opposite_primary/succession_position/side`。若任一集合未完成，保持 `unavailable`。配对代表该退出效果的候选，不保证退出选项此刻可达；可达性另由正式原生 war-termination option 决定。
3. `fp3_house_member`: CB 不是 `fp3_free_house_member_cb` 时为 `not_applicable_cb`；囚犯 House 不存在时为 `not_applicable_no_house`；其余只有在主攻方 House 和玩家 defender 身份均读到后才判断 `matched` / `not_matched`。`matched` 时保留 `major_prestige_gain/loss` 脚本语义、可计算 value 的实际原生金额或明确 `amount_unavailable`，并报告胜利释放 House 集合及若释放后不再有同 House 囚犯的失效条件。
4. 把 `matched_pair`、`fp3 matched` 与未解决的战俘/赎金价值映射成独立的 pending retention commitment，供非战争囚犯价值消费者按**同一帧** join。`not_in_pairs` 只否定一般 PoW 释放配对，不否定所有战争价值；无自动释放动作。

已有 `ReadWarExitPrisonerReleases` 原生函数做过一般配对枚举，但公开 `query-war-termination-exit-terms-v2` 因 `loaded_effect_preview_disabled_after_live_crash_rva_0x334C668` 返回 unavailable；窄 `ReadRaiktorSurrenderPrisonerReleases` 只覆盖 Raiktor CB。现在新增独立 `query-war-prisoner-release-pairs-v1-<WarID>`：它从暂停帧读实际 War/CB/双方参战者、primary 与前三顺位继承人及通用效果的 jailer→prisoner 候选，双采样校验日期和集合，不调用 loaded-effect preview，也不提交动作。Python 驱动只在该 WarID 的暂停快照暴露步骤，校验 native revision、日期、完整扫描和配对一致性；不完整或漂移直接拒绝。新接口**只证明通用效果的输入图**，不证明某个终战按钮此刻可用、已执行或 FP3 专用出口会调用此效果。

目前已落地[只读 source join](../../ck3_autonomous_player/src/xar_autoplayer/bridge/prisoner_war_retention.py)：严格比较六项暂停帧身份；只有参与者和前 3 顺位继承人两类原生扫描都明确完整，才允许发布 `not_in_pairs`；否则一般 PoW 一律 `unavailable`。它把 `matched_pair`、FP3 House 分支和当前终战选项可达性分开输出，保留脚本威望 value 与未知实际金额，不提交释放动作。

## attempt-05：新 DLL 的 H2825 通用 PoW producer 只读回执

本机外置 `D:\ck3-research-artifacts\war31-h2825-20260928\attempt-05\live-prisoner-readonly-01` 从原始 H2825 checkpoint SHA-256 `231513D308A7D62D2F9CBF354D872C9F15FF1FB2B24B2CCAFF2480CF5E14B13D` 冷恢复，以新构建的桥接 DLL SHA-256 `D5AE5B199007D29F0B5B928921FF7B7055C27A866169C62F41B15C6E49C17893` 执行 `query-war-prisoner-release-pairs-v1-16777231`。`query-release-pairs-payload.json` SHA-256 `DA66D81DFA1A3252A3427BF6BB15D919FE35E0689CB1D021F33B482F2261305E`：`accepted=true`、`status=available`、`read_only=true`、native revision `3`、`date_raw=53217624`、CB index `17` / `individual_county_de_jure_cb`，主攻 `30097`、主守 `29829`，攻方参与者 `[30097,35357]`、守方 `[29829]`。攻方 primary 加前三继承候选 `[30097,34729,31729,31044]`，守方 `[29829,38822,38988,38293]`；`release_pairs=[]`，`full_participant_scan=true`、`primary_and_first_three_successors_scanned=true`、`same_frame_stable=true`。这些是该战争通用释放效果的原生输入图，不是任何终战动作的执行结果。

同 attempt 后续 `ck3_query_player_prisoner_collection_private_v1` 返回 `private prisoner collection query returned RED or timed out`；正式终战可达性查询未执行。进程已退出，`session-exit.json` 记录原始与本次准备的 checkpoint 哈希相等；其 `error=ExceptionGroup` 表示整次三源 join 验收 **RED**。因此三人的 `generic_pow_pair_status` 在本次已完成的同帧验收中仍保持 `unavailable`；既有旧版私有集合和本次 producer 不应被冒充成一次成功的完整新 DLL 三源读回。FP3 对这场已确认非 FP3 CB 的战争仍是 `not_applicable_cb`。[attempt-05/06 精确摘录](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-PRISONER-RETENTION-H2825-20260928.attempts-05-06-readonly.json)随 Git 保存，原始 save/DLL/MCP 回执继续留在外置目录。

## attempts 06–07：私有集合独立复验 RED，07 定位在主线程执行前

attempt-06 用同一原始 checkpoint 和 build-04 配对 DLL/注入器独立冷恢复，**先**发私有集合查询，原生命令回执 `ok=false`、`prisoner collection query did not complete on stable paused frame`；120 秒传输上限没有掩盖该原生 RED。没有囚犯行，也没有继续查询 PoW producer 或终战选项。其六项帧字段与 attempt-05 的冷恢复相同，但分属两次进程，不能拼接成一次成功的三源同帧验收。

attempt-07 使用新 build-05 配对 DLL/注入器和独立 Steam 离线新鲜画面，再从 checkpoint 冷恢复。私有集合仍先于其他 rich query；原生 `command_result` 明确为 `ok=false`：`prisoner collection main-thread query timed out before execution (pump_start=16951, pump_end=16951, wake_attempts=32, wake_succeeded=32, wake_failed=0, last_wake_error=0)`。失败后的两次原生快照跨约 `5.61` 秒保持同一 `native:3`、public revision `4`、native revision `3`、日期 `53217624`、玩家 `29829` 与 episode；均 paused/map ready。心跳序号 `1455→1467`，但 main-thread `pump_epochs` 均为 `16951`，`executor_started_requests=0`、`executed_requests=0`。这把 RED 收窄到**排队后、执行器开始前**：32 次 wake API 成功不等于目标主线程实际继续 pump；当前证据尚不能确定为何 pump 停住。回执和精确 SHA 见[attempt-07 Git 摘录](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-PRISONER-RETENTION-H2825-20260928.attempt-07-main-thread-queued-wake-red.json)。进程正常退出且源/准备 checkpoint 哈希未变。

attempt-07 未取得私有囚犯行，也未查询通用 PoW producer 或终战选项。因此**截至该次 RED**，三人的同帧 `generic_pow_pair_status` 仍是 `unavailable`，终战可达性也未验收；attempt-05 的空通用配对扫描只保留为那次独立的 producer 证据。没有提交释放、赎金或战争退出动作。

## attempt-08：三源同一暂停帧只读 GREEN

新 attempt 从 SHA-256 `231513D308A7D62D2F9CBF354D872C9F15FF1FB2B24B2CCAFF2480CF5E14B13D` 的原始 checkpoint 冷恢复，使用 build-05 配对 DLL `307A3C752C95EA246738DC73A792EF376B0C5E2144BD547403F6153ADA4A6A27` 与注入器 `1C792EA3DE0779ACCCF3CE069A793C75947B17F0590B4A3C642E49A0436272AD`。本次 Steam 离线新鲜画面已独立目视回读。正式 read-only 脚本先等到暂停主线程的 `pump_epochs` 在同一 H2825 帧内前进：首次 gate `16571→16577`，私有查询前 gate `16577→16613`，两 gate 都是 `GREEN`，均未替查询提交原生 ticket。随后依次读取通用 PoW producer、正式终战选项和私有囚犯集合；两次查询间及最终的原生快照均保持 `snapshot_id=native:3`、public revision `4`、native revision `3`、日期 `53217624`、玩家 `29829`、episode `native-29829-2bc2d599f7f9`。

通用 PoW producer `query-release-pairs-payload.json` SHA-256 `DA66D81DFA1A3252A3427BF6BB15D919FE35E0689CB1D021F33B482F2261305E`，再次给出完整扫描和 `release_pairs=[]`。私有囚犯集合 `query-prisoners-payload.json` SHA-256 `B82ECF6BD529146815048011724AE10C2B5D4D18EB829F33E9032A90C16868B8`，返回完整三行、玩家 `29829` 为每人 jailer、custody relation 均已核验，House 分别为 `2370/null/null`。三人的独立**无条件释放 preview** 均为 `status=available`、`can_send=true`、`auto_accept=true`、`would_accept_now=true`，且 `read_only=true`、`action_surface_present=false`；这证明该个人释放预览合法，不表示已提交释放，也不与一般 PoW 配对为空冲突。source join `same-frame-source-join.json` SHA-256 `9217C85FFAF5A7B782801E7A3DD3F05FB751022E2A7284AE47ED9588B06EC34E` 给出三人相同的结果：

| 囚犯 full CharacterID | `generic_pow_pair_status` | `fp3_house_member_status` | `pending_war_retention_commitment` |
| --- | --- | --- | --- |
| `34486` | `not_in_pairs` | `not_applicable_cb` | `not_from_these_two_rules` |
| `44484` | `not_in_pairs` | `not_applicable_cb` | `not_from_these_two_rules` |
| `47028` | `not_in_pairs` | `not_applicable_cb` | `not_from_these_two_rules` |

正式 `query-war-termination-options-16777231` payload SHA-256 `955217CD4772EF0EEF6312DFC6B581FFB41A2C8444447BF77C11671A3D104DE2`：当前**投降可用**，白和平与胜利**不可用**，所以 join 中 `war_exit_option_available_now=true` 只对应投降这一项；三个选项的 CB 专用终战条款均 `cb_specific_terms_not_observable`，不能据此列出实际投降释放、资源转移或最终结算。`not_in_pairs` 只否定这场战争当前通用 PoW 效果中的配对，不否定上述个人释放预览；`not_from_these_two_rules` 只否定此 join 所覆盖的两条战争规则。赎金、关系价值、其他囚犯保留理由及未来日期仍未定价。只读结果 `read-only-result.json` SHA-256 `36C348A60E08E7BE816B9EC0BA57EF134FBD712A2590C16B5BC6AB360AF7FA51`，退出回执记录 CK3 进程为空、源与准备存档 SHA 未变、`error=null`；没有提交投降、释放、赎金、军队移动或日期推进。精确原始回执哈希及 gate 详情随[attempt-08 Git 摘录](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-PRISONER-RETENTION-H2825-20260928.attempt-08-same-frame-green.json)保存。build-05 CTest `172/172` GREEN，但静态测试不代替上述实机读回。
