# 全量持久化的自然增长观测

`machine_id: xenoamess-full-tower-eb9d2c1186`。实际观察时间和源码 SHA 见 [小回执](evidence/persistence-growth-observability-qualification01.json)。本项为软件路径验证；没有读取活跃 Driver/SAVE，没有游戏 RPC，没有实际长局性能验收。

在既有 `XAR_CK3_ARMY_TIMING_JSONL` 启用时，`driver.full_state_persistence` 增加下列标量。日志目的地、既有 stage 与完整写入行为保持原样。

| 字段 | 口径 |
| --- | --- |
| `history_json_bytes` / `history_rows` | 当前锁内已编码 `serialized_parts[1]` 的长度 / 已有历史列表长度；不是 Driver 文件大小，无额外 JSON 编码、hash 或深拷贝。UTF8 子阶段也携带此值。 |
| `persistence_attempt_id` | 复用原 `persist-driver-state:<started_ns>`，连接全量阶段与编码阶段；原 `step` 格式不变。 |
| `full_barrier_reason` | 13 个既有调用点逐一标注；命令记录含原 step，字符串最多 160 字符。标注不增加调用。 |
| `persistence_outcome` / `persistence_error_type` | 原写入函数返回后才标 `write_replace_returned`；原捕获失败分支标 `failed` 与异常类。并非 fsync 保证；无会话时为未尝试。 |
| `full_write_success_count` / `full_write_failure_count` | 当前 Driver 实例启用计时期间观测的成功/失败数；不是全局永久累计。 |
| `timeline_append_candidate` / `candidate_policy` | 仅 `ok and is_life_advance_step(step)` 家族分类，**不是 WAL eligibility**，未检查 exact-day、大小、完整 suffix 或恢复资格。 |
| `candidate_full_write_success_count` | 候选家族的实际全量写入成功数。 |
| `candidate_append_run_length` / `closed_candidate_run_length` | 连续候选全量写入成功数；遇其它成功 barrier 或失败即闭合。延后只读命令本来不写，因此不单独打断；不能据此认定 suffix-only 合法。 |
| `candidate_activation_churn_count` | 上述假设候选 run 的累计起始数；衡量频繁 barrier 造成的潜在激活周转，不是实际 WAL 激活数。 |
| `actual_wal_append_count` | 本生产路径恒为 0；WAL 仍 default-off。 |

计数更新位于已有写锁内。失败不增加成功数，失败后的下一次候选重新开 run；关闭计时后不更新计数。若中途关停/恢复计时，统计只覆盖启用观测，不能当作中间未观测写入也已连续验证。计数不进入 Driver JSON 或保存协议，不改变未知动作不重放、恢复、SAVE barrier、候选或策略。

验证使用真实 `_record_command`、`_encode_driver_state_locked`、`_persist_driver_state` 方法和极小合成历史，写入/日志均为内存 sink。两条新测试覆盖普通 full→连续候选→succession barrier→新 run，以及候选→写入 OSError→候选→关闭计时同 bytes。还执行受静态 reason 参数影响的一条既有婚姻缓存测试。新测试确认每次正常写入只调用一次既有 `driver_state_json_parts`，编码历史字节/行数精确，失败保留 dirty/error。它不证明设备实际写入耗时、长局内存或当前 Game 已采用。

后续只接自然闭批 stage 标量，结合既有完整 wall 账本评估历史增长、全量 barrier 分布及 run 长度。不能从候选数、局部编码耗时或短窗授予长期每游戏日吞吐达标。
