# CK3 1.19.0.6：穆巴里尊 87 号兵团的 `25 → 26.25` 尚不能归因

结论：**未证实具体修正来源**。[配对存档身份](maa-regiment-87-save-name-identity-2026-09-27.md)确认 RegimentID `87` 属于 ArmyID `16777221`、owner CharacterID `31549`，兵种为 `mubarizun`（穆巴里尊），原版基础坚韧 `25`。第 11／21 日[暂停帧与 schedule 对照](maa-regiment-87-refresh-source-boundary-2026-09-27.md)均给出旧缓存 Q100000 `2,500,000`、原生直接求值和下一 schedule `2,625,000`。这精确等于 `25×1.05=26.25`，但旧缓存产生时刻和当帧 modifier 聚合读数没有被同时冻结，不能把等式叫因果链。

[独立缺口 sidecar](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_maa87_plus5_source_gap_v1.json) SHA-256 `805473E3ACB9DB0926CA3412E17CC8D74937DF5E05513A2F701585963E5F20D4` 与[只读投影工具](../../ck3_autonomous_player/tools/project_native_maa87_plus5_source_gap.py)核对两份原始 v3 回执、[存档类型 sidecar](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_maa87_save_identity_v1.json)及原版脚本 SHA。v3 的该团 `effective_stats` 只有最终六维值，没有任何 modifier 分量；其 `maa_type.key` 仍为 `null`，存档补证没有改写旧回执。

至少两种不同原版脚本来源都存在字面 `+0.05`，展示了仅由结果反推来源为何不成立：

| 静态候选，**未证该角色持有或生效** | 原版入口 | 本案缺的事实 |
| --- | --- | --- |
| 全军坚韧 | `common/modifiers/01_dlc_ep1_modifiers.txt:302–305` 的 `ep1_flavor_2020_both_modifier`：`army_toughness_mult = 0.05` | CharacterID `31549` 是否具有该 modifier，以及求值器是否把它读进本团。 |
| 重步兵坚韧 | `common/buildings/00_duchy_capital_buildings.txt:2058–2062` 的 `character_culture_modifier`，门槛 `better_blacksmith_buildings`，`heavy_infantry_toughness_mult = 0.05` | 本案文化／建筑／受益范围是否满足门槛，以及 class 动态 enum 的实际读数。 |

这些只是**两个可复核例子，不是候选全集**；哪怕某一脚本条件在存档中看似成立，若没有 owner/type/class/目标及原生 reader 返回值的同帧绑定，仍不能证明它贡献了本次 `125,000` 原始差额。`0x2C8D6A0` 的原生路径还可读固定 `MOD_MAA_TOUGHNESS_ADD`、`MOD_MAA_TOUGHNESS_MULT`、`MOD_ARMY_TOUGHNESS_MULT` 和两个 class 动态 enum；目标省份还可经 `0x2C8F8FF` 进入六维聚合。单独观察最终值不能排除附加值、多个修正相抵或不同读取时点。

最小后续被动探针：先由 `0x23D2CE0` 的 side entry 完整 RegimentID `87` 绑定本次 `CRegiment*`，再核对传给 `0x239CAE0` 的 target 指针确为 `ProvinceID 2633`，同时核对 CombatID、source date、side、ArmyID、owner 和 type/class；若直接 v3 路径绕过该入口，须另证 `CRegiment* →` 全 generation ID 的只读映射，**映射不成立即拒绝安装内层 hook**。在已绑定的同一主线程求值调用内，记录 `0x2C8D6A0` 的 class 行、`0x2940E80` 在 `0x2C8D8E0/0x2C8D902/0x2C8D92B` 与 `0x2C8D94D/0x2C8D97E` 的实际返回、`0x2C8F7B1` 应用前向量、`0x2C8F7B9` 应用后向量、`0x2C8F8FF` 目标省份贡献及最终 `0x239CAE0` 的 `Stats38`。旧缓存形成时、暂停直接求值时和下一 schedule 入口需分别取样；只做容量有界、默认关闭的被动记录，不调用原生 mutator。对象、目标或时序任一不一致就保留 RED，不做差额归因。
