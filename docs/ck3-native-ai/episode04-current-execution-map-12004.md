# Episode 04 当前缺口与执行入口（2026-10-17）

**2026-10-17 本机当前接续（machine_id: `desktop-3fevhd2-1c74096080`；核至2026-10-16 18:41 UTC）。** [R186十四日与事件](episode04-r186-window-capture-12004.md)原片36.700秒并正常闭场；[R187两次启动前RED](episode04-r187-prestart-failures-12004.md)均无CK3/镜头；[R188第一段](episode04-r188-window-capture-12004.md)原生11日Mar20→Mar31、片内914帧/30.466秒，但有限尾抽帧可见Mar30，day12 hook超时且Resume未在片内提交。随后同PID的[片后跨月与正常闭场](episode04-r188-monthroll-close-12004.md)独立证实g12 Mar31→Apr1、正常保存、游戏exit0与屏幕释放；不追加到已终结原片。两次+2C0/+2C8同值物理写和[静态copy来源](episode04-r08-r188-copy-writers-12004.md)相接，付款、payer、币种、cadence及+28/+30 producer仍unknown；有限窗口无样本不证明不存在。核心 **6/14＝42.9%**、业务 **4/11＝36.4%**、合格动态 **0/11**、正式ABC **0/3** 不变，69段口播草稿不抵扣成片或人工签核。

新研究入口：[R06本地depth8前缀](episode04-r186-refill-parent-prefix-12004.md)仅本地mode0/flag0稳定，父链候选仍待新native与新实机；a31为**source-only/native NOT RUN**。[R08 classifier tier](episode04-r08-classifier-tier-threshold-12004.md)、[关联ID清理callee](episode04-r08-copy-callee28d6170-12004.md)及[R188 copy writer](episode04-r08-r188-copy-writers-12004.md)各自保留静态、实际和unknown边界；三份新便携消费者已离线通过，不等于付款归因。WarOverview 当前 a29 显式OFF/UI fallback，新flag与a30实机仍待验。实机 R186–R188 与 a29 native 来源是冻结 `d05b0c780b615faa714fdf0535403bb2e6941faf`；rebase 后 HEAD `53c559aa7f0caca8bc1c92b0c6f44b2ef8f72011` 加未提交源码属于新层，不能冒充旧实机部署。详情见[本轮交接](../handover/2026-10-17-war-episode04-r188-and-source-intake.md)；[精确清理](../maintenance/storage-retention-2026-10-17-r188-exact-reclaim.md)实际C回收1,642,663,936 B、D 0，此时容量不外推为后续准入。

新增可移机来源已接入：[合同贡献链](episode04-r08-contract-contributions-12004.md)、[local88 的组成](episode04-r08-local88-components-12004.md)和[业务归因审查](episode04-r08-semantic-attribution-audit-12004.md)。三个追加包分别封存5个、6个和3个完整逻辑函数，另含64B精确描述符数据；消费者在标准库及 `-O` 下核验原件、控制边和跨函数连接，不把这些静态层次提升为已付军费或周期。

本轮现场与容量事实的来源机器为 `desktop-3fevhd2-1c74096080`。其他机器可复用下列源码合同、消费者与实验设计；安装、权限、桌面、PID、容量及实机资格仍须在当地重新取得。旧日期的来源记录保留原范围，本页用于找到最新勘误与下一步。

**2026-10-16 15:05 UTC 当前接续。** [R185实机专题](episode04-r185-window-capture-12004.md)、[52份原件索引](evidence/episode04-r0185-20261016/source-index.json)、[便携事实](evidence/episode04-r0185-20261016/portable-facts.actual-a01.json)与[拍摄结果](../../promo/ck3_native_war_ai/episode-04-march-logistics/r185-capture-result-2026-10-16.md)绑定本机独立R0185、源码`c743520929d4f9a82c17c908b218075018598e2d`和a28：R184正常保存接续后，原生 **12/12自然日** 从1067-02-21推进至03-05；Army18面板人数跨月从1184显示为1173，只有可见变化，没有同次物理扣减与writer归因，**不增加R03正例**。客户区原片 **46.466秒／1394帧** 完整解码、正常保存／游戏exit0／屏幕释放；80秒hold阶段实际遭遇C卷新预算检查失败，因此最低时长未达，尚无clean span、完整人工观看或签核。研究 **6/14（42.9%）**、业务 **4/11（36.4%）**、合格动态 **0/11**、正式ABC **0/3** 均不变。

共享研发续线：[R06本地前缀候选](episode04-r06-local-prefix-continuation-12004.md)的a29/a30消费者接线有14项合同测试通过，但新native build与实机leaf尚未执行；[R08应用链](episode04-r08-rate-resource4-application-12004.md)、[六叶贡献链](episode04-r08-contract-contributions-12004.md)及[语义审查](episode04-r08-semantic-attribution-audit-12004.md)供影片核稿和智能体消费。新静态包a02/a03/a04分别封2/5/6个直接来源叶；a05可重算的是15条直接CALL，**CALL边不另算来源叶或业务通过**。合同单项raw贡献和局部槽写入已知，resource4业务名、军事已付额、payer与cadence仍unknown；R08不加分。下一R186的D卷scene迁移、`legacy_promoroot` profile核对及C卷新native 768MiB预算均处于准备／准入阶段，不写成已采纳或已拍摄。

研究整卡仍为 **6/14（42.9%）**，核心业务 **4/11（36.4%）**：R00/R02/R03/R11/R12/R13 已验收。合格连续动态证据仍 **0/11**。中文草稿覆盖 **69/69**，最终冻结稿、声音、新版成片与人工签核不因草稿覆盖而完成。

| 未闭项 | 已能复用的事实与代码 | 下一份必要证据 |
| --- | --- | --- |
| R01 / 新比较 T0 | [ready-T0 同帧入口](episode04-ready-t0-decision-12004.md) | 新鲜完整同帧状态、明确策略目标及正常保存；旧 continuation 不自动成为新 T0。 |
| R04 县进入 | [下一场原生条件与停止线](episode04-r04-next-scenario-12004.md) | 新鲜 first edge 的原生最终 condition=true，随后一次合法 Move 与实际物理扣兵；最多五个去重预览，没有正条件即停止。 |
| R05 饥饿 | [下一自然实验](episode04-r05-next-starvation-12004.md) | 自然低库存→库存结算→零库存→同次归因物理 debit；明确 full-history profile 与日志 fences。 |
| R06 补员 | [R183 depth8 原件、下一入口及修复](episode04-r06-next-receiver-12004.md) | R184 已实际验证 a27 开窗及独立可见后验，诊断 null 修复有效；receiver 仍 depth8 unavailable。[下一 local-entry-only 入口](episode04-r184-r06-local-prefix-12004.md)保持原预算，候选、选中、开关与实际 ADD 继续分开验收。 |
| R07 登船费用 | [双 fresh arms 与七日 NO-GO](episode04-r07-next-fresh-arms-12004.md) | 目前已知新登船边需31日，不能把旧续行截成七日。两臂须各自新冷载同一静止保存，付款来源与经济周期仍独立判断。 |
| R08 维护归因 | [缺口入口](episode04-r08-next-maintenance-attribution-12004.md)、[28C43A0](episode04-maintenance-callee-28c43a0-12004.md)、[2C142B0](episode04-maintenance-callee-2c142b0-12004.md)、[24E1E80](episode04-maintenance-postvector-24e1e80-12004.md) | 具名费率端函数已有完整来源，旧“body未持有”库存已过时。仍缺 c/d 军事类别 writer→同次应用→付款账户及周期；paid 保持 unknown。 |
| R09 特殊兵 | [下一场及 DATA 双计量](episode04-r09-next-special-army-12004.md) | 同一正常 S0 的独立反方向、完整库存/容量/权重和实际读回；保留原 strict freeze 失败。 |
| R10 A/B/C | [同 T0 三次冷载要求](episode04-r10-next-abc-t0-12004.md) | 三臂各自完整实机、相同源保存与策略冻结、独立身份和实际终态，当前 0/3；过期 relay 不可直接复用。 |

R183 的[专题与便携原件](episode04-r183-window-capture-12004.md)证明客户区屏幕区域能得到 1280×720 游戏图像。其外置录制仅保留 **239帧 / 7.966秒**截断原片；三日原生回执不等于三日都保存在片内。游戏以 timeout 清理，未取得拍后正常保存/正常退出。本场不增加动态或业务验收分子。

正式采集修复入口是本期 [canonical recorder](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/capture-recorder.md)：按实际客户区矩形采集，独立监测窗口/前台/遮挡，并在开始与 spawn 前核对完整录制时长加至少120秒闭场余量。源码和离线测试不抵扣下一场实录；R183 外置脚本不因后来改码而自动获得新守卫。

拍摄优先级与口播段号见[三条最小连续镜头计划](../../promo/ck3_native_war_ai/episode-04-march-logistics/review02/r184-shot-priority-2026-10-16.md)。它是待执行计划，不是已取得 clean span。存储回收与实际每日巡检部署见[独立回收工作记录](../maintenance/storage-retention-2026-10-16-dedicated-worker.md)；新重型写入须另取当次按卷准入，旧07:45额度没有续期。

## R08 费率应用链的静态补注（2026-10-16）

[raw resource4 便携专题与同源执行图](episode04-r08-rate-resource4-application-12004.md)：`28F7840`后段取得scalar B与完整current向量槽9 M，`wrap_i64(B-M)`经原生gate后进入`context+4A0` ADD或selector4 SUB。新增来源是完整938B scalar与54B gate；已有caller/keyAE原件同时便携保全。不能将raw4/4A0命名为金币或已付军费；较早NET应用、c/d业务producer、payer及cadence仍分开未闭。此静态追加不改变本页6/14、4/11、dynamic0/11的历史口径。机器 `desktop-3fevhd2-1c74096080`，无新实机动作。

## R184 正常闭场与代码接续（2026-10-16）

来源机器 `desktop-3fevhd2-1c74096080`。[R184专题及精简原件](episode04-r184-window-capture-12004.md)绑定 source `163530f1bbcabe5a97854625b3fab7568006ee65`、a27、独立身份与正常保存/退出0/释放。canonical 客户区区域原片实际 **22.766秒、683帧、1280×720/30fps**，全解码无截断；三帧原始尺寸直接审阅日期为1067-02-12/15/21。原生八份精确日回执、第九日过渡暂停误判、后续正常保存日期分别保全；没有新增 business/clean/人工签核，仍0/11。

C 的具名 `operation_root_relay.py` 已接入正常 constructor，绑定新 operation/S0/runtime/source/容量；按实际 prepared state 路径定位并计量完整 Driver/run 侧车。旧 legacy API 继续拒绝，正式 ABC **0/3**。共用三冷载要求见[R10](episode04-r10-next-abc-t0-12004.md)。新运行须重新绑定，不能借本轮代码与离线回归追认旧臂。

两支紧急回收的实际结果和每日只读巡检边界见[维护记录](../maintenance/storage-retention-2026-10-16-r184-emergency.md)。历史容量 deadline 没有延长；后续新场、构建和渲染分别重新准入。
