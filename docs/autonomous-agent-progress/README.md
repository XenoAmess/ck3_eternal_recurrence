# CK3 自动游玩智能体进度中心

本目录是自动游玩智能体的统一进度入口，回答四个问题：终极目标是什么、现在真正会什么、还缺什么、最近做了什么。
它不替代 exact-build 逆向证据、ABI 合同或实机 artifact；详细证据仍保存在
[`docs/ck3-native-ai/`](../ck3-native-ai/README.md) 与
[`docs/testing-workflow.md`](../testing-workflow.md)。

当前 headline（2026-08-31）：固定 production seed 的 G1 与随后第二个完整寿命均已 GREEN。第二寿命在无人接管的
production 长跑中自然触发 one-life terminal，完成匹配结算，再经
`death-terminal → start-next-episode → exact seed reload → 新 episode gameplay → durable checkpoint`
进入第三个 episode。该结果完成了同一冻结 seed 的 G2 全寿命重复门；它仍不代表不同 ruler/政府/DLC、普通 campaign
跨继承或全游戏自治已经完成。

## 导航

- [终极目标、当前能力与完整路线图](goal-and-roadmap.md)
- [2026-W35 一代人自治 blocker / 能力债账本](one-generation-blocker-ledger.md)
- [G1 一代人全寿命 production 续跑交接（2026-08-28）](g1-production-handoff-2026-08-28.md)
- [一代人 20-turn production canary 交接（历史）](one-generation-canary-handoff.md)
- [2026-09-02 休假交接总览](../handover/2026-09-02-shift-handoff.md)
- [2026-09-02 G2 与 open_kaishek 交接](../handover/2026-09-02-g2-open-kaishek-handoff.md)
- [2026-09-02 交接审计](../handover/audit-2026-09-02.md)
- [日/周计划会制度与模板](meetings/README.md)
- [2026-08-30 早会（补录）](meetings/daily/2026-08-30.md)
- [2026-08-29 早会（补录）](meetings/daily/2026-08-29.md)
- [2026-08-28 早会](meetings/daily/2026-08-28.md)
- [2026-08-27 早会（补录）](meetings/daily/2026-08-27.md)
- [2026-W35 周计划会（补录）](meetings/weekly/2026-W35.md)
- [2026-08-30 日报（滚动）](daily/2026-08-30.md)
- [2026-08-31 日报（滚动）](daily/2026-08-31.md)
- [2026-08-29 日报](daily/2026-08-29.md)
- [2026-08-28 日报](daily/2026-08-28.md)
- [2026-08-27 日报](daily/2026-08-27.md)
- [2026-W35 周报](weekly/2026-W35.md)
- [2026-W36 周报（滚动）](weekly/2026-W36.md)
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

- 执行过程中必须间歇性反思“是否还有事情应该同时做”。触发点包括：任务开始、任一工作包完成或阻塞、进入等待、CK3 排他槽
  取得/释放、优先级或计划改变。每次重新盘点 P0/P1、伴随同步、测试/CI、文档证据和后续门禁准备，把所有不依赖当前阻点、
  且文件和进程资源不冲突的工作及时并行铺开；只有 CK3 启动环节串行，CK3 运行时其他非 CK3 工作继续。
- 反思结果必须服务真实交付，不为填满并发制造工作：不得扩张未要求的功能、重复已有结论、重复运行没有新观察面的验收，或让
  低优先级工作抢占高优先级关键路径。并发工作包发生实质新增、暂停或完成时，在当日日报记录原因、状态和下一门槛。
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
