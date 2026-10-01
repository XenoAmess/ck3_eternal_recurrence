# R6 事件 14：已保存时点证据与 context admission

2026-10-01 的 R6 错误不能证明当前版本的 event-window ABI 或发布生产者有误。更早的 `native:5` 快照包含事件 14，但实际 SDK 请求前后保存的三份 `native:8` 快照都显示 `active_event=null`；两组 `date_raw` 都是 `53169336`。暂停且日期相同不代表事件展示状态属于同一份 native revision。

构建固定为 CK3 `1.20.0.2`，EXE SHA-256 `AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D`。本记录只读已有 artifact 和冻结 L6 源码，没有读取游戏进程内存、发送 pipe 请求、操作 GUI、重新测试或修改生产代码。

| 已保存证据 | revision / native revision | 事件状态 | 结果 |
| --- | --- | --- | --- |
| `construction-live-next/root-r6-fresh-material-01/snapshot-before.json` | `2 / 5` | instance `14`，authored option count `1` | 更早发布快照 |
| SDK `001-ck3_take_snapshot.json` | `2 / 8` | `null` | 实际查询前快照 |
| SDK `002-ck3_take_snapshot.json` | `2 / 8` | `null` | 实际查询前快照 |
| SDK `003-ck3_query_current_event_window_context_v1.json` | 请求 local revision `2` / event `14` | 当前快照为 `null` | `isError=true`，Python admission 拒绝 |
| SDK `004-ck3_take_snapshot.json` | `2 / 8` | `null` | 实际查询后快照 |

SDK 目录为 `artifacts/g2-offline-2026-10-01/targeted-sdk-r6/r6-current-event14-context-20261001T115859Z/`。完整路径、SHA-256、精简原始字段与后续 LAW packet 见 [保存证据清单](../../ck3_autonomous_player/native_bridge/research/event12002_r6_context_event.json)。原始失败不删除、不改签，不将它算作 native reader 失败。

## 实际拒绝位置

冻结树 `Z:\ck3_mod_rewrite\.task-tmp\g2live6` 的 `ck3_autonomous_player/src/xar_autoplayer/bridge/service.py:10290` 先获取 `self.snapshot()`，在 `10295` 读取 `active_event`。`10327–10332` 要求它是字典且 `instance_id` 等于请求值；此处产生 `event instance ID does not match the active event`。真正执行 native query 的 `self.execute_step(...)` 位于 `10346`，本次请求没有到达该调用。因此无需修改此 guard、schema 或 context ABI。

## 既有生产者与独立 reader 对照

冻结 L6 的 `ck3_12002_adapter.cpp:155` 用 `ReadEventsSnapshot(bindings_.events, observed)` 采集事件，`165` 才将观察结果交付。`ck3_12002_events.cpp:53–68` 的事件生产者经 `game_state+0xA0 -> embedded manager+0x34480 -> get_current_event` 读取当前对象，再读取对象 `+0x1BC` 的实例 ID、`+0x1B0` 的定义指针和定义 `+0x1AC` 的 authored option count。

独立 `ck3_12002_event_window_context.cpp:106–125` 的 observation prefix 复用同一 `ReadEventsSnapshot`；`175–211` 的定义身份读回使用同一 getter、manager offset 和实例 ID offset。`795–840` 在这些步骤之外还要求当前 paused/map/active instance 与请求相符。源码对照没有显示此次 SDK 错误来自两套不同的 instance offset；已有 [1.20.0.2 context ABI 与材料化边界](event-window-context-1.20.0.2.md) 继续有效，本任务没有重跑其验证。

## 收口边界

事件 14 在两份 native revision 之间消失的具体原因，不能由这些保存文件单独确定。本次不据此推断缓存、attachment、restore、GUI materialization 或生产者错误。后续 `r6-crown-action-readonly-20261001T120433Z/result.json` 的 `initial_frame.native_revision=11`，保存了 LAW 调用 `isError=false`；root 同时报告 fresh02 construction `material_source` GREEN/native `10`。这些结果说明应继续使用 fresh paused material，不能把更早快照的 event 14 带入新 native revision。

协调者已明确停止 ABI/VM_READ 展开。本包只交付保存证据报告，不新增内存诊断计划、fixture、测试、guard、cache 修复或生产 schema，也不提升 live/G2 readiness。后续只在当前快照再次发布有效实例时进入既有 event query 工作流。
