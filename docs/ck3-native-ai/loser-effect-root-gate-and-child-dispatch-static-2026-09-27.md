# 败方 loaded effect 根：节点门与 child 调度的静态边界

日期：2026-09-27。接续[同实例名称—根索引映射](loser-on-action-name-root-index-map-2026-09-27.md)，只读审计 CK3 `1.19.0.6` 的败方 on-action 执行根。EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；磁盘原版 `combat_on_actions.txt` SHA-256 `B35D696F472E801BB332D7204AA46008349E8AFBFDB38985C781EB099BBFB233`。没有启动或附加 CK3，没有调用 parser、trigger evaluator 或 mutator。

## 新闭合的执行结构

败方根由 `[database+0x38]+0x260` 取出，于 RVA `0x230B0EE` 传入通用 effect dispatcher `0x33F8350`。该 dispatcher **先**在 `0x33F8392` 调用 `0x33F6A20(current_node, context)`：后者在 `0x33F6ABA` 读当前节点 `+0x338` 的可选门指针，非空时于 `0x33F6AC9` 交给 `0x334C510` 求值；空指针走 true 分支。`0x33F8399` 在结果为 false 时直跳 `0x33F86F9`，绕过以下 child 调度。因此 `+0x338` 是**通用节点级执行门**，而非一个可凭偏移直接叫做“第 563 行 warscore trigger”的字段。

| 顺序 | RVA 与节点字段 | 已证的通用调度动作 |
| --- | --- | --- |
| 1 | `0x33F8392`，`node+0x338` | 可选节点门求值；false 跳过后续调度。 |
| 2 | `0x33F8561→0x33F8D00`，`node+0x2B0/+0x2BC` | 遍历步幅 `0x30` 的数组；元素首指针的虚表 `+0x30`、`+0x40` 两次通过后才调用 effect 回调。 |
| 3 | `0x33F8589→0x33F8720`，`node+0x2F8/+0x304` | 遍历步幅 `0x48` 的数组；元素 `+0x20` 非空时，再调用 `0x33F6A20` 检查该指针后才调用回调。 |
| 4 | `0x33F8633→0x33F8653`，`node+0x348` | 非空时递归调用同一 `0x33F8350`。 |

这些是**可用于未来定位 child 的遍历边**。目前没有读取任何运行时 loaded 根或数组元素，也没有解析加载器把磁盘第 563 行编译到了哪个节点/门/元素。特别是 `+0x338` 的求值、数组元素 `+0x20` 的求值、`0x30` 步幅元素的虚方法三条路径都可能出现条件检查；仅看到一个 `CCombatWarscoreTrigger` 类型、操作码 `0x3CB`、比较 RHS `1,500,000` 或时序相近，不能唯一证明它属于败方 on-action：原版 `combat_events.txt:2238` 还有完全相同的 `combat = { warscore_value >= 15 }`。

## 战果数值与写回的可证层级

磁盘脚本 `combat_on_actions.txt:561–575` 明确把 `combat = { warscore_value >= 15 }` 放在败方 `effect` 的第二个 `if.limit`；其满足后，`side_primary_participant` 的内层 `is_valid_for_legitimacy_change=yes` 才包含 `send_interface_toast` 内的 `add_legitimacy = minor_legitimacy_loss`。原版 script value 为 `0-50=-50`。这些是**源声明**。已有[正常终局研究](normal-result-loser-effect-war-score-gate-2026-09-27.md)证明单场 battle row/result 写入先于败方 on-action、该字段为 Q100000 单场非负幅度；因此源字面量 `15` 的算术投影为 `1,500,000` raw。已有[通用比较器研究](warscore-trigger-generic-ge-and-loaded-node-gap-2026-09-27.md)证明操作码 `0x3CB` 对 raw qword 执行 signed `>=`。但本轮**没有**从实际 loaded 子节点读出该操作码或 RHS，也没有看到该分支返回、`add_legitimacy` mutator 调用或实际 postcondition。不能把源声明和通用比较器拼成已验证的特定战斗 `-50` 写回，更不能据此声称战争已经终局。

下次受管实机若 Steam UI 门恢复，最小的只读证据要在同一 CombatID、WarID、败方、同线程下冻结实际 VFS 脚本来源与 bytes；记录 `0x230B0EE` 的根指针，沿上述节点门、两数组及递归边保存有界父链，直到唯一 `CCombatWarscoreTrigger` 指针，并与脚本编译来源交叉核对。**先完成身份与来源，再**在已[预检的 ABI 取数点](loser-warscore-trigger-passive-probe-abi-preflight-2026-09-27.md)被动复制该实例 `+0x50` 操作码、求值后 LHS/RHS raw 和返回值。要验证后续效果，还需同场跟踪 `add_legitimacy` 实际调用及对应人物的前后正统性；单靠 tooltip、战分行或正统性最终数值变化均不足以排除其他 effect。容量溢出、父链歧义、VFS 不符、线程/重入交错都保持 RED。当前 Steam UI 门未恢复，因此这些运行时项**未采样**。

## 复核

[exact-build verifier](../../ck3_autonomous_player/native_bridge/research/verify_loser_effect_root_gate_static.py)检查 EXE、on-action、同文字事件的 SHA，9 个原版声明行、32 个指令锚点、7 个相对 call 目标及两个关键分支目标。本机使用 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`（Python 3.14.7；环境含 `pefile`）运行通过。其成功输出仍明确标记 `loser_root_to_script_line_563_trigger_bound=false`、`loaded_loser_node_rhs_raw_verified=false`、`live_legitimacy_writeback_verified=false`；不代替 [名称—根索引 verifier](../../ck3_autonomous_player/native_bridge/research/verify_loser_on_action_index_map_static.py)或实机回执。

```text
<verified-python> ck3_autonomous_player/native_bridge/research/verify_loser_effect_root_gate_static.py --exe <exact-ck3.exe> --on-action <exact-combat_on_actions.txt> --combat-events <exact-combat_events.txt>
```
