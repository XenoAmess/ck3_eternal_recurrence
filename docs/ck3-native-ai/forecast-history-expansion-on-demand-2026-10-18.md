# 预测入口按需展开命令历史

`machine_id: xenoamess-full-tower-eb9d2c1186`，机器身份来源为 2026-10-18T10:56:09Z 的 `tools/ck3_live_run_id.py machine`。本轮只读取仓库源码并跑小合成测试，没有读取或统计 Driver、SAVE、媒体或索引，没有修改冻结 SDK、游戏或编码源。

[`strategy.py`](../../ck3_autonomous_player/src/xar_autoplayer/strategy.py) 的普通规划链原先在围城与普通接触预测入口前分别完整展开历史。这两个入口会先拒绝不适用局面：例如不相关阶段、非移动动作、军队身份不全、没有接触对象或参与者已经战斗中。现在通过可选工厂把完整展开推迟到各自首次历史读取处。原直接列表调用方式保留；相关局面仍完整展开一次，既有顺序、恢复行和原生查询绑定不变。两个消费者继续使用独立列表，没有跨轮缓存或共享可变视图。

2026-10-18T11:36:59Z 的 `BELOW_NORMAL(0x4000)` 单进程结果为 **54 passed, 14 subtests passed in 17.55s**。新增 19 项验证早退不调用工厂、相关接触保留缺失／陈旧查询的重查、当前模型风险拒绝，以及围城评估收到完整 AUTO 展开。实际普通规划调用边界还验证非移动局面只剩其他两个审查器的两次原有展开；本次两个预测入口均不再展开。既有通用预测、正在战斗的一日观察和前项工厂用例一并通过。

不改变策略、查询频率、模拟输入、精度或 Native 守卫。只证明确定未使用的历史物化被移除，未测实机墙钟或 CPU 收益。[精确证据](evidence/forecast-history-expansion-on-demand-2026-10-18.json)与[前项 Raiktor 边界](raiktor-history-expansion-on-demand-2026-10-18.md)分别记录。
