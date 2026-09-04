# B3 manager 首次 live 启动 RED 与文件边界取证（2026-09-04）

状态：**RED / material-and-call-graph-closure**。这是 B3 的首次真实 CK3 启动证据，但没有进入 paused gameplay，也没有取得 manager/subordinate 业务后置条件；B3 readiness 仍为 `static-ready-live-pending`。

## 冻结证据

- 冻结 canonical 基线：`ce458af71a2a44decc085766720082a8b724edb8`。
- artifact：`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-b3-48da012-20260904-054011Z\artifacts-live`。
- outer `report.json`：1,963,629 bytes，SHA-256 `B319F853623FF9443F3941F4078559D6E24CDBF0EF5D75BDCEBE269A5D961923`。
- cell `report.json`：1,941,861 bytes，SHA-256 `8CCD24257185BB39529BCEC0FAE9F03ACAABCF281455CE55BC49D6C159E4AC56`。
- `cell/final_error.log`：1,640,782 bytes，SHA-256 `C52DC7DAA975A6EA8EB60CCEF5429E35B0299CCD4A090EEFBEE995EE491956CF`；同字节的 shutdown 副本为 `cell/11_shutdown_error.log`。
- cell 用时 `310.617 s`，`result=RED`、`gameplay_acceptance_executed=false`、`gameplay_green_claimed=false`。
- managed PID `26016` 已退出；`native_cleanup.result=GREEN`，其 supervisor/session/PID/tree/job/global inventory/watchdog/control-file 检查全部为 true，`native_driver_closed=true`、`native_runtime_locks_released=true`。

## 首错与递归闭包

`final_error.log` 在同一时间戳 `13:59:44` 给出两个真实 loader/material 错误：

1. `zg361_phase2_central_008_stage10_manager_governance_effects.txt` 调用未知 effect `zg361_p2c_record_stage_effect`；
2. 同一文件调用未知 effect `zg361_p2c_record_red_effect`。

首次 product 只物化 central `002_m275_requisition` 与 `008_stage10_manager_governance`，没有物化
`zg361_phase2_central_003_dispatch_control_effects.txt`。而 `003` 正是上述两个 effect 的 provider。对 stage-10 root 做递归静态调用图闭包后，还能看到 `008` 直接依赖同一 provider 文件内的
`zg361_p2c_mark_lane_busy_effect` 与 `zg361_p2c_schedule_pump_effect`。真实日志只需要前两个未知 effect 就足以判 RED；后两个是递归静态审计补出的未物化依赖，不能伪写成 CK3 已实际打印的错误。

因此本轮分类是 **material/call-graph closure RED**：源树中定义存在，但候选投影漏选其 provider 文件。它不是“文件过大”的因果证据，也不是排除更早脚本/物化错误后的纯 loader-performance RED。正确修复入口是闭合递归 provider 选择并重建同一累计投影，不是在当前证据上继续细拆 effect。

## 当前文件边界核验

在 `ce458af` 上执行：

```powershell
py mod_zhongguo_style/tools/effect_file_boundaries.py
```

结果为 `GREEN: 427 files / 3718 effects; target misses=0; >20 violations=0; max non-legacy=10`。即当前共 427 个 effect 文件、3,718 个顶层 effect；所有 B2+ 非 legacy 文件最大 10 个，目标遗漏 0，超过 20 的违规 0。B3 manager 自身仍为 7 个用途片 / 43 effects / 单片最大 10。

这次 RED 不触发 size A/B。只有候选已经排除更早的 parser/material/call-graph 首错，且仍表现为纯加载阶段性能 RED，才按 [`testing-workflow.md`](../testing-workflow.md#加载性能-red先验证文件边界与单文件体量) 固定 exact build、profile、树与探针，进行只改变顶层 effect 文件边界的同条件 A/B。否则拆分结果无法回答文件体量是否影响加载性能。
