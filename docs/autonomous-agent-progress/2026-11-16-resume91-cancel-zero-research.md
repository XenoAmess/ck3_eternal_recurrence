# 2026-11-16 resume91：接手与 CANCEL 零写恢复研究

用户在阅读11月16日三份交接之后明确要求继续 CK3 智能体研究。本轮从正式 `bcba49ada67c028fc0747c1a9b2065d627568b31` 接手；其生产源码基线为 `04a226422b60c4f3e2604af538c9cf1da7101b40`。休假停止条件已由这次续行指令解除。旧交接仍记录当时事实。

## 真实问题与最小修复

E18 原件中，ARM80 已在 sequence1996 独立确认；CANCEL 子动作在 sequence2000 为 `REJECTED_BEFORE_DISPATCH / BEFORE_WRITE / request_bytes_written=0`，没有 ACK。提交时间 `2026-11-15T16:16:56.258008100Z` 晚于其原期限 `16:16:38.437412300Z`。父动作在2001仍为 `COMPOSITE_UNKNOWN`。拒绝文本同时涉及私令牌与期限，但原件只足以独立证明期限失败，不证明令牌身份改变。

正式消费者此前只允许 pause/resume/ARM 的零写结果，无法把严格零写 CANCEL 作为“仍 armed、可另发新取消”的历史尾部处理。修复必须贯通归档回放、Life 取消证明、组合动作、Root 工厂与冷恢复消费者；并减少同一次检查中的重复全历史遍历，使新令牌在实际提交时仍有效。

不改变旧子动作 ID、body、期限或终态，不重放 ARM 或被拒绝的 CANCEL。新取消必须重新取得同代 Status 与暂停同日期帧，取得新的有限令牌和下一 ordinal；最终仍需正 ACK、子独立 IDLE 与父独立 Status/后继帧。旧成功、EVENT 和 sole-ARM 分支继续保留。

原始证据入口：[11月16日源码与证据索引](../handover/2026-11-16-java-g2-resume91-vacation-handoff-source-index.json)中的 `e18_failed_end`、`e18_cancel_trace`、`cancel_wip_freeze`。WIP 当时只有3个局部 RAM 组件，无完整9叶实现或编测资格，不能将其当成已交付修复。

## 本轮分工与当前边界

按 AGENTS 的既有要求并行：Runtime 独占现场与账本，只读核实真实 frontier；Java 负责连贯最小源码及回归；Native 复用现有受管入口和已绿依赖，准备增量首编与受影响验证；Root 汇总进度。冻结 `D:/r64d`、原 Z 工作树和现场 `source307/build307` 不由源码工作覆盖。

Runtime 于 `2026-11-15T17:58:02Z` 核实：旧 Game145132 出生时间匹配，但已经 exit0；56732 已被不同出生时间的进程复用，不能作为旧 keeper 认领。全机 `ck3.exe=0`，Quarkus156476、Maven62484、outer153160、observer161796仍活。continuity 保持原字节100052B / `58c1e2992c5ccfa69ce3b51d4309179da1abd4a135c2090b57fcb59b1f31cbdb`，head2001 / repair_required / 父UNKNOWN；没有当前世界帧。未执行 GET、游戏查询/动作、启动、进程终止、采用或账本写入。

机器 `xenoamess-full-tower-eb9d2c1186` 已用当前 Windows 身份和现有稳定ID算法独立核实，未从旧委托记录追认。核实原件：`D:/ck3-state/resume91-runtime/research-resume-20261116-readonly01/RUNTIME-FRONTIER01.json`，23935B / `c379a06a2cdc081ef54baa5cea6c8e77c7dbaf4ab3152a4a40516273d6897979`；补正与恢复分析 `RECOVERY-ANALYSIS01.json`，5553B / `f39fad4b7a6875460fb292fd69d3c278fc153966e732bc1bd3a7245360b2c55d`。PID/出生时间以 Win32 读回为准；WMIC 原始输出保留，含逗号命令行的 CSV 行存在列错位，不作为精确字段绑定。

旧 `source307/build307` 已经由最终路径与卷GUID核实为真实 C 盘目录，并非 D 盘联接。本轮新增源码和编测留在 D 盘，不在活跃旧宿主目录累积输出。旧 Game 已退出后，实际恢复须先验证已有 checkpoint pair 与跨进程恢复协议，不能再向旧 Game 发 CANCEL80 或执行 E18 wrapper。CANCEL 修复仍是已发生功能故障的离线修复，不授予当前实机取消或 LOOP。

Native 已核本机默认 Maven 3.10.0/JDK21，复用既有受管 JUnit/编译入口和历史正式 classpath。14个生产TU首次编译 exit0 / contract_accepted=true，用时41.571123秒，产144class/2510435B；逐class来源及Java21检查通过，受管资源正常释放。现成依赖未重编，未运行repo全图Maven。

首版Test1编译成功后，首次whole36得到真实29P7F，用时77.930581秒。新5在测试构造时调用通用子命令生产者，试图延长旧父期限，被原guard正确拒绝，尚未进入新功能；改为来源签发CANCEL的实际构造，原期限guard保留。另旧2个watch用例的夹具只在find返回父动作、snapshot却遗漏父动作，影响冻结快照中的未决元数据保存；仅修测试快照，生产watch逻辑和断言保留。用原正式Life类作有界旧2对照时，旧classpath缺新Test引用的接口，JUnit发现阶段exit2/0tests，没有行为结论；不把它当“旧2原本失败”的证明，也不再扩展此对照。失败原件在 `D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/cz96j1`、`cz96b1` 保留。后继只编修正版Test，不重复编未变化的14生产TU。

新5回归涵盖零写尾部仍armed/不重放、新ordinal、重复尾部/错gen拒绝、Replay缺安装authority拒绝/回调路由，以及生产Composite的token→ordinal3→子独立Status→父另一次physicalStatus的完整软件闭环。Root Core私有DATA/adopt和实际derived注册路径本轮仅编译，尚无执行集成或实机恢复资格；不能把应用层fixture的注入回调当实际Root安装。

修正版Test1仅增量编译1TU/11class，用时9.330422秒；14生产TU原样复用。最终一次whole36为 **36P/0F/0E/0skip**，用时73.084241秒，包括完整 `LifeAdvanceLifecycleTest` 的29个方法（含新5）和原fresh-batch/ARM7个回归。受管CLOSE为result0 / terminal_observed=true，资源已释放。最终JUnit原件位于同一Native根下 `cz96j2/reports/TEST-junit-jupiter.xml`；配置、实际执行、产物和资源记录与它同工作包保全。

本次14生产源码与Test已经形成可审阅的软件修复包。它不等于当前Root安装、实际采用、已退出Game恢复或性能目标达到。软件闭档为 `cz96c1/SOFTWARE-CLOSED14-TEST1-WHOLE36-01.json`，18759B / `b2c62207be6e6541ada7ad9c2cb98e2f7f75c68fdf4b8d3fba847efb951c9914`；最终XML为68313B / `925507d6646eea3a172b66ecf05d88cc8ae6b0094c675e960cb99b4089bdfd16`。

源码已按15个Java文件单独提交并普通fast-forward推送至master：`fdce37aa628477c399b55898eed7fc154a032410`，parent为接手基线bcba49ada6，远端exact SHA已读回。没有更改历史拒绝或现场源码。首次查询时该SHA的 [Official Runner CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/43745893492) 与Linear history仍在运行，不标CI已绿；本地验收也不是repo全图Maven。AGENTS与本轮研究/日周报告在后继docs提交发表，不把docs提交当生产采用。

Native资源闭账：同根 `cz96c1/RESOURCE-CLOSED14-TEST1-WHOLE36-ONLYUNUSED-ONCE01.json`，6588B / `e16693390198cf94fb937f4d5374ae7414f0be554c88b15a570d1d53eca2f3f7`。本轮新fund16777216B，一次退还unused5734844B；raw987624460B、normal24389632B、cap1719664640B。保留11042372B中包含源码与Git上界，不能全部称新增实际对象；旧unused没有重复退还。Root文档新增Git在此scope之外。全部受管资源释放，Native JVM为0，不等于旧长期Quarkus/Maven已退出。源码SHA的Linear history后续已通过，官方Runner CI仍运行；本轮docs首次发表为 `38f447b3af353bdf29bf7a4ae8d4351382212567`。

## 已退出 Game 的下一施工入口

现有生产链为 `RootApplicationSession.restoreCheckpointPublic → RootPublicRestoreRuntime → RestoreCheckpointService → GameRestoreAdapter → JavaGameLifecycle.replaceSavedOnce → DriverBootstrap`。当前阻点已从源码明确定位：capture要求旧Game的新physical snapshot，createAttempt验证原managed Game仍有效，adapter固定 `requireRunning=true`。只把该布尔改为false无法解决前两项。即便装载原保存，Driver仍保留未结算行并进入 `READ_ONLY_UNRESOLVED`，不会自动清除父UNKNOWN。

后继应复用原 savedPair、lineage和episode的生产恢复链，为有真实退出证据的旧generation提供独立capture与替换后READ/Driver采用；旧UNKNOWN必须另有正规来源结果或operator retirement，不能靠加载存档绕过。原savedPair的date_raw53176992、save/driver路径仅从当前canonical head引用，本轮未重读87MB save或4MB Driver，不称已重新验证检查点内容。

## 研究结论的等级

本轮首先解决有真实失败依据的恢复消费者缺口；未声明新增游戏能力、LOOP、游戏日或 SAVE。G2 沿用最后完整6/8，10秒/新增确认保存日目标仍未达。零新增确认保存日不计算有限秒/日。旧年度保存政策继续沿用。

## 持续执行：退出现场的同检查点恢复（进行中）

用户指出单包发表后仍应继续演进，Root纠正了按单包交付停止的判断。用户随后明确“本地模型暂不可用，你来代替它完成全部任务”，当前执行者与现有分工接管实现、审阅、诊断及真实运行决策，不等待本地模型、不再发本地模型HTTP，也不把一个commit或软件通过作为停止条件。

原savedPair的save、Driver与ACK已核bytes/SHA及文件身份；Supervisor原terminal证明 `GAME_EXITED/NATURAL_EXIT/exit0/Job active0/cleanup_proven=true`。原worker只有ATTACHED连接，OWNED属于已退出Supervisor，不能沿旧PID颁发STOP权。原件在 `D:/ck3-state/resume91-runtime/research-resume-20261116-readonly02/` 的 `SAVEDPAIR-AND-EXITED-GAME01.json` 与 `EXIT-SOURCE-OPERATOR-INPUTS01.json`。

一次性初始化D盘actual开发图已完成：`D:/ck3-state/resume91-runtime/exited-restore-dev01`，source3201文件/46034039B，可复用build16859文件/111506942B，正文SHA及mtime一致，旧C源未改。报告 `ACTUAL-BASELINE-COPY01.json`，1353B/SHA `e73a285242ce4b8ed6fb1b4649392923bef6245ca41d962080089d775a959c42`。后继按叶增量，保留actual Life诊断、Core与postResume差异，未以formal整树覆盖。

`retire-exited`在Native attach之前，以真实退出私有角色进入原Core/原writer，追加v2行政隔离。第一次实际调用失败604.620秒，定位每次归档访问都重复Win32全机扫描；只把同锁成员资格检查与完整来源/进程检查分开，完整检查仍在准入、pre-append及结束。第二次失败92.792秒，原因是输入误用包含末尾LF的原文件SHA充当canonical Head.digest；保留两次失败原件、原请求和期限，均零追加。canonical head摘要核为 `bb6af7530c1d9c7f71281a6500e9b1e7594bc511d258728d515b84935c84a1ed`。

第三次独立新请求于 `2026-11-15T19:54:44.233430Z` 真实exit0，用时126.1786959秒，结果 `EXITED_LIFE_INTERRUPTION_RETIRED`。同writer追加sequence2002，effect仍为UNKNOWN；新head原文件100052B/SHA `d8b37715a6917d06b165dfd63353d0d8c26403fd7f2e6a02dc2a4f9f040a2e03`。原父、两个child、执行原件和UNKNOWN_EFFECT均保留，旧ID仍禁重发。未启动/attach Game，没有新增游戏日、SAVE或模型HTTP。原件 `runs/retire-exited03/ACTUAL-OUTCOME-WAL03.json`，7052B/SHA `0638d0f790130ca8d71889e833fb9e3c6ada6144f4aaa001a9447fbb3d71f64e`，相对上述actual开发根。

软件资格分开记账：实际opaque退出角色4项和旧writer/consumer2项已通过。早期Core夹具使用无效CAS输入，被旧Native归档guard拒绝；为此产生的05生产绕过已完全撤回，未被实际采用。Core负向回归保留该guard；真实正向资格来自上述第三次行政调用，不能将夹具或未采用候选当作正向证据。

完整 `restore-exited`复用原savedPair、lineage、episode、writer和Core恢复链，要求新Game两次独立READ、原Driver采用及真实OWNED生命周期。actual完整增量14源首编仅两个package-private SHA调用失败；只修该叶，并复用首轮成功的7源65class，再编剩余7源。最终actual完整族已安装，累计32源260class逐件核pin。完整Materials14与ENV Producer20回归为 **34P/0F/0E/0skip**，21.207秒；XML为Native根 `er97coldj1/reports/TEST-junit-jupiter.xml`，71205B/SHA `3dbf47ac45c2c3b8cfe69c96e604c6bd547aa0fdaa5e54a8b9c8f34d5dd35cc5`。

决策通道显式配置为file provider、`codex-session`、单次120秒、零backoff；保留原完整payload、原proposal/body/frame和期限guard，无HTTP fallback。请求metadata引用原完整payload，不截断为16KiB。实际3源8class已安装；File4、Config3及旧Pending2为 **9P/0F/0E/0skip**，10.810秒。软件闭档 `df98c1/SOFTWARE-CLOSED-ACTUAL-FILE3-TEST3-9PASS-01.json`，5122B/SHA `c412da02d8f3750bb5f42b5fd934a4574fcf86ef30736b2619d2fe8a4606b1d2`。专属执行者接待真实queue，当前0实际请求/0决策，不把测试决策计为实机。

当前后继阻点是正式Saved ENV生产工具的真实completion：旧工具财务schema只接受历史issuer和口径，不能伪造旧授权。正实现最小版本化ROOT_STANDALONE_V1分支，以本轮Root、attempt和真实fund核准；卷free继续覆盖峰值、其他未消费holds、system及safety，项目quota仅计保守占用上界、项目新增和其他真实项目holds，系统预留不冒充项目写入。独立64MiB scope不扩张；quota例外截至 `2026-11-15T21:25:40Z` 复核，max_project13303228397187B，依据最新全卷used上界13302571618304B、本次67108864B、当时other52799107B和512MiB仅供全卷baseline观测漂移的quota余量；余量不是项目新写入或新资金。Native逐scope剩余上界28409475B，Runtime normal24389632B无法立即分解时全部保守计入；后到finance4未消费余额另按真实数更新。此前小额度在全卷used漂移106541056B时真实拒绝，保留失败，不把unknown项目库存写成0。实际ControlBuild单源首编已GREEN，11.587秒/62class，产物即时交Runtime，不等Test或Git；来源 `finance101c1/ACTUAL-CONTROLBUILD1-COMPLETE-FAMILY09.json`，26736B/SHA `0b151778bfc27933f934b0ce6cac48c306940de54120e42156e381dbff6697e4`。新财务分支四项回归已 **4P/0F/0E/0skip**，14.053秒，XML `finance101j1/reports/TEST-junit-jupiter.xml`，50198B/SHA `dd98093a5dea49b690433f813393b314a27263217db59a1936d7870299260c3e`；首轮helper编译因文件末未使用的RegressionMain缺两个无关Test而RED，保留已生成class后只补必要helper，未扩旧金融测试全图。正式ControlBuild单源另取得typing资格，12.107秒/62class，未重跑4项。新财务生产源与Test两文件独立commit为 `80e146826f9d2ff7e8db925358f220d0d3a8900b`，parent为ea642b75，本轮报告随其后正常发表。4P是软件夹具验证，尚不是本轮工具真实receipt。Runtime已物理采用actual33源累计322class并全pins核对，bootstrap regular6jar已产出（主jar3650299B/SHA `f76a9df3d11d5e6ea856524818234126b330051d303d8417ec6ece0233c910ed`），5个旧D依赖同FileID只读硬链接复用、零依赖body复制。最后financial02以other64MiB明确保守上界绑定原期限，尚不预报真实ControlBuild结果。工具真实completion后生产新ENV，再取新SCREEN exact CAS并执行同pair恢复。

正式源typing与actual源编测分别保留。正式恢复17源及4项必要支持依赖typing已GREEN，正式Selector单源另取得typing资格；正式Materials whole14加Core占位CAS guard负例1终验 **15P/0F/0E/0skip**，28.315秒，XML `er97formalj15/reports/TEST-junit-jupiter.xml`，58528B/SHA `5f2e63fb4744aab36fd842ea4ed1dd6ab69af8921066d5d7885fd73a52119878`。不将actual通过外推formal全图或正式File行为9P。正式恢复与file provider共20生产源/6个Test已按26文件独立提交并普通FF推送 `ea642b750fab97254813238a93bea7ec82ca367f`，parent为a2ba2ade14，远端exact核实；首次误推不存在的main分支被Git拒绝，未改remote ref，随后正确推master成功。Linear history已通过，[Official Runner CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/43759986575)仍运行。Native只补必要依赖、复用未变化class，旧CANCEL36和退出角色已绿项不重跑。

官方CI最新6cc5dd7e6b的运行43747045789在reactor前下载Maven失败；旧过时运行已取消，未声称CI通过。已查官方固定Maven3.10.0下载会转向Apache archive，原SHA512一致；Root已修CiBootstrap的重定向处理，本地真实302→200回归1P，断言原body精确字节与两路各一次HTTP；生产校验和、大小与超时限制保持，该JUnit不声称覆盖SHA512。CI2已独立提交并正常FF推送 `a2ba2ade141697e9f8ca9cb680f4ec986a6718b2`，远端exact核实；新的 [Official Runner CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/43758282621)仍运行，不阻塞Runtime继续新ENV/恢复。

截至本段记录，尚未启动新Game，也没有新增确认保存日；G2仍沿用最后完整6/8，不计算有限秒/保存日。软件、正式发表、实际安装、实际运行与SAVE分别报告。后继继续实际恢复和真实Root循环，不在行政成功或软件闭档时停止。

## 工具真实构建、完成发布与读取修复（继续执行）

正式ControlBuild于20:52:25Z真实BEGIN，唯一attempt `resume91-tools-env01-20261116`，default Maven3.10.0/JDK21.0.10。仅本包135个main Java源真实构建，Maven自身23.522秒；受管cmd阶段25.9837926秒、exit0、Job active0、peakJob653148160B。该standalone baseline没有Test源码，原日志No tests to run如实保留；已有34/9/财务4软件结果分账，不冒全图测试。ControlBuild全阶段61.4542449999135秒exit1，因最终发布预留拒绝，未宣qualifying receipt。

精确原因：logs scope当前Native2454696B加固定2MiB receipt worst bound为4551848B，大于logs cap4194304B；whole当前Native28711184B小于58720256B。本次不缺全局64MiB。只读probe首编因package-private IoGuard访问失败，改为同接口ClassLoader的反射Proxy取得原生产计量，未将诊断false角色当completion许可。原ended-JVM历史filesystem peak未持久化，保留UNKNOWN/null，不能把新进程当前census冒原全程实测。

最小修复在原ControlBuild增加原成功Maven的完成发布与精确逐文件allocation计算，最终body上限保留；新typed来源强制区分CURRENT_COMPLETION_PHASE_ONLY和历史UNKNOWN，绑定原RED、原lease、原source/snapshot/6target及真实producer closure。原RED磁盘pretty为84959B（不同于compact stdout76142B），未改写。原135输入、snapshot和6target均冻结；外置增量63class/12.405秒GREEN，新3项软件回归3P/0F/0E/0skip，10.669秒，仅smoke数学/allocator/source边界，不冒真实reader通过。

第一次真实completion-only调用5.4367秒exit1，已CREATE正常完成凭据、会计与mandatory source三个文件，写后自验JSON object required。源头已实证为合法卷键D:/与Java规范根D:\的字符串错位；匹配release原entry key即可，不能改旧输入追认。另历史读取不能要求新reader与旧producer closure相同，改为核recorded producer完整冻结closure。最终reader2单叶63class/12.057秒GREEN，旧中间formal d306仅typing、已封未采用。

21:29:42.919088Z→21:29:44.290853Z，正式公开 `ControlBuild.main --verify-completion-source` 真实exit0/stderr0，消费原source与正常完成凭据；没有重CREATE或重Maven。证据 `D:/ck3-state/resume91-runtime/exited-restore-dev01/runs/tools-env-completion01/READER2-VERIFY-ACTUAL01.json`；原completion source8003B/SHA `6ded2cf22a4c8aeafbc7cc514f7d5769a8563c6bab76e9420cf0b599538c517e`，normal PASS85097B/SHA `c2aeff8b0f956807c39325fcf820c8e9e7ca541085d563cb9068635401974abc`。实际reader jar183597B/SHA `7322e89d8e265f4b7461a57b01edc954ee2e9b9fe26e39b33d41912526c3f120`，旧21:25:40lease按原21:16完成时刻验证，未刷新。

后继ENV还有真实CodeSource/closure约束：旧target6自带同reader缺陷，单换classpath不能冒称旧6读取成功。限定三family的read-repair composition v1正在施工：原Maven6、mandatory source、当前独立Root授权、新reader/producer/manifest三个源码与受管编译family、同CodeSource patchJar和六份原件来源copy，组成显式runtime7；新requestv3/ENVv5仅此分支可用，旧6与旧wire保持。编译证据列表复用已绿reader2，只编新Producer/Manifest2叶；直接cold消费者已核通过动态Manifest方法，无额外Root源码或内联旧ENVv4/runtime6硬值，不扩全loaded-class审计。

原lease及已产历史输出不改。当前read-repair准备/增量安装/校验另获Root有限授权21:25:09Z→22:25:09Z，限各既有scope累计cap，quota上界仍13303228397187B，当前新scope由Native按实际峰值独立fund，旧unused不重复退。新的SCREEN clean稀疏checkout已准备HEAD02e63089/dirty0，实际CLI source与installed SHA一致，尚未领取lease或启动Game。

CI最新实证补正：a2ba的Official run43758282621在step46仍于下载前失败，新错误明确HTTP404，固定ZIP在downloads站已移除。Root查官方archive目录与sha512同原pin，实际ZIP HEAD200/10102082B；只将CiBootstrap固定下载地址改为archive，版本3.10.0与校验和不变，单叶typing待首个非P0空档。旧302测试通过不证明该ZIP地址可用；最新完整Official CI尚未通过。中间ea642b运行已取消，保留02e当前完整运行与实际失败记录。

本段截止仍无新Game、新游戏日、新SAVE或真实模型决策，仍持续ENV→SCREEN→同pair恢复，不以工具读取成功或源码发表停止。

## 实际 ENVv5 已产出，继续同战役恢复

composition Producer/Manifest两叶真实10.953秒/44class GREEN，复用reader63；唯一定义source_ready为aggregate FileRef、compilations为列表。公共首调用在输入有效期34分钟被原30分钟上限拒绝；新独立请求改为有限窗口，旧请求保留。第二次到Rootauth精确比较时暴露Jackson LongNode/IntNode同wire整数差异，严格wire roundtrip修复，不放宽浮点/布尔。又为新Producer复用旧phase的Manifest33、丢弃旧Producer11，明确最终三family逐class来自对应source row，旧未采用Producer原件保留。只重编Producer1，67398B/SHA前缀edd2319f，11class/10.315秒GREEN；不重Manifest/reader/135。最终三family共107class，patchJar真实292294B。

另有真实公共metadata发行链旧issuer门：只在现有Contract/Guard/Command三localservice叶增当前Root capacity5/binding5，保留原declaration4/census4与旧v4角色。issuer为 `/root/ck3-resume91-root-20261116-research`，declaration owner仍真实/root，Runtime受Root委托执行；只限PROFILE_ENVIRONMENT、INITIAL_POLICY、ORIGINAL_DRIVER_RUN_PROFILE三个必要小metadata roles。首编Guard局部变量重名真实RED11.234秒，保留Contract17，仅修变量名后补Guard+Command25/11.881秒GREEN，三叶42class完整。没有借用budget_fast_lane身份，Native allocator仅作为真实fund来源。实际cold走ordinary容量guard，不读另一旧strict runtimeissuer合同，未另建runtime协议。

预算按物理计量补正：旧mirror曾按逻辑大小估算并退unused，不能称Native物理闭合。GetFileStandardInfo/FileID去重的当前实际allocation227168000B，较旧retained171966066B多55201934B；独立56MiB=58720256B修正，余3518322B只后继小尾，旧低估/UNKNOWN历史peak保留、旧unused不重退。另独立256MiB=268435456B用于同pair恢复与首有限OODA，替换320MiB提议；两READ cap128MiB/provider64MiB/driver和日志余64MiB，firstSAVE按实际已写与峰值另核，不降年度保存政策。两项fund后raw1623553224B/normal24389632B/cap1719664640B；后到issuer/Producer必要4MiB使raw1627747528B，仍留67527480B。卷used漂移原因UNKNOWN，当前quota13305050079232B仅有限范围与观测余量，review仍22:25:09Z，实际各scope不扩。

**22:06:38Z真实PUBLIC_ENV03 exit0**：三公共发行调用declare→census→Rootallocation（真实256fund）→binding5全部exit0，原Main消费binding后真正CREATE并readback。ENVv5为35866B/SHA `87972e61238c709bc48d3b50bd6cf96170ef09477dccf4fcdea1e74b973284b0`，Native FileID844424948039045/allocated36864B；guard ADMITTED，asset40960/control25136/unresolved0。原UNKNOWN、Maven6与历史lease都未改。此为真实环境产出，仍不是新Game或SAVE；后继立即公共SavedPolicy/OriginalDriverRunProfile、fresh SCREEN与同pair恢复。

CI archive URL单叶也已真正typing GREEN，7.083秒/70class，source163269B/SHA `0c8f67b0d34059c4761e62ba1ab3bb83ea0645f04c222722d4c8c21828d95378`；只复用冻结CI70作应用CP，无新runner，无重复302测试。最新02e旧URL的OfficialCI也在step46明确404，未进reactor；本次仅发表archive地址修复与真实进度，不声称完整CI已过。

## 首次 cold 实际终态与两个受限读取候选

SavedPolicy于22:10真实exit0，587B/SHA `88d4412b8e7931998555ba827d1377a3d7f892c0a43d8ad72972b29fec713682`；OriginalDriverRunProfile于22:11:37真实exit0，753B/SHA `18aa1a6a36f5211796288244b833122cc8048ad0fe46ce6296ebbb001d25d778`。最终plan5167B已由公共RootFrozenRunProfile.readExact真实6.1秒通过。新业务cfg2096B/SHA `9d4a9b14ead6629286630847818a040e0b9ba40c8a6db67276d69694c85b6b6d`，仍file/codex-session/120000ms/1attempt/0backoff；decision岗复核并持续监听，0实际请求。

首cold公共Main于22:17:43.692458Z真实BEGIN，JVM145896/birth134392546636823733。两次定点栈从SavedAttachmentSourceStore.requalifyConfirmed→historical cycle walk，推进至CanonicalSaveReceiptVerifier/PreparedCleanupNoEffectProof/FullJsonTree；119.9秒CPU5.3秒、289.7秒CPU10.8秒，主要是旧原件资格I/O，并非原重复Win32枚举故障。22:31:48精确进程GetProcessIoCounters读21091530778B/2927993次、other23185806次，不能当物理占盘或磁盘实际读取。原来源自然过期未刷新，始终无Game CREATE。

Root根据实证授权安全结束这次纯source调用。Runtime在fresh纯历史栈、ck3=0/child=0/claim absent、head/WAL2002与旧plan未变、NativeLaunchPolicy过期前claim边界核实之后，以保留精确kernel HANDLE只终止owned145896。22:45:07.529Z真实END，exit1223、WAIT signalled、wall1643.850996秒，stdout/stderr各0B。该阶段没有协作取消接口或独立console组，未冒CtrlBreak成功；早期helper把2002条numeric WAL及2002条sidecar合算4004而拒绝，未发termination，按原文件名协议纠正后才执行。未触旧Quarkus、Maven、复用PID或Game，也无第二并发worker。

SCREEN续租记录如实保留：实际源码上限600秒，180只是建议节奏。一次将其混淆而在仍fresh时正常release/reclaim；另一次安全停止检查期间超过600秒，终态/0CREATE确认后按原owner/latestseq正常expired release，22:47:37以03唯一新claim承接准备，未做过期heartbeat或改flags。Root已找到仓库现成ck3_mod_acceptance_keeper与shared screen_bus_lease，可由Runtime按真实当前CLI SHA、冻结checkout、唯一CAS writer复用，不另造runner；当前是否切换以运行岗实际回执为准。

源码只读结论排除直接安装旧Hpp2：Dmirror Ledger15833/9dda与Store63817/02d189仍exact，但初段qualify仅writer.locked，没有CAS historical scope。后续Core cold的data又是RootReservedRetirementArchive.View，默认generic scope没有向actual转发。Hpp2旧25class/15P不能解决无scope入口，未采用，不能由CreateFile栈推断收益。

独立候选1仅在RootJavaSavedBootstrap.qualify的writer.locked初始纯source callback开已有general scope，1024entries/64MiB/256handles，与后段同限界，不包Game CREATE、新READ或withObserved。actual59488B/SHA前缀36bcf9ae，base59172B/39852798；首编13.375秒/9class GREEN，映射 `initial108c1/ACTUAL-INITIAL-SCOPE1-COMPLETE-FAMILY01.json`，5680B/SHA `dea58f69cb6e1475480da3ad3d38ea828592431e841c29b0b6cc1cb17c3867a2`。这仅typing，不冒当前caller或提速资格。

独立候选2仅给受限DATA View转发generic historical scope，启用接口原sameGame default8192entries/256MiB/16384handles；callback仍原View、无Native facade/decoder/prefix及写权限，不借Native768MiB tier。actual13959B/11df4921，base13334B/876465c0，首编8.280秒/3class GREEN，映射 `forward109c1/ACTUAL-DATA-VIEW-FORWARD1-COMPLETE-FAMILY02.json`，3030B/SHA `f26954d7c8d48b49ee43817310e7700da4ae557522624f12abe7f12d7a991a2b`。新3项真实sharing32、关闭释放、身份/session/thread/写拒边界测试已3P/0F/0E/0skip，14.261秒，XML `forward109j1/reports/TEST-junit-jupiter.xml` 49683B/SHA `ce6b7a1cb88913e6ed885f492140771fd5d0dd8a150dcd28f7b3743161478518`，不以旧15替代。未混Hpp、未覆盖活源/类或冒第二次业务结果，完整receipt proof仍必须实际验证。

新独立Root来源窗口22:28:24Z→23:28:24Z，仅原107class/Maven6/samepair/56+256既有caps与同quota；旧源与旧Main期限不改。composition/ENV request/Frozen profile/plan按已有≤1h，outer bootstrap/declare/census/cap当次新签25min且不放宽原30min。最终新调用只能在上述真实END和0CREATE确认后进行，下一集成结果、Game/READ/Driver/LOOP/SAVE继续分账。

## 显式决策绑定、现成 keeper 与第二次真实 cold

决策岗只读发现实际openExitedCheckpointRecovery没有其它finish路径已有的bindDecisionSelector。若遗漏则nullable selector可能绕过file provider。本次只在新cold入口要求显式decisionProvider，缺失在Game前IOException；finishColdRestored之前按原activeSession/否则writer.locked材料sink绑定同selector，原六处/default/HTTP/Guard不改。actualAssembly97376B/SHA `6d47f3112b049882661a749d8eb1250d3049e95672521fb3132a096f94057cd9`，实际1TU/9class/13.939秒GREEN；formal102432B/a324另typing12.380秒GREEN。决策岗再次核Core.finishColdRestored→Staged.finish→pipeline.create→decisionSelector.ifPresent.bindSelector，绑定确入新ordinaryPlanner，不是闲置字段；最终174项CP九个Assembly首定义均在hook111c1且与完整family map逐件相同，旧R没有遮蔽。

初始scope/受限View/决策hook三生产源与新Test四文件已正式commit并普通FF发表 `e9d2ace1aad19e1294428d1cd29125f3dc4a5243`，parentf271，remote exact已核。正式Bootstrap额外typing16.054秒/9class，View与Test rawexactactual3P复用，未重旧135/15/file9。PUB4原件：`D:/ck3-state/resume91-java-delivery/exited-game-recovery-20261116/PUBLICATION4-COLD-HISTORY-AND-DECISION-HOOK-01.json`，5899B/SHA `c413640c48566e48974c2daaaf3958a396037f41344ad3dc4d24d6f8bd66bf88`；canonical Git disk80174B不冒FS净增。

既有keeper已真实接通而非新runner：同02e独立clean sparse checkout含原tracked CLI、ck3_mod_acceptance_keeper和shared lease模块，旧frozen checkout不改。旧03 freshCAS释放后04唯一claim，22:55:40Z keeper PID186736/birth134392569351637714 READY/首CAS10211；interval120、当前919…UPPER SHA明确覆盖旧默认、source==installed、无录制。manual对04完全停止，单一heartbeat writer；日志repo外、无STOP_REQUIRED。

P3三公共输出于23:15:10真实全部exit0，包含quote/declare/census/Rootcap5/binding5/CREATE/readback。最终newreview到2026-11-16T00:05:09Z，旧P1/P2材料与所有期限原样保留；finalcfg2096B/SHA `ea715b70eaab13e7f910a5f7949084d85027820146b6ac0067c0529f2caf0b08`仍五wire file/codex-session/120000/1/0。prepared入口177892B/SHA `90f51a14bae53c4c80e065e7ca75743cefc105bce1963eb80b96e78c21b7adb5`已由决策岗独立核首定义；公共FrozenSaved与keeper fresh检查通过。

**第二真实single于23:18:59.355932Z BEGIN**，JVM184880/birth134392583393363452，原公共RootOrdinaryWorkerMain restore-exited。旧145896真实terminal后才启动，0并发；外置21class（scope1 9/View3/hook9）已采用，原R/Maven135未覆盖。约45分钟资格包络到00:03:59，当前仅报告真实BEGIN，新的source/IO、Game、两READ、Driver、LOOP/queue/SAVE必须另取实际结果，未授性能提升或10秒目标。

23:24:57Z首个新scope1生产诊断真实完成：publication_attempts167791、held_path27147、acquired_retained127、fallback140517；entry_bound0/byte_bound0/handle_bound140517，peak_entries127、retained7648157B，原caps1024/64MiB/256handles；finish_succeeded1/validation_failed0。仅该scope完整成功，不是全cold或提速成功；Hpp不解handle-bound，当前活轮与bounds保持，等Core较大既有scope实测。

## 第二 cold 自然失败，继续修复完整 DATA 回放的重复工作

第二次真实调用于2026-11-16T00:04:23.534248Z自然END，exit1、wall2724.200283秒；同birth184880的OS exitFILETIME134392610633315079及controller END一致，未执行kill。stdout为WORKER_FAILED、game_stop_requested=false、pause NOT_ATTEMPTED。完整stderr在 `D:/ck3-state/resume91-runtime/samepair-restore03-20261116/logs/RESTORE-EXITED02.stderr`，7786B/SHA `90f224577f65a311bb9410c7126875d8458bad9e63ce984715ea07f120591cb0`。实际cause为Win32Host.deadline→JavaGameLifecycle.requireExitedMembership→Core.ReservedRetirementScope.requireCurrent→受限View.loadMaterial→DPS.rebuild/replayCooldown→readSameGameHistory：Lifecycle observation deadline expired；不是新Game退出或模型服务故障。

第二DATA scope最终publication410649、held331317、acquire13116、retained6072、unretained7044；fallback66216全部byte_bound，peak_entries6072、retained268434935B，原caps8192/268435456B/16384handles。finish_succeeded1仅说明finish函数完成；validation_failed1记录本次callback生命周期超期，stderr无suppressed清理异常，不能称完整资格成功或CAS坏件。23:58样本已累计24.54GB/222.7万逻辑readops，仍在DPS.rebuild/projectFull；过程IO计数不等于物理占盘或硬盘实际读量。终态head/claim等由Runtime另核；截至目前仍无新Game、READ、Driver、queue或SAVE信用。

下一候选只修复这条真实热点：四个生产叶DPS/DriverCapabilityRuntime/NativeOutcomeArchive/RootReservedRetirementArchive，加两个新Test共14项。Root私有构造的DATA source token绑定原受限View/session/thread，不暴露Native facade/decoder/prefix；仅在完整replayOriginal（含header、nested rebuild和最终aux比较）成功、trace关闭与当前来源复验后，保存完整aux的void校验结果。命中仍验证全部retained依赖并向外层trace登记；capture/transient/unheld/dynamic来源走完整原路径。独立128cells/8MiB估重/32768dependency memberships只控制可选复用准入，不扩大历史scope上限。

SourceReady03为 `D:/ck3-state/resume91-java-delivery/exited-game-recovery-20261116/data-replay-memo-candidate01/SOURCE-READY-DATA-ONLY-REPLAY-MEMO4-TEST2-03.json`，4572B/SHA前缀39a01a43。actual四叶首次真实typing17.578307秒GREEN/43class，完整family map `memo112c1/ACTUAL-DATA-MEMO4-COMPLETE-MODULE-FAMILIES01.json`17591B/SHA前缀b9277db6；新14测试与必要formal差异编译仍待。新source1536KiB与编测6MiB独立fund后raw1640097760B/normal24389632B/cap1719664640B，余55177248B；旧unused不重复退。部分实际closure可能全部落held集合，也可能合法零命中，实际收益NOT_PROVEN；不为命中削弱资格或改caps。

CI新实证：archive URL修复后的Official run43767579135已完成bootstrap-tools与qualified-tools两轮，各1207项/0F/0E/0skip，随后qualified child于2.963801秒exit1。缺件为hosted `artifacts/tools-postqualification/actual.json`（ControlCi.runQualified:1947）；不是原Maven下载404。原artifact14186941806为1113578B，Root只做有界内存读取，没有落盘复制。既有complete-Own及两项JUnit门保留，正在定位真实producer与hosted接线，不能伪造actual或称完整CI通过。

00:09:23Z真实末态核实：P3 ck3与worker-child均空，generationclaim absent，native-launch仅template01；head raw d8b37715…/sequence2002、numericWAL2002及sourcebindings2002均未变。TRUE-END-VERIFIED01为4940B/SHA `f39c334539be03105b5fb0af42eedde8200e7b606036f22270f083f6c16c95d9`；四个旧长宿主仍同birth存活，SCREEN仍唯一keeper。没有TerminateProcess，也没有以reap后的OpenProcess87否认此前同birth自然退出原件。

P4新来源准备00:10:09Z先真实拒绝：全D卷usedUpper13308196032512B，加原other512MiB及metadata2MiB后比旧quota13307902017536B多832983040B；当次无P4/binding/worker。Root随后给新独立00:10→01:10Z来源max_project13313094979584B＝该used上界+64MiB+原other512MiB+4GiB观测漂移余量，待fresh核。全卷增长原因及项目实际量仍UNKNOWN；观测余量不授新写额度、不改任何fund/scope cap，system64GiB+safety20GiB仍核。原P3及旧source/期限一律不改。

## 完整 DATA 复用的软件资格与 P4 准备

memo四actual生产叶首次17.578307秒/43class GREEN（Root4/Native18/Bridge14/DPS7）；formal仅Native+Bridge两rawdiff叶14.544161秒/32class GREEN，Root+DPS rawexact复用，没有重135源。第一轮新测试为APP10P/Root4E，Root均因java.io.tmpdir缺失在JUnit @TempDir前失败；只修实际目录准备后Root3P/1E，余1是负例夹具同线程嵌套另writer，未到目标断言。保留两轮RED，仅修合法foreign-session夹具，不改生产或断言。随后只重编RootTest1、跑未通过1及新增非空adapter1，18.904604秒2P/0F/0E/0skip。最终15个不同用例全部通过，不能称首轮14项全绿。

新增真实Native adapter用例由原writer建立合法CAS，原受限View load→独立trace非空→close，再新trace仅verify该依赖，证实同集合向外层trace传播，没有Game或Native动作。最终RootTest15287B/SHA前缀fe810465；新增两项XML `memo112j1/root-remaining2-03/reports/TEST-junit-jupiter.xml`49425B/SHA `56827c8fcba87c494e11359fd8f23da8fad685d4b62816339bc5ee4362256560`。已通过APP10/Root3未重跑，43生产类未重编。实际活READcapture/transient场景仍只有静态及机制失格证据，真实Native输入正例NOT_HELD；不将其写成实测。全cold实际可复用性与性能仍待P4。

P4三公共输出00:14:17.775416Z实际全部exit0：ENV35866B/0997096d…、SavedPolicy587B/8a27674d…、runprofile753B/0d747dc2…；新plan5165B/713aec8d…、cfg2096B/1f45a715…，旧P3不改。准备入口442969B/SHA `7cda92452616f3b2e34f9781009cb2f23449d03d10c5d1e8339eb0335f62f54b`，174项CP；决策岗独立核61个首定义全部匹配（memo43/initial9/hook9），旧forward family已移除，file/codex-session/120000/1/0五wire精确。此为metadata与软件准备通过，尚未BEGIN第三次业务。

实际新roots Native占94171952B，原256MiB余174263504B；SCREEN keeper每120秒原全量list审计约1.77MB，保守2MiB/轮，不能计0。余55分钟若再留56MiB尾量与两READ128MiB峰会超原scope，Root优先授权对已完成、早于当前10分钟且非最近三轮的旧renewal审计做一次无损归档，原inputs/ready/journal/admission及当前尾不动。普通逐文件ZIP达到3.67MB界后真实拒绝，0旧件删除；正在尝试唯一一次长字典TAR.XZ，≤4MiB且逐项bytes/SHA核对成功后才清理精确旧副本。未为此新fund40MiB，失败和占量如实保留；新的worker仍等实际容量资格。

最新e9的Official run43773320840实际更早失败，与d8b的missing-Own分开：ControlCi.verifyPlan:1689以默认8MiB调用sourceManifest，报Manifest content limit exceeded。当前Git build-tools总8438287B，含main Java4033910B/Test Java2638525B及固定资源，已跨旧界；该run尚未进入qualifiedTools阶段。原d8b两轮各1207P仍仅属于其原运行。CI只读结论还指出hosted未供应真实Own七项原始refs及匹配同机materialized map；真实Producer41/postqualifyTools实现存在，但不能靠伪actual或一行接线宣绿。当前不为P4扩profile或改冻结Maven，完整CI继续RED，后续按真实输入修复。

00:20:01.615823Z旧审计TAR.XZ真实PASS，20.7877秒：108个完整旧目录/432files、原logical63626830B，归档607616B+逐项索引235373B，共842989B<4MiB。每项解包path/bytes/SHA与源identity/mtime/content二次复验成功后，才逐精确文件unlink及空目录rmdir；inputs/ready/journal/admission/当前尾/keeper源码均未改，前后独立live_lease通过，原失败DEFLATE保留。证据 `P2/keeper-audit-archive02/ARCHIVE-VERIFIED-END01.json`2191B/SHA前缀324d40c5。旧字节完整可追溯，实际physical回收量以新census为准，不用logical差冒Native；没有新40MiB fund或重复unused退账。P4公共FrozenSaved也实际exit0，第三业务仍在最终阶段容量核验，尚不记BEGIN。

## 第三次唯一业务已开始，持续观察实际复用

四生产/两Test及Root五报告共11文件已正常FF发表 `96dbec280a5af31a8ede95ac38ac69dd8dd8cc25`，parent e9d2ace，远端master exact、index空、整树clean；没有为Git推迟业务。软件闭档 `memo112c1/SOFTWARE-CLOSED-DATA-MEMO4-15-DISTINCT-CASE-PASSES01.json`12702B/SHA前缀d28c1362。源scope与编测scope只退真实unused一次，后续Git独立272KiB，最新raw1639652816B/normal24389632B/cap1719664640B，余55622192B，Git scope尚待闭合，不借源尾或扩大运行fund。

P4于2026-11-16T00:22:57.067830Z真实BEGIN，JVM151504/birth134392621770699837，公共RootOrdinaryWorkerMain restore-exited；旧两个caller已真实terminal，单worker/无并发Game。启动前61首定义、15distinct逐method合并、FrozenSaved及SCREEN live lease均已核。归档后运行新roots Native44310152B，加未来keeper56MiB、两READ128MiB、8MiB小尾为245636744B<原256MiB，尚余22798712B；provider/SAVE须待实际READ量分阶段另核，未预授。资格原件 `P4/input01/EXECUTION-QUALIFICATION-AND-RESTORE-STAGE-ADMISSION01.json`14385B/SHA前缀52f9ee07，BEGIN28784B/e7e31777。

58秒样本仍retireExitedLifeInterruptionOnly历史原件读，新NativeArchive类已真实加载，尚未到memo；153.3秒样本已进入initialscope1→SavedAttachmentSourceStore.requalifyConfirmed，read2913201032B/369708ops、write14675B/3ops。此为逻辑进程IO与阶段证据，非Native占盘或收益。当前仍template01、claim absent、无新Game/READ/Driver/queue/SAVE；继续实际阶段与完整cold终态，不在发表或启动时停止。

P4 initialscope1于00:27:07真实完成，指标与P3同167791 publication/140517 handle_bound，finish1/validation0。其后349.7秒栈证明 `openExitedCheckpointRecovery→writer.locked(qualified::material)→ConfirmedSource.material→requirePhysical` 仍是另一段未包historical scope的完整fresh物理原件验证；并非新DATA memo失效。477.8秒样本才真实进入RetainedDataReplayScope.replay:118和新bridge/View；该118行是capture后的完整replayOriginal，不能当cache-hit。1229.8秒样本仍此完整分支，read18861559465B/2017066ops，尚无最终DATA指标或新Game/claim。

依据这两个已复现热点，Root授权独立P1两叶候选：只初始pure-source caller由256handles改2052，1024entries/64MiB及后段两处原限不变；只qualified.material原locked callback包同既有historical scope，完整fresh physical函数、session和原deadline均保留，不包Core后续、Game、新READ或写。原Store公式E=C+S、Hheld=2C+S，最后一CAS对前保4headroom，1024全CAS集的理论caller条件为2050；2052是本次独立选择，不将计数上界冒OS总句柄/kernel池或实际全集持有证明。actual Bootstrap59489B/095da3a6…、Assembly97938B/d7be6dff…；formal60023/5efc…、102994/3e42…，均未用于P4。

新Test6411B/fc58…使用12真实CAS/24文件核最后一对的26handles条件、25不足、entry11仍限制，以及正常/异常关闭后共享写句柄恢复、ledger与原件不变；不镜像2052常量。SourceReady7611B/cd8ea74c…，独立source640KiB已fund。现开始必要actual2/Test1/formal差异2增编，测试与收益均待真实终态，不混已闭memo资源或重跑旧43/15。CI另独立source3MiB用于显式Tools12MiB与新reactor封套六叶；旧8MiB/R6/R7不变，hosted legacy入口也须闭合，真实Own缺口仍保留。

P1软件现已全部通过：actual2/18class17.890796秒GREEN，完整family `p1h113c1`6858B/54ae3f12…；仅新增Test1真实21.823354秒1P/0F/0E/0skip，XML `p1h113j1/reports/TEST-junit-jupiter.xml`48728B/SHA `d52446135632e7ba055f3e5657bce10c5f13ba912ded0c556adadb0b34840400`；formal差异2/18class15.440923秒GREEN，`p1h113f1` family6732B/0c264d37…。未重旧43/15/135，不外推2052全规模OS压力或实际cold收益；P4继续原参数与原代码，没有热换。

P4第30分18秒样本00:53:15仍在Core DATA完整capture分支，read23613584774B/2192001ops、other26679476ops，stdout0/无END/claim absent，第二CAS与DATA最终统计未出。新CI封套6生产+3Test已冻结Ready10537B/2297b6ca…：Tools12MiB/1000files、一项目；R8保6144files/96MiB源/112MiBcopy及R7其它模块上限，只扩build-tools src至12MiB；当前LEGACY及complete canonical reactor均选择R8，pipeline HTTP/fixture级别仍原样。新11项加两旧selector方法待独立最小增编验证，旧STANDARD/R6/R7及冻结135的财务/completion段原body保留，尚无新的CI绿色信用。

## P4 真实终态及证据改变后的后继选择

P1三文件与五报告8文件已正常FF发表 `d1da4d07c15b7527eb2a7c19c54247336e5c2e34`，parent96dbec，远端exact/index空，CI九叶WIP明确未stage。PUBLICATION8为5217B/SHA `14d366aed76440f4e42f09486d20f57238d29f806eba497ffc3c0daded7e4cc9`；canonical新对象disk121044B不冒FS净增，独立208KiB guard保守关闭。旧96dbec的Official run43780185697已向服务端请求取消，d1da4d当前43783527222仍在执行；Linear history通过，完整Official绿色尚未取得。

P4于01:08:11.925485Z真实自然END，exit1、wall2714.8576838秒；原错Lifecycle observation deadline expired，未kill。stderr8230B/SHA `8816d0a55f35ee3cdb256154c8e4c8541561aa9f0ac8f417f038717e4021a845`；stdout379B WORKER_FAILED/game_stop_requested=false/pause NOT_ATTEMPTED。首次完整memo指标full_replays174、hits21、ineligible0、unretained109、scope_callback_succeeded0；异常clear导致entries/estimated_bytes/dependency_memberships为0，不能说从未有缓存。21个真实hit不等于完整cold或整体性能成功。

CAS2 publication434482、held342407、acquisition14325、retained6072/unretained8253、fallback77750全部byte_bound；peak6072/268434935B，原8192/256MiB/16384未变；finish1/validation1仍是超期callback收尾，不是独立坏件结论。01:10:20有界末态原件5434B/SHA `15bf54781b7aecd2d5b375007d2c33ac11ed33695845cb4768f3f9b325d2974e`：同birth自然exit1、ck3/workerchild空、claim absent、templateonly、head2002/raw d8b3…及numericWAL/sourcebindings2002不变；原save/driver FileID/mtime/bytes pointstat未变，未重复读87MB。四旧宿主同birth存活、唯一keeper正常；0第四业务、0新保存日。

01:03轻OS快照：ownedJVM private2355384320B/WS2363875328B、handles12566；global physicalavailable52350771200B、commitavailable68772405248B。01:05:44只读jcmd GC.heap_info（未GC.run/hist/dump）显示defnew629120K used315049K，tenured1398144K used1398144K，Metaspace used37404K；不是GC后live量或RSS上限。Root据此授权下一独立01:12→02:12来源在fresh容量/内存核验后采用P1，并只将source JVM heap2→4GiB、保持45min包络；4GiBheap+1GiB native是预算估算，未来Game32GiB/CI2GiB另计，不借Game Job或称硬RSS上限。复用原有archiveParsedMaterialDiagnostics只读开关，不新增缓存。

P4的新byte-bound证据使旧Hpp2重新成为直接相关候选：其payload字节可轮换，而metadata/Commit、payload HANDLE、Pin持续至finish；verifyLeasedPublication不为纯资格重新载入payload，缺pair仍失格。此前无scope/handle-bound的拒用理由保留为当时事实，不能继续用来否定本次新问题。Root授权fresh核原Ready及D两BASE仍exact、复用旧25class/15P，并在该overlay下只补当前真实Root非空DATA adapter方法兼容验证；不重编25/重跑全15、不加DATA256MiB、entry或handle上限。最终P5 BEGIN须独立资格/CP首定义核验，不用旧软件结果冒实际收益；原P1/CI包不混改。

CI六叶首编25.094秒RED，因复用actualD的RootSoftwareChildBootstrap.Config有15参数而正式HEAD为14；保留已产ControlBuild63/CiBootstrap71共134类，不修改正式消费者去迎合旧CP。仅补未改HEAD必要依赖1叶及四个未产消费者，17.893989秒GREEN/101class；变更六族完整226类另加该HEAD依赖9类。原RED保留，新13方法仍待真实运行，未跑Maven/135或Own，未授完整CI通过。

## 第四次唯一业务采用已验证的 payload/证明分离

P5 fresh物理内存available58150670336B、commitavailable74388615168B；4GiBheap+1GiB JVM native估算、Game32GiB、CI2GiB独立相加41875931136B，仍留physical16274739200B/commit32512684032B。DusedUpper13308216119296B（项目真实量/漂移原因UNKNOWN），加原other512MiB和metadata2MiB后仍小于既有quota13313094979584B，system64GiB+safety20GiB通过。只读诊断并非原actual已具备：formal有而actual6ac41b没有，故没有只加-D冒称启用；Java仅把7个既有diagnostic hunks移到冻结actual，逆向rawexact，actual其它两类差异保留。

新actual Native160594B/e028775e…真实1TU/18class12.460167秒GREEN，完整family6693B/327f84b0…。旧Hpp2 fresh核D BASE Ledger15833/9dda及Store63817/02d189、Ready2a26631b、完整25class、原15P及schema全部匹配，证明小件9742B/e9bf1dbd…。只补当前Root非空DATA方法，在新Native18+Hpp25+原memo43 overlay与诊断true下10.188428秒1P/0F/0E/0skip，XML48883B/SHA `545643ac43f500a5d257a59d44c308dfd8c344d26c1bef7d52ac38af02067a20`；真实stderr有scope_summary=true/key_absent1/final_entries1/retained_bytes3/completed1/limit64。未重编旧25或重跑原15，不授实际cold收益。

P5三公共输出01:23:59.933837Z全部exit0。原8组scope census发现keeper重长后若再加future尾量/READ会超256，Root另授权archive03，与archive02不重叠：01:27:29.920315Z/15.718秒真实PASS，396files/99dirs原logical58323306B→TAR.XZ568620B+索引211552B，逐项及源二次核后才精确清理，活输入/尾/源码未动；前后livelease通过，无新fund或unused退。tools日志误纳全W命名空间160MB仅是保守上界，补按production build-attempt前缀的actual28731664B/目录guard28829968B+m2hold8388608B<64MiB，不误称超额或退余额。

原P5 review02:12不足最后完整45min包络，Root在01:34授权独立晚签01:35→02:35，不改旧输出或deadline。新prepared559016B/d37d8b72…与旧175CP字符串、86class首定义、JVM与DATA组均相同，仅增加两份真实1P资格XML及新source/plan/cfg引用；决策岗只核差异。最终cfg2101B/68e7c785…五wire仍file queue01/codex-session/120000/1/0，plan5205B/4141e772…；Hpp25+NativeDiag18+P1callers18+memo剩25共86unique，旧Native18已在首定义中替换，没有误算旧43全族。

**P5-late第四且唯一业务于01:45:02.702082Z真实BEGIN**，JVM181900/birth134392671027048433，公共RootOrdinaryWorkerMain restore-exited。45min检查包络约02:30:02，来源review02:35；Heap4GiB、诊断true，DATA仍8192/256MiB/16384，原证据、旧UNKNOWN与head2002不改。归档后fresh6runroots Native58682608B+futurekeeper60817408B+两READ134217728B+8MiB尾=262106352B<原256MiB，余6329104B，provider/SAVE仍另按实量分阶段核。BEGIN30720B/fb77c3c4…、finalqualification4010B/0b6d5438…；软件、实际装载、BEGIN、Game/READ/Driver/queue/SAVE继续分账。

正式Hpp2差异另行移植：Ledger19391/b623与旧actual rawexact，Store68225/1fd4384b仅9个唯一hunks、其它formal差异保留；原新增3方法回归16128B/15d3b6e4…同rawexact纳入正式源，不用旧12替代新合同。Ready2为6027B/bdd0a334…，必要formal Store1 typing后单独发表，不是P5前置。CI Test3首编10.241529秒RED，只产新ToolsTest1class，缺HEAD两个小test helper；已定位723B+15709B，没有生产或断言修复，现让位P5后补helper2+未产Test2，原13方法尚未通过。

P5-late实际01:48:13完成初Bootstrap scope：publication167791/held116901/acquire1024/retained1024/unretained0，fallback49866全entry_bound、peak17374522B，原1024/64MiB/2052，finish1/validation0。01:49:57新material scope也真实完成：publication135318/held104472/acquire1024/retained1024/unretained0、fallback29822全entry_bound、peak28461667B、finish1/validation0。两段parse诊断分别protocol_hits23952/19281、fullMaterial_hits400/320，均miss759+8、无bytesUnequal/evictions，entries767/retained23219949B。此为本轮两个独立scope成功，尚非Core整体或Game；未做控制变量性能比较，不据更早阶段外推10秒目标。

后置formal Hpp2 Store1真实12.084533秒GREEN/18class，`hpp116f1` OUTPUTS43060B/5f651dc8…。Ledger旧7与源rawexact复用；正式纳入的旧新增3方法源与原完整3class fresh一致，23个直接Ledger/Store符号在formal Store18+Ledger7均可解析，ABI复用小件 `FORMAL-HPP2-RAWEXACT-OLDTEST3-ABI-REUSE01.json`8320B/b4199221…。未新跑旧3/15、不冒新formal行为矩阵。P5实际装载和软件兼容此前已完成，源码与回归据此独立正常发表；CI13仍另包继续。

## 显式源码封套的必要 13 方法已通过

Hpp2生产2+原新增回归1与Root五报告共8文件已正常FF发表 `0f0a83d7c0146a67ec57a1fc186d652d25e15c6f`，parent d1da4d，remote exact/index空，CI九叶继续未stage。PUBLICATION8为7575B/SHA `6feb86ec00bbc05baf26e4be890ad9502ea94abc47121cd406c30043879eab8d`；canonical对象disk100778B非FS净增，独立208KiB guard保守关闭。上个d1da4d Official run43783527222已向服务端请求取消，保留最新运行，未把取消记测试通过。

CI必要Test依赖补齐后15.198812秒GREEN/6class：只编HEAD两个小helper与未产Test2，原ToolsTest1class保留未重。六生产族226class+必要HEAD依赖9class、三个Test5class+helper2完整typing闭合；原25.094秒生产依赖差异RED及10.241529秒Test缺helper RED保留，正式profile逻辑未因这两次失败修改，没有fresh全六或135/Maven。

**新13方法真实17.431708秒13P/0F/0E/0skip**，显式parallel=false：Tools新11+选定Stage1/Parity1。XML `F/ci114j1/reports/TEST-junit-jupiter.xml`56774B/SHA `0cc8a92bbda012abfe7e1eae231908aacfb21105f2efe554218dc15d4ea41e1e`，ACTUAL1266B/569d90a7…。验证覆盖旧STD8/R6/R7枚举和上限不变、新Tools单项目/1000files/12MiB与.mvn8MiB、src/pom/固定资源全量同pin、精确12MiB与首超字节、1001文件拒绝、35项目R8仅Tools模块扩界、LEGACY/complete两入口新选择、Tools与Service/RootCard区分、原Lobby输入门及receipt读取边界。测试只建小POM图及单棵边界payload，未物化整图、未Maven/Own，也没有新的Official全绿信用。

P5-late 1584.35秒样本02:11:27仍Core DATA fullcapture、0Game/claim；read23814366570B/1342259ops、OS handles16804。标准只读heap_info同birth前后核：new total1258304K used707864K，tenured total2796224K used2045189K（73%），Metaspace37783K；未GC.run/hist/dump，不从OS private4506554368B/WS4504997888B推heap使用或GC后live量。最终Hpp/entry/byte/memo统计和完整cold终态仍待，不以已发表源码或本次CI13改写本轮结果。

## P5 真实句柄上限与后继受限 DATA tier

CI九叶与五报告14文件已正常FF发表 `e26e5ac318ae4ff68f1c3158767c279852d57cb3`，parent0f0a83d，remote exact/整树clean。PUB14为9530B/SHA `b9f89a828b0871e869e0133a809893c395f7e14d1e44bcb4aa1116b3bcd73bf6`；default-zlib219877B只是估计，实际Git blobs271990B/graph311838B，已按实际报价补64KiB使Git320KiB+meta16KiB guard覆盖，不称FS净增或未知退款。上个0f0a83d Official43789361076已请求取消，最新e26e Official43791639141继续；完整Official仍未通过。

P5-late于02:30:09.219723Z真实自然END，exit1/wall2706.5176786秒、Lifecycle observation deadline expired，未kill。Hpp/CAS Core publication791167/held708654/acquisition8191/retained8191/unretained0，fallback74322全部handle_bound，entry0/byte0；peak_entries8191/bytes268435456，原8192/256MiB/16384，finish1/validation1。Hpp2已消除此轮byte-bound，当前瓶颈已改变，不能以此授恢复或整体性能成功。DATA full242/hit28/ineligible0/unretained85/callback0，异常clear后的entries0不代表从未存储。Core parse completed0，protocol hit28000/miss63941、fullMaterial hit2045/miss9572，evictions73492、entry108/byte73385非互斥，peak1024/67108847B，byte缓存原限未改。

末态原件7553B/SHA `321720e5065985a3570350dba4547197a778a8e4154ade76b1ecf25844349828`：ck3/workerchild空、claim absent/templateonly、head2002/raw d8b3…及2002 numericWAL/sourcebindings不变；原save/driver pointstat原样、四长宿主同birth活、唯一keeper正常。退出时kernel FILETIME此轮NOT_HELD，不编造；immutable controller真实wait exit1/BEGIN同birth及session89624原件保留。stderr10753B/SHA `70fc9477f3a42c5bf6d47dc0585b3152bfaf432b4263e5259953e10c560f5298`，仍0新Game/READ/Driver/queue/SAVE信用。

Root授权新独立DATA tier v1候选16384entries/256MiB/32772handles；这是有限资源选择，不把74322次数当unique refs数，也不保证全集必然可留。旧ActionPorts generic DTO硬界8192/256MiB/16384及Native768MiB分支保持；只有私有Root来源token能开启新Store范围，same session/thread/fixed head和受限View、无decoder/native facade/写仍保。DPS只补既有admission拒绝/淘汰/成功publish/高水位诊断，128cells/8MiB/32768成员及验证顺序不变。源3MiB已独立fund，实际与formal BASE分开port，当前未编测/未采用/无第五业务；完整Ready和必要scaled回归后再给新独立来源窗口。

keeper旧审计archive04在新授权下02:43:08.909001Z/18.078秒真实PASS：444files111dirs、原logical65393586B→621664B TAR.XZ+236981B索引，全roundtrip和源二次复验后精确清理、与02/03不重叠，活输入/尾/源码不动、前后livelease通过，未新fund/返unused。旧P5来源02:35及45min包络原样，不追改失败。

并行读取e26e的Religious Ritual Fusion Static run43791639268发现独立真实故障：121个测试仅relocation source qualification因other.txt raw hash漂移报错。Root受控小Git复现（独立1MiB、仅子进程临时global配置、未改真实Git设置）：LF源8B，global autocrlf=true时默认clone变9B CRLF，显式clone local core.autocrlf=false恢复原8B及同SHA。证据 `D:/ck3-state/resume91-root-ci/rrf-clone-eol01/CONTROLLED-CLONE-EOL-RESULT01.json`2522B/SHA `3ebbab999c359af525313af104e47b0a03030c3b560d29b76e42332e16075c0a`。仅修改该Test的clone局部选项并新增raw signature断言；生产严格raw-hash拒绝不变，模块整链验证交后继真实CI，尚未宣称该121方法通过。

Root的RRF Test1+五报告6文件已独立正常FF发表 `1f361f55b66dfe02d4725b987b6af2241f00739e`，parent e26e，remote exact/index空，仅DATA tier候选仍WIP。PUB6为2269B/SHA `79c0aeab181666c2d6808dad91ca331347efef719e2c6fcdfc2f11a9c49b5fcb`；canonical1commit17tree6blob disk83814B非FS净增/peak。独立1MiB probe按current directory-guard340320B+原closure64KiB保守结清，只返unused642720一次；336KiB Pub guard保守关闭，不以未知Git peak退额。

该修复的**真实后继CI已通过**：Religious Ritual Fusion Static run43795343520（head1f361f55）completed success，03:01:36日志明确SourceQualificationTest10/0F/0E/0skip、RRF总121/0F/0E/0skip、BUILD SUCCESS。旧e26e失败保留，没有改生产raw-hash资格规则。上个e26e Official43791639141已请求取消，最新1f Official43795343586仍执行，不能用RRF绿色外推整个Official或Own通过。DATA tier源码/必要新回归继续，不以这次旁支交付停止恢复主线。

## 受限 DATA tier 四生产及必要八方法资格完成

最终四生产叶为RootReservedRetirementArchive、NativeOutcomeArchive、ImmutableArtifactStore及DPS；不改ActionPorts旧DTO、Core/Main、Native768MiB或策略。Store只增加包私有固定DATA factory 16384/256MiB/32772；public tier枚举仅资源数据，不能自己开启范围。Native必须核私有Root token的actual/view/session/thread/fixed head，callback始终同一受限View。DPS保128/8MiB/32768和验证顺序，仅增加singleton依赖/weight拒绝、原OR首因的LRU淘汰、successful publish及entries/bytes/memberships峰值，异常clear不清峰，不造不可达membership正例。

初actual4真实16.733335秒GREEN/48class（Root4/Native19/Store18/DPS7）后，源码复审发现新authority逐read调用session.persistedHead会反复读/hash snapshot，Runtime明确hold该Native19而未采用。仅Native修为独立只读头lease持续至整个CAS finish之后，前后边界完整读/hash及FileID/mtime/size复验，scope内cheap source/session/thread检查；写/delete/rebind由真实Win32持有保护。其间11.032秒RED为缺ContinuityJson import、0class，精确补import后12.418866秒GREEN/19class，不重另外三族。最终actual48 family `dat117c1/ACTUAL-TIER4-FINAL-REV03-COMPLETE-MODULE-FAMILIES01.json`19602B/7e41b698…，旧Native superseded原件保留。

Test2首次11.858秒RED/0class，因RootTest两处JUnit BooleanSupplier重载泛型推断；只加显式Boolean type witness、不改生产或断言，11.398秒Test2编译通过。实际8方法于03:36:08.944Z BEGIN→03:36:21.271Z ACTUAL，12.327505秒8P/0F/0E/0skip：Root5+DPS3。XML `dat117j1/reports/TEST-junit-jupiter.xml`54364B/SHA `aa1fdb3c458d30204f9b45cf7cd84c7c33a8235a3b8a662d7897157ed1b45c23`，ACTUAL1270B/510bda79…。覆盖旧generic大值拒绝、真factory实际limits诊断、无/错token/view/session/thread、原受限callback及无decoder/写、头/CAS正常异常释放、2×80KiB payload轮换持续双pair、entry1失格吸收与nested依赖，以及新DPS准入/峰值统计。没有16k文件物化、没有全规模OS压力或恢复收益结论。

后置formal只Native+Store两rawdiff叶13.691035秒GREEN/37class，Root/DPS与actual rawexact复用；完整family12998B/73331737…，没有Maven/135/旧矩阵重跑。实际48及8绿已直交Runtime，不等formal/Git或资源闭档；完整源REV04 Ready18696B/39be849a…保持实际/正式差异，不整叶覆盖现场。

Runtime03:19:32 archive05真实PASS：204files51dirs原logical30051910B→353084B TAR.XZ+109967B索引，全部roundtrip和源二次验证后精确清理，活输入/尾/源码不变、前后lease通过，未新fund/退unused。原P6三公共输出03:21:53真实全exit0、来源03:15→04:15保留原件；由于候选修复耗时，Root授权最终8绿后以实际当次UTC晚签独立60min新来源，旧窗口/输出/动作deadline不改。当前无第五业务/Game/保存信用，最终CP87/五wire/8资格后才新BEGIN。


## 第五次实际恢复开始；完整 CI 暴露共享夹具错误

受限DATA四生产/两Test与五报告已正常FF发表 `5f878ecad486bd7dfcddd1662669b34d7a40f1dd`，parent1f361f55，remote exact/index空；PUB11为7840B/SHA `98599884ff239310341be6f2a5a8589993ad6c21a33b592fb8ff8b6b7c401a38`。canonical disk210337B在Git224KiB guard内，非FS净增或峰值；源/编测/发表各自资源闭合，没有重复退款。

**P6-late第五次唯一业务于03:49:26.200887Z真实BEGIN**，公共RootOrdinaryWorkerMain restore-exited，JVM187700/birth134392745662034652/session30935。新独立来源03:42:11→04:42:11，旧03:15→04:15保留；prepared584505B/SHA `f02a8bf0698e68f2664585ad1dbc947bd07ede04343b24f667b96f6fa73b948e`，176 CP/87 unique首定义及Codex file五wire均核。heap4GiB/诊断true，新私有DATA v1为16384/256MiB/32772，旧generic/Native tier和memo预算未改。45min约04:34:26为观察检查点，未授权timer强杀。

BEGIN前archive06真实无损完成168files/42dirs、原logical24746202B，逐项roundtrip/源二次验证后才精确清理，活输入/尾/源码不变、前后lease通过。运行现量51921368B+keeper60817408B+两READ134217728B+尾8388608B=255345112B<原256MiB；provider/首SAVE仍须按实际READ实量另核，不借未来fund。heap4GiB+native1GiB是估算，不是硬RSS上限，future Game32GiB及CI2GiB独立相加39GiB，fresh物理/commit余量与D quota通过。

03:52:34 initialSavedBootstrap真实finish1/validation0：publication167791/held116901/retained1024/fallback49866全entry_bound、peak17374522B；03:54:09 material scope finish1/validation0：publication135318/held104472/retained1024/fallback29822全entry_bound、peak28461667B。两者原1024/64MiB/2052，parse各completed1，无eviction。03:57:28/实际elapsed481.9s已越Core材料precheck934，进入Core940→readSettledSameGame/readSameGameHistory，held metadata读取、handles11947，累计读10.496GB/990807ops。此时新DATA最终计数尚NOT_HELD，stdout空/templateonly、无真END或Game，不授收益、READ、队列或SAVE信用。

并行Official run43795343586（head1f）实际bootstrapTools为1229总/1226P/0F/3E/0skip，artifact14196267135/530327B有界内存读取。三E均ControlCiStageTest实际producer链：actualTypedProducerRoundTripsThroughTheSharedReaderWithOneNestedGoldenPlan、portableCheckoutSourceDataTravelsThroughTheOriginalFixtureRequestProducerAndReader、readerRejectsRemovedGoldenPlanAndARequestBeyondTheSharedWorkDeadline。生产显式Tools guard正确拒绝fixture的artifactId=metadata；仅将其共享producerInputs改成canonical standalone Tools POM并用既有显式TOOLS_20261116_12_MIB sourcePins，生产/断言不改。RootSoftwareFixtureInputsProducerTest只生成g2-http JSON、不拥有该POM，不扩改。前13选定方法未覆盖此三实际fixture，不能外推完整CI绿色。

当前新Test1候选61645B/f66a792a…，Ready6023B/26a2a7be…；源256KiB和distinct编测6MiB分别fund，先失败3再whole26一次，不跑本地Maven/full1229或重13。首编9.842秒RED/0class因Native漏已绿旧helper输出CP，保留失败，只修CP重编同源，不改生产迎合依赖。新Official43799855518截至04:00仍执行，尚无完整CI/Own绿色；实际恢复不等待此旁支。


Test1同源补既有helper CP后10.274780秒GREEN；三真实失败selectors14.966510秒3P/0F/0E/0skip。whole26首次真实16.160秒为19P/7E，七E均既有ControlCi.currentJavaCarrier同CodeSource guard：离线增编将ControlCi与CiBootstrap/ControlBuild分别置于两次绿输出目录，正式Maven为同目录，原选定13未覆盖此carrier。保留19P7E原XML，不改生产guard或Test断言；仅在同6MiB内把三族既有完整class同FileID hardlink到一个同源origin（0javac/0正文复制），核原bytes/SHA及首定义后只补失败7。最终若通过应记26 distinct组合，不称单份whole26全绿。


三族ControlCi50+ControlBuild63+CiBootstrap71共184原class真实同FileID hardlink共目录后，补失败7于43.621474秒真实7P/0F/0E/0skip；0javac/0生产guard改变。补7 XML `F/ci118j2/carrier-repair03/reports/TEST-junit-jupiter.xml`53070B/SHA `023d9d8ac00fcca9cc020fc2fc192301225b79dc583bebc22bac6fe0e651fc22`。原whole26 XML68199B/SHA `65b6c36d3359e606ed2b6543ab02f3fbd001967139536478ae44af14864bf523`保持19P/7E；新7与原19组成26 distinct最终通过，原三实际失败另已3P，不能改写为单份whole26全绿。此次仅Test1两行canonical fixture/pins改动，软件资格已齐，正常单包发表不等P6终态；完整Official及Own仍待真实后继结果。


P6-late04:14:20/elapsed1494秒仍Core940，现成栈DriverJson.model/LinkedHashMap递归规范转换；读29.304GB/1424101ops、handles18823、OSprivate4.511GB非heap结论，stderr尚无DATA/memo/parse终计数、无Game/真END。窄只读源码映射由Runtime当前firstorigin小件 `LOADED-FOUR-SOURCE-CURRENT-ORIGIN-PINS01.json`8243B/SHA `54bd8bac61c141c6ac383346880a1c9c6d3e1a4d6a0ec80e4831610a60dc8d81`绑定，不拿formal近似源当actual：Core940→CBJ4557同Game scope→4698逐READ→retainCapturedRead；Reader209 bytes/exactSHA→211因受限View decoder=null而DriverStateSnapshot.decodeComplete。Native parsed缓存为RawJson封套/验证，并非Complete或完整Jackson树，parsed hit不等于下游decode跳过。DPS memo hit省完整void header/cooldown/rebuild，但CBJ710/752/756的快照encode与SHA在其外；Complete快encode只拼私有Value bytes、小header，legacy才全树，单BigIntegerNode样本无法区分。调用次数、快路比例、同实例复用、CPU份额及主瓶颈均NOT_PROVEN，Hpp2 held也不等于payload字节驻留。

基于同一retainCapturedRead内afterDriver.encode连续重复的源码事实，另做只读最小机会核验：检查中间mutation/sideeffect与确定性，若成立仅在本次调用局部复用相同encoded byte[]用于原比较及原SHA；不跨调用cache、不减少exact验证，不改活P6。候选尚未实现/编测，收益未知，与新DATA tier最终结果独立。


CI fixture Test1+五报告已正常FF发表 `170f7b4837d2fae21480df8e8ec5b8b9ed5267b6`，parent5f878eca、remote exact/整树clean。PUB6为5853B/SHA `8cdcd071c98bce60927313103c3fa2c30353d6004998f763e36c78f90982f69c`；canonical graphdisk104127B非FS净增/peak，独立208KiB guard保守关闭。完整软件闭档 `F/ci118t1/SOFTWARE-CLOSED-CI-CANONICAL-FIXTURE-TEST1-FIRST3-WHOLE19-REPAIR7-DISTINCT26-01.json`17096B/SHA `9ba117195d55a388112376923eacfae6867e183cb4294a91a5b226e9f05f856b`一次核读；source256KiB及编测6MiB只返各自真实unused81920/1691696一次，Native该波按协议结束，不空闲轮询。新Official43802085477已启动，旧5f43799855518向服务端请求取消，取消不算通过；新完整CI尚未结论。

P6-late04:19:32/elapsed1806.3秒仍Core940 DriverJson.model/OpportunityJson.Obj规范转换，读38.127GB/1622523ops、handles19541，新DATA终计数仍NOT_HELD，stdout/template空/真END未有。OSprivate4.511GB不作heap用量或GC后live结论；不将单帧栈或旧parsed命中当性能根因。

源码局部复用只读资格已闭：Complete为final record，历史List.copyOf、sealed Slot/Value持私有bytes/clone accessor，编码之间仅原件读取比较与可选capturePin，无Driver mutation。actorId允许BigInteger子类，故不能无条件删除其第二次编码；采用邻近retainReadCapabilities既有的exact BigInteger class guard，标准不可变对象局部复用第一次encodedDriver，子类保第二encode原位置。原首encode→原件load/compare→原capturePin→SHA/stamp顺序和所有异常不变，零跨调用缓存。actual BASE553186B/16647bc5、formal BASE556842B/4cf5fc34；最终after553335B/72acc5e0与556991B/00fd1a3b只同一hunk，原3656B差异保全。

新独立source2MiB已fund，Ready02为4296B/a2a32d54…，根 `J/retained-read-after-driver-local-encoding-candidate01`；BASE仅引用旧冻结源/Git而非双复制。仅既有CleanRestartCanonicalWriterTest72242B/90d82daa一叶必要typing及capturedReadSuffixRetainsActualPublishedDriverWithoutReplayingReads方法，涵盖3条已发布READ、最终Driver bytes/stamp和改原row拒绝，不整类11或大Transport。actual1→Test1→该方法→formal1的distinct8MiB已授权，尚未报真实结果；不以源级少一次编码宣称实际收益或改活P6。


## P6 自然失败揭示 memo 权重压力；继续核实际回放机制

P6-late于04:34:34.592905Z真实自然END，exit1/wall2708.3920787秒、0kill；retained exact HANDLE的exitFILETIME134392772742097234，原session30935真实终态保留。错误仍Lifecycle observation deadline expired，Win32Host115→Life165→Core707→Root View.loadReceipt181→DPS.replayCooldown495→CBJ.retainCapturedRead741/Core940。04:36:04末态 `P6-late/logs/RESTORE-EXITED05-TRUE-END-VERIFIED01.json`8757B/SHA `f6e692708b529441a25025f4a0d9eabb109d7c32cac7e9c204baf252adbd3b6e`：0ck3/ownedchild/claim，head raw100052B/SHA d8b37715…仍2002，numericWAL/sourcebindings各2002，原savedPair FileID/bytes/mtime原样，不重读87MB；四旧宿主同birth活，SCREEN freshCAS10467，旧UNKNOWN_EFFECT与quarantine不变，0新业务/READ/Driver/queue/SAVE信用。

新CAS acquired_retained10289/unretained0/fallback0，entry/byte/handle回退均0，peak10289/268435456B，实际私有16384/256MiB/32772。tier确已消旧句柄回退，不能据此授完整恢复或性能成功。finish_succeeded1仅Native finish(failure)返回，validation_failed1因callback截止firstFailure非空，非callback成功、坏件或close失败；stderr无suppressed close异常。

**DATA full242/hits28/unretained0/successful_publishes241，weight_evictions234、entry/membership eviction0；peak_entries33/estimated_bytes8384693/memberships10480，dependency_rejections0/weight_rejections0。** 这证明原8MiB权重压力，不证明被淘汰key会再次使用或调高一定有收益。parse Core slot4 completed0，evict73327（byte73220/entry108非互斥）、fullMaterial hit2045/protocol27970。stdout379B/2f10321f…、stderr11039B/a430f851…保原件。04:31:30现成Win32整个JVM user591.609+kernel39.078秒，main134.313秒；同一Thread.print的VM Thread485.250秒、C2Compiler10.641秒/C10.297秒，不把main当全JVMCPU、VM Thread全归GC或OSprivate当heap。

下一先窄读真实memo key/复用关系和已有cooldown前缀机制，不盲调权重：DPS DATA分支若miss调用replayOriginal(...,null,null)，会绕开已有OwnedPrefixAccess的已验证前缀复用；Root受限View目前只装DATA scope。核其能否对同私有Root actual/View/session/thread/fixedhead复用已有OwnedPrefix，同时保持完整header、原件/依赖trace、nested rebuild、最终aux比较和失败吸收。此为只读施工评估，尚未实现/增编/采用，也未认定主因；旧8MiB/128/32768继续保持。

局部CBJ编码候选actual1真实27.015895秒/23class绿；Test1 typing20.491547秒/12class，旧fixture37family复用0编。Test准备的两次firstorigin拒均0BEGIN/0javac，分别旧fixture路径覆盖及相同root重复索引，只修CP metadata。直接READ1实际75.345064秒1E，原BASE23/同Testbinary/CP对照67.482766秒同E，触发旧retainReadCapabilities guard（candidate804/base802，由741先调用，未达752hunk），保两XML、不授采用。formal1随后24.688087秒23class绿亦不作行为通过。真实fixture遗漏为第2批READ前仍用初始空history的capability_state_source，最小Test修为每批前真实collector→既有refresh/publishCapabilityInputs→退出后重collect READ；保原2+1及全部断言/生产guard，单叶重编及同1方法补验中，不重BASE/两生产族或whole11。


CBJ真实fixture修复后，Test1再typing17.069296秒/12class，直接capturedReadSuffix方法73.983154秒1P/0F/0E/0skip；XML `F/cbj119j1/fixture-repair03/reports/TEST-junit-jupiter.xml`48179B/SHA `60c16e03e8f6635f60b4a2ed37213c30b6b7915486531b5bea569c7a4827e262`。生产actual23/formal23不重、原候选75.345秒及BASE67.483秒同guard失败均保。只Test每批前用既有producer刷新与发布当前Driver绑定的capability，原2+1已发布READ和最终bytes/stamp/改row拒绝断言不变。局部编码生产1+最小Test1与五报告按独立7文件正常发表；软件通过不授P6采用或速度收益。

下一P0只读确认：memo key是immutable Obj完整结构值、access-order LRU，非每次唯一identity；28hit证明有同值复用，但无evicted-key-return统计不能断言升32MiB有效。另DATA miss确实replayOriginal(...,null,null)，绕开既有OwnedPrefix；原Native prefix刻意只accept真Native facade，不能简单改宽。最小2prod(DPS+Bridge)+2Test方案已授权source1MiB，使用已认证private Root source.openAccess的同RetainedDataReplayAccess创建私有prefix适配器，checkpoint不外露、无Native/decoder/write；同词法scope，miss在原完整outer capture内复用原replayCooldown算法，保每次header、cycle/frame/processed/final aux及anchor依赖再次verify，nested trace吸收全部旧依赖，任何replay/verify/traceclose失败同时清prefix与memo，capture/unheld失格仍全读。旧Native accepts、DATA128/8MiB/32768、CAS档位不变；未写/未编测/未采用时不报收益。

P6后实际8个Runtime roots Native93557344B，按下一hour keeper64MiB+两READ128MiB+tail8MiB预估303272544B>原256MiB，当前不授新phase。fresh物理55.064GB/commit70.954GB，扣source5+Game32+CI2=39GiB估算后仍有13.188/29.078GB，DusedUpper13309771223040加原other512MiB/meta2MiB仍在quota内。Root据真实存储缺口授权archive07一次，沿既有lossless/全部roundtrip和源二次身份内容核验后exact清理，仅closed age>=10min且非最新9dirs，输出/index/receipt aggregate<=4MiB/120s、前后fresh lease，0新fund/假unused退款；未发新Main/source窗，归档结果尚待。


## DATA 前缀接线必要七项通过；准备第六次独立恢复

CBJ生产1+最小Test1+五报告已正常FF发表 `c4cb56ab7d8a08270873e4e987d83bf94682c1e9`，remote exact/index空；PUB7为9528B/SHA `122f4e08a9bc6964f0ee471b1c97e22162c5f6f21ccccb58d5024a0c7d774bd5`。实际37个Git对象disk233653B超过初始Git192KiB guard37045B，已独立只补64KiB一次，使Pub208→272KiB保守关闭0未知退款；不把对象disk称FS净增或peak。CBJ完整软件闭档5957B/952e19c3…、finalhandoff2541B/8702cf02…，源2MiB/编测8MiB各只返真实unused139264/798624一次，旧失败/metadata拒原件全保。

D11统一Ready `J/root-data-owned-prefix-reuse-candidate01/SOURCE-READY-ROOT-DATA-PREFIX2-TEST2-7-01.json`6947B/SHA `c2fa92c30063eaabaa31c639b5c9f40e87503331d29d96cf2e9e869859f32b7f`：actual DPS55919B/1053498b…+Bridge57480B/0a2b8f06…；formal只Bridge57967B/2b20…另需typing，DPS rawexact复用。TestDPS37062B/04835b0f…及Root22370B/97158142…，2prod/2Test，原Native source/注册/accepts、Root/Store与memo128/8MiB/32768不改。

actual2于14.405100秒真实GREEN完整22class（DPS7+Bridge15，旧7+14被替代，不叠算），family `F/dp120a1/ACTUAL-ROOT-DATA-PREFIX2-COMPLETE-MODULE-FAMILIES22-01.json`13410B/SHA `520fb855955c44f135f361c63bf4d75355dc354044b4883f2d694c374c5d42ea`；Test2 typing13.619180秒9class。必要7新方法真实25.210370秒7P/0F/0E/0skip（application6+真Root CAS/frame1），XML `F/dp120j1/reports/TEST-junit-jupiter.xml`53569B/SHA `3c778025bc996121af9ed741040cd6c9b02fad456e003c5e91204f9b3c8796d4`。覆盖跨aux同prefix及扩展、完整header/最终aux拒绝、nested旧依赖吸收、traceclose/verify异常双清、unheld/capture全读退路与不借外层Native prefix；真Root fixture仍decoder/Native prefix accessor(View)为null、写拒。最后只读计数prefix_anchor_hits3/proofs_replayed5与CASfinish1是scaled fixture证据，不外推实际历史复用长度或性能收益。无旧15/135/Maven重跑、无source RED/preBEGIN拒，formalBridge1后补中不作Runtime准备前置。

Root一次读working完整DPS/Bridge差异：4参显式绑定及ownsPrefix防借/清外层，原outer DATA capture内调用既有回放算法，异常清memo和私有checkpoint、保suppressed，计数只在本DATA prefix实际anchor成功和proof处理时增长；旧3参null路径/Native注册body不变。所有actual资格一绿已直交Runtime；其预组111unique/177 CP roots（新CBJ23+DPS7/Bridge15及已核其它完整族），小件887447B/SHA `ae7e9baed26c094ed160f8fcfff5de36d7e17cb7b2d36e966a658f0b24efd403`不可执行argv_prefix，尚无source/cfg。Root在05:07后授权于实际签发当次UTC新建独立60min来源，旧P6原件不改；fresh0Game/claim/head/pair/keeper、physical/commit与256MiB阶段峰及Decider最终CP111/五wire通过后可一次BEGIN第六P7 public restore-exited，heap4GiB/ActiveProcessor1/45min观察包络及旧限额保持。当前仅准备，未有新Main或Game/SAVE信用，不等formal/Git/预算close。

archive07真实04:42:56.516198Z/18.227秒完成324files/81closed dirs、原logical47721554B全部lossless保留，tar471096B/51582113…+index128381B/4732e725…+receipt<4MiB；全roundtrip及源身份/mtime/content二次核后exact清理，最新9dirs/活输入原样、freshCAS10474，0新fund/unused假退款。fresh Native52,970,328B+fullhour64MiB keeper/128MiB READ/8MiBtail=262,685,528B<256MiB，margin5,749,928B只是当次；最终admit用fresh现量和真实剩余Review尾量，非套旧值/从logical推物理回收。

Runtime完成tools64 exact attempt无child/未来写入声明2436B/4f0f62e4…，原fund1838B/99b7f8ce…与quote2226B/b0e048b7…由Native逐SHA核，priorreturns0。保38267152B（dirguard28829968+m2 UNKNOWN8388608+closure1MiB），首次onlyunused28841712一次：raw1684002496→1655160784；闭档2927B/SHA `d3a23e38e547416e34ef8e51df69551b990a98a5177b185f698bcaee9f28a62c`，无物理回收/补造历史peak。D11 distinct6MiB随后fund，raw1661452240/normal24389632/余33822768，源1MiB独立。新后续build另fund不借闭scope尾额。保留170f Official43802085477继续取得首份完整后继，不因c4新push取消；c4 Official43805867697亦执行，尚无完整CI/Own绿色。


D11后置formalBridge1真实12.096506秒GREEN完整15class，DPS与actual rawexact7复用、0重复编；family `F/dp120f1/FORMAL-DATA-PREFIX-BRIDGE1-COMPLETE-FAMILY15-01.json`8122B/SHA `2b4f9a8c7504d68dd96c8497612157d862d568b1be4f83b20272e833b38aeaa1`。最终actual22、Test2 typing9、七项真P与formal差异15资格齐，未重旧15/135/整图，四源码/Test+五报告9文件正常独立发表，不等实际BEGIN。Decider亦独立读取CP111/六组ACTUAL/OUTPUTS、CBJ1P和D11真XML/精确7方法/ACTUAL0d78655f…，来源/首定义一致；group3旧说明文字含DPS7但实际只有Store18+Root4，真实新DPS7位于D11首定义，原件保留、最终资格明确superseded。仍待Runtime新source/cfg及fresh资源后一次真实Main，不能据软件/预组CP称实际装载或恢复成功。


## 第六次 P7 真 BEGIN 与前两资格范围

D11四源码/Test与五报告已正常FF发表 `7c84876b45a3604669e394abed767261e7cdf188`，parent c4cb56ab、remote exact/整树clean。PUB9为11878B/SHA `897e05e964b9cbf47017555224010a68b1646cb4c1ff19a8c5d47ca249895499`，实际56新对象disk164603B在Git256KiB guard内，非FS净增/peak；Pub272KiB保守关闭0未知退款。完整软件闭档 `F/dp120a1/SOFTWARE-CLOSED-ROOT-DATA-PREFIX-ACTUAL22-TEST7-FORMALBRIDGE15-GREEN01.json`6688B/dce85b65…，finalhandoff3033B/b8b25015…；source1MiB/编测6MiB各只返unused434176/2790176一次，最新raw1658506416/normal24389632/余36768592，本波0未来hold。

archive08于05:17:10/10.792秒真实完成192files/48closed dirs，原logical28280384B无损保留，tar329684B+index84566B；全roundtrip+源二次身份/mtime/content核后exact清理，fresh lease10497，0新fund/假unused。选中NativeAlloc28664704不是净物理回收。基于fresh真实超256MiB峰，Root后续同流程站立授权仅在current+实际剩余Review keeper尾+128MiB READ+8MiBtail超原cap时维护，最多每10分钟一轮、每轮独立编号/完整验与receipt、只closed age>=10min且非最新9dirs、输出/index/receipt<=4MiB/120s、不碰活输入/别的路径；目标消超额加最多8MiB余量，不能循环无条件清理或借闭scope尾额。

**P7第六次同savedPair public RootOrdinaryWorkerMain restore-exited于05:24:44.605268Z真实BEGIN**，JVM185724/birth134392802846079027/session46585。主root `D:/ck3-state/resume91-runtime/samepair-restore07-20261116`（以下P7R）。BEGIN `P7R/logs/RESTORE-EXITED06-BEGIN.json`28103B/SHA `d02701233c27bef9cfe06ceb6e1fada5133453ea467d4c2c2ddc40dde6a08d9a`。新独立来源实际签发05:18:45→06:18:45，旧P6期限/动作不改；45min约06:09:44为观察检查点非强杀timer，sourceheap4GiB/ActiveProcessor1、CAS v1/memo8MiB旧限额保持。

三公共输出05:19:49全exit0，索引 `P7R/input01/PUBLIC-THREE-OUTPUTS-FINAL-SOURCE01.json`1781B/SHA `800520b7cd8e53cb0b07b49a8d57477fb3e70338a6d42ff82f10f41dacdc4c08`；FrozenSaved05:21:54 exit0。prepared `P7R/input01/PUBLIC-COLD-WORKER-ENTRY-PREPARED01.json`890924B/SHA `1a3131cd9a375dba2038a0b728c8b21117e33d952ab92814f10e60214fa37e11`；cfg2096B/SHA `d91d48abacdd5aa93934ef6111125ead40879a183491c8bf3b9323046961f5ca`，原file queue01/codex-session/120000/1/0；plan5165B/SHA `5491a5b939ffed22634d1612602599040151862413c029f4f00f4b42c35f8a22`，均在P7R/input01。Decider独立差异核177roots/111首定义及真软件资格，恢复唯一真实响应，未预填/HTTP/刷新原请求deadline。

05:24:06 fresh0Game/claim、head2002/raw d8b3…、原savedPair FileID/mtime与keeper租约全部通过。Runtime Native61305376+真实剩余Review keeper62914560+两READ134217728+tail8388608=266826272B<268435456B；provider64MiB/firstSAVE未预授，后阶段须按实际READ量核。physical/commit扣source5+futureGame32+CI2=39GiB估算后余15.833/32.078GB，Dquota通过；不把估算称RSS硬上限。

初始scope05:27:49、material scope05:29:23均真实finish1/validation0；publication167791/135318、fallback49866/29822全entry_bound，原1024/64MiB/2052，parse slots2/3 completed1且0evict。05:33:01/elapsed497.06秒仍Core940同战役历史、取样ContinuityState.toJson/ScopedHistory.edge，IO10.670GB/997910reads，OSprivate2.377GB非heap结论；新DATA/prefix末计数NOT_HELD、stdout空/templateonly、无真END/Game。仅确认实际装载与前两阶段，未据此授整体收益、READ/Driver/OODA/SAVE或有限秒/保存日。

完整CI保留170f43802085477已到Java整链阶段，最新7c43808836914执行；Root只请求取消中间c4 43805867697，取消不算通过。Java另接真实P1：旧run过Tools后缺postqualification实际产物，窄读发现外部D的Own24c源码不在repo且硬STANDARD8，与新Tools12M不兼容；真实expired历史完成件、genuine G2 capture-only/NOT_RUN和quota拒绝也需诚实供应。只读寻找显式新版consumer及现producers闭环，不降门/塞fixture/修改P7；完整Official/Own仍未获绿。


P7现成BEGIN/prepared/cfg/plan/公共三产物/FrozenSaved/最终phase绝对路径机器索引：`D:/ck3-state/resume91-runtime/samepair-restore07-20261116/logs/P7-ACTUAL-BEGIN-FROZEN-INPUTS-EXACT-INDEX01.json`2236B/SHA `1578eef41cb4ac61478f00de432c1f45874d1b6f29721da145096e0e148dd3a8`；只汇已有FileRef，未新增OS/Game查询或收益资格。


## P7 历史范围首次完成；真实 CAS 调用者上界修复

P7于05:44:31.440951Z真实自然END，exit1/wall1186.8357386秒，exact HANDLE exitFILETIME134392814710956667/session46585，不是45min超期、0kill。**Core历史DATA范围05:43:34真实callback成功**：full254/hits28/unretained0/scope_callback_succeeded1、prefix_anchor_hits249/proofs_replayed110、weight_evictions247；CAS publication418062/held406753/retained11309/fallback0，finish1/validation0。已证明新机制在实际历史使用并使该范围完整通过；此次同时采用局部encode和prefix，未做单变量因果比较，亦非整体恢复/Game/保存成功。

随后第一次实际到达的错误为 `ContractViolationException: finite immutable artifact bound required`，Store.limit897→readOriginal808→Native.readArtifact807→Core.ColdRestoreSource.requireOriginal855→requireCurrent859→qualifyColdRestoreSource955。stderr7034B/SHA `0ecc404eb9c90e080975ceabcab110abde4d9840f0a589aaad8c2ab72b307106`，stdout416B/a64c3b7…。外层parse.completed0是后续bound异常导致外层callback失败，与已成功的内层DATA/CAS分开，不称close失败或坏件。末态 `P7R/logs/RESTORE-EXITED06-TRUE-END-VERIFIED01.json`8478B/SHA `5cf94bd748ac3a1bb1093a6140bbbc66818670944dfb3a301181ed26814be722`：05:50:44真实0Game/ownedchild/claim，head2002/raw100052B d8b3…、2002numericWAL/sourcebindings、原save/driver FileID/bytes/mtime全不变，四旧host同birth活、keeperCAS10526，0重复save读取/动作或新日数。Decider05:52:48核queue absent/0requests/0responses后按协议结束watch，下一独立source再followup。

新的OtherOps诊断只读已有原件，不凭单帧判根因：P6 elapsed770.21秒CPU86.421875秒/Other23299286/read1027979/11528559569B；P7 elapsed863.04秒CPU79.828125/Other35040349/read1065542/12475994921B；P6 upper1057.78秒CPU130.609375/Other27755895/read1132311/15835134396B，无等时/等阶段对齐。源核Store dep loop前后requireActive，中间每ref metadata lease.read/payload.verifyCurrent及archive目录stamp；不能省各ref身份，Writer/WindowsLock/NoWrites为内存/ThreadLocal检查，不误称每ref Win32/读头。未证明目录持续custody/异常窗口等价，停止扩优化，转修本轮明确caller错误。

真实caller两处均在Core.ColdRestoreSource，错误把物理DriverCheckpointStore.MAX_DRIVER_BYTES=256MiB用于上游RawJson.fullMaterial的64MiB CAS原件。唯一包私有pure-byte helper改为 `min(RawJson.MAXIMUM_BYTES, ImmutableArtifactStore.MAXIMUM_ARTIFACT_BYTES)`，两原调用经helper，原全部session/head/material/deadline guard、完整bytes/encode比较与顺序保持。物理checkpoint256MiB、Store64MiB及历史其它limits均不改。只读发现同形的RootCanonicalDriverCoverage39属于旧Resolved迁移路线，current无实际caller，未扩改该类/Prisoners。

actual源337699B/386a08bf…→338142B/7d4b31a9…，formal344786B/81ef…→345229B/594c798b…，原7087B差异保全。新source2MiB独立fund06291e80…，actualCore1首编6.417199秒RED/0class为旧Tools JAR Manifest隐式lib/lib五个不存在alias触发-Xlint:path/Werror；显式P7原177CP本来有五个真实JAR。只在该轮javac排除path lint，保其它lint/Werror、原177CP和源不变，不造别名目录/改JAR；五真实JAR逐pin/首定义小件9352B/7a61bfd1…，原RED保。

actualCore1随后24.071355秒真实GREEN完整34class（旧R34被替换不叠算），`F/cas121a1/ACTUAL-COLD-CAS-BOUND-CORE1-COMPLETE-FAMILY34-01.json`17182B/SHA `282d9f5d27873ebb1410d1f985e85b9ad5c7c0e150563e2c6ba165be5e3a6ae9`。旧er97cold1曾为partial phase但所产34与R安装/本P7实际CP38逐SHA一致，不把旧partial冒整体绿。新Test3868B/e6e1b5c… typing13.683741秒，真实CAS角色1方法15.125632秒1P/0F/0E/0skip：合法>128KiB完整Driver正例、错bytes/SHA/超64MiB roleRef/物理tamper拒绝，无64MiB大分配或反射伪Core许可。XML `F/cas121j1/reports/TEST-junit-jupiter.xml`31474B/SHA `a00a1aed37d6aae460e9671cf1ff031837431203dc95ca8abca096ca430fdb7e`；实际资格1376B/SHA `cc2dcffa49bf1058f9d84872024bf9cbe8e9bf75fb77ac3b2109695d18c16320`，已直Runtime，formal1仅后补中。

Runtime预组CP145/178roots，`P7R/logs/NEXT-COLD-WHOLE-CP145-CANDIDATE-PREPARED01.json`1206490B/SHA `22d8c22838f0f343b5b82142456ba8452f0ac7c61e6525b5c1684dff18d7a842`；Decider独立核新34首位及原111逐rawpin全同、源码/实际编译资格一致。Root在真实CAS1P后授权下一第七P8：真实当次UTC独立60min新来源、公共输出/原pair/head/0Game/租约/物理commit和阶段容量/finalcfg差异全过后一次public restore-exited，旧P7不重跑，heap4GiB/1CPU/45min观察及全部限额保留。当前无新source/Main/Game，formal/Git/close不作运行准备前置。

真实完整Official run43802085477（170f）已结束失败，但bootstrap/qualified Tools分别163XML/**1229P/0F/0E/0skip**，两份ControlCiStageTest26及Tools12MiB11均全P，证明夹具修复后实际整类通过；后续exact NoSuchFile为tools-postqualification/actual.json。artifact14199902972/1133541B/SHA `60d54cc29c126649ac4872befd91f43d1480a483b6ec8f705ca4dde26c81f1b8`有界内存读取无ZIP落盘，汇总 `D:/ck3-state/resume91-root-ci/OFFICIAL-170F-TOOLS1229X2-POSTQUAL-MISSING-SUMMARY01.json`1926B/SHA `98f37246e6dffd3d73ad711b66a0c74a8f4e80eb3d4090f8510421cdd605155a`；仍无fullCI/Own绿色。

CI可施工新版方案独立source2MiB已fund09595503…，根 `J/hosted-tools-current-own-v2-candidate01`，在P0必要1P后开始，不与Core/Test混stage：repo-owned新Own test-source及明确v2输入/当前R8 capture-only、真实历史A/C与fullTools B、原正lease和genuine低subquota负准入+真实public CLI/0Maven拒绝原件、完整当前源projection/真产物>512，而非占位或冒旧CI-bug同card双判。原短lease必须原完成时有效，再自然过期，不回填；显式新CI有限window/profile，旧90min/v1/24c保持。复用既有Job/UTF8/ControlBuild/postqual链，无新runner/Python；离线16MiB只prospective，首次actual须hosted真A/C/B/Own/JUnit2，不能由小fixture授完整Own。当前caller6MiB独立，CI编测未BEGIN。


Caller修复后置formalCore1真实19.487734秒GREEN完整35class，源345229B/594c798b…及原7087B差异保持；family `F/cas121f1/FORMAL-COLD-CAS-BOUND-CORE1-COMPLETE-FAMILY35-01.json`17172B/SHA `e015095ed29d4ce57c289b2cf43e60937d1e69c7fd4395d5cfb34ca2b368ca52`。正式CP独立且all,-try/Werror原样，无-path例外；局部path排除仅此前actual旧Jar隐式alias环境。最终actual34+真实CAS1P+formal35软件齐，生产1/Test1+五报告7文件正常独立发表；CI新source/工作叶另包，不误stage，也不以发表挡Runtime下一独立source/实际恢复。
