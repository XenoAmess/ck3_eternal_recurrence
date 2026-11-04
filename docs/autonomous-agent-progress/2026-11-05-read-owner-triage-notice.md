# 首份负 fresh READ 原件归档后通知 owner

实际 batch3 曾在约60秒内发出80个不同只读 READ，均得到相同负 ACK，随后恢复才发现一个事件弹窗。这里增加的是早期诊断通知：原 `readAvailableFreshSnapshot` 在首份已完成的负 ACK 通过原绑定校验、dispatch 及可选 frame 两项归档回调均成功后，输出一行有界 JSON；原重试、次数、期限、UNKNOWN 同ID collect、成功投影与 Guard 全体不变。它既不判定 modal／Native 根因，也不触发 UI、重放控制或刷新旧 deadline。

通知记录真实 read request ID、当前实际 action scope（若有）、输入观察期限及有限错误。该 leaf 不持有父命令 deadline 或归档路径，明确标为 NOT_HELD／由回调保存，不虚造关联。错误 token 超1024字节省略正文，整行上限8192字节；格式、时钟或 stdout 的 IO／Runtime 诊断异常不改变原观察结果。原件归档、transport、canonical/proof 错误在该 catch 外，仍按原语义退出。`attempt==0` 仅尝试输出一次，不因 sink 失败再通知。

第一版真实1TU编译0／9类、6.5590724秒，但 outer 多了一个外部 `PacketIdentity` 的 InnerClasses 引用；没有发生实际 VM 拒绝，也不将该属性差异判作必然不能 redefine。第二版仅删去这项可选 packet 诊断的4行，原 ACK custody 和归档校验保留；真实1TU0／9类、6.2230804秒，Native 比较全部9类的 fields、methods（含 synthetic）、Nest／Inner／Enclosing／Record／Permitted 及父接口结构均相同。该结构证据不等于已实际 redefine。

新 Test 1TU生成8类，5.4888671秒；两个新方法2P，4.142秒；原 post-ACK 三个已编译方法仅受影响 RUN，3P，4.4918秒。新方法通过真实 software NativeGameTransport／receiver／custody 验证 UNKNOWN 只 collect 原ID、负 ACK 双归档先于一次通知且通知先于下次只读写入、sink 抛错仍返回原 Received、原件归档错误外逃并不继续、正 ACK 缺帧／持续 UNKNOWN 不误通知、长错误为有界合法 JSON，以及所有调用保持原输入期限。两个 XML 为 `3318b609…`／`f58bdc7b…`，无 error、failure、skip 或 abort；每 phase 的 fence、close 与 terminal 独立闭合并释放，没有重编旧生产、Support 或旧 Test。

正式生产与实际软件变体逐字相同：`c1308a3f…`；新 Test 原样为 `1a33beda…`。生产模型首派8000 length，全文未读整弃0采用、无R2；独立测试模型完整回包的新增方法源审均拒，owner 接管。第一版／第二版、模型及各阶段实际成本完整保留，见[来源索引](../maintenance/2026-11-05-read-owner-triage-notice-sources.json)。

截至此发表切点，没有为验证通知制造实机负 ACK、UI输入、GET 或重启；实际 source 采用、Quarkus instrumentation／loader 行为及现场通知送达由唯一 Runtime owner 另验。正常24继续，不能用这2P＋3P宣称 modal 自动恢复、全 Native 可用或性能达标。

新45秒热点调查仍区分路径：`finishPlanningReads` 是包含原 work 的上层包装。后到定向统计中 Publisher.flushActualReads／prepare、RootReadHistoryAuthority 与 unresolved-history 目标均无 captured presence；这不证明零调用，也不足将新 READ-scope 候选认作本窗热点。该任务唯一模型完整回包已源审拒收0采用，保成本、不R2、不送编测。下一源码调查沿实际出现的 ActionContinuityAuthority.reduce／canonicalReceipts 及原 live scope 的重复原件链，保动态身份／容量校验和 parser／hash／oldencode 冻结。
