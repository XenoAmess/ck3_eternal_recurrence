# 第一期机制实验的同进程启动恢复

此能力供共享验收队列使用。默认仍拒绝失败的宿主；只有显式传入原始 typed startup 错误及原操作者，才允许在原诊断 hold 内继续既有查询、事件选择、保存和正常退出接口。实现为 `tools/ck3_mod_acceptance_queue.py` 的 `validate_startup_failure_recovery`，不增加游戏原始命令或推进日期通道。

准入继续校验原冻结 argv、原 lease、实际 PID/create_time、state/pipe、原 manual-quit checkpoint 和原 hold deadline，并留出退出时间。恢复计划沿用公共 MCP schema、once ledger 与原子发布。旧错误报告先冻结，新操作单独记录；不能清除旧错误、重放未知结果动作，或将恢复后的局部成功写成整场验收通过。

## 2026-10-17 实际使用

`machine_id: 4-8e1c2f1861`；观察时间为 2026-10-17T08:40:11Z 至 08:57:50Z。证据根为 `C:/workspace/ck3-faith-and-power-20261017/episode01/live/4-8e1c2f1861--faith-and-power--R0001`。来源为原 `native-report.json`、`startup-recovery-operation-*.json`、`root-native-receipts/*.json` 及原始进程等待记录。原 CK3 PID 为 18236，create_time 为 1792225427.692187，connection generation 为 1。

原启动观察器先见 `fp3_struggle.0051`，并非准备事件，因而保存严格合同失败。恢复期间未重启 CK3，也未更换其加载输入或 native DLL。采集原事件实例 2 及实际唯一选项后，一次 MCP 选择首显示项；独立后读确认实例 2 消失，准备事件 `xar_faith_h01_prepare.1` 实例 1 出现。两个准备选项原生映射为 `[0, 1]`，重验证回执保存为 `startup-packets-revalidation-01.json`。该回执不追认原启动成功或产品验收通过。

2026-10-17T08:53:48Z，共同母档 F 实际保存，50,308,970 字节，SHA-256 `786afb9eb40e8952d8aeade35eebd869ad7c7383fc28894389e2859451f750f1`；随后在原存档覆盖前复制为外置活跃输入 `episode01/scenario/saves/F-pending-prepare.ck3`。08:54:52Z，一次选择准备事件的 A 项；独立后读确认事件消失，玩家 15893 的 rite 13 / faith 50 未变。08:55:22Z 保存 A，50,214,831 字节，SHA-256 `8cadd902d3360995ecfb1541013a72b80408ff041e25b9627592553e2cf9f662`，另冻结为 `A-hanafi-prepared.ck3`。这些是明确标注的独立机制实验输入，不是罗贝尔普通战役成绩。原保存结果中的 driver-state binding 仍为 `unconfirmed/save_binding_mismatch`，不以文件存在或 SHA 一致追认该项；下一次加载必须重新核对玩家、日期、礼仪及事件状态。

08:55:43Z，正常退出的只读查询在 Python 预验层因游戏改写 `profile/pdx_settings.txt` 被拒绝，尚未发送原生退出请求。异常逃出原诊断 hold，原宿主 finally 结束受管会话。实际保留 CK3 HANDLE 返回 exit code 1，宿主原 Popen 返回 1，公共 run 返回 2；该场为 RED，正常 GUI 退出未通过。资源回收不等于正常退出或业务通过。

08:57:29Z，确认原宿主与 CK3 已消失后才请求原 keeper 的合作 STOP；原 allocator/keeper 实际等待返回 0。08:57:50Z，原任务 `faith-e01-shared-a01` 以实际 CAS sequence 11222 释放，task 为 done、resources 为空；原件为 `root-screen-release-a02.json`。`a01` 是缺少 CLI SHA 参数的真实拒绝回执，保留不覆盖。

未来启动顺序已在[原版开局事件专题](fp3-struggle-intro-and-fixture-startup-order-12004.md)修复：先分辨实际 typed event，再使用共享规则或用户授权的第一显示项续行策略，最后严格观察准备事件。游戏改写设置文件导致的退出与录制错误需要共同修复运行期输入分类；本恢复接口本身不赋予这两项通过资格。
