# 同一次观察的行政发布后重建当前提案

Root 原本只在真正 READ 发布后于同一 writer round 重入。治理 beforeModel 完成行政发布时则退出整轮、重新捕获，再规划。本单元让实际 Root caller 使用一个四参 package overload：原 read flag 为真即短路，否则只由已完成的 Published preparation 请求原 rejoin；Blocked 不循环。原三参循环、每 pass 两次状态重置、writer／冻结退出、original accepted occurrence／source／更新后 Driver 和 current proposal 校验均保，原 deadline 不续。

复用的是同一次真实 packet，故原 cadence marker 去重；下一次真正 Native capture 仍可增加 miss，原三次无动作／30日冷却不改。不同 current occurrence 不能借旧 proposal／lease，原 fresh capture 合法 fallback 仍可重新资格。此行为不是三次不同 fresh capture 的纯等价 A/B，也不以减少检查次数报告收益。

新组合 Test 走真实软件 Native READ／ACK、publisher／CAS、actual collector、生产 Root 四参 helper、原 Planner／Controller；Feast no-action 来自实际 policy 的私 transcript，再由 GovernancePlanCompletion 与原 domain verifier 发布，不手写 Plan。原每 pass ROOT 依赖保留：OPTIONAL_CADENCE 不属于 READ_HISTORY lineage，导入后必须取得新的合法 ROOT。最终按初始 history 前缀及每个真实 Known receipt／contract／kind／request ID／归档原件逐一核对，只选择最后当前 proposal；没有为旧常量1条history／3轮改策略或扩复用守卫。另测同marker／newNative计数、原expiry、producer／flush／replan失败与Blocked。

actual 与 formal 各必要单 TU／6类首0，无新增类型；同一最终 Test10类在两个 Root 前缀上分别完整四项首次4P／0F／0E／0skip、POST输入不变、CLOSE释放。actual ACTUAL1424B／`9b54a8d446c835280af2cd8f968902882ab80d0bcee9f82a15614126d8597497`，CLOSE204B／`09b1e765c7bba4312b70a3ecb880db2c061eed91feb0340abc24d0d95e59c214`；formal ACTUAL1452B／`324c36725f2ddc1c709312f0a8cf5fc47a962185528ef6a25eecf726989db068`，CLOSE204B／`3bff9ee1b63ad46b0433422c4f9941c444ef39cd4ae8f353d4b278e572ba5c16`。原件在 D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/domain-rejoin61-{compile01,whole4-junit01,formal-compile01,formal-whole4-junit01}，机器 xenoamess-full-tower-eb9d2c1186，2026-11-12。

首 Test 同名 lambda 编译RED和错误总数假设的1F完整保留，未运行的跳过ROOT稿未采用；失败TempDir原两行未持，不倒填冻结证据。正式测试仅替换 Root 六类前缀，沿同一已资格 Fixture／domainproducer 闭包；不授未命中的正式 packet／timing 其它路径或私有 Managed／Core 顶层发行。两处生产 edit 来自本地模型完整响应，owner定合同、独立 helper完成真实组合测试；软件和正式发表不授实际分支命中、墙钟收益或10秒目标，不为文稿重启在途动作。
