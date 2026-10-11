# I4 R57：一个完整自然日后 owner/clock RED（2026-10-11）

R57使用Source15/O15、CASE8及a19，冻结checkout为 `91fabf43ae4b9c162a8cdcbd2ab98bbf353cb62f`。一个完整自然24小时已通过，day0003日期为53144736；第二次推进 `case-natural-day-0004` 失败，原错误为 `RuntimeError: campaign pause readback owner, clock or rejection state changed`。失败行没有 result、before/after 或具体typed predicate/context。

原OR条件六项均 **UNKNOWN**：identity_matches不成立、rejections改变、date倒退、public revision倒退、native revision倒退、pump倒退。至少一项触发，但当前原件无法确定是哪项；失败发生于preflight还是postpause也未保全。`allow_event_boundary=true`只是允许参数，不能证明事件发生。历史 `stress_points is malformed` 字符串不能证明本日新增拒帧，不能据此追认因果或补自然日信用。

现场以失败合同完成资源闭环。原public run在02:56:45.741269→03:08:29.297999 UTC返回2，verify返回2；原host PID13824 retained Popen wait实际1。原native的有限清理投影保留RED，managed thread finished与cleanup_ok为true、tree/job/control无残留，CK3 exit1；这不是正常GUI退出资格。ROOT直接审阅新的Steam离线图并恢复原显示1024×768×32@60；keeper failure=null/thread_exited=true、last_sequence4749，原allocator wait0。release-command-001实际0，释放回执见封存原stdout。

诊断读取保留两次实际历史：首次投影cap失败，随后ROOT明确授权一次纠正读取；无第三次native读取，也没有第二次读取day0003。纠正读取的同一raw缓冲生成cleanup projection，未为闭场重开native原件。READ/EXTRACT/INDEX及首次失败回执均原bytes封存；本发布包只读取这些既有小文件，没有读取native报告、SAVE、缓存、PE或图片。

exact91fab的Official Runner CI与Linear history均已SUCCESS，见封存metadata观察报告。CI成功不改变本场RED；没有GUIclose、expiry、SAVE或coldreload业务信用。第一期仍 **75%、NOT_GREEN**。014容量预约实际CLOSED尚待ROOT追加，本文不假填其终态。

后继最小诊断接点是保留原六项守卫和失败时点，追加精确predicate/source/current binding及调用点。此处没有生产修复、重测、重queue或实机重试。

精确原件、宿主/命令退出与现场回执见 [证据索引](acceptance/2026-10-11-i4-r57-owner-clock-red/INDEX.actual.json)。原保护与复核期限不续；原始证据按统一有限保留策略处理，正文不代替可用性登记。


## 11:30–11:35 CST 实际后继

014已实际闭账，原命令exit0；新增已知保留799291222B，保守carry136061962175B，未来预约0。首次1MiB receipt上限拒绝、第二次任务总线新鲜度拒绝均保留；仅将实际1291508B缓存复制回执的单处上限改为2MiB，刷新ROOT/coordinator状态后闭账。未读取native正文或重复抵扣旧清理信用，原quota/TTL不续。

宿主补入六项拒绝条件、source/current typed binding和五个调用点，沿既有exception→失败step→finally write持久化；原OR、错误字符串和readmission不变，不追加RPC或重试。新生产失败路径测试首轮fixture缺JsonLines依赖ERROR保留；修正fixture后仅两个失败方法重跑2 PASS，之前成功的调用标记/成功路径方法不重复。精确源码/AST保留检查及原回执见[后继索引](acceptance/2026-10-11-i4-r57-owner-clock-red/FOLLOWUP-INDEX.json)。状态STATIC_READY / LIVE_NOT_RUN；本次R57具体原因仍UNKNOWN，未授业务信用。
