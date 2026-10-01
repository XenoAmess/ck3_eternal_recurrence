# 2026-10-01：单日推进后的原生暂停拒绝恢复

R4 `root-first-heir-next-r4-07` 的生产调用为 `service.execute_step("life-advance")`，已有移动状态选择一日 timeline。原生 `set-speed-1`、`resume-map` 成功，清理用 `pause-map` 返回真实错误 `CK3 map state is unavailable`。Python 直接退出，地图仍继续运行。这是已发生的可靠性故障，本次修改只处理这条暂停拒绝。

冻结 L6 的 `native_driver.py` SHA 为 `09ee4f26a588c04cca4bfa257ae739f38a178a732a7d2db628946378adc2da19`。`_pause_life_advance` 从 19751 行开始，首个 `_execute_primitive_step("pause-map")` 位于重试分支之前。`_NativeCommandRejectedError` 保存 `native_error` 后直接抛出，因此既有第二次 pause、同 owner 检查、deadline 与 paused frame 观测都没有机会执行。共享 S 的对应方法应用前与 L6 原始字节一致。

失败前日期为 `53169240`，请求的下一日应为 `53169264`；稍后的 SDK frame 为 `53169336`，相对本次起点已多走 4 日，相对 h82 checkpoint `53169096` 已累计 10 日。root 后续 `113035/pause-result.json` 记录 `submitted`，紧接着的 `snapshot-after-pause.json` 仍为 `paused=false`。这再次证明 ACK 不能替代暂停后置状态。

最小修复只修改 `_pause_life_advance`：首个请求捕获 `_NativeCommandRejectedError`，仅当 `native_error` 精确等于上述错误时记录 `accepted=false`、`status=rejected`。随后刷新 semantic frame；恢复到 `map_ready=true` 时立即进入原有一次重试，不等待未被入队的首个 pause 生效。已接受请求继续等待 paused；其它原生错误照旧抛出。

重试仍使用原有 owner 判断、同一 command deadline、最多两次请求和真实 paused snapshot；公开 primitive revision 行为、一日 horizon 与其它步骤未改。恢复 actions 保存第一次拒绝与第二次实际 ACK，成功只来自随后观察到的暂停状态。没有增加 capability、协议字段或新门禁。

独立 `tests/unit/test_life_advance_pause_map_unavailable_retry.py` 不读取本机 artifact，不连接真实 pipe。它使用 synthetic endpoint 与状态帧，走完整 `driver.execute_step("life-advance") → _execute_life_advance → _execute_primitive_step → _pause_life_advance`。真实错误字符串保持原样，角色、日期、栈、连接和暂停发布均为合成数据；移动状态只用于选择相同的一日 horizon，没有执行军事命令。

四个定向测试 GREEN：首次拒绝后第二次请求及独立 paused frame 使 1 日推进成功；第二次仍拒绝时保留两次 bound；无关原生拒绝不重试；第二次只有 `submitted` 而没有 paused frame 时仍报错。没有重跑旧矩阵。初始测试夹具误选了多日 horizon，已中断并修正为合成移动状态；这不是实现失败。

机器合同在 `ck3_autonomous_player/native_bridge/research/fixtures/life_advance_pause_map_unavailable_retry_v1_source_contract.json`。实际故障、冻结方法、外部候选及应用记录保留于主 workspace 的 `artifacts/g2-offline-2026-10-01/pause-map-rejected-retry/`，生产应用与测试结果见 `production-result.json`。`production-application.json` 证明方法以外的共享文件字节保留，L6 未修改。

本次代码 readiness 为 `static-ready`。root 后续使用新 R7 runtime 做正常 `life-advance` 并确认稳定暂停；不人为制造 map 故障，不把 synthetic frame 称为实机。此工作包没有 CK3、pipe、UI 或 Git 操作。
