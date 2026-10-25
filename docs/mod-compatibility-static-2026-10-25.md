# 仓库内 Mod 共用与冲突分析（2026-10-25）

本次覆盖仓库内 **17 个玩家产品 Mod、136 个两两组合**。按当前发布清单，**未发现产品之间必须二选一的同文件或普通数据库对象覆盖冲突**；但有一组明确的功能抵消，以及宗教目录、宗族归属方面的条件限制。不能据此将全部组合标成实机通过。

最需要注意的是：

- **肃清曼荼罗伪信 + 地产类型转换**：前者会把后者转换出的寺庙城寨改回城堡；想保留这种地产时，二者相关功能不能同时启用。
- **宗教礼仪融合 + 礼与道／宗族化密教**：可以共载，但当前融合目录未集成另外两者的新信条、教义。
- **宗族化密教 + 礼与道／两个廷臣创造器**：切学派可能被视为背教，创造器指定的“与我同家族”可能被后续归宗同步改变。
- **主 Mod + 白绮特供版**：命名空间独立，可以共载；会保留两套功能相近的廷臣创造入口。

## 分析基线与“兼容”的含义

源码基线：`6b360480a5c8d9e123d09a8a735e96f31991dc22`。分析机器为 `machine_id: pc-20260924rtuf-f11af23c08`，观察时间为 `2026-10-25T04:53:07Z`。这是仓库源码分析，不是目标机器的 CK3 安装、Workshop 载荷或运行版本鉴定。

范围取各产品**实际发布生产者的文件清单**，共 **1,602 个文件**；扣除每包各自的 descriptor 和封面后，比较了 **1,570 个运行文件**、**10,345 个顶层脚本块**及 **81,135 个按语言区分的本地化键**。公共钩子、原版覆盖与重点玩法交叉另作人工阅读。输入清单摘要、原始源码集合指纹和扫描边界见[机器可读证据](mod-compatibility-static-2026-10-25.json)。

本文的判断分为：

| 标记 | 含义 |
| --- | --- |
| S | 静态未发现直接冲突，可以作为组合候选；没有授予组合实机资格 |
| R | 可以共载，功能重复 |
| F | 有确定的功能抵消；须关闭或避开相应功能 |
| H | 有条件的玩法后果；需接受规则交互或避开该使用场景 |
| I | 可以共载，但新增内容没有完成相互集成 |

没有把“声明支持同一版本”“文件名带前缀”“单包测试成功”当成组合兼容证明。亦没有把正常的共享资源消耗、同日事件增多或预想的性能问题直接认定为冲突。

## 产品清单

文件数含 descriptor 与实际在清单中的封面，采用已有正式九语言模式；RRF 当前清单为中英双语。版本是本次读到的 descriptor 声明，不代表这些版本已经在同一 CK3 build 下完成合用验收。

| 简称 | Mod 与源码目录 | 产品版本 | 声明支持 CK3 | 发布文件数 | 清单依据 |
| --- | --- | --- | --- | ---: | --- |
| XAR | [琉焰卿的永恒轮回](../XenoAmess_s_Eternal_Recurrence/) | 1.0.2 | 1.20.0.3 | 86 | [主构建器](../tools/build_release.py)的目录清单、整文件排除和生产块投影 |
| ERVC | [白绮特供版](../Eternal_Recurrence_Vivhite_Courtier/) | 1.0.2 | 1.20.0.3 | 27 | [RUNTIME_FILES](../tools/build_vivhite_release.py) |
| OX | [牛来](../ox_here/) | 1.0.3 | 1.20.0.3 | 22 | [RUNTIME_FILES](../tools/build_ox_here_release.py) |
| MRM | [肃清曼荼罗伪信](../mod_remove_mandala/) | 1.0.1 | 1.20.0.3 | 15 | [RUNTIME_FILES](../tools/build_remove_mandala_release.py) |
| XQOL | [XenoAmess 的体验优化](../mod_xenoamess_quality_of_life/) | 1.1.1 | 1.20.0.4 | 27 | [RUNTIME_FILES](../tools/build_xenoamess_quality_of_life_release.py) |
| RMTM | [重整河山](../mod_reclaim_the_motherland/) | 0.4.1 | 1.20.0.4 | 36 | [RUNTIME_FILES](../tools/build_reclaim_the_motherland_release.py) |
| TED | [驱策朝贡国](../mod_tributary_expansion_directives/) | 1.0.1 | 1.20.0.4 | 16 | [RUNTIME_FILES](../tools/build_tributary_expansion_directives_release.py) |
| XCCC | [天朝经商与贪腐框架维护版](../mod_celestial_commerce_corruption/) | 1.0.1 | 1.20.0.3 | 22 | [RUNTIME_FILES](../tools/build_celestial_commerce_corruption_release.py) |
| AUB | [自动升级建筑维护版](../mod_auto_upgrade_buildings/) | 4.0.3 | 1.20.0.3 | 17 | [RUNTIME_FILES](../tools/build_auto_upgrade_buildings_release.py) |
| DJC | [公国／王国／帝国法理征服维护版](../mod_de_jure_conquest/) | 1.0.0 | 1.20.* | 16 | [product.py](../mod_de_jure_conquest/tools/product.py) |
| CHT | [地产类型转换维护版](../mod_change_holding_types/) | 1.0.0 | 1.20.* | 17 | [runtime_files(True)](../mod_change_holding_types/tools/product.py) |
| SXAD | [超人强：越超人越强](../mod_superman_qiang/) | 1.2.0 | 1.20.* | 35 | [product.py](../mod_superman_qiang/tools/product.py) |
| ZG361 | [天朝特色 361 制官员绩效考核](../mod_zhongguo_style/) | 0.4.0 | 1.20.0.4 | 1,034 | [发布目录清单](../tools/build_mod_zhongguo_style_release.py) |
| LYD | [礼与道](../mod_li_yu_dao/) | 0.1.2 | 1.20.* | 83 | [collect_runtime_files](../mod_li_yu_dao/tools/build_release.py)及限定的 lyd helper family |
| XALW | [活武器](../mod_living_artifacts/) | 0.1.0 | 1.20.* | 57 | [runtime-inventory.json](../mod_living_artifacts/docs/runtime-inventory.json) |
| DES | [宗族化密教](../mod_dynastic_esotericism/) | 0.1.0 | 1.20.* | 25 | [ReleaseProduct](../mod_dynastic_esotericism/tools/src/main/java/org/xar/ck3/dynastic/release/ReleaseProduct.java)的 RELEASE_LOCALIZATION 模式 |
| RRF | [宗教礼仪融合](../mod_religious_ritual_fusion/) | 0.1.0 | 1.20.0.* | 67 | [product.json](../mod_religious_ritual_fusion/tools/product.json) + [generated-files.json](../mod_religious_ritual_fusion/catalog/generated-files.json) |

`ck3_autonomous_player/mod_bridge/` 是声明支持 1.19.0.6 的开发桥，不列为第 18 个玩家产品，也不建议将它加入普通播放集。各类 `fixtures/`、验收 Mod、历史证据包、构建工具、家徽网页编辑器和游戏参考目录均不参与产品两两矩阵。SXAD 当前为 **35 文件**，不能沿用旧指南中的 22 文件数字。

## 两两组合矩阵

只列上三角；下三角的“—”是对称项省略。**S 均表示静态候选，不表示长期游戏、性能、存档或组合实机已通过。**

| 组合 | XAR | ERVC | OX | MRM | XQOL | RMTM | TED | XCCC | AUB | DJC | CHT | SXAD | ZG361 | LYD | XALW | DES | RRF |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XAR | — | R | S | S | S | S | S | S | S | S | S | S | S | S | S | H | S |
| ERVC | — | — | S | S | S | S | S | S | S | S | S | S | S | S | S | H | S |
| OX | — | — | — | S | S | S | S | S | S | S | S | S | S | S | S | S | S |
| MRM | — | — | — | — | S | S | S | S | S | S | F | S | S | S | S | S | S |
| XQOL | — | — | — | — | — | S | S | S | S | S | S | S | S | S | S | S | S |
| RMTM | — | — | — | — | — | — | S | S | S | S | S | S | S | S | S | S | S |
| TED | — | — | — | — | — | — | — | S | S | S | S | S | S | S | S | S | S |
| XCCC | — | — | — | — | — | — | — | — | S | S | S | S | S | S | S | S | S |
| AUB | — | — | — | — | — | — | — | — | — | S | S | S | S | S | S | S | S |
| DJC | — | — | — | — | — | — | — | — | — | — | S | S | S | S | S | S | S |
| CHT | — | — | — | — | — | — | — | — | — | — | — | S | S | S | S | S | S |
| SXAD | — | — | — | — | — | — | — | — | — | — | — | — | S | S | S | S | S |
| ZG361 | — | — | — | — | — | — | — | — | — | — | — | — | — | S | S | S | S |
| LYD | — | — | — | — | — | — | — | — | — | — | — | — | — | — | S | H | I |
| XALW | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | S | S |
| DES | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | I |
| RRF | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

上表 136 对中，129 对未发现直接静态冲突，另有 1 对功能重复、1 对功能抵消、3 对条件玩法交互、2 对目录集成缺口。矩阵只描述两两关系；多 Mod 同时运行时的时序和资源叠加仍需组合验收。

## 有明确证据的限制

### F：肃清曼荼罗伪信 × 地产类型转换

CHT 提供 `ch_convert_holding_to_temple_citadel_decision`：[决议定义](../mod_change_holding_types/common/decisions/00_convert_holdings_decisions.txt#L357)最终调用[转换效果](../mod_change_holding_types/common/scripted_effects/cht_conversion_effects.txt#L58)，将地产变成 `temple_citadel_holding`。

MRM 的[全球清扫效果](../mod_remove_mandala/common/scripted_effects/mrm_effects.txt#L11)则遍历省份，把这种地产重新改为 `castle_holding`。它在[开局立即和两天后](../mod_remove_mandala/common/on_action/mrm_on_actions.txt#L26)清扫，之后经[年度分派](../mod_remove_mandala/common/on_action/mrm_on_actions.txt#L50)及[mrm.6](../mod_remove_mandala/events/mrm_events.txt#L43)重复执行；每月政府扫描与年度地产扫描应分开理解。

因此，两包能加载，但启用 MRM 默认规则后，CHT 这一转换的成果会在后续扫描中被撤销，造成已支付成本失去预期用途。**调整加载顺序不能解决。** 保留寺庙城寨玩法时应将 MRM 游戏规则设为 `mrm_disabled`（禁用），或不同时使用 MRM；需要 MRM 时可以继续使用 CHT 的其他转换，避开寺庙城寨目标。规则默认值见[mrm_game_rules.txt](../mod_remove_mandala/common/game_rules/mrm_game_rules.txt#L6)。

### I：宗教礼仪融合 × 礼与道

RRF 的[CatalogReader](../mod_religious_ritual_fusion/tools/src/main/java/org/xar/ck3/rrf/CatalogReader.java#L25)从指定原版 `game` 目录读取信条、教义和约束，当前生成目录不含 `lyd_*`。其[生产白名单校验](../mod_religious_ritual_fusion/common/scripted_effects/rrf_catalog_dispatch_00.txt#L64)会将未知的已选信条标为 `rrf_invalid_selection`；[提交条件](../mod_religious_ritual_fusion/common/scripted_triggers/rrf_draft_triggers.txt#L38)拒绝该状态。

LYD 的[36 学派礼仪](../mod_li_yu_dao/common/religion/rite_types/lyd_rites.txt#L7)实际使用 `lyd_tenet_*` 新核心。RRF 虽然会[从真实来源礼仪枚举核心](../mod_religious_ritual_fusion/common/scripted_effects/rrf_draft_effects.txt#L71)，也不能因此认为这些核心已受支持：把它们选入最终组合会被白名单拒绝。

可以保留 LYD 的正常学派玩法，并让 RRF 处理其目录已覆盖的原版内容；不能承诺 RRF 能融合 LYD 新核心。完整集成需要扩展共享目录生产链及其来源约束，单纯把 RRF 放到后面不生效。

### I：宗教礼仪融合 × 宗族化密教

RRF 当前目录也没有 `des_doctrine_none`、`des_doctrine_dynastic`。其教义候选和初始选择来自生成目录中的已知项，不能用于选择 DES 的宗族教义。未知项校验同见[rrf_catalog_dispatch_00.txt](../mod_religious_ritual_fusion/common/scripted_effects/rrf_catalog_dispatch_00.txt#L65)。

这不表示 DES 一加载就阻断 RRF 的全部普通融合：RRF 没有将每一种外来教义无条件加入已选列表。但**新 Faith／Rite 是否保留宗族化教义、如何建立或恢复绑定**没有完成双方集成。RRF 的[完成链](../mod_religious_ritual_fusion/common/scripted_effects/rrf_completion_effects.txt#L10)还会切换角色礼仪，可能进入 DES 的离宗／背教处理。需要保留宗族身份时，暂不把融合当作透明迁移手段。

### H：宗族化密教 × 礼与道

LYD 的[切学派效果](../mod_li_yu_dao/common/scripted_effects/lyd_school_effects.txt#L2)直接 `set_character_rite`。DES 的[背教判定](../mod_dynastic_esotericism/common/scripted_triggers/des_dynastic_triggers.txt#L15)比较的是**具体 Rite 身份**，同一个 Faith 不构成豁免；[礼仪变化回调](../mod_dynastic_esotericism/common/on_action/des_on_actions.txt#L6)会进入同步。

前提是角色已经属于有效绑定的宗族，且该绑定 Rite 启用了宗族化教义。在此前提下，即使仍属儒家 Faith，改用另一学派 Rite 也可能成为 DES 意义上的背教者。**这属于两套玩法规则共同生效，不是加载报错，也不会因为加载顺序而消失。**

没有有效宗族化绑定的普通学派转换，不因安装 DES 就自动变成背教。若希望学派可自由转换，不要同时对该玩法启用要求固定 Rite 的宗族绑定；若接受 DES 的严格规则，则需把换学派视为有宗族后果的选择。

### H：宗族化密教 × 主 Mod／白绮廷臣创造器

主 Mod 的[人物创建](../XenoAmess_s_Eternal_Recurrence/common/scripted_effects/xar_courtier_creator_effects.txt#L265)读取所选 Faith／Rite，随后在启用“与我同家族”时[设置玩家 House](../XenoAmess_s_Eternal_Recurrence/common/scripted_effects/xar_courtier_creator_effects.txt#L322)。白绮版也有[同一功能的独立实现](../Eternal_Recurrence_Vivhite_Courtier/common/scripted_effects/ervc_courtier_creator_effects.txt#L323)。

DES 会[把宗族化礼仪的信徒归入绑定宗族](../mod_dynastic_esotericism/common/scripted_effects/des_character_effects.txt#L13)，并对[新人物安排延后一天的同步](../mod_dynastic_esotericism/common/on_action/des_on_actions.txt#L52)。因此，若创造出的廷臣所信 Rite 的绑定宗族与玩家宗族不同，“与我同家族”可能在稍后被归宗同步改变。

需要稳定保持玩家 House 时，应选择与该要求一致的礼仪／绑定，或避开该组合配置。这不是创建器的 ID 冲突，也不等于 DES 会重写整棵家谱。创建当刻读回成功，亦不能证明同步后身份保持。

### R：主 Mod × 白绮特供版

主 Mod 的[xar_courtier_creator_decision](../XenoAmess_s_Eternal_Recurrence/common/decisions/xar_decisions.txt#L35)和白绮版的[ervc_courtier_creator_decision](../Eternal_Recurrence_Vivhite_Courtier/common/decisions/ervc_courtier_creator_decisions.txt#L1)是不同对象；GUI 注册、局部变量、flag 分别使用 `xar/xa` 和 `ervc`。

两包可以同时保留两个入口，白绮版也不以主 Mod 为强制依赖。若只需要一套廷臣创造器，按所需功能选择其一即可；无需为了规避不存在的同 ID 覆盖而调整顺序。

## 已检查、容易误判为冲突的组合

| 组合 | 静态判断与依据 |
| --- | --- |
| 主 Mod + 活武器 | 都接入建筑完成和死亡，但公共入口仅追加私有 on_action；契约进度与活武器状态使用不同变量。没有发现互相覆盖 effect 或写对方状态。 |
| 法理征服 + 体验优化 | `on_war_started` 两边均追加私有钩子。前者处理自己的法理大战，后者在玩家为主防守方且开关开启时延后一日召援，属于行为叠加。见[greatwar.txt](../mod_de_jure_conquest/common/on_action/greatwar.txt#L2)、[xqol_on_actions.txt](../mod_xenoamess_quality_of_life/common/on_action/xqol_on_actions.txt#L31)。 |
| 法理征服 + 驱策朝贡国 | 前者只识别三种 `*_de_jure_greatwar` CB；后者使用 `ted_directed_county_expansion_cb`。未发现朝贡战争被误判为法理大战的条件。见[CB 过滤](../mod_de_jure_conquest/common/on_action/greatwar.txt#L12)、[定向宣战效果](../mod_tributary_expansion_directives/common/scripted_effects/ted_tributary_expansion_effects.txt#L35)。 |
| 自动升级建筑 + 地产类型转换 | 未发现文件或 ID 覆盖。AUB 通过[add_building](../mod_auto_upgrade_buildings/events/auto_build.txt#L43)即时升级，不能误报为“自动启动施工后永久挡住转换”；CHT 的[在建检查](../mod_change_holding_types/common/scripted_triggers/00_convert_holdings_scripted_triggers.txt#L9)仍正常约束转换。 |
| 天朝 361 + 体验优化／经商贪腐／重整河山 | 涉及同一类天朝角色，但各自处理考核、任命、政府经济或王朝外交，当前未发现同对象覆盖。任命资格变化会改变可用候选，属于共同玩法环境；官职与政治变化的业务时序仍需实机组合检查。 |
| 肃清曼荼罗 + 礼与道／宗族化／礼仪融合 | MRM 改的是政府与地产，没有删除这些包的 Faith、Rite 或信条。名称中的“伪信”不能作为它清除其他宗教 Mod 的证据。 |
| 牛来 + 两个廷臣创造器／超人强 | 新增对象各自命名。招募、恋人关系与性行为统计是不同路径，不能把招募本身等同于已触发超人强经验。后续真实性行为接入可叠加，但没有因此发现冲突。 |

### 共享 on_action 的完整交叉清单

[现有钩子机制笔记](on_actions-events.md)区分了字段覆盖与 `on_actions` 列表扩展。本次这些共享入口均只向列表加入私有钩子，未在公共入口争抢 `effect`／`trigger` 字段；不能因搜到同名 hook 就判定不兼容。

| 公共入口 | 本次共同使用者 |
| --- | --- |
| on_game_start_after_lobby | XAR、MRM、XQOL、RMTM、XALW、DES |
| on_death | XAR、AUB、RMTM、LYD、XALW、DES |
| on_building_completed | XAR、XALW |
| on_war_started | DJC、XQOL |
| random_yearly_everyone_pulse | ZG361、XALW、DES |
| yearly_global_pulse | MRM、DES |
| yearly_playable_pulse | XQOL、ZG361 |

入口原件可对照[XAR](../XenoAmess_s_Eternal_Recurrence/common/on_action/eternal_recurrence_on_actions.txt)、[MRM](../mod_remove_mandala/common/on_action/mrm_on_actions.txt)、[XQOL](../mod_xenoamess_quality_of_life/common/on_action/xqol_on_actions.txt)、[RMTM](../mod_reclaim_the_motherland/common/on_action/rmtm_on_actions.txt)、[AUB](../mod_auto_upgrade_buildings/common/on_action/aub_on_actions.txt)、[DJC](../mod_de_jure_conquest/common/on_action/greatwar.txt)、[LYD](../mod_li_yu_dao/common/on_action/lyd_c3_lifecycle_on_actions.txt)、[XALW core](../mod_living_artifacts/common/on_action/xalw_core.txt)、[XALW content](../mod_living_artifacts/common/on_action/xalw_content.txt)、[DES](../mod_dynastic_esotericism/common/on_action/des_on_actions.txt)、[ZG361](../mod_zhongguo_style/common/on_action/zg361_on_actions.txt)。

这只说明钩子注册方式没有发现覆盖；不同私有钩子在同一游戏日的执行顺序、跨日后态及大规模角色遍历性能，均没有在本次静态分析中验收。

## 对第三方 Mod 最敏感的覆盖点

以下是**本仓产品对原版的覆盖接口**，不是已经发现它们彼此冲突。加入外部 Mod 时，应同时比较文件路径与对象 ID；不同文件名依然可能重定义同一个原版对象。

| 产品 | 需要重点比对的接口 | 当前仓内结论 |
| --- | --- | --- |
| XAR | [gui/window_succession_event.gui](../XenoAmess_s_Eternal_Recurrence/gui/window_succession_event.gui)，原版继承窗口的整文件投影 | 其他 16 包没有同路径文件；外部继承界面改造需合并注入 |
| XQOL | [succession_appointment](../mod_xenoamess_quality_of_life/common/succession_appointment/) 中 admin_governor、celestial_civic_governor、celestial_military_governor、meritocratic_civic_governor、meritocratic_military_governor | 其他包没有第二定义；外部任命资格改造是重点 |
| RMTM | [tgp_chaos_shattering_effect](../mod_reclaim_the_motherland/common/scripted_effects/zz_rmtm_vanilla_overrides.txt)、[tgp_has_access_to_ministry_trigger](../mod_reclaim_the_motherland/common/scripted_triggers/zz_rmtm_ministry_override.txt)、[situation_dynastic_cycle_claim_mandate_decision](../mod_reclaim_the_motherland/common/decisions/dlc_decisions/tgp/zz_rmtm_mandate_override.txt)、[offer_vassalization_interaction](../mod_reclaim_the_motherland/common/character_interactions/zz_rmtm_offer_vassalization.txt)及[外交评分修正](../mod_reclaim_the_motherland/common/scripted_modifiers/zz_rmtm_offer_vassalization_modifiers.txt) | 当前没有另一包重定义这些对象；仅改文件前缀不能使覆盖合并 |
| XCCC | [celestial_government](../mod_celestial_commerce_corruption/common/governments/xccc_celestial_government.txt)、[celestial_obligations](../mod_celestial_commerce_corruption/common/subject_contracts/contracts/xccc_celestial_obligations.txt) | 当前无第二定义；外部天朝政府／契约改造需核查 |
| SXAD | [四个原版性行为效果](../mod_superman_qiang/tools/product.py#L24)：had_sex_with_effect、had_sex_with_unknown_effect、rakish_brothel_night_effect、mandala_story_creation_aspect_get_kids_effect；另有七个 zz_sxad 原版事件覆盖 | 当前无第二定义；外部性行为与这七个事件的改造需合并接入 |
| XALW | [正式清单](../mod_living_artifacts/docs/runtime-inventory.json)中的 26 个原版路径：宴会活动、18 个生活方式技能树、单挑效果、3 个秘密文件、3 个压力事件文件；另有分片后的原版单挑效果定义 | 当前没有其他包覆盖相同路径或扫描到同名非钩子对象；对外部宴会／技能树／秘密／压力／单挑 Mod 的敏感面较广 |
| DES | [faith_conversion.0003](../mod_dynastic_esotericism/events/des_stock_family_conversion_events.txt#L22)、同文件的 faith_conversion_0003_valid_character，事件声明 id_override_priority=1 | 当前无第二定义；不能把所有 des_ 文件概括成“纯新增、完全不覆盖原版” |
| LYD、RRF | LYD 新 Rite／信条与 RRF 固定生成目录之间的接口 | 没有直接覆盖，但已有上述集成缺口 |
| ERVC、OX、MRM、TED、AUB、DJC、ZG361 | 以各自新增对象和钩子扩展为主；各自对原版政府、CB、建筑等对象仍有语义依赖 | 在本次产品集合内未发现直接覆盖冲突；不能外推为与任意外部 Mod 兼容 |

全部 17 个产品 descriptor 均未声明 `replace_path` 或 `dependencies`。没有 descriptor 依赖不等于没有原版／DLC／游戏版本前提。维护版与其上游旧版不在本次矩阵范围内，也不能把维护版之间的 S 外推为“维护版 + 上游原版”可同时使用。

## 共用选择与后续验证

日常播放集可以从矩阵中的 S 组合选择，并按需要加入 R 类重复入口。以目前源码看，没有为了这 17 包**互相覆盖文件或对象**而规定统一加载顺序的证据；不应编造一个排序来承诺修复 F／H／I。

需要寺庙城寨时避开 MRM 的对应清扫；需要稳定宗族／House 身份时认真处理 DES 的礼仪绑定；需要融合 LYD 信条或 DES 教义时，当前先视为未支持的集成需求。若要把这些条件组合升级为实机兼容，优先验证下列实际后态：

1. MRM + CHT：转换后跨开局延迟／年度扫描，读回地产类型和支付结果；再验证禁用 MRM 时结果保持。
2. DES + LYD：有、无有效宗族绑定各切一次学派，读回 Rite、Dynasty／House、背教与犯罪理由。
3. DES + XAR／ERVC：用相同与不同绑定宗族的 Rite 创造同家族廷臣，次日及维护后读回实际 House。
4. RRF + LYD／DES：分别验证新增核心的拒绝原因、教义候选，以及成功融合后的教义／宗族状态与保存冷重载。
5. 其他 S 组合：针对同时涉及的开局、战争、建筑、死亡和官职变更做业务读回，并保存、退出、冷重载；单纯加载到菜单不足以证明兼容。

这些是针对本次已识别交互的验证建议，**本次没有执行**。未来实机沿用[公共验收入口](ck3-mod-upgrade-fast-validation.md)，按目标机器重新核实际游戏 build、运行来源、离线状态与容量。

## 方法、已执行检查与剩余边界

本次只读调用既有发布清单／投影函数，未执行正式构建或部署。主包按 `tools/build_release.py` 排除验收专用文件、剥离 `XAR_ACCEPTANCE_ONLY` 段并展开 `XAR_RELEASE_ONLY` 行；LYD 排除空历史占位，DES 采用正式语言模式，RRF 合并基础与生成目录清单。随后以一次性 Java 分析器比较相对运行路径（大小写归一）、去注释与字符串分词后的顶层对象，以及按语言分组的本地化 key。数据库类别内的子目录统一比较，事件文件中的内联 scripted trigger／effect 也计入相应全局类别；公共 on_action、GUI 命名空间和重点机制人工复核。

结果为：运行文件路径交集 0；同语言本地化 key 的跨产品交集 0；检出的跨产品顶层对象重名仅上述 7 个公共 on_action，人工核为列表扩展。这个扫描不是完整 CK3 parser，没有覆盖所有嵌套数据库语义或证明每一条原版引用都有效；S 因而只代表在声明检查范围内未发现直接冲突。

本次未启动或连接 CK3／Steam、未检查订阅缓存、未修改 Mod 源码与加载顺序；没有新增组合实机 PASS。原版对象的升级兼容性、已有存档迁移、多人游戏以及多个 Mod 合开时的运行性能仍未验。旧版专题的历史通过不作为本次组合验收。

本任务仅在已解析为 D 卷的仓库内生成小型分析材料，记录采用[存储策略 1.0.0](storage-retention-policy.md)。本机完整资产／配额与并发预留台账未取得，因此不授予重型写入或全机存储清理通过；没有删除其他任务资产。临时分析器与输入展开表在完成检查后回收，保留本报告和精简 JSON 摘要，按 record 类别于 180 天复核；如相关产品先发生覆盖或清单变化，应提前重做受影响的静态结论。
