# R58：rejection counter 增量造成的实际 RED（2026-10-11）

R58（`bf-202609141645-5434332d4d--li-yu-dao--R0058`）实际 public run=2、verify=2、host=1，业务保持 RED。冻结 MAIN 为 `a1fc080a5f88e401a0b9417a27492f367027aa93`，实际宿主来自 Source16 `C:/csr16`。只消费 ROOT 已封的 [小投影与闭场原件](acceptance/2026-10-11-i4-r58-rejections-increment-red/INDEX.actual.json)，未重开993,691字节 native report；原 report 的一读 claim、SHA 与时间由投影原件保留。

唯一 successor 失败诊断位于 step9 `case-natural-day-0004`，callsite 为 `advance_campaign_event_boundary.preflight`。六个 OR predicate 中只有 index1 `current["rejections"] != source["rejections"]` 为true，counter实际1→2；其余identity/date/revision/native_revision/pump倒退谓词均false。两帧PID15452、generation1、actor31254、date53144736、revision8/native8相同，pump5052→5056。原诊断 underlying_cause=NULL，没有额外snapshot/RPC/retry。

该证据只定位实际被拒绝的counter增量。投影中的历史 `stress_points is malformed` 字符串不能归因到第二条新拒绝；第二条完整last-rejected payload摘要缺失，仍UNKNOWN。不能由R57旧失败、同日同角色或后继source-only代码推导R58已修复、第二payload已qualified或获准readmission。后继恢复实现由独立lane处理，不改变本场原RED。

原 Steam fresh001 退出1，输出目录未创建；recover001虽退出0，outcome为stale_or_unavailable，事件记录窗口没有20像素移动空间。随后display-fit001、fresh-offline002和challenge001各实际0才继续。原 admission path失败发生于lock/AD之前；后继path separator修正单独留小patch与原结果引用，不移动/重写旧预约路径。这些操作准备失败与恢复不授予业务信用。

本场实际managed_session_thread_finished=true、cleanup_ok=true，原session shutdown为tree_gone=true/job_active_processes_final=0、ck3_exit_code1；这些行政清理事实不等同正常GUI退出。ROOT最终亲审Steam离线、恢复原显示1024×768×32@60，final-review-restore-stop0；keeper a20 thread_exited=true/failure=null、原keeper/allocator均0。实际release CAS4794为done/resources=[]，原小stdout留存；不声明正常GUI或native零退出通过。

015预约实际闭账0，known retained796,799,715字节加1MiB closing bound，carry135,961,971,982字节、future0，无新credit；释放2GiB预约不表示删除或物理回收。raw证据期限2026-11-10T06:32:21.090574Z，checkpoint期限2026-10-25T06:32:21.090574Z，compact review2027-04-09T06:32:21.090574Z；源/native/cache原期限未续，不自动删除。Phase I仍75%估计、`NOT_GREEN`，C3/B4/I4完整业务没有新增PASS。
