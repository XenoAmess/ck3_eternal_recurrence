# V6 官方简中核对：宗教、特质与条件名称

machine_id：`4-8e1c2f1861`。本轮仅静态读取本机安装的 CK3 `game/localization/simp_chinese` 与对应定义；真实读取 UTC、逐文件 SHA-256、行号及引用链见[结构化核对表](knowledge/pilgrimage-v6-localization-religion-12004.json)。不构成新实机或界面验收。旧 V5 封包保留，本文件作为后继术语补注。

## 必须修正的称呼

| V5 用语 | 影片应采用的官方名称 | 本地化 key 与注意点 |
| --- | --- | --- |
| 朝圣偏好（当作栏目名） | **朝圣态度** | `doctrine_pilgrimage_name`；“偏好”可解释语义，不能冒充原版栏目 |
| 武僧（当作文化传统名） | **战斗祭司／僧兵** | `tradition_warrior_monks_name`／`tradition_tgp_warrior_monks_name`；两项都提供 `prowess_from_religious_traits`，不能统一改成一项而漏掉另一项 |
| 私人信条 | **个人信条** | `game_concept_personal_tenet` |
| 教会住所 | **教会庄园** | `game_concept_ecclesiastical_domicile` → `$game_concept_ecclesiastical_estate$` → 教会庄园 |
| 教会住所对应建筑（不指出具体建筑） | **教会庄园内的朝圣者收容所** | `baptistery_pilgrims_hospice_01_domicile_building`；02／03／04 均引用 01 同名，不是普通地产的“救济院”升级链 |
| 社交者（指 gregarious 性格） | **合群** | `trait_gregarious` |
| 药师（指 herbalist 特质） | **草药师** | `lifestyle_herbalist`／`trait_lifestyle_herbalist` |
| 医师（统称 physician 特质） | **医生** | `trait_lifestyle_physician`；等级名另为“新手医生／医生／著名医师” |
| 神秘主义（指人物特质） | **神秘主义者** | `trait_lifestyle_mystic`；实际等级可能显示智者／女智者、神秘主义者、行奇迹者，不能拿抽象学说名称代替特质名 |
| 神权（当作正式政体名） | **神权制** | `game_concept_theocracy`／`game_concept_theocratic_government`；`government_is_theocracy` 仍是实际条件 key，不擅自改写为只限“教会制” |
| 本地祭祀（当作决议名） | **举行一场祭祀仪式** | `visit_local_shrine_decision`；“本地祭祀”只可作说明 |
| 使徒相关信条（指 apostolic_succession） | **宗徒继承／使徒继承** | 拉丁礼仪语言与默认名称是“宗徒继承”；希腊礼仪语言是“使徒继承”；由定义中的 `name.first_valid` 选择 |
| 早期中世纪 | **中世纪早期** | `culture_era_early_medieval`；V6固定算例与口播仍须统一这一词序 |
| 兴趣点 | **重要地点** | `game_concept_point_of_interest`／`game_concept_points_of_interest` |
| 收入大臣 | **户部尚书** | `game_concept_minister_of_revenue` → `$councillor_steward_celestial_government_imperial$` → 户部尚书 |

## 朝圣态度与朝觐

| 对象 | key | 官方短名 |
| --- | --- | --- |
| 朝圣态度组 | `doctrine_pilgrimage_name` | 朝圣态度 |
| `doctrine_pilgrimage_forbidden` | `doctrine_pilgrimage_forbidden_name` | 禁止 |
| `doctrine_pilgrimage_encouraged` | `doctrine_pilgrimage_encouraged_name` | 鼓励 |
| `doctrine_pilgrimage_local_rites` | `doctrine_pilgrimage_local_rites_name` | 当地仪式 |
| `doctrine_pilgrimage_mandatory` | `doctrine_pilgrimage_mandatory_name` | 强制 |
| `doctrine_pilgrimage_mandatory_hajj` | `doctrine_pilgrimage_mandatory_hajj_name` | 朝觐 |

上述五个短名原来正确。部分教义另有描述名：“禁止朝圣”“鼓励朝圣”“朝圣义务”。不能把“强制”短名与“朝圣义务”描述名说成两项。没有另一个名为“允许”的第六项。

`game_concept_hajj` 的官方概念名为**朝觐**。特质内部 key `hajjaj` 的名称不是固定一个词：`common/traits/00_traits.txt:8917–8935` 的 `name.first_valid` 对空人物或男性引用 `trait_hajji`（**朝觐者**），对女性引用 `trait_hajjah`（**朝觐妇**）。因此讲内部同一特质可以写“朝觐者／朝觐妇（hajjaj）”；具体人物画面应使用其实际显示名。

## 朝圣者与其他特质

`pilgrim` 的官方显示名由 `common/traits/00_traits.txt:8831–8856` 决定：先判经验至少 100，再判至少 50，最后使用基础名。不能从英语词根再造“熟练／资深／虔诚”等等级名。

| 状态 | key | 官方名称 |
| --- | --- | --- |
| 不足 50 特质经验 | `trait_pilgrim` | 朝圣者 |
| 至少 50、不足 100 | `trait_pilgrim_2` | 老道的朝圣者 |
| 100 | `trait_pilgrim_3` | 高效的朝圣者 |
| gregarious | `trait_gregarious` | 合群 |
| shy | `trait_shy` | 害羞 |
| cynical | `trait_cynical` | 愤世嫉俗 |
| zealous | `trait_zealous` | 狂热 |
| vengeful | `trait_vengeful` | 睚眦必报 |
| patient | `trait_patient` | 耐心 |
| impatient | `trait_impatient` | 急躁 |
| humble | `trait_humble` | 谦卑 |
| witch | `trait_witch` | 巫师 |
| herbalist | `lifestyle_herbalist` | 草药师 |
| physician 通称 | `trait_lifestyle_physician` | 医生 |
| physician 三个显示档 | `trait_physician_1`／`_2`／`_3` | 新手医生／医生／著名医师 |
| mystic 通称 | `trait_lifestyle_mystic` | 神秘主义者 |
| mystic 初档按性别 | `trait_mystic_male_1`／`trait_mystic_female_1` | 智者／女智者 |
| mystic 后两档 | `trait_mystic_2`／`_3` | 神秘主义者／行奇迹者 |

## 宗教结构、资源与已正确名称

| 概念或定义 | key | 官方名称 |
| --- | --- | --- |
| Religion | `game_concept_religion` | 宗教 |
| Faith | `game_concept_faith` | 信仰 |
| Rite | `game_concept_rite` | 礼仪 |
| doctrine | `game_concept_doctrine` | 教义 |
| tenet | `game_concept_tenet` | 信条 |
| personal_tenet | `game_concept_personal_tenet` | 个人信条 |
| piety | `game_concept_piety` | 虔诚 |
| piety_experience | `game_concept_piety_experience` | 奉献 |
| piety_level | `game_concept_piety_level` | 奉献等级 |
| trait_level_track_xp | `game_concept_trait_level_track_xp` | 特质经验 |
| spiritual_fulfillment | `game_concept_spiritual_fulfillment` | 灵性满足 |
| learning_lifestyle | `game_concept_learning_lifestyle` | 学识生活方式 |
| theocracy | `game_concept_theocracy` | 神权制 |
| ecclesiastical | `game_concept_ecclesiastical` | 教会制 |
| confederation | `game_concept_confederation` | 联盟 |
| treasury | `game_concept_treasury` | 国库 |
| house_aspiration | `game_concept_house_aspiration` | 家族志向 |
| tenet_vows_of_poverty | `tenet_vows_of_poverty_name` | 神贫誓愿 |
| tenet_inner_journey | `tenet_inner_journey_name` | 内在之旅 |
| tenet_armed_pilgrimages | `tenet_armed_pilgrimages_name` | 武装朝圣 |
| ep2_activities_legacy_1 | `ep2_activities_legacy_1_name` | 踏过圣路 |
| just_one_more_hill_perk | `just_one_more_hill_perk_name` | 复越高山 |
| erudition_legacy_track | `erudition_legacy_track_name` | 学识传承 |
| erudition_legacy_4 | `erudition_legacy_4_name` | 真正信徒 |
| dynasty_perk | `game_concept_dynasty_perk` | 宗族传承 |
| early_medieval | `culture_era_early_medieval` | 中世纪早期 |
| holy_site | `game_concept_holy_site` | 圣地 |
| eminent_holy_site | `game_concept_eminent_holy_site` | 主要圣地 |
| point_of_interest | `game_concept_point_of_interest` | 重要地点 |
| minister_of_revenue | `game_concept_minister_of_revenue` | 户部尚书 |

“普通圣地”没有在本轮相关概念中找到独立名称；本片可解释为“本人信仰的一处非主要圣地”，不要把“普通圣地”做成仿原版的独立分类标签。主要圣地的实际概念 key 是 `eminent_holy_site`，不能凭英语解释另造 `major_holy_site`。

“奉献经验”可以作为解释其数值累积方式的普通句子，但不能标注为官方概念名；原版概念为“奉献”。“活动表现”“主奖励”“本体费用”“边际收益”等是本片分析用语，须在首次出现时解释含义，不把它们做成仿原版菜单标签。

## 核对方法与可复用边界

结构化文件保存逐条原始本地化值、整值 `$key$` 引用链、最终文字、源文件与行号，以及源文件字节数和 SHA-256。另有动态名称定义分支及建筑、教义、信条、文化传统、生活方式／家族传承的定义身份。

本轮只核当前导演稿相关术语；不宣称已经清点全游戏中文，不改原版文本，也不凭源码名称外推当前玩家的实际可选项。含语法引用的整句、触发条件、性别和礼仪语言不能通过简单全局替换安全处理，主稿应使用当前画面对象对应的名称。
