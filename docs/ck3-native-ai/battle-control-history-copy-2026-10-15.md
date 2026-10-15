# 战斗控制查询的无用历史复制（2026-10-15）

N40 P02 两次实际 `query-battle-control-snapshot-v1-100663310` 返回完整合法战斗 DTO，但整体分别耗时 10.916202 s、9.431225 s。其 `normal_plan_turn` 分别为 1.459556 s、0.385442 s；规划返回至完整响应结束还剩 9.455492 s、9.044748 s。两份最终响应仅 270,924 / 271,464 字节，不能把这一执行区间直接归因于巨大 MCP 返回。

来源为同获准 D 根 `continuation40-cold-prep/p02-responses/0029-1-result.json`、`0035-1-result.json` 和通过 Windows share 7 读取的 `ordinary-stage-timings.jsonl`。该日志没有 battle-control Native send/wait/normalize 的独立 timer，因此 9 s 的内部拆分未被实际计时证明。

源码显示 `_execute_battle_control_snapshot_v1_query` 在普通成功路径使用三份快照，fresh-pump 路径增加一份：starting、refreshed、primitive submission、post-current。此前均使用默认带完整 Native command history 的公开快照；同帧 transient retry 也有额外的默认快照。这个函数只消费实际 paused/frame/actor/army/combat 资格，不消费 command history，复制大历史是明确的无用工作。

本次仅将该函数四处 `take_snapshot()`（包括 retry）设为 `include_native_command_history=False`，并为它调用的 `_execute_primitive_step` 传入已有的同名 False 参数。primitive 的 capability、公开 revision、Native revision、原请求发送与等待、结果验证、postcondition 路径均保持不变。实际 battle DTO、独立缓存、正常命令结果记账及原有同帧只读 retry 合同也不变。公开 `take_snapshot()` 的默认行为及其他命令没有修改。

外置运行叶严格基于实际 P03 NativeDriver SHA-256 `bd6d41dc2fa39f8a3ba3b4a23b4b0f74a0e69f854b1f98a28c5ae7dc34b34160`；候选 SHA-256 `c489c5931f2cefb3aadb0c81a59fae4af19a4aad7c5460f2c507307ee0a041f2`。逆变换对比证明除五处参数调整外，整文件完全相同，保留 P03 的历史缓存、事件与 horizon 修复。永久开发树只应用同一个函数的小 hunk，没有复制整份运行叶。

外置十项定向测试运行真实 Driver 候选和完整合成战斗帧，覆盖成功、新鲜 pump、缺 capability、错误公开 revision、actor/frame 漂移、同帧 retry、漂移后不 retry、未知 Native 错误及坏结果。历史复制哨兵全为零，原历史仍保留，最终结果仍正常记账。新 portable 测试覆盖成功/fresh-pump/同帧 retry/漂移不 retry；另更新并验证一个受参数影响的现有 snapshot fixture。这五项 portable 检查通过，未重复旧完整矩阵。

```text
python -B -X utf8 -m pytest -q -p no:cacheprovider tests/unit/test_battle_control_history_free.py tests/unit/test_battle_control_snapshot_v1_bridge.py::BattleControlSnapshotV1NativeDriverTests::test_exact_live_new_pump_rechecks_frame_then_submits_once
```

本次没有改 Native DLL、游戏、录制或其他 Driver 方法。实际性能改善须由同局 SDK 温替换后的完整 MCP 回执验证；现有证据不能宣称已消除全部 9 s、达到 10 ms Native 查询或实现长期每游戏日 0.5 s。
