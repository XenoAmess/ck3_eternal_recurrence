# R483/R484 Stage 10 来源捕获分派 RED

## 结论

旧轮次 R483 完成 frontend warmup 并清理后，当前轮次 R484 作为唯一 gameplay 实例恢复了已准入的 R159 单玩家来源。loader、native readiness、MCP capability、error-log scan 与运行时加载顺序均为 GREEN。来源捕获在任何玩家切换、保存或游戏时间推进前因 operator 分派缺陷停止：继承的 AF5 `_run()` 调用了基类 validator，丢失已经通过 preflight 的 `source_player_character_id` 等目标字段，最终保留 `KeyError: 'source_player_character_id'`。

这是 harness RED。它没有执行 B1、`.90`、`.120` 或任何游戏输入，不能改变 P1 的 `8/9` 口径。P2 最终宣传视频继续 `LOCKED`。

## 生命周期

- 旧轮次 R483 warmup PID `32368`，完成响应式 Frontend 门后由受管生命周期清理；当前轮次 R484 gameplay PID `174416`，connection generation `1`。两者没有重叠。
- R484 在 `date_raw=53154120` 恢复玩家 `32904`，paused/map-ready，main-thread mailbox ready；loader gate 最终 GREEN。
- action 入口读取目标字段时立即 RED；没有 `set-player-character-v1`、没有 `save-checkpoint`、没有日期变化。
- MCP cleanup 请求 `r483-r484-stage10-source-cleanup-1` 只发送一次。canonical cleanup 与 managed cleanup 均 GREEN；R484 和旧轮次 R483 均已终止，CK3 与端口 `12438` 为零。

## 最小修复

`Stage10PlayerSourceCaptureOperatorJob._run()` 现在显式调用本模块的 source-specific `validate_activation()`，再把完整 bound 传给共享 `_execute()`。新增定向测试直接断言 worker 不会回落到基类 activation 合同。控制面、DLL、游戏文件、启动配置、加载顺序和产品树均未改变；仍只有 `status / capture-source / cleanup`，仍不允许 retry。

聚焦测试 normal/optimized 各 `4/4` GREEN，另有 `py_compile` 与 `git diff --check` GREEN。修复后必须使用递增的新轮次执行一次新 activation，不能在 R484 原地重试。

## 冻结证据

运行目录：`Z:\ck3_mod_rewrite\_runtime\p1-stage10-source-capture-r483-r484-c87f704-20260912`

| artifact | SHA-256 |
|---|---|
| native session start | `5BA31B8D9140FCD19FC9C5D4BF2D0288963FD4268EB857152B0BE48A83DD9741` |
| native readiness GREEN | `9B5C70B7D8F462301EA385CF0902FDCDF6DAB26FF4FD60C0A40AA81565D3FD9F` |
| loader gate GREEN | `4511D9DB164116B669DC4D7384A6EB55556B8628D3BA4A64A775FE864A71EF95` |
| source-capture RED | `38A803528911D272EF46662A710749C63778A47E53E2D51A75E1CC11C6D47FBA` |
| canonical cleanup GREEN | `0EE5E54EB16E874CBFFBCE88C68612F6D9837AC29515CA59C56D56B59359A21F` |
| managed cleanup GREEN | `1C6F6B35BBD4501C29594A04C5FD8EADA15504C68EC1C3BD0CCA235653EA7780` |

