# CK3 native event contract

更新时间：2026-08-23；目标版本：CK3 `1.19.0.6`。

## 最小快照

所有 Python gameplay driver 面向 planner 输出同一个可选字段：

```json
{
  "active_event": {
    "source": "native",
    "instance_id": 731,
    "option_count": 3,
    "title": null,
    "options": [
      {"index": 0, "option_number": 1, "label": null, "enabled": true},
      {"index": 1, "option_number": 2, "label": null, "enabled": true},
      {"index": 2, "option_number": 3, "label": null, "enabled": true}
    ]
  }
}
```

没有事件时为 `null`。native DLL 最小只需发布 `instance_id` 与
`option_count`，Python 会生成无文本的 options；文本不是后台运行的前置条件。
视觉 OCR 的既有 `title`、`option_number`、`visible_text` 会投影到同一结构，其中
`visible_text` 对应 `label`。旧 session 只记录到
`ordinary event interrupted` 时，可发布“事件存在但选项未知”的结构，随后只能显式调用视觉
`resolve-current-event`，不能伪装成 native 已支持。

## 选项编号

- 对 planner、MCP 和 semantic step：`option_number` 为 **1-based**，步骤名是
  `select-event-option-1` … `select-event-option-N`。这与现有 OCR 的
  `Shift+1` … `Shift+N` 编号一致。
- 对 CK3 原生命令 payload：`index` 为 **0-based**。DLL 把步骤后缀减一后写入
  `CSelectEventOptionCommand +0x24`。
- `instance_id` 对应 `CSelectEventOptionCommand +0x20`。调用方可把它和 snapshot
  revision 一并传给 `ck3_select_event_option`，防止把旧事件的选择应用到新事件。

DLL hello 可广告 wildcard capability
`game.command.select-event-option-N`。Python 不把字面量 `N` 暴露为 action；它根据当前
`active_event.option_count` 动态展开成精确的 `select-event-option-1..N`。

## Planner 与 MCP 行为

- active event 优先于存档、婚姻、战争和时间推进计划。
- 有分数时选择最高 `strategy_score`，并以最靠前选项打破平局；native 无文本/分数时选第一个
  enabled 选项。
- 精确 primitive 可用时，planner 直接返回 `select-event-option-N`。
- primitive 不可用但 hybrid 明确广告视觉 `resolve-current-event` 时，planner 返回该视觉步骤；
  这是一条显式 fallback，不藏在 native driver 内。
- 两条路径都不可用时，MCP plan 返回 `selected_step: null` 与 `required_step`，不误报可执行。

MCP 提供：

- `ck3_select_event_option(option_number, event_instance_id?, expected_revision?)`
- `ck3_resolve_active_event(event_instance_id?, expected_revision?)`

第二个工具按上述 planner 规则选择 enabled 选项，再调用精确 primitive。

## 当前证据与后续闭环

对 `ck3.exe 1.19.0.6` 的静态逆向已定位：当前本地玩家事件查询 RVA
`0x2706AD0`，event object `+0x1BC` 为 instance id、`+0x1B0` 为 event data；
event data `+0x1B0` 为 option pointer array、`+0x1BC` 为 option count。
`CSelectEventOptionCommand` 布局与提交队列证据见
`ck3_autonomous_player/native_bridge/research/README.md`。

本页 Python/MCP 接线与下述 `life-advance` composite 已由纯宿主 fixture 覆盖，并于
2026-08-23 完成 minimized CK3 实机验证：窗口保持最小化，`date_raw` 从
`53167488` 推进到 `53170608`；原生快照发现 `instance_id=14`、`option_count=5`，
提交 `select-event-option-1` 成功，下一快照已切换为 `instance_id=15`、
`option_count=3`。整段过程未调用 OCR、截图、聚焦、键盘或鼠标后端。

## Native composite `life-advance`

Python native driver 在 DLL 同时广告 snapshot/wait、`set-speed-5`、`resume-map` 和
`pause-map` 时额外广告 composite `life-advance`。它不是发给 DLL 的伪 primitive，而是以下严格
native-headless 序列：

1. 读取 fresh starting snapshot/date；
2. 提交 `set-speed-5` 并等到 snapshot 确认 speed 5；
3. 提交 `resume-map` 并等到 `paused=false`；
4. 等到日期向前变化或出现 `active_event`；
5. 若事件未自动暂停则提交 `pause-map`，并确认 `paused=true`；
6. 若当前事件的精确 `select-event-option-N` 已广告，选择最高分 enabled option（无文本时第一项），
   提交并等到 event instance 消失或切换；否则保持事件暂停、显式返回
   `event_resolution=unsupported`；
7. 返回 `starting_date(_raw)`、`ending_date(_raw)`、`elapsed_days`、`paused`、
   `ordinary_events`、最终 snapshot id/revision 与 primitive action 记录。

该 composite 不调用 OCR、键鼠、窗口恢复或视觉 backend。hybrid 只有在 native 没广告该 composite
时才按既有 capability 路由选择其它 backend；一旦 native composite 开始，失败不会在视觉端重放。

2026-08-23 minimized 实机预探针观察到：调用方持有 public revision `2` 时，自然 snapshot 已推进到
`3`，直接 primitive 会被 Python optimistic revision 检查拒绝。composite 因此在每个 primitive 前
使用 fresh snapshot；若 mismatch 只体现为日期向前、且 active event/paused/speed 未变，只允许重取并
重试一次。事件或控制状态发生变化时不重试。对应 fake endpoint 状态推进与竞态 fixture 已覆盖。

同日实机 composite 从 `map_ready=false` 的早期加载快照自然等到 ready，在窗口始终最小化
的情况下连续完成 90 次 `life-advance`，共推进 94 个游戏日，每次都回到
`paused=true`。该样本段没有出现事件；上述连续推进探针则独立闭合了事件分支。
