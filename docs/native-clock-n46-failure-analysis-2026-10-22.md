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
