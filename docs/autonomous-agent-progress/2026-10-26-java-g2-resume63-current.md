# resume63：REA、Java 全能力迁移与 G2 接续

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-27T09:11Z 更新；任务继续执行。本页接续 [resume62 交接](../handover/2026-10-26-java-g2-resume62-rea-runtime-handoff.md)和[来源索引](../handover/2026-10-26-java-g2-resume62-rea-runtime-handoff-source-index.json)。

目标是使用 REA 完成 G2 M0–M7 原生研究与 Java 落地，完成 Python 能力迁移后使用 Java 继续普通自动游玩。[完整对照](2026-10-26-resume63-migration-and-g2-matrix.md)分别记录八项业务门槛及全迁移范围。当前 Java CK3 启动、新增游戏日、SAVE、RESTORE均为0，完整实机 G2仍0/8。

2026-10-26T14:35–22:00Z的完整历史、失败和当时有限卡保存在已交付的 `fff86e9c2aebb1eb00d1151875e1266cbc5a4b24` 文档快照；后继文档交付 `534375b1bda095ff92846dbfbb866a30e4c0e117` 保留远端同事增量。本页压缩已归档段，不删除对应原件或把旧失败回填成通过。

继续复用独立 SRC/BUILD/m2/TMP。Host唯一写Maven输出与Tools源，各领域按短窗交接；已知错误先局部增量，必要修复闭合后最终完整验收。Native普通runtime/Bridge采用新卡-j2/16GiB，保留旧8GiB失败；REA最多四个独立provider按READY与实际内存调度，不重复取证。Genesis保持seq0，禁止重建。Steam只后台核离线，启动前另取新鲜准入；不接管身份未核旧CK3，不启旧蓝色决策窗。

任务总线 ck3-java-g2-rea-resume63-20261026；Root状态9108/resources空（实际08:58:52Z）。全部大输出使用获准D根。Git由Delivery普通FF保同事远端；Root HEAD/index与既有dirty不整体stage/reset。

此前04:30–06:00北京时间首实机乐观窗口已撤回，当前没有可靠替代时间。31000秒为完整SDK覆盖预算，不是预计等待时间。后继门槛为：必要迁移局测与真实Tools资格→Own和Native正式产物/原生corpus/精确EXE登记→完整SERVICE和Fresh4、Canonical30→当前权威与后台Steam准入→Java罗贝尔1066首批→真实SAVE/RESTORE。首场SAVE必须由普通动作产生，不可预造为启动循环前置。

## 2026-10-27T09:11Z 实际进展

本页此前全文19901B/SHA66640f022e029a6d9fd0d95abedd80413e9a1008e5c81572af58b5142deeb51a已逐字节核保存在提交3a2b06bfb7a4ef1e2a41c11a7dcfe8974b038bb5。本次压缩已交付历史，不删除原件，不改失败。下文为同machine_id后继。

Tools172完整VERIFY已独核：151 XML、1142/1142P、674 pins、1466类正文及完整六部署一致；WJP exit0/1557.0979s/active0/峰1381801984B，Controller0/1631.5958s。[独核](</D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04/acceptance63-tools172/TOOLS172-INDEPENDENT-FULL-VERIFY01.json>)22658B/SHA40ad2f17615eebd38b75317e61521e024117644d9349b5faf04839a85c66ef74。实际生产回执W/logs/build-java-tools-host172-final.json205527B/SHA5012360b919fe61a077e484216365178fe18a5ecddf1561c46905e9fb30c2610；六部署位于W/build/java-tools-host172-final/ck3-control-build-tools。

Own172原41→Own46编译/运行→2JUnit全PASS，四ChildJob active0；实际42角色、7 relocation、135同归档类。Own Java34.5194s，JUnit Java11.8097s。[actual](</D:/ck3-state/ck3-java-g2-resume63-own-successor03/artifacts/tools-postqualification/actual.json>)29625B/SHAbea6adaa84c4500ae9318e78f9fa130c2ce66501716e5017257841e60b8e57ab；SDK card消费此件，standing须消费其full_own_actual_ref26131B/47604360…，不能用机械binding替31000秒软件scope。旧155缺42-role失败不追改，Root仅亲读原件，不冒独立全部复核。

Main169增量编译0/121.913s，32reactor实际6main+6test模块重编；170六Jar0/19.219s/0javac/0JUnit，是当时cut。171建设5P、Physical1P2E，合8=6P2E；173 APP同名Life20P，LS26超时无完整XML，不授其结果。样本线程在原测试全树身份扫描，方法完成数未知；未找到可证等价的小缓存方案，不放身份或UNKNOWN守卫。

171三叶后继已采用：Physical从真实HELLO读connection，文件身份异常增加具体path/NIO/native双观测，既有IdentityTest同步；原比较/拒绝顺序未变，净1047B/0页。174真实6whole65/65P，exit0/30.280s，0Jar，含通知40+规划15+Identity7/LongPath3。175 APP三whole15=14P1E，Holy4/M7Kernel6P；Army缺war_termination_exit_terms数组，NT三whole20因前置失败未运行。该夹具57B已soleCAS STOP，未授复验通过。176仅Physical整类3已09:09:12Z启动，不重建设/Identity；后续原LS15及NT仍须实际完成。

当前局部源保护343、外部输入536，不是FinalMain全图；两新增诊断contracts叶本在旧base内，345猜数已撤回。Launcher唯一Main BUILD/TMP executor，Host唯一源码CAS；完整Tools独立TMP，Native及REA可并行。

Native Source146不重物化，3994包/3984Native保持。新Binding172实际65.5876s/exit0/Job0，原件R/compile-binding-qualified172-01/COMPILE-SOURCE-BINDING01.json3080438B/SHA7d6d077745a4bec8699cd0c35a881df6be50a721cbfdd3e316d46e3af0020e11；继续原bound request，成功后正式ENV与Root原prereg分scratch并行。精确EXE管理员登记/实际三数组读回、正式Bridge及五Holy BUILD/run/corpus仍未完成。

REA此前[代码/数据与接收者](../rea-ck3-research/resume63-code-data-and-receiver-results.md)、[四项原生边界](../rea-ck3-research/resume63-four-native-boundaries.md)均已交付。本轮M1 919+376B、M2 1070B、M5虚槽8+目标49B、M6前缀140+held87B均采样/独审闭场：M1返回仍经opaque28F3470；M2诊断mode不是hidden/disabled；M5无direct注册不排除transitive；M6返回来源闭到全局槽5C67538一次快照，loaded bank/身份未授。新单页聚合正在落地；实际owned provider峰1，未报四后端并发或提速/模型token信用。

最新两文档已FF交付3a2b06bf并保9ba同事更新，Root HEAD/index不改。47431官方CI实际因缺同runner fixture-production输入失败，两轮636P不等于全图通过；不扩hosted平台、不把此缺口加为本机首Game前提。当前Java启动、游戏日、SAVE、RESTORE仍0，G2实机0/8。余下主线为必要Main whole与完整SERVICE、Native正式产物/corpus、实际FinalMain/SDK全部命令及独立continuation，随后原Java普通罗贝尔1066首批和真实SAVE/RESTORE；没有可靠首实机时点。

## 09:26Z 后继实际

176 Physical三项实际仍1P2E、exit1/208.935s，非timeout；已越过旧HELLO/metadata断点，严格心跳守卫拒绝。共享测试夹具只持续发snapshot、不更新初次heartbeat是真实原因。两test叶已soleCAS STOP，净791B/0页：经原transport发新heartbeat+原snapshot，原测试验真实packet更新，不延TTL/假clock/改UNKNOWN；复验仍未完成。175缺必填空数组57B亦已采用，尚未授Army/NT通过。

Native bound-request172实际130.6175s/exit0/Job0，ENV-REQUEST01.json1107297B/SHA7180721173e1c85f275a7bd64be7bb7bc931a77b0ca52fa10f499874f10b1812。正式ENV原4readonly已真实启动，work09:40:51Z；2MiB单独输入分区内Root已wx/fsync生成DECLARED-SOURCE01.json76644B/39d998ee15dae83906085713c6f72580dee48a87964428d6e5ff65501bb50b83与DECLARED-MANIFEST01.json1303799B/7ebd6f4f9265aa04d1242484142e2b281b0a1b0cd405b723412c448db4c1572e，独立D:/ck3-state/ck3-java-g2-resume63-prereg-qualified172-01。仅声明配置，非Java writer或管理员设置证据；原review/UAC准备并行，不等ENV。

新[候选、条件、receiver与bank来源](../rea-ck3-research/resume63-candidate-condition-slot-bank-results.md)已读审：8182B/SHAacd3c9a0df8e72a51f38b6a0f94c83079d25ec6e9816231348b8925c0172766c。sources及REA README已CAS，同行RAM/文件边界、实际provider峰1与source-derived I/O均明确。

别名W=D:/codex-ck3-demos/2026-10-22-java-phase1；R=D:/ck3-state/ck3-java-g2-resume63-m0-native01。所有引用仍以实际原件canonical FileRef为准。
