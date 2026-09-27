# WAR31 保存层威望与累计声望分账（2026-09-28）

[单次投降实机记录](war31-r0197-one-shot-live-result-2026-09-28.md)先前只对比了 `prestige.currency`，因此 Landolf 的当前威望净变化是 0，却没有回答 `prestige.accumulated`（累计声望／fame 进度）是否变化。新[只读投影器](../../ck3_autonomous_player/tools/project_war31_fame_delta.py)固定历史 material report SHA-256 `84154554437CE96FB751DC6DB23E65847CA974CD92917A2FCB32B12C3FC11634`，再次校验两份 Rakaly 文本 SHA，按已核对的人物块行号分别读取 `currency` 和 `accumulated`，并要求 `currency` 与原报告逐字值一致。

| 人物、原版保存字段 | 1074.11.17 | 1074.11.23 | 保存层净变化 |
| --- | ---: | ---: | ---: |
| Robert 29829 `prestige.currency` 当前威望 | 2526.55450 | 2496.55450 | **−30** |
| Robert 29829 `prestige.accumulated` 累计声望 | 5815.61947 | 5815.61947 | 0 |
| Landolf 30097 `prestige.currency` 当前威望 | 856.20500 | 856.20500 | 0 |
| Landolf 30097 `prestige.accumulated` 累计声望 | 1115.20500 | 1145.20500 | **+30** |

全部计算用保存值乘以 `100000` 后的整数完成，未用浮点近似。外置原始结果 `D:/ck3-research-artifacts/war31-live-20260927/attempt-05/fame-accumulated-delta-01.json` SHA-256 **`980C63AD32C6B6A875DC5783499738A5429E565C15964CFE8F5A478162481DE2`**；收紧人物块终止检查后的独立 `fame-accumulated-delta-02.json` 逐字节同 SHA。原始 R0197 与战后 save SHA 分别是 `1AF4055F...CC8` 和 `A29A41B2...EDB5`，完整值在报告中。

结论是**两份相隔六日的精确保存中的净变化**。本投影没有在动作即时原生帧读取 Landolf 的累计声望，也没有排除六天内其他写者；所以不能把 `+30` 严格归因到投降那一条指令、推广到所有 de-jure CB，或称为 h2743 当前投降条款。决策模型若估计退战代价，必须将可花费的当前威望和累计声望分别记账，不得用其中一项净零覆盖另一项。

验证：真实双 save SHA 已由历史 material report 的 Rakaly 复现核验，本投影再读两份对应文本 SHA 与人物块；`test_project_war31_fame_delta.py` 普通及 `-O` 各 `3 passed`，覆盖分账、错人物定位与缺失累计字段拒绝。合成单测没有代替实机报告。
