# 单场战分脚本门：原生 `>=` 分支已定位，败方实例值仍待绑定

日期：2026-09-27。继续[败方 effect 战分门](normal-result-loser-effect-war-score-gate-2026-09-27.md)的有界只读研究。
目标 CK3 1.19.0.6 EXE SHA-256 为
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；
原版 `game/common/on_action/combat_on_actions.txt` SHA-256 为
`B35D696F472E801BB332D7204AA46008349E8AFBFDB38985C781EB099BBFB233`。
没有启动、附加 CK3，或执行脚本 effect。

## 本次真正闭合的原生比较边

| RVA / 地址点 | 已确认的数据流 |
| --- | --- |
| `0x53C371 → 0x437A068` | 注册原生名字串 `warscore_value`；既有专题已绑定 `CTriggerEntry<CCombatWarscoreTrigger>`。 |
| `0x284F631 → 0x437D490` | factory `0x284F5F0` 给该 trigger 实例安装 vtable；表 `+0xC8` 指向 `0x99F920` 通用比较函数，表 `+0x100` 指向 `0x284C7A0` 战分 accessor。 |
| `0x99FA6D` | 通用比较函数经虚表 `+0x100` 取得左操作数 qword；该 trigger 的 accessor 在 `0x284C830` 读 `CCombatResultData+0x40`，即已证的单场 Q100000 幅度。 |
| `0x99FA92/0x99FAA9` | 将实例 `+0x10` 的右侧表达式交给 `0x9698B0` 求值；返回的是运行时右操作数，不是 EXE 内硬编码的 `15`。右侧也可能是表达式，不能把 `+0x10` 无条件命名成裸常数。 |
| `0x99FAAE/0x99FAB1` | 从实例 `+0x50` 读取操作码；等于 `0x3CB` 时进入 `0x99FAED`。`0x99FB81/0x99FBA5` 的装载路径确实从输入 token 读操作码并写入同一 `+0x50`。 |
| `0x99FAED/0x99FAF0/0x99FAF8` | 读取右侧 qword，比较 `lhs_raw` 与 `rhs_raw`，以 signed `setge` 返回；**等于也通过**。这只证明操作码为 `0x3CB` 时的通用原生语义。 |

原版败方脚本的字面条件仍为 `combat = { warscore_value >= 15 }`。
按已证字段的 Q100000 尺度，**预期**右侧为 `1,500,000`；但本包不能把这个预期写成
“该 loaded node 的原始整数已在 EXE 中找到”。EXE 只包含通用构造器/比较器，脚本文本由游戏装载后
实例化 trigger；操作码 `+0x50` 和右侧表达式求值均来自**运行时节点**。
磁盘源脚本 SHA 不证明实际 VFS 未被 mod 覆盖，也不提供该败方节点的地址、`+0x50` 原值、
右操作数求值结果或其实际分支返回。故本轮仍不能静态证明
`on_combat_end_loser` 的实例恰走 `0x3CB` 且 RHS 恰为 `1,500,000`，更不能声称 `-50` 已写回。

## 复核工具与下一次同场实机门

[exact-build verifier](../../ck3_autonomous_player/native_bridge/research/verify_warscore_trigger_generic_compare_static.py)
核对两份源 SHA、脚本原文、13 处精确指令、注册名字及两个 vtable slot；
成功仍显式输出 `loaded_loser_node_opcode_verified=false`、`loaded_loser_node_rhs_raw_verified=false`。

```text
<verified-python> ck3_autonomous_player/native_bridge/research/verify_warscore_trigger_generic_compare_static.py --exe <exact-ck3.exe> --on-action <exact-combat_on_actions.txt>
```

本机验证通过。仓库外反汇编原文在
`D:/workspace/ck3_native_war_ai_promo_work/normal-result-comparator-static-20260927/`：
`trigger-constructor.txt` SHA-256 `4c00a96336d8437a530c00b515fcc3e38ce55f460d53448933ef59a3a59d113c`，
`trigger-registration.txt` SHA-256 `bd20496a2d0e42914796edce3ce7ec0ee7e91b6d8eaf7080aa53ae23c6ba83a8`，
`trigger-evaluator.txt` SHA-256 `535097562bf558e31c66f631e045130650ac784f31cc24ff00963d39930e6de0`，
`trigger-generic-eval.txt` SHA-256 `476883184dd3126cde94ae28ba967c29dbf04ebc7ef8dcc40af4db82b732d112`。

下一次由唯一受管 CK3 owner 在**同一自然 normal_result** 中被动取证：先冻结 EXE/DLL、
VFS 中实际载入的 `combat_on_actions.txt` 来源与 bytes、CombatID/WarID/两方身份及 paused date；
在 `0x230B0EE` 败方 effect dispatch 内，定向记录 `0x99F920` 的 trigger 指针/vtable、
实例 `+0x50` 操作码、`0x99FA6D` accessor 返回的 lhs qword、`0x9698B0` 给出的 rhs qword、
`0x99FAF8` 返回 bool，再与同场 result `+0x40` 和后续 effect 回读关联。
必须用调用上下文或稳定节点身份证明采到的是败方该脚本条件，不能把别的 `warscore_value` 使用者拼进来。
探针只读、容量受限，不主动调用 evaluator/mutator；若身份、VFS、时间或分支不一致，保持 RED。
