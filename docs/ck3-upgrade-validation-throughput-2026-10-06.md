# CK3 1.20 迁移验证的吞吐与本机续行

用户在读取[10 月 6 日交接](ck3-upgrade-handoff-2026-10-06.md)后要求继续执行，并询问本批迁移为何缓慢、怎样改进。本文记录有实际失败依据的判断，不计算尚无完整阶段计时支持的原因占比。原产品顺序、正式发布门槛、过程资产保全与单机 CK3 独占保持。

## 已观察的成本

| 成本 | 具体依据 | 当前处理 |
| --- | --- | --- |
| 产品与验收工具同时迁移，失败难以直接归属 | TED 暂停控制、RMTM situation 初始化、QOL 夹具资格各有原 RED；详见交接各产品入口 | 每次重试只解决已定位的阻点，复用对应现成输入，不重新展开全矩阵 |
| 环境故障中断已有效的业务链 | CCC R2/R4 实际 ENOSPC，核心与剩余 GUI 信用分开 | 新鲜盘点后再开场，不把旧空闲量或压缩设置当作问题已解决 |
| 冷启动与载入重复支付 | 本次 R0005 验收器 10:59:47 UTC 开始，约 11:01:25 到达稳定书签页面，之后仍有地图载入 | Python 修复保留同一有效 CK3 进程；只有加载输入或 binary 改变、进程失效等实际条件要求时冷重启 |
| 启动判定阻止业务开始 | R0005 的 event-free owner gate 被介绍事件挡住，400 秒准入超时；未读 root 不能称政府不合格 | 用已有 typed 事件观测与正常选择处理已源审的介绍，原 policy 与预算不变 |
| 准备包未转成运行结果 | 交接有多套 READY/NOT_RUN 输入；5/10 正式发布完成 | 一个产品实际通过后立即完成正式构建、上传、公开 Notes、规定缓存业务和永久记录，不等待全批 |
| 单机独占与完整发布闭环 | 本机游戏/桌面/上传串行，公开回读与缓存业务均为现有门槛 | 后台只推进不冲突的下一入口和实际故障修复，不用代理数量替代实机吞吐 |

## 本次接手的实际增量

资源只读快照 `2026-10-06T10:40:57Z`：C 空闲 21,099,585,536 B（约 19.65 GiB），系统 commit 为 21,114,740,736 / 39,359,959,040 B，pagefile 5,100,273,664 B，CK3/验收器为空。交接停机的 3.35 GiB 已过时；改善原因 UNKNOWN，本次缓存删除、Steam 重启、pagefile 修改和系统重启均为零。[完整原件](C:/workspace/ck3-upgrade-20261006/resume-space-agent-01/resource-snapshot-01.json) / SHA-256 `0ca7ea09d8d28819abb2bd0ba17b05b26e7981f32cdadcb4bb7df64e6a629c59`。

[写入错误诊断](ck3-native-ai/runtime-write-error-context-2026-10-06.md)已在 master 提交 `69c163ff3c51fb54f5122c9fc8bff73f0113af74` 并普通推送。5 项必要检查通过；诊断不宣称修复 ENOSPC，也不重跑原产品核心。

新场 `4-8e1c2f1861--celestial-commerce-corruption--R0005` / a78 在新鲜离线原图与 nonce `228ad7760f4b` 亲审后一次启动。准入超时后仍保留同一 PID 12492 / generation 1 的暂停现场。介绍原图关闭后，追加只读双帧、原资格日志、campaign root 四步全部成功，原 Timeout 未清；完整原 RED 先另存不可变字节。实际 root 是独立 celestial/hegemony 皇帝 34422，早先按 ID 变化推测已切官员的结论撤回。

原 900 秒 hold 到时，报告 `2026-10-06T11:23:14.226025Z` finished / RED，`managed_session_thread_finished=true`、`cleanup_ok=true`，盘点无 CK3/该 harness/watchdog。keeper 实际退出0、线程已退出，末 seq4274 后单次 CAS4275 为 done/resources=[]。[实际释放回执](C:/workspace/ck3-upgrade-20261006/resume-root-01/a78-screen-release-01.json)。没有正常 GUI OS0、剩余生产 GUI、source PASS 或正式发布信用。具体源审、热观测、最小修复与下一输入边界见[启动介绍专题](ck3-native-ai/ccc-startup-dynastic-intro-2026-10-06.md)。

一次对无帮助入口的旧挑战脚本执行 `--help`，意外生成两张挑战图且当时未持有 screen lease；两图与报告完整移动到外置原件并记录[保全回执](C:/workspace/ck3-upgrade-20261006/resume-root-01/steam-challenge-mistaken-help-preservation.json)，没有 CK3 启动，不作为准入证据。后续正式挑战均在 a78 独占下执行。第一次正常挑战图未包含 Steam，第二次挑战在启动前已超 120 秒，均保留且不授准入；最终使用 recovery02/challenge03 的亲审结果。

## 后续执行方式

1. 按已通过核心与剩余 UI 分别记账，下一场只取得仍缺的生产决议 Confirm、撤销、traits/cooldown 和正常退出。
2. 先把真实启动介绍阻点修成通用 registry 知识及既有 typed 能力组合，再用新的冻结 Python 输入、原 DLL 开场；不重逆向或重编 native。
3. 每次冷试注明唯一改动、预期解除的实际阻点和剩余业务；如果同一失败未改变，不继续冷试。
4. 每个有效工作包一次必要验证后立即 commit/rebase/普通 push；失败事实与通过事实分开保留。记录阶段时间以便以后统计，不虚构总耗时占比或下一产品 ETA。

当前正式发布仍为交接的 5/10；本次写入诊断与启动修复不计作产品发布。下一项仍是 CCC，之后消费已有 QOL18/RMTM10/TED11 入口，361 最后。

## R0006：首次 map-ready 提前于有效通知查询

UI20 / a79 / `4-8e1c2f1861--celestial-commerce-corruption--R0006` 从 committed `13b4942a91fa5459d5dc37bf7de7e95c38cc27b6`、Source18 与原 DLL 开场。当次离线原图 nonce `df0d43bbfea5` 已亲审。12:12:12 UTC 新资源快照 C free20,598,800,384 B、commit20,641,062,912 /39,359,959,040 B、CK3为空，未清理或改系统。

12:17:48.136518 的第一次 typed context query 在30.009秒后失败，server stderr为 `application-main typed query failed or its snapshot changed`。首次 native map-ready 通知帧的原图仍显示载入0%；native observer此前存在 read-in-progress /4859ms读取。没有执行通知选择。原完整失败报告先永久保全；同一PID11412/generation1热现场的三个快照、资格、context共五步实际成功，12:29:16.016312 读到 `.0051`、ROOT34422、native0唯一shown/enabled，证明既有DLL可完成查询。

前两个快照仅相隔0.23秒，同cached pump epoch，观察入口正确拒绝；后取新frame3通过原严格递增要求。准备和前台交接消耗了剩余现场时间，正常选择23入口提交前原900秒hold已结束。报告12:33:20.701318 finished/RED；独立held OS handle在signaled后读到退出1，无GUI0或D0成功。`managed_session_thread_finished=true`、`cleanup_ok=true`、本场进程库存空；keeper退出0/线程退出/末4323，单次CAS4326 done/resources=[]。原报告SHA `d91ad8aa836325f417b3d5906cf6272b95bb77a4487d4fc97ff15020ccb8b1c1`，见[闭场库存](C:/workspace/ck3-upgrade-20261006/resume-root-01/a79-final-inventory-01.json)和[释放](C:/workspace/ck3-upgrade-20261006/resume-root-01/a79-screen-release-01.json)。

这次不是ENOSPC，也不是原政府policy或native capability缺失。下一修复只把通知query放到当前读取完成、同一owner稳定双帧之后，复用Source18/原DLL与原预算；正常通知及D1→D3连续执行，减少现场脚本准备与人工交接。上述热成功不追认旧RED为GREEN。
