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

本页 Python/MCP 接线已由纯宿主 fixture 覆盖；实际 minimized CK3 的事件发现、提交和事件消失
仍需一次实机验证。完成该验证后，`life-advance` 可组合为：记录起始日期 → speed 5 → resume →
等待 `active_event` → 必要时 pause → resolve → 返回终止日期与兼容的 `ordinary_events`。
