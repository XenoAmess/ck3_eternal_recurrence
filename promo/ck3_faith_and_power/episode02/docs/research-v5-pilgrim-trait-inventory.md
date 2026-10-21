# 朝圣者特质：全安装脚本影响库存（CK3 1.20.0.4）

**后继原生补注（2026-10-22）：** 本文封稿后的[精确等级与初始化链a02](research-v5-native-tier-12004.a02.md)已闭合“源等级块无预差分，基础＋所有已达阈值块累计”、直接新轨道初始化0、重复授予不重置。下文及库存JSON中“等级加载预处理／初始化未闭”保留其当时观察身份，当前按这条后继补注读取；异常缺`limit`的默认语义仍未闭。该补注不是新实机结果，不改原来源清单或原DELIVERY。根`ai_zeal=5`与track的AI modifier分列，未擅算整体AI总值。

本清单回答的是：当前安装脚本中，哪些入口会授予、删除或写入 `pilgrim`／`hajjaj`，哪些条件改变朝圣者经验，哪些只读取该特质、改变收益或影响 AI／事件抽选。它不以几个活动实例代替全部入口。

- `machine_id: 4-8e1c2f1861`。实际检索时间、每个来源的 SHA-256、行号、覆盖摘要及复核时间见[机器可读库存](knowledge/pilgrimage-v5-pilgrim-trait-inventory-12004.json)。
- 来源根：`C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game`。本轮只读取安装源、既有日志，没有启动游戏、调用 Native、拍摄或验证当前 DLC 启用状态。
- 全量检索覆盖 `common` 2,871、`events` 577、`history` 748、物理存在的 `dlc` 文本 72、`dlc_metadata` 2，共 4,270 个定义文本；另补读 trait `.info`／`.lookup` 与动态 helper 边界。所有可用 DLC 规则已包含在 common/events 的检索内，DLC 目录也独立检查；“文件存在”不等于该账号拥有或本局启用了 DLC。
- 宽检为不区分大小写的 `pilgrim`／`hajj`，加宗教特质文化参数。5,182 个非注释行命中完整保存为 `[来源ID, 行号, 类别ID]`，共享来源 pin，避免重复源码。类别是检索提示，不能把名字、头像标记、工具提示或某个 `trait = pilgrim` 选项图标判为写入效果。
- 窄检另追 `add_trait_xp`／特质授予和删除、动态参数 helper、倍率键、经验读取、活动表现 helper。各文件完整 SHA 与全扫描清单摘要均在 JSON；没有复制游戏全源码。

## 先分清五种影响

| 类别 | 何时改变什么 | 不应怎样表述 |
|---|---|---|
| 特质授予／移除 | 改变人物有无 `pilgrim` 或 `hajjaj` | 不能说全部必须先完成一次玩家主持的朝圣 |
| 特质经验写入／倍率 | 对 `pilgrim` track 请求经验，或提供其经验增益修正 | 这不是钱包虔诚，也不是奉献等级经验 |
| 活动分→结算经验 | 先改变本次活动分，再由档位旗标决定 5／10／20／40 请求 | 活动分本身不是特质经验；+10 活动分不等于 +10 特质经验 |
| 等级／资格／收益读取 | 按经验、礼仪、文化、身份开启效果或选项 | 读取经验不会自动增加经验 |
| AI／随机抽选 | 改变 AI 的活动或选项偏好、事件／随机列表的权重 | 不能改写成玩家经验倍率或必定获得某结果 |

## 1. 两个特质的身份、替换与删除

`pilgrim` 在 `common/traits/00_traits.txt:8755–8894` 定义，只有一个简写 track，track 名按 `_traits.info:225` 的规则也是 `pilgrim`。名称门槛为 50／100，不能把曼荼罗读取的 25／50／75／100 四个门槛误当四级朝圣者名称。

`hajjaj` 在 `00_traits.txt:8896–8953` 定义，男性／女性显示 Hajji／Hajjah；它没有 track，不能升级“哈吉经验”。两个 trait 块没有互相列为 `opposites`；本轮未找到自动把 `pilgrim` 替换成 `hajjaj` 的脚本。授予其中一个不能据此推断另一个被移除。

唯一字面 `remove_trait = pilgrim` 位于 `events/religion_events/faith_conversion_events.txt:92–96`：新旧 faith 的 **religion 不同**才删除。仅在同一 religion 内改信不满足这条删除条件；但朝圣进行中改变 faith 另会触发活动有效性检查，不是同一回事。本轮未找到 `remove_trait = hajjaj`；这只是已扫脚本的负结论，不能外推成所有引擎／控制台／模组操作都不能删除。

**27处授予／1处移除是字面计数，不是所有泛型效果的总数。** 还必须计入下列不写死 trait 名的宗教／类别选择器。

### 泛型宗教／类别路径

| 路径 | 为何可能触及pilgrim | 来源／实际调用 |
|---|---|---|
| `remove_sinful_trait_effect` | 从当前人物特质中按当前 rite 的罪恶条件抽一个，没有 personality 限制；禁止朝圣教义下 pilgrim 是罪恶 | `00_religion_effects.txt:829–839` |
| `add_virtuous_trait_effect` | 从当前rite美德中抽未拥有、无相反特质冲突的trait，没有 personality 限制；encouraged／Acts of Apostles等可使pilgrim为美德 | 同文件 `842–875` |
| `replace_sinful_trait_effect` | 先删一个罪恶，再加一个美德；是否抽到pilgrim取决于当前rite和人物候选集合 | 同文件 `878–880`；唯一实际事件调用在 `religious_decision.0211` 的 meditation_reflection 分支，`religious_decision_events.txt:1999–2002` |
| 悔罪加冕誓言决议 | `every_character_trait` 中筛当前rite罪恶，再将 lifestyle／fame 加入移除列表；pilgrim 是 fame，若当前rite将其视为罪恶，会进入该列表 | `10_ach_oath_decisions.txt:1754–1784`；决议自身誓言、身份与期限资格仍须满足 |

这些入口是条件路径，不是每次冥想必得／必失朝圣者。当前hajjaj没有track，且本轮没有找到将其列为美德／罪恶的当前定义，不能仅凭“category=fame”就断言悔罪誓言一定移除hajjaj。

同时核对了泛型排除项：乳母灌输美德、净土去罪、CE1传说祖先美德／罪恶交换、CE1瘟疫悔罪、BP2幻想朋友换性格均有 `personality` 选择器，排除 fame 的 pilgrim；日本健康奇迹选 `illness`，不选这两个特质；指挥官传授、疾病／教育／性格参数化helper也不能因目标参数是动态的就虚构pilgrim绑定。完整动态写入候选及参数边界另存JSON `generic_trait_mutation_candidate_index`，其中没有已验证目标绑定者不会冒充确定授予／删除入口。

### 获得入口全类别

| 入口 | 接收者与条件 | 来源 |
|---|---|---|
| 普通／宗教目的地抵达 helper | 主持人、参加者无 pilgrim 时授予；已有者进入经验／替代奖励分支 | `00_pilgrimage_effects.txt:216–315`；实际所有调用见 JSON `direct_helper_definitions_and_calls` |
| 抵达随行人员 | 按 helper 的旅队、宗教和目的地条件给随行者 pilgrim 或 hajjaj；有些检查在 `any_entourage`，有些在 `every_entourage.limit`，不能改写成全员都逐一通过同一资格检查 | 同文件 `317–395`、`412–484` |
| Hajj 完成 | 本人没有 hajjaj 时授予；已有者转学识生活方式经验或补虔诚旗标，不给 hajjaj track 经验 | 同文件 `399–411`；完成日志入口 `68` |
| 麦加身份补发 | 开局／统治者设计完成：麦加持有者、mandatory_hajj 且无 hajjaj；运行中的 `hajj.0010→0011` 按首都麦加及礼仪条件补发 | `on_action/game_start.txt:649–656`、`ruler_designer.txt:30–37`、`hajj_events.txt:34–100` |
| 营地宴会讲述朝圣 | 符合专用成年可用 trigger、同信仰的另一名参加者：没有则授予，有则经验 | `activities/pulse_actions/camp_party_actions.txt:1707–1786` |
| 传奇圣所建成 | `county.holder`：没有则授予，随后请求 +30；已有者同样请求 +30 | `buildings/00_legendary_buildings.txt:74–95` |
| 特定事件／NPC | 神秘人事件链、外国教士、FP2 决斗成功、圣骑士团事件、朝圣队领袖等各自接收者；不能把 NPC 的授予记到玩家账上 | 完整 27 处字面授予见附表及 JSON |
| 角色生成／历史初始 | 模板、历史人物、`create_character`、随机特质列表、历史角色重建可初始携带；生成模板也可能附带 XP | 全部命中见 `creation_trait` 与 `history_or_generation` 索引 |
| 调试决议 | `wild_goose_chase_decision`，`decision_group_type=debug`／`debug_only=yes`；没有则授予，有则 +5 | `decisions/test_decision.txt:2–42`；不作为普通玩家朝圣路径 |

### 27处字面授予逐项表

“非固定NPC”表示按实际作用 scope，可以是玩家或 AI；不表示玩家这次必得。生成模板的随机权重与前置资格保存在 JSON，不能把某个随机分支当固定初始特质。

| ID | 短名／授予特质 | 接收者 | NPC范围 | 精确来源行 |
|---|---|---|---|---|
| W001 | 营地虔诚故事／pilgrim | 同信仰第二参加者，无特质时 | 非固定NPC | `camp_party_actions.txt:1780` |
| W003 | 传奇圣所／pilgrim | 建成时 county.holder | 非固定NPC | `00_legendary_buildings.txt:88` |
| W006 | Wild Goose Chase／pilgrim | 使用调试决议者 | 调试专属 | `test_decision.txt:38` |
| W008 | 朝圣队领袖／pilgrim | 有 peasant_pilgrim_leader 标记的随行者，后移出角色 | 事件NPC | `pilgrimage_on_actions.txt:163` |
| W009 | 开局麦加／hajjaj | 麦加持有者，mandatory_hajj | 非固定NPC | `game_start.txt:656` |
| W010 | 设计统治者麦加／hajjaj | 新设计角色，麦加持有者且mandatory_hajj | 设计角色 | `ruler_designer.txt:37` |
| W011 | 建筑师生成／pilgrim | master_mason_character，新角色随机分支5 | 生成NPC | `00_peasants_template.txt:1599` |
| W012 | 本地朝圣者生成／pilgrim | location_pilgrim_template 对应分支 | 生成NPC | `00_priest_character_template.txt:1124` |
| W013 | 本地朝觐者生成／hajjaj | 同模板另一对应分支 | 生成NPC | 同文件 `1129` |
| W018 | 旅行者生成／pilgrim | traveler_character 随机分支20 | 生成NPC | `07_ep3_character_templates.txt:533` |
| W019 | 旅行者生成／pilgrim | 同模板随机分支10 | 生成NPC | 同文件 `541` |
| W021 | 资深交际花生成／pilgrim | experienced_courtesan_character 随机分支10 | 生成NPC | `10_ach_character_templates.txt:267` |
| W026 | 普通抵达主持人／pilgrim | helper 中的 root 主持人，无特质 | 非固定NPC | `00_pilgrimage_effects.txt:234` |
| W027 | 普通抵达参加者／pilgrim | helper 中非主持人的当前角色，无特质 | 非固定NPC | 同文件 `280` |
| W028 | 普通抵达 helper 的Hajj旅队支路／hajjaj | every_entourage_character 中无 hajjaj 者；外围any检查和内部循环筛选不相同 | 随行角色 | 同文件 `339` |
| W029 | 普通抵达 helper 的pilgrim旅队支路／pilgrim | 通过该循环NAND等条件且无pilgrim的随行者 | 随行角色 | 同文件 `382` |
| W030 | Hajj完成本人／hajjaj | helper 当前角色，无 hajjaj | 非固定NPC | 同文件 `404` |
| W031 | Hajj完成穆斯林旅队／hajjaj | 宗教为伊斯兰且无hajjaj的随行者 | 随行角色 | 同文件 `433` |
| W032 | Hajj完成非穆斯林旅队／pilgrim | 非穆斯林、自信仰圣地条件且无pilgrim的随行者 | 随行角色 | 同文件 `471` |
| W048 | 麦加首都补发／hajjaj | hajj.0010选出并触发0011的角色 | 非固定NPC | `hajj_events.txt:78` |
| W049 | 神秘人入队链／pilgrim | scope:2010_mystic | 事件NPC | `pilgrimage_events.txt:3811` |
| W050 | 神秘人结局2013／pilgrim | scope:2010_mystic | 事件NPC | 同文件 `3977` |
| W051 | 神秘人结局2014／pilgrim | scope:2010_mystic | 事件NPC | 同文件 `4029` |
| W052 | 神秘人结局2015／pilgrim | scope:2010_mystic | 事件NPC | 同文件 `4067` |
| W079 | BP2外国教士／pilgrim | scope:foreign_cleric | 事件NPC | `bp2_yearly_events_6.txt:5044` |
| W081 | FP2朝圣事件决斗成功／pilgrim | fp2_yearly.4007 的 root | 非固定NPC | `fp2_yearly_events.txt:3438` |
| W085 | 圣骑士团成员／pilgrim | 无pilgrim、有order_member，且liege领导本faith圣骑士团的角色 | 身份角色 | `holy_order_events.txt:451` |

## 2. 全部 43 个字面朝圣者经验写入块

以下“+N”都是脚本传给 `add_trait_xp` 的基础请求，不是本轮已测的最终人物增量。普通入口多数先检查“已有 pilgrim 且经验 <100”，表中记为 **P<100**；不带这条检查的入口单独标出。达到上限、舍入、倍率应用次序不能仅由请求字面值确认。JSON 每一项保留来源 pin、精确块行号及条件链；同一个事件可能有多块，所以 43 不是 43 个独立事件。

| 写入块 | 入口短名／资格 | 基础请求 | 来源行 |
|---|---|---|---|
| W002 | 营地宴会“虔诚故事”，被选中的同信仰第二位参加者已有 pilgrim；无 <100 guard | 整数随机 20–40 | `camp_party_actions.txt:1769` |
| W004 | 传奇圣所建成，county.holder 已有 pilgrim | 30 | `00_legendary_buildings.txt:82` |
| W005 | 同上，没有 trait 则先授予再请求经验 | 30 | 同文件 `89` |
| W007 | debug 专属“Wild Goose Chase”，已有 pilgrim；无 <100 guard | 5 | `test_decision.txt:32` |
| W020 | traveler_character 生成后，若已获得 pilgrim；无 <100 guard | 随机范围 55–80 | `07_ep3_character_templates.txt:577` |
| W033 | 普通抵达主持人：已有 trait，PAM 且本 faith 有 secured-pilgrim-routes 变量、经验<100；外层无 limit 异常，见下节 | 30 | `00_pilgrimage_effects.txt:246` |
| W034 | 同一异常树的内层 else：前一 secured 条件不成立且 <100 空分支未接走；不能称“普通重访+20” | 20 | 同文件 `260` |
| W035 | 普通抵达非主持人：PAM／secured routes／P<100；外层也无 limit | 20 | 同文件 `292` |
| W036 | 普通抵达非主持人：前一 secured 分支不成立、P<100 | 10 | 同文件 `304` |
| W037 | 普通抵达 helper 旅队循环，已有 pilgrim 的符合该循环筛选者；无 <100 guard | 10 | 同文件 `386` |
| W038 | Hajj helper 非穆斯林随行者、自信仰圣地、已有 pilgrim；无 <100 guard | 10 | 同文件 `475` |
| W039 | give_pilgrim_xp_effect，P<100 | 5 | 同文件 `497` |
| W040 | pious 结算，P<100＋perfect_pious_reward | 40 | 同文件 `643` |
| W041 | pious 结算，P<100＋high_pious_reward | 20 | 同文件 `650` |
| W042 | pious 结算，P<100＋mid_pious_reward | 10 | 同文件 `657` |
| W043 | pious 结算，P<100＋low_pious_reward | 5 | 同文件 `664` |
| W044 | 圣人墓 POI，已有 pilgrim；若省份有圣人须本 faith 承认；无 <100 guard | 随机 3–5 | `pam_saint_point_of_interest_types.txt:30` |
| W045 | 大教堂 POI，已有 pilgrim，extended_nave 标记 | (随机 3–5)×2 | `travel_point_of_interest_types.txt:1846` |
| W046 | 同上，前项不成立、cathedral_pilgrim_xp 标记 | (随机 3–5)×1.5 | 同文件 `1862` |
| W047 | 同上，前两项不成立、cathedral_glass_pilgrim 标记 | (随机 3–5)×2 | 同文件 `1877` |
| W055 | pilgrimage.2006 的 travel_smart 专属选项；P<100，前一学识替代奖励分支须未接走 | 5 | `pilgrimage_events.txt:3263` |
| W056 | pilgrimage_2013_outcome_effect：前面“无 mystic／mystic 未满／学识生活方式”分支都未接走，再检查 P<100 | 10 | 同文件 `3622` |
| W057 | pilgrimage.2030.b：zealot intent 或狂热且无不信者秘密；P<100 | 5 | 同文件 `4732` |
| W058 | pilgrimage.3004.a：基督教、陆地有效位置、学识达到 high_skill_rating；P<100 | 10 | 同文件 `7234` |
| W059 | pilgrimage.3102.b：伊斯兰、陆地有效位置、不是 cynical；P<100 | 5 | 同文件 `7359` |
| W060 | pilgrimage.3201.a：印度教、陆地有效位置；P<100 | 5 | 同文件 `7432` |
| W061 | pilgrimage.3202.a：印度教／佛教／耆那教，或礼仪有 sanctity_of_nature；森林／丛林／针叶林、旅程进度<0.8；P<100 | 20 | 同文件 `7532` |
| W062 | pilgrimage.3301.c：佛教、陆地有效位置、学识 high_skill_rating；P<100 | 10 | 同文件 `7622` |
| W063 | pilgrimage.6001.c：BP1、朋友／旅队等事件资格、狂热选项；穆斯林还有 drunkard 事件门槛；P<100 | 5 | 同文件 `8190` |
| W064 | pilgrimage.6520.a：事件旅伴条件成立；选项要求 zealous 或 vengeful；P<100 | 10 | 同文件 `10889` |
| W065 | pilgrimage.6800.e：事件的宫廷／随行者条件成立，狂热选项；P<100 | 20 | 同文件 `13622` |
| W066 | pilgrimage.6830.c：reflection intent、非腾格里、已有 votive_artifact、P<100 | 20 | 同文件 `14287` |
| W067 | pilgrimage_intent.1030.a：reflection intent；已有 P<100 才经验，无 trait 是另一笔虔诚 | 10 | `pilgrimage_intent_events.txt:827` |
| W068 | pilgrimage_intent.1041 immediate：已有 pilgrim；**没有 <100 guard** | 10 | 同文件 `1042` |
| W069 | pilgrimage_intent.1043 immediate：P<100 | 10 | 同文件 `1173` |
| W070 | pilgrimage_intent.1100.a：reflection intent；P<100 | 5 | 同文件 `1812` |
| W071 | pilgrimage_intent.1110.a：海上／旅伴事件、altruism intent；P<100 | 5 | 同文件 `1986` |
| W072 | 同事件 .b：reflection intent；P<100 | 5 | 同文件 `2013` |
| W073 | 同事件 .c：zealot intent；P<100 | 5 | 同文件 `2040` |
| W074 | 同事件 .d：whole_of_body／herbalist／巫师 trigger／physician 四选一，且无 pilgrimage_herbalist_modifier；P<100 | 10 | 同文件 `2114` |
| W080 | ep3_contract_event.0045 随机列表 30 分支，被作用者已有 pilgrim；无 <100 guard | 整数随机 20–40 | `ep3_contract_events.txt:4131` |
| W082 | pam_great_projects_events.0002 选项中已有 pilgrim；大教堂状态生产与角色 XP 同时发生 | (随机 3–5)×1.5 | `pam_great_projects_events.txt:221` |
| W083 | pam_great_projects_events.0003 选项中已有 pilgrim | (随机 3–5)×2 | 同文件 `622` |

### 动态写入补项：不能被“trait = pilgrim”字面搜漏掉

另外五个 `random_traits_list` 明列 pilgrim 候选，也不会出现在“trait=pilgrim”计数中；它们是随机候选，不保证每个生成角色都拥有。

| 生成入口 | 候选 | 来源 |
|---|---|---|
| monastic_order_leader_character | pilgrim，候选权重10，列表count为0–2 | `00_holy_order_character_templates.txt:410–420` |
| fp3_sufi_mystic | pilgrim候选 | `04_fp3_character_templates.txt:244` |
| ep3_frankokratia_crusader_template | pilgrim候选 | `07_ep3_character_templates.txt:401` |
| pam_crusader_template | pilgrim候选 | `pam_character_templates.txt:168` |
| clan.1201 的角色创建 | pilgrim候选，weight base10 | `events/government_events/clan_events.txt:1013` |

`pilgrim_character` 模板（`04_ep2_james_character_templates.txt:1–23`）初始给 pilgrim，之后调用 `add_random_tiered_trait_xp_effect`，参数 `TRAIT=pilgrim / LEVEL_1=no / LEVEL_3=yes`。通用 helper 在 `00_pool_effects.txt:76–120` 有三个参数化写入块；本绑定禁用第一档，启用 **55–80（权重10）或100（权重5）** 两个分支。这是新生成角色的初始经验，不是玩家每次旅行额外掷这张表。43 统计是字面写入块，这条参数绑定另列，不混算。

完整检查也包括 tutor／grand mentor／nomad／hunt 的动态 trait helper：其实际调用参数或分支枚举限定为别的 trait；不能因为 helper 接受任意参数就说它会给 pilgrim。`gain_trait_or_experience_effect` 的实际调用也未绑定 pilgrim。

### +5 helper 只有四个实际调用，不能包装成“每次抵达+5”

`give_pilgrim_xp_effect` 的调用位于：`pilgrimage.2003.c:2779`、`pilgrimage.3001:6922` 的接受选项、`pilgrimage.6002.c:8349` 狂热选项、`6531_positive_outcome:10977`。其自身先判 P<100 请求 +5；否则依次可能给学识生活方式经验、狂热减压或其它替代奖励（`00_pilgrimage_effects.txt:488–513`）。这里的狂热／学识不是把原先 +5 乘大，而是改变进入哪条分支。

### 抵达主持人的真实异常，不用注释补出奖励

`give_pilgrim_trait_or_xp_effect:236–270` 的实际括号是：

1. 无 pilgrim：授予。
2. 后接一个**没有 limit 的外层 else_if**；内部先判 PAM＋secured routes＋XP<100，请求30。
3. 内层下一条 else_if 判 XP<100，**块内为空**。
4. 内层 else 才请求20。
5. 学识生活方式与 trait-piety flag 是该外层 else_if 的后续同级分支。

因此不能把第4步的20按注释追认为“普通主持人重访+20”。在通常的条件链解释下，已有者且 XP<100、无 secured routes 会落入空块；但外层缺 limit 的引擎接受／拒绝和执行语义，本轮没有原生验证。既有 V3 error.log 中未检出文件名／else_if／limit 诊断，**没有日志不等于已经证明加载或执行成功**。非主持人外层也缺 limit，但内部有 secured20／普通10／学识替代／flag 梯级。完整静态树保留在 JSON，公式研究另以“源码输入”和“通常解析推导”分开。

## 3. 经验倍率：全部六条赋值，只有三类生产者

| 生产者 | 值 | 生效资格与边界 |
|---|---|---|
| `ep2_activities_legacy_1`，活动传承“踏过圣路”（Walking the Sacred Path） | `pilgrim_xp_gain_mult=0.5` | Dynasty character modifier；选择传承有 EP2 条件。不是泛称“冒险遗产” |
| `just_one_more_hill_perk`，“复越高山” | `0.2` | 放在 `government_character_modifier` 中，**government_is_theocracy** 才生效；不是所有拿到 perk 的人物都加20% |
| `baptistery_pilgrims_hospice_01` | `0.05` | ecclesiastical domicile 内部建筑 |
| 同建筑 `_02` | `0.05` | previous_building 指向 `_01` |
| 同建筑 `_03` | `0.05` | 升级链，有主建筑资格 |
| 同建筑 `_04` | `0.05` | 升级链，有主建筑资格；四个定义不能直接说同时+20% |

精确来源为 `01_ep2_dynasty_perks.txt:36`、`00_wanderer_2_wayfarer_tree_perks.txt:91–94`、`11_ecclesiastical_domicile_buildings.txt:3867/3910/3957/4004`。JSON `xp_multiplier_producers` 保存全部六条和 pin。

实际键是 `pilgrim_xp_gain_mult`，不是 `pilgrim_experience_modifier`。后者在覆盖范围内零字面命中。`pilgrim_xp_degradation_mult` 只有格式显示定义（`00_definitions.txt:3021`），没有赋值生产者；pilgrim trait 本身也没有 `monthly_track_xp_degradation`。不能由这个键名编出经验每月衰减。

整轮另有[精确EXE静态研究](research-v5-native-trait-xp.md)，已闭合原生 `add_trait_xp` 算术（EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，该专题JSON pin见库存 `native_xp_semantics`）。人物须已持该特质，单track解析到索引0。定点标度Q=100000：

```text
base > 0: factor_raw = Q + pilgrim_xp_gain_mult_raw + trait_track_pilgrim_xp_gain_mult_raw
base < 0: factor_raw = Q + pilgrim_xp_loss_mult_raw + trait_track_pilgrim_xp_loss_mult_raw
delta_raw = trunc_toward_zero(base_raw * factor_raw / Q)
new_xp_raw = clamp(old_xp_raw + delta_raw, 0, 100*Q)
```

两个已生效gain键在因子中相加，只做一次向零截断，然后加旧经验、裁到0–100；没有第三个通用XP修正读取。base为0不写XP，缺失modifier返回0；未见因子本身另作下限裁剪。脚本值进入raw之前的换算、`add_trait` 初始化／保留XP仍未闭，源级别块如何预处理也仍是独立问题。这是静态机器码证据，**不是这次真的给某人物加过经验**。

补充全 `common/events/dlc` 四键检索：`pilgrim_xp_gain_mult` 共7处（六赋值、一显示定义）；`trait_track_pilgrim_xp_gain_mult`、`pilgrim_xp_loss_mult`、`trait_track_pilgrim_xp_loss_mult`均0。loss键和degradation显示键不同，不能互换。[费用／奖励／XP公式研究](research-v5-cost-reward-xp-formulas.md)复用同一原生专题，不另造公式。

## 4. 活动配置与表现：确有一条间接经验箭头

`pious_type_option_effect` 与 `very_pious_type_option_effect` 对 pious／Hajj 类型请求活动分 +10／+40；worldly 对应 helper 只对 worldly 生效。`bonus_to_all_types_effect` 实际调用前两种普通 helper；它的“不含 Hajj”注释与 pious helper 明确含 Hajj 的代码不一致，不能以注释覆盖代码。

随后 `resolve_pilgrimage_type_reward_effect:1301–1367` 按活动分 `<25 / [25,50) / [50,75) / >=75` 给 pious 或 worldly 旗标。`give_pious_type_reward_effect:632–670` 才在 P<100 下分别请求 5／10／20／40。因此活动表现既能影响主虔诚，也能影响 **pilgrim 特质经验请求**；不能把这条箭头删掉。Hajj 类型会得到 pious 旗标，但一个只有 hajjaj、没有 pilgrim 的人物不通过该 XP helper 的 trait guard。

距离还有一条间接输入：`account_for_pilgrimage_length_type_effect:1287–1297` 给短途活动分+5、中程+3，长／极长没有该补分。其调用在 `pilgrimage.txt:2380` 的目的地 `on_phase_active` 内、具体 `2417`；初始化0另在 `2748`。不能把抵达补分提前画在出发前，也不能只加途中事件来推最终活动分。选择、自动 pulse、旅途事件、距离补分的 compact 调用索引见 JSON；它不是把所有事件完整重抄一遍。

要分开的无直接倍率项目：距离的主虔诚基数、fidelity、pomp、inner journey 的主虔诚乘数、普通圣地的主虔诚减半、联盟主奖励加成，都没有直接乘到这四个 trait XP 请求的代码。事件、距离可另经活动分或独立写入影响 XP，不能由“无直接倍率”说成“绝无任何间接影响”。

## 5. 礼仪、信条、教义、文化、性格与身份

| 项目 | 真正作用 | 分类 |
|---|---|---|
| forbidden pilgrimage 教义 | 禁止普通朝圣活动资格，并把 pilgrim 列入罪恶特质（weight100、scale2） | 资格／宗教评价；不自动删除或乘 XP |
| encouraged pilgrimage 教义 | can_go_on_pilgrimage、basic_pilgrimage_rewards；pilgrim 为美德（weight30、scale2） | 资格／特质收益／美德 |
| local rites 教义 | local_shrine_offering、can_go_on_pilgrimage、basic_pilgrimage_rewards | 资格／特质收益 |
| mandatory pilgrimage 教义 | can_go、mandatory_pilgrimage、basic rewards；无特质的教义基准有月虔诚−.25、同信仰好感−5 | 资格／特质收益；不等于 XP 倍率 |
| mandatory Hajj 教义 | can_go、mandatory_hajj、basic rewards；相关教义基准同为−.25／−5；身份补发也读该条件 | 资格／hajjaj 收益／身份 |
| Acts of Apostles 信条 | pilgrim 被列为美德（weight15、scale1） | 宗教评价，不是+15 XP |
| Secured Pilgrim Routes | PAM＋faith 上25年变量，由决议／事件／effect 生产；抵达 helper 读该变量后走30／20分支 | 直接改变分支请求；不是仅持 Armed Pilgrimages 信条就无条件生效 |
| Warrior Monks 两种文化传统 | 提供 prowess_from_religious_traits，激活 pilgrim／hajjaj 的 prowess 块 | 等级收益，不是 XP 增益 |
| 狂热／愤世嫉俗等个人特质 | 有的是真正 option trigger：zealous、vengeful、NOT cynical；有的仅 ai_chance，另有减压分支 | 每个位置分开判断，不给性格一个通用 XP 系数 |
| 学识、神秘学／药师／医师／巫师等 | 有的选项或 helper 优先分支决定拿不拿 pilgrim XP；如 mystic未满优先拿 mystic经验 | 资格／互斥分支，不是统一经验倍率 |
| 主持人／参加者／随行者／NPC | 不同入口、guard 与接收 scope；麦加持有者和神权身份也另有特例 | 必须标出谁实际收 trait 或 XP |
| 麦加首都、改信、年龄、可用性、冷却、当前旅行／目的地、疾病失效等 | 控制进入或完成活动的资格 | 改变到达写入点的可能，不直接放大每笔经验 |

礼仪参数使用**当前角色 rite**，不能将旧版 faith.tenets 读法直接套用。完整源码参数定位在 `20_doctrines.txt:1652–1791`、`00_pam_tenets.txt:728–737`、`00_combat_traditions.txt:1022–1038`、`tgp_traditions.txt` 的对应传统，以及 `pam_effects.txt:7951–7979`。JSON 来源 SHA 可一一核对。

UI名称另须区分栏位：`reflection_intent` 的官方简中意图名为“深思熟虑”，同名的 fidelity 设置仍是另一个字段；本文保留key防止混淆。Acts of Apostles 的实际显示名会随礼仪语言变化，本文不伪定唯一中译。

## 6. 等级效果原值：不假造最终聚合

源码原值如下；此表的“base／50／100”表示定义层，不宣称这些块在引擎里相加或彼此替换。

| 定义层 | 无条件／文化 | basic_pilgrimage_rewards | mandatory_pilgrimage |
|---|---|---|---|
| pilgrim base | 旅行速度+5、安全+5；文化参数命中 prowess+2；AI zeal5 | 月虔诚倍率+.05、zealot好感+5 | 月虔诚倍率+.35、同信仰+5、zealot+5、clergy+5 |
| track50 | 文化 prowess+3；AI zeal10 | 月虔诚倍率+.1、zealot+10、learning+1 | 月虔诚倍率+.4、zealot+20、clergy+10 |
| track100 | 文化 prowess+3；AI zeal15 | 月虔诚倍率+.1、zealot+20、异文化+5、learning+2 | 月虔诚倍率+.4、zealot+40、clergy+10 |
| hajjaj（无track） | 伊斯兰好感+5、旅行速度+5、安全+5；文化 prowess+2；AI zeal10 | 无该条件块 | 它读取 mandatory_hajj：月虔诚+.35、同信仰+5、zealot+10 |

`_traits.info:196–240` 明确 track 以0–100经验门槛定义、门槛升序、简写产生同名 track；`242–256` 说明 culture／rite 条件修正。精确EXE另已看到**加载后的modifier容器先root、再各已达threshold折入同一输出，同ID做ADD**；但源定义到runtime容器的预处理尚未追全。因而源码“.4 offset−.25/add.15”注释不是最终净值证明，不能直接用“.35+.4=.75”或“.35+.4+.4”计算月虔诚，也不能说已实测“完全替换”。应区分“loaded fold已见”与“源码各档净效果仍未闭”。

下游还会读 XP：朝圣传说种子读取50／60／75；曼荼罗能力／story cycle读25／50／75／100；教廷 pious 值、任命／决议门槛、学识合约成功权重、旅行事件特殊选项等也读取该 track。这些是 **经验的消费者**，不是新经验生产者。所有79个 `has_trait_xp={trait=pilgrim...}` 条件块在 JSON `xp_predicate_readers` 中完整列出。

## 7. AI、事件概率与无影响负结论的范围

活动 `pilgrimage.txt` 的 `ai_will_do`／类型 AI 条件，事件 `ai_chance` 中的 zealous、cynical、greed、zeal 等，以及 `00_activity_scripted_modifiers`、`00_ai_value_effects`，会改变 AI 是否去、选什么。它们不在玩家按下同一合法选项后，把 +5 改成 +10。事件 `weight_multiplier`／随机列表选择影响事件或结局的机会；有些事件 trigger 则是玩家也受约束的硬资格。此三类分开，不将所有带 `weight` 的东西称为 AI（美德／罪恶 weight 也有不同用途）。

本轮负结论有明确边界：

- 没有检出 `pilgrim_experience_modifier`、全局 `trait_xp_gain_mult` 或 `trait_track_pilgrim_xp_gain_mult` 实际字面生产者；不能把月生活方式经验增益套到 pilgrim track。
- 没有 pilgrim 的字面负经验／set XP 写入，也没有其 monthly_track_xp_degradation；没有显式 hajjaj 删除或 pilgrim↔hajjaj 自动替换。这不证明引擎、控制台、外部模组绝无这些能力。
- 扫描文化／信条／教义／traits／modifiers 后，直接 XP 倍率生产者仍只有上列六条；文化 prowess、宗教好感／美德和主虔诚修正不得混入经验率。
- 在固定结算旗标且不改变独立事件分支的条件下，主虔诚公式中的排场／普通圣地等不是 trait XP 公式因子；短途／中程补分是另一条真实间接路径。
- 本清单穷尽的是当前源内目标写入者、验证过的动态绑定、倍率生产者、直接条件／消费者及活动分输入。没有声称枚举整个世界一切因果祖先：钱、战争、健康或任意人物事件都可能影响能否活着到达一个写入点。

## 使用和验证边界

供游玩智能体参考时，应先检查当前版本／机器／来源 SHA，再以原生实际人物、trait XP、rite、活动类型、旅队 scope 和事件选项确认资格；这里是规则库存，不能直接证明某次已经授予或某笔经验已到账。不要执行两个互斥选项来“补齐”库存，也不要凭脚本请求量覆盖实际人物经验。

本线程实际做过：全范围检索、写入块与动态绑定核对、来源 SHA 回读、JSON 序列化往返，以及生产器限定检查。整轮的另一线程完成精确EXE静态XP算术专题，本线程已实读并pin它。没有新游戏、当前DLC资格或实际人物增量验证；异常抵达默认解析、trait初始化和源级别预处理保持未知。

存储勘误：早期未交付派生 JSON 曾因重复保留祖先上下文达到803,460 B，超过本线程512 KiB子额；已先留原大小／SHA／原因的小回执，再原位缩为共享pin的紧凑索引，没有复制超额原件。该历史超限不追认为通过。回执在外置任务目录 `pilgrim-inventory-size-correction.actual.json`；最终体积与类型检查结果见交付消息及 JSON验证记录。

## 附录：全部36处历史／静态创建 trait 赋值

此处为 `trait = pilgrim/hajjaj` 的初始或创建赋值，不是 `add_trait` 运行时授予；历史人物ID和脚本root均原样保留。`.lookup` 的旧索引记录仅映射名字，不另算创建效果。

| ID | 来源 | 行号 | 人物ID／脚本root | 赋值 |
|---|---|---|---|---|
| W014 | `common/scripted_character_templates/04_ep2_james_character_templates.txt` | 4 | `pilgrim_character` | `trait = pilgrim` |
| W016 | `common/scripted_character_templates/04_fp3_character_templates.txt` | 173 | `fp3_gnostic_paragon` | `trait = pilgrim` |
| W017 | `common/scripted_character_templates/04_fp3_character_templates.txt` | 284 | `fp3_zoroastrian_armed_pilgrim` | `trait = pilgrim` |
| W022 | `common/scripted_effects/00_historical_characters_scripted_effects.txt` | 1300 | `spawn_historical_characters_effect` | `trait = pilgrim` |
| W023 | `common/scripted_effects/00_historical_characters_scripted_effects.txt` | 1405 | `spawn_historical_characters_effect` | `trait = pilgrim` |
| W024 | `common/scripted_effects/00_historical_characters_scripted_effects.txt` | 2780 | `spawn_historical_characters_effect` | `trait = pilgrim` |
| W025 | `common/scripted_effects/00_historical_characters_scripted_effects.txt` | 4452 | `spawn_historical_characters_effect` | `trait = hajjaj` |
| W053 | `events/activities/pilgrimage_activity/pilgrimage_events.txt` | 5017 | `pilgrimage.2050` | `trait = pilgrim` |
| W054 | `events/activities/pilgrimage_activity/pilgrimage_events.txt` | 5039 | `pilgrimage.2050` | `trait = pilgrim` |
| W075 | `events/decisions_events/iberia_north_africa_events.txt` | 2196 | `iberia_north_africa.2011` | `trait = pilgrim` |
| W076 | `events/decisions_events/iberia_north_africa_events.txt` | 2234 | `iberia_north_africa.2011` | `trait = pilgrim` |
| W077 | `events/decisions_events/iberia_north_africa_events.txt` | 2370 | `iberia_north_africa.2012` | `trait = pilgrim` |
| W078 | `events/decisions_events/iberia_north_africa_events.txt` | 2401 | `iberia_north_africa.2012` | `trait = pilgrim` |
| W086 | `history/characters/anglo_saxon.txt` | 7224 | `walpurga_1` | `trait = pilgrim` |
| W087 | `history/characters/anglo_saxon.txt` | 7266 | `walpurga_3` | `trait = pilgrim` |
| W088 | `history/characters/anglo_saxon.txt` | 7286 | `walpurga_4` | `trait = pilgrim` |
| W089 | `history/characters/anglo_saxon.txt` | 7319 | `walpurga_6` | `trait = pilgrim` |
| W090 | `history/characters/armenian.txt` | 9358 | `vardapet_1` | `trait = pilgrim` |
| W091 | `history/characters/bavarian.txt` | 10106 | `bavarian0003` | `trait = pilgrim` |
| W092 | `history/characters/bedouin.txt` | 14442 | `extra_bedouins_0019` | `trait = pilgrim` |
| W093 | `history/characters/berber.txt` | 7307 | `danis0004` | `trait = pilgrim` |
| W094 | `history/characters/berber.txt` | 7706 | `khali0002` | `trait = pilgrim` |
| W095 | `history/characters/eastereggs.txt` | 4108 | `easteregg_ali_kara` | `trait = hajjaj` |
| W096 | `history/characters/eastereggs.txt` | 4796 | `easteregg_ola_jentzsch` | `trait = pilgrim` |
| W097 | `history/characters/eastereggs.txt` | 8232 | `easteregg_shehabulddin_alessawey` | `trait = pilgrim` |
| W098 | `history/characters/ecclesiastical.txt` | 11262 | `et_york_1066_1` | `trait = pilgrim` |
| W099 | `history/characters/egyptian.txt` | 2013 | `bahitawi_1` | `trait = pilgrim` |
| W100 | `history/characters/han.txt` | 145543 | `wang_chuyi_1` | `trait = pilgrim` |
| W101 | `history/characters/han.txt` | 146030 | `jiang_kui_1` | `trait = pilgrim` |
| W102 | `history/characters/irish.txt` | 2180 | `7253` | `trait = pilgrim` |
| W103 | `history/characters/japanese.txt` | 103257 | `jojin_1` | `trait = pilgrim` |
| W104 | `history/characters/khazar.txt` | 1072 | `extra_khazars_1` | `trait = pilgrim` |
| W105 | `history/characters/saxon.txt` | 5193 | `20224` | `trait = pilgrim` |
| W106 | `history/characters/tajik.txt` | 919 | `1000230509` | `trait = pilgrim` |
| W107 | `history/characters/tajik.txt` | 993 | `extra_tahirids_3` | `trait = pilgrim` |
| W108 | `history/characters/viet.txt` | 1736 | `khong_lo_1` | `trait = pilgrim` |
