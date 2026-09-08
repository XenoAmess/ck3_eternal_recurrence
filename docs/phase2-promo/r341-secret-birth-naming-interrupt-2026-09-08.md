# R341 隐秘出生命名中断（2026-09-08）

## 实机结果

- R341 从冻结的 R248 候选存档继续推进 cross-cycle/endgame source 路径；输入存档为
  `83,449,160` bytes，SHA-256
  `C7E5CA119F4DB4D9BFE738859DD5E32DEC6F9F1F804D91F9B26ED5D256E219DA`。
- CK3 1.19.0.6 在 `date_raw=53213208` 暂停于 `birth.1010`，event instance
  `209`，root/player `32904`，只投影一个 enabled native option `0`。
- 旧合同在任何选择前以 `known-interrupt-contract-drift` RED；
  `selection_attempted=false`。受管 cleanup 为 GREEN、failed checks 为空、最终
  CK3 进程槽清空；原始 R248 存档哈希保持不变。
- report / cleanup SHA-256 分别为
  `559FF16B912FB4BD99914466E632306881E5C89C45E266FF668D3484A40A142E` / 
  `52C5388C2E95A8A8A856308FCB348921641F3E7EF5D3BED247FB1EEE09BC8F22`。

## 精确原版合同

R341 的完整 saved-scope 帧是：

- `child=16842384`、`real_father=36350`、`mother=37337`；
- `father` 是 type `character` 但 typed identity unavailable 的 weak scope；
- `is_bastard`、`is_child_of_concubine`、`matrilineal` 为三个 boolean scope；
- `new_secret` 为 `secret`；没有 `spouse_of_mother`。

CK3 1.19.0.6 原版 `common/scripted_effects/00_pregnancy_effects.txt` 的
`pregnancy_maintainance_effect` 可在 disputed-heritage 或
unmarried-illegitimate 路径保存 `new_secret`，随后
`events/birth_events.txt` 触发 `birth.1010`。该事件的 immediate 只有在母亲存在
primary spouse，或新生儿存在 assumed father 时才建立 `spouse_of_mother`；当前帧两者
都不可解析，因此“有 `new_secret`、无 spouse scope、father identity unavailable”是
源码可达的精确变体。事件唯一 option 没有 gameplay effect，仅关闭命名通知；runner
仍不操作命名 widget。

实现只新增这一组八-scope `scope_variants`，继续绑定 event/root/date window、三名可解析
角色的互异关系、不可解析 father、`new_secret: secret` 和唯一 native option 0。缺少
`new_secret`、混入 `spouse_of_mother`、father 意外变成可解析角色或 secret 类型漂移都会
fail-closed。没有第三次 occurrence 的实机证据，因此 `max_occurrences` 保持 `2`。

## 验证与边界

- manager recovery interrupts：normal / `-O` 各 `40/40` GREEN；
- promotion source checkpoint runner：normal / `-O` 各 `83/83` GREEN；
- 只读并行源码审计确认旧婚配帧和新 secret 帧均通过，未启动第二个 CK3；
- 修复 commit `231a321be656216a81302078baf12aa5e628f5f2` 已普通 fast-forward
  push 到 `origin/master`，未 merge、未 force-push。

本轮只闭合验收线上已出现的原版通知变体，不增加业务 scene、definition、stage 或
宣传素材计数。canonical source registry 仍为 `3/4`，下一轮继续目标
`capture_cross_cycle_endgame`。
