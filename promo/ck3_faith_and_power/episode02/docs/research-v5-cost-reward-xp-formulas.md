# 朝圣费用、虔诚与朝圣者经验：1.20.0.4 可复算公式

**后继原生补注（2026-10-22）：** [a02等级与初始化链](research-v5-native-tier-12004.a02.md)在本稿封包后闭合了源码等级块无预差分累计、直接新轨道初始0及重复授予不重置。下文和公式JSON中这几项“未闭”属于封稿时状态，当前结论沿该后继来源更新；缺`limit`默认语义、主管GUI绑定等其他边界保持。增益／截断／封顶仍使用已绑定的a01，不重跑或改写原DELIVERY。

这份研究把**活动规划费、途中另付费用、活动表现分、可花虔诚、奉献经验、朝圣者特质经验**分开计算。前三类活动收费不是同一基数乘同一折扣；朝圣者经验也不能从主虔诚奖励倒推。

`machine_id: 4-8e1c2f1861`；实际源读取始于 **2026-10-21T19:38:48Z**。研究根为当前安装 `C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game`；使用 1.20.0.4／EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518` 版本上下文。本文脚本采集子任务没有重新 hash EXE、启动游戏、调用 Native 或取得新的业务实测；XP 写入边界另引用本轮独立静态专题，不把它叫作游戏实测。每份实际文件的完整 SHA、字节数、行号与最终读回时间在 [结构化公式](knowledge/pilgrimage-v5-cost-reward-xp-formulas-12004.json)。本文的数值例全部是**条件建模**，不是 R22／R31 净变化。

源码中的 PAM／By God Alone 标识本身不证明本机改写。来源沿用[既有同版本来源核查](../../source-provenance-review-2026-10-17.md)，本机读回另记，不继承外机安装事实；也不把第三方镜像当官方全目录完整性认证。

## 1. 符号与钱的输入值

以下 `I` 为当前角色 `monthly_character_income`，不是当前金币余额；`t` 为 `primary_title.tier`，`T=max(t−1,1)`。`E` 是活动时代缩放：部落时代 0.75、早期中世纪 1、高中世纪 1.5、晚期中世纪 3；没有 culture 时这个活动值保持 0。金钱动态上限使用同样的四档倍数，但无 culture 时保留上限原值，即 `E_gold=1`，不能把两个无文化分支混用。[S03:1493–1535；S04:49–114]

定义 `q=0.25` 当且仅当 `has_treasury=yes`、角色不是 `top_liege` 且 `is_landed=yes`，否则 `q=1`；`ceil5(x)=5×ceil(x/5)`。则：

```text
G_minor = ceil5(min(max(3×I×q, 15), 150×E_gold))
G_medium = ceil5(min(max(6×I×q, 50), 300×E_gold))
```

先乘收入，再下限、上限，最后向上整到 5 的倍数；因此最终上限是 `ceil5(原上限)`，例如部落时代 minor 的 112.5 经整 5 可到 115。`00_basic_values.txt` 顶部注释里的 `minor_gold_value=30`、`medium_gold_value=100` **不是当前实际定义**；真正定义在 `01_dynamic_values.txt:53–110`，收入倍数在基础值 451–456。`G_minor` 因而不是固定 30；活动本体的最低收费随它改变。[S04；S05]

## 2. 朝圣规划费用：逐层相加，不能全价一起打折

对选定目的地和选项，脚本可展开部分为：

```text
C_activity_script = C_body + C_pomp + C_destination
C_known_planning  = C_activity_script + Σ(已选旅行选项收费)
```

旅行主管聘用、特殊资源补给等还由独立旅行规划入口报价；途中事件再单独记账。不能把 `C_known_planning` 冒充任何人物在任何路线的最终实际总支出。活动格式定义明确区分本体 `cost`、选项 `cost`、阶段 `cost` 与仅供概览的 `ui_predicted_cost`。[S13:190–197、392–402、517–539]

### 2.1 本体基础费 B

```text
B0 = 30 × max(t−1,1)
B1 = B0 × (部落政体 ? 0.5 : 1)
B2 = B1 + (主头衔高于公爵 ? 50 : 0)
B  = B2 × (AI且hard ? 0.5 : AI且very_hard ? 0.25 : 1)
```

注意部落减半发生在王／帝额外 +50 **之前**。时代缩放随后在朝圣本体函数中使用。无部落／AI折扣时，按标准头衔 tier：伯爵 30、公爵 60、国王 140、皇帝 170；无地人物仍按其实际 `primary_title`／脚本上下文计算，不能只按显示名猜 tier。[S03:772–810]

### 2.2 本体收费 C_body 的完整顺序

从 `x=B×E` 开始，严格按下表更新；不满足条件就跳过该步。源码为 `50_pilgrimage_values.txt:286–481`，调用者为活动 `cost:865–900`。[S01；S02]

| 顺序 | 条件／来源 | 更新 |
|---|---|---|
| 1 | `hunt_urge_for_pilgrim_badges_modifier` | `x -= G_medium` |
| 2 | `ghost_pilgrimage_promised_modifier` | `x -= G_medium` |
| 3 | `hajj_promised_modifier` | `x -= G_medium` |
| 4 | `pilgrimage_promised_modifier` | `x -= G_medium` |
| 5 | 家族 `ep2_activities_legacy_1` | `x -= 0.5×B`，减的是未乘时代的 B，不是整价五折 |
| 6 | imaginary-friend 旗标且故事目的地等于当前 `scope:province` | `x *= 0.5` |
| 7 | `court_event_discount_pilgrimage` | `x *= 0.75` |
| 8 | `pam_sf_pilgrimage_funded_modifier` | `x *= 0.5` |
| 9 | spiritual fulfillment cheaper 参数 | major：`×0.5`；普通：`×0.75`；major 优先，不两次叠乘 |
| 10 | house aspiration `humility_pilgrimage_discount` | `x *= 0.75` |
| 11 | realm law `cheaper_pilgrimages` | `x *= 0.75` |
| 12 | domicile 参数 `estate_cheaper_pilgrimage_cost` | **此时** `x -= 0.2×B×E`；减原时代基数的 20%，不是现值八折 |
| 13 | rite 参数 `local_shrine_offering` | `x *= 1.75` |
| 14 | 无地冒险者或游牧政体，且 `clerical_justifications_perk` | `x *= 0.5` |
| 15 | confederation `any_member_activity_cost_reduced` | `x *= 0.9` |
| 16 | `tgp_reflection_modifier` | `x *= 0.8` |
| 17 | `tgp_ceremonial_liege_events_0020_discount=flag:pilgrimage` | `x *= 0.85` |
| 18 | `mandala_godking` 变量且为 AI | `x *= 0.25` |
| 19 | 最低值 | `x=max(x,G_minor)`；无整价最大值、无本体最后整 5 操作 |
| 20 | 持有 `e_minister_of_revenue` | caller 再 `×0.85`，故最终甚至可以低于第 19 步的 floor |

前四项是独立 `if`，源码没有互斥；真实角色能否同时具有它们要读状态。所有这些都只在其消费函数明确覆盖的费用层生效。备注中的“halves every cost”不是一个额外的总价全局乘法。[家族系数 S07:93；estate S10:2304；fulfillment S09:2160–2172]

付款资源：**神权政体且有 treasury**，上述朝圣本体、排场和阶段费走 treasury，gold 分支为 0；否则走 gold，treasury 分支为 0。`e_minister_of_revenue` 的额外 0.85 本轮只在本体 caller／UI预测出现，不能擅自套到排场和距离费。[S01:865–900、1720–1783、1832–1951、2136–2368]

### 2.3 排场费与随行人数档

设 `A=T+E−1`。三个逐项加法 `b+(bT−b)+(bE−b)` 化简为 `b×A`，**不是 `b×T×E`**。[S01:1720–1783、1832–1891、1980–2039]

| 排场 | 直接选项费 | 脚本随行选择 |
|---|---|---|
| humble | `−10×A` | 本选项没有直接 `travel_entourage_selection`；后续出发事件会以 7 为补人目标 |
| appropriate | `0` | 本选项按 base weight 选最多 5 名 |
| ceremonial | `((50×A − legacy?25:0) × journey_planner?0.8:1) × funded?0.5:1` | base+extras weight，最多 10 名 |
| throng | `((100×A − legacy?50:0) × journey_planner?0.8:1) × funded?0.5:1` | base+extras+everyone weight，最多 20 名 |

表中三元条件各自带括号理解，例如 `legacy?25:0` 是“有该传承则减 25”。humble 的负费用没有 ceremonial/throng 的家族、journey planner 或 funded 乘法分支；不得为了凑统一总价折扣而补上。appropriate／ceremonial／throng 的 5／10／20 是**加人 selector 的上限，不是实际到场数，也不是每人收费系数**。活动还另有 `standard_travel_entourage_additions,max=5` 的基本选择规则；不同 selector 的实际去重／有效人选由活动创建器处理，不能把常量简单相加当承诺总人数。本体、排场、目的地三段收费中都没有 `实际人数×单价`。[S02:154–281；S01:1812–1816、1956–1964、2103–2112、2655–2658]

后续 `travel_start_event.1060` 有真实消费者：按四档目标 **7／5／10／20**，先从本地可选人物中补入，仍不足时仅玩家分支创建朝圣者；循环比较的是整个 `current_travel_plan.num_entourage_characters`，不是只数新加的人。已有数量超出目标时不裁员；事件触发、有效人选、后续损失与实际成员还须区分，不能把目标值说成到达时保证人数。[S31:2171–2304、2456–2514]

### 2.4 目的地阶段费 C_destination

`d_cost=capital_province.squared_distance(scope:province)`，先算 `G_medium×k(d_cost)`，然后**依次**乘 `E`、匹配目的地的 imaginary-friend 0.5、无地冒险者且有 clerical justifications 0.5、funded 0.5。冒险者这段只检查 `landless_adventurer_government`，不能把本体的游牧分支自动搬来。家族减项、house humility、spiritual fulfillment、estate 减项、court 0.75、local shrine 1.75、confederation 0.9 等没有在本阶段重复消费。[S01:2136–2368；S06]

| d_cost 区间（平方地图距离） | k |
|---|---:|
| `≤22500` | 0 |
| `(22500,62500]` | 0.2 |
| `(62500,422500]` | 0.4 |
| `(422500,722500]` | 0.6 |
| `(722500,1440000]` | 0.8 |
| `(1440000,2402500]` | 1 |
| `(2402500,9000000]` | 1.2 |
| `>9000000` | 1.5 |

`scope:province` 不存在时源码保留最初的 `G_medium`，不把它冒称已选路线；实际选定目的地的报价才使用表。该阶段无额外 min/max 或最后整 5；`G_medium` 自己先被收入上下限和整 5 处理。收费距离与下一节奖励距离**阈值不同，起点 scope 也不同**，都不等于实际绕路里程或旅途天数。

### 2.5 fidelity／类型、旅行选项、主管与补给

虔诚型／世俗型／Hajj 与 obligatory／标准／contemplative 本身没有另一个 gold `cost` 块。fidelity 会改奖励与速度：obligatory 给旅行 `travel_speed_mult=+0.5`，contemplative 为 `−0.5`；humble 给 `travel_safety=−25`。这些是对应 modifier 的增量，不保证最终总速度恰好变为 1.5 倍／0.5 倍，也不能倒算一项不存在的按日固定朝圣费。[S01:1563–1709、2840–2882；S23:266–279]

旅行选项的三个基础价格是 `low=2×T×W`、`medium=5×T×W`、`high=10×T×W`，`W=0.75` 若有“准备充分” `well_prepared_perk`，否则 1；`very_low=0.5×low`，当前这批付费项没有消费 very_low。前述排场的 0.8 则来自“旅行规划” `journey_planner_perk`，不是同一个折扣。最大可选数为 2。[S11:97–140；S30:NTravel.MAX_SELECTABLE_TRAVEL_OPTIONS]

| 付费旅行选项 | 档 |
|---|---|
| 三种购买装备：rough terrain／desert／forest | low，直接 gold |
| experienced captains | medium |
| experienced mercenaries | high |
| jungle expert／mountaineer／forder／desert warrior／rough terrain expert／court physician | low |
| cultural ambassador | gold／treasury 为 medium；游牧额外 herd 分支却为 low，不能按注释统一 |

上表按不同选项定义去重共有 **12 项**：3 种装备＋船长＋佣兵＋6 种 low 雇员＋文化大使；一个选项的 gold／treasury／herd 分支不重复计数。雇员规则：无 treasury 才付 gold；游牧时 gold 再 ×0.5；有 treasury 则付全额 treasury；游牧另付一份 herd，不是把 herd 当金币折扣后忽略。其 `on_applied_effect` 还可能将同一基数付给雇员，这是收款方入账，不应再从雇主重复扣一遍。无 `cost` 的其余旅行选项只可说“无直接选项费”，后续效果／事件另算。[S12]

完整旅行界面另外消费 `TravelPlanner.AccessCostBreakdown`、`Character.GetTravelLeaderCost`／`GetTravelLeaderCostBreakdown`、`TravelPlanner.GetProvisionsCost`／`GetProvisionsCostBreakdown`。[S14:178–188、751–754、800] 已找到主管对应的实际 **scripted_cost key `travel_leader`**，其脚本定义可以完全展开：[S33:662–689]

```text
若该 cost 的 root.liege 存在且不是 landless adventurer：
  L_script = max(scope:speed_aptitude / 5, 1)
           + max(scope:safety_aptitude / 5, 1)
否则 L_script = 0
round = no；只有 gold 项，无本式整 5 或最大值。
```

不能把 `root.liege` 条件自行改写为所有旅行主办者条件；两项 aptitude 是调用时传入的值，不是直接拿人物 stewardship／prowess 代替。本式已闭合，**GUI getter 最终是否消费此 key 及其 root／scope 绑定**仍没有 exact 引擎调用证据；这比把整项写成“主管价未知”更窄。若实际选定／需支付主管费，应将该次真实 `L` 加入报价，不能默填 0。

主管还存在独立的**经常月薪**，不是朝圣专属按日费，也不等于上述一次 cost：`court_position_travel_leader_salary` 从0.1起，雇主 ecclesiastical ×0.25、文化 cheaper_court_positions ×0.8、满足中国霸权与对应高薪参数 ×1.2、hard／very_hard的AI雇主 ×0；total salary 再按 Inner Circle 同家族资格免薪，否则义务牵制半薪，另可因 half-salary 变量名单 ×0.5、increase-salary 名单 ×1.5，无地冒险者雇主最终 ×0。`travel_leader_court_position.salary` 以雇主是否有 treasury 选择 treasury／gold；月薪支付次数按实际任职和月份记，不把雇员收到的 salary 再算雇主第二次扣费。[S34:1132–1194、3383–3441；S35:1003–1034；S36；S37:89；S38:137–150]

补给的 `provisions` 是资源报价，不盲改作金币；其 `GetProvisionsCost` 数值 producer 仍未在本研究闭合。这里没有把每名随行人员或每一天臆造成确定金币支出。

途中固定请求与随机支出另计：例如 6840 A/B 均请求 `min(G_medium,15)=15` gold、同 +25 基础虔诚；选择、事件是否出现、支付通道后验均另记。募捐、住宿、强盗、交通、圣物购买／赠予等未发生的事件费用不能事前当已付款；不同事件调用的 `pay_short_term_gold`、cost 或直接资源 effect 也不能自动套用同一全局折扣。完整行程支出为**实际规划付款 + 实际出现且选择的事件付款 + 其他已确认独立费用 − 实际退款／收入**，不是用平均随机费用替真实钱包差。

### 2.6 UI 预测不是确认页实际报价

`ui_predicted_cost` 对所有圣地算平均距离费、对四种排场用 `(0−10+50+100)×T×E/4` 作平均，再应用它自己的减项和乘项，最后 floor 与向上整 5；它对冒险者还用 0.25，和 actual body 的 0.5 不同，且没有完整覆盖 actual 新增分支。**不能从活动列表上“预计花费”反推本体、选定排场或实际旅费**。[S01:902–1381]

## 3. 主虔诚公式与奉献经验

这里 `d_reward` 是 `PILGRIM.capital_barony` 到目标 holy site 的 `squared_distance`；活动开始按它保存 `pilgrimage_distance` 枚举，后面消费枚举，不按沿途走过的总天数重新累加。[S15:880–944；S01:2696–2707]

| d_reward | 距离基础 R0 |
|---|---:|
| `≤100000` | 100 |
| `(100000,1000000]` | 150 |
| `(1000000,5000000]` | 250 |
| `>5000000` | 350 |

家族 `erudition_legacy_4` 在这个距离值内部 ×1.3。它与降低费用／提高 pilgrim XP 的 `ep2_activities_legacy_1` 是两项不同传承。[S02:6–59、147–149]

设 `D=1.3` 或 1；`F=0.5/1/1.25` 分别为 obligatory／标准／contemplative；`A_trait=50` 当角色确有 `should_get_trait_piety` 旗标，否则 0；`A_pomp=50` 为 humble 或 ceremonial、100 为 throng、appropriate 为 0。主脚本基数是：

```text
P_script = (R0×D×F×Q + A_trait + A_pomp) × J × H × C
```

| 项 | 条件与数值 |
|---|---|
| Q，虔诚型／Hajj 表现档 | `<25:1.1`；`[25,50):1.25`；`[50,75):1.75`；`≥75:2.5` |
| Q，世俗型 | 不生成 pious reward 旗标，故主虔诚 Q=1；仍有主虔诚，不是世俗型没有虔诚收入 |
| J | rite 参数 `tenet_inner_journey_humble_pilgrimage_bonus` 且 humble：1.5，否则 1 |
| H | 目的地县匹配本人信仰 `is_eminent=no` holy site：0.5，否则 1；不能泛化为所有非首选地点 |
| C | confederation cohesion 参数 `any_member_increased_pilgrimage_rewards`：1.1，否则 1 |

顺序是**距离、家族、fidelity、表现先乘 → 资历／排场再加 → J/H/C 再乘**。没有另一个通用“zealot_intent 倍率”或“性格倍率”直接乘本式；性格／意图可改变事件条件、选项、AI偏好，不能把权重当收益倍率。[S15:516–629、1301–1369]

活动进度不是钱包：`activity_special_type_progression` 开始设 0；到目的地短程另 +5、中程 +3；匹配已选 special_type 的普通 pious/worldly helper 每次 +10，very helper +40。不匹配不加；helper 要求变量存在，没有在这些 helper 中看到 100 clamp。结算先按进度锁角色 reward flags，再调用奖励，7000 after 清 flags。不要把活动 log 的 `score=50/100`、显示段位 0/25/50/75/100 或某次 `add_piety` 误写为 track XP。[S16:4304–4384；S15:1225–1369；S01:2416–2417、2575–2579；S22:15091–15145]

世俗表现除主虔诚外，按档给接触文化接受度 1/3/5/7，或对应五年修正；是否进入文化分支还检查自己是文化领袖、旅行计划访问文化列表等，不是给虔诚 Q 再乘一次。Hajj 用同一距离主式和 pious 表现档，但主角另走 hajjaj 的授予／重复分支。[S15:673–876、399–411]

**主式以外另发的奖励**：符合山地／丘陵相关 rite 参数和地形时再 `add_piety=100`；清贫誓愿 host 满足个人信条、活动尚未付该奖励的 guard 时另 `add_piety=150`，以活动变量防重复；这两项不能再乘主式的 F/Q/J/H/C。tenet 的十年修正、神秘主义随机奖励、spiritual fulfillment 与合法性是独立渠道。月虔诚修正影响月收入，不可直接乘进本次主式。[S15:94–213、1136–1207；S28:1475–1498；S09:2589]

最终普通正 `add_piety` 还经过引擎资源调整。已有同机 EXE9870 资格已闭合 `28BC6D0` 的正值属性 0x59、倍率 `max(0,1+m)`；该专题没有给属性硬套人类可读名称，本轮也不冒称已经枚举它的全部 producer。设经过该原生调整／固定点处理后的正增量为 `p`，旧钱包为 `w`：

```text
wallet_gain = p
devotion_xp_gain = max(0, p − max(0,−w))
```

钱包非负时两者等增；负钱包先补债，只有超额给奉献经验。普通负 `add_piety` 只扣钱包；`add_piety_and_experience` 则是另一条强制双写通道。多个独立奖励逐次到账时，要用每一步的新钱包计算，不能把特质 XP 混进来。[已有原生语义专题](../../../../docs/ck3-native-ai/holy-site-piety-experience-consumer12004.md):13、25、29。这里复用历史静态资格，不是本轮新 Native 验收。

## 4. 朝圣者特质经验：逐次写入，不是距离×天数

`pilgrim` 有一个单 track，50／100 是特质效果和显示级别阈值；`hajjaj` 没有这个 track。`lifestyle_traveler`、学习／漫游生活方式经验、奉献经验与活动 special_type 分数均为其他存储。以下是**每次 effect 请求的脚本基础 XP**；引擎增益、clamp／舍入单独处理。

### 4.1 到达／首次授予与重复：异常空分支必须按文本展开

普通到达事件调用 `give_pilgrim_trait_or_xp_effect`。无 pilgrim 时只 `add_trait=pilgrim`，不是同块再加 20；脚本没有初次授予时明确 `add_trait_xp=20`。对于已有 trait，当前安装文本的 host 外层 `else_if` **没有 limit**，内部还有一个只有 `limit(xp<100)`、没有 effect 的空 `else_if`。[S15:216–315]

按标准条件块语义逐层展开，不能按注释改写为想象中的版本：

| 调用身份／已有状态 | 实际脚本分支 |
|---|---|
| host，无 trait | 添加 trait；本分支不显式加 XP |
| host，有 trait，PAM且本信仰有 `pam_secured_pilgrim_routes`，当前 XP<100 | 请求 +30 |
| host，有 trait，未满足上一项且 XP<100 | **空分支，请求 XP=0** |
| host，有 trait，XP≥100 | 内层 else 请求 +20；不能擅自假设它会在 engine 中突破上限 |
| host 后置 learning／flag 分支 | 在“已有 trait 被无 limit 的前一 outer else_if 接走”的文本控制流下被遮蔽，不能据它承诺学习 XP 或 +50 虔诚 |
| non-host，无 trait | 添加 trait |
| non-host，有 trait，secure routes条件且 XP<100 | +20 |
| non-host，有 trait，非上述但 XP<100 | +10 |
| non-host，XP≥100 | 学习生活方式者 +300 学习生活方式 XP，否则置 `should_get_trait_piety` |

这是对精确括号、空块和先后顺序的**静态控制流推导**；表中有关“外层接走／遮蔽”的结论以缺 `limit` 默认通过的条件块语义为前提，**本轮尚未取得该默认语义的 exact 引擎闭合证据**。没有把异常源自动修好，也没有声称读取过当前游戏编译器如何处理它的既有日志。若编译器拒绝此无 limit 结构或处理方式不同，须保留该独立事实，不能继续拿预期 +20 做结论。基础调用位置由到达事件提供，不能把到达事件列表中的所有调用相加成每趟都会执行。

同一 helper 的随行分支还可对符合相关身份／信仰圣地条件的人授予 pilgrim；已具者请求 +10。Hajj 路线中的穆斯林／麦加分支另授 hajjaj；不能把全体随行都视为主角的重复逻辑。[S15:317–395、412–485]

### 4.2 结算表现额外 XP

`give_pilgrimage_reward_effect` 的四种距离分支都调用同一个 `give_pious_type_reward_effect`，因此**距离没有再把特质 XP 乘 1／1.5／2.5／3.5**。当角色已有 pilgrim 且当前 XP<100，按 pious flags 请求：low +5、mid +10、high +20、perfect +40。世俗 flag 不满足该 pious 分支，所以世俗型不是同样白得一份 pious +40。[S15:632–670、1136–1164]

Hajj 主角 `give_hajj_trait_or_xp_effect`：第一次加 hajjaj；已具者若学习生活方式则 +300 学习生活方式 XP，否则置 trait-piety flag，再进入同一主奖励 wrapper。它本身**没有**对 hajjaj 加 track XP；若一个人物另外已经有 pilgrim 且满足 pious flag／XP guard，公用 wrapper 的 pilgrim 分支仍应独立检查，不能把“是 Hajj”写成无条件 pilgrim+40。[S15:399–411]

### 4.3 事件中的固定 helper +5 与其余写入

`give_pilgrim_xp_effect` 的规则是：有 pilgrim 且 XP<100，请求 +5；否则若处于 learning lifestyle，给 +100 学习生活方式 XP；否则 zealous 分支给 medium stress loss，其他给 minor stress loss。**zealous 改的是 fallback 压力，不是乘特质 XP。** 本机 common/events 全文本只找到四处真实 caller：`pilgrimage_events.txt:2779、6922、8349、10977`；它们分别属于具体事件选项，不是活动每月、每站、每次到达都执行的基础 +5。[S15:488–513；S22]

旅途中 POI 的 3–5 随机 XP、特殊 shrine／合同／camp party 等写入，与角色意图／性格对事件权重的影响，交叉引用本轮独立[完整特质影响库存](research-v5-pilgrim-trait-inventory.md)和[逐写入点 JSON](knowledge/pilgrimage-v5-pilgrim-trait-inventory-12004.json)。不能把其“可能发生的写入”加成一趟朝圣必然总 XP。这里不重做那份全库库存，也不把学习 lifestyle 或 mystic 的 +5 当 pilgrim +5。

### 4.4 全局 gain modifier 与教义的边界

实际修正名是 `pilgrim_xp_gain_mult`，不是凭显示名推断的 `pilgrim_experience_modifier`。本次安装找到的赋值源为：

- `ep2_activities_legacy_1`（活动家族传承 **踏过圣路／Walking the Sacred Path**）角色修正 +0.5；同块另给 traveler XP +0.5，它们是两个不同属性。[S24:28–43]
- “复越高山” `just_one_more_hill_perk` 的 `government_character_modifier` +0.2，**须 government_is_theocracy**，不能给所有有该 perk 的人物套用。[S25:91–94]
- 教会住所 `pilgrim` 对应建筑四个升级定义各 +0.05；升级替换规则及合法建筑资格见库存，不是同一建筑全升级后直接把四条当 +0.20。[S26:3867、3910、3957、4004]

本轮另一个有限静态专题已对 **EXE98702f 的 exact 1.20.0.4** 闭合执行器，不再仅凭百分比显示表猜算法。`add_trait_xp` executor `0x2D29CF0` 调 `0x28BAF50` 算增量，实际读 trait 与 track **两项**修正，不读第三个通用 XP 倍率。对 pilgrim 单 track：

```text
b_raw = 本次脚本基础 XP 的原生固定点值（1 XP = 100000 raw）
x_raw = 写入前该 track 的固定点 XP

若 b>0：M_raw = 100000 + 当前 pilgrim_xp_gain_mult_raw
                         + 当前 trait_track_pilgrim_xp_gain_mult_raw
若 b<0：M_raw = 100000 + 当前 pilgrim_xp_loss_mult_raw
                         + 当前 trait_track_pilgrim_xp_loss_mult_raw

delta_raw = trunc_toward_zero(b_raw × M_raw / 100000)
new_xp_raw = clamp(x_raw + delta_raw, 0, 10000000)
new_xp = new_xp_raw / 100000
```

该写入要求人物已持有对应 trait；`add_trait_xp` 不替代 `add_trait`。**零基础直接返回，不写 XP**，上面的写入式用于非零基础。正／负值选择 gain／loss，不是按最终 delta 的符号重新选；固定点的向零截断也不等同于 UI 的整数四舍五入。两项 modifier **先加到 1，再单次乘**，不是 `×(1+traitMod)×(1+trackMod)`；没有依据在前面另添一个 `max(0,M)`。最终写入 clamp 到 **0–100 XP**，然后更新等级／缓存；本次请求 +40 不保证余量不足时还能实际增加40。缺失 modifier／无效 ID 读回 0。人物当前总修正值与哪些建筑／perk真正激活，依然要按实际资格和后态区分，不能把源里所有定义都堆到一个人物上。公式适用于可表示的固定点输入；脚本值进入 raw 前的转换舍入与任意巨大整数溢出没有被这个局部式额外认证。

例如假设合法激活的 trait gain 总值 +0.5、track gain 0，基础 +40 的 delta 是60；旧80实际到100，只增加20。若两项分别+.5和+.2，基础40变68，不是72。以上均是引擎式条件算例，未读当前人物 modifier，也没有新游戏实测。精确消费者证据见 [原生 trait XP 专题](knowledge/pilgrimage-v5-native-trait-xp-12004.json)。该专题还看到已载入 modifier 对象的合并是先 root、再所有达到阈值的 track 块，同 ID 累加；但源码常量到这些运行时对象的加载预处理没有全闭，**不能据此把源里的 .35／.4／.4 直接相加宣布月虔诚净值**。首次添加 track 的初始化、该加载预处理，以及前述缺 limit 默认语义都是另外的边界。

pilgrim 的 rite 参数 `basic_pilgrimage_rewards`／`mandatory_pilgrimage` 在 trait／track 定义里消费为月虔诚、意见等修正，**不是独立的 pilgrim XP 倍率**。单 track 的 50／100 阈值不是按虔诚等级解锁。当前 pilgrim 定义也没有 `monthly_track_xp_degradation`；只有一个 degradation modifier 的显示定义，不支持宣称所有朝圣者经验按月自动衰减。[S17:8755–8894；S18:196–240；S27:2977–2980、3021]

## 5. 两组可复算算例

以下均是源码条件算例；不使用任何 R22／R31 的实际净变化作数值输入。

**例 A：一次规划收费。** 假设公爵 `t=3`、非部落、人类玩家、早期中世纪 E=1、月收入 I=10、q=1，无任意折扣，目的地收费平方距离 d=500000，appropriate，选择 low 档“雇佣登山者” mountaineer。

```text
G_minor=ceil5(clamp(30,15,150))=30
G_medium=ceil5(clamp(60,50,300))=60
B=30×(3−1)=60
C_body=max(60,30)=60
C_pomp=0
C_destination=60×0.6×1=36
mountaineer=2×2=4
已展开脚本金币合计=60+0+36+4=100
```

若另需聘任主管，完整金币还加实际报价 L；例如单独假设前述 cost 条件成立、speed／safety aptitude 为40／50，则该脚本 `L_script=8+10=18`。其 GUI 绑定仍按上一节保留证据边界。补给资源另列，途中事件另记，**不是看到 100 就承诺钱包最后只少 100**。同一人物改 ceremonial，则无折扣排场费 `50×(2+1−1)=100`；若另有活动家族传承和 journey planner，排场变 `(100−25)×0.8=60`，本体变 `max(60−30,30)=30`，距离仍 36，故这三段合计 `30+60+36=126`，而不是对原来的 196 一起打五折。

**例 B：即时同奖，结算不同。** 假设虔诚型、短程基础100、标准 fidelity，无家族收益加成、没有 trait-piety flag、ceremonial+50、普通非 eminent 圣地 ×0.5，6840 前活动分65，之后不再变动，原生 piety 调整倍率为1。

```text
6840 A 与 B：各请求金币15，各即时基础虔诚+25。
A匹配pious：65→75，P_script=(100×2.5+50)×0.5=150
B不匹配pious：仍65，P_script=(100×1.75+50)×0.5=112.5
同+25即时虔诚，结算主奖相差37.5。
```

有 pilgrim 且 XP<100 时，两条结算额外 trait XP 基础请求分别为 +40 与 +20，按上一节精确式应用 gain 和剩余空间；不能把基础请求直接叫作最终增量。若单独示意普通 `add_piety` 的补债语义，令调整后 p=150、旧钱包−100，则钱包至50、奉献经验仅+50；这不是又多给150特质经验。独立奖励与后续事件不从该简化例子外推。

## 6. 来源、可确定范围与剩余缺口

全部 S 编号、完整 SHA、准确行号和旧研究身份在配套 JSON。本文展开的是**当前实际安装内容的脚本规则与已绑定历史引擎语义**，没有新游戏资格；既有 R31 first-display fallback 也不会因这份研究被追认为当时已有专用策略。

已确定：动态金钱上下限／整 5、本体所有当前消费的折扣顺序、排场和阶段单独公式、两套距离表、fidelity／special_type 不直接加价、主虔诚所有当前算式系数、activity progress 与 trait XP 的直接消费者、重复到达异常空分支的文本控制流。

剩余精确边界：主管 GUI getter 到已展开 `travel_leader` cost 的 exact root／scope 绑定、补给的引擎数值 producer；活动创建器的最终综合报价／负选项费钳制与人数去重；trait 初次授予的 track 初始化、源码 trait modifier 的加载预处理、缺 limit 的默认语义；所有未发生事件的支出与随机写入。已闭合的 XP gain／loss 两属性加法、固定点单次乘、向零截断、0–100 clamp、运行时 modifier fold 和主管脚本 cost 不能再整体列作未知。未知项不能伪写 0，未发生事件不能事前宣称已发生。这里只给可定位接口和最小缺口，不以“不确定”抹掉已展开的脚本数值，也不越权新开 Native 逆向或游戏去补。
