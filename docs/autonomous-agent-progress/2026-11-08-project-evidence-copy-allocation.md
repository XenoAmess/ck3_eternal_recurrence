# P144：证据长度与 SHA 共用同次私有 packet 副本

仅修改 Assembler 的公开 `projectFull` 和私有 `projectFullWithNativePacket` 两处证据 guard：声明未初始化局部数组，在原 first getter 的 `.length` 操作数中赋值，后续原 fresh SHA 使用同一私有副本。ObservedFrame 为构造／访问均克隆的 final record，ExactRef 为无回调的不可变字段 getter；不提前读取，不调整 facts／stateSHA／evidence.bytes／长度比较／SHA receiver 的求值顺序，长度不匹配时仍不 hash。所有消息、hash／parser／Guard、P143 counter、后继解析和 projection body 保持，无新生产类型或 API。

P141 没有 emitted 这两处 guard 的直接 clone 链，邻近7972是后继 getter，不能作直接频率或成本证据；历史整体 `PARTIAL_BUDGET_FAILURE` 保留。本单采用基于窄所有权证明与实际 caller 测量，模型未参与，0 HTTP。

## 必要验证及真实覆盖

生产首次必要 Assembler 1TU／6类实际通过，Driver3保持。Native 最初准备器把 Reader 来源硬编码在 cp[3]，实际为 cp[2]，在 CFG／claim／Java 前 ValueError；原件保留，独立 Q02 修 metadata 后才首次编译，非源码／Java失败。

测试实际为2TU／8类：新修改310Test6类，加未持有可证缓存的原 `DriverNativePacketInputDataTest` 首次必要编译2类。该原Test逐字等 d47 Git20795B／019fe1d5…，不改、不作为新Git文件。最初 Ready 的1TU6只为 proposal，后到授权及 immutable source pin 另件补充，不覆盖原Ready，也不称旧类曾缓存通过。

功能新方法验证 null／facts／stateSHA／证据长度／SHA／坏 framing 的复合失败顺序及正向 v3完整语义。真正私有分支由既有 `packetInputsKeepLexicalDataAndStrictFallback` 经公开 `replayCapturedOriginals`、null decoder 到 `assembleWithNativePacket` 进入，保 lexical／原件与回退；旧 Replay P4／v3并不进入该分支，本单不借其名称授覆盖。功能2方法与唯一组件1方法共3个不同方法（2new＋1affected）跨2JUnit全P；无 Replay／Generic Boundary／Applied／Main／JFR额外运行。

## 实际公开 projectFull v3 的四行组件

A 是最新 P143 Driver3＋Assembler6完整9类，同 child loader，含 EncodedByteCount；B 为新 Assembler6及原 P143 Driver3 parent。不用旧 A8，避免把 count 改动混入本单。双方对同 frame／facts／ref 对称反射调用实际公开 v3 `projectFull`；各自 FullSnapshot 的公开 getter 核对 actual／facts身份、originalEvidence、完整 semantic bytes／member order／binding及原 packet／state SHA，不 cast parent FullSnapshot 或扩展 Complete／P4 类型闭包。getter与后置核验在 target bracket 后，完整费用仍计入JUnit。

固定 A/B/B/A，无额外 target warmup，输入 state3400339B／packet3400438B：

| 行 | wall ms | 当前线程 CPU ms | 当前线程累计分配 B |
| --- | ---: | ---: | ---: |
| A0 | 118.1650 | 62.50 | 70290768 |
| B0 | 38.8133 | 31.25 | 64607760 |
| B1 | 36.4624 | 31.25 | 64469704 |
| A1 | 32.8048 | 0 | 67870968 |

分配均值69080868→64538732B，少4542136B（6.57509978%），两 B 均低于最小 A。以末 A 为基准，两 B 少3263208／3401264B；首 A 额外2419800B、B0额外138056B，均值差不能全归一次 clone。局部引用可能延长数组存活，累计分配不等 peak／live heap。

wall均值75.4849→37.63785ms（−50.1386%）只作冷样本描述：两个 B 都慢于末 A。CPU均值同31.25ms，但末 A 的0为粗量化，百分比 UNKNOWN，不能报零成本或 CPU提速。Root只采用软件 allocation，不授稳健延迟、私有路径速度、完整 verify／物理IO／worker或自然频率收益。

## 完整成本与原件

旧／parent Driver初始化379.6361／2.5125ms，Assembler load/init1.1107ms，setup1.9918595秒；报告物化前2.2650106秒。生产编译 actor／outer6.7108022／7.6915秒，测试编译7.5056475／8.533175秒；功能5.1215725／6.0913758秒，组件5.0700292／6.0665047秒。actor含父记录与资格工作，不称纯child wall；功能／组件 child stderr均302B，outer stderr0不能代替。

首生产 BEGIN `13:55:24.597883Z` 至末组件 CLOSE `14:06:29.646418Z` 为665.048535秒；更早候选Ready至末CLOSE为1011.802741秒，包括准备器0Java错误、审阅、编译及等待。原错误不删、不追加 JVM挑绿；本单聚合元数据1625753B低于4MiB，P141旧预算失败不改写。

本单0 saved，源码／软件／发表与 Runtime／新依赖热载／SAVE分层，不授 head47／P100 或10秒目标。后继P145 clone合同暂不实施；P146另准备固定三版本96调用的D实验方案，接受无CPU／延迟收益或回退结论，不用本单冷均值替代。

- [Root allocation-only 决定](D:/ck3-state/resume91-root/post-vacation-20261107/P144-EVIDENCE-PRIVATE-COPY-ALLOCATION-SOFTWARE-ADOPTION01.json)：5309B／`2a0ba0c8d250c0343a7b44b240e118d10cddc32a678f26e66979a4240f01a5c6`。
- [Native 最终资格](D:/ck3-state/resume91-native-integration/p144-evidence-length-test01/QUALIFIED-P144-THREE-METHOD-SOFTWARE-AND-PUBLIC-V3-COMPONENT01.json)：100317B／`8047c5e7c5d4b75e6a112917c7fb0934230207332aba24c8f63d1aba2428b05f`；[唯一四行原件](D:/ck3-state/resume91-native-integration/p144-evidence-length-test01/tmp-component/junit-13238113093731517316/p144-evidence-packet-copy-component.json)：6396B／`be8e2d928d1dd02cac25d0896b6526a940a8090f6053050270043f7a06888d78`。
- [Owner 全实际复核](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-evidence-length144/P144-OWNER-ACTUAL-REVIEW01.json)、[2TU8及immutable原件补充](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-evidence-length144/test-draft01/ACTUAL-TWO-TU-AND-IMMUTABLE-PACKET-SOURCE-APPEND01.json)及[同字节正式采用](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-evidence-length144/FORMAL-ADOPTED-AFTER-ACTUAL01.json)。
