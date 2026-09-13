# CK3 1.19.0.6 玩家威望只读观测

## 状态

- **[static-confirmed]** 本合同绑定 CK3 `1.19.0.6 (Scribe)`，`ck3.exe` SHA-256 为
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- **[implementation-confirmed]** native state snapshot 新增加法字段
  `played_character_prestige`，以 signed Q100000 `{raw, scale}` 发布当前玩家威望。
- **[live pending]** 当前只完成离线 native fixture 和 Python consumer；在项目所有者解除 CK3
  使用限制前，不把该字段写成 production-live。

## 必要性与读取路径

GEN-034-D 要在唯一战争退出动作后核对条款中冻结的威望变化。退出前的
`primary_resource_balances` 和 `attacker_prestige_delta` 已经可读，但旧 WarID 消失后不能再调用
战争条款查询；通用 snapshot 此前只发布金币，因此无法诚实验证动作后的威望余额。

本实现复用战争退出 reader 已验证的同一 exact-build leaf：

```text
local player entry -> full CharacterID
full CharacterID -> generation-checked CCharacter
CCharacter + 0x1A8 -> character extension
extension + 0x130 -> int64 prestige raw
scale = 100000
```

玩家角色不存在时字段为 `null`。玩家存在而 extension 为空时按原生资源读取语义发布合法零。
Python consumer 只接受精确的 `raw/scale` 键集、signed int64 raw 和固定 `scale=100000`；旧 producer
省略字段时保留 `None`，所以 state snapshot schema 与 protocol version 继续为 `1`。

```json
{
  "played_character_prestige": {
    "raw": 12000000,
    "scale": 100000
  }
}
```

该字段经现有 `ck3_take_snapshot` / state snapshot MCP 路径发布，不增加机器、账号、路径或 CK3
轮次依赖，也不提供任何写入动作。当前范围只覆盖 GEN-034-D 需要的 prestige；没有顺带扩张 piety、
legitimacy 或经验资源。

## 离线验证

- `xar_ck3_game_access_test.exe`：GREEN，验证无玩家时 `0/100000`，有玩家时
  `12000000/100000`，并复用 full-generation CharacterID 解析。
- Python normal / optimized：直接相关的 legacy/missing-field、有效负金币与有效威望透传、畸形威望
  拒绝测试均 GREEN（各 `2/2`）。
- `py_compile` 与 `git diff --check`：GREEN。
- 本包没有启动、连接、读取或终止当前人工 CK3 进程。

## GEN-034-D 边界

该观测口只解除“动作后 attacker prestige 余额不可见”的静态阻塞。战争动作 ACK、旧 WarID 消失、
实际 delta、truce、source-specific loss、checkpoint 与 cold restore 仍必须在同一个有界 managed
lifecycle 中验证；ACK 和字段存在都不能单独关闭 GEN-034。

