# CK3 1.20.0.3：派系 watch 与一般战争 prior 的输入范围

2026-10-06，研究与最小施工方案。现有策略把任何 targeting faction 都排除在一般战争 prior 之外；已有原生告警查询能够区分当前 watch 与 dangerous，因此可以用真实同帧威胁替换这个过粗的数量条件。此包尚未修改策略；新的当前 applicability 由 Root 下一批保存的 campaign-root／faction query 决定。历史 512 的 false 不沿用到后帧。

冻结源码为 700d0a79c53326ba1c99bc9cecde353104b0837e，独立 checkout Z:/gfp1。冻结 CK3 1.20.0.3／Steam25652598，EXE SHA-256 94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6。复用 [exact .3 ABI reuse 合同](../../ck3_autonomous_player/native_bridge/research/ck3_1_20_0_3_abi_reuse.json) 的 war_entry 与 faction alerts／layout／metrics／county 四个 PASS 包；没有新 EXE 读取、hash、构建、测试或游戏操作。旧合同的 nonwar group 是迁移分类，不能恢复已撤销的战争授权限制。

## 实际问题与原生来源

[strategy.py](../../ck3_autonomous_player/src/xar_autoplayer/strategy.py) 的 same_frame_general_scope（冻结行14274–14287）将独立、feudal、domain 未超限、正 Q100000 收入与 player_targeting_faction_count==0 合为一个布尔值。故数量非零时只报告 independent_feudal_economic_scope，而没有消费既有危险/强度输入。已读到的 570-plan06、590-plan05 为合法 claim31050-11-0／claimant29829，双方 network0，native ratio31781／31330，唯一 blocker 是该复合 scope。550-plan09、630-plan24 实际是 alternative assessment，不把这些具体叶误记为 NO_DECLARE；同批其他阻塞由 Root 原记录汇总。

现有 [战争进入 ABI](../../ck3_autonomous_player/native_bridge/research/ck3_1_20_0_2_war_entry.json) 经 .3 reuse 固定：2C13460 解析 effective target；1A22D30 构造完整 State16；1A24010 分别以 actor filters1/1/1、target0/0/0 累计网络；1A23240 产出 distance、target total、actual ratio、双向 AI entries 与 flags。生产查询允许当前 declarable target 或 active-war opponent，并不依赖 campaign-root 的 targeting count==0。完整 AI 的 chance／offensive penalty／cooldown／hostage／CB评分／Top5 路径仍见 [战争原生树](war-declaration.md)；该文旧1.19地址不直接变成 .3 外层 AI 等价证明。本方案是已闭合输入上的最小我方策略，未声称复刻整棵原生宣战树。

派系 reader [ck3_12002_faction_alerts.cpp](../../ck3_autonomous_player/native_bridge/src/ck3_12002_faction_alerts.cpp) 在 exact .3 application-main 上复用原生身份与指标：Character+1C0 的 land+120／12C 给 full FactionID；storage5D1DE90／fallback5D1DE10 回查；Faction+20 的 definition 与+44领袖、两类成员分别复制。native2601EF0 给百分比点 power，26021A0 给当前动态 power threshold，Faction+28 给 discontent，2601B50 给最终月增长，2601C60 给月份，2603AB0 给 at-war。危险 native1D65BF0(faction,faction) 与源解释一致才发布。当前规则为人类领袖，或 peasant 的 months≤12，或非peasant 的月增长>0；已有 faction war 另交 war handoff。县领 exposure 用 populist、power>动态threshold、target!=player，见 [指标树](ck3-1.20.0.2-faction-metrics.md) 与 [完整来源](ck3-1.20.0.2-faction-alerts.md)。

~~~mermaid
flowchart TD
  L[exact .3 current legal declaration] --> E[2C13460 effective target]
  E --> S[1A22D30 State16 + 1A24010 actor and target networks]
  S --> P[1A23240 native power assessment]
  R[current player full ID] --> F[land120/12C full FactionIDs and storage]
  F --> M[2601EF0 power + 26021A0 dynamic threshold + growth/months]
  F --> D[1D65BF0 current stock dangerous rule]
  D --> H{human leader?}
  H -->|yes| Y[dangerous]
  H -->|no| T{peasant?}
  T -->|yes| Q{native months <= 12?}
  T -->|no| G{native monthly growth > 0?}
  Q -->|yes| Y
  G -->|yes| Y
  Q -->|no| W[watch]
  G -->|no| W
  M --> A[existing ready normalized faction query]
  Y --> A
  W --> A
  A --> C[same frame with campaign root and current declaration]
  P --> C
  C --> B[proposed: watch count > 0 may enter existing aggregate prior]
  B --> O[existing conservative prior admission and typed outcome]
  C -. unknown future faction growth / depleted-force reaction .-> U[remaining strategy quality gap]
  O -. unavailable declaration-bound regiment/arrival inputs .-> V[complete prewar battle forecast remains partial]
~~~

## 现有 MCP 输入已经足够

query-player-faction-alerts-v1／ck3_query_player_faction_alerts_v1 已发布。其 [normalizer](../../ck3_autonomous_player/src/xar_autoplayer/bridge/player_faction_alerts_contract.py) 校验 full IDs、target为玩家、实际 count/rows一致、danger解释与native结果一致，并导出 dangerous/watch/war_handoff/exposed_county。readiness.alert_ready 由现有四个组件得出，exact_ultimatum_timing_ready=false；这不是等待精确 ultimatum 才能使用 watch 的理由。县领或 surrender_impact 的独立不可用不应被误当作 targeting row 的合法空值；本最小方案直接消费现有已可用 planner_projection，不扩大合同。

[native_driver.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py) 的查询结果含 queried_snapshot_id／queried_revision／queried_native_revision；[service.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/service.py) 同时发布 source／binding 中的 snapshot_id、revision、native_revision、date_raw及paused。先复用生产成功的 normalized payload，再按现有 strategy 的 same-frame recovery 方式从 snapshot／成功 command history 取当前叶。比较 player full ID、date_raw、native revision，以及已有 envelope 当前 snapshot／public revision；不把历史512或上一次查询沿用到日期推进后。无新 DTO、RVA、native collector、MCP、pipe 或 DLL 依赖。

历史 [512 faction packet](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/512-peace-current-faction-alerts.json) 绑定 native845/public846/raw53271912：targeting2、alert_ready=true、planner dangerous=false，两个非peasant均 growth−3/月。33554465 populist 的 power17.866%、threshold75%、discontent4；50331692 liberty 的 power19.591%、threshold75%、discontent0；两个 months0 是负增长的合法结果，不表示马上 demand。它与 [508 root](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-responses/508-campaign-root-after-war.json) 的 native844 不是同一帧；只证明 provider 与 watch事实曾真实可用，不合成当前策略输入，也不证明后来550/570/590/630的危险值。

## 最小 owned 实现计划

1. 只改 strategy.py 的一般战争分支及两个小 helper：恢复当前成功 faction-alert 叶；把已有经济条件与派系风险说明分开。既有 count0 路径维持当前行为。非零且暂无同帧叶时先选现有 query-player-faction-alerts-v1，取得数据后在同帧重新选择；不再反复把存在派系当作经济失败。历史窄 claim／de-jure canary无需一起扩张。
2. 非零且现有 ready planner_projection.dangerous=false 时，记录 watch IDs、每行 power/threshold/discontent/growth/months，进入已有 general-native-war-entry-battle-prior-v1。当前dangerous分支使用现有延期/治理选择并明确实际原因；at-war继续现有战争路径。使用原生final危险值，power与动态threshold作为真实质量输入/解释，不新增固定75/80阈值、不把不同派系百分比加成敌军人数或新风险预算。
3. 现有 _forecast_required_war_entry_plan 直接运行 forecast_prewar_power_battle：256 trials、120日、uncalibrated aggregate surrogate。其既有 admission 是 Wilson lower≥0.95 且 unresolved≤5%；可返回现有 typed DECLARE，也可 NO_DECLARE。数量替换因此影响现有整体选择，不能说仅多读一次输入或自身保证宣战成功。该提议没有新增自动宣战授权门。
4. 这一步解除的是现有 aggregate prior 的输入范围。prewar_scope_contract 仍 advertised=false，declaration-bound regiment-v3／arrival输入另缺；required_capabilities 中的名字不代表查询已可用。不能据此发布 prewar native parity、完整battle forecast、完整OODA或live信用。
5. 源树和新 actual same-frame pair封存后，再写一个新的 focused production planner case：同帧count2/watch进入aggregate evaluation；保持危险/缺叶路径的实际选择并验证old512不被消费。只执行这一个必要case一次，不重跑旧war-entry矩阵。当前阶段测试执行0，策略修改0。

Root负责提供最新保存的 snapshot、campaign-root与faction-alert实际叶；当前新同帧 applicability尚未取得。本包可交付 source-closed 方案与下一项owned改动，readiness=research；完整人物准备、Entry、未来派系危机／军力耗减后的反应、长期战争策略仍是质量缺口，不因此阻断已有可用aggregate模型施工。

外置字段与封存来源：Z:/ck3_mod_rewrite_process_assets/g2-background-20261006/faction-battle-prior-scope/。Root合并当天/W41，不编辑shared reports、g78或gb0。
