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
