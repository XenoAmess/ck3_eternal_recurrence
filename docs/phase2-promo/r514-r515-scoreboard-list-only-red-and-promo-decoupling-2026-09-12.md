# R514/R515：received list-only ACL RED 与宣传录制解耦

## 结论

R514 Frontend warm-up 与 R515 gameplay 都已终止，当前 CK3/FFmpeg 实例数为零。R515 越过 loader、native readiness、paused seed、HUD 与 R513 GUI context 修复，首个宣传片段在计分板 source query 处返回 `acl_inconsistent`；未发生 gameplay input，录制的 2.03 秒失败 take 没有 clean span，P2 素材仍为 `0/8`。

这不是产品计分板坏掉。根因是只读 bridge 把产品的 received 列表可见性与当前玩家 self dossier 错误捆绑。canonical seed 的当前玩家 `29037` 有 `zg361_sb_r_01_char=26347`、received owner `32904`、cycle `2`，但没有 `zg361_sb_self_char`，全存档也没有任何角色带该变量。产品 GUI 明确以 `zg361_sb_r_01_char` 决定 received 列表面，以独立的十四字段全量门禁决定 self detail。

## 最小整改

1. native ACL 解码现在接受合法 list-only 状态：首行必须是有效角色；存在的 header 字段必须按类型解码；self dossier 全部缺失时保留逐字段 `variable_absent`，并返回 `surface_available=true / current_player_is_subject=false`。只要 self dossier 有一项存在，原有全量 identity/policy join 仍严格执行，部分或矛盾 tuple 继续 RED。
2. Python normalizer 把 received 约束改为单向蕴含：`current_player_is_subject=true` 必须有列表面，列表面存在不再强迫当前玩家拥有 dossier。
3. 宣传首镜头只执行真实 `open` 动作和独立 later-query 可见性证明。该 capture-only 证据明确保留 `production_capability_advertised=false`，只允许本次视觉片段 GREEN，不提升 scoreboard 生产能力。完整 managed/received 双表面 action matrix 保留在正式 scoreboard 验收中，不再作为“只展示计分板”的宣传片段前置。

整改使用一个 native list-only fixture、一个 Python 合同测试、现有 visual-handler 覆盖和一个 promo wiring 断言验证；不扩大到长跑或全仓测试。接口语义变化要求根仓提交后同步 open_kaishek。

## 证据

- attempt：`Z:\ck3_mod_rewrite\_runtime\p2-capture-r514-r521-616c754-20260912`
- outer report：`96064EB5FB2E7D4CECF5D60ACA784A6474AB0FEC5787C08BDE656A56214F19F4`
- inner report：`8222EF4A9152D1357E6D5BC05CA970A9EE96009CE041073F3F2C2EDA9383D81A`
- cleanup：`6F2D6800126FD4980A3338586EF4A2D144C7FDB004E990CA68C0127DD0FD3141`
- failed take：3,669,187 bytes，`5C86B18B4824B01D716065C1943A225CB5F7A319872E09B4293E9B0F423414EB`
- timeline：`9A4393A4C97814EAEE09FACEFC730BCACF749DC09F9DFDF441C3426902A98A53`
- canonical seed：57,377,787 bytes，`8E6CEB97E97CD6B9185EBBCCE38B42FC087E0B800CD5E321037C9F29A79E45B9`
- player-scope offline report：`61A0951F2CA4D0E22DD9B77A85DF67D217C97B00FFE58F0D5B1491F769F5BD9A`
- self-discovery offline report：`9505D6EC6A1B55FB412773A1367D03CB01D5E5510A03B60BAB26196AB54D206D`

## 下一步

从提交并同步后的 HEAD 生成新 Release DLL。下一次启动依次记为新轮次 R516 Frontend warm-up、R517 gameplay；这是 DLL/合同变化，禁止热重跑。R517 只验证 state query、首镜头 open/visible/close 并继续既定八段录制，出现新的真实 RED 时按该片段最小范围处理。
