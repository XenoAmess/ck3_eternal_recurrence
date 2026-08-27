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
| GEN-001 | B0 | 一代人 supervised runner | 现有 managed runner 覆盖战争或专用 fixture，尚无“直到玩家死亡”的统一终止合同 | 固定 seed、无人输入循环、周期 checkpoint、死亡/一代结算终点、首个 blocker artifact | 待施工 |
| GEN-002 | B1 | 当前事件有多个合法选项 | current-window identity/presentation 与有限 indicator 已 live；scope wire 已 static-ready；完整效果与 semantic readiness 仍不足。现已实现只吃 same-frame shown+enabled 的可审计 fallback，并把直接动作升级为旧 full instance 必须推进 | 正常交互桌面完成 scope query 与多选事件 degraded selection live；artifact 验证候选账本、预期 native index、旧 instance 推进、paused/episode/cleanup | static-ready；live 待 `GEN-008` A/B |
| GEN-003 | B1/B2 | pending character interaction | ordinary white peace typed primitive 与 notification ACK 已有；其它 stock terms/effects 不完整 | 对必须答复的合法互动提供按类型的最小 accept/decline/ack policy，并验证旧 full ID 消失 | 未开始 |
| GEN-004 | B1 | 已有战争到终局 | 移动、围城、接敌、战斗 hold/retreat 与 normal terminal 较成熟，但完整 victory/white-peace/surrender 路径未闭合 | 当前 run 遇战时至少有一个合法终局路径、战后解散/保存/继续 | 未开始 |
| GEN-005 | B2 | 非战争长期治理 | 经济、内阁、生活方式、家庭等大多不是通用 native semantic policy | 不出现强制 UI 时允许时间推进；出现阻塞则提升为 B1 并补最小动作 | 记账观察 |
| GEN-006 | B1 | 自然死亡与结算 | 一代结算 snapshot/immutable seed primitive 已有，但尚无自然完整 episode | runner 观测玩家死亡，读取结算、保存 artifact 并正常终止 | 未开始 |
| GEN-007 | B2/B3 | 战斗质量 | reinforcement assigned/join、异常 terminal 与 forecast 未全闭合 | 若不阻塞当前 run 先记录；真实卡住或导致无法结束战争时提升为 B1 | 记账观察 |
| GEN-008 | B0（环境） | 当前执行会话无法启动 CK3 live acceptance | 相同 exact EXE/save/runner 在 `CodexSandboxOffline`、`WinSta0\\CodexSandboxDesktop-*` 中于启动期固定崩溃 `ck3+0x1DABD89`；当日既有 live GREEN 均来自 `xenoa` 的普通交互环境。事件 scope query 从未执行，因此不能判为 capability RED | 在 `xenoa` 正常交互 PowerShell / `WinSta0\\Default` 原样复跑 a860702 default-off acceptance，完成同命令 A/B；在此之前继续可离线的 blocker-removal，不改 native 逻辑掩盖环境差异 | 外部 A/B 待执行 |

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
