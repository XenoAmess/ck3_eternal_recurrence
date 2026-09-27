# 追击硬伤写入顺序与终局 side 归因补记：exact-build 勘误

适用原版 CK3 `1.19.0.6-steam23530548`，`ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。只读 [`verify_combat_final_side_attribution_static.py`](../../ck3_autonomous_player/native_bridge/research/verify_combat_final_side_attribution_static.py) 检查 12 处原始字节、8 条直接调用边，还逐指令扫描 `0x23C9770..0x23C98F5` 的函数体。下述是 **static-confirmed**，没有启动 CK3，也没有新增逐日实机对拍；因此任何未命名的归因行字段和脚本副作用均保持 **live-unverified**。

## 每日追击：底层硬伤先于 entry.soft 写回

[主研究](battle-simulation.md#pursuit--screen)已闭合 `0x23CD660` 依 frozen soft pool 算预算、两遍按原生顺序分配的数值公式。本轮补充两个 writer 的**指令顺序**：

| `0x23CD660` 内路径 | 先执行 | 后执行 | 可观察分层 |
|---|---|---|---|
| 第一遍 | `0x23CDA59` 调 `0x239C840(CRegiment*, hard_raw)` | `0x23CDA72` 写 `CCombatRegiment+0x20 = old_soft - hard_raw` | 先永久写入底层整数 component，后改战斗 entry 的 soft raw |
| 余数第二遍 | `0x23CDC77` 再调 `0x239C840` | `0x23CDC89` 写同一 entry 的 `+0x20` | 仍是底层先行；随后更新本遍 soft |

这不改变此前两遍分摊的**最终算术值**，但此前伪代码把 `entry.soft -= hard` 排在 `0x239C840` 前，应改为上表顺序。`0x239C840` 的底层 component setter 有[额外条件清零分支](combat-component-writeback-and-terminal-reset-static-2026-09-27.md)；若以后需要对拍任一 callback 或中途状态，不能把两次写回视为原子一步。第一遍 `0x23CDA72` 使用的 entry 指针来自原生 array 首址 `0x23CD8D2..0x23CD8D9`，不是 attribution row；第二遍直接写 `r15+0x20`。

## 正常终局：`0x23C9770` 不是兵员 reset

原文档将 `0x230A9AC/0x230A9B8` 的 `0x23C9770` 调用称为“两侧 reset”。函数体不支持这个名字：

1. `0x23C977A` 从 `CCombatSide+0x10` 取 ordered ArmyID 数组；逐军由 `CArmy+0x38/+0x44` 读 RegimentID，并经 full-ID 比对解析 `CRegiment*`。
2. 对每个兵团，`0x23C9839` 读取底层 `CRegiment+0x38` 的**当前整数人数**，`0x23C9848` 乘 `100000` 转 Q100000；`0x23C9844` 取 `CRegiment+0x18` type 指针，`0x23C984F` 取 `+0x148` 角色 ID。此处取的是底层当前人数，不是 combat entry 的 `current+0x18`、`soft+0x20`，也不是 type `+0x38`。
3. 函数在 `side+0xC8` 指向的归因容器 `+0x38/+0x44` 中按 `(type pointer, character ID)` 查找 `0x50`-byte 行；未找到时仅有的一处函数体 call `0x23C989C → 0x23DE6F0` 创建行。`0x23C98AB: add qword ptr [rcx+0x48],rdi` 把该兵团 `current_integer×100000` 累加到匹配行 `+0x48`。`+0x48` 的正式业务字段名未由 serializer 或 GUI 反证，不在此猜成“存活”或“死亡”列。

逐指令写入扫描显示，函数体唯一**直接非栈内存写入**是行 `+0x48`；其唯一直接 call 是上述行创建。它没有在本函数体调用 `0x239C840`、`0x23D2E30` 或写 `CCombatRegiment+0x18/+0x20`。这证明它不是软伤返还或兵员重置函数；`0x23DE6F0` 的行插入副作用仍应按容器变更保留。不能由此声称整个终局 cleanup 不会通过别的函数修改兵员。

同一 finalizer 的 exact 顺序是先 `0x230A984/998 → 0x23DB050` 投影两侧 result，接着 `0x230A9A3 → 0x230AF10` 分派 normal result envelopes，**然后** `0x230A9AC/B8 → 0x23C9770` 处理 side 归因。`suppress_normal_result_envelopes=true` 的 `0x230A657` 直接跳过这整段。若未来要将 row `+0x48` 纳入 result/战分或智能体终局统计，须先证其后续 reader、可见字段与实机前后值；目前只应把它作为**终局后置归因行更新**，不把该行当作前述 result 投影的已确认内容。

## 对整场胜率核的直接约束

每日追击的永久损失仍走 `0x239C840`；正常终局的 `0x23C9770` 不应被模拟器另加一次软转硬、清零兵团或“恢复软伤”的步骤。只有在独立原生前后回读绑定同一 CombatID、RegimentID、type/character 行、原始日更边界与源档 hash 后，才能确认该后置 `+0x48` 对公开结果或下一场接战输入的实际影响。尤其不能用这个静态函数体推断 terminal winner、retreat destination、event effect 或游戏 UI 统计数值。
