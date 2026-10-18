# Raiktor 审查按需展开命令历史

`machine_id: xenoamess-full-tower-eb9d2c1186`。机器于 2026-10-18T10:56:09Z 通过 `tools/ck3_live_run_id.py machine` 核对。本轮只读取工作仓源码并执行小合成测试，当前游戏、冻结 SDK 和视频编码源未修改。

[`choose_one_life_turn`](../../ck3_autonomous_player/src/xar_autoplayer/strategy.py) 原先在调用 Raiktor 消费者前立即展开全部命令历史。消费者却会先根据暂停状态、窗口、CB、战争身份与强制要求优先级返回；这些路径根本不读取历史。现在调用方传入延迟工厂，消费者只在原本首次读取历史的位置调用它。无关局面不展开；相关局面仍得到原 `_expanded_command_rows` 产生的完整列表一次。

消费者既有 iterable API 保留，直接调用方不必提供工厂。该改动不缓存、不截取历史，不改变查询频率、优先级或战争选择。恢复后的历史边界、当前帧查询资格和未知终局提交的防重条件保持原样。普通 Driver 仍在同一次内部规划的原历史锁下持有稳定输入；工厂不跨轮保存。

2026-10-18T11:31:06Z 完成一次 `BELOW_NORMAL(0x4000)` 单进程验证：新工厂 17 项、原消费者 7 项，以及合并后前两项 NativeDriver／最近索引回归 39 项，共 **63 passed, 6 subtests passed in 17.02s**。无关帧工厂调用为 0；相关帧为 1，计划输出与完整预展开输入一致。实际普通规划入口另验证已到下一个消费者边界而未提前展开，相关查询则保留完整 AUTO 展开。

减少的是确定未使用的 Python 历史物化；没有本轮实机墙钟、CPU 或编码速度收益测量。精确来源与资格见[证据](evidence/raiktor-history-expansion-on-demand-2026-10-18.json)。
