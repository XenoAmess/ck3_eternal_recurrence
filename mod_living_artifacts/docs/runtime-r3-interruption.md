# R3：中断现场与资源恢复

`machine_id: pc-20260924rtuf-f11af23c08`。场次为 `pc-20260924rtuf-f11af23c08--living-artifacts--R0003`，源码冻结在 `3c0428b14d02f039de095719f4f80bd71c2b0a39`。以下事实来自该机器 2026-10-22 UTC 的实际观察，不作为其他机器的资格。

02:25:03Z 后台读回 Steam 离线，随后公共入口实际启动 CK3 PID 4288。02:28:13Z 原生流程提交过一次 Robert Start，结果为 `SINGLE_START_ACKNOWLEDGED_POST_STATE_PENDING`，禁止重投。最后保留报告仍为 RUNNING，含 493 次等待观察；地图就绪，但尚未取得夹具启动日志和独立角色绑定。因此该场没有进入产品业务验收，不能记为成长、装备或喂养通过。

02:28:53Z 显示设备仅枚举 640×480，实际游戏截图也为该尺寸；当时 CK3 日志选择 Microsoft Basic Render Driver。02:43:30Z 重新观察到 1920×1080 和完整显示模式列表。显示恢复不能反向补足旧场的业务证据。

用户中断执行后，原 run/allocate 工具会话已经不可查询。02:42Z 起实际进程清点未发现 CK3，后续双源 `tasklist+Toolhelp32` 与运行器进程检查也确认空闲；host、keeper、游戏等原 PID 均不在当前进程表中。原始 host/keeper wait、正常退出结果和最终 native report 均未产生。旧报告与五份安全控制文件完整保留，退出码继续为未知，不能补造正常关闭或 native cleanup 成功。

02:47:52Z 使用原任务总线的 CAS 将过期屏幕租约 **336 → 338** 释放为 `waiting / resources=[] / unresolved_red`。实际原件保存在外置工作包 `environment/r3-interrupted-resource-close-a01/`：`stdout.json` 为真实 CAS 输出，`current-empty-processes.json` 为双源观察，`closure-input.json` 固定全部原始输入；`qualification-error.json` 保留第一次因错误假设 supervisor PID 相等而被拒绝的结果，`qualification-a02.json` 保存修复后的真实资源资格。

共享修复位于 [中断资源校验器](../../tools/ck3_mod_acceptance_interrupted.py) 和 [公共 allocator](../../tools/ck3_mod_acceptance_allocate.py)。Windows venv 的 Popen redirector 与实际 interpreter PID 分别保留，逐个核实当前缺席。恢复过程核对原 frozen/READY/prepared、唯一 Start、原始控制 nonce、实际 canonical CAS 事件和当前双源进程状态；旧 state 保持隔离，不能用于新场，也不删除其 unsafe marker。公共 allocator 在写入下一份机器 admission intent 前，会在原 writer 锁内再次执行同一真实校验器。

验证为新增 **11 项回归通过**、校验器与测试两模块 strict mypy 通过；真实 allocator 中新增恢复函数和修改的 admission 函数，经实际 mypy 检查均无诊断。完整 allocator 仍有 33 项历史诊断，本次没有声称整模块通过。既有 adapter 25 项、missing-normal 12 项回归通过。新增回归及类型检查均进入持久 CI。

本轮还修正共享 CI 步骤的 `PYTHONPATH`，使其显式包含真正运行时使用的 SDK 源目录；原 CI run `39710147384` 的 `ModuleNotFoundError: xar_autoplayer` 失败保留，不能称为已经通过。

这些结果只允许继续准备独立的新场。完整实机验收、中文产品界面审阅、Workshop 上传、截图上传和缓存加载验收仍未完成。旧场最小关键证据及控制文件用于当前恢复与问题复核，最迟于 2026-10-29 UTC 复核用途，按仓库统一存储策略处理。
