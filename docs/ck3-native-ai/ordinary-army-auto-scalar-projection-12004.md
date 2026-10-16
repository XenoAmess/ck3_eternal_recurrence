# 普通自动回合军力查询的标量投影（1.20.0.4）

普通 `auto_turn` 军力查询只消费完整军队 scope、标量军力和同帧状态，却曾为每支军队归一化全部富 manager 子树。私有 AUTO 路径现在校验并返回所需标量；显式 `query-army-strengths-v1`、指定 `army_ids` 的查询，以及行动后的军力回读仍使用完整归一化和原合同。私有入口拒绝指定 `army_ids` 或非 `ordinary_core_v1` profile。

该投影保留查询的完整 ordered scope、字段类型与值、native/public revision、connection、actor、episode、日期和 snapshot 绑定、原始 command history 与缓存隔离。AUTO 不再执行富 manager 跨子族一致性校验，因此该优化仅适用于普通 AUTO 的已知标量消费者；显式查询继续提供这项校验。它不改变战争接敌、行动准入或战果确认。

同一 19 支军队场景的已完成实机回执：P11 两次完整 Army RPC 分别为 2.986666 与 3.476177 秒，其中归一化分别为 1.996572 与 2.614423 秒；P13 一次和 P14 七次使用相同三份性能源码，合计 8 次 RPC 中位 0.925924 秒、归一化中位 0.000290 秒。P14 单独七次 RPC 中位 0.964014 秒、归一化中位 0.000277 秒；Native pipe 等待中位 0.530188 秒，普通规划中位 0.367792 秒。这说明归一化热区已被实际消除，整条查询仍受 Native 等待与规划影响。P10 的 50 次中位 6.397431 秒受旧家庭机会查询混杂，不作为同条件收益比值。逐回执 SHA、分段时间及源码 pin 见外置 `D:/codex-ck3-demos/2026-10-14-robert-30year/p31-army-p13-actual01/P13-P14-ARMY-ACTUAL.json`（首次 8 样本 SHA-256 `9cc2c17e5e13c35a4905438c4c386d164b360c7fe935f5ce8cbd9b68548fe851`）。

回归覆盖真实合成 Driver/Service AUTO、同帧回执、缓存别名隔离、显式富查询仍完整，以及畸形标量零业务动作拒绝；新测试 2 项、相关现有测试 10 项通过。实机结果属于 P13/P14 已完成查询，不能外推为整段录制吞吐或所有 Army 子能力的验收。
