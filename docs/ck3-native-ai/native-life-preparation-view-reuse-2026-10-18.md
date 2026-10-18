# 普通时间推进准备阶段复用同一视图

`machine_id: xenoamess-full-tower-eb9d2c1186`，机器身份由 `tools/ck3_live_run_id.py machine` 于 2026-10-18T10:56:09Z 实际读回。源码基线为 `646972a2`；本次不读取游戏、Driver、存档、媒体或索引，也不修改冻结运行树。

[`_execute_life_advance`](../../ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py) 原先相邻两次构造完整 `state.capabilities()`，分别取动作列表和原生能力。现在这两项取自同一次受 Condition 锁保护的返回值。结果窗口时间上限的较早读取，以及最终动作能力守卫，仍在原位置执行。基线源码的该准备链有三次状态能力读取；当前生产函数的合成链观测到两次，返回对象没有被修改。

同一函数还会在 `_history_lock` 内先恢复开放强攻生命周期，再调用未知强攻检查；后者原先再次恢复相同历史。现在传入刚生成的列表，仅在此次锁持有期间复用；独立调用未提供该参数时仍走原恢复路径。没有跨轮缓存、截断历史或改变恢复后的索引。空列表也直接复用。上一强攻推进失败的额外查询及所有未知强攻拒绝保持原样。

低优先级 Python 实际读回 `BELOW_NORMAL(0x4000)`。两个 focused 模块于 2026-10-18T11:05:13Z 核对为 `16 passed, 6 subtests passed in 2.32s`：完整时间推进／原生日截止合成链保留一日后验、零日弹窗中断和一次 resume；八种历史覆盖 Start、Stop、失败 Stop、成功／失败恢复、包裹 AUTO、失败推进和空历史。复用前后未知强攻输出相同，历史、快照和已恢复列表不被修改。

精确来源、调用数量、测试命令与机器记录见[证据](evidence/native-life-preparation-view-reuse-2026-10-18.json)。这只能证明减少重复 Python 构造与历史恢复，墙钟和 CPU 收益仍未知；测试耗时不能作为游戏性能数据，既有战役均速也不归功于本改动。
