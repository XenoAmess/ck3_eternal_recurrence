# 2026-10-11 公共队列提交开销优化

R53 所选第27天小回执显示，单日周期约40.74秒，host记录的五项原生步骤合计8.767秒。四次提交的文件mtime至host row开始间隔合计约26.95秒；这是文件时间代理，尚未分解为实际子进程、import、Git或bus的独立秒表。原host拾取ACK后的前三项等待仅0.156/0.103/0.149秒，没有证据支持靠缩短轮询消除大部分开销。

公共客户端新增有条件的进程内队列调用，复用冻结的完整queue/keeper/launcher模块。每次重新核验三个文件的精确bytes，缓存编译代码而非状态，不污染全局同名模块。仅当当前解释器与选定解释器一致、实际环境逐项相等且选定queue具备deadline API时使用；否则在首次提交前选择原子进程路径。尝试后失败不降级、不重放。

两次完整租约检查、每次合计四个Git调用和两个bus调用、once ledger、原子发布、ACK与业务结果区分均保留。原提交预算沿monotonic deadline传至每次Git/bus调用及keeper的有限追赶；没有额外等待线程，原hold UTC截止独立保留。原argv仅在子进程路径算实际执行，结果明确记录 execution_mode、argv_executed 和兼容原因。

2026-10-11 04:08:29–04:08:34 CST，外置003候选9项测试实际8PASS/1FAIL。失败暴露旧hold局部变量覆盖新增monotonic参数，最终发布前没有正确拒绝超时。004只把该局部变量的三个标识token改名，原hold90/0秒条件保持。04:11:03–04:11:07仅重验原失败项，实际1PASS/exit0，已通过8项不重复；原003失败原样保留。测试使用隔离文件和替身，没有实际bus、CK3或native调用。

ROOT采用四份生产文件和独立测试，精确核对前像/后像与AST；新增测试接入官方CI。[小原始证据索引](acceptance/2026-10-11-i4-queue-submit-overhead/INDEX.actual.json)保留两次实际测试、原失败、最小修复、来源和有界计时。`open_kaishek` 为not-applicable：本包覆盖Python提交和调度，没有新增CK3 script子集。

每日帧复用已将日常提交由4次减至3次；本包旨在减少另起Python进程的成本。实际提速仍UNKNOWN，完整I4预算、自然日、事件和结果门槛均不改变。一期保持75% / NOT_GREEN。新路径须进入新的共同Python source后实测，不能追认到正在构建的Source12或旧R53。
