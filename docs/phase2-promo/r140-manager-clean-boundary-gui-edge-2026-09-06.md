# R140 管理周期干净边界与验收 GUI 触发沿（2026-09-06）

## 实机结论

- frozen source：`84346622ac9023cfd24a9df8d2c625937ade80fc`。
- 产品仍是 R130 的 1,031-file 正式投影，关键 B2 文件逐字节等价检查为 GREEN。
- CK3 PID `197040`、connection generation `1`，默认 5 速推进。
- `tribute_mission.1002` 与 `tribute_mission.1005` 均按已登记的精确事件合同处理成功。
- 玩家始终为 CharacterID `32904`；本轮没有 owner terminal，不能计入健康保护的第三次角色死亡。
- 在 `date_raw=53154120` 首次取得 `review_now_eligible=true`、`b1_active=false`、`central_active=false`、`pp_active=false` 的暂停干净评审边界。
- `manager-cycle-recovery.json` SHA-256：`E50DD0E8EA9CF83BEC08DA9BD92514C0093284E09C9BCCC2645108B44BE14B70`。
- `runner-report.json` SHA-256：`CE395E028774D443FA122BCB2F0362AE3224C42CD651B5B3D03F20A6B2EA7911`。

## RED 分类

R140 的产品时间线恢复为 GREEN，最终 RED 位于 acceptance-only fixture：直接经理诊断 GUI 在存档载入时执行过一次，当时 B1 尚活跃；它的 0.5 秒动画状态结束后，不会仅因业务条件后来满足而自动重新进入。因此干净边界到达后，`zga_phase2_manager_seed.1` 没有出现。

这不是产品功能 RED，也不是 loader 性能 RED。R140 没有改动或否定既有单文件强制拆分规则；当前 fixture scripted-effect 文件仍只有 3 个顶层 effect，符合每文件 1–10、原则上不超过 20 的边界。

## 可复用经验

需要在长时间线之后执行的 scripted-widget 动作，不能依赖一个在载入时已经为 true、已经执行过 `on_start` 的动画状态“按 duration 自动重试”。应把一次性诊断与业务入口拆开：诊断状态负责载入帧证据；入口状态以完整业务门槛为 `IsShown` 条件，载入时为 false，待业务门槛满足时形成明确的 false-to-true 触发沿，再执行幂等 effect。

R141 的最小修复只增加上述 acceptance-only 入口状态，复用既有 `zga_phase2_manager_seed_maybe_begin_effect`；不写产品变量、不打开产品 B1、不改变 R130 产品字节。
