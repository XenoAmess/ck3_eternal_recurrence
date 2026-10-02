# E2-09 新配对终局轨：a05 实机证据索引（2026-09-28）

状态：**原生同源配对已取得；原速录像已编码、尚未完成人工 1× 审阅与 clean spans 认证**。本轨从 F085 day27 存档重新冷启，使用新的 DLL / injector 与新 run；旧 024 原件的 RED 状态和数值不因本次采集自动改变。

## 受管边界

- 外置 attempt 根目录：`D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-pair-20260928-a05-live/`。
- 来源存档 SHA-256：`F085D8ABB89A354FA1004DBE8800505BC952AA8A68C0EA21AAB788F9875FEEB3`；来源回执 SHA-256：`5198123BD71842624A3FB933492F78C3BB11C65D2DED634E3965FDC79B90A012`。当次原生加载回读在 `ck3-output/native-start-readback.json`，`postcondition_verified=true`，角色 29829、起始 `date_raw=53146872`。
- Steam 离线的新鲜画面与人工审阅在外置 `episode02-terminal-offline-20260928-a02/steam-frame-freshness.json`、`steam-reviewed-offline.json`；审阅图 SHA-256 `DE289DE2ADF528A6B2C97CC605CEC1B094A7D61D31FF2D714CBED1B7FB3C1310`。
- a05 静态准入回执 SHA-256 `9A98CE3CA00A3EAC6049DE0722D43C95390635660809C5EAB9EEF7F5B4139ECD`。实际使用的分段 helper SHA-256 `776DC1B4AB5B62DECDA43738271BE70EC3AADBE101B2CF910A5B148D8E76BF26`；单日 `observe → 原生响应绑定的可见 mark → advance`，推进前后均校验同一活动录像和余量门。
- `ck3-output/capture-report.json` 的 `environment_session_complete=true`、`cleanup_process_inventory.processes=[]`；受管游戏会话于 10:52:11Z 自然退出。task-bus 独占 `ck3-screen` 已在 seq1777（11:02:37Z）显式释放。10:55Z 写入的 `999-e2-finish.json` 晚于自然服务结束，未作为退出原因；原样保留。

## 原生身份、时间和数值

| 节点 | 可复核原件 | 结果 |
| --- | --- | --- |
| 战分前态 | `recording-e2-09-terminal-a01/marks.jsonl` 的 `e2t-s01-war4-before` 及其截图 SHA `C69C87ED84D6E8060DDC08ACEAE4881CBF65A36E7FC54AEAC6F3996779D65FD6` | WarID 4 战分 0%；原生面板显示我方进攻 943、敌方防守 6046，1066-12-30；同日 CombatID 16777218。 |
| 逐日门 | `terminal-pair-steps/e2t-s01-d27-*`、`e2t-s02-d28-*` 至 `e2t-s02-d31-*` | 由 `date_raw=53146872` 一日一日推进到 `53146992`。每次 advance 前有同帧 control/revision 和活动录像截图 mark；day28–31 的 phase 为 pursuit。 |
| 新 run 终局 writer | `terminal-pair-steps/e2t-s02-d32-observe.json` 与 `ck3-output/interactive-requests-responses/e2t-s02-d32-terminal.json`，后者 SHA `3CAC1F8F89545C299A957EB49C1B8636BB9A14C2707680A458FA8104EF9B1782` | 同帧 `CombatID=16777218`、`WarID=4`、`date_raw=53146992`、`terminal_kind=normal_result`、revision 19。War battle row 0 `value_raw_q100000=5000000`，胜方不是战争进攻方，因此进攻方 delta `-5000000`，即 -50 战分；denominator 输入 `sum_int32=996`、最低值后 996；hard loss 原始量 `53662042`（该字段量纲见原生响应，不直接作屏幕整数）。 |
| 战分后态 | `recording-e2-09-terminal-a02/marks.jsonl` 的 `e2t-s02-d32-war4-after` 及截图 SHA `59D61E6378B8EF8EC0E14ACAC69A2EE4F6F523B8AE1378AD5A5CD8FD1B508149` | 同录制段原生面板清晰显示总战分 -50%、战斗项 -50%，我方 897、敌方 5642，日期 1067-01-04。战分面板上缘被同帧无关事件弹窗遮住，关键战分和双方人数仍可读。没有为移除弹窗选择会改变游戏状态的事件选项。 |
| 同录制段绑定 | `terminal-pair-steps/e2t-s02-d32-verify-terminal.json` | `same-recorder-terminal-mark-bound-unreviewed`；writer response SHA 与后态 mark 一致，recorder PID 25032，同一 a02 原速片。此状态只证明机器绑定，**不等于人工完整观看**。 |

两个原速文件为 `recording-e2-09-terminal-a01/raw/e2-09-terminal-a01.mkv`（SHA-256 `C2E3AB8B0E60171316DD445B999B95E91227211666FE78CCF797F733AFDA315B`）及 `recording-e2-09-terminal-a02/raw/e2-09-terminal-a02.mkv`（SHA-256 `25A13691259215848D77EAAB8AED9C0E281AF59A8AEB126E5D726EC6FE73A9BC`）。各自 `recorder-final.json` 给出 600.000 秒、1920×1080 H.264、完整首末 PTS，分类均为 `ENCODED_UNREVIEWED`。mark 的 `approx_seconds_from_recorder_start` 不是视频 PTS；正式剪辑点须以原速片逐帧回读确定。

## 离线 PTS 与素材保全

- 可重跑脚本：`audit_terminal_pair_raw_pts.py`，SHA-256 `BB53A2B63C30762A1A1EB20F8FDB0B4FC7823C7D816DC08C0D2D696AA9D14EAD`。执行命令：`<verified-python> audit_terminal_pair_raw_pts.py --attempt-root D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-pair-20260928-a05-live --output <new-append-only-json>`。最新外置报告 `episode02-terminal-pair-a05-pts-audit-20260928-a03.json` SHA-256 `6FDE20151A6E51EC760BB6CFFAA0B30DC21413363A74149100D949681FC16391`；a01/a02 历史报告原样保留。
- 对现存 `ffprobe.json` 的**每一帧** PTS 做只读检查：a01 16,934 帧，a02 16,560 帧；各段均首 PTS 0.000、末 PTS 599.967，严格递增，尺寸始终 1920×1080。a01 最大相邻间隙 0.067 秒；a02 最大间隙 **7.566 秒**（PTS 271.267–278.833），另有 0.767 秒、0.467 秒间隙。因此不能笼统称 a02 全段为 clean span；最大缺帧区位于 day30 可见 mark 约 226 秒与 day31 mark 约 329 秒之间，需在正式剪辑中避开或另行审阅。
- a02 writer mark 的墙钟导航点约 397.339 秒、后态 mark 约 487.692 秒；报告只列最近视频 PTS 397.333、487.700 **供定位**，不把墙钟偏移当作精确同步。分别从对应原速 raw 抽帧保存在外置 `episode02-terminal-pair-a05-frame-a01/`；目视确认终局事件弹窗和后态战分 -50% 与原始 mark 相符。该两帧抽检不构成完整 1× 审阅。
- 独立 `xar-promo` native run 位于外置 `episode02-terminal-pair-a05-native-run-20260928-a01/run-manifest.json`，最终 manifest SHA-256 `D7EBB1063B10E721BAF58CB762EB037B6B8B3652B50CC725EA47D6F68B5C39BA`。它以最新正式 wheel v0.2.1（SHA-256 `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`）保全 21 件原件/派生审计材料，包括两段 raw、ffprobe、marks、原生 writer、前后态截图、source save、静态准入和回执。`validate-authoring-a02.json` SHA-256 `E8A62B65D32DE423C7B74B27A2B3019CF6DFE8A32F656218C93114B1FC3BBEA3` 报告 `GREEN`、21 artifacts、`files_checked=true`；它只证明所声明文件和哈希可读，不证明镜头 clean 或人工签核。

## 剪辑准入

本轨可以作为 E2-09 的新同源数字和镜头候选，卡片来源应明确写 **a05 新配对 run**，不得把 024 旧 DLL 缺失的历史数值当作 a05 证据。先对两段 raw 做自动一致性审计、抽帧与 clean spans 索引，再由真人按 1× 审阅拟用片段。上述工作前，任何完整画面、成片或人工签核均保持 pending。
