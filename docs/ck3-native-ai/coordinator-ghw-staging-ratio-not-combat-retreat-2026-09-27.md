# 普通战争协调器的一个比例门：大圣战集结，不是战中撤退

日期：2026-09-27。只读本机 CK3 1.19.0.6 磁盘文件；EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；
`game/common/defines/ai/00_ai.txt` SHA-256
`C78F9CD8DF9938CC9F38E817BCB6E32CD13720B5BD9DE077B85E3E1C6F030293`。
没有启动、附加或修改 CK3。本包只裁决 coordinator tick 中 `0x1855359 → 0x18554F0` 的一个
“兵力比例+计时”可疑入口；不否认别处可能有战中 AI 自愿撤退 policy。

## 调用、阈值与写回

| 精确 RVA | 可确认事实 |
| --- | --- |
| `0x18552F5/0x1855305/0x1855359` | 同一 `0x18550D0` tick 先调用 `0x1859FF0` stack 调整，再按前置标志调用 `0x185A780` 目标重算，之后调用 `0x18554F0`。前两者已有[计数器](war-film-target-countdowns-2026-09-23.md)和[目标选择](war-film-target-selection-2026-09-23.md)专题。 |
| `0x18554FF..0x185550A` | 被调函数要求 coordinator `+0x68 & 0x44 == 0x44`，否则返回；这两个 bit 的正式枚举名未恢复。 |
| `0x1855510..0x1855571` | `+0xB0` / `+0xC0` 有递减、负数哨兵和到期分支。不能仅凭计时器把它叫作“撤退冷却”。 |
| `0x18555D3 → 0x18744A0`、`0x18555E1/0x1855682` | 按 stack/subunit 累计 helper 给出的 qword 量，形成总量 `r14` 与符合后续位置/身份条件的子集量 `rsi`。`0x18744A0` 读 CUnit、解析 CArmy 并调用 `0x226F270`；本包没有给这个 qword 完整的兵力/战力 ABI 名称。 |
| `0x18556B8..0x18557A4` | 以 `max(r14,100000)` 作分母，算 `rsi/denominator` 的 Q100000 比值；`0x18557A4` 与 runtime `0x570DF48` 比较，`<=` 不改变状态。 |
| `0x18557B2` | 比值**严格大于**该阈值时，写 coordinator `+0xC0=-1`；窗口中没有向 CCombat 发撤退、构造 kind-2 移动或提交命令的 direct call。 |

`0x18B5DE3` 把同一 runtime slot `0x570DF48` 与 `0x18B5DF1` 的原版名字串注册，
名字是 `MIN_POWER_ARRIVED_TO_STOP_STAGING_FOR_GREAT_HOLY_WAR`。
原版 define 文件第 1799–1803 行声明值 **0.9**，注释说明达到集结省的最低己方总 power 比例才停止集结。
因此这里的 `0.9` 是**大圣战集结门**；不能读成“战损 90% 时撤退”或“战斗胜率阈值”。
数值比较本身是 `ratio > 0.9`，等于 `0.9` 不写 `+0xC0=-1`。
原版注释有助于命名意图，但子集量 `rsi` 的全部业务过滤、bit `0x44`、计时器生命周期仍需另证。

这给出有界否定：**在检查过的 `0x18554F0` 分支，没有发现基于当前 Combat 战损的主动撤退派令。**
不能从这一个分支推断普通战争协调器、间接调用或全游戏不存在这种策略。
现有 [0.45 撤退复合门](combat-prediction.md#撤退复合门)已确认属于接战前 unit-stack 战略退让/重派，
同样不能当作 active CCombat 中第 15 日后的自愿撤退。

## 复核与后续调查边界

[只读 verifier](../../ck3_autonomous_player/native_bridge/research/verify_coordinator_ghw_staging_gate_static.py)
检查整份 EXE/define 的 SHA、16 处确切指令、runtime slot 和原版名字串：

```text
<verified-python> ck3_autonomous_player/native_bridge/research/verify_coordinator_ghw_staging_gate_static.py --exe <exact-ck3.exe> --ai-defines <exact-00_ai.txt>
```

本机验证通过。反汇编原文保存在仓库外
`D:/workspace/ck3_native_war_ai_promo_work/ordinary-war-retreat-static-20260927/`，
其中 `coordinator-tick.txt` SHA-256 `e6637e2876044de615238db87fa7b6119c9f33a441c89571d59bc9ce401c0c4b`，
`coordinator-subtick-tail.txt` SHA-256 `a2f6b0f04debe0ee7506dd37ca3ebdc9f3ed6b1bc1aa1fa023c2805583c00b29`，
`threshold-registration.txt` SHA-256 `cc03f8b483291077a2ff02264da418dcb75740fd8eff3b45c309d7f51bd0a372`。
这不是一次自然 AI 撤退的运行证据。

下一最小静态对象不再重复此集结分支、已知接战前 `0.45` 门或 raid 清理。
应从普通战争 AI 在 **active CCombat** 中的 CUnit/CArmy 指针出发，寻找同时读取战斗结果预测或损耗、
测试时机、调用通用移动/owner-subset 撤退的同一 producer；若 direct-call census 没找到，继续审计
move-command vtable / dispatcher 的间接生产者。找到后需同一 CombatID、Army full ID、日期的自然实机派令证明。
