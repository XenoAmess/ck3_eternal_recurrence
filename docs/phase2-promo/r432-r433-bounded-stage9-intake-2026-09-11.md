# R432–R433 Stage 9 有界准入与 R390 终态复用

日期：2026-09-11（Asia/Shanghai）

## 结论

R432 没有证明 Stage 9 存在产品 bug。它从过早的 checkpoint 启动，370 游戏日主要用于恢复 B1；到硬上限时
Central 尚未启动。R433 随即用零游戏日查询确认该判断，没有扩大 bridge、修改产品或续跑时间线。

现行 Stage 9 门已由冻结的 R390 实机记录收口：R390 在真实 Career Learning provider 终态
`zg361cl.390` / instance `1201` 上选择 authored `1` / native `0`，旧事件实例消失且
`postcondition_verified=true`。R390 的 23 个 Stage 9 provider/event 产品文件与当前 R430 候选逐字节相同，
因此该实机证据可以转移到当前候选。P1 从 `5/9` 更新为 **`6/9 = 66.7%`**；Stage 10、Stage 11 和代表性
终态 cold restore 仍为 PENDING，P2 继续 `LOCKED`。

## R432：到硬上限即停

- 输入为 R422 的 `terminal-partial-attempt-02.ck3`，SHA-256
  `9B8CA99765BC1AD78ADE1B3EAB6417060C7FFC29C9C942D88C8F29EECCAF7B7F`。
- 目标只允许等待 `zg361cl.390`，游戏日硬上限为 `370`，不连跑 Stage 10/11。
- 运行在 absolute deadline `54490368` 返回 RED：
  `promotion path exceeded its 370-day configured observation bound`。RED artifact 为
  `Z:\ck3_mod_rewrite\_runtime\p1-stage9-r432-20260911\live-artifacts\terminal-stages-red.json`，
  SHA-256 `2D33D87660BCC6D6EED0CFDDABD36687A88344CBD38C3398AB18D3EEAF557805`。
- 日志出现 `unavailable weak subjects pruned` 和
  `callback-free zero-survivor calibration cycle retired before restart`，说明 R432 确实先消费了 B1 恢复。
- 到上限后没有延期。canonical / operator cleanup 均为 GREEN，SHA-256 分别为
  `06513524F46FB60996100B83C364B0C011B6D6FD39DAEFFE3AC9198EBE1BC9F9`、
  `6943473B1C6054E0C6AFA9B6099059395F138BABA2A178074C90F5F5C35C4B70`。

## R433：零游戏日状态判定

R433 只加载 R432 的 autosave，保持暂停并读取已有 promotion-progress bridge；`date_raw` 前后均为
`54487200`，七项零推进检查全部 GREEN：

- `central_active=false`，Central stage `1–11` 全部为 false；
- `cl_partial_open=false`、`cl_digest_pending=false`、`cl_cycle_matches=false`；
- `cl_frozen_positive=true`、`cl_expectations_match=true`、AH/AI complete 均为 true；
- 当前没有 active event。

这组状态说明该存档未进入当前 Central 周期，不能用来诊断 Stage 9 provider。本轮 artifact 为
`Z:\ck3_mod_rewrite\_runtime\p1-stage-status-r433-20260911\live-artifacts\zero-advance-stage-status.json`，
SHA-256 `C4FCFAEE4F77B9C1D715A965A7A5827EACA1A138A9B352F97233285D15692689`。canonical / operator cleanup
SHA-256 为 `70F19ADA916F1A23F234125E0D5064EFDF62B8DA7038E066CE5CD6BB8AFB5F53`、
`0526AF1E094C00FADA265C1A25A6446A8D8B6CE706186A6D7ABDF300FE780F30`。

R433 附带的旧 B1 helper 把合法的零幸存者退役态判为 RED，因为它只接受有奖励的非零幸存者终态。该 helper
超出自己的适用域，不作为 B1 verdict；R430 的十项零幸存者后置收据仍是 B1 的权威证据。

## R390 Stage 9 终态复用合同

R389/R390 的启动报告把唯一 CK3 会话绑定到：

- source commit `7f21638a24183025935ccce04194759f2021e810`；
- product tree `8A260E2E3803AE329D875640563120E867CF3FBE21231011C251B9968E3322CB`；
- CK3 `1.19.0.6` / EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；
- PID `190136` / connection generation `1` / player `32904`。

R390 Stage 9 entry receipt 为 GREEN，并在 `date_raw=53615592` 真实暂停于 `.390`。冻结 continuation 随后记录：

- instance `1201` 的全部 identity、pre-selection、selection checks 为 true；
- authored option `1` 映射到 native index `0`；
- selection accepted，revision `941 → 942`；
- `old_event_instance_id=1201`、`new_event_instance_id=null`、`postcondition_verified=true`。

从 R390 启动基线到当前 commit `4553a429f69d1df15d31d59e14300067c7c33320`，Career Learning 的 20 个
effect 分片、`.390` 事件文件、Central Stage 9 分片及 serial pump 共 23 个加载文件逐字节相同。期间唯一 Central
产品改动是 Stage 11 的 `zg361_phase2_central_009_stage11_workforce_endgame_effects.txt`，不属于 Stage 9
provider/event surface。

机器门收据：

- `Z:\ck3_mod_rewrite\_runtime\p1-critical-path-assembler\r390-stage9-terminal-live.json`
- SHA-256 `6C91ADF634F32406B3368C8DE5859D4D1D59B5B45CAE190C5F2466B55CD1CB9E`
- 23 个 product-surface identity 与 21 项 gate check 全部为 true；归档过程
  `ck3_relaunch_performed_for_packaging=false`。

## 后续执行约束

Stage 10 必须另找真实 `zg361mg.120` provider terminal；R390 时间线没有该事件，不能把 Stage 10 N/A 或 Stage 11
事件替代它。Stage 11 因 R390 后发生过脚本修复，也不能复用 R390 的旧结果。后续只从更接近对应边界的 checkpoint
执行有限目标；小修只做因果范围内验证，单个 bug 不建立永久长跑场景。
