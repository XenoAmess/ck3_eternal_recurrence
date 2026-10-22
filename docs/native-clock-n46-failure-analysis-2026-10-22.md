# N46 exact-day 时钟失败分析与共享修复边界

`machine_id: xenoamess-full-tower-eb9d2c1186`。分析观察时间：2026-10-22 12:43 UTC。这里只读现存请求回执和源码；没有 Game RPC、Driver/SAVE 正文读取、冻结运行图修改或构建。机器事实只适用于本机本次证据。

## 已证实的失败

场次为 `runtime-a46`，Game PID `50688`。FULL `11543` 在内部 AUTO `11558` 返回错误，原请求不可重放。来源目录为 `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime-a46/p37-responses/`。

| 证据 | 实际值与含义 |
| --- | --- |
| `11558-1-result.json` | 2026-10-22 12:38:41.893001 至 12:39:22.706907 UTC，40.8139032 秒 |
| 原始文件 SHA-256 | `a29abe49623a8da965af385526b2b9a22ad0ed30d321d0ac340d4149fc74d9de` |
| 错误合同 | `xar.exact-day-clock-failure.v2`；`credit=0`，`never_replay=true` |
| 日期 | 起始、最后等待帧均 `53279400`，目标 `53279424`，未观测新增游戏日 |
| 时间状态 | 起始 `paused=true`，最后等待及清理前 `paused=false`，speed `3` |
| 主等待窗口 | 30340 毫秒；heartbeat `11148 → 11270`，122 次，最大间隔 379 毫秒 |
| owner/verified pump | `371716 → 371768`，仅增加 52；最后变化在窗口第 6817 毫秒 |
| observer | started/completed 同为 `1898406187`，`read_in_progress=false`，最后读取可用；主等待后段没有新完成 |
| 清理 | 两次 `pause-map` 都是 `accepted=true/status=submitted`；未观测暂停后态，不能计为成功 |
| 清理尾部 | owner/verified 又到 `371770`，observer completed 到 `1898434734`；有两次回调恢复，仍无暂停或日期推进证明 |

外层 `11543-1-result.json` 记录 8 次 AUTO、7 次 MET、0 次 SAVE，已有 RPC 行合计 63.9075572 秒。其中失败 AUTO 自身约 40.814 秒。该和不含外层后续响应写入等耗时，不能当完整批耗时，更不能据此报告秒/日改善。

结论是：**pipe 传输心跳保持存活，Game owner pump 和快照生产在主等待中后段长期停止推进，暂停结果未知。** 两者必须分别建模。最后约 23.5 秒没有 pump 增长；清理尾部又增加两次，因此也不能将它描述为永久死锁。

## 源码解释与尚未确定的根因

冻结 SDK `src32/xar_autoplayer/bridge/native_driver.py` SHA-256 为 `15a1eca3cee4f79be51a4144258650822e49146c93b7a87257319f848928d06b`。其 `_wait_for_life_advance_snapshot` 等待语义帧；超时返回最近帧。exact-day 路径在该帧仍未暂停时抛错，随后执行原有清理。它没有因为收到 heartbeat 而授予一天成绩，也没有把暂停 ACK 当后态。本次错误不支持通过延长超时、提高速度、重复 FULL 或重提交 UNKNOWN 来修复。

当前仓库共享 C++ 可解释事件生产关系：

- `native_bridge/src/bridge.cpp` 的 `RunConnectedSession` 独立发送 heartbeat，再尝试发布已有快照。worker 活着不要求 owner pump 继续增长。
- `native_bridge/src/main_thread_query_mailbox_v1.cpp` 的 `ObserveMainThreadPumpAndDrainV1` 只接受已核准的 PeekMessage/SDL 返回位置，增加 pump epoch、读 owner stamp、调用 snapshot observer，再推进 verified proof。hook 转发原函数后才进入这个过程。
- `native_bridge/src/ck3_12002_semantic_adapter.cpp` 的 `WorkerAdapter::Observe` 在 owner 内同步读取快照，并分别记录 started/completed。两者相等且 `read_in_progress=false`，没有证据表明当时正卡在 raw snapshot reader 内。
- Native32 passive journal core 的原始 Clone/Delete/Execute/Append 调用保持原有转发；其诊断输出不执行 Game 查询、mailbox 工作或时间命令。现有响应无法证明它导致本次停滞。

上述 C++ 是当前共享源码审查，不自动等于已加载 DLL 的逐文件构建来源证明。审查时 `main_thread_query_mailbox_v1.cpp` SHA-256 为 `2fc9fc6d5b46a5ec0d80d65e2475e160b023a55225bc9c6de8ea78bd83bf9eed`，`ck3_12002_semantic_adapter.cpp` 为 `ba2265b777fe6b52089a23aa5912b9f4cb47e7bfc388245084116852d6b434ba`。下一版资格检查必须重新绑定精确源码闭包、DLL 和实际游戏 EXE。

仍不能区分：原生主线程长任务、原事件泵调用尚未返回、运行时未再经过已核准事件泵位置，或其他 owner hook 阶段停滞。回执明确将 `active_hook_calls`、mailbox `state` 列为 `not_on_wire`，也没有原函数入口/出口与 owner 执行阶段的时间。没有这些证据时，宣布具体函数死锁或归因 Python 性能都超出事实。

## 下一版共享变更

1. 在既有 C++ 事件泵 hook 补充固定容量的原子诊断：hook 入口、原函数返回、owner drain 入口/出口、最后阶段与时间、active calls；经现有 heartbeat 输出。沿用当前线程、EXE、来源和连接身份，不改变原函数转发次数，不加 Game 查询、重试、睡眠或命令。同步带出现有 verified-owner wake 计数和 mailbox state。64 位时间、序号及身份进入跨语言合同后使用规范十进制字符串。
2. 新的故障观察模型和纯分类器用 Java 创建，放入一期共享合同边界；输入先严格校验，再分别输出传输活性、owner 推进、快照新鲜度和暂停后态。缺失、null 和零值分别处理。真实故障固定 `credit=0`、不可重放；尾部恢复少量 pump 不授予继续游戏资格。HTTP 服务存活也不授予 Game 资格。
3. 只有取得具体阶段证据，才修改实际停滞位置的共享 C++。既有原生代码保持其语言，不能将 Java 迁移变成修改 DLL ABI 的借口。当前冻结 SDK/runtime 不热改；不创建新的 Python 模块或 attempt 专用恢复实现。

以上是待执行的下一版方案，**本文件不是修复通过、重启或继续动作的资格**。暂停结果未知时仍需按当前场次受管关闭与恢复合同处置；不能由分类器推断安全。

## 执行真实失败路径的回归

- 固定保留原始 `11558` 响应及其 SHA；Java 测试通过真实入站解析器读取它，断言 transport alive、owner stalled、date unchanged、pause unknown、zero credit 和禁止重放。断言两次 submitted ACK 与末尾两次 pump 都不能变为暂停成功、恢复资格或已保存进度。
- 负例覆盖错误类型（bool/浮点冒充序号）、缺必填字段、错 schema、来源 SHA 不符、连接变化、heartbeat 停止、observer 仍在读取、pump 计数回退以及不同阶段独立采样。不能将非原子观测伪装成同一瞬间的快照。
- C++ host fixture 直接运行实际生产 hook，使用确定时钟验证入口/出口与状态更新；覆盖原函数阻塞、原函数抛出、非核准调用位置、observer 不可用及恢复后再次推进。必须验证原函数原有转发/异常语义和无额外 Game 调用。局部计数器单测不能替代这个闭环。
- 最后对完整新来源闭包完成构建、全部消费者和持久 CI，再在实际 Game 运行。实机分别记录 ACK、native pause/date 后态、完整批耗时与真正新增且保存的游戏日。本分析阶段未执行这些新回归或编译。

## 13:10 UTC 补充：迟到完成线索与最短修复路径

仍为同一 `machine_id`。以下追加不覆盖原 `11558` 失败帧、UNKNOWN 或零成绩。

保留录制元数据 `recording-latest.json` 的帧时间为 **12:43:03.316555 UTC**，SHA-256 为 `146246a12a17689a279aa8d35b6b52d3aad7ddcf5ffb6703776bfefe5289e928`。人工查看其绑定的 `recording-latest-game.png`，画面显示“暂停”和 **1082 年 2 月 16 日**；图片 SHA-256 为 `e2fca40ad8ddf2003d418f8b277500a244894f08e7b319bf70bb053da67118d0`。原 `ROOT-POSTSTART02-game.png` 显示 2 月 15 日，SHA 为 `f50633f64ea1d9bbc51fc5f64fd550919efa3862fb6240cdc4181e61658424c4`。没有 OCR、视频导出或新 Game 查询。录制明确 `hidden_Game_freshness_qualified=false`，所以这是支持迟到推进并暂停的视觉线索，不能追认 native 成功或保存成绩，也不能确定完成的准确时刻。

原 `ordinary-stage-timings.jsonl`（SHA `a4af62b3098b5698f3d16134a6c2380dbad2d1c1e12cd44054c726c7a7687335`）还保留 Game `GetProcessTimes`：从 12:38:42.181964 到 12:39:12.521941 UTC，30.3401168 秒内进程 CPU 增加 **2.953125 秒**；两次 PID/出生时间绑定相同。它证明进程仍有 CPU 活动，不支持“整个窗口一直满载计算”的说法；不能区分原生等待、长任务或具体线程。读取器是冻结 `clock_observation_timing_v1.py`，SHA `34ffbd45381675db60faeb0e36146508cd6234465690d48d7a507ef40e29bda0`。

预检 SEM/CAP 的完整 heartbeat 显示 PeekMessage hook 已安装、SDL hook 未安装，direct-control wake 计数均为零。这只证明预检时刻；故障摘要未保留其后的 wake 计数、mailbox state 或 active calls。owner/current TID 在故障缓存中均为 `247596`，failure 为零、stop=false，不能据此推断主线程未等待。SDK stderr 为空也不能代替这些缺失字段。

源码解释现在更具体：

1. 冻结 `native_driver.py:1897` 将 life-advance 等待默认设为 30 秒。`mcp_server.py:515` 的 native-headless factory 没有覆盖该参数，exact-day 路径使用这个默认值；它适用于所有这类等待，没有“首 unpause”专用宽限。原日志实际等待 30.0034584 秒。该 `mcp_server.py` SHA 为 `3dec1f1f8d78bf1ed546fac429bf8f0e4f025448accbb4608094211a56f45632`。
2. `native_driver.py:25979` 清理先等待暂停，返回后才在 25985 取消原 generation。原日志暂停等待失败，走到外层异常处理，**没有执行取消**。原 `armed_reply` 仍只是先前 generation `1` 的 ACK，不能冒充失败后的 slot 查询。
3. 共享 `tactical_daily_sentinel_v1.cpp` 没有 wall-clock TTL。arm 后保持 armed，直到 cancel 或 native trigger。`XarTacticalDailySentinelHookV1:1013` 在原 final-stage 函数返回后执行 `ProcessTacticalDailySentinelAfterTickV1:795`；到达 target 后在 873 触发 `PublishTerminalState`，经 `PauseAtStableBoundary` 暂停并转 triggered。故“SDK 超时后原 generation 迟到达 target 并自动暂停”在机制上成立。该共享文件与 Native30 构建输入中的同名保留文件 SHA 均为 `25f16c2d21bba1a040abff4bc2876366109dcfdcb70aa9307d7ecc9cbde889a5`；这不补造本场缺失的终态读回。

**下一版优先实现 Java 的迟到结果核对，阶段计数后置。** 已有只读 native step `research-query-tactical-daily-sentinel-v1` 直接读取 slot；已有 MCP `ck3_execute_step` 和 `ck3_take_semantic_snapshot_private_v1` 可承载 status 与新鲜语义帧。需要原 Queue 在 HALT 后提供严格限定的 reader port，由原连接与单一序号/owner 执行；Java 不得另连单客户端 native pipe，也不得重放 AUTO、arm、resume、pause 或 cancel。

Java 在有界、来源绑定的 reconciliation 窗口内核对同一 Game 出生身份、连接、actor/episode、原 arm generation、start/target/speed/mode、triggered 终态及暂停和日期后态。未满足仍 UNKNOWN；满足只产生迟到观测证据，原请求仍零 credit、不可重放。接续必须调用实际共享 reducer 预演，并在原 writer 锁内重验、去重提交；不能由纯分类器授予继续资格。首 tick 的合理宽限尚未实测，不能凭这张晚帧给出准确耗时或无限等待。这样可在同一 Game 内收集迟到结果，不必先重编 DLL 或反复冷启动。

暂停失败后保留 armed 是安全边界，不能直接改成 finally cancel。现有 C++ 回归 `TestGenerationBoundPausedCancelDisarmsAndAllowsNextArm` 明确要求：unpaused 时 cancel 返回 `requires_paused` 且继续 armed，确认 paused 且 generation 匹配后才能取消。迟到查询也只证明新观测，不补证旧 ACK；Java 不取消结果未知的 armed。
