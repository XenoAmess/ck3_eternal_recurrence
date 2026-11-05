# resume91 Runtime 交接：539 已结算，历史消费待修复

切点：2026-11-05 10:20–10:23 UTC；机器 `xenoamess-full-tower-eb9d2c1186`。运行 owner `/root/runtime_continue`。配套[机器证据索引](2026-11-05-runtime-resume91-handoff44-source-index.json)，历史入口为[11 月 4 日总交接](2026-11-04-java-g2-resume91-vacation-handoff.md)及其[来源索引](2026-11-04-java-g2-resume91-vacation-handoff-source-index.json)。旧局、旧 PID 和旧 STOP 状态不覆盖下述新局切点。

## 持续续行授权与实际委托终态分开记录

本会话用户在 11 月 4 日休假指令之后已明确“你恢复对 CK3 的操作，我玩完了。继续执行任务吧”，并选择“继续原自动游玩那一局（独立 profile 的 autosave_exit.ck3）”。该续行授权持续有效。AGENTS 顶部是 11 月 4 日历史段的重贴，不是新 STOP。本次 Runtime 一度误判并把旧权限段写入本文，现明确撤回；首次文档提交保留历史，由正常后继更正，不能据此新增停止文件、清除 hold、强杀或停工。这个失误没有产生 STOP marker、Game/keeper 操作或取消在途 GET。

10:20:02 的既有 OWNER/HEAD 薄读确认：唯一委托 `2ad92b89-a7e6-4756-82f3-eabe09abae74` 已 `DELEGATE_COMPLETED`，OWNER 为 `FAILED_DELEGATE`。实际 END 是 **10:04:24.696448 UTC**，异常 `java.io.IOException`，`exit_code=null`；不能把 null 写成正常退出 0。没有新 LOOP。因委托在交接前已经结束，本次没有新写 STOP marker；“没有发出新停止请求”与“已有真实委托终态”分别记账。

旧 incident521 的自身 marker 已在第 42 次恢复前合法移入 D 归档，当前不复建、不借其作为用户暂停。依持续授权继续第 44 次最小受控恢复，不需要再次向用户或 Root 确认；不能执行已消费的 once 脚本。下述 10:20 切点仅证明当时尚无 GET44，不是停止授权，也不外推后继运行阶段。

## 当前同局与账本

当前账本 `D:/ck3-state/ck3-java-resume91-business-user16/continuity/continuity.json`：89481 字节，SHA-256 `3a53ed79c4d8e0404d835e0c4c3f68532f29f7d1b254c22d5c5914ed76f9f72f`，sequence **539**，`repair_required`，cycle **23**，`pending_receipt=null`，batch11 为 `BATCH_INTERRUPTED`。10:20 薄读前后文件身份、大小与修改时间稳定。实际 Driver ACTION 历史仍为原 527。

最后持有的同一进程身份如下；这是既有运行物证，不把本次 docs 工作说成新增 Game 健康查询：

| 进程 | PID | birth FILETIME |
| --- | --- | --- |
| Game | 117900 | 134382986922161575 |
| keeper | 34052 | 134382986871091921 |
| Quarkus dev 宿主 | 97584 | 134383031688380897 |
| 外层启动进程 | 86108 | 134383031267149795 |

当前 session 为 `resume91_after_user_20261105_01`，继续的是独立 profile 的原 `autosave_exit.ck3` 局。仍使用 Java21 / Quarkus dev；不能套回旧 plain Main 或把离线 javac 产物直接注入活跃 build。

## 已完成的原动作，绝不能重放

原事件 521 已真实结算为 **527 SETTLED/APPLIED**；完整 command、Attempt、dispatch、body SHA 和原期限保持。随后已真实发布 **528 ACTION527 → 529 RETAIN → 530 SETTLE/VISIBLE_GAMEPLAY**，cycle22→23、pending 清空。该周期日期前后都为 `53162232`，零新增日；不是新的保存。

新 Sway 原动作的 535 INTENT、536 RUNNING、537 UNKNOWN 是同一完整命令。537 原因是嵌套 writer session；其查询命令为 `ordinary-sway-opportunity-v1`，`query_selected_target`、`submit_allowed=false`。原期限 **2026-11-05T09:10:41.675462900Z** 保持过期，没有重试执行。

第 43 次受控只读恢复已经真实将该原动作结算为 **539 COMPOSITE_SETTLED / COMPOSITE_NO_GAMEPLAY_WRITE**。539 的完整 command、body 和 execution 与 537 相同；这不是 APPLIED、SchedulerSaved、推进或保存信用。原 539 receipt 为 7277 字节 / `87c925183ad9bc230b6cc5871c23271238a0711c5231ae1597c6d39ada049438`。不能重跑 537、重建 539、刷新期限或伪造 pending。

539 后真实失败发生在必经历史消费：`RootActionHistoryMaterialSourceFactory$Installed.requireNoGameplayWrite:241` 仍要求 identical installed Life producer；经 `DriverActionHistoryPublisher.publish:158`、`RootReadPublicationActions.reconcileInSession:68` 回到 Controller。因此原终态保留，历史消费、完整 bootstrap、普通 LOOP 尚未恢复。

## 第 44 次候选已具备软件资格，尚未采用

唯一目标是 `local-service/src/main/java/org/xar/ck3/control/service/root/RootActionHistoryMaterialSourceFactory.java`。当前 C 源仍为 **69288 / `340de5f21bcd02af2950436bb7f11eb828bf402bee524987fc950fb30ef9c94a`**，交接脚本只读重核与 Ready.before 相同。候选 final02 为 **72347 / `b500b1d6dec8e2d035bd0c1b90adccf9d1c5ac84b8e0fb62d0d7180430090260`**。

该候选只给已有 NoGameplay 历史消费增加严格 Sway 分支：实际同 Root owner、唯一 installed Sway、同 retained archived 对象、实现/decoder/replay source 元组、完整 canonical receipt、真实 source no-write 与 mandatory archived verification，以及原 head/documents/absence/repair 末校验。原 Life 分支和其它文件字节保留；没有新增 issuer、控制或 fake Root 软件正例。

首版真实 compiler RED 保留：把接口 `ActionCoordinatorPort` 直接传给要求 `RootApplicationSession` 的 owner 校验，0 class；不能用源码审阅 PASS 掩盖它。final02 改为实际 Root pattern 校验、foreign 强拒，再调用原 owner 校验。Native 唯一 1 TU 于 **10:17:23.986930→10:17:33.382711** 首编成功，javac **8.3601222 秒**、10 class，终态/post/fence/close 全释放。10 个 class 名相同；`Installed` 新增 synthetic lambda 并重编号，须正常 loader，不能承诺 body redefine。

final02 Ready 为 `a952c173…`，Native qualification 为 `8ae11c1a…`，独立源码审阅 final02 为 `f75166db…`，完整路径在索引。没有新增 Test 门，也没有重跑旧 Test69/其它旧绿。上述只授源码与类型资格，**未授 C 采用、GET44、实际 Sway 历史消费或普通 LOOP**。

依现有持续续行授权，运行 owner 先核同 Game/keeper/宿主、head539 及 current Factory 前像；用新的单叶 once adopter，加已审非语义资源 comment 触发同宿主正常 Quarkus loader。旧 delegate 已 END，纯 instrumentation 不会使它复活。唯一 GET 后以 30 秒小 OWNER/log 观察首次 receipt/END，立即裸报并解除 Native 的本次 churn HOLD；不等完整包装或正式 Git。真实验证目标是消费已结算 539 的历史、完整 bootstrap、Controller 和普通 LOOP；然后继续自然新日与保存，绝不重放原动作。

## 性能与保存仍未达标

最后确认保存仍是 SAVE59：8 个已保存游戏日，saved date `53158368`。已结算日期 `53162232` 对应 eligible169，不能作新保存分母。年度自然保存阈值仍为 `53167128`，不为交接强制保存或降低保存频率。

主恢复累计窗口从 **05:07:14.559606 UTC** 起，普通窗口从 **08:39:49.993497 UTC** 起；失败、准备、GET、重载及等待全部继续计入，各自新增 `SAVE_CONFIRMED` 日为 0，不能报告有限秒/保存日。目标 10 秒/新增确认保存日未达到。

最近 batch11 墙钟 294.4208702 秒，规划 168.2115062、观测 64.0267185、动作 35.1274186 秒。实际模型 HTTP 73.182 秒、TTFT72.586 秒、请求体 1722641 字节；reported prompt540862 只是服务报告值，不能独立证明上下文或 cache。该批没有新增日或保存。不要为交接、候选或研究再采 JFR、重启 Game/DLL 或停止健康 worker。

## 原件与正式发表

本次只读冻结总件：`D:/ck3-state/resume91-runtime/resume-after-user-play-20261105/runtime-handoff44/RUNTIME-CUT44.json`，7502 字节 / `7deee7c698fb505d14607c68a4a8dec0d62073f044736fadb3b34004fb6b45c8`。它保存 OWNER、HEAD、43 实际 loader、539 receipt/event、44 Ready/qualification 与独立审阅的原 pin 和冻结 pin。未读 Driver/SEM/save 正文，未发 HTTP/GET/Native，也未修改 C/账本。

正式业务 Git 仍由 Java owner 维护 `D:/r64d`；Z 工作区的大量历史 dirty 不 reset、stash、广 stage、wholecopy 或 force。本交接只新增两份明确 docs 文件，由既有正式发表者正常提交推送；机器 D 原件及私有材料不进入仓库。
