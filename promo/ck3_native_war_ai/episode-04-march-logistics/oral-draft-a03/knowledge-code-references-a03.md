# a03知识、代码与来源

本稿所有知识/代码引用使用公开固定commit，未入库的R0173暂用包内相对事实摘要。没有原片、截图、原游戏响应、save或二进制资产的新副本；原位置仍由Root保全。本文件不配音。

## 已入库知识

| 用途 | 固定来源 | 结论范围 |
| --- | --- | --- |
| 原生中文与单帧权限 | [TERM专题][terms]、[R0169索引][term-index] | 原始固定清单11/11，各自编码10/11；Root8单帧已审/16未审，新锁定原图encoded=null，不等于整期研究或成片完成率。 |
| 补给恢复/实际补员 | [补给与容量][supply]、[完整补员记录][refill] | R0164独立+14→15 stock291.22808→300仍1086/1087；R0165独立+20→21仅53 actual9→10、总1087，非一段无缝现场。 |
| 合军 | [R0168同暂停实际合军][merge]、[执行继承][merge-tree] | 完整27团6746/6747，fixed两stage116.51751/cap300；nonclamp，upperclamp仍pending。 |
| 周期与县界旧窗口 | [R0162实证][r162]、[周期时钟][clock] | 周期child净−31、县抵达main净−127各自时间/身份；不合成饥饿、死亡或完整事件账。 |
| 当前县域条件/预算 | [R0171正式专题][r171-doc]、[正式摘要][r171-summary]、[输入ABI][county] | Jan20/0新增日、236条件预算、front725/mode1/false，full27/37不变；不称已扣236。 |
| 更新与路线边界 | [R0172正式专题][r172-doc]、[索引][r172-index]、[有条件整数复核][r172-analysis]、[登船/登陆边界][r172-boundaries] | +15→17净−67/stock−6.14035/clock stamp53147760；资格和applied/refill ledger未知。+30→32与+42→44整数不变，landing许可需新基线。 |
| 月收入/净额/军费 | [R0168 true NET][cash] | Jan11月净额+0.29948=4.69417−4.39469，已包含军事；current3.88749/allraised4.87050分开，非未来上限或累计付款。 |

R0172知识与35-file包正式提交 `3e2737b5909616cd2ab301da59352250410bafb8`；Root/整合lane记录对应官方CI `37307724065 SUCCESS`。本lane只核已保存提交导出与收据SHA，没有新增Git或CI调用。TERM固定提交 `accc385ecb4086f8912cd9492f95e049c8065f7d` 仍保留其原门槛和单帧权限。

## 可复用代码

| 层 | 固定源文件 | 作用边界 |
| --- | --- | --- |
| 原生查询 | [Strength reader][reader]与[exact .3 binding声明][bindings] | CUnit/CArmy full代际/backlink；当前库存/容量/月变化/首边/县域输入。生产文件名含12002，不表示把新增.3getter外推到.2。 |
| JSON投影 | [共享serializer][serializer] | raw与scale100000原样；integer soldiers scale1，合法0/false与unknown分开。 |
| 完整补员数据 | [DATA reader][refill-reader] | 实际团Strength与DATA记录域不同，无record不能当0实际士兵。 |
| Python合同 | [county normalizer][county-python]与[war contract][war-python] | keys/source/scale/当前人数一致性，false不改unknown，unknown不补0。仅读当帧，不生成执行损耗/支付ledger。 |
| 便携复核 | [TERM verifier][term-verifier]、[R0172 verifier][r172-verifier] | bytes/SHA、join、cohort、有条件算术；离线检查不是新的游戏执行或人工signoff。 |

这些源码由Root实际R0171/R0172来源绑定到 `7f1db1a773e647b9f31378d4a9ccf57a60cf9e73` 与a08 DLL，EXE exact1.20.0.3。查询自身version/hash实际null保持不变；独立build/session来源不回填成payload字段。本包只沿用已核文件pin，不新增调用getter、编译或测试EXE。

## 数学说明（编辑卡可用）

R0168正权重样本：D weight_raw566000000、S吸收角色weight_raw108600000、总674600000；库存分别raw8299737、29122808；scale100000。两stage向零截断：

```text
shareD = trunc(566000000*100000/674600000) = 83901
shareS = trunc(108600000*100000/674600000) = 16098
contribD = trunc(83901*8299737/100000) = 6963562
contribS = trunc(16098*29122808/100000) = 4688189
post_raw = min(6963562+4688189, actualcapacity30000000)
         = 11651751 = 116.51751
```

share和99999不补齐、不归一、不改一次浮点平均。D weight本例等于5660×100000不推广为所有目的军；S不得误用自己目的角色字段108100000或postweight。capacity由postgetter读300，不相加/平均或由quality猜。实际preclamp<capacity，upperclamp未实证。

R0172两日窗口 raw53147736→53147784 / public40native39→public45native44：6746→6679，27actual/37DATA身份顺序/max不变，16actual与17DATA整数下降，有条件有序回放matches。stock11651751→11037716；before月getter−877192、after−614035，供给stamp53147040→53147760（stamp间30日不是窗口过30日）。执行时rate未记录，aftergetter不补成已执行参数。两端供给远高于严格<10，supplybudget0，不是饥饿；actual applied/refill ledger和零隐藏补员未知。

R0171 UI赴利雪43days/Mar4来自包内 `sources/r0171-ui-eta-observation.json` 的Root审图事实摘要；首边30days由正式R0171输入支持。两范围不同，不用43−30生成后续精确时间。该摘要不携带截图，原图hash只保留来源，不向机器外扩大媒体分享。

## 未入库R0173事实摘要

[包内半分摘要](sources/r0173-half-split-facts.json)使用Root已提供的总结和动作绑定，不是原游戏packet。原JSON和完整检查继续原位置保留；未来master包pending，本文不制造公开来源已发布事实。

Mar5/raw53148432，从Jan20/raw53147376起+44日，actor33388/episode `native-33388-930004d2d2a0`；同pausednative2/pub3→native3/pub4。Main public/native0为3337/3371、15actual/25DATA；新public204/native199为3342/3376、12actual/12DATA。完整27actual/37DATA逐ID不变、disjointunion守恒；库存两军均11037716，capacity30000000/10000000独立读，childstock>capacity不改写。两军当前monthly均−423728/100000，仍同2174；clock历史stamp/anchor复制，不推新grace。当前统帅unknown；两军分开恢复与futureclamp均pending。

1506只写编号，不称London；Root London目标1527。Unit190 reference_absent保持unknown，不命名运输类型或0士兵。R0173子军public204/native199不混R0169的33554436；R0164/65与R0172/73使用不同相对日期基准。

[terms]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/accc385ecb4086f8912cd9492f95e049c8065f7d/docs/ck3-native-ai/army-logistics-native-terminology-12003.md
[term-index]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/accc385ecb4086f8912cd9492f95e049c8065f7d/promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0169-terms/index.json
[term-verifier]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/accc385ecb4086f8912cd9492f95e049c8065f7d/promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0169-terms/verify_portable_evidence.py
[supply]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/7f1db1a773e647b9f31378d4a9ccf57a60cf9e73/docs/ck3-native-ai/army-current-supply-capacity-attrition-12003.md#L248
[refill]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/7f1db1a773e647b9f31378d4a9ccf57a60cf9e73/docs/ck3-native-ai/army-regiment-replenishment-raised-reserve-12003.md#L547
[merge]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/7f1db1a773e647b9f31378d4a9ccf57a60cf9e73/docs/ck3-native-ai/army-merge-r0168-no-tick-weighted-supply-12003.md
[merge-tree]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/7f1db1a773e647b9f31378d4a9ccf57a60cf9e73/docs/ck3-native-ai/army-meeting-merge-supply-inheritance-12003.md
[r162]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/7f1db1a773e647b9f31378d4a9ccf57a60cf9e73/docs/ck3-native-ai/army-episode04-periodic-and-county-arrival-loss-r0162.md
[clock]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/7f1db1a773e647b9f31378d4a9ccf57a60cf9e73/docs/ck3-native-ai/army-monthly-update-order-12003.md
[r171-doc]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/3e2737b5909616cd2ab301da59352250410bafb8/docs/ck3-native-ai/army-county-entry-current-inputs-r0171-runtime.md
[r171-summary]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/3e2737b5909616cd2ab301da59352250410bafb8/promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0171-county-inputs/summary.json
[county]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/7f1db1a773e647b9f31378d4a9ccf57a60cf9e73/docs/ck3-native-ai/army-county-entry-current-inputs-12003.md
[r172-doc]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/3e2737b5909616cd2ab301da59352250410bafb8/docs/ck3-native-ai/army-r0172-periodic-siege-loss-runtime-12003.md
[r172-index]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/3e2737b5909616cd2ab301da59352250410bafb8/promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0172-periodic-loss/index.json
[r172-analysis]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/3e2737b5909616cd2ab301da59352250410bafb8/promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0172-periodic-loss/periodic-analysis.json
[r172-boundaries]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/3e2737b5909616cd2ab301da59352250410bafb8/promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0172-periodic-loss/neutral-boundaries.json
[r172-verifier]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/3e2737b5909616cd2ab301da59352250410bafb8/promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0172-periodic-loss/verify_evidence.py
[cash]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/7f1db1a773e647b9f31378d4a9ccf57a60cf9e73/docs/ck3-native-ai/war-cash-net-live-r0168-2026-10-05.md
[reader]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/7f1db1a773e647b9f31378d4a9ccf57a60cf9e73/ck3_autonomous_player/native_bridge/src/ck3_12002_army.cpp
[bindings]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/7f1db1a773e647b9f31378d4a9ccf57a60cf9e73/ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12002_army.hpp
[serializer]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/7f1db1a773e647b9f31378d4a9ccf57a60cf9e73/ck3_autonomous_player/native_bridge/include/xar_bridge/army_strength_v1_serializer.hpp
[refill-reader]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/7f1db1a773e647b9f31378d4a9ccf57a60cf9e73/ck3_autonomous_player/native_bridge/src/ck3_12003_army_replenishment_records.cpp
[county-python]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/7f1db1a773e647b9f31378d4a9ccf57a60cf9e73/ck3_autonomous_player/src/xar_autoplayer/bridge/army_county_entry_inputs_contract.py
[war-python]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/7f1db1a773e647b9f31378d4a9ccf57a60cf9e73/ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py
