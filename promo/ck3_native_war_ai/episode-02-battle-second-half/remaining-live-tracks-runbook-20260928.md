# E2-04/05/06 剩余镜头：精确来源与最短受管取材顺序

2026-09-28 静态就绪审计。本文未启动 CK3、未录新画面，也未给任何旧研究 attempt 补造 raw 或 clean span。下列 SHA 已在各自历史原生保存回执和无启动预检中冻结；执行时仍须重新核本机文件字节和本次最新正式 xar-promo Release。

## 必须分开的三次单日回放

源档/回执路径均在 `D:/workspace/ck3_native_war_ai_promo_work/` 下；原版 CK3 EXE 固定 SHA `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，玩家 `29829`，WarID `4`，玩家 ArmyID `18`，CombatID `16777218`。

| 最小录制轨 | 冻结源档与真实保存回执 SHA-256 | 本机 DLL/injector 精确 SHA-256 | 原生边界及旧无启动证据 |
| --- | --- | --- | --- |
| `e2-04-d05`，致残/第 6 日 | `episode01-paired-counter-trace-attempt-010/d05-immutable.ck3`：`695F1FDE17457004EB8D060C1F21146C3605374806DABACF6FB5FAB386882885`；`.../ck3-output/interactive-requests-responses/d05-save.json`：`6650C0DB79D063E066AB72402735C22FAE9FCB5D458A56CE1C10B9545CD1F3C7` | 当前 `D:/workspace/cwb2/` 的 DLL `EB643577E0DE6214582A667B3C6C52DB712CA75E46374BECB9DB5C36204F67E7` / injector `CE8A20C7B25A697058AB69B03629D6B7655BB2935AD147DF1E84895A826BF247` | `53146344→53146368`；无启动 `episode02-e2-04-day05-preflight-20260928-a01` 为材料 READY，**非运行时验收**。旧 039→040 的后档 `9ACACDE3...B7F9A` 是另一条历史回放，不能接作新拍后帧。 |
| `e2-05-d26`，击杀/第 27 日 | `episode01-paired-counter-trace-attempt-010/d26-immutable.ck3`：`C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B`；`.../ck3-output/interactive-requests-responses/d26-save.json`：`78931511D31E8400334D28DAD276F4CCDFBB342A901FC00B0BAFDCDEDA29584C` | 同上 | `53146848→53146872`；无启动 `episode02-e2-05-day26-preflight-20260928-a01` 材料 READY。020 击杀抽签、070 成长权重、036→038 次帧名册是三个独立旧回放；038 后档 `CD0648D7...08A55` 只来自 036。 |
| `e2-06-d11`，085 增援/首次出伤 | `episode01-full-edge-attempt-004/trace-d11-immutable.ck3`：`3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953`；`.../ck3-output/interactive-requests-responses/trace-d11-save.json`：`DD986180C7E9C4B42D43FC634884F5294387D18CF8F798012FAD621B37E9E4A5` | 历史 085 DLL `D:/wai/ck3_autonomous_player/native_bridge/build-fresh-20260927T025104Z-572e2125/xar_ck3_bridge.dll`：`1CC2AE965CD0EE897F918D50AF038F3DA874354DA7F3A57D2710B7BCCF44366F`；injector `D:/workspace/ck3_build_join_width_phase_thread_20260927/xar_ck3_bridge_injector.exe`：`34A1AB183F5173844A74E52A7F68195AAD859C380DFCA6B7E76F40611A51FB2D` | `53146488→53146512`；静态材料 `join-085-attempt-001` GREEN，旧受管无启动尝试因当时已有 CK3 而 environment RED，**须在自己取得空闲屏幕后重做**。085 旧 battle-control sibling 查询 RED，但私有 join/full-entry 局部捕获成功；本次须独立验证。 |

所有三个旧 capture report 的 `raw_video=null`、`clean_spans=[]`。旧卡可以作为明确标 `039→040`、`020`、`070`、`036→038`、`085` 的研究板；新实机画面必须标新 attempt 身份。随机路径不同就改新素材数字/文案，不能把历史数值贴在新画面上。

## 三个 600 秒窗口足以先取得最小实拍集

先完成 E2-02/03 当前屏幕 attempt 并释放，再按 `e2-06-d11`、`e2-04-d05`、`e2-05-d26` 串行取屏。这是**三个**相互独立的源载入和 recorder，计划原片下界为 `3×600=1800` 秒；另需冷载、地图、GUI、媒体封口时间。085 只需一次第 11→12 日回放就能给 E2-06 与 E2-07 共用画面，先做它以便尽早暴露旧 battle-control 查询限制。039→040、036→038 的历史后档冷载比较，以及 020/070/036 三次各自重拍，先不占这批屏幕；若剪辑要把它们的旧精确数值称作**新同帧实拍**，必须另排独立 run 并重取数据。一个新的第 26 日回放只能提供它自己的事件和次帧 UI，不能同时成为旧 020、070、036 三条随机轨。

每次领取任务总线 `ck3-screen:acquired`；无其他 CK3/录制进程后取当次窗口变化和原始桌面像素，亲自审阅 Steam“离线模式”并写新回执。画面分辨率、CK3 窗口完整可见性、英文键盘与鼠标坐标门按 [E2-02/03 首次实拍 runbook](first-live-recording-runbook-20260928.md)执行。三条轨都用全新外置 attempt/state/output/profile/pipe；先无 `--capture` 预检，再**另一个**新 attempt 显式 `--capture`。`capture_session.py` 必须设 `--frontend-timeout 900 --interactive-seconds 3600 --enable-private-phase-trace --steam-offline-receipt <本次已审回执>`，配本表精确 `--checkpoint-save`/`--checkpoint-receipt`/DLL/injector。默认前端等待 360 秒偏短；近期本机冷载曾超过它。无启动 READY 只证明材料，不证明运行时 trace 钩子。

冷载后停在来源日期、墨西拿战斗与战争 UI 可见。先用 `record_bounded_gameplay.py record --seconds 600 --track <轨名> --workdir <新 recorder 子目录> --session-output <本次 ck3-output> --source-save <本轨源档> --source-receipt <本轨真实保存回执> --steam-offline-receipt <本次回执>` 启动唯一 FFmpeg recorder；该命令保持独立会话直到自然封口。然后执行同目录 [`remaining_live_step.py`](remaining_live_step.py)：

1. `observe --track <轨名> --session-output <本次 ck3-output>`；它只读源帧、玩家、WarID 4、ArmyID 18 和日期。骑士两轨还要求 battle-control 同帧 CombatID `16777218`；085 的历史 battle-control sibling RED，observe 明记尚未绑定 CombatID，只有后续私有 trace begin 接受该 ID 后才能推进。
2. 用 `record_bounded_gameplay.py mark --workdir <新 recorder 子目录> --kind <本轨-before> --date-raw <本轨源日期> --combat-id 16777218 --war-id 4 --capture-screenshot` 追加画面锚点。骑士两轨再传 `--control <本次 ck3-output>/interactive-requests-responses/<轨名>-control.json`；085 传 `--report <本次 ck3-output>/interactive-requests-responses/<轨名>-snapshot.json`。mark 的墙钟不是媒体 PTS；确认游戏画面实际包含所需面板后才能继续。
3. `advance --track <轨名> --session-output <本次 ck3-output> --recorder-workdir <新 recorder 子目录> --sequence-token <本 run 新的正整数>`。脚本先重读同一暂停 revision、检验正在运行的 600 秒 recorder 和哈希绑定 mark，然后在**本次独立 profile**保存一次 checkpoint、按历史私有 action envelope arm trace、提交且只提交一次 `life-advance`、finish trace、读次日快照。任一失败或请求超时都保留 request/response/intent，**不得重发同一轨**。脚本的 `ONE_DAY_CAPTURED_UNREVIEWED` 只证明一日边界与来源绑定，不证明指定骑士事件、085 数值、UI 可见、raw PTS 或 clean span。
4. 在同 run 录人物/名册或入列/战宽的事件后 UI、标 `after` 并保存各回执与截图。等 recorder 自然结束并保全 raw、stderr、完整 ffprobe、逐帧 PTS，再用 `remaining_live_step.py finish --track <轨名> --session-output <本次 ck3-output> --recorder-workdir <新 recorder 子目录>` 收束受管会话；任何 RED/partial 原样保留。按 [PTS 审计器](audit_raw_video_pts.py)和正式 CK3 adapter 的新 report/timeline/evidence-index/clean-frame 合同，另立审片与 bundle。只有逐帧核 UI/日期/对象、原速 clean span 和最终 1× 人工完整观看后，才能给成片精确字节签核。

E2-04 的“`34333` 致残、61 团属性变化”、E2-05 的“14 人抽中 `34120`、目标 `33437` 死亡及 `69→68/30→29`”、E2-06 的“ArmyID `22` 13 团、2570 起始/2560 当前、`2467/2220`、首次出伤 `2220`”在**新 run**中都尚未取得；逐项对照新 private trace、同日/次日原生输入和 raw UI。085 必须保留 join/full-entry/首次出伤同钩子原件；若新 DLL 的 trace finish 未捕获对应字段，就把该新 run 降为场景画面，计算卡继续只标历史 085。新 run 没有被证实的精确数字，不给新镜头配旧卡的“同一实测”字幕。
