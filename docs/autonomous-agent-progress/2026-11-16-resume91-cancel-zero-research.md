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
