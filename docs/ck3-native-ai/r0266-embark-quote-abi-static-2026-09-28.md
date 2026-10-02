# R0266 上船报价的原生候选：静态调用链

## 预测集合与计划动作的额外门禁

精确 EXE 的预测更新在 RVA 0xE81CC0 记录条目数量，0xE81CDB 与 0xE81CE6 将一个 ID 和一个尚未释义的 QWORD 写入每条 12-byte 临时记录；0xE81D2D 对条目数是否超过 32 作分支，随后 0xE81F99..0xE82009 遍历条目逐个取价并累加到图标缓存。该缓存代表预测集合的总价候选，不能仅凭数值相等绑定单支军队或一次 MoveArmy。必须证明集合全部 ID、选中动作的 typed step、军队、完整路线、preview 序号、原生 quote ID 与同帧缓存刷新属于同一次报价；当前没有此证明。新加四个精确指令锚点通过普通和优化 Python 静态校验，未启动游戏。五项战争现金仍为 null。

状态：**精确版本静态候选，未取得同帧金额，不得填写现金收据。**本页只读取 CK3 1.19.0.6 的 `ck3.exe` 和原版脚本；EXE SHA-256 为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。没有启动、连接或修改游戏进程。

原版 `game/gui/map_icon_layer.gui:650` 使用 `FleetPredictionMapIcon.GetEmbarkCostBreakdownTooltip`，`game/localization/english/gui/mapicons_l_english.yml:27` 用 `FleetPredictionMapIcon.GetEmbarkCost|V0` 展示上船价格。单看这个名字不能得到原生金额；本页的精确 EXE 校验沿注册器、缓存和计价函数继续追踪。

| 证据 | 精确 RVA 与结论 |
| --- | --- |
| GUI 绑定 | `GetEmbarkCost` 唯一名字在 `0x4101938`；注册器 `0xE1659` 引用它，`0xE16DD` 交给注册调用的 callback 为 `0xE89490`。`GetEmbarkCostValueBreakdown` 名字在 `0x41018F8`，注册器 `0xE12CE` 绑定 callback `0xE86390`。`IsCostOverOwned` 名字在 `0x4101308`，注册器 `0xE1858` 绑定 callback `0xE894D0`。 |
| 读取和生命周期 | `0xE894A1..0xE894B6` 从图标 `+0x68` 指向的 **0x90 字节费用行**读取行 `+0x78` QWORD，并复制到 GUI 返回值；这条 callback **没有重新计算报价**。构造器 `0xE817A1` 将该行指针写入图标 `+0x68`，`0xE817C0/E817FE` 把同一行装入图标 `+0x70` 的 0x50 字节 breakdown wrapper；`0xE86390` 的 `GetEmbarkCostValueBreakdown` 返回此 wrapper。行构造在 `0xE81728/0xE81778` 把金额槽置零。`0xE816DD/E816E4` 安装虚表 RVA `0x41003F0`；虚表第二项指向下述更新函数 `0xE818E0`，将缓存读和预测更新连到同一图标类。**不能把图标 `+0x78` 误读为金额**。 |
| 原生累加 | 预测更新函数 `0xE818E0..0xE8212A` 在 `0xE81F99` 清零累计器，遍历 12-byte 条目，`0xE81FBF` 取每项首 DWORD ID，经组件存储表解析对象；`0xE81FFA` 调用 `0x22775F0`，`0xE81FFF` 将返回输出的 QWORD 相加，`0xE820DE/E820E2` 写入**图标 `+0x68` 指向的费用行 `+0x78`**，`0xE820E6..0xE820F1` 重绑 breakdown wrapper 并刷新。对象 ID `+0x10` 与现有 bridge 的 `kArmyIdOffset` 相符，路径向量 `+0x38/+0x44` 也与 `CUnit` 布局相符；仍须在实际帧核对条目和计划军队 ID。 |
| 计算器 ABI 候选 | `0x22775F0` 入口保留 Windows x64 `RCX`、`RDX`、`R8`；调用点提供组件对象、QWORD 输出地址和 GUI 详情对象。`0x22779C4` 对 `R8` 做空值分支；尾部 `0x2277B52..0x2277B7B` 先按 `±50000` 对 Q100000 值作整金币舍入，再乘 `0x186A0 = 100000`；`0x2277B82..0x2277B89` 将结果写入原 `RDX` 指向的 QWORD，并以该输出地址返回。每项经此路径得到的金额为 100000 的整数倍，累加后仍如此。代码经过其他 helper、虚表调用和可选 GUI 详情构造；这些下层的副作用及空 `R8` 路径尚未全部证明，**不得把此函数接为可调用的 live getter**。 |
| 金币语义和比例 | `IsCostOverOwned` 的 `0xE8248F` 读取角色扩展 `+0x100` 的金币 QWORD，`0xE82496..0xE824A3` 将其与同一图标 `+0x68` 指向的费用行 `+0x78` 作有符号比较。现有 bridge 在 `ck3_11906.cpp:1114,1135,10577-10581` 将扩展 `+0x100` 定为 `played_character_gold.raw`，比例 `100000`。这和计算器尾部的 `×100000` 一起支持**Q100000 金币报价候选**；其他政府货币分支仍须核对。 |

精确验证器 [`verify_war_cash_embark_quote_candidate.py`](../../ck3_autonomous_player/native_bridge/research/verify_war_cash_embark_quote_candidate.py)核对 EXE SHA、三个唯一名字及其 RIP 引用、三个 callback 的 RIP 目标、图标虚表三项、费用行/wrapper 指令与预测集合的指令锚点；普通 Python 与 `-O` 均通过。它固定输出 `safe_to_call_from_live_bridge=false`、`same_frame_amount_observed=false`、`priced_action_identity_proven=false`。外置探索脚本保存在 `D:/ck3-research-artifacts/r0266-embark-static-20260928/`；这些脚本不读取 CK3 进程。

**交付边界。**缓存只代表某个原生舰队预测图标上次更新时的成本。尚未证明该图标唯一、属于 Robert、对应所选 `move-army` 的军队、原点、目标和全路线，也未证明缓存与暂停帧同时更新。只有未来的受管同帧被动读回同时核对这些身份、原生 revision、日期、国库及可见 GUI 金额，才能把缓存作为该动作的报价候选。`0x22775F0` 的计算链还需证明所有下层纯读，才能考虑主动查询。H2825 未取得上船报价；`immediate_war_action_cost_raw`、`pending_war_cash_raw`、未来上界、风险预算与战争最低保留额继续为 `null`。
