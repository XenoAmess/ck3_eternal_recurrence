# G2-M4 LIFE 正式消费者的受控接线（2026-09-16）

状态：`static-ready / live pending`。本包针对标准封建和平治理两年窗口的生活方式最小动作，承接 [原生重心与技能树](lifestyle-focus-perk-ai.md) 已冻结的 exact-build 树，以及 LIFE2/LIFE4 状态和最终合法候选、LIFE6/LIFE7 typed 提交与物质回执。CK3 版本仍为 1.19.0.6；本包没有启动 CK3，也没有把静态测试写成实机 OODA。

`choose_one_life_turn` 先处理强制事件、pending interaction 和战争；只有普通和平 `life-advance` 分支才消费公共同帧 `query-campaign-root-context-v1` 所证实的 feudal government 与战争空集。受控候选随后查询默认 OFF 的 slot43 `private-query-player-lifestyle-formal-v1`。如果同帧管理重心已有未花点，且原生 `CanSelectPerk` 最终合法候选包含 `cutting_corners_perk`，策略选择唯一 `private-select-player-lifestyle-perk-v1`。提交前持久写入 `action_state_unknown` 与 action ID；typed ACK 只表示待核验。后续独立 paused frame 读 `private-query-player-lifestyle-receipt-v1`，仅当 `HasPerk=true`、revision 与 snapshot ID 前进、结果匹配当前 episode 才确认 applied，再把物质回执交给下一正式 turn 消费。未知状态阻塞该动作，禁止盲重试。

受控入口是 `native_auto_run(..., completion_contract="bounded", allow_private_lifestyle_formal_trial=True)`；普通正式入口不传该 flag，公共 query/action、MCP、能力广告和公开 schema 均不变。该 Python source 消费接线只有聚焦 normal 与 Python `-O` 测试证据，不能凭私有单动作宣称 production-live loop。open_kaishek 当前没有 LIFE 私有消费者，公共接口兼容；后续若公开 typed 资产，必须先冻结版本及被动适配格式。

当前阻塞是 exact-build 的 LIFE2/LIFE4 私有 slot43 查询将当前玩家状态与已绑定的 lifestyle window 最终候选绑在一起。普通 production 存档若当前 window 未绑定，查询会回 `native_lifestyle_state_or_final_candidates_unavailable`，不能将其解释为合法空候选。R739 的封建/和平公共根已观察，但未采集 LIFE current focus、XP/点数、window 或原生最终合法性，因此尚不能封成“可做真实 perk”的实机 READY 候选。下一项最小施工是同版本只读当前玩家状态与 window/source 绑定诊断，并在唯一 CK3 负责人控制的真实 paused R739 对照帧核验；若合法 perk 不存在，记录真实场景并寻找合同允许的场景。focus 动作所需的 target stewardship progress 仍缺源，本包没有注册或广告 focus。

有界实机收口须固定 CK3 EXE SHA、DLL/source/Python commit、mod/DLC/profile、普通存档、起始 frame、动作及 checkpoint 位置；断言公共根 → 私有同帧合法查询 → 正式策略选一个 perk → typed submit → 独立后帧 `HasPerk` → 下一 turn 消费，并检验状态/暂停/停止。slot43 内存 pending ACK 暂不能跨真实 CK3 进程冷恢复；需另按恢复合同查询实际游戏状态、保留 action ID 后再认定 cold restore，当前不宣称治理恢复门通过。
