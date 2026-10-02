# E2-05 a02 同 run 骑士事件候选审计

2026-09-29。外置 run 为 `D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-05-d26-live-20260929-a02/`。屏幕负责人于 2026-09-28 19:22:21 UTC 明确 RELEASE 后，本审计才读取已封存的小型原生 JSON、marks 与截图文件哈希。未打开 CK3、未解码原始录像、未审截图画面，也未改写外置 run。聚焦[校验器](verify_e2_05_a02_candidate.py)返回 GREEN 的含义只是下列**候选事实与精确原件一致**。

## 原件身份

本 run 从旧 010 生成的第 26 日不可变存档 **独立冷载**：存档 52,880,496 字节，SHA-256 `C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B`；来源回执 SHA-256 `78931511D31E8400334D28DAD276F4CCDFBB342A901FC00B0BAFDCDEDA29584C`。CK3 EXE 为 1.19.0.6，SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；本次候选 DLL SHA-256 `EB643577E0DE6214582A667B3C6C52DB712CA75E46374BECB9DB5C36204F67E7`。共享源存档不等于共享运行轨迹，020、070、036→038 的抽签和后态不能移植到 a02。

| a02 原件（相对外置根） | 字节 | SHA-256 |
| --- | ---: | --- |
| `ck3-output/capture-report.json` | 8,654 | `F0A9F2461F72C2B2B55109142C796F14D09097439824CFADFE19F5C8DB537859` |
| `ck3-output/operator-steps/e2-05-d26-observe.json` | 4,240 | `7239F68CFE7C517468628E061BD50AD84E44E0492D965F010972DBD0FC1E9294` |
| `ck3-output/interactive-requests-responses/e2-05-d26-control.json` | 83,317 | `D41E384CE022C261E15E3761980A0A78E26BA0B21C9FCF3F2393F062F03CEC1F` |
| `ck3-output/interactive-requests-responses/e2-05-d26-trace-begin.json` | 11,489 | `95E81F63B449EB9E4AA301672CD95053F241C60723C34A4BE1B70E481E9F91B9` |
| `ck3-output/interactive-requests-responses/e2-05-d26-one-day.json` | 19,929 | `ED502C01BEBDDA1887D2A48133D8807C98A2547D7008706FED6528F32461BB95` |
| `ck3-output/interactive-requests-responses/e2-05-d26-trace-finish.json` | 431,957 | `BFF0A9CFCE858C88B9FEA67D0FB646CDB7175BA7DC957898769BE02D5479C7D0` |
| `ck3-output/interactive-requests-responses/e2-05-d26-post-snapshot.json` | 215,859 | `062907DC73AAD127C766F45E754BEC7457E8C6B956D842A87DB2BF35B6030249` |
| `ck3-output/operator-steps/e2-05-d26-advance.json` | 7,324 | `304EFA9223DCB2DC5313736938E890382139FBE2BA85E43E1910DD0ADA22C6CA` |
| `recording-e2-05-d26-a01/marks.jsonl` | 3,307 | `3266390257DAEFF91114FF1E7D017192ECF50D836776D1BC5E8191643C9C5337` |
| `recording-e2-05-d26-a01/recorder-final.json` | 1,927 | `B27C9434789CF4BD8F0F6BE3273902AE1274DBE1DD1D614D40F6068CC78AD7F4` |
| `ck3-output/session-result.json` | 7,433 | `09D67A493473ED4FA6C65B643114B6EBE92AC40B9E2E5CD356B02E2A1AA76D42` |

校验器还逐字节检查 d26 snapshot、存档后 control、三张 marks 所指 PNG 与各自报告。原始 MKV 只按录制器报告核对文件大小 2,451,530,594 字节；报告给出的 SHA-256 为 `7FC3D614C50AD958DA57359248A196A230BD2B0B5B511EF242596837042C1C0F`，本审计**没有重新哈希或解码 MKV**。

## 同 run 能确认的窄事实

1. d26 同源快照与原生 battle-control 查询绑定 WarID `4`、ArmyID `18`、CombatID `16777218`、省 `2633`、玩家角色 `29829`；日期原始值 `53146848`，暂停、主阶段第 22 日，ArmyID 18 为战斗 side 1。存档后的控制查询仍是这一日和同一战斗。受管推进恰好一日到 `53146872` 并暂停；普通后态仍列 WarID 4 和 ArmyID 18 `in_combat=true`。
2. 私有 trace 的前五条边界保持**精确相同**的两条既存 `knight_wounded_by_enemy` 战报。索引 5（第六条）`native_capture_after_side1_phase_fire_return_0x2309EFF` 的 `capture_failure_flags=0`，战报从两条变为三条；新增行精确为 `stable_key=knight_killed_by_enemy`、`type_raw=3`、`side_index=1`、`target_right=false`、`left_character_id=33437`、`right_character_id=34120`。a02 原生记录可支持“战报在本次 side 1 phase-fire 返回边界新增”这句话；左 33437 属 side 1、右 34120 属 side 0 骑士名册，但这里没有重放选择器内部抽签。finish、前后 checkpoint 与七条记录均带同一受管日 token `101`、CombatID `16777218`；前两条日期为 `53146848`，后五条为 `53146872`。
3. 索引 5（第六条）记录的 side 1 仍有团 `65` 和骑士 `33437`，人物 `33437` 的 `current_regiment_id=65`、`death_marker_present=false`。索引 6（第七条）`paused_next_day_stable_query` 的 side 1 团条目由 24→23、骑士条目由 14→13；前后 ID 集合差异中，消失的分别是团 65／骑士 33437；原排程条目的 `current_character_id` 由 33437→0。side 0 骑士 ID 集合未变。这支持**本 run 暂停时该参战团与骑士从战斗侧名单移除**，不是完整角色死亡证明。
4. 六条可读取人物数组各 36 项，同一人物跨边界重复记录，`death_marker_present=true` 合计 **0/216 个记录位**；索引 5（第六条）的 33437 标记仍为 false。索引 6（第七条）暂停记录 `capture_failure_flags=16`，人物、战报、勋业数组全空，所以不能把最后一条空数组当成“全员存活”或“全员死亡”的读数。整份 trace 自报 `status=failed`、`failure_flags=1040`、`record_count=7`、`production_trace_ready=false`、`original_trace_ready=false`、`full_mutable_transition_bundle_complete=false`。
5. `marks.jsonl` 三个场景标记分别指向 d26 前、d27 后和 d27 玩家骑士画面；所列源 JSON、报告、PNG 的字节与 SHA 均匹配。标记的 190.884、304.990、388.113 秒是录制器单调时钟近似值，原件明确写明 **不是视频 PTS**。录制器返回 `ENCODED_UNREVIEWED`、600 秒、2560×1440、12,656 个有 PTS 帧、FFmpeg/ffprobe 均 exit 0；`clean_spans_certified=false`、`human_review_completed=false`。会话 `shutdown.ok=true`、`cleanup_proven=true`。

## 使用边界与下一步

正式视频可以把 a02 暂列为“同 run 战报新增与战斗侧名册移除的候选原始证据”。**不能**口播“a02 已原生证明 33437 死亡”“34120 经 14 人候选抽签被选中”“成长列表走了 40/30/15 的空分支”，也不能让旧 020/070/036→038 的计算卡冒充这段录像。是否展示战报、名单和前后 HUD，须从 a02 原片另做 PTS 定位与 1× 连续审阅；若要把角色死亡写成确定事实，需要同 run 第 27 日可用的人物死亡状态读数或正式受审画面。若要把选择器数字写成 a02 结论，还需要 a02 自身的候选集合、draw/index 和相关写回回执。现有原件既不满足这些门，也不满足完整原生转移 trace 门。
