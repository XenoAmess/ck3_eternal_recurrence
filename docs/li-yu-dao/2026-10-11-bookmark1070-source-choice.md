# bookmark.1070：共享源码选择合同

R59 已识别 CK3 1.20.0.4 的 `bookmark.1070`。原共享记录指定第三项，但要求全部 saved scopes 的固定形状，无法消费本场携带的继承作用域。现在仅这条 exact-build 事件的第三项按所选效果真正依赖的作用域检查：`root.capital_province`，没有具名 saved-scope 依赖。原始上下文保留，继承作用域身份不因此获得资格；其他事件及历史 .3 仍沿原检查。

本机已核原版 `events/bookmark_events.txt` SHA-256 为 `5A5CE08980D8C4FDA1DCF40EC26E12D8973C01286F4DA42A6D939776CFD50E03`。第三项创建一支250人军队（125征召兵、50弓箭手、50轻骑兵、25重骑兵），不增加另外两项中的宣称或好感修正。这是有界续行选择，没有宣称最优、无副作用或已观察到军队结果。

2026-10-11 09:26 UTC，相关 policy 单测模块 **49项通过**，包含新增9项。随后消费 R59 已入库的38,106字节公共 typed 回执作只读兼容回放：推荐 public option3/native2/rendered2，failed_checks为空。没有查询当前游戏或提交选项。原 `effect_preview_ready=false`、`semantic_decision_ready=false` 保留，增兵物质结果、I4及产品业务均未通过。

实际测试命令和只读回放见 [小证据目录](acceptance/2026-10-11-bookmark1070-policy/TEST-RESULT.actual.json) 与 [回放结果](acceptance/2026-10-11-bookmark1070-policy/R59-POLICY-REPLAY.actual.json)。原始现场见 [R59专题](2026-10-11-i4-r59-case10.md)。下一项是独立公共续行 case 绑定新的 fresh typed query 后选择一次并继续自然冷却期观测；原无选择 discovery case 保持不变。阶段继续75%估计 / NOT_GREEN。
