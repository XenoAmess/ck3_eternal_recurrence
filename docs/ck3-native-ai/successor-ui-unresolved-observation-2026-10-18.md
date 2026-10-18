# 继承后 UI 的未解决状态投影

`machine_id: xenoamess-full-tower-eb9d2c1186`，源码封装观察时间 `2026-10-18T11:17:16Z`。
来源为当前公共源码和合成软件输入；[机读证据](evidence/successor-ui-unresolved-observation-2026-10-18.json)绑定源码 SHA、命令和边界。本次没有读实际游戏、Driver、SAVE、原片或运行树，没有调用 Native、MCP、桌面或游戏。

原 timeline 合同允许 `identity=none` 同时保留 `has_open_succession=true` / `blocks_simulation=true`。它表示未解决的原生观察，不能凭 `none` 认定继承 UI 清除；事件消失、逻辑玩家/episode 已切换也不能代替清窗读回。事件的 root 仍可能是前任，不能为了匹配新玩家改写 scope。

新纯函数 [project_successor_ui_observation_v1](../../ck3_autonomous_player/src/xar_autoplayer/bridge/succession_ui_observation_v1.py)接受稳定的继任者快照，以及**原 guarded Service 查询返回的内部 context**。它复用原完整 timeline/event normalizer，校验当前 Native revision/date/event instance，保留完整 timeline 和原事件 root；事件 build 必须匹配快照 exact hello。快照必须 paused/map-ready、玩家 alive、episode identity 已稳定且角色一致，并带 Game PID/连接代次。函数不做查询、文件读写或 UI 操作。

| `ui_clearance` | 观察含义 |
| --- | --- |
| `modal_present` | 原生明确识别 death/game-over/select-destiny surface；不因此授权 Continue。 |
| `unresolved` | `none` 但任一 open/blocked 为 true，或仍有活动事件。 |
| `unknown` | timeline 来源不可用，保留未知。 |
| `clear` | 同帧 timeline available、identity none、open/blocked 双 false，且没有活动事件。 |

事件不可用继续保持不可用；它不会阻止原有陌生事件处理策略，也不提供选项映射或选择授权。活动事件处理后，调用方仍须取得新的 timeline 读回，之后按原 typed Close/独立后验合同处理仍在的 modal。即便投影为 clear，它也不授权 SAVE/Close、普通信用或未知动作重试。

这个叶不能证明查询来自所声称的进程，不能替代 owner 的原 source epoch、Game birth、query envelope、继承逐 title reconciliation、once intent、实际保存与独立 postSEM/MET。调用方必须继续保留这些原证明。当前没有把它接入任何 owner/SDK/Host06/P85 事务，没有授予 deferred checkpoint 资格或整条事务已通过的结论。

4 项新 focused unittest 最终通过（0.005s；含 8 个坏输入子例），使用实际原 normalizer，但所有快照、事件、日期和 PID 均为合成：旧 root/新玩家共存、不可用事件、事件消失但 open 仍 true、三类 modal、严格 clear 和 unknown，以及旧帧/异事件/异 build/待决 episode/混合角色/消失后陈旧事件。没有重跑历史九 call 或 P85 矩阵。CI 已接这一个小测试文件。

M7 仍缺多 ruler/seed/government 的实际普通游玩及继承和精确配对 checkpoint 的真实新 Game 冷恢复；同场两次自然继承与 SDK-only 轮换不能补齐这些格。M6 自然命名收益→终态→之后普通使用仍须实局来源。G2 保持 **6/8**。

2026-10-19追加（machine_id: xenoamess-full-tower-eb9d2c1186，封定2026-10-18T16:33:54Z）：公共owner新增内部opt-in持久UI义务；[源码与软件测试摘要](evidence/successor-ui-pending-ledger-source-2026-10-19.json)绑定六叶。原before_submit全部旧守卫及外部拦截通过后，先写handoff_unverified、文件fsync并读回，再允许原logical Continue；原full/title/persist通过才转pending。首次保留失败留下未验证意图，只收集原回执、不重发。冷读重跑原完整验证，核机器、源码epoch、原Game出生/镜像、goal/actor/episode；新SDK连接另需原ledger SHA到新帧的精确内部授权，epoch仅初始化计算一次。

binding摘要不能自签授权：真实Service必须使用实际driver登记、由ledger.load签发的同值binding，重核磁盘SHA、原Game/源码epoch与完整证明。伪造birth/epoch后重算摘要仍拒。原typed Close前按proof SHA建立create-only UNKNOWN意图，fsync/读回失败零提交；ACK、异常、结果写失败均保防重锁。原Close validator和独立post通过才resolved；原_materialize_checkpoint先拒未解决义务。原full/Close/timeline验证器AST未改，无pending且无opt-in沿旧路径；已有pending缺binding在session前拒。

Root最终独立跑新旧两模块12测试通过（chunk521b2c，body0.953秒／实际外层0），包含真实Service伪造拒绝、冷owner先Close后普通AUTO、0Continue重放及失败守卫；早期失败在摘要保留。全为合成端点和临时小JSON，零真实Native/SDK/Host/游戏/桌面/媒体操作。仅支持原Game仍存活的owner/SDK重建；新Game／载SAVE后出生改变按设计拒，冻结Host06/SDK未采用，旧report缺出生证据不补造。没有directory-fsync或掉电完整性保证。M6命名收益终态、M7跨Game/多格实局仍缺，G2继续6/8；不授影片或业务完成信用。

2026-10-19追加：采用接缝只读审计。`machine_id: xenoamess-full-tower-eb9d2c1186`；实际源码观察始于 `2026-10-18T17:12:07Z`，HEAD `91c570484452a915dcc24024de5ce166e48e1c85`。以下是待实现的采用合同，**Host06 当前未采用**。

实际 SDK 入口是 `bridge/mcp_server.py:460 load_driver` → `:503` 创建 driver → `:1644 create_server` / `:1660` 闭包 Service → `:2867 ck3_auto_turn`；这条链不进入 `native_auto_run`。queue owner 与 App 分进程，不能用 queue 的 ledger 对象或自签 JSON 代替 App 登记。安装应在全部原 policy 后、原 `create_server` 前；用 canonical `xar_autoplayer.successor_ui_pending_ledger_v1` 在真实 driver 上初始化。仅复用首次真实 SEM 与 OS identity，核旧 ledger/epoch/birth 后 load 签发内部 binding；此前 pending 挡 AUTO/Close/SAVE，保原只读入口。源码 SHA 仅初始化计算。

四处消费接缝按序补齐：

1. 原 `before_auto_turn_submit` 显示/ACK及所有拦截通过、返回 None 后才写 preintent；不能替换 publisher 回调。
2. App 增 after-result 留存：保原 AUTO 全文及 `mcp_server.py:2899` 原 persistence-failed 分支，经原 full/title/goal/persist 验证才 retain；此处不提前 Close。
3. `tools/g2_saved_campaign/m7_ordinary_successor_queue.py:291 finish_transition` 仍旧 raw timeline 分支，`:327 checkpoint_if_clear` 只看事件。薄 adapter 需消费 deferred 义务，保 none+open 矛盾和旧 root，事件交完整普通 planner；事件消失后仍取 fresh timeline，不能提前 SAVE。
4. App 原 guarded timeline/typed Close/SAVE 需持有同一登记对象：Close 前唯一意图，原完整 Close 与独立 post 后 resolve，再允许原 SAVE。当前公共 SAVE 不经过 `native_auto_run._materialize_checkpoint` 新门。UNKNOWN/ACK后不得再建意图或重发；所有原继承/六帧/title/goal/persist 门保持。

无游戏最小资格应穿新生成 App 全 bootstrap、registered MCP 软件端点及真实 queue coldloader：原 Continue→旧 root 事件→同 birth 新 conn 冷 load→普通事件→fresh timeline→唯一 Close/SAVE；拒绝未登记/别名 class、伪 epoch/birth 重签、既有 UNKNOWN、持久失败和 none+open 提前 SAVE。复用原 validators，不将纯 ledger 测试当整 owner 资格。

真正运行缺口仍是新 COW 实际入口/source tuple、首个真实 Game birth/preintent、自然继承全后验、同 Game 冷恢复门禁/Close/独立 post/SAVE及随后普通执行。fresh1066 必须建立新 state/真实 birth，只迁来源知识，不迁旧 UI ledger；载 SAVE 或新 Game 的 birth 变更必须拒此 sameGame 授权，另需 checkpoint/lineage 合同，不能回填旧出生证明。仓库未见 private Host06/freeze producer，旧回执不能冒新采用。此轮未写代码、测试或运行树，M6/M7实机缺口未补，G2仍 **6/8**。

2026-10-19追加：App preintent→retain 的最小采用边界（尚未实现）。`machine_id: xenoamess-full-tower-eb9d2c1186`，本轮实际仓库源码观察 `2026-10-18T18:37:10Z` 起；没有重查 Git 或读取冻结树。

新增证据是参数缺口：`GameplayBridgeService.auto_turn(self, *, before_submit=None)` 在 `service.py:4753` 执行一次原 `_execute_planned_turn`；`:5037` 原回调**仅**得到 `{plan, selected_step, snapshot_id, revision}`。`:1778 plan_turn` 返回 detached deepcopy；`:676 _observed_planning_source_frame` 的八字段含 actor/PID/conn，却没有 terminal、前任 episode_character_id、campaign goal。故不能把现回调直接接 `ledger.begin_transition(before, candidate)`，不能用 result.reconciliation 倒造提交前证明，也不能把 plan summary 补成真实 snapshot。

现有实际签名可保留：`load_driver(factory, *, state_dir=None, succession_lifecycle_binding=None, ...)` → `create_server(driver, *, profile_dir=None, before_auto_turn_submit=None)` → App 内闭包 `GameplayBridgeService(driver)`。queue 的 `continue_successor(queue, expected_episode, transitions)` 通过原 `queue.call('ck3_auto_turn', {}, ...)` 进入此 App；`consume_completed(queue, turn, response_path, source_snapshot, source_path, transitions, checkpoint_pair=None)` 只消费原回执。跨进程没有可信内存 ticket 传递，SDK不能直接使用 queue 的对象/JSON 注册权限。

下一小补丁仅宜做 App 内 preintent→retain，不顺带自动 Close：真实 driver 初始化/冷 load 后登记 canonical ledger；仅在原 planner 实际选 Continue、原显示/ACK回调返回 None 后，由 App 保留真实 pre snapshot/capabilities 的内部 ticket。优先复用已取得且可证明 exact 的原快照；若没有，只在这一稀少分支取 history-free pre/post 与 caps，并严核 candidate 的 snapshot/revision、原 planned 八字段与真实 pre 六帧/PID/conn。非 Continue 不读、不写。意图之后若 revision 拒绝或结果未知，仍保 handoff_unverified，不能清锁重发。

原结果已提供 `reconciliation`、新旧角色/episode、自然继承标记及 `driver_state_persistence_diagnostic`，应原样复用；这些不是独立 post snapshot。App result hook 可在 `:4753` 后、原结果仍保全时，用实际 post 与原 `_verify_natural_succession_transition(result, *, snapshot, binding, before, succession_lifecycle)` 验证，再 `ledger.retain(transition, snapshot, *, verification)`。goal 可复用 SDK `strategy.py:6226 continue_ordinary_campaign_goal_v1(pre_goal, reconciliation)` 算期望，和真实 post normalized goal 全文相等；queue 原 `goal_matches` 仍独立保留，不跨进程回调、不移门。retain失败必须保原 AUTO/失败诊断及 once 锁；不得遮蔽原已应用动作或改变 `mcp_server.py:2899` persistence-failed 分支。后继 deferred UI仍需上一节 queue/Close/SAVE采用，不能靠这一小补丁称完整 READY。

代表软件测试只需实际 App/registered MCP 的一次 Continue：原callback先运行、唯一 preintent先于原executor、原完整验证后retain、返回原结果；再拒绝缺pre/混合四元组、callback拦截零意图、pre写失败零执行、post/goal错误保原已执行回执且禁止重发；普通step断言0新增 snapshot/caps/ledger写。此轮仅建议，**未运行这些测试**。来源实际 SHA256：service.py `912eed9b61d2879a82c78bc9602ef6fb8efb9c86bfea1def4fc1d98fcd48a116`；mcp_server.py `979303fcdd4dee9811dc748a289a16091d65def4521596737b1180eb9f0a078a`。Host06仍未采用，实局自然收益/跨格继承与新Game冷恢复仍缺，G2保持 **6/8**。

## 2026-10-19：常驻 App 与实际 Queue 采用已实现，尚未部署实机

`machine_id: xenoamess-full-tower-eb9d2c1186`。机器身份于 `2026-10-18T19:13:15Z` 由 `tools/ck3_live_run_id.py machine` 实际读回；最终软件验证的精确 UTC、命令、源码 SHA、早期失败及边界见 [机读回执](evidence/successor-ui-app-owner-source-2026-10-19.json)。以下追加实现事实，不将上文历史建议改写为当时已完成。

结论：已经有合法原生继承和角色重绑；此前完整 App/Queue 对继承后窗口及持久义务的采用不完整。本次补的是常驻采用链。**采用新源码的同一个 App/driver 可处理多次自然继承，不要求每次死亡改代码或重启智能体。** 当前已录素材使用的冻结 Host06/SDK 不会因此热更新；本次没有改冻结运行树、重启真实智能体、启动下一局或进行实机复验。

继承人先由 CK3 的合法继承规则决定。`continue-as-reconciled-successor` 对 CK3 已经切换的真实玩家核对原期待与每项头衔，随后重绑 episode 和既有 campaign goal；该逻辑步骤不是任意指定角色，也不发出更换统治者命令。后续 death modal 的 typed Close 是另一项动作，必须独立证明清窗及日期结果。真正无合法后继、对账不匹配或 game over 继续保留真实终局，不伪造续行或另开局。

实际采用路径为 `create_server` → 同一个 Service 的 [App owner](../../ck3_autonomous_player/src/xar_autoplayer/bridge/successor_ui_app_owner_v1.py) → 原 dispatcher/driver → [Queue consumer](../../tools/g2_saved_campaign/m7_ordinary_successor_queue.py)。只有既有 ordinary lifecycle 且原 successor 原生通道已合法启用的 driver 自动安装此 owner；没有新增 opt-in，也不替未资格 experimental 能力开门。已有 pending 却缺合格 owner 时在变更前拒绝，保留只读诊断。

1. 原完整 planner、所有原拦截和原显示/ACK 回调先运行。只有实际选中合法 Continue 才额外取得提交前的 history-free snapshot/capabilities，逐项核原计划八字段、前代、真实 OS Game birth/image、生命周期和 goal，随后 fsync/读回唯一 preintent，再执行原逻辑步骤。
2. 使用独立 post snapshot/capabilities 跑原完整继承验证，并以原 `continue_ordinary_campaign_goal_v1` 算出的期望全文比对实际 goal；原 driver persistence 门仍在。通过后登记 canonical ledger 的 pending。失败保全原已执行/未知回执和防重锁，MCP 返回包含原完整 turn 的错误诊断；不因留存失败重发 Continue。原 persistence-failed 分支仍优先。
3. 旧 root 事件仍交完整普通 planner；陌生事件沿原采集和第一显示可用选项策略，角色交互通知继续使用原策略。未解决的 UI 义务跨普通事件处理保留。事件消失之后必须重新查询 timeline；`identity=none` 同时 open/blocked 为 true 仍不能 Close 或 SAVE。含 pending interaction 时先延后 UI 清窗，不能越过通知。
4. `ck3_resume_successor_ui_v1` 是观察入口，不隐含提交 Close。实际 Queue 保持观察 RPC 与 typed Close 分离，保留原 async 取消在动作前的阻断。Close 同样先执行原显示/ACK 回调，落唯一 UNKNOWN 意图，执行原 typed 通道与完整 validator，独立 post 通过才 resolve。ACK、异常、留存失败都不会重新武装动作。公共 SAVE 和 generic save step 都受同一 ledger 门禁。
5. App 自己的 AUTO 也能继续处理 pending：普通事件继续走普通 planner；合法 modal 则完成一次 Close，原回执随 `successor_ui_resumed` 返回。实际 Queue/ordinary loop 对这个结果单独消费，不把它当另一场自然继承或另一个普通 cycle。SAVE 仍使用独立当前帧。

同一个 Game 的 SDK/App owner 重建可重新加载义务：核机器、源码 epoch、实际 OS birth/image、原完整继承证明和当前 goal，由实际 App 的 canonical ledger 签发新 connection binding。Queue 只保留这次实际 App 响应作为读回证据，不改旧 successor proof，也不把客户端 JSON 传回注册或授权 Service。新 Game、载 SAVE 导致 birth 改变、来源改变或 UNKNOWN Close 均拒此 same-Game 恢复，不提供通用迁移捷径。

包内新增机器身份叶由 [生成器](../../tools/gen_ck3_live_run_identity_package.py) 从 `tools/ck3_live_run_id.py` 的原 AST 精确投影，算法保持单一来源；不再假设外置 SDK 存在 `../tools`。当前 setuptools 自动发现 `xar_autoplayer` 包的 `.py` 叶；未来 COW/freeze producer 必须包含新 owner、生成身份叶以及 epoch 所需的全部源码，缺失即拒绝 bootstrap。隔离 cwd、Python `-I`、仅提供 package src 路径的完整 registered MCP bootstrap 已通过；这不是某份冻结 SDK 已实际部署的证明。

最终实际子进程与外层均 0：**36 tests / 26 subtests，19.60 秒，chunk `7e17db`**。测试穿真实 registered MCP Client、Service/dispatcher 和同步/异步 Queue；driver、planner 的当前选择、过程身份与所有游戏帧均为合成。覆盖同 App 两次继承 `19→23→29`，原 origin 不变、goal progress 精确 `+2`、同 driver/ledger；完整旧 root 陌生事件→fresh timeline→唯一 Close→SAVE→后续普通 turn；同 birth 新 connection 的 App 重建后真实 Queue 完成旧事件/Close/SAVE；原 completed 逻辑 Continue 和 AUTO 清窗回执各自消费且不重放；拦截、混帧、缺 goal、错误 post/goal、原 persistence/retain 失败、none+open、UNKNOWN ACK、异 birth、无合格 owner及真终局。无 pending 的普通 turn 断言没有新增 snapshot/capabilities RPC。原 full/title/Close validators 没有改写。早期两项实现缺陷和一次合成 fixture 缺字段的失败保留在回执。

已有历史实机来源仅在此精确复用一条：[AUTO368 子链](evidence/p50r1-natural-successor-actual-2026-10-18.json)，同机器 `2026-10-17T19:27:31.655608Z`、Game51028/birth FILETIME134367033244212072，`31254/native-31254-8d3a8440eb30 → 40695/native-40695-9cf747ffe1ee`，titles2230/2231/2262 matched；一次 Close372、SAVE374、SEM375 保原 campaign/origin31254、current40695/progress1，随后 FULL376 十轮普通游玩。其前置 AUTO361 曾需要保留原回执的元数据恢复，不能用该成功子链宣传整场没有维修。永久存档中的 actor82925 不单独证明第二次继承完整闭环；本次第二次继承是软件代表，不补实机信用。

本包只有小型源码、临时 JSON 和精简记录；无媒体读写、全盘扫描、大文件哈希或永久存档操作。仍须在后续用户允许的新运行中建立实际 source tuple/Game birth/preintent，并自然取得全后验和普通玩法。新 Game/SAVE lineage、更多 ruler/seed/government 与 M6 自然收益终态仍未由本补丁验收，**G2 继续 6/8**。

### 2026-10-19 追加：原 driver 异常后的 direct Continue 防重修复

`machine_id: xenoamess-full-tower-eb9d2c1186`，实际软件验证 UTC 与完整新源码 epoch/pins 见 [独立修复回执](evidence/successor-ui-app-owner-once-repair-2026-10-19.json)。先前 36 tests 及 Root 独立复核仍是其当时真实结果，**没有覆盖原 driver 抛异常后再走 public `ck3_execute_step` 的分支**，不追认当时已经堵住此缺口。

独立只读复查发现：旧 `before_continue` 写入的内存 ticket 同时被 generic driver gate 当作权限。原 driver 抛异常时未走到 `after_continue`，ticket 残留；AUTO 的持久 pending/load 门能阻止再发，但 public generic step 可能再次进入原 driver。软件负对照只用 HEAD 旧 `driver_step` AST 替换内存方法，两个模式真实重进 driver 到两次：原动作未应用模式为 `2 attempts / 1 applied`，已应用但结果未知模式为 `2 / 2`；原本要求分别为 `1 / 0` 与 `1 / 1`。该旧 guard 负对照实际外层 1、两项 async 包装断言 errors，保留真实分类，不当作正常成功。

现将证据 ticket 与提交权限分开：只在当前 App AUTO 调用栈及原线程内、durable preintent 已读回后，建立一次 dispatch permit；进入原 driver **之前消费**，所有返回和异常均在 `finally` 撤销临时 scope/permit。ticket 残留不再授权 generic 请求。原异常继续返回，持久 `handoff_unverified` 与禁止重放标志均不清除；不依赖底层 driver 恰好已经清掉 reconciliation 才防住第二次调用。

新增用例穿实际 registered MCP：原 driver 在应用前抛异常、或应用后返回未知异常，然后依次调用 generic Continue、AUTO、generic Continue，均确认原 driver 仍只被调用一次、应用计数分别为 0/1，原错误文本保留且 ledger 仍未验证。最终新源码 **37 tests / 28 subtests，20.17 秒，chunk `e76ccb`，实际子进程及外层均 0**。没有部署冻结 SDK、操作真实游戏或增加 G2 完成信用，仍为 **6/8**。

## 下一次获准运行时的低开销采集清单

`machine_id: xenoamess-full-tower-eb9d2c1186`；本轮仓库源码只读观察从 `2026-10-18T19:31:02Z` 开始，本文追加于 `2026-10-18T19:39:36Z` 之后。仅核仓库源码、权威 requirements 与小型软件回执；没有运行新测试、Git、Game、Native、MCP、桌面或媒体操作。

新公共源码已经具备实际 App 采用点，不能继续描述为“只有 native-auto-run opt-in”：`create_server` 构造同进程 `SuccessorUIAppOwner`，在真实 driver 上登记 canonical ledger；仅原 `ordinary_campaign_succession` 与 private death-Continue 许可同时满足才启用，未准入配置若已有 pending 仍拒。Service 在原 callback 后保留 preintent，原执行结果后用真实 post、原 full 验证器及 SDK goal 函数 retain；Queue 独立保留 full/title/goal 门，再消费 App resume、typed Close/独立后验及 SAVE。上节已另记 direct Continue 异常后的 once 缺口与修复，不把原 36 项测试外推为该分支当时已安全。当前只能称公共源码和软件组合闭包；**冻结 Host06 / future1066 entry 尚未采用，真实运行仍未资格**。

1. **启动只采一次身份与来源。** 在用户允许的新运行中，从实际既有启动回执及首个合格帧留存 machine/UTC、Game PID/真实 birth/image、EXE/Native 身份与广告、实际 SDK/App/Queue/source epoch、episode、campaign goal、government_key/family、初始 checkpoint/seed 来源。不要从统治者姓名推政府，不以新标题/PID/SDK认定独立 seed。新 Game 用新 state/ledger；只迁来源知识，不迁旧 UI 义务。此项不是当前启动许可，也不允许补填旧 birth。
2. **自然边界复用原请求，不重复提交。** 批末只索引已经完成的原 AUTO 与独立 pre-terminal、SEM/CAP、小投影来源，按 machine+campaign+old/new episode 去重。留存原六帧/PID/conn、旧 expectation 的实际来源帧与距死亡年龄、逐 title reconciliation、原 goal 与 post goal；较早 first-heir 观察不能升级成死亡前 fresh 全 title。原 App preintent/obligation 和 Queue thin 都是来源，两个 owner 的同一转换不能算两次自然继承。未知、持久失败或原请求尚未结算时，只收集原回执，禁止再次 Continue。
3. **UI 事实与动作分开。** 保留原 timeline 的 identity/open/blocked、当前事件 instance/definition/旧 root，以及 App 的 pending/clearance。none+open、事件消失或新 actor 均不等于清窗。原事件交完整普通 planner；必须由 fresh timeline 决定原 typed Close 是否需要且合法。Close 保留唯一意图、完整原结果和真实 ending date；随后原独立 SEM/MET、checkpoint 物化配对及后继普通 plan/结果各保来源。Close 内置时间推进单列，不造额外普通 cycle；ACK、submitted、婚配 pending 或移动命令不能升级为清窗、婚配成功、已到达或战争获胜。
4. **cold 证据顺应实际维护。** 不为每个 batch 专门重启。若本来需要同 Game 的 SDK-only 维护，保旧 ledger SHA/源码 epoch、原 birth、正常旧 owner 关闭、实际新 conn、first paused SEM、内部 rebind 与 0 重放，之后观察原待办完成及普通执行。真正 SAVE→新 Game 的 birth 改变仍会被此 sameGame ledger 拒绝：另需旧进程真实退出、精确 checkpoint/配套状态、真实新 birth、同 episode/高层 goal、无旧动作重放及随后普通执行的 lineage 合同和实证。不能把 SDK 重连或永久存档中的 actor 字段当新 Game 冷恢复通过；现补丁没有授该资格。
5. **M6 按原 action/full instance 收完整生命周期。** 正常 planner 自然 Start 后，留 action/actor/target/完整 SchemeID/generation、真实 applied receipt 与独立唯一实例。继续保较早 `scheme_sway_opinion` baseline、首次新增正增量的 `first_named_gain_intervention`、后来 `terminal_intervention`，以及后续普通消费的 `following_native_revision` / `following_date_raw` 与归档 `previous_interventions`。首次正增量来源不能被最终同值 material 刷新替代。总好感、Start ACK、phase success、行消失、手动 typed Stop 或 `terminated_unattributed` 各自不足以报有用自然终局/原因归因；保留原合同的未知，而非制造成功。
6. **复用月门与已有返回体。** 优先采普通 AUTO 的 post-Start、quiet-query、合格 stationary-hold optional 回执及原 ledger 的状态变化；无 active、未到期、原 pending 和缺资格分开统计，不新增每 AUTO RPC、手动 Start/Stop 或抢战争行动。只保存首次具名增量、终态/后续消费及身份变化的来源。批末离线计数分清零机会、cooldown、pending、native unavailable、阶段收益、terminal 与 following，不从零 Start 推断缺 flags，也不以缺某项采集为当场新增 stop-gate。

以上字段只从已结束的小回执/已有小投影抽取 path/bytes/SHA 和必要指针，不复制完整 history、Driver、SAVE 或媒体。单件过大且没有已有小投影时记 `oversized_source/not_observed`，不能为此在普通运行热点重扫大正文。下一局同为封建罗贝尔可增加新来源的自然连续性，但不会自动补另一 government family；独立 seed 仍须真实 initial-state 来源。合法分封/改宗主/独立变化如实记，不新增为 M7 必测死亡变体，尤其不能把主动授独立算自然继承。

验收仍按 [原 requirements](../autonomous-agent-progress/g2-requirements-v1.json) 和 [M6/M7 覆盖合同](p55-g2-m6-m7-natural-coverage-2026-10-18.md)：M6 尚缺当前可采纳 source 下真实具名新增收益→自然有用终态→普通后续消费；M7 尚缺 multiple rulers/seeds/governments 及精确 checkpoint/继承后的高层意图恢复的更广实证。已有两次同场角色转换、公共 resident 采用和软件冷连接组合均不自动补齐。**G2 保持 6/8；本清单不增加实机、影片或业务完成信用。**
