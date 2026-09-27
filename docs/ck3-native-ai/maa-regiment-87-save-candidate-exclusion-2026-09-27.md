# CK3 1.19.0.6：兵团 87 两个 `+5%` 候选在配对存档中的排除边界

本页接续[兵团 87 双类型入口审计](maa-regiment-87-dual-type-source-boundary-2026-09-27.md)。对第 11／21 日配对原生存档、Rakaly 0.8.19 解码文本、冻结 v3 回执、原版脚本及 SHA-256 为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 的 `ck3.exe` 作只读核对。**两项曾以算术吻合而列出的脚本示例，在两份来源存档中都没有对应的持久化实例；这收窄了候选，不证明当前 `26.25` 的实际修正来源。**

可重建的[只读投影](../../ck3_autonomous_player/tools/project_native_maa87_save_candidate_exclusion.py)与[冻结机器边界](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_maa87_save_candidate_exclusion_v1.json)核对两份原始 save SHA、解码文本 SHA、v3 SHA、87／16777221／31549／2633 身份、三个原版脚本文件和 exact EXE。机器边界 SHA-256：`EB4D06E60882ACD66DBC3F15C4E342467806725054FBB3827C7775BAB56C347B`。没有启动 CK3，也没有新增原生运行时读数。

| 曾列候选 | 原版脚本与入口 | 第 11／21 日存档实证 | 可下的结论 |
| --- | --- | --- | --- |
| `ep1_flavor_2020_both_modifier` 的 `army_toughness_mult=0.05` | `common/modifiers/01_dlc_ep1_modifiers.txt:302–306`；`events/dlc/ep1/ep1_flavor_events.txt:4181–4183` 是 `add_character_modifier`、期限 5 年 | 两份解码存档全局均 **0** 次出现该 modifier key；Army 16777221 的 owner CharacterID 31549 记录也没有它。同文件仍有 224／225 个 `timed_modifier` 块，说明解码文本确实保留这类记录。 | **排除两份来源存档中的这一项持久化人物修正实例。** 不推出所有可能的 `MOD_ARMY_TOUGHNESS_MULT` 值为零，也不以存档缺席代替暂停帧原生返回值。 |
| `blacksmiths_02` 在 `better_blacksmith_buildings` 参数下的 `heavy_infantry_toughness_mult=0.05` | `common/buildings/00_duchy_capital_buildings.txt:2032,2058–2063` 的 `character_culture_modifier` | 两份解码存档全局均 **0** 次出现 `type="blacksmiths_02"`；同一建筑链的 `blacksmiths_01` 均出现 **1** 次，说明建筑等级被保存且此处无第二级。 | **排除来源存档里由该具体二级建筑产生的修正实例。** 不能排除其他建筑、文化参数、职业兵种或目标省份提供相同数值。 |

这个排除限定在**原始存档的序列化状态**。冻结 v3 回执与来源 save 有配对 SHA，且第 11／21 日两份 v3 都将同一兵团 87 列在 Army 16777221、owner 31549、目标 Province 2633，有效坚韧 Q100000 原始值 `2,625,000`。但回执没有从加载、暂停到求值的逐项修正值或事件写入追踪；因此不能把上述存档缺席升级为“同帧原生 enum 返回零”，也不能解释旧缓存 `2,500,000` 何时、为何形成。`25×1.05=26.25` 仍只是算术见证。

具体剩余缺口保持分层：固定 enum `0x1AC/0x1AD/0x1A7` 的实际返回未采；有效属性 type `CRegiment+0x118` 与 counter type `+0x18` 是否同指针、有效属性 class 行 `+0x2E/+0x3A` 的动态 enum 未采；由 `CRegiment+0x28` 解析出的来源军队、其遍历对象和目标 Province 的六维附加向量未采。保存状态能排除两个特定脚本实例，不能给这些槽填零或绑定新来源。

恢复实机门禁后，最小被动同帧采集沿用[双类型审计的合同](maa-regiment-87-dual-type-source-boundary-2026-09-27.md)：只筛全 generation 的兵团 87、Combat 16777218、Army 16777221、目标 2633 和来源日；在旧 entry 缓存形成、暂停直接求值、下一 schedule 三处记录两个 type 指针及有效 class 行、基础坚韧、三个固定和两个动态 enum 的 `0x2940E80` 返回、军队来源对象、`0x23C2DF0` 前后中间坚韧及目标向量。同步观察人物 timed modifier、文化建筑生效状态与求值间是否有写入。只有相同对象、线程、目标和时点的原生读数才能回答 `25→26.25` 的归因；仅有后两次值只能解释当前值的组成，不能解释旧缓存差额。

复核时用主工作树已验证有依赖的 `tools/.venv/Scripts/python.exe` 运行上述投影的 `--help`，然后传 `--exe`、`--game-root`、`--identity-sidecar`、`--day11-v3`、`--day21-v3` 和 `--check-sidecar`，所用绝对来源路径记录在[配对存档身份 sidecar](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_maa87_save_identity_v1.json)及[冻结 v3 门禁](maa-regiment-87-human-identity-gate-2026-09-27.md)。该检查只读，无游戏进程连接。
