# R53 inputs 缓存回收：四批实际完成（2026-10-11）

R53 inputs 已实际完成4批，删除3,728文件、145,991,635逻辑字节。原 plan、apply、close command001 均退出0；apply 实际 UTC 05:46:03 至05:47:04，close05:52:39.664至05:52:40.551。原 [AGG、event、claim、CLOSED及命令证据](acceptance/2026-10-11-r53-input-cache-reclamation/INDEX.actual.json) 保留，AGG `all4_complete=true`、failure=null。4个 batch detail仅留原位精确引用，不复制明细账或重新读取缓存正文。

12项差异缓存保留。额外 ROOT metadata 命令退出0，`KEPT-TWELVE.actual.json` 在05:49:05.427400确认12叶都为 regular/present 且size与原值相同，共950,396逻辑字节；只stat、cache body reads=0。这证明保留时的存在与size，未新增正文哈希一致性结论。独有输入、SAVE、native及保留seed不在删除范围；旧prepared如需原路径验真为 `RESTORE_REQUIRED`，旧TTL不续。

admit001 原外层退出1，不能改成admit0：第一次入口已写有效AD，stdout单条APPROVED；thin随后重复调用已执行过的main，第二次入口被create-only拒绝。CLOSED原 `original_admission_outer_failure_recovery` 记录只接受既存第一次AD，未重放、未新增预约。原 RESULT/stdout/stderr与必要单入口/CRLF修正来源分列保存，原失败attempt不覆盖；后继005/H003静态审阅不代替本轮实际命令。

唯一事件 `lyd-closed-r53-input-cache-seed-base-20261011-001` 的145,991,635字节只claim一次，旧CASE5零marker及旧事件不重复扣。闭账前carry135,309,984,254，减本轮actual credit后为135,163,992,619；前值已计新增保留写入，不能直接从更早parent135,302,413,670裸减回收量。CLOSED remaining reservation=0，48MiB预约释放只结束future写入额度。known retained=5,762,220字节，加1MiB closing upper bound；fresh free=619,607,281,664，free差额不独占归因本次动作，逻辑删除量不等于物理分配回收量。

raw review 为2026-11-10T05:37:21.767370Z，compact review 为2027-04-09T05:37:21.767370Z；原缓存review仍2026-10-17T13:06:29.278808Z，不自动续期/删除。AD20246字节、来源索引/静态审阅及大identity/detail只保存外置精确ref。MAIN未由此包改动；此项只授存储维护事实，不授CK3/C3/B4/I4业务信用，Phase I仍75%估计、`NOT_GREEN`。
