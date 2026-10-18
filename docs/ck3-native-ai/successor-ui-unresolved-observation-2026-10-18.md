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
