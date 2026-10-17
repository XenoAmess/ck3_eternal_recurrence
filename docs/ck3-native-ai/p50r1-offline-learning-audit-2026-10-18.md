# P50R1 批后来源学习审计（截至 closed 6029）

本轮已封的 **130 份批次、9 个 incident 均有持久来源知识，生产加载器离线读回 9/9 known**；缺失来源分析为 **0**。原先 unknown 的 5 个事件实例（4 个定义）和 1 个角色互动通知，均已由实际后台 worker 分析并发布。本次没有重复写 registry、增加策略或修改 SDK。

本次审计机器为 `xenoamess-full-tower-eb9d2c1186`，通过 `tools/ck3_live_run_id.py machine` 重新读取；最终证据观察 UTC 为 `2026-10-17T20:41:09.482285+00:00`。机器可读的来源、SHA、选择及加载器结果见 [审计证据](evidence/p50r1-offline-learning-audit-2026-10-18.json)。

## 范围与实际输出

外置工作根记为 `N=D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep`，`R=N/robert30-clean-campaign01/native25-cold-generation01`，`C=N/robert30-clean-campaign01/offline-learning/p50r1`。

- 输入仅为 `R/p50r1-offline-batches/0068.json` 至 `1544.json` 的 130 份封定 manifest，以及其中明确引用的小 before/after、实际 worker 小回执、持久条目及 source-facts。125 份为空，5 份含新增记录。
- 末批 `1544.json` 自身记 `cumulative_cycles=6029`、`new_incidents=[]`，已经覆盖本轮 6029 终点。随后 Root 执行零新调用清理 1550 并正常关闭 P50R1；参见 [续行记录](p50r1-same-game-continuation-2026-10-18.md)。
- 实际启动来源是 `N/p50-presentation-prepare01/offline-p50r1/launch_p50r1_offline_workers_owner.py`；输出在 `C/vanilla-events` 与 `C/character-interactions`。`N/offline-vanilla-event-analysis` 不是本轮输出。启动回执的 owner 254232、worker 194772/118460/274304 是历史进程身份，本审计未据此宣称它们当前仍存活。
- 原始 manifest、incident 和 SDK closed 回执本身未带 `machine_id`，其原记录身份保持 `unknown`，不凭路径追认。本次机器读回与带机器 ID 的 worker owner 包装回执分别记录在证据中。

未读取 Driver、SAVE、媒体或大 AUTO；未重审 P43，也未读取或更改 R2 namespace 准备。

## 本轮逐项闭合

索引为原生 zero-based；API 号为 index+1。所有事件均按当帧显示顺序选择第一已启用项，不能把“第一显示项”写成固定 API 1。

| 批次 | 实际定义／实例 | 当场来源识别 | 实际选择 | 批后持久库与生产读回 |
| --- | --- | --- | --- | --- |
| 68 | `pam_bull_events.0004`／72 | known | index 0／API 1 | exact known |
| 597 | `bp1_house_feud.0840`／74 | unknown | index 0／API 1 | 已发布，exact known |
| 721 | `birth.9002`／75 | unknown | index 0／API 1 | 已发布，exact known |
| 721 | `bp2_yearly.8040`／76 | known | index 0／API 1 | 原条目同源重绑定，known |
| 785 | `secrets.0110`／81、79 | unknown ×2 | index 2／API 3 | 两实例共用已发布指纹，均 exact known |
| 785 | `bp2_yearly.8042`／77 | known | index 0／API 1 | 原条目同源重绑定，known |
| 785 | `adultery.4001`／80 | unknown | index 1／API 2 | 已发布，exact known |
| 907 | `sway_ruler_to_my_rite_interaction`／`-1761607550` | unknown | 原版左侧 `Reject` | 已发布，interaction source/GUI known |

四份 event review 分别复核 68、597、721、785；一份 interaction review 复核 907，五份 `unresolved` 均为空。原本 unknown 的 event review 共写入 5 条 incident 结果，去重后对应 4 个持久指纹；通知另有 1 个指纹。所有 manifest SHA 均与 review 内的输入 pin 一致。

实际 after 中，8 个事件分别记录 `command_acknowledged=true` 与 `event_instance_advanced_verified=true`。通知分别记录 ACK、`original_pending_advanced_verified=true`、`status=rejected` 和原 pending 已无；没有用 ACK 代替窗口推进。

## 来源与选项效果

共享库的 facts 保留完整原定义、所有原生选项、名称条件、trigger、scope、直接效果、immediate/after；通知保留完整 interaction、on_accept/on_decline 与 GUI SHA。下表仅摘要实际选中的分支，完整 bodies 仍由证据指向原持久 facts，不重复复制原版源码。

| 定义 | 实际选项的原版语义 |
| --- | --- |
| `pam_bull_events.0004` | 确认项本身无直接 option effect。 |
| `bp1_house_feud.0840` | 设定 `scope:house_feud_rival` 为宿敌，调用宽容性格压力 helper；AI 分支还消费复仇心与勇敢值。 |
| `birth.9002` | 采用姓名建议的来源分支，给建议者 +15 感激 opinion，调用生育虔诚 helper；仍有在世同名官员的条件 opinion 分支。姓名 tooltip、条件与 helper 均保留原文。 |
| `bp2_yearly.8040` | 为 `scope:crush` 排入两天后的 `bp2_yearly.8041`；原 AI 条件未离线求值。 |
| `secrets.0110` | index 2 要求存在 `consort_bastard_parent`，该 option 本身无直接效果；完整事件 immediate/after 仍保留。 |
| `bp2_yearly.8042` | 有婚姻变量时调用婚姻 helper，否则与 `scope:crush` 建立恋人关系。 |
| `adultery.4001` | 按配偶／情人是否在管辖内、未入狱、违法及失败性行为等条件调用监禁；另有宽容性格压力分支。 |
| `sway_ruler_to_my_rite_interaction` | 左侧拒绝进入 `on_decline`，调用 `pam_sway_to_rite_on_decline_effect`；不将调用 helper 推断为已改宗或已改变关系。 |

原版文件 SHA-256：

| 相对 `game/` 的来源 | SHA-256 |
| --- | --- |
| `events/dlc/pam/pam_bull_events.txt` | `596a8f4ce0c9e64119b2e65917ec56f984c58882e5ccb0adbd2e56893d89f937` |
| `events/dlc/bp1/bp1_house_feud.txt` | `8e0d1d0014692de2a9cd4afe3fa0f21ba7d25572a6e0a08701734704aa0632a8` |
| `events/birth_events.txt` | `d2dc5b2a7b7f42e356ddbd0ba7b708aaef2603033ea07d2ff0becb46bbd436d5` |
| `events/dlc/bp2/bp2_yearly.txt` | `67df046bf1a6b2fe6186e26d9eb9586c6346dbaeb78f0e5b46baaede4c385332` |
| `events/secret_events/secrets_events.txt` | `17e31688436eda16af4fe2c4b18122a2c227a8acd9010c6238a223e33ccdea64` |
| `events/relations_events/adultery_events.txt` | `af8de94001cdba23fd385ee6b4672415461a828a004344bf3e30b146fafd46bd` |
| `common/character_interactions/pam_interactions.txt` | `2db73b0da8572e218f1a677a91ff4281a890ade115e6dc40e696ecb59c0b1049` |
| `gui/interaction_notification_window.gui` | `a3c946a98346de2f57c5c3408a24bf298329df24a6ab25ec88d893befa1fe6e0` |

## 验证与边界

一次离线回放使用本轮实际 worker 指定的 `sdk-p48-candidate01/src`，调用生产 `load_source_reviewed_event_v1`（8 例）与 `load_source_reviewed_interaction_v1`（1 例），针对现有共享 `R/state` 验证来源、facts、构建和当帧身份，得到 **9/9 known**。没有实例化服务、提交动作或发布新条目。加载器与回放原件 SHA 见 JSON。

闭合的是 [批后来源学习合同](vanilla-event-offline-source-known.md)。原始 `offline_analysis_pending=true` 表示捕获当时的状态，保留不改；后续 review、持久 facts 和生产加载器实际读回共同证明随访已经完成。没有给最优策略、原生 AI 等价、完整 timeline 合同或具体关系／监禁／虔诚效果授予通过；本次没有新增实机成绩或 R2 部署资格。

这是文档与现有知识库审计，未修改或执行 CK3 脚本，`open_kaishek` 不适用。未重复单测。新增输出均为小记录，沿用机器绑定的 Root 同范围容量回执，按通用存储策略 1.0.0 归纳外置派生物与复核小型 canonical 记录；没有删除或新增重型预留。
