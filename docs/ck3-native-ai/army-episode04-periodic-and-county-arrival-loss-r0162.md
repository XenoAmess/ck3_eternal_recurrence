# R0162两条实际扣兵窗口：周期围城减员与县抵达减员

Root受管1.20.0.3实机端点已经观察到两条不同变化：**+5→+6，围城分队170/native161净少31；+6→+9，主队0/native0抵达县1513时净少127。** 本lane只读取Root的独立SDK回执、暂停采样及冻结原生执行树，没有调用SDK、操作屏幕或恢复游戏。下列是端点及源执行链支持的机制判断，不是未见事件/战斗已排除，也不是死亡统计。

## 周期围城窗口（53147280→53147304，实际24raw/ΔD1）

分队170身份、六个actual团ID、max及其persistent/chunk身份均相同。它始终留在1506，空route、movement not_applicable、not_gathering，实际siege6的besieging_army_id=170，assault_in_progress=false。前后源帧精确绑定、paused、同actor33388/episode/pipe/PID/connection_generation/build，端点无event/interaction/combat/retreat。

child实际bucket11，selected从10变11；+188的storage64从300333821678253472变300333868922893992，low32日期从53147040变53147304；+190不变。供给82.99737→74.22545，恰为−8.77192（−877192/100000）。两端高于50，不能讲成低供给或饥饿减员。stock `NSiege.MONTHLY_ATTRITION=0.01`（00_defines第985行），当前getter两端1%；这条应归为**围城背景的周期更新/减员**。

| actual团ID | before→after | 净变化 |
| --- | --- | --- |
| 0 | 1000→990 | −10 |
| 1 | 800→792 | −8 |
| 2 | 100→99 | −1 |
| 3 | 20→20 | 0 |
| 7 | 800→792 | −8 |
| 11 | 400→396 | −4 |

总3120→3089，max3120。31吻合 `floor(3120×0.01)`，也吻合这一数据点各团1%whole人数取整合计。**原生实现仍是先算预算、再按筛选后的团顺序分配，不能把这次数值巧合提升为一般“每团独立乘1%”算法。** 以observed order11/2/3/0/7/1、将不变的20人数团3作为未参与者，eligible总3100和budget31，已闭合的remaining-budget/remaining-soldiers算法逐项精确得到4/1/0/10/8/8。团3为何被筛出，DTO没读definition+2A0，不自行命名其角色或该字段；membership属于有明确标记的重建推断。

此分队每团native_data_record_count=1且唯一chunk可读，首record在这**两个端点**恰好覆盖全部六record；六团两端native_can_replenish与native_chunk_can_replenish均false、chunk身份一致。可讲“可读记录在前后端点都不允许补员”；不能宣称整个未见间隔所有补员入口已关。同期main0仍2540，sea16777220仍1086。

## 县抵达窗口（53147304→53147376，实际72raw/ΔD3）

main0/native0从1506/route[1513]抵达1513/完整空route，state3→regular1，movement权重1980000→0；+188的全64/low32均不变、stock仍82.99737。native selected11→14，main实际bucket0；相同window child170的更新stamp留在+6，人数3089不变。

stock `COUNTY_MOVEMENT_ATTRITION_PERCENTAGE=0.05`（642行）、`MINIMUM_COUNTY_MOVEMENT_ATTRITION=100`（643行）；native24E2400独立经24E2250判定、24E6670计算movement预算，和周期24E3430是两个入口。movement预算计算全部valid actual当前兵数，取比例与modified minimum较大值并cap；24E2559/25E9再按definition+2A0≤0选primary承受者；25F7–2611用有序剩余预算分配，2609调用同一26341B0 soldier writer。完整路径/字节沿用既有exact EXE证据。

| actual团ID | before→after | 实际减员 |
| --- | --- | --- |
| 4 | 800→760 | 40 |
| 5 | 400→380 | 20 |
| 6 | 20→20 | 0 |
| 8 | 100→95 | 5 |
| 9 | 20→20 | 0 |
| 10 | 800→759 | 41 |
| 12 | 400→379 | 21 |

总2540→2413，max2540。预算 `floor(2540×5%)=127`；这不是把每团各自乘5%的结果。以实际order4/5/6/8/9/10/12、将两支20人数团6/9视为未参与者，eligible2500：`127×800/2500→40`，余`87×400/1700→20`，余`67×100/1300→5`，余`62×800/1200→41`，余`21×400/400→21`。五项完整解释127，也解释后两个团多出的整数尾差。

预算、原生筛选/ordered整数规则、边境抵达、stock/stamp未变彼此吻合，支持口播“县移动边界上的另一笔兵员损失”。未直接采样effective movement proportion/minimum modifier、24E2250每个输入或执行hook，仍保留这是源＋端点的具体机制推断。团6/9的+2A0 runtime值未读，不能宣称已证明其游戏语义。

## 同窗海路到达与公开残留行

sea16777220保持相同public/nativeFullID，725/embarked4/route[1506]→1506/sieging3/完整空route；14团及其max/归属不变，人数1086/1087不变，+188不变。可讲该端点窗口海军抵达且净兵数没变，不能推广为海路永不损耗。其getter0→1%是到达后围城上下文变化；不能用这个事后rate倒推海上减员。

公开army roster移除166：before health该行native_carmy_id/current_soldiers/regiment_strengths已经null；其它三actual军的全部27个ArRg FullID/owner/max逐项不变，没有actual团增删/转属。仍按runner在route/state/public-roster边界保存并停止，不盲目继续循环；不能把残留CUnit166消失写成真实团兵被丢弃。海军加入siege6后围城总strength从3089变4175，正好是3089+1086。

建议口播：“围城分队轮到自己的更新时，供给下降，兵力少了31。主军抵达新县时，又出现另一笔127的移动损失；原生先算整军预算，再把整数扣兵分给符合条件的团。海路军同窗已经上岸，这段前后人数保持1086。” 所有数字都是这两个已绑定的暂停端点净变化，采用“兵员损失”，不说“31/127人死亡”。

证据见 `periodic-siege-loss-receipt.json`、`county-and-sea-arrival-loss-receipt.json`，paired extracts绑定Root的sample/result/context精确SHA；失败的初次提取保留，未用于结论。open_kaishek不适用原生执行/实时入口身份。新增laneSDK0、屏幕0、游戏天0、录像0、共享树修改0。
