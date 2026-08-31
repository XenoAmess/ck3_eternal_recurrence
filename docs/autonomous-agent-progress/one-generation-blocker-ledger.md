# 一代人自治：阻塞与能力债账本

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
截至 2026-08-31，同一冻结 seed 的第二完整寿命、结算与再次跨 episode loop 已完成；当前 broadened G2 continuation 的新 blocker 是
WarID `50331699` / `raiktor_claim_cb` 的 primary-attacker surrender 只有 typed partial，尚缺六域 dynamic terms，不能把合法且 auto-accepted
的 surrender 直接当成已可决策或已可执行。

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
| GEN-034 | B1（G2） | Raiktor 特殊战争可合法投降，但 CB-specific actual terms 不可观测 | frozen continuation 的 CharacterID `29829` / WarID `50331699` 为 primary attacker，`raiktor_claim_cb`、1281 日、战分 `-50`；surrender validator/available/auto-accept/`would_accept_now` 全真。`05ae0bf` 只发布 claimant/targets/claims 与静态 formula；actual gold、favor-hook、war-bound regiment（active/cleanup）和 PoW 已有相互独立且 fixture-confirmed 的 native core，但尚未组成统一 terms wire，dynamic/decision/action readiness 全 false | 实现 gold、F/prestige、truce、PoW、favor hook、war-bound army 六域 same-frame reader；静态闭合 add-hook preview 与 regiment origin/lifetime 两个 reverse gap；普通 `claim_cb` 不变，旧 crash reader 继续禁用；一次 CK3 启动完成双查询、typed surrender、六域 postcondition、postwar checkpoint | partial native implementation/fixture；统一 wire、policy、MCP 与 live pending |

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
- [static design] GEN-034 的最小解除范围固定为六域：actual gold；`cb_prestige_factor` 与 attacker prestige delta；truce days/expiry；
  实际 PoW release pairs；conditional favor-hook application；按来源 regiment 读取的 current war-bound army losses。faction/opinion/feud/
  Mandala/LAAMP 留作显式 broad 能力债，不伪装为零，也不阻塞这个窄 `decision_terms_ready`。完整 reader 与策略合同分别见
  [war-termination.md](../ck3-native-ai/war-termination.md) 和
  [player-war-exit-policy.md](../ck3-native-ai/player-war-exit-policy.md)。
- [static design] gold/F/PoW 可复用既有 exact ABI；truce 复用 `0x3373000`，只差一次 pointer-only Raiktor root shape probe，并且绝不执行
  ContextEffect。剩余两个 reverse gap 是：（1）`add_hook` effect vtable、preview callback/collector slot 与 favor-hook type identity；
  （2）`spawn_army war=scope:war` 在 CRegiment/special-troop 对象上的持久 origin、bound-WarID、keep=false 字段及 serializer。
  ArmyID、参战方、名称或初始 3000 人都不能替代来源字段；合并后的军队必须按 surviving regiment 追踪。
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
