# 原生观测返回后的处理继续使用原 scope 截止时间

机器：`xenoamess-full-tower-eb9d2c1186`。原失败及完整源码留在执行机器的 `failure125-readiness-deadline`；没有重放原世界动作。

## 实际故障与来源

2026-11-04，第125批的父动作已 APPLIED，收尾阶段取得的新原生观测时间为10:28:47.6150425Z。Driver join 后的校验时间为10:29:55.9444903Z，超过该次读取截止时间10:29:40.9215063Z，但尚未达到原批次截止时间10:30:14.3076572Z。此次周期尚未完成结算，不能把已观察日期提前计为保存或完成周期。

实际报告只有错误 detail，没有调用栈。源码定位链为 `SessionController.completeCycle → ready/available → RootSessionObservationPort.observeAfter → NativeReadinessCollector.observeBorrowed/capturePhysical/qualifyPhysical`，这是完整源码关系，不冒充实际栈采样。

调用者已经分别传入读取截止时间和整段处理截止时间。`capturePhysical` 正确用原 IO 截止时间约束 transport；`qualifyPhysical` 在 Driver join 后仍用这份较短的 IO 截止时间校验 now，并传给后续进程检查、能力投影和来源校验，造成预算接线不完整。

## 窄修复

仅修改 `NativeReadinessCollector`：原始读取保留原 IO 截止时间，观测时间必须不晚于它且不能是未来时间；接收后的处理使用已经传入的原 scope 截止时间。后续 lifecycle、capability 和 source 调用同时改接 scope，避免只改首个条件而把过期预算继续向下传。

最终 scope、writer head、原始 packet、Driver、进程、运输代次及来源检查保持原有语义。没有刷新旧命令截止时间、扩大预算、重试控制动作或重启游戏。单预算调用仍令 IO 与 scope 相等，原到期行为不变。

新增包内静态纯时间谓词供必要回归测试；它不授予物理或游戏权限。因为新增方法，不能将这份候选冒充仅修改方法体的原地重定义；实际运行采用仍由运行 owner 控制正常 Quarkus 新 loader。

## 验证与采用状态

- 单文件候选与实际运行源码基线精确对应，块外字节正逆验证通过。
- 独立 Test 源码已交付：5方法、10次断言，覆盖跨 IO 但未过 scope 的合法处理、观测等于 IO 边界、晚于 IO、未来时间、scope 严格边界及单预算基线。
- 生产975真实单TU编译exit0，生成38个class。执行器随后因Windows Path与字符串排序不同而报actor1；该失败和原END1保留。独立后验逐路径、大小、SHA验证38个现有产物完全一致，只解决排序载体问题并正常释放原资源，没有再次编译生产源码。
- 976仅编译这一个新Test TU，exit0，生成1个class。977于2026-11-04T11:25:35.913903Z记录五项测试全部成功、零跳过，进程exit0、正常fence/END。两项编译和五项DATA回归分别记录，不将测试准备、执行器元数据失败和Java代码错误混算。
- 该通过范围是时间谓词及当前生产源码的必要编译，不代替整条物理观测链或实机恢复。实际运行仍由owner执行官方Quarkus单源增编与正常新loader；本验收切点尚未授实际重载、LOOP或原周期结算成功。

## 本地模型参与

普通三消息 HTTP，4份完整当前源码，有限输出3500。实际完整 stop／DONE，模型耗时23.351秒、TTFT7.297秒，使用55660＋2865 tokens，cached tokens未报告。生产窄补丁代码原样采用，owner代码修正为0，仅投影到原文件行尾。

诊断、预算角色和具体修改合同已由owner确定，属于强引导实现，不是模型自主定位故障。独立测试另有一次8.870秒请求，owner修正两处import并合并方法，行为期待保持。准备、审阅、编测和恢复成本另计；没有新增OpenCode原生工具会话，也没有据模型等待时间宣称降低了总owner成本。
