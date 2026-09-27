# R0244 本机 War4 同帧 v3 只读复测（2026-09-27）

这是对 [R0244 请求](../autonomous-agent-progress/coordination/war-requests/requests/WAR-INPUT-R0244-20260927.json) 的**独立本机场景通路检查**。原请求是 War48、Army16777237 对 Army16777417、省份2640；本检查点是 War4、Army18 对 Army24、省份2638，绝不能将两者的结果互代。原 War48 存档、driver sidecar 和匹配 DLL 未在这台机器上找到；本尝试也不执行一跳移动、战斗或胜率验收。

## 冻结输入与无游戏预检

源清单 [`war-r0244-local-v3-source-manifest.json`](war-r0244-local-v3-source-manifest.json) SHA-256 `76D41D89165A305A2A4A9FFB3707E846BB35D439F22F58FC18386954FE34F13F`，锁定 CK3 EXE `2D00FF31…F83DB86`、058 原版静止检查点 `91CEE43C…BEDD592`、save 回执 `CBDC1F1B…71B`、同帧快照 `3F247A89…90A9`、063 曾使用的桥 DLL `7CCF1E7C…89CC3`、注入器 `C3110B4F…977B4`。回执记录 `pure-vanilla-enabled-mods-empty`、`xar_off`、raw date `53144520`；快照记录暂停状态、玩家角色29829、War4、可控静止 Army18 在2619、非撤退 Army24 在2638，以及完整敌军 ID 集合。预检同时逐文件重算上述 SHA，而不是只相信源清单。

`tools/war_r0244_local_v3_probe.py preflight` 先分别为 attempt-02 和 attempt-03 完成**无游戏**预检；两个独立 `input-freeze.json` 均以 `live_status=NOT_STARTED` 开始，保存六个源文件 SHA、采集脚本 SHA `0BB22F6E…5F45A6`、各次采样脚本 SHA、精确 capture/probe argv 和启动门禁。旧 attempt 063 已有同类查询历史，但没有提交一跳移动；它不是这两次新采集。

## 受管步骤与失败保全

1. 由协调者取得独占 CK3/屏幕资源，确认新的 Steam 离线实时画面，并把经审阅的 `steam-offline-receipt.json` 放入**本次**外置 attempt；不得复用旧截图或旧回执。
2. 核对 `input-freeze.json` 的 `capture_argv` 后，在该计划的 `capture_cwd` 中执行受管 `capture_session.py --capture`。两次均报告 exact build match、同一 EXE SHA 和 v3 桥能力；失败时按受管流程清理进程并保留 RED 工件。
3. 新 session 的 `interactive-requests` 和 `interactive-requests-responses` 出现后，执行计划里的 `probe_argv`。采样脚本只发 `ck3_take_snapshot`、`ck3_get_capabilities`、`ck3_execute_step` 的原生路线预览、全敌军路线接触查询、精确 v3 查询，再读一次快照；最后发 `finish`。不发送 `move-army`、`resume-map`、`plan_turn` 或其他游玩动作。每个响应均核对连接代次、native/public revision 与 snapshot ID；路线预览/接触回包还携带 episode ID，v3 回包按其实际合同没有 `queried_episode_run_id`，因此由同连接身份和前后快照 episode 不变共同约束。日期须仍为 `53144520` 且暂停，兵团、省份、路线及 v3 的 scenario/completeness 必须匹配。

attempt-02 的 v3 实际返回 `available`、schema 3、`input_observation_ready=true`，同一 snapshot `native:3`、public/native revisions `4/3`、连接代次 `1`；但第一版验收器错误要求 v3 回包中不存在的 `queried_episode_run_id`。该次 `v3-read-only-red.json` 与全部原始回包永久保留为 RED，不能反写 GREEN；采集进程仍安全退出。修正只放宽这个可缺字段，并新增同字段缺省测试；原有已出现字段的错值、连接代次、双 revision 和其他失败门禁不放宽。修复已在 master `2730ab163`。

## 独立 attempt-03 结果

新的外置目录为 `D:/ck3-research-artifacts/war-r0244-local-v3-attempt-20260927-03/`。Steam 窗口位移前后像素差异证明 14:04 UTC 的新桌面截图不是旧帧；人工直接审阅同一 `steam-moved.png` 底部“离线模式”，截图 SHA-256 `DF7AC0B1992C0383EB5D4A36F21A6EA48CF34DFD8DEA45AE6D9B1283B23764A5`。启动前 CK3/录制进程均为零，Steam 未切换在线。`input-freeze.json` SHA `284996A1E366FD4EBD4564C13A118195503E31F4E6E615363EE68157F8735F14`；源清单仍是上述精确 SHA。

六项原始只读响应和 `finish` 的 request 集合已逐个核对，没有游玩动作。原始 v3 响应 `020-v3.json` SHA `BE333C06325F40E4585FF4240884F0B4B15A8C4E19F0ABC22D4807258E94C72B`：`query-combat-simulation-inputs-v3-2638-2643-a-1-18-d-1-24` 为 `available`，schema 3，`input_observation_ready=true`。原生全路线依次为 `2624→2631→2630→2629→8753→2626→2627→2633→2639→2643→2638`；v3 使用实际路线进入点 2643，查询的双方是 Army18 和 Army24。查询前后均为 raw date `53144520`、`native:3`、public/native revisions `4/3`、episode `native-29829-23be5ac45c12`，连接代次 `1`。`v3-read-only-result.json` SHA `66F7B254CCD2541562D74D5463BDF79CB0B233366EABB8A8E23D65237109B201`。

离线复核回执 [`war-r0244-local-v3-attempt-03-audit.json`](war-r0244-local-v3-attempt-03-audit.json) 与外置原件 `offline-audit.json` 字节相同，SHA `C439215CE8072105A1DE6406C8963CA3DA992B64EC54585859119DEC8911F9C4`，逐字节核验六项响应 SHA、精确请求集合、v3 载荷、前后帧与连接代次，以及受管清理。`session-result.json` SHA `60BA820FE957F8736190FB9F380C35D105015D1BBA2C4ED656C9475A554D6D06`，记录 `exit_reason=stop`、`cleanup_proven=true`、`tree_gone=true`、job 最终 0 个进程、final CK3 inventory 空；capture/probe 进程退出码均为 0，事后独立进程检查也没有 CK3 或录制进程。`capture-report.json` 的 `ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO` 只表示无视频的环境 session，并不是本片视频拍摄或战斗结果。

因此可以确认**本机 War4 同帧 v3 查询通路成功**。它不证明原 War48 配对、模型胜率、移动提交或下回合决策。原请求的正式验收还须原 War48 存档/driver/DLL 的精确配对，以及实际动作、读回、下一回合与恢复回执。

离线单测：`tools/test_war_r0244_local_v3_probe.py` 在普通及 `-O` 下均为 `2 passed`；覆盖错误源 SHA、重复 attempt、暂停场景/待处理交互、返回的同帧字段与 v3 scenario 拒绝，并验证 v3 缺省 episode 字段的真实合同。两次 `preflight` 均重算六个源 SHA。此研究未从 OneDrive 下载任何文件。
