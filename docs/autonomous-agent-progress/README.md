# CK3 自动游玩智能体进度中心

本目录是自动游玩智能体的统一进度入口，回答四个问题：终极目标是什么、现在真正会什么、还缺什么、最近做了什么。
它不替代 exact-build 逆向证据、ABI 合同或实机 artifact；详细证据仍保存在
[`docs/ck3-native-ai/`](../ck3-native-ai/README.md) 与
[`docs/testing-workflow.md`](../testing-workflow.md)。

## 导航

- [终极目标、当前能力与完整路线图](goal-and-roadmap.md)
- [2026-W35 一代人自治 blocker / 能力债账本](one-generation-blocker-ledger.md)
- [G1 一代人全寿命 production 续跑交接（2026-08-28）](g1-production-handoff-2026-08-28.md)
- [一代人 20-turn production canary 交接（历史）](one-generation-canary-handoff.md)
- [日/周计划会制度与模板](meetings/README.md)
- [2026-08-29 早会（补录）](meetings/daily/2026-08-29.md)
- [2026-08-28 早会](meetings/daily/2026-08-28.md)
- [2026-08-27 早会（补录）](meetings/daily/2026-08-27.md)
- [2026-W35 周计划会（补录）](meetings/weekly/2026-W35.md)
- [2026-08-29 日报](daily/2026-08-29.md)
- [2026-08-28 日报](daily/2026-08-28.md)
- [2026-08-27 日报](daily/2026-08-27.md)
- [2026-W35 周报](weekly/2026-W35.md)
- [2026-08 月报：完整能力盘点](monthly/2026-08.md)
- [2026-08-27 阶段成果演示手册](demos/2026-08-27-event-window.md)
- [Show-off 视频规范与索引](demos/README.md)
- [日报模板](daily/TEMPLATE.md)
- [周报模板](weekly/TEMPLATE.md)
- [月报规范与模板](monthly/README.md)

## 信息层级

当不同文档的表述发生冲突时，按以下顺序核实，不用进度报告覆盖底层证据：

1. exact-build ABI JSON、生产代码与冻结 artifact；
2. `docs/ck3-native-ai/` 对应专题及 Mermaid 原生决策树；
3. `docs/testing-workflow.md` 的实机验收记录；
4. 本目录的路线图、日/周计划会、日报、周报和月报摘要。

计划会、日报、周报与月报是便于持续协作的索引，不是把 `implemented` 升级为 `live` 的证据来源。报告引用的状态必须能回链到上述
前三类材料。

## 状态词汇

| 状态 | 含义 |
|---|---|
| `research` | 已有原生数据或反汇编研究，但尚未形成可用生产接口。 |
| `static-ready` | ABI、实现和离线测试已闭合，尚无真实 paused production 验收。 |
| `fixture-live` | production bridge 在明确的外部夹具/playset 中完成实机闭环；不能外推为 stock 全场景。 |
| `production-live primitive` | 某个真实只读查询或动作原语已通过生产实机，但尚未形成完整策略闭环。 |
| `production-live loop` | 一个有界场景已完成“观察 → 决策 → 操作 → 后置验证”，必要时含冷恢复。 |
| `complete` | 该能力域同时通过原生 AI 树、观测、动作、策略和验证五道门，并满足其场景矩阵。 |
| `blocked/deferred` | 有明确外部阻点或所有者暂缓；不能写成已完成。 |

命令 ACK、字段名存在、长期 `null`、单元测试通过、单个 fixture GREEN 都不能单独成为 `complete`。

## 更新节奏

- 每天在次日 00:00（Asia/Shanghai）正式收口前一自然日的 `daily/YYYY-MM-DD.md`；同日有多个里程碑时持续滚动更新。
- 前一日日报收口后立即创建新一天 `meetings/daily/YYYY-MM-DD.md` 早会；当天日报正式收口时逐项对照该早会，标明完成状态、
  未完成原因、是否顺延以及计划外成果。
- 每个有项目工作的 ISO 周持续更新 `weekly/YYYY-Www.md`，并在下周一 00:00（Asia/Shanghai）正式收口。
- 前一周周报收口后立即创建新一周 `meetings/weekly/YYYY-Www.md` 计划会；周报正式收口时逐项对照该周计划，不能只罗列成果。
- 日报和周报只交付文字，不要求也不默认制作视频；已有日级、周级或阶段性录像只作为可选历史素材，缺视频不影响报告收口。
- 每个自然月 27 日 00:00（Asia/Shanghai）更新 `monthly/YYYY-MM.md`，并配套一条覆盖截至当时全部真实能力的 show-off
  视频。英语是主叙事，简体中文是画面内副标题/字幕；中文字幕须按句意断句并受实际渲染宽度约束。缺成片或抽检未通过时，
  月报保持“未完成/重制中”。详细规范见 [`monthly/README.md`](monthly/README.md) 与 [`demos/README.md`](demos/README.md)。
- 报告必须区分“已完成”“正在进行”“为什么做”“证据/测试”“未闭合”“下一步”。
- live attempt 无论 GREEN 或 RED 都保留真实结论；不得通过修改预期、删去失败或把 harness 成功写成 capability 成功来美化状态。
- 宗教域继续遵守所有者暂缓：只允许战争中的圣战 OODA 和婚姻确实需要时的最小 faith 判定两项窄例外。
