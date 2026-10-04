# CK3 1.20.0.3：已集结围城部队补员与再动员的原生输入树

2026-10-03 file-only 研究。当前安装原版为 `Z:/SteamLibrary/steamapps/common/Crusader Kings III/game`，CK3 1.20.0.3 / Steam25652598；exact EXE SHA-256 `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6` 已由本包只读文件核对。源码首次读取 HEAD5cbc0ee17f3d6cd2065c1a482607ef6975eef447，后续读取为3cf7f7475c0474f12a08c28fb17b45a990cda2c6；Root同时发布，消费文件分别冻结SHA，不把移动HEAD说成单一未变源码快照。

分派的当前实机基线为 Robert29829 / episode `native-29829-2bc2d599f7f9`，CUnit83886367 → CArmy50331794 在2604围城，2290人，原生ETA109，三场主防御战争。Root随后提供fresh h5030/date53238336 strength：current/max2290/2461、40CArmyRegiments、supply100、base power7482900000Q100000。已集结缺额171不是未集结reserve。本包未查询进程、SDK、pipe、窗口或存档，这些数值属于协调者提供的实际文件基线；没有新增游戏日或收益。

本包所有 `stock-lane/`、`abi-lane/` 和JSON相对证据名均相对外置artifact根 `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/army-reinforcement-raise/native-replenishment/`，不是仓库专题的相对路径。

## 当前能得出的结论

原版AI允许在已经拥有军队时再尝试集结levy。`RAISE_LEVIES_COOLDOWN=180` 是 AI 重试时间参数，`RAISE_ADDITIONAL_TROOPS_RATIO=0.1` 在 AI 已决定需要更多军队之后控制 reserve 累积；它们不是玩家 CRaiseTroopsCommand 的全局禁令。无已集结部队时才适用初次集结门：待集结数量达到自己最大兵力0.3，或敌军兵力0.5。完整硬编码 need-more判定、tick起点、精确重试顺序尚未闭合。

当前bridge能读取已集结CArmyRegiment current/maximum，因此能观察缺员；这不能给出未集结reserve、可补员性或未来补员数。现有 `battle_reinforcement` 查询观察战场coordinator分配与join，并非兵团招募补员。不能把已有军队的 `maximum-current` 当作能立即新集结的士兵数。

当前MCP默认集结公告还要求无可控军队，是我方公开step投影条件。因为Robert已有83886367，不能通过解散当前围城军来满足这一条件，再把它声称为原版AI再动员策略。补集结的施工入口是原生未集结reserve/当前CanRaise查询与已有CRaiseTroopsCommand最终validator，保留当前围城ArmyID。

## 原生AI再集结输入树

精确原版来源 `common/defines/ai/00_ai.txt:508–538,1548–1576`。

```mermaid
flowchart TD
    A["active military evaluation"] -. "unknown: .3 scheduler/tick and need-more predicate" .-> B{"已有已集结部队？"}
    B -->|否| C{"待集结/自己max≥0.3 OR 待集结/敌军≥0.5"}
    C -->|是| R["safe-county selector inputs"]
    C -->|否| W["不满足该初次集结输入门"]
    B -->|是| D["AI levy retry cooldown180日"]
    D -. "unknown: timer起算/重试次序" .-> E{"原生AI已决定need-more？"}
    E -->|是| F["累积待集结/possible troops≥0.1"]
    F --> R
    R --> S["双方safe-raise搜索1 county；距wargoal最近5个safe counties"]
    S -. "unknown: .3候选评分/tie-break" .-> T["chosen rally county / native raise command"]
    T --> U["实际新CUnit与gathering后态回读"]
    classDef unknown stroke-dasharray: 6 4,fill:#fff4e5,stroke:#b36b00;
    class A,E,T unknown;
```

原文包含拼写 `rasied`，语义仍明确为already raised后need-more。行政军队另有 `CHECK_ADMIN_ARMIES_COOLDOWN=360`（514–518）；不能把它外推为普通Robert的征召兵冷却。

## 裁撤兵士团与解散已集结军队必须分别研究

原版 `common/script_values/00_ai_values.txt:1779–1795` 明确规定 gold MAA维护费超过 `ai_men_at_arms_expense_gold_max` 后AI会裁撤MAA，默认比例0.6；1796以后的时代、头衔、指令、政府分支动态调整，因此0.6不是当前Robert最终阈值。其它prestige/herd/treasury/barter分支独立求值。

`common/defines/ai/00_ai.txt:683–689` 的 `REGIMENT_OBSOLETION_SCORE_DIFFERENCE=20` 只有在旧兵团比最好可招募兵团低该分差，并且因成本或上限无法再招募时，才描述其裁撤输入。624–665同时给出toughness10、attack10、pursuit3、screen1、siege1000、同类subregiment减20和角色/兵种稳定随机0..20%评分扰动。这是投资/永久裁撤MAA，不是临时解散正在围城的Army83886367。

```mermaid
flowchart TD
    M["MAA经济/质量评价"] --> B{"费用超过动态resource-specific max band？"}
    B -->|是| D["stock描述：裁撤MAA"]
    M --> O{"stock分差阈值20 AND 无法因cost/cap新增？"}
    O -->|是| D
    R["raised army in siege"] -. "unknown: .3 native AI disband/recover/re-raise decision" .-> U["不得用MAA永久裁撤树替代"]
    R --> V["既有玩家disband最终validator：当前命令合法性"]
    V -. "不是AI是否应解散的utility/tick" .-> U
    classDef unknown stroke-dasharray: 6 4,fill:#fff4e5,stroke:#b36b00;
    class U unknown;
```

已有当前bridge `ck3_12002_military.cpp:127,453–481` 绑定 disband最终validator RVA0x296A620，完整CUnit generation/controllable核对后构造原生命令；`.3` adapter使用精确SHA和已冻结迁移bundle。这仅说明玩家typed命令合法性路径存在，不证明Robert现在可以解散、不证明原生AI会解散，也不改变当前围城策略。

## exact .3 二进制名称锚点

本包 `exact-ai-raise-name-xrefs.json` 保留EXE SHA、字符串RVA、rip-relative LEA xref、64字节原文与SHA。名称锚点：RAISE_LEVIES_COOLDOWN0x45AE030、MIN_RATIO_SELF0x45ADFF0、MIN_RATIO_ENEMY0x45AE010、ADDITIONAL_RATIO0x45ADFA8、DEFENDER_SAFE_DISTANCE0x45AF270、ATTACKER_SAFE_DISTANCE0x45AF298、NUM_SAFE_COUNTIES0x45AF220。

这些 xrefs 目前只定位名称注册/元数据访问，**不能当作AI实际tick调用链**。本包不把1.19.0.6的旧RVA移植到1.20.0.3，也不重跑已GREEN的battlecoordinator bind5D20550。

## 补员观测与施工入口

### 当前stock已确认的补员条件与域

| 原生输入 | exact stock证据 | 结论边界 |
|---|---|---|
| levy基础月补员0.03、MAA基础月补员0.1 | `common/defines/00_defines.txt:636–637` | 原文明确unraised chunks，不能说当前围城军每月自动补3%/10%。 |
| MAA补员开关/费用 | `gui/window_military.gui:485–493` | IsMilitaryReinforcementsEnabled与GetMilitaryReinforcementCostTooltip是独立查询入口；非conditional_maa_refill政府才显示该checkbox。 |
| understrength "Reinforcing" 标签 | `gui/window_menatarms.gui:318–324` | 只判未满员且非conditional_maa_refill，没有检查开关、付款或地域，不能充当最终可补员性。 |
| MAA金币负债停止补员 | `localization/english/game_concepts_l_english.yml:1523` | stock规则已确认，当前Robert实际gold/debt另读。 |
| levy负债修正 | `common/modifiers/00_basic_modifiers.txt:378–391` | debt0/1分别−0.1/−0.2；不是MAA停止补员的同一布尔条件。 |
| 围城中补员率0 | `localization/english/game_concepts_l_english.yml:679–681` | 语境限定holding garrison，不能外推为正在围城的field army不补员。 |
| 友好领地补员修正 | `common/lifestyle_perks/00_martial_2_authority_tree_perks.txt:127–140` | Prepared Conscription给非landless-adventurer友好地域levy补员修正1；不能推断Robert拥有perk或当前2604实际友好。 |
| supply恢复 | `localization/english/game_concepts_l_english.yml:1171,1176` | 低于当地limit且处友好地域恢复供给；不是兵团补员条件，敌占与合法holder须分开。 |
| levy gather移动速率 | `common/defines/00_defines.txt:583` | 未集结levy gather40distance/day，新增reserve不等于立即抵达当前军。 |
| stand-down返乡延迟 | `localization/english/gui/rally_point_window_l_english.yml:20–21` | 近期解散兵返乡会延缓再集结，未闭合固定公式。 |

完整17文件pins和剩余例外保存在 `stock-lane/ROOT-DELIVERY.json`；原文取证在 `stock-lane/EVIDENCE.md`。

```mermaid
flowchart TD
    R["Regiment current/max/type/IsRaised"] --> U{"原生unraised chunk？"}
    U -->|是| B["stock基础levy0.03 / MAA0.10月率"]
    B --> M["原生modifier、payment、government条件"]
    R --> T["MAA补员toggle；当前资源debt"]
    T --> M
    M --> C["exact .3 262C700 native权限 / 262CAD0 fraction"]
    R --> P["独立2657F10 chunk predicate；不人工AND"]
    C --> O["同paused帧分别发布bool与signed fraction"]
    P --> O
    O -. "actual raised transfer/未来净人数与tick因果待实读" .-> N["日/月后独立逐团数量回读"]
    G["holding garrison siege rate0"] --> S["独立garrison系统"]
    SP["supply恢复/attrition"] --> A["独立field-army供给系统"]
    classDef unknown stroke-dasharray: 6 4,fill:#fff4e5,stroke:#b36b00;
    class N unknown;
```

### exact .3 getter施工字段（静态闭合，不是实机值）

`abi-lane/military-reinforcement-tooltip.json` 冻结原生tooltip0x12FF1B0..0x12FF883，SHA `0a2b5abe963c869cbbd337752f24d01ce0de46e5fb131b5b462d858defa4083a`。该路径从MilitaryView+0x218 FullCharacterID正常解析CCharacter，再读+0x1C0军事组件byte+0x4A9；0x12FF237–260选择TT_REINFORCING_MAA_YES/NOT，0x12FF78C–7A1选择CLICK_STOP/START。因此MAA自动补员开关可以从当前角色军事组件直接只读，不依赖实际MilitaryView对象。开关不是全套CanReplenish；missing component不能当作实际false。

| getter/对象 | 已闭合静态语义 | 施工注意 |
|---|---|---|
| CRegiment，magic0x52656769 | 七个0x24-byte chunk从+0x18开始、total maximum+0x128 | 原版GUI Regiment receiver，独立于field army regiment。 |
| CArmyRegiment，magic0x41725267 | 现有strength current/max+0x38/+0x3C | 不是新补员getter的CRegiment receiver，禁止直接共用指针。 |
| 0x262CAD0(CRegiment* RCX,int64_t* RDX)→RAX=out | signed *out monthly fraction Q100000 | 完整分支bytes由abi-lane冻结；不拿基础0.03/0.1替代当前原生结果，不说它是army净补人数/月。 |
| 0x262BC90(CRegiment* RCX)→EAX int32 | 满员时间路径使用上述monthly fraction，单位月；fraction0时native时间也0 | 不能把零时间说成已经满员或保证即刻满员；实际逐月人数另验。 |
| bool0x262C700(CRegiment* RCX,Chunk* RDX)→AL | 补员许可读取toggle、government/resources/army状态；部分native分支调用bool0x2657F10(Chunk* RCX)→AL | type+0x118对象!=ObDG分支0x262C763直接true；**不能手工与2657F10做AND**。分别发布两个原生bool与fraction，保留native分支语义。 |
| bool0x2657F10(Chunk* RCX)→AL | 该独立chunk predicate按current<max、province、army flags/retreat/native0x24ACAC0判定 | 不是262C700所有分支必经门；两项bool不合成一个伪native最终许可。 |
| persistent CRegiment storage | exact .3 slot0x5D1EB68，fallback0x5D1EB58 | 不复用field ArmyRegiment storage0x5D1F340；fullID+0x10/generation roundtrip分别验证。 |
| CArmyRegiment→CRegiment | native0xD14960中0xD14A7C先由5D1F340解析actualArRg；若+0x2C count非零，D14AE8读RAX=[RCX+0x20]，D14AEC取R9D=[RAX+8] persistentFullID | +0x20指首DATA RECORD，**不是pointer array**。record stride/layout未闭合，不遍历猜stride；首record对应persistent七chunks，再按chunk+0x10 actualArRg回链核对。 |
| Chunk字段 | max+0/current+4/persistentFullID+8/actualArRgFullID+0x10/unraised-count排除byte+0x14/state+0x18 | 两种FullID不可互换；许可与未集结count使用的原生条件分别处理。 |
| int32 0x262B860(CRegiment* RCX)→EAX | native unraised count，GUI scalar wrapper0x262D2E0调用；基于七chunks扣除blocked/assigned/dead容量，clamp≥0 | 资格为byte+0x14==0、actualArRgID+0x10==-1、current+4>0，非max-current军缺额。所有levy/MAA owner roster闭合另见reserve-lane，不能用MAA-only冒充allreserve。 |

0x262B860..0x262B8F4 exact函数148字节 SHA `6111e34ed91cbd7eecc5bc53209d3c5d2a23238a2c0ae074ca15ae1a2903a293`，原文在 `stock-lane/reserve-lane/regiment-count-functions.json`。它以persistent+0x128起始总maximum，七chunks中未符合native资格的项扣max，符合项扣max-current，最终返回非负可用活兵；不把未来可能补员计入当下可集结兵。

0x262CF40与0x262BC90已核清同一persistent receiver的+0x128确为maximum；0x262C700中title lookup结果对象的同+0x128是owner CharacterID。相同数字offset跨对象没有统一语义。

**现已封闭10个原生函数：** `abi-lane/ROOT-DELIVERY.json`、`abi-lane/native-abi.json`（SHA `8b2848041af660d158ccea8fe51119d355d2f3a5785df9e3235357eb0c1f4fad`）、`abi-lane/EVIDENCE.md`（SHA `a7b20401150a89e8db2dfb03f9dfba2f0a26f3a02fb66638206d102e7c6b0715`）给出每个完整函数的ABI、bytes/SHA、pDATA或明确leaf ret边界；source3cf7f74到封包0fd88714间消费源码文件逐字节不变。当前仅为研究与静态ABI闭合，未新增字段fixture或live验收。

实际MAA GUI caller0xD15F96–0xD15FB6和levy caller0xD16288–0xD162AA仅把persistent本体和首chunk+0x18交给262C700；true才计算262CAD0，否则显示rate operand0。它们没有额外与2657F10相AND。当前新查询逐actual-matched chunk分别发布两bool与wholepersistent fraction，保持first-record-per-army-regiment覆盖声明，不冒充遍历未闭合stride的全部data records。

Persistent补员owner可能是玩家军队所含的vassal/titleholder；CUnit当前owner仍绑定Robert，但不能强制每个persistent Regiment owner也等于Robert，否则会错失真实levy来源。已有CUnit+0x178→CArmy、CArmy+0x124→同public CUnit、CArmyRegiment+0x140→该CArmy和chunk双向FullID分别绑定原生对象。

并行stock-lane与abi-lane结果在同目录回链。原生需要同一当前帧的未集结人数、levy current/max、兵团raised/满员状态、补员开关和真实最终补员条件。ArmyComposition.GetUnraisedNumberOfSoldiers、GetCurrentNumberOfLevies、GetMaxNumberOfLevies，以及MilitaryView.IsMilitaryReinforcementsEnabled是当前stock GUI命名入口。未集结reserve由本工作包parent追，补员getter证据即时交给Root/army_supply_attrition及其fixture lane合入同一军力查询；不存在第二套重复reader/wire/normalizer修改。

正常围城日级军力下降并不单独说明未补员、损耗率或补员disabled；需同时读取current/max/类型、supply/attrition和native补员最终输入。Root/army_supply_attrition拥有现有军力reader/wire/normalizer修改，本包只提供原生字段和ABI证据，避免重复投影。

本包readiness为research；精确源码/stock/二进制研究不增加Robert production-live、补集结、兵力恢复、围城收复、战争胜利、保存日或G2信用。未闭合getter按具体xrefs继续施工，不以unknown终止当前战斗与围城主线。

## 2026-10-03 v43 当前 paused production 实读

前文离线 research/static-ready 与旧帧资格保留为各自施工阶段和冻结日期的历史事实；本节只提升本次 v43 实际已读字段，不回填旧帧 live。

Root 新 runtime `g45/v43` 冻结源码 `8e2cfbee4981af7f80398ec09129c1cf0f3dbe54`，CK3 exact `.3` 版本及 EXE SHA 保持本页上述绑定；唯一 Robert29829 普通战役 `native-29829-2bc2d599f7f9` 继续，game PID14124 处于后台暂停。本次只消费既有生产查询文件，不启动 SDK、不运行夹具、不操作窗口、不新增游戏日。

生产叶 [016-ck3_query_army_strengths.json](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/runtime-preparation/v43/actual-sway-new-fields-and-counter-scope-v43-01/016-ck3_query_army_strengths.json) 为 **GREEN**，SHA-256 `1f1f863e3ad77ad2ea59ad344ec1a5ae8c6178309e1e839a7c1514a04a913577`；date53240136、public revision2/native3、snapshot `native:3`、paused=true。既有 consumer 一次消费生成 [CURRENT-HEALTH.json](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/army-supply-attrition/actual-current-health-v43/CURRENT-HEALTH.json)。同 SDK30708 已正常关闭，整批 exit1 的原因是独立 defaultRaise012 RED，不能把本叶 GREEN 写成整批 GREEN。查询叶内 version/EXE SHA 为 null，版本绑定来自 Root 已冻结的 runtime，未伪造叶内身份字段。

当前玩家 CUnit83886367 → CArmy50331794，40 ArmyRegiments，current/max2248/2461；Root 同暂停帧正常保存 h5377，save SHA-256 `1b24b41318a27a75d4148ec58d9dcad93d74ec1be4f7e31b4eec30ed6ca998e6`。本 lane 不增加该正常保存的日信用，不以暂停帧兵数差构造伤亡。

首记录投影实际包含40个 ArmyRegiment rows：26 available、14 unavailable，14个原因均为 `army_regiment_first_record_absent` 且 actual native record count 为0。这是该回链入口在这些 row 的真实无首记录，不合成 hidden source、零补员率或全军不可补员结论。

26个 available rows 匹配26个 persistent inline chunks；`native_can_replenish` 分别 true14/false12，独立 `native_chunk_can_replenish` 分别 true6/false20。实际结果再次说明不能用人工 AND 替换两项原生返回值。persistent whole-Regiment monthly fraction raw/Q100000 含3075、10000、4200、3825、3000、4125、5700、3150、4575、3675；完整频次在 receipt。它们不是当前 ArmyRegiment 或整军净补兵人数/月。

真实 native data-record count 分布为0×14、1×20、2×2、3×2、4×1、5×1，六个 row 多于一条 record。已读首记录/双 FullID 匹配 chunk 原生当前许可与 fraction 提升为 **limited production-live primitive**；全部 record 覆盖与整军净补兵预测仍未完成。需要完整覆盖时，具体施工入口是 native `0xD14960` 下 actual ArmyRegiment+0x20 data-record 基址/+0x2C count 的 stride与完整遍历、persistent解析及 chunk双向回链；现有首记录路径和已读原生 getter 直接复用，不再研究同一 getter。此质量差距不阻断当前以 supply/capacity/attrition 和已有军力进行普通移动/围城解围。

```mermaid
flowchart TD
    A["v43 paused: 40 actual ArmyRegiment rows"] --> C{"actual data-record count"}
    C -->|0: 14 rows| E["first_record_absent; 不伪造补员零值"]
    C -->|positive: 26 rows| F["真实 first persistent record + 双FullID匹配26chunks"]
    F --> B["独立 native262C700 与2657F10 bool"]
    F --> M["whole persistent262CAD0 monthly fraction"]
    B --> P["首记录当前输入 production-live primitive"]
    M --> P
    C -. "count>1: 6 rows; stride完整遍历未闭合" .-> U["全部record覆盖施工入口"]
    P --> D["当前 army health 与正常战术继续"]
```

没有声明补员动作、完整未集结reserve、全军净月补员、战斗胜利或新游戏日。当前 SDK 的 defaultRaise012 RED 由其 owner 处理，与本叶首记录真实已读区分记录。当前补给三数值 actual 见 [容量/损耗专题](army-current-supply-capacity-attrition-12003.md) 的同日追加。

Root 本次协调收口的累计保存日为3992，自然继承0；本健康查询与文件整合新增0日。该计日来自 Root 总账，不由补给、兵数或月贡献推算；2248/2461 的差额不作为24小时损耗或战斗伤亡。

## Exact .3 gathering remaining days: 2026-10-03 numeric closure

This increment closes the previously name-only `Army.GetGatheringDaysLeft` entrance. Status is **research / exact static ABI closed**; source projection and production observation are owned by the coordinator. It does not claim a new live sample. Read-only source is frozen `Z:/g47`, HEAD `7a0bef46588292d26c74716a39fe02b348d3ee65`; exact build is CK3 **1.20.0.3**, Steam **25652598**, EXE SHA-256 `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`.

The bridge-callable leaf is **RVA `0x24E9070`**, signature **`std::int32_t (*)(const void* actual_carmy)`** on Windows x64: **RCX = actual CArmy**, **EAX = signed int32 game days, scale 1**. There is no hidden output pointer or fixed-point result. The entire leaf is **`[0x24E9070,0x24E90E9)`**, **121 bytes**, SHA-256 **`8ea314c82d44c11c275c31d0f4394521efe1da910bd29d53d87d0398d75881fd`**. It performs no calls or stores. The full span ends in RET followed by seven INT3 bytes; the next function starts at `0x24E90F0`. Two independent lanes recovered identical full bytes and return/date arithmetic.

| Evidence | Exact closure |
| --- | --- |
| Name and registration | String `GetGatheringDaysLeft` at `0x4736AE8`; MOVUPS name copy at `0x4EA703`; `0x4EA77E` loads callback `0x24EA330`, registration call `0x4EA789`. Full initializer `[0x4EA690,0x4EA809)`, 377 B, SHA `be4263ce77e88e6d969ac78f8f8962c6cf463f1de38ffb7dc01a5b858e33992d`. |
| GUI callback | `[0x24EA330,0x24EA368)`, 56 B, SHA `86f34e580feee5ef5cfa00b60eea1c6105b849ee471614da4636b36584fbeecf`. Calls the core at `0x24EA342`; writes integer expression output and returns bool AL. Use the numeric core for the bridge. |
| Independent receiver caller | Native state formatter `[0xD19270,0xD19A04)`, SHA `ba35034a660cecc0d0cc2775d1454596abb2c74d9ce039414897910aae1e15f3`. State 5 branch `0xD19437` reads CUnit `+0x178`, resolves CArmy through store `0x5D1DE48` and object full ID `+0x10`; call `0xD19477` invokes the same core with actual CArmy in RCX. EAX goes to an integer formatter. |

The core reads the current native raw date through global slot **`0x5C68C50`**, gathering record pointer array **CArmy `+0x50`**, and signed record count **`+0x5C`**. For each record, its first signed raw date participates in a maximum initially seeded with the current date. Its precise result is:

```text
D(raw) = trunc_toward_zero((int32(raw) - 0x29C55C0) / 24)
days_left = max(0, D(max(current_raw_date, record_raw_dates)) - D(current_raw_date))
```

The signed division-by-24 multiply/shift/sign correction occurs separately for the two dates. A day boundary can therefore produce a positive result when fewer than 24 raw time units remain. The production reader should invoke the native core rather than reproduce this arithmetic or infer remaining time from movement ETA, progress fraction, the 40.0 gathering speed, or the AI's 180-day raise cooldown.

Reuse the existing strength-reader receiver during its paused owning-thread sample: public **CUnit full ID** through store `0x5D1E380` and object `+0x10`; internal CArmy full ID at **CUnit `+0x178`** through store `0x5D1DE48` and object `+0x10`; existing **CArmy `+0x124` == public CUnit ID** branch. Bind the core in the current exact `.3` adapter and invoke it inside that branch. The callback does not receive a CUnit, GUI context, or temporary composition object. No additional army magic or military-action gate is required.

The core has **no gathering-state test**. The native state formatter applies it in **state 5**, so the same strength query should publish a signed integer for a resolved state-5 army, including **valid zero**. Other states publish **null / `not_gathering`**; a failed binding or receiver read remains a separate unavailable status. Zero is neither a read failure nor proof that troops already attached or reached the capital.

```mermaid
flowchart TD
  Snapshot[Fresh public CUnit and actual state] --> Join[Existing full-ID CUnit to CArmy join and backlink]
  Join --> State{Existing native state code 5?}
  State -->|yes| Core[Call CArmy core 24E9070]
  Core --> Days[Integer remaining days; valid zero]
  State -->|no| Other[null / not_gathering]
  Days --> Observe[Read actual regiments, current soldiers and position]
  Observe --> Input[Current inputs for waiting and reinforcements]
  Days -. Root next paused query .-> Pending[Actual countdown value not sampled by this lane]
  Input -. future transit outcomes .-> Arrival[Actual delivered troops and arrival remain observed separately]
```

Root's supplied raise frame contains public CUnit `167772189` -> CArmy `83886088`, province `2618`, state 5, regiments/current/max all **0**. This lane did not refresh that frame or read its countdown. The callable closure removes the numeric-field construction gap; Root owns the next actual query and normal-day observation. Reserve 123 remains a separate unraised quantity.

Evidence package: `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/army-reinforcement-raise/runtime-v45-gathering-observation/native-days/ROOT-DELIVERY.json`, including `getter-lane/EVIDENCE.md`, complete body/caller pins, `abi-lane/RECEIVER-INTEGRATION.md`, and day/week fields. No SDK, game/window interaction, shared source mutation, Git, old fixtures, native invocation, repeated raise, or build was performed by these research lanes.

## 2026-10-04: gathering remaining days reaches production-live primitive

Runtime **v46** actual016 accepted the strength query with status **available** (Root-reported `public2/native3/native:3`). New public CUnit **167772189**, native CArmy **83886088**, returned **7 game days**, status **available**, ready **true**, while current/max soldiers and regiment count remained **0/0/0**. The same paused actual014 placed it at province **2618**, native state **5 / gathering**, not in combat. This establishes a **production-live primitive** for the numeric remaining-days observation; it does not establish a complete reinforcement loop or turn unraised reserve 123 into present combat strength.

Old public CUnit **83886367**, native CArmy **50331794**, returned days **null**, status **not_gathering**, ready **true**, with **2259/2460** soldiers and **39** regiments. Actual014 placed it at **2616**, state **7 / moving**, not in combat, with the nine-hop route **[8754,2613,8752,2628,2626,2627,2633,2634,2640]**. This frame demonstrates successful non-gathering applicability reporting separately from a failed read. Valid gathering zero remains supported by the earlier static fixture/native formula; this frame observed **7**, not an actual zero-day countdown.

Actual018 completed normal SAVE for the same **Robert 29829**, session **native-29829-2bc2d599f7f9**, at **h5509 / raw date53240928**, **91443885 bytes**, SHA-256 **7ded957a3c703ceb5bd5bd3515444c5c04d01de0594da1812a2ba99440fabafb**. There was **no day advance**. The run's overall result remains **RED**; its cause is retained by the parent from cached evidence. That run-level result does not change the independently observed gathering primitive. These facts were supplied by the sole actual consumer; this lane did not reopen artifacts, invoke SDK, build, test, edit shared files, run Git, or use a window. Next reinforcement decisions can consume the observed 7 days together with actual current troops and positions; delivered troops and arrival still require subsequent actual observation.

## 2026-10-04: bounded raise/gather loop reaches production-live loop

Runtime **v46** fresh query **004**, sequence **3**, accepted/status **available**, Root-reported `public2/native37/native:37`, at raw date **53241096**, returned new public CUnit **167772189** / CArmy **83886088** with actual **123/123 soldiers**, **1 regiment**, gathering days **null / not_gathering / ready true**. The same-frame result placed it at **2618**, state **1 / regular**, empty route, not in combat. New supply was **100/100**, current attrition **0**, monthly supply change **+20**. The 123 soldiers can now receive actual delivered-troop credit from this frame; this is not a deduction from the previous unraised reserve. Arrival at the capital or combat is not demonstrated.

Old public CUnit **83886367** / CArmy **50331794** was retained at **8754**, state **7 / moving**, not in combat, with eight remaining hops **[2613,8752,2628,2626,2627,2633,2634,2640]**, **2259/2460 soldiers**, **39 regiments**, supply **120/300**, current attrition **0**, and monthly supply change **0**. The result was **GREEN**, with **none failed**. Normal SAVE **006** retained the same **Robert 29829 / episode2bc**, **h5534 / raw date53241096**, **91825231 bytes**, SHA-256 **22e9028da99a4f77ba5b5485b912065f38aa9761fc9100a1adf63d4dd238f028**. Root reported SDK **99980**, normal closed exit **0 / GREEN**.

The bounded sequence is now a **production-live loop**: one default-raise action created the new zero-strength ID, one initial normal day exposed the actual 7-day countdown, Root advanced seven normal days, and the fresh frame confirmed positive soldiers, gathering completion, and the retained old army. Initial raise was **raw date53240904 / h5496**; the countdown phase was **raw date53240928 / h5509**; completion at **53241096** is **8 game days from raise**. Credit applies only to this raise/gather loop; full war and autoplay remain incomplete. Root owns the Oct4 seven-day advance and sole consumption of the three current files. This documentation lane used only supplied facts, with no artifact/source reread, SDK, advance, test, build, shared edit, Git, or window use.

### 2026-10-04 v47：合并后保留军的实际兵力与现任指挥官

这次独立消费只读取 `actual-merge-local-reinforcements-01/007-ck3_query_army_strengths.json` 和 `009-ck3_query_army_commander_candidates_v1.json`，各一次。两条查询同为 public revision `3` / native revision `13` / snapshot `native:13`，日期 raw `53241096`；007 query sequence 为 `3`，009 为 `2`。玩家为 Robert `29829`。Root 提供的运行时标识为 `v47 / g51 / source1c / R24`，游戏 PID `32372`；SDK `37552` 正常关闭、exit `0`、批次全部 GREEN。运行时和关闭信息来自 Root 的实际报告，本消费者没有读取环境、result、checkpoint 或合并成员查询。

| 公开 CUnit / 原生 CArmy | 实际当前 / 最大兵力 | 团数 | 实际补给 / 上限 | 月度补给变化 | 当前损耗 | 集结剩余天数 / 状态 / ready |
| --- | --- | --- | --- | --- | --- | --- |
| `167772189 / 83886088`，保留军 D | `1770 / 1770` | `7` | `99.999 / 100` | `+20` | `0` | `null / not_gathering / true` |
| `83886367 / 50331794`，原军 | `2259 / 2460` | `39` | `120 / 300` | `0` | `0` | `null / not_gathering / true` |

D 的兵力 `1770` 是 007 当前 native getter 的结果，可以计入实际兵力；此前雇佣军 `1647` 和地方征召军 `123` 的相加不作为本次信用依据。D 的补给原值为 `9999900`、scale `100000`，必须保留为 `99.999`；上限原值 `10000000`，月度变化原值 `2000000`，当前损耗原值 `0`，同用 scale `100000`。AI base power 原值为 `4840400000` / scale `100000`；它不是胜率。

009 的 `current_commander` 独立对象为 `status=available, character_id=34867, unavailable_reason=null`。同一原生 CArmy 的 `current_movement_speed.current_commander_character_id` 也为 `34867`，该上下文可观察；D 位于 `2618`，状态 `regular / 1`，路径为空，未战斗、未撤退。当前指挥官对应候选行可观察，`available=true`、`final_eligibility_observable=true`、`can_assign=false`；这不会改变其已经被选中的当前事实。该 false 的原因没有在本包中读取，不补造解释。已读 quality 为 native AI base quality `28`、generic advantage points `28`、siege phase time modifier raw `-10000`；本包不另推该 raw 的缩放。

本次两条查询各自达到 `production-live primitive`。合并动作和成员关系由 `war_goal` 的唯一消费者记录；完整合并闭环须由 Root 将它的动作／成员证据与本包的独立实际兵力、指挥官观测结合。补给加权截断及指挥官继承的原生数学由军队供给工作包维护，本包只向它提供这份同帧 decoded summary，不让它二读 raw，也不从公共总人数强推未发布的原生权重。未宣称战斗、抵达目标或完整战争完成。

外部 receipt：`Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/army-reinforcement-raise/runtime-v47-postmerge-strength-commander-consumption/ROOT-DELIVERY.json`，SHA-256 `08f9260d550af7bd64cd6a064dfd099eb204feb08d653e13530f1d5a031da103`。输入完整 SHA、两个 query 的参数和当前指挥官对象保留在 receipt 及同目录 raw cache；Oct4／2026-W40 报告片段在 `report-lane/`。本消费者 SDK、推进、重复查询、测试、Git、共享写入、窗口和构建均为 `0`。

### 2026-10-04 v49：战斗后的两军前态与合并后主军实读

唯一兵力消费者各读一次 `actual-post-battle-merge-hot-python-01/005-ck3_query_army_strengths.json` 和 `010-ck3_query_army_strengths.json`。Root 报告 SDK `84390` 正常关闭、exit `0`、GREEN；当前 Python 为 hot `g54/8898`，原生运行时仍是 `R24/g51`，本次没有为这份双 row 观测制造新 DLL。两次查询日期都为 raw `53241792`，均 `accepted=true/status=available`。

| 查询 / 公开 CUnit / 原生 CArmy | 当前 / 最大兵力 | 团数 | 补给 / 上限 | 月度补给变化 | 当前损耗 |
| --- | --- | --- | --- | --- | --- |
| 005 前态主军 `83886367 / 50331794` | `2253 / 2460` | `39` | `120 / 300` | `+20` | `0` |
| 005 前态 J `167772189 / 83886088` | `1647 / 1770` | `7` | `99.999 / 100` | `+20` | `0` |
| 010 后态保留主军 `83886367 / 50331794` | **`3901 / 4231`** | **`47`** | **`111.52397 / 300`** | `+20` | `0` |

005 参数为两 IDs、expected public revision `2`，query sequence `9`，实际 public/native revision `2/154`、snapshot `native:154`。010 参数只有主军、expected public revision `3`，query sequence `10`，实际 public/native revision `3/155`、snapshot `native:155`。后态补给原值 `11152397`、上限原值 `30000000`、月度变化原值 `2000000`、当前损耗原值 `0`，scale 均为 `100000`。三条实际 row 的集结字段全部是 `null/not_gathering/ready=true`；它只证明可观察的非集结状态，本消费者没有读取移动、战斗或其他 unit state。

当前兵力信用以 010 的实际 getter **3901** 为准。前态公开当前兵力合计是 `3900`、最大兵力合计 `4230`、团数合计 `46`；后态分别多 `1/1/1`。AI base power 前态原值合计 `11921100000`，后态实际原值 `11981100000`，同 scale `100000`，差 `600` power points；它不是胜率。差值只作为原生前后结果记录，未从这两条查询读取原因，不由公开总人数强推原生补给权重，也不为了相等而改写实际数字。

这两条强度观测达到 `production-live primitive`。Root 发起的 `83886367-with167772189` 合并动作和成员结果由另一个唯一消费者确认；本包不从“后查询只请求主军”推断 J 已消失，不重复读取其他 snapshot、merge、war、result 或 checkpoint，也不宣称独立战斗终态、完整战争或完整自动游玩完成。本增量推进 `0` 日，当前 Root 全局日数未随任务给出，不沿用历史 `4032/4040` 作为当前数值。

Receipt：`Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/army-reinforcement-raise/runtime-v49-postbattle-merge-strength-consumption/ROOT-DELIVERY.json`，9545 bytes，SHA-256 `88897872d38c4a7ac00b64aaa12b248bc8c19877e77977c851dd96e79aa2c426`；其中保留两输入完整 SHA、原生前后数值和精确参数。Oct4／2026-W40 报告字段在同目录 `report-lane/`。SDK、重复查询、推进、测试、Git、共享写入、窗口和构建均为 `0`；未重复读取旧 `1770` 证据。


## 2026-10-04 第4期：完整actual逐团人数投影，离线验证通过

第4期的P0-LOSS/P0-REFILL需要比较每个actual军团的真实人数。现有首record补员行只覆盖persistent匹配chunk，不能替代完整actual军团人数，尤其是无首record与多record行。现有军力查询新增可选`regiment_strengths`数组，每行只发布`army_regiment_id/current_soldiers/maximum_soldiers/scale=1`；ID是generation-checked CArmy成员数组里的CArmyRegiment FullID，数值直接复用同次Strength迭代已有的`+0x38/+0x3C`读取，没有新增getter或扩大persistent record遍历。

整军current/max继续来自原生getter。**数组求和一致性是现有producer的available输出不变量，不是新推导的原生普适公式**：旧Strength已要求native getter结果等于该迭代sum，否则返回`native_helper_mismatch/unavailable`。新增数组只在旧准入通过后发布，normalizer镜像这一构造约束。无可用整军帧不发布部分数组；实际零团为`[]`，旧生产者缺字段保持可读。原补员两bool、wholepersistent比例和first-record覆盖语义不变。

本机只读重新核对CK3 1.20.0.3 / Steam25652598、EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`；解释器为主树`tools/.venv/Scripts/python.exe`，Python3.14.7。focused验证通过：MSVC仅生产reader+fixture EXE，生产reader→共享serializer→候选Python normalizer的8条生成wire，以及Python契约10 tests。原始编译与fixture回执为`C:/ck3-war-episode04-research-20261004-a01/refill/implementation-a01/native-build-a01/army-reader-ci-result.json`，完整wire、Python输出和结果在同包`checks-a01/`。六文件patch和before/after SHA保全在`regiment-strengths.patch`与`patch-manifest.json`，patch SHA `dd66ab4446ad27dcd9b7d07f390337aa028a0c10f7cd38472da9e9cc12b1ec20`。

最初外置镜像缺主树`tools/build_release`导致import失败，保留为environment RED；显式供应主树tools只读路径后，同一主venv验证通过，未将环境缺失记为业务代码RED。所有旧输入、失败和中间编译产物保留。此包没有SDK、游戏/窗口操作、DLL构建/部署或新实机样本；readiness为**offline production-reader fixture**，不是production-live。

下一步由正式操作者冻结新runtime、严格构建并在真实paused query验证完整逐团数组。P0-LOSS采样绑定session/date/revision、public CUnit/native CArmy及完整actual FullID，分别保存逐团current/max、补给/容量/月贡献/当前损耗，并记录战斗、补员、集结和编成变化。端点人数差只记净变化；确切损耗因果要结合执行链和排除混杂。P0-REFILL用同一军队真实补给恢复的连续镜头对照实际兵数；人数端点不变可以说明两项状态不同，不能证明过程完全未补员。详细最小案例、native plan及日/周字段保全在`D:/ck3-war-episode04-research-20261004-a01/refill/`。


## 2026-10-04 R0161：完整actual逐团人数首次实读

Root独立William主案，人物33388，R0161；source `f8530f4aeb64735dbeae4831f3bc6c315276bb88`，DLL SHA `726d0f1970b4df4f7fc30bc641f31d0183b197efbebd1c1d9c240f2a6233b3f5`，CK3 1.20.0.3 / Steam25652598及EXE SHA保持本专题绑定。EXE/DLL完整身份由`prepared-main-case-a01/prepared.json`核对，source由`capture-source-freeze-a02/manifest.json`核对；它们在`C:/ck3-war-episode04-research-20261004-a01/`。health叶内game_version/EXE SHA是null，未伪造其身份字段。actor/run绑定来自Root的实际运行报告。

`operations-main-case-a01/starting-health-a01/002-000-health.response.json`实际`accepted=true/status=partial`，query1、public3/native2、snapshot`native:2`、raw date53147160、paused=true。源文件SHA `74a1ffd31f4c4718983f7844f3d90c08289bdc9463eb40154dfb81f4835dac24`。两条available行完整发布27个actual ArmyRegiment FullID，逐团scale均1；逐团current/max SUM分别精确等于该行原生整军getter。

| public CUnit / native CArmy | actual团数 | actual current/max及SUM | 首record覆盖 | 补给/容量 | 月贡献 | 当前损耗 |
| --- | ---: | --- | --- | --- | ---: | ---: |
| 0 / 0 | 13 | 5660/5660，SUM相同 | 13 available，全为count1 | 82.99737/100 | −10 | 0.01即1% |
| 16777220 / 16777220 | 14 | 1086/1087，SUM相同 | 9 available、5无首record | 291.22808/300 | 0 | 0 |

第二军唯一actual缺员行为FullID53，9/10；该行当前两补员bool均false。FullID56–60各有actual1/1士兵，但首record count0、`army_regiment_first_record_absent`；这直接显示完整actual数组和persistent首记录查询的不同覆盖域。多record行为50/51/54/61/62/82，当前匹配首chunk兵数合计680，不能替代actual整军1086。主军本帧13个single-record匹配chunk合5660，不能将这种当前完整匹配外推为其他军的全record覆盖。

主军13行两补员bool都false，且实际已经满员；不能据此说这支军永久不补员。第二军当前匹配chunk中`native_can_replenish=true`有7条，独立`native_chunk_can_replenish=true`为0条；仍不得人工AND或换算全军净月补兵。当前health没有发布`special_supply` flags，也不能将未映射的chunk state_raw1视作特殊补给标志。

Army166为`native_carmy_not_found/unavailable`，是请求批次partial的独立行；没有观测到它的CArmy或兵数，不能记为第三支军或0兵。前两军完整actual数组达到**production-live primitive**，尚无补给恢复、实际补员或损耗前后因果loop。它们本帧月贡献分别−10和0，都不是已经取得正补给恢复的观察窗口。

唯一消费输出、27行完整人数表、runtime绑定、native plan及日/周字段在`C:/ck3-war-episode04-research-20261004-a01/refill-live-review-a01/ROOT-DELIVERY.json`。native plan已`check --for-observation/render`，这里只提升具体源叶的实读，结构检查不代替语义或新实机。此消费lane没有SDK、进程/窗口读取、日期推进、测试或DLL部署，新游戏日0；Root正式录像与随后状态转移由各自新packet记录。


## 2026-10-05：R0162 完整actual人数与补员边界

初始三支可读实际军队共27个actual团6746/6747；公开166行native-null，不能当第四支真实人数0军。拆军只转移六个完整ID，current/max不变。day+6 child3120→3089；day+9 main2540→2413，完整27 FullIDs、归属与max没有增删。到达帧可读合计6588/6747。前后完整数组和逐团尾差见[两类扣兵研究](army-episode04-periodic-and-county-arrival-loss-r0162.md)。

拆分child的六团两端各唯一record且对应chunk可读；native_can_replenish与chunk_can_replenish都false只属于这些端点。其余军队仍保持首record范围，未扩大为全persistent净补员合同。截至最后有效逐段采样初始+22日没有正人数净增，不能据此排除隐藏补员。主军到1513后 stock82.99737、month−5，未实现补给恢复；当前损耗率0也不等于正补给或正补员。后续pause失败产生大空窗，不将最终+88端点并入此逐日表，不从中反推第25日补给、月初补员或reserve迁移。


R0162范围补充：第三支实际军16777220在+15日1086→1076，max1087保持；五团减2/2/3/1/2，共10。此前“−31与−127两次”只属于拆分13团family，不能当全部27团变化计数。完整分组在 split-live-r0162-a01/seal-a02/ALL-ARMY-CHANGE-SUMMARY.json。

## 2026-10-05 / W41 — complete persistent DATA mapping construction

Root selected one increment to the existing `ck3_query_army_strengths`: complete persistent DATA records for each already resolved ArmyRegiment. The published `regiment_strengths` array already covers ArmyRegiment current/max; the published `regiment_replenishment` array explicitly covers the first persistent record. Neither substitutes for all stored DATA records. The sealed R31 coverage summary contains 28 readable first-record rows out of 41 ArmyRegiments, with their native DATA record counts summing to 42. That is evidence of additional stored records. The later R32 Clock24 terminal health is independently `3515/3884`; its 369-person aggregate deficit has not been assigned to those earlier records. No new actual frame was read for this construction.

Exact 1.20.0.3 / Steam 25652598, EXE SHA `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`: the sealed `2633340` chain closes ArmyRegiment DATA `+20`, capacity/count `+28/+2C`, stride `0x10`, persistent full ID `record+8`, and chunk ordinal `record+C`. Resolve the full-generation `Regi` identity and the seven inline chunks at persistent `+18`, stride `0x24`; retain the stored index, persistent identity, ordinal and reciprocal ArmyRegiment identity. This supersedes the earlier first-record implementation's bounded stride coverage; its historical evidence remains valid.

Each record exposes physical current/max/state separately from the native effective current used by `262C9D0`: state `3` with physical current `0` contributes maximum as effective current. The two native eligibility calls remain independent. The persistent `+148` prepared Q100000 fraction is an actual cached execution input; the fresh `262CAD0` result is a separate current getter. Neither rate is an observed army net refill. The cached fraction, when exposed, is part of the same complete-record observation and does not create a second query family or a forecast.

A legitimate native count `0` produces an available empty record array. It supplies no persistent ID, dummy chunk, false eligibility or zero fraction. A record whose identity or reciprocal link cannot be resolved retains its stored index and its own unavailable status; this does not replace the parent army's observed health with null or invent an unavailable whole-army status. Complete DATA coverage still cannot invent a persistent source for a zero-record ArmyRegiment.

```mermaid
flowchart TD
    A[Resolved ArmyRegiment and actual current/max] --> H[Native DATA base and count]
    H -->|count zero| E[Available records empty]
    H -->|count positive| R[Every stored record index and FullID/ordinal]
    R --> I[Exact persistent identity and reciprocal inline chunk]
    I --> P[Physical current/max/state]
    P --> C[Native effective-current rule]
    I --> B[Two independent native eligibility results]
    I --> F[Prepared cache and separate fresh fraction]
    C --> O[Actual record deficit association]
    B --> O
    F --> O
    O -. later month conditions require a later observed frame .-> M[Normal future native allocation]
```

Source ledger: `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261005/army-replenishment-current-input-v66/source-ledger/FULL-DATA-CONSTRUCTION-ENTRY.md`, 6100 bytes, SHA-256 `465ed3ba75ff112b586bf4afaea7c3a92d02a04053d82b59c1fa0f05fd1f89d7`. The ledger reuses the already sealed exact-build allocation and aggregate-refresh chain. Construction adds no game days, SDK calls, EXE reads, window interaction or automatic army action. Readiness and the final production contract are recorded with the source packet and its two new focused production cases; an actual paused query remains Root's next qualification step.


### Published contract and two new production cases

The frozen source packet adds `regiment_replenishment_records_v1` on the same army row. Native locator: `command_result.result.army_strengths[*].regiment_replenishment_records_v1`; normalized MCP locator: `structured_content.army_strengths[*].regiment_replenishment_records_v1`. Match army rows by `army_id` and the nested array by `army_regiment_id`; there is no additional wrapper. The old first-record array and its output remain unchanged.

Each ArmyRegiment entry has `army_regiment_id`, `source="native_all_data_records"`, `status` (`available/partial/unavailable`), `ready`, `native_data_record_count`, `unavailable_reason`, and `records`. A readable native count zero yields available/ready true and `records=[]`. Each record retains `record_index`, `persistent_regiment_id`, `chunk_index`, `status`, `unavailable_reason`, `current_soldiers`, `maximum_soldiers`, `effective_current_soldiers`, `state_raw`, independent `native_can_replenish` / `native_chunk_can_replenish`, and separate `persistent_monthly_replenishment_fraction_raw` / `persistent_prepared_replenishment_fraction_raw` with their respective scale fields fixed to `100000`.

Exactly two new production cases ran once through the actual parent strength reader and serializer. The first keeps a full first record and a deficient nonfirst record, independent predicates, prepared zero versus a positive fresh getter, and state3 physical zero versus effective maximum. The second retains legitimate empty coverage and a genuinely unavailable reciprocal record while the parent army remains available. Compile `/O2 /W4 /WX` exited 0 in 4.2596791 seconds; native execution checked 28 explicit requirements in 0.1056475 seconds; registered MCP `-B -O` consumed the same two native outputs and passed 20 checks in 4.3737575 seconds. No old Clock24/first-record case or matrix was rerun.

Source readiness is **static-ready**. Frozen 11-path packet: `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261005/army-replenishment-current-input-v66/full-data-observer/ROOT-ONLY-FULL-DATA-REPLENISHMENT-OBSERVATION-v66.patch`, 60072 bytes, SHA-256 `674f5db7b78085a5b92e6f9b803b1b1022fcebbba685e364dcfb343368e567e7`; parent publisher receipt 9118 bytes, SHA `30a53909f4bae54fb7751095018724ecc402d4b997c2c32cdacddd8bf5ed5b33`. The sole new production-case receipt is `full-data-observer/production-fixture/ROOT-DELIVERY.json`, SHA `50826652614d460ae96b8b2e93a3c326355a48b4618243d8b6f5af2bf26f70a0`. The packet includes the necessary new translation unit in the existing isolated army CI runner; no old CI step was rerun.

### R34 actual existing-query coverage, before full DATA deployment

Root's actual `014-ck3_query_army_strengths.json` was consumed as one complete buffer and converted to shared complete/cache subtrees. It is an independent frame: R34 / PID57600, source `bef2c4b7ba34cffc6abb6c22f7abd6325078dcc3`, native revision `3`, public revision `2`, paused raw date `53256120`. Query/global scope and all three army rows are available. The native source `game_version` and `executable_sha256` fields are actual null; the frozen Root runtime identity remains separate provenance.

| Army | Actual current/max; regiments | Supply/cap; monthly change; attrition | First coverage; native DATA total | Deficit by ArmyRegiment record count |
| --- | --- | --- | --- | --- |
| Own `301989997` | `3515/3884`; `41` | `300/300`; `0`; `0.01` | `28` available / `13` absent; `42` | total `369`: `263` on count1, `106` on count>1, `0` on count0 |
| Guard `184549452` | `3000/3000`; `24` | `100/100`; `+20`; `0` | `24` available; `24` | `0` |
| Enemy `268435597` | `2772/4702`; `41` | `300/300`; `+20`; `0` | `38` available / `3` absent; `133` | total `1930`: `538` on count1, `1392` on count>1, `0` on count0 |

The 13 own and 3 enemy unavailable first rows in this new frame all report `army_regiment_first_record_absent`. Their ArmyRegiment current/max difference is zero in this frame; this does not mean every future zero-record row is full. The `106` and `1392` are deficits of ArmyRegiments that contain multiple DATA records; they are **not** an attribution of all those deficits to unobserved nonfirst chunks. This now supplies a same-frame value basis for full DATA observation without changing the earlier R31/R32 evidence.

All three are observed `not_gathering`, gathering ready true and days null. All three clock blocks are available/ready: current `D=394005`, selected bucket `15`; own/guard/enemy buckets `0/28/6`, and last-success raw dates `53255760/53255712/53255904`. Complete AI owner-recall subtrees are present and were handed to their independent sole cached consumer; this topic does not qualify their selection semantics.

R34 has **no `regiment_replenishment_records_v1` field**: it predates the new packet. Existing health and clock observations are a **production-live primitive**; the new complete-record fields still need Root's deployment and independent paused query. The query is observed recovered after prior unavailable attempts; this leaf does not prove the cause of that recovery. No original raw was read by peer lanes.

Original leaf SHA-256 `77e4cbb1797c89551ffb05553f46f4b06b04bff91661d47e219ad4583b07606d`. Full parsed result and domain caches are indexed by `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261005/army-replenishment-current-input-v66/actual-r34-health-consumption/ROOT-DELIVERY.json`, 9821 bytes, SHA `494fa07bf00177a7239f68cea6e1771a41eda864356f02b66dc26b24880ad51a`. Normal SAVE provenance from Root is h7763 / 96643979 bytes / SHA `49a44fddd1dc490dd67ddf70353df9cf915de0428d42cf22fc07fbd3745b084e`, environment `1d61c93015d5c48e9b74550ab7fcabbc8ad4cdabacffe03fbad5d310f55538e5`. Total saved game days remain Root's `4658`; this work adds `0`, including `0` Oct5 game-day credit. Oct5 / W41 report fields are in the respective source/fixture and actual-consumption receipts.


### Root source adoption after this actual frame

Root applied, committed and pushed the complete 11-path source packet as `324938d0b879f26a618b7704a520305b760f56ec`. The earlier document attempt had a real context conflict after independent upstream `cddb7e3d` changed this topic; it wrote zero shared files. This new append preserves the complete current upstream prefix and reuses the sealed source/test/R34 coverage text without another raw read or verification.

Root subsequently completed 14 ordinary game days: total `4672`, resume `1519`, Oct5 `+14`, raw date `53256456`, normal h7807. Those later days do not change R34's earlier `4658`/Oct5 `0` query frame above. The new full DATA fields have not yet been queried from the next deployed native runtime, so source adoption and the later day credit do not confer full DATA production-live status. Root owns that independent paused query after the unified v62/g67 build/deployment.

### R35：完整 DATA 与实际 prepared 输入首次 paused 观测

2026-10-05，原 `ck3_query_army_strengths` 同口 paused 叶 accepted/available，native3/public2/date53256456。父代理唯一读取 original013 后封完整缓存，本 lane 仅消费该授权缓存一次；三个 Army 行及新增 sibling 均 available，106 个 ArmyReg snapshot、199 个 stored record 全 available，partial/unavailable 均零。记录按原顺序保留，没有 dedup；16 个合法 native count0 snapshot 为 available/ready、records[]，不降低父 Army health readiness。

| Public Army / native CArmy | 当前/上限 | ArmyReg / DATA records | 合法 count0 / multi | 首记录 / 非首记录 physical 缺额 | 两项资格 true/false |
|---|---:|---:|---:|---:|---|
| 301989997 / 201326670 | 3515/3884 | 41/42 | 13/6 | 350/19 | CanReplenish 26/16；ChunkCan 0/42 |
| 184549452 / 167772208 | 3000/3000 | 24/24 | 0/0 | 0/无非首记录 | CanReplenish 0/24；ChunkCan 0/24 |
| 268435597 / 184549476 | 2843/4702 | 41/133 | 3/25 | 770/1089 | CanReplenish 127/6；ChunkCan 70/63 |

主军首28记录有23条缺额，非首14记录有2条缺额：ArmyReg117440605 的 record1 / persistent882 / ordinal0 为127/145（缺18）；ArmyReg218104157 的 record1 / persistent904 / ordinal2 为2/3（缺1）。两条独立资格均 true/false，fresh Fraw 分别5625/3225，prepared Fraw 均0，scale100000。当前同帧350+19=369与主军 health gap 相符；这是本帧已观测关联，不把历史 R31 coverage 和 R32 gap 拼成因果，也不建立任意 record sum 必等 Army health 的规则。

全199 records 的 fresh whole-persistent getter F 均为正，实际 CReg+148 prepared F 均为合法0且与 fresh F 不同；两 bool 分别发布。上述月首执行输入与当前资格是独立真值，不能把 fresh getter 直接授作当前执行补人数，也不能推下一月首缓存仍0、未来资格永久false或损失原因。本帧 physical/effective 缺额相同，未观察到 state3/current0→effectiveMax 实例；该分支仍回链既有 native/fixture 证据。

此项达到 `production-live primitive`：完整 DATA 缺额与 prepared 输入可在现有 paused 查询观察；补员恢复循环、未来日期和全战役没有因此完成。实际 query source.game_version/executable_sha256 仍null，Root外层091bb268/R0035/PID110044仅作 provenance，不回填 source。军力叶 GREEN 与第三 death 查询缺参数造成的 Harness RED 分开；normalSAVE017准确锚点仍由Root消费。本 lane 0新SDK/raw/source/test/day/window/Git，共享专题仅由父代理采用本追加段。


The exact ArmyRegiment joins in the independent cached association lane also match each army's raised current/max gap in this frame: own `369/369`, guard `0/0`, enemy `1859/1859`. All 23 own and 31 enemy deficient ArmyRegiments have readable deficit records; positive deficit left without record association is zero. The two own armies remain separate observations (`3515` and `3000`, combined current/max `6515/6884`), with no merge, new raise or reserve credit. The strength query does not publish the current unraised reserve or default-raise legality.

The current clock view is independently available/ready for all three: raw `53256456`, native D `394019`, selected phase `29`, observed buckets own/guard/enemy `0/28/6`. Last-success dates are `53255760/53256432/53255904`, grace anchors `53251464/53251272/53249376`, loaded grace `30`. All three gathering states are `not_gathering` with ready true and days null. The original 64-bit storage values remain exact in the clock cache. This is a current observation; it does not rerun or broaden the old Clock24 loop.

Outer Root provenance is frozen source `091bb268aae3e533daeb853c1f8f34aa736ca62a`, R0035, native PID110044, execution `16cbd061-552e-4e4d-bb67-7c0892d08781`, environment SHA `38666cec554cab6152f16df89440a448cf8c988347a54e961777238aa666e626`. These identities are separate from native source null fields. Formal progress is Root's `4672` total / `1519` resume / Oct5 `+14`; the new query/consumers add no game days. SDK30243 closed exit1 because the separate third death query lacked required arguments; the army query is independently GREEN. Normal SAVE017's exact anchor remains owned by Root, with no peer reread.

The original army leaf was consumed once as a complete buffer: SHA `5e3625acec6b7ee6a6c2e1e94f55b0c6c7c2626ab899981c25583662ff7d372d`. Complete/subtree caches are sealed by `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261005/army-replenishment-current-input-v66/actual-r35-full-data-once/COMPLETE-CACHE-ROOT-DELIVERY.json`, 11828 bytes, SHA `cef8b2eac6584423c56550ef7e79d6f496915e458c7a8421edd1c6cef3e9fb45`. A full-DATA receipt SHA `56edd028aa356b168e25f94203996061a1334d31e94b265ea42b01f0129d1920`; B association receipt SHA `872df23ef9f0b8ce5e8157e8c989196f28243d5a91ed8cf424c239d313f2fb82`; C clock receipt SHA `1022bd4b33580984175bfb6c64aac6bd304252469c9a4c6e25c2e322700087dc`. AI semantics are handed only through the sealed AI subtree to their sole domain owner. The new full DATA and prepared input capability is now **production-live primitive**, with no claim of a completed replenish/recovery action loop.


### R36：当前 DATA 与时钟差异，有限同输入补员条件

2026-10-05，独立 paused `ck3_query_army_strengths` 实际 native3/public2、date53256888、query sequence1；global/scope与三军均available。主军301989997/CArmy201326670 **3480/3878、40团、41 DATA**，供给300/300、月变化0、attrition fraction0.01，状态raw3；guard184549452仍3000/3000、24团/24 DATA，敌268435597仍2843/4702、41团/133 DATA。当前105个ArmyReg snapshot、198条DATA全available，16个count0合法空数组；三军均not_gathering/readytrue/daysnull。主军当前缺额398＝首记录379＋非首记录19；当前上限3878与旧3884明确分开。

按 Army/ArmyReg/persistent FullID/ordinal 和 stored occurrence 关联 R35→R36，198条身份匹配（185未变、13变化）、0新增、1条旧记录不再出现在当前数组。13条保留记录的current合计−34；旧ArmyReg16780830/persistent954/ordinal1的record0为1/6，当前不在数组，故观察算术为current−35、maximum−6、regiment−1、DATA−1。这里记录身份与数值变化，不证明对象永久删除，也不把−35归因为attrition或补员。

当前clock三军available/readytrue：D394037、selected phase17，实际桶仍0/28/6。own/guard/enemy last-success低32日期为53256480/53256432/53256624；相对R35，own与enemy各+720 raw，guard不变。grace anchors仍53251464/53251272/53249376、loaded grace30；原始+188/+190完整64位整数由缓存精确保留。新发布 `merge_supply_destination_weight_raw` 为346700000/300000000/284000000，scale100000；它与当前公共士兵数3480/3000/2843独立，不擅自当作损耗qualified count。

只复用已封 exact .3 native链：`262C6A0` 的prepare检查 `262C700(CReg,CReg+18)` 固定首chunk0，false写prepared+148为0，否则以fresh getter写cache；它不能由任意selected ordinal的同名predicate替代。`262C9D0` 先对prepared F≤0返回false且保留预先零输出；F>0才用独立chunk `2657F10`，整数 `q=trunc0(min(max*F,(max-effectiveCurrent)*100000)/100000)`，ALtrue仍可能整数q0。本帧198条prepared F均为0、fresh getter均为正，所以**若用本帧同值调用core，各条条件q为0**；查询没有实际调用补员动作，不推未来月首重新prepare后的值。`2A98AE0` 已封continuation没有显式末清prepared+148；这不闭合全局writer生命周期。完整attrition qualified count、独立siege contributor及outer `24E3A4D` quarter分支仍由损耗专题owner闭合，未用全军×0.01代替实证损耗。

Outer Root绑定g68/source60a11f657c6e49db165cb79ad23be97343d7a86c、R0036/execbf96fdca-27a3-4413-ae17-b312701f7e6d/PID82512；native query source.game_version/executable_sha256仍actual null，未回填。Root精确正常SAVE：h7877/date53256888/96786421 bytes/SHA5c5ea2fd45d1e7b47c295916246a0f2272d368305629d0551465abceef61ccc2；完整env SHA未给，只有Root前缀feaaa...，不补造。总4690、Oct5+32为Root已有进度，本次读取零新日。

原013完整buffer仅读一次，SHA7a656a671fbe3c2940bf3a20f8ccc1a0e2298350dfb862c57445e6520851deec；完整/AI/clock/DATA缓存 receipt：`Z:/ck3_mod_rewrite_process_assets/g2-resume-20261005/army-replenishment-current-input-v66/actual-r36-full-data-once/COMPLETE-CACHE-ROOT-DELIVERY.json`，11587 bytes，SHA0aabf7376caf107717e447c543ea79d08cfde830843ce6bdf2f20483e93df5e4。A差异receipt SHAae6d2537e674076058996895aa66afabe578a784c82b6a220e2872e275529439；B当前有限条件receipt SHA63b9d5fef16e7e6b0cae608da392bf20ec0ab9ce5519176650c5a8697d51ccbf，source账本receipt SHA2f93d301afd6aef37466aad1c6943cbd1422c9101cecfa87123fafa33f6b9e30；C时钟receipt SHAd15b34e7b55729457e1639a88df0b5b106d538e2bbe37ad6332873ef71ab0ad0。继续保持complete DATA/current inputs的production-live primitive；不授补员恢复loop，0新SDK/source/test/window/Git。
