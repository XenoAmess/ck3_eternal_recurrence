# R11：预览中止与失败资源收尾

机器为 `pc-20260924rtuf-f11af23c08`，场次为 `pc-20260924rtuf-f11af23c08--living-artifacts--R0011`。实际场次在 2026-10-22 UTC 执行，使用 c13、来源提交 `abcfefeda3f2d140a80b6c161e15f9215c859938`。本记录于 2026-10-22 16:35 UTC 后核对原件；精确路径、SHA 和核对时间见[来源回执](evidence/r11-preview-failure-and-resource-close.json)。

`feeding_preview` 的原始结果为 **BLOCKED**：实际自然推进 0 天，保存观察 1 次；四项正式检查均未通过。第二次人工预览回执被当时的图片时效守卫拒绝，原始诊断是 `ValueError: PNG is stale or outside this event review`。后续源码修复不改变 R11 的结果，也不把它记为喂养通过。

保留了以下局部实机证据：

- 玩家 `31254`、活武器 `402`、普通材料 `403`，事件 `xalw.11` 实例 `3`。Root 的首份原图审阅记录显示基础经验和本次经验均为 **80**，普通材料名显示正确；原图捕获于 15:21:29Z，审阅操作记录为 15:22:07Z。
- 随后选择来源定义中的 `xalw.11.cancel`（“保留材料”）。`preview-cancellation.json` 保留原动作、取消前后两个独立库存查询和返回管理事件的查询。它是已执行路径的局部证据；正式 `PREVIEW-CANCEL-01` 单元仍保留原来的 BLOCKED。
- 再次打开同种材料的确认事件，实例变为 `5`。第二份原图审阅也记录显示 80，但本场消费者拒绝该回执后停止业务流程，未提交喂养确认。只有初始保存，没有材料消耗和经验结算的保存后态，因此不能证明喂养交易、四种稀有度或日志检查通过。

收尾保留原始 **public exit 2、host exit 1**。原持有句柄的等待未被触发，`exit_code=null`，OS0 未获证明。其后的原生报告记录 `exit_reason=stop`、强制清理的 CK3 退出码 `1`、Job 活动进程数 `0`、进程树消失和控制文件清除；这些事实不构成正常 GUI 退出或 native0。

Keeper 经协作 STOP 后，由原父进程实际等待返回 `0`，线程结束、无 keeper 错误。屏幕任务 `ck3-living-artifacts-screen-a14` 在 CAS 序号 `520` 进入 `done`，`resources=[]`。共享 `previous_failed_live_resource_closure` 于 **16:34:06Z** 实际验证原件和当前进程状态，扫描 170 个进程且无运行时占用，并确认原 game、host、keeper、supervisor、公共 run/allocate 进程已结束及控制文件缺席。该结果仅允许下一场申请资源；`business_pass`、`release_pass`、`normal_close_qualified`、`typed_normal_exit_proven` 和 `actual_retained_os0` 均为 false。

资源封包沿用已有 `ck3-mod-acceptance-failed-live-resource-closure-v1` 和 `retained-wait-expired-then-native-cleanup` 分支。共享消费代码补充了真实 `command/intent/process/exit/completion` 五份原件的合同，以及顶层 `error=null` 时必须绑定具体失败步骤的诊断；同时修复 Windows 命名管道参数不能作为磁盘路径解析的实际故障。旧 host0 STOP 分支和原始场次文件均未改写。49 项相关回归通过；原样提取的 11 个完整函数/类型定义及新增回归整文件 strict 通过，未宣称整个历史 allocator 模块 strict 全绿。源码回归使用带真实来源 Pin 的小型摘录与明确构造的临时文件/进程观察，不能作为新的实机通过。

外置下一场 `previous_failure_close` 输入是 `environment/r11-failed-resource-closure-a01/closure.json`（8943 B，SHA-256 `5f99c44f1449c0a9b8ee7de70084692648898d38906042ba1adc160ba2e375c9`）。下一次 allocate 仍须通过共享代码重新核对当前资源；本记录没有启动 CK3、创建新场次或发布产品。

16:37:51Z 对本场完整 `error.log` 的[只读复查](evidence/r11-error-log-summary.json)另提供局部 UI 修复证据：24 条均为静态告警，未发现运行时或未归类错误；真实打开管理页与普通材料确认页期间，R8 的缺失 `xalw_suppression_timer_sequence`、材料 scope 和 tooltip 错误未复发。此复查不改原场次 BLOCKED，不授予实际喂养、付费镇压或完整发布通过。R10 使用另一份 NPC 夹具，其 28 条静态告警不能与本场数量作业务错误增减比较。
