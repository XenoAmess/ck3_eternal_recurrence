# 361 B2 同检查点接受 / 协商 / 拒绝矩阵

状态：2026-09-01 `static-ready / runner integration pending / live pending`。本文件记录独立编排器
[`tools/zg361_phase2_b2_checkpoint_matrix.py`](../../tools/zg361_phase2_b2_checkpoint_matrix.py)
的冻结合同。普通与 `-O` 确定性测试已通过；本轮没有启动 CK3，也没有生成 paused live artifact，因此不得写成
`fixture-live`、`production-live primitive` 或 `production-live loop`。

## 要解决的问题

`zg361b2.40` 的接受、协商、拒绝会消费同一个待回应 PIP 案。若在 A 路点击后直接点 B/C，后两路读到的是已经被 A
改写的世界，不是同一前置条件。新编排器把三路验收固定为一笔事务：

1. 在真实玩家本人收到 `zg361b2.40`、游戏暂停时，先读 typed event context 与 B2 provider；
2. 只保存一次原生 checkpoint，并冻结它的绝对路径、文件名、字节数、SHA-256、日期、玩家以及
   `owner / subject / cycle / case`；
3. A=`accept`、B=`negotiate`、C=`refuse` 每一路开始前都从这同一份字节恢复，绝不承接上一条路线的结果；
4. 每路重新读取当前 session 的 event instance 和三项 typed option，再最多提交一次真实
   `select-event-option-N`；
5. ACK 只算提交回执。只有旧事件离开且 B2 provider 发布同案的 action-specific state/response receipt，路线才 GREEN；
6. C 路结束后再从同一 checkpoint 做第四次恢复，重新读到 pending 基线，然后关闭最终 session；
7. 每次恢复都要求新 PID、连接代次恰好加一、原 PID 已独立证明退出；末尾再次证明整条受管 PID lineage 全死。

这样得到的是“同一份真实前置世界的三种反事实”，而不是三次彼此污染的顺序点击。

## 身份与 event instance

跨恢复必须保持不变的是产品身份：

- event definition 必须始终为 `zg361b2.40`；
- owner、subject、cycle、case 与 pending state 必须匹配冻结基线；
- played character、暂停日期与 episode 必须匹配；
- 三项 option 的原生 index、rendered index、shown/enabled 与简中/英文产品语义必须完整匹配。

event instance ID 属于当前 CK3 进程的窗口实例，不把首次 session 的数字盲目带进下一次冷恢复。每一路先通过
`query-current-event-window-context-v1` 取得本次恢复后的正数 instance ID，再由 single-submit proxy 将 action cell
的第一帧和 `select-event-option-N` 同这个 ID 绑定。检查到 preflight 后换窗、旧实例、错误 option 或第二次提交时，
会在调用真实选择前 fail closed。每一路原始 instance 都进入 sidecar，可核对其属于哪一个 PID / connection generation。

## 检查点与恢复合同

编排器直接消费现有 `GameplayBridgeService` 原语，不新增 provider：

```python
service.save_checkpoint(expected_revision=...)
service.restore_checkpoint(expected_revision=...)
```

保存结果必须有 `accepted=true`，内部 checkpoint 必须为 `status=saved`，并给出真实 path、name、正字节数、
64 位十六进制 SHA-256、冻结日期与本人 episode character。每次恢复必须返回同 path/name/size/SHA/date、
`status=restored`，并由 lifecycle receipt 精确证明：

- `previous_pid` 等于恢复前 PID；
- `pid` 等于恢复后 bridge PID，且两者不同；
- `lifecycle_intent=restore`；
- connection generation 恰好从上一代加一；
- 恢复前 PID 的进程树已经独立不可见。

任一路 path、字节数、hash、日期、玩家、episode、case 或代次漂移都会 RED。即使 restore receipt 已经漂移，
编排器仍先尽量发现新 PID、把它纳入 cleanup lineage，再报告失败，避免“验收失败后遗留一个未记账 CK3”。

## 一次真实提交与独立后置条件

每一路由既有
[`tools/zg361_phase2_b2_action_cell.py`](../../tools/zg361_phase2_b2_action_cell.py)
执行。编排层额外包一层 single-submit service proxy：

- `accept` 只允许 option 1；
- `negotiate` 只允许 option 2；
- `refuse` 只允许 option 3；
- option 必须绑定刚才 typed preflight 的 event instance 与 revision；
- 一个 arm 调用第二次 `select_event_option` 时立即 RED，第二次不会到达真实 service。

路线成功还必须保留 action cell 的完整 `precondition / selection_submission / postcondition_observations /
postcondition`，并满足 `ack_is_postcondition=false` 与 `postcondition_query_green=true`。因此“命令 ACK 成功但 provider
没变”、旧事件未离开、换案或超时都不会被误报为 GREEN。

## 进程所有权与失败恢复

调用方通过很薄的 `B2ManagedProcessLifecycle` adapter 接现有 runner 进程所有者：

```python
class Lifecycle:
    def prove_pid_dead(self, pid: int, *, reason: str) -> dict: ...
    def stop_session(self, pid: int, *, reason: str) -> dict: ...
```

`prove_pid_dead` 必须做独立、有界的进程树观测，不能把 shutdown/restore ACK 原样抄成 `dead=true`。正常流程的
最终 shutdown 要返回匹配 PID、`ok=true`、`cleanup_proven=true`、`tree_gone=true`，之后还会对全部 tracked PID
再查一次。任一旧 PID 仍活即 cleanup leak，整批保持 RED。

发生 stale instance、checkpoint drift、typed option 缺失、重复提交、后置条件缺失或其他异常时，编排器会：

1. 原样保存已经取得的 RED 与 raw payload；
2. 若已有 frozen checkpoint，则再尝试一次 exact final baseline restore；
3. 重新读取 pending PIP 基线；
4. 关闭当前 session，并对所有已发现 PID 做最终死亡证明；
5. 返回带完整 recovery/cleanup 的 `B2SameCheckpointMatrixError.evidence`。

恢复与 cleanup 成功不会把原始业务 RED 翻绿；它们只证明失败没有污染后续批次。

## 保留的过程素材

`artifacts_directory` 使用 write-once 文件；同名文件存在时直接失败，绝不覆盖旧 attempt。成功矩阵固定保留：

| 文件 | 内容 |
|---|---|
| `00_matrix_contract.json` | 本次禁止 OCR/坐标/测试决议及同 checkpoint 合同 |
| `01_initial_prechoice_raw.json` | 首次 snapshot、event context、B2 provider 与 typed 投影 |
| `02_frozen_checkpoint_raw.json` | 原始 save receipt、hash 身份与 save 后再次读取的 pending 基线 |
| `10/20/30_*_restore_raw.json` | A/B/C 各自恢复 receipt、前后 PID/代次与旧 PID 死亡证明 |
| `11/21/31_*_prechoice_raw.json` | 每路当前 event instance、三项 option 与同案 identity |
| `12/22/32_*_action_raw.json` | 每路完整 action cell、真实 ACK、独立 provider 后置条件与 submit 计数 |
| `40_final_restore_raw.json` | C 路之后第四次 exact baseline restore |
| `41_final_prechoice_raw.json` | 最终恢复后仍为同案 pending 的只读证明 |
| `42_final_shutdown_raw.json` | 最终 session 受控关闭原始结果 |
| `43_pid_lineage_cleanup_raw.json` | 全部受管 PID 的最终死亡证明 |
| `99_b2_same_checkpoint_matrix.json` | 汇总与 readiness 边界 |

RED 时另写 `90..93_recovery_*.json`；已经生成的成功/失败 arm 原始素材全部保留，不删除、不拿下一次 attempt 覆盖。

## 调用与验收

后续共享 runner 只需把现有 `GameplayBridgeService` 和进程 owner 包成上述 adapter：

```python
result = run_b2_same_checkpoint_matrix(
    service,
    lifecycle,
    owner_character_id=owner_character_id,
    artifacts_directory=attempt_dir / "b2_same_checkpoint_matrix",
)
```

初始实现轮按协调要求未修改 `tools/run_zhongguo_acceptance.py`。离线测试：

```powershell
py tools/test_zg361_phase2_b2_checkpoint_matrix.py
py -O tools/test_zg361_phase2_b2_checkpoint_matrix.py
```

测试覆盖完整三路/四次恢复、write-once artifacts、checkpoint hash 漂移、case 漂移、typed option disabled、
ACK 后 provider 不变、stale event instance、重复提交与 PID cleanup leak。它们只证明编排合同，不冒充 CK3 实机证据。

2026-09-04 r9 已把 canonical paused seed 提升为 ready，但其初始 B2 provider 精确为 `case_not_found`，不是可直接交给矩阵的
`zg361b2.40`。下一步是在共享 runner 增加 product-only focused route：从 r9 seed 有界推进真实 `zg361.50` option 1，证明旧
event instance 消失并等待新的 `zg361b2.40`/provider 出现，然后才调用上述矩阵。矩阵自行完成四次 restore 与第五个最终 session
清理，不能嵌入现有单次 save/restore lineage，也不能直接用全量 `--phase2-live-batch` 撞已知 scoreboard RED。首次实机前状态仍是
`static-ready / production-live pending`；实机 RED 必须优先修 MCP/provider 或产品语义，不得回退到 OCR、坐标或测试决议。
