# 第4期原生术语与单位：行军、补给、损耗

2026-10-04 / P0-TERM。当前已完成原版文件提取，真实 tooltip 截图待屏幕协调者采集。此报告没有 GUI 调用、SDK、游戏进程读取、输入或录像信用，不能单独把导演案 P0-TERM 标为整包完成。

当前安装根为 `C:/SteamLibrary/steamapps/common/Crusader Kings III`；Steam manifest `buildid=25652598`、`StateFlags=4`，当前 EXE SHA-256 为 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`，与已冻结 CK3 1.20.0.3 身份一致。提取时主仓 HEAD 为 `563a55c5393086d3b795e7ac8fa7e0fd488d5f01`。

107 个 key 的简中与英文原始行、行号、26 个原文件与小型提取件的 SHA-256 保存在 [terminology-evidence.json](D:/ck3-war-episode04-research-20261004-a01/terms/terminology-evidence.json) 和 [source-sha256.json](D:/ck3-war-episode04-research-20261004-a01/terms/source-sha256.json)。英文与中文行号不总相同，应按 key 对应，不按同一行号取英文。小型提取件保留未展开的原版 `$...$`、`[...]` 与格式指令；下表中文解释只协助口播，实际显示句子仍须当前实图核对。

## 口播术语与单位

| 对象 | 原版 key / 原文 | 英文 | 单位与口播用法 |
| --- | --- | --- | --- |
| 当前携带补给 | `SUPPLY_STATE_TOOLTIP`：`补给：$SUPPLY$/$FULL_SUPPLY$`；`game_concept_supplies`：补给 | Supplies / Supply | 分子是这支军队当前补给。原文未称百分比，不能把 `100/300` 读成补给 100%。说“当前补给”。 |
| 军队容量 | `MOD_SUPPLY_CAPACITY_ADD`：`[supply]容量`；`ARMY_SUPPLY_CAPACITY_INCREASED_BY_COMMANDER` 又使用“补给上限” | Supply Capacity | 分母来自 `ArmyWindow.GetFullSupplyCapacity`。说“这支军队的补给容量”，这是原版 modifier 已有用词；无需另造“携行点数”。 |
| 当地上限 | `game_concept_supply_limit` / `SUPPLY_LIMIT`：补给上限 | Supply Limit | 概念描述明确是男爵领能够容纳的士兵数量。说“当地补给上限，能支持多少名士兵”，不与军队容量比较。 |
| 月变化 | `SUPPLY_STATE_POSITIVE/NEGATIVE`：`±$CHANGE$补给/月` | Supplies/month | 是补给/月，不能读为士兵/月，也不证明下次实际增加相同数值或每月一日结算。 |
| 补给状态 | `SUPPLY_STATE_0/1/2`：补给充分／补给不足／挨饿 | Well Supplied / Undersupplied / Starving | 采用这三个原生名称。状态阈值与效果由机制包及同帧实图解释，本包不推断。 |
| 补给免消耗提示 | `SUPPLY_STATE_NO_LOSS_PERIOD`：近期集结后，在某日期之前不会使用补给；`SUPPLY_STATE_GATHERING`：集结完毕前不会使用补给 | recently raised / gathering | 原文是“不会使用补给”，不能扩大成不会发生任何损耗或伤亡。 |
| 特殊部队的补给例外 | `SUPPLY_STATE_EVENT_TROOPS_IGNORING_SUPPLY`：这支军队中的某数量士兵没有使用补给 | Soldiers … not using supply | 是提示中的实际人数。威廉1066主案须拍此提示并读取实际值后再决定是否适合展示补给压力。 |
| 月损耗 | `ARMY_ATTRITION_TT`：每月损耗：百分比（士兵图标人数/月） | Monthly Attrition | 同时展示 `%` 与名士兵/月。这是当前计算提示；本期窗口实际少了多少人仍需排除其他因素。 |
| 月损耗来源 | `ATTRITION_SIEGE/RAID/SUPPLY`：围攻／劫掠／缺乏补给 | Siege / Raiding / Lack of supplies | 完整拍原生 breakdown；围攻沿用第3期范围，不重讲进度。 |
| 行军提示的单次损失 | `UNIT_WILL_TAKE_HOSTILE_COUNTY_ATTRITION`：移动将导致某数量名伤亡 | Move will result in … casualties | 原版此提示用“伤亡”。口播说“这里提示这次移动将导致多少名伤亡”，并区分旁边的每月损耗。执行后的真实变化待单变量实验。 |
| 补员 | `MONTHLY_REINFORCEMENT_COST_LABEL`：每月补员；`TT_REINFORCING_MAA_YES_TITLE`：补员兵士；`ARMY_COMPOSITION_ENTRY_REINFORCE`：`（$REINFORCE$/月）` | Reinforcement / Reinforcing | 说“补员”或“兵员补充”，不用“增援”同时代指另一支军队到场。逐团人数补员提示为人数/月；军事页费用提示的值为费用/月。 |
| 当前兵数与满员数 | `ARMY_TOTAL_SOLDIERS`：总士兵：当前／最大；`TT_REORG_SOLDIERS`：士兵：当前，最大：最大 | Total Soldiers / Soldiers / Max | 单位名士兵。差值不能自动当成立即可集结 reserve，也不能当成当前损耗死亡数。 |
| 路段剩余时间 | `UNIT_STATE_MOVING`：移动：剩余某天数；`UNIT_WILL_ARRIVE`：抵达某地，剩余时长（日期） | Moving / … days left | 原生显示可为整日或日期；口播读当前提示，不声称其等于精确抵达 tick。 |
| 下令前 ETA | `PROVINCE_TOOLTIP_ETA`：预期抵达时间：时长后（日期） | Predicted arrival | 说“预期抵达时间”；下令、当前原生估计、实际抵达分别绑定各自帧。 |
| 停止 | `ARMY_HALT`：停止移动；`STOP_GATHERING`：停止集结 | Halt movement / Stop gathering | 两个不同按钮与效果，不能把停止集结当成取消移动。 |
| 锁定 | `game_concept_movement_lock/locked`：移动锁定 | Movement Lock / Movement Locked | 简中概念说完成“一半进度”，英文说“more than half”。正好50%的执行边界必须由 native predicate/连续帧闭合，不能仅由本地化定稿。 |
| 分兵 | `SPLIT_ARMY_IN_HALF`：平分；`SPLIT_ARMY_CUSTOM`：分出新军队 | Split in half / Split off new Army | 正式讲按钮时用“平分”或“分出新军队”。“分兵休整”可作方案描述。 |
| 调编与合军 | `SPLIT_ARMY_CUSTOM_TWO`：整编；`MERGE_ARMY`：合并军队 | Reorganize / Merge armies | 会合是到同一地点；点击“合并军队”另有真实身份与数值变化，不能把两件事混称增援。 |
| 月维护 | `MONTHLY_MAINTENANCE_LABEL`：每月维护费；`TT_MAINTENANCE_RAISED_ARMIES`：已集结军队：金币/月 | Monthly Maintenance / Raised armies | 费用与游戏净现金变化分开；军事页“最大军事维护费”是预计值，非已付总额。 |
| 营地食物概念 | `game_concept_provisions`：给养 | Provisions | 与军队“补给”是不同原生概念。本期威廉/有地统治者案例只用军队补给。 |

## 可以执行的 tooltip 拍摄入口

这里给控件和语义入口，不给固定桌面坐标。执行者取得当次原始截图、尺寸和 focus 后再按现有坐标合同定位；GUI 文件只说明预期入口，不能证明此刻窗口已经出现。

| Shot ID | 入口 | 应取得的画面与同帧记录 |
| --- | --- | --- |
| TERM-01 | 选中军队，标题区 `supplies` 的补给袋图标/`supply_text` 数值组；`window_army.gui:390`，tooltip `Army.GetSupplyStateTooltip` | 大原生面板与完整补给提示。记录角色、ArmyID、驻地、日期；拍当前/容量、月变化、状态、breakdown和将领容量说明。 |
| TERM-02 | 同面板补给组左侧损耗百分比组；`window_army.gui:376`，tooltip `ARMY_ATTRITION_TT` | `%`、人数/月和来源完整可读；零损耗帧与有损耗帧各一，且绑定当前 Army。 |
| TERM-03 | 点击一个具体地产，伯爵领窗口展开该地产，`window_county_view.gui:1562` 的“补给上限”数值；tooltip `HoldingView.GetSupplyLimitTooltip` | 当地上限与原生 breakdown；保留地名与当前玩家身份。也可由地产地图 tooltip `HOLDING_TT_SUPPLY` 展开同概念。 |
| TERM-04 | 军队补给提示中的蓝色“补给”；当地上限提示中的蓝色“补给上限” | 两份当前原生概念 tooltip，显示携带补给与当地士兵容量的区别。 |
| TERM-05 | 军队已移动时，`window_army.gui:1077` 的 `status_text`；tooltip `Army.GetMovementInfoForTooltip` | 抵达地、剩余时长和日期；完整地图路线。地图军队 tooltip 的 `involved_army_movement` 也调用同getter。 |
| TERM-06 | 军队已选中，下令前 hover 候选目的地地图；原生 `PROVINCE_TOOLTIP_ETA` 与 `PROVINCE_TOOLTIP_CLICK_TO_GO` | “预期抵达时间”“右键点击向此处进军”；若有敌对伯爵领伤亡或登船费警告，完整保留。 |
| TERM-07 | 移动状态文本旁 `halt_button`，`window_army.gui:1118`；tooltip `ARMY_HALT` | 按钮“停止移动”提示、当前路段未锁定/已锁定分别取帧。动作前后及实际路段结果另由 P0-MOVE 连续录像闭合。 |
| TERM-08 | 已锁定军队地图 tooltip，`cooltip.gui:2717` 的 `involved_army_movement_lock`；锁图标与 `ARMY_TOOLTIP_IS_MOVEMENT_LOCKED` | “移动锁定”及其概念提示；留好原生路径进度同帧 native 值。 |
| TERM-09 | 军事页 `window_military.gui:483` 的“每月补员”勾选框，hover `MilitaryView.GetMilitaryReinforcementCostTooltip`；军队兵种项目 `window_army.gui:945` 的 `troops` | 先拍“补员兵士”/费用提示，再拍具体军团当前/最大人数及可出现的每月人数提示。若当前 troops getter未显示补员人数，记录实际呈现，不能补画未出现字段。 |
| TERM-10 | 军队页 `split_in_half_button`，tooltip `ArmyWindow.BuildSplitHalfTooltip`；`unit_custom_split_button`，tooltip `BuildSplitCustomTooltip`；多选军队的 MergeSelected 按钮 | “平分”“分出新军队”“整编”“合并军队”的当前中文、可用/不可用原因。动态操作由 P0-SPLIT 保存前后Army及兵团身份。 |
| TERM-11 | 军事页“每月维护费”及其 breakdown；选中地图目的地存在登船时的“会支付登船费” | 当前费用提示与原版金币图标，使用费用包同帧 native 读数。不能用1.19登船quote当1.20当前数值。 |

`Army.GetSupplyStateTooltip`、`Army.GetMovementInfoForTooltip`、`MilitaryView.GetMilitaryReinforcementCostTooltip` 都是动态原生 getter。本包只证实 stock GUI 绑定和文字模板存在，没有执行这些 getter，不能凭 key 存在声称完整提示已采。

## 必须保留的边界与下一步

1. P0-TERM文件部分已完成；11个镜头需求均为待拍，截图列表空。取得当前实图后补上截图路径、SHA、人物/Army/日期与审图结果，才闭合本包。
2. 当前容量 modifier 使用“补给容量”，将领说明又使用“补给上限”。口播统一“军队的补给容量”与“当地补给上限”；逐字引用 tooltip 时保留原文。
3. 损耗概念将逃亡、疾病和饥饿也列作人数流失来源，不能把所有损耗称为死亡。地图单次移动警告原文“伤亡”单独解释。
4. 锁定阈值的中英文区别交给移动包；本包不裁决正好50%时何时锁定。
5. 补员名词已核对；完整军团record与实际人数转移仍由 P0-REFILL闭合。DLC冒险者“手动补员”概念描述也已保全，不能套用到威廉有地案例。
6. 当前威廉主案是否包含大量免补给特殊部队由主案包核查；若其 tooltip 有该行，应明确显示实际人数，避免设计无补给压力的对照。

`open_kaishek`判定为 `not-applicable`：本工作只提取当前localization文字和GUI原生getter绑定，没有执行script/finite runtime/replay或游戏动作语义，native tooltip最终渲染亦非该离线预验能够替代。未重跑旧游戏/bridge验证。

## 日报与周报可录入字段

- 工作包：P0-TERM / exact1.20.0.3术语文件研究；107个双语key、26个原文件与小提取件SHA。
- 状态：`source-verified, live-tooltip-pending`；当前实图0、SDK0、游戏输入0、录制0。
- 新发现：补给容量可复用原版modifier用词；同名补给上限需要限定主体；停止移动/停止集结不同；月补员费用不等于月兵数；锁定概念中英阈值措辞不同。
- 下一门槛：屏幕协调者按TERM-01至TERM-11采当前实图，绑定主案Army/驻地/日期；移动包闭合阈值，主案包核查特殊部队补给例外。
- 富化归属：术语与GUI定位是通用CK3知识，可入主仓原生专题；主案具体实图与回放属于本期冻结媒体证据。无第三方mod源码或素材。


## 2026-10-05 R0165：四项当前术语已有原图及原片单帧

这是对上文文件研究阶段“11项待拍”的追加更新。当前 exact1.20.0.3、William33388、episode `native-33388-c6f1ef2b4089`，运行 source `fea65ebb763da5b2ddf7acd4897cd80a7a7a0f59`/a06。证据及原始 key/GUI 定位继续见[本期R0165索引](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0165-index.json)，旧107key材料不重写。

| 项目 | Root直接审阅的实际原始PNG | 已直接审阅的原片单帧 |
| --- | --- | --- |
| TERM-01 补给 | Sea16777220，Jan26、1086人；补给300/300，补给充分，当地1086/4960，+15补给/月；友方+20、冬季−5、将领−12%。容量与当地容纳人数保持不同单位 | PTS107.167s，完整补给提示，包括容量加成说明；不把将领−12%误作容量加成 |
| TERM-02 每月损耗 | Sea零值0%（0/月）与Army0非零1%（−56/月）、围攻+1%；非零端独立Army窗口effective_visible=true/current_subject_id=0/owner33388，pausedFeb1 | PTS195.3s零值、1617.767s非零值；当前提示不是该月实际已损失56人的因果验收 |
| TERM-05 当前移动 | Sea1087人、pausedFeb1，当前抵达Argentan剩3天（1067Feb4） | PTS1705.6s；这是当前移动估计，实际抵达仍另读 |
| TERM-07 停止移动 | Sea的“停止移动”及H快捷键当前提示；本次没有执行停止或键盘动作 | PTS1744.767s；停止前后、锁定两侧连续结果仍属P0-MOVE独立门槛 |

因此当前术语PNG覆盖为4/11（约36%，固定镜头清单计数），不等于本期研究或制作的加权完成率。TERM-03/04/06/08/09/10/11仍欠完整镜头；TERM-10只取得“平分”及移动锁定无法平分的实际警告，合并/整编部分未拍。这个警告不完成独立TERM-08“移动锁定”概念提示，也没有执行分军。

自然PNG由Root `reviews.json` SHA71ca7ccca56f6b88afe3b2c71a91510876f60de80e751367b4f920e75015f6a8及新增七图`addendum-a02.json` SHA6c8d09fb06997bf7d5c86d9230d4959675d30153bc2738cd70671c0728667fed绑定；这些PNG的raw_video_timecode_binding继续null。五个decoded中心由独立`encoded-centers-a03.json` SHA6460e3de60c7e3c76f1c4a943f90de1ba9e6b5f98ae4429014a2b53782230efc绑定实际encodedPTS/timebase/rawSHA，只授这五帧。平分PNG的monotonic搜索区间1875.9283351–1876.429109s超出实际raw末PTS1799.967s，编码绑定为null，不能挪到尾帧。

两次typed Supply/Attrition文本缓存读回仍真实拒绝：`tooltip_hover_source_top_unlocked_join_failed;capacity=1;count=1;hover=different;top_source=bound;top_locked=1`。自然提示像素和Army窗口身份成功不追认typed cache刷新。完整原片媒体PASS、五个单帧直接审图均不自动生成连续clean spans、完整1×影片审阅或签核；这些值保持false。


## 2026-10-05 R0168：十二原片单帧与严格术语门槛追加

[R0168 术语索引](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0168-terms/index.json)将 Root 明确授予的十二个 decoded PNG 内容绑定到实际 PTS/PNG SHA 和当前 stock key/GUI；旧三十候选 pending 报告保留。TERM-03 的 Holding 上限3680与基础2000/发展1200/沿海+25%/森林−10% breakdown、TERM-06 的 Brest 下令前52天/3月4日 ETA及登船费警告、TERM-11 的月维护与同日暂停费用读数满足原门槛。整项新增03/06/11，累计01/02/03/05/06/07/11共7/11（约64%，固定镜头清单计数）。

TERM-04 已有当地上限概念 child，携带补给概念 child仍缺；TERM-09已有野驴炮3×20/20与Sea射石机9/10，军事页补员勾选框/费用提示仍缺。TERM-08的锁标与“一半进度”概念已可读，但原门槛要求同帧native进度：day4 hover raw53147256/public14/native13的snapshot无Strength行，不能复用Jan11进度，因此整项仍pending。其HUD是Jan15，Jan20是正文ETA、剩5天。TERM-10有既有平分拒绝图和本轮分出新军队tooltip，完整平分/整编/可用合并提示仍pending；实际numeric merge不代按钮文字。

Root十二单帧只授这些PNG，未授全部三十候选、连续clean spans、完整1×观看或signoff。3524.9s/3574.9s的postmerge6746、116/300、将领portrait/Jan20可用于界面说明，合军写回另依独立索引；海上额外维护和“会支付登船费”不证明实际已付款。军费已含于本轮true NET，不能再扣。正式研究加权比例与分母仍null。
