# Episode 04 当前缺口与执行入口（2026-10-16）

本轮现场与容量事实的来源机器为 `desktop-3fevhd2-1c74096080`。其他机器可复用下列源码合同、消费者与实验设计；安装、权限、桌面、PID、容量及实机资格仍须在当地重新取得。旧日期的来源记录保留原范围，本页用于找到最新勘误与下一步。

研究整卡仍为 **6/14（42.9%）**，核心业务 **4/11（36.4%）**：R00/R02/R03/R11/R12/R13 已验收。合格连续动态证据仍 **0/11**。中文草稿覆盖 **69/69**，最终冻结稿、声音、新版成片与人工签核不因草稿覆盖而完成。

| 未闭项 | 已能复用的事实与代码 | 下一份必要证据 |
| --- | --- | --- |
| R01 / 新比较 T0 | [ready-T0 同帧入口](episode04-ready-t0-decision-12004.md) | 新鲜完整同帧状态、明确策略目标及正常保存；旧 continuation 不自动成为新 T0。 |
| R04 县进入 | [下一场原生条件与停止线](episode04-r04-next-scenario-12004.md) | 新鲜 first edge 的原生最终 condition=true，随后一次合法 Move 与实际物理扣兵；最多五个去重预览，没有正条件即停止。 |
| R05 饥饿 | [下一自然实验](episode04-r05-next-starvation-12004.md) | 自然低库存→库存结算→零库存→同次归因物理 debit；明确 full-history profile 与日志 fences。 |
| R06 补员 | [R183 depth8 原件、下一入口及修复](episode04-r06-next-receiver-12004.md) | 一次军务原生开窗及独立可见后验、同帧 receiver 读取；候选、选中、开关与实际 ADD 分开验收。首 key 命中和诊断字段修复仍须新构建/现场。 |
| R07 登船费用 | [双 fresh arms 与七日 NO-GO](episode04-r07-next-fresh-arms-12004.md) | 目前已知新登船边需31日，不能把旧续行截成七日。两臂须各自新冷载同一静止保存，付款来源与经济周期仍独立判断。 |
| R08 维护归因 | [缺口入口](episode04-r08-next-maintenance-attribution-12004.md)、[28C43A0](episode04-maintenance-callee-28c43a0-12004.md)、[2C142B0](episode04-maintenance-callee-2c142b0-12004.md)、[24E1E80](episode04-maintenance-postvector-24e1e80-12004.md) | 具名费率端函数已有完整来源，旧“body未持有”库存已过时。仍缺 c/d 军事类别 writer→同次应用→付款账户及周期；paid 保持 unknown。 |
| R09 特殊兵 | [下一场及 DATA 双计量](episode04-r09-next-special-army-12004.md) | 同一正常 S0 的独立反方向、完整库存/容量/权重和实际读回；保留原 strict freeze 失败。 |
| R10 A/B/C | [同 T0 三次冷载要求](episode04-r10-next-abc-t0-12004.md) | 三臂各自完整实机、相同源保存与策略冻结、独立身份和实际终态，当前 0/3；过期 relay 不可直接复用。 |

R183 的[专题与便携原件](episode04-r183-window-capture-12004.md)证明客户区屏幕区域能得到 1280×720 游戏图像。其外置录制仅保留 **239帧 / 7.966秒**截断原片；三日原生回执不等于三日都保存在片内。游戏以 timeout 清理，未取得拍后正常保存/正常退出。本场不增加动态或业务验收分子。

正式采集修复入口是本期 [canonical recorder](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/capture-recorder.md)：按实际客户区矩形采集，独立监测窗口/前台/遮挡，并在开始与 spawn 前核对完整录制时长加至少120秒闭场余量。源码和离线测试不抵扣下一场实录；R183 外置脚本不因后来改码而自动获得新守卫。

拍摄优先级与口播段号见[三条最小连续镜头计划](../../promo/ck3_native_war_ai/episode-04-march-logistics/review02/r184-shot-priority-2026-10-16.md)。它是待执行计划，不是已取得 clean span。存储回收与实际每日巡检部署见[独立回收工作记录](../maintenance/storage-retention-2026-10-16-dedicated-worker.md)；新重型写入须另取当次按卷准入，旧07:45额度没有续期。
