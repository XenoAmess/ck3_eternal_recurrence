# 礼与道 R0005：加载 RED，随后观察到崩溃

本轮结论 **NATIVE_LOADING_RED_AND_CRASH_OBSERVED**，`normal_exit=false`，`cause=NOT_PROVEN`。实际冻结提交 `18b1944d1784d3e4ec57189c016335ef135b9b34`，产品树 `77f74591f299874efcd20c2672f143c362e54caa`，CK3 1.20.0.3 / build 25652598。已保存的[两套官方 L0 CI](ci/README.md)成功，不能据此给本轮实机通过。

实际 run `bf-202609141645-5434332d4d--li-yu-dao--R0005`、execution `bf0a2e3a-f038-4fac-9ab1-f7b6d1ccba6d`、任务 `ck3-lyd-live-006-20261004`，PID12524／HWND7406548。正式生产59件＋普通入口夹具7件＋R5 I2夹具7件，逐项核对[原 PREPARED](inputs/PREPARED.json)和实际挂载字节／SHA。原[生产 manifest](inputs/production.manifest.json) SHA `f938644617764247bdec21eacd7023a5f93c0c79c5c48972b9483f9c20720692`及两夹具报告原样投影；I2输入为全36派、setup预期35+1的冻结R5候选，不能记成setup已执行。

## 加载错误与实际进度

[最终 error.log](logs/crash-observed/logs/error.log)为840bytes，SHA `3c6efe65ca5e46aa5604eebbc3a401cf8a4bfe9cfac9184d36ffa7bbdd5319d5`，共4个[E] header：I3 `hidden_trigger`未知1条，I3非法连续`prev`链3条，位置分别line71两实例、line135一实例。[分类账](error-classification.json)保留原行。旧R4同核心／参数divergence、夹具employer/location和变量使用诊断均不在本次实际最终error中；这个有限的日志事实不证明修复后正式流程已运行。错误与随后崩溃的因果关系尚未建立。

[11:24:17Z 的原图](screens/normal-exit-check.png)直接显示CK3大厅／主菜单，[原元数据](run/normal-exit-check.json)绑定该图SHA及CK3 foreground。文件名含normal-exit，但图中CK3仍存在，不能算正常退出。启动及loading帧和[退出前快照](logs/pre-exit/report.json)原样保留。未开始campaign、未attach、未取得当前native profile或实际角色ID、未保存；I1/I2/I3/I4所有正式玩家流程、D+1、D+30、reload均 **NOT_RUN**。native-profile.template仅为准备模板。

启动前[新鲜Steam位移原图](offline/steam-moved.png)、[位移收据](offline/steam-frame-freshness.json)、[root离线审阅](run/offline-reviewed.json)绑定同一图哈希并记录“离线模式”。本包只读取旧原件，没有操作当前Steam。实际设置文件与请求值另在[JSON报告](report.json)记录，未给campaign设置UI验收信用。

## 退出请求、崩溃与操作证据边界

根于 `2026-10-04T11:21:44.417217+00:00` [向实际CK3窗口posted WM_CLOSE](run/normal-close-request.json)。原件秒数为11:21:44.417Z，口头约11:21:45；请求本身不证明退出，也不证明崩溃原因。随后[exception原件](crash/ck3_20261004_192419/exception.txt)记本地19:24:21（UTC+08换算11:24:21Z）的 `C0000005 / EXCEPTION_ACCESS_VIOLATION`，CK3栈帧均无函数名，不能判定具体根因。

root工具输出说明11:27:32Z的坐标命令被参数校验拒绝，未发鼠标／键盘输入。本地没有独立原始拒绝命令stdout/stderr或点击receipt，因此仅保留[已有crash报告中的来源注记](logs/crash-observed/report.json)和helper源码，不制造拒绝执行证明，不记点击、成功退出或因果结论。

实际[crash报告](logs/crash-observed/report.json)观察到CrashReporter PID2596／HWND13829678；helper对其语义WM_CLOSE请求，未提交崩溃报告。[11:31:22Z进程回读](run/crash-exit-processes-001.json)随后确认CK3与CrashReporter均不存在，并明确normal_exit=false、termination=CRASH_OBSERVED。这是崩溃后生命周期闭合，不是正常退出成功。

[keeper FINAL](lifecycle/keeper-FINAL.json) seq2698、thread_exited=true、failure/entry_error=null；screen_released=false保留原值。[随后CAS2699](run/screen-release-completed.json) resources=[]、done、精确head18b1944d；[allocator completed-red](run/allocator-completed-red.stdout.txt) seq5绑定同一run/execution，reason明确记录加载错误、WM_CLOSE后观察崩溃、无campaign/attach及reporter已闭合。旧attempt和状态原件没有改写。

## 永久小包与保全

原7件crash文件合计39,858,628bytes完整保留在外置原目录。[crash索引](crash/original-crash-index.json)记录每件原路径、bytes、SHA；小包逐字节复制exception/settings/meta及3个log，**不复制**39,386,417bytes minidump。其[元数据](crash/dump-metadata.json)只含精确原hash／header，未作符号化或dump诊断。

[完整外置原件索引](full-external-index.json)记录命名R5根及省略项，包含所有dump、cache、ZIP、keeper明细身份；原件永久保留。本包收录freshSteam PNG／回执、原launch/frames、59+7+7挂载源、退出前与崩溃后最终日志、退出case原件/helper及精确18b CI初始pending至终态包，不裁图、不改日志、不借用R4或后续修复输入。[JSON报告](report.json)和最终index绑定全部投影。本包生成未改tracked、未操作游戏／屏幕，未重读CI。
