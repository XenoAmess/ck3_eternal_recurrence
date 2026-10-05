# CK3 1.20.0.3：B合军补给上限截断的实际窗口

2026-10-06记录；原生样本为威廉33388案、1067年4月12日同一暂停点，raw53149344。来源源码7f1db1a773e647b9f31378d4a9ccf57a60cf9e73；exact .3 EXE SHA-256为94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6。前后public/native revision从130/129到131/130，episode为native-33388-23726fbd8a80，游戏日推进0。

这次合军的整数加权值为113.06109，超过合军后实际容量100；原生库存实际读回100，与上限截断精确相符。它可以独立作为合军补给研究，不能把同次B的兵团/统帅条件失败改成比较成功。[精确来源与离线索引](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0175-B-merge-upper-cap/index.json)，[B整体终态索引](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0175-b-gate-stop/INDEX.json)。

| 实际合前角色 | 人数/满员 | 库存 | 容量 | 本次算式使用的权重 |
| --- | ---: | ---: | ---: | ---: |
| 目的军D，public/native0 | 3344/3371 | 126.13988 | 300 | 原生目的角色getter334100000，即3341.00000 |
| 被吸收军S，public204/native199 | 3345/3376 | 100 | 100 | 本军current3345×100000，即334500000 |

S本身的destination getter334300000没有用于S角色；D所有当前人数3344也没有替换D的原生角色权重3341。stock是absolute supply units，不是库存/容量百分比。

## 两次整数截断及实际上限

沿用[已有合军继承树](army-meeting-merge-supply-inheritance-12003.md)和[角色权重只读合同](army-merge-role-weights-observer-12003.md)。在Q=100000、正权重和非负库存这一路径，先逐军算`q_i=floor(w_i*Q/sum(w))`，再逐军算`term_i=floor(q_i*stock_i/Q)`，最后累加并clamp到0..合后实际capacity。

```text
wD = 334100000
wS = 3345 * 100000 = 334500000
qD = 49970 ; qS = 50029
termD = 6303209 ; termS = 5002900
preclamp = 11306109 / 100000 = 113.06109
actual post capacity = 10000000 / 100000 = 100
expected post stock = 10000000 ; observed post stock = 10000000
```

份额和为99999，是逐项整数截断结果，不补成100000；不能简化成普通浮点平均，亦不能相加两军容量、库存或月贡献。实际消费者精确封存Root stagehelper a02的weighted_supply原函数，完整helper34391B/SHA529bf4f1f6f97a52b0ba51f67a47aa79f97c2a10570946f3ac1be2ff139e07ca；纯函数segment SHA12ed9c53ad2f92a6ea8974a2af47da618112c049816eb9f0ab57ae9d02bf42bf。只编译这一纯函数，不导入stagehelper顶层或操作原生。

## 同次B冻结条件没有通过

合军前合计6689/6747，合军后6690/6748。原27个Regiment FullID的完整行均保留，但多出FullID16778273的1/1行，合后总28团；37条DATA的identity及完整行均相同，没有新增DATA。新行的来源和玩家分类未知，不能命名为骑士、补员、死亡或任何应用事件。typed统帅从D27357变为33388；S合前为33388。这里未证明统帅变化或新兵团产生的机制，也不以此推出容量变化的独立因果。

Root正式终态为STOPPED_GATE_INCOMPLETE：共同起点raw53148432、绝对END53150592，+38停止、尚余52日，deadline_reached=false。它是原协议兵团和统帅gate失败后的提前终止，非90日时间耗尽；London_endpoint_metrics为空、arrival_comparable=false、winner为空。此前休整、返程和本次上限窗口仍各有研究价值；不能repair统帅、删去新增行、重置起点或继续推进后把结果冒充原B。[原终态exact JSON](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0175-B-merge-upper-cap/terminal-sources/formal-B-terminal.json)。

Root报告直接审过同暂停点合军原图，见终态里的单帧元数据；本研究包没有读或携带图片/录像，不授clean span、全片1×审阅或成片签核。C尚未取得终点，不能排序三方案赢家。

## 跨机器复核与边界

[消费者](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0175-B-merge-upper-cap/replay_merge_arithmetic.py)与[包校验器](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0175-B-merge-upper-cap/verify_frozen_package.py)只需标准库Python、包内相对路径sources和新输出文件：

```text
<verified-python> -I -S -B promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0175-B-merge-upper-cap/verify_frozen_package.py --output <new-verify.json>
<verified-python> -I -S -B promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0175-B-merge-upper-cap/replay_merge_arithmetic.py --output <new-arithmetic.json>
```

实际12项focused数学/负测通过，包含D/S角色互换、只看cap会掩盖错误、两次截断与浮点均值区别、错误scale/weight/stock、修改helper及来源换字节拒绝。后续formal-terminal新增6项通过，旧12项不重跑；隔离目录校验与数学重放逐字节相同。离线核算不产生新实机、支付账、正常outcome loop、TTS或影片进度。本次actual上限100不外推为其他合军的固定容量；.2 ABI不由本样本赋值，正权重路径不替代零权重/异常分支验证。`open_kaishek`无法覆盖此原生合军/内存ABI，not-applicable。
