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
