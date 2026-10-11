# I4 日期读回与失败退出的共享修复

[R61](2026-10-11-i4-r61-case12.md) 的运行中观测仅触发第 31 项拒绝：心跳日期比语义快照提前 24 小时。Python 目前分别接收 heartbeat 与 semantic 数据，返回对象可能包含不同发布时点的信息；具体 native 发布次序与延迟原因仍 UNKNOWN。

共享 host 现在只对这一种运行中、无事件、同 owner、无其他拒绝的观测继续只读等待。它保留原来的截止时间，记录待定观测但不计业务进度；后续必须通过原 32 项完整资格及 successor 检查，并追上已观测到的最大心跳日期。其他日期差、身份或拒绝计数变化、时钟回退、事件、取消、超时仍拒绝。它不修补字段，不重发 pause／resume／speed；最终原有暂停及业务断言保持。

once-only queue 的 `finish_hold` 现在显式支持 `failure_shutdown=true`，调用冻结 host 已有的严格 failure-shutdown 原语。默认／false 继续使用原正常退出原语，非布尔值拒绝；原 HANDLE exit 0、managed session 完成及 cleanup 条件不变。失败退出不能取得正常关闭或业务通过资格。该修复的外置精确候选已经在 R61 完成一次实际生命周期恢复，host 原始 wait 仍为 1。

定向验证：日期收敛七项测试于 `2026-10-11T13:20:15Z` 实际通过，覆盖实际 advance 入口、唯一日期差、原截止时间、零动作重发及身份／其他拒绝反例；queue 五项测试于 `12:42:07Z` 实际通过，覆盖失败／正常原语隔离、once-only 发布及严格负例。两组均已接入正式 CI；本记录不预报 CI 或后续实机结果。原件见 [日期测试命令](acceptance/2026-10-11-i4-r61-case12/raw/date-convergence-test-RESULT.actual.json)、[日期测试输出](acceptance/2026-10-11-i4-r61-case12/raw/date-convergence-test.stderr.log) 与 [queue 测试](acceptance/2026-10-11-i4-r61-case12/raw/queue-fix-TEST-RESULT.actual.json)。

Source18 与 R61 冻结输入不变；下一公共实机必须绑定包含修复的新 Python source，继续复用已选 native 与经审阅的缓存兼容输入。R61 保持 RED，一期约 75%（估计）／NOT_GREEN；尚无 I4 自然到期、事件选择或冷重载新增通过。
