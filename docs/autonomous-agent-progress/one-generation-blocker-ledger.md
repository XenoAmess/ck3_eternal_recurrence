# 一代人自治：阻塞与能力债账本

## 2026-09-21 R0036-R0043 GEN-034-D replay and same-session closure ledger

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Correct pre-terminal continuation | production candidate GREEN; action not submitted | formal `native_auto_run` terminal intercept | R0039 report `0DCE56AA...78A6`; action input `6612D273...583D`; source capture `FF76C8E1...EB04`; agent `c05e940c` | `41/41` turns; continue / white-peace / surrender compared on one frame; surrender won by `11,661,500`; one frozen `surrender-war-16777285`; no action submitted | candidate checkpoint `44AEE0C8...65B0`; driver `E102C20E...40BC`; cleanup and process-zero GREEN | Execute terminal choice on its producing paused frame, then prove material result, postwar checkpoint, new-process restore and next turn; `/root` | same-session repair branch active until linear master delivery and immediate cleanup |
| Pre-action cold-restore authorization replay | capability RED retained; zero action | frozen R0039 action runner | R0040 report `A6A4B981...6858` | Same date/war/score/duration, but restored target total changed `22889080000 -> 16433600000`, ratio `226973 -> 162959`, and recommendation flipped `surrender -> continue`; authorization rejected before submit | Cleanup and external CK3/injector process-zero GREEN; no postwar checkpoint because no action occurred | Do not retry the stale authorization. The default-off repair keeps intercept and one action on the same driver/frame; focused normal/`-O` each `130/130` GREEN; run one new canonical live round | no native ABI/public MCP/open_kaishek change; live closure pending |
| Same-session dynamic terminal advertisement | capability RED retained; zero action; narrow static repair GREEN | terminal callback on the producing driver/frame | R0041 report `850F14F0...609D`; agent `1353324a`; PID `136748` | `41/41` turns; surrender again won by `11,661,500`; callback's four read-only queries were GREEN, but capabilities had been captured before they refreshed the dynamic WarID literal, so action gate blocked on `recommended_action_step_not_advertised` | No action or postwar save/restore; source triplet unchanged; candidate cleanup and process-zero GREEN | Refresh capabilities after option/power/terms reads, then run one new canonical round; normal/`-O` combined suites each `142/142`; `/root` | fix branch active; no native ABI/public MCP/open_kaishek change |
| Stable source identity after natural army merge | capability RED retained; zero action; narrow static repair GREEN | terminal callback on the producing driver/frame | R0042 outer `B3D441DC...0CE`; native `42A41260...410`; final driver `BDB3E2A5...A65`; agent `a466ac14`; PID `106896` | `41/41` turns; refreshed action gate authorized `surrender-war-16777285`, then the pre-action source check rejected six creation CArmy containers versus one current merged container. WarID plus all 24 persistent/current regiment IDs were identical; h1985-h1988 are read-only and no terminal command exists | h1984 checkpoint `1A11C221...581` remains recoverable; cleanup/tree reclaim GREEN and a fresh external inventory was zero | Bind source→active on stable WarID/persistent/current regiment identity; retain complete active set including current CArmy for active→cleanup; recursively retain async leaf errors; normal/`-O` direct consumers each `140/140`; `/root` | temporary repair ref requires cleanup after linear master delivery; no native ABI/public MCP/open_kaishek change |
| GEN-034-D source-bound terminal closure | **complete**; G2-M0 visible outcome closed | formal `native_auto_run` same-session terminal callback | R0043 outer `9294D8B8...13EE`; native `2B726601...2D6`; driver `EB46D74F...E4F`; agent `8ec1153e` | One paused frame compared continue/white peace/surrender and submitted only h1989 `surrender-war-16777285`; the independent post frame proved WarID absence, exact gold/prestige deltas, directional persisted truce and destruction of all 24 source-bound regiments; h1995/h1996 next formal cycle consumed the peaceful state and disbanded the residual army without surrender replay | h1993 checkpoint `A89BCF26...B296`; h1994 replaced PID `77580→41264`, retained postwar resources/truce/WarID absence; cleanup/tree reclaim and fresh external process-zero GREEN | None for M0. Continue with ordinary production natural-event, succession and governance gates; `/root` | `8ec1153e` is on remote master and its temporary implementation branch is deleted; frozen runtime worktree remains an evidence dependency until artifact retirement |

R0036 was voided after obsolete CLI aliases failed before launch; R0037 was a
prelaunch wrong-DLL-path RED; R0038 reused an already post-intercept pair and
therefore completed `64/64` turns without a new terminal interception. Those
attempts and R0041/R0042 are retained as RED history. R0043 closes the same-session chain, so authority is now G2
`2/8`, Council remains `1/4`, and GEN-034 is `4/4`.

## 2026-09-21 R0034-R0035 GEN-034-D action-runner lifecycle ledger

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Long-war terminal candidate | production candidate GREEN; action not submitted | formal `native_auto_run` -> terminal intercept | R0034 outer `A0DBA3F2...002FF`; native `37EB0706...668D`; frozen input `51847A20...9EEC`; source `e0dbcefe` | Turn41 retained exact option/power/terms certificate; surrender beat continue by `11,661,500`; literal `surrender-war-16777285`; all boundaries retained `action_submitted=false` | New h1984/date53190816 checkpoint `27E1EB29...EC36` and driver `87D195FF...489F`; candidate cleanup GREEN and process count zero | Execute only emitted action in a distinct canonical round; verify material postwar/later turn/checkpoint/cold restore; `/root` | source package integrated on master; frozen runtime remains active until successor action candidate is retired |
| Rebound lifecycle handoff into action driver | R0035 capability RED retained; minimal static repair GREEN; replay pending | emitted GEN-034 action runner command | R0035 report `52CB1007...0E1F`; rebound environment `bc4540a2...dfca -> 2a5f9500...774f` | Driver pipe rejected the legacy default before readiness; `mcp_sequence=null`, therefore no terminal query/submission/result occurred; immutable source pair unchanged | Runner cleanup and external process-zero GREEN; failed writable attempt retired, R0034 h1984 pair remains the retry source | Freeze repaired runtime, allocate new round, re-emit/rebind an unchanged authorized runner command, then complete action/postcondition/restore; `/root` | repair branch active until linear master delivery and immediate cleanup |

This repair changes only the private live action runner's use of an existing
validated succession-lifecycle binding. Native ABI, public MCP and
`open_kaishek` are `NO-CODE-CHANGE`. Authority remains G2 `1/8`, Council `1/4`,
GEN-034 `3/4`.

## 2026-09-21 R0033 GEN-034-D action-step projection ledger

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Long-war Raiktor terminal literal projection | production RED retained; narrow static repair GREEN; live replay pending | formal `native_auto_run` -> three-way action gate | R0033 native `54440267...29C6C`; outer `9D1EBE90...A8E9`; source agent `2a3201b5` | Turn41 current-frame option/power/terms chain stopped on `recommended_action_step_not_advertised`; failed turn retained no recommendation certificate/literal; zero terminal submissions and no runner input | R0033 durable checkpoint at turn32/date53190768 exists, but replay will use the clean R0032 pair; R0033 cleanup GREEN and CK3=0 | Integrate/refreeze, cold replay to a matching intercept, then execute only emitted action and verify material result/later turn/checkpoint/new-process restore; `/root` | feature branch active; cleanup required immediately after linear master delivery |

The repair changes only Python dynamic action-step projection, execution and
lifecycle revalidation, plus semantic-surrender to typed-attacker-defeat
postcondition comparison. Native ABI, public MCP and `open_kaishek` are
`NO-CODE-CHANGE`.
Authority remains G2 `1/8`, Council `1/4`, GEN-034 `3/4`.

状态：**G1 与首个固定-seed G2 跨 episode gate 均于 2026-08-30 完成；能力债与扩展矩阵继续**

所有者指令时间：2026-08-27 09:47（Asia/Shanghai）

所有者再次确认：2026-08-27 11:14（Asia/Shanghai）——相关逻辑仍必须先梳理 exact-build CK3 原生 AI；梳理完成后不要求
立即照搬原生实现，允许用最小实现先解除整局 blocker，并把未采用分支与质量差距记账。

本账本服务于一个具体阶段目标：让 Agent 从固定 production、map-ready seed 开始，无人代打地持续游玩，直到当前玩家角色
死亡并完成一代结算。这里优先记录“会让整局停住”的 blocker；不会阻塞流程但影响决策质量的缺口记为能力债，首次 GREEN
后继续打磨。

2026-08-30 最终 run `20260830T070223Z-one-generation-1f934571` 已取得首次 G1 GREEN：`155/155` turns，CharacterID
`29829` 自然终止后等到 `commit_serial=1` 的 committed settlement，三处人生分数均为 `14.8`，record/no-heir/cleanup 全绿。
report SHA-256 为 `FF689E88...EFB3`，terminal sidecar 为 `D26744BF...850E`。下表保留全部历史 RED 与能力债；GEN-001/006
现已关闭。G2 前探关闭 GEN-032 后，严格 runner 又以三次独立 attempt 完成 GEN-009；其中 capability RED 与 harness RED 均保留，
最终 GREEN 已实走 `start-next-episode`、新 run ID、新 episode gameplay 与 durable checkpoint。
截至 2026-09-12，同一冻结 seed 的第二完整寿命、结算与再次跨 episode loop 已完成；它们是历史前置证据，不纳入现行 G2 的
8 项可见 OODA 分母。当前 G2 为 `0/8`，权威状态见 [`g2-requirements-and-execution.md`](g2-requirements-and-execution.md)。
当前 P0 仍是 `GEN-034`：R459 已闭合 source-specific loss/truce 与一次真实 surrender/postwar，R471 已闭合 active-war
strategic-power primitive；余下入口只有 policy-level campaign dominance、versioned strategy profile、same-frame white-peace comparison
和三路 recommendation/action。旧 index `9/10` shape 枚举已被后续证据淘汰，不得再作为施工入口。

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
| GEN-001 | B0 | 一代人 supervised runner | `1f934571` 从 `0DF9CB66...69C` 冷恢复同一 episode，`155/155` turns、`53` gameplay、`15` checkpoints、`1` terminal；CharacterID `29829` 自然终止，settlement 与 cleanup 全绿 | 已满足；保留 fixed-seed G1 artifact，不重复 canary。下一阶段以更多 seed 与普通 campaign 跨继承验证泛化 | 2026-08-30 resolved；G1 qualified production-live loop |
| GEN-002 | B1 | 当前事件有多个合法选项 | current-window identity/presentation 与有限 indicator 已 live；scope wire 已 static-ready；完整效果与 semantic readiness 仍不足。现已实现只吃 same-frame shown+enabled 的可审计 fallback，并把直接动作升级为旧 full instance 必须推进 | 场景出现或专项验收时在正常交互桌面完成 scope query 与多选事件 degraded selection live；artifact 验证候选账本、预期 native index、旧 instance 推进、paused/episode/cleanup | static-ready；场景 live pending，`GEN-008` 已解除 |
| GEN-003 | B1/B2 | pending character interaction | 原生 inbound reply 树已冻结；signed int32 full ID 已 production-live，`pay_ransom` 与 definition-bound `arrange_marriage_interaction` 均已完成 typed query→reject→旧 full ID 消失/变 null→继续推进。婚姻分支只匹配 direct recipient、完整四角色、无 intermediary、六 option 全未选与 reject legality；unknown/宗教/其它 special 仍 fail-closed，100% enforce 优先与 war-special 门不变 | 继续由长跑首个真实 key 驱动逐定义审计；补 `spar`/unique-accept/intermediary/notification live，并以 typed terms + utility 替换 reject-first；婚姻后续补发送时 acceptance 与 secondary pair/alliance 结果 | 两条 exact reject loop production-live；通用语义与婚姻最优性 B2 |
| GEN-004 | B1 | 已有战争到终局 | 当前 `claim_cb` primary-attacker 已 production-live 完成 options→claim terms v1→white-peace submit；AI 异步回复后 WarID 消失，残军解散，立即保存和平 checkpoint 并冷恢复继续。720 raw cooldown 期间不重复查询/提议。它不是原生等价或完整 v2 | 保留本切片；由下一次实际战争扩 victory/defeat、其它 CB/角色、多战争与完整 outcome utility | narrow production-live loop；通用终战 B2/B1 待场景 |
| GEN-005 | B2 | 非战争长期治理 | 经济、内阁、生活方式、家庭等大多不是通用 native semantic policy | 不出现强制 UI 时允许时间推进；出现阻塞则提升为 B1 并补最小动作 | 记账观察 |
| GEN-006 | B1 | 自然死亡与结算 | `1f934571` 死亡后没有立即停止；等到 `ready=true / commit_serial=1 / source_character_id=29829`。顶层、settlement 与 recorded episode 分数均为 `14.8`；record persisted，`continue_as_heir_after_death=false / heir_gameplay_actions=0`，cleanup 全绿 | 已满足；terminal sidecar `D26744BF...850E` 与 report `FF689E88...EFB3` 冻结保留 | 2026-08-30 resolved；fixed G1 episode production-live loop |
| GEN-007 | B2/B3 | 战斗质量与吞吐 | ordinary active combat、committed route 与 baseline 已选定的 stationary objective 均以 speed 3 production-live；`6421f80c` 的完整 turn-loop 为 `165d / 156.566s = 63.232 日/分钟`。`a2c81a0 / 95a466b` 将 typed speed 1–5 与严格策略中立替换合同合入 production；`9186bfa3` 再次实机走通 stationary/route speed 3，但短 run 含冷启和事件，不作为吞吐样本 | speed 3 已重复越过 `>=60 日/分钟` hard gate；G1 保留已验证 speed 3。继续在完全相同战争合同下做 speed-4/5 matrix、碾压局零暂停和 120 stretch 预研；不得改变宣战、参战、目标、投降、议和或终战偏好 | speed-3 全部目标类型 production-live；60 hard GREEN；120 stretch 与 speed-4/5 live gate 未完成 |
| GEN-008 | B0（环境） | 执行会话曾无法启动 CK3 live acceptance | 旧 `CodexSandboxOffline / WinSta0\\CodexSandboxDesktop-*` 启动崩溃仍作为历史环境 RED 保留；当前宿主已是 `xenoa / console session 1 / WinSta0\\Default`，连续完成 white-peace、冷恢复、pending reply 与长跑，证明不再是当前 blocker | 无；未来环境切回隔离 desktop 时按相同 host guard 拒绝，不改 gameplay source 掩盖 | 2026-08-27 resolved |
| GEN-009 | B1（G2） | 死亡后启动下一 episode | immutable seed 为 `76,980,533` bytes、SHA `E3B4A97D...C5D91`、`date_raw=53211552 / CharacterID=29829`。formal attempt 01 在 terminal-inside-sentinel 后置误判 RED；attempt 02 因并行 CK3 owner lock 为 0-turn harness RED；attempt 03 从旧 PID `57484` 重启到 `33200`、connection `1→2`，新 run ID `native-29829-fffa4ba935f6`，精确 seed reload 后完成一次 visible gameplay，并保存 `date_raw=53211576 / history=4 / BB4CD2B5...DC235` 的新 episode checkpoint | 已满足首个 fixed-seed G2 gate；保留三次 attempt、ACK、输入/输出 checkpoint、driver state、logs 与 sidecars。下一步是第二个完整寿命及不同 seed/ruler/government/DLC 矩阵，不重复本 gate | 2026-08-30 resolved；cross-episode production-live loop，report `22F54519...E565` |
| GEN-010 | B1→B2 | 和平态存在合法宣战项，但完整 war-entry evidence 未齐 | 原生 declaration tree 与 native power 已先冻结/实读；旧 planner 因 forecast/cost/exit 缺失 `selected_step=None`。现以 `war-entry-minimal-defer-v1` 记录完整缺口并选择 `NO_DECLARE→life-advance`，即使 declare literal 可达也绝不宣战 | G1 已解除；后续补 participant arrival、combat forecast、campaign cost、exit assessment 与 calibrated utility 后才允许智能宣战 | continuation production-live；智能 war entry B2 |
| GEN-011 | B3 | checkpoint 仍有未命中的尾部形状 | 当前 live 的 pending white-peace→WarID 消失→残军 disband 已有即时战后 checkpoint；但“终止动作直接 applied 且无残军”、restore 前历史 anchor 未按最新 restore epoch 截断、以及 generic dirty gameplay 后立刻 planner-blocked 的尾部保存仍未实机触发 | 只有真实 production 路径出现进度丢失时升为 B0/B1；首次 G1 前不为理论形状扩 runner | 记账观察 |
| GEN-012 | B1 | `life-advance` 暂停收尾被连续 public revision 饿死 | `aff784d` 与 `3bd8934` 分别实证一次 fresh retry 仍可 race、public-CAS convergence 可在 speed-five 帧流中饥饿；exact DLL `51fe8cf` 证明 native `pause-map` 自己 fresh-read 并幂等提交。`8efa23f` 仅让 composite owner 绕过该冗余 public gate；正式 run 已从 `578B...5C38` cold restore 跨过旧超时并持续到 `history=2380/date=53203800`，保存 25 个新 checkpoint | 已满足：一次请求、一次 ACK、同 deadline 验证 paused；direct primitive/query/其它 action 保持原 gate。保留两轮 immutable RED，后续只在同故障复发时重开 | 2026-08-27 resolved；blocker-removal production-live |
| GEN-013 | B1→B3 | 长跑 query/history 复制与持久化写放大 | 真实冻结 state 为 79,517,587 bytes；旧 threatened-siege 规划同帧执行 167 条查询，用户观测 121 条查询约 26 分钟。`a8ff95f` first-safe、`7cb0b75` 只读批量持久化及 `79b8d2a → e0688c7 → 9ff04ae` transcript/history 去复制已完成同 checkpoint live A/B。随后 target-only war-entry 修复将同一 literal 中位耗时从 `5.539740s (n=169)` 降到 `1.400889s (n=5)`，起点到新战吞吐约提升 `13.08×`；checkpoint/cleanup 全绿 | 原复制/持久化 B1 与 target-only 热点均已满足；保留不同样本量与端到端 pause/barrier 差异，不把全部吞吐收益归因于一个查询函数。后续只由新的真实 profile 重开 | 2026-08-28 resolved；target-only production-live primitive/loop |
| GEN-014 | B1→B3 | `pause-map` ACK 后未在原窗口观察到 paused | 原 RED 与 `F15D383B...35559` 已冻结；bounded retry 实现后从 `53210760 / 79B71103...85F2` 完成 `12/12` cold revalidation、6 gameplay、2 checkpoints、cleanup 全绿，推进到 `53210904 / 367967CD...C3221`。六次 pause 均一次成功，未命中第二次 retry 分支；后续长跑继续跨过该日期 | 当前 blocker 已解除；仅在同故障真实复发或命中 retry 分支时补 live 覆盖，不为未发生形状阻断 G1 | 2026-08-28 resolved；一般路径 production-live；rare retry B3 live pending |

| GEN-015 | B1 | timeline 控制状态已生效但 semantic snapshot 未到 consumer | 原 resume/pause RED 已冻结。`f1230f6` 将 publish/delivery rejection 暴露到 consumer；fresh diagnostic 实见 8 个 state frame 被拒，最终原因是 pending full ID 被错误当作非负整数而非 signed int32，不是 CK3 未切换 timeline。`cf98648` 修复后从同一 `53211480 / FBC40774...D9E9C` cold replay 成功跨过 life 与 fresh snapshot，随后 `c21c096` canary 连续推进并保存新 checkpoint | 已满足：fresh frame 必须到达 consumer，pause/resume 仍只信真实 semantic state；保留 delivery diagnostic，后续只在相同拒收复发时重开 | 2026-08-28 resolved；state delivery production-live |
| GEN-016 | B1 | pending full ID 的 signed int32 被 consumer 判 malformed | diagnostic run `20260827T181439Z-one-generation-a991f39a` 保留 8 个 rejected state frames；`cf98648` 将除 `-1` sentinel 外的完整 signed int32 全域贯通 Python/C++ query、reply、ACK、planner 与 lifecycle。fresh live 后实见 `instance_id=-2013265918`，typed query available 且无 malformed frame | 同一负 ID 在 snapshot、typed query、reply lifecycle 中逐字保持；`-1` 仍唯一 invalid sentinel | 2026-08-28 resolved；production-live primitive/loop |
| GEN-017 | B1→B2 | `arrange_marriage_interaction` 被 opaque special 分类阻断 | `cf98648` live query 证明 exact stock AI→玩家请求：ID `-2013265918`、四角色齐、无 intermediary、六 option 全未选、accept/reject/block 合法。按 exact-build 原生树，`c21c096` 只为该窄合同增加 reject-only；canary 已 query→reject→旧 full ID 为 null→继续 5 个 visible gameplay，并产生 2 checkpoints/cleanup GREEN | B1 已满足；后续若婚姻质量成为真实问题，再补发送时 `ai_accept`、secondary pair/alliance outcome 并替换 reject-only，不先扩完整婚姻系统 | 2026-08-28 blocker-removal production-live；婚姻效用 B2 |
| GEN-018 | B1 | 一支军队有 contact-free horizon，但另一支可控驻军仍被威胁 | `1048a45` live 证明 stationary `target=current` 在 native reader 返回 `route_unavailable`；`e619219` 改为复用同一 fresh moving horizon 的完整 hostile timelines，按原生闭区间重投影 hold。`12/12` canary 跨过旧帧，正式 run 随后又连续推进 38 日 | 已满足：保留 subject-bound moving proof；stationary row 只使用同 snapshot 完整 hostile timelines；全军 conjunction 后仅推进一日并 paused 重读 | 2026-08-28 resolved；blocker-removal production-live |
| GEN-019 | B1 | CFleet carrier 被误投影为独立 tactical army | 正式 run 中 `150995278` 与 embarked canonical `33554818` 连续 59 日逐省同步；旧 reader 把前者投影为 `regular/empty route`，触发 186 次 `army_not_move_ready` preview、耗时 `572.765s`。exact-build 原生链确认 raw-kind `1` 经 CFleet 间接回到 CArmy 且被 move/contact gate 拒绝 | `ReadArmies` 只发布 raw-kind `0`、有效 `CUnit+0x178 → CArmy` 且 `CArmy+0x124` self-backlink 的 row；fresh canary 中 carrier 出现/preview 均为零，canonical row 保留并推进 | 2026-08-28 resolved；`816442e` production-live |
| GEN-020 | B1 | 所有 exact objective route 都在玩家首跳前发生当前省接触 | `53216424` 的 185 条 route 都先在 `53216448` 与 `117440838@5692` point overlap；`b5865f3` exact-day live 到 endpoint 后仍无 combat/retreat/war transition | 只有全部 conflict 都是不可避免 current-Province point overlap 时才推进一个 exact day，并要求真实 strong transition | 原 planner blocker 已绕过；endpoint postcondition live RED，转 GEN-022 |
| GEN-021 | B1 diagnostic | 预测 conflict hostile 是否已实际进入接触省 | `9b7d254` 增加 proof hostile 实际入省后置条件，但同 checkpoint live 仍无入省；闭区间 ETA 不能冒充 movement/contact 已结算 | 保留 RED；改为读取同日 fresh semantic endpoint，不再猜敌军已经入省 | 诊断假设已被 live 否定；由 GEN-022 接管 |
| GEN-022 | B1 | 日期到达 prediction endpoint，但 movement/contact lifecycle 尚未形成 strong transition | `76cae78` same-date refresh 已 live：revision 前进但双方仍 moving、非 combat/retreat；`4a7d7ce` 只允许一个严格相邻日 follow-up。formal run `20260828T000753Z-one-generation-a09470a0` 已穿过该 gate 并继续至 `53220312` 的独立 GEN-023 | point-overlap marker 后最多再推进一日；只接受 terminal、war set change、subject removed、active combat 或 retreat；无强状态即 RED，禁止第三日 | 2026-08-28 resolved for continuation；`4a7d7ce` production-live loop |
| GEN-023 | B1 | contact-free exact route 缺 required advance literal | 在 `53220312`，ArmyID `117440751→3610` 的 exact horizon 已证明 `53220312→53220336` contact-free，但 backend 未广告 required advance literal；`b4a1cc4` 修正 capability/subject-scope 映射后，从同 checkpoint 穿过旧帧 | 已满足：只有 fresh timed subject 与其它 moving/stationary safe rows 的全局 conjunction 才广告该一日 literal；后续 sibling 缺口转 GEN-024 | 2026-08-28 resolved；blocker-removal production-live |
| GEN-024 | B1 | 同一全局推进中 moving sibling 缺独立 fresh proof | GEN-023 首次修复后，另一支 moving sibling 的 current Province 恰落在 hostile closed-horizon endpoint，不能借主 subject 的 proof 放行。`9be9571` 改为逐 moving army 收集同 snapshot/date/native revision、同 hostile scope 的 fresh exact proof | 全军 conjunction 中每支 moving army 都有自己的 exact proof；多份 proof 只共同授权一个全局日。formal continuation 已穿过旧帧并运行至战争结束 | 2026-08-28 resolved；blocker-removal production-live |
| GEN-025 | B1 | primary defender raise 后被完整退出证据门自锁 | `WarID=100663382`、day 0、score 0、primary defender；raise 已生成 gathering ArmyID `100663369`，旧 planner 却要求 terms + opponent acceptance + campaign forecast 才继续。exact-build 原生树证明普通 continue 不消费这些退出输入；同时冻结 query 证明 `0xC569F0` 的 bool 是 `player_victory`，旧 defender query/write 极性会互换投降和胜利 context | 只放行明确 `primary=true` 回到既有 route/tactical OODA；退出动作仍保留自身证据门。query/surrender/enforce 恒用 player-relative `false/false/true`，以 score-0 defender golden 与 defender 写动作回归锁定；从 `53231232 / DF7DBFF8...9005E` cold revalidate | `58f647f` static-ready；fresh native 39/39、Python 1408/skipped3；live pending |
| GEN-026 | B1 harness | plan→execute 间 paused snapshot revision 收敛 | formal turn 38 的只读 war-entry query 以 expected `517` 在执行入口读到 `518`；gate 位于 request allocation/send 前，零 native submission。旧 opaque 分类仍丢弃最新 `53241528 / 1AEC...B61548`，回退 seed 会额外损失 429 游戏日 | 窄 typed pre-submit mismatch；runner 最多一次 fresh readiness、身份复核与 whole-turn replan，并更新本轮 before。第二次漂移停止；typed zero-submit 与已知 non-save failure 保留 durable anchor，未知 save/step 仍失效 | `e5a3f09` static-ready；Python 1412/skipped3；fresh formal continuation running |
| GEN-027 | B1→吞吐 P0 | embark route 边界的 arrival timeline unavailable；旧路线又要求逐日 query/pause | 原 RED 保留：`53256000` 的共享首边为 `progress=0 / cached speed=0 / recalculated speed=0`，full helper 不可直接使用。exact fallback 与独立显式 route sentinel 已实现；cold run `20260828T080926Z-one-generation-9e0ac8cb` 连续 5 个 speed-3 route arm 共推进 44 日，全部零 external/intermediate pause、零 running RQ/overshoot，并在真实 contact 同日停表转入 battle OODA | 已满足；`78d46b4` 使 production 默认广告 `committed_route_sentinel_live_ready` 与 canonical composite。保留严格 scope/subject/target/bound、完整 watch、`combat_count=0`；Python `1506/3 skipped`、native `39/39`，后续只在相同边界真实复发时重开 | 2026-08-28 resolved；committed-route production-live loop |
| GEN-028 | B1 + 吞吐 P0 | 全局 warscore 下降被错误绑定为玩家当前省战败，且多战争重复逐日终战 RQ | formal run `ca52af74` 在 history `5739` 暴露 WarID `33554565` 因远端 occupation `50→16`、本地敌军为零，却错误封锁 objective `2635`；同期为 `337 query / 148 gameplay` | 本地 defeat memory 现只在真实同省非撤退 hostile/contact 时写入；negative termination 仅复用 7 日且在 `claim_cb` 第 365 日提前到期。cold canary `90d3cf79` 已从原 RED 帧连续完成 20 个 7 日 stationary arms并到 `53266944`，证明旧路线锁死与逐日暂停均已跨过 | 2026-08-28 resolved；blocker-removal live，stationary canary 由 GEN-029 接续 |
| GEN-029 | B1 harness + 吞吐 P0 | stationary sentinel 漏接 ordinary player-decision boundary，导致事件已阻断日期却继续空等 | 历史 RED `90d3cf79 / 71e3b7c1 / e8cec411` 将根因固定为 `53267040` 的 event 47。最小包新增 generation-bound cancel、独立 player-decision stop、一次 fresh-bound pause 与 modal checkpoint 延迟，并撤销专用 60 秒 wait。cold live `6421f80c` 在同日捕获 event 47，下一回合选择 option 1、随后才保存 checkpoint，再继续到 `53270568`；`100/100`、cleanup/tree-gone GREEN | 已满足：事件/pending 立即交回既有 policy；不伪造 sentinel terminal，不改变战争意愿；同代 cancel/status、paused decision identity、零 modal save 与后续继续均有 live 证据 | 2026-08-28 resolved；blocker-removal production-live，report `DC66418A...732C1C` |
| GEN-030 | B1 harness | player decision 与 native sentinel 在 deadline 同日转移状态时仍盲目 cancel | 历史 RED `cbbd3fab` 在 `53278752` 同时观察 event 51 与七日 deadline。`9186bfa3` 的 turn 8 精确重现同日边界：generation 2 为正常 `triggered`，`date_deadline / ticks=7 / intermediate pause=0 / overshoot=0`；composite 没有 cancel，返回 `player_decision`，随后 query 并选择 event option 1，旧 event 消失且日期不变 | 已满足：同代 armed 走 cancel→idle；同代正常 triggered 保留完整 stop 证明后免 cancel；failed/无证明 idle 仍拒绝；事件优先级与战争策略均未改变 | 2026-08-28 resolved；exact same-day blocker-removal production-live，report `2C764FEC...6C83` |
| GEN-031 | B1 native capability | war-termination options query 未绑定已发布 paused revision | 历史 RED `33876238` 在 `53278752 / native:25 / revision=26` 的第二个 WarID query 发生 row mismatch。`fc0f878` 让 native handler 消费 expected revision，并在 admission/completion 进行完整 snapshot sandwich；只在稳定成功后推进 query sequence。Python 只把明确 stale/admission-changed/completion-changed 的零写入拒绝映射为既有一次 whole-turn replan，真实四字段 mismatch 继续硬 RED并留最小 diff | `9186bfa3` turn 11/12 已在同一 paused native revision 26 连续成功查询 WarID `83886203 / 134217852`，跨过原失败边界；后续查询至 turn 20 持续成功，cleanup 全绿 | 2026-08-28 resolved；`fc0f878` blocker-removal production-live，report `2C764FEC...6C83` |
| GEN-032 | B1 | 玩家自然死亡先于 tactical sentinel 正常 stop，terminal 边界不能稳定化 | 三次早期 attempt 先关闭 terminal 识别与日期漂移；formal G2 attempt 01 又证明同一 bound episode 的 terminal surface 在 pause 服务期间可从死亡角色演化为继承人。最终合同只固定 bridge/connection/episode owner；played-character、alive 与 `dead→changed` terminal reason 可单调演化。event/pending interaction 的 exact identity 不变 | formal G2 attempt 03 已在相同生产边界返回 `death-terminal`，随后继续完成 GEN-009；driver 回归 `196 passed + 212 subtests`，相关聚合 `468 passed + 287 subtests` | 2026-08-30 resolved；terminal sentinel blocker-removal production-live；边界由 G2 live 再校准 |
| GEN-033 | B1（G2） | 新接触战斗的 full CombatID/BattleResultID 为负，被旧 consumer 当成未物化 | attempts 08/09 在 `53291904` 分别报 `active_combat_identity_failed` / `subject_combat_id_invalid`；attempt10 唯一一次 `+24h` 后仍因“缺 positive CombatID”停止。exact-build 证明两类 ID 均为 opaque signed full dword、low24 仅选槽、`-1` 唯一 missing。attempt11 先穿过 CombatID 后暴露 BattleResultID，同一修复后 attempt12 双查询稳定读到 `-2147483647 / -2046820351` | signed identity 原样贯穿 reader、wire、contracts、planner literal、battle action/transition/terminal journal 与 sentinel；同 checkpoint 做真实 action 后 paused requery 并保存 durable checkpoint | 2026-08-31 resolved；attempt16 production-live loop slice，完整 G2 第二寿命仍进行中 |
| GEN-034 | B1（G2） | Raiktor 三路战争退出仍缺同帧完整决策 | R459 已在 WarID `33554473` 上完成一次 typed surrender，证明 source-specific 兵力 `3000→0`、persisted truce expiry `53227656`、checkpoint 与 cleanup；R471 又在 paused `native:3` 两次读取玩家 `13075500000`、对手 `16770900000`、ratio `128262/100000`。GEN-034-A 已把该双查询转换为 v2 measured-power dominance certificate，receipt `AB0DB567...E0569`，并保持 forecast/utility/action false。`raiktor_exit_budget_v1.json` 的 profile `1.0.0` 与 GREEN 收据 `BB20D872...7981` 闭合 B。早期 index `9/10`、root shape、Truce vtable 与“source/pre/loss=false”均已被后续证据取代 | 只做余下两包：C 同一 paused frame 取得 white-peace terms/utility comparison；D 三路 recommendation 后只提交一次 action，并在下一 paused frame 验证 WarID/loss/truce/resources、保存和冷恢复。R459/R471 输入直接复用；不得重跑旧 ABI 枚举或扩成长跑 | **unresolved，G2-M0 in progress（2/4 子包完成）**；当前全局 G2 为 `0/8`；campaign dominance 与 strategy profile complete，white-peace/integrated decision 待闭合 |

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
3. `G2 repeatable`：同一合同至少跨入一个新 episode，精确 seed 重载后完成可见 gameplay 与 durable checkpoint。首个 fixed-seed gate
   已 GREEN；第二个完整寿命和多 seed/ruler 矩阵仍待扩展。
4. `G3 broadened`：增加 ruler、政府、战争/和平起点与 enabled-feature 代表场景。

本周的 G1 与首个 G2 gate 已取得；后续按真实 blocker 扩展第二寿命与 G3 场景，不重复同 seed 验证来替代玩法增量。

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

## 2026-08-27 20:13：GEN-012 pause revision 饥饿根因

- `3bd8934` 的正式续跑 `20260827T115837Z-one-generation-9bed68f0` 已 production-revalidate 前一修复并继续同一 episode：完成
  `47/48` turns、`23` gameplay turns、`23` visible gameplay turns 与 `7` checkpoints；随后第 48 回合以
  `native life-advance pause-map revision convergence timed out` 停止。角色 `29829` 仍活、无 terminal，cleanup 全绿。
- 权威 `report.json` 为 `225,174` bytes、SHA-256
  `FF8D78C5E0D1CBA6D85BEEE6D0D752AA844EEFD4E9DF896E02FC74E255A470A2`；`first-blocker.json` 为 `3,965`
  bytes、SHA-256 `6DDD926CCFADA821121A987F2103335A758EF3CCFD53944940EFC11FF2149C97`。driver state history `2175`
  是失败的 `life-advance`；此前 `2173` 已成功推进至 `date_raw=53199216`，但尚未达到三次推进 checkpoint cadence。
- 最新显式可信恢复点为 turn 42、`date_raw=53199144`、history `2169`、size `74,009,701`、SHA-256
  `578B02896FBCD04BD96212C8B1E3A337A689EFC1C3753B5060013717D7B95C38`。退出前 CK3 的普通 `last_save/autosave`
  已在失败窗口写成另一份 `DFA62E1D...40B3B`，没有匹配的显式 driver checkpoint anchor，故不得用它替代 `xar_checkpoint.ck3`；
  轮转的 `autosave_1.ck3` 则与显式 checkpoint 逐字节一致，可作为独立物理互证。
- exact production DLL commit `51fe8cf` 的命令分发证明 `pause-map` 不解析或比较 JSON `expected_revision`，而是直接调用
  `SubmitPauseMap`；后者 fresh-read 当前 CK3，paused 时幂等返回，否则构造并入队 `paused=1`。因此连续 Python public-revision
  equality 重试没有增加 native 正确性，只会在 speed-five 帧流中饥饿。真实故障与 exact-build 代码共同构成必要性证据。
- 下一最小修复只改 composite-owned `_pause_life_advance`：fresh-read 后若已 paused 就采用；否则调用同一个 primitive sender 但不做
  Python expected-public-revision 比较，仍发送 fresh native revision 作为 wire 审计字段，且只允许一次真实请求、一次 action 记录与
  同 deadline paused 验证。direct `pause-map`、所有 query、其它 primitive/planner/AI policy 均不变；没有证据支持更广扩张。
- blocker-removal 已 static-ready：连续 running revision、event/speed drift、sender refresh 时自动暂停、单 deadline、ACK 后不重提、
  non-revision 错误直抛，以及 direct stale `pause-map` 仍被拒绝均有回归。聚焦为 `10 passed, 2 subtests passed`，完整 driver 为
  `128 passed, 102 subtests passed`，auto-run + gameplay bridge 为 `201 passed, 48 subtests passed`；全 unit suite 为
  `1318 passed, 2 skipped, 882 subtests passed`。`py_compile` 与 `git diff --check` GREEN；仍须从 `578B...5C38` cold restore
  实机越过该 10 秒边界并形成更新 checkpoint，才能关闭 `GEN-012`。

## 2026-08-27 21:05：`8efa23f` production revalidation 与正式长跑续行

- `origin/master` 与干净主线 HEAD 均为 `8efa23f18c23dee0aff05b5606eb70de7bd6ca34`。本轮已推送链完整包含：
  `7a89c58` production continuation、`4b82d5b` 必要性与成本规则、`e23abe2` 两日 battle-hold 反例、`0848d61` 最窄
  correlated two-day 接纳、`726a1c0` committed life-score 合同、`75c67d2` 首次 revision blocker 文档，以及依真实长跑递进的
  `aff784d`、`3bd8934`、`8efa23f` 三个 pause 修复。没有为理论风险扩张 scope。
- `aff784d` attempt `20260827T112207Z-one-generation-3c7aa5e2` 的 immutable RED 是 `106/107` turns、`53` gameplay、
  `17` checkpoints 后 `expected 183, current 185`；report/blocker SHA 为 `BC10E3DE...DBF42DB4` / `8FC4B407...B45028B`，
  最新可信恢复点 `history=2119 / date_raw=53198376 / 73,968,716 bytes / AE73EFE1...C75B42`。
- `3bd8934` attempt `20260827T115837Z-one-generation-9bed68f0` 的 immutable RED 是 `47/48` turns、`23` gameplay、
  `7` checkpoints 后 10 秒 convergence timeout；report/blocker SHA 为 `FF8D78C5...55A470A2` / `6DDD926C...2149C97`，
  最新显式恢复点 `history=2169 / date_raw=53199144 / 74,009,701 bytes / 578B0289...5C38`。两轮角色 `29829`、episode
  `native-29829-ee172aa720db` 均未改变、无 terminal、cleanup 全绿；它们是已解除 blocker 的历史证据，不得删除或改写成 GREEN。
- 正式 run `20260827T122055Z-one-generation-aebccf6f` 使用干净 runtime `8efa23f` 与 exact DLL `51fe8cf`，从
  `578B0289...5C38` cold restore，按 `--max-turns 50000 --timeout 604800 --readiness-timeout 300
  --checkpoint-every-advances 3` 运行。`history=2176 / date_raw=53199504` 已越过旧 10 秒边界，随后 checkpoint 持续成功；
  `GEN-012` 因此从 static-ready 升为 blocker-removal `production-live` 并关闭。
- 21:05 只读快照的最后 durable checkpoint 为 `history=2380 / date_raw=53203800 / 75,195,047 bytes / SHA-256
  A75EF923D369E9E86DDCC20C6B59E9F104F03E2462C98E3FEF62BB197E0AA3A4`，之后 `history=2382` 又成功 life-advance 至
  `53203848`。从 restore 后 command history 推导当前 `186` successful / `109` gameplay turns 与 `25` checkpoints；runner 的
  `report.json` 尚未 finalize，故最终计数以后续报告为准。角色仍存活，terminal/blocker absent，runner/CK3 正在运行，尚无 cleanup
  或 G1 结论。
- 自然死亡后不能立即结算：必须继续等待琉焰卿 Mod 发布本次 `ready=true / commit_serial=1` committed settlement，并把
  `terminal-settlement.json.one_life_settlement.final_score` 记录为“人生分数”。它须与顶层 `score`、
  `recorded_episode.score` 严格相等，且 record persistence、cross-run record、零继承人 gameplay 与 cleanup 全绿，才能标 G1。

## 2026-08-28 00:32：GEN-013 查询/复制放大解除与最新恢复点

- 三轮 live A/B 都从 `date_raw=53209560`、SHA-256
  `A8DD4034C32856B8D1E05D6B834BBBF3C51AA74DA038BB22A0CA23A998AD76CF` 的同一 immutable checkpoint 起跑，
  因而能把代码差异与战局差异分开。`79b8d2a`、`e0688c7`、`9ff04ae` 的 turn-loop 运行段分别为
  `48.134s / 44.875s / 24.684s`。
- `79b8d2a` 首/尾 query 为 `3.398s / 2.579s`、life 为 `5.065s / 4.600s`；`e0688c7` 分别为
  `3.317s / 2.516s` 与 `4.583s / 4.111s`；`9ff04ae` query 已降至约 `0.050–0.068s`，life 首/尾仍为
  `4.569s / 3.643s`。复制账本对应为 life `9→1→0`、planning `1→0`（约 `600.637→5.813ms`）、termination
  query 内部 `3→0`（约 `1815.527→1.852ms`）。因此只关闭已实证的 query/history B1；剩余 native life latency 降为 B3，
  不自动派生新优化任务。
- 最新 `9ff04ae` 轮为 `12/12` turns、6 gameplay、6 queries、2 checkpoints。六个 gameplay turn 全部是
  `player_tactical / speed=1 / elapsed_days=1`，每次均回到 paused；cleanup 全绿。最终 checkpoint 为
  `date_raw=53209704`、SHA-256 `39379D0224788198FECCCA82DA4B7B7257DB7E1AEE6B3750F62AA845E312678A`，
  driver-state SHA-256 为 `D47DAA...BDA`。
- speed 3 仍未 production-live：同一玩家 12-hop route 与敌军追尾形状持续命中 tactical gate，没有
  `remote_enemy_route` 起始帧、speed-3 elapsed 或 overshoot evidence。这不会重开 GEN-013，也不能靠人为取消路线制造样本；恢复
  正式 G1 后等待战局自然出现合法帧。
- 最新实现全量 unit 为 `1341 passed, 2 skipped, 900 subtests passed`，独立审查 `PASS`。这些测试与三轮 A/B 只证明性能路径、
  checkpoint 与 cleanup，没有替代 `GEN-006` 的自然死亡和琉焰卿 committed life-score gate。

## 2026-08-28 00:53：GEN-014 pause ACK 后观测窗口

- 正式 `9ff04ae` run `20260827T163217Z-one-generation-ace7cbcf` 从 `39379D02...12678A` 恢复后完成
  `85/86` turns：43 queries、42 gameplay、14 checkpoints，推进至 `date_raw=53210712`。随后一次
  `life-advance` 在 pre-action paused frame 后报 `native life-advance did not observe the paused map`。`report.json` SHA-256
  为 `49D2A8BB8C15D638046D67833A68FA08493CF0632ECECFC7F79C846388B50808`，`first-blocker.json` SHA-256 为
  `A0BD8C79E32EA1FA34C42DF8A293F715D93A9D556B24AF0B7DF561F04B4FA484`；角色 `29829` 仍活，cleanup 全绿。
- 这不是 GEN-012 的 public-revision pre-submit starvation：当前 composite 已用 `expected_revision=None`，故错误只能位于首次
  `pause-map` ACK 之后、真实 paused frame 之前。artifact 没有保存 ACK status 或窗口内各帧，不能声称 native queue drop；
  `GEN-014` 只记录已观察到的 post-ACK timeout。
- driver history 明确 index `2960` 是 `date_raw=53210712 / F15D383B...35559` 的成功 checkpoint，之后只有一条成功只读 query 与
  失败 life，无新 save；磁盘 checkpoint bytes 与 metadata 相符。opaque `auto_turn` 的通用 invalidation 只是 runner 无法看到内部
  selected step 的保守标记，不是本文件被污染的实证。该 checkpoint、匹配 driver state `D272510F...FA323` 与 RED artifacts 已另行冻结。
- 未修改 `9ff04ae` 从同一个 `F15D383B...35559` 冷恢复的 4-turn 重放没有复现：两次 query、两次 speed-one life 全部成功，
  每次仅推进一日并回到 paused；最终 checkpoint 为 `date_raw=53210760 / 79B71103...85F2`，cleanup 全绿。正式续跑优先使用该更新
  anchor；F15D 保留为 fallback。该 non-repro 只证明瞬时形状，不把原 RED 改写为 GREEN。
- blocker-removal 只扩 composite pause owner：首次 ACK 后先观察 1 秒；同 bridge generation、episode、map-ready、speed/event
  owner 仍 running 时，在原 10 秒绝对 deadline 内恰好补交一次 exact handler 已证明幂等的 `pause-map`。第二次仍须等待真实
  `paused=true`，没有第三次、不重置 deadline、不改 direct primitive/query。错误会记录 attempt count、每次 ACK status 与最后
  revision/date/speed/paused；第二次 request 自身失败也保留第一次 ACK。
  当前聚焦 `12 passed, 141 deselected, 10 subtests passed`、完整 driver `153 passed, 128 subtests passed`、全 unit
  `1344 passed, 2 skipped, 908 subtests passed`，独立复审 PASS；live cold revalidation 完成前维持 `static-ready / B1 open`。

## 2026-08-28 01:19：GEN-015 timeline state publication

- `0ceb7d8` 先从 `53210760 / 79B71103...85F2` 完成 production revalidation：`12/12` turns、6 gameplay、2 checkpoints，
  每次只推进一日并回到 paused；cleanup 全绿。最新 checkpoint 当时为 `53210904 / 367967CD...C3221`。六次 pause 均只提交一次，
  因而这是一般路径 live GREEN，不声称命中第二次 retry。
- 随后的正式 run `20260827T171107Z-one-generation-ee8ac4b9` 从该点完成 `51/52` turns、25 gameplay 与 8 checkpoints，
  然后在 `date_raw=53211504` 的 paused pre-action frame 后报 `native life-advance did not observe the running map`。报告 SHA-256
  `52CED5F755F529AA96A358603397E24B800F134779575718272D80049E4C8419`，blocker SHA-256
  `C9BFA9E66006046DF76CE85FB9ECBE80D50145937A53C01DEF7963E06A782114`；角色 `29829` 存活，cleanup 全绿。游戏日志在失败窗口内
  记录 `paused=true -> paused=false`，证明 resume 已由 CK3 应用。
- profile 上的最后 checkpoint `date_raw=53211480 / FBC4077473BD48A76F500D6485950F0DBD7841E9AA71AADD67A70044C3AD9E9C`
  与 driver-state history index `3038` 完全匹配。`3039..3042` 是 checkpoint 后尾，cold restore 会截断；runner 的旧 seed fallback 是
  opaque auto-turn 的保守分类，不是 checkpoint 损坏。
- 未修改 `0ceb7d8` 从该 anchor 的独立 cold replay 成功恢复同一角色/episode，并把首个 life 从 `53211480` 推进到 `53211504`；随后
  pause ACK 为 `submitted -> already_paused`，游戏日志确认 `paused=false -> paused=true`，但 Python 最终仍停在
  `native_revision=5 / paused=false`。replay blocker SHA-256 为
  `D49E84C10A686C69C59491419526F091D2CAC530653042B4DF4DB4274C2002CC1`，cleanup 全绿。这证明 GEN-014 的一次 retry 尚不能修补已由
  bridge 去重的 consumer state frame，也把正式 resume 与 replay pause 统一为 GEN-015。
- exact-build `PublishSnapshot` 在内部 `previous_snapshot == fresh snapshot` 时去重，且该 equality 没有 consumer adoption ACK。
  最小修复只在 exact handler 返回 `already_paused/already_running` 时清掉 previous 后执行现有 fresh publish；composite resume 与 pause
  对称地在原 10 秒 deadline、同 PID/generation/episode/map/speed/event owner 内最多补交一次。两边最终仍必须观察真实 state frame，
  不信 ACK，不扩展其它 action 或协议。
- 用户要求继续压低每游戏日耗时。冻结 80.7 MB production driver-state 的独立基准表明：旧 barrier 中位数 `0.944s`，其中
  `deepcopy=0.544s`；在锁内直接编码 compact JSON bytes 后为 `0.234s`，状态文件缩小约 `52.1%`，单日预计节省 `0.710s`。
  该改动不变更 schema/version/API/恢复语义，已有独立全 unit 与并发审查 PASS；仍须移植到当前 HEAD 并做 fresh-DLL live A/B。
- 01:48 static gate 已闭合：GEN-015 与 compact persistence 的两个独立审阅均 PASS；全量 Python
  `1350 passed, 2 skipped, 908 subtests passed`。fresh Release `xar-native-gen015-20260828T0145Z` 完成 `37/37` CTest 与
  `ck3_11906.hpp` dependency gate；DLL/injector SHA-256 为 `50227D28...831F2` / `2F6CEB43...35B5C`。因此实现为
  `static-ready`，但在该 fresh DLL 从 `53211480 / FBC40774...D9E9C` 命中真实 frame/retry 前，GEN-015 继续保持 B1 open，
  不写 production-live。

## 2026-08-28 03:23：GEN-015/016/017 实机解除并恢复正式长跑

- 战斗速度研究以独立提交 `5f8687a` 覆盖 `1/2/3/4/5` 全档：五档都执行同一 CK3 逐日 movement/contact/combat
  计算链，高倍速只压缩外部观测/决策窗口。该专题仍是 `static-confirmed / live pending`，没有借静态矩阵宣称 speed 2–5
  已进入 production selector。
- `f1230f6` diagnostic run：
  `C:\Users\xenoa\AppData\Local\Temp\xar-delivery-diag-f1230f6-state\runs\20260827T181439Z-one-generation-a991f39a\report.json`
  （SHA-256 `A6827430C6B37D1BFA7F11F08E10831B92023C34F53F489C8F803EE87E52A3AB`）记录 8 个到达 native driver、
  却被 consumer 拒绝的 state frames。最后帧仍显示游戏在 `date_raw=53211600 / speed=1 / paused=false` 运行；具体拒绝原因为
  `native pending_character_interaction is malformed`。这把 GEN-015 从笼统 timeline 丢帧收窄为 pending ID 消费合同，不把 ACK
  或游戏日志单独当成功。
- `cf98648` 把 pending `instance_id` 改回 exact wire 的完整 signed int32：`-1` 是唯一 invalid sentinel，零和其它负数均为
  结构合法。全量 Python 为 `1352 passed, 2 skipped, 913 subtests passed`；fresh native build 为 `37/37` CTest，DLL SHA-256
  `67B7231B55FB55788D1069C984589B91ABC0D25F8540B7E42FF7BFC4703CB535`。fresh live report：
  `C:\Users\xenoa\AppData\Local\Temp\xar-signed-pending-cf98648-state\runs\20260827T184232Z-one-generation-25fe58db\report.json`
  （SHA-256 `0D2BBFA638ED2BEC3F27D754DE5B64AE931F2627D4EB51FBC3F03EF125CC77D0`）已真实读到
  `instance_id=-2013265918`，typed pending query 为 available，未再产生 malformed state frame。该 run 随后因尚未分类的
  `arrange_marriage_interaction` 正确 fail-closed；`first-blocker.json` SHA-256
  `A8DF58EBF6AB25EDF633BFA6596A33ECBB8B6901E9A156F8A79FF5A6951F64D3`，cleanup 全绿。
- exact-build 婚姻原生树确认该请求是 stock AI→本地玩家的 marriage special，而不是 war payload。当前观测缺少发送时
  `ai_accept` raw/breakdown、secondary pair 与 alliance 后置语义；因此 `c21c096` 没有扩通用婚姻策略，只对本次实见合同提供
  definition-bound reject-only：direct recipient、四角色完整、无 intermediary、六 option 全未选、reject 原生合法且命令可达。
  拒绝会留下五年 `player_declined_marriage`，所以明确是 G1 blocker-removal，不声称原生等价或语义最优。
- `c21c096` canary：
  `C:\Users\xenoa\AppData\Local\Temp\xar-marriage-reject-c21c096-state\runs\20260827T191804Z-one-generation-8c116e3e\report.json`
  （SHA-256 `3980E4A2CD7F140A98488184C2095B3B41EF92EC80505B837177200705DD3973`）为 `12/12` turns，负 ID typed
  query→reject submitted→旧 full ID 为 null，并继续取得 5 个 visible gameplay；2 个 checkpoint 均成功，最终为
  `date_raw=53211576 / SHA-256 EEBE541E5C6CA8372E95F294FA3C93B9E7A423D8E8281EE7E0FE9BC4CFB0B57B`，CharacterID
  `29829` 仍活且 cleanup 全绿。结果是 `bounded_incomplete`，只证明三个 blocker 已跨过，不是 G1。
- 正式 run `20260827T192055Z-one-generation-1d8c0f50` 已从上述 EEBE checkpoint 归档 immutable seed 后，以
  `--max-turns 50000 --timeout 604800 --readiness-timeout 300 --checkpoint-every-advances 3` 启动。当前 report 仅为
  `status=seed_archived / outcome=in_progress / finalized=false`；不得提前填写最终 turns、cleanup、terminal 或人生分数。只有
  CharacterID `29829` 自然死亡后继续等到琉焰卿 committed settlement，三处人生分数与全部 qualification gates 一致，才标 G1。

## 2026-08-28 03:26：GEN-018 多军队全局 contact horizon

- 上一节记录的正式 run 已于 `2026-08-28 03:25`（Asia/Shanghai）finalize；不能继续称为 in progress。report：
  `C:\Users\xenoa\AppData\Local\Temp\xar-marriage-reject-c21c096-state\runs\20260827T192055Z-one-generation-1d8c0f50\report.json`，
  SHA-256 `FC7D4E5069C84A4D10A3E5359A387C3F9BD5CD422FFE20D45ACCEB0ADDD4DF90`；`first-blocker.json` SHA-256
  `AB9FDD76D0251070F1A12AAE8CAE51C2CB23B0CA675EF229DF42724C35500AB0`。
- run 为 `104/105` successful turns：54 query、50 gameplay，其中 49 个 visible gameplay；16 个 periodic checkpoint 全部成功。
  最后 durable checkpoint 为 `date_raw=53212728 / history=3172 / SHA-256
  ED3675867A2780CCD0FD9B77AE80E3BDDFC40EEA47879224914470001732E2A7`，`recoverable_from_checkpoint=true`。
  CharacterID `29829` 仍活、settlement 为 `not_terminal`，managed cleanup 全绿。
- blocker 是 planning phase `native_war_route_contact_horizon_global_blocked`，要求
  `complete-global-route-contact-horizon`。ArmyID `33554818` 虽已有到 Province `5715` 的一日安全 contact horizon，但 ArmyID
  `150995278` 仍作为 Province `8658` 的可控 regular 驻军被判 threatened；后者不在战斗/撤退、无 route，且 move target
  不可观测。planner 没有选择动作，因此这是新的真实 B1，不是 bound、cleanup 或婚姻回归。
- 下一施工必须先按 exact-build 原生 AI 账本闭合该多军队/驻军分支，再做解除当前 blocker 的最小可验证动作；不因本次失败
  扩展无实证的安全门禁。修复后从 ED367586 checkpoint 继续同一角色/episode，G1 与人生分数仍未完成。

## 2026-08-28 05:11：GEN-018 live 关闭与 GEN-019 canonical tactical identity

- `1048a45` 的第一次 cold replay 没有伪造成功：subject `150995278 → current province` 的 exact native query 明确返回
  `route_unavailable`。`e619219` 因此只复用同 snapshot、fresh moving horizon 已经发布的完整 hostile timelines，按同一闭区间
  规则重投影 stationary hold。canary
  `C:\Users\xenoa\AppData\Local\Temp\xar-marriage-reject-c21c096-state\runs\20260827T201025Z-one-generation-03f57fda`
  为 `12/12`、4 gameplay、2 checkpoints；report / bound SHA-256
  `95B33802F9F3DAD4673CEF7B5F9408175FFC0468946EDB6696A947F98133E9CB / 5150DF839DE30C80B86D8513874608B5D815604A1418D0995CB446F5230B2783`，
  cleanup GREEN。随后正式 run 又推进 38 日，GEN-018 关闭。
- 正式 run
  `C:\Users\xenoa\AppData\Local\Temp\xar-marriage-reject-c21c096-state\runs\20260827T201247Z-one-generation-c1cdfbc7`
  为 `301/302` successful turns、77 query、224 gameplay、38 visible gameplay、12 checkpoints、`940.429s`；report /
  blocker SHA-256 为
  `C011A2B624FF5EF4333F4FD1AE51A0BA6B942A4C47A99E1D912635C5405DD226 / 1BF4F6668B4D4396B174504DF791315366349DA8B395B72807866D573A735A87`。
  最新 durable checkpoint 是 `date_raw=53213688 / history=3308 / b60348da223585995b5e1cf1a022180d0f3d89cad6e4094f66da107c608324f1`；
  角色存活、cleanup GREEN。
- GEN-019 的行为证据：`150995278` 自 `53212320` 起与 `33554818` 连续 59 日沿
  `8651→1038→1037→8658→1017→942→1111→8665→947→8668→950→951` 同步；只有 `33554818` 收到 move，前者
  route 始终为空。随后正好 186 次 preview 全为 `army_not_move_ready`，总计 `572.765s`。这不是 186 条真实候选路线，而是同一
  non-orderable carrier 的扫描放大。
- exact-build `ck3.exe` SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。原生链：CUnit raw-kind `0` 用
  `+0x178 → CArmy`，raw-kind `1` 用 `+0x17C → CFleet → +0x1C CArmy`；CArmy `+0x124` 给出 canonical CUnit。
  `CanArmyUseMoveMode` 与 contact queue 明确拒绝 kind 非零；`GetUnitState` 不检查 kind，故 `regular` 不能证明可下令。正式枚举名
  仍未知，文档只使用 raw-kind 描述。
- `816442e` 只发布 raw-kind `0`、generation-valid CArmy 且 self-backlink 的 tactical row；不扩通用 fleet/attachment schema。
  全量 Python `1374 passed, 2 skipped, 915 subtests passed`，fresh native `37/37`；DLL SHA-256
  `E66E923530833160DC256F3E2E66B9D7E0DB42F26CD310F4C774DD3A02818573`。独立只读复核确认 raw-kind/CFleet/backlink
  与原生 move/contact gate 一致。
- fresh cold canary
  `C:\Users\xenoa\AppData\Local\Temp\xar-marriage-reject-c21c096-state\runs\20260827T210853Z-one-generation-19717952`
  为 `12/12` turns、7 query、5 gameplay、2 checkpoints，推进到 `53213808`；report / bound SHA-256
  `7BB967D2ED60E7003A7FF6037AA10E923BA4EF8F0D74047C238286B2982B1AC5 / 7A7C6BD63D437D95EFEFA85DEA7A3B453CDC089A283C3C98C1CB21552D96C233`。
  history `3309..3323` 对 `150995278` 的出现/preview 都是 0，`33554818` 仍完成两次 proof-bound advance；最终 checkpoint
  `467CB119404AAB2FA401DE95DBE17600A3E269B444D68CBCD7A1D48B8D50A441`，paused、map-ready、角色存活与 cleanup 全绿。
  结果是可恢复 `bounded_incomplete`，不是 G1；下一步从该 anchor 继续直到自然死亡与琉焰卿 committed 人生分数。

## 2026-08-28 08:28：GEN-020→023 unavoidable-contact endpoint

- formal run `20260827T221605Z-one-generation-f02c81cb` 为 `676/677` successful turns、296 gameplay、
  110 visible gameplay、36 checkpoints；report / first-blocker SHA-256 为
  `231FAF47A6F6F4B29EE5F508D36F50D0B6EAF0DED426614E051C274C9963A924 /`
  `4B93EE56EC680C130F1D28351598E2D5AB842C5EBA75A2B0CFE3967756AADED4`。durable checkpoint 为
  `date_raw=53216400 / history=3661 / 26298014ACAD7E121FEE6618D5AE4AFFC1A52B6B6ED988A51B3E6D5DB8AA4383`；
  角色 `29829` 存活、cleanup GREEN。`53216424` 的 subject `33554818@5692` 要到 `53216688` 才完成首跳，而敌军
  `117440838` 在 `53216448` 到达 `5692`；全部 185 条 objective route 都先命中这个 point overlap。
- `0ec7e2f` 先冻结 exact-build 原生树与反制边界；`b5865f3` 只实现 proof-bound unavoidable exact-day。live
  `20260827T225828Z-one-generation-e74fb9df` 精确 `53216400→53216424→53216448` 后仍无 strong transition，
  report / blocker SHA-256 为
  `0CAA13221A470D71496ACE49B6C1C43E0260F002C13ACAB510C05F64EF06791E /`
  `A4EE8434F37293F8C96F9DB1C69C7CEF8866EBCC4CB45EB3EDE440F01F62925A`。
- `9b7d254` 加入 conflict hostile 实际入省观测；live `20260827T231856Z-one-generation-2318df2a` 仍 RED，
  report / blocker SHA-256 为
  `5E67925F38D85D068131914254495603480156F4FCB2F7ED899313471DA4A079 /`
  `F495A83251BD346C96481668C6E007C5C90D753D0121492E59146FEB4536B7EED`。这否定了“最后已发布帧里敌军已经进入 5692”；
  ETA 闭区间 endpoint 只是预测边界。
- `76cae78` 增加一次幂等 same-date paused refresh 与完整失败 evidence。formal run
  `20260827T234150Z-one-generation-46069983` 的 refresh ACK 为 `already_paused`，public/native revision
  `10/9→11/10`；refresh 后 subject 仍 `33554818@5692` moving、hostile 仍 `117440838@5693` moving，双方均非
  combat/retreat。report / blocker SHA-256 为
  `4D21FD1662906C094544E80D15B840B7B31BB745EF8F1F9DBDD974054B64085C /`
  `39CA98290B6B595800CB51FD7D67045DDBD4B7D69C5DF0B6BC8E0309D0BDDE66`，cleanup GREEN。这排除了只因 stale cache
  漏看已发生接触。
- `4a7d7ce` 的 strict follow-up 只接受所有 conflict 都恰落在
  `horizon_end == ending_date == starting_date + 24` 的 point overlap，并且 subject 首跳晚于该端点；marker 绑定 episode、
  subject 与相邻日期。第二日只接受 episode terminal、active-war set change、subject removed、active combat 或 retreat。
  enemy ID/Province/intent 变化不能冒充成功；仍无强状态就记录 `exhausted_without_strong_transition` 并禁止第三日。独立复审
  找到并修复 Province drift 绕过第三日限制。相关回归 `376 passed / 191 subtests`、driver
  `165 passed / 141 subtests`、全量 `1394 passed, 2 skipped, 928 subtests passed`。
- production revalidation 路径：
  `C:\Users\xenoa\AppData\Local\Temp\xar-marriage-reject-c21c096-state\runs\20260828T000753Z-one-generation-a09470a0`。
  它从上述冻结 checkpoint 穿过 GEN-022，并在独立 GEN-023 finalize RED；因此 GEN-022 blocker-removal 保持
  `production-live loop / resolved for continuation`。最终为 `380/381` successful turns，counts
  `query=211 / gameplay=169 / checkpoint=54 / recovery=0 / terminal=1`，166 visible gameplay，elapsed `810.217s`。
  report / first-blocker SHA-256 为
  `AFEECF331F298F73F41D62A4CA78AE1C69C5BD09850EF4E692394645FDA12809 /`
  `52C46EA6AA0335A7A7086021EC5B3FD1BF2AC373AFE1673C9B8E8659C0AAAD50`。
- 最新 durable checkpoint 为 `date_raw=53220288 / history=4087 / size=79345233 / SHA-256
  C8C2926F63451725ABE9C496B7966B5C3971FD0B06CC5223B832A657176567D5`。CharacterID `29829`、episode
  `native-29829-ee172aa720db` 不变且角色存活；cleanup 全绿、CK3 已退出。163 个推进日对应 `12.07 游戏日/分钟`，
  推进事务约 `4.555 秒/日`，不是每游戏日 30 秒。
- GEN-023 发生在 `53220312`：ArmyID `117440751→3610` 的 exact horizon 已证明
  `53220312→53220336` contact-free，但 backend 没有广告 required advance literal；错误原文为
  `the exact route is contact-free for one day but this backend cannot advance it`。最小解除只修 capability/subject-scope 映射，
  然后从 `53220288` 冷恢复，不扩路线质量或新安全门禁。
- 同期五档速度研究提交 `3c2a9c7`：1/2/3 ongoing parity 是 research harness live GREEN；1–5 核心 terminal 一致，
  但 strict warscore parity 因同档漂移保持 RED-inconclusive。当前交叉路线只把 speed 2 作为下一 research A/B 候选；
  production selector 继续 speed 1。G1、terminal 与琉焰卿人生分数仍未完成。

## 2026-08-28 12:47：GEN-007 ordinary speed 3 production-live 与零中间暂停

- `f4ddc3d / 42a813d / dcf7f16 / 289c85f / 42601a5` 把 exact-build battle decision sentinel 接入正式
  selector，并将 watch 集合扩为全部 6 支可控 canonical army。普通 active combat 默认 speed 3；当前 sentinel 只在 watched army
  identity/route/move-target/CombatID/retreat、ordered roster、原生暂停、terminal、45 日 deadline 或异常变化时
  回到 paused planner，不再按游戏日暂停或执行 running rich query。
- production artifact：
  `C:\Users\xenoa\AppData\Local\Temp\xar-full-watch-production-56eac58-state\runs\20260828T043404Z-one-generation-ce48a71c\report.json`，
  SHA-256 `30C247B6C470BB1B867D90456282A25B6D30CC85E49C805263A2427AB32A7CEC`。从 immutable
  `53195952 / 08964AFA6D6CD56C6F7ACB9B24A79E30FC7C125936FD88E6635E4008B6203686` 恢复后 `3/3` turns；正式 planner
  选择 speed 3，全 6 army watch 从 `53195952→53196048` 连续推进 4 日到 terminal，`intermediate/external pause=0/0`、
  running rich query `0`、overshoot `0`，wrapper/observed terminal 与 cleanup 全绿。`turn_limit` 只是显式 3-turn canary bound。
- full-watch terminal speed-5 primitive：
  `C:\Users\xenoa\AppData\Local\Temp\xar-full-watch-terminal-speed5first-56eac58.json`，SHA-256
  `AE8D8EC25B4CF38BB864212099F9F9251C0BD37E0362BE22EE60B45C60DEFEF4`。同一冻结 seed 的 `[5,1]` 两臂都在
  `53196048` 得到相同 outcome core `F5FC814BA7088AB34D4A36F1071FFF0C5528F32C7809E59110F46FEEF6B2C38B`，均为零中间/外部暂停、
  零 running rich query、零过冲；speed 5 `2.000491s`，speed 1 `10.030168s`，约 `5.01×`。该 seed 是玩家败退 pursuit，
  只证明全监视 terminal primitive，不冒充 player-won pursuit 或双 `4x` crush selector 证据。
- sparse decision epoch 已把非 terminal 的下次 native stop 从固定逐日改为绝对日 gate：同帧 legality 明确 `too_early` 时取所有
  subject 的最早合法日，否则最多 45 日；普通战从 maneuver 预计约 3 个原生决策停点，从 main 约 2 个，从 pursuit 约 1 个。
  decided/crush terminal mode 忽略普通 phase/winner 漂移，目标合同就是直接 5 速跑到首个真实语义终点，零中间暂停。
- 失败证据未删除：早期 production arm 因 full-watch command 长度与 idle army 非正 direct target 分别 RED；最终只将
  `ProvinceID <= 0` 的 direct target 规范为 absent，并把 sentinel step 上限按 64 IDs 精确放宽为 795 bytes。fresh native
  `39/39` CTest；主线 Python `1402 tests / 3 skipped / 948 subtests` 全绿。
- GEN-007 因而不再把 speed 1 当正式默认，也不把 speed 2 当目标档。尚未自然出现的 player-won pursuit 与双 `4x` checkpoint
  保持 live-pending；下一场满足条件时做完整 `1,2,3,4,5,5,4,3,2,1` 冻结矩阵并校准 selector，但它们不抢占当前 G1。正式长跑从
  `53224848 / E317CB7F...C2EE` 继续；CharacterID `29829` 自然死亡后仍必须等待琉焰卿 committed 算分，再记录人生分数并结算。

## 2026-08-28 14:06：GEN-013 target-only live 与 GEN-025 primary defense

- target-only formal run `20260828T053149Z-one-generation-9ace0939` 为 `14/15` turns、6 visible gameplay、1 checkpoint；
  report / first-blocker SHA-256 为 `433A661E...82C5 / 1C74C447...24A`，cleanup/tree-gone 全绿。同一 target-specific
  assessment literal 的中位耗时由 `5.539740s (n=169)` 降到 `1.400889s (n=5)`；起点到新战争出现的推进吞吐约提升
  `13.08×`。GEN-013 的 target-only 路径升为 production-live，但保留样本量和端到端 pause/barrier 差异边界。
- GEN-025 冻结点是 `date_raw=53232216 / WarID=100663382 / naval_expansion_cb / score=0 / primary defender`；
  raise 后已观测 gathering ArmyID `100663369@2619`，却被旧完整 exit-evidence gate 阻止继续。最新 durable checkpoint 是
  `53231232 / history=4966 / DF7DBFF8213E504EEE9D3C438424AF5E05B6F1219F1EA718D76664395DE9005E`。
- 原生树确认 day-0 普通防御进入 military controller，完整 terms/forecast 只约束实际退出。`58f647f` 只让明确
  `primary=true` 继续既有 route/tactical OODA；primary identity 为 unknown 时仍要求 `game.state.active-wars`。
- 同次实证修正 `0xC569F0` 为 `player_victory`：query 两行固定 surrender=`false`、victory=`true`；写动作固定
  surrender=`false`、enforce=`true`。否则 primary defender 的投降/胜利会反向构造。score-0 defender golden、两种 defender
  写动作和 Python 错误标签回归已加入。fresh native `39/39`，DLL `A8EBDFAD...A427`；全量 Python
  `1408 tests / skipped 3`。当前为 static-ready，下一步 cold revalidation 后才能关闭 GEN-025。
- `e8fa51b` 另将少暂停/零暂停预研落到运行合同：普通 speed 3 移除不改变 hold 的 phase/winner 粗停；double-`4x` crush
  仅在 native final-stage 做同日 dominance invalidation，优势未失效就以 speed 5 从 admission 直达 terminal，正常路径零中间主动暂停。
  下一实验用 `1,2,3,4,5,5,4,3,2,1` 平衡矩阵；不抢占 GEN-025 cold continuation。

## 2026-08-28 16:05：GEN-027 路线零速边界与 committed-route 少暂停 canary

- formal run `20260828T064918Z-one-generation-38aa5830` 完成 `159/160` turns：`98 query / 61 gameplay /
  19 checkpoint`、60 visible gameplay、elapsed `416.427s`。report / first-blocker SHA-256 为
  `F8F834A33DFA8859A62872335B10E07B3E827DF80040CE22C148F891C4FE9D1A /`
  `E409EC428046A106C7E79E871E4C01379DEC0CFCE5AE919D6D6B0471C1C19A9B`；角色 `29829` 与 episode 未变且存活，
  cleanup/tree-gone 全绿。
- 最新 canonical checkpoint 是 `date_raw=53256000 / history=5183 / size=87300437 / SHA-256
  EE6D1B3703733FA827164ACDD26015C0F337257A2AE3850B5619088A0ED06D85`；driver state 仍绑定该 checkpoint，失败尾部只比
  anchor 多 2 行。旧 report 因普通 bridge error 丢失 plan 而错误标 seed fallback；当前 runner/service 修复会保留明确 non-save
  parameterized step 与该最新 durable anchor，不重试普通 unavailable。
- blocker 是 hostile `167772577` 在 embarked route 的共享首边形成
  `progress=0 / cached speed=0 / recalculated speed=0`。原 `0x2247320` 会把零扩展的 `0xffffffff` 从 duration 扣除；最小 reader
  fallback 只对该 exact 边界调用现有 `0x22475E0` 算首边，再把 index-1 shallow tail 交回 full helper。count-1、重复 front、
  `progress>0` 零速与 `0xffffffff` fixture 已覆盖，不把放宽扩展到其它形状。
- 吞吐主路径不再逐日 query 这条 route：新 canonical step
  `committed-route-sentinel-advance-army-<subject>-to-<target>-until-<date>` 显式绑定 scope/subject/target/bound；完整 watch 中任一
  active combat/retreat、subject 自己的 moving/route/target 不匹配或 sibling 替代都拒绝。独立
  `committed_route_sentinel_canary_ready` 默认 false，只由 `--allow-committed-route-sentinel-canary` 显式开启；speed 3 一次
  resume 后只在 route target、CombatID/contact、retreat、army identity、native pause 或 deadline 当日停。
- ordinary decision hook 已删除 phase/winner-only stop。旧 main-day-12 同 checkpoint 对照为 speed 1 `32.002s`、speed 3
  `11.248s`（约 `2.85×`），唯一粗停点恰是同日 phase+winner 且 planner 无新动作；当前保留 wire enum，但 hold policy 不再为它们
  单独暂停。double-`4x` speed-5 零中停继续采用独立 guarded mode 预研：native 内部定长 guard rows、同日 dominance invalidation、
  无每日 mailbox/RQ；只有真实 qualifying checkpoint 的完整 `1,2,3,4,5,5,4,3,2,1` 十臂矩阵才开放。
- fresh native build `xar-g1-sparse-route-build-20260828T1536` 为 `39/39` CTest；DLL/injector SHA-256 为
  `103198873504B5CEA93270CE5A71324F8D52ED0463DA639EBB472961A50610F9 /`
  `4A3E322D1900664A25C2549A4E5619E037036872882B48C1DC212F9C675839FC`。完整 Python 为
  `1482 passed / 3 skipped / 990 subtests`。一次 10 项环境 RED 仅因临时工作树被忽略的 CK3 junction 缺失；恢复指向已验证源目录后
  环境组 `54 passed / 1 skipped`、全量复跑上述全绿。当前状态仍是 static-ready；下一步必须从 EE6D checkpoint 跑显式 cold canary。

## 2026-08-28 16:17：GEN-027 production-live 关闭

- 首次使用新 pipe 的 launch-only attempt `20260828T080859Z-one-generation-600e5731` 在 CK3 启动前因 cold checkpoint 没有该 pipe
  对应的 v2 driver state 拒绝；0 turn、未启动 CK3、未改 save。report / blocker SHA-256 为
  `F7896DAE0BBF6342584D2D6EA16E69822692F99BCFCE6DF0077AFD71A45EA940 /`
  `68646E09029F1C65152A6A873A4597B1FF063856D97A7EB71B396B136A50BC32`。这是参数化 harness RED，不是 capability RED。
- 改回 checkpoint 绑定的 `\\.\pipe\xar_ck3_restore_exact2_7aff1d0` 后，cold run
  `20260828T080926Z-one-generation-9e0ac8cb` 完成 `20/20` turns、`11 query / 9 gameplay / 3 checkpoint`；report / bound-only
  blocker SHA-256 为 `713348FCA67C44A1D83A94FC9D5B42184C0B894CD2B5151AE3CFEAF8F4178F73 /`
  `2CA214C3755AE6388C457F38AC11C36DAE0C95B65E9C89CACD4A2FB21EBCFDF7`。cleanup/tree-gone 全绿，角色 `29829` 存活。
- 5 个 committed-route arms 分别推进 `6/9/10/11/8` 日，共 44 日；全部
  `external_pause_count=0 / external_rich_query_count=0 / intermediate_pause_count=0 / overshoot_days=0`。第五臂在
  `53257056` 以 `route_target_changed + combat_transition` 同日停表，没有漏过接触。
- 接战后两个 ordinary speed-3 arms 连续推进 `15+24` 日；第一个只在 absolute day gate 停，第二个以
  `combat_transition + combat_unavailable + combat_terminal` 停。两臂同样零中停/RQ/过冲，证明 phase/winner-only stop 已在
  production 路径消失。
- 最新 checkpoint 为 `53258328 / history=5207 / size=87715536 / SHA-256
  5AFCE04F64960FF4491CCE4FD2DC6F62254B3D44E46FCACB9CEB9282BFA28960`。route composite 现从显式 canary 晋级为默认
  production capability，gate 改为 `committed_route_sentinel_live_ready=true`；严格绑定合同不变。GEN-027 关闭，下一步从该点
   直接恢复正式一生长跑。

## 2026-08-31：GEN-033 signed battle identity 关闭，G2 第二寿命继续

- frozen source 为 `date_raw=53291904 / history=2096 / checkpoint SHA-256
  0D5B9F116DDAEFCD7C8DE0A9446924B88814D78FFBBD35FFD1F5E10C8D812858`，CharacterID `29829`、episode
  `native-29829-fffa4ba935f6`。
- attempts 08/09 是 production capability RED，report SHA-256 分别为
  `1F8AB25CD92F092B144FFEBB80DB9741C5409CD0D033D5B938D81F261B7B88DA /`
  `8567FB3F191DED7F09FF8A79AEF7C48A593750DC4F2C417074F0217B48977E5A`；两次 cleanup 全绿，checkpoint 未变。
- attempt10 只执行唯一允许的 one-day materialization；`53291904→53291928`、revision
  `4/native3→7/native6`，下一 frozen revision 仍被旧 positive-only planner 阻断，禁止第二次 advance。report / blocker
  SHA-256 为 `ECD945B9...78A9E / 54D57640...EDB0`。
- exact-build `ck3.exe` SHA-256 `2D00FF31...DB86` 的 `0x22771FC/0x2277204/0x2277220` 与
  `0x23083B7/0x23083C1/0x23083DF`（并在 `0x230845C/466/484` 重复）证明 signed full-ID 规则。attempt11
  `20260831T011000Z-signed-combat-id-query` 因 `battle_result_resolution_failed` 保留为下一层 RED；report / driver-state
  SHA-256 为 `ED8AC58D...1CE6 / 72CD4A94...DCCE`。
- attempt12 `20260831T011500Z-signed-battle-result-query` 为 paused production-live GREEN：同帧两次 query 均返回
  `CombatID=-2147483647 / BattleResultID=-2046820351 / Province=2619 / maneuver day 1 / finalized=false`。report / frame /
  driver-state SHA-256 为 `63FE9E3C...1D66 / 5AD7B6D6...30AF / 8672911D...FB96`，cleanup 全绿。
- attempts 13–15 依次证明一次 query、冷恢复仍从 checkpoint 截断后的 query history 开始，以及同 session 必须先完成 battle
  query + 三场 termination query 后 planner 才能进入 action；它们均是 bounded query-only、日期未推进，不是 capability RED。
- attempt16 `20260830T174839Z-next-episode-daf8eb6f` 完成 `6/6` turns（query 5、gameplay 1、checkpoint 1）。唯一
  gameplay action 是 speed-3 battle decision epoch，`53291904→53292072` 共 7 日，以 `combat_roster_changed` 停表，随后
  paused query 在 `native:13 / revision14 / native_revision13` 返回同一 signed IDs 与 `main` phase。新 checkpoint 为
  `history=2103 / size=96130176 / SHA-256 ED031039DA50C5FFA2FB9E5F47AF329BC2F4A56133816968584AF17B42C1C8E3`；
  report / output driver SHA-256 为 `3954608B...9326 / 4FC09FE1...F631`，session/shutdown/tree/driver cleanup 全绿，
  target HKL 最终保持 `0x04090409`。
- 回归基线：最终相关 Python `562 passed + 360 subtests`；全量 Python
  `1583 passed, 3 skipped, 1120 subtests passed`；native CTest `44/44`。唯一 WinError 5 pytest cache warning 是既有环境告警，
  不影响结果，也未扩修。
- 用户 turn 中断留下的 run `20260830T180744Z-next-episode-1cd83c9e` 保持
  `preflight_ready / finalized=false`，不重标为 capability RED。中断前后台已完成到 `history=2181 / date_raw=53295288` 的
  durable ACK；checkpoint 实物与 driver `last_checkpoint` 同为 `96,977,945` bytes、SHA-256
  `816B8B02E894B61CA8DBA8B9B1A283EF01C51849732FD45B3432004E28626D26`。接手时 CK3 inventory 为空；残留
  `owner.json` 指向死 PID，只是 harness/user-turn interruption 现场。
- 最终 continuation `20260830T182851Z-next-episode-19d679de` 从上述锚点 cold resume，`472/472` turns、墙钟
  `1198.576s`，counts 为 query `310`、gameplay `160`、checkpoint `151`、terminal `1`、recovery `1`。turn 468 的
  stationary-objective sentinel 在自然时间推进 `53319720→53319768` 时观察 `played_character_changed` 并立即停表；没有
  `die`、控制台或人工死亡动作。turn 469 `death-terminal` 得到 matching episode settlement：score `0`、blessing `7`、
  heir gameplay `0`，且记录前世已完成 Palermo holy-war win。
- turn 470 把 PID `72636→39036`、connection generation `1→2`、episode run ID
  `native-29829-fffa4ba935f6→native-29829-6e06850de2a3`，精确重载 immutable seed；turn 472 完成新 episode 一次
  visible gameplay，保存 `history=4 / date_raw=53211576 / size=76979953 / SHA-256 56C00CDC...408E`。15/15 qualification
  gates、session/shutdown/tree/driver cleanup 全绿，结束后 CK3=0，`first_blocker=null`。
- report / terminal / next-episode SHA-256 分别为 `2D798DAB...C4DD / C72C3A11...667A / BB570624...33A3`。fresh
  Release build 为 222 steps、native CTest `44/44`；DLL / injector SHA-256 为
  `3B1BE173...4EB6 / 0E85B1F5...ACC6`。HKL 启动与十分钟复验都实际发现系统可把 CK3 线程带回 `0x08040804`，均被立即
  纠正并留在 `0x04090409`；五分钟中间证据为全程英文。本轮不用 OCR。
- readiness 现提升为“同一冻结 seed 的 G2 第二完整寿命、结算及再次跨 episode production-live loop”。G1 `155/155`
  formal GREEN 不变；下一项不再重复该 seed，而是不同 seed/ruler/government/DLC 的泛化矩阵。

## 2026-08-31：GEN-034 Raiktor surrender 六域 blocker

- [production-live input] `xar-g2-post-call-ally-continuation-07acdfe-20260831T0425Z` 的 25/25-turn continuation 将 WarID
  `50331699` 从战分 `-48` 推进到 `-50`，最终 checkpoint SHA-256
  `60108A5DA03DC3A8315A3E79897D9CF2F49763910A8AA15A462E7DD0B6AAF164`。同一 paused 状态证明玩家是 primary attacker、
  CB=`raiktor_claim_cb`、战争 1281 日，surrender 的 validator/available/auto-accept/`would_accept_now` 全真。继续重复跑局不会补出
  缺失的 CB-specific terms；下一施工项是 native/MCP 只读观测。
- [fixture-confirmed partial / pending-live] `05ae0bf` 把旧 `unsupported` 提升为 distinct typed partial：真实 claimant、target order、claim
  rows，以及 source-authored gold/F/truce/PoW/hook formula、legitimacy/influence 精确零、hostages=false。actual gold、prestige/F、truce、
  PoW、hook 与 war-bound current losses 均仍 unavailable，`dynamic_deltas_ready=false / decision_ready=false /
  automatic_surrender_ready=false / ready=false`；它不授权 surrender literal。
- [fixture-confirmed native core / pending wire+live] PoW 独立 production helper
  `ReadRaiktorSurrenderPrisonerReleases` 已闭合完整 participant、双方 primary+前三继承人候选与 actual release pairs；完整扫描后的空
  pairs 是合法零，War/CB/primary/claimant 与 participant/succession/jailer 图必须在同一 paused date 双采样一致。fixture 覆盖真实 pair、
  完整空集、malformed succession、jailer drift、running frame、stale full WarID、非 Raiktor CB 和零 command submission。它尚未进入
  application-main mailbox、terms JSON/MCP 或策略输入，因此不改变六域 readiness，也没有取代一次启动 live matrix。
- [fixture-confirmed native core / pending wire+live] actual-gold 独立 production helper `ReadRaiktorSurrenderGold` 已闭合唯一 final
  primary attacker→defender transfer、双方 current gold 与 `0x28DBE90` authoritative monthly income。它在每次原始 visible-root preview
  前后重读 finance/identity，要求两次完整样本及最终 paused Snapshot/CB-key 一致；cached income leaf 即使与 callable 不同也不参与门禁。
  fixture 已覆盖 row 缺失/重复/反向/负数/malformed、preview finance mutation、completion CB-key drift、null root slot、running frame、
  非 Raiktor CB、成对 teardown、零 hidden projection 与零 command submission。它尚未接 mailbox、terms JSON/MCP 或策略输入，故不改变
  六域 readiness，也没有取代一次启动 live matrix。
- [fixture-confirmed native core / pending wire+live] F/prestige 独立 production helper `ReadRaiktorSurrenderPrestige` 已把 final F 与 attacker
  prestige delta 原子闭合：同一次 original `CB+0xA28` visible-root traversal 中，collector 捕获唯一 typed primary-attacker prestige callback
  并将全部 callback 恰好 forward 一次；root slot11 proxy 在 `0x3380170` 销毁临时 wrapper 前读取唯一 identifier-82 final row。它要求
  `F>=0`、`10F` 不溢出、delta=`max(-10F,-1000×100000)`，冻结并跨两次 sample/final 复核 original root vtable+slot11 identity，且每次 preview
  前后 current prestige/identity 相同，两次完整样本及 final paused Snapshot/CB-key/role 相同。fixture 覆盖 zero/cap、factor/callback/container
  错形、公式/overflow、preview 与跨样本 drift（含返回同值的 root identity swap）、running、stale WarID、
  错 role/CB、成对 teardown、零 hidden/broad/command。它尚未进入 mailbox、terms JSON/MCP 或策略输入，没有 paused CK3 artifact，故不改变
  六域 readiness，也没有恢复 production-disabled broad exit reader。
- [static design] GEN-034 的最小解除范围固定为六域：actual gold；`cb_prestige_factor` 与 attacker prestige delta；truce days/expiry；
  实际 PoW release pairs；conditional favor-hook application；按来源 regiment 读取的 current war-bound army losses。faction/opinion/feud/
  Mandala/LAAMP 留作显式 broad 能力债，不伪装为零，也不阻塞这个窄 `decision_terms_ready`。完整 reader 与策略合同分别见
  [war-termination.md](../ck3-native-ai/war-termination.md) 和
  [player-war-exit-policy.md](../ck3-native-ai/player-war-exit-policy.md)。
- [partial native implementation] gold/F/PoW/favor 已有 production core；favor 的 WarID-bound wrapper 现要求 exact paused
  `raiktor_claim_cb`、玩家 primary-attacker role、original root vtable 与非空 slot11，并在 claimant 不同时双采样 exact hook row、runtime hook
  identity 与全部 War/CB/role 身份；claimant=attacker 则精确 false 且零 traversal。它尚未接统一 terms wire/MCP/live。truce 复用
  `0x3373000`，只差一次 pointer-only Raiktor root
  shape probe，并且绝不执行 ContextEffect。仍未闭合的来源 reverse gap 是 `spawn_army war=scope:war` 在
  CRegiment/special-troop 对象上的持久 origin、bound-WarID、keep=false 字段及 serializer。
  ArmyID、参战方、名称或初始 3000 人都不能替代来源字段；合并后的军队必须按 surviving regiment 追踪。
- [static/fixture-ready / not-live] `94d367e` 新增独立 generic war-bound regiment observer：只接受 exact paused
  `raiktor_claim_cb` frame、primary-attacker owner、相同 full-generation WarID、`bound_war_id` 与 `keep=false`，按每个 present
  CArmyRegiment generation 汇总当前 soldiers，并可在独立 postwar frame 逐 frozen persistent/current/CArmy generation 发布
  `destroyed/still_alive`。它明确不把 generic row 升格为 `norman_highwaymen`，也不把 authored `6×500=3000` 当 measured pre soldiers
  或 loss；`source_specific_attribution_ready / pre_soldiers_ready / proven_soldier_loss_ready` 全为 false。Python 普通与 `-O` 各
  `6/6 GREEN`，MSVC Debug/Release 均以 `/W4 /WX` 编译并运行 GREEN；source contract SHA-256 为
  `26652A0FCB9D0C185272E7C3B2721A9EC93BC5C5CDC5003D2B9D9EE16B105241`。没有 public wire 或 paused CK3 artifact。
- [static/fixture-ready aggregation / not-live] `5e2dfea` 新增独立 claims-base + six-domain same-frame aggregate。这里 claims 是
  target/claim rows 与 attacker-defeat disposition 的基础语义；“六域”严格指 gold、prestige、PoW、favor、truce 与
  generic war-bound current。七个 child 的 paused snapshot/native revision、date、WarID、CB、attacker/defender/claimant 必须一致；
  任一缺失产生显式 `incomplete` 且 `action_terms_ready=false`，present child 跨帧或错形则 aggregate unavailable。完整 fixture 只能令
  aggregate-local `action_terms_ready=true`；`automatic_surrender_ready=false`，不替代 options/recipient/policy gate。truce 不推算
  expiry；postwar cleanup 使用独立 frozen-ID frame；source attribution/pre/loss 继续全假。Python 普通与 `-O` 各 `8/8 GREEN`，MSVC
  Debug/Release `/W4 /WX` GREEN；source contract SHA-256 为
  `4D9A67F1C8DBD0528823E11C320DB1CFA57C4C30DF3B377595B26F7281A08500`。它未接 shared/public wire、MCP、policy 或 CK3 live。
- [non-regression] 普通 `claim_cb_claim_disposition` 的 schema、JSON、readiness、GEN-004 white-peace 路径不得改变，也不得被新增 Raiktor
  binding 反向门禁。历史 broad `ReadWarTerminationExitTerms` 继续在任何 preview 前返回
  `loaded_effect_preview_disabled_after_live_crash_rva_0x334C668`；Raiktor 新 reader 只遍历原始 visible root，hidden truce 只做
  pointer walk 与 direct duration evaluator，禁止重用导致两次实机 crash 的 projection。
- [fixture gate] 覆盖普通 claim golden 不变、Raiktor happy path、六域逐项缺失/重复/错 scope/generation、F formula/overflow、truce shape/
  stability/expiry、PoW jailer/succession、hook true/false/type、regiment origin/merge/full scan、collector/context teardown 和零 game-object
  write。另锁定 production-disabled reader 与“Raiktor path 不引用 hidden projection”的 source contract。
- [single-launch live matrix] MCP-first、英文 HKL、禁止 OCR；复用 frozen CharacterID `29829` / WarID `50331699` checkpoint。一次 CK3
  启动内完成：同帧 options+terms 两次且 payload 相同；任一六域未 ready 时 surrender literal 不可见；保存 pre-surrender checkpoint；
  策略门满足后只提交一次 typed surrender，ACK 仅记 `submitted_pending`；旧 WarID 消失后核对 gold/prestige、claims、truce、PoW、hook、
  war-bound source regiments 和非目标军队；保存 postwar checkpoint 并继续 G2。
- [postcondition boundary] 优先在同一 paused `date_raw` 完成 command 应用。如果必须跨日，日收入、其它 effect 与 truce 起算会污染精确
  delta；没有 action-boundary observer 时该臂记 capability RED，不能只用 WarID 消失冒充六域 GREEN。GEN-034 只有 implementation、
  fixture 与上述一次启动 live matrix 全部完成后才能关闭。

## 2026-09-01：GEN-034 conservative pairwise policy core

- [static/fixture-ready policy / not-live] `630ff35` 新增
  `raiktor_continue_vs_surrender_policy_v1`。其输入严格冻结 exact paused frame identity、claims base、六个 dynamic domains、完整
  campaign dominance certificate 与具 provenance 的 owner budget profile；战争分数 `-50` 和 1281 日只作为模型输入，不是投降理由。
  continue 与 surrender 分别使用保守上下界，只有一方在全部 hard budget 内并以显式 switch margin 严格胜过另一方时，才产生 pairwise
  preference；否则返回 underdetermined。
- generic war-bound current 只可作为 conservative exposure，不能冒充 `norman_highwaymen` source attribution、战前兵力或 proven loss；
  authored `3000` 同样不能进入 measured loss。policy 不恢复已因两次实机 crash 禁用的 broad exit reader，也不放宽普通 `claim_cb`
  white-peace 纵切。
- 当前冻结 checkpoint 缺 public truce/generic-war-bound 同帧 wire、campaign dominance certificate 与显式 budget profile；white peace 也未评价。
  因此合同明确保持 `recommendation_ready=false / full_exit_decision_ready=false / automatic_surrender_ready=false / action_literal=null`。
  该提交没有 MCP action、没有 CK3 paused artifact，也没有 submit/postcondition；readiness 仅为
  `static-fixture-policy-core / not-live`。
- `630ff35` 的 Official Runner CI `33460057790` 已 terminal SUCCESS。这个 GREEN 只验证 policy/fixture 合同，不改变四域 live 边界，
  也不关闭 `GEN-034`。最小下一步仍是 public same-frame six-domain input → campaign/budget evidence → white-peace comparison → typed
  surrender single-submit → 六域 action-boundary/postwar live matrix。

## 2026-09-01：truce evaluated duration public wire 接入（实机待验）

- `6be8831` 将已有 `raiktor_surrender_truce_v1` pointer/evaluator core 接入正式
  `ReadWarTerminationTerms` 与 `query-war-termination-terms-v1-<full-generation WarID>` / MCP wire。当前只公开非负
  `evaluated_days`（及其 `evaluated_days_observable`），`actual_expiry_observable` 固定为 `false`、`expiry_date_raw` 固定为
  `null`；任何 `current_date + days` 推算都不计为 expiry 观测。
- 整合线 fresh MSVC/Ninja 产物目录为
  `Z:\ck3_mod_rewrite\_build-g2-truce-integration-20260901b`，DLL SHA-256
  `CFDA6FF379F25A250696CAD2497AE5FDDB78559E924E787F6B86B13D7608B578`，injector SHA-256
  `92F54D2701C5A64BB3735E74C3B869360DEA89CCE0B47EAE4481B475166A0E13`。Python terms/truce contract 普通与 `-O` 回归通过；
  fresh CMake 全构建成功，CTest `56/71`，其余 `15` 项仍是既有 source-contract/harness 路径失败。
- 本次 fixture metadata 更新后的可核验 SHA-256 为：truce source contract
  `E168CA7B6382B2CCBD8D0619220ADF82A8AE79E525D9CE6E149CCFF9C0F86368`；six-domain source contract
  `05C3C40180FCFEC6E33C5DB627287C7FCF361C5B5228374D953BD5119DAD3C79`；continue-vs-surrender policy contract
  `9BDFE4EEB1A1CB9C57F66D67325656FEBF73FD31101904310D92F0D1E628B2C5`。
- 这只改变 truce duration leaf 的 public-wire 状态，不提升完整六域 aggregate、policy 或 action readiness。没有 paused CK3 live
  artifact，`truce_ready` 的实机双读/同帧 probe 仍 pending；generic war-bound source/pre/loss、campaign/budget、white-peace、typed
  submit 与 postcondition 仍未闭合，故 `GEN-034` 继续 **unresolved**。

## 2026-09-02：GEN-034 private pre-reset live RED

- 一次 frozen exact-build paused、只读双查询已用显式 OFF-by-default 的 instrumented DLL 捕获 production reset 前的 typed failure；
  两行均为 `root_shape_drift`（code `9`）、`pointer_shape_verified=false`、`evaluated_days=-1`、
  `expiry_observable=false`、`context_destroyed=true`。这证明当前 reader 在调用 duration evaluator 前即退出，不能把
  `war_days` schema、静态 evaluator call-site 或 `current_date + days` 冒充 live duration/expiry。
- runner report SHA-256 为
  `31377779207957E3D18D7260945F5CD933DCCC497F2C1844A95D5CC01F02421E`；private JSONL SHA-256 为
  `47514E299D87F6878229115BB60897F5E23FA28DACEE81937619D21A44D268EF`。同帧 identity、四域只读 payload、
  source invariant 与 cleanup GREEN；没有 time advance 或 surrender/white-peace/enforce mutation。
- `GEN-034` 继续 **unresolved**，`truce_ready=false`、`decision_ready=false`。下一入口缩小为 private staged
  loaded-tree shape capture：标出 `ResolveUniqueTruceNode` 的具体失败检查及对应 vtable/count/capacity 实值；没有该新证据前不改
  offset/shape contract、不扩 public wire/readiness、不重复本次 checkpoint replay。完整证据边界见
  [G2 private truce live capture](../ck3-native-ai/g2-truce-private-live-capture-2026-09-02.md)。

## 2026-09-02：GEN-034 exact next-layer live NO-GO

- 在此前 exact Context 证据基础上，唯一一次 bounded private live 只读取
  index 9 的 `0x44D1E18(1/1)` 唯一 child，以及 index 10 的
  `0x41E36D0(6/6)` 六个 children。两条 capture 完全一致：index 9 为
  `[0x4446EF0]`；index 10 为
  `[0x44D2138, 0x44D2138, 0x44786C8, 0x41B1E90, 0x44D1E18,
  0x44D1E18]`。没有节点匹配 Truce vtable `0x4461CA8`，因此没有生成
  duration 地址，也没有调用 evaluator。
- live report SHA-256 为
  `804496739A9945083AAA7E5D641DC8E9ECF0660B58A725BA499DCF4065CDE3C7`；
  private JSONL SHA-256 为
  `DF6AD111C22034F8287D7695F4905B84FE24543F33004AD369F60902FAC00A37`。
  cleanup/source invariant GREEN，未推进时间、未发送战争终止 mutation。
- 本结论覆盖本页顶部 GEN-034 行中“下一包枚举 1+6 children”的旧待办：该
  待办已完成且结果为 NO-GO。下一最小入口改为离线解析五个唯一 RVA
  `0x4446EF0 / 0x44D2138 / 0x44786C8 / 0x41B1E90 / 0x44D1E18`
  的 COL/type descriptor/RTTI 与 bounded container shape，优先确定仍可能通向
  `0x4461CA8` 的唯一路径；在静态证据未唯一化前不再启动 CK3，不改 production
  `19/14/index 9`、public ABI 或 readiness。`GEN-034` 继续 **unresolved**。

## 2026-09-02：GEN-034 four-entry nested live NO-GO

- RTTI 收窄后的唯一 bounded live 已完成四个入口。index 9
  `CIfEffect+0x258=null`；index 10 scripted-list common `1/1` 为
  `0x44D1D50`；两个 CIf common 分别为 `1/1:[0x44D1E18]` 与
  `2/2:[0x44D2138,0x44D27B8]`，且两者 `+0x258=null`。两条记录完全
  一致，Truce `0x4461CA8` match count 为零。
- report/private JSONL SHA-256 分别为
  `A89D7EBE4BC31352D51BF0AB7FB1FE6351B288F71CF1B9482C00F478506DCDC3` /
  `DF77E246787B8B1EE11DCB933442FBECA66547C048F2E02674DE02B955FD011E`；
  cleanup/source invariant GREEN，无 evaluator 或 mutation。
- 所有已读 `CIfEffect+0x258` 均已收口为 null，不再列作 pending。下一包只离线解析
  `0x44D1D50` 与 `0x44D27B8` 的 exact RTTI/COL/container 语义；静态不能唯一化前
  不再启动 CK3。public/readiness/production shape 不变，`GEN-034` 继续
  **unresolved**。

## 2026-09-02：GEN-034 residual RTTI 与源码顺序纠正

- 离线 exact-build RTTI 将 `0x44D1D50` 定名为
  `CShowAsTooltipEffect`（`0x60`），将 `0x44D27B8` 定名为
  `CJominiContextEffect`（`0x100`）；两者都在 `+0x40/+0x4C` 持有 common
  effect vector。Context 的 `+0x60/+0x6C` 是另一份 scope/configuration
  storage，不是 effect child vector。
- 冻结原版 `raiktor_claim_cb.on_defeat` 顶层顺序与前序 live shape 一一吻合：
  index `7` 是四 child 的 `add_truce_attacker_defeat_effect`，index `9` 是一
  child 的 discontent，index `10` 是一 child 的 LAAMP tooltip，index `11`
  是二 child 的 mandala。故先前仅按 `1/1` shape 缩到 `9/10` 的路线被纠正；
  唯一下一只读路径返回 index `7` 的
  `default child1 hidden_effect -> child0 Context -> child0 expected CAddTruce`。
- `+0x258=null` 只覆盖实机读取过的三个父 CIf 对象，不能外推到递归 child；
  因 index `9/10` 已被源码语义排除，后者无需继续探测。artifact SHA-256 为
  `3A56A1ACBF49591C0787EADE412C2C8F23E49E253DAC00C4ADB7A7624B628DB3`，
  focused test `4/4` GREEN，未启动 CK3。production shape/public ABI/readiness
  均不变，`GEN-034` 仍 **unresolved**；index 7 路径必须经一次 bounded live
  后才能更新生产合同。

## 2026-09-11：GEN-034 natural-source R441 与 hash-bound 续跑入口

- R441 在唯一 CK3 PID `140912` 上用既定 520 秒窗口验证了原版事件 OCR 修复：18 个事件均通过已验证的选项点击关闭并恢复时间。
  `bookmark.1071.a` 未出现，因而没有 source capture、bridge attach 或 surrender；这不提升 `GEN-034`。exact-build 定义要求
  `gold>=100`、`is_at_war=no` 与非玩家拜占庭持有者，且初始排程为开局后 1–7 年。R441 已到 1073-10-31、694 金，故不再扩大
  单次 timeout。
- R441 后继存档为 85,561,556 bytes、SHA-256 `A0E122CA…51A98`。adapter 现以成对参数绑定该输入，启动前检查 exact
  `1.19.0.6` 存档头与哈希，并在 fresh userdir copy 后复核大小与哈希；no-launch 实档 admission GREEN，收据 SHA-256
  `1D5B0B77…88B`。聚焦测试 normal/`-O` 全绿，当前没有 CK3 存活实例。
- 该入口只消除重复播放 R441 前缀的成本，状态为 static-ready。下一项仍是一轮从该 exact checkpoint 开始的 bounded live；只有
  自然事件六次 source execution、同 PID current、唯一 surrender 与 postwar cleanup 全链成功后，才可提升 source-specific
  loss/comparison input。campaign、budget、white-peace、decision/action/automatic surrender 和 `GEN-034` 仍 unresolved。

## 2026-09-11：GEN-034 R442 resume load 与 OCR 空窗边界

- R442 已实机验证 R441 checkpoint 的逐字节 copy/load，唯一 PID `43852` 从 1079-01-01 推进到 runtime log 可见的
  `1082.4.23`。一次 8 秒 HUD 日期 OCR 空窗被送入 modal-only recovery；画面没有可验证选项，runner 以 harness RED 停止并完成
  cleanup。没有 source capture、bridge 或 surrender，`GEN-034` 不变。
- 修复范围只覆盖该实证故障：无 verified modal option 时重做现有时间轴动作，并要求读到严格更晚游戏日；无法证明推进仍为 RED。
  adapter normal/`-O` 各 `23/23`。R442 最新 successor `3D8755AE…6E07` 已通过 no-launch admission
  `C10FDE71…5391`，下一项是一轮 bounded continuation，不重放 1066–1082 前缀。

## 2026-09-11：GEN-034 R443 source 场景耗尽

- R443 实机验证 no-modal 恢复分支在无法证明日期推进时保持 fail-closed；保留帧显示罗贝尔在 1084-05-06、69 岁死亡并进入
  继承暂停。exact `.1071` 调度和 trigger-fail retry 均绑定历史角色 `1128`，故不能用 Roger successor 延续冻结
  CharacterID/source lifecycle。
- receipt `CFBB1AFF…0DB6`、终态帧 `A2C78B8D…63CF`、report `28EF8764…DFD7`；cleanup GREEN，CK3=0，source capture/
  bridge/surrender 均未发生。该链为 `SCENARIO_EXHAUSTED`，`GEN-034` 继续 unresolved。
- 下一施工入口从“继续旧存档”改为 fresh natural run 的 peace-precondition control：必须先以 exact-build、可观测输入证明并维持
  `is_at_war=no`，再启动下一轮；不得用 console 触发冒充 natural source，也不得再无控制地等待完整寿命。

## 2026-09-11：GEN-034 R444 snapshot 纠错与 source 去向

- R444 exact native snapshot 给出 played character `29829`、`active_wars=[]`，否定了“R441/R442 一直因战争使 `.1071` trigger
  fail”的假设；没有必要构造 surrender precondition。adapter 因仍要求顶层 `played_character_id` 而 harness RED，已最小兼容
  canonical `played_character.character_id`，focused normal/`-O` 各 `23/23`、real-save no-launch admission GREEN。
- R441 successor 中 `show_historical_gui` 与 `raiktor` 位于同一序列化角色记录、相距 59 bytes；exact `.1071:immediate` 正是创建
  Raiktor 后写这两项。故 source 已自然出现，但标题漏识别后 generic modal recovery 在 observer 未 arm 时关闭了事件。
- R444 classification SHA-256 `3827A3E1…E5D4`，cleanup GREEN、CK3=0、mutation 零。`GEN-034` 仍 unresolved；下一入口是
  target option 的高置信识别并保证 `atomic_arm` 先于 click，不再通过延长 live 窗口获取同一事实。
## 2026-09-11：GEN-034 `.1071` arm guard 与最近 pre-target source

- target option 现在在 generic recovery 前检查；完整文案失败时，只有 option 区域同时存在 `扶上 / 君士坦丁堡 / 皇位`
  才允许定位，随后严格 `atomic_arm → click`。normal/`-O` 各 `24/24`，未启动 CK3。
- R441 三个 autosave 均已有同记录 `raiktor`；R440 1068-01-03 save 尚未出现该 marker，是最近可用 pre-target lineage。
  其 SHA-256 `D1E469D0…CDA9D` 已通过 input-specific no-launch admission `5E6A0A00…AACD`。
- `GEN-034` 仍 unresolved；下一入口是一轮从该边界启动的 source-specific lifecycle。该轮只验证自然目标的 arm/capture 与既有
  same-PID continuation，不再重新跑 1066–1068 前缀。

## 2026-09-11：GEN-034 R445 外交信件 harness RED

- **现象**：R445 从 `1068-01-03` pre-target lineage 推进至 `1069-08-16` 后停在掌玺大臣外交失败信件；
  `.1071` 尚未 capture，故 source-specific loss、comparison、decision/action readiness 不变。
- **根因**：exact-build `chancellor_task.1004` 是 `chancellor_task.1003` 经
  `task_foreign_affairs_side_effects` 打开的 unavoidable letter event。唯一选项 key 为 `chancellor_task.1003.a`；
  现有 source adapter 没有该事件的高置信处理分支。
- **修复**：`3b632641ab839a6b9d569208e762fc39ad9fa052` 只在正文和选项区同时命中
  `掌玺大臣 / 外交行为 / 可怕的误会` 时关闭唯一选项并恢复时间。normal/`-O` 各 `25/25`，实际截图回放 GREEN；
  shared runner、DLL 和游戏文件不变。
- **资产同步**：`.1004` 通用事件记录与新 source-index 在
  `dacc1d759d349ff142f167e265f09077c51da27d`；`open_kaishek` 兼容同步为
  `2a558f6317551ba5f04f7d95009071d7f96bc90c`。
- **状态**：`HARNESS_RED -> static-ready fix`；产品 RED 为 false。R445 已结束、cleanup GREEN、CK3=0。
  R446 使用 SHA-256 `431320AAC5094501BE48005C3A13E7FF0B4C75A56639A47C96352D04B1AFDBFF` 的最近 successor，
  final no-launch admission SHA-256 `8A3C4FFA6E3C3A68738B6B06184F053C855B53196C896111B405A92971CBBE0F`。
- **关闭条件**：一轮有界 R446 仍须自然命中 `.1071`、先 arm 后 click，并完成同 PID source/action/postwar lifecycle；
  未满足前 `GEN-034` 保持 unresolved，T1 保持 90%。

## 2026-09-11：GEN-034 R446 target-click acceptance RED

- **到达**：R446 自然到达 `1070-09-02 bookmark.1071`；`.1071.a` 点位 `(931,934)`，observer ready、断点安装、
  action-arm identity 全部匹配。
- **失败**：adapter 发出单次点击后没有验证 rendered option 消失；observer 捕获 0 executions，恢复断点字节后 detach 失败。
  因无 post-click 画面，不能区分 click 未接受与 native no-hit。classification SHA-256
  `FEDFC309F84F2B7ECB66B52CA99F98D15768360FC90BAD7AFF8F5EE6181E7F59`；cleanup GREEN，CK3=0。
- **伴随原版 RED**：`bookmark.1071:immediate:1477` 的 tooltip scope 错误发生在点击前五秒；保持记录，不能冒充 option mutation 结果。
- **修复**：`85b7c8b49802a981f78e2e285f515f12e52a5812` 要求已 arm 的目标选项在最多三次点击内由同一高置信识别器确认消失；
  否则保持 RED。normal/`-O` 各 `27/27`。
- **下一输入**：R446 latest save SHA-256
  `523D365EC6E566EE7432C99B04AD682C99BFCA92D26FDA7EDE340AACCCA38709`、无 `raiktor`；R447 admission SHA-256
  `BCF0467F59E1BEEFD02B2868BF4F159980E595137F58790A4A93860097475112`。
- **关闭条件**：R447 必须同时证明目标选项消失、六次 source execution、observer detach 与同 PID continuation；当前
  source/comparison/decision/action/automatic-surrender 均不 ready，`GEN-034` unresolved，T1=90%。

## 2026-09-11：GEN-034 R447 native hit 与 evaluated-name 证据门

- **已关闭的不确定性**：R447 首次点击后 `.1071.a` 由同一高置信识别器确认消失；private observer 随即在 exact `spawn_army` breakpoint 返回 `armed-hit-evaluated-name-mismatch`。断点安装、原字节恢复和 debugger detach 均有记录，因此 source mutation 确实被调用。
- **真实根因**：旧 observer 在 append evidence row 前要求运行时字符串等于 authored key `norman_highwaymen`。现有专题已把该字符串定位为 supporting evidence，而不是 source 唯一选择器；这项旧检查导致命中存在却输出零行。
- **最小修复**：`8e2a8917143e261ccac589436b44baafdb1b9d14` 删除前置拒绝，保留实际字符串；最终 `ValidateSixExecutions` 仍要求六行 identity 一致后才能 GREEN。新 executable SHA-256 `B05E0B6D3CA8DBEC41C8C5107AB8F9AACD4E99981E442AC1DBF3077868241007`，self-test 与 normal/`-O` 各 `53/53` GREEN。
- **输入与边界**：R447 latest pre-target save SHA-256 `89D15B8ACB0E69E6C439D658582B63DC1F8AD11EC687089E5021A5961607D4DD` 已通过 R448 no-launch admission `5FF8771F9CCCA853FA4C4FE8FA7B7BE0787C3EAB5EEF25B18FD8FD5A9601E3EB`。R447 已结束，cleanup GREEN、CK3=0；原版 tooltip scope RED 保留，但已由 mutation breakpoint 命中排除为执行阻断。
- **仍未关闭**：尚未取得并审阅六行实际 `evaluated_name`、source-specific measured loss、comparison input、decision/action 和 postwar lifecycle。`GEN-034` 保持 unresolved、T1=90%。下一步只允许一轮 R448 近边界捕获；若 identity 不同，先审阅 artifact 再改合同，不原地反复测试。

## 2026-09-11：GEN-034 R448 六行 source 已取得，lifecycle 尚未续接

- **取得**：R448 捕获六个 unique loaded node/CArmy generation、同一 full-generation WarID `33554473`、24 条 persistent/current 映射与实测 `3000` 创建兵力。`.1071.a` 已确认接受，breakpoint restore、debugger detach 和 cleanup 全部 GREEN。capture SHA-256 `B819D4C94B3BD25EC1B505368801FE5EC2BD09CBCEFB934543B687CB1A984A1D`。
- **RED 根因**：六行运行时名称均为本地化显示值 `诺曼路匪`，旧 validator 却要求 authored key `norman_highwaymen`。R448 因此为已解释的 harness/contract RED；产品 RED 为 false，原版 tooltip scope RED 也已由 native breakpoint 命中排除为执行阻断。
- **修复**：`0235a50241f3dd6c37d375ff00bf56d76620d3a9` 要求名称非空且六行一致，不再用 authored key 选择 source；WarID、节点、generation、兵力聚合和 regiment 映射门全部保留。新 executable SHA-256 `020F051DDE034CBBC67C5A308F8E035FFA3E224844AC413261AA257466B0F185`，self-test 与 normal/`-O` 各 `53/53` GREEN。
- **状态**：R448 在 observer RED 后未进入 bridge/current/termination/postwar；故 source-specific loss、comparison、decision/action/automatic-surrender 仍不 ready，`GEN-034` unresolved、T1=90%。R448 已结束、CK3=0；autosave 与近边界输入逐字节相同且无 `raiktor`。
- **下一关闭入口**：只运行一轮 R449，消费修正后的 locale-neutral capture 并在同 PID 继续 current checkpoint、唯一 termination 与 postwar cleanup。若出现新的明确 RED，冻结并分类；不得为已证名称事实再跑重复轮次。

## 2026-09-11：GEN-034 R449 启动前动态 WarID seam 修复

- **实证冲突**：R448 source capture 的 full-generation WarID 是 `33554473`，旧 lifecycle/CLI 却冻结 `50331699`。自然事件创建的新战争不能预先复用历史 generation ID；直接运行会在 observer GREEN 后必然 RED。
- **同分支缺口**：concrete continuation 未声明 outer owner 已传入的 `expected_war_id`，因此旧代码即使 WarID 恰巧相同也会在首次走通分支时发生参数错误。
- **修复**：`5743466d1074af68ff12930bbe299becc12fef8c` 从已规范化 source capture 取 WarID，并贯穿 lifecycle；CLI 值只做可选相等断言。既有 full-generation、same-PID、active-war、checkpoint、mutation 和 postwar 校验不变；normal/`-O` 各 `53/53`。
- **边界**：本包未启动 CK3、未提升 readiness。R448 已结束、CK3=0；`GEN-034` unresolved、T1=90%。下一步重新做 hash-bound no-launch admission 后才允许唯一 R449。

## 2026-09-11：GEN-034 R449 debugger detach race

- **已通过**：R449 六行 source capture 使用动态 WarID `33554473`，locale-neutral name、unique node/CArmy、兵力和 regiment 映射全部通过；`.1071.a` 接受、breakpoint restore 与 outer cleanup GREEN。
- **RED**：final debug event continue 后，单次 `DebugActiveProcessStop` 返回失败，故 observer 覆盖为 `debugger-detach-failed`；R449 没有进入 bridge/current/termination/postwar。capture SHA-256 `E382E079DC7A6124A9961E174A3E802F8E67B0C95403325FB16485FD51A5E178`，产品 RED 为 false。
- **最小修复**：`454f515d8ef55ddf6e3cd5eccfa0a8cfb26e7630` 允许最多 20 次、每次间隔 25 ms 的 detach，记录 attempt count 和 last Win32 error；最多 sleep 475 ms，耗尽继续 RED。self-test、normal/`-O` 各 `54/54`。
- **状态**：R449 已结束、旧轮次 R448 已结束、CK3=0；T1=90%、`GEN-034` unresolved。下一轮只能消费同一近边界输入验证 detach 后继续 lifecycle，不重跑已证名称/WarID研究。

## 2026-09-11：GEN-034 R450 当前输入上的停战期限缺口

- R450 已取得 source-specific 当前帧：WarID `33554473`、`raiktor_claim_cb`、玩家为 primary attacker、24 条 war-bound regiment、实测 3000 当前兵力；六行 source capture 和 debugger detach 均 GREEN。
- 两次同帧公开 terms 查询都返回 gold、prestige、PoW 与 favor，但 `truce.evaluated_days_observable=false`。因此 aggregate 的唯一 missing domain 为 `truce`，`action_terms_ready=false`；没有创建 checkpoint、没有提交 surrender、没有 postwar 结果。
- 这取代 GEN-034 表格中早期“继续枚举 index 9/10 shape”的施工入口。旧 shape 枚举已经完成且不能解释当前 production reader 的输入依赖失败；下一入口改为只读 pre-termination probe，在 exact build 和当前 WarID 上记录 default truce reader 的明确失败阶段。正常 lifecycle 的六域门不变。
- R450 classification SHA-256 `4ACA6BC721D9D9286E572200F03D3526A2D69D53B302DFBEB5E60A545E387047`；source 未变、cleanup GREEN、CK3=0。`GEN-034` 继续 unresolved，T1=90%。

## 2026-09-11：GEN-034 R451 只读诊断入口

- 新 probe 只复用既有自然 source、同 PID bridge 与两次公开 terms 查询，在 mutation checkpoint 前终止；合同要求零 action、零 postwar，并把 `PROBE_COMPLETE` 与 `terms_ready` 分离。
- default-OFF 诊断 build 在不改变 default reader 分支的前提下记录具体 stage、callback/failure counts 与 context identity/destruction。诊断 ON 与默认 OFF 均编译通过；normal/`-O` 聚焦测试各 `57/57`。
- no-launch receipt SHA-256 `E10DA2DBF2DDD3F7B427972223F4162BA886875F1445F47C4320BD375FC6B56D` 绑定 source SHA-256 `89D15B8ACB0E69E6C439D658582B63DC1F8AD11EC687089E5021A5961607D4DD`；open_kaishek 私有依赖同步为 `89ea4218151e2b340463c85d682ebd6b765cb651`。这只提供一次 R451 精确取证入口，不提升 truce/terms/action readiness；`GEN-034` 继续 unresolved、T1=90%。

## 2026-09-11：GEN-034 R451 pause OCR 遮挡

- R451 六行 source、动态 WarID 与 detach GREEN 后，顶部 in-game 通知占据 pause OCR 区域，导致 bridge 前 harness RED。report `51F38C32…9E559`、classification `85C21779…04D7A`；零 diagnostic/checkpoint/action/postwar，source 未变、cleanup GREEN、CK3=0。
- 窄修复仅在 pause click 后要求 3 秒 HUD 日期严格冻结，不能读取或日期变化仍 RED；adapter normal/`-O` 各 `30/30`。R452 admission `F89EE9D5…02CCF` 已绑定同一 source。
- 该故障不改变 GEN-034 的能力缺口或 readiness；`GEN-034` unresolved、T1=90%。下一步单次 R452 才能取得 default reader telemetry。

## 2026-09-11：GEN-034 R452 启动架构根因与最小修复

- R452 唯一 PID `132200` 完成六行 source 和 WarID `33554473` 的只读探针；公开 terms 仍只缺 `truce`。诊断两行均为 `collector-vtable-verified / callback_count=0 / last_failure=invalid_request`，证明 preview-entry capture 在回调前没有成功 arm。
- 根因是 live adapter 普通启动 CK3，待 source capture 后才用 `--pipe` 注入；该模式不调用只允许在主线程恢复前执行的 `XarCk3BridgePrepareStartup`，因此 preview-entry observer 从未安装。该结论取代继续更换 CB/input shape 的旧施工方向。
- R452 没有 checkpoint/action/postwar，source SHA-256 `89D15B8A…D4DD` 未变，cleanup GREEN、CK3=0；report/diagnostic/classification 为 `3EE2B4C5…D7C7` / `116553E6…F628` / `FF4A3928…EEFB`。
- adapter 已改为复用通用 runtime 的 suspended process：唯一进程校验后以无 `--pipe` injector 执行 Prepare，再恢复主线程；source 后仍以原 `--pipe` 启动同 PID MCP worker。runtime 纳入 manifest 哈希依赖，focused `31/31` GREEN。根实现 `8f1a522c0163796056ae8bc1281839b4fed8edf1` 与 T2 记录 `9505a1e30dcb24cfbd3c9dfdc63bd41a1c5fee5e` 已推送。当前仅 static-ready；下一步只运行一轮 R453 有界只读复验，`GEN-034` unresolved、T1=90%。

## 2026-09-11：GEN-034 R453 suspended identity harness RED

- R453 唯一 PID `26952` 在主线程挂起时只有清单 identity、没有 CIM/Toolhelp `ExecutablePath`；旧校验因此在 Prepare 前回收目标。主线程未恢复，source/bridge/query/mutation 均未开始，源存档未变、CK3=0。report/classification 为 `554D8D41…6458` / `520DFC89…1BD4`。
- 最小修复继续要求全局只有同一 PID，并在清单路径为空时通过共享 suspended-process 的保留 Win32 handle 读取 image path，再执行 exact path/hash 校验。R454 no-launch admission `5DBB22DE…6F46` READY；根提交 `69f0fbf5d7e7d723d12726064c1c23a9f1b4563e`、T2 记录 `cd6545fac7c284d63261798d3d1313bf771540b6` 均已推送。`GEN-034` unresolved、T1=90%，下一步只有一轮 R454 只读复验。

## 2026-09-11：GEN-034 R454 outer-owner startup-mode 合同 RED

- R454 唯一 PID `77472` 通过 suspended identity，完成 pre-resume Prepare 并恢复；外层 owner 随即拒绝新 `suspended-prepared-normal-event` receipt，因为旧合同仍写 `normal-event`。source/bridge/query/mutation 未开始，cleanup GREEN、CK3=0；report/classification 为 `F6EC3AAE…CC78` / `46FD0B0E…4122`。
- outer owner 与 fixture 已同步新字面值，其他模式继续 fail-closed；两模块 focused normal/`-O` 各 `40/40` GREEN。R455 admission `B43F5BD9…50BB` READY；根提交 `55702c167ed31c940a717484e0d939560397f4c3`、T2 记录 `24ee29b71af1c9c7ce36107f1019695f0d0b35e0` 均已推送。`GEN-034` unresolved、T1=90%，下一步只运行一轮 R455。

## 2026-09-11：GEN-034 R455 当前输入的 truce terms GREEN

- R455 唯一 PID `196216` 通过完整 source-first 只读链；WarID `33554473` 的两次同帧公开 terms 均返回 `evaluated_days=1825`，`terms_ready=true`。诊断两行均为 `traversal-complete`、一个有效 callback/context、`reader_returned=true`、`last_failure=none`、context 已销毁。
- report/capture/diagnostic/classification 为 `E4C3DCFC…DC69` / `DD33C69C…CD70` / `28CA8EB5…E774` / `DB6C587A…EDD8`；零 checkpoint/action/postwar，source 未变、cleanup GREEN、CK3=0。R450 的当前输入 truce observation RED 已关闭，不再重复该只读探针。
- `source_specific_loss_ready=false`、`comparison_input_ready=false`、`decision/action/automatic_surrender=false`，因此 `GEN-034` 仍 unresolved、T1=90%。根证据提交 `4bed362d87eda2028e745db6f03a8c44f7df401f`、T2 capability 记录 `18cb4fa3df8e4a04f353bf72f376a0f45179e3c6` 均已推送。下一入口是同一已验证启动链的一次正常 lifecycle：durable checkpoint、唯一 surrender、postwar cleanup/expiry 与 source-loss join。

## 2026-09-11: GEN-034 R456 post-checkpoint successor harness RED

- R456 unique PID `179252` reached a successful durable checkpoint after the same source-first and terms path. The harness then rejected snapshot/public/native revision changes even though PID, bridge generation, date `53187096`, episode, character, paused state, and active WarID `33554473` all remained stable. It submitted only two terms queries and `save-checkpoint`; surrender was never submitted. This adds no product RED.
- The minimal contract change retains the exact source-frame binding and records a separate post-save successor frame with strictly increasing revisions. Focused lifecycle/owner/adapter tests pass `48/48` under normal and optimized Python. R457 no-launch admission `3AAE6BA0...FD701` is READY; `GEN-034` remains unresolved and T1 remains 90% until that one bounded normal lifecycle supplies action/postwar/source-loss evidence.
## 2026-09-11: GEN-034 R457 diagnostic-build dependency RED

- R457 passed source, terms, durable save, and the successor gate, but the private capability check stopped before surrender. The selected R451 diagnostic DLL has both postwar candidate flags `OFF`; command history contains no surrender. This is an explained harness configuration RED, product RED=false, cleanup GREEN, CK3=0.
- The normal manifests again bind the prior postwar-capable DLL/injector, whose frozen CMake cache has both required flags `ON`. Focused tests pass `48/48` in normal and optimized Python; R458 admission is READY (`A270F42E...D20F`). `GEN-034` remains unresolved and T1 remains 90% until the bounded R458 action/postwar result.


## 2026-09-11: GEN-034 R458 checkpoint-to-action revision RED

- R458 passed its source, terms, and durable checkpoint gates with the postwar-capable DLL, then stopped before surrender. The successful save advanced the public revision, while the private continuation supplied the pre-save revision to the optimistic action gate. Command history ends at `save-checkpoint`; this is an explained harness RED, product RED=false, cleanup GREEN, CK3=0.
- The minimal fix passes the validated post-checkpoint successor revision to surrender. Focused lifecycle/postwar/owner/adapter plus directly changed pin/intake manifest tests pass `59/59` in normal and optimized Python, and R459 no-launch admission is READY (`45B981E2...26F1`). `GEN-034` remains unresolved and T1 remains 90% until the bounded R459 action/postwar result.


## 2026-09-11: GEN-034 R459 source-specific loss and comparison input GREEN

- R459 unique PID `123140` completed the entire bounded normal lifecycle. It submitted one typed surrender for WarID `33554473`, proved the six-event source set was 3000 soldiers before termination and destroyed to 0 afterward, and read the persisted native truce expiry `53227656` twice. Checkpoint `FAA32578...4E78`, cleanup, session identity, and every ticket check are GREEN.
- The production report is now policy-consumable through offline intake `43B0A053...4FE1`; `source_specific_loss_ready=true` and `comparison_input_ready=true`. The consumer needed only a production-schema alignment for `terms_ready` and preflight `live_executed`; focused tests pass `5/5` in normal and optimized Python, with no further CK3 launch.
- `GEN-034` remains unresolved and T1 remains 90%. The exact remaining providers are campaign dominance, owner-authored budget, and same-frame white-peace comparison. Three-way comparison, recommendation, decision, action, and automatic surrender remain false.

## 2026-09-12: GEN-034 active-war power query static-ready

- The existing production-live exact-build strategic-power query now admits a
  current active-war primary opponent as well as a declaration target. It
  returns an explicit source classification and keeps the native payload, DLL,
  one-target bound, paused-frame binding, and fail-closed behavior unchanged.
- Focused contract/driver/service/strategy/MCP tests pass `23/23` in normal and
  optimized Python. No CK3 instance was started for this small interface
  package; current round R469 and old round R468 remain terminated.
- This opens one bounded read-only query against R459's durable pre-surrender
  checkpoint. Until that live value exists, campaign dominance remains
  incomplete. Owner-authored budget and same-frame white-peace comparison are
  also still missing, so `GEN-034` stays unresolved and T1 stays at 90%.

## 2026-09-12: GEN-034 R470 native admission RED

- R470 reached the exact-build paused checkpoint for WarID `33554473` and
  primary opponent `28551`, but its first official MCP query failed with
  `application-main war-entry query failed:target_not_declarable`.
- The live result disproves the static assumption that only Python restricted
  the query to declaration targets. The native frame and reader also enforce
  that restriction before calling the strategic evaluator. The second query
  was not attempted; there was no retry, time advance, or mutation.
- Report SHA-256 is `CCF29894...E022D`; source checkpoint
  `FAA32578...4E78` and restored driver state `A5DB3F1E...4B5E` are unchanged,
  cleanup is GREEN, current round R470 and old round R469 are terminated, and
  CK3=0.
- The next implementation is limited to native admission of same-frame active-war
  primary opponents plus focused tests and one bounded R471 query. Campaign
  dominance remains unavailable; owner-authored budget and same-frame
  white-peace comparison are also absent. `GEN-034` remains unresolved and T1
  remains 90%.

## 2026-09-12: GEN-034 active-war native admission correction

- The native frame now freezes declaration targets and active-war primary
  opponents separately; the one-target reader admits either source while
  retaining all existing exact-build, main-thread, paused-frame, identity,
  double-sample, and wire contracts.
- Fresh MSVC Release compile/link completes `545/545`; the two directly
  affected CTests pass `2/2`. Candidate DLL SHA-256 is
  `65C14FE2...B61EF`, injector SHA-256 is `C4CE2042...E389`, and the header
  dependency gate is GREEN. No CK3 was started for this package.
- This is static-ready only. One bounded R471 read-only query must replace the
  R470 RED before campaign dominance can consume the value. `GEN-034` remains
  unresolved, T1 remains 90%, T0 P1 remains 6/9, and P2 remains `LOCKED`.

## 2026-09-12: GEN-034 R471 active-war strategic-power primitive GREEN

- R471 produced two identical official MCP results on paused snapshot
  `native:3`: player `29829` power `13075500000`, opponent `28551` total
  `16770900000`, ratio `128262/100000`, and target source
  `active_war_primary_opponent`. Every native readiness bit is true.
- The report's RED is confined to a runner audit that read absent `history`.
  Canonical `native_command_history` proves exactly two successful read-only
  query rows and no mutation/time advance. The helper correction passes focused
  normal/optimized `1/1`; offline reclassification is GREEN without a CK3
  restart. Report/reclassification SHA-256 values are
  `F4676762...E7CD` / `D8F43EAB...24C9`.
- This closes the strategic-power observation provider as a production-live
  primitive, but campaign dominance still needs a policy-level certificate.
  Owner-authored budget and same-frame white-peace comparison are also absent.
  `GEN-034` remains unresolved and T1 remains 90%.
- Current round R471 is terminated, old round R470 is terminated, and CK3=0.
  T0 P1 remains 6/9 and P2 remains `LOCKED`.

## 2026-09-12: G2-M2 exact-build event registry consumer static-ready

- The generic one-life planner previously ignored all shared vanilla-event safe choices and always used its death/cancel/native-order fallback when
  `semantic_decision_ready=false`. For `tgp_travel_events.0030`, that fallback would choose native 0 even though the reviewed contract requires the
  bounded authored 2/native 1 route.
- The new direct-projection consumer binds the observed event root to the current played character and checks the exact saved-scope names, counts
  and types together with snapshot/rendered option counts, native order and enabled projection. A matching record produces its
  registered choice; a known drift remains paused, while an unknown key keeps the existing fallback.
- Contracts that require variants, dynamic option prefixes, occurrence accounting, deferred choice or scenario invalidation remain explicitly blocked.
  This package is `static-ready / live=false`; normal and optimized focused tests are each `30/30` GREEN. G2-M2 is now in progress, but the fixed
  program denominator remains `0/8` until structured effects, campaign scoring and three natural event outcome loops are live.

## 2026-09-12: G2-M2 played-character stress observation static-ready

- `tgp_travel_events.0030` can now be selected from its exact-build registry contract, but the generic snapshot previously exposed no
  material state that could verify its medium stress-loss outcome. The only stress reader was embedded in war-exit terms and therefore
  unavailable to a travel event.
- The native state snapshot now publishes additive `played_character.stress_points` from the already used generation-checked
  `CCharacter+0x1A8 -> extension+0x2F8` path. The Python driver validates and preserves non-negative values while accepting legacy
  snapshots that omit the field.
- Release DLL and `game_access` fixture compile/link/run GREEN; Python normal/invalid-value tests are `2/2` GREEN. This remains
  `static-ready / live=false`: a single future paused read must prove the production field. The planner/service/native-action chain now
  binds exact `.0030` option 2 to the same-character before/after values; stress increase, identity drift or a missing ready observation is
  RED, while unchanged stress cannot count as material evidence. Focused normal/optimized tests are `8/8` GREEN. G2-M2 and global G2 remain
  `in_progress` and `0/8` respectively pending the bounded live outcome and the other two event loops.

## 2026-09-13: G2-M2 first option-variant consumer static-ready

- R374 froze `natural_disaster.7031` with rendered native indices `[0,2]`; exact source records `[2]`, `[0,2]` and `[0,1,2]` as the only
  supported projections, all retaining the source-reviewed terminal warning route at native 2.
- The registry consumer now resolves only this event's current projection before applying the existing scope, shown/enabled and root checks.
  Unregistered shapes remain blocked, and every other variant-bearing event still requires an explicit reviewed consumer package.
- Focused policy tests pass normal/optimized `8/8`. This is `static-ready / live=false`; it uses frozen evidence and launches no CK3 process.
  G2-M2 remains in progress and global G2 remains `0/8` until three natural event action/outcome loops are production-live.

## 2026-09-13: G2-M2 selected-choice structured effects static-ready

- The shared read-only event knowledge response now publishes one versioned selected-choice effect profile for exact
  `tgp_travel_events.0030` and `natural_disaster.7031`. The first records authored base stress loss `-30` plus the observable
  non-increasing stress relation; the second separates its non-material warning tooltip from the unavoidable, currently unobserved
  common-after character-variable write.
- The registry policy copies a profile only when its selected native index matches the resolved exact choice. The `.0030` material
  comparator consumes the profile's observable postcondition instead of maintaining a duplicate metric/relation table.
- Focused normal/optimized tests are each `27/27` GREEN. Status is `source-structured / static-ready / live=false`: character stress
  modifiers prevent an exact runtime `-30` promise, and generic event-context-v2 effect extraction remains open. No CK3, recorder,
  desktop input, DLL or mod tree was used; global G2 remains `0/8`.
## 2026-09-13: G2-M2 second material event comparator static-ready

- R414 already supplies a real pre-selection frame for `trait_specific.8001` with player ROOT, empty saved scopes and enabled native options
  `[0,1]`. Exact source gives native 1 `add_gold = minor_gold_value`; the dynamic value depends on monthly income, treasury and era, while
  its authored whole-gold minimum is 15. A fixed expected runtime delta would therefore overstate current observation.
- The state snapshot now publishes additive top-level `played_character_gold` from the previously closed exact-build
  `CCharacter+0x1A8 -> extension+0x100` leaf as signed Q100000. Planner, native action and outcome service bind the same full CharacterID,
  starting snapshot/revision and pre/post raw values. Only a strict increase is a verified material change; unchanged/decreased balances,
  identity drift or missing readings do not pass.
- The Release DLL and native `game_access` fixture build and run GREEN; focused Python normal/optimized tests are each `30/30` GREEN.
  Status is `static-ready / live=false`. One bounded `.8001` action is the only live proof authorized for this path; no single-event long run
  is required. G2-M2 and global G2 remain `in_progress` and `0/8` pending three production event loops.
## 2026-09-13: G2-M2 third material event path static-ready

- `death_management.1007` already has R374 historical action evidence: exact player-root/no-killer three-scope projection, one native option,
  and event instance advance. Its sole source effect is `stress_impact` with authored `minor_stress_impact_gain=20`; the after block is a
  display-only tooltip.
- The direct registry consumer now admits this key's `unique_character_scope_excludes` only when the typed dead-character full ID differs from
  the player. Its structured profile drives the existing same-character stress comparator with a `non_decreasing` relation: positive delta is
  material, unchanged is honest non-material evidence, and a decrease/binding drift does not pass. Other extended-scope contracts remain blocked.
- Focused normal/optimized policy/profile/comparator tests are each `25/25` GREEN. Six deterministic stale inventory assertions exposed by the
  earlier 188th record were synchronized from `187/333` to `188/334`; their affected modules pass normal/optimized `45/45`. This is
  `static-ready / live=false`. The R374 hot park has no durable checkpoint, so live material proof is encounter-driven and must not trigger a
  dedicated long run. All three G2-M2 target events now have static material comparators; three production material loops and campaign scoring
  remain open, so global G2 stays `0/8`.
## 2026-09-13: G2-M2 bounded campaign utility profiles static-ready

- The three exact target events now publish `xar.ck3.vanilla-event-campaign-utility/v1`. Each profile records a bounded objective,
  source-reviewed ordinal rank, discrete utility facts and alternative reasons. `.0030` and `.8001` both rank native 1 first, directly
  excluding a fixed-first-option policy; `.1007` is marked as the sole legal route and retains its adverse stress direction.
- The registry copies a profile only when its native index matches the proven choice. `one-life-turn-v1` publishes it as
  `event_campaign_utility` and marks campaign utility ready for that decision. `cross_event_numeric_score` stays null,
  `calibration_status=not_calibrated` and `semantic_optimal=false`, so no unmeasured exchange rate between stress, gold, traits and time is
  invented.
- Focused query/policy/planner tests pass normal/optimized `26/26`. This closes the static objective/utility input for the three G2-M2 target
  events. The completion gate remains three production recommendation/action/material loops; generic effect extraction, dynamic goal switching
  and cross-domain numeric calibration remain breadth/quality debt rather than substitutes for those live outcomes. Global G2 stays `0/8`.

## 2026-09-13: G2-M1 direct landed-vassal identity observation static-ready

- The production-live campaign-root primitive already identifies the current ruler, primary title, capital and liege chain, but it did not
  enumerate the ruler's direct landed vassals. The only existing roster was an offline save-topology candidate and is not eligible as paused
  production truth.
- The exact-build reader now walks the frozen Character storage in the same application-main double observation. It requires each admitted row
  to be alive, generation-valid, native-immediate-vassal to the current player and backed by a generation-valid primary title. The wire publishes
  a sorted duplicate-free `direct_landed_vassal_character_ids` vector; any read or second-sample failure returns typed
  `direct_landed_vassals_unavailable` rather than a partial roster.
- Release DLL compile/link, direct native reader and source-contract fixtures are GREEN. Python driver/service/MCP/live-harness focused tests pass
  normal/optimized `30/30` each. The field remains `static-ready / live=false` because the two historical campaign-root artifacts predate it.
  One future bounded paused read may close the production primitive while sharing an already-required G2 session; no dedicated long run is
  required.
- G2-M1 is now `in_progress`, but global G2 remains `0/8`. Realm-neighbor identity/adjacency, the canonical entity directory, aggregated ruler
  and realm state, minimum alerts and the turn-bundle consumer remain open; the direct-vassal vector alone does not satisfy the visible M1 gate.

## 2026-09-13: G2-M1 adjacent external Province-holder identity static-ready

- The next missing campaign-root input was an exact paused identity for at least one holder across the player's territorial boundary. The
  implementation extends the existing query instead of adding another mailbox round trip: it scans the frozen Province array and map-node
  adjacency rows, resolves the native Province holder, and classifies the holder's immediate-liege chain against the current player.
- `adjacent_external_province_holder_character_ids` contains sorted, duplicate-free, living generation-valid holders of Provinces directly
  adjacent to the player subrealm. The player, direct and indirect subrealm vassals, unowned Provinces and water rows cannot enter the vector.
  This is an identity input for the future entity directory; it does not claim that every row is an independent realm ruler or top liege.
- Exact leaf `0x220C3F0..0x220C49F` is frozen at SHA-256 `531558C7...B8D8`; the ABI asset also freezes Province array and adjacency layout.
  Release DLL compile/link and direct reader/source-contract fixtures are GREEN. Python driver/service/MCP/live-harness focused tests pass
  normal/optimized `30/30`; candidate DLL is `2,615,808` bytes / `35079262...5B3834`.
- Status remains `static-ready / live=false` and global G2 remains `0/8`. One future already-required paused G2 session may verify both new
  identity vectors together; no dedicated long run is warranted. The next M1 gap is canonical holder-to-title/top-liege entity mapping plus
  minimum ruler/realm/succession alerts and the turn-bundle aggregate.

## 2026-09-13: G2-M1 relationship entity-directory identity search static-ready

- Candidate discovery no longer requires a caller to pre-supply the player, direct-vassal or adjacent-holder IDs. The independent read-only
  `ck3_search_entities_v1` MCP tool consumes exactly one already-gated campaign-root query, then applies a declarative relationship filter,
  complete CharacterID ordering and keyset pagination.
- Each row exposes component-level `available`, `unavailable` or `not_applicable` state. Self components reuse the same source frame;
  direct-vassal immediate/top lieges are exact consequences of the native enumeration rule; related title/capital and adjacent-holder lieges
  remain unavailable until the next native batch reader exists. Directory readiness therefore covers identity/relationship consumption and
  reports title/realm component completeness separately.
- Contract/service/official MCP SDK focused tests pass normal/optimized `19/19`. This package adds no native mailbox, DLL, mutation, CK3 round,
  recording or desktop input. It remains `static-ready / live=false`; G2-M1 remains in progress and global G2 remains `0/8`.
- The next construction input is a same-frame full-generation batch resolution of related CharacterIDs to primary title and native
  immediate/top liege. It will canonicalize boundary Province holders to realm identity before minimum alerts and the core turn bundle are
  considered ready.

## 2026-09-13: G2-M1 related-character title and realm identity static-ready

- `campaign-root-context-v1` now batch-resolves the exact union of direct-vassal and adjacent-holder IDs in the same double observation. Each
  sorted row carries the source relationship role, required primary title/tier, legal-null capital, native immediate/top liege and independent
  bit. No new RVA or mailbox command was needed.
- Full-generation Character/Title round-trips, Province pointer identity and role-specific liege invariants are mandatory. An adjacent holder
  remains outside the player subrealm but may share the player's top liege as a sibling vassal; callers may group by top liege without losing
  the original boundary-holder role.
- Any row failure returns typed `related_character_contexts_unavailable` for the whole root frame. Release DLL build/link, direct native reader
  and source-contract executables are GREEN; focused Python normal/optimized tests pass `35/35`.
- `ck3_search_entities_v1` now exposes complete primary-title and top-liege components for its current relationship scope. Status remains
  `static-ready / live=false`, M1 remains in progress and global G2 remains `0/8`; minimum ruler/realm/succession alerts and the turn bundle are
  the next implementation gap.

## 2026-09-13: G2-M1 primary-title succession observation

- The existing campaign-root query now exposes `primary_title_succession_character_ids` from the exact-build ordered Title succession span.
  It validates every full-generation CharacterID and binds the whole native-order vector to the existing application-main double observation.
- This removes the prior lack of a real input for the minimum primary-title heir alert. It does not answer per-title partition, succession laws,
  claims, game-over risk or continuation after death; those remain G2-M3 scope.
- Release DLL plus direct native reader/source-contract fixtures are GREEN and focused Python normal/optimized tests pass `35/35`. The field is
  `static-ready / live=false`; it must be sampled only during a future already-required paused G2 session. M1 and global G2 remain open at
  `in_progress` and `0/8` until the minimum ruler/realm/succession alerts and `ck3_query_turn_bundle_v1` are delivered and live-checked.

## 2026-09-13: G2-M1 first turn-bundle aggregate

- `ck3_query_turn_bundle_v1` now binds one cached semantic snapshot to one campaign-root query and publishes six planner-facing domains without
  additional native RPCs. It provides minimum alive/landless, direct-vassal/adjacent-holder and primary-title heir alerts from real existing
  observations; event/pending and compact war summaries are included when their normalized snapshot surfaces exist.
- The bundle deliberately remains `status=partial` and `readiness.ready=false`: income, health, domain, council, faction and partition
  observations are still absent. This closes an aggregation gap, not the M1 live gate or its complete state breadth.
- Focused normal/optimized tests pass `26/26`, including official MCP listing/call and binding/identity drift rejection. No CK3 or desktop resource
  was used. The next construction entry is an exact-build read-only income/domain slice rather than another unavailable-only wrapper.

## 2026-09-13: G2-M1 player monthly income observation

- The existing war-exit implementation had already proven `0x28DBE90` as the complete monthly-gold-income evaluator and recorded a paused case
  where `extension+0x2B0` lagged it. `campaign-root-context-v1` now reuses the evaluator for the played Character, requires the caller output
  pointer, generation-revalidates the Character and includes signed Q100000 income in the complete two-sample frame equality gate.
- A failed call or identity/value drift returns whole-frame `player_monthly_gold_income_unavailable`. The bundle consumes this observation and
  marks ruler resources ready only with current gold plus income; it still reports full readiness false for health, domain, council, faction
  and partition.
- Native reader/source-contract fixtures and focused normal/optimized Python suites are GREEN; candidate Release DLL is `2,636,800` bytes /
  `98FC2431...0566C2`. This is `static-ready / live=false` and will share a future bounded paused G2 read. It does not create a dedicated run or
  change G2 `0/8` / GEN-034 `2/4`.

## 2026-09-13: G2-M1 player domain capacity observation

- Stock HUD uses `Character.GetDomainSize/GetDomainLimit`. Their exact-build reflection registrations resolve to core RVAs `0x260BA50` and
  `0x260BA20`; campaign-root now calls those native functions, generation-revalidates the player and double-samples both values.
- The turn bundle's domain component now reports size, limit, free capacity and over-limit count with `realm_domain_ready=true`. This closes only
  the current capacity input. Holding identities, building state, construction and grace-period penalty semantics remain explicit later work.
- Native fixtures and Python normal/optimized `39/39` are GREEN; status is `static-ready / live=false`. M1 still needs health, council, faction,
  partition and one shared bounded paused read, so global completion remains `0/8`.

## 2026-09-13: G2-M1 targeting-faction minimum alert

- The stock `has_targeting_faction` trigger registration resolves to exact-build evaluator `0x283FAE0..0x283FB51` (SHA-256
  `7A4C1EED3FF52B5573AD7598350DB3270954E38FB0F1CF872080851D4C00ECEE`). It validates the full-generation Character, reads
  `CCharacter+0x1B8` land state and treats the signed count at `land_state+0x12C` as threatened exactly when nonzero.
- `campaign-root-context-v1` now double-samples a nonnegative `player_targeting_faction_count` and returns typed
  `player_targeting_factions_unavailable` on pointer, identity, range or sample drift. The turn bundle exposes count/threatened,
  `alerts.faction_threat` and `realm_faction_alert_ready=true`.
- The slice deliberately excludes faction identities, types, members, power, discontent, demands and deadlines. Native reader/source-contract
  fixtures and focused Python normal/optimized `40/40` are GREEN. Status is `static-ready / live=false`; it will share the next bounded paused
  G2 read instead of creating a dedicated long run. M1 still lacks health, council and partition, and global G2 remains `0/8`.

## 2026-09-13: G2-M1 player health observation

- `Character.GetHealth` is frozen through exact-build reflection name RVA `0x4324C10`, registration `0x509CB0..0x509E12`, thunk
  `0x2622660..0x2622696` and core `0x2619AD0..0x2619B18` (SHA-256 `B6E37007...A89840`). Campaign-root now calls that core, requires the
  caller output pointer, generation-revalidates the played Character and double-samples signed Q100000 health.
- The turn bundle publishes the raw value, `dying_or_worse / below_fine / fine_or_better` and `ruler_health_below_fine` using the stock
  `death_chance_dying_health=1.5` and `fine_health=3.0` thresholds. No treatment or prognosis policy is claimed.
- Native fixtures and focused Python normal/optimized `42/42` are GREEN. Status is `static-ready / live=false`; the next shared bounded paused
  G2 read will verify it with the other pending campaign-root fields. M1 now lacks council and partition plus two-scene live acceptance, so
  global G2 remains `0/8`.


## 2026-09-13: G2-M1 held-title partition observation

- Exact-build evidence proves `CCharacter+0x1B8 -> land_state+0x1E0` is the
  full-generation held-title ID vector and that the stock My Realm builder
  groups titles by each `CLandedTitle+0x278` first successor.
- Campaign-root now publishes an all-or-nothing county-or-higher title/heir
  vector with title, holder, tier, successor and primary-title consistency
  gates. Turn bundle derives the current split-risk state without claiming
  succession law, claims or post-death outcome.
- Native reader/source-contract fixtures and focused Python normal/optimized
  `42/42` are GREEN. Status is `static-ready / live=false`; this field joins the
  existing bounded shared campaign-root live read. M1 now lacks council plus
  that shared live acceptance, so global G2 remains `0/8`.

## 2026-09-13: G2-M1 typed council observation

- The exact-build reader consumes the land-state active-task ID vector and
  publishes every materialized council position with generation-validated
  incumbent/owner identities, stable task and position keys, typed targets,
  frozen state and typed progress. Five standard landed, non-nomadic core
  positions are complete; auxiliary vacancies remain explicitly incomplete.
- The campaign-root contract and turn bundle preserve the component. Supported
  scenes can make `realm_council_ready=true`; out-of-scope landless or nomadic
  scenes keep the root available while the component is typed unavailable.
- Native Release reader/serializer and source-contract fixtures are GREEN, the
  bridge DLL links, and Python normal/optimized `47/47` are GREEN. Status is
  `static-ready / live=false`; M1 now lacks only its existing bounded two-scene
  paused live gate, and global G2 remains `0/8`.

## 2026-09-13: G2-M1 bounded two-scene production closure

- Reusable runner commit `411c5441d8f6a4d2e5b12f7e1e0c0528b8aaf301` binds one immutable source save, one managed CK3 process, two direct root reads plus one turn bundle per scene, and one typed player switch. Focused harness tests pass normal/optimized `19/19`.
- Old round R638 retained a real product RED: both characters returned `direct_landed_vassals_unavailable`. The valid exact-build, same-process switch, paused date, unchanged source and cleanup evidence isolated the new full Character-storage scanner. It incorrectly rejected readable non-null entries whose object generation no longer matched their slot.
- Fix commit `700fae3fcca5af1ebfee26d4cbaf26d3c5f0a2a9` follows the frozen stock enumerator: stale/reused generations are skipped, unreadable pointers still fail, and every admitted member still round-trips its full CharacterID. The directly affected native fixture is GREEN and includes a non-null stale-generation control.
- New round R639 is GREEN in one PID/connection generation on unchanged date `53178264`. Independent ruler `29829` and vassal ruler `36108` both have ready roots and turn bundles; relationship vectors, related contexts, partition and six occupied council tasks per scene are observed. Source SHA-256 stays `9104CCB8...12CC63`; cleanup proves the process tree gone.
- The 444,994-byte artifact at `Z:\ck3_mod_rewrite_process_assets\g2-m1-r639-700fae3\g2-m1-two-scene-live.json` has SHA-256 `CFF681146A344AE18FDEB36C20BDAEAFC2A30344023CC7827E9A77006C3530DB`. G2-M1 is complete and global G2 advances to `1/8`. Deeper faction data and broader rank/government matrices remain later milestones rather than reopening M1.

## GEN-034 utility-model prerequisite update (2026-09-13)

The former wait for a separate owner-approved utility file is closed as a
workflow blocker. The active path now uses the versioned, replaceable
`raiktor_exit_utility_v1.json` baseline and strict provider; model and budget
bytes are independently hash-bound, and an operator override must bind the
default model identity. This is strategy configuration rather than native-AI
equivalence or live evidence. GEN-034 remains `2/4`: C still requires one
same-frame narrow white-peace observation plus evaluation, and D still requires
one recommendation, one action and the bounded postwar/cold-restore checks.

## GEN-034-C narrow white-peace input update (2026-09-13)

- The white-peace terms producer is now `static-ready`: it strictly binds the
  existing safe options query, narrow Raiktor terms query and surrender session
  aggregate, then projects only values proven by the exact-build white-peace
  branch or identical shared expressions. The broad loaded-effect preview RED
  is unchanged and its production dispatch remains disabled.
- Focused normal/optimized tests pass `6/6`; the output already feeds the
  existing same-frame terms comparator. The remaining C blocker is one bounded
  production frame plus versioned utility evaluation. Therefore GEN-034 stays
  `2/4`, with D still requiring one recommendation, one semantic action and the
  postwar/checkpoint/cold-restore verification.

## GEN-034-C immediate-exit evaluator update (2026-09-13)

- The static-ready narrow projection now feeds a strict same-unit evaluator for white peace and surrender. It binds the exact surrender aggregate, repository budget profile and utility model and records per-feature contributions, uncertainty penalties and hard-budget eligibility.
- The evaluator preserves seven white-peace and nine surrender effects as unobserved; current regiments are not misreported as proven surrender losses. Focused normal/optimized projection and evaluator tests pass `10/10`.
- This output does not value continue, recommend among three exits or authorize an action. C remains blocked only on one bounded production frame, so GEN-034 stays `2/4`; D remains the later one-recommendation, one-action and postwar/cold-restore package.

## GEN-034-C bounded live runner update (2026-09-13)

- The reusable managed runner for the remaining C gate is static-ready. It allows exactly one termination-options read and one narrow terms read at the same paused revision, rejects any additional native command, and keeps broad preview, time advance and all exit actions disabled.
- Focused normal/optimized tests pass `4/4`. The next step is one no-launch identity admission and, only if GREEN, current round R640 against the immutable R459 checkpoint.

## GEN-034-C first live input and consumer repair (2026-09-14)

- Current round R640 did not launch CK3 because the system Python lacked `win32api`; its 8,057-byte harness RED is retained at `Z:\ck3_mod_rewrite_process_assets\g2-gen034c-r640-dc42838\report.json`, SHA-256 `656C26958FF36D3FEB0FF90623F15D9324B9BEEAEAD90578C753CF78F240658C`.
- Current round R641 used the shared project environment and completed exactly one options query followed by one narrow terms query in the same paused production frame. Exact-build admission and cleanup were GREEN, but the consumer rejected the options object because `normalize_war_termination_options()` emitted `source=native` and did not accept that same normalized shape as input. The 94,506-byte RED report has SHA-256 `AAF02DFB7B678C1889FB14D6C37DCBE7A48A907FE68DB0D23272F4BA33D15370`; retained driver state has SHA-256 `10792DC261D8D51083FF2A4C570696CF70AA703A1998902551EB63E45FCC0807`.
- The focused repair makes the normalizer idempotent only for the canonical `source=native` decoration and continues to reject every other source or extra key. The live composition helper now returns the provider's typed `evidence_required` projection when white peace is unavailable and does not call the utility evaluator on incomplete evidence. Focused normal/optimized contract, projection and runner tests pass `18/18` per mode.
- R641's actual frame is zero-day and zero-score; its native validator and final recipient response make white peace unavailable. GEN-034 remains `2/4`. One bounded rerun must first preserve that typed blocker, after which C needs the smallest reachable paused frame where white peace is actually available; broad preview and every mutation remain closed during C.

## GEN-034-C typed negative live closure (2026-09-14)

- Current round R642 stopped in no-launch preflight because the handoff used `xar_bridge_injector.exe` instead of the real `xar_ck3_bridge_injector.exe`. Current round R643 used the correct binary, started one CK3 process, and timed out before native readiness while the debug log still showed ordinary content loading; cleanup and source invariants are GREEN. Its 9,589-byte report has SHA-256 `BC1F0F89C05734CA56AB7B5FFC2E0CD46D2B03A0E28E516069E817B7155B6F54`.
- New round R644 extended only the cold-readiness budget. It reached CharacterID `29829`, WarID `33554473`, date `53183856` and completed exactly the options/terms read pair. All 13 exact-build checks, official MCP envelopes, same paused before/after binding, exact two-command history delta, cleanup and source hashes are valid. The 3,509,196-byte report is `Z:\ck3_mod_rewrite_process_assets\g2-gen034c-r644-63bb714\report.json`, SHA-256 `9844B817995A876C1B48C7BDDF42826B4866F8E8C9680EB79F0EA53D4FECBA0B`; driver-state SHA-256 is `7D92159CC19E988600A713A2BA0217A4B99133BD18183ED4FD1D9765EEB9845E`.
- The projection now correctly returns `evidence_required` with exactly `white_peace_native_option_unavailable` and `white_peace_final_recipient_response_unavailable`; the evaluator is absent and no action or time advance occurred. This closes the negative-path live proof and supersedes R641 for consumer behavior, but does not close C or change GEN-034 `2/4`.
- Do not repeat this zero-day frame. The next input must reuse an existing Raiktor checkpoint at the already-frozen white-peace admission horizon if present; only if absent may a bounded preparation runner advance and save that one war. Broad preview stays disabled, and the C run remains two-read/no-action.

## GEN-034-C 135-day evidence and 365-day preparation seam (2026-09-14)

- Current round R645 reused the R456 pre-action source at date `53187096` and
  observed `war_duration_days=135`. White peace remains unavailable in the
  exact native option and its final recipient response, so this is retained
  typed negative evidence rather than a C completion. Report SHA-256 is
  `C6858122FCC4120E4715E220D4B711BF05180B741C294185A69C4BFE51A201FE`;
  cleanup and source invariants are GREEN.
- The 135-day frame will not be rerun and no intermediate dates will be
  enumerated. The reusable horizon runner advances only to target date
  `53192616` (365 war days), stops on the first event/identity/war/pause RED,
  permits one resume and at most one pause, and saves only after one native
  option query proves white-peace validation and final-response availability.
  It contains no event-selection or war-termination call. Focused tests pass
  normal/optimized `4/4`.
- GEN-034 stays `2/4`; the next evidence attempt is the one bounded preparation
  run. No public MCP schema, native ABI or open_kaishek consumer changed.

## GEN-034-C R646 deterministic event interrupt (2026-09-14)

- The first horizon attempt advanced once from war day 135 and encountered
  active event instance `7` at day 158/date `53187648`. It stopped before any
  option, termination action or checkpoint write. Exact-build proof, immutable
  source and cleanup are GREEN. Retained report SHA-256 is
  `47B9F94BFDAA12DB47435351F958C3A6C608745B82AE942D5A3782AC17808AA9`.
- The base wrapper labelled the failed sequence generically as a paused
  double-sample failure; snapshot evidence makes the event interrupt explicit.
  The horizon runner now emits `event_encountered_before_horizon`, pauses once,
  queries the existing exact-build current-event context and saves the
  unresolved frame. Event selection remains absent from source and policy.
- R646 does not satisfy the vanilla-event SOP because the lossy snapshot lacks
  a definition key. The next bounded run exists only to capture that same event
  through the official MCP and freeze it for source review; it cannot continue
  toward the horizon or choose an option. GEN-034 remains `2/4`.

## GEN-034-C R647 exact event capture (2026-09-14)

- Current round R647 issued the same sole resume, paused on the first interrupt,
  queried `ck3_query_current_event_window_context_v1` and saved the unresolved
  event. It identified exact-build `chancellor_task.1104`, instance `7`, at
  date `53187648`; the root is CharacterID `29829`, all five saved scopes are
  typed Character scopes, and native option `0` is the only shown/enabled
  continuation. No event option or war-exit action was submitted.
- Exact source SHA-256 is
  `EAF95612E4AEC6BF0CEDBC1ACA1C66C8087DD280BC42A60296F824437A5A46EB`.
  `.1103` directly triggers `.1104`, whose sole option applies only the
  authored timed neighbor-opinion modifier. The reusable vanilla-event registry
  already records the event, selected option and the same root/role relations.
- The retained RED report is 120,058 bytes at
  `Z:\ck3_mod_rewrite_process_assets\g2-gen034c-r647-1975271\report.json`,
  SHA-256 `B9EC5A960EDBD96A4B82E88F530FAF9E4362DB8C94FD43AA99D70481EFE35DA7`.
  Its unresolved checkpoint is 69,333,480 bytes, SHA-256
  `01CAACED503F803E201CA4646D598DA0AAA152452E198D8CE719A77A48DB49B2`.
  Cleanup and immutable-source checks are GREEN.
- GEN-034 remains `2/4`. The immediate blocker is limited to consuming three
  already-versioned relationship fields: exact `character_scopes`, alias
  `character_scope_matches_any`, and distinct
  `character_scope_differs_from`. That consumer must fail closed on missing,
  ambiguous or drifted Character identities before the checkpoint can proceed.

## GEN-034-C event relationship consumer (2026-09-14)

- The exact-build shared contract now freezes all five saved-scope names and
  Character types together with native option projection `[0]`. The direct
  registry policy can evaluate its player binding, non-player exclusions,
  chancellor aliases and distinct neighbor relation; this admission is limited
  to source-reviewed `chancellor_task.1104`.
- Normal and optimized focused suites each pass `24 tests / 200 subtests`.
  Offline replay of the retained R647 MCP context returns only option 1 with no
  failed check. Drift in the liege binding, either alias or neighbor relation
  is covered and remains blocked without an option number.
- This closes the Python consumer gap but supplies no live mutation evidence.
  GEN-034 remains `2/4`; the next action is one managed event acknowledgement
  from the R647 checkpoint, followed by a successor checkpoint or the next
  typed interrupt. No native ABI, public MCP wire or open_kaishek shape changed.

## GEN-034-C bounded registered-event continuation runner (2026-09-14)

- `run_registered_event_checkpoint_continuation.py` is static-ready. It
  cold-restores a path/hash-bound event checkpoint, queries the official current
  event context, accepts only a shared-registry `recommended` option, selects it
  once and saves one successor checkpoint. Event instance, revision, key,
  CharacterID, WarID and date are bound before mutation.
- The postcondition requires the event to close with the same paused character,
  date and active war. A chained event, identity drift or policy rejection is a
  RED before checkpoint promotion. Time advance, broad preview and all three
  war-exit actions are absent. Focused normal/optimized tests pass
  `14 passed / 7 subtests` per mode.
- This runner reuses the existing official MCP and versioned registry. It adds
  no public protocol or native ABI and does not affect open_kaishek. GEN-034
  stays `2/4` pending one bounded live use on the R647 unresolved checkpoint.

## GEN-034-C registered-event no-launch admission (2026-09-14)

- The path/hash/identity preflight is GREEN for the R647 unresolved checkpoint
  (`01CAACED...49B2`) and its current driver state (`FDAA47C6...48D9`). It also
  binds the exact executable, DLL, injector, product tree, CharacterID `29829`,
  WarID `33554473` and date `53187648`.
- The 3,462-byte no-launch report is
  `Z:\ck3_mod_rewrite_process_assets\g2-gen034c-event-continuation-preflight-5ef1cc7.json`,
  SHA-256 `228692C3518AAA37A1F14CB2AF75A669A45A533C30F0C3CB6EDAB80DCEE3AD65`.
  It proves `ck3_started=false` and `profile_prepared=false`.
- The owner has placed a temporary CK3-use hold. This preflight creates no CK3
  round and consumes no screen resource. GEN-034 remains `2/4`; continue with
  offline implementation and retain the admitted live command for later.

## GEN-034-D v2 recommendation contract (2026-09-14)

- The old full campaign-forecast v1 is no longer the only recommendation path.
  A new bounded provider uses the existing production-capable immediate-exit
  utility result and a same-frame v2 measured-power certificate. Continue is a
  versioned strategy baseline minus the model's relation penalty, explicitly
  not a battle or campaign forecast.
- A unique margin winner maps to one typed action; static fixtures cannot emit
  it. The provider binds snapshot/revisions/date/connection/episode/PID/WarID
  and both characters, and records route-specific postconditions without
  claiming submission or verification. Normal/optimized focused tests pass
  `7/7`.
- Remaining blocker: resolve the queued event, reach the C horizon, take two
  same-frame power reads, then execute one recommendation and verify the action,
  material postconditions, checkpoint and cold restore. GEN-034 remains `2/4`;
  G2 remains `1/8`; no CK3 process was used for this package.
- The same-frame read phase is now executable as one bounded managed runner. It
  admits exactly one option query, one terms query and two power queries, then
  freezes the production recommendation and planned action without submitting
  it. Normal/optimized focused tests pass `4/4`. Remaining implementation is
  the one-action/postcondition/checkpoint/cold-restore executor; live use stays
  queued under the owner's CK3 hold.
- Exact action admission is now implemented offline. It verifies the
  recommendation hash, complete paused identity, empty event slot and current
  action/capability advertisement before emitting one revision-bound
  authorization. It is integrated into the recommendation report but performs
  no mutation. Related normal/optimized tests pass `18/18`; the remaining D
  blocker is execution plus observed postconditions and cold restore.

## GEN-034-D post-action prestige observation (2026-09-14)

- The generic paused state snapshot now publishes additive signed Q100000
  `played_character_prestige`, using the exact `CCharacter extension+0x130`
  leaf already exercised by the war-exit terms reader. This is the minimum
  missing observation needed after the old WarID disappears.
- Native fixture and focused Python normal/optimized tests are GREEN. Legacy
  snapshots may omit the field and malformed fixed-point values fail closed.
- Status remains `static-ready / live=false`. It does not prove submission or
  the expected delta; action, WarID/loss/truce/resource comparison, checkpoint
  and cold restore remain open. GEN-034 stays `2/4`, G2 stays `1/8`.

## GEN-034-D frozen postcondition expectations (2026-09-14)

- The recommendation certificate now freezes exact player gold/prestige
  `pre_raw`, selected `delta_raw` and expected `post_raw`, plus WarID, opponent,
  truce days, destroyed cleanup and cold-restore requirements. The action gate
  carries this same object without recomputing it.
- D's postcondition surface is aligned with its accepted requirement:
  WarID/loss/truce/resources followed by checkpoint/cold restore. Claims,
  prisoners and favor stay in route utility but no longer enlarge this
  milestone's live gate.
- Focused recommendation/action-gate suites pass `14/14` in normal and
  optimized Python. This is offline contract progress only; GEN-034 remains
  `2/4`, G2 remains `1/8`.

## GEN-034-D pure postcondition verifier (2026-09-14)

- The six frozen termination expectations now have one executable pure
  verifier. It consumes the existing action result, successor paused snapshot,
  action-bound source-loss/truce evidence, and native save/restore results; it
  performs no command, filesystem operation or CK3 access.
- An ACK proves only exact authorized submission. GEN-034 can close only after
  old WarID absence, exact gold and prestige balances, source-specific cleanup,
  directional persisted truce expiry, and cold-restored semantic identity all
  pass. A verified continue result deliberately leaves GEN-034 open.
- Focused recommendation/action-gate/verifier tests pass `20/20` in normal and
  optimized Python. Status remains `static-ready / live=false`; the queued C
  horizon and one bounded D execution remain the live blockers.
## GEN-034-D source-bound postwar evidence composer (2026-09-14)

- A pure evidence composer now joins the retained source capture, the current
  action-frame generic war-bound observation, the successor snapshot, one raw
  exact-store cleanup query and two raw persisted-truce queries. The complete
  WarID plus persistent/current regiment generation sets must match before
  source-specific cleanup can be asserted. The current action-frame CArmy set
  is then frozen and must match cleanup exactly; creation-time CArmy containers
  may naturally merge and are not cross-war identity. WarID absence by itself
  remains insufficient.
- The truce reads must be consecutive, normalize to the same native payload,
  remain on the successor native revision and contain the exact directional
  expiry frozen by the authorization. A valid `no_truce` or surviving source
  generation produces a named RED instead of a synthetic evidence packet.
- The emitted packet is consumed unchanged by the six-check verifier and can
  close its pure fixture. Focused recommendation/action-gate/evidence/verifier
  tests pass `26/26` in normal and optimized Python. No CK3, filesystem or MCP
  operation occurs in the composer; live action and cold restore remain open.

## GEN-034-D bounded action runner and termination cleanup binding (2026-09-14)

- The managed runner now revalidates the authorized paused snapshot and exact
  source/current regiment generations before it can submit its single semantic
  action. This closes the earlier ordering hole where the same check happened
  only while composing post-action evidence.
- The private default-OFF cleanup dispatch had a concrete route mismatch: the
  production driver can submit white peace, while cleanup admitted only a
  surrender ACK. It now records a same-connection, same-WarID termination ACK
  for either white peace or surrender, consumes it after one successful cleanup
  read and resets it with the retained baseline. Public surrender remains
  disabled and the MCP capability/wire is unchanged.
- Focused normal/optimized Python tests pass `29/29`; an enabled MSVC Release
  candidate build is GREEN. This removes the static execution blocker but does
  not supply live action, resource delta, truce, cleanup or cold-restore proof.
  GEN-034 remains `2/4` and the next action is one bounded managed lifecycle.

## GEN-034-D R657-R661 immutable replay boundary (2026-09-14)

- R657 retained two successful same-frame exit reads before the application-main
  strategic-power query failed. R658 moved power first and failed at the same
  boundary. Their report SHA-256 values are `80F42145...73C` and
  `2D654EDB...4BF`; the RED is preserved rather than converted into evidence.
- A reusable, hash-bound offline join reuses R471's production power evidence
  with R657's exact R459 exit terms. It emits a production `continue`
  recommendation without authorizing a live action. The recommendation report
  SHA-256 is `D9222517...4E9`.
- R659 submitted one authorized `resume-map` after two fresh reads but sampled
  the same frame. R660 then observed 42 read-only snapshots for five seconds
  without a successor. R661 removed all fresh reads and made `resume-map` the
  first gameplay command; its unique PID `194108` still remained paused across
  45 read-only observations at `native:3` / revision `4` / date `53183856`.
  R661 report SHA-256 is `BD6682AA...5DA2`, final driver-state SHA-256 is
  `C9D503E9...ED84`, source inputs are unchanged and cleanup is GREEN.
- R655/R656 used a different checkpoint/source frame and advanced immediately
  with the same first-command shape. The remaining RED is therefore scoped to
  R459 map-control execution, not recommendation or action ordering. No more
  unchanged R459 retries are permitted. GEN-034 remains `2/4`, G2 remains
  `1/8`, and the active implementation queue moves to G2-M2 production event
  loops while this fixture seam remains recorded.

## G2-M2 R662-R664 first material event loop (2026-09-14)

- R662 stopped before mutation because the new runner compared the advertised
  concrete `select-event-option-1/2` steps with a literal `...-N` placeholder.
  Exact-build failure report SHA-256 is `C29D2289...5248`; cleanup and immutable
  source checks are GREEN. The one-line gate repair is commit `3a30488`.
- R663 passed exact-build but the fresh application-main event-window query
  timed out. No event action was submitted; report SHA-256 is
  `548A064C...534C`, cleanup and source checks are GREEN. Because the immutable
  checkpoint is itself sealed by R414's production query, commit `b4542f2`
  replaces this repeated read with a hash/identity-bound context replay.
- R664 is GREEN on unique PID `124060`: registry objective
  `increase_liquid_reserve_without_random_persistence` chose
  `trait_specific.8001` native option 1, instance `1075 -> null`, and gold raw
  `2042495773 -> 2043995773` (`+1500000`, Q100000). Exact command delta is one
  `select-event-option-2` plus one `save-checkpoint`; date `53783472` did not
  advance. Report SHA-256 is `AB718B94...BC63`, successor checkpoint SHA-256 is
  `8506B83C...2616`, source inputs are unchanged and cleanup is GREEN.
- G2-M2 now has `1/3` required production material event loops. Global G2 stays
  `1/8`; two target loops remain and no dedicated event long-run is authorized.

## G2-M2 bounded horizon REDs and replay cutoff (2026-09-14)

- R665-R670 exercised only the short, frozen R555-to-`tgp_travel_events.0030` trajectory. Each run stopped before the target action and preserved its RED. The runner fixes produced by these facts are separately committed through `89ae41f`; the latest report SHA-256 is `79FB89A4...ED3B`.
- R670 submitted only `set-speed-1`, did not observe its state within the bounded ten-second window, and therefore sent no resume, event query, or selection. Source integrity and process cleanup are GREEN. This is a harness/runtime-materialization RED, not a gameplay success.
- The old R555 source is removed from the active retry queue. `tgp_travel_events.0030` remains pending for a new near-event encounter. R374's nearest pre-`death_management.1007` autosave is about 231 game days earlier, so `.1007` material stress proof also remains encounter-driven. No dedicated single-event long run is authorized. G2-M2 remains `1/3` and global G2 remains `1/8`.

## R671 war-entry mailbox pre-reader RED (2026-09-14)

- Current round R671 restored the verified R664 successor checkpoint and returned seven native declaration rows, then `query-war-entry-assessments-v1-1-38436` failed before gameplay mutation or time advance. The generic error lacked the mandatory reader `:<stage>` suffix, so the live fact is a mailbox/application-main failure before a typed business-data result, not a power-reader diagnosis.
- The real implementation defect was insufficient terminal observability plus an outlier `2000 ms` queued budget. The bounded fix uses the established production budgets (`8000 ms` queued, `2000 ms` executing slice) and maps every wait/completion/reader-stage terminal state without weakening RED semantics. Focused native tests are GREEN; rebuilt DLL SHA-256 is `6562CD13...1994`.
- Current round R671 is terminated and all old rounds are terminated. G2-M2 remains `1/3`, global G2 remains `1/8`, and one short new-round replay is required; no unchanged campaign or single-event long run is queued.

## R672 war-entry operational blocker closed (2026-09-14)

- New round R672 held the R671 source inputs constant and used only the rebuilt `6562CD13...1994` DLL. All three bounded turns passed: declarations available, `query-war-entry-assessments-v1-1-38436` available on the same paused revision, then `NO_DECLARE` advanced 30 days and saved checkpoint `8D918606...CCB4`.
- The run is qualified with no blocker; report/log SHA-256 is `A803C1E4...BA6D`, final driver state is `76AF995D...B654`, and cleanup leaves CK3/injector at zero. R671 remains RED as historical evidence, while its operational retry entry is closed.
- This restores the ordinary campaign path. It does not change G2-M2 counting (`1/3`) or global G2 (`1/8`); remaining registered events stay encounter-driven rather than receiving dedicated long runs.


## R673 stale declarable-war projection (2026-09-14)

- Current round R673 completed five normal NO_DECLARE campaign advances before a one-target assessment failed with target_not_declarable at native:159, date 53787792. The failed request made no gameplay mutation. Run log SHA-256 is CF92D2D...4DE3, final driver-state SHA-256 is 30902F5E...BA0B, and cleanup is GREEN.
- Evidence shows one declaration query at the starting frame followed by repeated assessment/advance pairs. The Python driver kept the original declaration rows across native revisions, so the planner could select a target whose legality had expired. The native evaluator correctly rejected it; the RED is classified as a Python cross-frame cache defect.
- Declaration rows and generated target actions now require exact paused-frame, connection and episode ownership. Any new snapshot clears them and returns the strategy to query-declarable-wars; query results that cross frames never enter the cache. Focused normal/optimized tests pass 14/14. One short R674 checkpoint replay remains before this operational blocker can close.


### R674 closure of the stale-declaration operational blocker

- Fix commit c1d91c0 bound declaration rows to their exact paused frame. New round R674 cold-restored checkpoint F2E84CF1...D27B, then completed a fresh declaration query, a successful current-target assessment and one NO_DECLARE advance in three turns.
- The run is qualified with no first blocker. Preflight/run/driver/checkpoint SHA-256 are 4E0BC602...F03BE, C5B37439...1CC09, A6033D85...4567E and 4F72E469...61686; cleanup is GREEN and no CK3/injector survives.
- R673 remains a historical RED. Its operational blocker is closed, so no further dedicated replay is authorized. G2-M2 stays 1/3 and ordinary encounter-driven progress resumes.


## R675 post-fix ordinary campaign evidence (2026-09-14)

- Current round R675 completed four consecutive fresh declaration/power/advance cycles, 12/12 successful turns and date 53787072 to 53789952. The current legal target changed from 38436 to 83395 after the first advance and was refreshed before assessment.
- Status is qualified with no blocker; log/driver/checkpoint SHA-256 are D42D7EF7...32A5A, 0AD53440...1F53 and 223E4C65...16092. Cleanup is GREEN and all CK3/injector processes are gone.
- The R673 operational blocker remains closed and receives no more replay. No registered target event appeared; G2-M2 remains 1/3.


## G2-M3 succession expectation and reconciliation contract (2026-09-14)

- The first M3 package freezes the current production-live per-title first-heir
  projection against the living episode ruler and exact paused frame. The pure
  comparator accepts only a paused `played_character_changed` frame plus a
  same-frame successor turn bundle.
- It reconciles only predecessor-owned titles. Titles the successor already
  held are reported separately and cannot become false inheritance mismatches;
  absent-title holders remain unknown instead of being invented. Focused tests
  pass `5/5` in normal and optimized Python.
- Status is `static-ready / integration-live pending`. No native/MCP interface
  changed. The remaining blocker is driver retention, first-successor-frame
  query/reconciliation and a distinct real-successor continuation path; the
  immutable-seed replay path is not evidence for that outcome.


## G2-M3 persisted expectation and transition fixture (2026-09-14)

- The native driver now retains the latest same-frame succession expectation
  in its existing private driver-state v2 envelope and restores it only for the
  same PID/episode identity. Old state files remain readable because the field
  is optional and additive.
- Cold checkpoint/seed restore, Phase 2 source staging and explicit operator
  player rebind clear it. A natural played-character transition retains it and
  the fixture proves prediction -> same-PID hot recovery -> successor frame ->
  estate reconciliation. Focused tests pass `10/10` in normal and optimized
  Python.
- This does not yet continue gameplay as the heir. The next active blocker is
  the runner integration and one bounded natural transition artifact; no public
  MCP/native surface changed.

## G2-M3 real-successor continuation static-ready

The planner service now refreshes the persisted succession expectation on each
eligible paused living frame and reconciles it on the first eligible
`played_character_changed` successor frame. After the predecessor's normal
death settlement completes, the strategy selects
`continue-as-reconciled-successor` only when both the successor identity and
predecessor-title distribution match. The driver keeps the live campaign and
process, sends no CK3 command, clears character-scoped caches, and binds a new
one-life run to CK3's already-played successor.

A missing or mismatched reconciliation blocks this path and cannot fall back to
immutable-seed replay. Focused contract/service/strategy/driver tests pass
`10/10` in normal and optimized Python, including the existing distinct seed
replay regression. Status remains `in_progress / static-ready`; one bounded
exact-build natural-death artifact is the remaining integration gate. No native
ABI, MCP tool, game file, dependency, launch configuration or load order
changed.

## G2-M3 bounded runner continuation proof static-ready

A review of the actual production owner found that `native-auto-run` still
stopped immediately after every `death-terminal`, so the previously completed
planner/driver action could not execute in an ordinary bounded campaign. The
runner now continues after a natural `played_character_changed` settlement,
verifies the matched predecessor/successor transition, unchanged PID,
connection, frame and date, zero CK3 command/restart, and the new episode
identity before gameplay resumes. Its report preserves these facts in
`natural_succession_transitions`.

Strict one-generation runs still end at death; immutable-seed next-episode runs
retain their separate restart contract. Focused normal/optimized boundary tests
pass `4/4`, including both existing terminal modes. This package changes the
private runner report shape but no native ABI, public MCP tool, DLL, game file,
dependency or load order. M3 remains `in_progress / static-ready` and global G2
remains `1/8` pending one bounded exact-build natural-death artifact.

## R676 celestial council scope RED (2026-09-14)

- Exact paused CharacterID `32904` at date `53789952` returned
  `council_unavailable` on the first campaign-root read, causing
  `turn_bundle is unavailable` before gameplay input. Run/driver/error hashes
  are `CE1C66A4...E24CF7`, `C83767D4...3ED7C`, and
  `4C3C2EF4...E0C7F`; cleanup is GREEN.
- Existing evidence identifies the ruler as celestial government. The council
  scope predicate was broader than its five-seat memory-layout contract. The
  minimal repair marks `government_is_celestial` outside that component while
  retaining every other root observation.
- Focused native fixtures and candidate DLL build are GREEN. The blocker stays
  open pending one short R677 replay; natural death remains the later M3 gate
  and receives no dedicated long run.

## R677 optional selected-game-rule component RED (2026-09-14)

- R677 cold-restored CharacterID `32904` at date `53789952`. The first
  campaign-root query passed the corrected celestial council scope boundary,
  then returned `selected_game_rule_tokens_unavailable`. The planner emitted no
  gameplay input, the game date did not move, and managed cleanup is GREEN.
- Run, final driver-state and error-log SHA-256 are
  `0FC0C00D7FDE01F032C17956D086B0DF076D157A424018D4327D955B2F33028D`,
  `74676EC7CAC08AC8A5F8EC82852A833E5A6F1BDE0A4AA3866D2AC63804D60E08`, and
  `107628E983A0A46044B5D2626B883ACFCE22BA3819EBF49E84F505917EF131AF`.
- Root cause is a monolithic availability boundary: optional game-rule token
  enumeration erased otherwise valid ruler, estate and succession evidence.
  The candidate contract keeps root `status=available`, publishes
  `selected_game_rule_tokens=[]` and count `0`, marks that component and
  aggregate readiness false, and retains independent fields. Celestial council
  remains typed unavailable and the turn bundle may be `partial`.
- Focused validation produced candidate DLL
  `68E3746D35601C3197165A91ED85C5E5AA5C362C5EEF882123487E52B2ED2B76`.
  The operational blocker remains open pending one three-turn R678
  differential replay proving partial-bundle expectation capture. R678 is not
  a natural-death run; the naturally occurring death/reconciliation artifact
  remains the later M3 integration gate.

## R678 application-main executor timeout and partial mailbox gap (2026-09-14)

- Commit `764e1c4` and DLL `68E3746D...B2ED2B76` passed no-launch preflight,
  then the only campaign-root command at history index `621` ended
  `timeout_cancelled_before_execution`. The executor did not take the request;
  this attempt therefore did not return either the expected partial result or
  a business-data unavailable reason.
- The run completed `0/1` turns, sent no gameplay input, left date `53789952`
  unchanged and captured no succession expectation. Cleanup is GREEN and the
  old round R678 process is terminated. Metadata/run/driver/cleanup hashes are
  `DF7401C0...016BD`, `51D66A8D...11456BF`, `2CE3FA57...DE79BFD`, and
  `D7007C3D...FA303`.
- A separate source audit found that
  `campaign_root_context_v1_mailbox.cpp` defines `typed_available` as also
  requiring aggregate `readiness.ready=true`. That contradicts the candidate
  contract's valid available root with optional rule-token readiness false;
  once executed, that shape would be converted to `internal_error`. This is a
  deterministic follow-up defect, not an inferred cause of the observed
  executor timeout.
- The blocker stays open. Repair the mailbox admission and its focused fixture,
  then run one short new round R679 differential replay. Do not claim the
  optional contract production-live before R679 returns the partial bundle and
  captures the succession expectation; natural death remains a separate M3
  gate.

## G2-M3 mailbox/cold-readiness blocker closed by R681 (2026-09-14)

- R680 showed that FIX2 did not clear the cold paused-pump boundary. Under its
  single three-turn allowance, the first campaign-root ticket timed out before
  execution with pump epoch `9849 -> 9849`, executor starts `0 -> 0` and
  executed requests `0 -> 0`. It completed `0/1` turns with unchanged date and
  no gameplay. Probe/run/driver/cleanup hashes are `A1E9B898...82B997`,
  `4C34D4FF...C18DD`, `FCDB79A8...619EE`, and `F27BCDE1...61F1F`.
- FIX3 commit `080bc507ee9c2e1c2fa1decd787a3927c15a12e4` requires a pump
  epoch observed after the current cold binding baseline before admitting
  readiness. R681's completed typed campaign-root result proves this behavioral
  fresh-epoch gate and executor completion. Successful exact epoch values were
  not serialized and are not asserted.
- R681 completed `3/3` bounded turns: campaign root `available`, celestial
  council typed `unavailable`, selected game-rule tokens empty with readiness
  false, aggregate readiness false, and a planner-consumed `partial` bundle.
  It captured succession expectation `32904 -> 88187` for primary title
  `16761`, advanced 30 days (`53789952 -> 53790672`) and saved checkpoint
  `CDCC3771B1179667ECD017817781B2A93A412EA82EC9455B08EECE170F2FBC61`.
- Evidence root is
  `Z:\ck3_mod_rewrite_process_assets\g2-m3-r681-cold-pump-edge-080bc50`.
  Acceptance/run/driver/cleanup-inventory hashes are
  `2BED139B...6B14`, `EFBFF36A...5C866`, `19421B49...40734`, and
  `086138C3...B2D1`. Cleanup is GREEN and no CK3/injector process remains.
- **Closure:** mailbox pickup, partial-root publication, partial-bundle
  consumption and pre-death expectation capture are production-live for this
  exact build. G2-M3 stays `in_progress`, global G2 stays `1/8`, and the only
  remaining integration gate is a bounded naturally encountered death that
  reconciles the actual successor/title distribution and continues in the same
  campaign as the real successor.

## G2-M4 first faction intervention seam (2026-09-14)

- Exact-build stock data confirms that `gift_interaction` explicitly considers
  factioneering vassals, rejects repeat `gift_opinion`, auto-accepts an AI
  recipient, transfers the engine-evaluated `gift_value` and applies
  `send_gift_opinion`. The generic native definition lookup and
  validate/construct/queue command path are byte-frozen in
  `docs/ck3-native-ai/factions-and-rebellions.md` and its source-contract
  fixture.
- The first narrow M4 OODA is a single budgeted gift to a real targeting-faction
  member who is also a REALM2 direct landed AI vassal. Completion requires the
  same-date gold delta and modifier-specific `gift_opinion` evidence, followed
  by a requery of the same faction. A submitted ACK or the count alone does not
  qualify; a faction that remains after the gift is recorded as mitigation,
  not resolution.
- Status is `research / live=false`; no native, public MCP, schema, action or
  planner interface changed. The next blocker is the targeting-faction
  span/stable identity/member observer, followed by exact actor/recipient gift
  value/opinion preview and the generic send action. Generic religion remains
  outside scope.

## 2026-09-16 01:19 incremental delivery gate ledger (G2-REPORT-R730-R733)

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Bounded standard-feudal preview | GO, user-startable; G2 not changed | native_auto_run / ck3_auto_turn | frozen ZIP SHA0E233DCB...4EB2; native eefc88e/Python d11268f | R701 nonempty ransom reject, independent pending clear and next turn; R706 ZIP smoke5/5 | R702 checkpoint/stop, R704/R706 new-process same-goal no duplicate | Whole-war/Council/succession outside advertised preview; /root | Preview artifact frozen; no temp branch dependency |
| M4 construction definition source | R735 definition_identity RED still open; exact source repair static-ready, live held by user machine reservation | controlled same-feudal paused world source query, public OFF | R735 finalac reportSHA B58DFA61...E05A58; repair master1f5bc54 exact CBuildingType getter RVA864750/global570C108 | R735 first vtable0x441EF38=CCourtTypeSetting; repaired true CBuildingType source has focused /Od,/O2 tests and PE verify, but no final-DLL seal/live legality/action | R735 PID102076/job/watchdog recycled; original feudal pair unchanged | When CK3 is released, seal new DLL and repeat private legality; then typed build/material result/next turn; m4_closed_view | repair final1f5bc54 on master; temp refs cleaned; clean clone retained for pending seal |
| FEUDAL selected 1066 model | R734 frontend_setup_view_unverified RED still open; exact GUI-context repair static-ready, live held by user machine reservation | official MCP NewGame->Bookmarks plus guarded private read-only model, public OFF | R734 artifactSHA B8B5D098...ECC13; repair master0ab58c0 source-only no-launch manifestSHA04CF6831...968A | R734 Bookmarks tree real; keys/date/government UNOBSERVED; narrow app/idler/handler/view RTTI plus unique named-root fallback /Od,/O2 focused GREEN, no final DLL/live/new seed | R734 PID9512/job/watchdog recycled; no first1066 checkpoint | Once CK3 is released, seal/replay read-only setup model; require verified candidate before typed selection/StartGame; feudal_start_game | repair final0ab58c0 on master; temp refs cleaned; clean clone retained for pending seal |
| GEN034-C/D War | material war disappearance and subsequent consumption observed; terminal-policy gates insufficient; 2/4 unchanged | official native-auto-run cold checkpoint | R770 sourced036e2b1; reportSHA8D53F76D...DC8C90; independent sealSHABFB6DE13...06191; final pair C3C0661F...BE5C8A/6EE56860...9CE52E | Cold-restored active WarID218103854; fixed stationary horizon executed; player capture at score-100 led to native automatic war disappearance; later formal turns consumed result, resolved notification, disbanded and checkpointed; zero R770 terminal/declaration actions | New process R770 restored R769 pair in same episode; postwar pair exists but has not yet been cold-restored | Require one same-frame three-way agent choice and typed terminal action, material truce/CB settlement and postwar cold restore; /root | stationary fix finald036e2b1 on master; temp refs cleaned, physical clone removal auto-review blocked |
| M5 five distinct native legal family candidates | R733 preliminary campaign-root timeout RED; final67c source repair static GREEN/new short candidate READY_NO_LAUNCH, public OFF | official/controlled final67c read-only native family query once user releases CK3 | manifestSHADE3302BC...0CE9C, runnerSHA836440C4...AA3, source67cafd0, reused exact DLLSHAE4CC64EB...53EB5C | R733 pump7851->7851/executor0 RED; five legal rows/raw0 mapping unexercised, no score/action/result | paired R695 source preserved; R733 PID169796/job/watchdog recycled, candidate no-launch only | Live post-ready pump, then five legal rows/joint score/typed action/next turn; m5_legal_scene | original67c and temporary work/integration refs cleaned |
| M4 lifestyle minimum | deterministic policy static-ready; formal private LIFE6/LIFE4/LIFE7 wire in progress, public OFF | native_auto_run only after typed wire/legality, no CK3 now | master88430bc pure private policy; source branch work/g2m4-lifestyle-formal-wire-20260916 | existing same-frame policy legal focus/perk choice tested normal/-O6/6; no gameplay/material next turn | no live checkpoint or cold restore | Finish episode-bound action receipt/checker and native glue, then real two-year bounded gate; m4_lifestyle_min | pure-policy temp refs cleaned; formal-wire branch active |
| M4 real faction intervention | Budgeted chooser static-ready; deterministic B0: normal production lacks full paused row/details query and typed send-gift receipt route; public OFF | native_auto_run only after private native query/action and Python adapters | masterda3fbed chooser, docs/ck3-native-ai/faction-gift-formal-route-gap.md exact source anchors | Existing FACTION6/16 source components and tests do not expose a production command; no real gift/opinion/faction next turn | no faction cold restore | After sole bridge/CMake writer releases files, add paused private row/member+metric/preview and one-shot typed gift/receipt; then formal Python consumption and real positive scene; /root/m4_faction_min | old policy temp refs clean; reused clean clone, physical recursive deletion auto-review rejected |
| Natural death_management.1007 | exact-build trigger contract documented, no natural paused encounter | ordinary production event loop, never forced trigger for natural gate | masterf87604f heir-death-stress source doc; exact event/on_death SHA31591A...FB7/F9D596...041 | no natural .1007 selection/stress change or same-campaign successor continuation yet | natural heir cold restore absent | Encounter-driven paused trigger, independent old-instance disappearance/stress postcondition, next turn/heir cold; natural_death_event_gate | source-doc temp branch/worktree/ref cleaned |
| Council final four scenes | Private typed-reject entrance static-ready; public query/action and advertisement OFF | Existing controlled acceptance first, then native_auto_run formal choice after all gate evidence | R696 already-councillor positive rejection; new controlled entrance mastereb586f7; no-launch evidence SHA D86BF857...0513C | R695/R700 guest/pending/fireability isolated positive IDs all empty; new entrance returns positive_missing, so three live rejects and formal appointment/next-turn incumbent unexecuted | R696 paired historical scene; no Council formal cold goal restore | Real guest/pending/replacement-fireability scenes, distinct legal/reject/replace/wait proof, then public query→formal typed appointment→independent incumbent→next turn; /root | entrance original ce628c4→final eb586f7 on master; remote/local temp refs/worktree cleaned |

## 2026-09-16 R771-R772 incremental delivery ledger

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Exact `ransom_interaction` pending drain | production-live loop for this exact definition; generic interaction ad remains OFF | `native_auto_run` / `ck3_auto_turn` | source `89d6e07f`; R772 report SHA `D874AD4F...BB87A`; receipt `7AB815BD...BBE11` | Fresh instance `-100663276` appeared naturally; typed same-frame query -> one legal formal reject -> independent disappearance -> later official queries and gameplay advance, with no duplicate or retry of the old unqueried ID | New CK3 process restored R771 durable pair; R772 periodic/final pair `C9C428A0...C3255` / `721BEED4...37F4`; cleanup proven | Other interaction definitions remain definition-gated and fail closed; /root | ransom code original `a132f92d` -> final master `89d6e07f`; temp remote/local refs and agent clone cleaned |
| MCP exact-build address binding | documented current behavior; no capability-state change | native bridge adapter and MCP-facing typed queries/actions | `docs/ck3-native-ai/mcp-ck3-addressing-and-upgrade-migration.md`; master `bc382cff` | Exact SHA + module base + frozen RVA/layout/calling convention; local signatures verify known code and support offline relocation work, no arbitrary-build auto-scan claim | Upgrade requires a distinct adapter plus paused snapshot, typed material-result and cold-restore evidence | New CK3 build has no support until its adapter passes affected gates; /root | document commit on master; no temporary branch remains from document delivery |
| Exact ransom/postwar continuation | GREEN bounded cold restore; no public-ad delta | `native_auto_run` / `ck3_auto_turn` | R773 report `E978F07E...C238A`; verdict `112F3F71...125C4`; seal `A30CADA8...4778`; source `89d6e07f` | 16/16; pending null throughout, old IDs absent, reply0; WarID218103854 absent throughout, declaration/terminal0; four gameplay turns and 135 days | New process restored R772 pair; final pair `3405752B...260F69` / `4E40A24E...7C7685`; cleanup proven | Truce/settlement fields unavailable, so GEN034 stays2/4; final R773 pair not yet restored; /root | exact-source detached worktree removed/pruned after run; no branch |
| Council final four scenes | R774 query-only GREEN, new gate closure0/4; public/action/ad OFF | controlled private final-gate query | report `386E5231...755A`; verdict `76904C4E...373C`; three ordinary candidate IDs34445/37629/77483 | All four positive sets zero; vacancy fireability explicitly unevaluated; gameplay0 and save/date/revision unchanged; no appointment | Query-only private run, no production goal-continuity claim; cleanup proven | Need materially different natural guest/candidate-pending/occupied non-fireable scene before typed appointment; /root | existing integrated runner/native artifact, no source branch |
| G2-M3 natural succession and successor recovery | Natural inheritance/reconciliation GREEN; continuity RED; M3 remains in progress | `native_auto_run` / `ck3_auto_turn` | source `89d6e07f`; R775 report `FE1AA1B6...AB8AC`; M3 verdict `9870BD29...3EC66C`; generic verdict `9711BB68...1508`; blocker analysis `D8D37A7E...AB4EE`; query master `c9dc6f91`; controller ABI `0F1D607C...5BD00`; recovery decision `F3B7E197...A8E91` | Natural `31853 -> 35465`; expected/actual titles `524/525/530/533` all matched; zero-command/zero-restart continuation; successor query and one gameplay submission; turn14 date/event no-progress RED | Successor checkpoint `2C0F4333...E505E3` is before gameplay while driver `DA3B3822...9E219` is after receipt; cleanup proven, CK3=0 | Private owning-thread query wire integrated but registry/ad OFF and blocks_simulation unavailable. Run one R776A read-only paused query; then exact typed Close, receipt reconciliation without retry, a different legal successor step, paired checkpoint and cold restore same plan/no duplicate; /root | Static query `ab35a4c0` -> `6e859427`; private wire `81a6ad1f` -> `c9dc6f91`; all associated remote/local work+integration refs/worktrees cleaned; R775 exact-source worktree retained only while B0 fix consumes it |
| R775 event and war scans | Evidence not observed; no capability-state change | read-only scan of formal report | event scan `1F4807BF...18A6`; war scan `27E39C5C...DD73` | Neither `tgp_travel_events.0030` nor `death_management.1007`; no new WarID/termination query/action; old WarID218103854 stayed absent with no duplicate action | R775 cold start reconfirmed old-war absence from the R773 pair | Natural target events and GEN-034 C/D remain open; event and war owners | read-only artifacts outside Git; no branch |

## 2026-09-16 R782-R783 ordinary preview increment

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Fresh standard-feudal `xar_off` seed | production-live seed; portable package pending | controlled private frontend seed, then formal `native_auto_run` | source master `08eaf832`; R782 report `695234CF...FBB1`; seed pair `94FA7F56...89F41` / `66EC923D...31C42` | Public root proved Murchad/1066/feudal and `xar_off`; checkpoint result, driver top level, last checkpoint and history anchor share ordinary/no-pact/environment binding | R783 restored in a different CK3 process and preserved actor/episode/lifecycle | Operator still defaults legacy profile in some paths; copied state needs strict versioned rebinding; ordinary_operator_wiring / ordinary_seed_rebinder | seed source integrated and old temp branch cleaned; new operator/rebinder branches active |
| Ordinary bounded production loop | GREEN same-state cold restore; not full campaign | formal `native_auto_run` with cold checkpoint and ordinary/no-pact flags | R783 report `EF35A852...59337`; verdict `8F9F6D1A...D9FA7F`; final pair `74294B03...EDF1A` / `354D4DE3...FE34B` | paused declaration query + power assessment -> typed declaration -> independent WarID5 -> next-turn termination query; later ArmyID33 raise/move/combat; 20/20 turns and +28 days | New PID150160 restored R782 pair; periodic/final checkpoint and cleanup proven | Natural succession, portable ZIP, 1066-1453 and second seed remain open; /root | external evidence sealed; source master clean |

## 2026-09-17 R795-R796 ordinary white-peace blocker

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R795 cold-start admission | Harness RED, zero capability action | `g2_preview_operator.py run` | report `6F53E81D...762625`; seal `164B1BD5...3118B`; source `67f65d82` | Outer timeout 600 expired at 602.96 seconds before readiness allowance 720; turns/query/action/checkpoint all zero | Source checkpoint and driver unchanged; cleanup GREEN | Use measured-safe whole-run bound greater than readiness; fixed to 810/720 in R796 | External evidence sealed; no Git source change |
| WarID5 no-safe-route white peace | Capability RED; one submission only | formal `native_auto_run` cold restore | R796 report `F92AFE0E...52A09`; receipt `17D4EA6A...4A398`; seal `A7A20DBA...561A`; static repair `836ad237` | Two termination queries, one six-day advance, exactly one `offer-white-peace-5`, honest `submitted_pending`, one response-day advance, then old `native_war_no_safe_exact_route`; no duplicate | Cold restore truncated R794 history261-264. Durable save remains pre-action history260 `55A51F5D...FDE82`; R796 action tail is not checkpointed | Static fix waits daily through tenth-day native observation boundary and fails explicitly afterward. Live replay needs an explicit rolled-back-timeline recovery decision; Council remains queued behind it; /root | Code and docs prepared in clean C: clone; CK3/injector zero |

## 2026-09-17 R797-R802 ordinary terminal recovery closure

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Council occupied-scene gate | GREEN query, no new gate; 1/4 | private gate-only | R797 `B6345292...4641` | already3, guest0, pending0, replacement-denial0; mutation0 | full process cleanup; no production-continuity claim | wait for materially different positive scenes; public OFF | `0aa366ef` master; temp refs clean |
| Sender-side white-peace recovery decision | GREEN exact-absent after two preserved harness REDs | public typed query under bounded production-owned session | R798 zero-query readiness RED `B9349287...6195`; R799 ledger RED `421EE026...AE3D`; R800 GREEN `257104F8...133A`; fix `851c36dc` | R800 one query, no gameplay/date/save mutation; WarID5 remained active and outbound proposal was exact absent | exact history264→checkpoint260 truncation, restore261 and complete recycle | query is recovery-only and does not advertise terminal capability by itself | all commits FF master; temp refs clean |
| Ordinary WarID5 material terminal loop | CLOSED for observed exact-build branch | formal `native_auto_run` | R801 report `E6E47677...48C6`; seal `DCA82714...2D96`; code `b9b6f249` + `aba36a4e` | one same-frame three-way choice; one `offer-white-peace-5`; immediate h269 pending checkpoint; independent old WarID absence; next turn disband; h289 peaceful checkpoint | R802 report `12BE7379...BD2`: new process restored h289, abandoned later tail, no reoffer/redeclare, +32 days, h293 pair `DFC96CFD...71AF7` / `7C79FE4C...48EF0` | Raiktor GEN-034-C/D remain 2/4; whole campaign and natural succession continue from h293; /root | all source ordinary-FF master; remote/local temp branches removed |

## 2026-09-17 R839–R847 incremental delivery ledger

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| User-startable bounded preview | GO, unchanged | packaged `g2_preview_operator.py` / `native_auto_run` | ZIP `E32D2057...A1273`; manifest `CAA552E0...D4E5`; qualification `9F7DA87B...C1AA3` | Existing R805 nonempty action/result/next-turn and R806 cold recovery remain the advertised package evidence | Guide stop/status/restore commands are now self-contained; no ZIP byte change | Whole campaign, later ordinary branches and broad G2 remain outside the frozen package; /root | No package branch; docs sync branch removed after master delivery |
| GEN-034-C / D | C complete; D blocked_live; GEN-034 3/4 | production `native_auto_run` | R839 report `BD798BAE...1FEE6`; pair `5D040C7E...7B236` / `842CCC35...97CC7`; R846 report `63CFCDD4...34D1` | R839 same-frame three-way choice, exactly one surrender, independent WarID/both-army disappearance, later formal consumption | R846 new process restored h671, replay0, continued formal work and saved h693 pair `9893F8C1...C08C` / `8315217A...F83` | D lacks matching creation-time source capture and the complete fixed six-item source-bound certificate; /root | `bbf53990` and later static event patches on master; associated temp branches/worktrees cleaned |
| Natural `prison_notification.2002` | production-live exact loop; M2 still in progress | exact registry consumer inside `native_auto_run` | R842 `60554323...24C2`; R846 `63CFCDD4...34D1` | Both natural occurrences used query → one typed option → independent old-instance disappearance → later formal turn; R846 also checkpointed | R846 began from the R839 cold pair and saved h693 | Required `.0030` and `.1007` remain absent; `health.7500` static fix still lacks live recurrence; event owner | event projection commits `256d57e4` / `a5db1e5d` on master; temp branch cleaned |
| Ordinary War25 regroup and post-move recovery | GREEN bounded continuation; terminal open | formal `native_auto_run` | R845 report `2A86B334...5D8E`; R847 report `DBA987B5...0CE7B`; final pair `50993AC4...10031` / `8290560E...3F57E` | R845 one preview + one move then route/battle consumption; R847 zero duplicate preview/move/assault/terminal, battle-to-retreat and three later daily turns | R847 new process restored R845 h503; h516 and h521 checkpoints; cleanup proven | War25 active, capital arrival absent, 100-year/full campaign open; /root | code commits `01d48050` / `c1887eeb` on master; temp branches/worktrees cleaned |

## 2026-09-17 R848–R854 ordinary War25/declaration-query closure

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Ordinary War25 terminal and declaration final-validator parity | Exact War25 branch GREEN; R853 query/submit B0 closed for exact scene; whole campaign open | formal `native_auto_run` | R853 report `A64457EB...2A8DD`; R854 report `848E56BD...45464A`; code `729c5b26`; native DLL `28FC55A5...5A75EAE29` | R853 one surrender, independent WarID25 absence, Army304 disband and later consumption; later declaration row was rejected by final validator without result. R854 filtered it in four fresh queries, consumed each empty set and advanced 145 days with surrender/disband/declaration replay0 | R854 new process restored the safe R853 h624 pair and truncated the failed tail; final h640 pair `36E13194...D66FC` / `34FB1623...4C754`; cleanup proven | Future legal declaration positive case, h640 cold restore, 100-year/full campaign remain open; GEN-034-D unchanged; /root | implementation temp refs cleaned; docs temp branch removed after master delivery |

## 2026-09-17 R855–R859 ordinary prefix and event-consumer increment

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Ordinary h640→h878 continuation | GREEN bounded prefix; 100-year/full campaign open | formal `native_auto_run` | R855 report `0F38E2B5...5A700`; R856 `05703538...538C`; R857 `5B9D...E383`; R859 `B5F76FB4...73ACD` | R855 20/20 +354d; R856 100/100 +1649d to natural poet pre-action stop; R857 12/12 +198d; R859 12/12 +196d with formal queries/gameplay and paired checkpoints | R857 restored h836; R859 restored exact h857 under source `463a2159`; final h878 pair `CAA6F180...F8C1` / `867843F8...155B`; cleanup proven | 100-year gate, full campaign, required natural events and succession remain open; /root | health consumer branch integrated at `463a2159` and removed locally/remotely |
| Natural `health.1001` direct consumer | static-ready after natural RED; live action open | exact registry consumer inside formal planner | R858 report `82C774...5282`; source `463a2159`; exact source doc and four direct tests | R858 natural no-physician projection stopped before action; static policy now selects authored1/native0 and preserves physician variant authored4/native3 | R859 proved new-process recovery and further progression, but event did not recur | Need a natural post-fix recurrence for typed action, independent result and later consumption; event owner | integrated and cleaned; public generic event advertisement unchanged |

## 2026-09-18 R860–R861 befriend recovery ledger

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `befriend_outcome.0002` direct consumer | success projection production-live; failure projection live-open | exact registry consumer inside `native_auto_run` | source `d3133d18`; R860 RED `4BA536C7...38F2`; R861 GREEN `623BAB4F...47A7`; close `890EA1CC...D7F4` | R861 variant0 recommended authored3/native2/rendered1; one typed option3; instance5→null; stress20→60; gold unchanged; next formal query and later advance consumed absence | New process restored R860 h961, discarded no-action failed tail, saved h981 pair `6A8720C6...2D20` / `488A52B4...A5FC`; cleanup proven | Failure variant was natural pre-action in R860 but has not run post-fix; keep that branch live-open. R860 earlier `fervor.1002` degraded native0 is a separate B1; /root | befriend implementation branch cleaned after FF master; R861 evidence branch pending this report commit |

## 2026-09-18 R862 ordinary-prefix and fervor ledger

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `fervor.1002` exact modal continuity | static-ready after observed production B1; live recurrence unobserved | exact registry consumer inside `native_auto_run` | source `d5fba52c`; exact source `06807E78...3F63`; R862 report `EB6FF99B...A3233`; close ledger external | R862 did not recur; no post-fix action is claimed. Contract selects only authored3/native2 on the exact five-scope/three-option projection and fails closed on drift | R862 new process restored h981 and completed the full bounded window; final h1146 pair `442FC751...92AE2` / `B5C18328...2FE01` | Need natural recurrence -> one typed option3 -> independent stress/window result -> later formal turn; keep unadvertised and do not generalize religion; /root | original `395c1acf` -> rebased `d5fba52c` on master; temp remote/local branch and worktree removed |
| Ordinary h981→h1146 continuation | GREEN bounded prefix; 100-year/full campaign open | formal `g2_preview_operator.py run` -> `native_auto_run` | R862 report `EB6FF99B...A3233`; operator `5C8D105E...BD3F`; close external | 100/100, 50 queries, 50 gameplay turns, +1,522d; natural `court_chaplain_task.0311/.0312` each used exact query -> sole option -> disappearance -> later consumption | Cold-restored same actor31853/episode/objective from h981; 16 checkpoints; final pair above; cleanup proven | `.0030`, `.1007`, natural succession, 100-year and whole campaign remain open; /root | no evidence/source branch; master clean |

## 2026-09-18 R863 Council query-only ledger

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Council four final gates | query-only GREEN, new closure 0; authority 1/4 | private `run_council_native_gate_scene_v1.py`, action OFF | candidate `69F77CB4...1E82C`; R863 report `AC7ECA23...6F5D8`; terminal `55A6C2D4...C0E24`; close external | h961 actor31853/steward31507; candidate10; already3, guest0, pending0, replacement-denial0; gameplay0/helper-delta0/date+revision+save unchanged | Exact durable h961 save was cold-loaded; query-only scene then fully recycled PID125360/job/watchdog | h961 retired. Need a later natural frame with an isolated guest/pending/replacement denial before any action-ON rejection; public query/action/ad stay OFF; /root | no Git branch; external candidate sealed |

## 2026-09-18 R864 primary-defender capital-hold ledger

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Ordinary defensive-war continuity with no title objective | R864 blocker removed and production-live twice; superseded by R865 contact B0 | formal `g2_preview_operator.py run` -> `native_auto_run` | source master `ee03bad5`; repair final `351d4dfb`; R864 report `53970EED...9624E`; R865 report `7D0843ED...8524` | R865 freshly observed the same natural primary-defender war, raised once, consumed regular Army234881216 and selected the strict exact-capital hold twice before enemy route intent changed | h1179/date53281008 checkpoint `8CF78229...29CB` contains the confirmed war/raise/hold prefix; discard h1180-h1183 and never replay raise | Reuse the existing stationary contact-horizon query/advance for strict threatened-capital frames, then cold-replay h1179; `/root/war_recovery_decision` implementation, `/root` integration/live owner | R864 original `2a5e44e` -> final `351d4dfb`; temporary remote/local branch and worktree removed; PID64384/injector reclaimed |

## 2026-09-18 R865 threatened-capital contact-horizon ledger

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Primary-defender exact-capital contact transition | production capability RED; scoped static repair on master, live replay next | formal `g2_preview_operator.py run` -> `native_auto_run` | R865 source `351d4dfb`; report `7D0843ED...8524`; external seal `D4993C4D...BCB1`; repair final `0f9bd870` | R864 hold branch was selected twice. At the next decision frame enemy184549393 targeted capital45 over `[8747,23,8749,45]`; generic `native_war_no_safe_target` stopped before the stationary horizon query, with no failing-turn command. Direct repair matrix normal/`-O` is 10/10; gameplay normal is 242/242 | h1179/date53281008 `8CF78229...29CB` is the sole anchor. It includes the confirmed h1174 raise. h1180-h1183 are discarded; no unconfirmed action and no duplicate-raise permission | Cold-replay h1179 under `0f9bd870`: existing target=current horizon only for strict fresh-capital frames; contact-free -> proof-bound one-day advance, unavoidable -> existing strict transition, stale/unavailable/route-away -> RED. No native ABI/schema/MCP change; `/root` | original `9e4219a` -> rebased final `0f9bd870`; remote/local branch, implementation/basecheck worktrees removed; PID64384/injector reclaimed; authority remains preview GO, GEN-034 3/4, Council 1/4, G2 1/8 |
| Primary-defender post-battle native-rally hold | CLOSED production-live for the observed strict branch; wider war/campaign open | formal `g2_preview_operator.py run` -> `native_auto_run` | repair final `a0fc877e`; R867 report `EA07E451...4CBA0`; R868 report `52B6F95C...A430`; close `573A0B29...70E6B` | R868 new process restored h1340, freshly queried termination and selected two strict rally-hold one-day advances; each produced an independent paused postcondition. Army184549472 stayed regular/stationary at8750; repeat raise/move/disband/declaration/terminal/old-army actions all zero | h1347/date53282472 pair `A3AB0B3E...564EC` / `7339B8DD...5DF47`; no unconfirmed action; cleanup proven. The new pair has not yet had a second-process cold restore | Future R869 may restore h1347 and consume changed state. Refreshed exact preview ZIP still needs its existing three-round qualification; 100-year/full campaign and authority gates remain open; next owner | original `649731ad` -> rebased final `a0fc877e`; remote/local implementation branch and worktree removed; PID115176/injector reclaimed |

## 2026-09-18 R869 refreshed-preview eligibility RED

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Refreshed R868 preview eligibility | Native-readiness RED; refreshed preview remains NO-GO, while the previously qualified R802 preview remains the user-startable package | packaged `g2_preview_operator.py eligibility` | report `D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-1d881477-r868-extracted-smoke\runs\r869-eligibility\report.json`, SHA-256 `6E27FB0E2747BE1FF086EC02E691EACC9796AE9908A5A919C39940D36026A2E3`; candidate source `1d881477` | CK3 PID100924 ran for 722.303 seconds, but native readiness timed out with `last=None`; readiness/sequence stayed null and there was no gameplay action, typed action, formal turn, or date advance | Source and prepared checkpoints remained unchanged. The report records cleanup proven, process recycled, and an empty postflight CK3 inventory; there is no independent close receipt, so cleanup is not promoted beyond the report's own evidence | Rebuild or materially change the native candidate before one bounded eligibility retry; do not treat this unchanged failed candidate as deliverable. Authority remains G2 `1/8`, GEN-034 `3/4`, Council `1/4`; `/root` | No source branch or capability commit resulted from R869; evidence remains outside Git |

## 2026-09-21 R0030–R0032 GEN-034-D long-war terminal ledger

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pending army-merge continuity | production-live GREEN for the exact source-bound Raiktor continuation | formal `native_auto_run` continuation | source master `4739a049`; R0031 native report SHA-256 `51CD…730D2`; final pair `D23C…AD5D` / `4B71…71BF` | R0030/R0031 consumed all five merges with zero pending receipts and continued through real siege, battle and retreat state; no merge replay or terminal action | R0032 started a distinct CK3 process from the exact R0031 pair and completed `256/256` turns; final driver SHA-256 `CB60994D…A76D1`; cleanup and CK3=0 | Merge B0 closed for this scene. Terminal-policy B0 below remains; `/root` | merge fix already on master `4739a049`; its temporary refs were cleaned |
| Long-war three-way terminal selection | static-ready fix; production replay pending; GEN-034 still `3/4` | formal `native_auto_run` -> same-frame recommendation/intercept | R0032 native report SHA-256 `5671E3F1…373B`; outer report `4E20723D…D118`; model `1.1.0` candidate | At day `804`, score `-3`, power ratio `228560/100000`, the old fixed penalty wrongly kept continue ahead of available surrender. New rule scales only the losing opponent-stronger tail after `730` days; exact replay computes continue `-114,280,000` vs surrender `-101,825,000` | Clean R0032 final pair exists with no pending terminal action; a refrozen-runtime cold replay from it has not yet run | B0: obtain matching production intercept, execute only emitted action, verify material result/later consumption/checkpoint/cold restore. Tests normal/`-O` each GREEN through `259/259`; no public MCP/native/open_kaishek change; `/root` | implementation branch active until linear master delivery and immediate cleanup |

The runnable user preview remains the independently qualified R888 artifact;
this policy candidate does not replace or invalidate it. Authority remains G2
`1/8`, Council `1/4`, GEN-034 `3/4` until the live terminal chain closes.

## 2026-09-22 R0044–R0046 ordinary current-rally repair and continuation

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Timed-unsafe county fallback to native rally | B0 closed for observed exact branch; production-live | `g2_preview_operator.py run` → formal `native_auto_run` | R0044 RED `EDE952DC...2B08`; original fix `72a88f29` → master `0636a81f`; R0045 GREEN `00296B7E...E877` | R0044 advanced three proven days then skipped rally query when both county routes were timed-unsafe. R0045 queried `8750`, advanced twice, and subsequent formal turns consumed each result | R0045 new process restored R0044 h1511 `DFB93843...14A2F`, discarded six read-only tail rows, saved h1536 `2205BC09...8171` / `AA064220...76A9`; cleanup proven | Wider objective quality remains open; this B0 required no new observation/ABI/MCP. `/root` | feature remote/local branch deleted after rebase/linear master push; detached runtime retained only while current continuation uses it |
| Ordinary h1536→h1662 continuation | GREEN bounded prefix; 100-year/full campaign open | same formal production entry | R0046 report `E1513900...D684`; final pair `03D08AE8...B301` / `13BFB01D...A842` | 100/100, +28 days. Exact stationary contact materialized; next turn queried battle-control and executed battle epoch; old army disappeared, then formal raise created Army251658580 and later turns continued | Distinct R0046 process restored h1536; six checkpoints plus h1662 final pair; cleanup/process-zero GREEN | Natural `.0030`/`.1007`, player death/succession, Council three gates, 100-year/full campaign remain open; `/root` | no new source branch; runtime/current artifact retained for next bounded continuation |

## 2026-09-22 R0080→R0081 private construction cold receipt

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Private bounded construction submit→material result→cold consumption | R0080 material action proven but Python receipt RED; R0081 private branch GREEN; public OFF, G2-M4 open | `native-auto-run --allow-private-construction-formal-trial` | R0080 original manifest `55192021…D42213`; Python receipt fix original `e65563f`→master `8e0df178`; compatible native `573f742` DLL `47196B7E…E171760`; R0081 manifest `ED175A02…8B8BDAA2` | R0080 one typed request `construction-submit-987aec8771e1451ba389f0d1b10cb2c3`, independent active 2103/2635/24/1 by actor29829, gold50035659→35035659 exactly 15000000 native cost. R0081 first formal turn receipt `applied/postcondition_verified`, next formal turn `life-advance` consumed same receipt, zero duplicate submits; 20/20, +3,672 raw date | R0080 immediately paired post-ACK save `1928BD74…0CBAE`; R0081 new PID120024 cold restored it, final pair save `E47C21E4…CA395`, process-zero and canonical completed-green | Private construction branch closed only; two-year window, public construction, legal council reassignment, real vassal/faction response and lifestyle still open. R0080 RED retained; `/root` | PR #20 original/integration refs/worktrees CAS cleaned; R0081 report PR #21 original `8a1aaaa/b263c1c`→master `14f3aa4/5d0151e`, original/integration refs/worktrees CAS cleaned |

## 2026-09-22 R0082 legality probe and R0083 first-seed event RED

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Observed first-heir marriage final legality | private read-only paused branch GREEN; public MCP/strategy/action OFF, M5 open | `query-observed-first-heir-marriage-legality-v1` private literal | R0082 report `040319A1…AFDA4BFD28`, typed `D7C3FE9B…8A8B698A`; source `b7a76e9`; doc original `e1654cb`→master `743e6c4` | same native:3 frame heir38822, 657 distinct can-send/final-legal, raw0=657, native rank null, no gameplay action or date advance | original save unchanged, PID165884/injector0; old R736 driver is not a cold checkpoint | Existing contract still requires same-version paused unavailable/RED branch before public MCP decorator/hello; joint candidate scoring and formal marriage loop remain; `/root/war_gen034` | R0082 candidate source worktree removed; doc PR #22 original/integration refs/worktrees CAS cleaned, no MCP implementation ref retained |
| Ordinary first independent 1066 seed continuation | R0083 natural event B0 RED; 100-year/first full campaign open | PRV-008 formal `g2_preview_operator.py run`→`native-auto-run`, 100-turn bounded | R782→h1662→R0068/69/70→R0074→R0077/78/79 byte-linked pair; R0083 frozen manifest `F22D0A88…DDCB4`, raw report `60C21482…234AF2` | turn7 natural `death_management.1000` instance15 rejected exact `scope:dislike:type`; 0 option; 6 previous turns +42 game days observed in 129.554s; no durable progress beyond R0079 | valid R0079 date_raw53316384 save `2AB80577…6CF8F`/driver `B057FCB8…DEB02`; RED driver unpaired, no new save; PID106784 recycled, canonical completed-red | Exact Boolean `dislike` projection repair normal/`-O` then same safe pair bounded replay; do not rerun unchanged candidate; target paused 1166-09-15 (~80.4 years left), cumulative-version contract review pending; `/root/event_inheritance` | No source branch for R0083 run; EVT fix branch active; report branch `codex/progress-r0082-r0083-20260922` pending |

## 2026-09-22 R0084 same-seed focused replay and durable continuation

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Natural death_management.1000 exact Boolean scope | static/affected replay passed, but natural corrected branch NOT observed; R0083 RED live-open | formal `g2_preview_operator.py run`→`native-auto-run` | repair original `fd59c2d`→master `349fefd`, PR #23; R0083 immutable RED `F22D0A88…DDCB4`; R0084 `0AE2BE9B…EF0096A` | Frozen R0083 payload offline recommends authored3/native2, but R0084 natural `.1000` did not recur: no typed event action/material result claim. Separate incoming grant-vassal typed reject turn15→independent null→turn16 consume | R0084 new PID96940 from valid R0079 pair, 20/20 +147 durable days, final paired save `E9B4BFF2…87E1F0`/driver `2F89A595…FAE23`, history157 no tail; cleanup and canonical completed-green | Wait for opportunistic same-build natural recurrence during original 1066 objective; do not unchanged-seed RNG replay; `/root` | EVT #23, progress #24, and R0084 report #25 original/integration refs/worktrees CAS cleaned |

## 2026-09-22 R0085 natural health.1101 100-year-stage RED

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| First independent 1066 seed 100-year stage | R0085 natural event B0 RED; target date1166-09-15 still open | production `g2_preview_operator.py run`→`native-auto-run` with existing 50k-turn/7-day bound | Python349fefd/native B114; R0084 paired `0AE2BE9B…EF0096A`; R0085 frozen `C475CC60…8E5A5` | 90/91 successful, observed+616d/257.41s, then `health.1101` instance17 registry requires extended character/scope/unique-exclusion consumer; no event choice | last safe game save turn77/h259/raw53332848 SHA `85B38878…E588F9` = durable+539d; post-RED driver h275 unpaired at RED; CK3/injector0 | EVT-B0-R0085 exact variant-local consumer + normal/`-O`; later R0086 formal cold bind and action prove this observed branch (below), original RED retained; `/root/event_inheritance` | R0085 report PR #26 original/integration refs/worktrees CAS cleaned; fix PR #27 likewise |

## 2026-09-22 R0086 cold lineage and natural health.1101 modal result

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Health.1101 exact scoped option and R0085 recovery B0 | GREEN for observed modal/action/next turn, `ill` trait readback not claimed; hundred-year gate OPEN | `g2_preview_operator.py run`→formal `native-auto-run --cold-start-checkpoint` | Python original `691c635`→master `08319e5`; native B114; R0086 frozen `B4044ABA…2BB677` | Natural same instance17 at turn13, turn14 recommended authored1/native0 submitted once; independent paused native:27 old17→null and turn15 consumed absence without replay. Original source removes ill in immediate before click; no independent trait readback | New PID87176 confirmed save SHA85B3/actor36403/date53332848, physical h275→259 + new h260 restore. 20/20 +110d, final paired save `E76AE2D6…CB902`/driver `12C700EF…736425`, h287, process0 | Continue original 1066 seed toward paused1166-09-15 from R0086 new pair; R0083 .1000 natural corrected branch still live-open; `/root` | PR #27 code, #26 R0085 report refs/worktrees CAS cleaned; R0086 report branch `codex/progress-r0086-20260922` pending |

## 2026-09-22 R0087 natural epidemic event RED

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| First independent 1066 seed epidemic.1100 continuity | R0087 B0 RED; 100-year/M2 still open | production `g2_preview_operator.py run`→`native-auto-run` existing 50k-turn/7-day bound | Python08319e5/native B114; R0086 paired `B4044ABA…2BB677`; R0087 frozen `04074375…0F4EA` | turn85 instance19 snapshot3, materialized native0/1 shown+enabled, saved epidemic/province/infected_county opaque; option variant consumer rejected, zero typed choice. 84 successful turns, observed +615d/238.61s; safe durable only +581d | safe turn75/h387/raw53349432 save SHA `420393C0…97ADAC`; postRED driver h398 unpaired, read-only formal loader computes h398→h387 but no new physical pair. PID152176/injector0/ledger completed-red | Exact original option-variant contract and source effects, focused normal/`-O`, then new-PID short cold replay from safe anchor; source native0 in feudal may be notice-only, so no M2 material claim from ACK/dismissal; `/root/event_inheritance` | R0087 run no Git branch, EVT fix and report branch `codex/progress-r0087-20260922` active |

## 2026-09-22 R0088 first-seed allied-war counterpolicy RED

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Ordinary first-1066 seed 100-year stage after epidemic contract fix | R0088 WAR-B0 RED; original R0087 epidemic RED live-open, hundred-year stage OPEN | production `g2_preview_operator.py run`→`native-auto-run` 20-turn/900s short affected replay | Python protected `cf2c1de`/native B114; R0088 immutable `F22CE6E9…8C070`; original R0087 `04074375…0F4EA` | 10/11 turns, observed +27 days; natural allied attacker war201326601 player not primary, turn8 raised Army452985015, turn9 advanced, turn10 native strength operational routing values 2242/837 soldiers and AI base power raw6431600000/2720800000, turn11 planner refused to guess combat or chase without exact objective. No epidemic .1100 recurrence, no new event action/material result | New PID135048 verified same actor36403/date53349432/source save SHA and official h398→h387/new h388 restore. No new save: safe h387/raw53349432 save `420393C0…97ADAC` remains; postRED driver `3612001F…F6D59` unpaired and raised army only in discarded tail; CK3/injector0, canonical completed-red | WAR-B0-R0088 exact-build allied-war native tree, scoped read-only/strategy fix only with observed frame; normal/`-O` then one formal focused recovery, not unchanged RNG replay. Current independent progress owner /root; council_gate diagnosing | EVT PR #30 original/integration temp refs/worktrees already cleaned; R0088 evidence/report branch `codex/progress-r0088-20260922` active until protected integration and CAS cleanup |
| R0088 natural `char_interaction.0232` forced-event choice | distinct EVT-B0: degraded generic first-option production consumption, not semantic/material GREEN; original WAR RED remains separate | production same `native_auto_run` turn5 query→turn6 typed native0→turn7 consume | original R0088 `F22CE6E9…8C070`; immutable additive identity correction `4FF8060E…A505B15` | native event definition calc3670232, instance19 reused across cold branches; two shown options. Generic native0 was submitted, independent old modal19→null, but its decision lacked exact semantic inputs, and this entire action exists only in discarded unpaired tail. Epidemic .1100 did not recur | same safe h387/raw53349432; official R0089 no-launch plan `4F510166…B81CD8` retains old h388 restore and discards h389..402 on future bound cold resume; no CK3 R0089 yet | EVT-B0-R0088 exact vanilla options/native consumer, no generic first; both EVT + WAR protected-integrated before one focused restore; /root/event_inheritance and /root/council_gate | original R0088 report master `67561b1` and temp refs/worktree CAS cleaned; this addendum branch pending protected integration |

## 2026-09-22 R0089 exact event loops and physician forced-event RED

| Delivery gate / capability | Status | Formal entry | Artifact / source | Actual game and next-turn evidence | Restore evidence | B0/B1 gap / owner | Branch cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Same first-1066 seed epidemic/rebel call + century stage | technical 20/20 but product EVT-B0-R0089 RED; WAR old branch not observed, hundred-year OPEN | formal `g2_preview_operator.py run`→`native-auto-run` 20-turn/900s affected replay | EVT original `383f87d`→master `c66571e`; WAR original `82a3b67`/rebased `16c6b8a`→master `ba37a03`; frozen R0089 9-file manifest `79661336…3C9FC` | turn6 char_interaction.0232 exact registry authored2/native1, independent modal null and next-turn consume; turn12 epidemic.1100 exact registry authored1/native0, independent modal null and next-turn consume, but county/notification material still unknown. turn18 physician_epidemic_events.1000 option3 rendered native1/2, generic authored2/native1 semantic_unknown; modal null only, not semantic/material GREEN. 20/20, +47 days, old allied WAR branch not recurring | fresh PID165736 restored R0088 h387 source save `420393C0…97ADAC`; final h411/raw53350560 game save `9D900730…A5B7`/driver `C4954A89…672D7C` physically paired **after** generic option, continuation safety under review. CK3/injector0; canonical completed-red despite operator technical qualified | EVT-B0-R0089 exact vanilla tree/variant consumer normal/-O then product recovery review; do not launch 100-year stage on unqualified h411 or call war branch live. /root/event_inheritance event, /root/council_gate restore audit, /root single-instance integration | #33/#34 refs/worktrees CAS cleaned; R0089 report branch `codex/progress-r0089-20260922` pending protected integration; M5 PR #35 candidate valid but not loaded |
