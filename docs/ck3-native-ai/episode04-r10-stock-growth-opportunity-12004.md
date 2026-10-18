# B 库存增长：当前最小追加观测

机器 `desktop-3fevhd2-1c74096080`，2026-10-18 UTC 离线复核，仓库读取源 `bc4604bed4eb8558b3f4e0e554a642aa69a4ba2f`。没有 SDK、GUI、游戏推进、构建或主树写入。只读具名小件与 35,034 B 的 R216 portable ZIP；未读存档或完整 Driver body。B 两地仍 **0/2**。

已有正常 S0 有库存增长空间。R206 William 正常源为 72,572,514 B / `aaf7cfc4fef4f22d28ae7d174ffc6642bc586449a3fae9d51b0ba6a45ddb65da`，actor33388，旧 Army/CArmy0，date53147376，1506。Root 本轮路由其库存 116.51751/cap300；R216 视频小审阅在同源显示116/300。Mar31 正常源为74,273,410 B / `42dfd2c0ceb1d004ac7b34d921dee174f86b0c854237d447b173ccbebbd1f0bc`，已在2170，R214/R215画面均103/300。这里103与116是显示读数，不倒造其精确 raw。下一场仍从原件 fresh row 读取 stock/cap 和比例。

最低成本先筛 **2170（Bayeux）**：Mar31 S0 已在当地，可以直接复用下一 R06 的已有 pre-full。它已具低于cap的库存和正常可继续来源，尚无本轮小原件证明当地正月率或 resupply eligible。第二个可定位候选为 **1513**：R216 从 R206 同一正常源已实测一跳7日到达，最后仍显示116/300，但它不是已证增长点。不同 S0 的这两个候选不能拼成同 T0 的正式 B/ABC。1506保留为负率对照：R211在当地实际 callback 的库存0→0，月率−877192/100000。分兵并迁出一支可能改变当地 usage，但两支仍在原省时不能把省级完整 contributor usage 直接除2；其他已计入军队也须保留。目前无法诚实给两个正增长点的概率排序，2170仅因无需新增行军而先读。

源码决定观测时机：`2A9A570` 按 uint32(GameState+9C)%30 选实际存储桶，并在每个原始 occurrence 上调用24E3410；成功的24E4CF0一次加入完整 `current_supply_change_monthly_raw`，**不除30，也不以每月1日为唯一触发日**。它先检查 Unit170!=3、非combat、非gathering、Army5C==0，再要求 signed32(date.low32−graceAnchor)/24 严格大于 loadedGrace。成功后按0与当前capacity钳制。正loaded gain不保证最终rate为正；超限扣减和province component也参与最终值。

R211首帧为 date53147376、storedD389474、当前phase14，Army0只在phase0，graceAnchor53144256、loadedGrace30：elapsed130，严格门槛已经通过，不必另等31天。既有 frozen-bucket 条件选择+16日；真实day16到date53147760/storedD389490/phase0，callback 的 before/after Province均1506、stock均0，更新日期真的变化。它证明这里有自然桶机会和非正库存结果，不证明增长，也不以供给物扣337代库存增长。R216到1513只用了7日，未覆盖该旧+16机会；这也不能反向证明1513没有增长。

[当前机会合同](evidence/episode04-r10-stock-growth-opportunity-12004/QUERY-CURRENT-OPPORTUNITY.contract.json)与[实际增长合同](evidence/episode04-r10-stock-growth-opportunity-12004/QUERY-ACTUAL-GROWTH.contract.json) 分开消费。前者并入下一 R06 已有的同帧 `ck3_query_army_strengths` pre-full，不新增一次查询、SDK或场次；保留原 `observed_history_full_v1` 和原 ordered preparation 模式。读取2170实际 row 的正率、grace、完整省contributors、clock、all30 buckets及source-derived next date/D。下一日应将 **source-derived next D** join到该query的all30桶，不能把当前桶命中当下一日，也不从宿主日历猜D。缺该next pair则unknown。

若该完整row final rate<=0、stock>=cap或 admission不成立，当前没有可直接等待的正增长机会；不为B盲等90日。若正率且有headroom/admission，桶机会仍是条件候选：逐日仅沿原获准 exact-day 流程和独立snapshot前进，不能为了B重Arm。R06只推进Mar31→Apr1；若下一桶不含该Army，就记录“本日未覆盖stock机会”，不为B另加天。

后者只消费已有实际自然callback：新sequence晚于before fence、相同完整Army/native身份、正确完整CDate64、无capture failure、same-instance、event前后均为同一驻留省、stock正差分，并由正常day/claim/clock与完整端点stock链对齐。当前R06 owner确认只regular_core scoped ON，supply journal保持既有OFF；缺叶/null保持unknown，不为B擅开族。若未来已有Root明确捕获机会可满足合同，再调用现有 `comparison/strategy_b_site_growth.py`。一天的troop +10、月界flag、getter正值或条件投影均不能替它。

本包增加的是准确的机会选择输入。它不新增growth正例、不授予future runtime/capacity、不开新场、不改变R06策略。[仓库相对来源与精确pin](evidence/episode04-r10-stock-growth-opportunity-12004/index.json)引用既有canonical原件；原片、Save与大normalized raw未复制。
