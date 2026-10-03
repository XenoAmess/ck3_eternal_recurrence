# CK3 1.20.0.3：儒家与天主教／基督教内容差异

研究日期：2026-10-03。范围是本机 Steam 原版 **1.20.0.3（Crozier），build 25652598** 的脚本与本地化。安装根目录为 `C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/`，下文路径相对其 `game/`。结论是静态代码研究，没有启动游戏，不代表逐项实机验收。DLC 条件单独列出；代码存在不等于任何 DLC 配置均可使用。

宗教文件的缩写路径均相对 `common/religion/`：`religion_types/`、`faith_types/`、`rite_types/`、`doctrine_types/`、`doctrine_group_types/`。只写文件名时沿用该文件已出现的目录。版本和原版文件 SHA-256 见[来源清单](ck3-religion-confucian-christian-comparison-1.20.0.3.sources.json)。

儒家少的内容集中在独立教会组织、教会政治、圣事、隐修和大圣战。圣地、朝圣、礼仪、个人核心信条、加冕和葬礼仍有对应系统。比较对象必须分清天主教专属、基督教宗教限定、默认教义差异及政府门禁。

## 当前版本的数据结构

- `00_confucianism.txt:1–52` 是宗教级默认教义，`00_faith_types.txt:1398–1417` 定义一个 `confucian_faith`（儒家）。
- 预定义经学、道学是该信仰下的礼仪，核心教义定义在 `00_rite_types.txt:1182–1210`。经学为仁政／孝道／安居乐业，道学为仁政／孝道／格致。信仰定义注释记录 867 主礼仪经学、1066 主礼仪道学。
- 天主教 `catholic` 的主礼仪是 `roman_rite`（`00_faith_types.txt:535–608`）。罗马礼仪的初始 `faith = christian_faith` 与分裂前后历史转换共同工作，不能套用旧版“每个 faith 直接带三核心教义”的结构。
- 原版静态定义含 **19 个基督教 faith、27 个基督教 rite**，儒家是 **1 个 faith、2 个 rite**。这是预定义条目数量，包括历史或异端条目；不等于某一开局同时存在的数量，也不能用来直接衡量玩法质量。来源是 `faith_types/*.txt`、`rite_types/*.txt` 的顶层定义与宗教／信仰关联。

## 已确认的缺口

| 内容 | 儒家相对天主教／基督教的差别 | 条件和原版证据 |
| --- | --- | --- |
| 宗教领袖与教宗外交 | 默认没有宗教领袖，没有教宗这个独立权力中心；缺少通过教会求钱、请求宣称和申请婚姻裁决的相同渠道。儒家本身允许自由离婚，不能说没有离婚。 | 儒家 `religion_types/00_confucianism.txt:12,19`；基督教 `00_christianity.txt:13,20`。求钱 `common/character_interactions/00_religious_interactions.txt:6845–6859`；无PAM求宣称 `:7220–7232`；PAM教会宣称 `pam_interactions.txt:7992` → `pam_scripted_triggers.txt:1753–1755,1561–1567`；离婚审批 `00_marriage_interactions.txt:4613–4621`。这些能力通常依赖领袖／教义，并非全基督教无条件拥有。 |
| 基督教教会局势 | 儒家不参与基督教教会的阶段推进、改革、授职危机和相应教会会议。 | `common/situation/situations/pam_christian_situation.txt:8,67–86` 的参与条件显式要求 `christianity_religion`；属于 PAM（`by_god_alone`）内容。 |
| 枢机、教宗选举与反教宗 | 缺少枢机职位、影响教宗选票及争夺教宗合法性的政治链。枢机制由选举教义控制；反教宗／竞争宗教领袖入口按领袖教义判断，不能统一说是天主教硬限定。 | 天主教定义 `faith_types/00_faith_types.txt:546–608`；`common/character_interactions/pam_interactions.txt:4484,14200`；`common/decisions/dlc_decisions/pam/pam_antipope_decisions.txt:29–40` 要求属灵领袖且排除无领袖礼仪。 |
| 教宗诏书 | 儒家没有教宗颁布诏书、藉此塑造天主教教会的入口。 | `common/decisions/dlc_decisions/pam/bulls_decisions.txt:28–33`；`pam_scripted_triggers.txt:3963–3964` 的 `has_papacy_trigger` 写死为 `faith:catholic`，是PAM天主教限定。 |
| 核心信条流行度 | 没有基督教的核心信条流行度与教会思潮机制；通用个人核心信条并不等同于这一系统。 | `common/scripted_triggers/pam_scripted_triggers.txt:3959–3961` 明确 `christianity_religion` 限制。 |
| 独立教区与教会地产 | 儒家默认平信徒神职人员、世俗任命；缺少基督教教区和专门的教会政体／教会租约体系。 | 儒家定义 `:15,35`；基督教定义 `:5–6,16,36`；`doctrine_types/40_doctrines_special.txt:1–9` 的基督教特殊教义提供 `has_clerical_regions`。仍有神殿和宗教顾问，不能写“没有神职人员”。 |
| 圣事与宗教制裁 | 儒家默认“无圣事”，没有默认的绝罚、求大赦／赎罪券参数；临终圣事决议另有基督教身份限制。 | `doctrine_types/20_doctrines.txt:2361–2392`；儒家定义 `:37`，基督教定义 `:38`。临终圣事 `common/decisions/dlc_decisions/pam/pam_decisions.txt:1027–1064` 要求 PAM、`christian_fulfillment` 与 `last_rites_active`。 |
| 隐修与修道会 | 默认没有宣誓出家及创办修道会、围绕修道会核心教义开展的相应玩法。 | 儒家定义 `:36`；`20_doctrines.txt:2173–2253`；`common/decisions/00_holy_order_decisions.txt:605–621` 与 `common/scripted_triggers/pam_scripted_triggers.txt:994–1005`。这是默认教义差异，不能说一切儒家自创礼仪永远无法选择隐修。 |
| 军事修会 | 默认不能创建军事修会；即使宗教定义列了修会名字，也不证明具备创建资格。 | 儒家“法界圆融”特殊教义 `40_doctrines_special.txt:416–424` 提供 `immaterial_harmony_no_holy_orders`；创建门禁 `common/scripted_triggers/00_religious_triggers.txt:996–1011` 排除该参数。 |
| 大圣战／十字军 | 默认没有宗教领袖与启用大圣战的参数，不具备天主教式十字军动员链。 | `common/scripted_triggers/00_great_holy_war_triggers.txt:9–23,69–86`。十字军也不是所有基督教分支自动拥有；普通圣战需另行分析。 |
| 基督教专属灵性玩法 | 儒家使用非基督教的通用灵性满足模型，缺少基督教专属的告解、展现奉献、提供属灵指引等入口与专属等级效果。 | `common/spiritual_fulfillment/00_spiritual_fulfillment_types.txt:1–113` 为基督教七级模型，`:115–177` 为非基督教五级 fallback；`pam_decisions.txt:57–65,147–150,239–241` 的身份／DLC门禁。不是“儒家没有灵性满足”。 |
| 大教堂伟大工程 | 没有 PAM 基督教大教堂的建造与升级工程入口。 | `common/scripted_triggers/pam_scripted_triggers.txt:787–791` 要求 PAM、公爵以上、`christian_fulfillment`；`common/buildings/pam_buildings.txt:61–106` 另有建筑启用条件。不是“儒家没有任何特殊建筑／伟大工程”。 |
| 基督教守护圣人与圣人敬礼强化 | 没有选择基督教守护圣人，以及圣人敬礼核心信条提供的封圣减费、额外圣物加成等。封圣和圣物的通用／非基督教路径另见下文。 | `pam_decisions.txt:889–910` 显式限定基督教与个人Dulia参数；`tenet_types/00_pam_tenets.txt:153–180` 限定宗派／个人选择并提供强化。中文名见 `localization/simp_chinese/dlc/pam/pam_tenets_l_simp_chinese.yml:1173`。 |
| 历史宗教目标 | 没有基督教的阻止／造成／弥合大分裂及天主教恢复教廷／归还罗马的对应宗教剧情。 | `common/decisions/80_major_decisions_roman.txt:435–436,825,894`；`pam_decisions.txt:2577,2693,2814`；`common/decisions/10_religious_decisions.txt:1423`。拆除教廷是反例，见下文。 |
| 神职傅油加冕 | 少的是教会傅油路径，普通加冕和加冕宝物仍存在。 | 儒家 `doctrine_no_anointment`，基督教 `doctrine_imperial_anointment`；`20_doctrines.txt:1928–1938,1964–1984`。 |

## 不能算作完全缺失的内容

1. **圣地**：儒家五处圣地为曲阜、长安、洛阳、汴梁、青城山，见 `faith_types/00_faith_types.txt:1406–1415`。天主教同样列五处，不能把圣地数量列为儒家缺项。
2. **朝圣**：“当地仪式”仍有 `can_go_on_pilgrimage`、`basic_pilgrimage_rewards` 和地方圣坛供奉；见 `20_doctrines.txt:1710–1729`。对应奖励、支出和宗教风味有差别，不等于朝圣系统消失。
3. **普通圣战**：儒家默认核心教义没有 `holy_wars_forbidden`。`common/casus_belli_types/00_religious_war.txt:20–29,600–610,1240–1247` 分别在伯爵领／公国／王国圣战门禁排除天朝制。宗教敌意和其他角色／目标条件仍需满足；不能把天朝制限制归为儒家宗教全面禁止圣战。
4. **创建／修改礼仪**：`00_religious_triggers.txt:3021–3247` 的通用入口未按儒家或华夏宗教作整体禁止；成年、和平、身份、次数、领袖关系等其他条件仍适用。宗教领袖属于主礼仪级教义，见 `doctrine_group_types/00_doctrine_group_types.txt:70–73`。自定义教义可能补上部分差异，不能因此推断获得显式检查基督教身份的系统。
5. **加冕与葬礼**：通用加冕门禁见 `common/scripted_triggers/10_ach_scripted_triggers.txt:1`，通用葬礼门禁见 `common/activities/activity_types/funeral.txt:10–23`；儒家的家族仪式仍有自己的葬礼路线。DLC／等级／政体条件不应写成宗教整体禁用。
6. **圣人／先祖与圣物**：`common/scripted_triggers/pam_saint_triggers.txt:45–59` 只对基督教追加Dulia条件，非基督教不要求尊崇先祖核心信条；`:78–82` 为非教区信仰使用圣地的路径。`common/decisions/dlc_decisions/pam/pam_saint_decisions.txt:82–90,556–568` 的封圣、提取圣物没有基督教身份硬限制，仍需DLC、合格先祖／圣者、地点、角色等条件。因此不能笼统写“儒家没有圣人、封圣和圣物”。基督教守护圣人与Dulia强化须另列。
7. **拆除教廷**：`80_major_decisions_roman.txt:1009–1029` 按首都地区、天主教对自己的敌意、现教宗身份等判断，没有儒家宗教排除。不能把这个针对天主教的决议错当成天主教独占。

## 儒家的内容方向

儒家默认核心教义把宗教资源与统治、家庭和学问联系起来：仁政包含巡察、救灾、宽宥等，孝道包含亲子牵制和祖传宝物，安居乐业包含拉拢与五伦关系，格致包含儒家经典／经文研习和知识宝物。见 `common/religion/tenet_types/00_tenet_types.txt:5480–5500,5555–5572,5637–5649,5715–5727`。

科举、官僚、功绩、王朝循环等大量东亚玩法由政府、文化、地区及 DLC 共同控制；不能把全部天朝玩法当作儒家信仰独占，也不能用它们逐项抵消教会系统的缺口。经典研习决议的实际条件见 `common/decisions/dlc_decisions/tgp/tgp_china_decisions.txt:925–950`。

## 证据边界

本专题回答默认原版内容和可见脚本门禁，不声称所有引擎／AI／UI分支已逆向闭合。不根据单个关键词命中、文件行数或本地化名断定玩法可用。未在此开展 CK3 实机、发布或自动玩家策略施工。

## 检查与复现

通过 launcher `rawVersion` 和 Steam manifest `buildid` 确认版本，再交叉检查宗教／信仰／礼仪默认数据、教义参数、实际活动／决议／互动入口及简体中文本地化。来源清单保存对应原版文件哈希与预定义关联；不把原版源码或资产复制入仓库。文档检查使用 `git diff --check`，没有为纯研究文档运行游戏验收或产品构建。
