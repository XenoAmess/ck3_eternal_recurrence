# resume63：REA、Java 全能力迁移与 G2 接续

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-28T01:29:46Z 更新；任务继续。本页接续 [resume62 交接](../handover/2026-10-26-java-g2-resume62-rea-runtime-handoff.md)与[来源索引](../handover/2026-10-26-java-g2-resume62-rea-runtime-handoff-source-index.json)。[完整对照](2026-10-26-resume63-migration-and-g2-matrix.md)区分八项业务门槛和全迁移范围。

目标：REA M0–M7研究及Java落地，完整迁移后普通自动游玩。Java启动/日/SAVE/RESTORE均0，G2实机0/8。首启与迁移并行；31000秒仅SDK预算。

旧14:35–22:00Z历史在 `fff86e9c2aebb1eb00d1151875e1266cbc5a4b24`；后继 `534375b1bda095ff92846dbfbb866a30e4c0e117`、`3a2b06bfb7a4ef1e2a41c11a7dcfe8974b038bb5` 保留完整失败/当时scope。前页19901B/SHA66640f022e029a6d9fd0d95abedd80413e9a1008e5c81572af58b5142deeb51a归档3a2b；随后7939B/SHA9b48367aeaf95a566ff1bd5060af3241f2f8d308263fe46edbed915930467982已完整交付 `9eb67939de0039839179140785cd0a57978296bd`。本次压缩旧171/176叙述，不删原件、不回填旧失败。

复用独立SRC/BUILD/m2/TMP，改动模块及必要依赖增量，最终完整验收。Host唯一源码CAS，Launcher唯一Main输出writer。Genesis seq0保护，Steam后台fresh离线，不接管旧CK3、不启蓝窗。保Root HEAD/index及dirty，本次仅此页，不Git。

## 已有正式Tools与Own

Tools172完整VERIFY独核151XML/1142P/674pins/1466类/六部署；WJP0/1557.0979s/active0/峰1381801984。[独核](</D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04/acceptance63-tools172/TOOLS172-INDEPENDENT-FULL-VERIFY01.json>)22658B/40ad2f17615eebd38b75317e61521e024117644d9349b5faf04839a85c66ef74。原回执W/logs/build-java-tools-host172-final.json205527B/5012360b919fe61a077e484216365178fe18a5ecddf1561c46905e9fb30c2610。

Own172原41→46及2JUnit P/四Job0，42角色/7 relocation/135同档类。[actual](</D:/ck3-state/ck3-java-g2-resume63-own-successor03/artifacts/tools-postqualification/actual.json>)29625B/bea6adaa84c4500ae9318e78f9fa130c2ce66501716e5017257841e60b8e57ab；standing须取full_own_actual_ref26131B/47604360…，非机械binding代31000s。Own192的03曾被10MiB帽小于固定pending16MiB拒；后继09实际0/118.8966158s，Own46及2JUnit P/四Job0，actual29624B/9fbfde98e57fca4ffddfe6c775b4993f9c51a4fd063cfb460f70b638b675f013，非首Menu前置。

Tools204已真完整PASS并RAM独核：151XML/1149P/674pins/1467类/六部署；原回执W/logs/build-java-tools-host204-final.json205526B/e564b75335db0da0b45b26195cff418cad9a7fc3cf81303745ac9c36aa2b0705。WJP0/1615.1762793s/active0/峰1436704768，outer0/1703.8846058s。capture无fixture共享修复正式验收，不授SDK/Game。

方法纠偏：Root未尽早跑通启动链，把全迁移验收、重复来源证明和逐阶段发行队列置于首启之前，且实际消费者间缺陷发现太晚。首次Menu只保真实硬依赖；纯配置与长whole解耦、authority数据期限与CPU窗分开，短slot拒即释放。轻metadata32→30GiB按实峰限定，不降重型门。一次coherent输入+原capture snapshot，索引复用后者，不为索引另复制树；MainDev继续增量修。现有原capture及受限消费者不要求builder自身新full资格；局部回归与普通Jar通过即可进入此受限路径，不冒完整VERIFY。

首输入5901文件已真实一次物化；未编译/未被消费的候选随后保前像受控 amendment，未热改旧runtime/SDK。seal03 当前83755903B。capture01在Maven前35.038s真拒：LS/APP源码超旧18/13MiB子界；原件保留。R7仅改两子界至19/14MiB，全局96MiB/6144文件不变；Tools215原整类4P/10.0464462s，216普通Jar0/5.562439s，非新full151。

capture02 已实际执行：2026-10-28T00:51:50Z 启动，01:00:33Z 正常退出1/523.3001529s；失败回执4013794B/00230320cc162005ef265029641fe6a5b7a366797d8faeaa3dfd50ed2f576d25。全部35个 Maven reactor 模块编译/打包 SUCCESS，WJP0/297.2421034s，实际峰1317060608B；本轮按设计不执行 JUnit。失败仅在后置 SourceFile 审计：真实 Java 测试源目录与声明 package 不同，旧审计错误假设两者一致。已采用共享 resolver 两叶修复，实际解析 package，局部 whole9 与原4032 class 只读重审接续；冻结失败图不热改、不改写为成功。最终 coherent 图还需纳入 broker v2 消费者，然后做一次完整验收。

用户已要求“一次 UAC，以后不再进行”。正维护现有受保护 SYSTEM broker，C 盘只存小型运行组件、D 盘存请求与证据；Java/旧 producer 同步 nullable v2，安装后另用普通 token 登记真实新构建路径。当前仍无新安装/新 UAC/管理员成功设置读回。详细边界见 [broker 专题](../ck3-native-ai/project-exe-defender-broker.md)。原1223失败保留，不重放旧请求。

## Main增量的实际范围与剩余失败

190–192累计APP8whole71P、NTKnown9P；196原producer整1/9vectorsP。196超时596.374s，Checkpoint5F、SourcePrep3P1E（新tamperP、旧freshness/deadlineE）、MCP已进入无XML均保留。200正常90=79P1F10E，8whole46P复用；4项缺真实MCP/SDK输入，不冒软件P。

[统一51叶CAS](</D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume63/host_integration/MAIN185-FIFTYONE-LEAF-DEADLINE-CONSUMER-SOURCE-ADOPTED01.json>)34248B/SHA c83279c33d390fb8fec306ccd72a84c1c092a3511c2ab6ded474bc6ddede6dba；187编译0/78.143s、188 Jar0/17.781s；189正常571.549s，Physical1P2F、MCP7P1F。SAVE原生30s守卫到期/bytes0，command120仍有效。

全Maven复用同Dev/BUILD/m2/TMP。capture15双审采用：O63/MAIN196-CAPTURE-PROTOCOL-FIFTEEN-LEAF-SOURCE-ADOPTED01.json10837B/2a508f7b9bb28b3121fe2b0a3952e28fd90a4360fd0701ddc7e39d59cf532d1d。继而ArmyCore13+4TEST统一17叶采用；修3轮javac类型错后204增编0/80.794s、205 Jar0/18.261s，436源/536外部/167 runtime。M0 termination三叶已采用，4whole18待跑。207正常919.766s/24=12P5F7E；208正常81.109s/NT4=2P2F，越过旧pin后遇fixture final≠lastprefix。修测试不延TTL。wire仅error文本，Java身份留DIRECTORY。

## Native ENV、登记与五Holy

Native146冻结，3994包/3984Native保留。Binding17265.5876s/0/Job0：R/compile-binding-qualified172-01/COMPILE-SOURCE-BINDING01.json3080438B/7d6d077745a4bec8699cd0c35a881df6be50a721cbfdd3e316d46e3af0020e11；bound-request172130.6175s/0/Job0，ENV-REQUEST01.json1107297B/7180721173e1c85f275a7bd64be7bb7bc931a77b0ca52fa10f499874f10b1812。

ENV172原4readonly实际PASS，458.711s/Job0；回执2695178B/SHAcf812cd3d6f62dbf7760ae24e97634635f0a843b2dd3f6befa6318ebf4328026。此范围不等于管理员登记或全部设置生效。

旧prereg02失败；04 ShellExecute真实CANCELLED1223：[RESULT04](</D:/ck3-state/ck3-java-g2-resume63-prereg-qualified172-01/RESULT04.json>)8046933B/e59e99dc341f705eec65d0567305cc73e8901b109aea943baaf4c52cebf06266。0Admin/settings、不重放。固定broker根及3files ABSENT。需新built manifest后按原REGISTER核真实登记。

原prereg声明：DECLARED-SOURCE01.json76644B/39d998ee15dae83906085713c6f72580dee48a87964428d6e5ff65501bb50b83；DECLARED-MANIFEST01.json1303799B/7ebd6f4f9265aa04d1242484142e2b281b0a1b0cd405b723412c448db4c1572e，位于独立D:/ck3-state/ck3-java-g2-resume63-prereg-qualified172-01。仅声明，不授Admin。

Holy5 prepare P493.506s：[PREPARE-CLOSE](</D:/ck3-state/ck3-java-g2-resume63-m0-native01/holy-qualified172-01/PREPARE-CLOSE01.json>)2039B/b9fbc53434041bf83b847fc230677945945853eb9b5e9fbf2f41e8da66f0a853。首formal BUILD configure失败/216.507s/Job0，0--build。HostX64/Hostx64字面变化触发cache reset→Cygwin Ninja/cl not found，对象确被清，旧lib/DLL/5EXE保留。共享4叶局34P、192完整1147P；Holy不阻首Menu。

Native147真物化/verify P4927490B/8677374ad91da0573272d73ed32816078c6229fef9e81f141e40b57a819505f0。runtime687CXX j4 P434.278s/峰2.05GB；Bridge359CXX j2/16G命令P490.132s/峰8.90GB，外层错误unchanged断言RED保，不重编。新Binding/ENVrequest P；Inventory172 P398.022s/Job0。ENV147首lease owner错拒55.1499s/0cmd；修后实际P552.3660644s/Job0，actual2695410B/c8d4fa22b9dbc87a5875f9f9d070883dfd6f01b19baeca340a585080ed7d362c。formal BUILD实际P994.7675298s/Job0，仅3CXX+6links，actual3204011B/8b03110d2420ce22b7e776931402bb304b39b90196e764cef9bf06647f2a3343。

新built REGISTER请求01实际600s timeout/输出ABSENT/0UAC；02实际0/633.8582197s/Job0，请求1108504B/fd00274283a8ff00778a4a75170d1d276da6d59f220caa21067d73960e5ae48b。新UAC首计划195916B/b852cbc16d031083e761f2f470e879acb58e66c82b8a746e5240349dffceccdf只读review因无写入的Z卷容量字段拒。D-only后继Plan02为195916B/373c5a45bdb0652ef1000dc514b63009f5aae3766d0d1e1f60fceb514e9e8272，review真P531.90215s；Root实际读8054925B/b801d52c488da75f91a672d3fa62a9d2319b4e8562b31b036e9c6cd7e8c663c5并独立核同一runas argv后批准。execute实际688.460091s/Job0，RESULT02为9358358B/5790d5e42a6c60ff165aafed96723aae0fe6cf929ba44c98222a81028005df20：CANCELLED/Win32 1223/ACKfalse，0admin子进程、0设置读回、无REGISTER actual。不认定用户手动取消；有限后台诊断当前session1/WinSta0可见/Default桌面，不能证明过去提示可见。已异步询问用户交互桌面新UAC可否处理，未重试，旧CANCELLED04也不重放。

## SDK授权、REA知识与后继

DataReview03已由Root真写2081B/SHA前缀f00a926…；原写窗28日04Z、data06Z，不扩其scope。完整SDK31000秒、Fresh4、Canonical30、SERVICE仍未完成；七态actualManaged provider/SERVICE循环正在最小原入口修复研究，不能声称Fresh4会自动解决。授权、准备和实际覆盖分列。

[代码/数据与接收者](../rea-ck3-research/resume63-code-data-and-receiver-results.md)、[四项原生边界](../rea-ck3-research/resume63-four-native-boundaries.md)与[候选、条件、receiver及bank来源](../rea-ck3-research/resume63-candidate-condition-slot-bank-results.md)已随9eb交付。末页8182B/SHAacd3c9a0df8e72a51f38b6a0f94c83079d25ec6e9816231348b8925c0172766c保六case及同行边界、实际provider峰1、source-derived I/O。没有新正向query；signed-fullID独立后继只在RAM审，不热改冻结Native146。M4 finalquote仍缺同帧source，23B标签候选已撤回，不授退款报价或动作资格。

9eb官方CI两fixture request=null前置RED/reactor NOT_RUN。两验证6配置资产原CREATE/readback P，原875288漏目录实际分配，修正957208<1MiB，保原错误记录。两个FORMAL各87文件真P；PROFILE三phase均原Java0/全部输出读回MATCH。menu ENV112265B/b6c7eaf184268820c99f5043476477e661630eab0d3aaa5a7194a3473df95dc4，entry112484B/c9dd6336b0129ba27ff34b31472dfe7e68f4007bd0bcaad6838c237af67f2f0c。InitialPolicy/v4后继准备中；Root核实ALL_ORDINARY指完整普通能力/非fixture，实际XAR_ON按旧Python既有one-life显式绑定ROGUE，不称普通继承。NativePlan生产者拒ordinary附加输入、Frozen消费者却要求v4请求在该闭包，真实矛盾已核；正修共享生产入口，不移除消费者守卫。

209 NT整4P；210 M0整18实际2P11F5E，未来测试修复仍RAM，不将RED改写。212正式发布整13实际1P12E，缺Git/root配置及小数fixture已局修；214实际正常RED/529.180s，整13为12P1E，唯一E是旧反射签名漏首参、尚未进该case Guard。生产者整4和Guard另8真P；后继TEST强类型直调修复待编验。两个PROFILE已实际退出后才启动214。两genesis/Robert seq0未动。M3 35Java+5CPP小gzip候选未采。每次启动须fresh后台Steam；实际Java启动/日/SAVE/RESTORE仍0。

NativePlan附加v4必要两叶已采用，Main215真实增编0/123.169s，32MAIN暂未改，必要Jar/回归接续。候选seal03为5901文件/83755903B，完整139910424B；census621232B/5cf4f00e74a5d3f3aee76279724d1baa9b761553c310584422f46ed721fa5ae3。曾误把Native3984清单装入Review.completeRuntimeSources，引出2MiB/数量扩界建议；Root追实际调用者发现Java部署与独立Native inventory是两轴，已撤回整批RAM、0源码采用，不放宽原界。NativePlan原producer必须用首次Main实际captured completeDeployment物理路径，单纯同SHA的Main41路径不能代换。Console标准依赖已真取得，whole3尚未执行。

别名W=D:/codex-ck3-demos/2026-10-22-java-phase1；R=D:/ck3-state/ck3-java-g2-resume63-m0-native01。所有引用以实际原件canonical FileRef为准；未知保持未知。
