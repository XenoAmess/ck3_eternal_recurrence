# SDK34 Driver 持久化窄候选（未部署）

## 结论

当前重复成本主要是**完整 JSON 文件临时写入**，不是历史 JSON 重复序列化。SDK34 已用 `DriverStateHistoryJsonCache` 增量缓存历史；在先前固定的 P32 和平 288 日窗口，52 次 Driver 全态持久化共 38.726398 秒，其中 JSON 序列化仅 0.026660 秒，完整字节拼接 1.185337 秒，临时文件写入 36.837887 秒（全态持久化的 95.1%）。重做 JSON 编码没有可见收益。

本包把既有、默认关闭的 WAL29 实验闭包**逐窄补丁重基到 SDK34**：只改 `native_driver.py` 和 `native_session.py`，新增既有 `driver_state_wal_v1.py`。既有成功 `life-advance`（包括本窗口 8 日推进）在显式开启后可将新增完整历史行及全部非历史字段写入原子小 journal；SAVE、普通全态 barrier、正常关闭仍回写原 v2 全态；旧冷读者遇 active v3 sealed base 明确拒绝。默认关闭时继续原 v2 写入。游戏强度、宣战、事件、90 日 SAVE、未知 ACK 的业务判定代码未变。**这是离线候选，不是 SDK34 实机提速结论，也没有热装。**

## 原生产链和消费者

- `sdk-p34-candidate/src/xar_autoplayer/bridge/native_driver.py:9083–9130` 的 `execute_step` 取得实际结果后调用 `_record_command`；后者在 `:10688–10782` 将完整原结果复制进历史。成功只读查询已有 deferred 分支，建设完成回读仅在有完整 `in_progress` 证据时 deferred。
- `_persist_driver_state` `:11633–11807` 在写锁与状态锁内冻结非历史字段、增量编码完整历史，然后原子替换 `native-session/driver-state.json`。`_encode_driver_state_locked` `:11105–11155` 的 warm history cache 已避免每次重新 `json.dumps` 旧行。
- P32 52 次写入中，37 次是日期推进；6 次建设回读实际均为 `status=unavailable / completion_status=unobserved / postcondition_verified=false`，不能用现有“已验证在建”规则跳写；另有 SAVE、事件和只读拒绝。仅把这些未知/失败回执当作可忽略 noop 会损失原始失败证据。
- 冷消费者仍按完整 `format_version=2`、checkpoint/history 绑定恢复；候选 active journal 使用 `format_version=3` sealed base 防止只复制旧基线时静默接续。`native_session.py` 的冷 checkpoint 验证对 active journal 拒绝；相同进程恢复读完整 base+journal 后立即全态 barrier，跨 PID 冷迁移须先在已关闭目录 materialize v2。SAVE 与正常关闭是全态 barrier。

## 测量与限制

已封存 `p34-hot-sdk-prep01/TACTICAL-FULL-HISTORY.json` 7,108,891 字节、550 行，SHA-256 `c37b7f60398f18901a1b01a3c11494d9b0da4ebfc34d33b03656b6cefa05c189`。使用其原始历史加一条**真实已完成 P32 八日推进回执**作离线存储夹具；完整下一态 7,106,335 字节，单个 journal 1,787 字节，`replay` 后完整 v2 字节 SHA 精确相等。首次启用要额外生成约 7.1 MB sealed v3 基线，此次无小写入收益；连续 journal 才能减少完整写盘。现有 warm cache 对该夹具批量墙钟约 1.14 毫秒/次，而 journal 编码约 0.042 毫秒/次；Windows `process_time_ns` 对短调用以 31.25 毫秒粒度跳动，不能据此声称精确单次 CPU 节省。完整 JSON 从头编码 44–49 毫秒/次是**旧路径对照，不是现有 SDK 的常规成本**。所有这些是内存/字节离线测量，未测试实际游戏或 HDD 写盘时间。

按 P32 原回执顺序，37 次成功 `life-advance` 中，若每个其他全态写入都保留 barrier，预计 14 次位于 barrier 后首次激活、23 次为连续 journal 追加。这 23 次在未启用时全态持久化合计 16.848707 秒，即**理论最多 0.058502 秒/游戏日可削减**，还须扣除 WAL 激活、journal 原子写、校验与 barrier 成本。不能把 37 次全部算成收益，也不能宣称该候选已经把 1.041361 秒/日降到 1 秒以下。

## 验证与交付边界

`test_p34_wal_candidate.py` 的 7 项聚焦测试通过：默认关仍 v2、两条真实八日回执完整重放、连续 journal/基线 stat 篡改拒绝、缺段/乱序/截断/外部基线拒绝、旧冷读者拒绝 active journal、离线 materialize、SAVE 回执和正常关闭全态 barrier。`git apply --check` 对 SDK34 两叶均通过，正向补丁和反向候选核验均通过。新增输入没有复制 7.1 MB 原夹具，整个私包约 1.75 MB，低于 16 MiB 上限。

若未来考虑开启，先审 Root 当前直接读取或复制 Driver state 的入口是否在 active journal 时明确失败；随后在受控 SDK 代际验证实际 `full_state_temp_write_bytes`、journal 写入墙钟与完整冷恢复，失败只可在正常关闭/离线 materialize 后返回 v2。当前稳定 SDK34 与 Game/OBS 保持原样。

精确叶 SHA、SDK34 基线 SHA、补丁 SHA、测试和夹具见 `DELIVERY.json`；离线数值见 `BENCH.json` 与 `WAL-BENCH.json`。
