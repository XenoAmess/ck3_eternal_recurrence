# 败方 on-action：名称表到执行根的序号映射已静态闭合

日期：2026-09-27。本页接续[败方 loaded effect 树身份审计](loser-loaded-effect-tree-source-identity-static-2026-09-27.md)，对 CK3 1.19.0.6 做有界、只读、exact-build 静态复核。EXE SHA-256 为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，磁盘原版 `combat_on_actions.txt` SHA-256 为 `B35D696F472E801BB332D7204AA46008349E8AFBFDB38985C781EB099BBFB233`。没有启动、附加 CK3，也没有读取或执行 loaded effect。

## 新闭合的映射

此前查到两个数值相同的 `+0x260`，却属于不同基址：`[COnActionDataBase+0x50]+0x260` 是名称表的 `on_birthday`，而败方执行读取 `[database+0x38]+0x260`。**它们不能按相同字节偏移配对。**本次找到加载器使用的共同**元素序号**，消除这一误配：

| 位置 | exact-build 指令证据 | 含义 |
| --- | --- | --- |
| `0x25048A4–0x25048C1` | `root+0x38` 数组按 8 字节元素寻址，配置 `0xC3=195` 个槽 | on-action 执行根指针表 |
| `0x25049A4–0x2504A10` | `name+0x50` 数组按 0x20 字节字符串元素寻址，同样配置 195 个槽 | 对应的名称表 |
| `0x25052A4–0x25052B8` | 名称表 `+0x980` 写入 `on_combat_end_loser` | 名称序号 `0x980/0x20=76` |
| `0x2506B30→0x2506C9E→0x33F75C0` | `COnActionDataBase` 次级虚表 `+0x08` 的加载方法把次级对象 `RSI-0x88` 还原为数据库主基址传给通用加载器 | 加载器操作的是上述同一主对象的名称/根表 |
| `0x33F7B45–0x33F7B91` | 从主基址 `+0x50` 取名称表，按 `0x20` 逐项比较解析名称；匹配序号在 `RDI` | 名称匹配产生索引 |
| `0x33F7BF0–0x33F7D06` | `RBX=RDI*8`；从保存的同一主基址 `+0x38` 取根表；将解析所得 `R13` 写到该索引 | 名称序号原样成为执行根序号 |
| `0x230B0A9–0x230B0EE` | 普通终局败方路径从 `+0x38` 根表的 `+0x260` 读指针，作为 `0x33F8350` 的 `RDX` | 执行根序号 `0x260/8=76` |

所以**数据库结构和加载器的静态映射**为 `on_combat_end_loser` 名称序号 76 → 同序号的 loaded effect 根。`on_birthday` 名称表 `+0x260` 是序号 19，其相应根表位置应为 `19*8=+0x98`；它不是败方执行根 `+0x260`。此结论说明为什么两个字节偏移看似冲突，并给出实际配对规则。`0x33F75C0` 的 `R12` 在入口保存主基址，`[RBP+0x490]` 是入口 RCX 的栈保存位；`0x33F7B9A/0x33F7CFA` 从它恢复基址，故不是把名称表误当根表。

## 尚未取得的实例证据

这条映射**只到败方 on-action 执行根**。磁盘文本第 563 行有 `combat = { warscore_value >= 15 }`，但本次没有从该根唯一走到其 `CCombatWarscoreTrigger` loaded 子对象，亦没有读到该实例 `+0x50` 操作码、右操作数求值后的 raw qword 或分支返回。原版磁盘 SHA 也不等于正在运行的 VFS 来源证明。已证的通用 `0x3CB` signed `>=` 比较器与按 Q100000 推出的 `1,500,000`，仍不得升级成该实例的 live 读值，更不能据此认定 `-50` 正统性已写回。

**相同数字也不是实例身份证。**本机原版 `game/events/war_events/combat_events.txt:2238` 还有逐字相同的 `combat = { warscore_value >= 15 }`，该文件 SHA-256 为 `CF4E7F43786477DF43319638138232086CFD477FEE0F2951B34DD41BE265CADD`。因此某次比较命中即使类型、`>=` 操作码和 RHS `1,500,000` 均吻合，也不能仅用这些特征判定来自败方 on-action 第 563 行；须绑定执行父链与脚本来源。此处只证明存在原版同文字候选，不声称该事件在当前战斗中被加载或执行。

后续最小静态目标是闭合 `0x33F8350` 败方根到第 563 行 trigger 的父链，优先解码根 `+0x2B0/+0x2BC`、`+0x2F8/+0x304` 两种执行数组与 `+0x348` 递归子指针中的实际 child/trigger 载荷；解析期 `0x28` 字节记录不得未经验证就命名为源行号。若静态分析仍不能唯一绑定，受管实机的第一阶段只能在同场、同线程、容量受限地记录败方根及父子边，并冻结真实 VFS 来源/bytes、CombatID、WarID、日期、败方身份；这一阶段的候选命中不证明第 563 行。父链与来源确认后，第二阶段才可按[被动探针 ABI 预检](loser-warscore-trigger-passive-probe-abi-preflight-2026-09-27.md)在 `0x99FAF0` 读取同一指针的操作码和已求值两侧 raw。重入、溢出、线程或节点身份不一致一律 RED；不调用原生 evaluator、parser 或 effect。

## 复核

[exact-build verifier](../../ck3_autonomous_player/native_bridge/research/verify_loser_on_action_index_map_static.py)检查三份 SHA、on-action 原版唯一声明及事件文件的同文字反例、31 个指令锚点、两个调用目标、`COnActionDataBase` 次级虚表加载槽以及索引算术。本机运行通过；成功输出仍明确为 `actual_vfs_bytes_verified=false`、`loser_root_to_script_line_563_trigger_bound=false`、`loaded_loser_node_opcode_verified=false`、`loaded_loser_node_rhs_raw_verified=false`。

```text
<verified-python> ck3_autonomous_player/native_bridge/research/verify_loser_on_action_index_map_static.py --exe <exact-ck3.exe> --on-action <exact-combat_on_actions.txt> --combat-events <exact-combat_events.txt>
```
