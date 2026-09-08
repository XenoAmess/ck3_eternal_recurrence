# R342 大圣战解锁通知中断（2026-09-08）

## 实机结果

- R342 从冻结 R248 候选存档推进 cross-cycle/endgame source 路径；输入为
  `83,449,160` bytes / SHA-256
  `C7E5CA119F4DB4D9BFE738859DD5E32DEC6F9F1F804D91F9B26ED5D256E219DA`。
- R341 新增的 `birth.1010` secret-birth scope variant 已在重放中通过，时间线继续经过
  portfolio、credit-project 与 P3，随后在 `date_raw=53223552`、event instance
  `346` 暂停于此前未知的原版 `great_holy_war.0011`。
- 未知事件在选择前 RED；受管 cleanup GREEN、failed checks 为空、最终 CK3 进程槽清空，
  原始 R248 存档哈希未变。report / cleanup SHA-256 分别为
  `D6ECB1FC51396B30555F298FA1BC891EE7D4806F0ABFACEF54C41ACDAFF9207D` / 
  `257D0DAB76C6347A65D12DBBB192D4855033E5C1450B090927070092C771F938`。

## 精确原版合同

CK3 1.19.0.6 原版
`events/religion_events/great_holy_war_events.txt` SHA-256 为
`E431A0E2FDFF5E49FB572B7184DE9B498F982B95AED875334AD1432D0F88CBA7`。
hidden `great_holy_war.0010` 先设置 religion 的 `variable_ghw_unlocked`，再向每个玩家投递
`.0011` flavor notice；因此解锁已在通知窗口之前完成，不受玩家按钮影响。

R342 的完整 MCP/native 帧为：

- root/player `32904`；
- `awakening_faith` 为 opaque `faith` scope；
- `ghw_first_sponsor=background_temple_scope=32201`，两者均为非玩家 character；
- snapshot authored option count 为 `5`，唯一 visible/enabled 按钮映射 authored option
  `4` / native index `3`。

原版 `.0011` 五个 option 都没有 gameplay effect，事件 after 也只有
`custom_tooltip`。合同只绑定上述三个 scope 的名称、类型、sponsor alias、root 排除、完整
option projection，并确认 native 3。它不查询 faith identity、doctrine、tenet、fervor，
也不建立通用宗教策略；范围严格限制在项目规则允许的“战争中的圣战”窄例外和本次已实证
阻塞事件。

## 验证与边界

- holy-war 专测 normal / `-O` 各 `1/1` GREEN；
- manager recovery interrupts normal / `-O` 各 `40/40` GREEN；
- promotion source checkpoint runner normal / `-O` 各 `83/83` GREEN；
- `py_compile` GREEN；
- 修复 commit `c029cd0a76781194553930d13865a263acbcda14` 已普通 fast-forward
  push 到 `origin/master`，未 merge、未 force-push。

本轮只解除验收线上的原版通知中断，不增加业务 scene、definition、stage 或宣传素材计数；
canonical source registry 仍为 `3/4`，R343 继续目标
`capture_cross_cycle_endgame`。
