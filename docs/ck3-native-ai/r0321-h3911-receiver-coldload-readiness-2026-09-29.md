# R0321 H3911 接收端冷载与只读门（2026-09-29）

## 范围与身份

本机接收的 H3911 六件由 `D:\ck3-research-artifacts\war-intake-20260928\r0321-h3911-matched-pair-001\receipt.json` 逐件哈希确认。接收原图存档 SHA-256 为 `5EFB3B3CF3EE7368C6C12D4C984B4A0366AA8A971409165016E3DC24725A4746`，源 driver 为 `DE09EA8B3648FAE89F90E5459991BC66AE52154971948DB39C353D05EEAAEE33`，DLL 为 `C71F6A5DFE8D23374B5B73F9DFA18AD9455CFF087D36EC93D2D29F7F610E8786`。来源候选代码是 `2eb9cb9523d9c02055882d9418395d0cce35cc31`，DLL 对应原生代码为 `a6d1ae845f11e1e0bae79cac3fd9c30b00afae59`。本接收 worktree 的 Python 入口和模块路径由 `run_r0321_h3911_receiver_readonly.py --check-static` 与每次 `launch-plan.json` 显式记录；不会依赖主 venv 的 editable 安装指向。

两次尝试都从上述同一存档建立**新**外置 attempt，运行正式 `prepare-profile`、`rebind-ordinary-seed-v1` 和 `native-one-generation-preflight`，仅在 Steam 离线新鲜画面与独占屏幕任务总线之后才启动 CK3。两次受管退出后，源六件、准备存档、派生 driver、DLL、injector 和游戏 EXE 的回读哈希保持一致，CK3 进程库存为空。没有提交移动、攻击、日期推进或其他游戏动作。

## 两次 RED 的准确边界

| 尝试 | 外置证据 | CK3 及 MCP 时序 | 能证明的结论 |
| --- | --- | --- | --- |
| attempt-1 | `D:\ck3-research-artifacts\r0321-h3911-receiver-20260928\attempt-1-h3911-readonly-no-launch\live-h3911-readonly-v1\` | `debug.log` 在 15:46:40Z 进入 `CGameState::InitPostRead`，15:46:45Z 完成附庸缓存阶段；15:46:51Z 第 30 次快照第一次返回 `map_ready=true`，但 `episode_identity_pending=true`、`played_character=null`、`active_wars=[]`。 | 首版接收 runner 过早把地图就绪当完整身份，失败属 receiver 门错误。没有执行四项只读查询；来源存档、战争集合和预测均未被验证。 |
| attempt-2 | `D:\ck3-research-artifacts\r0321-h3911-receiver-20260928\attempt-2-h3911-readonly-no-launch\live-h3911-readonly-v1\` | `readiness-050.json` 于 16:05:06Z 仍返回 `native game state is not available yet`；CK3 在 16:05:07Z 进入 `InitPostRead`，16:05:12Z 整理附庸缓存，GUI 初始化日志延续到 16:05:46Z。紧接的第 51 次 `ck3_take_snapshot` 未在既定 120 秒单调用界限内返回，于 16:07:25Z 超时。 | 快照请求撞上首次原生状态发布窗口。具体内部阻塞点尚未证明；不能把它当来源存档无效。没有拿到完整同帧身份，也没有执行四项只读查询。 |

第二次 `failure.json` 为 183 B，`readiness-050.json` 为 349 B，`session-stdout.jsonl` 为 4,423 B，`session-exit.json` 为 1,463 B，`mcp-stderr.txt` 为 0 B。`session-stdout.jsonl` 记录 15:52:25Z 启动、16:07:29Z 停止、受管 cleanup `ok=true`；`session-exit.json` 证明 `returncode=0` 且 `ck3_pids_after=[]`。游戏日志在 attempt 的 `state\profile\logs\` 下。全部旧文件保留原样，任何 GREEN 不能倒填旧尝试。

## 下次修正与检验

新接收 runner 在 MCP 初始化后先**只读**新 attempt 自己的 `state\profile\logs\debug.log`。仅当日志出现按顺序排列的 `CGameState::InitPostRead` 和 `Setup powerful vassals among`，且文件修改时间不早于本次启动，才等待额外 60 秒缓冲，然后发出第一条 `ck3_take_snapshot`。每次观察追加到 `coldload-gate-probes.jsonl`，通过后另存 `coldload-gate.json`。此日志阶段只控制**何时查询**，不代表地图、角色、战争或帧已被证明。

该等待仍占用原有 1800 秒帧就绪期限；每个 MCP 调用仍为 120 秒，总 session 仍为 3000 秒。进入快照阶段后，必须连续两次读到完整稳定的暂停 H3911 帧、CharacterID `29829`、WarID `16777231`、源日期和 episode 身份，才允许原定四个只读查询。任何身份、哈希、能力或查询结果不匹配仍记 RED；正式战斗预测和攻击始终禁用。

无游戏聚焦测试 `test_h3911_readiness_gate.py` 覆盖缺日志超时、后读阶段与完整缓冲、缓冲不得越过既定截止、跨 attempt 日志拒绝、旧同路径字节拒绝。已通过 5/5；`py_compile`、`git diff --check`、`--check-static` 均通过。**这些静态检查不构成 H3911 接收实机复现**。第三次尝试需等待屏幕重新释放，重新取得 Steam 离线新鲜原图、独占租约、新外置 attempt 与正式 no-launch 准备。
