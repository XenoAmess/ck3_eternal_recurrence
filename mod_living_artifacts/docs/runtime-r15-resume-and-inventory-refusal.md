# R15 恢复场次：库存查询失败，业务未通过

`machine_id: pc-20260924rtuf-f11af23c08`；观察时间为 2026-10-22T21:57:53Z。外置工作包为 `D:/workspace/ck3-living-artifacts-20261022`（EXT）。本记录不授予金币修复、计时、冷加载或发布资格。

用户恢复任务后，c18 `5b1408fb3cc7b359eb5a43342861e8a521ab9d28` 经正常后继 freezer 实际 exit0，正式 staging 为 57 文件；沿公共 plan、prepare、allocate、绑定 preflight、run 启动 R0015。没有重编 C++，没有修改冻结源或原 Prepared。实际 CK3 PID9404，原生会话开始于 21:02:54Z。

装备前的既有库存 GUI 回调正在等待时，Root 额外提交了未获此来源资格的 `ck3_query_ingame_ui_window_v1(window_kind=inventory)`。该步骤于 21:15:50Z 被实际 managed-source 守卫拒绝，并使 host.error 锁存。Root 不应把这次通用查询作为回调前置；后续场次应直接使用原 GUI 回调及其原生装备后验，不重放这一查询，也不清空错误或放宽守卫。

原 `live/pc-20260924rtuf-f11af23c08--living-artifacts--R0015/case-output/living-artifacts-threshold-result.json` 于 21:15:52Z 记录 **BLOCKED、0 自然日、6 次计预算调用、1 次实际 Save、8 项均 BLOCKED**；错误为 `Actual shared host failed; preserve error and do not replay`。库存窗口后来显示、以及迟交的 GUI 回调，均不改变原终态。没有实际装备、付费压制或金币扣款通过信用。

闭场保留业务失败和资源清理的区别：

- Root 审阅自动保存未勾选的退出确认框，经有坐标回执的 GUI 正常退出桌面；原生进程于 21:46:58Z 实际 exit0，持有的 OS 句柄 signaled/exit0。
- 原 `normal-close-result.json` 的 `failure_lifecycle_completed=true`、`failure_preserved=true`、`normal_close_qualified=false`、`business_pass=false`；源失败保留。native tree/job/control 清理已证明，不能据此改写业务或正常关闭资格。
- 原 host wait1、public run wait2；只读保存服务 wait3，因为只完成 1/7 保存。原 allocate/keeper wait0，keeper thread_exited=true、failure=null、last_sequence636。
- `EXT/environment/r15-screen-resource-close-a02/release.stdout.json` 实际 CAS636→637，done、resources=[]。a01 因 CLI SHA 大小写精确匹配要求而拒绝，未修改锁；保留原失败。
- `EXT/environment/steam-offline-r15-closed-20261023-a01.json` 于 21:57:53Z 后台观察 offline/true；Steam PID8580、出生 FILETIME `134371126587222837`、版本11.15.70.27。后继启动仍须重新取证。
- 原卡 task-close：`EXT/environment/storage-threshold-a26-20261023-a01/r0015-task-close/20261022T215631070489Z-task-close.json`，实际 exit0，未删除资产。新场次另核存储预算。

关键原件还包括 R0015 `native-report.json`、`host-original-process-exit.json`、`keeper-actual-parent-exit.json`，公共 run `EXT/environment/public-operations/20261022T210242011086Z-run/exit.json`，以及 `EXT/environment/r15-inventory-route-a01/actual-post-review.json`。原截图、点击与失败查询回执保留，不制造替代原件。

并行源码进展：计时用例的显式初始印记及首次/renewed04 实际保存守卫已提交为 `2bc852be3396b8386491ddff7ed60a15ef4862df`。它只提供 90 日 fixture 持久化输入，不授喂养动作信用；完整 cold workflow 命令组与 53 文件 strict 通过，计时和冷加载实机仍未运行。Java 临时 scratch 元数据计量修复提交为 `5c1f01d8664a92d3dc25823d1ffc8a9197999f50`，本地 48 项目标测试通过，Official 后继 CI 需独立观察。两项都已普通推送至 master，不能替代游戏业务验收。
