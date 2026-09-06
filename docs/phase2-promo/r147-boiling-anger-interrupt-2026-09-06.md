# R147 原版“怒火中烧”响应中断（2026-09-06）

## 实机结果

- frozen source：`dfffe66004a18199ad7fb8140e7d54c704277975`；源代码 ZIP SHA-256：
  `996099565b37f4fa274ea48d7bdff1ffb01d4781c5bf9e1f089109baea2a8c6d`。
- no-launch preflight GREEN：3,187 个 tracked files 与 ZIP 完全等价；R130 的 1,031 文件产品投影及四个关键
  B2 effect 继续逐字节 GREEN。
- CK3 只启动一次，PID `102676`；默认 5 速，玩家 CharacterID `32904`，fixture 生存保护只安装一次。
- B1 仍 active 的推进途中，runner 在 `date_raw=53148288` 暂停于新原版事件 `stress_threshold.2202`，
  按未知事件 fail-closed，因此尚未到达 clean review boundary，也没有执行 R147 的同日 GUI 激活脉冲。
- `manager-cycle-recovery.json` SHA-256：
  `0b943d913fc51dc74b6eb6a379a1aa69da58073d72d9096837cbdb9362cec283`；
  `runner-report.json` SHA-256：
  `0270ffa7d4ee397e8eba9ad6d1489794aa8e26c9b273c6ce492ab87ce6216ecf`。

## 精确原版合同

CK3 1.19.0.6 原版 `events/stress_events/stress_threshold_events.txt` 证明该事件是另一角色精神崩溃后向
被斥责者发出的响应事件。当前实机帧中：

- root / `character_to_yell_at` 都是玩家 `32904`；`stress_character` 是非玩家 `26849`；
- 原版共两个互斥选项，但当前不存在 `rival` scope，因此 option 0 隐藏；唯一可见按钮映射 native option 1；
- immediate 在不存在 `rival` 时无效果，native option 1 只执行 `add_stress = medium_stress_loss`，不改产品状态。

runner 合同据此绑定 exact event key、两个 typed character scope、完整一-of-二可见按钮形状及 native option 1。
新增专项测试同时证明 option index 或 scope 漂移会 RED。该合同只覆盖 R147 已观测的精确帧，不是 namespace-wide
自动点击规则。

玩法状态、事件身份、scope 和按钮都来自 MCP/native；顶层 OCR/image 仅用于非玩法 legal-consent/front-end gate，
`coordinates_used=false`。本轮是验收线新原版中断，不是产品 RED，不改变逐号 readiness。
