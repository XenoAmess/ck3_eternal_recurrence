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

## 2026-09-22 R0051 差异场景与下一个原生触发口

R0051 从 ordinary h1809/date `53284392` 的新 paired save/driver，以 master `8b6202f` 修正后的规范零填充轮次场景工具、query ON/action OFF，在唯一 CK3 进程 PID117464 执行了 201.616 秒真实只读查询。报告 `Z:\ck3_mod_rewrite\.task-tmp\RUN-001\council-h1809-candidate\live-R0051\report.json` SHA-256 `D725CBE1AF1493631FB2B1D7D0137A1E947028953E9897C86D610D36EFDF9FBD`：四类隔离计数依次为 `1/0/0/0`，日期、paused revision 和源/目标存档未变、进程回收。它证明场景工具可用，**没有**关闭任何后三门；h1809 与 R863 h961 一样退役，不可不变重查。Council 保持 `1/4`，公共 query/action/ad OFF。

下一次普通生产续跑仅在自然出现以下同帧原生判别量时采样，而非另开长跑或重复 h1809：标准封建 AI 成年封臣利用有效 hook 或 `can_demand_council_seat` 接受 `force_onto_council`（exact build `00_vassal_interactions.txt:1614,1715`），设置 `block_fire_councillor`（`00_councillor_triggers.txt:366`、effect `:686`）后，检查原生 occupied steward `CanConfirm=false` 并有另一名普通替换候选；guest 必须是 provider 行真实 `is_pool_guest_of`；pending 必须是玩家→该候选、recipient full ID 相同的真实未决互动。上述是 exact-build 源码场景线索，**尚无可用的正例 paired checkpoint**；观察到阳性后才冻结原生终端并运行既有受控拒绝合同，不因线索先开公共广告。

## 2026-09-22 接班离线场景索引与只读入口

现存三份 ordinary feudal 私有 gate 终端均按冻结 SHA 经
`inspect_council_final_gate_scene.py` 重新分类。以下路径是交接机证据定位；迁移到别的机器时须重新定位原件并核 SHA，不能只替换盘符。

| 旧轮次 / 配对场景 | 原生帧与席位 | 原始报告 SHA-256 | isolated already / guest / pending / replacement denial |
| --- | --- | --- | --- |
| R0047 / h1662，`Z:\ck3_mod_rewrite_process_assets\g2-council-r0046-h1662-query-20260922\live-R0047\` | raw `53283744`，owner `31853`，总管 `31507` 在职，6 候选 | `C4F487C81494E409B99685BE546F8A7000E10CC3746AF659C52865BCA02F05BE` | `2/0/0/0`；already IDs `30909/36567` |
| R0051 / h1809，`Z:\ck3_mod_rewrite\.task-tmp\RUN-001\council-h1809-candidate\live-R0051\` | raw `53284392`，owner `31853`，总管 `31507` 在职，3 候选 | `D725CBE1AF1493631FB2B1D7D0137A1E947028953E9897C86D610D36EFDF9FBD` | `1/0/0/0`；already ID `36567` |
| R0102 / h1094，`Z:\ck3_mod_rewrite\.task-tmp\COUNCIL-R0101-VACANT\candidate-h1094-query-only\live-R0102\` | raw `53368176`，owner `36403`，总管空席，4 候选 | `9E5B7FCA9F31DB07CB7664075BB3369F19BDA3510CA79A0C5023195BF4CBB623` | `1/0/0/0`；already ID `36567`；空席不能验 replacement |

三份 `raw-terminal-result.json` 的 SHA-256 依次为 `6D39E87EAE67D68B1024746C39689AB8AA285E93A1C0ABF9931F870C96376F09`、`A91600ED953A7B8D6852F06C0008DC7D6282A7C03946CE4874CF1FA26794E933`、`88BE65AD17928D4C749135BE158975F2BB8BB50130FB3FD3AD8EB6CBF57EFCFD`。这些都是只读结果，不能把已闭合的 already 门重复记数，也不能把 ordinary 候选或空席当作后三门阳性。h1566/raw `53371896` 的现存 driver 历史没有 `council_final_gates` 终端；其战争阻塞也不允许为了 Council 场景盲目推进日期。

最小下一个入口是普通战役自然到达**新的**合法 paused checkpoint 后，先离线确认同源 save/driver、`ordinary_campaign_succession/xar_off`、冻结 EXE/DLL/加载配置与总管席位。replacement 必须有在职总管和另一名真实 provider 候选；guest/pending 即使席位空缺，也只能由同一帧 native gate 行证明。若场景相对上表有实质差异且 CK3 唯一实例队列允许，使用既有 `materialize_council_native_gate_scene_candidate_v1.py` 制作独立只读候选，并由 `run_council_native_gate_scene_v1.py --preflight-only` 完成 no-launch 校验；之后至多一轮 action-OFF、≤480 秒 Stage Q。冻结新 `raw-terminal-result.json` 与对应配对后，只在 `isolated_guest_rejection_ids`、`isolated_candidate_pending_rejection_ids` 或 `isolated_replacement_fireability_denial_ids` 至少一个非空时，按既有四门受控 runner 准备独立 action-ON 拒绝候选。否则退役该帧，不重查同一场景。当前没有可启动 action-ON 的后三门候选；Council 保持 `1/4`，public query/action/ad OFF。

## 2026-09-22 h2083 轻量筛查：尚无 Council 实机候选

旧轮次 R0127 的 h2083/raw `53386440` save SHA-256 为
`DF6B61DDE358726EC9B1C126C93302A6A31B800D890C1D88AB184407CFC26080`；
交接机 `Z:\ck3_mod_rewrite\.task-tmp\RUN-001\war-h1955-continuation-source82c6703-nolaunch-20260922\state-final\native-session\driver-state.json`
SHA-256 为 `291DEAD9EE9FE1542D4F100A88C1D2A5B8933CB25D010EEE02C9919ECBE8D887`。
该 driver 有 2,096 条历史，durable checkpoint 只绑定至 `history_index=2083`；所以尾部 13 条不是可直接冷恢复的 paired state。边界内最近的 campaign-root Council 观测在 index `2077` / raw `53385672`，actor/owner 均为 `36403`，`councillor_steward` 空席。index `2084` 的同日 raw `53386440` 只读观测也显示空席，但位于 durable 边界外，只能作排除线索，不能当作已配对的 checkpoint 结果。R0127 当前 pending `perk_alliance_interaction` 是 `31506→玩家36403`；Council 的 candidate-pending 门要求**玩家→该候选 full CharacterID**，故此入站请求不符合。历史 index `9` 的玩家 `arrange-marriage-36403-29940` 已在 raw `53301576` 独立回读为 `accepted_marriage`，也不能冒充当前未决提议。driver 内没有 Council final-gates 终端。h2083 不提供 replacement 阳性，也没有 guest/pending 阳性证据；本包不制作候选、不占 CK3。

正常战争/百年续跑的轻量筛查只消费已有正式观测，不另开议会长跑：

1. 每个**新耐久配对**先检查同帧 ordinary feudal、玩家身份、日期、`councillor_steward` 占位及其来源索引。若边界内没有与 save 日期/玩家一致的原生 Council 帧，标记 unknown，不用早一帧代替。空席立即排除 replacement；在职仍只是一条线索，需原生 `incumbent_can_be_fired=false` 与另一普通候选同帧成立。
2. guest 仅在自然 pool guest/廷臣场景有明确线索后安排一次 provider 查询；`yearly.1090` 是原版候选生成线索，事件选项本身不证明 `candidate_is_guest=true`。pending 仅在有玩家发出的未决 proposal，且 recipient full ID 可能进入 steward provider 时安排一次查询；AI→玩家请求不计入。
3. WAR B0 已让出唯一实例窗口、该帧与上述退役帧有实质差异时，先用**官方恢复器**产出无未配尾、`ordinary_campaign_succession/xar_off` 的 save/driver 合法 pair；再复用已有 Council materializer、冻结 query-only DLL/EXE 与 `run_council_native_gate_scene_v1.py --preflight-only` 核版本、mod/DLC、环境、配对和 action OFF。Stage Q 只读上限 480 秒、动作数和日期增量均为零；查询无 isolated 阳性就退役该帧。

上述条件是调度线索，不将根上下文空席、自然事件或任何命令 ACK 升级为 guest/pending/fireability gate。四门仍 `1/4`，公共 Council query/action/ad 继续 OFF。
