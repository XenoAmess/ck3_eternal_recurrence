# 361 B2/PIP MCP-first gameplay action cell

状态：2026-09-01 `static-ready / runner-wired`。本文件记录独立 helper
[`tools/zg361_phase2_b2_action_cell.py`](../../tools/zg361_phase2_b2_action_cell.py)
的调用合同及 batch runner 接线；helper 与 runner 的普通、`-O` 离线测试已通过，但尚未取得
CK3 paused live artifact，不能写成 `fixture-live` 或 `production-live`。

## 结论：不需要新增 action MCP

现有 MCP 能力已经足以完成 #015 本人回应：

1. `query-current-event-window-context-v1` 在暂停帧中给出事件定义、root/saved
   character scope 和三项已解析、已启用选项；
2. `select-event-option-N` 以 event instance ID 和 public revision 绑定一次真实点击；
3. `query-zhongguo-b2-pip-snapshot-v1` 在动作前后给出 received-self PIP 案卷及
   `owner / subject / cycle / case / state` 五元身份。

因此本 action cell 只是上述生产能力的消费者，不另造 provider、不使用 OCR、不读取坐标，
也不引入“按变量名执行 effect”之类的测试后门。

## 三条动作语义

| action | 事件/选项 | 必须看到的 paused provider 后置条件 |
|---|---|---|
| `accept` | `zg361b2.40` 第 1 项，“Accept the plan and its support.” / “接受计划及配套支持。” | 同 owner/subject/cycle/case，state `1 → 2`，response `1`，本人 author，goal revision `false`，refusal receipt `0` |
| `negotiate` | 第 2 项，“Revise the goal once, then begin.” / “修改一次目标，然后开始执行。” | 同案 state `1 → 2`，response `2`，本人 author，goal revision `true`，refusal receipt `0` |
| `refuse` | 第 3 项，“Refuse, and let only the next cycle judge it.” / “拒绝，并只让下一轮评价此事。” | 同案 state `1 → 5`，response `3`，本人 author，goal revision `false`，refusal receipt等于 case |

helper 会同时核对：

- 当前事件定义必须恰为 `zg361b2.40`；其他事件即使也有三个按钮也直接 RED；
- event root 必须是 played character；保存的 prompt owner/subject 必须分别等于传入
  owner 和 played character；cycle/case/state 三个冻结 scope 名必须全部存在；
- 三项 option 必须按原生 index 0/1/2 完整展示并启用，解析文本必须逐项匹配当前简体中文或
  英文产品语义；不能只按“第几个按钮”盲点；
- 动作前 provider 的 gate 与 PIP 四元不可变身份必须相同，state 必须为 `1`，本人回应必须为
  pending 且唯一 acknowledgement receipt 已绑定 case；
- 动作后仍须暂停、同一天、同 played character、同 bridge connection，并由 provider 发布
  同一不可变案卷的目标 state/response receipt。

current-event-window v1 当前只闭合 character scope 的 typed identity，不能读取三个 scalar
saved scope 的数值。这里不伪造这些值：scalar scope 只验证冻结名称存在，真实 cycle/case/state
数值来自 exact-build B2 provider；而 `zg361b2.40` 产品 trigger 本身又逐项核对五个 frozen
prompt scope 后才允许窗口出现。后续若通用 event scope query 原生增加 scalar typed identity，
可在 helper 中增加交叉核对，但它不是本 action cell 的新 provider 前置。

## ACK 与 GREEN 的边界

`select-event-option-N` 返回 `accepted=true/status=submitted` 只表示命令已进入游戏主线程，永远不
算后置条件。helper 只有在旧 event instance 已离开、且 B2 provider 发布上述同案状态转移后才返回
`result=GREEN`；证据中固定记录：

- `ack_is_postcondition=false`；
- `postcondition_query_green=true`；
- 动作前后完整五元 identity、选项语义投影和 paused binding。

ACK 成功但案卷不变、错误事件、选项语义漂移、owner/subject 不符、case 被换、provider
unavailable、日期/玩家/连接发生漂移或超时，全部 fail closed，并通过
`B2PipActionCellError.evidence` 返回当时的 RED sidecar。

## Runner 接入与 save/restore

入口：

```python
run_b2_pip_gameplay_action_cell(
    service,
    owner_character_id=owner_character_id,
    action="accept",
)
```

helper 不自行存档、恢复或推进日期。三项产品 effect 都在事件选择时立即执行；在同一暂停日期读取
provider 是更强的原子后置条件，额外 `life-advance` 反而会混入不相干日结算。正式 batch runner
现已在外层实现 `save-checkpoint → accept action cell → postcondition snapshot → restore-checkpoint`：

批次按现有产品事件链先完成 Incident action，再等待 B2 prompt；恢复 B2 基线后继续 post-restore
Incident/B2/Workforce/AI-owned 只读观测，而不是在已经推进过的 seed revision 上查询。

- 动作前先运行只读 domain matrix，再冻结含待回应 PIP 的基线；
- runner 只在 event-free map 通过 MCP `set-speed-1` / `resume-map` 等待，并用
  `query-current-event-window-context-v1` 锁定 exact `zg361b2.40`；若先出现其他事件则原样 RED，
  不猜测也不自动关闭；readiness 落在 `05_phase2_b2_pip_prompt_readiness.json`；
- restore 的 `expected_revision` 绑定动作及 provider 后置条件之后的新 paused revision，不复用
  pre-action revision；
- `05_phase2_b2_pip_gameplay_action_cell.json` 原样保存 helper 的 pre/action/post 或 RED sidecar；
- `06_phase2_save_restore_lineage.json` 保存 checkpointed action、动作后的第一 PID binding、恢复后的
  第二 PID binding 与存档 SHA；恢复后继续同一组只读 domain matrix 并比较语义投影。

若还要在同一基线验证另外两条选择，应每条路线各自从冻结 checkpoint 恢复，禁止在已经消费的 PIP
上重放第二项。本批只接 `accept`；Workforce、AI-owned case 与 scoreboard named-widget 三项产品
动作仍缺失，因此 phase-two 总结果必须继续为 RED/incomplete。

## 离线验收

```powershell
py tools/test_zg361_phase2_b2_action_cell.py
py -O tools/test_zg361_phase2_b2_action_cell.py
```

测试覆盖三条正确路线、简中/英文 option 语义、错误事件、文本漂移、scope/五元身份漂移、拒绝
ACK、ACK-only 假阳性、旧窗口不退出、provider unavailable、换案与超时；runner 静态/fake MCP
测试另覆盖 checkpoint/action/restore 顺序、动作后 revision 绑定、B2 RED sidecar 原样保存，以及
成功后只从缺失动作表移除 B2。下一步是在 G2 释放实机槽后运行真实 paused `zg361b2.40` batch，
取得上述两个 artifact；在此之前不得提升 live readiness。
