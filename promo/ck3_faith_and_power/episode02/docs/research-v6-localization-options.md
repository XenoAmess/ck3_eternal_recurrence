# V6 官方简中核对：活动配置、旅行与相关技能

本包只核对当前安装的 CK3 1.20.0.4 原版文件。`machine_id: 4-8e1c2f1861`；机器身份于 `2026-10-22T02:10:31Z` 重新执行 `tools/ck3_live_run_id.py machine` 读回。具体源文件读取时间、SHA-256、行号及间接引用链见[知识 JSON](knowledge/pilgrimage-v6-localization-options-12004.json)。未启动游戏，不将文件读取等同于当前人物实际菜单或已加载本地化。

## 导演稿必须落实的更正

- 界面栏目确实是“忠诚”和“排场”。不能因为英文 `fidelity` 或源码注释 `LEVEL OF DEVOTION` 就改叫“虔诚度”“奉献等级”。“虔敬程度”“投入档”可用于解释，不能冒充原版栏目名。
- `reflection_intent` 正式名为“深思熟虑”。它与“忠诚”栏的同名选项是两个对象。旁白应说“意图栏的‘深思熟虑’”和“‘忠诚’栏的‘深思熟虑’”；“反省”是动作说明，不另造一个“反省”意图名称。
- “义不容辞／朝圣者／深思熟虑”“朴素／适度／讲究／盛况空前”“行善／热忱／娱乐”都与当前原件一致。名称存在不等于当前人物四种意图都可选，第四候选集合的资格仍按既有研究边界处理。
- `erudition_legacy_track_name` 为“学识传承”，第四项 `erudition_legacy_4_name` 为“真正信徒”；“博学传承”应改。`ep2_activities_legacy_track_name` 为“活动传承”，第一项为“踏过圣路”。泛指 `dynasty_perk` 时官方概念是“宗族传承”。
- `travel_leader_court_position` 默认为“旅队主管”，不能写成“旅行主管”。`court_physician_court_position` 默认为“私人医生”，不能把“宫廷医师”当作这个职位的正式名称。
- 上述两个职位有天朝情境名称。独立、帝国及以上且符合天朝标记的分支为“桥道顿递使／太医”；非独立、帝国及以下且符合天朝标记的分支为“前驱官／医学博士”。片中西欧模型沿用默认名称，跨政体画面按实际分支核对。
- `entourage` 的概念名是“旅团”，`cultural_acceptance` 是“文化接受度”，`perk` 是“技能”。“随行”可作普通动词；字幕标识对应游戏对象时用正式名。“文化接纳度”应改。
- “准备充分”“复越高山”“旅行规划”均确为对应技能名称。29 项旅行选项的既有 `name_zh` 逐项与本轮原件一致。

## 栏目、选项与中文描述的边界

活动定义将 `pilgrimage_option_fidelity` 和 `pilgrimage_option_pomp` 作为分类键。原版 GUI 分别用 `ActivityOptionCategory.GetName` 和 `ActivityOption.GetName` 读取分类与选项名；特殊类型横幅直接读取已选项名。名称核对因此不能只搜同义词。

“不带任何你宫廷的人出发”“带上保镖或优秀的骑士”“还带上仆人和虔诚的扈从”“每个感兴趣的角色都会加入”是排场描述中的不同语句，**不是另一组已核实的独立菜单名称**。描述还带人数脚本值和对象占位；本包保存原始模板，不把未渲染的模板当作最终画面文字，也不由描述保证实际旅团精确人数。

“带上医疗设备”有独立的“（仅抵消瘟疫）”富文本后缀，基础选项名仍是“带上医疗设备”。栏目、选项名、描述、后缀分别保存，避免把描述里的解释替换成菜单名称。

本轮对安装目录 `localization/simp_chinese` 的 1250 个 YML 做目标 key 定义检查；本包 86 个不同目标 key 均只有一处定义。87 条记录包含一条为了间接引用示例重复展示的“斥候”；其中 4 条为动态描述模板，另有富文本片段。未发现目标 key 重定义冲突，不推论全游戏所有 key 都没有冲突。

## 间接引用的处理

原始 `$KEY$` 与解析后的文本分别保存，引用链每一层带源 SHA 和行号。例如 `hire_travel_leader_decision` 的“寻找$travel_leader_court_position$”解析成“寻找旅队主管”；`leisurely_option_effect` 的“$leisurely_option$”解析成“悠闲之旅”。这里说明的是静态字面引用，职位运行时情境覆盖另判。

`[GetTrait(...)]`、`[EmptyScope.ScriptValue(...)]` 和游戏概念链接是运行时模板，不用字符串替换假装取得人物最终名称、人数或值。本包没有把这些模板列为已核实的完整最终显示名称。

以下表格由知识 JSON 的已核对记录生成。`Lxx:行号` 对应文末精确文件清单；所有名称均保留源 key，读者可直接重查本地化原件。

## 1. 活动配置与意图

| key | 原件文本／解析后文本 | 来源 |
| --- | --- | --- |
| `activity_pilgrimage` | 朝圣 | L01:3 |
| `pilgrimage_option_fidelity` | 忠诚 | L01:114 |
| `pilgrimage_option_pomp` | 排场 | L01:122 |
| `pilgrimage_type_pious` | 虔诚朝圣 | L01:107 |
| `pilgrimage_type_worldly` | 世俗朝圣 | L01:109 |
| `pilgrimage_type_hajj` | 朝觐 | L01:111 |
| `pilgrimage_fidelity_obligatory` | 义不容辞 | L01:115 |
| `pilgrimage_fidelity_pilgrim` | 朝圣者 | L01:117 |
| `pilgrimage_fidelity_contemplative` | 深思熟虑 | L01:119 |
| `pilgrimage_pomp_humble` | 朴素 | L01:123 |
| `pilgrimage_pomp_appropriate` | 适度 | L01:125 |
| `pilgrimage_pomp_ceremonial` | 讲究 | L01:127 |
| `pilgrimage_pomp_throng` | 盛况空前 | L01:129 |
| `reflection_intent` | 深思熟虑 | L01:133 |
| `altruism_intent` | 行善 | L02:18 |
| `zealot_intent` | 热忱 | L01:136 |
| `reduce_stress_intent` | 娱乐 | L02:3 |

## 2. 全部 29 项旅行选项

| key | 原件文本／解析后文本 | 来源 |
| --- | --- | --- |
| `adventurers_scout_for_talent_option` | 搜索人才 | L03:92 |
| `adventurers_make_local_deals_option` | 高风险交易 | L03:89 |
| `adventurers_search_for_secrets_option` | 搜寻秘密 | L03:75 |
| `adventurers_encourage_relationships_option` | 鼓励关系 | L03:69 |
| `adventurers_gather_inspiration_option` | 搜集灵感 | L03:84 |
| `adventurers_proselytize_zealously_option` | 向当地人传教 | L03:79 |
| `adventurers_forward_scouts_option` | 斥候 | L04:669 |
| `purchase_rough_terrain_gear_option` | 购买探路者装备 | L03:63 |
| `purchase_desert_gear_option` | 购买旱地探索者物品 | L03:65 |
| `purchase_forest_gear_option` | 购买荒野工具包 | L03:67 |
| `experienced_captains_option` | 雇佣经验丰富的船长 | L03:8 |
| `hire_experienced_mercenaries_option` | 雇佣佣兵卫队 | L03:12 |
| `hire_jungle_expert_option` | 雇佣丛林追猎者 | L03:17 |
| `hire_mountaineer_option` | 雇佣登山者 | L03:21 |
| `hire_forder_option` | 雇佣涉水者 | L03:25 |
| `hire_desert_warrior_option` | 雇佣沙漠战士 | L03:34 |
| `hire_rough_terrain_expert_option` | 雇佣森林向导 | L03:30 |
| `court_physician_option` | 带上医疗设备 | L03:38 |
| `cultural_ambassador_option` | 雇佣文化大使 | L03:42 |
| `hire_allied_mercenaries_option` | 私人军队 | L03:142 |
| `appeasement_option` | 安抚 | L03:144 |
| `leisurely_option` | 悠闲之旅 | L03:146 |
| `tutor_child_option` | 教学之旅 | L03:150 |
| `fancy_mounts_option` | 优良坐骑 | L03:46 |
| `military_recruits_option` | 训练骑士 | L03:48 |
| `superior_armaments_option` | 优良军备 | L03:57 |
| `anxious_option` | 加快脚步 | L03:59 |
| `circumspect_option` | 谨慎 | L03:61 |
| `estate_mounts_option` | 华丽的马匹 | L03:140 |

## 3. 相关技能、宗族传承、职位与概念

| key | 原件文本／解析后文本 | 来源 |
| --- | --- | --- |
| `toe_the_line_perk_name` | 服从上级 | L05:86 |
| `fearful_troops_perk_name` | 以怖治军 | L05:94 |
| `digging_for_dirt_perk_name` | 深挖黑料 | L05:15 |
| `chains_of_loyalty_perk_name` | 层层效忠 | L05:80 |
| `popular_figurehead_perk_name` | 大众领袖 | L05:75 |
| `zealous_proselytizer_perk_name` | 热忱宣教 | L05:35 |
| `mercenary_contacts_perk_name` | 佣兵合同 | L05:183 |
| `local_hero_perk_name` | 一方英雄 | L05:173 |
| `know_your_land_know_your_people_perk_name` | 地利人和 | L05:191 |
| `well_prepared_perk_name` | 准备充分 | L05:168 |
| `journey_planner_perk_name` | 旅行规划 | L05:180 |
| `just_one_more_hill_perk_name` | 复越高山 | L05:170 |
| `clerical_justifications_perk_name` | 教权辩护 | L05:38 |
| `ep2_activities_legacy_track_name` | 活动传承 | L06:2 |
| `ep2_activities_legacy_track` | 活动[dynasty_perk\|E] | L06:4 |
| `ep2_activities_legacy_1_name` | 踏过圣路 | L06:5 |
| `erudition_legacy_track_name` | 学识传承 | L07:30 |
| `erudition_legacy_4_name` | 真正信徒 | L07:35 |
| `game_concept_intent` | 意图 | L08:795 |
| `game_concept_entourage` | 旅团 | L08:2205 |
| `game_concept_travel_options` | 旅行选项 | L08:2196 |
| `game_concept_travel_safety` | 安全性 | L08:2201 |
| `game_concept_travel_speed` | 速度 | L08:2203 |
| `game_concept_travel_danger` | 危险 | L08:2198 |
| `game_concept_dynasty_perk` | 宗族传承 | L08:756 |
| `game_concept_perk` | 技能 | L08:759 |
| `game_concept_cultural_acceptance` | 文化接受度 | L08:1304 |
| `travel_leader_court_position` | 旅队主管 | L09:504 |
| `court_physician_court_position` | 私人医生 | L09:354 |
| `travel_leader_celestial_imperial` | 桥道顿递使 | L09:849 |
| `travel_leader_celestial` | 前驱官 | L09:851 |
| `court_physician_celestial_imperial` | 太医 | L09:841 |
| `court_physician_celestial` | 医学博士 | L09:843 |

## 4. 间接引用与富文本片段

| key | 原件文本／解析后文本 | 来源 |
| --- | --- | --- |
| `court_physician_option_suffix` |  #weak （仅抵消瘟疫）#! | L03:39 |
| `hire_travel_leader_decision` | 寻找$travel_leader_court_position$ -> 寻找旅队主管 | L09:506 |
| `leisurely_option_effect` | $leisurely_option$ -> 悠闲之旅 | L03:149 |
| `adventurers_forward_scouts_option` | 斥候 | L04:669 |

## 5. 排场描述原始模板

- `pilgrimage_pomp_humble_desc` (L01:124)：$EFFECT_LIST_BULLET$不带任何你[court\|E]的人出发，这使[travel\|E]变得危险<br>$EFFECT_LIST_BULLET$你加入了[EmptyScope.ScriptValue('pilgrimage_entourage_pomp_humble_max_value')]名随机朝圣者组成的队伍<br>$EFFECT_LIST_BULLET$完成后能获得更多[piety\|E]<br><br>#weak 朝圣的时光应当用来静默退省。与陌生人同路的普通朝圣者队伍是最为合适。#!
- `pilgrimage_pomp_appropriate_desc` (L01:126)：$EFFECT_LIST_BULLET$你带上保镖或优秀的骑士，也许还有朋友<br>$EFFECT_LIST_BULLET$最多[EmptyScope.ScriptValue('pilgrimage_entourage_pomp_appropriate_max_value')]名随机朝圣者加入你的队伍<br>$EFFECT_LIST_BULLET$完成后的[piety\|E]奖励不受影响<br><br>#weak 道路险要，旅途遥远。精神纯洁是一回事，有勇无谋又是另一回事。#!
- `pilgrimage_pomp_ceremonial_desc` (L01:128)：$EFFECT_LIST_BULLET$你#EMP 还#!带上仆人和虔诚的扈从<br>$EFFECT_LIST_BULLET$最多[EmptyScope.ScriptValue('pilgrimage_entourage_pomp_ceremonial_max_value')]名随机朝圣者加入你的队伍<br>$EFFECT_LIST_BULLET$完成后获得的[piety\|E]提高<br><br>#weak 信仰需要遵守礼节，即使远离家乡。不带随从难道还能遵守礼节吗？#!
- `pilgrimage_pomp_throng_desc` (L01:130)：$EFFECT_LIST_BULLET$[court\|E]里每个感兴趣的[character\|E]都会加入你<br>$EFFECT_LIST_BULLET$最多[EmptyScope.ScriptValue('pilgrimage_entourage_pomp_throng_max_value')]名随机朝圣者加入你的队伍<br>$EFFECT_LIST_BULLET$完成后获得的[piety\|E]大幅提高<br><br>#weak 所有的信徒都应该去我们的圣地……我打算帮助他们。#!

## 6. 栏目与 GUI 绑定

| 来源行 | 实际读取 |
| --- | --- |
| L10:2065-2081 | ActiveActivityOption.GetCategory -> ActivityOptionCategory.GetName |
| L10:2119-2141 | ActiveActivityOption.GetOption -> ActivityOption.GetName |
| L10:639-649 | GetSelectedSpecialOption -> ActivityOption.GetName |
| L11:126-167 | GetPotentialIntents / CanPickIntent -> ActivityIntent.GetName |
| L12:281-281 | TravelOption.GetNameNoTooltip |
| L13:115-115 | TravelOption.GetNameNoTooltip |
| L14:1563-1714 | Category definitions fidelity / pomp |
| L15:66-85 | Physician celestial localization conditions |
| L15:569-588 | Travel leader celestial localization conditions |

## 7. 精确来源文件

| ID | 安装根相对路径 | SHA-256 |
| --- | --- | --- |
| L01 | `localization/simp_chinese/event_localization/activities/pilgrimage_events_l_simp_chinese.yml` | `cecb7052ac6672f1fd99a0008a8e7d6ccca474069a17e8a9902c55571cd272b3` |
| L02 | `localization/simp_chinese/dlc/ep2/dlc_ep2_intents_l_simp_chinese.yml` | `161ce7882f92a7686e246b3e5d62c68f6d5da3be8593cdd673e9fbe12459faf3` |
| L03 | `localization/simp_chinese/dlc/ep2/travel/dlc_ep2_travel_options_l_simp_chinese.yml` | `c617aa958f51b5e54a218ddee92e16cf27450c504dca705d5e60d97f4bc3bdf0` |
| L04 | `localization/simp_chinese/domiciles/domicile_buildings_l_simp_chinese.yml` | `89e3f8e3b5865ef540f434de43f77c1124dcb69d8982acb54364c685523428ac` |
| L05 | `localization/simp_chinese/lifestyles/perks_l_simp_chinese.yml` | `d099b5175d07f269f1b0d43a524093c66e96fa92a122f213c7e9647b2c0778b5` |
| L06 | `localization/simp_chinese/dlc/ep2/dynasty_legacies/dlc_ep2_dynasty_legacies_l_simp_chinese.yml` | `fbaf49c265cd61d010fb8dbc9c7f1379f711ce8b729ff0708f142aee2d783d4a` |
| L07 | `localization/simp_chinese/dynasty_legacies/legacies_l_simp_chinese.yml` | `4be7b323a5f6d3059e3ea109719ea2620da593c3e77123f5be035d079ffcdd64` |
| L08 | `localization/simp_chinese/game_concepts_l_simp_chinese.yml` | `66f9adef09db299f100c3b28ffbcd37d675c746c4ff1aa05927af8d66ac8de86` |
| L09 | `localization/simp_chinese/court_positions_l_simp_chinese.yml` | `8ed0a794dc8971b8cfba562b1991b5f0c7a8ae7af5d115d53f9cc6c884575636` |
| L10 | `gui/window_activity_planner.gui` | `2f18263ad5be79bfc10c9bc33fd1ccff1e41a0be2bafc7d19e4f9cf0b58feb54` |
| L11 | `gui/window_activity_intent_selection.gui` | `07b09863a0064aad7abe1e061a93c979b5edcbc662cb8918a535c3a33a93a91a` |
| L12 | `gui/window_travel_planner.gui` | `0cdf5197fac7389d20a71c3018cbbdebf727c3240ea30f65ae5032706cfe13e3` |
| L13 | `gui/window_travel_option_selection.gui` | `041a0d6ca2e5ca05fcd2d8744c7e8f38bbad7f23c948e4f02867052d42948d5c` |
| L14 | `common/activities/activity_types/pilgrimage.txt` | `24153043485b035cb0477de7306649027cb68c039e4a9d903776eddd870d8b9f` |
| L15 | `common/court_positions/types/00_court_positions.txt` | `a49fca3df3ae5d087d94621d3147db88bdb4f458d97c717e1821b43aa87cc951` |
