# R0266 上船报价的原生候选：静态调用链

状态：**精确版本静态候选，未取得同帧金额，不得填写现金收据。**本页只读取 CK3 1.19.0.6 的 `ck3.exe` 和原版脚本；EXE SHA-256 为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。没有启动、连接或修改游戏进程。

原版 `game/gui/map_icon_layer.gui:650` 使用 `FleetPredictionMapIcon.GetEmbarkCostBreakdownTooltip`，`game/localization/english/gui/mapicons_l_english.yml:27` 用 `FleetPredictionMapIcon.GetEmbarkCost|V0` 展示上船价格。单看这个名字不能得到原生金额；本页的精确 EXE 校验沿注册器、缓存和计价函数继续追踪。

| 证据 | 精确 RVA 与结论 |
| --- | --- |
| GUI 绑定 | `GetEmbarkCost` 唯一名字在 `0x4101938`；注册器 `0xE1659` 引用它，`0xE16DD` 交给注册调用的 callback 为 `0xE89490`。`IsCostOverOwned` 名字在 `0x4101308`，注册器 `0xE1858` 绑定 callback `0xE894D0`。 |
| 读取和生命周期 | `0xE894A1..0xE894B6` 从 GUI context `+0x68` 指向的对象读取 `+0x78` QWORD，并复制到 GUI 返回值；这条 callback **没有重新计算报价**。对象构造在 `0xE81728/0xE81778` 把该槽置零。`0xE816DD/E816E4` 安装虚表 RVA `0x41003F0`；虚表第二项指向下述更新函数 `0xE818E0`，将缓存读和预测更新连到同一图标类。 |
| 原生累加 | 预测更新函数 `0xE818E0..0xE8212A` 在 `0xE81F99` 清零累计器，遍历 12-byte 条目，`0xE81FBF` 取每项首 DWORD ID，经组件存储表解析对象；`0xE81FFA` 调用 `0x22775F0`，`0xE81FFF` 将返回输出的 QWORD 相加，`0xE820E2` 写入图标对象 `+0x78`。对象 ID `+0x10` 与现有 bridge 的 `kArmyIdOffset` 相符，路径向量 `+0x38/+0x44` 也与 `CUnit` 布局相符；仍须在实际帧核对条目和计划军队 ID。 |
| 计算器 ABI 候选 | `0x22775F0` 入口保留 Windows x64 `RCX`、`RDX`、`R8`；调用点提供组件对象、QWORD 输出地址和 GUI 详情对象。`0x22779C4` 对 `R8` 做空值分支；尾部 `0x2277B52..0x2277B7B` 先按 `±50000` 对 Q100000 值作整金币舍入，再乘 `0x186A0 = 100000`；`0x2277B82..0x2277B89` 将结果写入原 `RDX` 指向的 QWORD，并以该输出地址返回。每项经此路径得到的金额为 100000 的整数倍，累加后仍如此。代码经过其他 helper、虚表调用和可选 GUI 详情构造；这些下层的副作用及空 `R8` 路径尚未全部证明，**不得把此函数接为可调用的 live getter**。 |
| 金币语义和比例 | `IsCostOverOwned` 的 `0xE8248F` 读取角色扩展 `+0x100` 的金币 QWORD，`0xE82496..0xE824A3` 将其与同一图标 `+0x78` 作有符号比较。现有 bridge 在 `ck3_11906.cpp:1114,1135,10577-10581` 将扩展 `+0x100` 定为 `played_character_gold.raw`，比例 `100000`。这和计算器尾部的 `×100000` 一起支持**Q100000 金币报价候选**；其他政府货币分支仍须核对。 |

精确验证器 [`verify_war_cash_embark_quote_candidate.py`](../../ck3_autonomous_player/native_bridge/research/verify_war_cash_embark_quote_candidate.py)核对 EXE SHA、两个唯一名字及其 RIP 引用、两个 callback 的 RIP 目标、图标虚表三项和 34 个指令锚点；普通 Python 与 `-O` 均通过。它固定输出 `safe_to_call_from_live_bridge=false`、`same_frame_amount_observed=false`、`priced_action_identity_proven=false`。外置探索脚本保存在 `D:/ck3-research-artifacts/r0266-embark-static-20260928/`；这些脚本不读取 CK3 进程。

**交付边界。**缓存只代表某个原生舰队预测图标上次更新时的成本。尚未证明该图标唯一、属于 Robert、对应所选 `move-army` 的军队、原点、目标和全路线，也未证明缓存与暂停帧同时更新。只有未来的受管同帧被动读回同时核对这些身份、原生 revision、日期、国库及可见 GUI 金额，才能把缓存作为该动作的报价候选。`0x22775F0` 的计算链还需证明所有下层纯读，才能考虑主动查询。H2825 未取得上船报价；`immediate_war_action_cost_raw`、`pending_war_cash_raw`、未来上界、风险预算与战争最低保留额继续为 `null`。
