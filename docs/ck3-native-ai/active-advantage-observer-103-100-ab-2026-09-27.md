# 优势分项观测 103/100 同源 A/B：原数值复现，诊断仍不可用

103 与 100 均从第 12 日原版 checkpoint SHA-256 `E6155C9C127EC3D1D758468653E8ABC3458A96B50EA053E303FDCCAD18C0B731` 恢复，并推进到相同 CombatID `16777218` 的下一原生日更；保存回执 SHA-256 `A68C4D38CC14B11FCB4078E8D9074C9EE5793B0EF20674199327E6D0A983B415`。两次 preflight 实测原版 EXE SHA-256 同为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，DLL 不同：100 是 counter observer，103 增加 advantage observer。本页只用两个已结束 attempt 的只读文件，不重新启动 CK3。

原始 103 `c103-trace-finish.json` SHA-256 `0F40394F58FFFDC2C35FF812893729E83E1997700C4E964530446E6E90DBA938`；100 `c100-trace-finish.json` SHA-256 `644580703FE18769B081CCEBCC96B473BF459E4489835777117D6B070014FBFC`。可运行[只读 A/B 比较器](../../ck3_autonomous_player/tools/project_advantage_components_ab_103_100.py)，传入两个 attempt 目录及 `--expected` [冻结结果](../../ck3_autonomous_player/native_bridge/research/fixtures/advantage_components_ab_103_100.json)。比较器同时调用生产合同 `normalize_runtime_advantage_components_v1`，检查原始 SHA、checkpoint/EXE 身份、一日控制门、双方 counter 向量和已发生的出伤；不信任手抄摘要。`--expected` 仅核验投影字节，`--check` 才要求**所有**门槛 GREEN；本案的 `--check` 应以非零退出。

| 项目 | 100 与 103 核验结果 |
| --- | --- |
| 主 trace | 两者 `failure_flags=0`、各七条 record；before date raw `53146512`，after `53146536`，同一 CombatID。它只说明既有主 trace 的受管边界。 |
| 两侧动态反制 | 完整 13 类向量逐值相等；side0 context `125000`，只有 class8 retention `10000`，其余 `100000`；side1 context `100000`，class0/1 为 `10000`，其余 `100000`。 |
| 反制后攻击 / 最终出伤 | side0/side1 postcounter raw `7086468150 / 1367059376`；outgoing raw `116572401 / 63568260`，两次逐值相等。 |
| 103 优势行内部 | base `-300000`；side0 `roll 7×100000 + commander 3500000 + aggregator 0 = 4200000`；side1 `roll 8×100000 + commander 4200000 + aggregator 0 = 5000000`；resolved `-300000 + 4200000 - 5000000 = -1100000`，也与主 trace 缓存字段一致。 |
| 103 诊断准入 | `materializations[0].complete=true`，但 `advantage_components.available=false`、`failure_flags=64`。标准化结果 `diagnostic_observation_complete=false`、`forecast_usable=false`。100 不含此可选诊断。 |

`64` 在当前[观测器源码](../../ck3_autonomous_player/native_bridge/src/combat_advantage_components_observer_v1.cpp)的 `AggregatorHook` 对应四项共用的失败位：原调用返回指针非空、caller 恰为 `0x2307EBA`、side index 匹配、该 side 之前恰有一次 helper call。该位无法区分究竟是哪一项失败，也无法知道何时发生；两条已记录 side 恰各有两次 helper 调用，并不抵消这个额外失败证据。不能因为一行整数等式自洽就将该观测器标为 GREEN，更不能将其用作下一日优势输入、原生优势来源全闭合或整场胜率校准。A/B 仅说明增加 103 观测器后，**此一次**可比较的既有 counter/postcounter/outgoing 数值未改变，不能证明所有场景下无扰动。

103 的 `input-freeze.json` 中 `exe_sha256` 写成 `2D00FF3103EF...`，与该 attempt preflight 测得的 `2D00FF3101EF...` 不符；这是保留在原始 attempt 的元数据缺陷。比较器同时冻结两份 input-freeze 和 preflight 字节，明确输出 `matches_measured_preflight=false`；门槛分列为 `raw_ab_comparison=GREEN`、`freeze_manifest_provenance=RED`、`overall=RED`。本页依据实测 preflight 与 bridge hello 判断 EXE 身份，但**不声称整体验收 GREEN**，也不覆盖或悄悄修正原文件。

下一轮如继续调试，应保持同源存档、只读记录 `AggregatorHook` 四项各自的失败位与调用序号/return RVA，并做另一次正常日、事件日和增援日的成对验证。修复前 103 的优势数值只能作**失败诊断中的内部一致性线索**；动态优势来源与跨日转移仍未验证。该边界与[优势观测器合同](active-combat-original-advantage-observer-2026-09-27.md)一致。
