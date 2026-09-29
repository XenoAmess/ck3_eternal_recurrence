# E2-04 a07：致残战报与勇武仍为 11 的事实边界

2026-09-29 独立离线审计。只读已封存的小型 JSON、既有原版存档解析与原版脚本；未占屏、启动 CK3、解码录像或修改 #451。本报告没有审看 a07 GUI 画面或给镜头 clean span 签核。

## 精确来源与同 run 观察

| 来源 | SHA-256 / 身份 |
| --- | --- |
| a07 `ck3-output/capture-report.json` | `48A17B2AE2BB55FD4A7AA6B64A030500C206D0BD4D22C4DADFFAD18B41562F8B`；独立冷载 `episode01-paired-counter-trace-attempt-010/d05-immutable.ck3`，52,172,645 字节，SHA `695F1FDE17457004EB8D060C1F21146C3605374806DABACF6FB5FAB386882885`；来源保存回执 SHA `6650C0DB79D063E066AB72402735C22FAE9FCB5D458A56CE1C10B9545CD1F3C7`。 |
| a07 `e2-04-d05-trace-begin.json` | `EAAF6C6AA69D20AFFA8CD455ECACCA94672F9F6A59BAEA1DECD001B3FD8BB6DB`；CombatID `16777218`，受管 token `72907`。 |
| a07 `e2-04-d05-one-day.json` | `9986C2A69CEA8D9E79F079B766D74E1E1495144C26D421EB9A4DF5C53A40ED45`；`53146344→53146368`，仅一日、最终暂停。 |
| a07 `e2-04-d05-trace-finish.json` | `5D2DDED6A49E173418C9C93DF00FC5D832E1CE9303E76E665FEC3E5A548968B8`；`bounded_trace_available`、`failure_flags=0`，同一 token/CombatID 的七条边界。`production_trace_ready=false`、`full_mutable_transition_bundle_complete=false`。 |
| a07 `e2-04-d05-post-snapshot.json` | `D1B726150EAD0142B74A65841DEB47CCF70C465F3F74CE20574E758642BF312B`；d06 暂停，但 `last_checkpoint_submission.date_raw=53146344` 仍是 d05。 |

在 a07 trace 的索引 0–4，唯一战报为此前已有的 `knight_wounded_by_enemy(47029,33435)`。索引 5（第六条）side 1 phase-fire 返回后，列表追加且仅追加 `knight_maimed_by_enemy`，`left_character_id=34333`、`right_character_id=47032`；索引 6（第七条）暂停后仍保留。七条的 CharacterID `34333` 均在团 `61`，`death_marker_present=false`、`prowess=11`；团 61 的 `effective_damage_raw=96,250,000`、`effective_toughness_raw=19,250,000` 始终未变，Q100000 下分别为 962.5／192.5。索引 6 的普通伤亡字段另有变化，不能以团人数变化推算其单位属性。用户提供的同 run d05/d06 第五行勇武 11 画面描述与原生字段相符，但本审计没有直接审图。

同一 d05 来源存档在既有 066 只读解码中有 melted SHA `3EA734AECA5992CA8DDAD87564C1B7090A7AC677DF23C1069764A5C93F42C4CA`（本次已复核该文件哈希）。其中 34333 的人物块 SHA `473A0934E66900AEE307BD72D1BAF37B5F4676F52E6A2077E632F2282D9A53B6`，`alive_data`、`regiment_id=61`、基础勇武 `3`，trait 为 `callous/craven/humble/education_martial_2/cautious_leader`，无 `one_legged/disfigured/one_eyed/maimed/wounded`；47032 基础勇武 `10`、威望货币 `300`。这些是**a07 冷载前的源档状态**，不是 a07 d06 后态。

## 历史 039→040 能解释到哪里

历史 039 的来源档 SHA `D978D75A2212604CFDD9BF7FBDEF3424E85E39C5092D7245D04590694017FA01`，**不同于 a07 的 695F…**，故是独立随机回放。两源档的 34333 源人物块 SHA 恰同为 `473A0934…53B6`，只证明该人物起点相同，不证明事件分支或后态相同。039 的 `007-finish.json` SHA `EC61C0FD308E09B95FED5F7D9AB0BEFA01054DD87ECD45A4D9897BEBBFC2DA14`：和 a07 一样在索引 5 新添 `knight_maimed_by_enemy(34333,47032)`，并且索引 0–6 的 34333 勇武**也一直为 11**、团 61 有效伤害／坚韧**也一直是 96,250,000／19,250,000 raw**。因此“事件已入战报，但同日七边界数值尚未改变”在有完整后存档的历史回放中也确实发生过。

039 同次 `008-after-save.json` SHA `0947BFCE60C184EBF5803D16BA34E84F36C52821513AB5C9B76BC0237F447301` 绑定其 d06 不可变后存档 SHA `9ACACDE3E2D1987180EFE5FFDDC32B092146E6116779AF0D4BEBC7C97B9B7F9A`；该存档的人物块有新增 `one_legged + wounded_1`，人物仍存活。040 从**这份 039 后存档**重新冷载，原生 `003-v3.json` SHA `A02504FC9D71F4CAB5D87AC0EE3BD67A044A29A258505A98A1E0FB95897D1E44` 才读到同身份骑士有效勇武 `7`、团 61 伤害 `61,250,000` raw、坚韧 `12,250,000` raw（612.5／122.5）；[原有逐对象投影](../../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_knight_maim_next_input.json)将这些原件精确绑定。

原版 `combat_phase_events/00_knight_phase_events.txt:921–950` 先记 `knight_maimed_by_enemy` 战报、再调用 `maimed_in_battle_effect`；`scripted_effects/20_health_effects.txt:1227–1268` 随机选择断腿、毁容、独眼或重伤及其后续效果。两文件当前 SHA 分别为 `E8F8E4978BB1AF130D74AA6ED72EE41F014B09C9F324608EBFB0E87D56A5EDB1`、`6D7DEF1245D899DE4DEBC42136815BC7F4D14F6A467A8320355507AD03528F12`。trace 的实现于 `combat_phase_event_trace_ring_v1.cpp:429–432,615–621` 只读当前人物对象勇武字段和战斗团条目的存储伤害／坚韧字段，**不读取 trait 列表，也不触发重算**。故 a07 的 11/962.5/192.5 只能陈述为**该时点读口的值**；它既不否定脚本随后写回，也不证明 a07 已得到 039 的断腿分支。历史 039 显示脚本 trait 写回与这些读口即时更新可以分离；具体是缓存失效、每日刷新还是复载触发重算，本审计没有直接证明。

a07 未保存 d06 精确后存档：外置 `save games/war_film_checkpoint.ck3` 与 d05 来源同 SHA `695F…`，`autosave.ck3`、`xar_checkpoint.ck3`、`xar_episode_seed.ck3` 三份同 SHA `9EFE18AC86AC2E4BB64AF6D1E64146A4DD120846658BA27CF096FA9F7861AAC1`，对应 `e2-04-d05-before-save.json` 明载的 **d05** 保存（`date_raw=53146344`）。a07 后态普通 snapshot 也仍指该 d05 提交。因此 a07 的致残 **trait 分支、人物后存档、下一次 V3 的勇武和团 61 属性均 UNKNOWN**。039→040 的 `11→7` 与 `962.5→612.5` 不得写成 a07 同一次实拍结果。

## 本期 E2-04 叙事与下一次取证

当前 a07 镜头若经 PTS 与 1× 审看可用，准确口播为：“第六日这场战斗的战报新添 34333 被 47032 致残；暂停时骑士列表仍显示 11 勇武，战斗统计读口也还没有下降。致残的具体伤情和下一帧战斗输入，留待同一回放的保存证据确认。”计算卡若要展示 `11→7`、`962.5→612.5`，只能明确标为**历史 039→040 研究板**；不能覆盖 a07 实拍并写成其后果。a07 的最新事件镜头也不能证明随机列表选第 0 项或已获得 `one_legged+wounded_1`。

若要在正式 E2-04 中用新同源回放讲“致残后输入从 11 降到 7”，需新建 a08 独立 attempt：精确校验 d05 不可变源档 `695F…`、保存回执、CK3 EXE/DLL/injector 与冷载身份；暂停 d05 同帧读 WarID/ArmyID/CombatID/日期与 V3 基线，受管 begin 后仅推进一日。先在 a08 自身 trace 证明同一 token/CombatID/date 的新增事件及人物 ID；事件不出现、对象不同、或分支不能区分时保持 RED，不强行续写历史 039 的数值。在 a08 d06 暂停的新 revision 上，使用已有受管 `ck3_save_checkpoint(expected_revision)` **一次**提交真实 d06 保存；该 API 会写 `save games/xar_checkpoint.ck3`、driver history/seed 等，须在新隔离 profile 中预存已有文件，冻结请求/响应、`date_raw=53146368`、路径、字节、SHA 与独占复制的 `d06-immutable.ck3` 及 sidecar，不以 ACK 代替落盘校验。再从这份新 d06 存档**独立冷载只读**同 CombatID 的 V3，逐对象核 34333／团 61 的勇武、效能、单位伤害／坚韧以及战斗身份。只有 a08 自己的保存解析和冷载 V3 同时闭合且实际读数确为 `11→7`，才能为 **a08** 录制对应数字口播；a07 与 a08 仍是不同运行，正式镜头须据实标注来源。若选择器改走其他致残分支、后存档与 V3 不匹配或未复现事件，数值结论继续 RED。
