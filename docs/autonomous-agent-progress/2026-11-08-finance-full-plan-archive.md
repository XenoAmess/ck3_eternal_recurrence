# P111：Finance quote 保留完整 PlanningRequest 原件

本地日期 2026-11-08，实施原件的 UTC 日期为 11 月 7 日。持续优化目标保持 active；本单元不处理原 P100／UNKNOWN 链，也不授实际装载、Game 行为或新增保存日。

P110 已缩减现金 SDK 的声明角色，但 Finance quote v2 把完整 PlanningRequest 放在 1 MiB manifest 中，仍会拒绝带大历史的合法原件。P111 保留小请求的原 v2 inline 表示；仅当 PlanningWire 原始编码本身超过 1 MiB 时，使用新 v3 manifest 的 `planning_request_ref`。完整原字节通过现有同 writer 的 FullMaterial CAS 保存并实际 `loadFullMaterial` 读回，核长度、SHA 和每一字节。现有 FullMaterial 上限仍为 64 MiB，并非 PlanningWire 的 256 MiB 都可归档。

verify 与 originalRequest 共用严格版本加载器，每次重新实际打开全文。v2、v3 分别检查精确字段集合，未知、缺失、null、非文本 schema 及混合字段拒绝；不从解析、权限或原件失败回退到另一格式。旧 v2 的 quoteObject／quoteBytes、1 MiB 结构与数值合同保持，原命令及其 hash 不重写。

完整 source、Session、原 head、SEM、四 read、各 owning decoder、六份原 spending document 及 pin 校验保留。Current 的七领域软件夹具与 Archive 所要求的六领域分别记账，后者包含 CHILD_DEFAULT_MARRIAGE。P110 的共享现金角色只在原件核验之后供 SDK 判断，不裁归档全文来过门。

实际源码为 application/effects/FinanceEvidenceArchive.java，32472 B／SHA256 `3e626327bb264ac9fde4638b025b20a74e4d512eb1f7d5c03a959c527357f6c2`。必要生产 1 TU 已 exit0／4 class／5.3175682 秒，UTC 20:13:15.869740Z 实际资源关闭；P110 Collector 12 class 原字节复用，未重编。

两次真实模型请求分别为 11952.204／17744.303 ms，TTFT 4189.712／963.776 ms，prompt/output 31593/1311 与 31485/2952，cached tokens 均未报告。首轮未接通 writer 与两个 reader 的版本分派，拒收；第二轮核心部分采用，owner 修正候选不完整括号并保留旧 helper。它们没有作为失败版本编译。

完整公共集成使用 ActionWriterIntegrationFixture、实际 collector、PlanningReadCoordinator、ContinuityWriter 与 NativeOutcomeArchive；只在自有临时目录内生成明确软件数据。七领域在同一 writer 注册并导入，四读由实际 Guard 和 receipt 生产，checkpoint port 明示软件标记而非 SAVE。源码中的 dispatch／observer 与历史 ROOT 回调均禁止在本单元调用。测试复制真实 ready 发布的非 snapshot 观察字段，当前 snapshot 则来自真实 held Complete，不用构造 actionSteps 充当注册证明。

完整软件验证已通过，三个新方法分别来自三个真实 JVM：Test03 的旧 v2 结构／cap／decimal 方法 1P，Test07 的 small v2 公共集成 1P，Test08 的 large v3 公共集成 1P；不是一次同 JVM 3P。large 最终实际 42.1415376 秒、outer 42.8581214 秒、控制台 runner 40409 ms；XML suite 为 40.165 秒、唯一 testcase 为 40.134 秒。UTC 20:59:20.715767Z 实际关闭并释放资源。

最终 large 原 PlanningWire 为 1060851 B／SHA256 `96e5502c07617103fb4debc7a05169111878d3ce624ecec8ec70c83f4f43009a`，manifest 为 13737 B；small 原件 8060 B、v2 manifest 21488 B。大原件包含未知成员顺序和 1.00／-0.0 词法，完整回读及 PlanningWire 重解码均逐 byte 相同。实际 bind→verify→originalRequest、重建业务 Archive 对象冷读、严格 FullMaterial lane、无 full lane 的显式拒绝、未知／缺／null／非文本／混合 schema、超 64 MiB 引用、缺件／错误 SHA／错误文档及外部同字节别名拒绝全部通过。原七领域文档、head、完整 request 与零 action writes 断言通过；未冷启真实 writer、执行 Native action 或制造 Root 权限。

保留 owner Test checked-IOException 编译 RED、Native 漏 JNA tmpdir 的前置运行错误、owner packet producer 误用 StrictJson 不支持预算的运行错误，以及实际 Gift producer 未选出候选的后继失败。一次必要 small 诊断明确返回 root_private_member_or_frame_mismatch，实际 request／ROOT 均 actor73、native2、date53144328，direct vassal 包含 67108866。

随后具名 first-class 核验发现：实测 CandidateCodec／Policy 来自旧缓存、不含已发表 NativeFactionId 合同，整个既有 CP 也缺该 class；当前源码和原 faction-zero-final 数据均明确允许 faction0。按具名 P090／NativeCharacter 谱系复用 10 个当前 source family 的 77 class 原字节，仅必要增编当前 CandidateCodec 1 TU／1 class、exit0／3.6971659 秒，不把原合法 0 改成非零或重跑 P090 旧绿。该依赖采用与本次 Archive 1 TU 分开记账，未将首次编译／夹具依赖冒成零工作。

缓存同步后 Test07 是 1P／0F／1E：large 所有归档断言与打印完成后，因测试把大量只读冷／负例 I/O 放在外层 physical capture 内，退出时超原 25 秒窗口 1.9739644 秒；它仍是 error，不追认为通过。Test08 仅将 large 归档重放移到 capture 已正常关闭／qualifyPhysical 后，仍在同一个 held writer 内，真实 current→gift→bind 保留在原 capture 中。全部冷读／负例保留，request、command、read 的原期限生成规则与生产 freshness／Guard 均未改变。只重跑此前 large 方法，small 和 codec 的原绿保留。

具名原件目录：`D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/finance-full-plan111`；生产实际为 `D:/ck3-state/resume91-native-integration/p111-finance-full-plan-prod01`，公共夹具首次两 TU／39 class 为 `p111-public-fixtures01`，0 旧测试执行。最终 large 原件为 `p111-finance-full-plan-test08/actual/junit`，依赖闭合为 `p111-current-finance-consumers01/REUSED-CURRENT-P090-CONSUMERS.json`，64081 B／`e92bc3ef10e7e2143e6173e112276b790154e1f020375a9df9dde3d428e9bb1c`。全部环境、源码、旧缓存及 lease 编排失败原件分别保留。P112 已独立正常发表；P113 完整 Construction quote／material 的原件引用闭环继续，原 UNKNOWN／P100 限制不变，10 秒／新增保存日目标未达。

原资格 `D:/ck3-state/resume91-native-integration/p111-finance-full-plan-test08/QUALIFIED-P111-FULL-PLANNING-ARCHIVE.json`（17694 B／`19752cf5fddd64e6736f00449ab2b72f32b5677a0b3b076f1e48b24a2e01f80a`）保留；其误名 manifest SHA 字段已在同根 `QUALIFIED-P111-FULL-PLANNING-ARCHIVE02.json` 更正为 full_planning_sha256，18384 B／`d622728027ecdc0683e8c32da9ae43e970021de7d41e32fa32d41b89d61324f2`。本文 96e55… 始终指完整 PlanningWire，未给 manifest 虚填哈希。一个新 Test TU 累计六次必要变源编译，首 RED／五次 green；不是六个新增测试 TU。manifest 大小缩减来自引用表示，全文仍独立保存，不是存储压缩或已测运行提速。
