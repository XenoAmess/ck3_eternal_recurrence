# H2743 法理县退出条款：原生只读入口的窄边界

本轮只对已由完整 SHA-256 固定的 CK3 `1.19.0.6-steam23530548`
EXE 做定向磁盘 RVA 读取；没有启动 CK3、求值 effect／preview、访问游戏内存或占用屏幕。
EXE 的完整 SHA 为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
[短区间读取工具](../../ck3_autonomous_player/native_bridge/research/disasm_ck3_bounded_disk.py)
每次最多读取 `0x1000` 字节目标区间，另读 PE 头和五处冻结指令；其文件尺寸与锚点检查
只用于防误读，**不能代替**已有完整 SHA 证明。现有
[V2 作用域回执](../../ck3_autonomous_player/native_bridge/research/dejure_title_scope_resolution_gate_v2_1_19_0_6.json)
和[效果审计](h2743-defender-surrender-static-effect-audit-2026-09-28.md)仍是身份与脚本来源。

| 最窄候选 | 本轮磁盘字节所证 | 对 H2743 producer 的结论 |
| --- | --- | --- |
| `setup_de_jure_cb` 的 `scope:target` | `0x2E9F5AF/B6` 将 effect `+0x260` 送进 `0x995CB0`；后者调 `0x336AB40`。动态求值器 `0x336AC47`、`0x336AC8B` 分别调用实际节点虚表 `+0x30`、`+0x20`，并在 `0x336ACB1` 把结果写入 caller output。 | 节点类型、目标函数、传递写集合及有效上下文仍未闭合。不能单独调用 `0x995CB0` 或把战争 `targeted_title_ids=[2128]` 当循环外临时 `scope:target` 的同帧求值。 |
| `F` 输入计数 | setup `0x2E9F6E3–70B` 传入多个栈容器；helper `0x2E9FFF0–2EA001C` 按 effect `+0x260` presence 选择 `0x28B21E0` 或 `0x28B1EB0`。两支都建立动态容器；前者 `0x28B227D–28E` 又调用 `0x20B4E10` 后循环筛选并追加记录。helper `0x2EA0021–2E` 将容器计数写入 setup caller 栈，setup `0x2E9F710–722` 读取该计数、乘 `100000`、送入 writer。 | 计数是动态处理结果，静态上不能等同于 `target_titles` 长度 `1`。它也不是已经读到的最终 `cb_prestige_factor`。 |
| `F` 写入 | `0x2E9F2C0` 把传入的 Q100000 数值纳入结构并调用 `0x33590D0`；后者 `0x3359123–158` 在容器中查找 identifier，`0x335953F–560` 可更新已有 row，`0x3359566–57A` 可插入新 row。 | 这是**修改上下文容器**的路径，不是纯只读 getter。既有 claim CB 的 root-proxy/loaded-effect traversal 不自动适用于此 de-jure effect；本项目已记录该类预览崩溃，禁止在原游戏态重试。 |
| `resolve_title_and_vassal_change` | [预入队回执](../../ck3_autonomous_player/native_bridge/research/dejure_resolve_prequeue_gate_1_19_0_6.json)仅证明 type `0x17` 对比、其他类型的条件处理和五个容器计数检查；[预览回执](../../ck3_autonomous_player/native_bridge/research/dejure_defender_surrender_preview_1_19_0_6_abi.json)证明其 preview `0x7E9220` 只是返回 true。 | 任何入口都没有给出当前完整 title／holder／人物 liege／vassal 的最终操作图。构造时 `type=0` 和历史 R0197 迁移不能填 H2743 delta。 |

因此，**当前可证明纯只读的最窄 live 入口只到已交付的 V1 战争身份、
`targeted_title_ids` 和双方行动前余额**；它们的语义分别是输入列表和前态。
本次找不到可单独调用、能返回运行时 `scope:target`、最终 `F` 或完整变更图的
无副作用原生函数。下一步只能在静态闭合对应节点和变更处理链后写纯投影，
或取得游戏已经物化的、绑定同一 effect/WarID/revision/generation 的结果槽并双采样。
在此之前，三个结果字段继续是 `null`，`material_complete=false`、
`recommended_outcome=null`、`action_literal=null`。
