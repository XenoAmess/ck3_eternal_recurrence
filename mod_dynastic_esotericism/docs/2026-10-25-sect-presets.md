# 两项教派预置：原版字段与组合边界

2026-10-25 需求版本 2 的实现候选，目标产品版本 0.2.0。用户已确认：各建立独立 Faith 及同名 main Rite，均归入既有 `christianity_religion`。不是把两项 Rite 挂入既有 `catholic` Faith，也不替换原版天主教或罗马礼。

本地来源观察：`machine_id: desktop-3fevhd2-1c74096080`；观察时间 `2026-10-25T15:17:35Z`；机器身份由 Main12 的 `python tools/ck3_live_run_id.py machine` 实际返回。本文所读游戏根为 `C:/SteamLibrary/steamapps/common/Crusader Kings III/game`，文件实际可读。交接记录将此安装标为 CK3 1.20.0.4；本次字段研究没有重新核验 EXE／build，不能单独授予版本或实机业务资格。

## 层级与文件

| 显示名称 | Faith | main Rite | 图标 key |
| --- | --- | --- | --- |
| 繁育教派 / Procreation Sect | `des_procreation_faith` | `des_procreation_rite` | `des_procreation` |
| 白绮教派 / Vivhite Sect | `des_vivhite_faith` | `des_vivhite_rite` | `des_vivhite` |

定义位于 `common/religion/faith_types/des_faiths.txt` 和 `common/religion/rite_types/des_rites.txt`。每个 Faith 指定 `faith_details.religion = christianity_religion`、`main_rite`、`origin = catholic`、`graphical_faith = catholic_gfx`、`historical = no`；复用天主教五圣地，耶路撒冷／罗马／圣地亚哥为 eminent，科隆／坎特伯雷为普通圣地。这里没有抢占既有教宗头衔或写历史信徒。`origin` 的原版说明用于信仰来源及历史领袖处理，不新增 UI 宗教层级。

核心信条及用户指定教义均放在对应 main Rite。Faith 仅显式携带原版隐藏的 `special_doctrine_is_western_christian_faith` 分类，沿用西方基督教表现与肖像选择；这不是新增玩家自选特殊教义。两 Rite 明确 `create = yes`、`convert = yes`，不指定原版头衔作为 founder。

原版结构依据：

- `common/religion/faith_types/_faith_types.info`：`main_rite`、`faith_details`、`origin`、`historical` 及 Faith／Rite 教义覆盖合同。
- `common/religion/rite_types/_rite_types.info`：父 Faith、显示名、图标、创建与改信开关、核心信条及教义字段。
- `common/religion/faith_types/00_faith_types.txt:535–609`：`catholic` 的 Religion、main Rite、图形文化与圣地。
- `common/religion/rite_types/00_rite_types.txt:1–70`：`roman_rite` 结构；`insular_celtic` 直接预置 `special_doctrine_pope_blessing` 的现成例子。
- `common/religion/doctrine_types/40_doctrines_special.txt:455–464`：隐藏西方分类。
- `common/defines/graphic/00_graphics.txt:747、750`：`DYNAMIC_RITE_ICON_PATH` 与 `FAITH_ICON_PATH` 都是 `gfx/interface/icons/faith`。两层均引用同一用户资源，正式文件为 `des_procreation.dds` 与 `des_vivhite.dds`。图标导入证据由单独资源流程保存，本文不宣称图片转换或游戏显示已通过。

`localization/<language>/des_sects_l_<language>.yml` 提供九语、每语 25 个明确键：四个对象各五键，加两帝国教廷的名称／形容词及直属领主层级提示五键。Rite 使用对应 Faith 的本地化引用，使两层名称保持一致。Faith 描述仅介绍教派理念与宗族归属，DLC 与工程边界留在本文。2026-10-26追加的帝国领袖与用户图 CoA 见 [帝国领袖专题](2026-10-26-empire-heads.md)，政府绑定已按用户更正撤销；不放宽下述原版选择限制，实际取得与继承仍待验。

## 核心信条

下表行号均相对于本机实际读取的游戏根；本地化名称来自 `localization/simp_chinese/religion/religion_core_tenets_l_simp_chinese.yml` 或 `localization/simp_chinese/dlc/pam/pam_tenets_l_simp_chinese.yml`。

| 教派 | 用户名称 | 原版 key | 定义来源 |
| --- | --- | --- | --- |
| 繁育 | 你们要生育繁殖 | `tenet_be_fruitful_and_multiply` | `common/religion/tenet_types/00_pam_tenets.txt:827` |
| 繁育 | 肉欲高扬 | `tenet_carnal_exaltation` | `common/religion/tenet_types/00_tenet_types.txt:386` |
| 繁育 | 圣分娩 | `tenet_sacred_childbirth` | `common/religion/tenet_types/00_tenet_types.txt:3275` |
| 白绮 | 战争狂人 | `tenet_warmonger` | `common/religion/tenet_types/00_tenet_types.txt:3462` |
| 白绮 | 基督的精兵 | `tenet_miles_christi` | `common/religion/tenet_types/00_pam_tenets.txt:1288` |
| 白绮 | 追逐权力 | `tenet_pursuit_of_power` | `common/religion/tenet_types/00_tenet_types.txt:4462` |

“你们要生育繁殖”和“基督的精兵”保留原版 `requires_dlc_flag = by_god_alone`、`is_shown = { has_pam_dlc_trigger = yes }` 与基督教限定。预置不加静默 fallback，不把未拥有 DLC 说成已拥有；目标机器 DLC、实际加载及效果仍须验收。

## 共同普通教义

除 `des_doctrine_dynastic` 外，下表全部定义在原版 `common/religion/doctrine_types/20_doctrines.txt`，中文显示名由原版 `localization/simp_chinese/religion/religion_l_simp_chinese.yml` 绑定；加冕显示名位于 `localization/simp_chinese/activities/coronation_activity_l_simp_chinese.yml:82`。

| 用户选择 | 精确 key | 定义行号 |
| --- | --- | --- |
| 男女平等 | `doctrine_gender_equal` | 808 |
| 正义 | `doctrine_pluralism_righteous` | 1043 |
| 神权制 | `doctrine_theocracy_temporal` | 1110 |
| 世俗信仰领袖 | `doctrine_temporal_head` | 1224 |
| 鼓励朝圣 | `doctrine_pilgrimage_encouraged` | 1683 |
| 多神论 | `doctrine_polytheist` | 2014 |
| 宗族化 | `des_doctrine_dynastic` | 本产品 `common/religion/doctrine_types/des_doctrines.txt` |
| 侧室 | `doctrine_concubines` | 44 |
| 允许离婚 | `doctrine_divorce_allowed` | 106 |
| 没有人是私生子 | `doctrine_bastardry_none` | 127 |
| 无限制婚姻 | `doctrine_consanguinity_unrestricted` | 977 |
| 接受同性关系 | `doctrine_homosexuality_accepted` | 235 |
| 性变态为美德 | `doctrine_deviancy_virtuous` | 334 |
| 接纳男性通奸 | `doctrine_adultery_men_accepted` | 414 |
| 接纳女性通奸 | `doctrine_adultery_women_accepted` | 475 |
| 杀死亲族成员是犯罪 | `doctrine_kinslaying_extended_family_crime` | 533 |
| 巫术为美德 | `doctrine_witchcraft_virtuous` | 731 |
| 神职征兵 | `doctrine_clerical_function_recruitment` | 1299 |
| 神职性别不限 | `doctrine_clerical_gender_either` | 1367 |
| 允许神职结婚 | `doctrine_clerical_marriage_allowed` | 1385 |
| 世俗，可被剥夺 | `doctrine_clerical_succession_temporal_appointment` | 1430 |
| 天葬 | `doctrine_funeral_sky_burial` | 1850 |
| 允许傅油礼 | `doctrine_anointment_permitted` | 1941 |
| 鼓励隐修 | `doctrine_monasticism_encouraged` | 2071 |
| 圣事为核心 | `doctrine_sacraments_central` | 2298 |

“杀死亲族成员是犯罪”使用 `extended_family_crime`，没有替换为另一项“杀死宗族成员是犯罪”的 `any_dynasty_member_crime`。

## 特殊教义

全部定义在原版 `common/religion/doctrine_types/40_doctrines_special.txt`；每项属于独立 doctrine group，可以同时定义。中文绑定来自原版 `religion_l_simp_chinese.yml:942–966、1131`，圣洁祝福为 `dlc/pam/pam_character_interactions_l_simp_chinese.yml:945`。

| 用户名称 | 精确 key | 定义行号 | 显式预置 |
| --- | --- | --- | --- |
| 摩西的教导 | `special_doctrine_is_jewish_faith` | 46 | 繁育 |
| 耶稣的教导 | `special_doctrine_is_christian_faith` | 1 | 繁育 |
| 先知的圣训 | `special_doctrine_is_islamic_faith` | 26 | 繁育 |
| 华夏宇宙观 | `special_doctrine_is_sinitic_faith` | 86 | 繁育 |
| 多种宗教交织 | `special_doctrine_is_eastern_faith` | 66 | 繁育 |
| 诺斯替主义 | `special_doctrine_is_gnostic_faith` | 104 | 繁育 |
| 吉兹亚 | `special_doctrine_jizya` | 401 | 繁育、白绮 |
| 圣洁祝福 | `special_doctrine_pope_blessing` | 477 | 繁育、白绮 |

`special_doctrine_has_jizya_doctrine` 只有遗留本地化名称，实际定义是 `special_doctrine_jizya`。诺斯替特殊教义使用 `special_doctrine_is_gnostic_faith`，不额外占用三核心信条中的一槽。

原版 Religion 继承继续生效。`common/religion/religion_types/00_christianity.txt` 会为未被覆盖的组提供 `abrahamic_hostility_doctrine`、`special_doctrine_is_christian_faith`、`doctrine_scriptural` 等默认项，因此白绮仍拥有继承的“耶稣的教导”。不能把用户的显式两项特殊教义误读为禁止原版父 Religion 继承。Faith 的隐藏西方分类另见上文。

## 原版创建界面限制与待验范围

以下是实际读取到的原版 picker 约束，产品不修改这些定义，也不重定义同名空教义：

1. `20_doctrines.txt:1129–1134、1241–1246`：神权制与世俗信仰领袖在 `can_pick` 中互斥。
2. `20_doctrines.txt:1953–1962`：允许傅油礼的 `can_pick` 排斥无领袖及世俗领袖。
3. `00_tenet_types.txt:3487–3501`：战争狂人的 `can_pick` 排斥基督教、伊斯兰教、犹太教与二元神教。
4. `common/religion/doctrine_group_types/00_doctrine_group_types.txt:78–81` 将信仰领袖组标为 `main_rite = yes`；本次各自新建 Faith 及 main Rite，没有试图给既有天主教下的普通分支 Rite 分设信仰领袖。
5. 同文件的 `pope_blessing` 为 `doctrine_lock = rite` 且 `is_available_on_create = { always = no }`；静态预置有原版 insular_celtic 先例，后续编辑行为仍依原版约束。
6. 同文件 `doctrine_coronation` 在创建界面要求 `has_ach_dlc_trigger = yes`。不得以静态预置忽略目标机器资格。

本轮实现只写明确预置组合，不扩大原版全局选择范围。必须在新正式包中执行 LIVE-12／13，检查实际三核心信条、全部指定教义、父 Religion、main Rite、图标和实际功能；记录加载时是否保留这些组合以及后续编辑限制。源文件存在、语法解析、Java 构建或 HTTP 成功都不能替代此项业务结果。没有实际游戏后态前，本文件不声明预置组合可玩、世俗领袖已成立或全部效果已生效。

新档无初始信徒时不写伪造的 Dynasty 或 founder；实际角色进入预置 Rite 后，沿共享宗族化路径建立／加入绑定。现有保存中的新增 Faith／Rite 引擎补载行为尚待实机，不能从新档定义推定旧档已存在两对象。
