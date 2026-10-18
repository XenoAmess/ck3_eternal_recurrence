# R10 公共准备 case：正常 S0 与 typed readiness

离线实现来源 `40b331653107ec40ba410ce791cfd7b737e96c3b`；执行机器 `machine_id: desktop-3fevhd2-1c74096080`，2026-10-18。它补齐一个真实接口差距：旧 A/B/C relay 消费完整 envelope，公共 `CaseClient.execute_plan` 返回 control rows，军队 MCP 默认又只有 compact summary。这里复用 `ensure_common_full_army_client`，从原 host wire 恢复完整结果；保留 compact 原行、完整恢复 proof 与明确标注的 derived envelope。它没有建立 SDK、另启 host、改写原行或制造 Driver `raw_result_reference`。

公共入口用 `tools/ck3_mod_acceptance_r10_products.json`、产品 `war-episode04-r10`、case `r10-common-preparation`。它只准备普通 vanilla 保存的空 mod profile；正常来源沿用 `capture_bootstrap.checkpoint_source`，现场沿用公共 single runtime/allocator/keeper 和同一个 `CaseClient`。运行只执行当前暂停帧、full strength、typed commander、private current cash、occupation collection 和独立末帧，调用已有 `ready_t0_readonly_requests_12004/evaluate_episode04_ready_t0_12004`。它不推进日期、不提交 Move/split/merge/Save，不把 readiness 当共同 T0 或正式比较。缺省 `native_carmy_id/agreed_commander_id` 保持未知；原件会采集，但 readiness 不会因此获得通过。

`CommonRequestRelay.request` 提供旧函数的 `request/body/is_error/machine_id` 形状，同时写明 `transport_origin=derived_common_control_envelope_not_original_SDK_transport`。原 public 行和 derived body 可以不同；错误/未知请求在提交前记为已用，不能在同一 relay 重发。`army_history_evidence.raw_result_reference` 表示旧完整 Driver 文件，这里没有这种原件，不能伪造。现有 legacy live constructor 还限制 vanilla 分配 ID；公共 ID 不能改名伪装。这些旧 constructor 没有被跳过或动态重写。

纯 A/B/C 函数通过 `evaluate_policy_records` 复用：A 的 `admit`、B 的 `recipe`、C 的 `start`，保持既有实际参数与消费者验证；它们不调游戏。**公共 formal A/B/C stage executor 仍需继续接线**，本 case 和这三个 pure 函数不能称为已可自动完成 90 日三臂。下一施工直接使用当前 common client 的 full-wire references 替代旧 Driver-only reader，保留 once claims、逐日 exact-day、到场后 D90 及真实竞争终点，不把通用模块复制为新 host。

正式资格继续按 [共同 T0 合同](episode04-r10-next-abc-t0-12004.md)：先完成可回答的共同准备场和正常保存，再冻结 plan，三次独立冷载同一 S0。B 两处驻点必须分别具备同省静止、自然 callback province before/after、完整队列及实际正库存差分；月率正值不是增长。当前两站 `0/2`，正式 ABC `0/3`。`compare_fees=true` 必须等 R08 实际维护应用/payer/cadence 合格；不会把缺失费用填零或自行切换正式比较范围。

准备命令的真实公共参数如下；runtime 是届时重新绑定的共同 manifest，输入/预算由 Root 在新场容量准入后填写，不沿用 R208 的 deadline 或占用。

```text
<verified-python> -B -X utf8 tools/ck3_mod_acceptance.py prepare --runtime <new-current-runtime.json> --products tools/ck3_mod_acceptance_r10_products.json --product war-episode04-r10 --case r10-common-preparation --case-inputs <new-inputs.json> --prepare-output <new-prepared-directory>
```

OpenK 预验本包 `not-applicable`：不产生 CK3 script/fixture，只对 typed 原生查询与保存来源做 Python 接线。一个 compound synthetic 测试覆盖真实错配：原 compact 行和返回 full body 不相等时能保留两者来源，按已有组合器仅发送六个请求，Army 0 保留，重复 ID 在第二次发送前拒绝。它没有验证实际 ABI/军队/T0/库存/费用/视频，实际运行与正常闭场继续独立结算。
