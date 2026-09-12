# CK3 1.19.0.6 玩家压力点只读观测

## 结论与状态

- **[static-confirmed]** 本文只绑定 CK3 `1.19.0.6 (Scribe)`，EXE SHA-256 为
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- **原生 AI 决策树：N/A。** 本包只读取当前玩家已经存在的压力点，不模拟 CK3 AI 的减压决策。
- **[implementation-confirmed]** native `state_snapshot.state.played_character` 新增加法字段
  `stress_points`。Python native driver 保留该非负整数；旧 snapshot 或 fixture 未携带该字段时仍可读取。
- **[live pending]** 当前没有使用新字段的真实 paused artifact，所以能力状态是 `static-ready`，不能写成
  `production-live`。下一次允许启动 CK3 时，只需在一个既有 paused 场景读取一次，不扩成长期矩阵。

## Exact-build 读取路径

现有战争退出资源读取器已经使用同一条路径；本包把它复用到通用玩家 snapshot：

```text
local player entry -> full CharacterID
full CharacterID -> generation-checked CCharacter
CCharacter + 0x1A8 -> character extension
extension + 0x2F8 -> int32 stress points
```

`ResolveCharacter` 会校验 low-24-bit storage slot 与对象内 full-generation identity。extension 为空时沿用既有资源
读取语义发布 `0`；负数视为读取失败，整份 native snapshot 不发布猜测值。C++ fixture 已从 extension `+0x2F8`
读出 `42`，并证明负数被拒绝。

这项读数不等于 stress level、临界阈值、健康风险或减压决议可用性。当前 wire 只承诺非负的 native stress-point
整数；其它健康/压力状态仍是后续独立观测缺口。

## Wire 与兼容性

有玩家角色时，native snapshot 的相关片段为：

```json
{
  "played_character": {
    "character_id": 707,
    "alive": true,
    "stress_points": 42,
    "betrothed_id": null,
    "primary_spouse_id": 808,
    "spouse_ids": [808]
  }
}
```

没有玩家角色时 `played_character` 仍为 `null`。协议版本保持 `1`：该对象此前已经以可选的继承人与婚姻字段做
加法演进，Python consumer 继续接受旧 producer 未提供 `stress_points` 的 snapshot。新 native producer 对存在的玩家
角色总会发布该字段。

## G2-M2 后置验证入口

`tgp_travel_events.0030` 的 source-reviewed 选择是 authored option 2/native 1，效果包含玩家压力下降。新字段允许
在选择前后的 paused snapshot 中绑定同一 full CharacterID 并比较压力点：

1. 选择前记录 `character_id`、`stress_points` 与 event instance；
2. 提交既有 registry 选择并等待 event instance 前进；
3. 在后置 paused snapshot 中要求同一玩家角色且 `post_stress_points <= pre_stress_points`；
4. 只有 `pre_stress_points > 0` 且实际读数下降时，才把该轮计入 G2-M2 的 material-delta 证据。

若选择前已经为零，事件可以安全关闭，但该结果不能冒充“已验证压力物质变化”。registry consumer 尚未自动执行上述
对账；这仍是下一个 Python 施工包。新字段也不改变 P1、视频门禁或当前 G2 `0/8` 完成数。

## 聚焦验证

- Visual Studio 2026 Release：`xar_ck3_bridge.dll` 编译与链接 GREEN；
- `xar_ck3_game_access_test.exe`：GREEN，覆盖 stress `42` 与负值拒绝；
- Python native-driver 正常/异常合同：`2/2` GREEN；
- `py_compile` 与 `git diff --check`：GREEN。

