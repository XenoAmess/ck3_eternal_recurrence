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
| GEN-001 | B0 | 一代人 supervised runner | strict `one_generation` 合同已在正常交互桌面多次 production-live：cold seed、无人输入循环、周期 checkpoint、first-blocker 与 cleanup 均实走；最新 100-turn run 完成 `100/100`、`49` gameplay 与 `5` durable checkpoints，只因 bound 收口并留下可冷恢复的 `53179800` anchor。自然死亡 settlement 尚未发生 | 从最新 checkpoint 进入全寿命长跑；只把真实 B0/B1 提升施工，直到同 episode 自然死亡并生成匹配 `terminal-settlement.json` | runner production-live；G1 未完成 |
| GEN-002 | B1 | 当前事件有多个合法选项 | current-window identity/presentation 与有限 indicator 已 live；scope wire 已 static-ready；完整效果与 semantic readiness 仍不足。现已实现只吃 same-frame shown+enabled 的可审计 fallback，并把直接动作升级为旧 full instance 必须推进 | 场景出现或专项验收时在正常交互桌面完成 scope query 与多选事件 degraded selection live；artifact 验证候选账本、预期 native index、旧 instance 推进、paused/episode/cleanup | static-ready；场景 live pending，`GEN-008` 已解除 |
| GEN-003 | B1/B2 | pending character interaction | 原生 inbound reply 树已冻结；exact allowlist 现为 `spar_with_knight_interaction` 与 war-sensitive `pay_ransom_interaction`。后者已 production-live 完成 typed query→reject→旧 full ID 消失→继续推进/checkpoint；unknown/宗教/其它 stock definition 仍 fail-closed，100% enforce 优先与 war-special 门不变 | 继续由长跑首个真实 key 驱动逐定义审计；补 `spar`/unique-accept/intermediary/notification live，并以 typed terms + utility 替换 reject-first | `pay_ransom` reject loop live；通用语义 B2 |
| GEN-004 | B1 | 已有战争到终局 | 当前 `claim_cb` primary-attacker 已 production-live 完成 options→claim terms v1→white-peace submit；AI 异步回复后 WarID 消失，残军解散，立即保存和平 checkpoint 并冷恢复继续。720 raw cooldown 期间不重复查询/提议。它不是原生等价或完整 v2 | 保留本切片；由下一次实际战争扩 victory/defeat、其它 CB/角色、多战争与完整 outcome utility | narrow production-live loop；通用终战 B2/B1 待场景 |
| GEN-005 | B2 | 非战争长期治理 | 经济、内阁、生活方式、家庭等大多不是通用 native semantic policy | 不出现强制 UI 时允许时间推进；出现阻塞则提升为 B1 并补最小动作 | 记账观察 |
| GEN-006 | B1 | 自然死亡与结算 | strict runner 在死亡后继续等待琉焰卿 Mod 的 committed settlement 与必要 record persistence；只接受本次执行且 `ready=true`、`commit_serial=1`、source CharacterID/settlement/cross-run record/no-heir/cleanup 全部匹配的 `death-terminal`。`terminal-settlement.json.one_life_settlement.final_score` 是权威“人生分数”，并须等于顶层 `score` 与 `recorded_episode.score`。最新 100-turn run 中 CharacterID `29829` 仍存活、`terminal=null`，自然完整 episode 尚未发生 | production 长跑观测玩家自然死亡，生成匹配 CharacterID `29829` 且三处人生分数一致的 `terminal-settlement.json`，并以全部 qualification gates GREEN 正常终止 | aggregate static-ready；自然 episode live 待执行 |
| GEN-007 | B2/B3 | 战斗质量 | reinforcement assigned/join、异常 terminal 与 forecast 未全闭合 | 若不阻塞当前 run 先记录；真实卡住或导致无法结束战争时提升为 B1 | 记账观察 |
| GEN-008 | B0（环境） | 执行会话曾无法启动 CK3 live acceptance | 旧 `CodexSandboxOffline / WinSta0\\CodexSandboxDesktop-*` 启动崩溃仍作为历史环境 RED 保留；当前宿主已是 `xenoa / console session 1 / WinSta0\\Default`，连续完成 white-peace、冷恢复、pending reply 与长跑，证明不再是当前 blocker | 无；未来环境切回隔离 desktop 时按相同 host guard 拒绝，不改 gameplay source 掩盖 | 2026-08-27 resolved |
| GEN-009 | B1（仅 G2） | 死亡后启动下一代 | production6b 的 `episode-seed.json` 指向另一 state，复制体内没有配套 `profile/save games/xar_episode_seed.ck3`；非空旧 metadata 还会阻止自动重建。strict G1 不执行继承人 gameplay，因此不影响单寿命 canary/死亡结算 | 跨代前复制并逐字节验证被引用 seed（63,874,889 bytes，SHA `46A753F02AAE87299AD9658DA898F5938C1103B251E1EF56AD29FE38E9EAF53D`）到新 state，或明确清理旧 metadata 后从受管路径重新建立；随后实测 `start-next-episode` | G1 非阻塞债务；G2 前必须处理 |
| GEN-010 | B1→B2 | 和平态存在合法宣战项，但完整 war-entry evidence 未齐 | 原生 declaration tree 与 native power 已先冻结/实读；旧 planner 因 forecast/cost/exit 缺失 `selected_step=None`。现以 `war-entry-minimal-defer-v1` 记录完整缺口并选择 `NO_DECLARE→life-advance`，即使 declare literal 可达也绝不宣战 | G1 已解除；后续补 participant arrival、combat forecast、campaign cost、exit assessment 与 calibrated utility 后才允许智能宣战 | continuation production-live；智能 war entry B2 |
| GEN-011 | B3 | checkpoint 仍有未命中的尾部形状 | 当前 live 的 pending white-peace→WarID 消失→残军 disband 已有即时战后 checkpoint；但“终止动作直接 applied 且无残军”、restore 前历史 anchor 未按最新 restore epoch 截断、以及 generic dirty gameplay 后立刻 planner-blocked 的尾部保存仍未实机触发 | 只有真实 production 路径出现进度丢失时升为 B0/B1；首次 G1 前不为理论形状扩 runner | 记账观察 |
| GEN-012 | B1 | `life-advance` 暂停收尾期间连续 revision turnover | 首个一次重试修复已在正式续跑中越过旧 `159→160` 边界并形成 17 个新 checkpoint，但第 107 回合又以 `expected 183, current 185` 停止；日志证明 CK3 已 resume 并执行引擎帧，仍属 composite pause 阶段的真实 production race，不是 CK3 AI policy | 只让 composite owner 在既有 command timeout 内令 `pause-map` 对 fresh running frames 收敛，采用真实 paused 帧且最多记录一次成功提交；不放宽 typed query/其它 primitive/旧 plan。单测后从 `AE73...5B42` cold checkpoint 续跑 | 更新 blocker-removal static-ready；production revalidation pending |

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
- 唯一成功终点是本次实际执行的 `death-terminal`：检测到死亡后仍须等到琉焰卿 Mod 发布 `ready=true`、`commit_serial=1`、
  source CharacterID 匹配的完整 settlement，并在新纪录场景等到 record persistence。其
  `terminal-settlement.json.one_life_settlement.final_score` 是权威“人生分数”，必须与文件顶层 `score`、
  `recorded_episode.score` 完全一致；零继承人 gameplay 与 cleanup 也必须吻合。启动帧已有 terminal、裸 terminal status、
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

## 2026-08-27 15:54：100-turn bounded continuation

- 正常交互桌面 run `20260827T074858Z-one-generation-0e20ca35` 从 cold checkpoint `date_raw=53178504` 启动，并在所有
  before/after snapshot 中保持 CharacterID `29829`、episode `native-29829-ee172aa720db` 与 alive binding。
- 共执行 `100/100` successful turns：`51` query、`49` visible gameplay、`5` durable checkpoints、`0` recovery、`0` terminal；
  日期推进到 `53179800`。最后一次 checkpoint 在 turn `100` 成功保存，size `67,931,059`、history index `575`、SHA-256
  `71F23BB9F735AE118E4580AE62A9B3CE4C22AEB2AF22A91447A0484FCE38C1BF`，可继续冷恢复。
- 最终 CharacterID `29829` 仍存活，active event、pending interaction、war 与 army 均为空，`terminal=null`、settlement
  `not_terminal`。runner 因此正确输出 `turn_limit / bounded_incomplete / ok=false`；`first-blocker.kind=run_bound_exhausted`
  只是人工运行边界，不登记为新的 B0/B1，也不改变 `GEN-006` 尚未 live 的事实。
- cleanup `session_report_ok/shutdown_ok/tree_gone/cleanup_proven/driver_closed` 全真，CK3 已退出。权威 report：
  `C:\Users\xenoa\AppData\Local\Temp\xar-one-generation-canary-20260827T1511-claim51fe8cf-state\runs\20260827T074858Z-one-generation-0e20ca35\report.json`，
  SHA-256 `784B6D17AC7F6C220C5E234914E03FA2539CD801E29FAC4F5C2ED4A91D8E827C`；first-blocker SHA-256
  `70B7625263ED09EFD376A727C5CF7274D7038B525C9C8F5C44F0F572813206A3`。
- 下一施工严格限定为从该 durable checkpoint 执行全寿命续跑：`--max-turns 50000 --timeout 604800
  --readiness-timeout 300 --checkpoint-every-advances 3`。再次仅耗尽人工边界则继续恢复；真实 B0/B1 才先更新对应 exact-build
  原生树并做最小 blocker-removal。只有匹配 CharacterID `29829` 的 terminal sidecar 与全部 G1 gates 闭合后才升级状态。

## 2026-08-27 19:12：GEN-012 runtime revision blocker

- 修复两日 battle hold 后的正式续跑 `20260827T104548Z-one-generation-5eb950f7` 已真实跨过旧 battle blocker：共完成
  `96/97` turns、`44` gameplay turns、`14` checkpoints，战斗正常结束，普通事件完成 option-1 生命周期，且继续出现合法的
  一日与两日推进。随后第 97 回合在 opaque `life-advance` 内命中
  `native gameplay revision mismatch: expected 159, current 160`；这是 harness B1，不是新的战争/事件/原生 AI 策略 blocker。
- 权威 `report.json` SHA-256 为 `7F5ECDCF1133BF4D071425B29D542F069F2812086866489DE196A28A3CE17994`；
  `first-blocker.json` SHA-256 为 `9243C785F434C8354D5D39E921A093FC748C30D9D3C2E2033145724F89DD81D1`。
  CharacterID `29829` 与 episode `native-29829-ee172aa720db` 仍存活且未改变，mailbox 和 cleanup 全绿。
- report 因 opaque composite 合同保守回落 immutable seed；独立字节取证另确认 turn 93 的最新已完成 checkpoint 未被尾部覆盖：
  `date_raw=53196960`、history `1996`、size `73,492,278`、SHA-256
  `1D6A994388232C130AE1BD168132D9ECBE6825725D7FF8E53A4A8C3F9E4F443D`，并与 `last_save.ck3`、`autosave.ck3` 完全一致。
  后续仅把它复制进 fresh state 重新冻结为 cold seed，并让 restore 按 anchor 截去失败分支 history。
- 最小修复只针对 `life-advance` 的暂停收尾：fresh 帧已暂停时采用该真实后置帧；仍 running 时仅在既有事件/速度语义稳定的
  条件下，以 fresh revision 最多再提交一次 `pause-map`。不允许 service 通用 re-plan、不削弱 query same-frame gate，也不改
  battle controller、war termination、ongoing-battle 或其它 CK3 AI policy 树。只有实机续跑越过此边界并保存更新 checkpoint 后，
  `GEN-012` 才能关闭。
- blocker-removal 已 static-ready：自动暂停并携带 active event 的 fresh 帧会被真实采用且不伪造 action；仍 running 的一次无害日期
  竞争只提交一个 fresh-native-revision `pause-map`；event/speed 漂移、第二次 running race、非 revision 错误仍失败。完整
  `test_native_bridge_driver.py` 为 `123 passed, 102 subtests passed`，`test_native_auto_run.py` 为
  `32 passed, 13 subtests passed`，`test_gameplay_bridge.py` 为 `169 passed, 35 subtests passed`。全 unit suite 除临时 worktree
  `safe.directory` 外为 `1307 passed, 2 skipped`；带进程局部 Git 配置重跑环境套件为 `54 passed, 1 skipped, 7 subtests passed`。
  独立只读审阅 PASS；尚未据此声称 production-live。

## 2026-08-27 19:47：GEN-012 连续 running revision 实证

- `aff784d` 的正式续跑 `20260827T112207Z-one-generation-3c7aa5e2` 已越过旧 `159→160` blocker，共完成
  `106/107` turns、`53` gameplay turns、`52` visible gameplay turns 与 `17` checkpoints，角色 `29829` 和 episode
  `native-29829-ee172aa720db` 均保持存活。第 107 回合随后在 opaque `life-advance` 中停止：
  `native gameplay revision mismatch: expected 183, current 185`；无 terminal，cleanup 全绿。
- 权威 `report.json` 为 `495,998` bytes、SHA-256
  `BC10E3DEA91392C2B25B3661231A858E81B1C9B79615865985CE59BBDBF42DB4`；`first-blocker.json` 为 `3,968`
  bytes、SHA-256 `8FC4B4074F9B42AA14F0911740813146F3F68DAB21E1081D6738E9901B45028B`。driver state 尾部为：
  history `2119` checkpoint 成功，`2120` query 在 paused public revision `180` 成功，`2121` `life-advance` 无 result 并失败。
- CK3 debug log 在 19:42:08--19:42:11 记录真实 scheme/effect/army/migration simulation ticks，blocker 发生于
  19:42:13.207；故障不在入口或首个 set-speed 之前，而是 resume 后令 map 重回 paused 的提交窗口。artifact 未保存内部 refresh
  frame，不能进一步声称是 event 还是 speed 字段变化。
- 最新可信物理恢复点为 `date_raw=53198376`、history `2119`、size `73,968,716`、SHA-256
  `AE73EFE1CC099BDB5BC474F500442723A55D8AC0FB2348172DC88E84A9C75B42`；`xar_checkpoint.ck3`、`last_save.ck3`、
  `autosave.ck3` 三者逐字节一致，失败尾部未再次保存。后续从该 anchor 冷恢复，不能采用 report 的保守 immutable-seed fallback。
- 必要性证据只支持一个最小增量：`_pause_life_advance` 在既有 command timeout 内持续以 fresh running revision 提交
  `pause-map`，直到观察到 paused 或超时；已 paused 的帧直接采用且不伪造 action，成功提交最多记一次。不得扩为 service 通用重试，
  不得削弱 query same-frame gate，也不改变 planner、战争、事件或其它原生 AI 决策树。预期收益是解除已复现的长跑 B1，并让同一
  episode 从最新 checkpoint 继续；没有证据支持其它防御性扩张。
- 更新 blocker-removal 已 static-ready：循环仅存在于 `_pause_life_advance`，每次 pre-submit mismatch 读取 fresh frame，并把同一
  绝对 deadline 的剩余预算传给 command-result 与 paused-postcondition 等待；ACK 后立即退出提交循环，只记录一个真实 action。
  自动暂停、连续两次 running race、event/speed drift、deadline 零提交、非 revision 错误直抛和 ACK 后不重提均有回归。
  聚焦为 `8 passed, 2 subtests passed`，完整 driver 为 `126 passed, 102 subtests passed`，auto-run 为
  `32 passed, 13 subtests passed`，gameplay bridge 为 `169 passed, 35 subtests passed`；全 unit suite 为
  `1316 passed, 2 skipped, 882 subtests passed`。`py_compile` 与 `git diff --check` GREEN，独立只读审阅 PASS；在从
  `AE73...5B42` cold restore 实机越过并保存更新 checkpoint 前仍不得关闭 `GEN-012`。
