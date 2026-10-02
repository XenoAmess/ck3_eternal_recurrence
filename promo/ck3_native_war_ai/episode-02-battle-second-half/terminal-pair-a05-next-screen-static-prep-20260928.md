# E2-09 下一受管窗口：a05 静态准备

2026-09-28，等当前 a02 录制、审计和清理完成后，本轨才排到屏幕。**本次只做无屏幕准备**：未检查或操作桌面、Steam、CK3、PID 或任务总线；未领取 `ck3-screen`；未调用任何 `--execute`。须由 `/root` 明确通知 a02 PIDs 清零及 lease 释放，执行者才可领取独占屏幕并取得新鲜 Steam 离线画面。

## 已冻结的正式输入

- [正式 xar-promo Release](https://github.com/XenoAmess/xar_promo_toolchain/releases/latest) 与本次新下载的 GitHub API 均为非 draft、非 prerelease `v0.2.1`。新 wheel 为 190,405 B，SHA-256 `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`，与 API 发布 digest、`tools/requirements-promo-toolchain.txt` 和解释器 `direct_url.json` 一致。API 原件 SHA `B84B40AA335B8493B5EC6A85F88EAFD0F9913825D6E5745C39032333A8318E7C`。主工作树解释器 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe` 为 Python 3.14.7，`xar-promo 0.2.1`；已核顶层、`start-run`、`validate`、`preserve` 的 `--help`。`D:/w/e2/tools/.venv` 不存在，所以显式使用已验证的主解释器。下一实际 capture 若出现新正式 Release，另立新 run 并更新 pin/解释器，不能把今日检查当作长期许可。
- 已从 `D:/w/e2/.../project/promo-project.json` 精确字节创建 `e2-09-terminal-pair-20260928-a01`：[外置 run manifest](D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-screen-prep-20260928-a01/xar-run/run-manifest.json)。配置 SHA `B00B4EA61EC2240ED1CBF718F654137F5ABED3953E1E3BF7F204CC38332F2778`；manifest 在保全 release API、wheel、a05 静态和准入回执四项后的 SHA 为 `A88540C5318B38EB10E39A8047AD01D1F7ED32C899BAE6765524BF39D6875112`，`validate --json` 为 `GREEN`、`files_checked=true`、`artifacts=4`、`chapters=6`。后续 `preserve` 将合法追加 manifest 历史，不能再用当前 SHA 判断之后的版本。
- [append-only 静态准备回执](D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-screen-prep-20260928-a01/static-window-preparation.json) SHA `086F2549D4738F77F6B1B4D8D579FDFB587F96677498EF50817B53B228A4AB15`。a05 静态/准入回执分别为 `9A98CE3CA00A3EAC6049DE0722D43C95390635660809C5EAB9EEF7F5B4139ECD` / `DB9C23ECF5633704090D97CDFAF5A61DE30913C71D25F442ACA5957908B01935`。
- 复算源第 27 日 save / 保存回执 SHA：`F085D8ABB89A354FA1004DBE8800505BC952AA8A68C0EA21AAB788F9875FEEB3` / `5198123BD71842624A3FB933492F78C3BB11C65D2DED634E3965FDC79B90A012`。CK3 EXE / 候选 DLL / injector SHA：`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` / `FCAFBA2A73E1EEF1E2651ADD40F71CE66B9FE16E4E61BD014DBA65C9965AEBD8` / `3773042110D9E207FD02E00BF5376A033E71B70433B6B650088550A522B581C5`。
- 集成入口 `D:/w/e2/.../integration/capture_session.py` SHA 仍为 `D62555C435E23A1057ACD0FF0C4EB834F1E52A4089E9702A1B5FB3A1D996F48A`，所以 a05 仍适用。入口允许 frontend 上限 1500 秒；本次选择 frontend **900**、checkpoint map **1800**、interactive **2400**、outer native session **5220** 秒。有界逐日驱动 1800 秒、最迟第 36 日。若入口字节、候选 DLL 或源档改变，停止使用 a05 并生成独立 a06 静态回执和新路径。
- 集成执行脚本也已只读哈希：阶段调用器 `4E7BFE6D9D9D8927122C5A83A1B2E595B0F2C9C8F016E5FCBC1697216012AD9B`；逐日驱动 `74E7E299C94F7DF204EBFD2B331DFD1B2A4074950A6188561E08DC6ED60C0A30`；600 秒录像器 `B4158528A38E1C6B7EF59F8B9D1123F7476817C8E40863BE357B1A576F48933F`；整数投影器 `82D55247A1E7D796BAD148072722DB70D58601034BF974C89B8ABD1B21DA8B75`；PTS 审计器 `85C842D05765BC81AF2937BC0CF4433EE41CFBAEFE2D5BD8EDB953BB8308814B`。脚本变动时先审阅差异，不能直接沿用此执行清单。

## 唯一待创建的采集路径

`a05` 的 no-launch root 为 `D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-pair-20260928-a05-preflight/`，live root 为同名前缀 `...-a05-live/`，当前两者均**不存在**。live root 内的 recorder 子目录也保留未创建：`...-a05-live/recording-e2-09-terminal-a01/`；预计 raw 为其 `raw/e2-09-terminal-a01.mkv`，原生桌面 30 fps、最多 **600 秒**。这些是唯一建议路径，不能拿旧 024 或旧 a04 目录重跑；若任何路径先被其他 attempt 占用，另立 a06 或下一个 append-only 编号。

## 窗口执行清单

1. 收到 `/root` 对旧 a02 **PIDs 清零、lease 释放**的明确通知后才领取 `ck3-screen:acquired`。拍、直接审阅并保全当前 Steam 离线画面；遵守 stale frame 恢复、窗口几何、英文键盘和截图坐标合同。再核 a05 static receipt 及入口 SHA，并复查最新正式 xar-promo Release。
2. 从集成树用 [阶段调用器](invoke_terminal_pair_stage.py)对 a05 执行 `--stage no-launch --execute`，确认新 `...a05-preflight/ck3-output/preflight.json` 为 `READY_FOR_BOUNDED_LIVE_ATTEMPT` 且 `ck3_started=false`；确认 save/DLL/injector/EXE 与 900/1800/2400/5220 预算。任何 RED 保全，不复用该目录。
3. 同一 a05 静态回执加**本次**新鲜离线回执，以独立受管命令会话运行 `--stage live --offline-receipt <本次回执> --execute`。该调用会等待会话结束，须另开控制会话做录制与逐日驱动。等 `native-start-readback.json` 验证载入，并在完整可见的墨西拿战斗和 WarID `4` 战分面板上核第 27 日 `53146872`、actor `29829`、CombatID `16777218`、ProvinceID `2633`。先拍前态，记录面板和 native snapshot/WarID 的同帧身份。
4. 调 [原始录像器](record_bounded_gameplay.py)的 `record --seconds 600 --track e2-09-terminal-a01`，workdir 用上面的未创建 recorder 子目录，`--session-output` 指向 `...a05-live/ck3-output`，传本次源 save、保存回执及新鲜离线回执。录像器会独立运行 600 秒；确认它已写 `recorder-start.json` 后，用 `mark --capture-screenshot --kind war4-before --date-raw 53146872 --combat-id 16777218 --war-id 4` 加前态锚点。不可并行启动其他会推进日期的脚本。
5. 立即用 [逐日驱动](drive_terminal_pair_live.py) `--static-receipt <a05-static> --run-root <a05-live> --execute`，每日只推进一个原生日，保全 snapshot/control/terminal、一次 life-advance 的请求响应 SHA 和 UTC/monotonic mark。第 32 日起等 `normal_result`；最迟第 36 日或 1800 秒停止。writer 必须是**本次新 run**的 WarID `4`、分子、八桶分母、CB 倍率、row、攻方符号。终局立即让原速 raw 拍到 winner、败军离开原 CombatID 和 WarID `4` 面板后态，并追加 `war4-after` mark。
6. 如果终局或后态晚于该 600 秒 raw 的最后 PTS，**本次视频配对仍 RED**；不能把运行时 writer 与无画面/旧 024 的 `-50` 拼作同轨。保留 raw、partial、stderr、逐帧 ffprobe、marks、受管回执和失败原因，下一次重新开独立 run/workdir。若录制完整，用 [PTS 审计器](audit_raw_video_pts.py)和[整数投影器](project_terminal_pair_numbers.py)分别核原速连续性及新 writer 数字，人工逐帧审 UI/日期/对象、clean spans，再做 1× 完整观看；自动 GREEN 或上屏卡片不等于人工签核。

**当前阻断**：旧 a02 屏幕清场通知、新鲜 Steam 离线画面、no-launch 与 live 实测、WarID `4` 前后 UI、raw PTS、normal writer 分母及人工审阅都未发生。a05 是准入方案，旧 024 动态数字不能复用为这条新 run 的证据。
