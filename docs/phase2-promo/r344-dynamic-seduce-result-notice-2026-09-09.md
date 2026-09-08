# R344 动态勾引结果通知（2026-09-09）

## 实机结果

- R344 从冻结 R248 候选存档推进 cross-cycle/endgame source 路径；输入为
  `83,449,160` bytes / SHA-256
  `C7E5CA119F4DB4D9BFE738859DD5E32DEC6F9F1F804D91F9B26ED5D256E219DA`。
- 时间线在 `date_raw=53217600`、event instance `342` 暂停于已知的
  `seduce_outcome.4900`；root/player/`target_liege` 均为 `32904`，本次
  `owner=28443`、`target=34991`，只显示 enabled native option `0`。
- R328 的同一事件曾出现 `owner=30320`、`target=37337`。两帧共同证明
  `owner` 和 `target` 是随游戏进程变化的第三方参与者，不能固定到一次
  观测 ID；稳定身份只有玩家 `target_liege=32904`。
- 旧合同在选择前按 `scope:owner` / `scope:target` fail-closed，R344 因而
  RED；cleanup GREEN、failed checks 为空、最终 CK3 进程槽清空，原始输入
  存档未变。report / cleanup SHA-256 分别为
  `F2DD2493B1FE797AE8E5EC7997004A7692990A27365D5FD2A899CADB36874000` /
  `ACF2401918DA8F59EA2A0CA0CAC75E68035FE09FCD50F870D31C2E84642D5493`。

## 精确原版合同

CK3 1.19.0.6 原版
`events/scheme_events/seduce_scheme/seduce_scheme_outcome_events.txt`
SHA-256 为
`8562D31D9A0F244B4B2C8D926B7BB1D2CB942B1244D7CFCA76BB1CB7B127C151`。
原版注释将 `.4900` 定义为向目标的领主/东道主发送的失败尝试通知；事件
保存 `target_liege`，左右肖像分别取动态 `owner` 与 `target`。唯一 option
调用 `seduce_outcome_publicised_attempted_crimes_or_nothing_effect`，把已由
上游判定的公开未遂犯罪结果应用到两名参与者之间，没有第二条可选路线，
也不触发后续事件。

R344 完整 saved-scope 帧为：

- `scheme: scheme`、`owner: character=28443`、`artifact: artifact`、
  `target: character=34991`；
- `ignore_cheating_error_check: boolean`、`discovery_chance: value`、
  `scheme_discovered: boolean`、`target_liege: character=32904`；
- snapshot option count 为 `1`，唯一按钮为 native `0`。

修复保留八个 scope 名称、类型、数量和唯一结果按钮的完整约束；把动态
参与者改为关系约束：`owner`、`target` 都不得等于玩家，且二者彼此不同、
也都不得等于 `target_liege`。这既允许真实 ID 演进，也不会把任意事件误认
为同一通知。

## 验证与边界

- manager recovery tests normal / `-O` 各 `40/40` GREEN；
- promotion source checkpoint runner normal / `-O` 各 `83/83` GREEN；
- `py_compile` 与 `git diff --check` GREEN；
- 修复 commit `dc3bdea3d767e9635781697bb9d9d8819397ba1c` 已普通
  fast-forward push 到 `origin/master`，未 merge、未 force-push。

本轮只修正真实实机轨迹中的动态参与者合同，不新增业务 scene、definition、
stage 或宣传素材计数。canonical source registry 仍为 `3/4`，R345 继续
`capture_cross_cycle_endgame`。
