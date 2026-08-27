# 一代人自治：阻塞与能力债账本

状态：**2026-W35 最高优先级 / 进行中**

所有者指令时间：2026-08-27 09:47（Asia/Shanghai）

所有者再次确认：2026-08-27 11:14（Asia/Shanghai）——相关逻辑仍必须先梳理 exact-build CK3 原生 AI；梳理完成后不要求
立即照搬原生实现，允许用最小实现先解除整局 blocker，并把未采用分支与质量差距记账。

本账本服务于一个具体阶段目标：让 Agent 从固定 production、map-ready seed 开始，无人代打地持续游玩，直到当前玩家角色
死亡并完成一代结算。这里优先记录“会让整局停住”的 blocker；不会阻塞流程但影响决策质量的缺口记为能力债，首次 GREEN
后继续打磨。

## 分级

| 等级 | 定义 | 处理顺序 |
|---|---|---|
| B0 | 主循环无法启动、进程失控、无法观察当前帧或无法恢复 | 立即处理 |
| B1 | 必须回应的事件/互动/战争状态无法采取合法动作，时间无法继续 | 紧随 B0 |
| B2 | 能继续但只能使用低信息启发式，可能降低角色收益或生存率 | 记录输入、选择与结果；不阻塞首轮 |
| B3 | 覆盖面、策略精度、性能或展示不足，不影响当前一代继续 | 首次 GREEN 后打磨 |

## 当前账本

| ID | 等级 | 场景 | 当前事实 | 最小解除条件 | 状态 |
|---|---|---|---|---|---|
| GEN-001 | B0 | 一代人 supervised runner | 已在现有纯原生 owner 上实现严格 `one_generation` 合同与 artifact wrapper：固定 cold seed 归档、无人输入循环、可调周期 checkpoint、first-blocker、死亡结算与 cleanup gates 均已 `static-ready`；没有另造 gameplay loop | 在正常交互桌面用最终 clean source/new prepared state 跑 20-turn canary，再启动长跑并由首个真实 blocker 排序 | static-ready；production live 待 `GEN-008` |
| GEN-002 | B1 | 当前事件有多个合法选项 | current-window identity/presentation 与有限 indicator 已 live；scope wire 已 static-ready；完整效果与 semantic readiness 仍不足。现已实现只吃 same-frame shown+enabled 的可审计 fallback，并把直接动作升级为旧 full instance 必须推进 | 正常交互桌面完成 scope query 与多选事件 degraded selection live；artifact 验证候选账本、预期 native index、旧 instance 推进、paused/episode/cleanup | static-ready；live 待 `GEN-008` A/B |
| GEN-003 | B1/B2 | pending character interaction | 原生 inbound reply 树已冻结；notification 保持 ACK-only；`ordinary-reject-unique-accept-v1` 仅对 exact-build 明确 allowlist 的 `spar_with_knight_interaction` 启用，未知/宗教/其它 stock definition fail-closed；active war 并存时 100% enforce-demands 无条件优先；known/opaque war-special 继续阻塞 | 正常交互桌面实测 allowlisted reject 与 unique-accept 各一次，验证 plan 分类/候选账本、旧 full ID 消失、结果状态与 cleanup；随后发布 typed definition/subtype classification、terms 与 utility，替换单键 fallback | static-ready；production live 待 `GEN-008` |
| GEN-004 | B1 | 已有战争到终局 | 原生终战树与 exact-build ABI 已先冻结；现有新 source 已实现最窄 `claim_cb` 进攻方白和 counter-policy：逐 option typed final response、same-frame options→claim terms v1→offer、提交后 WarID 消失/仍存在两态结果与 720 raw 冷却。它不是原生等价或完整 v2；production6b 尚未用新 DLL 读到 final response/v1 | 用与新 source 配套的新 DLL 在 production6b fresh paused frame 依次取得 options 与 v1，命中全部门后提交；WarID 消失才算 applied，pending 则同日推进一次并在冷却期恢复军事 OODA；随后验证战后解散/保存/继续 | narrow static-ready；production-live pending |
| GEN-005 | B2 | 非战争长期治理 | 经济、内阁、生活方式、家庭等大多不是通用 native semantic policy | 不出现强制 UI 时允许时间推进；出现阻塞则提升为 B1 并补最小动作 | 记账观察 |
| GEN-006 | B1 | 自然死亡与结算 | strict runner 现只接受本次执行且 source CharacterID/score/settlement/cross-run record/no-heir/cleanup 全部匹配的 `death-terminal`，并输出独立 terminal sidecar；自然完整 episode 尚未实机发生 | production 长跑观测玩家自然死亡，生成 `terminal-settlement.json` 并以全部 qualification gates GREEN 正常终止 | aggregate static-ready；自然 episode live 待执行 |
| GEN-007 | B2/B3 | 战斗质量 | reinforcement assigned/join、异常 terminal 与 forecast 未全闭合 | 若不阻塞当前 run 先记录；真实卡住或导致无法结束战争时提升为 B1 | 记账观察 |
| GEN-008 | B0（环境） | 当前执行会话无法启动 CK3 live acceptance | 相同 exact EXE/save/runner 在 `CodexSandboxOffline`、`WinSta0\\CodexSandboxDesktop-*` 中于启动期固定崩溃 `ck3+0x1DABD89`；当日既有 live GREEN 均来自 `xenoa` 的普通交互环境。事件 scope query 从未执行，因此不能判为 capability RED | 在 `xenoa` 正常交互 PowerShell / `WinSta0\\Default` 原样复跑 a860702 default-off acceptance，完成同命令 A/B；在此之前继续可离线的 blocker-removal，不改 native 逻辑掩盖环境差异 | 外部 A/B 待执行 |
| GEN-009 | B1（仅 G2） | 死亡后启动下一代 | production6b 的 `episode-seed.json` 指向另一 state，复制体内没有配套 `profile/save games/xar_episode_seed.ck3`；非空旧 metadata 还会阻止自动重建。strict G1 不执行继承人 gameplay，因此不影响单寿命 canary/死亡结算 | 跨代前复制并逐字节验证被引用 seed（63,874,889 bytes，SHA `46A753F02AAE87299AD9658DA898F5938C1103B251E1EF56AD29FE38E9EAF53D`）到新 state，或明确清理旧 metadata 后从受管路径重新建立；随后实测 `start-next-episode` | G1 非阻塞债务；G2 前必须处理 |

## Degraded heuristic 纪律

- 每个相关策略仍须先完成对应 CK3 原生 AI 树与 exact-build 证据账本；不得先猜策略、事后补文档。
- 研究完成后不强制照抄原生树，也不要求等待原生树的全部质量分支都实现。允许先做能解除 blocker 的最小 deterministic
  policy，但必须登记未采用的原生输入、分支、质量差距与后续替换入口。
- 只能从原生观测证明合法且当前可执行的候选中选择。
- 每次降级选择记录缺失字段、候选集合、采用的 deterministic rule 与后置状态。
- 首轮目标是继续游戏与保住可恢复性，不声称选择最优。
- 若动作后没有可观察的预期状态变化，立即记为 blocker；ACK 不计成功。
- 宗教继续冻结；仅圣战战争 OODA 与婚姻必要判定允许最小 faith 输入。

## 首轮验收阶梯

1. `G0 runner-ready`：统一循环、终止条件、artifact 和 blocker 输出可运行。
2. `G1 one-generation GREEN`：一个固定 production seed 无人工游戏输入走到自然死亡/结算。
3. `G2 repeatable`：同一合同至少再跑一轮，checkpoint 恢复后仍能继续。
4. `G3 broadened`：增加 ruler、政府、战争/和平起点与 enabled-feature 代表场景。

本周最高优先级是尽快取得 G1；G2/G3 与策略质量持续推进，但不得反过来阻塞首个 G1。

## 2026-08-27 11:56：G0 static-ready

- `native_auto_run` 新增向后兼容的 `completion_contract=one_generation`；原 bounded 合同保留。strict 模式冻结初始
  episode CharacterID/run/date，要求 exact v2 cold checkpoint，检查每个 before/after binding，并沿用已验证的三次 eligible advance
  checkpoint cadence。
- 唯一成功终点是本次实际执行的 `death-terminal`：terminal reason、完整 settlement、source CharacterID、score、record
  persistence、cross-run recorded episode、零继承人 gameplay 与 cleanup 必须全部吻合。启动帧已有 terminal、裸 terminal status、
  `strategy-review`、`settlement_unavailable` 或上限耗尽均不能 GREEN。
- `native-one-generation` 会先归档固定 seed checkpoint 与匹配 driver state，再原子写 `report.json`；失败写
  `first-blocker.json`，成功写 `terminal-settlement.json`。blocker 以 first-write-wins 保留当前失败尝试的 plan、动作、result、
  before/after、active context 和最后 durable checkpoint；即使失败发生在 turn append 前，attempted count 也不会错误归零。
  bound exhaustion 明确只是 `bounded_incomplete`。
- 默认 cadence 是 3 次 verified eligible advance，不是 3 个游戏日；和平 `life-advance` 通常约 30 天一步，因此默认大致是季度级
  恢复点。此前 365-action 默认最坏可能丢掉约三十年进度，现已作为实际恢复性问题纠正。fixed
- checkpoint 使用同一 `xar_checkpoint.ck3` 原位覆盖；保存命令开始提交后若 post-snapshot/hash/history 验证失败，core 会立即撤销
  所有同路径旧 metadata 的可恢复声明；readiness preflight 在提交前失败则保留旧恢复点。严格 wrapper 只把前一种 blocker 降级重绑
  到本次 `seed/` 中不可变归档的 checkpoint + driver state，宁可丢掉本轮进度，也不声称已被覆盖的旧字节可恢复。
- 组合式 `service.auto_turn()` 在 typed outcome 返回前无法暴露 planner 选中的 step；其中途异常按“可能已经提交 save-checkpoint”处理，
  同样撤销 live path 并回落 immutable seed。返回 blocked/terminal 或其它 typed step 后再解除该不透明窗口。
  seed 证明从当前 map-ready recovery anchor 到死亡的一代过程，不把 seed 之前的出生/即位历史算成本次 Agent 游玩。
- orchestration 复用既有 planner/driver，没有新增策略候选或评分，因此本包不派生新的原生 AI 树。首次 live blocker 若要求修改事件、
  互动、战争或其它策略，仍先更新对应 exact-build 原生专题，再允许最小实现并记账。

## 2026-08-27 12:51：GEN-003 ordinary reply static-ready

- 施工前置复核了 `events-and-interactions.md` 与 `interaction-structured-terms.md` 已冻结的 exact-build pending/reply 树：主动
  `ai_will_do`、AI responder `ai_accept` 与 human pending reply 是不同模型；accept/reject/block/ACK legality 必须独立读取。
- `strategy.py` 现只对 exact same-frame/full-ID、角色/路由/deadline/legality 完整，且命中 exact-build 单键 allowlist
  `spar_with_knight_interaction` 的 request 启用 `ordinary-reject-unique-accept-v1`。`special_war_binding_not_applicable` 与
  `special_data_present=false` 不再冒充通用 ordinary 证据；未知 stock、mod、宗教 definition 均 `definition_unclassified` fail-closed。
  allowlist 证据是原版 `00_tradition_interactions.txt` 完整文件 SHA-256
  `E3B7330D8DFD9C82522D65629B6DD991D319B76B41C388CE483E351D829391E3` 及第 1–200 行完整 definition：双方不在战争、accept
  仅启动 non-lethal bout，且没有 faith/religion/marriage、`special_interaction`、`target_type`、`auto_accept` 或 `on_decline` 字段。
  `invite_to_activity_interaction`
  因可承载 `activity_wedding` 而被移出 allowlist；bridge 未发布 subtype 时不得猜。reject 原生合法却 action 不可达时保持
  blocked，不会改走 accept；accept 只在其它三路都被原生明确判为非法且自身唯一合法可执行时使用。notification 的 ACK 路径未改。
- active war 与 allowlisted ordinary pending 并存时，planner 只暂存 pending plan，必须先检查 100% war-score enforce-demands；回归
  fixture 已覆盖 40% 后返回 reject 与 100% 时优先 `enforce-demands-88`，不再允许 pending 提前 return。
- plan 与 strict runner 已有 compact-plan 字段共同保留 full ID/key/roles/deadline/legality/special binding、frame binding、缺失语义、
  四路候选/action reachability、rule ID、recommended/selected action 与 blocked reasons。策略继续声明
  `native_ai_equivalent=false`、`semantic_optimal=false`、`semantic_decision_ready=false`。
- strict runner 已把 pending mirror 加入 semantic delta，并新增 reply lifecycle gate：typed status/old full ID/sender、remaining pending 与
  after snapshot 必须全部匹配，才产生 `pending_interaction_changed` visible gameplay、dirty state 与尾部 checkpoint。compact result 保留
  有界 lifecycle 字段；缺失 typed postcondition 直接以 `pending_interaction_lifecycle_postcondition_failed` 停止。
- 三个 known war-exit subtype 额外审计 exact outcome/WarID/primary roles/revision 和当前 active-war row；即使 binding 完全吻合，
  `special_outcome_terms_ready=false` 仍强制 blocked。opaque、mismatch、stale、unknown legality、identity mismatch 与无可执行 channel
  同样不提交。
- 未采用/质量债：按 interaction 类型的 target/exchange/effect 与 campaign utility、intermediary/recipient AI raw/final acceptance，
  以及 war-exit 的 resource/claim/truce/prisoner/hostage dynamic terms。下一替换入口仍是补 typed semantics，不把 reject-first 冒充
  高智商或原生等价策略。
- 验证：本次优先级/allowlist 阻断修复后，`test_gameplay_bridge.py` 为 `161 passed, 31 subtests passed`；GEN-003 六文件聚焦
  聚合为 `251 passed, 68 subtests passed`。修改 Python 文件经项目虚拟环境 `py_compile` 通过，相关差异经 `git diff --check` 通过。
- 本阶段只达到 static-ready；production reject/unique-accept 的旧 full pending ID 推进与实际结果仍待正常交互桌面验收。

## 2026-08-27 14:25：GEN-004 最窄 `claim_cb` 白和包 static-ready

- 施工前置复核并同步了 `war-termination.md` 与 `player-war-exit-policy.md` 的原生 interaction/context、validator、
  final recipient evaluator、`claim_cb` claim disposition 与三 outcome 优先级。owner 允许本轮不等待完整 exit-terms v2 / campaign
  forecast，而先交付解除一代人 blocker 的最小 counter-policy；它明确不是 CK3 原生 AI 等价实现，也不是最终高智商止损策略。
- 新 strict options schema 要求每个 option 都有
  `recipient_response={status,decision_status_raw,would_accept_now}`。exact-build native reader 在每个最终 context 析构前复用
  `ReadWarExitRecipientResponse` / `0x2C43B40(context,1,0,null,null)`；validator=false 或 status>=3 只使该 option response
  显式 unavailable，不使整份 options query unavailable。Python 严格拒绝字段缺失、bool 冒充 int、0/1/2 以外 status、
  null/available 交叉污染和 `would_accept_now != (raw != 2)`；正 acceptance raw 不能覆盖 final status=2 的拒绝。
- planner 与 direct execute 只在同 paused frame、同 snapshot/revision/native revision/connection/episode、full WarID 下启用：玩家为
  primary attacker，CB 恰为 `claim_cb`，`0 <= score < 100`，战争至少 365 日，white peace permission/context/validator/available
  全真，无 hostage，typed final response 明确 `would_accept_now=true`；随后同帧查询 claim terms v1，要求 ready、claimant=played
  character、declared targets 与战争目标一致且全部 claim present。weak claim 也允许，因为原版 `claim_cb` 白和保留并强化 weak
  claim；要求全部 strong 反而会错误阻塞合法的结构性止损路径。宗教、圣战、其它/未知 CB 与 surrender 均不进入本切片。
- active event 仍最先处理；其后全局 100% enforce-demands 永远先于 auto-accept notification、普通 pending interaction、
  battle-control 与白和，即使 enforce literal 暂不可达也不能降级到后续动作。普通 pending 位于白和之前。白和提交 ACK 必须
  exact shape；随后读取命令后当前可用的 paused observation（不声称 revision
  必然推进），并要求同 bridge PID、connection
  generation、episode、played CharacterID 与同 date。旧 WarID 消失才输出 `applied`；仍存在只输出 `submitted_pending`，同日只
  `life-advance` 一次让 AI 处理，之后同 WarID 在 720 raw（30 日，24 raw/day）内不重复提议。持久 history 在 restore 后继续
  抑制重复，`+719` 仍阻断、`+720` 才可重试。
- strict runner/artifact 保留 bounded plan decision 与 `war_termination_result` 的 submission/result 字段。`applied` 必须同时有旧
  full WarID、after 中 WarID 消失和 `war_changed` semantic evidence；pending 的 remaining row 必须与 after 实际 row 完全一致，且
  pending 不计 visible gameplay 或 completion。ACK-only、malformed ACK、错 date/episode/CB/claimant/targets 均不能冒充战争结束。
- production6b 的**现有只读证据**仅能静态预测会命中前半门：played CharacterID `29829`、WarID `16777290`、玩家 attacker/
  primary、最新战分 `37`、declared target `[2388]`；历史帧曾见 duration `436` 与 WP validator/available=true，但都必须 fresh
  重查。acceptance `+12.7912` 不能代替 final response；现有 artifact 完全没有新 `recipient_response`，也从未查询 v1 terms，
  文档中的旧 strong claim 不能复用为 machine input。预期序列是 T1 options、T2 同帧 v1、T3 offer；若 pending，T4
  `life-advance`，其后 WarID 消失才继续 disband，否则 720 raw 内恢复军事 OODA 而不重提。
- 兼容边界：固定 G1 handoff 的 source `480f287` 与旧 DLL 仍是一个独立 legacy 组合，不能和新 strict Python source 混配；新
  schema 会有意拒绝旧 DLL 缺失 `recipient_response` 的 options row。首次 live 必须另建与本 source 配套的新 DLL canary，不得
  静默复用旧 clone，也不得在 fresh canary 前把新字段写成 live。
- 未采用/替换入口：完整 exit-terms v2 的逐人资源、actual truce/PoW/hostage、动态 title/vassal operations，以及 finance、兵力、
  encounter distribution、增援/围城 ETA、人格/文化/其它战争等原生/campaign 输入仍记为质量债；production outcome 会驱动后续
  校准。本包没有借战争例外扩展 faith/religion 研究。
- 离线验收：相关 Python 四文件聚合 `322 passed, 170 subtests passed`；MSVC Release 全 native build 成功，CTest
  `37/37 passed`。这是 static-ready，不是 production-live loop，也不解除正常交互桌面上的 fresh new-DLL canary 前置门。
