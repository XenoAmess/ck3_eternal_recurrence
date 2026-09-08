# R354：宦官人贡原版事件变体

## 结论

R354 在自然推进第 4 个 Phase 2 source checkpoint 时，于
`date_raw=53231832` 停在原版 `tribute_mission.1002`。这是 CK3 1.19.0.6
源码定义的宦官人贡分支，不是产品故障：可见 authored option 精确投影为
native `0/2/3`，保存 scope 含 `eunuch_character` 而不含
`concubine_character`。

原合同只登记了 R136 的妃妾人贡分支 `0/1/3`，因此本轮按预期 fail closed，
没有选择任何按钮。修复只给同一原版事件补充第二套互斥的精确 scope/option
变体；两个分支仍固定选择 authored option 4 / native option 3（拒收），不修改
mod 内容，也不把 ACK 当业务状态。

## 原版定义

冻结文件：
`Crusader Kings III/game/events/dlc/tgp/tgp_tribute_mission_events.txt`。

- option A / native 0：两种人贡均可加入宫廷。
- option B / native 1：仅 `concubine_character` 存在时显示。
- option C / native 2：仅 `eunuch_character` 存在且可任命宫廷职位时显示。
- option D / native 3：拒收；按两类 scope 分别写入拒收标志。

R354 实机保存的 `secondary_recipient == eunuch_character == human_tribute ==
35197`，`actor == tributary_scope == 34162`，玩家/接收者为 `32904`；14 个
scope 名称、类型和别名关系均已登记为一个整体，不能与妃妾分支交叉拼接。

## 证据与验收

- RED 报告：
  `Z:\ck3_mod_rewrite\_runtime\p2r354endgamesource\report.json`
  - SHA-256：`F3BE673F06DC5B30B1A01FC7CAEB7E6E1CFE4B7F791E3555AE7D6FE9C47C3733`
  - `result=RED`
  - `event_instance_id=225`
  - `failed_checks` 仅为旧妃妾投影与本次宦官投影的差异
- cleanup：
  `Z:\ck3_mod_rewrite\_runtime\p2r354endgamesource\09_phase2_native_session_cleanup.json`
  - SHA-256：`5B1CE8D0548DA74FC3E48E81B1BCDF5864B87EBDC0B8A60263915C5B533BD3E1`
  - `result=GREEN`，PID `189412` 已回收
- 原始 R248 checkpoint 前后保持 `83,449,160` bytes，SHA-256 均为
  `C7E5CA119F4DB4D9BFE738859DD5E32DEC6F9F1F804D91F9B26ED5D256E219DA`。
- 专用两变体测试：normal `2/2`、`python -O` `2/2` GREEN。
- manager recovery 整组：normal `41/41`、`python -O` `41/41` GREEN
  （各含 1 个环境条件 skip）。
- tribute 专题：normal `2/2`、`python -O` `2/2` GREEN。

R354 只证明并修复该原版随机中断合同，未产出第 4 个 source checkpoint，
因此 canonical source coverage 仍为 `3/4`。
