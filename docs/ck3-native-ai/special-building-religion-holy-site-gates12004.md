# 特殊建筑：宗教与圣地条件的完整有界清点

machine_id: `4-8e1c2f1861`；UTC观察时间 `2026-10-18T06:13:53.238823+00:00`。本机安装文本按SHA逐文件绑定，目标版本1.20.0.4；本任务没有重新验证EXE/build或启动游戏，不能充当新的实机收益验收。

采用或新建圣地，只可能改变某个建筑的圣地关联条件。每个建筑等级自己的建造、启用和持有者条件须分别检查。源码定义、可建/启用资格、已建状态与净收益后读是不同层次。

## 范围与完整性

结构解析了 `common/buildings/*.txt` 的22文件、989个顶层建筑定义，复用仓库解析器并逐字段比对带行号解析结果。正式`type=special`有482个定义（按等级计，不能当482座独立地标），其中115个命中本报告宗教/圣地门；其余367个没有这些门。另有15个`great_building`单列，3个大教堂等级以`christian_fulfillment`作启用门，12个没有宗教/圣地门。普通442、公国首府50不在特殊建筑分类内。

482项分布：特殊矿215、主特殊建筑197、ccp3 26、cp8 23、cp6 12、传奇5、pam4。安装DLC目录30份描述文件未发现额外建筑/触发器脚本覆盖或ZIP；这些DLC相关定义在本次base/common源集合中。文件存在不证明账号拥有或当前启用了相应DLC。

递归展开所用的14个参数化scripted-trigger调用，宏参数逐次替换；没有未解参数、循环、重复定义或不支持的调用。扫描源共有3866个scripted-trigger定义。所有实际叶谓词均人工核对归类，未仅凭建筑名或关键词计数。115+3个命中定义的官方简中名全部闭合；非宗教矿`building_liangzhe_mines_03`没有可解析官方名称，保持空值，不猜三级名称。

本报告完整范围为`is_enabled`、三个`can_construct*`以及`can_rebuild`触发域。美术的graphical faith、名称、旅游/宗教旗标、虔诚奖励或AI权重不是信仰启用门，不能拿来推定合法性。政府、地产类型、创新、文化、变量、工程状态等非宗教门在完整公式中保留；后验净效果未测。完整余项清单在[清点数据](evidence/special-building-religion-holy-site-gates12004/catalogue.json)的`nonreligious_inventory`，源闭包在[来源清单](evidence/special-building-religion-holy-site-gates12004/source-manifest.json)。

## 三层不能混

原版`_buildings.info`规定：`scope:holder`是barony title的持有者，`scope:county`才是所属伯爵领。建造需`is_enabled AND can_construct_potential AND can_construct_showing_failures_only AND can_construct`，还需原版槽位、等级、资源等引擎条件。某域未写谓词只表示无该域额外定义条件，不能直接记作当前Can=true。

`is_enabled=false`时正常效果不授予且不能建造；fallback若存在需另查。持有建筑所在地头衔并不保证启用。`character_modifier`收件人是地产所有者；`county_holder_character_modifier`是伯爵领持有者；`county_modifier`和`province_modifier`分别作用于county与province对象，不能把所有收益都记给玩家。每条清点记录列出实际modifier receiver字段及fallback/override存在性。

本文H只读`barony.is_holy_site_of(scope:holder.faith)`，没有额外写入主要等级、Active、稀有度或伯爵领持有者Faith条件。不要把圣地类型修正的另一套消费者门移植到建筑。

## 逻辑符号

H：该barony是**地产持有人Faith**的圣地。I/C/J：地产持有人分别属伊斯兰/基督教/犹太教宗教，**OR**其**当前礼仪**具有相应`*_syncretic_actor`参数。E/S：其宗教属`rf_eastern`/`rf_sinitic`，OR个人rite具相应参数。Z：琐罗亚斯德教宗教，OR个人rite具`eastern_syncretic_actor`；保留原版这个具体参数，不改名。其余精确信仰、礼仪、教义、精神成就类型条件保持原key。

## 六组可讲的真实定义对照

1. 麦加大清真寺：名称不等于硬编码伊斯兰门。定义启用只检查持有者Faith圣地关系H。
2. 圣索菲亚大教堂启用H；阿亚索菲亚清真寺额外建造I，启用I OR H。伊斯兰分支已真时，不必为启用另补H。
3. 圆顶清真寺启用H AND NOT J：只有圣地关联仍不足；犹太教或相容的当前礼仪反而触发排除。
4. 第三圣殿额外建造H AND J，启用H OR J。能使用既有建筑，不表示满足新建条件。
5. 苾利诃地湿伐罗神庙启用E，额外建造需持有者文化庄园创新；它没有H门，也不是只限印度教。
6. 帕特农神庙额外建造要求持有者宗教等于hellenic_pagan所属宗教，启用还要H。这是宗教层级相等，不能改说成exact Faith，也没有综摄替代。

这些例子还受其非宗教建造门约束。例如`building_requirement_tribal=no`递归后排除部落、游牧和wanua三种政府flag，并非只排除部落制。没有本轮新实机操作，以上不能说成建筑已启用或数值已到账。

## 全部命中定义

按启用门优先分组仅为阅读便利；下表逐阶段逻辑才是依据。`额外建造`列仍须与启用门合取；未列非宗教门见JSON完整公式。每行source范围与文件SHA在来源清单可精确核验。

### 正式特殊建筑

#### 宗教/信仰/礼仪等硬门，无圣地替代（58定义）

| key／官方简中名 | 额外建造宗教门 | 启用宗教门 | 源文件与行 |
|---|---|---|---|
| `buddhas_of_bamian_01`／梵衍那大佛 | — | E | `common/buildings/00_special_buildings.txt:2461–2507` |
| `notre_dame_01`／巴黎圣母院 | can_construct: C | C | `common/buildings/00_special_buildings.txt:2881–2953` |
| `brihadeeswarar_temple_01`／苾利诃地湿伐罗神庙 | — | E | `common/buildings/00_special_buildings.txt:2959–3031` |
| `shwedagon_pagoda_01`／瑞德宫大金塔 | — | E | `common/buildings/00_special_buildings.txt:3037–3100` |
| `ananda_temple_01`／阿难陀寺 | — | E | `common/buildings/00_special_buildings.txt:3106–3169` |
| `khajuraho_01`／渴树罗城 | — | E | `common/buildings/00_special_buildings.txt:3249–3305` |
| `hall_of_heroes_01`／一级英雄殿 | — | OR(scope:holder.has_religion = religion:baltic_religion, scope:holder.has_religion = religion:slavic_religion, scope:holder.has_religion = religion:finno_ugric_religion, scope:holder.has_religion = religion:siberian_religion) | `common/buildings/00_special_buildings.txt:3665–3699` |
| `hall_of_heroes_02`／二级英雄殿 | — | OR(scope:holder.has_religion = religion:baltic_religion, scope:holder.has_religion = religion:slavic_religion, scope:holder.has_religion = religion:finno_ugric_religion, scope:holder.has_religion = religion:siberian_religion) | `common/buildings/00_special_buildings.txt:3701–3735` |
| `hall_of_heroes_03`／三级英雄殿 | — | OR(scope:holder.has_religion = religion:baltic_religion, scope:holder.has_religion = religion:slavic_religion, scope:holder.has_religion = religion:finno_ugric_religion, scope:holder.has_religion = religion:siberian_religion) | `common/buildings/00_special_buildings.txt:3737–3771` |
| `hall_of_heroes_04`／四级英雄殿 | — | OR(scope:holder.has_religion = religion:baltic_religion, scope:holder.has_religion = religion:slavic_religion, scope:holder.has_religion = religion:finno_ugric_religion, scope:holder.has_religion = religion:siberian_religion) | `common/buildings/00_special_buildings.txt:3773–3807` |
| `hall_of_heroes_05`／五级英雄殿 | — | OR(scope:holder.has_religion = religion:baltic_religion, scope:holder.has_religion = religion:slavic_religion, scope:holder.has_religion = religion:finno_ugric_religion, scope:holder.has_religion = religion:siberian_religion) | `common/buildings/00_special_buildings.txt:3809–3841` |
| `palace_of_ctesiphon_02`／泰西封大王宫 | can_construct: OR(Z, scope:holder.faith = faith:manichaean_faith, scope:holder.faith = faith:nestorian, scope:holder.faith = faith:hellenic_pagan) | — | `common/buildings/00_special_buildings.txt:5275–5335` |
| `church_of_the_theotokos`／诞神女教堂 | can_construct: C | C | `common/buildings/00_special_buildings.txt:6049–6106` |
| `hagios_demetrios`／圣迪弥特里教堂 | can_construct: C | C | `common/buildings/00_special_buildings.txt:6173–6225` |
| `saint_lazarus`／圣拉匝若教堂 | — | C | `common/buildings/00_special_buildings.txt:6284–6337` |
| `sumela_monastery_01`／苏梅拉修道院 | — | C | `common/buildings/00_special_buildings.txt:6342–6399` |
| `sumela_monastery_02`／翻修的苏梅拉修道院 | can_construct: C | C | `common/buildings/00_special_buildings.txt:6401–6461` |
| `meteora_01`／迈泰奥拉 | — | scope:holder.rite.rite_has_doctrine = special_doctrine_is_eastern_christian_faith | `common/buildings/00_special_buildings.txt:6637–6693` |
| `meteora_02`／迈泰奥拉 | — | scope:holder.rite.rite_has_doctrine = special_doctrine_is_eastern_christian_faith | `common/buildings/00_special_buildings.txt:6695–6757` |
| `mount_athos_01`／阿索斯山 | — | scope:holder.rite.rite_has_doctrine = special_doctrine_is_eastern_christian_faith | `common/buildings/00_special_buildings.txt:6762–6811` |
| `mount_athos_02`／阿索斯山 | — | scope:holder.rite.rite_has_doctrine = special_doctrine_is_eastern_christian_faith | `common/buildings/00_special_buildings.txt:6813–6872` |
| `mount_athos_03`／阿索斯山 | — | scope:holder.rite.rite_has_doctrine = special_doctrine_is_eastern_christian_faith | `common/buildings/00_special_buildings.txt:6874–6935` |
| `apollinare_nuovo`／新圣亚坡理纳圣殿 | — | C | `common/buildings/00_special_buildings.txt:6940–6996` |
| `saint_catherine`／圣埃卡特里纳修道院 | — | C | `common/buildings/00_special_buildings.txt:7001–7059` |
| `jvari_monastery`／十字圣架修道院 | — | C | `common/buildings/00_special_buildings.txt:7064–7120` |
| `etchmiadzin_cathedral`／瓦加尔沙帕特主教座堂 | — | scope:holder.rite = rite:armenian_rite | `common/buildings/00_special_buildings.txt:7125–7182` |
| `cattolica_stilo`／斯蒂洛教堂 | can_construct: C | C | `common/buildings/00_special_buildings.txt:7187–7243` |
| `hosios_loukas`／成德者路喀修道院 | can_construct: C | C | `common/buildings/00_special_buildings.txt:7248–7301` |
| `sofia_ohrid`／圣索菲亚教堂 | can_construct: C | C | `common/buildings/00_special_buildings.txt:7306–7362` |
| `leshan_giant_buddha_01`／乐山大佛 | — | OR(E, S) | `common/buildings/00_special_buildings.txt:7799–7855` |
| `yungang_grottoes_01`／云冈石窟 | — | OR(E, S) | `common/buildings/00_special_buildings.txt:7861–7912` |
| `wudang_mountain_temples_01`／武当山道观 | — | OR(E, S) | `common/buildings/00_special_buildings.txt:7918–7965` |
| `shaolin_monastery_01`／少林寺 | — | OR(E, S) | `common/buildings/00_special_buildings.txt:7971–8022` |
| `lingyin_temple_01`／灵隐寺 | — | OR(E, S) | `common/buildings/00_special_buildings.txt:8028–8083` |
| `giant_wild_goose_pagoda_01`／大雁塔 | — | OR(E, S) | `common/buildings/00_special_buildings.txt:8089–8146` |
| `angkor_wat_01`／吴哥窟 | — | E | `common/buildings/00_special_buildings.txt:8355–8414` |
| `po_klong_garai_01`／波克朗加莱塔 | — | E | `common/buildings/00_special_buildings.txt:8519–8569` |
| `borobudur_01`／婆罗浮屠 | — | E | `common/buildings/00_special_buildings.txt:8618–8675` |
| `jokhang_01`／大昭寺 | — | E | `common/buildings/ccp3_special_buildings.txt:274–314` |
| `konark_temple_01`／拘拿罗迦太阳神庙 | — | E | `common/buildings/ccp3_special_buildings.txt:717–758` |
| `vatapi_caves_01`／伐多比窟 | — | E | `common/buildings/ccp3_special_buildings.txt:1085–1121` |
| `mont_st_michel_01`／圣欧伯的圣弥额尔圣堂 | — | C | `common/buildings/cp6_special_buildings.txt:112–175` |
| `mont_st_michel_02`／圣米歇尔山罗马式修道院 | can_construct: OR(C, H) | C | `common/buildings/cp6_special_buildings.txt:180–264` |
| `mont_st_michel_03`／奇迹修道院 | can_construct: OR(C, H) | C | `common/buildings/cp6_special_buildings.txt:269–354` |
| `mont_st_michel_04`／设防的圣米歇尔山修道院 | can_construct: OR(C, H) | C | `common/buildings/cp6_special_buildings.txt:359–444` |
| `sanchi_stupa_01`／散脂大佛塔 | — | E | `common/buildings/cp6_special_buildings.txt:450–510` |
| `buddha_kamakura_01`／镰仓大佛 | — | E | `common/buildings/cp8_special_buildings.txt:44–99` |
| `pyramid_lingapura_01`／陵伽补罗金字塔 | — | E | `common/buildings/cp8_special_buildings.txt:103–155` |
| `maijishan_grottoes_01`／麦积山石窟 | — | OR(E, S) | `common/buildings/cp8_special_buildings.txt:159–212` |
| `three_pagodas_dali_01`／大理三塔 | — | E | `common/buildings/cp8_special_buildings.txt:216–272` |
| `muara_takus_01`／麻拉塔库斯禅邸 | — | E | `common/buildings/cp8_special_buildings.txt:362–415` |
| `stone_pagoda_01`／弥勒寺石塔 | — | E | `common/buildings/cp8_special_buildings.txt:419–469` |
| `temples_angkor_01`／吴哥窟 | — | E | `common/buildings/cp8_special_buildings.txt:990–1038` |
| `temples_angkor_02`／吴哥窟 | — | E | `common/buildings/cp8_special_buildings.txt:1039–1093` |
| `pam_abbey_of_st_gall_01`／圣加仑修道院 | — | C | `common/buildings/pam_buildings.txt:313–365` |
| `pam_palais_de_papes_01`／教宗宫 | — | C | `common/buildings/pam_buildings.txt:370–424` |
| `pam_lateran_basilica_01`／拉特朗圣若望大殿 | — | C | `common/buildings/pam_buildings.txt:429–483` |
| `pam_reims_cathedral_01`／兰斯大教堂 | — | C | `common/buildings/pam_buildings.txt:488–542` |

#### 圣地 AND 宗教条件（2定义）

| key／官方简中名 | 额外建造宗教门 | 启用宗教门 | 源文件与行 |
|---|---|---|---|
| `holy_site_imam_ali_mosque_01`／伊玛目阿里清真寺 | — | AND(H, I) | `common/buildings/00_special_buildings.txt:967–1032` |
| `parthenon`／帕特农神庙 | can_construct: scope:holder.faith.religion = faith:hellenic_pagan.religion | AND(scope:holder.faith.religion = faith:hellenic_pagan.religion, H) | `common/buildings/00_special_buildings.txt:6108–6168` |

#### 圣地 AND 宗教排除条件（1定义）

| key／官方简中名 | 额外建造宗教门 | 启用宗教门 | 源文件与行 |
|---|---|---|---|
| `dome_of_the_rock_01`／圆顶清真寺 | — | AND(H, NOT(J)) | `common/buildings/00_special_buildings.txt:3504–3573` |

#### 圣地 OR 宗教/礼仪等替代（38定义）

| key／官方简中名 | 额外建造宗教门 | 启用宗教门 | 源文件与行 |
|---|---|---|---|
| `holy_site_great_mosque_of_cordoba_01`／科尔多瓦大清真寺 | — | OR(I, C, H) | `common/buildings/00_special_buildings.txt:1113–1189` |
| `holy_site_great_mosque_of_djenne_01`／杰内大清真寺 | can_construct: OR(I, H) | OR(I, H) | `common/buildings/00_special_buildings.txt:1195–1279` |
| `holy_site_great_mosque_of_samarra_01`／萨迈拉大清真寺 | can_construct: OR(I, H) | OR(I, H) | `common/buildings/00_special_buildings.txt:1285–1369` |
| `holy_site_cologne_cathedral_01`／科隆大教堂 | can_construct: OR(C, H) | OR(C, H) | `common/buildings/00_special_buildings.txt:1375–1470` |
| `holy_site_canterbury_cathedral_01`／坎特伯雷圣殿 | can_construct: OR(C, H) | OR(C, H) | `common/buildings/00_special_buildings.txt:1476–1570` |
| `holy_site_canterbury_cathedral_02`／坎特伯雷神殿 | can_construct: OR(C, H) | OR(C, H) | `common/buildings/00_special_buildings.txt:1572–1666` |
| `holy_site_canterbury_cathedral_03`／坎特伯雷主教座堂 | can_construct: OR(C, H) | OR(C, H) | `common/buildings/00_special_buildings.txt:1668–1761` |
| `holy_site_prophetic_mosque_01`／先知清真寺 | can_construct: OR(I, H) | OR(I, H) | `common/buildings/00_special_buildings.txt:1768–1848` |
| `the_friday_mosque_01`／星期五清真寺 | can_construct: I | OR(I, Z, H) | `common/buildings/00_special_buildings.txt:3175–3243` |
| `hagia_sophia_02`／阿亚索菲亚清真寺 | can_construct: I | OR(I, H) | `common/buildings/00_special_buildings.txt:3429–3498` |
| `temple_in_jerusalem_01`／第三圣殿 | can_construct: AND(H, J) | OR(H, J) | `common/buildings/00_special_buildings.txt:3575–3659` |
| `temple_of_uppsala_01`／乌普萨拉神庙 | can_construct: OR(C, H) | OR(C, H) | `common/buildings/00_special_buildings.txt:4445–4523` |
| `temple_of_uppsala_02`／乌普萨拉大教堂 | can_construct: OR(C, H) | OR(C, H) | `common/buildings/00_special_buildings.txt:4525–4604` |
| `lund_cathedral_01`／隆德大教堂 | can_construct: OR(C, H) | OR(C, H) | `common/buildings/00_special_buildings.txt:4610–4686` |
| `holy_site_basilica_santiago_01`／圣地亚哥‑德孔波斯特拉主教座堂 | — | OR(I, C, H) | `common/buildings/00_special_buildings.txt:5018–5088` |
| `imam_reza_shrine_01`／伊玛目里达圣陵 | — | OR(I, H) | `common/buildings/00_special_buildings.txt:5094–5167` |
| `minarets_and_remains_of_jam_01`／贾姆宣礼塔 | can_construct: I | OR(I, H) | `common/buildings/00_special_buildings.txt:5391–5451` |
| `mount_fuji_01`／富士山 | — | OR(scope:holder.religion = religion:shintoism_religion, H, scope:holder.faith.has_doctrine = special_doctrine_immaterial_harmony) | `common/buildings/00_special_buildings.txt:9606–9654` |
| `itsukushima_jinja_01`／严岛神社 | — | OR(scope:holder.religion = religion:shintoism_religion, H, scope:holder.faith.has_doctrine = special_doctrine_immaterial_harmony) | `common/buildings/00_special_buildings.txt:9660–9725` |
| `itsukushima_jinja_02`／严岛神社 | — | OR(scope:holder.religion = religion:shintoism_religion, H, scope:holder.faith.has_doctrine = special_doctrine_immaterial_harmony) | `common/buildings/00_special_buildings.txt:9727–9790` |
| `cluny_abbey_01`／克吕尼修道院 | — | OR(C, H) | `common/buildings/ccp3_special_buildings.txt:72–129` |
| `cluny_abbey_02`／克吕尼大教堂 | — | OR(C, H) | `common/buildings/ccp3_special_buildings.txt:130–186` |
| `damascus_mosque_01`／大马士革大清真寺 | — | OR(I, H) | `common/buildings/ccp3_special_buildings.txt:225–270` |
| `beta_giyorgis_01`／拉利贝拉圣乔治教堂 | — | OR(C, H) | `common/buildings/ccp3_special_buildings.txt:355–398` |
| `holy_wisdom_01`／圣智教堂 | — | OR(C, H) | `common/buildings/ccp3_special_buildings.txt:402–445` |
| `duomo_florence_01`／圣莱伯拉大主教座堂 | — | OR(C, H) | `common/buildings/ccp3_special_buildings.txt:532–573` |
| `duomo_florence_02`／圣若翰洗礼堂 | — | OR(C, H) | `common/buildings/ccp3_special_buildings.txt:574–618` |
| `duomo_florence_03`／圣母百花大教堂 | — | OR(C, H) | `common/buildings/ccp3_special_buildings.txt:619–665` |
| `duomo_florence_04`／圆顶 | — | OR(C, H) | `common/buildings/ccp3_special_buildings.txt:666–713` |
| `wawel_cathedral_01`／圣玛利亚圣亚肋叔咏祷司铎座堂 | — | OR(C, H) | `common/buildings/ccp3_special_buildings.txt:919–972` |
| `wawel_cathedral_02`／圣玛利亚圣亚肋叔总咏祷司铎座堂 | — | OR(C, H) | `common/buildings/ccp3_special_buildings.txt:974–1027` |
| `wawel_cathedral_03`／圣玛利亚与圣亚肋叔主教座堂 | — | OR(C, H) | `common/buildings/ccp3_special_buildings.txt:1029–1081` |
| `holy_site_st_peters_basilica_01`／圣伯多禄大殿 | can_construct: OR(C, H) | OR(C, H) | `common/buildings/cp6_special_buildings.txt:6–107` |
| `boudhanath_01`／觉主塔 | — | OR(H, E) | `common/buildings/cp6_special_buildings.txt:517–587` |
| `yazd_mosque_01`／亚兹德大清真寺 | can_construct: OR(H, I) | OR(H, I) | `common/buildings/cp6_special_buildings.txt:594–685` |
| `qutb_minar_02`／库特卜尖塔 | can_construct: OR(H, I) | OR(I, H) | `common/buildings/cp6_special_buildings.txt:740–823` |
| `qutb_minar_03`／扩建的伊斯兰之力清真寺 | can_construct: OR(H, I) | OR(H, I) | `common/buildings/cp6_special_buildings.txt:829–921` |
| `qutb_minar_04`／阿拉伊尖塔 | can_construct: OR(H, I) | OR(H, I) | `common/buildings/cp6_special_buildings.txt:927–1010` |

#### 圣地关联路线（16定义）

| key／官方简中名 | 额外建造宗教门 | 启用宗教门 | 源文件与行 |
|---|---|---|---|
| `holy_site_cathedral_01`／大宗座圣殿 | can_construct: H | H | `common/buildings/00_special_buildings.txt:26–114` |
| `holy_site_mosque_01`／大清真寺 | can_construct: H | H | `common/buildings/00_special_buildings.txt:116–194` |
| `holy_site_fire_temple_01`／大祆祠 | can_construct: H | H | `common/buildings/00_special_buildings.txt:196–279` |
| `holy_site_pagan_grand_temple_01`／大神庙 | can_construct: H | H | `common/buildings/00_special_buildings.txt:281–367` |
| `holy_site_indian_grand_temple_01`／大神庙 | can_construct: H | H | `common/buildings/00_special_buildings.txt:369–453` |
| `holy_site_buddhist_grand_temple_01`／大寺庙 | can_construct: H | H | `common/buildings/00_special_buildings.txt:455–552` |
| `holy_site_japanese_temple_01`／大社 | can_construct: H | H | `common/buildings/00_special_buildings.txt:554–635` |
| `holy_site_chinese_temple_01`／大寺庙 | can_construct: H | H | `common/buildings/00_special_buildings.txt:637–718` |
| `holy_site_se_asia_pagan_temple_01`／大神庙 | can_construct: H | H | `common/buildings/00_special_buildings.txt:720–801` |
| `holy_site_other_grand_temple_01`／大神庙 | can_construct: H | H | `common/buildings/00_special_buildings.txt:803–886` |
| `holy_site_mahabodhi_temple_01`／摩诃菩提寺 | — | H | `common/buildings/00_special_buildings.txt:895–961` |
| `holy_site_great_mosque_of_mecca_01`／麦加大清真寺 | — | H | `common/buildings/00_special_buildings.txt:1038–1107` |
| `hagia_sophia_01`／圣索菲亚大教堂 | — | H | `common/buildings/00_special_buildings.txt:3360–3427` |
| `mount_baekdu_01`／白头山 | — | H | `common/buildings/00_special_buildings.txt:10204–10244` |
| `my_son_sanctuary_01`／美山圣地 | — | H | `common/buildings/cp8_special_buildings.txt:716–768` |
| `confucius_temple_01`／孔庙 | — | H | `common/buildings/cp8_special_buildings.txt:896–947` |

### 奇观补表

#### 宗教/信仰/礼仪等硬门，无圣地替代（3定义）

| key／官方简中名 | 额外建造宗教门 | 启用宗教门 | 源文件与行 |
|---|---|---|---|
| `great_project_cathedral_01`／罗马式大座堂 | — | scope:holder.has_spiritual_fulfillment_type = christian_fulfillment | `common/buildings/pam_buildings.txt:61–144` |
| `great_project_cathedral_02`／哥特式大座堂 | — | scope:holder.has_spiritual_fulfillment_type = christian_fulfillment | `common/buildings/pam_buildings.txt:146–226` |
| `great_project_cathedral_03`／火焰式尖顶大座堂 | — | scope:holder.has_spiritual_fulfillment_type = christian_fulfillment | `common/buildings/pam_buildings.txt:228–308` |

## 给游玩智能体的比较输入

先固定要解锁或利用的**具体建筑key与等级**，查真实barony holder而非默认玩家。把额外建造门和启用门分别求值，再评估采用/新建到底能补哪个H；若OR宗教分支已满足，增加圣地不是这个分支的必要投入。若是AND硬门，采用补H也不会补齐另一宗教/礼仪条件。

然后读建筑已建/等级/槽位/是否废墟、DLC当前启用、原版Can、实际建造费用及资源，最后独立读启用和正确收件人的净效果。保持`state_observed=false/native_legality=null/action_ready=false`，直到对应实时输入和后验齐全。本清点不授普通战役、当前收益或整个产品PASS。

迁移文件：本Markdown → `docs/ck3-native-ai/special-building-religion-holy-site-gates12004.md`；`catalogue.json`、`source-manifest.json` → 同名evidence目录。完整离线中间AST无需复制成游戏文件或进入运行profile。
