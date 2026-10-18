# 私有推进等待只读取快照可用性

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-18 UTC 的源码资格记录见外置 `perf-sdk06-ownerresponse01/SNAPSHOT-WAIT-DELIVERY01.json`（SHA-256 `e66dda9b84105a6854a53c35a10c38649de3235ecae350c724876edc21dea06e`）；该目录位于 `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep`。

[`NativeProtocolState.snapshot_supported`](../../ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py) 在原 Condition 锁下复用原快照谓词：已连接、已有语义快照且广告包含 `game.state.snapshot`。私有 `_wait_for_life_advance_change` 只需要这个布尔值，改用该读取后，无需为它生成完整动作列表和诊断字典。公共 `capabilities()` 内容保持原样。

原 Condition 等待、修订与超时校验、最新内部快照、时钟观察和 `finally` 计时均保留，没有减少原生查询、改变游戏策略或放宽后验。源码只能证明每次私有等待少构造两项未消费的输出；墙钟和 CPU 收益未知。

源绑定资格比较了冻结 SDK49 `native_driver.py`（SHA-256 `1173808083bfef752ec1efd43b2555153b3fc9b5c1243e3985c7e1ee3dee48d8`）与修改前公共源码的两个目标函数，函数文本及 AST 相同。外置八项生产函数对比通过；公共测试直接使用当前模块，覆盖 32 种状态、无多余构造、原等待参数、断连或不可用、异常、时钟观察和计时收尾，不依赖外置冻结文件。

2026-10-18T07:36:36Z 读回本次公共 focused 结果：[`test_event_history_free.py`](../../ck3_autonomous_player/tests/unit/test_event_history_free.py) 与 [`test_clock_observation_timing_v1.py`](../../ck3_autonomous_player/tests/unit/test_clock_observation_timing_v1.py) 合计 `26 passed in 5.79s`。当前源码 SHA、测试输出和文件清单封于同一外置目录的 `SNAPSHOT-WAIT-PUBLIC-QUALIFY01.json`；此为源码资格，测试运行时间不是游戏性能数据。

当前 R14 的冻结 SDK49 未修改。本页不声明新补丁已部署，也不将既有窗口均速算作本改动收益。未来 SDK06 须使用其实际来源冻结和组合资格；新 Robert 的 Native 能力及同帧比较不能沿用旧角色的运行资格。
