# 第三期原生简体中文术语库：CK3 1.20.0.3

本词库保存本机原版 CK3 **1.20.0.3 Crozier** 的简体中文与英文名称、使用上下文和第三期的替换理由。它覆盖旧稿 129 个 cue、9 份板卡规格及 19 个实际 ASS 文件中的术语；完整目录包含 **246 个原生 localization key、52 组用词规则和 68 份来源文件 pin**。逐 key 的精确原文、语言、文件路径、源行及完整文件 SHA-256，以及 GUI／定义上下文，见[机器可读词库](episode03-native-chinese-terminology-1.20.0.3.json)。JSON 保留原文格式、概念引用和占位符，不把解释性的展开结果冒充原字符串。

此库把概念标题、按钮原文、事件名、状态名和教学解释分别记录。例如正式概念是“围攻进展”，原生强攻提示也会写“围攻进度”，每日明细标题则是“每日进度”。引用具体原图时保留该处原文；新板卡和旁白的正式概念采用概念标题。旧专题里的“围城”“总工作量”等历史标题与研究变量保留原样，后续文案采用本库的名称及限定。

这是已完成证据的离线入库：本次没有启动 CK3／Steam，没有新增实机行为验收，也没有进行成片 1× 人工观看或记录 signoff。只整理简体中文和原生英文，没有翻译其他七种语言。

## 版本与来源

| 项目 | 已核对的来源 |
| --- | --- |
| 原版目录 | `C:/SteamLibrary/steamapps/common/Crusader Kings III/game` |
| 当前安装的 `binaries/ck3.exe` | 101039736 bytes；SHA-256 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`；本次只读重算 |
| Steam build | `25652598`；回链已有精确版本研究与实机登记，本次没有执行新的 Steam 版本验收 |
| 围攻中文 UI 本地化 | `localization/simp_chinese/gui/siege_window_l_simp_chinese.yml`；5425 bytes；SHA-256 `d332a17e5facc1d231bf22ae1241c405bc1ae2fe1f2f399c9915755ff7844b59` |
| 围攻英文 UI 本地化 | `localization/english/gui/siege_window_l_english.yml`；5718 bytes；SHA-256 `73475a83a2df57d188788c95f4e95be9b231a94f8c732d683355439f0a56d3dc` |
| 中文概念名称与说明 | `localization/simp_chinese/game_concepts_l_simp_chinese.yml`；350826 bytes；SHA-256 `66f9adef09db299f100c3b28ffbcd37d675c746c4ff1aa05927af8d66ac8de86` |
| 原版围攻窗口 GUI | `gui/window_siege.gui`；SHA-256 `8236d9d1ca373dc19d9e138948864b84887a4516756e1b293f26e2cd88c6b0b9` |

全部来源文件的完整 pin 见 JSON 的 `source_pins`；具体中文／英文源行见 `native_keys`，GUI 与定义的窄上下文见 `gui_and_definition_contexts`。更换游戏版本时应先核对这些文件与 EXE 的实际 SHA，再重新提取名称及相关绑定，不能仅沿用版本号。

## 完整名称与替换规则

下表的“讲解用名”明确不是独立原生 UI 字段。每组的旧词、出现 cue／板卡、推荐理由及未闭合边界保存在 JSON 的 `terminology_groups`；每个原生 key 的完整中英文本在 `native_keys`。表内军团规模、创建人数和 60／69 是本案及其兵种的例子，不是所有兵种共有的固定数字。

| 类别 | 原生名称或明确讲解用名 | key | 建议 |
| --- | --- | --- | --- |
| 围攻 | 围攻 | game_concept_siege | 正式概念统一用围攻；围攻窗口是自然界面称呼。 |
| 围攻 | 围攻进展 | game_concept_siege_progress, SW_TT_PROGRESS | 首次定义围攻进展；具体讲数值与完成比例时明确区分。 |
| 解释性量 | 累计围攻进展（讲解用名） | SW_TT_PROGRESS, game_concept_siege_progress | 把工作/已做工作改说已经积累的围攻进展；首次说明这是为理解比例所作的划分。 |
| 解释性量 | 完成围攻所需的总进展（讲解用名） | SW_TT_PROGRESS, game_concept_siege_progress_desc | 采用完成围攻需要达到的进展总量，后文可简称所需总进展。 |
| 围攻 | 每日围攻进展 | SW_DAILY_SIEGE_PROGRESS, SW_TT_DAILY_PROGRESS, SW_DAILY_PROGRESS | 旁白用每日围攻进展/每天增加多少进展；读tooltip时可逐字说每日进度。 |
| 军队 | 士兵数量 / 当前参与围攻的士兵数 | game_concept_soldiers, SW_TT_MEN_BALANCE_BASIC_INFO | 当前实际参加围攻的士兵数是清楚口语；保留符合条件这一限定。 |
| 军队 | 守军 | game_concept_garrison, SW_TT_GARRISON | 名称正确，保留。 |
| 解释性量 | 守军比例 / 计算使用的有效守军上限 | game_concept_garrison, SW_TT_PROGRESS | 说明分子为当前守军、分母为计算所用有效上限；满员是口语状态。 |
| 围攻 | 城防等级 | game_concept_fort_level | 城防数字/城防改说城防等级。 |
| 兵种 | 攻城武器 | game_concept_siege_weapons, SW_SIEGE_WEAPON | 正式名称用攻城武器，不用器械作为面板字段名。 |
| 兵种 | 射石机 | mangonel | 本案mangonel用射石机；泛称投石机不能替代这个具体兵种名。 |
| 兵种 | 围攻等级 | MAA_SIEGE_TIER | 正式属性名用围攻等级。 |
| 兵种 | 围攻进展 / 天 | MAA_SIEGE_VALUE, REGIMENT_SIEGE_TT | 攻城武器提供的每日围攻进展；如说有效数值，明确是研究计算用修正后数值。 |
| 兵种 | 有效的最大城防等级 | REGIMENT_SIEGE_MAX_FORT_LEVEL | 逐字提示为有效的最大等级为…级城防等级；口语可说对最高多少级城防有效。 |
| 军队 | 军团规模 / 每规模军团士兵数 | STACK_SIZE_MAA, MV_CREATE_REGIMENT_MAX_SIZE_TT, MV_CREATE_REGIMENT_SIZE | 规模1满员10名士兵，当前5名相当于半个满员规模；每档编制改每规模军团士兵数。 |
| 军队 | 由5名士兵开始，并补员至10 | MV_REGIMENT_START_SIZE, MV_CREATE_REGIMENT_MAX_SIZE_TT | 本案常规创建路径按原生提示讲开始人数与后续补员。 |
| 界面计数 | 攻城武器一栏显示60/69 | SW_SIEGE_WEAPON | 仅028/E3A06-011读武器栏时改成攻城武器一栏显示六十/六十九。 |
| 围攻 | 基础 / 兵士 / 围攻士兵 | SW_TT_BASE_PROGRESS, SW_TT_MAA_PROGRESS, SW_TT_MEN_PROGRESS | 034可说说明里列着基础、兵士与围攻士兵。 |
| 事件 | 围攻事件 | SIEGE_EVENT | 讲阶段结算时叫围攻事件；阶段是实现/解说层次词，不伪称正式标签。 |
| 事件 | 围攻事件之间的时间间隔 | SW_TT_TIMER, SIEGE_ACTION_BREACH_EFFECT | 口语可简称围攻事件间隔。073/009的16天是当前间隔，不是再等16天。 |
| 围攻 | 最大剩余时间 / 最多持续… | SW_TIME_LEFT_TT, SIEGE_WINDOW_END_DATE_SHORT, SIEGE_WINDOW_END_DATE | 解释可说预计剩余时间；直接读原图用最大剩余时间或最多持续…原文。 |
| 事件 | 城墙破损 | SIEGE_ACTION_BREACH | 作为事件名称使用城墙破损。普通描述可说城墙出现缺口。 |
| 事件状态 | 完好无损 / 小缺口 / 大缺口 | SIEGE_ACTION_BREACH_LEVEL_0, SIEGE_ACTION_BREACH_LEVEL_1, SIEGE_ACTION_BREACH_LEVEL_2 | 一级/二级状态引用改说小缺口/大缺口；首次可括注内部对应一级/二级。 |
| 事件 | 断粮；状态粮食满仓 / 缺粮 / 断粮 | SIEGE_ACTION_STARVATION, SIEGE_ACTION_STARVATION_LEVEL_0, SIEGE_ACTION_STARVATION_LEVEL_1, SIEGE_ACTION_STARVATION_LEVEL_2 | 事件标题断粮保持；讲两次升级时分别说变成缺粮，再变成断粮。 |
| 事件 | 疾病爆发；状态没有疾病 / 疾病蔓延 / 疾病猖獗 | SIEGE_ACTION_DISEASE, SIEGE_ACTION_DISEASE_LEVEL_0, SIEGE_ACTION_DISEASE_LEVEL_1, SIEGE_ACTION_DISEASE_LEVEL_2, SW_TT_DISEASE_PROGRESS | 事件正式名疾病爆发；状态分别疾病蔓延/疾病猖獗。 |
| 事件 | 守军逃亡 | SIEGE_ACTION_DESERTION | 事件名使用守军逃亡。 |
| 事件 | 僵持 | SIEGE_ACTION_STALEMATE | 名称正确，保留。 |
| 概念与按钮 | 强攻 / 强攻堡垒 / 停止强攻 | game_concept_assault, SW_START_ASSAULT, SW_STOP_ASSAULT, SIEGE_ASSAULT_TT_INFO_ACTIVE | 概念可叫强攻；讲点击的按钮原文强攻堡垒，进行中提示强攻进行中，停止按钮停止强攻。 |
| 预览 | 减员（未开启提示） / 伤亡（进行中提示） | SIEGE_ASSAULT_TT_INFO, SIEGE_ASSAULT_TT_INFO_ACTIVE | 开始预览按提示说预计每日减员；进行中提示按原文说每天造成伤亡。 |
| 围攻状态 | 围攻进度不会推进 / 没有足够士兵 | SW_BLOCKED_LARGE_GARRISON, SW_BLOCKED_MOVEMENT_OR_COMBAT, SW_TOO_FEW_SOLDIERS | 可以口语说围攻受阻，但说清士兵不足或移动/战斗原因。 |
| 军队 | 补员；到场增援为解释口语 | game_concept_reinforcements, MAA_REINFORCING, MV_REGIMENT_START_SIZE | 同团人数恢复叫补员；另一支军队抵达可叫增援/援军，说明其到场后参与围攻。 |
| 按钮 | 合并军队 | MERGE_ARMY | 提操作用合并军队；普通合兵是口语。 |
| 军队 | 军队 / 军团 / 士兵 / 兵士 / 征召兵 / 将领 | game_concept_army, game_concept_regiment, game_concept_soldiers, game_concept_men_at_arms, game_concept_levies, game_concept_commander | 专有概念用这组原生名称；指挥官若作为概念名改将领。主力为指本案较大那支军队的自然口语。 |
| 战争 | 占领 | game_concept_occupation | 军事占领用占领；由威廉控制是自然解释。 |
| 领土 | 地产 / 设防地产 | game_concept_holding, game_concept_fortified_holding | holding作为概念用地产，fortified holding用设防地产。刘易斯可以具体说城堡/地产。 |
| 头衔 | 伯爵领 / 伯爵领首府 / 男爵领 | game_concept_county, game_concept_county_capital, game_concept_barony | 096/117的县/县首府用伯爵领/伯爵领首府；所有设防地产占领才说完全占领这个伯爵领。 |
| 战争 | 宣战理由 | game_concept_casus_belli | 098/099改宣战理由。 |
| 战争 | 战争分数 | game_concept_war_score | 全称战争分数；占领分项是说明其中占领一项的口语。 |
| 战争界面 | 战斗 / 囚禁 / 占领 / 计时 | WAR_OVERVIEW_BATTLES, WAR_OVERVIEW_IMPRISONMENT, WAR_OVERVIEW_OCCUPATION, WAR_OVERVIEW_TICKING | 逐项对照标题用战斗、囚禁、占领、计时；解释可说俘虏提供分数、占据目标提供分数。 |
| 战争 | 战争目标 | game_concept_war_target | 110改战争目标，说明控制目标的持续时间。 |
| 战争按钮 | 强制执行要求 | TAB_VICTORY, SEND_BUTTON_VICTORY | 111及任何按钮卡使用强制执行要求。 |
| 战争 | 和平提议 / 无条件和平 / 投降 | game_concept_peace_offer, TAB_WHITE_PEACE, TAB_DEFEAT | 和谈是清楚口语；若具体点按钮用原生名。 |
| 资源 | 金钱 / 战利品 / 围攻获胜 | game_concept_gold, SW_TT_LOOT, msg_siege_won, msg_siege_loot | 正式资源名金钱，围攻窗口名战利品，通知标题围攻获胜。金币图标是解释口语，不能标作原生概念标题。 |
| 头衔与归属 | 持有者 / 头衔 / 公爵 / 伯爵 | game_concept_holder, game_concept_title, duke, count | 头衔角色正式称持有者；法律上归谁为解释口语。 |
| 领土 | 领地首都 | game_concept_realm_capital | 正式概念为领地首都，别和伯爵领首府混用。 |
| 战争 | 战争 / 战斗 / 进攻方 / 防守方 | game_concept_war, game_concept_battle, WAR_SCORE_ATTACKER_TICKING, WAR_SCORE_DEFENDER_TICKING | 这组名称为原生概念或原版行文；本案站在进攻方保持。 |
| 不同概念 | 占领 / 控制力 | game_concept_occupation, game_concept_control, game_concept_county_control | 军事控制是占领的口语；另一个原生概念控制力是伯爵领内政数值。 |
| 人名 | 威廉 | William | 中文主体用威廉；英文行William为原生对应。 |
| 人名 | 哈罗德 / 哈拉尔 / 利奥夫温 | Harold, Harald, Leofwine | 这些姓名原文正确；Harold与Harald不能互换。 |
| 地名 | 诺曼底 / 英格兰 / 刘易斯 / 肯特 | d_normandy, k_england, b_lewes, c_kent | 中文主体统一这些原生地名；中文板卡case可写威廉 / 刘易斯，1067。 |
| 文化地名 | 南撒克逊 / South Seaxe | cn_south_seaxe, c_sussex | 本场UI用南撒克逊，英文对应South Seaxe；Sussex是基础名的英语，不能替代同场文化UI名。 |
| 具体战争 | 诺曼人征服英格兰；宣战理由类型入侵 | war_1066_Norman_Conquest, norman_conquest_cb | 实际战争标题诺曼人征服英格兰保留，CB类型名为入侵。 |

## 城墙破损与缺口状态

| 层次 | 原生简中 | 原生英文 | key |
| --- | --- | --- | --- |
| 围攻事件 | 城墙破损 | Breach | `SIEGE_ACTION_BREACH` |
| 城墙状态 0 | 完好无损 | Intact | `SIEGE_ACTION_BREACH_LEVEL_0` |
| 城墙状态 1 | 小缺口 | Small Breach | `SIEGE_ACTION_BREACH_LEVEL_1` |
| 城墙状态 2 | 大缺口 | Large Breach | `SIEGE_ACTION_BREACH_LEVEL_2` |

中文原文位于围攻窗口本地化第 24、30、31、32 行；英文对应文件同源行。“城墙破损”是事件名，“小缺口／大缺口”是状态名，不能把事件与状态统一改成“破口”。对当前 1250 份简中本地化的已保全搜索没有找到围攻用的独立 `breach`／`large_breach` 概念标题或“小破口／大破口”词组；计谋中的 `scheme_breach` 不属于这项围攻证据。

已直接复看历史 1067 年 4 月 15 日原图：提示写的是**“城墙：大缺口”**，事件间隔效果为 `-30%`。原图 `ui6-162858-4cd42097/desktop.png` 的 SHA-256 是 `d4be5849b81844eea9e22430c24a14e174d03ef3d01b3fb3ceeb77f1a3dc57db`，完整路径见 JSON 的 `old_case_ui_references`。旧 `E3A06-017` 的“大破口”是稿件转录用词，不能标作原生 UI 原文。旁白可说“城墙出现缺口”，正式状态卡使用“小缺口／大缺口”。

同样区分断粮事件与补给状态：事件名“断粮”，状态依次为“粮食满仓／缺粮／断粮”。疾病事件名为“疾病爆发”，状态为“没有疾病／疾病蔓延／疾病猖獗”；每日进展明细里的“疾病”仍按该处原文引用。

## 攻城武器、兵士与围攻士兵是三处不同栏目

| 具体位置 | 原生中文及英文 | 已闭合的含义 |
| --- | --- | --- |
| 围攻窗口计数栏 | 攻城武器 / Siege Weapons；`SW_SIEGE_WEAPON` | GUI 第 1043 行给标签，第 1049 行读取 `SiegeWindow.GetSiegeMachinesCount`。本案可说“一栏显示 60／69”；本项不增造台、件或名的单位。 |
| 每日进展明细 | 兵士 / Men-at-Arms；`SW_TT_MAA_PROGRESS` 的原字符串为 `[men_at_arms\|E]` | 有效军团围攻属性按当前规模折算后汇总的贡献，原生 getter 为 `0x247ECE0`。它不是普通人数超过守军的那一项，也不能认定所有贡献必来自纯攻城武器兵种。 |
| 每日进展明细 | 围攻士兵 / Besieging Soldiers；`SW_TT_MEN_PROGRESS` 的原字符串为 `围攻[soldiers\|E]` | 对普通非负人数及本版本 defines，局部计算是 `0.01 × floor(max(0, B − G) / 200)`。`B` 为符合条件的实际围攻士兵数，`G` 为当前守军。 |

`SW_TT_MAA_PROGRESS` 与 `SW_TT_MEN_PROGRESS` 的中文原字符串在 `siege_window_l_simp_chinese.yml` 第 13／14 行；概念 `men_at_arms` 展开为“兵士”，`soldiers` 展开为“士兵”。不能把“兵士”当作所有士兵的同义词，也不能因武器栏叫“攻城武器”而把每日明细的“围攻士兵”一并替换。旧 `034` 读的基础／兵士／围攻士兵应保留，旧 `028` 和 `E3A06-011` 读武器计数时改为“攻城武器一栏显示……”。

这两项的标签绑定已有当前 EXE 离线补证：每日函数区域 `0x251F170..0x251FD54` 为 3044 bytes，SHA-256 `dbbd82904d3959e6f2d4278b893f2c1f95563cc463f054a1213935a2b1338563`，与原保全区域一致。兵士项的调用位于 `0x251F366` 或 `0x251F390`，`0x251F3AF` 指向字符串 `SW_TT_MAA_PROGRESS`；人数项在 `0x251F473..0x251F498` 取得守军及符合条件的围攻人数并完成减法、钳制、整数除以 200 和乘 `0.01`，`0x251F4B5` 指向 `SW_TT_MEN_PROGRESS`。两段窄字节、反汇编、字符串和 SHA 均保存于 JSON 的 `daily_progress_column_mapping`。

已直接复看 1067 年 1 月 21 日原图 `ui6-155756-6c372ed9/desktop.png`（2877743 bytes；SHA-256 `56475504a404c8d4037e93e76dab276b3b8ef93adbc17a3b29e1c155606e1aad`）：每日进度显示 `2.7`，明细为基础 `+1.0`、**兵士 `+1.4`、围攻士兵 `+0.3`**；实际围攻人数 6746、守军 460，局部人数项 `0.31` 与一位小数的 `0.3` 相容，不是 `1.4` 的来源。原始补证文件 `daily-tooltip-label-scope.json` 为 15801 bytes，SHA-256 `cdfed0aec6051a2cb25d213f830d6298adc3368911aac5da43b3b74a2fbddd76`，精确路径及 pin 在 JSON 的 `source_provenance.daily_column_proof`。

这只闭合了两个明细项目的计算与标签，不是本案完整每日公式的实机复算。每个军团的实时有效属性、全部角色／缓存修正和普通每日进展 getter 尚未全部独立读到；一位小数格式的舍入／截断方式也没有因本次标签核对而闭合。区间净增 `2.78` 继续是两端读数的差，不能用显示的三项精度补造完整算式。`B` 来自省份内满足条件的军队／军团当前人数，不是玩家全部地图军队总和。

## 进展数值、阶段间隔与军团规模

`SW_TT_PROGRESS` 的精确中文模板是 `#T [siege_progress|E]：#V $PROGRESS|1$/$TOTAL|0$#!#!\n`。讲解可以把这两个数分别称作“累计围攻进展”和“完成围攻所需的总进展”，首次说明是为理解比例而采用的教学称呼；原版没有在所查界面为它们另设“工作／总工作量／净 work／日速”标题。进展数值与完成百分比要分开，总进展也不能讲成始终固定的门槛。有效守军上限等研究量没有因为取了中文名就变成已独立采到的 UI 字段。

旧 `073` 的 16 天位于“围攻事件”标签下：`window_siege.gui` 第 1193 行显示 `SIEGE_EVENT`，第 1201 行读取 `SiegeWindow.GetSiegePhaseLength`；第 1181 行的圆形进度读取 `GetPhaseProgress`。可说“窗口此时显示 16 天的围攻事件间隔，并不是从现在还要等 16 天”。`SW_TT_TIMER` 的 `$DAYS$` 则是提示里的“下一个围攻事件”，`$TOTAL$` 是发生间隔，不能把二者混读。城墙破损效果说明直接写“围攻事件之间的时间间隔”；不把当前全部间隔变化只归因于缺口。另一个 ETA 提示为“最大剩余时间／最多持续……”，口语“预计剩余时间”应保留估计含义。

具体兵种 `mangonel` 叫“射石机 / Mangonels”。其“围攻等级”与地产的“城防等级”是不同属性。“有效的最大等级为……级城防等级”可口语简称“对最高多少级城防有效”，不添加新属性 key。原生“军团规模”“每规模军团士兵数”与当前人数分开；本案射石机规模 1 满员 10 名、常规创建先有 5 名再补员，是该兵种与创建路径的例子。“半个满员规模”是计算解释，不等同于物理攻城机台数。

同团恢复人数使用原生概念“补员”，另一支军队抵达可以自然说“增援／援军”，抵达后是否满足参与围攻条件仍需实际状态。按钮名称为“合并军队”；合并操作本身不奖励额外围攻进展。

## 强攻、战争和人物地名的用法

概念名是“强攻”，开始按钮是“强攻堡垒 / Assault Fort”，停止按钮是“停止强攻 / Stop Assault”，进行中提示写“强攻进行中”。未开启时的预览使用“减员”，进行中提示使用“伤亡”。原生措辞不能把预览变成已经发生的死亡证据；实际兵力净少也不能全部自动归因于强攻阵亡。游戏暂停、围攻受阻和停止强攻分别描述不同状态。

战争分数的现有标签 key 为战斗、囚禁、占领、计时；解释可说“俘虏提供战争分数”“控制战争目标获得计时分数”，原版 tooltip 本身也会使用俘虏措辞。按钮是“强制执行要求 / Enforce Demands”，旧“强制要求”须改。这里保留本地化 key 与原版 GUI 所暴露的 getter／tooltip 证据，不声称静态 GUI 字面直接调用这些标签 key，或完整二进制标签路径已闭合。名称校正也不取消总分 `±100` 的提前返回、占领截断与 cap 顺序，以及本案占领增分分母未复算的边界。

领土正式名称采用“地产／设防地产”“伯爵领／伯爵领首府／男爵领”，领地首都不能与伯爵领首府混用。军事上的控制可以口语解释占领；另一个内政概念“控制力”不能替代占领。头衔持有者与军事占领者分开。资源概念正式名为“金钱”，围攻栏为“战利品”，通知标题“围攻获胜”；“金币图标”可作图示解释。本案通知奖励 9 不证明整段金钱余额变化只有占领这一原因。

人物使用威廉、哈罗德、哈拉尔、利奥夫温，Harold 与 Harald 不互换。1066 开局及本案没有额外事实支持时，不把威廉称为英格兰国王，也不代换成另一个绰号。地名采用诺曼底、英格兰、刘易斯、肯特。本场文化名是 `cn_south_seaxe` 的“南撒克逊 / South Seaxe”；`c_sussex` 的“萨塞克斯 / Sussex”是基础名，不能代替同场文化 UI 名。原版 `c_sussex` 的盎格鲁撒克逊／古撒克逊命名列表指向该文化名，上下文保存于 JSON。

具体战争标题是“诺曼人征服英格兰”，而 `norman_conquest_cb` 的类型名是“入侵 / Invasion”。本案不是普通 claim 宣战理由；不能因最初选题的计划或通用术语表，把后来实际拍摄的诺曼入侵改写成宣称战争。

## 外置来源与现有研究回链

原始术语证据、旧稿出现位置、逐句替换建议及逐板卡建议永久保存在 `D:/ck3-war-episode03-revision-20261003-a01/native-terminology/`。本入库没有复制完整 ASS、旧字幕对白、整份旧稿或过程素材；JSON 保留其精确文件 pin，便于从历史输入核对替换缘由。

| 已保全的外置输入 | bytes | SHA-256 |
| --- | ---: | --- |
| `native-terms-catalog-a01.json` | 832857 | `fe0f603bdaea2a7675fe77b0bda3f35fb4ac5f8ce4615b5956ee4311cbe75a43` |
| `siege-native-evidence.json` | 123744 | `86b36cbcfa36f3b7fea9f07c891c9a0da5f90a827308d65e517fa85f652fa515` |
| `war-names-native-evidence.json` | 159550 | `12194ae12b7b3a4d9178e9201b1f8ac8f5ef1fd76d42e06fa93826ee014df2b1` |
| `old-text-inventory-a01.json` | 467480 | `c113002d7d94e85ca3c61b36a682aae3e43fe70ba596bd11ecf44bf47a5e858c` |
| `cue-and-board-replacement-plan-a01.json` | 399984 | `f7bcf3b77871966f17f57b3366646f6ea7ee22d00bc92cae206ec1b6d140f4ce` |
| `native-terminology-review-a01.md` | 13983 | `61482ecf2996202e60ffa0192e9039eace48e9d595221b7d96777bc2f0072e06` |

计算与实机结论继续回链到[围攻进展研究](episode03-siege-progress-1.20.0.3.md)、[围攻事件研究](episode03-siege-events-1.20.0.3.md)、[强攻研究](episode03-assault-1.20.0.3.md)、[占领及战争分数研究](episode03-occupation-war-score-1.20.0.3.md)、[威廉／刘易斯实机案例](episode03-william-lewes-live-2026-10-03.md)、[案例证据索引](episode03-william-lewes-evidence-index.json)及[1.20.0.3 原生迁移专题](crozier-1.20.0.3-native-migration.md)。本词库不修改这些历史来源的字节或重新解释失败 attempt。

原生说明中“多于守军”与另一阻塞说明中“少于守军”的不同表述，也不授权以本地化文案代替已验证的原生比较规则；起围／每日外层条件未闭合之处继续保留。后续视频改稿及重新排版、配音、编码应创建新输入与新 attempt；这份词库仅提供名称、栏目关系和已保全证据。
