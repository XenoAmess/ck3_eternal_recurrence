# E2-04/05/06 后续取材静态就绪报告

审阅时间：2026-09-28 10:02 UTC。仅做文件哈希、CLI 与既有回执核对；没有启动 CK3、占用屏幕、创建新取材 run 或改写历史 attempt。执行步骤以 `remaining-live-tracks-runbook-20260928.md` 为准。本报告不能替代当次屏幕租约、Steam 离线原图审阅和新 run 的 no-launch 预检。

## 当前可用输入

2026-09-28 当次访问独立仓库 [latest 正式 Release](https://github.com/XenoAmess/xar_promo_toolchain/releases/latest) 指向 `v0.2.1`。本次显式解释器为 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`，`xar_promo --version` 与 `pip show` 均为 `0.2.1`；仓库精确 wheel pin 的 SHA-256 为 `f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621`。依赖探测：`psutil 7.2.2`、`Pillow 12.3.0`、`mcp 2.0.0`、`pywin32 312`，FFmpeg/ffprobe 命令均可解析。开始**每个**新 run 前仍须重查 latest；若变更，先更新 pin、安装及验证相关 `--help`。

当前 CK3 EXE `C:/SteamLibrary/steamapps/common/CRUSAD~1/binaries/ck3.exe` 再哈希为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。三轨的来源、实际保存回执和二进制也在本次逐文件重新哈希，全部与冻结表一致：

| 轨道 | 精确源档 SHA-256 | 原生保存回执 SHA-256 | DLL / injector SHA-256 | 日期门 |
| --- | --- | --- | --- | --- |
| `e2-06-d11` | `episode01-full-edge-attempt-004/trace-d11-immutable.ck3`：`3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953` | 同 attempt 的 `ck3-output/interactive-requests-responses/trace-d11-save.json`：`DD986180C7E9C4B42D43FC634884F5294387D18CF8F798012FAD621B37E9E4A5` | `D:/wai/ck3_autonomous_player/native_bridge/build-fresh-20260927T025104Z-572e2125/xar_ck3_bridge.dll`：`1CC2AE965CD0EE897F918D50AF038F3DA874354DA7F3A57D2710B7BCCF44366F` / `D:/workspace/ck3_build_join_width_phase_thread_20260927/xar_ck3_bridge_injector.exe`：`34A1AB183F5173844A74E52A7F68195AAD859C380DFCA6B7E76F40611A51FB2D` | `53146488→53146512` |
| `e2-04-d05` | `episode01-paired-counter-trace-attempt-010/d05-immutable.ck3`：`695F1FDE17457004EB8D060C1F21146C3605374806DABACF6FB5FAB386882885` | 同 attempt 的 `ck3-output/interactive-requests-responses/d05-save.json`：`6650C0DB79D063E066AB72402735C22FAE9FCB5D458A56CE1C10B9545CD1F3C7` | `D:/workspace/cwb2/xar_ck3_bridge.dll`：`EB643577E0DE6214582A667B3C6C52DB712CA75E46374BECB9DB5C36204F67E7` / 同目录 `xar_ck3_bridge_injector.exe`：`CE8A20C7B25A697058AB69B03629D6B7655BB2935AD147DF1E84895A826BF247` | `53146344→53146368` |
| `e2-05-d26` | `episode01-paired-counter-trace-attempt-010/d26-immutable.ck3`：`C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B` | 同 attempt 的 `ck3-output/interactive-requests-responses/d26-save.json`：`78931511D31E8400334D28DAD276F4CCDFBB342A901FC00B0BAFDCDEDA29584C` | 与 E2-04 相同的 `cwb2` 配对 | `53146848→53146872` |

上述相对源档路径的根是 `D:/workspace/ck3_native_war_ai_promo_work/`。E2-04/05 各有旧 `episode02-e2-04-day05-preflight-20260928-a01`、`episode02-e2-05-day26-preflight-20260928-a01`，结果 `READY_FOR_BOUNDED_LIVE_ATTEMPT` 且 `ck3_started=false`；它们只证明当时的材料。E2-06 的旧 085 静态材料可查，但当时受管 no-launch 因屏幕上另有 CK3 而 environment RED。三轨均没有新实机画面或 clean span。

## 每轨新窗口的可执行门

1. 等 E2-09 清场并由主代理交接后，查 task bus owner、CK3/FFmpeg 空进程，独占 `ck3-screen`。每轨重新用本次真实窗口变化和原始桌面截图确认 Steam“离线模式”；屏幕、几何、键盘与面板门按首次实拍 runbook。不得沿用 E2-02/03 离线回执。
2. 每轨先建立新的 xar-promo `start-run --run-id <唯一ID> --run-directory <独立平级 native-run 目录> <当次ProjectConfig>`，保留配置精确字节快照；另设外置 `.../<track>-preflight-<new-id>/` 与 `.../<track>-live-<new-id>/`、不同 state/output/profile/pipe。不要因 `start-run` 提前创建 live root。先运行 `capture_session.py` **不带** `--capture`，要求 `READY_FOR_BOUNDED_LIVE_ATTEMPT`、`ck3_started=false`、新查的源和二进制哈希相等；再用另一个全新目录执行 live。`--frontend-timeout 900` 给地图门最多 1800 秒；live 加 `--interactive-seconds 3600 --enable-private-phase-trace --steam-offline-receipt <本次审阅回执> --capture`。当前 `capture_session.py --help` 已实证支持这些参数。未拿到独占屏幕时不要调用这项空进程敏感预检。
3. 原生 map/source readback 后，以同源档与回执开一个独立 `record_bounded_gameplay.py record --seconds 600`，先验当前原生桌面尺寸、`pyautogui.size()` 与首帧编码尺寸相同，再运行 `remaining_live_step.py observe`、追加带原生回执和截图的 `before` mark。脚本实际 CLI 已核 `e2-06-d11/e2-04-d05/e2-05-d26` 三轨，`record`/`mark` 参数也已核。
4. 在 recorder 仍运行且同一暂停 revision、同源 `before` mark 完整时，单次执行 `advance --sequence-token <本 run 新正整数>`。脚本先保存本 run 的前帧 checkpoint，arm 私有 trace，再做**一次** `life-advance` 并取次帧。任何超时、来源分叉、control RED、保存失败或 trace RED 都原样留档，不在同轨重发；前帧日期仍在时也只能作为场景镜头。E2-06 的旧 battle-control sibling RED 仍是限制：私有 begin 可证明 CombatID 被解析，却不能单独证明 ArmyID 18 同帧 membership。
5. 录后帧的事件/人物/名册或入列/战宽 UI，追加 `after` mark。让 600 秒 FFmpeg 自然结束，保存 raw、stderr、recorder-final、完整 ffprobe 和逐帧 PTS；只在 recorder 封口后 `remaining_live_step.py finish`，核受管清场再释放租约。新 raw 和原生报告需要另外的 PTS/人工画面审阅；`ONE_DAY_ADVANCED_UNREVIEWED` 与编码完成都不等于 clean span。

推荐串行顺序是 **E2-06 → E2-04 → E2-05**，先暴露 085 的历史 control/trace 风险。最小原始录像预算 `3×600=1800 秒`。本机 E2-02/03 冷启动到地图约 11 分钟，按每轨冷载、UI/几何、10 分钟录像和清场估 **30–50 分钟独占屏幕/轨，合计 90–150 分钟**；这是排程预估，遇冷载达到 `900+1800` 秒门、画面异常或 RED 时不能压缩录像或越过受管会话截止。每轨 3600 秒 interactive 是上限，实际应在 raw 封口后尽早安全结束。

停止边界：E2-04 只取第 5→6 日，E2-05 只取第 26→27 日，E2-06 只取第 11→12 日；第 6/27 日的旧后档与旧 020/070/036/038/040/085 研究轨不拼成同一新运行轨迹。新 run 若没有同 run 事件、计算输入与 UI 回执，旧卡只按历史研究板展示，不给新画面贴旧精确数值。所有原件、失败和 partial 都 append-only 保全。
