# 原版AI经济建筑评分的不同输入链

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-25 UTC恢复工作后的有限静态研究，冻结CK3 1.20.0.4 / build25734779，EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。只读取八份具名stock脚本及既存研究，不连接Game、不读EXE、不修改策略。这里扩展resume60的`CONSTRUCTION-SCORE-WAR-SOURCE03`中明确未展开的trigger依赖，不重复授予其旧结论新实机信用。

## 原版候选、排序和负担检查目前能证明什么

当前`common/buildings/_buildings.info`声明：先收集potential building列表，包含domicile building，排除holding和Great Project等；计算所有候选ai_value并排序，保留距最高分20%范围的候选，随机选择后才判断可负担，不能负担则开始存钱。它还警告过高分昂贵建筑可能让AI长期存钱，放弃改善经济的投资。

这是作者接口说明，不能单凭它证明actual4真实native cache、候选producer、最终浮点/MTTH语义或调度cadence。此前保留的170字节caller从命令构造才开始，上游695字节前缀仍待唯一mapper取回；没有把每日、每月、建筑完工或钱包改变猜成已证重算触发。`buildings/*.txt`中搜索`ai_potential`无字面命中只对这个源目录成立，不能解释为引擎无potential筛选。

玩家GUI的潜在/失败显示由`can_construct_potential`、`can_construct_showing_failures_only`、`can_construct`等控制。原版AI评分、GUI缓存和我方亲持领地世界扫描分别记录；原生合法性函数可用并不等于完整原版候选搜索已复刻。

## 新展开的一期经济与升级经济分支

`00_standard_economy_buildings.txt`的farm estate两级使用不同输入，不可把一个“偏好经济建筑”布尔字段代替全部评分来源。

| 评分分支 | 实际来源和语义 |
| --- | --- |
| `farm_estates_01` | base15，一级首都奖励、一级经济偏好、文化修正、general、economy directive，以及同时满足watermill/windmill terrain条件的factor2。文化/地形闭包未在本包求值，不给最终总分。 |
| 一级经济偏好 | `ai_tier_1_economical_building_preference_modifier`加5的条件是holder经济繁荣personality，或`ai_desire_economy_buildings`角色flag。 |
| `farm_estates_02` | base9，general、economy directive及另一种`ai_economical_building_preference_modifier`；`free_building_slots>0`声明factor0。该来源不能被解释为原生合法性false。 |
| 升级经济偏好 | holder的`ai_rationality>=25`，或wealth/domain的focus-or-trait，或当前income小于三倍expenses时，添加`ai_economic_preference_value`。后者从1开始，在holder首都且无空槽时加1，有tax assessor且无空槽时再加1。 |

新追到`00_lifestyle_triggers.txt::has_focus_or_focus_trait_trigger`的wealth/domain分支：实际focus和对应lifestyle trait是备选，wealth接受`avaricious`，domain接受`architect`。仅读取当前focus指针会漏掉原版明确声明的trait分支。与之不同，下面economic guts中的domain条件直接使用`has_focus`，不能给两者套同一个简化判断。

`00_ai_value_triggers.txt::ai_has_economical_boom_personality`具有多条OR来源：Civilian/building行政契约flag、家族focused-on-economy modifier、economic guts且warlike personality=false、属国/非独立者的overlord经济法令，以及creation家族aspect。其外层NOR排除conqueror变量和destruction/serenity/trickery aspects。这是定义中的角色personality，不是“当前没有战争”。warlike personality本身读取契约、家族、特质、AI性格、政府/文化、远征变量、overlord法令等；本包不推断当前任何角色走哪一枝。

`economical_ai_guts_trigger`要求`ai_boldness>0`，并满足domain当前focus、calm/patient/diligent/generous/stubborn/profligate或city/castle builder modifier中的至少一项。最后的`NAND`包含greedy、impatient、家族organized-for-war三项：它排除这三项同时满足的组合，不能误写成任一项即排除。该分支是本轮新增的具体依赖闭合，不创建另一个评分实现。

## Directive分数有明确AI边界

economy directive加10不仅检查`vassal_directive_building_focus_economy` flag，还调用`vassal_is_valid_and_follows_directive_trigger`。后者明确要求非top liege、landed、至少county、`is_ai=yes`，再调用valid与follows两条共享trigger。

valid要求实际vassal-of关系，且不与liege为rival、不与liege交战、没有disloyal特质；当前administrative分支与else都检查vassal-of，不能凭注释猜出额外例外。follows要求administrative、对liege意见至少50、trusting/loyal、friend/lover、强hook、指定perks、crown/church authority3或legitimacy至少5等任一分支。

因此把directive flag直接变成玩家建造评分+10会丢掉原版AI限定及服从语义。这里只记录差异，不给玩家增添AI限制，也不修改其已授权建设策略。被liege宣战这条关系阻断与角色参与其他战争不同，不能合并成“所有战时directive失效”。

## 战争资金与当前bridge的边界

此前已证general modifier仅在conqueror变量与gold不高于safe-spending阈值组合时扣1000，safe-spending声明为两倍war-chest maximum；它不是“正在战争就减1000”。native war-chest maximum实际来源、与建设saving bucket的连接及最终可负担caller仍未知。原版18个月war-chest define不能替换我方已实现的24个月/400金币强储备。

我方bridge目前先按authored收入净增量与实际费用选玩家候选，再通过当前财务、current/all-raised月预算、应急雇佣和原writer重验。它没有自动采用上述personality、directive或stock随机排序。没有同帧原生候选/score及端到端结果，不声明它与原版相等、更优或更快。

## 新定位的调度声明与预算类别区别

`defines/ai/00_ai.txt`1–98声明short/medium/long/rare/strategy五类按tier分组的重算间隔，并列出每tick最少128个task、通常cap192和load balancing允许的最大staleness8天。以数组中公爵位置为例，声明值分别为7/30/60/180/180天；这个位置沿同文件显式标注Unlanded、Barons、Hegemony的tier顺序读取，不是本轮原生enum资格。尚未找到建设task的实际class/注册/调度caller，因此不能把其中7天或8天直接写成建设重算周期或cache寿命，也不能声称金币改变会立即重算。

114ff的`BUDGET_CATEGORY_SHORT_TERM_MIN`声明的是低于短期gold/treasury阈值时，对其他类别支出/存钱更犹豫，其数组为25/25/200/200/400/400/400；它与另一个`MIN_WAR_CHEST`的25/25/50/100/200/300/400不是同一字段。spiritual head/holy-order还分别声明gold或treasury保留额。不能根据相同数值把short-term min、角色reserved gold和war chest合并成一个native预算字段，也不能把current wallet当作各bucket余额。

同源图由`D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/construction/ai_investment02/research-plan02.json`生成到`research-graph02.md`；八文件精确SHA与来源层在plan中，01原件保留。图把源码声明与actual4 native边明确分开。下一有限入口仍是695字节前置caller；只有取回并核实际调用/比较/成功边后才继续定位候选producer或重算写入，不追callee扩大采样。这个研究不列为首场前置，不扩退款专题，也未改我方policy。
