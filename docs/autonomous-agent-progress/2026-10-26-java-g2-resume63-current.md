# resume63：REA、Java 全能力迁移与 G2 接续

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-27T00:46Z 更新；任务继续执行。本页接续 [resume62 交接](../handover/2026-10-26-java-g2-resume62-rea-runtime-handoff.md)和[来源索引](../handover/2026-10-26-java-g2-resume62-rea-runtime-handoff-source-index.json)。

目标是使用 REA 完成 G2 M0–M7 原生研究与 Java 落地，完成 Python 能力迁移后使用 Java 继续普通自动游玩。[完整对照](2026-10-26-resume63-migration-and-g2-matrix.md)分别记录八项业务门槛及全迁移范围。当前 Java CK3 启动、新增游戏日、SAVE、RESTORE均为0，完整实机 G2仍0/8。

2026-10-26T14:35–22:00Z的完整历史、失败和当时有限卡保存在已交付的 `fff86e9c2aebb1eb00d1151875e1266cbc5a4b24` 文档快照；后继文档交付 `534375b1bda095ff92846dbfbb866a30e4c0e117` 保留远端同事增量。本页压缩已归档段，不删除对应原件或把旧失败回填成通过。

继续复用独立 SRC/BUILD/m2/TMP。Host唯一写Maven输出与Tools源，各领域按短窗交接；已知错误先局部增量，必要修复闭合后最终完整验收。Native按真实8GiB峰值采用-j1；REA最多四个独立provider按READY与实际内存调度，不重复取证。Genesis保持seq0，禁止重建。Steam只后台核离线，启动前另取新鲜准入；不接管身份未核旧CK3，不启旧蓝色决策窗。

任务总线 `ck3-java-g2-rea-resume63-20261026`，00:39:32Z heartbeat9058，resources为空；财务CAS683仅前向必要净额，不延旧执行卡。Root本轮必要构建、Own、SDK、Native、Delivery及具体REA范围的owner review至2026-10-27T12:00Z，各命令仍须自己的新鲜卡和资源。全部大输出使用获准D根。Git由Delivery普通FF、保留同事远端；本地master HEAD/index和既有dirty不整体stage或reset。

此前04:30–06:00北京时间首实机乐观窗口已撤回，当前没有可靠替代时间。31000秒为完整SDK覆盖预算，不是预计等待时间。后继门槛为：必要迁移局测与真实Tools资格→Own和Native正式产物/原生corpus/精确EXE登记→完整SERVICE和Fresh4、Canonical30→当前权威与后台Steam准入→Java罗贝尔1066首批→真实SAVE/RESTORE。首场SAVE必须由普通动作产生，不可预造为启动循环前置。

## 22:00Z 前向结果（本地27日06:00）

machine_id为`xenoamess-full-tower-eb9d2c1186`。Full119的Maven stdout为BUILD SUCCESS，149份新XML独核1093/1093成功、0失败/错误/跳过，实际134 main/167 test重编；但外层生产者真实exit1/1754.9402208s：普通bootstrap Jar旁缺lib目录，producerClosure在Maven之后拒绝。fresh deployment自己的Jar/lib5存在且匹配，不能混称Maven失败或fresh缺依赖。最终BuildReceipt没有产生；内层Maven数值exit、WJP峰值/active未持久化，不能据stdout补成0。实际晚启动少23.2679843s的原窗口偏差也保留。[独立拒绝回执](</D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04/acceptance63-tools119/TOOLS119-INDEPENDENT-FINAL-REFUSAL01.json>)13556B/SHA`9aeed8a45b85ff23525c57c8bebc26e6341332b0de3b110aa55d732d99c9da3e`。后继修现有POM依赖复制/普通载荷输出路径，同dev/classes/m2继续复用；119原snapshot和bootstrap不覆盖，不重跑未变的整批作为局修前置。

Main120真实164项150成功/9失败/5错误；121真实85项81成功/4失败；122真实55项41成功/3失败/11错误，均保原件。Finance观察8、Family恢复4等已通过，不能相加冒完整迁移验收。实际生产修复包括错误能力名称、mandatory诊断早退、M0计划custody及军队canonical预算；测试的日期/receipt版本/checked IOException也分别按真实合同窄修。12302/12303均是编译退出1，无JUnit。12304在原目录`--offline -T2 -pl local-service -am process-test-classes`真实exit0/15.7397199s，99必要源与1096基线MATCH，仅重编APP一个测试、NT一个主文件和LS一个测试。随后APP122三叶修复净10388B已采用，实际受影响整类测试仍待新有限phase；不授全图/业务通过。

canonical helper整模块58/58及14项canonical导入/路径核对已真实通过，Job均0。已有venv会重定向子PID，不能满足原UAC实际PID守卫；负例已验证direct-base Python可保持rootPID==receiptPID，尚无管理员设置执行。共享Java v2修复将完整机器ID helper纳入runtime inventory。Holy五个原生target实际-j1编译链接exit0/37.1218006s、Job0，峰660918272B；五份正式Shared运行/corpus尚未产生。Commander14场景原生corpus仍缺，不能用合成gold或跳过代替。保留源与可复用编译源正在共享typed合同内对齐，Bridge与fixture共同消费。

REA M7新117B/25条指令已闭：旧引用计数1减至0才写job+60=3，随后调用释放相关函数；3不授成功、异常、取消或清理完成。原enqueue的queue指针与manager+1C0计数器已在新结果纠正，旧原件不改。[结果](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m7-job-helper01/RESULT01.json>)8243B/SHA`87d232bf4ba5d99efb343e77d2d7695ec6189987c633d1955450f7644b4ff451`。Java生产链没有直接消费内部job状态，因此不新增孤立模型；现有拒绝仅以state3授继承资格的回归方向与此一致。

21:57:35Z普通heartbeat9046/resources为空。Root新review到23:30Z，仅供必要后继发新有限卡，旧expiry/真实失败不改。文档已FF交付fff86e9c，完整Java源图尚未交付；原04:30–06:00乐观首实机窗口已撤回，尚无可靠替代时刻。新的Java CK3启动、游戏日、SAVE、RESTORE均0，完整G2仍0/8。继续完成实际测试、Tools/Own/SDK、原生运行资格，再后台刷新Steam离线准入并切Java实机。

## 23:00Z 前向结果（本地27日07:00）

同machine_id。Main126真实Army13+NT MAA6共19/19通过，exit0/12.8630684s；生产仅修严格canonical wire比较，未给DTO热路新增encode/parse，原Pythonoracle与错误protocol/custody回归都运行。127 Store15全过，NT原producer2中1失败，Root5未执行：SCRIPT双引号完整保存在class，却在直接ProcessBuilder启动后丢失。本机JDK字节码实核默认allowAmbiguousCommands=true走LEGACY；原测试改用已有WindowsJobProcess，SCRIPT和预期不改。128真实进入OpenBLAS后触256MiB预算、child124，未把它改称引号问题。局部将BLAS三线程变量置1、保60s/256MiB，130原整2真实通过，exit0/10.913351s。

129单独原RootRestorePhysicalIdentityTest整5/5通过，exit0/111.9007813s，suite97.638s；原ready20s、validity30s和nested query未放宽。原批Store、NT失败和旧JFR五失败仍各有原件。这是软件恢复回归，未授真实Game SAVE/RESTORE。Host实际129回执33598B/SHA`e16190e53f327f057fb4d3092bf46723ee4e9e70fd927db90a90f3ef3a628c1c`；130回执33532B/SHA`e8d570d9a5c0f0b168b4f90b0a647cb9f71c7111232d48e845fed93e6b7d4acb`，均在O63。

Tools131同缓存局部编译exit0/21.2088631s，重编135main/169test，169输入与test树EXACT；328source及104/109保护输入MATCH。[独核](</D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04/acceptance63-tools131/TOOLS131-INDEPENDENT-COMPILE01.json>)无JUnit信用。132实际222=217P2F3E；fullWitness、ENV compile绑定、UAC原pin与两原样Python资源134同窗采用，6类61=60P1E。唯一嵌套codec错误修后135仅Defender16/16P（22.2935538s），v1/v2完整Result往返及根尾随拒绝均过；134另五类45P独立保留。136普通Jar+lib5与1466classes完整MATCH，137默认Maven离线实际装入D缓存，0/1.8359574s；均非qualifiedT。Holy5登记缺口正补显式v2单目标链，最终input仍HOLD不复制；Main8Jar独立继续。

Root将9df nullable与Declared V1/V2完整前向合并；首69项68P/1F为静态夹具两个非void空body，最小修后完整69/69及两项改范围strict通过。Python producer原样V2 JSON3802B已在135通过Java核心读取与codec回归；[实际终态](</D:/ck3-state/ck3-java-g2-resume63-m0-native01/helper-nullable-test01/NULLABLE-TEST02-CLOSE01.json>)保留首败。实际WMI/Add/UAC为0，尚无新qualified Tools或新Java CK3。

REA新增M1 caller1757、M4 SIMD locator、M5 helper477、M6 prefix128均实际闭场；M1批量输入/前置gate、M5 F10/F18写入、M6初始RCX来源已闭，仍不授自然继承或战争合法性。M4找到1候选，218B注册体仅按明确新范围准备鲜卡，review至2026-10-27T12:00Z，不延旧卡。无消费者的字段不硬塞Java模型。完整SDK至少31000秒是覆盖预算，非耗时预测。必要修复闭合后一次封存；新增游戏日/SAVE/RESTORE为0，完整G2仍0/8。

## 2026-10-27T00:46Z 前向结果（本地08:46）

同machine_id。Main138首轮因未选政策依赖失败，只实际生成3Jar；139仅validate。140复用同目录默认Maven选必要依赖，真实exit0/15.9051908s，reactor31项中仅剩余5Jar新产，0编译/测试；8个当前普通Jar已齐，不授完整SERVICE。独审核五Jar8073个条目body/POM及138三原SHA。后继RuntimeDuplex9、M2Unknown、LS/MCP/M7及mandatory Combat corpus回归尚待执行，已通过的Root5/Army19不无因重跑。

Tools141新增Holy五个显式单目标v2分支，保留v1原target/枚举语义。实际135main/169test编译成功；34项为33成功、1错误，无失败/跳过：Defender17（含五target两schema）和ActualReader6全过；CurrentPlan11中的唯一错误为测试把jna.tmpdir覆盖到JUnit临时目录，加载DLL仍被VM持锁，清理AccessDenied，非业务断言失败。142仅两测试叶净1256B/0新增簇：沿用已批准harness JNA目录、保cleanup/identity/copy断言，并在原Reader负例补HOLY形状正例、缺ENV/graph及legacy卡真实拒绝。142重测17项待终态；不重复已绿Defender17。FinalTools源输入仍未复制，142通过后沿原ControlBuild完整VERIFY，136普通bootstrap仅作为生产入口，不能称新qualifiedT。

全能力复核发现新增真实迁移断链：Python auto_turn在长动作期间启动camera_pre_advance_scope并调度LatestCameraFollowWorker，Java当前普通AUTO尚未接入跟随worker，transport只接REALM/QUERY，不能把基础camera合同当迁移已完。现准备最小Java接线：原单writer持intent/once permit及实际结果归档，异步worker仅处理不可变请求与有限原生采集；保持游戏UNKNOWN全局守卫，不能用第二writer或串行等待冒充原行为。代码与验证仍待完成。

远端498b5af的失败runtime恢复修复属于机器4-8e1c2f1861，不能外推本机。原canonical allocator在本地及历史Source33仍是旧pin；新测试属于独立CI三整模块step，不在Canonical30或Fresh4。须先采用真实源码，再由原producer更新新canonical_sources→plan→bound→config；历史Source33不改，不填尚未存在路径的未来SHA。

REA又取得两项有限进展。M4完整218B注册体证实GetCancelTooltip对应callback12B4480；该63B callback双解码逐字节一致、三阶段exit0/0owned，只检查空输入并转交三处opaque调用，未计算退款，Java仍empty quote/credit0。M1在完整mapped .text单目标流式定位得到唯一原始E8候选2787FC1→2785FD0，包含RF[2787C10,27883DB)1995B；未读主体、未证明指令边界或自然继承。M5 helper477闭合F10/F18写入但不授战争合法性；M6初始RCX home来源不授loaded bank；M7 state3不授完成/成功。完整八M研究仍未完成。

官方534375 CI `40420386291` 已FAILURE：bootstrap与qualified各636通过，完整链缺实际fixture-production request而NOT EXECUTED，非javac失败。没有把局部测试或HTTP/ACK外推实机。新Java CK3、游戏日、SAVE、RESTORE继续全0。
