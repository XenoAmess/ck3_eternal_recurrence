# M2 `.0110` 近邻物质证据库存（2026-09-23）

状态：`evidence_insufficient / waiting for natural paused scene`。本次只读核对现有制品和主线代码；未启动 CK3、注入器或操作者，未推进日期，也未改变 M2 合同。包 `M2-0110-NEAR-PAIR` 基于远端 `master@3c75e063aadb37b8d55a5ad17f1bdf512fc26c70`。

## 事件与已有两端

完整原版事件 ID 为 `epidemic_events.0110`，本案选中 authored option 3 / native index 2（`.0110.c`）。绑定 CK3 `1.19.0.6-steam23530548`，EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。冻结原版 `game/events/dlc/ce1/epidemic_events.txt:368-412` 的 SHA-256 为 `FEF2972BD4F778818CD3A414C337D036F5132C1598FEBAB0E2623E0252DB7A1E`；其 option c 对旧疫县施加五年 minor/tiny 恢复修正，并在 `has_legitimacy = yes` 时施加 `miniscule_legitimacy_loss`。冻结 `00_legitimacy_values.txt` 将该值定为 `-20`，SHA-256 `13E43166356B5DD99358F435330B03CB9BE95AB5913280318B01681186E23A2E`。[原版调用链与决策树](epidemic-events-0110-recovery.md)、[县修正私有查询 ABI](m2-0110-county-modifier-observer-abi-2026-09-22.md)已有完整依据。

| 证据 | 实际值 | 边界 |
| --- | --- | --- |
| R0099 h1023 安全源 | actor `36403`、raw `53367816`、legitimacy `283`（Q100000 原值 `28300000`）；save `FE3D3259F0AD81609C376816BB5337FBF35B715E24BCF860B47533D4EBA8BA6C`，原始 RED driver `250BA6B42A9CB251FDB2B162B98AE1F88A56E2A768A82244BC085AC5258BB7AC` | R0113→R0114 两段冷恢复只读 GREEN；在事件动作前 **2 游戏日**，不是同日 pre frame。旧 RED driver 尾不能与 h1023 save 直接强配。 |
| R0101 自然事件 | raw `53367864`、instance `23`；h1034 查询、h1035 唯一 typed `.0110.c`；独立 native:10 中旧 instance 消失，后续正式 turn 消费 | 原正式报告 SHA-256 `7A82922E808A368006402C15E6AD624F76BFC2A601C081DAAF1D8BF97CF60972`。当帧没有 legitimacy 或县修正读数。 |
| R0101 首次事件后 checkpoint 记录 | h1041/raw `53367888`、报告中 save SHA-256 `07D6D867C96A760CDECA760420E8C6F7FCC7B77AC2022521755D54A19C990198` | 比动作晚 **1 游戏日**；报告各 checkpoint 共用 `state-final/profile/save games/xar_checkpoint.ck3` 路径，该物理文件已被后续 checkpoint 覆写。历史记录不能充作现存可恢复配对。 |
| R0101 h1094 最终安全源 | actor `36403`、raw `53368176`、legitimacy `263`（Q100000 原值 `26300000`）；save `2F6F3DCA9E9CD92D87FDE1CD296A581F6A3A38F11E2781765E99815B7769C39A`，原始 RED driver `95959FB66C457B12E38690B0B1D05E208DC08FB28A80AAC9A393C4C70712536E` | R0115→R0116 两段冷恢复只读 GREEN；与 h1023 相隔 **15 游戏日**。原 RED driver h1095–h1097 为未配对尾，正式恢复器须裁切。 |

两端合法性差 `263 - 283 = -20` 与 exact-build 选项效果一致，但中间有十五次一天的行军推进，未独立排除日期流逝或其他世界效果；不能据差值独占归因。R0101 的 gold/stress 零变化也不能代替正统性或县修正。上述 hash、冷恢复结果与两端原始配对见[不可变证据清单](<Z:/ck3_mod_rewrite_process_assets/m2-0110-bounded-live-20260922/EVIDENCE-MANIFEST.md>)及 [R0101 运行清单](<Z:/ck3_mod_rewrite/.task-tmp/RUN-001/century-r0101-preflight/R0101-evidence-manifest.json>)。

## 当前只读口与下一次自然场景

主线已有私有 `query-player-epidemic-recovery-v1` 列表模式和 `query-player-epidemic-recovery-v1-title-<full LandedTitleID>` 显式县模式，CMake `XAR_CK3_ENABLE_G2_CE1_RECOVERY_PRIVATE_V1` 默认 OFF。Debug/Release 原生 fixture、Python 传输 fixture 和私有 Release DLL 为静态证据；**尚无自然 paused 场景的该口实机读回**。`player_legitimacy_v1` 已在旧两端实机读出。无需重复静态库存或重放旧随机时间线来凑近邻事件。

下一次标准封建 production 主线自然出现 `.0110` 时，从同一 paused revision 冻结事件 key/instance、玩家 CharacterID、raw 日期、`has_legitimacy` 分支、疫情强度、可见合法 native option、legitimacy，以及私有列表模式给出的完整县 title IDs 与各县 minor/tiny 前值。若 list 口返回 unavailable，应先修这个真实观测缺口，不能把空/未知列表当作县结果。正式策略仅提交一次合法 typed 选项；在日期未推进的独立 paused 后帧核对旧 instance 消失、同角色 legitimacy 及按前帧 title IDs 逐县读出的 minor/tiny 后值，再由下一正式 turn 消费并保存合法 save/driver checkpoint。若旧修正前值已存在且无可读期限，单凭后值 presence 仍不足以证明新增或续期；该县保持 pending。若日期跨天或角色/instance 漂移，保留 RED/证据不足，不将差值归因。

目前没有已保存的 **同日动作前 + 动作后** 原始 save/driver 配对，也没有未消费的自然 `.0110` paused scene，因此本包没有合法的官方 no-launch 候选可准备。等待正常主线自然出现时再按现有只读口与官方恢复器建立新配对；不为此开专题长跑、不强制事件、不改旧合同或门数。
