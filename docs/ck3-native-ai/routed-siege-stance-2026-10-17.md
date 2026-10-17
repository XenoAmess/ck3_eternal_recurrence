# 已有完整出发路线的围城姿态

`machine_id: xenoamess-full-tower-eb9d2c1186`。SDK45实际AUTO695因 `native_war_defender_siege_relief_observation_blocked` 没有选出步骤。693军队查询和696独立SEM显示，两支敌军仍标记sieging，却已明确发布去2623的完整路线 `[2623]`；不能继续把它们当作原地围城的静止目标。

公共Strategy仅增加23行：目标可观察、当前省份与目标为不同的合法整数、路线完整非空且终点匹配、明确未战斗及未撤退，才跳过专用静止围城解围预测。敌军仍留在普通完整接触范围，后续必须查询Native horizon；不据此授contact-free、军令ACK、可推进日期或战争结果。缺目标、空／部分路线、错终点、同省份及bool值均保持阻塞。公共其他功能和Driver未改。

正常导入公共源码的三项便携测试、七个否例和一项既有unsafe-route回归通过。真实投影重放使普通 `choose_one_life_turn` 选择四支完整敌军的 `native_war_stationary_contact_horizon` 查询，而不是直接推进。夹具仅保存已完成响应字段与原SHA，不是完整Driver历史。另抽查三项旧siege断言仍RED；恢复A09原函数后同样逐项复现，原断言未改，不能称旧大套件全绿。详见[来源与测试清单](evidence/routed-siege-695-public-transplant-2026-10-17.json)。

## 46启动失败与47健康前缀分开记录

46实际queue exit1／application exit2：启动配方传入正式MCP parser尚未接入的route4／AB参数，应用construct之前即退出。另一CLI支持这些参数不证明正式MCP已支持；这不是Native故障。原stderr与失败退出保留。

47独立薄重试使用同一SDK46业务manifest `ecdde940…`，移除不支持参数，沿既有默认speed3／AB false。Root实际首批健康+2日后开启窗口14，同Game51028和5ebe录像继续；本段只记录该固定健康前缀，不是实时运行指针，也不把启动成功当成695后续接触安全或整场稳定验收。后继正式MCP参数接线候选另审，当前运行端不变。

稳定30年优先，然后<1秒／日，再0.5秒／日，均未达成；G2仍6/8。

## 前批CI的准确终态

原03dfde06的[Official39045432676](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39045432676)失败保留：旧shared acceptance测试绕过构造器后缺少HolySite opt-in字段。外部A09e482d只更正测试夹具、未改生产守卫；其[Official39046231975](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39046231975)和[Linear39046231990](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39046231990)均SUCCESS。后继成功不改写原失败，本695提交CI另行计量。
