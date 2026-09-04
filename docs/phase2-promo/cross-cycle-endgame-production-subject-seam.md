# Cross-cycle endgame production subject seam

基线：`714be35`（包含 `806e9c7` 之后的 canonical 增量）。状态：
`static-ready-live-pending`；本包未启动 CK3。

## 已闭合的代码入口

`tools/zg361_phase2_cross_cycle_endgame_production_subject.py` 新增一个严格、只读的
product subject checkpoint binder。它只接受下列状态：

- 父 checkpoint 是 formal cell 已保存的真实 owner-facing `zg361we.361` bytes/SHA；
- CK3 的普通单人 `Switch Character` UI 已把 `#361` 保存 scope 中的 exact subject 变为
  played character；
- 日期未推进、地图暂停、没有 active event；
- 新 checkpoint 的真实文件、bytes、SHA-256、parent result SHA、save lineage、owner、
  subject 和 date 全部匹配；
- product-only，且 `fixture_used=false`、`typed_event_fixture_used=false`、
  `console_used=false`、`generic_character_rebind_used=false`。

binder 不执行换角、不选 event option、不写变量，也不把 checkpoint receipt 当成业务
GREEN；它只把已发生且已保存的 production UI 结果接入 formal cell。

formal cell 的 production 分支随后在同一 played-subject paused frame 顺序调用两个现有
read-only provider：

1. Workforce collective provider 必须观察同一 AL owner/subject/cycle/case、M360 choice 3、
   route-C debt due at cycle+1，以及 ready/consumed 的三周期 M361 charter；
2. AI-owned B1 provider 必须独立观察同一 owner/subject，证明 owner alive、AI、celestial、
   authorized，subject 是其 direct subject，且 B1 cycle 等于 Workforce terminal cycle。

两项 provider 都通过后 formal cell 才能 GREEN。UI 动作 ACK、checkpoint save ACK、事件
可见性或 caller 自报 `owner_is_ai` 均不能替代它们。旧 acceptance-only typed fixture 分支
仍保留用于已有回归，但明确不算 production evidence。

## 没有修改的产品语义

本包没有修改任何 mod effect/event，因此：

- `#356` 仍固定从 AL state 1 起步；
- M357–359 仍须来自真实 B1/B2 receipts；
- `#360` route C 仍建立下一周期 debt 并把 AL 4→5；
- `#361` 仍要求第三周期 history/evidence，且仍只对 human owner 显示；
- 所有玩家/AI gating 保持原状。

没有新增 effect 文件，也没有接触 B4 pre-B WAIT 或 frozen B3 r5 artifact。

## 仍需的 live/runner 依赖

formal runner 还缺一个已实机证明的 managed ordinary-UI primitive：在真实第三周期
`#361` 选择产品 option 后，通过 CK3 单人 UI 把控制权从 owner 切到 exact subject，确认
owner 已成为 AI、日期不变、scope 未丢失，然后保存 product-only subject checkpoint。

这次只提供该 checkpoint 的严格消费端；没有 live UI receipt 时不得构造 receipt 或宣称
production GREEN。下一次 CK3 串行验收应保存：

- owner-visible `#361` parent checkpoint bytes/SHA；
- ordinary UI switch 前后 screenshot/snapshot、日期与 exact CharacterID；
- played-subject child checkpoint bytes/SHA/parent SHA/save lineage；
- 同一 paused revision 的 Workforce response 与 AI-owned B1 response；
- formal cell 的最终 sidecar。

若普通 UI 在 exact build 不可稳定自动化，当前 seam 保持 `live-pending`；不得回退到
fixture、`set_player_character`、console 或 public generic rebind。
