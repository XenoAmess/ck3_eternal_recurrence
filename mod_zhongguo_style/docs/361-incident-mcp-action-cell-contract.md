# Incident X/Y/Z MCP gameplay action cell

状态：`static-ready / fixture-tested`

实机状态：`not-live-tested`

## 为什么动作入口不是 `zg361ip.190/290/390`

X/Y/Z 终态回执事件分别是 `zg361ip.190`、`zg361ip.290`、`zg361ip.390`，但三个事件都由
受评者案卷中的 `zg361_case_*_owner` 接收，事件 ROOT 是管理者。现有
`query-zhongguo-incident-snapshot-v1` 则是严格的 received-self provider：当前玩家必须是案卷 subject，
caller 只能提交 expected-owner equality filter。把管理者回执事件的 option ACK 与受评者 provider 拼在一起，
需要先换玩家，已经破坏同一 played-character、同一帧和同一 ACL 绑定，不能作为 X/Y/Z gameplay GREEN。

因此本 cell 使用真正的 subject-side 产品入口：

1. 等待并绑定 `zg361.50`；current-event ROOT 必须等于当前玩家，saved scope
   `zg361_notice_prompt_owner` 必须等于 runner 冻结的上司 CharacterID；
2. 固定选择 authored option 1（`zg361.50.a`，正式签收）。它调用
   `zg361_deliver_325_notice_effect`，后者在真实清算成功后调用
   `zg361_p2c_on_result_delivered_effect`，这是唤醒中央二期管线的产品动作，而不是测试注入；
3. 若随后出现 `zg361.4`，只允许 authored option 1（认命）继续时间线；任何其他事件立即 RED，不猜选项、
   不 OCR、也不把单选事件一律自动关闭；
4. 每次 `select-event-option-1` 后必须看到旧 event instance 消失。command ACK 只记录为 submission，
   不能作为结果；
5. 在一个真实 paused snapshot 上逐一查询固定 profile `x/y/z`。三者必须共享 owner、subject、cycle、
   probe serial、applicability source/consequence 和三项资源快照；
6. 正案必须是 X state 8、Y/Z state 6，且各自 `kpi.disposition=pending`、`pending=1`、`consumed=0`；
   无事故必须是三域一致 exact N/A，且 `kpi.disposition=not_staged`；
7. 同帧再用一个不同的错误 owner 查询三域，必须全部得到
   `owner_filter_mismatch + terminal.kind=unavailable + readiness.ready=false`，否则 ACL RED。

## 代码入口

可复用 helper：

```python
from xar_autoplayer.bridge.zhongguo_incident_action_cell import (
    run_incident_xyz_gameplay_action_cell,
)

evidence = run_incident_xyz_gameplay_action_cell(
    service,
    owner_character_id=incident_owner_character_id,
)
```

失败时抛出 `IncidentActionCellError`，其中 `evidence` 保留截至失败点的事件 identity 查询、action ACK、
实际 event-instance transition、provider poll 与失败原因，runner 应原样写入 artifact。这个 helper 不写文件、
不启动 CK3，也不依赖 runner 私有函数，因此可以在 phase-two runner、独立 provider live fixture 与后续
`open_kaishek` differential harness 中复用。

当前无需新增 native action：`current-event-window-context-v1 + select-event-option-1 + pause/resume/set-speed-1`
已经能表达真实产品动作。若实机证明 seed 无法到达 `zg361.50`，应修 seed/bootstrap producer；不得退回
`zg361ip.190/290/390` 的管理者回执，也不得用 OCR 点击替代 same-frame owner/subject 证明。

## 已覆盖的 fixture RED/GREEN

- 正案 X/Y/Z pending KPI GREEN；
- 三域 exact N/A/no-KPI GREEN；
- event-free seed 有界等待后到达 `zg361.50`；
- 错事件、错误 notice owner、错误 native option index；
- ACK 成功但旧 event instance 未消失；
- 中途出现未知事件；
- KPI disposition 伪造、跨 profile probe 漂移；
- wrong-owner ACL 泄漏；
- capability 缺失与入口超时。

这些都是 fixture 证据，尚不提升 CK3 live readiness。首次正式集成必须保存 paused snapshot、三域 response、
wrong-owner response、两次 option materialization 与最终 runner report。
