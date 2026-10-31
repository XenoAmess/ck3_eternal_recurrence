# 董卓的专属设定与玩法

**有董卓，而且已经实际以董卓完成第一期取材。** 他在 190 新档是掌握朝政的丞相／权臣，有西凉事件兵、吕布义子关系、《董卓本纪》以及焚雒迁都、诸侯讨伐和诛董危机。原版面板中的六张190推荐卡没有他；本次用外置的纯选人书签追加董卓卡，复用真实`history_id=dong_zhuo_2`，进入后的原生玩家ID为5048。该入口没有修改人物、历史持有、兵力、事件或规则。

初次源码研究与后继实拍均在`machine_id: 4-8e1c2f1861`完成，安装版为CK3 1.20.0.4。本局从190.1.1推进至190.5.1，实际120日、1次原生保存，拍到迁都、讨董开战和市丘单战胜利；讨董战争尚在，未央邀请未触发。机器与能力边界见[实拍记录](filming-01/README.md)，导演稿见[第一期](../episode-01-dong-zhuo.md)。这些机器事实不外推其他执行机。

早期主包源码摘要保留在[source-pins.json](source-pins.json)；本次新增事件、原版依赖、议和覆盖与原生代码的SHA索引在[filming-01/source-index.json](filming-01/source-index.json)。下文未标明覆盖者的模组定义属于主包3780919688；议和包3820784621同路径覆盖必须按实际加载顺序判断。

## 开局就有的特殊设定

| 设定 | 当前代码做了什么 | 来源 |
| --- | --- | --- |
| **挟持献帝的权臣** | 190 初始化强制拜相、设历史辅政者，并调用通用权臣接管；实际傀儡关系仍看当时阶段与资格 | `zz_hd_190_startup_effects.txt:261`；`zz_hd_palace_crisis_effects.txt:103`；`hd_court_regent_effects.txt:307` |
| **郿国与郿侯** | 动态建帝国级领地容器；190 分支只设 `hd190_mei_container`，另授县侯“郿侯”。不能把旧注释的“郿王”套给当前开局 | `zz_hd184r_dong_effects.txt:39`；`zz_hd_190_startup_effects.txt:800` |
| **西凉事件兵** | 一次性给羌骑 50 组、湟中义从 50 组、重甲步兵 200 组；注释按约三万设计。前两种每组 100 人。部队需补给、不可继承；实际兵数须读回 | `zz_hd184r_dong_effects.txt:7`；`common/men_at_arms_types/hd_regional_maa_types.txt:269`、`:521` |
| **吕布与西凉班底** | 初始化收吕布为义子；吕布、李儒、牛辅、华雄、徐荣、李傕、郭汜等在满足条件时归入董卓宫廷 | `zz_hd_190_startup_effects.txt:308`、`:335` |
| **召位继承** | 给董卓加 acclamation 继承法，避免普通天朝任命路径把相关头衔分散 | `zz_hd_palace_crisis_effects.txt:550` |
| **甲士环卫** | 190 初始化给十年剧情保护，含健康与敌对计谋抑制；诛董的脚本结算前会移除。它不等于免死 | `common/on_action/zz_hd_dynasty_startup.txt:126`；`common/modifiers/zz_hd_historical_timeline_modifiers.txt:9` |

角色历史在 `history/characters/east_asian_liangzhou_180_200.txt:439`，文化凉州，DNA `dong_zhuo`，性格有野心、暴怒、施虐，军事教育四级。历史段写有 192 年死亡记录，但不能用这条历史数据断言从 190 开始玩的董卓届时必死；运行事件另有玩家分支。

## 董卓本纪与焚雒西迁

`common/story_cycles/zz_hd_historical_character_story_cycles.txt:18` 定义可见的《董卓本纪》。本地化包含凉州起家、奉召进京、据有司隶、废立天子、吞并并州、诸侯会盟、迁往长安、迎战联军、扼守关中、据关自守和关中失守等篇章。

**这些是故事阶段，不是同名自由决议。** 190 开局已经完成拜相、废立和吕布归附等状态，不能承诺再从进京重演一遍。

当前 190 联军初始化会把董卓“焚雒西迁”事件排到 31 天后，首轮讨伐检查排到 91 天后；均依历史事件开关及联盟初始化等条件。迁都事件 `hd_palace_crisis.0023` 只有一个选项，调用迁往长安、毁坏雒阳建筑与控制／发展等效果，并推进本纪。**这是专属剧情内容，当前文件未给“坚守雒阳、不焚城”的第二个选项。**

定位：`zz_hd_190_startup_effects.txt:425`；`events/zz_hd_palace_crisis_events.txt:555`；`zz_hd_palace_crisis_effects.txt:254`、`:304`。讨董战争有专门流程，不能默认能用普通和约任意改写，组合议和规则见[代码分析](code-analysis.md#议和先区分普通战争和专用战争)。

本局迁都在190.2.1实际触发，讨董战争在190.4.2实际成立。31天、91天分别是源码排期与宣战检查，不能对其他新档保证同日开战。当前有效的议和覆盖`common/scripted_effects/zz_hd_anti_regent_lifecycle_effects.txt:249`仍检查进攻方控制虎牢758或洛阳787；满足条件时经`hd_peace_route_script_end_effect`及防重复守卫按进攻方胜利结算。迁都长安不会移除这两处判定。本局没有走到该战争结算，不能把代码研究当成实机分流验收。

## 最适合拍摄的玩家选择是未央之约

这条链很值得作为视频题眼：**知道入朝可能被杀，还要不要去？**

当前脚本沿用 `hd_dong_192_*` 的旧命名和“192 年诛董”注释，实际 190 新档调度已是 **开局后 516 天** 检查，不能按函数名解说成固定 192 年。只有历史事件开启才在开局安排这次检查。

检查时要董卓、王允在世，汉朝天子存在，董卓不是天子本人，王允未被囚禁，且没有已排期／已处理的冲突状态。**吕布不是启动这次检查的必需存活条件**；他影响后续谁来动手。

玩家董卓会得到“未央之约”两项选择：

- **照常入朝**：进入诛董执行流程。脚本在满足后续条件时直接结算谋杀；吕布在汉境内且未被囚禁时由吕布动手，否则可由王允动手，不是普通暗杀计谋随机掷骰。
- **称病不出**：将检查推迟 **365 天**。当前效果没有写入“永远免于诛董”的标记，不能宣传成一次选择永久安全。

若王允或吕布由玩家控制，调度也有让相应玩家决定动手或延后的入口；玩家董卓分支优先。旧 `hd_dong_queue_murder_effect` 已为空，不能再说两场讨董战争结束后三十天就必然遇刺。

代码里 `<200.1.1` 只位于某条条件不满足时的重试分支，不能据它承诺“熬过 200 年就安全”。

这是已完成离线分析的专用选择：若后续仍要保持董卓主角存活，应在核对本次原生显示项后选`.0020.b`称病，而不能沿陌生事件默认第一项。杀掉或囚禁吕布不能据此宣称已解除王允兜底的脚本诛董。本次取材停在190.5.1，未执行这一策略，也未注册新的生产事件策略。

定位：`common/on_action/zz_hd_dong_aftermath_on_actions.txt:57`；`common/scripted_effects/zz_hd_dong_aftermath_effects.txt:117`、`:122`、`:167`、`:173`；`events/zz_hd_dong_aftermath_events.txt:4`、`:156`。

## 董卓能用哪些决议

本轮搜索没有找到以董卓身份为唯一显示条件的独立决议清单；专属部分主要放在初始化、本纪和事件里。可以另看适用于他的**通用权臣制度**：

- **弃天子自立**：显示要求为当前通用权臣；执行要求有地、未被囚禁，消耗 **1,000 威望**。效果意图为解除控制、卸去官职、交还满足条件的京畿／相关头衔，再带其余领地独立。这不是董卓独占按钮。董卓另有历史辅政修复钩子，两者实际联动尚未验证，不能承诺点后永久摆脱剧本。
- **控制天子**：通用决议有摄政、势力与原生傀儡等要求，并且要求当前不存在通用权臣等状态。董卓已完成控制时不能把它当作可重复点击的收益按钮。
- **膺禅登极**：确有受禅流程，但要真实实封王等身份、对应摄政关系、`diarchy_swing>=80`、皇帝为自己原生傀儡，以及 DLC／游戏规则等条件。190 的帝国级郿国容器缺 `wj_rf_rank=2`，不能据标题等级承诺开局受禅称帝。县侯 `wj_peer_rank` 与实封王 `wj_rf_rank` 也不是同一个字段。

宫廷政变、募天子亲兵等属于皇帝反制权臣的玩法，不应列成董卓自己的专属决议。

定位：`common/decisions/hd_court_decisions.txt:4`；`common/scripted_effects/hd_court_regent_effects.txt:430`；`common/decisions/WJ_emperor_puppet_decisions.txt:12`；`common/scripted_triggers/WJ_abdication_triggers.txt:3`、`:9`。

## 第一期的叙事方向

用户已确定董卓为第一期主角，曹操为第二期。曹操讲“几座小城如何起家”；董卓讲“手里握着天子和强兵，如何守住权力与性命”。外面是诸侯讨伐，里面是王允和吕布，他的矛盾集中，适合反派视角。

已定片名为**《洛阳炙手，公卿憎我，天下讨我》**。本次实拍按开局身份、西凉军、焚雒迁都、诸侯讨伐和市丘交锋收束；“未央之约”只作注明来源的后续事件预告，不能剪成已经接到邀请或已经称病。市丘胜利有实际保存中的`win=5048`结果支持，原生终态查询失败仍保留；它不代表整场讨董战争获胜。

具体拍法见[第一期董卓导演案](../episode-01-dong-zhuo.md)；[第二期曹操](../episode-02-cao-cao.md)另用新档，不把两条线拼成同一局。

## 实拍后已分析的开局与任命事件

下表是已保存来源的事件知识，不是已注册的自动选择策略。显示项会被trigger过滤，源文件第一项与原生第一显示项须分别绑定。完整文件SHA按表内路径查询[本次来源索引](filming-01/source-index.json)。

| 事件 | 选项与效果 | 来源 |
| --- | --- | --- |
| `tgp_china_career.0001`“侍奉天子” | A加每月功绩+5%、儒学教育经验+10%；B加每月影响力+5%、生活方式经验+10%，修正均无显式期限。保存emperor最高领主scope不切换玩家。本局首个实例2的root为董卓5048，emperor8928。 | 原版`events/dlc/tgp/tgp_china_career_events.txt:14`；`common/modifiers/10_tgp_modifiers.txt` |
| `ep3_admin_events.0002` | 获得最高级实地总督头衔的介绍。prosperity在有地且merit政府时显示，加3年勤勉总督：建筑花费-10%、`build_speed=-0.1`、发展增长+10%、压力获得+20%；lazy加压力、diligent减压力。inspection另需实地county，加free_inspection并按同样性格处理压力；通用`.a`仅减miniscule压力。 | 原版`events/dlc/ep3/ep3_admin_events.txt:190`；`common/modifiers/10_tgp_modifiers.txt:1026` |
| `realm_maintenance.2001` | 新获帝国级primary_title、有前持有人且没有另一个帝国头衔即可触发，不专指取得天子`h_china`。immediate在有ACH DLC时重置加冕法律，再设had_coronation_prompt和quirk；唯一选项中的加冕分支却要求没有该flag。`get_title`只在show_as_tooltip，不能说点击后才授头衔或已经加冕。 | 主包`events/realm_maintenance_events.txt:281` |
| `char_interaction.0111` | 总督任命告知。immediate调用change_to_administrative_effect，唯一确认项无额外效果。helper会按政府、领主及家宅条件分支，不能从名字认定董卓已改成拜占庭行政制。 | 议和覆盖`events/interaction_events/character_interaction_events.txt:698`；原版`common/scripted_effects/00_administrative_effects.txt:47` |
| `hd_hanfl.1301`“五德之次” | 五项依次土、金、水、木、火；写王朝德运并替换不限期修正，对应管理、军事、谋略、学识、外交生活方式经验+5%。无前德加minor合法性；按火→土→金→水→木→火相生加medium合法性；其他承继减minor威望。土德只有在前德为火时才是相生奖励，须读本次saved scope。 | 主包`events/zz_hd_hanfl_dewu_events.txt:7`；`common/scripted_effects/zz_hd_hanfl_effects.txt:88`；`common/modifiers/zz_hd_hanfl_modifiers.txt:137` |
| `diarchy.0021` | 本任期的权臣／共治介绍。immediate设intro flag，非ruler才另加500无经验威望。`.a`与`.a.sedate`按arrogant专用条件互斥显示，均向diarch侧移动minor权力天平；前者按ambitious/content、后者按diligent/lazy改变压力。`.b`加minor威望，arrogant减压力、humble加压力；仅玩家lazy显示`.c`，减medium威望、卸任并减massive压力。`trait=`不等于获得trait。 | 主包`events/diarchy_events/diarchy_events.txt:167` |

五德入口`common/on_action/zz_hd_hanfl_on_actions.txt:70`同时涵盖`h_china`和地方帝国，要求celestial政府、王朝无现有德运等，保存前朝德运后排7天事件。五德弹窗与帝国级头衔介绍都不能单独证明董卓已当天子。

## 实拍后已分析的时代消息、地方选择与交互

| 事件／交互 | 已读效果与拍摄边界 | 来源 |
| --- | --- | --- |
| `hd_dc_era.0001`“诏令未至之地” | dynastic_cycle处于chaos或hd_standoff时给玩家全屏通知；唯一项仅tooltip，无主权或领土变更。 | 主包`events/hd_dc_era_events.txt:3` |
| `hd_court.0001`“天子蒙尘” | 权臣接管后传播的通知；只要求new_regent与emperor scope存在，唯一确认项无效果，不会再次夺权。 | 议和覆盖`events/hd_court_events.txt:7` |
| `hd_world_news.0005`“关东举兵” | 唯一news项无效果。消息与当前战争成立须分别读回，点击不再宣战，也不证明战争结束。 | 主包`events/zz_hd_world_news_events.txt:94` |
| `hd_hanfl.4201`“坏五铢” | 通知本体只显示史料tooltip。上游首次满足迁都完成、董卓存活及日期条件时，已经给京兆、扶风、冯翊全部法理县加5年税收-15%、发展增长-10%，随后广播；不是玩家按确认才作出铸钱选择。 | 主包`events/zz_hd_hanfl_timeline_events.txt:565`；`common/scripted_effects/zz_hd_hanfl_effects.txt:602`；`common/modifiers/zz_hd_hanfl_modifiers.txt:27` |
| `hd_hanfl.2004`“争水” | 京兆／冯翊首都且未见过时触发。A“立石定规，均水于民。”给首都县5年每月控制力+0.5、民众好感+5；B“豪右多力，从其所请。”加minor_gold_value，首都县5年民众好感-10。 | 主包`events/zz_hd_hanfl_regional_events.txt:88`；`common/modifiers/zz_hd_hanfl_modifiers.txt:76` |
| `WJ_ai_routes.0003`请举茂才 | ACCEPT显示与执行均校验资格；成功给actor候选人名士／茂才资格（最高功绩等级+3等）、给recipient举荐者一年名额冷却。玩家recipient成功后才收酬答：offer1为actor付300金，offer2为recipient获对actor的favor_hook。DECLINE不授资格、不收费；两项after按serial/requester清pending。 | 主包`events/WJ_ai_routes_events.txt:69`；`common/scripted_effects/WJ_ai_routes_effects.txt:13`、`:79`；`WJ_office_roads_effects.txt:229` |
| `demand_courtier_interaction` | 接受迁走secondary_actor及同宫廷配偶、未成年子女。一般分支中被索取者对recipient意见-10、actor对recipient+20、recipient对actor-15，勾hook则使用hook；吏部尚书同realm分支免通常意见惩罚。拒绝不迁人，actor对recipient-15。发送给被索取者5天防重复标记，对recipient冷却3年。 | 主包`common/character_interactions/zz_dm_obedience_tributary_interactions.txt:5`；另有`00_tributary_interactions.txt:3400`同key定义，两份来源均保留，不以日志无告警证明运行绑定 |
| `grant_vassal_interaction` | 玩家收件人须回复，AI才auto_accept。接受将secondary_actor改为recipient直属附庸并增加recipient对actor意见；actor原为recipient附庸时，另与被转出者设3650天双向停战。拒绝不change_liege，向actor发0211来信；clan另有unity增减，nomad另有法理分支。 | 议和覆盖`common/character_interactions/00_vassal_interactions.txt:3` |

普通待回复交互要保留双方、secondary_actor、显示按钮和后态；回复ACK与旧窗口消失分别记录。本次4条原生拒绝记录不意味着已收到人才或附庸。实际动员、战斗保存与退出接口的适用范围另见[技术记录](filming-01/README.md#动员与原生接口边界)。
