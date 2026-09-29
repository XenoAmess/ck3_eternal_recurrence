# E2-04 a07：第 5→6 日同轨实拍与证据边界

2026-09-29 CST。此页只索引外置、不可覆盖的 a07 原件；与 a04–a06、历史 039→040 和 E2-05 分轨。正式 CK3 / 录像来源字节留在 `D:/workspace/ck3_native_war_ai_promo_work/`。本次尚无 clean span、人工 1× 审片或成片签核。

## 来源与受管准入

| 门 | a07 原件与结论 |
| --- | --- |
| 源 | `episode01-paired-counter-trace-attempt-010/d05-immutable.ck3`，52,172,645 B，SHA-256 `695F1FDE17457004EB8D060C1F21146C3605374806DABACF6FB5FAB386882885`；同目录 `ck3-output/interactive-requests-responses/d05-save.json` SHA-256 `6650C0DB79D063E066AB72402735C22FAE9FCB5D458A56CE1C10B9545CD1F3C7`。不是 d26 存档。 |
| 二进制 | CK3 EXE `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；DLL `EB643577E0DE6214582A667B3C6C52DB712CA75E46374BECB9DB5C36204F67E7`；injector `CE8A20C7B25A697058AB69B03629D6B7655BB2935AD147DF1E84895A826BF247`。 |
| 原生 GUI | a04 UI 保存原件 `native-ui-saved-settings-a01.pdx.txt` SHA-256 `E6AD4D44435F17B77C6A5BD6554AB812FBF396D9A27370DB7CF9B56D658FDF7D`；本次 before/postmap/posthold 的原生 `value="1"` 区块 SHA-256 `F5172E8A9DC92E8998957B5F443575608D04AC44342CE085DF23370CDA26F593` 均通过，仍以实际像素判画面。 |
| 工具链 | `D:/w/e2` 固定 HEAD `306064c5372b4c043a17758d84902a52349e6cb2`；`capture_session.py` SHA-256 `A6C101159B904F380B50FAD764F0DB01D9FB1B297B4145F43A05AB713F701C67`；正式 `xar-promo 0.2.1` wheel SHA-256 `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`，独立 manifest `episode02-e2-04-d05-xar-run-20260929-a07/run-manifest.json` SHA-256 `92C8CFDD1B1B3998875D76E4F7C4A1C0D5751CF1631837EF56D8A180AA659EDE`。 |
| 屏幕/Steam | `promo-episode02-e2-04-a07-capture-20260929` 于 23:03:41Z 独占 `ck3-screen` seq2212，常驻 180s heartbeat；`episode02-e2-04-d05-offline-20260929-run-a07-a03/` 的两张随机挑战原图确证当前像素变化，执行者直接审阅第二张中的 Steam“离线模式”；`reviewed-steam-offline.json` 为正式 live 入口。桌面 2560×1440 的 Win32/GDI/pyautogui 一致，原显示 1920×1080。旧 a01/a02 重复哈希原样保存，不作 fresh 证据。 |
| 新预检/会话 | `episode02-e2-04-d05-preflight-20260929-a07/ck3-output/preflight.json` 为 `READY_FOR_BOUNDED_LIVE_ATTEMPT`、`ck3_started=false`；`episode02-e2-04-d05-live-20260929-a07/ck3-output/` 是独立 live root/pipe。warmup 清理后 final CK3 PID11952 于 23:15:17Z 启动，23:32Z 地图 ready；a06 的 watchdog prelaunch RED 不是本次运行结果。 |

## 同帧和原生画面

`ck3-output/operator-steps/e2-04-d05-observe.json` 绑定 `date_raw=53146344`、paused、actor29829、War4、Army18、Combat16777218、province2633，`native:3` / wrapper revision4 / native revision3，同帧 combat control `accepted=true`。原始地图经只作用于呈现的 `center-map-on-landed-title` 到 `c_messina` / capital province2633；点击按原图 2560×1440、`pyautogui.size()` 与 `desktop_coordinate_map.py --receipt` 换算，点击 ACK 后另拍原图判业务状态。

局部战斗窗原图在 `episode02-e2-04-d05-screen-lease-20260929-a07/`：

| 原图 | SHA-256 | 原生像素结论 |
| --- | --- | --- |
| `battle-panel-cursor-clear-a01.png` | `9D1A6D31DB083609506E17BAEE11BF3495682618906C688C5132CDF04F7E50E1` | 2560×1440。1288/2003 双方兵数、+1 优势、兵种图标与底部 `11名骑士` / `13名法里斯` 全部可读；装饰边框越出底缘，实际字段没有截断。 |
| `player-knights-hover-a01.png` | `F371372AC7251E649C7383E1BE02DA5C02F385A976E2646B5568AD5E1A989BD4` | 同一暂停 d05 的己方 11 人姓名/勇武 tooltip 全部可见。 |
| `enemy-knights-hover-a01.png` | `375083F5BBD6440E1CEF3116074A6FA343A3ECF1783C0793F88E9A7C9547C07F` | 同一暂停 d05 的对方 13 人姓名/勇武 tooltip 全部可见。 |
| `battle-panel-final-prerecorder-a01.png` | `762AF33866847DDD5C9CD2B0A7360316F8BB1E7F007DF6418E4D1F770F85A1B2` | 看完两侧名单后回到战斗窗；双方兵数、优势、兵种和 11/13 名单行仍可读，无遮住面板的 tooltip。 |
| `d06-player-knights-hover-a01.png` | `943A34223CFE5C19FFEE5488C5D4C9F2F678B1CBD6A5DA21DBC37AA566E425BD` | 同 run 暂停 1066-12-09，己方名单仍 11 人，原图不显示目标角色新伤残标记或勇武下降。 |

以上逐项视觉结论只指这些原始帧。显示出的 34333 对应姓名仅可根据同一原生 roster 的唯一 11 勇武值推断为己方名单第 5 行；没有直接显示内部 character ID 的 UI 原图，旁白不可把这一步写成像素直接验证的 ID。

## 唯一录像与一次日期动作

外置 `episode02-e2-04-d05-live-20260929-a07/recording-e2-04-d05-a07/` 是全新录制 workdir。`recorder-start.json` 记录 2026-09-28 23:55:10.714827Z、唯一 FFmpeg PID15404、30fps `gdigrab`、真实桌面 2560×1440、600s 和 argv。生长中的 MKV 在录制中由 `ffprobe` 只读确认视频 stream 2560×1440；`geometry-admission.json` 的 GDI/Win32 与 `pyautogui.size()` 一致。`marks.jsonl` 的 `d05-before` 标记在 23:58:03Z 绑定当次 combat control、observe 回执、原始截图 SHA-256 `EFC7C208E8FB81CB2D0D815ECEDD1D329C6F013667F0F1EF24989B24E0D14718` 和最终入录画面 SHA。墙钟 mark 不是视频 PTS。

只提交一次 `remaining_live_step.py advance --sequence-token 72907`，`ck3-output/operator-steps/e2-04-d05-advance.json` 于 23:59:23Z 返回 `ONE_DAY_ADVANCED_UNREVIEWED`；原生 post 为暂停 `date_raw=53146368`、actor29829、War4、Army18 仍 combat、snapshot `native:7` / wrapper revision8 / native revision7。`d06-after` mark 于 00:02:50Z 绑定原始 d06 名单和同 run trace，未续日。

`recorder-final.json` 于 00:07:52Z 封口：FFmpeg/ffprobe exit0，原始 `raw/e2-04-d05.mkv` 2,459,812,208 B、SHA-256 `950D94FE20A937806A1A8976160D66D8BF04D5DE3C7CD85A67D7DF5ACE45D3C9`；视频 2560×1440、format duration 599.966s、13,309 帧、首末 PTS 0.000000/599.933000。状态严格为 `ENCODED_UNREVIEWED`，`clean_spans_certified=false` / `human_review_completed=false`。全量帧 PTS 间隙审计待现金 CK3 冷载磁盘窗口结束后以新外置输出执行；当前布尔 `video_pts_complete=true` 仅证明首末与 count，不是连续性证明。13,309 帧低于名义 30fps×600，正式素材尚需断档和视觉审阅。

## 34333 事件的事实边界

同 run 原件 `ck3-output/interactive-requests-responses/e2-04-d05-trace-finish.json` SHA-256 `5D2DDED6A49E173418C9C93DF00FC5D832E1CE9303E76E665FEC3E5A548968B8`。`managed_trace.trace.records[0]` 己方 Army18 骑士勇武序列为 14,14,13,12,11,10,9,5,4,3,2；唯一 11 勇武对应 regiment61 / character34333。原图己方 tooltip 也仅有一行 11 勇武，因此只能以原生 roster + 唯一值**推断**该行与 34333 对应，不能称像素直接读到 ID。

`records[5]` 首见 `knight_maimed_by_enemy`，left_character_id34333、right_character_id47032、`side_index=1`、`target_right=false`；`records[6]` 仍有此 event。records[0]→[6] 中 34333 的 `current_regiment_id=61`、`current_regiment_back_reference_matches=true`、`death_marker_present=false`、martial13、learning8、**prowess11 不变**。regiment61 仍在 Army18，`effective_damage_raw=96250000`、`effective_toughness_raw=19250000` 不变；`current_fighting_raw=99677→99335`，`soft_casualties_raw=207→426`，`hard_casualties_raw=116→239`。trace 没有该角色 trait 字段，d06 原图也没显示已应用伤残或有效勇武下降。因此本次只可说**原生 trace 记录一条关联 34333 的 maimed battle event，次帧仍留在 regiment61 / 可见名单未减员**；伤残 trait 是否已落、强度何时变化仍未证，不得把历史 039→040 的具体数值或另一 run 的镜头拼给 a07。旁白稿当前第 52–56 行需按新轨重新核对后才能配此画面。

独立历史核对显示，039 的同日 trace 也仍是 prowess11、regiment61 攻防 raw 96250000/19250000；039 后续真实 d06 存档才见 `one_legged` + `wounded_1`，040 是**另一次冷载**读到 prowess7、团攻防 61250000/12250000。该 11→7 计算卡只能明确标为 039→040 的历史研究板。a07 没有对应同源后态存档，视频不得将该数值卡接作 a07 战斗窗的下一帧或同轨结果。

来源身份勘误：039 live 的 command/checkpoint-copy/source-receipt 与 a07 均绑定 attempt-010 的 d05 存档 SHA-256 `695F1FDE17457004EB8D060C1F21146C3605374806DABACF6FB5FAB386882885` 和 sidecar `6650C0DB79D063E066AB72402735C22FAE9FCB5D458A56CE1C10B9545CD1F3C7`。它们是**同源字节的独立运行**；039→040 的后态仍不能当作 a07 的实机次帧，DLL 与 RNG 路径也须各自核验。历史 `D978…` 只见于后续 projection recheck，不是 039 的 live 冷载源。

本次**没有可冷载的 d06 受管存档及真实保存回执**。`e2-04-d05-before-save.json` 的保存发生在 23:59:06Z 左右、date_raw=53146344；隔离 profile 的 `autosave.ck3`、`last_save.ck3`、`xar_checkpoint.ck3`、`xar_episode_seed.ck3` 的 mtime 均在 23:58:57–23:59:10Z，先于 23:59:23Z 的一次日期动作。`war_film_checkpoint.ck3` 是启动前 d05 源档副本。不能将这些文件的存在或 d06 post snapshot 当作 d06 checkpoint，更不能下次按 d06 冷载。若需续拍角色特质，应从有新真实 save receipt 的新 attempt 再做。

## 收尾

`remaining_live_step.py finish` 只在录制自然结束后发唯一 finish 请求。`ck3-output/session-result.json` 于 00:09:06Z 显示受管 `environment_session_complete=true`、进程库存空；外部录制独立于 capture session，后者的 `ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO` 不否认上表单独封存的原始 MKV。`display-restore-a01.json` 于 00:11:27Z 确认 CK3/FFmpeg/OBS 无残留，把 2560×1440 恢复原 1920×1080，Win32 与 `pyautogui.size()` 一致。watchdog 停止；任务总线 00:12:30Z seq2236 `done/resources=[]`，`ck3-screen` 正式释放。

后续只读工作：新 append-only 全量 PTS 审计、稀疏视觉核对、可能的 clean span 候选、人工 1× 审片与同 run 口播/卡片事实修订。任何机器 GREEN 都不自动生成 clean span、人工签核或成片。
