# 现役战斗：连续推进帧与重载帧不可直接串算

同一原版 CK3 1.19.0.6 战局的第 12 日、CombatID `16777218`、`date_raw=53146512`、主战 day 8，有两组可重复的暂停观察：[098](active-counter-output-trace-attempt-098-2026-09-27.md)、[099](active-counter-output-day12-checkpoint-attempt-099-2026-09-27.md)、[106](active-advantage-reinforcement-attempt-106-2026-09-27.md)分别从第 11 日原存档连续推进一天，得到同一组关键 battle-control 字段；100 与 104 则独立载入 099 保存的第 12 日存档 SHA-256 `E6155C9C127EC3D1D758468653E8ABC3458A96B50EA053E303FDCCAD18C0B731`，得到另一组相同字段。两组的 EXE SHA-256 均为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。这是一项**观察到的条件差异**；单靠这些回包不能把原因专断归于存档序列化、载入回调或某个 modifier。

| 同一第 12 日字段 | 连续推进：099 / 106 | 重载后：100 / 104 |
| --- | ---: | ---: |
| 基础优势 `base_advantage_raw`（Q100000） | `-300000` | `-300000` |
| 已解析优势 `resolved_advantage_raw`（Q100000） | `-1100000` | `-600000` |
| 攻击侧 `side_strength_raw` | `125474` | `120954` |
| 防守侧 `side_strength_raw` | `36020` | `24640` |
| 原生反制输入职业兵条目数，攻击/防守 | `24/14` | `24/14` |

四份回包中的 `active_counter_inputs_v1` 两侧条目逐项相同；CombatID、日期、phase day、基础优势和战宽也相同。区别集中在 battle-control 的派生有效属性：攻击侧 24 条职业兵中，17 条 `effective_damage_raw`、24 条 `effective_toughness_raw`、22 条 `entry_strength_raw` 有差异；防守侧 14 条中分别有 12、14、13 条差异，另有 3 条 `effective_siege_raw` 差异。两侧非兵团字段除 `side_strength_raw` 外相同。由此可知，**同样的兵团名单和克制 class 输入并不足以保证重载后的有效攻击、坚韧和优势与连续战况相同**。

[只读哈希绑定投影](../../ck3_autonomous_player/native_bridge/research/fixtures/battle_reload_frame_divergence_099_100_104_106.json)由[对照脚本](../../ck3_autonomous_player/tools/project_battle_reload_frame_divergence.py)验证 099 的 save 字节与回执、098/106 和 100/104 各自的同源原生输出、四份 battle-control 原始回包的 SHA。它要求组内关键字段全等、组间上述差异精确重现。连续帧对照的 099/106 回包 SHA-256 分别是 `FFE286DC1422A54A330A53F29BD4541512F9E75A4C0DE112584CFC934F2022B6`、`6D024AD861F07DF056D2B7118E2C0607B5E52A3CC7F1DC6F6AC858C86919198E`；重载组 100/104 分别是 `428B64DEA74202B5C5A2835E3079964C2227EC83946B3BB7A666E6D3CAB364EF`、`1B6C78931B72C749F71E948477E568012BF9B40475D4A6105E94C9D05DE71D0A`。投影读取原始外置 attempt，不启动 CK3。

对研究和智能体的直接约束是：每次决策只使用**当前实际运行帧**重新查询的优势、有效属性和克制输入；不能把连续推进第 12 日的 `-11` 优势与重载第 12 日的兵团属性拼成一组。100/104 的同源重载 A/B 与 098/106 的同源连续 A/B 各自有效，但把前一天的连续结果和下一天的重载输入直接当作无缝原版日更链，会跨过这个未闭合的边界。要研究原因，需在同一精确存档上分别捕捉保存前、载入完成后、首个 manager refresh 前/后以及伤害读取时的优势缓存与有效属性来源；此前保持 `next_day_non_roll_advantage_sources` 和动态转移缺域，不将本差值塞进预测公式。

复验命令：

```text
tools\.venv\Scripts\python.exe ck3_autonomous_player\tools\project_battle_reload_frame_divergence.py --attempt-098 D:\workspace\ck3_native_war_ai_promo_work\episode01-active-counter-output-attempt-098 --attempt-099 D:\workspace\ck3_native_war_ai_promo_work\episode01-day12-checkpoint-attempt-099 --attempt-100 D:\workspace\ck3_native_war_ai_promo_work\episode01-active-counter-output-attempt-100 --attempt-104 D:\workspace\ck3_native_war_ai_promo_work\episode01-active-advantage-components-attempt-104 --attempt-106 D:\workspace\ck3_native_war_ai_promo_work\episode01-active-advantage-reinforcement-attempt-106 --expected ck3_autonomous_player\native_bridge\research\fixtures\battle_reload_frame_divergence_099_100_104_106.json --check
```
