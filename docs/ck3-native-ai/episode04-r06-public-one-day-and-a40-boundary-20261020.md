# E04 R06 公共单日入口与 A40 未完成资格（2026-10-20）

`machine_id: desktop-3fevhd2-1c74096080`。记录时间2026-10-20 07:54 UTC；机器事实来源为下列精确原件索引。本轮延续[交接](../handover/2026-10-20-war-episode04-vacation-handover.md)与[R0217实际结果](episode04-r0217-direct-debits-and-normal-close-20261020.md)。

研究仍为10/14（71.4%），业务7/11（63.6%），正式动态0/11，ABC0/3，B库存点0/2。本轮新增代码和失败诊断均不增加业务或影片验收信用。

## 已交付源码

公共 `r10_prepare` 在同一客户端接入互斥的 R04/R06 路由，默认准备流程保留。R06 先完成来源、配置、实际资格、同进程 census、补员槽位、日期及 DATA 检查，再进入一次录制与精确一日；未知动作结果不重投。只读晚导出须恢复调试寄存器与 detach 后才能进入公共保存/正常闭场。

独立复核修正两处启动边界：实际启动前重新核对 observer EXE 字节与资格/SYSTEM 回执；长时间等待录制后重新核对同份 census 的300秒有效期，并在 EXE/资格读回之后再次检查。过期或替换时均须在 claim/Popen 前拒绝。

最终专项测试18/18、R04路由1/1及通用适配器25/25实际通过；专项测试已接入正式静态 CI。它们验证离线合同与启动拒绝行为，没有启动 CK3，也没有取得 R06 ADD 观测。参见[源码及复核精确索引](evidence/episode04-r06-public-one-day-20261020/SOURCE-INDEX.actual-a01.json)和[独立复核](evidence/episode04-r06-public-one-day-20261020/R06-INDEPENDENT-REVIEW.actual.json)。即使后续取得目标指令 ADD，同 Core 关联也不自动证明全局物理闭包或 R06 整卡。

## A40 编译成功，运行资格未完成

实际生产绑定源码 `93b27601aed449515b69aabed62e1af7cc61c1fc`、native tree `fee86631356f556271445157523c62abfd62951e`。761步编译/链接完成，但原生产器 exit1：新增 C 盘构建根不在本机已安装 broker 的获准根目录内。Root 在选择新构建根时漏查该项，保留原失败，不能用编译成功替代精确 EXE 排除登记。

已准备仅增加该精确根目录的 policy/manifest 候选，完成普通 token 的只读审查；安装后的原策略、固定任务和 runtime seal 未被替换。一次原生提权启动于07:27:17 UTC返回 Windows 1223（操作已取消），未取得子进程句柄、PID 或管理员执行回执。无法由错误码判断取消者，也没有再次自动提交。SYSTEM 登记、UI cold、worker/V5 cold及 A40 qualification 均未完成。

原件见[A40精确复制计划](evidence/episode04-a40-incomplete-20261020/COPYPLAN.prepared-a01.json)、[实际未完成闭场](evidence/episode04-a40-incomplete-20261020/actual/A40-INCOMPLETE-ATTEMPT-CLOSURE.actual-a01.json)与[来源说明](evidence/episode04-a40-incomplete-20261020/README.md)。prepared 候选不是已安装状态。旧 a39 及其他场次资格不得外推到本次源码或构建输出。

## 本轮运行与容量边界

没有分配新 R06 run ID，没有启动 CK3、SDK 或录制。当前工作包 C 盘配额止于2026-10-20 08:00 UTC；公共准备至少1800秒、正常闭场900秒、清理120秒，尚不含本轮准备与实验。07:17 UTC剩余2558秒已不足2820秒，因此新场次被提交前拒绝，不能用旧场加载速度缩短守卫。

未分配 scene 的2.25 GiB预留已撤销；A40失败构建实际 allocation 410,566,320 B、1501文件，native future 已归零。07:54:56 UTC容量监视器原进程exit0、正常stopped；shared128 MiB归零，全部已知C/D执行future为0。最终结果追加于[容量原件目录](../maintenance/evidence/episode04-capacity-20261020/r06/)，旧42,132,678 B仅 carry-only，无新增执行额度。最终C配额余量3,708,283,706 B、D底线余量77,733,888 B仅绑定该次观测。未删除基线、原始失败证据或唯一恢复输入。

后继须另取当前容量与有限时间窗，重新核对实际构建/登记/冷测资格及 Steam 新鲜离线画面后，才可从已验证的正常 Mar31 S0 尝试公共 R06 一日；不追认本轮为实机通过。完整影片的完成时间仍取决于剩余研究、业务与正式镜头验收。
