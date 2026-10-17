# C盘旧shader BATCH02精确回收

`machine_id: desktop-3fevhd2-1c74096080`。本记录仅证明该来源机器当时的结果，盘符与路径不是跨机器前提。归档候选准备UTC：`2026-10-17T01:55:30.960295+00:00`；沿用既有实际回执与独立读回，本次没有新增清理、扫描、原片读取或实机复测。

按[通用存储策略](../storage-retention-policy.md)与[参数1.0.0](../storage-retention-policy.json)，Root确认R195已正常exit0，后继R196及未来工作不消费R183/R184/R185的这3份旧warm cache，派生角色已结束。因此允许用途到期的可重建缓存提前回收，不声称默认7天已满、同字节替代或零重编译成本。Root独立复审1000/1000通过后，仅解除本计划1000叶的整根保护；不授权删除目录或其余9498候选。

执行UTC为`2026-10-17T01:46:40.572625+00:00`，固定授权窗口`2026-10-17T01:45:31+00:00`至`2026-10-17T02:15:31+00:00`，没有顺延。实际删除**1000/1000**，失败/留置**0**；本批实测单链接分配量 **C：90,095,616 B，D：0 B**，逻辑量88,172,068 B。独立读回UTC`2026-10-17T01:47:24.889911+00:00`确认1000个唯一FileID对应路径均已缺失，18份来源小凭证保持一致，3个原目录仍在。

| 本机精确缓存根 | 已删叶 | 本批分配量 |
| --- | ---: | ---: |
| `C:/ck3-e04-resume-20261015-a01/live12004-r183-siege-diagnostic-a01/state-a01/profile/shadercache` | 324 | 26,845,184 B |
| `C:/ck3-e04-resume-20261015-a01/live12004-r184-window-capture-a01/state-a02/profile/shadercache` | 335 | 31,182,848 B |
| `C:/ck3-e04-resume-20261015-a01/live12004-r185-window-capture-a01/state-a01/profile/shadercache` | 341 | 32,067,584 B |

执行重新核过精确计划、机器、同handle文件ID/size/FILETIME/link1/allocation、真实路径/祖先reparse、Restart Manager和进程消费者，持有18份来源小凭证的只读保护句柄，按独占`DELETE|READATTR`句柄逐叶删除；守卫任一失败即停止并保留partial的合同已执行，实际无失败。没有新增扫描其他9498候选，没有删除save、S0、原片、config、生产物、来源配方、正常闭场原件或现用/后继现场；R176源与R191 normalS0继续保护。

这些精确叶的**派生物原件已不可读取**；保留gzip计划及小回执，不制造同名替身。历史[前两批回收](storage-retention-2026-10-17-r194-derived-reclaim.md)合计669,929,472 B和既有1397个OBJ均不重复计入本批。整卷free是并发快照，不据其差值登记信用；worker未改容量ledger/registry、未新增free credit或预留。

每日北京时间04:00任务仍是只读巡检，**不是自动GC**。本次执行不改变`automatic_gc=false`，也不修改定时任务或机器profile。

[证据索引](evidence/2026-10-17-e04-c-shader-batch02/index.json)提供原gzip、Root授权、实际结果和独立读回的精确bytes/SHA-256及原外置来源；所有4份来源保持原字节，内部绝对引用保留历史语境。详细计划30天复核归纳、小凭证180天复核，不自动续期。本说明只归档已有结果，不授权再次清理。
