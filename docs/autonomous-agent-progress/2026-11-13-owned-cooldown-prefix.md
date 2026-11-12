# 已持有的冷却 proof 前缀复用

历史恢复会在每个 canonical edge 重建 Driver/cooldown，后继又从最早 proof 重放前缀。Source70只处理实际 Native archive、同一原 owner／writer Session 和有界 HistoricalReadScope 已持有原件的私有冷却 fold。普通 live `inSession`、未知外部 Archive 和 opaque 来源仍完整旧路；这不是本轮 Action profile 最大的 derived-guard/canonical-receipt 热链修复。

NativeArchive 的真实 facade 经 owner／Session／Store／writer／当前scope精确检查后，应用层只持一个私有 VerifiedPrefix：原 proof sources、已处理集合、末状态与最后proof，不持完整Driver、Nativeframe或许可。trace在COOLDOWN chainwalk和proof-ref读取之前开始，已验证依赖包含收集阶段的原proof。匹配前缀仍核原max-chain、seen/cycle、末aux和原state。命中前后按同一Store租约重新验证全部依赖；未持有、fallback、不同scope或opaque路径完整回放，不凭head/state相等省当前校验。

Store的依赖trace有界、嵌套外层含内层实际读取、fallback/disqualify为粘性；`verifyRetainedDependencies`先核持有成员，再走原leased-publication metadata／身份检查，不重建历史payload。真实mtime或identity变化保留firstFailure并poison当前scope，退出清理。before/after文件身份、ACL、动态root、容量、force及原错误先序没有删除。正式原lease retirement语义保，成功close/remove会使活动trace失去可复用资格。

final03进一步只圈COOLDOWN：原declaration/strategy header完整原体每次先验证，失败清cell；opaque failed-READ历史head检查也显式拒绝prefix资格。不同处理阶段或proof不被当成不同basis的证明；旧模型两次NO虚构loadMaterial/loadNativeFrame自动调用opaque verifier，均未采用。生产四叶全由owner实现，未将这两答的零hunk改记成实现贡献。

实际首次四TU49类首编0，Store真实Windows fixture整4P，消费者整2最终P。消费者首0P2E源于测试在readonly HistoricalScope内发布suffix/badProcessed物料，被原Store guard正确拒；修订仅将物料预先实际CAS发布冻结，原断言／两方法与guard不改。final03实际仅DPP＋Archive两TU19类必要差额首编0，Runtime/Store qualified family复用，同一Store4＋consumer2一次整6P。正式四TU49类独立首编0，复用原Test/helper，独立同整6首次6P/0FES，21:40:44.468548Z释放。不是沿actual绿转授formal。

原日志的有限小fixture支持真实私有分支：cold一次replay为8次publication entry；同scope三次warm replay（含真正alias）仍8；未知publicProxy两次为16；base＋两次append共三replay为12。全部scope正常finish、validation失败0。这里的entry counter不包括`verifyRetainedDependencies`直接做的metadata/lease检查；命中前后各做新鲜校验，所以不得称零IO、CPU提速或生产命中率。短前缀甚至可能增加guard工作。badAux／processed拒绝、fallback／嵌套／poison／freshmtime由实际回归覆盖，ACL-specific及全部Root授权矩阵未授。

Store测试只partial借用了本地模型第二完整测试稿的nested/fallback/current-scope断言和控制片段。首稿空stub和第二稿非法装配均未执行；owner提供原合法Store＋WriterFixture装配、imports／receiver／预算与另外两项实际负例。旧模型任务误称originalWriterLock不存在是owner反馈错误，不移给模型；实际getter存在。生产四叶、consumer测试及后到final03均不借此授模型实现贡献。

正式源码保原差额：Runtime unavailable-query过滤，Archive诊断／historicalBorrow／provenance集合，Store cause-walk／单租约pair retirement／decimal stamp保留；不是active整叶覆盖。四个正式候选为DPP43116B/e4d8b64d…、Runtime55618B/f718a6ab…、Archive136670B/ee2934c0…、Store52622B/a7893ec4…。新增私有数据类型与结构未授HCR、新type装载或正常reload能力。

具名来源根 `D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/life-postcondition-p0-20261112-01/persistent-cooldown-prefix-source70` 下的SOURCE-READY70-03.json（5760B／8967bedf…）与SOURCE-READY70-FORMAL03.json（5137B／20f86306…）保exact全SHA／BASE／差异。Store test11086B/fa1e0979…；consumer revision02 test20682B/7e47ca11…，均正式保留。

Native原件根 `D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01`：cooldown-prefix70-delta03-compile01／delta03-whole6-junit01、cooldown-prefix70-formal03-compile01／formal03-whole6-junit01及最早Store/consumer失败原件保留。SOURCE70-FINAL03-ACTUAL-FORMAL-WHOLE6-AND-181JVM-COST01.json（23189B／951b307f…）保全部XML、输入未变、ACTUAL／CLOSE、既有metrics和累计成本；不为取证新跑诊断。

本单元未被Runtime采用，当前实际worker仍Source69＋71＋73。Source70是cold/readonly历史scope软件候选，不授ordinary Action profile覆盖、现场hitrate、速度、Game推进或SAVE。源代码、软件、正式发表、未来loader资格与实际行为分开；健康Game／worker不为文稿或这个候选另启／重载。
