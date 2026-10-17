# 多信仰共享圣地：原生库存与圣物替换

`machine_id: 4-8e1c2f1861`。本次只读复核时间：`2026-10-17T18:19:09.528750+00:00`。来源固定为 CK3 1.20.0.4、EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518` 的既有有限函数包；精确原件 SHA、RVA 边界和函数体 SHA 见 [compactevidence.json](native-sharing.evidence.json)。没有操作游戏、读取进程或重新构建，也没有把旧实机结果扩充成新的替换验收。

同一个实际 HolySite 完整 ID 只有一份物理库存和槽位；不同信仰关联到同一个对象。供奉替换时，旧圣物在合法 actor 存在的正常路径上转给本次命令的执行角色。自动选槽不比较各信仰的圣物价值。这三点应分别进入智能体的状态模型、交易后态和决策规则。

## 同一对象，共用库存

原 `265B000..265B09D` 按完整 HolySite ID 从全局 storage `5D1DE80` 解析对象，并核对代际。`BB6C50..BB6C55` 的完整 getter 直接返回 `site+28` 内嵌 Inventory，参数中没有 faith。构造器 `26583D0..26585EE` 初始化这一份库存及 `site+68` 槽表；`D68090..D68098` 返回另一个字段 `site+98` 的关联信仰数组。Faith 的普通/显赫圣地集合保存站点 ID，不为每个信仰另建库存。

| 状态 | 身份或来源 | 智能体应如何保存 |
|---|---|---|
| 圣地实例 | 当前 session + 完整 HolySite ID | 一个物理对象；保留代际 |
| 圣地库存 | `site+28`；owned refs 为 `site+80` | 一个原序完整 ID 列表 |
| 圣地槽位 | `site+68`，每行 24B，artifact ID 在 `+10` | 一个槽数组；显式保存空槽和未知 |
| 关联信仰 | `site+98`；各 Faith 反向引用站点 ID | 关系集合，不复制库存 |
| 圣物所有权 | artifact `+78` 角色、`+7C` 圣地 | 两个独立字段均读回并解析 |
| 认可与收益 | 原 `2530EF0(artifact,faith,...)` 等 | 按信仰保存观察结果；不能等同物理归属 |

以上“共用”以同一个运行时完整 ID 为准。中文同名、definition key 相似或同一县内有两个 HolySite，不能单独证明它们是同一个实例。也不能从关联数组直接宣称每个信仰得到相同 modifier；实际受益范围由 runtime 专项另证。

## 替换旧物时交给谁

完整供奉 receiver `29AADE0..29AB4EB` 的 secondary-this 参数为 site `+8`、新 artifact `+C`、actor `+10`、slot `+14`。它先按站点解析同一对象，校验显式槽或调用原 picker，并在 `29AAF22` 抓取该有效槽的旧 artifact ID。随后 `29AAF40` 把本次 actor 保存到 EBX，`29AAF52` 调 `2530300(new,site)` 转入新物。

旧槽非空、actor 及旧 artifact 完整引用有效时，`29AAFFF` 调的是 `252FDD0(old,actor)`。其完整字节已在旧 bounded 包内：`252FE54` 从旧圣地库存移走，`252FE59` 清除 old 的圣地 owner，`252FECC` 写角色 owner 为目标 actor，`252FF02..252FF0D` 把 old 加到该角色 Inventory。新物随后在 `29AB021` 装入同一站点的同一有效槽。旧物没有按原捐献者、县主、教宗或“物品所属信仰”另分配；这些角色只有恰好等于本次 actor 时才会收到。

`2530300` 的已复核有限前段 `2530300..25304BF` 则清除新物旧角色归属、写入新圣地 owner，并加入 `site+28`；其后事件/脚本尾部不在本次完整证明范围内。独立取出 receiver `29AB8A0..29ABB12` 也先查同一 `site+28` 的 equipped membership，正常有效 actor 路径调用相同 `252FDD0`。无有效 actor 的特殊 fallback 不作为正常玩家成功。

这属于原版执行器语义，不授权直接调用 receiver。现有操作仍只走实际可见启用按钮的原回调、冻结预览和原版许可。

## 自动槽位不是收益优化器

完整 `2C805E0..2C806CB` 没有下游调用。它只以新物的 artifact type 判断槽兼容：通用槽，或两个类型字段相符。按原槽序，找到第一个兼容空槽就返回；没有空槽时，选兼容已占用槽中旧 artifact `+B0` 稀有度最低者；平手保留先出现的槽。它不比较新旧稀有度差额，也不读取 faith 认可、宗教收益、玩家自用价值或替换成本。

因此，同槽中的旧圣物即使对另一个关联信仰有意义，也没有自动选槽层的单独保护。合法替换会改变所有视角所引用的同一份物理库存。不过，能否操作仍受原版规则限制：`29AB4F0` 将真实旧槽 ID 交给新物供奉规则，旧物有效时还检查其移除规则。共享库存不能推导为任何人都可拿走任何圣物。放弃圣地返还的脚本规则由 script lane 单独审查。

## 已有 MCP 如何规划，以及最小补测

现有 action-context 已提供真实 effective slot、非空 replacing artifact、两物 owner、当前选择和原生效果预览身份；动作请求可冻结 `relic_expected_effective_slot_index`、`relic_expected_replacing_empty=false`、`relic_expected_replacing_artifact_id=A` 与 fresh preview SHA。规划器应在调用前独立比较新物 B 的贡献、旧物 A 的损失、关联信仰受影响范围、两物的个人用途、收回 A 的价值及实际成本。原 picker 只作为执行机制，不作为“值得供奉”的依据。

最小新增实机 cell 是一次合法、共享站点、非空槽的替换：

1. 当前实际站点 S 至少关联两个信仰；同一暂停帧读回其关联/反向 ID、库存和槽位。槽 k 中有旧物 A，A 的圣地 owner 为 S；当前玩家真实拥有不同的新物 B。
2. 经现有 typed 选择 B 和 desired 槽 k，独立读回 `108/110`。新 action-context 必须显示 effective=k、replacing=A，并取得真实按钮与 fresh 原生预览；原供奉、移除许可都实际满足。
3. 使用上述非空替换冻结条件，只提交一次现有 `enshrine_relic`。未知结果不得重试。
4. 在独立后续稳定帧读回：槽 k=B；B 的圣地 owner=S、角色 owner 空且离开玩家 owned；A 的角色 owner=实际 actor、圣地 owner 空，进入玩家 owned 且不再 site-equipped；其他槽不变，S 的关联信仰关系仍可核对。ACK 仅表示待验证。
5. 这能补足共享非空 replacement 的结构和归属证据。若要讲明某个外教实际损失或获益，还需对那个信仰的原认可 predicate 与实际 beneficiary/modifier 结果取证；由 runtime lane 继续，不能从 sanctified ID 数组或 rarity 代替。

现 reader 的认可视角主要是玩家信仰与县主信仰。需要任意关联信仰视角时，应在同一个 source-bound MCP reader 上增加有界、完整 ID 核验的逐 faith 观察，并单独取得资格；未知值保留为 unknown。本轮没有新增这个运行能力或重跑整套 modifier 研究。

本次源记录预算 100 KiB，使用 active v3 预留；精确容量和来源在机器可读回执。`2026-10-24T18:19:09.528750+00:00` 复核小型记录和活跃来源的用途，按通用存储策略处理可重建派生物，不永久延长全部原始资产的保留。
