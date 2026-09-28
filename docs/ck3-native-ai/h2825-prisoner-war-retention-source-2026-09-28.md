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

当前还缺主攻方 full CharacterID 与 House、两侧参与者和两侧 primary title 前三继承人；同帧按囚犯 ID 得到的实际一般 PoW 配对也未发布。一般 PoW、赎金和其他扣留价值仍是 `unavailable`。任何一个人的释放动作均未提交。

## 可交付的只读接口合同

为每个请求 `WarID + jailer full CharacterID + prisoner full CharacterID` 发布以下字段，并把它们绑定到同一 `snapshot_id`、public/native revision、日期、EXE/DLL SHA：

1. 当前战争 `CB canonical key`、主攻/主守 full CharacterID、双方 participant full CharacterID 集合及来源；任一项读不到即 `unavailable`，不能代填空数组。
2. `generic_pow_exit_release`: 依据第 1607–1656 行，在两侧 primary 与前三顺位继承人、实际 jailer relation 全部可读时，给出 `matched_pair` 或 `not_in_pairs` 和精确 `jailer/prisoner/opposite_primary/succession_position/side`。若任一集合未完成，保持 `unavailable`。配对代表该退出效果的候选，不保证退出选项此刻可达；可达性另由正式原生 war-termination option 决定。
3. `fp3_house_member`: CB 不是 `fp3_free_house_member_cb` 时为 `not_applicable_cb`；囚犯 House 不存在时为 `not_applicable_no_house`；其余只有在主攻方 House 和玩家 defender 身份均读到后才判断 `matched` / `not_matched`。`matched` 时保留 `major_prestige_gain/loss` 脚本语义、可计算 value 的实际原生金额或明确 `amount_unavailable`，并报告胜利释放 House 集合及若释放后不再有同 House 囚犯的失效条件。
4. 把 `matched_pair`、`fp3 matched` 与未解决的战俘/赎金价值映射成独立的 pending retention commitment，供非战争囚犯价值消费者按**同一帧** join。`not_in_pairs` 只否定一般 PoW 释放配对，不否定所有战争价值；无自动释放动作。

已有 `ReadWarExitPrisonerReleases` 原生函数做过一般配对枚举，但公开 `query-war-termination-exit-terms-v2` 因 `loaded_effect_preview_disabled_after_live_crash_rva_0x334C668` 返回 unavailable；窄 `ReadRaiktorSurrenderPrisonerReleases` 只覆盖 Raiktor CB。现在新增独立 `query-war-prisoner-release-pairs-v1-<WarID>`：它从暂停帧读实际 War/CB/双方参战者、primary 与前三顺位继承人及通用效果的 jailer→prisoner 候选，双采样校验日期和集合，不调用 loaded-effect preview，也不提交动作。Python 驱动只在该 WarID 的暂停快照暴露步骤，校验 native revision、日期、完整扫描和配对一致性；不完整或漂移直接拒绝。新接口**只证明通用效果的输入图**，不证明某个终战按钮此刻可用、已执行或 FP3 专用出口会调用此效果。

目前已落地[只读 source join](../../ck3_autonomous_player/src/xar_autoplayer/bridge/prisoner_war_retention.py)：严格比较六项暂停帧身份；只有参与者和前 3 顺位继承人两类原生扫描都明确完整，才允许发布 `not_in_pairs`；否则一般 PoW 一律 `unavailable`。它把 `matched_pair`、FP3 House 分支和当前终战选项可达性分开输出，保留脚本威望 value 与未知实际金额，不提交释放动作。H2825 的**现有实机输入**只能给三人 `fp3_house_member_status=not_applicable_cb`、`generic_pow_pair_status=unavailable`。独立通用 PoW producer 已完成源码接线和离线编译/测试，但**尚无使用新 DLL 的 H2825 实机读回**，不能把三人写成已完成 live PoW 分类，也不能声称赎金价值或完整扣留价值已求出。非战争消费者可把新 producer 的 `war_prisoner_release_pairs_proof` 与同一帧的私有囚犯集合接入上述 source join；只要帧身份不合，保持 `unavailable`。
