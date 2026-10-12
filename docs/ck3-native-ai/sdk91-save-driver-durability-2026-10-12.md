# SDK91 SAVE 与 Driver 持盘边界：源码审查

SDK91 冻结来源为 `50a1a5451227d1b30f42394dd02ddfbaea26a1ff`。本文复用 Source24 的 593 行具名源码窗口及四路静审，记录 SAVE 与 Driver 持盘的现有合同。R103 的实际 SAVE、关闭、完整 13-stream freeze 和恢复事实仍以原生产回执为准。

Source25 的原始有限工作包为 `sdk85-source-preparation/sdk86-candidates/g2-driver-save-durability-source25`，位于本轮外置输出根。它沿用原 4 GiB 父准入、64 KiB source/output 配额及复核期限 `2026-10-12T16:47:28.264315+00:00`，未续期。本文未实现新 Driver 功能或改变容量模型；Root 全文静读后整合。

审查来源为以下外置 SDK91 文本。下列行号均对应这份冻结树，不能自动视为后续 master 的行号。

- `D:/codex-ck3-background-spill/ck3-sdk91/ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py`
- `D:/codex-ck3-background-spill/ck3-sdk91/ck3_autonomous_player/src/xar_autoplayer/bridge/service.py`
- `D:/codex-ck3-background-spill/ck3-sdk91/ck3_autonomous_player/src/xar_autoplayer/environment.py`

**SAVE 会尝试完整持盘，但 `checkpoint.saved` 不是 Driver 持盘成功回执。** [service.py:4462](/D:/codex-ck3-background-spill/ck3-sdk91/ck3_autonomous_player/src/xar_autoplayer/bridge/service.py:4462) 的 `save_checkpoint` 调用共享 `execute_step("save-checkpoint")`，并只检查返回的 `checkpoint` 是否为字典。服务的共同调用在 [service.py:4440](/D:/codex-ck3-background-spill/ck3-sdk91/ck3_autonomous_player/src/xar_autoplayer/bridge/service.py:4440)。

原生保存分支先提交保存、等待游戏 checkpoint materialization，再在内存中更新 `_last_checkpoint`、episode 绑定、预定 `history_index = len(_command_history) + 1` 和 rollback scope，随后建立 episode seed 并返回；见 [native_driver.py:11542](/D:/codex-ck3-background-spill/ck3-sdk91/ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py:11542) 至 11609。该 history index 是保存时预定的历史关联，尚不是已持盘的 sequence 证明。

共同执行尾在 [native_driver.py:8621](/D:/codex-ck3-background-spill/ck3-sdk91/ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py:8621) 调用 `_record_command(step, ok=True, result=result)`。记录器深拷贝完整 result、追加历史并设置 dirty；见 [native_driver.py:10163](/D:/codex-ck3-background-spill/ck3-sdk91/ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py:10163) 至 10177。当前延迟谓词只接受成功的 `query-*` 或两类 army/combat preview；见 [native_driver.py:23807](/D:/codex-ck3-background-spill/ck3-sdk91/ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py:23807)。`save-checkpoint` 不符合该条件，所以同步走完整 `_persist_driver_state`，并使用 `capture_failure_diagnostic=False`。

完整持盘在 [native_driver.py:11044](/D:/codex-ck3-background-spill/ck3-sdk91/ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py:11044) 获取实例 write lock；11057–11078 在 state lock 下编码完整快照并清除 dirty，随后释放 state lock，但保持 write lock 直到 11085–11093 的原子写结束。写入期间新 query 可以再次设置 dirty。同一 Driver 实例的持盘因此串行；这些锁没有证明跨实例或跨进程互斥。

`OSError`、`TypeError`、`ValueError` 被持盘层捕获后，11104–11105 恢复 dirty 并保留 `_driver_state_error`。只有特定 successor continue 的 capture 分支返回带 `attempt_binding` 的 failed/unconfirmed 诊断；见 [native_driver.py:11097](/D:/codex-ck3-background-spill/ck3-sdk91/ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py:11097) 至 11121，以及 8624–8642。普通 SAVE 不使用该分支，因此这三类持盘失败后仍可能返回原游戏保存结果。成功分支只清除 error 与已有的自然继承 unconfirmed 标记，没有生成 SAVE 专属的成功 attempt 或 persisted sequence 回执。其他未捕获异常的行为不能概括成“所有失败都会返回 saved”。

**实际原子写 helper 是 `write_bytes_atomic`。** 导入来源在 [native_driver.py:49](/D:/codex-ck3-background-spill/ck3-sdk91/ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py:49)；许可的两份 SDK bridge 文本中没有 `_atomic_write_json` 定义或调用。完整 helper 见 [environment.py:318](/D:/codex-ck3-background-spill/ck3-sdk91/ck3_autonomous_player/src/xar_autoplayer/environment.py:318) 至 349：

- 临时路径固定为 `path.with_name(path.name + ".tmp")`；Driver 对应同目录 `driver-state.json.tmp`。
- 先 `temporary.write_bytes(payload)`，再 `os.replace(temporary, path)`。带 timing 的分支保持相同顺序，`finally` 只记录耗时。
- 没有显式 fsync、flush 或失败后的 unlink/临时文件清理。失败可能留下 `.tmp`，下一次写仍使用同名文件。
- 正常返回支持“写入和替换调用没有抛异常”，不能外推显式刷盘或掉电后的持久性。

`write_text_atomic`、`write_json_atomic` 只是编码与 JSON 序列化薄封装。固定临时名与实例锁支持一次该实例的完整 Driver 临时重写预留；独立完整状态复制 F 和 Driver 临时写入 D 没有互斥证明，现有 F+D 预留继续同时保留。

**现有公开状态可以报告当前错误，但没有每次 SAVE 的成功持盘证明。** [service.py:740](/D:/codex-ck3-background-spill/ck3-sdk91/ck3_autonomous_player/src/xar_autoplayer/bridge/service.py:740) 直接返回 Driver capabilities。Driver 在 2473 返回顶层字典，2497–2518 暴露 `native_session_control`，2521–2522 暴露角色/run；`diagnostics` 是另一个顶层字段（2725）。因此准确读取路径如下：

| 原字段路径 | 可记录的事实 | 不能据此推出 |
| --- | --- | --- |
| `capabilities.native_session_control.driver_state_error` | 当前已记录的 Driver 错误，源码 2513 | 值为 null 不证明某次 SAVE 已成功持盘 |
| `capabilities.native_session_control.configured`、`driver_state_path` | 持盘配置及实际目标路径，2498、2507 | 配置存在不等于写入完成 |
| `driver_state_restored`、`driver_state_restore_kind`、`episode_binding_state` | 同一公开对象内的恢复或绑定状态，2512、2514–2515 | 恢复状态不等于本次持盘成功 |
| `cold_candidate_rejection`、`episode_transition`、`episode_transition_error` | 同一公开对象内的既有生命周期状态，2516–2518 | 不补出 SAVE 专属 attempt 证明 |
| `capabilities.episode_character_id`、`episode_run_id` | 当前角色/run 身份，2521–2522 | 身份匹配不证明对应 history index 已持盘 |

该公开对象没有 dirty、last-persisted sequence 或成功持盘 attempt 字段。dirty 在写入前就被清除，不能单独当作成功状态。正常关闭的 [native_driver.py:23618](/D:/codex-ck3-background-spill/ck3-sdk91/ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py:23618) 至 23637 会按 dirty 尝试 flush，但可因 natural successor unconfirmed 或记录到 error 而退出；关闭完成没有提供 SAVE 专属持盘确认。

Root 使用现有接口的最小 SAVE barrier 检查表如下。每项分别保留来源和实际结果，不把它们合并写成源码并未提供的持盘成功事实。

1. 保留原 SAVE 请求与返回回执引用，记录已有 checkpoint status、history index、日期、episode IDs 及游戏文件元数据。它们说明该次游戏保存和内存关联；没有的字段明确记为未知。
2. 从原生产 capabilities 接口读取上述准确公开路径，保留当前 error、配置、路径与角色/run；用原受管 PID、创建时间、pipe 和请求身份记录关联。公开 error 在 `native_session_control` 下，不在 `diagnostics` 下。
3. 对公开路径指向的实际 Driver 文件及其固定 `.tmp` 分别记录前后 stat：存在状态、大小和 mtime。stat 只说明文件状态或变化，不证明内容完整、某个 sequence 已包含或角色绑定已持盘；不读取或 hash 大文件正文。
4. 单独保留正常 SDK close 的实际结束与退出回执。关闭前的 error 值不能代表关闭期间没有新错误，关闭 ACK 也不等于 flush 成功。
5. 分开报告游戏保存 materialization、当前 Driver 错误状态、文件变化和关闭结果。`saved`、error=null、dirty=false、stat 变化及 close ACK，无论单独还是组合，都不能补出当前接口缺失的 per-attempt persist proof。缺少该证明时，Driver durability 保持 unknown；不据此重发原 SAVE、删改历史或实现新 Driver 功能。

原失败、未知和历史运行记录保持各自原状；本文不给新增 SAVE、自然继任或游戏天数信用。
