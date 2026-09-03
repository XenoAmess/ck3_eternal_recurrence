# 天朝二期增量 P1：纯 case-kernel 实机证据（2026-09-03）

## 结论

P1 在 CK3 1.19.0.6 中通过了启动边界：日志出现 `Frontend` 与
`End loading of history`。因此，“一期基线 + 两个 case-kernel 文件”本身
不会把游戏卡死在早期加载阶段。

本轮不能算完整 parser/live GREEN：runner 的专用 wrapper-consumer observer
没有收到样本，最终 `result=RED`、`live_verdict=heartbeat_not_observed`；这与
CK3 已到达 Frontend/history 是两个独立结论。投影还会让一期的 seed dispatcher
看到尚未挂载的 B1/incident effect，`error.log` 中有 845 行脚本诊断，属于
刻意缩小投影造成的 projection RED，不是 P1 导致的 native 启动崩溃。

## 冻结输入与投影

- CK3：`1.19.0.6`；EXE SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- 源提交声明：`c91a1d01ee2708ae934591e4e8ae17e2f9bdf39b`
- P1 product：一期 byte-authoritative old-core 51 +
  `common/scripted_effects/zg361_case_kernel_effects.txt` +
  `common/scripted_triggers/zg361_case_kernel_triggers.txt`
- 文件/字节：`53 / 7,313,274 B`
- product/source-tree SHA：
  `f3edcb560e07f14967c73908b8558d252bd5d134ca7e3095d3a3dad72df37a7d`
- projection manifest：
  `Z:\ck3_mod_rewrite\_runtime\phase2-revised-checkpoints-20260903-manual\p1-pure-kernel\projection.json`
- manifest SHA：
  `05F85CAC9819FC4BA58028FAE02D20D70EC26450BCF29A2FC05E868ABDE382BA`
- 离线严格预检：
  `Z:\ck3_mod_rewrite\_runtime\phase2-revised-checkpoints-20260903-preflight\artifacts-p1-pure-kernel-r2\preflight.json`
  ，SHA `53988DB04F91F81814555222EA160AEE897EFE4B26F75004769C3E7A7797ED19`

## 实机 attempt

- 正式 attempt：
  `Z:\ck3_mod_rewrite\_runtime\formal-phase2-revised-p1-pure-kernel-c91-20260903-r4`
- runner report：`...\artifacts\runner-report.json`
- report SHA：
  `2517CEF49FFCD34CB1D1D79D03EBF4CFFA60DDECD540C63624C90F33E76D07FB`
- CK3 本轮 PID：`22996`；启动 `15:34:33`（Asia/Shanghai）
- `debug.log`：329,315 B，SHA
  `D6535C9B15D12D65A46E04942937FD336649E59F804B0330A48782731680D853`
- `error.log`：202,150 B / 845 行，SHA
  `7FC41C4F4F0DBC6D27B363E9EABC328661837147DBEBF2EF38F79DEEDDB9A85F`
- 关键 marker：
  - `15:35:25` `Setting idler 'Frontend'`
  - `15:35:25` `End loading of history`
  - `15:35:20` `>>> Total of : 881`（仅计数 marker，不作失败判据）
- 首要 projection 诊断：`zg361_b1_open_cycle_effect`、
  `zg361_ip_open_x_case_effect` 未在 P1 挂载；随后出现 `else` 级联和大量
  `set but never used` 变量告警。
- 清理：runner cleanup `GREEN`，进程树消失、最终 CK3/injector inventory
  为空、`contract_errors=[]`；runtime projection 与 clean-source 均保持不变。

## 当时的下一步（已由后续矩阵取代）

先对 P2 `02-b2-closure`（P1 + B2 effect/event/localization，64 文件）做
strict no-launch preflight；通过后再占用唯一 CK3 槽。P2 的 value/跨域依赖仍标为
conditional，不能把静态 Gate A/B 当成 parser-clean 或正式发布。

该步骤随后已经执行；最新权威顺序以
[`phase2-incremental-startup-batch-plan-2026-09-03.md`](phase2-incremental-startup-batch-plan-2026-09-03.md)
与 [`2026-09-03-vacation-handoff.md`](../handover/2026-09-03-vacation-handoff.md) 为准。
