# Shared acceptance keeper / queue 修复与 R0051 边界

15:55 UTC：两处共享Python工具修复已采用，验证通过；R0051业务仍RED，一期75%/NOT_GREEN。

keeper读取可能遇到同一owner心跳CAS已提交、OWNED_CAS journal尚未追加的竞态。修复仅在原严格owner/唯一资源/clean HEAD/新鲜度校验通过且sequence确实更新时，共享最多3秒等待journal追赶；返回仍要求真实journal和新的bus读取sequence完全相符，最多3轮bus读取。STOP、续租失败、过期、换HEAD和额外资源保持拒绝，未重放任何queue或业务动作。该源码竞态可确定性复现，R0051当次owner拒绝缺少带时间的bus原包，实际根因仍UNKNOWN。

queue原先只提取finished_native_exit_zero_proof，遗漏直接依赖finished_native_process_exit_zero_proof，导致正常退出后finish_hold确定性NameError。现在提取两份实际host函数并显式调用原success predicate，原一次性claim、schema、冻结身份、owner和原子发布检查保持。

旧keeper10项实际覆盖由初8项和更正夹具后的2项组成，最初错误期望和回执保留。采用后只运行新增截止时间跨越1项，通过；正式源queue六项通过。详见[原复现及更正](acceptance/2026-10-10-shared-acceptance-keeper-and-queue/INDEX.json)与[采用及实际验证](acceptance/2026-10-10-shared-acceptance-keeper-and-queue/formal-source/INDEX.actual.json)。原封包REPORT中pending/SOURCE_ONLY是封包时事实，后续采用以formal-source记录为准。

R0051启动首次root查询成功，未触发取消重试，不授该分支实机信用。实际推进6日，业务完整观察只覆盖前5日。初始SAVE证明冷却存在；无到期、最终SAVE或后续冷重载证明。原公开run/verify均返回2，原normal-close因上述NameError失败且没有normal-close-result。实际GUI退出及retained OS0成立；严格核验原target和三项claim均不存在后，只提交一个新命名行政finish_hold，独立取得native0/host0并释放现场。原业务与正常关闭失败保留，行政闭场不能追认通过。详见[R0051终态](../li-yu-dao/acceptance/2026-10-10-i4-natural-r51/REPORT.md)。

其他执行机器应通过master取得相同共享工具和可移植测试，既有冻结树保持历史原样。后继实机必须新冻结、新single-use case、新鲜Steam离线直接审阅及独立容量准入，不能修改旧冻结源或放宽缓存身份。
