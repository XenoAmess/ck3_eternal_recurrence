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
