# R0001 首次加载：fixture RED 与最小修复

2026-10-03，主执行者启动 `bf-202609141645-5434332d4d--de-jure-conquest--R0001`，本机 CK3 1.20.0.3、Steam build 25652598，真人入口为1066罗贝尔1128。主执行者回读暂停、map_ready、角色运行时ID31254、日期raw53144328、无战争；完整加载和费用证据由主执行者另记，本记录只冻结本轮 fixture 诊断与修复。

对该 attempt 的真实 `state/profile/logs/error.log` 只读保存了 [当时日志快照](fixture-initial-load-red-2026-10-03-R0001.log)。它包含27条 `jomini_eventmanager.cpp:599`：`events/djct_duchy.txt`、`djct_kingdom.txt`、`djct_empire.txt` 使用 namespace `djct` 却未在各自文件声明；另观察到2条 `jomini_effect.cpp:1146`，指出 `djct_outside_holder` 已赋值却从未使用。后者计数只是本次快照，不是尚在运行的 attempt 最终日志总数。

这是 **HARNESS_RED**。结构 parser 只证明括号和条目结构，之前的 parser PASS 不能证明 CK3 跨文件 namespace 合同。此轮实际读取的加载 RED 不可被后续修复覆盖，也不能把费用验证或尚未执行的九场战争写成 GREEN。

`tools/gen_acceptance_fixture.py` 只做两处最小修复：为三份场景 events 文件分别写入 `namespace = djct`；删除真正未使用的 `djct_outside_holder` 赋值。其余初始准备、战争、参战与结算逻辑保持此次候选字节。费用资源准备另有外置 setup-only inbox，只加资源与威望等级，既不触发事件也不启动战争。

新 fixture 位于 `C:/workspace/two-mod-maintenance-20261003/de-jure-fixture-R0003/`，旧 R0001／R0002 与 R0001 live attempt 的冻结 fixture 均保留。逐文件生成一致性、Clausewitz 结构 parser、各 events 文件独立 namespace 检查通过；9场／72条预期 PASS 合同原样保留。16份 runtime 与 R0001 production 逐字节相同，**runtime改动0**。证据与全部新 fixture SHA 见 [修复复核报告](fixture-minimal-repair-review-2026-10-03-R0003.json)。

R0003 仍为 **live NOT_RUN**，等待主执行者新 attempt 做 clean 加载与九场矩阵。现有 fixture 对重复授予同持有人、串行战争后完整辖域／休战未恢复的可能状态污染暂不猜改；只有实际日志与状态 RED 到来后再最小修复。
