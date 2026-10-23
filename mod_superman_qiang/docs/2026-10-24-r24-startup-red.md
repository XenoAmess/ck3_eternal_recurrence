# R0024 解析与夹具启动失败

本轮不是业务通过。`machine_id: desktop-3fevhd2-1c74096080`；观察范围为2026-10-23T16:26Z–16:48Z，CK3 1.20.0.4/build25734779，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。公共 run 为 `desktop-3fevhd2-1c74096080--superman-qiang--R0024`，原始现场保存在 `C:/ck3-superman-validation-20261023`。

游戏实际进入地图，但没有推进到夹具第1天，没有真实基线保存、月度计数结果或通知复现结果。原生 error.log 证明局部 helper 无法在新事件文件中解析，且7个覆盖事件缺少明确优先级。其原件 SHA-256 为 `736d2bec0bc49631d1f2d61a8626f999ebebe81265af59ffeee25a3a9fcc73c8`。修正及来源守卫见[解析修复](2026-10-24-inline-projection-repair.json)。

公共启动 policy 等待 `BASELINE_READY`，夹具却在 `days=1` 才产生该标记；初始暂停造成等待环。另一个离线复查发现 `SAME_MONTH_READY` 未进入实际 marker inventory，第二阶段不能被命名触发。自然夹具现在即时产生独立 ARMED，只把它用于启动资格，业务继续要求第1天 BASELINE；receipt明确列入同月阶段标记。自然与通知夹具的游戏脚本补齐BOM和真实事件主题。

原公共队列在启动等待阶段拒绝正常退出查询（`Original shared host is no longer held`）。Root保留原PID 28300的同步/查询句柄后，经原窗口标题栏关闭按钮打开普通退出确认，直接审阅自动保存未勾选，再通过统一坐标换算工具点击“退出到桌面”。未发送生命周期 stop、未调用强制终止。retained handle于16:40:26Z返回退出码0；原生会话独立报告 `exit_reason=process_exit`、code0、Job在清理前已为0、watchdog/control清空。随后公共 `failure_shutdown` 的一次 `finish_hold` 保留原错误并结束host；host仍RED，`normal_close_qualified=false`。

操作证据：

- `ops/R0024-operator-retained-exit.actual.json`，SHA-256 `3bea3d1dc3c06376c4288f8b2748a30c07ba01d3a0b1cdc80003977f5ff0ecd4`。
- `ops/R0024-titlebar-focus-click-a01.png` 是实际自动保存未勾选画面；`ops/R0024-normal-quit-final-click-a01.png.json` 是最终换算、前台PID及点击回执。回执不单独证明退出。
- `runs/<run-id>/native-report.json` 保留原失败、原生清理和 `post_failure_exit_finish_hold`；`host-original-process-exit.json` 证明原host Popen实际返回1。
- keeper实际退出0；`ops/R0024-screen-release.actual.json` 的CAS8454已done且resources为空，SHA-256 `d3b89f2c4cf6091e0cd88d848f95e1eb5e15ea06908518d1099b301b4282ea71`。后继使用现有 `previous-shared-managed-session` 清理资格，不将它计作业务通过。

2026-10-23T17:04Z，修正后的完整产品CI命令组实际通过：共享发布13项、产品发布/通知夹具11项、运行时与自然夹具58项，共82项；静态验证和35文件构建检查通过。严格mypy检查gen/runtime_data/product三个完整文件，普通检查加 `--check-untyped-defs` 覆盖validator/prepare/test_runtime三个完整文件，均通过。另以实际安装核对完整来源、9个定义、10个局部helper与EXE，静态报告为 `ops/source-validation-repair-a05.json`，SHA-256 `7a51eb221324b93db59e112d98a7f4d76ea41543652c497f7e84d2daf658cdfc`。这些结果不替代下一轮引擎解析与业务验证。

生成投影和10个原版helper快照保留来源空白；`git diff --check` 对原版行尾空白返回2，不能通过清理这些源文本破坏逆恢复合同。其他自有代码另行检查。未上传Workshop。

原始场次/截图/日志按[通用存储策略](../../docs/storage-retention-policy.md)在2026-11-22复核；当前保留理由是解析失败与启动等待的首份实证。小型结论及身份回执在2027-04-22复核，不构成无限期保护。
