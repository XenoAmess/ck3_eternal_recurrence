# 现役优势缓存前刷新：骑士称号聚合与兵团属性分流（2026-09-27）

本页只审 CK3 `1.19.0.6`、`ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。只读 [`verify_active_advantage_refresh_inputs.py`](../../ck3_autonomous_player/native_bridge/research/verify_active_advantage_refresh_inputs.py) 先复核[缓存及暂停叶子链](active-advantage-paused-input-timing-2026-09-27.md)，再核六段 `.pdata` owner、40 处精确机器字节和七个直接调用目标；[冻结夹具](../../ck3_autonomous_player/native_bridge/research/fixtures/active_advantage_refresh_inputs_11906.json) SHA-256 `4906377F609E571E5492E3B7CC0ED73376B104492C0868BB4D377BF0794A771B`。本轮未启动 CK3，不占桌面，也未在暂停查询中调用任何原版刷新 helper。

`0x2308D50` 在两侧 `0x2307CB0` 计算之前，先对 side0、side1 各调用 `0x23CBCE0`，再分别以目标 Province 调 `0x23CC2B0`。两次刷新**输出位置不同**，不能统称一个未知的“优势修正”：

| 原版函数 | 已证输入和写回 | 对当前模型的直接结论 |
| --- | --- | --- |
| `0x23CBCE0`，称号聚合刷新 | 首先检查 `side+0x11C`，非零时在锁保护下清 `side+0x11C/+0x184/+0x1EC` 三个 modifier 计数。随后只按 `side+0x40/count+0x4C` 的 MAA-like entry 原序、`0x60` stride 遍历；由 entry `+0x08` full RegimentID 重解 Regiment，经 `CRegiment+0x148` full CharacterID 和 `CCharacter+0x18` generation/有效性门，读取角色 `+0x1A8` accolade 链及链 `+0x568` full AccoladeID，再校验 accolade `+0x08` generation/有效性。仅通过者在 `0x23CBE99` 把 `side+0x110` 作目的地传给 `0x251B8F0`。 | **当前 side modifier 聚合器的称号项在缓存求值前重建**；单拷贝暂停帧 `side+0x110` 不能推定下一次求值。未进入该 MAA 顺序的 levy entry 不沿这条称号刷新链贡献。失效角色/称号跳过，但此 helper 的明确写入是聚合计数与目标容器，不能把跳过解释成删兵团。 |
| `0x251B8F0`，称号来源应用 | `0x251C200` 先作来源门；随后从 Accolade `+0x58` 读 row 指针、`+0x64` 读 count，按 `0x18` stride 取 row `+0x08` selector 与 `+0x10` 来源指针，后者加 `0x400` 后与 selector 一同送 `0x28A32A0`；其返回对象 `+0x390` 以 Q100000 scale 送 `0x21D3DD0` 写入传入的 `side+0x110` 聚合器。 | 这是可具体命名的**称号来源输入集合**，不是一个从 `commander_raw` 或 `resolved-base-roll` 倒推出的常数。row 的加载对象与 selector 语义未由本证据逐项闭合，不能仅凭整数编号宣称具体游戏称号加成。 |
| `0x23CC2B0`，entry 属性刷新 | 按 side levy `+0x28/count+0x34`、MAA `+0x40/count+0x4C` 各自原序，以 `0x60` stride 把每行和目标 Province 交给 `0x23D2CE0`。后者从 entry `+0x08` full RegimentID 解析当前 Regiment，调 `0x239CAE0` 取得属性结果，然后明确写回 entry `+0x30/+0x38/+0x40/+0x48/+0x50/+0x58`；其中既有研究已把 `+0x40/+0x48` 确认为有效伤害/坚韧。 | 此函数的显式写回是**兵团 entry 属性**，并没有把上述字段直接写入 `side+0x110`。它仍影响后续真实出伤/伤亡与骑士属性，不能从下一日战斗模拟输入中删除。其余四个写回字段只按偏移记录，不在本页擅自命名。 |

因此对优势**非 roll 分项**，这条刷新链把缺域缩小到具体的 MAA entry→Regiment→Character→Accolade 身份与称号来源 row、角色与 side 的其他 modifier、当前目标 Province/关系及将领状态。`0x23CC2B0` 是同次 materialization 的另一个重要更新，但不能把它写入的 entry damage/toughness 误称为 `aggregator_raw`。完整 side/commander 分项仍需原调用处对拍；此静态结论不意味着只有称号来源会影响优势。

现有 v3 **假想接战同帧模型**构造 local shell 后确实调用 `0x2308D50`，因而由原版在 local side 上执行上述刷新，并以原版总 helper 做等式门禁。它证明的是所给假想军队名单及目标在该帧的 local-shell 求值。现役 `active_combat_resume_inputs_v1` 虽有两 bucket 的有序 entry 和选中将领，却不暴露每个 MAA entry 的 `CRegiment+0x148` 当刻角色、其 accolade full ID/有效性、称号 row 来源身份及下一次刷新后状态；也未把假想接战的 local shell 当真实现役 Combat 的下一日状态。故不得把 v3 `resolved_dynamic` 拷为现役未来日非 roll 输入，也不得移除 `next_day_non_roll_advantage_sources` 缺域。

可行的下一步只读合同是在同一个 generation-valid CombatID/side、revision、日期与原始缓存生成 ordinal 上，按 entry 原序绑定 RegimentID、角色 full ID、称号 full ID、通过门的结果、来源 row count/selector/loaded identity，并在原版 `0x23CBCE0` **前后**取 `side+0x110` 的规范化 modifier 来源切片；另在 `0x23CC2B0` 前后记录六个 entry 字段及目标 Province 身份。任何身份、count、顺序或加载对象不一致整组 unavailable。应让现有受管原调用 observer 扩充有界复制点后做相邻日对拍；不得为了暂停查询主动重调这些 mutating helpers。

其中称号来源的全 row gate 与现有 v3/现役名单差异，已进一步收窄在[最小 typed 输入合同](active-accolade-roster-input-contract-2026-09-27.md)。
