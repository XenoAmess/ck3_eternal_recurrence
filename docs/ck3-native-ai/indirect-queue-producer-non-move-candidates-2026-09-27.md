# 从战中撤退执行端反查：两处通用入队候选的有限排除

日期：2026-09-27。只读 CK3 1.19.0.6 磁盘 EXE，SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；
未启动、附加或修改游戏。目标是从已核 [CMoveUnitCommand 间接 apply](war-film-move-command-constructors-2026-09-23.md)
反查尚未归因的通用入队生产者，并防止把邻近的 `0x973E00` 调用都当作军队撤退。

## 回溯边界

已有战中 owner-subset 执行链为 `CMoveUnitCommand` secondary vtable `0x432BFB0+0x08`
`→ 0x26B4710 → 0x2308850 → 0x23CA360`；direct source census 对最后一步只见
`0x2308AC1` 的 move apply 与 `0x24E3D08` 的继承清理。继承调用有不同参数，不能代表 AI 的撤退决策。
真正的 move command 主/次 vtable 地址点为 `0x432BF18/0x432BFB0`。

对 `0x1800000..0x1900000` 的已解码代码扫描 `0x973E00` direct call，出现 **35 处**候选。
这份清单只用于选点，没有把 35 处都分类、也没有扫描全 EXE 或间接调用。
优先取靠近已知 army/controller 代码的 `0x187B5DE`，发现不是 move 后换下一处 `0x187BA0C`：

| 入队调用 RVA | 同一构造窗口的 vtable 写入 | MSVC RTTI 原名 | 判定 |
| --- | --- | --- | --- |
| `0x187B5DE` | `0x187B54F/55A` 装 `0x40829F8/0x40829C8` | `CSendCharacterInteractionCommand` | 角色互动命令；不是 `CMoveUnitCommand`。 |
| `0x187BA0C` | `0x187B9D8/9E3` 装 `0x43304F0/0x4330588` | `CExtendMercenaryCompanyCommand` | 延长佣兵团合同命令；不是 `CMoveUnitCommand`。 |

两条 `call` 的相对位移都精确指向 `0x973E00`；vtable 前的 MSVC COL 分别回指上述
TypeDescriptor，同名主/次对象偏移为 `0/24`。这比依据调用地址或全局队列函数推断业务类型更可靠。
这两处没有形成“读取当前 `CCombat` 战损/预测 → 选择撤退 → 生成 kind-2 move → apply”的同一路径。
**有限结论仅排除这两个候选**；队列扫描其余 33 处、动态 factory/克隆、未扫描区域和间接调用仍未知，
不能写成普通战争 AI 没有主动撤退。劫掠失败清理与[大圣战集结比值门](coordinator-ghw-staging-ratio-not-combat-retreat-2026-09-27.md)
也不在本次候选内，不能混作普通战争策略。

## 可复核证据与下一候选

[exact-build verifier](../../ck3_autonomous_player/native_bridge/research/verify_indirect_queue_non_move_candidates_static.py)
检查 EXE 整体 SHA、两个 submit 的相对 `call`、四条 RIP-relative vtable 装载、MSVC COL/RTTI 与
真正 `CMoveUnitCommand` 地址点的不相等：

```text
<verified-python> ck3_autonomous_player/native_bridge/research/verify_indirect_queue_non_move_candidates_static.py --exe <exact-ck3.exe>
```

本机验证通过。仓库外原始材料在
`D:/workspace/ck3_native_war_ai_promo_work/ordinary-war-retreat-static-20260927/`：
`queue-submit-war-ai-xrefs.txt` SHA-256 `1e97e39d6e107d9bcec770f5a583a335465359ce0b91b60143af9f3e44306e52`；
`queue-187b.txt` SHA-256 `cc7b963159fdb03368869ed1cefaeba5432b45e08319def7b5f81c1bf8e5502e`；
`apply-direct-xrefs.txt` SHA-256 `f34c8055fa5ae95ad5b459f5ca86c3390897a12bc2429599a740206c531a8fea`。
扫描输出是引用候选，只有本文逐条恢复的指令边界/RTTI 可用于上述结论。

下一最小静态候选是 [a05 未闭合的空 move-command factory](war-film-move-command-constructors-2026-09-23.md#empty-factory-的已知与未知)
的后续字段填充者或共享队列上游：先证明其确实填了 CMoveUnit full ID/目标省，
再追同一生产者是否读取 active CCombat、预测或战损与时机门。只有观察自然实机中同一
CombatID/CUnit full ID 的 producer、队列和 apply，才能升级为 AI 自愿撤退的运行结论。
