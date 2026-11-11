# 单个 Life 退役与已结算原件的恢复

本单元把一次真正未知效果的旧 Life 中断，与后来已成功执行、但尚未消费材料的新 Life 分开处理。旧命令、子回执、原期限、保存对和 Driver 原件全部保留；没有重发旧控制，没有把 operator 决定写成 APPLIED、NoEffect 或游戏日信用。

以下事件时间均为 UTC，文档日期为本机 2026-11-12。实际 Game 始终为 PID145132／出生134388549310428814，episode 为 `resume91_offline04_20261111T071454Z`。

原 parent346 的 ARM339 已结算，resume345 在成功 ACK 后遇到 fresh READ 不可用。后继同 ID 只读恢复把 resume 写成348 SETTLED/APPLIED，349父仍为 COMPOSITE_UNKNOWN：原 clock stop／generation-bound cancellation 没有确认。原执行期限 `2026-11-11T17:41:30.687424200Z` 没有延长。

独立维护操作先取得当前暂停，再对原 generation14 执行一次明确的新 operator cancel。19:29官方 pause-map ACK 加真实后 snapshot 确认 paused，前台窗口保持；20:09独立 cancel ACK 为 accepted/canceled，随后官方 STATUS_ONLY READ 确认 generation14 为 idle。它们没有补进旧父的 children，也没有因此结算旧349或授予推进信用。维护 helper、状态入口和 Native 编译／现场回执保留在独立证据目录，未作为正式变体部署。

## 退役与普通续接

请求 v2 明确使用 `retained-life-interruption`，绑定同 Game／episode、原父完整命令和 body、全部原子 reservation、当前实际 writer 前驱，以及真正的 operator 指令。`prior_requests` 显式保留旧 Sway 请求，旧 Sway 隔离和原 ID 永久不重放的约束继续有效。单个 Life 退役没有封掉整个 Life 域。

350是独立的 `OPERATOR_ABANDONED_UNKNOWN_EFFECT` 终态，保留原 execution；351是无新信用的非零恢复事件。它分别保留 current completed13、saved cycle1、8 saved days、dirty、eligible12、完整 Driver／Goal，以及真实 used batch 集合；只消费原 batch5，后继为6。集合按身份验证，不假定 Set 的迭代顺序就是批次顺序。

已归档观察按原前驱和完整因果链重放，当前签发仍要求实际 CAS 前驱。旧指令窗口到期不阻止核验其当时已提交的历史事实。授权文档按原 SHA／大小从实际 immutable archive material 查询，不把外部 locator 冒作 archive 内路径，也不放宽 artifact-root、parser、hash、旧编码或普通 Guard。

普通恢复明确支持已提交350／351之后的首个空 batch6。其历史353只能在已验证的351、唯一实际 BATCH_STARTED352、相同 owner／action head／cycle／saved／operator proof之后重放；原一般 open-batch、批次序号、cycle ref及完整 reducer 校验保持。

## 已 APPLIED 的377只消费一次

31次冷 Java 接入后，358真实执行 event option1，361计为 C14 VISIBLE_GAMEPLAY，0新日。随后新 Life377已经 COMPOSITE_SETTLED/APPLIED、resume375已经 SETTLED，真实结果为105→107的2日；故障发生在之后的材料 hook，尚未 RETAIN，不能根据 batch 的 ACTION_UNKNOWN 文案重放或退役377。

初版 operator 外部 wrapper 破坏了普通 Life 所需的同一个 `LifeAdvanceRootReplay` 实例。最终将 operator 分支移到原 replay 内部，恢复原 `binding().verifier() == life.replay()` 与 typed Recorded 提取；原材料 identity 检查及普通完整 replay 算法保持。379随后实际发布了377的 Driver 材料。

新增只读 DATA 角色只认当前 C14／saved1、pending=null、latest canonical fully APPLIED Life、完整已结算 children、原 owner／source／body／plan，且 before105匹配既有 cycle binding、ending107匹配原 target。它不伪造 pending、UNKNOWN、restart capture 或 C15。

真正 RETAIN 前再次检查该角色及已发布的同 source Driver 材料；真正 RETAIN 后改用原严格 pending-completed-Life 角色，仍须同一个377和完整材料。原 UNKNOWN 修复分支、primitive 分支及其它 composite 的限制保留；没有把 CompositeSettled 强转为 primitive Settled。当前 writer 前驱与历史 reducer 重放分别验证。

36次实际消费完成：380 RETAIN于21:57:16.719231Z，381 SETTLE于21:57:49.615777100Z，C15分类 ELIGIBLE_ADVANCE，新增2 eligible days；21:57:50.040316100Z LOOP next8，382才实际 BATCH_STARTED8，383是 Driver READ history。21:59:37冻结 head387 running、pending=null、completed15、saved cycle1，确认保存仍8日，本恢复新增 SAVE=0。旧350的未知效果没有进入这2日信用。正常 worker 不等待本次 Git 发表。

## 验证、差异与成本

- 原349非零 DATA 回归首次1P／0FES；它不代替 private issuer、Controller 或现场验收。该机器原件测试留在隔离证据目录，没有引入依赖本机 frozenRoot 的常规 CI 测试。
- 最终正式12个 SourceFile 中，6个外置编译输入与实际 qualified 源逐字相同，复用28类；另6个保留正式既有 Saved 差异并仅作必要编译，首次0／127类／accepted／CLOSE released，组合155个完整来源类。没有重编全 SDK、重跑旧测试或把正式变体装入 Runtime。Git按既有属性作 LF 正常化，发布 blob SHA另记，不把它与 CRLF编译输入的 raw SHA混为一项。
- 12叶均为原 Git tracked 文件的最小变更。Factory／Replay早期因文件系统定位误判为“新增叶”；后到 `git show HEAD` 确认 tracked，HEAD原文与 held active BASE仅 LF／CRLF不同，旧正式正文没有被回滚。其它正式旧差异逐 hunk逆回验证保留。
- 全过程真实失败保留：状态入口缺 coordinator、32帧读取预算耗尽、普通首 DATA 角色遗漏、外部授权 locator误入 archive、saved-open角色和历史353衔接、热 loader缺新增类型、普通 Life wrapper identity、未 RETAIN 已 APPLIED 角色、repair UNKNOWN门、primitive cast。各次通过不追授前次失败或未来健康；30的 GET200不证明新类型热可见，31冷接入事实另记。
- Native累计25次软件 JVM（23编译、2次实际 JUnit），actor `210.9908889001235365s` 嵌在 operator `263.857147799921222s` 内，不能相加；Runtime 的 Maven、live helper和等待另账。原维护5P的 Java结果通过，但 managed事后协议误用留下 accepted=false／close1，后到0VM原 XML独核保留，未重跑。
- 原4MiB metadata增长 FAILED及全部旧 cap／失败原件不改；后继工程预算按真实前瞻分阶段选择，最终正式阶段80MiB，具名成本切点14 roots为66,478,509B。准备、错误、恢复、等待及发表后耗时均不剔除。新增确认保存日为0，本单元不报有限秒／保存日，不宣称10秒目标或性能收益通过。

可核原件：

| 原件 | bytes／SHA-256 |
| --- | --- |
| `D:/ck3-state/resume91-runtime/quarkus-dev307-runtime/attempt26/readonly-recovery-actual26/READONLY-RECOVERY26-RESULT.json` | 6177／`2b710000a8955452427a30841a33eb6aa6049f61bd0de91282e60c5fd5700f75` |
| `D:/ck3-state/resume91-runtime/quarkus-dev307-runtime/attempt36/actual-retain-settle-loop36/ACTUAL-RETAIN-SETTLE-C15-LOOP36.json` | 4213／`608b7b72243083c03199b191db83db040af1ba3ed2158275c21d44e7ee8c010c` |
| `D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/life-postcondition-p0-20261112-01/formal-life-transplant02/FORMAL-SOURCE-READY02.json` | 20029／`d938350fed9f5534e6d8792b7f183408243c0715f993dd54f3e0a22428d77e69`；其 tracked 分类后到更正按上文，不覆盖原稿 |
| `D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/FINAL-FORMAL12-COMBINED155-AND-25JVM-COST01.json` | 17259／`453d3df37971f1da47c1ef8e13c8d0a994e2529a20a1813700a9a5e4fbb29701` |

本文记录软件与具名现场切点；原保存对、其它旧世界计数和已发表历史正文不改写。
