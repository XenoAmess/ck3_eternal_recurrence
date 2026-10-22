# 二期V6：实际图表分页与逐项覆盖

本稿将既有研究落成实际文字表，不新增游戏、媒体或当前菜单资格。machine_id: 4-8e1c2f1861；机器身份承接父任务 faith-e02-director-v6-terminology-20261022-root 的当轮准入。整理时间写于覆盖JSON。

相关章内口播期间持续挂屏、逐行强调，之后再加静音余量；不能在句末闪表冒充覆盖。静音3至6秒不是声称能读完全部文字，而是留出读表及暂停余量。每屏最多6个数据行；实际字号、行高和暂停可读性尚未进行像素验收。

仅三列表格的机制文案用于排版；页面ID、来源ID、key、脚本文件名、JSON指针是作者定位，不进入旁白和成片。表内研究短语是机制说明，不假称官方事件标题。正式界面名由两份V6术语表约束。忠诚栏与意图栏同名的深思熟虑必须保留栏位。

旅行最多同时选2项，低／中／高价为2T／5T／10T；准备充分适用时乘0.75。无只表示定义未另写直接cost，不能讲成整趟免费。金币、国库和牧群分别读实际分支；文化大使金币／国库用中档、牧群用低档。

经验页数字均是基础请求，再套当前增益、逐次写入、旧经验及0至100封顶；互斥分支、随机范围、不同接收人不能相加成必得总数。朝圣者、老道的朝圣者、高效的朝圣者为三档；朝觐者／朝觐妇另无经验轨道。

资料专用页不进视频时长。历史、NPC、调试、创建明确标识，不能剪成普通玩家新增操作。完整原始守卫由来源指针保留，删去内部key不等于可以删去关键资格。

主片 28页，资料 11页；额外静读 **101秒**。

[JSON](knowledge/pilgrimage-v6-screen-coverage-12004.json)


## A01

主片展示 / 本屏3条 / 额外静音4秒

即时收益和类型匹配分别判断；世俗仍有主虔诚，朝觐没有朝觐者经验轨道。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 虔诚朝圣 | 义务朝觐礼仪须先有 朝觐者／朝觐妇；其他人物还须通过通用活动条件 | 虔诚／朝觐 处理分支 增活动表现；按四档增加主虔诚项及合资格朝圣者 经验 |
| 世俗朝圣 | 同上；不是只有愤世嫉俗者可选，那些人格条件出现在 电脑选择权重 | 去程追踪文化；完成仍有距离主虔诚奖励，额外给文化接受度或 5 年人物修正，不使用虔诚表现倍率 |
| 朝觐 | 义务朝觐礼仪或 伊斯兰教且当前礼仪允许朝圣；只能麦加，另有本人首都排除及记忆检查 | 虔诚表现分支；专门到达／仪式链，完成可获朝觐者。不是一个与朝圣者相同的可升级 经验 轨道 |

作者来源（不上屏）：
- `A/pilgrimage_type_pious` -> `SETUP:/activity_options/0`; `SETUP:S01:1392-1441`, `SETUP:S01:1392-1441`, `SETUP:S05:1225-1239`, `SETUP:S05:1301-1337`, `SETUP:S05:632-670`
- `A/pilgrimage_type_worldly` -> `SETUP:/activity_options/1`; `SETUP:S01:1442-1482`, `SETUP:S01:1442-1482`, `SETUP:S10:59-72`, `SETUP:S05:673-874`
- `A/pilgrimage_type_hajj` -> `SETUP:/activity_options/2`; `SETUP:S01:1483-1558`, `SETUP:S01:1483-1558`, `SETUP:S26:1554-1557`, `SETUP:S01:256-265`, `SETUP:S01:2473-2485`, `SETUP:S05:399-485`

## A02

主片展示 / 本屏3条 / 额外静音4秒

本栏倍率只进主虔诚相应位置；速度修正不是最终速度倍数；同名意图另占一栏。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 义不容辞 | 高级活动；穆斯林须义务朝觐或急躁，其他须义务朝圣或急躁 | 进入旅行时附加 旅行速度修正+50%；主虔诚公式前段 ×0.5；抵达通常进入可于一日后离开的事件分支，有条件分支允许留下 |
| 朝圣者 | 默认，无额外门槛 | 没有此栏速度修正或奖励倍率；非朝觐 普通抵达按 3 个月推进阶段 |
| 深思熟虑 | 高级活动，且耐心／朝圣者／朝觐者之一 | 进入旅行时附加 旅行速度修正−50%；主虔诚公式前段 ×1.25 |

作者来源（不上屏）：
- `A/pilgrimage_fidelity_obligatory` -> `SETUP:/activity_options/3`; `SETUP:S01:1564-1637`, `SETUP:S01:1564-1637`, `SETUP:S01:2840-2855`, `SETUP:S15:271-274`, `SETUP:S05:522-531`, `SETUP:S11:9205-9287`
- `A/pilgrimage_fidelity_pilgrim` -> `SETUP:/activity_options/4`; `SETUP:S01:1638-1645`, `SETUP:S01:1638-1645`, `SETUP:S01:2398-2409`
- `A/pilgrimage_fidelity_contemplative` -> `SETUP:/activity_options/5`; `SETUP:S01:1646-1708`, `SETUP:S01:1646-1708`, `SETUP:S01:2857-2867`, `SETUP:S15:276-279`, `SETUP:S05:534-543`

## A03

主片展示 / 本屏4条 / 额外静音5秒

廷臣选择与出发补人是两步。上限和整队目标不是额外新增人数，也不保证最终人数；不要把朴素说成没有任何旅伴。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 朴素 | 高级活动；神贫誓愿个人信条时为默认；减去 10×(阶级系数+时代系数−1) | 无此档专属廷臣选择块；公共随从仍存在。安全 −25；主虔诚后加 50；相应内在之旅礼仪再 ×1.5；出发时向总人数 7 补齐 |
| 适度 | 无额外费用；有高级活动时不能持神贫誓愿强制朴素个人信条 | 核心廷臣权重，选择上限 5；出发时向总人数 5 补齐；无排场虔诚加法 |
| 讲究 | 高级活动，不能持上述神贫誓愿标记；基数 50 | 核心+额外廷臣权重，上限 10；向总人数 10 补齐；主虔诚后加 50 |
| 盛况空前 | 同上；基数 100 | 加上更广泛同信仰廷臣权重，上限 20；向总人数 20 补齐；主虔诚后加 100 |

作者来源（不上屏）：
- `A/pilgrimage_pomp_humble` -> `SETUP:/activity_options/6`; `SETUP:S01:1714-1796`, `SETUP:S01:1714-1796`, `SETUP:S01:2655-2659`, `SETUP:S01:2870-2880`, `SETUP:S14:2158-2304`, `SETUP:S14:2456-2470`, `SETUP:S05:569-607`
- `A/pilgrimage_pomp_appropriate` -> `SETUP:/activity_options/7`; `SETUP:S01:1797-1825`, `SETUP:S01:1797-1825`, `SETUP:S06:160-216`, `SETUP:S14:2471-2485`
- `A/pilgrimage_pomp_ceremonial` -> `SETUP:/activity_options/8`; `SETUP:S01:1826-1973`, `SETUP:S01:1826-1973`, `SETUP:S06:160-251`, `SETUP:S14:2486-2500`, `SETUP:S05:569-584`
- `A/pilgrimage_pomp_throng` -> `SETUP:/activity_options/9`; `SETUP:S01:1974-2121`, `SETUP:S01:1974-2121`, `SETUP:S06:160-283`, `SETUP:S14:2501-2515`, `SETUP:S05:586-595`

## I01

主片展示 / 本屏2条 / 额外静音4秒

已有特质和经验能使同一回应改付另一种资源，费用、表现和经验的守卫分别看。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 深思熟虑 | 开启反省事件及目的地活动行为；默认意图不等于固定奖励 | 停下来沉思会延迟10天；无朝圣者时给50虔诚，已有且未满时给10基础经验，满轨后另给100虔诚。虔诚／朝觐下另可能+10活动表现；性格还能改变压力。原有状态决定同一回应写入哪种奖励 |
| 行善 | 开启施舍、照料等选项，检查地点、身份及扩展内容包；有些花动态金币换虔诚、地方效果或好感 | 海上共同事件的行善项可给随行者好感、合资格朝圣者+5基础经验及虔诚类表现+10；目的地照料旅行者、捐寺和济贫分别有自己的费用与所得，不统一固定给分 |

作者来源（不上屏）：
- `I/reflection_intent` -> `SETUP:/intents/1`; `SETUP:S02:4-45`, `SETUP:S01:2645-2653`, `SETUP:S02:4-45`, `SETUP:S09:73-78`, `SETUP:S12:781-845`, `SETUP:S08:294-481`
- `I/altruism_intent` -> `SETUP:/intents/2`; `SETUP:S03:65-131`, `SETUP:S03:65-131`, `SETUP:S09:62-66`, `SETUP:S08:594-700`, `SETUP:S43:640-1158`, `SETUP:S12:1963-1994`

## I02

主片展示 / 本屏2条 / 额外静音4秒

尝试与成功另判。娱乐为共享候选，用虚线标当前集合未知；不能仿造当前第四菜单。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 热忱 | 开启传教、招募、宗教交流及相关目的地行为；实际改信还要看目标和结果 | 一次传教动作先调用虔诚表现处理分支，再判外交／学识挑战。成功可能改目标信仰并给虔诚，失败可能损失虔诚；表现上升不能证明传教成功，也不是自动获得狂热人格 |
| 娱乐 | 通用意图没有选择即固定减压；相关酒馆朋友事件权重可乘2，仍检查朋友、Friends & Foes内容包和旅程进度等条件 | 邀请聊天会延迟30天并读世俗表现处理分支；合群可减压，害羞或狂热者可加压；后续狂欢者特质等依事件另判。不能把娱乐等同稳拿朝圣者经验 |

作者来源（不上屏）：
- `I/zealot_intent` -> `SETUP:/intents/3`; `SETUP:S02:48-104`, `SETUP:S02:48-104`, `SETUP:S09:67-72`, `SETUP:S12:25-100`, `SETUP:S08:486-590`
- `I/reduce_stress_intent` -> `SETUP:/intents/0`; `SETUP:S04:3-17`, `SETUP:S04:3-17`, `SETUP:S11:8071-8134`, `SETUP:S09:57-58`, `SETUP:S21:126-137`, `SETUP:S11:8211-8509`

## T01

主片展示 / 本屏5条 / 额外静音3秒

按本页身份条件显示，不拼成F0公爵同时可选29项；明确资源与费用档及每项真正改动的安全、速度、事件或人物结果。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 搜索人才 | 冒险者，未有 服从上级；无 | 速度 −5；移动后人才招募池；该 技能 自身也可直接开启池 |
| 高风险交易 | 冒险者、以怖治军；无 | 安全 −20；有战利品的地点给动态交易收入，逐地点记账防重复 |
| 搜寻秘密 | 冒险者、深挖黑料；无 | 速度 +10／安全 −10；密谋值百分比机会得合资格秘密 |
| 鼓励关系 | 冒险者、层层效忠、至少 3 成年廷臣；无 | 速度 +5／安全 −5；移动后婚姻、友谊、情人事件池 |
| 搜集灵感 | 冒险者、大众领袖；无 | 速度 +5／安全 −5；管理÷6（至少1）概率给合资格廷臣灵感 |

作者来源（不上屏）：
- `T/adventurers_scout_for_talent_option` -> `SETUP:/travel_options/0`; `SETUP:S17:1-23`, `SETUP:S10:2166-2187`
- `T/adventurers_make_local_deals_option` -> `SETUP:/travel_options/1`; `SETUP:S17:25-46`, `SETUP:S10:327-343`
- `T/adventurers_search_for_secrets_option` -> `SETUP:/travel_options/2`; `SETUP:S17:48-70`, `SETUP:S10:344-404`
- `T/adventurers_encourage_relationships_option` -> `SETUP:/travel_options/3`; `SETUP:S17:72-98`, `SETUP:S10:2190-2203`
- `T/adventurers_gather_inspiration_option` -> `SETUP:/travel_options/4`; `SETUP:S17:100-122`, `SETUP:S10:453-483`

## T02

主片展示 / 本屏5条 / 额外静音3秒

按本页身份条件显示，不拼成F0公爵同时可选29项；明确资源与费用档及每项真正改动的安全、速度、事件或人物结果。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 向当地人传教 | 冒险者、神权制或对应个人信条资格决定是否显示；热忱宣教技能或相应个人信条决定是否可用；无直接费用 | 速度 +5／安全 −5；学识百分比机会改当地合资格流浪者**礼仪**并给 25 虔诚 |
| 斥候 | 冒险者及营地解锁参数；无 | 安全 +20／速度 −5 |
| 购买探路者装备 | 冒险者统治者；低 | 山地、丘陵、湿地、洪泛平原低档危险削减 |
| 购买旱地探索者物品 | 同上；低 | 沙漠、草原、旱地、沙漠山地低档危险削减 |
| 购买荒野工具包 | 同上；低 | 森林、针叶林、丛林低档危险削减 |

作者来源（不上屏）：
- `T/adventurers_proselytize_zealously_option` -> `SETUP:/travel_options/5`; `SETUP:S17:124-155`, `SETUP:S10:405-452`
- `T/adventurers_forward_scouts_option` -> `SETUP:/travel_options/6`; `SETUP:S17:157-180`, `SETUP:S18:15-28`
- `T/purchase_rough_terrain_gear_option` -> `SETUP:/travel_options/7`; `SETUP:S17:182-231`, `SETUP:S19:48-95`, `SETUP:S18:21-22`
- `T/purchase_desert_gear_option` -> `SETUP:/travel_options/8`; `SETUP:S17:233-281`, `SETUP:S19:48-95`, `SETUP:S18:21-22`
- `T/purchase_forest_gear_option` -> `SETUP:/travel_options/9`; `SETUP:S17:283-329`, `SETUP:S19:48-95`, `SETUP:S18:21-22`

## T03

主片展示 / 本屏5条 / 额外静音3秒

按本页身份条件显示，不拼成F0公爵同时可选29项；明确资源与费用档及每项真正改动的安全、速度、事件或人物结果。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 雇佣经验丰富的船长 | 统治者；中 | 沿海／海域危险 −45；招募或创建临时船长并同行 |
| 雇佣佣兵卫队 | 有范围内合资格闲置佣兵首领；高 | 速度 +10／安全 +20；加首领同伴，不等于获得一整支可作战佣兵军 |
| 雇佣丛林追猎者 | 统治者、非冒险者；低 | 丛林中档危险削减，临时向导 |
| 雇佣登山者 | 同上；低 | 山地／沙漠山地／丘陵中档危险削减，临时向导 |
| 雇佣涉水者 | 非冒险者且可玩统治者；低 | 湿地／洪泛平原中档危险削减，临时向导 |

作者来源（不上屏）：
- `T/experienced_captains_option` -> `SETUP:/travel_options/10`; `SETUP:S17:331-497`, `SETUP:S17:381-490`, `SETUP:S19:45-46`, `SETUP:S37:1583-1613`
- `T/hire_experienced_mercenaries_option` -> `SETUP:/travel_options/11`; `SETUP:S17:499-636`, `SETUP:S17:499-637`, `SETUP:S37:1583-1613`
- `T/hire_jungle_expert_option` -> `SETUP:/travel_options/12`; `SETUP:S17:638-810`, `SETUP:S17:638-811`, `SETUP:S37:1583-1613`
- `T/hire_mountaineer_option` -> `SETUP:/travel_options/13`; `SETUP:S17:812-987`, `SETUP:S17:812-988`, `SETUP:S37:1583-1613`
- `T/hire_forder_option` -> `SETUP:/travel_options/14`; `SETUP:S17:989-1163`, `SETUP:S17:989-1164`, `SETUP:S37:1583-1613`

## T04

主片展示 / 本屏5条 / 额外静音3秒

按本页身份条件显示，不拼成F0公爵同时可选29项；明确资源与费用档及每项真正改动的安全、速度、事件或人物结果。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 雇佣沙漠战士 | 统治者、非冒险者；低 | 沙漠／草原／旱地中档危险削减，临时向导 |
| 雇佣森林向导 | 同上；低 | 森林／针叶林中档危险削减，临时向导 |
| 带上医疗设备 | 统治者，现任私人医生由电脑控制且可行动；低 | 只减瘟疫危险；不是凭按钮新雇一名医师 |
| 雇佣文化大使 | 统治者；中，牧群分支低 | 加大使同伴；移动中按实际名单分支增文化接受度，不是所有地点无条件立刻给 |
| 私人军队 | 启用Wandering Nobles内容包、已有佣兵合同技能；无直接费用 | 速度 +5／安全 +5 |

作者来源（不上屏）：
- `T/hire_desert_warrior_option` -> `SETUP:/travel_options/15`; `SETUP:S17:1165-1340`, `SETUP:S17:1165-1341`, `SETUP:S37:1583-1613`
- `T/hire_rough_terrain_expert_option` -> `SETUP:/travel_options/16`; `SETUP:S17:1342-1515`, `SETUP:S17:1342-1516`, `SETUP:S37:1583-1613`
- `T/court_physician_option` -> `SETUP:/travel_options/17`; `SETUP:S17:1517-1586`, `SETUP:S17:1517-1586`, `SETUP:S07:1456-1489`
- `T/cultural_ambassador_option` -> `SETUP:/travel_options/18`; `SETUP:S17:1588-1766`, `SETUP:S17:1638-1702`, `SETUP:S10:108-163`
- `T/hire_allied_mercenaries_option` -> `SETUP:/travel_options/19`; `SETUP:S17:1768-1785`, `SETUP:S18:15-22`

## T05

主片展示 / 本屏5条 / 额外静音3秒

按本页身份条件显示，不拼成F0公爵同时可选29项；明确资源与费用档及每项真正改动的安全、速度、事件或人物结果。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 安抚 | 启用Wandering Nobles内容包、已有一方英雄技能；无直接费用 | 月暴政 −0.8／月恐怖 −0.4 |
| 悠闲之旅 | 同上；无 | 速度 −20／压力获得修正 −0.5；完成后经过省份数×15**威望经验** |
| 教学之旅 | 启用Wandering Nobles内容包、已有地利人和技能；有未满15岁、同地且可随行的玩家继承人；无直接费用 | 速度 −5／儿童好感 +5；带继承人，走本人不同地产授业，最多 8 个地点 |
| 优良坐骑 | 非冒险者，直属地产马厩04或骆驼牧场04；无 | 速度 +20 |
| 训练骑士 | 公爵以上、非冒险者、军校01；无 | 安全 +10；选至多 3 名较弱现有骑士同行、进入训练递归事件 |

作者来源（不上屏）：
- `T/appeasement_option` -> `SETUP:/travel_options/20`; `SETUP:S17:1787-1804`, `SETUP:S18:21-22`
- `T/leisurely_option` -> `SETUP:/travel_options/21`; `SETUP:S17:1806-1830`, `SETUP:S10:1531-1547`
- `T/tutor_child_option` -> `SETUP:/travel_options/22`; `SETUP:S17:1832-1902`, `SETUP:S17:1832-1901`, `SETUP:S36:525-619`
- `T/fancy_mounts_option` -> `SETUP:/travel_options/23`; `SETUP:S17:1904-1926`, `SETUP:S18:15-19`
- `T/military_recruits_option` -> `SETUP:/travel_options/24`; `SETUP:S17:1928-1983`, `SETUP:S17:1928-1983`, `SETUP:S38:187-308`

## T06

主片展示 / 本屏4条 / 额外静音3秒

按本页身份条件显示，不拼成F0公爵同时可选29项；明确资源与费用档及每项真正改动的安全、速度、事件或人物结果。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 优良军备 | 公爵以上、非冒险者、铁匠01；无 | 安全 +10，宝物损耗减少修正−20% |
| 加快脚步 | 统治者且急躁／怯懦／鲁莽之一；无 | 速度 +20／安全 −10 |
| 谨慎 | 统治者且善变／专断／多疑之一；无 | 速度 −10；敌对阴谋阶段延长、成功率 −50 |
| 华丽的马匹 | 住所马匹解锁参数；无 | 速度 +10／同伴好感 +10／月威望 +1 |

作者来源（不上屏）：
- `T/superior_armaments_option` -> `SETUP:/travel_options/25`; `SETUP:S17:1985-2008`, `SETUP:S18:15-22`
- `T/anxious_option` -> `SETUP:/travel_options/26`; `SETUP:S17:2010-2032`, `SETUP:S18:15-19`
- `T/circumspect_option` -> `SETUP:/travel_options/27`; `SETUP:S17:2034-2060`, `SETUP:S18:15-22`
- `T/estate_mounts_option` -> `SETUP:/travel_options/28`; `SETUP:S17:2062-2084`, `SETUP:S18:15-22`

## X01

主片展示 / 本屏5条 / 额外静音3秒

表现先判档，基础经验请求再经过增益、旧经验与上限。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 通用朝圣者经验请求 | 已有朝圣者且经验不足100；实际调用资格另判 | 5 |
| 虔诚类完美表现结算 | 已有朝圣者且经验不足100；至少75分档 | 40 |
| 虔诚类高表现结算 | 已有朝圣者且经验不足100；50至不足75分档 | 20 |
| 虔诚类中表现结算 | 已有朝圣者且经验不足100；25至不足50分档 | 10 |
| 虔诚类低表现结算 | 已有朝圣者且经验不足100；不足25分档 | 5 |

作者来源（不上屏）：
- `W/W039` -> `TRAITS:/writers/38`; `TRAITS:W039`, `TRAITS:S186:497-500`
- `W/W040` -> `TRAITS:/writers/39`; `TRAITS:W040`, `TRAITS:S186:643-646`
- `W/W041` -> `TRAITS:/writers/40`; `TRAITS:W041`, `TRAITS:S186:650-653`
- `W/W042` -> `TRAITS:/writers/41`; `TRAITS:W042`, `TRAITS:S186:657-660`
- `W/W043` -> `TRAITS:/writers/42`; `TRAITS:W043`, `TRAITS:S186:664-667`

## X02

主片展示 / 本屏5条 / 额外静音3秒

抵达与结算是两次入口；缺limit和空分支未闭，不能承诺每次重访固定经验。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 抵达主办者：保护路线分支 | 已有朝圣者且经验不足100；启用By God Alone内容包、本信仰有保护朝圣路线状态；异常外层条件语义仍待核 | 30 |
| 抵达主办者：异常后续分支 | 前一保护路线条件不成立，且经验不足100的空分支未先接走；不是重访必得 | 20 |
| 抵达参加者：保护路线分支 | 非主办、已有朝圣者且经验不足100；By God Alone内容包及保护路线状态；异常外层待核 | 20 |
| 抵达参加者：另一分支 | 非主办、已有朝圣者且经验不足100；前一保护路线分支不成立；异常外层待核 | 10 |
| 抵达时的旅团经验 | 已有朝圣者并通过该循环筛选；不预先检查经验是否不足100 | 10 |

作者来源（不上屏）：
- `W/W033` -> `TRAITS:/writers/32`; `TRAITS:W033`, `TRAITS:S186:246-249`
- `W/W034` -> `TRAITS:/writers/33`; `TRAITS:W034`, `TRAITS:S186:260-263`
- `W/W035` -> `TRAITS:/writers/34`; `TRAITS:W035`, `TRAITS:S186:292-295`
- `W/W036` -> `TRAITS:/writers/35`; `TRAITS:W036`, `TRAITS:S186:304-307`
- `W/W037` -> `TRAITS:/writers/36`; `TRAITS:W037`, `TRAITS:S186:386-389`

## X03

主片展示 / 本屏5条 / 额外静音3秒

明确实际收经验的人；性格是分支资格，不是统一经验倍率。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 朝觐的非穆斯林旅伴 | 非穆斯林、目的地为本信仰圣地、已有朝圣者；不预先检查经验是否不足100 | 10 |
| 酒馆朋友事件的狂热回应 | 启用Friends & Foes内容包、符合朋友及旅团事件资格；穆斯林另检查酒鬼门槛；已有朝圣者且经验不足100 | 5 |
| 旅伴事件的回应 | 实际旅伴事件条件成立；狂热或睚眦必报；已有朝圣者且经验不足100 | 10 |
| 宫廷和随行者事件的回应 | 实际宫廷与随行者条件成立；狂热；已有朝圣者且经验不足100 | 20 |
| 深思熟虑意图的还愿物回应 | 深思熟虑意图、非腾格里、事件已保存对应宝物对象；已有朝圣者且经验不足100；宝物对象不是特质 | 20 |

作者来源（不上屏）：
- `W/W038` -> `TRAITS:/writers/37`; `TRAITS:W038`, `TRAITS:S186:475-478`
- `W/W063` -> `TRAITS:/writers/62`; `TRAITS:W063`, `TRAITS:S227:8190-8193`
- `W/W064` -> `TRAITS:/writers/63`; `TRAITS:W064`, `TRAITS:S227:10889-10892`
- `W/W065` -> `TRAITS:/writers/64`; `TRAITS:W065`, `TRAITS:S227:13622-13625`
- `W/W066` -> `TRAITS:/writers/65`; `TRAITS:W066`, `TRAITS:S227:14287-14290`

## X04

主片展示 / 本屏5条 / 额外静音3秒

宗教、学识、地点与个人性格改变可进入的回应。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 基督教旅途回应 | 基督教、有效陆地位置、达到所需学识门槛；已有朝圣者且经验不足100 | 10 |
| 伊斯兰旅途回应 | 伊斯兰、有效陆地位置、非愤世嫉俗；已有朝圣者且经验不足100 | 5 |
| 印度教旅途回应 | 印度教、有效陆地位置；已有朝圣者且经验不足100 | 5 |
| 自然中的宗教回应 | 印度教／佛教／耆那教，或当前礼仪有自然神圣条件；森林／丛林／针叶林、旅程进度不足80%；已有朝圣者且经验不足100 | 20 |
| 佛教旅途回应 | 佛教、有效陆地位置、达到所需学识门槛；已有朝圣者且经验不足100 | 10 |

作者来源（不上屏）：
- `W/W058` -> `TRAITS:/writers/57`; `TRAITS:W058`, `TRAITS:S227:7234-7237`
- `W/W059` -> `TRAITS:/writers/58`; `TRAITS:W059`, `TRAITS:S227:7359-7362`
- `W/W060` -> `TRAITS:/writers/59`; `TRAITS:W060`, `TRAITS:S227:7432-7435`
- `W/W061` -> `TRAITS:/writers/60`; `TRAITS:W061`, `TRAITS:S227:7532-7535`
- `W/W062` -> `TRAITS:/writers/61`; `TRAITS:W062`, `TRAITS:S227:7622-7625`

## X05

主片展示 / 本屏4条 / 额外静音3秒

无特质、已有未满、已满可改付不同资源；即时写入与选择后写入分开。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 深思熟虑意图：停下沉思 | 已有朝圣者且经验不足100才给经验；无特质者另给虔诚 | 10 |
| 深思熟虑意图的即时结果甲 | 已有朝圣者；不预先检查经验是否不足100 | 10 |
| 深思熟虑意图的即时结果乙 | 已有朝圣者且经验不足100 | 10 |
| 深思熟虑意图：说明动机 | 深思熟虑意图；已有朝圣者且经验不足100 | 5 |

作者来源（不上屏）：
- `W/W067` -> `TRAITS:/writers/66`; `TRAITS:W067`, `TRAITS:S229:827-830`
- `W/W068` -> `TRAITS:/writers/67`; `TRAITS:W068`, `TRAITS:S229:1042-1045`
- `W/W069` -> `TRAITS:/writers/68`; `TRAITS:W069`, `TRAITS:S229:1173-1176`
- `W/W070` -> `TRAITS:/writers/69`; `TRAITS:W070`, `TRAITS:S229:1812-1815`

## X06

主片展示 / 本屏4条 / 额外静音3秒

四个回应各有资格，不能把同一事件四项奖励加成必得总数。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 海上旅伴：行善回应 | 海上旅伴事件资格、行善意图；已有朝圣者且经验不足100 | 5 |
| 海上旅伴：深思熟虑回应 | 同一海上旅伴事件资格、深思熟虑意图；已有朝圣者且经验不足100 | 5 |
| 海上旅伴：热忱回应 | 同一海上旅伴事件资格、热忱意图；已有朝圣者且经验不足100 | 5 |
| 海上旅伴：照料回应 | 身心俱悉、草药师、巫师资格或医生四选一；没有该事件既有照料修正；已有朝圣者且经验不足100 | 10 |

作者来源（不上屏）：
- `W/W071` -> `TRAITS:/writers/70`; `TRAITS:W071`, `TRAITS:S229:1986-1989`
- `W/W072` -> `TRAITS:/writers/71`; `TRAITS:W072`, `TRAITS:S229:2013-2016`
- `W/W073` -> `TRAITS:/writers/72`; `TRAITS:W073`, `TRAITS:S229:2040-2043`
- `W/W074` -> `TRAITS:/writers/73`; `TRAITS:W074`, `TRAITS:S229:2114-2117`

## X07

主片展示 / 本屏4条 / 额外静音3秒

重要地点也可成长；大教堂的互斥分支只取实际进入的一项。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 圣人墓重要地点 | 已有朝圣者；省份有圣人时须本信仰承认；不预先检查经验是否不足100 | 随机 3–5 |
| 大教堂重要地点第一分支 | 已有朝圣者；具有加长中殿对应状态 | (随机 3–5)×2 |
| 大教堂重要地点第二分支 | 已有朝圣者；前项不成立，具有对应朝圣经验状态 | (随机 3–5)×1.5 |
| 大教堂重要地点第三分支 | 已有朝圣者；前两项不成立，具有对应教堂玻璃状态 | (随机 3–5)×2 |

作者来源（不上屏）：
- `W/W044` -> `TRAITS:/writers/43`; `TRAITS:W044`, `TRAITS:S216:30-33`
- `W/W045` -> `TRAITS:/writers/44`; `TRAITS:W045`, `TRAITS:S217:1846-1852`
- `W/W046` -> `TRAITS:/writers/45`; `TRAITS:W046`, `TRAITS:S217:1862-1868`
- `W/W047` -> `TRAITS:/writers/46`; `TRAITS:W047`, `TRAITS:S217:1877-1883`

## X08

主片展示 / 本屏3条 / 额外静音3秒

营地和建筑等活动外入口也可成长，因此等级不能倒推朝圣次数。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 营地故事的经验 | 同信仰第二名参加者已有朝圣者；不预先检查经验是否不足100 | 整数随机 20–40 |
| 传奇圣所建成 | 该伯爵领持有者已有朝圣者 | 30 |
| 传奇圣所建成后首次授予 | 该伯爵领持有者原无特质；先授予朝圣者，再给经验 | 30 |

作者来源（不上屏）：
- `W/W002` -> `TRAITS:/writers/1`; `TRAITS:W002`, `TRAITS:S010:1769-1777`
- `W/W004` -> `TRAITS:/writers/3`; `TRAITS:W004`, `TRAITS:S016:82-85`
- `W/W005` -> `TRAITS:/writers/4`; `TRAITS:W005`, `TRAITS:S016:89-92`

## X09

主片展示 / 本屏3条 / 额外静音3秒

随机结果和大项目状态另判，不是每趟必遇。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 学识合约的随机结果 | 实际随机列表的对应分支被选中；被作用者已有朝圣者；不预先检查经验是否不足100 | 整数随机 20–40 |
| 大教堂大项目结果甲 | 已有朝圣者；大教堂状态和人物经验分别写入 | (随机 3–5)×1.5 |
| 大教堂大项目结果乙 | 已有朝圣者，且实际大项目事件分支成立 | (随机 3–5)×2 |

作者来源（不上屏）：
- `W/W080` -> `TRAITS:/writers/79`; `TRAITS:W080`, `TRAITS:S239:4131-4139`
- `W/W082` -> `TRAITS:/writers/81`; `TRAITS:W082`, `TRAITS:S248:221-227`
- `W/W083` -> `TRAITS:/writers/82`; `TRAITS:W083`, `TRAITS:S248:622-628`

## X10

主片展示 / 本屏3条 / 额外静音3秒

前一分支可能先给学识或神秘主义者经验，不能把所有潜在奖励累计。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 旅行中的特殊回应 | 有本事件记录的旅行人物旗标、已有朝圣者且经验不足100；前一学识替代奖励分支未接走；人物旗标不是特质 | 5 |
| 神秘人事件的结果 | 此前无神秘主义者、神秘主义者经验未满、学识生活方式分支均未接走；已有朝圣者且经验不足100 | 10 |
| 热忱回应 | 热忱意图，或狂热且无不信者秘密；已有朝圣者且经验不足100 | 5 |

作者来源（不上屏）：
- `W/W055` -> `TRAITS:/writers/54`; `TRAITS:W055`, `TRAITS:S227:3263-3266`
- `W/W056` -> `TRAITS:/writers/55`; `TRAITS:W056`, `TRAITS:S227:3622-3625`
- `W/W057` -> `TRAITS:/writers/56`; `TRAITS:W057`, `TRAITS:S227:4732-4735`

## DX01

资料专用，不进影片 / 本屏2条 / 额外静音0秒

资料页不进主片；生成、开局、历史、调试与事件NPC分开，不伪装成玩家按钮。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| debug 专属“Wild Goose Chase”，已有 朝圣者；无 <100 guard | debug 专属“Wild Goose Chase”，已有 朝圣者；无 <100 guard | 5 |
| traveler_character 生成后，若已获得 朝圣者；无 <100 guard | traveler_character 生成后，若已获得 朝圣者；无 <100 guard | 随机范围 55–80 |

作者来源（不上屏）：
- `W/W007` -> `TRAITS:/writers/6`; `TRAITS:W007`, `TRAITS:S052:32-35`
- `W/W020` -> `TRAITS:/writers/19`; `TRAITS:W020`, `TRAITS:S177:577-583`

## G01

主片展示 / 本屏4条 / 额外静音4秒

先讲实际接收者，再讲获得条件。首次直接授予初始化0，后续事件仍可另加经验；朝圣者和朝觐者不自动互换。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 普通抵达主持人／朝圣者 | 处理分支 中的 当前主办者，无特质 / 玩家或电脑角色均可能，依实际接收者 | 朝圣者 |
| 普通抵达参加者／朝圣者 | 处理分支 中非主持人的当前接收者，无特质 / 玩家或电脑角色均可能，依实际接收者 | 朝圣者 |
| 普通抵达 处理分支 的朝觐旅队支路／朝觐者／朝觐妇 | 主办者走朝觐，旅团中存在伊斯兰且走朝觐的角色；随后逐人循环给尚无朝觐特质者，循环未重复同一宗教筛选 | 朝觐者／朝觐妇 |
| 普通抵达 处理分支 的朝圣者旅队支路／朝圣者 | 主办者的旅团存在通过宗教及朝觐排除条件、且把目的地视作自身信仰圣地的人；逐人另排除同时为伊斯兰且目的地麦加者，再给无朝圣者者 | 朝圣者 |

作者来源（不上屏）：
- `W/W026` -> `TRAITS:/writers/25`; `TRAITS:W026`, `TRAITS:S186:234-234`
- `W/W027` -> `TRAITS:/writers/26`; `TRAITS:W027`, `TRAITS:S186:280-280`
- `W/W028` -> `TRAITS:/writers/27`; `TRAITS:W028`, `TRAITS:S186:339-339`
- `W/W029` -> `TRAITS:/writers/28`; `TRAITS:W029`, `TRAITS:S186:382-382`

## G02

主片展示 / 本屏4条 / 额外静音4秒

先讲实际接收者，再讲获得条件。首次直接授予初始化0，后续事件仍可另加经验；朝圣者和朝觐者不自动互换。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 朝觐完成本人／朝觐者／朝觐妇 | 处理分支 当前接收者，无 朝觐者／朝觐妇 / 玩家或电脑角色均可能，依实际接收者 | 朝觐者／朝觐妇 |
| 朝觐完成穆斯林旅队／朝觐者／朝觐妇 | 宗教为伊斯兰且无朝觐者／朝觐妇的随行者 / 随行角色 | 朝觐者／朝觐妇 |
| 朝觐完成非穆斯林旅队／朝圣者 | 非穆斯林、自信仰圣地条件且无朝圣者的随行者 / 随行角色 | 朝圣者 |
| 麦加首都补发／朝觐者／朝觐妇 | 麦加首都月度事件实际选出并触发身份授予的角色；玩家或电脑角色均可能，依实际接收者 | 朝觐者／朝觐妇 |

作者来源（不上屏）：
- `W/W030` -> `TRAITS:/writers/29`; `TRAITS:W030`, `TRAITS:S186:404-404`
- `W/W031` -> `TRAITS:/writers/30`; `TRAITS:W031`, `TRAITS:S186:433-433`
- `W/W032` -> `TRAITS:/writers/31`; `TRAITS:W032`, `TRAITS:S186:471-471`
- `W/W048` -> `TRAITS:/writers/47`; `TRAITS:W048`, `TRAITS:S226:78-78`

## G03

主片展示 / 本屏4条 / 额外静音4秒

先讲实际接收者，再讲获得条件。首次直接授予初始化0，后续事件仍可另加经验；朝圣者和朝觐者不自动互换。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 营地虔诚故事／朝圣者 | 同信仰第二参加者，无特质时 / 玩家或电脑角色均可能，依实际接收者 | 朝圣者 |
| 传奇圣所／朝圣者 | 建成时 该伯爵领持有者 / 玩家或电脑角色均可能，依实际接收者 | 朝圣者 |
| The Fate of Iberia内容包的朝圣决斗 | 该朝圣决斗事件中实际成功的角色；玩家或电脑角色均可能 | 朝圣者 |
| 圣骑士团成员／朝圣者 | 无朝圣者、有圣骑士团成员身份，且领主领导本信仰圣骑士团的角色 / 身份角色 | 朝圣者 |

作者来源（不上屏）：
- `W/W001` -> `TRAITS:/writers/0`; `TRAITS:W001`, `TRAITS:S010:1780-1780`
- `W/W003` -> `TRAITS:/writers/2`; `TRAITS:W003`, `TRAITS:S016:88-88`
- `W/W081` -> `TRAITS:/writers/80`; `TRAITS:W081`, `TRAITS:S243:3438-3438`
- `W/W085` -> `TRAITS:/writers/84`; `TRAITS:W085`, `TRAITS:S259:451-451`

## DG01

资料专用，不进影片 / 本屏5条 / 额外静音0秒

资料页不进主片；生成、开局、历史、调试与事件NPC分开，不伪装成玩家按钮。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| Wild Goose Chase／朝圣者 | 使用调试决议者 / 调试专属 | 朝圣者 |
| 朝圣队领袖／朝圣者 | 有 peasant_pilgrim_leader 标记的随行者，后移出角色 / 事件NPC | 朝圣者 |
| 开局麦加／朝觐者／朝觐妇 | 麦加持有者，mandatory_hajj / 非固定NPC | 朝觐者／朝觐妇 |
| 设计统治者麦加／朝觐者／朝觐妇 | 新设计角色，麦加持有者且mandatory_hajj / 设计角色 | 朝觐者／朝觐妇 |
| 建筑师生成／朝圣者 | master_mason_character，新角色随机分支5 / 生成NPC | 朝圣者 |

作者来源（不上屏）：
- `W/W006` -> `TRAITS:/writers/5`; `TRAITS:W006`, `TRAITS:S052:38-38`
- `W/W008` -> `TRAITS:/writers/7`; `TRAITS:W008`, `TRAITS:S086:163-163`
- `W/W009` -> `TRAITS:/writers/8`; `TRAITS:W009`, `TRAITS:S090:656-656`
- `W/W010` -> `TRAITS:/writers/9`; `TRAITS:W010`, `TRAITS:S092:37-37`
- `W/W011` -> `TRAITS:/writers/10`; `TRAITS:W011`, `TRAITS:S173:1599-1599`

## DG02

资料专用，不进影片 / 本屏5条 / 额外静音0秒

资料页不进主片；生成、开局、历史、调试与事件NPC分开，不伪装成玩家按钮。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 本地朝圣者生成／朝圣者 | location_pilgrim_template 对应分支 / 生成NPC | 朝圣者 |
| 本地朝觐者生成／朝觐者／朝觐妇 | 同模板另一对应分支 / 生成NPC | 朝觐者／朝觐妇 |
| 旅行者生成／朝圣者 | traveler_character 随机分支20 / 生成NPC | 朝圣者 |
| 旅行者生成／朝圣者 | 同模板随机分支10 / 生成NPC | 朝圣者 |
| 资深交际花生成／朝圣者 | experienced_courtesan_character 随机分支10 / 生成NPC | 朝圣者 |

作者来源（不上屏）：
- `W/W012` -> `TRAITS:/writers/11`; `TRAITS:W012`, `TRAITS:S174:1124-1124`
- `W/W013` -> `TRAITS:/writers/12`; `TRAITS:W013`, `TRAITS:S174:1129-1129`
- `W/W018` -> `TRAITS:/writers/17`; `TRAITS:W018`, `TRAITS:S177:533-533`
- `W/W019` -> `TRAITS:/writers/18`; `TRAITS:W019`, `TRAITS:S177:541-541`
- `W/W021` -> `TRAITS:/writers/20`; `TRAITS:W021`, `TRAITS:S178:267-267`

## DG03

资料专用，不进影片 / 本屏5条 / 额外静音0秒

资料页不进主片；生成、开局、历史、调试与事件NPC分开，不伪装成玩家按钮。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 神秘人入队链／朝圣者 | scope:2010_mystic / 事件NPC | 朝圣者 |
| 神秘人结局2013／朝圣者 | scope:2010_mystic / 事件NPC | 朝圣者 |
| 神秘人结局2014／朝圣者 | scope:2010_mystic / 事件NPC | 朝圣者 |
| 神秘人结局2015／朝圣者 | scope:2010_mystic / 事件NPC | 朝圣者 |
| BP2外国教士／朝圣者 | scope:foreign_cleric / 事件NPC | 朝圣者 |

作者来源（不上屏）：
- `W/W049` -> `TRAITS:/writers/48`; `TRAITS:W049`, `TRAITS:S227:3811-3811`
- `W/W050` -> `TRAITS:/writers/49`; `TRAITS:W050`, `TRAITS:S227:3977-3977`
- `W/W051` -> `TRAITS:/writers/50`; `TRAITS:W051`, `TRAITS:S227:4029-4029`
- `W/W052` -> `TRAITS:/writers/51`; `TRAITS:W052`, `TRAITS:S227:4067-4067`
- `W/W079` -> `TRAITS:/writers/78`; `TRAITS:W079`, `TRAITS:S236:5044-5044`

## D01

主片展示 / 本屏1条 / 额外静音4秒

一处字面删除不是全部删除路径；下一页接动态罪恶与美德选择器。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 跨宗教改信 | 新旧信仰所属宗教不同 | 删除朝圣者；同宗教内换信仰不满足此条 |

作者来源（不上屏）：
- `W/W084` -> `TRAITS:/writers/83`; `TRAITS:W084`, `TRAITS:S257:96-96`

## M01

主片展示 / 本屏6条 / 额外静音5秒

增益相加后乘基础请求，再写入旧经验封顶。四级升级定义不证明同时四份生效。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 朝圣者收容所 01 | 教会庄园实际生效建筑；四级不直接相加 | +5% 朝圣者经验增益 |
| 朝圣者收容所 02 | 教会庄园实际生效建筑；四级不直接相加 | +5% 朝圣者经验增益 |
| 朝圣者收容所 03 | 教会庄园实际生效建筑；四级不直接相加 | +5% 朝圣者经验增益 |
| 朝圣者收容所 04 | 教会庄园实际生效建筑；四级不直接相加 | +5% 朝圣者经验增益 |
| 踏过圣路 | 宗族传承实际生效 | +50% 朝圣者经验增益 |
| 复越高山 | 技能持有者且符合神权制条件 | +20% 朝圣者经验增益 |

作者来源（不上屏）：
- `M/baptistery_pilgrims_hospice_01` -> `TRAITS:/xp_multiplier_producers/0`; `TRAITS:S054:3867`
- `M/baptistery_pilgrims_hospice_02` -> `TRAITS:/xp_multiplier_producers/1`; `TRAITS:S054:3910`
- `M/baptistery_pilgrims_hospice_03` -> `TRAITS:/xp_multiplier_producers/2`; `TRAITS:S054:3957`
- `M/baptistery_pilgrims_hospice_04` -> `TRAITS:/xp_multiplier_producers/3`; `TRAITS:S054:4004`
- `M/ep2_activities_legacy_1` -> `TRAITS:/xp_multiplier_producers/4`; `TRAITS:S056:36`
- `M/just_one_more_hill_perk` -> `TRAITS:/xp_multiplier_producers/5`; `TRAITS:S072:93`

## D02

主片展示 / 本屏4条 / 额外静音5秒

当前宗教待遇也会改变动态授予与移除候选。91个检索候选不是91个闭合入口，这里只列已验证路径。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 当前罪恶选择器 | 当前礼仪将朝圣者视为罪恶，且实际候选中抽中 | 可能删除朝圣者 |
| 当前美德选择器 | 当前礼仪视为美德，未拥有且无相反冲突，并被抽中 | 可能授予朝圣者 |
| 先删罪恶再加美德 | 宗教决议事件对应沉思分支调用，实际抽选另判 | 可能删或加，不是必然交换 |
| 悔改誓言的处理 | 朝圣者为名声类，当前视为罪恶，另满足誓言决议资格 | 进入对应移除列表；人格专属路径另排除 |

作者来源（不上屏）：
- `D/remove_sinful_trait_effect` -> `TRAITS:/semantic_inventory/generic_trait_mutation`; `TRAITS:S324:829-839`
- `D/add_virtuous_trait_effect` -> `TRAITS:/semantic_inventory/generic_trait_mutation`; `TRAITS:S324:842-875`
- `D/replace_sinful_trait_effect` -> `TRAITS:/semantic_inventory/generic_trait_mutation`; `TRAITS:S324:878-880`, `TRAITS:S343:2001`
- `D/repent_oath_decision` -> `TRAITS:/semantic_inventory/generic_trait_mutation`; `TRAITS:S046:1754-1784`

## DH01

资料专用，不进影片 / 本屏6条 / 额外静音0秒

资料页不进主片；生成、开局、历史、调试与事件NPC分开，不伪装成玩家按钮。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| pilgrim_character |  | 特质 = 朝圣者 |
| fp3_gnostic_paragon |  | 特质 = 朝圣者 |
| fp3_zoroastrian_armed_pilgrim |  | 特质 = 朝圣者 |
| spawn_historical_characters_effect | if/title:b_tangiers/create_character | 特质 = 朝圣者 |
| spawn_historical_characters_effect | if/title:b_london/create_character | 特质 = 朝圣者 |
| spawn_historical_characters_effect | if/title:b_sigtuna/create_character | 特质 = 朝圣者 |

作者来源（不上屏）：
- `W/W014` -> `TRAITS:/writers/13`; `TRAITS:W014`, `TRAITS:S175:4-4`
- `W/W016` -> `TRAITS:/writers/15`; `TRAITS:W016`, `TRAITS:S176:173-173`
- `W/W017` -> `TRAITS:/writers/16`; `TRAITS:W017`, `TRAITS:S176:284-284`
- `W/W022` -> `TRAITS:/writers/21`; `TRAITS:W022`, `TRAITS:S183:1300-1300`
- `W/W023` -> `TRAITS:/writers/22`; `TRAITS:W023`, `TRAITS:S183:1405-1405`
- `W/W024` -> `TRAITS:/writers/23`; `TRAITS:W024`, `TRAITS:S183:2780-2780`

## DH02

资料专用，不进影片 / 本屏6条 / 额外静音0秒

资料页不进主片；生成、开局、历史、调试与事件NPC分开，不伪装成玩家按钮。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| spawn_historical_characters_effect | if/title:b_bukhara/create_character | 特质 = 朝觐者／朝觐妇 |
| pilgrimage.2050 | immediate/hidden_effect/create_character | 特质 = 朝圣者 |
| pilgrimage.2050 | immediate/hidden_effect/create_character | 特质 = 朝圣者 |
| iberia_north_africa.2011 | immediate/random_list/70/create_character | 特质 = 朝圣者 |
| iberia_north_africa.2011 | immediate/random_list/30/create_character | 特质 = 朝圣者 |
| iberia_north_africa.2012 | immediate/random_list/50/create_character | 特质 = 朝圣者 |

作者来源（不上屏）：
- `W/W025` -> `TRAITS:/writers/24`; `TRAITS:W025`, `TRAITS:S183:4452-4452`
- `W/W053` -> `TRAITS:/writers/52`; `TRAITS:W053`, `TRAITS:S227:5017-5017`
- `W/W054` -> `TRAITS:/writers/53`; `TRAITS:W054`, `TRAITS:S227:5039-5039`
- `W/W075` -> `TRAITS:/writers/74`; `TRAITS:W075`, `TRAITS:S233:2196-2196`
- `W/W076` -> `TRAITS:/writers/75`; `TRAITS:W076`, `TRAITS:S233:2234-2234`
- `W/W077` -> `TRAITS:/writers/76`; `TRAITS:W077`, `TRAITS:S233:2370-2370`

## DH03

资料专用，不进影片 / 本屏6条 / 额外静音0秒

资料页不进主片；生成、开局、历史、调试与事件NPC分开，不伪装成玩家按钮。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| iberia_north_africa.2012 | immediate/random_list/50/create_character | 特质 = 朝圣者 |
| walpurga_1 |  | 特质 = 朝圣者 |
| walpurga_3 |  | 特质 = 朝圣者 |
| walpurga_4 |  | 特质 = 朝圣者 |
| walpurga_6 |  | 特质 = 朝圣者 |
| vardapet_1 |  | 特质 = 朝圣者 |

作者来源（不上屏）：
- `W/W078` -> `TRAITS:/writers/77`; `TRAITS:W078`, `TRAITS:S233:2401-2401`
- `W/W086` -> `TRAITS:/writers/85`; `TRAITS:W086`, `TRAITS:S272:7224-7224`
- `W/W087` -> `TRAITS:/writers/86`; `TRAITS:W087`, `TRAITS:S272:7266-7266`
- `W/W088` -> `TRAITS:/writers/87`; `TRAITS:W088`, `TRAITS:S272:7286-7286`
- `W/W089` -> `TRAITS:/writers/88`; `TRAITS:W089`, `TRAITS:S272:7319-7319`
- `W/W090` -> `TRAITS:/writers/89`; `TRAITS:W090`, `TRAITS:S273:9358-9358`

## DH04

资料专用，不进影片 / 本屏6条 / 额外静音0秒

资料页不进主片；生成、开局、历史、调试与事件NPC分开，不伪装成玩家按钮。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| bavarian0003 |  | 特质 = 朝圣者 |
| extra_bedouins_0019 |  | 特质 = 朝圣者 |
| danis0004 |  | 特质 = 朝圣者 |
| khali0002 |  | 特质 = 朝圣者 |
| easteregg_ali_kara |  | 特质 = 朝觐者／朝觐妇 |
| easteregg_ola_jentzsch |  | 特质 = 朝圣者 |

作者来源（不上屏）：
- `W/W091` -> `TRAITS:/writers/90`; `TRAITS:W091`, `TRAITS:S274:10106-10106`
- `W/W092` -> `TRAITS:/writers/91`; `TRAITS:W092`, `TRAITS:S275:14442-14442`
- `W/W093` -> `TRAITS:/writers/92`; `TRAITS:W093`, `TRAITS:S276:7307-7307`
- `W/W094` -> `TRAITS:/writers/93`; `TRAITS:W094`, `TRAITS:S276:7706-7706`
- `W/W095` -> `TRAITS:/writers/94`; `TRAITS:W095`, `TRAITS:S278:4108-4108`
- `W/W096` -> `TRAITS:/writers/95`; `TRAITS:W096`, `TRAITS:S278:4796-4796`

## DH05

资料专用，不进影片 / 本屏6条 / 额外静音0秒

资料页不进主片；生成、开局、历史、调试与事件NPC分开，不伪装成玩家按钮。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| easteregg_shehabulddin_alessawey |  | 特质 = 朝圣者 |
| et_york_1066_1 |  | 特质 = 朝圣者 |
| bahitawi_1 |  | 特质 = 朝圣者 |
| wang_chuyi_1 |  | 特质 = 朝圣者 |
| jiang_kui_1 |  | 特质 = 朝圣者 |
| 7253 | 1030.1.1 | 特质 = 朝圣者 |

作者来源（不上屏）：
- `W/W097` -> `TRAITS:/writers/96`; `TRAITS:W097`, `TRAITS:S278:8232-8232`
- `W/W098` -> `TRAITS:/writers/97`; `TRAITS:W098`, `TRAITS:S279:11262-11262`
- `W/W099` -> `TRAITS:/writers/98`; `TRAITS:W099`, `TRAITS:S280:2013-2013`
- `W/W100` -> `TRAITS:/writers/99`; `TRAITS:W100`, `TRAITS:S282:145543-145543`
- `W/W101` -> `TRAITS:/writers/100`; `TRAITS:W101`, `TRAITS:S282:146030-146030`
- `W/W102` -> `TRAITS:/writers/101`; `TRAITS:W102`, `TRAITS:S283:2180-2180`

## DH06

资料专用，不进影片 / 本屏6条 / 额外静音0秒

资料页不进主片；生成、开局、历史、调试与事件NPC分开，不伪装成玩家按钮。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| jojin_1 |  | 特质 = 朝圣者 |
| extra_khazars_1 |  | 特质 = 朝圣者 |
| 20224 |  | 特质 = 朝圣者 |
| 1000230509 |  | 特质 = 朝圣者 |
| extra_tahirids_3 |  | 特质 = 朝圣者 |
| khong_lo_1 |  | 特质 = 朝圣者 |

作者来源（不上屏）：
- `W/W103` -> `TRAITS:/writers/102`; `TRAITS:W103`, `TRAITS:S284:103257-103257`
- `W/W104` -> `TRAITS:/writers/103`; `TRAITS:W104`, `TRAITS:S285:1072-1072`
- `W/W105` -> `TRAITS:/writers/104`; `TRAITS:W105`, `TRAITS:S288:5193-5193`
- `W/W106` -> `TRAITS:/writers/105`; `TRAITS:W106`, `TRAITS:S289:919-919`
- `W/W107` -> `TRAITS:/writers/106`; `TRAITS:W107`, `TRAITS:S289:993-993`
- `W/W108` -> `TRAITS:/writers/107`; `TRAITS:W108`, `TRAITS:S291:1736-1736`

## DR01

资料专用，不进影片 / 本屏6条 / 额外静音0秒

资料页不进主片；生成、开局、历史、调试与事件NPC分开，不伪装成玩家按钮。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| pilgrim_character | after_creation/add_random_tiered_trait_xp_effect | TRAIT = 朝圣者 |
| monastic_order_leader_character | random_traits_list_candidate_not_guaranteed | 朝圣者 |
| fp3_sufi_mystic | random_traits_list_candidate_not_guaranteed | 朝圣者 |
| ep3_frankokratia_crusader_template | random_traits_list_candidate_not_guaranteed | 朝圣者 |
| pam_crusader_template | random_traits_list_candidate_not_guaranteed | 朝圣者 |
| clan.1201 | random_traits_list_candidate_not_guaranteed | 朝圣者 |

作者来源（不上屏）：
- `W/W015` -> `TRAITS:/writers/14`; `TRAITS:W015`, `TRAITS:S175:19-19`
- `R/1` -> `TRAITS:/random_trait_list_pilgrim_candidates/0`; `TRAITS:S172:418-420`
- `R/2` -> `TRAITS:/random_trait_list_pilgrim_candidates/1`; `TRAITS:S176:244-244`
- `R/3` -> `TRAITS:/random_trait_list_pilgrim_candidates/2`; `TRAITS:S177:401-401`
- `R/4` -> `TRAITS:/random_trait_list_pilgrim_candidates/3`; `TRAITS:S179:168-168`
- `R/5` -> `TRAITS:/random_trait_list_pilgrim_candidates/4`; `TRAITS:S254:1013-1013`

## F01

主片展示 / 本屏3条 / 额外静音6秒

只改一个输入。L为未闭合的旅队主管独立报价，不能代0。F0和F1接近上限吞掉经验差，F2才显示增益后的实际差额。

| 条目 | 资格／实际对象 | 具体影响／基础请求 |
| --- | --- | --- |
| 固定公爵，无折扣或经验增益 | 中世纪早期，头衔等级3、计算项2，收入10；费用与奖励平方距离各50000；虔诚朝圣、忠诚朝圣者、排场讲究；非主要圣地，已有经验80；雇佣登山者 | 60+100+12+4=176＋独立主管报价；65／75分主虔诚112.5／150；基础经验20／40均实际+20至100 |
| 只开启踏过圣路 | 初始模型其余条件全部保持 | 30+75+12+4=121＋独立主管报价；主虔诚仍112.5／150；经验请求调30／60，仍均实际+20至100 |
| 只改原经验 | 传承模型原经验80改20，其它条件保持 | 仍121＋独立主管报价；主虔诚仍112.5／150；实际经验+30／+60，终值50／80 |

作者来源（不上屏）：
- `F/F0` -> `FORMULA:/models`; `FORMULA:/cost`, `FORMULA:/piety`, `FORMULA:/trait_xp`
- `F/F1` -> `FORMULA:/models`; `FORMULA:/cost`, `FORMULA:/piety`, `FORMULA:/trait_xp`
- `F/F2` -> `FORMULA:/models`; `FORMULA:/cost`, `FORMULA:/piety`, `FORMULA:/trait_xp`
