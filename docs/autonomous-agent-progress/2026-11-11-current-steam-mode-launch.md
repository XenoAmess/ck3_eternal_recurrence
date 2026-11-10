# P0：按本次授权保持 Steam 当前模式启动原版存档

用户明确要求“我要求你这次不进入离线，直接开启ck3”。本单元增加显式 `GameSupervisor current-steam-mode configuration owner-directory authorization.json`，普通两参入口及 `run(Path,Path)`、`launchNew/launchSaved` 仍走原 offline 观察和消费路径。当前模式入口只允许 SavedGame，并绑定本次 request/session/machine、原 Steam PID/birth/exe、原始选中 save、用户原话与有限账号会话证据及精确 deadline；不改变 Steam 模式、不操纵其窗口或其它游戏，不把有限未见冲突写成全远端无人占用，也不伪造 QualifiedOffline 或 online 证明。

生产源码仅四叶：GameSupervisor、JavaGameLifecycle、ManagedGameSession 和新增 CurrentSteamLaunch。新 Authorization 只是数据声明；真正 QualifiedCurrent 私有构造由 live producer 持有原 Steam 只读 HANDLE后发行，CREATE 前10秒墙钟/单调时钟时效和一次消费，消费原件 CREATE_NEW/readback/flush。原 Saved 准备、唯一 CREATE、挂起注入、HELLO、Job owner、UNKNOWN 与清理路径共用，没有复制整套生命周期或全局 property 逃生门。同ID换模式/授权源返回 UNKNOWN，不重放。Managed Owned 的两种资格严格二选一、Attached两者皆空；旧 Owned9参和 Attached8参二进制构造签名保留。旧 Owned传null资格现在拒绝，这是非法输入收紧，不宣称全部非法输入行为不变。

Source01 新 reader误沿用 strictMapper 的 SNAKE_CASE，与实际约定的 camelCase不符；Source02只在该fresh mapper copy显式 LOWER_CAMEL_CASE，保留重复/未知字段、primitive及coercion等严格规则，全局mapper与原Runtime授权数据不改。新类10606B/8df9dbe5…；三个旧叶分别13558B/0bb6bf9a…、34374B/ff722552…、19829B/a0ae5846…。requireLoadedClass是现有兼容hook，不把它当作真实代码来源验收。

首次必要4TU编译实际RED：正式Lifecycle已有两个 startBefore 调用，而原Runtime224的 WinJob无此API。原失败/partial产物保留且未live。修复只增编HEAD既有 WindowsJobProcess.java（89859B/3edabfea…）作为必要第5TU，不改它的源码、不退回旧start削弱CREATE/主线程恢复期限，也不全树重建。第二次5TU实际0/CLOSE，完整65类=Current3+Supervisor6+Lifecycle16+Managed5+WinJob35。新WinJob保留实际Game所需旧API，但没有旧startIndependentOwner及其两个独立启动专属类型；首次真实BEGIN前发现并保留错误预案，实际 Launcher JVM专用原224，只有它启动的 GameSupervisor child使用新65前缀+原224。不能称新SDK对整个旧224全部二进制兼容。

必要纯DATA测试直接读取原真实1342B/60a7ecb3… camelCase授权wire，再做目标正例、错request/deadline等12项；实际12通过、0/CLOSE，没有调用Steam/Game/live issuer或伪造资格。正例使用原 issued窗口内时点，不冒当时实时许可。共四个软件JVM：首4TU RED、必要5TU成功、测试1TU编译、DATA执行。actor合23.355678600026295秒嵌在operator合29.494130000122823秒内，不能相加或充当完整耗时。Native前核→DATAclose998.003184秒→final1162.057389秒，Source01→824.185600/988.239805秒，Source02→585.324811/749.379016秒；更早开始UNKNOWN，所有准备、重试修复、错误与等待保。final写后两metadata根1778941B，非连续峰值或Java堆/JNI峰值。

原17:16准备请求没有BEGIN/consume，放弃件与原17:46期限保留，未刷新旧命令。运行岗另立真实新request/session `resume91_currentmode02_20261110T174228Z`，精确deadline18:12:28.795205Z和新auth02。launcher 17:42:29.053081→30.553818 UTC exit0只证明launcher返回；17:42:35.301902真实 GAME_OWNER_READY：Game143600/birth134388061530438310，独立keeper86768/birth134388061498702292，Native HELLO6065B，启动pipe已释放，Steam模式变化0。实际模式消费977B明确CURRENT_UNCHANGED_NOT_QUERIED/offline_qualification=false/remote_absence_or_online_proof=false。软件DATA12与这个真实issuer/CREATE分别验收，不将测试当运行许可。

两次原Core负结果完整保留：17:43:37 application_main_not_ready，17:46:31 application_main_executor_unavailable，均UNAVAILABLE且当时无map/actor/date。后到17:50:24.042447→27.925224原Core9075B/9078b6c4…明确map_ready=true、actor31254存活、date53168040、paused=true、speed5；这只授当次地图切点。后继Java-only交接由运行岗另账，17:52旧Dev宿主实际END3221225786与原delegate END0分别保存，不伪clean host；新Dev启动、LOOP、Quarkus热替换与SAVE未由本文授予。新SAVE为0，不借旧累计日作分母，秒/新增保存日没有新有效数值，10秒目标未达。

主要原件：N=D:/ck3-state/resume91-native-integration/current-steam-mode-p0-20261111，J=D:/ck3-state/resume91-java-delivery/current-steam-mode-launch-p0。

- J/source01-owner/SOURCE-READY01.json，1971B/25663f7b…；J/source02-owner/SOURCE-READY02.json，1908B/27d53429…，只camel-case读取修正的inverse/diff与Source01原件保留。
- N/RUNTIME-READY-ACTUAL65-DATA12-AND-OLDABI01.json，9831B/11bac7e5…；N/ALL4JVM-REPAIR-DATA12-COST-DELIVERY01.json，15633B/f336caa8…；所有软件错误/原记录和代价不删。首writer数close调用3误写而实际2的写前断言工具0.7308894秒，02只纠正计数成功；模型误报未据此改源码，模型审阅不充验收。
- Runtime `current-resume268/manual-return-currentmode-20261111-attempt02/physical-owner-currentmode02/owner.json`及ACTUAL-LAUNCH-BEGIN/END268，绑定真实launcher/keeper/Game/HELLO原件；消费、HELLO和launch事件位于 `D:/ck3-state/ck3-java-resume91_currentmode02_20261110T174228Z/artifacts/native-launch/`。
- 原地图证据 `D:/ck3-state/resume91-runtime/manual-return-20261111/newworld-core-20261110T175024Z/originals/summary.json`，9075B/9078b6c4…；J/SOFTWARE-AND-ACTUAL-CURRENTMODE02-MAP-CUT01.json固定上述切点和来源，不新增查询。

正常发表仅四生产源码与本文、daily、W46；WinJob是既有HEAD源码的必要增编债，没有伪造该文件Git变更。D:/r64d、活跃source307、原账本/UNKNOWN/P100/Guard/parser/hash/oldencode不改，P221仍0measure。Git、软件、实际新Game启动、地图、业务LOOP和保存分层，发表不是实机恢复前置。
