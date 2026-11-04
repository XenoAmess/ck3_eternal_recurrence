# ACK 后只读 fresh READ 的暂不可用重试

本单元修复实际连续两次出现的功能阻点：Life 的 resume 已得到成功 ACK，后续只读 fresh READ 却返回 `fresh_full_state_native_read_unavailable`，原 Factory 随即退出 Java。重试只针对这一个已完成负 ACK 的精确错误，不重发 resume、ARM、SAVE 或其它游戏动作，也不修改原命令期限。

实际第二次失败发生于2026-11-04T21:20:24.384881Z，resume76 ACK 后记77 UNKNOWN、父78 COMPOSITE_UNKNOWN；原期限仍为21:48:11.530924300Z，当时尚余约27分47秒。原件为 Runtime `repeated-negative-read-source18/SOURCE-READY18.json`（11525B／737529fb…）中的12份完整实际源及失败18（10243B／b8ddf187…）。错误必须从原始 NativeWire CommandResult 的 `error` JSON 字符串读取，不能匹配诊断文本或 result token。

新增的包内静态 `readAvailableFreshSnapshot` 是生产 `ActualObservations.freshObservation` 真正调用的只读操作。每个 Unavailable 的 dispatch 与可选原始帧先归档，再判断是否重试；UNKNOWN 只收取原 requestId 的一次结果，未结算时不另发 READ。只有保留原始出站固定 READ、ACK 绑定一致、`native_ok=false` 且原始错误精确等于上述字符串时，才允许下一个新只读查询。其它错误、拒绝、格式／来源不符或归档失败直接沿原失败出口返回，不进行宽泛 IOException 重试。

所有调用保留传入的同一期限，以实际 `maximumFrames` 限制次数，并在重试前按剩余期限裁剪100ms间隔；不生成 `now+timeout` 新期限。中断继续由原调用方恢复线程标志并保留原动作。旧 Received 分支的 ACK 原件、FreshSnapshotQuery、frozen observation、语义装配、帧绑定、来源验证及最终期限检查逐字保留。

模型首派使用12份完整源423013B和5415B合同，21:34:42.595607Z至21:35:38.200476Z真实200／length，55.6047636秒，TTFT10.9592573秒，prompt86056／completion8000。整份内容未读、未提取、0代码采用，没有R2或拼接；源码由 owner 接管。实际 Factory 前像57421B／5dcc2bd0…，候选61284B／c21fe6d6…，仅2个 owned span，全文逆还原一致。正式同一叶的前后字节与该实际变体恰好分别相同；其它文件未整份搬运。

Native 必要首编仅 Factory 1TU，2026-11-04T21:39:42.310814Z至21:39:49.124930Z实际0，javac6.1804063秒／9类／stderr0；ACTUAL contract accepted、MANAGED-CLOSE0、持久 fence、terminal 已观察、预约已释放。已有 normal／A／其它生产和支持类均未重编。新增方法及 lambda 形状不授原地 body redefine，也不把编译当作端点行为、实际装载、周期结算、SAVE或提速通过。

独立软件资格已闭：必要的新 local-service 测试支持桥只转发真实 transport 构造器，避免依赖未接入本模块的 native-transport test-jar；没有生产／POM改动。最初桥＋Test 2TU编译0／5类／5.0398355秒，首JUnit因方法带临时目录参数而无参 selector 不匹配，发现阶段exit1／1.8472175秒、0方法／0断言开始，原红完整保留。只把临时目录移到类字段，原3方法操作和断言全文不改；新Test1TU0／4类／5.6026444秒，桥1与生产9复用，真实3方法3P／4.2186175秒。XML43074B／0c32dd1b…，0error／failure／skip／abort，全部actual／fence／close／terminal及资源释放逐项核对。

3个方法内验证两次精确负ACK先保存后新只读query、真实Received／custody／paused数据；UNKNOWN只同ID collect、未解决时不重写；其它错误不重试；次数与原期限耗尽、归档异常和中断不重放。每次传入同一个期限，真实出站只包含固定READ，没有游戏控制。该资格是软件 NativePacketPort 数据及实际 receiver／生产只读操作，不伪造完整 Managed Root 私有发行／archive／adopted authority，也不授实际 resume 结算或性能。

Native 总资格 `QUALIFIED-POST-ACK-READ-SOFTWARE02.json`（29539B／168e46a4…）、独立 `INDEPENDENT-RESULT02.json`（16693B／9ccd1fab…）和owner行为Ready（16018B／3a016c90…）可追溯。原跨模块旧桥首次编译的原件也保留，没有把它当作本模块依赖或重编旧绿。Runtime独占后继实际采用、正常loader／宿主及清洁边界；Git、文档和软件资格不作为原已执行动作只读收束的前置。源代码／3P／实际装载／真实周期和SAVE分别记账。

新世界首保存是独立已发生事实：Root21:28:32独核原46→只读结算49、C1 SETTLE52及SAVE59，保存时间21:18:10.777188800Z，date53158176→53158368、native26／public14，新8日全部保存。原 command／body SHA／deadline 未变、来源为 SameGameWatch。旧世界508observed／501eligible／365saved、C69和未确认C70不混入新世界分母。首保存后批2再次失败，任务仍在进行；完整端到端性能与10秒目标不因一次ACK或软件通过而授信。


后到 C2／实际采用切点：Root独核84于21:40:53.853522900Z SETTLE／ELIGIBLE_ADVANCE／C2／pending=null，date53158560、native46／public22，新世界累计16eligible，保存仍首C1的8日；85为真实WORKER_RESTART_CAPTURE，原78不重放，旧期限不变。独核 `C2-CAPTURE85-INDEPENDENT-VERIFIED.json`（5889B／879a4962…）与Runtime cleanEND19（17019B／d78522fa…）分列，不据85捕获补授旧世界2370分支或旧C70。

软件3P后，Runtime独占正常清洁边界，采用本P0 Factory＋M7政府上下文完整4叶，共5份实际源；`attempt20/SOURCE-ADOPTED20.json`及原Java精确释放／自有hold保全消费回执分别记录。原Game117900／keeper34052的birth保留，原账本字节未改；不是Game重启、控制重放、离线class注入或body redefine。Maven outer86108实际START21:58:46.714041Z，随后Host97584／birth134383031688380897的新生命周期与21:59:59.4024086 LOOPnext3由Runtime转报；outer START文件本身不证明内层Host／LOOP。当前正在首真实postsetter后态验证，尚不以装载／LOOP授该重试分支已命中、实际Life完成、新SAVE、自然M7或提速，后继按真实回执追加。此段只读已有D回执，无新查询或GET。
