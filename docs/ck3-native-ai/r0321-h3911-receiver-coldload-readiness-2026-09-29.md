# R0321 H3911 接收端冷载与只读门（2026-09-29）

## 范围与身份

本机接收的 H3911 六件由 `D:\ck3-research-artifacts\war-intake-20260928\r0321-h3911-matched-pair-001\receipt.json` 逐件哈希确认。接收原图存档 SHA-256 为 `5EFB3B3CF3EE7368C6C12D4C984B4A0366AA8A971409165016E3DC24725A4746`，源 driver 为 `DE09EA8B3648FAE89F90E5459991BC66AE52154971948DB39C353D05EEAAEE33`，DLL 为 `C71F6A5DFE8D23374B5B73F9DFA18AD9455CFF087D36EC93D2D29F7F610E8786`。来源候选代码是 `2eb9cb9523d9c02055882d9418395d0cce35cc31`，DLL 对应原生代码为 `a6d1ae845f11e1e0bae79cac3fd9c30b00afae59`。本接收 worktree 的 Python 入口和模块路径由 `run_r0321_h3911_receiver_readonly.py --check-static` 与每次 `launch-plan.json` 显式记录；不会依赖主 venv 的 editable 安装指向。

三次尝试都从上述同一存档建立**新**外置 attempt，运行正式 `prepare-profile`、`rebind-ordinary-seed-v1` 和 `native-one-generation-preflight`，仅在 Steam 离线新鲜画面与独占屏幕任务总线之后才启动 CK3。三次受管退出后，源六件、准备存档、派生 driver、DLL、injector 和游戏 EXE 的回读哈希保持一致，CK3 进程库存为空。没有提交移动、攻击、日期推进或其他游戏动作。

## 三次 RED 的准确边界

| 尝试 | 外置证据 | CK3 及 MCP 时序 | 能证明的结论 |
| --- | --- | --- | --- |
| attempt-1 | `D:\ck3-research-artifacts\r0321-h3911-receiver-20260928\attempt-1-h3911-readonly-no-launch\live-h3911-readonly-v1\` | `debug.log` 在 15:46:40Z 进入 `CGameState::InitPostRead`，15:46:45Z 完成附庸缓存阶段；15:46:51Z 第 30 次快照第一次返回 `map_ready=true`，但 `episode_identity_pending=true`、`played_character=null`、`active_wars=[]`。 | 首版接收 runner 过早把地图就绪当完整身份，失败属 receiver 门错误。没有执行四项只读查询；来源存档、战争集合和预测均未被验证。 |
| attempt-2 | `D:\ck3-research-artifacts\r0321-h3911-receiver-20260928\attempt-2-h3911-readonly-no-launch\live-h3911-readonly-v1\` | `readiness-050.json` 于 16:05:06Z 仍返回 `native game state is not available yet`；CK3 在 16:05:07Z 进入 `InitPostRead`，16:05:12Z 整理附庸缓存，GUI 初始化日志延续到 16:05:46Z。紧接的第 51 次 `ck3_take_snapshot` 未在既定 120 秒单调用界限内返回，于 16:07:25Z 超时。 | 首个可玩帧绑定与完整历史投影发生在该请求期间；具体卡点缺进程 profile。没有拿到完整同帧身份，也没有执行四项只读查询。 |
| attempt-3 | `D:\ck3-research-artifacts\r0321-h3911-receiver-20260928\attempt-3-h3911-readonly-no-launch\live-h3911-readonly-v1\` | 新鲜 Steam 离线挑战及六件哈希通过；17:10:25Z `InitPostRead`、17:10:30Z 附庸初始化，60 秒缓冲完成后约 17:11:37Z 发首个 `ck3_take_snapshot`，17:13:37Z 达 120 秒超时。MCP initialize 成功、stderr 0 B、无 `readiness-001`；游戏日志最后于 17:11:03Z 更新。调用期间没有原始桌面截图，不能证明地图可见。 | 仍没有首帧或四项只读查询。派生 sidecar 在首调用内写出 3,912 行、43,893,020 B；`session-exit.json` 证明受管清场与 `ck3_pids_after=[]`，任务总线 17:14:23Z seq 1943 正式释放屏幕。不能把超时解释为来源存档错误。 |

第二次 `failure.json` 为 183 B，`readiness-050.json` 为 349 B，`session-stdout.jsonl` 为 4,423 B，`session-exit.json` 为 1,463 B，`mcp-stderr.txt` 为 0 B。`session-stdout.jsonl` 记录 15:52:25Z 启动、16:07:29Z 停止、受管 cleanup `ok=true`；`session-exit.json` 证明 `returncode=0` 且 `ck3_pids_after=[]`。游戏日志在 attempt 的 `state\profile\logs\` 下。全部旧文件保留原样，任何 GREEN 不能倒填旧尝试。

三次尝试的机制复核发现，原 public `ck3_take_snapshot` 会在 `take_internal_semantic_snapshot()` 之后无条件附加完整 `native_command_history`。attempt-1 的成功包约 43,819 B、历史为空；attempt-2/3 首可玩帧内的恢复把历史增至 3,912 行，派生 sidecar 43,893,020 B，离线 JSON 的历史一项约 46,943,996 B。当前 MCP SDK 会同时编码 pretty text 与 structured content，等价完整回包约 141.6 MB 单行；stdio reader 在未遇换行前反复拼接缓冲。这个机制足以解释超过 120 秒的风险，但缺当次 MCP 进程 profile，仍不把它写成唯一实测根因。`restore-checkpoint` sidecar 是首个快照**内部**绑定产物，不能作为首快照之前的等待门，否则会自锁。

## 下一次的修正与检验

新接收 runner 在启动 CK3 前记录 `prelaunch-debug-log.json`，并要求该 attempt 的 `debug.log` **不存在**，拒绝复用旧日志。MCP 初始化后只读这个新 attempt 自己的日志；仅当日志出现按顺序排列的 `CGameState::InitPostRead` 和 `Setup powerful vassals among`，且文件修改时间不早于本次启动，才等待额外 60 秒缓冲。缓冲中如 marker 消失、文件身份改变或长度回退，立即 RED。每次观察追加到 `coldload-gate-probes.jsonl`，通过后另存 `coldload-gate.json`。此日志阶段只控制**何时查询**，不代表地图、角色、战争或帧已被证明。

随后保存当次原始桌面图，作为地图是否可见的独立诊断；截图本身不替代 Steam 离线新鲜挑战或游戏身份。`ck3_get_bridge_diagnostics` 连续两次必须证明 DLL pipe 连接到受管 CK3 PID、匹配 EXE SHA、心跳序号前进且语义状态已发布。首次可玩语义帧后，在外置 attempt 内复制完整派生 driver sidecar，复制前后与副本三次哈希相同，并验 3,912 行、末行 `restore-checkpoint`、日期、存档 SHA 与 episode/角色。新 MCP 私有工具只在显式 `--private-semantic-snapshot-readonly`、native-headless stdio 下出现，直接返回 `take_internal_semantic_snapshot()` 的同帧语义字段，拒绝 transcript 字段与超过 8 MiB 的原始 JSON；原 public 工具合同不变。完整历史继续保留在 sidecar 和外置副本中，不通过 MCP 大回包传输。

日志、桥诊断及首/稳快照等待仍占用原有 1800 秒帧就绪期限；这些就绪调用单次至多 120 秒，且不得越过该期限。四项查询和后验快照也各至多 120 秒，受总 session 3000 秒限制，但不复用已经完成的帧就绪截止。MCP 初始化、每次快照和只读查询的提交前、返回后同步核对独占屏幕租约，原有租约 watchdog 也继续运行；后读桌面截图前的租约核对同样是不可降级硬门。收到响应后先保存原始 envelope，再检查租约和期限；即使门随后 RED，也保留已收到的字节。进入快照阶段后，必须连续两次读到完整稳定的暂停 H3911 帧、CharacterID `29829`、WarID `16777231`、源日期和 episode 身份，才允许原定四个只读查询。四项查询均要求精确 snapshot/revision/native revision；强度查询的源合同是三行 list（一支我军、两支敌军），并要求 WarID、角色和同帧缓存完全匹配，再通过现有 `strategy._same_frame_army_strength_balance` 导出正式分区入参。任何身份、哈希、能力或查询结果不匹配仍记 RED；正式战斗预测和攻击始终禁用。

无游戏聚焦测试 `test_h3911_readiness_gate.py` 与 `test_h3911_private_semantic_snapshot_mcp.py` 覆盖原有日志/期限负例，以及新桥 PID、心跳、状态门、3912 行完整历史副本、私有工具显式开关、语义等值、transcript 拒绝和 8 MiB 超限拒绝；`test_native_bridge_driver.py` 的 4096 行样本确认内部/公共快照的其余语义字段相同。`py_compile`、`git diff --check`、`--check-static` 也必须通过。**这些静态检查不构成 H3911 接收实机复现**。第四次尝试需等待屏幕重新释放，重新取得 Steam 离线新鲜原图、独占租约、新外置 attempt 与正式 no-launch 准备。
