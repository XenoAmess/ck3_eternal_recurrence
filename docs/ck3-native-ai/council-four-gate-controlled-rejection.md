# 议会四类门：受控拒绝入口（1.19.0.6）

状态：**private / no-launch source-ready / live positive scene absent / public OFF**。本入口只补
guest、候选人 pending interaction 与替换 incumbent 不可解职三类 typed 拒绝的受控验收。
R696 已取得 `33435` 的 `candidate_already_councillor` typed 拒绝；它是第四类独立证据，
不能用来替代这三类。原版精确来源、RVA 与场景边界仍以
`ck3_autonomous_player/native_bridge/research/council_final_gate_natural_scenes_1_19_0_6.json`
为准；EXE SHA-256 固定为
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。

R695 私有终端 `F053530B...33D30` 与 R700 私有终端 `C0C31AC4...340E5`
均只有 already-councillor 阳性。新增 `council_four_gate_reject_v1.py` 对两份完整冻结
终端的六次 gate 检查均返回 `positive_missing`，不会选择候选 ID。R700 checkpoint
`599B9EEE...27F64`、driver `2C1A792A...E08312C`、DLL `77515453...59ECA8D`
虽是可核验同源组合，但 DLL 的 private assignment gate 为 **OFF**；R696 的 action-ON
DLL 与旧 `dev3b_r639` save `9104CCB8...2CC63` 配对，仍没有后三类阳性。
因此当前没有可合法执行这三种拒绝的实机场景；无需碰运气重跑旧存档。

R863 又对比 R797 晚 3,585 游戏日的普通封建 h961 durable pair 做了一次新的 private
query-only 实机读取。该帧有 10 个候选：already-councillor 独立阳性仍为
`28925/30909/36567`，另有七个 ordinary 候选；guest、candidate-pending 与 replacement
fireability denial 三个独立集合仍全部为空。运行保持 action OFF、gameplay action 0、
native helper delta 0、日期/revision/save bytes 不变并完整回收 PID125360。报告/原生终端为
`AC7ECA23...6F5D8` / `55A6C2D4...C0E24`。这不关闭新门；h961 已退休，不再无修改重查。
Council 权威状态仍为 1/4，public query/action/ad 继续 OFF。

当普通封建 production 运行自然产生新的阳性 paused 帧时，受控负责人应在**同一帧**
封存原生 private gate 终端、游戏 checkpoint、对应 `driver-state.json` 与 exact-build
action-ON DLL。`inspect_council_final_gate_scene.py` 必须从原生 provider 行给出以下独立
列表之一：`isolated_guest_rejection_ids`、
`isolated_candidate_pending_rejection_ids`、
`isolated_replacement_fireability_denial_ids`。任何列表为空、重叠到更早拒绝原因，
或字段为 unknown/null 时都不提交动作。guest 需真的是 provider 行里的 `IsGuest`；
pending 需是玩家对该候选的未决互动（recipient full ID 相同），不是 AI 发给玩家的
互动；fireability 需 native `CanConfirm=false`，脚本中的 25 年解职锁只是场景线索。

新受控 candidate 独立目录使用 `council-four-reject-candidate.json`，schema 为
`xar.ck3.private.council-four-gate-reject-candidate/1.19.0.6-v1`、
`status=sealed-no-launch`。它须明确冻结 `gate`、`save_name`、源/目标 save SHA、
`driver_state_sha256`、`scene_terminal_sha256`、EXE/Python/DLL/injector SHA、
`game_dir`、`python`、唯一 pipe、三项 CMake private flags ON 与
`public_registered_or_advertised=false`。同目录另有
`council-four-reject-plan.json`（只能由真实原生终端选出 full CharacterID）、
`native-scene-terminal.json`、`source-save/<save_name>.ck3`、
`fresh-profile-state/profile/save games/<save_name>.ck3`、
`fresh-profile-state/native-session/driver-state.json`、`candidate-bin/` 与
`source-repo/`。`run_council_four_gate_reject_v1.py --preflight-only --artifact-root
<candidate-dir>` 仅检查同源配对和 private action-ON 配置，不启动 CK3。
`prepare_council_four_gate_reject_plan.py` 先对冻结的原生终端 SHA 和所选 gate 生成
`council-four-reject-plan.json`；CLI 不接受 CharacterID，缺阳性行不生成 plan。
真实正例、制品与轮次未冻结前，此命令只能返回证据不足，不能称验收 GREEN。

取得机器独占所有权并另行分配单调递增 R 轮次后，同一 runner 的 live 路径重新查询
当前 paused 原生行，只从该行选 full CharacterID；若与封存场景的 owner、incumbent、
日期、候选数或阳性 ID 不一致就停止。每轮最多提交一个 typed 拒绝，要求
`rejected_before_submit` 与对应失败键、native helper 未调用、无 pending ACK；
随后再做独立 paused 查询确认 incumbent 不变、日期未推进，回收自己启动的 CK3 实例
并核验源/目标 save 均未改写。这只关闭相应拒绝门的受控证据；正式 public query →
策略选择 → typed 任命 → 独立后帧 incumbent → 下一 turn 消费与 cold restore 仍须另验，
此前 Council query/action 不注册、不广告。
