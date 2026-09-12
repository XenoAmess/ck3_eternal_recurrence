# CK3 1.19.0.6 玩家金币只读观测

## 结论与状态

- **[static-confirmed]** 本文只绑定 CK3 `1.19.0.6 (Scribe)`，`ck3.exe` SHA-256 为
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- **[implementation-confirmed]** native state snapshot 新增顶层 `played_character_gold`，以 `{raw, scale}` 发布玩家当前金币；
  `scale` 固定为 `100000`，`raw` 接受负数以保留真实债务，不把负余额误判为读取失败。
- **[live pending]** 该字段和 `trait_specific.8001` 后置比较器均为 `static-ready / live=false`。现有 R414 artifact 只冻结了
  选择前事件窗口，没有由当前实现产出的金币帧或选择后读数。下次允许占用 CK3 时只需一次有界事件动作验证。

## Exact-build 读取路径

本包复用战争退出资源查询已经闭合的玩家身份和金币 leaf：

```text
local player entry -> full CharacterID
full CharacterID -> generation-checked CCharacter
CCharacter + 0x1A8 -> character extension
extension + 0x100 -> int64 gold raw
scale = 100000
```

`ResolveCharacter` 继续核对 low-24-bit storage slot 与对象内 full-generation identity。没有玩家角色时顶层字段为 `null`；
存在玩家角色而 extension 为空时，沿用原生 getter 语义发布合法零。Python consumer 只接受键集合严格为 `raw/scale`、
`raw` 位于 int64 范围且 `scale=100000` 的值。该读数表示当前个人金币余额，不代表月收入、可支付性或某项事件的最终动态金额。

## Wire 与兼容性

```json
{
  "played_character": {
    "character_id": 707,
    "alive": true,
    "stress_points": 42,
    "betrothed_id": null,
    "primary_spouse_id": null,
    "spouse_ids": []
  },
  "played_character_gold": {
    "raw": 35000000,
    "scale": 100000
  }
}
```

字段放在顶层，避免把资源余额混入既有 `played_character` 身份/关系对象。state snapshot schema 版本保持 `1`，字段是加法演进；
Python driver 接受旧 producer 省略该字段并把它保留为 `None`。事件动作结果同时输出同角色的
`starting_played_character_gold` 与 `ending_played_character_gold`，每个观察都携带 CharacterID、raw 和 scale。

## `trait_specific.8001` 后置验证

exact source 中 authored option 2/native 1 执行 `add_gold = minor_gold_value`。`minor_gold_value` 由月收入、当前 treasury 与 era
共同求值；`00_basic_values.txt` 给出的 authored minimum 是 `15` whole gold。因为当前 snapshot 没有冻结这些完整动态输入，
effect profile 明确写 `runtime_delta_exact=false`，比较器只承诺同一角色的 Q100000 raw 金币严格增加：

1. planner 仅对 exact `trait_specific.8001` authored option 2/native 1 生成 material expectation；
2. expectation 绑定选择前 snapshot ID、revision、full CharacterID 和金币 raw；
3. action 复用已有前后 paused snapshot，不增加额外查询或等待；
4. 同角色且 `post_raw > pre_raw` 才是 `verified_change`；不变、下降、身份漂移或读数缺失均不能通过；
5. 实际 delta 作为观测结果保存，但不得声称它在执行前精确等于 `15` 或其它常量。

这使 `.8001` 成为 G2-M2 第二条具备真实物质状态后置的事件路径。它仍须一次 bounded production action 才能升级；不得为该
单事件开启长期游玩或扩大事件矩阵。

## 聚焦验证

- Visual Studio 2026 Release：`xar_ck3_bridge.dll` 与 `xar_ck3_game_access_test.exe` 编译、链接 GREEN；
- `xar_ck3_game_access_test.exe`：GREEN，fixture 读出 `35000000/100000`；
- Python registry、profile、planner、action、comparator：normal/optimized 各 `30/30` GREEN；
- `py_compile` 与 `git diff --check`：GREEN。

旧 CMake build tree 的 CTest 命令含混合 Cygwin/Windows 绝对路径，导致 CTest 无法启动目标；同一次增量构建生成的 fixture 已按
Windows 原生路径直接执行并通过。该 harness 路径问题不改变代码测试结论，也不是产品 RED。

## 证据

- 金币 ABI 与既有资源查询：[`player-war-exit-policy.md`](player-war-exit-policy.md)、
  [`war-termination.md`](war-termination.md)；
- 事件 source：`Crusader Kings III/game/events/trait_specific_events/trait_specific_events.txt:1221-1225`，SHA-256
  `A4882239AB219EFB2BB082C983403E6E24B8C9DD481E5643ADFE3321ACAC43F7`；
- 动态值 source：`Crusader Kings III/game/common/script_values/01_dynamic_values.txt:53-70`，SHA-256
  `049303EFF8ABFDFCADCC31D27E2633A26A2E877E4E2980D4A42C53D6B76D7064`；
- 基础值 source：`Crusader Kings III/game/common/script_values/00_basic_values.txt:49-64`，SHA-256
  `9268A54F0E425D409D9D0F20D884E0A3D0A89DF85A0B6644D56133C0C4CB0096`；
- R414 选择前 artifact：`_runtime/p1-post-chaos-terminal-r414-20260911/live-artifacts/terminal-stages-red-attempt-06.json`，
  SHA-256 `BEEB7C1C2FE0A30FA056ABCED1C28EA83BD0739DC0D1225BE4CA1C3C738700E6`。
