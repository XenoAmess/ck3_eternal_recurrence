# G1 一代人全寿命 production 续跑交接（2026-08-28）

更新时间：**2026-08-28 19:53（Asia/Shanghai）**

这是一份可执行交接，不是 G1 完成声明。当前角色 `29829` 仍然存活；最新 bounded cold run 只用于验证刚修复的
GEN-030/031 边界并生成更晚的 durable checkpoint。接手者的首要工作是从该 checkpoint 继续同一 episode 的正式
`native-one-generation` 长跑，直到自然死亡，并在死亡后继续等待琉焰卿 Mod 提交算分结果。

## 当前结论

- G1：**未完成**。CharacterID `29829`、episode `native-29829-ee172aa720db` 仍保持不变，角色仍存活。
- GEN-030：**resolved / production-live**。event 51 与七日 deadline 同日出现时，generation 2 已是正常
  `triggered`；composite 没有再错误 cancel，而是保留 date/ticks/trigger/pause/zero-overshoot 证明并优先处理事件。
- GEN-031：**resolved / production-live**。此前发生 mismatch 的 WarID `134217852` 已在同一 paused frame 中与
  WarID `83886203` 连续查询成功；native reply 绑定同一稳定 snapshot，未再混入 deferred frame。
- 战争性能：stationary 与 committed-route speed 3 已是 production 默认；正式持续样本为
  `165 游戏日 / 156.566 秒 = 63.232 游戏日/分钟`，通过 `>=60` 硬线。`120` 仍是冲刺值而非当前承诺。
- 策略中立：高速 sentinel 只能替换 baseline planner 已经选定的同 WarID、同军队、同 objective
  `life-advance`，不改变宣战、参战、续战、议和、投降或终战意愿。最多 7 游戏日的终战/接受度复查延迟是所有者已接受的
  性能妥协；有同日 native watch 时仍优先无损停表。
- 环境已释放：本交接形成时 CK3 已退出；最新 run 的 session report、shutdown、process tree cleanup 与 driver close 全绿。

## 唯一应使用的代码线

- mainline worktree（tracked tree/index clean）：
  `C:\Users\xenoa\AppData\Local\Temp\xar-agent-mainline-worktree-20260827-1254`
- 分支：`agent-mainline-20260827`
- 已验证并推送的 runtime/source baseline（交接文档提交会在其后）：
  `fc0f87844ade595ded99168b7d5d1dee2619184f`
- 最近三个提交：
  - `a2c81a0` — policy-neutral 高速 sentinel 候选与 1–5 速 typed surface
  - `95a466b` — stationary speed 3 production 晋级
  - `fc0f878` — war-termination query same-frame snapshot binding

**不要在 `Z:\ck3_mod_rewrite` 的脏工作树上执行、清理或覆盖用户改动。** 所有续跑、修改、测试、提交与 push 都应从上述临时
mainline worktree 继续。不要再 cherry-pick 性能代理的旧原始提交；它们的合法重构已经以 `a2c81a0 / 95a466b` 合入。

## 当前可恢复状态

- state dir：
  `C:\Users\xenoa\AppData\Local\Temp\xar-marriage-reject-c21c096-state`
- bridge pipe：`\\.\pipe\xar_ck3_restore_exact2_7aff1d0`
- episode：`native-29829-ee172aa720db`
- CharacterID：`29829`
- 最新 checkpoint：
  `C:\Users\xenoa\AppData\Local\Temp\xar-marriage-reject-c21c096-state\profile\save games\xar_checkpoint.ck3`
  - `date_raw=53279256`
  - `history_index=6159`
  - size `92,642,200` bytes
  - SHA-256 `0DF9CB6615FC19B89D4067F74C72E23221B84A337795546957725DB455C4869C`
- 当前 driver state：
  `C:\Users\xenoa\AppData\Local\Temp\xar-marriage-reject-c21c096-state\native-session\driver-state.json`
  - size `24,445,123` bytes
  - SHA-256 `E066C1D45673D54DB2E3A58D9C0EE2B1EE8ADB4909936C4534B3A94A04DDFD00`
- 不要回退到旧的 `53278416 / 164A3960...02DE4` anchor；最新 `0DF9CB66...69C` 已经跨过 GEN-030/031。

## exact-build runtime 与 profile

fresh Release build：

- build dir：`C:\Users\xenoa\AppData\Local\Temp\xar-gen031-war-query-build-20260828T2025`
- DLL：`xar_ck3_bridge.dll`
  - SHA-256 `3EFA9131166EDEC20B4754C887A44C079065AF832C452AB87C952E1C5CA5FE16`
- injector：`xar_ck3_bridge_injector.exe`
  - SHA-256 `D23DF840148BF04095F3D82BC0C59D81BD67E23A9B2D6ADF55133EEB0E74024D`
- source fingerprint：`E539113F363A1DB8956D9707B5FA481F776CED7497CC5598F05FFE3ECCFB2794`
- fresh native Release CTest：`40/40` 通过。

profile 已由 `fc0f878` prepare 并 verify：

- semantic environment SHA-256：`f89cd5ebf6494fda11587986d4bf558e4d7d071167309ac4e55a51c888ca1a9b`
- environment JSON 文件：size `34,249` bytes，SHA-256
  `DA2A7AE5A2B11902469D01800AE6230C314533537AE6098EBB3185B1838DACC1`
- production tree SHA-256：`f4e63fffa6cf9332ba41eb5985d1cb72f280f4bf375a15473f4638f43cf944be`
- rules SHA-256：`6cca52869f5bc32de1b509dd63255f8847875134933e936f97125ebc6be092f7`

若源代码没有变化，接手时不需要再次 prepare；可直接 `verify-profile`。若确实修改了 runtime，才重新 prepare/verify 并记录新哈希：

```powershell
$env:GIT_CONFIG_COUNT='1'
$env:GIT_CONFIG_KEY_0='safe.directory'
$env:GIT_CONFIG_VALUE_0='C:/Users/xenoa/AppData/Local/Temp/xar-agent-mainline-worktree-20260827-1254'
& 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe' 'ck3_autonomous_player\agent.py' `
  --state-dir 'C:\Users\xenoa\AppData\Local\Temp\xar-marriage-reject-c21c096-state' `
  --game-dir 'Z:\ck3_mod_rewrite\Crusader Kings III' --bridge-mode disabled prepare-profile
& 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe' 'ck3_autonomous_player\agent.py' `
  --state-dir 'C:\Users\xenoa\AppData\Local\Temp\xar-marriage-reject-c21c096-state' `
  --game-dir 'Z:\ck3_mod_rewrite\Crusader Kings III' --bridge-mode disabled verify-profile
```

## 最新 live artifact

run dir：
`C:\Users\xenoa\AppData\Local\Temp\xar-marriage-reject-c21c096-state\runs\20260828T114802Z-one-generation-9186bfa3`

- `report.json`：size `178,956` bytes，SHA-256
  `2C764FCEC7AEFBAC016D7FD83B716EC01462C4A1BFAB0FC076CC1AEFA5A46C83`
- `first-blocker.json`：size `4,961` bytes，SHA-256
  `286CCF7CA5F0A6E18805B431B2CE153E0EA9A03D5ACBAF3DD6B57DEE6E3E35E8`
- 结果：`20/20` successful turns；13 query、7 gameplay、2 checkpoints、6 visible gameplay；cold-start 总墙钟
  `102.462s`。
- 停止原因：`turn_limit / bounded_incomplete`。这是刻意设置的交接边界，不是真实 blocker；
  `recoverable_from_checkpoint=true`。
- 清理：`session_report_ok=true`、`shutdown_ok=true`、`tree_gone=true`、
  `cleanup_proven=true`、`driver_closed=true`。
- 该短 run 约推进 35 游戏日，包含冷启动、事件与移动动作，**不是持续吞吐验收样本**；不要用它覆盖上面的
  `63.232 游戏日/分钟` 正式稳态测量。

关键 turn 证据：

1. turn 8 的 stationary speed-3 arm 从 `53278584` 精确推进 7 日到 `53278752`，结果为
   `date_deadline / ticks=7 / intermediate_pause=0 / overshoot=0`；同日出现 event 51。
2. sentinel generation 2 为正常 `triggered`，composite 返回 `stop_kind=player_decision`，没有错误 cancel；turn 9 查询事件、
   turn 10 选择 option 1，日期不变且旧 event 后置消失。此处是 GEN-030 的 exact live GREEN。
3. turn 11 查询 WarID `83886203`，turn 12 查询此前失败的 WarID `134217852`；两者均成功绑定同一 paused
   `native revision=26`。其后直到 turn 20 查询持续成功，没有四字段 mismatch。此处是 GEN-031 的 live GREEN。
4. WarID `33554565` 在 turn 8 期间自然结束并消失；没有改变投降、议和或终战阈值。
5. turn 15/18 的 committed-route speed-3 arm 分别连续推进 10/11 日。

## 已完成验证

- 相关 driver/runner 回归：`240 passed`，另有 `224 subtests`。
- 完整 Python suite：`1521 passed, 3 skipped, 1058 subtests`，墙钟 `159.73s`。
- fresh native Release：`40/40` CTest。
- `fc0f878` 已推送到远端 `origin/master`，当时 ahead/behind 为 `0/0`；形成本文档前 tracked tree/index clean。
  只读全量 untracked 扫描对 `ck3_autonomous_player/.pytest_cache/` 报 `Permission denied`，因此不宣称该缓存目录经过穷尽审计；
  它不影响 tracked source、构建、checkpoint 或续跑。

## 接手后的第一条正式命令

先确认没有 CK3 进程、当前 `origin/master` 包含 runtime baseline `fc0f878` 与本交接文档，并可选重算 checkpoint 与
driver-state 哈希。然后在 mainline worktree运行：

```powershell
$env:GIT_CONFIG_COUNT='1'
$env:GIT_CONFIG_KEY_0='safe.directory'
$env:GIT_CONFIG_VALUE_0='C:/Users/xenoa/AppData/Local/Temp/xar-agent-mainline-worktree-20260827-1254'
& 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe' 'ck3_autonomous_player\agent.py' `
  --state-dir 'C:\Users\xenoa\AppData\Local\Temp\xar-marriage-reject-c21c096-state' `
  --game-dir 'Z:\ck3_mod_rewrite\Crusader Kings III' `
  --bridge-mode native-headless `
  --bridge-pipe '\\.\pipe\xar_ck3_restore_exact2_7aff1d0' `
  --bridge-dll 'C:\Users\xenoa\AppData\Local\Temp\xar-gen031-war-query-build-20260828T2025\xar_ck3_bridge.dll' `
  --bridge-injector 'C:\Users\xenoa\AppData\Local\Temp\xar-gen031-war-query-build-20260828T2025\xar_ck3_bridge_injector.exe' `
  native-one-generation --max-turns 50000 --timeout 604800 `
  --readiness-timeout 300 --checkpoint-every-advances 3 --route-contact-speed 3
```

stationary speed 3 已是 production 默认，不需要旧 canary flag。不要重复 20-turn canary；直接执行正式长跑。

## 后续处理顺序

1. 若只命中 turn/wall bound，角色仍活且 checkpoint/cleanup 全绿：从该 run 的最新 durable checkpoint 直接续跑，
   不登记真实 blocker，也不回退 episode。
2. 若发生真实 B0/B1：保留 `report.json` 与 `first-blocker.json`；冻结同 exact build 的原生 AI/ABI 证据，只做消除该故障的
   最小合法修复，然后从最新 checkpoint 继续同一 episode。
3. speed 4/5、碾压局零暂停和更高吞吐继续是有价值的并行预研，但不得抢占会直接阻断 G1 的真实 B0/B1，也不得改变战争策略。
4. CharacterID `29829` 自然死亡后，**不能在死亡帧立刻宣告完成**。必须继续等待琉焰卿 Mod 产生 committed settlement，
   再读取并记录人生分数。
5. 只有匹配本 episode 的 `terminal-settlement.json` 同时满足以下条件，才可标记 G1 GREEN：
   - `ready=true`、`commit_serial=1`；
   - source CharacterID 为 `29829`；
   - `one_life_settlement.final_score == 顶层 score == recorded_episode.score`，并把该数值明确写入日报、周报和最终交付；
   - settlement、cross-run record、no-heir gameplay、zero-heir continuation 与 cleanup 全部通过；
   - 不在结算后启动继承人 gameplay。
6. G1 完成后才处理 `GEN-009` episode seed 债务并进入 G2。

## 明确不要做的事

- 不要操作或清理脏的 `Z:\ck3_mod_rewrite` 工作树。
- 不要回退到 `164A3960...02DE4` 或更旧 checkpoint。
- 不要把 bounded `first-blocker.json` 当成 capability RED。
- 不要为性能降低宣战、参战、续战意愿，或提高投降/议和意愿。
- 不要在琉焰卿 committed score 出现前标记死亡结算或 G1 完成。
- 不要让 speed-4/5 预研拖住当前正式一生长跑。
