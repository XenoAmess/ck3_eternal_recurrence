# 2026-10-01：R1 → R2 checkpoint 环境绑定迁移

实际 h82 checkpoint 的完整 `succession_lifecycle` 已绑定 R1 环境 SHA；R2 合法 runtime／profile 变化产生新的 environment SHA。原生产 `one_generation_preflight.py` 比较整个 lifecycle dict，因此会返回 `one-generation driver lifecycle differs from the prepared profile`。旧的 legacy rogue 兼容分支不适用于已有正式绑定的 checkpoint。

现有 `rebind-ordinary-seed-v1` 仅接受 ordinary／xar_off。实际 seed 为 rogue_one_life／xar_on／terminal_settlement_required，不能借此重分类。`NativeHeadlessGameplayDriver.bind_succession_lifecycle_v1` 只处理 adoption 前内存绑定，也不会迁移持久化 checkpoint。

新增正式文件入口 `xar_autoplayer.checkpoint_environment_rebinder.rebind_checkpoint_environment_v1(spec, expected_source_environment_sha256=..., expected_pipe_name=...)`。先由原有流程准备新 target profile，再原样复制 full-v2 driver 与 checkpoint；随后调用入口。它复用既有 profile verifier、driver consumer、cold checkpoint validator、save integrity 与三锚替换 helper，只更新以下三个值：

- `succession_lifecycle.environment_sha256`
- `last_checkpoint.succession_lifecycle.environment_sha256`
- `command_history[last_checkpoint.history_index-1].result.checkpoint.succession_lifecycle.environment_sha256`

其余 lifecycle 字段必须与新 profile 绑定结果相同，保留 rogue／ordinary、xar 开关、pact contract 和 source；存档、episode、完整 history、campaign goal 及其它 driver 内容原样保留。操作只使用目标 state 的既有文件锁，不查询进程、不连接 pipe、不驱动游戏；原生产预检中的 zero-CK 要求未改动。失败时恢复目标 driver 原字节，原 seed 始终作为输入保留。

本次实际输入为 actor `29829`、episode `native-29829-3f80e147d033`、date `53169096`、history index／length `82`，原 pipe `\\.\pipe\xar_ck3_bridge_migration_12002`。checkpoint 为 `67,290,734` 字节，SHA `4e14c9d64bfd6a5323c8b8c9174065a43de5c963c3488e45453498e81cebbbaa`；原 driver 为 `335,584` 字节，SHA `89bf040a2a0a8e2f8ccd736f7e652deed06f9ac472fbeda9ee5b9f17c16f8efa`。R1 source environment SHA 为 `158fb4a4d7db2a4673566fb1f40ba7c6bd1a64c39359379c9885b31f1462b691`。

离线复现使用实际完整 pair 与明确标记的 matching 新 profile bytes：production preflight RED → 正式 API → production preflight GREEN。preflight 的 process inventory 与 profile verifier 使用 fixture 输入，其余 driver consumer、cold checkpoint、save integrity 均走实际生产函数。递归 JSON diff 精确只有三条环境 SHA；原 seed 与 save 字节未变。两个必要 unit tests 通过，覆盖完整恢复和拒绝生命周期重分类。

证据位于主 workspace 的 `artifacts/g2-offline-2026-10-01/lifecycle-environment-rebind/`：`result.json`、`migration-receipt.json`、`reproduce_actual_pair.py` 和两次 production preflight report。此处 readiness 是 `static-ready`，尚未生成实际 L2／R2 profile，不声称完成实机恢复。

真实 target 由 `r2_file_candidate` 在 root 提交并生成稳定 L2 后准备，再调用相同 API。receipt 提供 `driver_state.target_sha256`／`target_size`、未变的 save SHA、target lifecycle 与 `no_launch_preflight_expectations`。候选准备器应重新 qualify 实际 derived pair，刷新身份、预检 argv 与 receipt；不可继续使用旧 driver SHA。

独立 module CLI 可供既有准备流程调用，`PYTHONPATH` 指向稳定 L2 的 `ck3_autonomous_player/src`：

```powershell
python -B -m xar_autoplayer.checkpoint_environment_rebinder `
  --state-dir <new-prepared-state> --game-dir <game-dir> `
  --expected-source-environment-sha256 158fb4a4d7db2a4673566fb1f40ba7c6bd1a64c39359379c9885b31f1462b691 `
  --expected-pipe '\\.\pipe\xar_ck3_bridge_migration_12002' `
  --receipt <migration-receipt.json>
```

本工作包没有修改 `native_driver.py`、preflight 或中央 CLI，也没有进行 CK3／pipe／UI／Git 操作。实际 R2 资格与后续启动由协调者及候选准备 owner 继续。
