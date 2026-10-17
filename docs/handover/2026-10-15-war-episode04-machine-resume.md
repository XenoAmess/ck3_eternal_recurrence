# 战争四期：本机恢复与 Review02 前置

> 最新切点（2026-10-15T13:16Z，machine_id `desktop-3fevhd2-1c74096080`）：
> R0173完成22个精确自然日，取得登船实付3金币源链和未锁定Halt次日仍停原处；研究整卡 **3/14＝21.4%**。
> R07同T0无登船对照仍缺，维护费仍unclosed。新增360秒原片全片解码通过，Halt发生在片尾之后，不能算Halt入镜。
> Review02全文/TTS/重剪 **0%**；旧Review01成片与交付保留。游戏正常exit0，保存与屏幕释放已完成。
> 便携原件、生产消费者重算命令及实证边界见[本轮研究结果](../ck3-native-ai/episode04-r0173-boarding-halt-12004.md)。下文保留各历史时间切点。

本记录的 `machine_id` 为 **`desktop-3fevhd2-1c74096080`**，由 `tools/ck3_live_run_id.py machine` 实际取得。2026-10-15 的本轮工作根为 `C:/ck3-e04-resume-20261015-a01/`。以下安装、容量和桌面事实仅属于这台机器；其他机器复用代码与知识时，重新取得自己的身份与实际读回。

## 版本与现场

- 更新前本机仓库为 `9fbeabad1c4435bf16f79b8714e5078885daf5b1`；已通过 fetch/rebase 更新到远端主线。中途磁盘满导致的失败已保留回执，恢复后正常完成，没有 merge 或强推。
- 2026-10-15T06:52:20Z 的本机 skill `inspect` 读到 **CK3 1.20.1 / Steam build25870654 / public**。实际游戏目录为 `C:/SteamLibrary/steamapps/common/Crusader Kings III`，客户端在 D 盘。不能据其他机器的回退记录宣称本机已经是 1.20.0.4。
- 07:04:41Z 本机缓存列表确实列出 `1.20.0`，其说明为 `Old Version 1.20.0.4 (Crozier)`；实际选中项仍为默认公开版。缓存列表不是当前服务器可用性证明。
- 07:37:07Z Root 实际审阅本机新桌面：下载页明确显示 Steam 离线模式，画面时钟为15:37。**本段记录时尚未上线、提交版本切换、完成下载或启动新实机。**
- 目标 tuple 为 **1.20.0.4 / build25734779 / EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`**。它是待验证目标，不是本机现有 EXE 的验收结果。

本机证据：工作根下的 `steam-inspect-a01/result.json`、`steam-list-cached-a01/result.json`、`steam-downloads-offline-a06/{desktop.png,uia.json}`。历史 [skill 切换资格](../../skills/steam-ck3-versions/references/qualification-2026-10-15.json)缺少来源机器身份，已明确标 `machine_id: unknown`；原始成功事实与证据 pins 保留。

## 拍摄入口已修的具体故障

旧 [capture_bootstrap.py](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/capture_bootstrap.py)固定要求 1.20.0.3；仅换新 DLL 无法准备 .4 拍摄。现增加显式参数：

```text
prepare --expected-game-version 1.20.0.4 --expected-character-id 29829
```

其余必需路径参数仍按实际 `prepare --help` 提供。新 .4 准备及载入核实际安装版本、Steam build、EXE hash 与完成状态；录制开始核原生 adapter、实际玩家 Robert29829、同一 PID 和 connection generation。新 prepared、环境和本入口执行回执带 canonical machine ID，.4 prepared 不接受缺失或异机身份。历史 .3 prepared 不改写，也不追认所属机器。

外置候选完成16项原版本守卫检查及8项机器身份增量检查；Root 应用后实际验证顶层和 `prepare --help`、`git diff --check`。这些是代码/CLI 验证，**不代表本机 .4 冷启动、录制或业务研究通过**。

公共原生 frontend 已有 .4 Robert 入口；新生产构建须同时启用：

```text
XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1=ON
XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1=ON
XAR_CK3_FEUDAL_1066_TARGET_ROBERT_V1=ON
```

不能沿用旧 a08/.3 DLL 的资格。构建复用 `tools/run_native_msvc.py`，三个目标为 `xar_ck3_bridge`、`xar_ck3_bridge_injector`、`xar_ck3_bridge_host`，Release、jobs16、`BUILD_TESTING=OFF`；实际编译、精确路径 Defender 登记及新原生 hello 另行结算。

## Review02 仍要取得的结果

已有 .4 exact-day sentinel、loss writer/supply callback journal、regular-core 自然阶段及完整队列查询代码应直接复用；既有来源或他机资格不抵扣本机新观察。`observed_history_full_v1` 才包含相关历史族，默认查询缺事件不能解释为没有损耗。

本机新版研究与拍摄尚未开始。顺序为：版本完成并恢复离线 → 最小运行时资格 → 至少10个真实单日采样 → B 的1/1/统帅微实验 → 围城、县界、饥饿及补员的实际执行与完整整数 → Halt/改道及真实后果 → 登船实际支付与维护结算 → 同一新T0的完整 A/B/C。费用率和钱包净差不能替代实际支付，旧 B 中止及 C 两日采样偏差不能追认为合格比较。

新案只用 Robert29829 原普通战役；旧 William/.3 片段如引用须独立标清主体、版本和历史范围。核心主张闭合后才写长配音及重剪，不用“未确认”口播继续承担主片结论。人工1×完整观看与 signoff 仍是独立交付，不能用机器审计替代。

## 容量与工具输入

按统一存储策略已回收本机部分旧派生、重复副本和三段已释放用途的旧 .3 原片，保留关键 PNG/native 台账；三段原片不可重建，连续像素历史及重新抽样能力已失去，不能写作被后继录像完整覆盖。精确可用性及删除结果在工作根的 `capacity-lane/`、`story-lane/`、`d-raw-dedup-lane/`；计划量不算实际释放量。

07:31:45Z 的 C 盘获准项目根盘点完整、unknown0，逻辑占用153,148,384,783B；空闲36,186,443,776B。该时点固定 OneDrive 项目目录仅做本地 metadata/NO_RECALL 读取，未读正文、下载、改同步或删除云文件。新重型写入仍须按卷由 Root 串行登记峰值、系统增长、安全余量与限期配额例外；不把 C 盘余量当 D 盘余量。

07:26:03Z 实际查询独立工具链最新正式 GitHub Release，仍为 `v0.2.1`，wheel SHA-256 `f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621`，与仓库 requirements 一致。本机选用 `tools/.venv/Scripts/python.exe`，Python3.14.7，实际 `xar-promo --version` 与顶层 help 通过；尚未创建新版 render run。外置 `promo-release-probe-a01.json` 保存此次查询，后续新 run 仍按届时正式最新版本复核。


## 2026-10-15 R0171 实际运行、采样与退出追加

本节更新前文较早“尚未开始/目标尚未安装”的时间截面，机器仍为 **`desktop-3fevhd2-1c74096080`**。本轮现场读取与原生构建来源冻结于 `4c16cec6e2b4ecd0f12faa5c0f23237a7bd01843`；现场结束后 Root 已 fetch/rebase 最新 `origin/master`，本追加读取点为 `111e09b98e2290e9b67a480b39c451cebb774cf2`。仓库更新不代表新的 DLL 已构建或部署。

### 本机版本与正常 Robert 身份

本机已经实际完成 **1.20.0.4 / Steam25734779 / EXE `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`** 的版本切换，并于08:16:26Z恢复Steam离线。本轮 R0171 是正常1066 Robert战役，稳定人物来源为 `bookmark_rags_to_riches_duke_robert`、历史人物1128／`d_apulia`；本场实际 runtime FullCharacterID 是 **31254**，不是前文启动前猜测的29829。历史ID与runtime FullID不是同一编号，31254也不能直接搬给另一台机器或下一次加载。

身份由原版书签来源与普通Start控制流、008/009/010独立本场读回、011正常保存及其有限头部共同支撑：游戏PID13664、Python owner7404、connection generation1、episode `native-31254-2b025c67832d`。缺失的独立selected packet、未解析的first_name/birth/history人物record保持原边界，没有制造这些字段。旧prepared的expected29829与超时回执原样保留。依据：`steam-switch-12004-a01/tool/result.json`、`STEAM-VERSION-OPERATION-COMPLETE.actual-a01.json`、`robert-runtime-identity-a01/actor-identity.actual-a02.json`。

Root在同一PID实际采用Python身份guard与有限侧存配置，未因纯Python修正重启CK3。09:20:46Z guard APPLY成功，09:28:55Z独立READBACK成功；旧prepared摘要前后相同，start dryrun正确绑定31254。第一次READBACK在APPLY完成前执行而失败，旧侧存APPLY也曾在变更后因remote命名空间无`__file__`写回执失败；两者及随后成功读回均保留。当前热修只授这个已证明runtime，不自动成为未来冷载证明。旧外置bootstrap候选还发现“run前就pin尚未生成的新PID proof”的时序阻塞。a02外置修正已通过一条新增离线聚焦测试：run仅冻结预留绝对路径，在真正recording start时才pin并验证本场新proof；尚未授未来实机资格。依据：`owner-guard-hotfix-a01/{APPLY.actual-a01.json,READBACK-FAILURE.actual-a01.json,READBACK.actual-a02.json}`、`owner-python-hotfix-a01/READBACK-FULL.actual-a02.json`、`python-bootstrap-fix-a01/ROOT-DELIVERY.actual-a01.json`。

### 已完成十个精确日；归因账仍未通过

同一场景累计取得 **10个连续speed5真实日**，raw **53144376→53144616**；逐日均为+24，sentinel generation3→12、零overshoot并实际暂停。采样经过三个脚本attempt；只读status拒绝或侧存失败后保存失败、读取实际已暂停端点再续，不重复resume，不回档重造。09:39:06Z终态为`clock-pilot-complete`。

| 数据范围 | 实际结果 | 可授结论 |
|---|---|---|
| 第1日 | 完整Driver JSON 7,698,734B；原军18为1096/1096、集结剩3日 | 该日完整结果保留，非原始pipe字节；不是因果损耗/补员通过 |
| 第2日 | 完整Driver JSON 20,597,691B；1124/1124、集结剩2日 | 实际已暂停端点经只读恢复；不把恢复读当重走一天 |
| 第3日full尝试 | 32MiB侧存总预算不足，留下约4MiB partial；JSON不完整 | 原失败保留，不算第三份完整结果 |
| 第3–10日 | 8个`ordinary_core_v1` compact结果；第10日1196/1196 | 只授时钟、人数和当前字段；不包含完整历史族 |

第1日至第10日端点人数 **1096→1196**，后段原生画面与状态读回已显示集结完成。它是本场集结过程中的人数变化，**不是已归因的MAA自然补员或损耗执行闭环**。完整loss/refill cause ledger仍为0 qualified；当前损耗getter0、完整JSON保留、计划校验或fixture PASS均不能补这项信用。早期limit0导致的完整旧结果不能从MCP摘要复原；query3虽保留766632B完整结果，也没有可恢复的U18 matching loss/supply事件。依据：`live12004-robert-a01/exact-daily-pilot10-a01/day-01.actual.json`、`exact-daily-continuation-a02/{day-02.actual.json,FAILURE.actual.json}`、`exact-daily-continuation-a03/{day-03.actual.json,…,day-10.actual.json,RESULT.actual.json}`；三处日目录均在`live12004-robert-a01/`下。早期单日`EXACT-DAY-SPEED5-PILOT.actual-a01.json`仅是旧切点，不覆盖本节十日终态。

### 本轮原片与正常保存

唯一录像已经正常结束，FFmpeg返回0、recorder Job进程0。文件为`live12004-robert-a01/raw-gathering-pilot10-a01/raw.mkv`，**1,340,528,561B**，既有SHA **`57960c02be49f27a2c3f868245141f24f819a44ffabbbcca57da332c59a26b28`**。实际ffprobe9.0.1读到 **482.866秒、2560×1440、30fps、单H.264视频流、无音轨**。六张JPEG只抽代表单帧，没有全片解码/PTS审计或连续clean认证；Root已直接看过结尾1196集结完成，其余五张未逐张审阅，人工1×完整观看与signoff均未完成。SHA沿用Root既有来源，本次抽帧未重新哈希原片。依据：该raw目录`result.json`与`capture-media-audit-a01/{probe.actual.json,ROOT-DELIVERY.actual-a01.json,06-ending.jpg}`。

离场前046正常保存成功：`state-a02/profile/save games/xar_checkpoint.ck3`，**68,761,349B**，SHA **`b4b0acd0d5e79b0f3f087c85b15be65f3b8aab7a6b70bfee944a13bc5f87fb40`**，raw53144616、actor31254。原始正常开局immutable seed保留，不能把后续checkpoint覆盖说成初始seed被替换；新checkpoint尚未做冷载验收。保存证据为R0171的`responses/046-checkpoint-after-pilot.json`，原始seed来源见身份a02回执和`responses/011-identity-save.json`。大保存文件未为本追加重新读取或哈希。

### 现场已退出并释放

最终通过原生界面的桌面退出确认结束游戏；09:54:44Z，预先保留的原PID HANDLE signaled且exit0。随后受管session于09:54:45Z正常结束，实际 **5025.564秒、restart_count0**，Job在任何termination前已为0且final0、tree_gone/cleanup_proven，SDK线程和keeper均停止。09:58:02Z任务总线CAS **5325→5326**、DONE、resources为空；09:57:12Z桌面已恢复 **1024×768**。这不外推为typed native orderly-exit动作已合格；早先WM_CLOSE等待仍未退出的回执保持失败/未完成状态。依据：`stock-normal-exit-a03/observer-result.actual.json`、R0171的`session-result.json`和`bootstrap-result.json`、`capture-display-restore.actual-a01.json`、`bus---expected-cli-sha256-latest.json`。

### 尚需完成的工作

付款观察器只完成本机离线连接fixture **202项native检查＋68项独立wire consumer检查，失败0、实际game调用0**。最新fixture为外置`C:/ck3-war-episode04-research-20261004-a01/payment-observer-qualification-20261015-a01/build-a09/`，总交付在其父目录`ROOT-DELIVERY.actual.json`；它不能证明新生产DLL已部署、真实登船已经付款或maintenance cadence／applied military component已闭合。Python控制入口也只是外置candidate与聚焦离线PASS。

下一现场先完成必要源码整合和相应全量生产构建／Defender精确输出登记／新hello，不重复已闭getter。修正未来proof在recording start才pin的时序，并对新的PID/episode取得实际正常来源绑定；旧热修receipt不跨冷载继承。历史导出需要真正启用对应自然阶段采样、及时drain，并在有限预算下保全当前所需主体与事件，不能以默认compact缺事件推“没有发生”，也不能因两天已耗28.3MB就无界扩大侧存。

核心研究仍按现有R03–R13完成：围城/县界/严格S<10饥饿的实际physical debit、自然补员ADD及合法开关、分合军特殊record/统帅来源、未锁Halt/已锁Halt/改道、真实登船付款与维护结算，最后新T0完整A/B/C。十日clock通过不抵扣这些结果。已写好的69段改稿映射仅是离线编辑工作；Review02全文、TTS、重剪、成片核验与交付均未完成，不把本次原片当Review02成片，也不重复用“未确认”撑主口播。

### 完整侧存引用的可复用修正

`ck3_autonomous_player/src/xar_autoplayer/bridge/army_query_history_reference.py` 只按当前成功summary中的精确引用读取，核对文件字节数、SHA、query sequence、snapshot和revision；不以目录最新文件替代，不读取失败partial。2026-10-15T10:13Z在上述机器实际运行可移植聚焦回归：真实有限预算writer先成功再产生partial，失败summary在打开文件前被拒绝，早先成功结果仍可读取，**1 passed**。这是本轮误读partial的修复，不补发任何历史采样资格。

## 2026-10-15T10:18Z 观察器与拍摄入口整合

机器 `desktop-3fevhd2-1c74096080` 上，Root整合了显式family采样控制、[实际付款调用链与被动观察器](../ck3-native-ai/war-payment-passive-12004.md)、完整Driver结果回执、Robert稳定来源意图及录制start时才pin新runtime proof的入口。侧存默认仍0，可显式选择最大512MiB；这不是给旧run扩容，也不是容量准入或已完成24日归因。

10:18:55Z实际主树聚焦验证 **5 passed**：proof后发布、512MiB边界、真实Driver/MCP的family控制接线、compiled-payment样本consumer与默认现金查询兼容。旧现金测试另8项通过；Root新写的元数据断言曾误访问空annotations，修正后只重跑该失败case。原有202＋68 native fixture不重复执行，完整生产DLL编译、冷载与真实付款仍待完成。工作根下 `integrated-payment-capture-check-a01/RESULT.actual.json` 和stdio保留此次验证。

容量源审查另发现 `regular_core` 仍先采全局persistent对象且有4096物理对象上限，本场manager已见17880对象，可能在轮到Army记录前耗尽；不能把开关成功或增加侧存预算说成补员cause ledger合格。下一实机可先只开natural获取付款，regular-core采集范围的修复并行外置研究，不阻止拍摄已可观察的机制。

## 2026-10-15T11:21Z R0172 实际付款窗口试拍与正常关闭

本节所有现场事实的 `machine_id` 均为 **`desktop-3fevhd2-1c74096080`**，实际工作目录为 `C:/ck3-e04-resume-20261015-a01/live12004-payment-a01/`。本次源码与生产 DLL 冻结于 `5bb336b6677923453988c50dfbbda2c334c049c8`；11:19Z 现场关闭后才更新主树，不能把后续提交追认为本场运行源码。总回执 `CLOSED.actual-a01.json` 为17,566B，SHA-256 `41d3a2348a0287ac8595ba4b89c9a9e15d95849da75ccb7941fa921218d6d960`。

### 新生产构建与身份

- 本机 `.4 / build25734779 / EXE 98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518` 已实际安装，Steam保持离线。10:32Z另取窗口位移与新像素并直接审阅离线画面，未以停滞的任务栏时钟代替新鲜度；证据为工作根 `steam-offline-payment-fresh-a04/` 及 `steam-offline-payment-reviewed-a04.json`。
- `native12004-payment-20261015-a03` Release/jobs16实际编译返回0，DLL SHA为 `a9a1323a4ece7121cf7470ef7b741ab6fb1f7dfc6a10fe358e937375e16147ae`，injector为 `07703493c942aba326c4d9820cc755d7c1f768566d811a8ae052c4835b15f894`，host为 `0260fed6f852f3f9e62a2b8a7cbf9b28cdb3c7c98e3e7ab1bddf62bf6fee9491`。实际构建、定义核验和SYSTEM精确EXE排除读回在工作根 `native-payment-build-completion-a03.json`、`native-payment-build-qualification.actual-a02.json` 与构建目录 `defender-exe-exclusions/20261015T103430Z-fb93e35e/receipt.json`；没有请求新UAC。
- R0172为正常R0171存档续行，**不是重新创造初始T0**。实际PID20560、创建FILETIME134365345411777295、connection generation1、episode `native-31254-0057f5024437`、actor31254。`runtime-actor-identity.actual-a01.json` 为6008B，SHA `89e0cedc3695cf783647850feb8ee1cc3f8199d6dafe4a3ece6f2e498b266aef`；稳定Robert来源不授其他加载的runtime编号资格。

### 实际推进及止线

从raw53144616推进到53145048，共 **18个连续精确自然日**，逐日sentinel均+24、零overshoot并暂停。第18日时钟原回执与11:17Z独立快照仍为同一暂停端点；**只有前17日通过完整Driver结果校验**，没有完成原定24日计划。MoveArmy18→海区1033只提交一次，实际路线经2624、1036、8653、1034；终态Army18仍在2624、1196/1196、补给300/300，尚不能授登船或扣费结论。

第18日完整侧存实际为16,902,837B，超过本案单包16MiB止线，脚本在打开和解析该文件之前拒绝继续。精确引用为 `state-a01/native-session/army-query-history-results/army-query-80879aa62a3d416ab94f8ff4a0d0db1a.json`，SHA `fa2b533e961cd931e39041573c2ee9abc735989b7b37a8abf4ecf0b8c4d68834`，不是partial，也不是原始pipe字节。全部Driver侧存实际247,354,345B，仍低于512MiB总额度；**总额度未超不能取消单包止线**。下一轮先约束导出主体与历史范围，不直接扩大上限。

逐日证据在 `clock-raw-daily24-continuation-a03/day-01.actual.json` 至day-03，以及 `clock-raw-daily24-continuation-a04/day-04.actual.json` 至day-17；第18日原时钟为本run `responses/clockraw24a04-d18-06-clock-status.json`，终态为 `responses/024-final-paused-snapshot.json`。旧attempt的revision竞态和响应文件尚在写入时的JSON读取失败均保留；恢复只读同一结果或当前状态，未重发Arm/Resume。外置读取器现等待同一响应文件写完，未改正在运行的DLL。

### 付款观察器失效边界与修复候选

本场只显式启用natural_phase，其余8个研究族保持关闭；付款窗口起初独立读回已admitted，随后第1日即返回 **`snapshot_read_failed`**、窗口关闭、采样epoch2且journal清空。此后不自动重开。空records **不能证明没有付款**，本场qualified boarding debit、loss/refill cause ledger仍未通过，maintenance仍unclosed。

离线源码已定位：`bridge.cpp`把完整语义快照暂不可读直接视为付款窗口身份失效，调用Invalidate并清空journal；具体首次失败的缓存分支未保留，不能追认是哪一个。候选改为仅在已admitted窗口下读取当前exact `.4` adapter的fresh core identity，再走原owner/map/alive/connection/date/natural守卫；失败仍关闭，不借旧snapshot、不发布partial、不增加revision，也不自动打开窗口。外置三文件patch只通过 `git apply --check`，**未整合、未编译、未运行**；还需真实 `.4` adapter解包smoke及窄连接回归，然后新生产DLL和合法新现场。候选索引为工作根 `capability-lane/payment-window-snapshot-diagnostic-a01/ROOT-DELIVERY.actual-a01.json`，SHA `2378272008c7f6d44a8c54700cde2fcde9d6b238cf01a771bb05920703591bfb`。

另一条离线来源研究已闭合exact `.4` physical refill writer：core RVA`2A98AC0`，请求计算`262C9B0`；实际ADD为`2A98B88`的`add dword ptr [rax-0xC],edx`，目标为Regiment+`1C+physical_ordinal*24`，与槽内qindex不同。后续`2A98BEF`另有清零；Army刷新`24E8100`→缓存`2633320`，`26338A0/26338A3`写ArRg当前/最大缓存。整个callback净差不能替代某条ADD的执行账。来源包为工作根 `capability-lane/regular-core-writers-source-a01/ROOT-DELIVERY.actual.json`，SHA `78c24703ddff7155b333ff8db107d9a5727697024469ee2694fca59095b549d5`；只授静态来源定位，尚无新的指令执行探针或实机补员归因。其他机器复用上述知识时必须先匹配EXE tuple。

### 原片、保存、退出与保留期限

唯一原片 `raw-payment-window-a01/raw.mkv` 为 **2,658,761,575B**，SHA `ffa85d42cbcede70a7ddf19a4c02d0e9051df0953c19c16068016ef45a89b9b3`；实际ffprobe为 **900秒、2560×1440、30fps、单H.264流、无音轨**。FFmpeg返回0且Job进程0；这是15分钟原始录像，不是15分钟合格镜头，尚无连续clean认证、全片1×人工观看或signoff。`media-probe.actual-a01.json`沿用已保全的原片SHA，未重哈希整片。

11:17Z正常存档 `state-a01/profile/save games/xar_checkpoint.ck3` 保存成功，68,450,356B，SHA `be327216d366627c46effe1f976f1f479899276a02c88e2511591d6cf732e881`，raw53145048；immutable seed仍为原始53144616。该新checkpoint尚未冷载验收。11:19:14Z保留的原进程HANDLE signaled/exit0，随后session退出且Job在任何termination前已为0、tree_gone、SDK/keeper已停；11:19:49Z显示恢复1024×768，11:20:25Z任务总线CAS5353→5354释放完成。证据为 `stock-normal-exit-a01/observer-result.actual.json`、本run `bootstrap-result.json`、`display-restore.actual-a01.json`、`screen-release.actual-a01.json`，不外推为typed native normal-exit能力合格。

11:21Z收口容量实际C空闲33,267,949,568B、D空闲22,745,317,376B。当前checkpoint、原片与故障关键证据保护至 **2026-10-16T07:45:01.597Z复核**，用途为Review02接续及观察器修复，不无限续存。下一次开机前仍须新鲜本机离线证据、容量准入及新PID身份；新片费用、损耗/补员、Halt/改道及同T0 A/B/C等研究缺口未被这些原片抵扣。

## 2026-10-15T11:59Z 继续任务与明确进度口径

本轮机器仍为 `desktop-3fevhd2-1c74096080`。用户要求继续研究与拍摄，并汇报百分比；从本节起使用明确的**新版Review02整卡验收**分母，不把静态来源、fixture、原片时长或改稿映射折算为已完成主张，也不重写旧估算。

| 范围 | 截至本切点实际完成 | 剩余 |
|---|---:|---|
| 已有Review01制作、机器审计、客户端交付 | 3/3，100% | 人工完整1×及signoff单列未完成 |
| Review02研究卡R00–R13 | 2/14，14.3% | R00本机准入、R02精确日能力已闭；R01新比较T0及R03–R13业务整卡未闭 |
| R03–R13核心机制/对照完整闭环 | 0/11 | 围城、县界、低库存饥饿、physical补员、登船付款、维护、特殊分合军、ABC、三类路线操作 |
| 新版合格动态证据包 | 0/11 | 两段共23:02.866原片保留，不代表clean跨度 |
| Review02最终69段稿及声音 | 各0/69 | 已完成的是69/69离线改稿映射 |
| 新版render/审计/人工完整签核/指定交付 | 0/4 | 尚未开始，不用Review01冒充新版完成 |

逐卡评估与行号来源在工作根 `progress-evidence-a01/ASSESSMENT.actual-a01.json`。这组比例是整卡接受率，不是代码工作量比例或对历史知识归零。排期估计为：北京时间10月15日21:30前完成付款窗口/导出范围的最小修复资格并争取恢复补拍；核心研究暂估2–4天，同新T0的A/B/C必须串行，证据冻结后改稿/声音/重剪/审计另1–2天，目标交付窗口10月18–21日。维护结算来源及自然场景尚未知，时点是调度目标，出现真实新证据后更新，不承诺未知事件按期发生。

本轮并行包已取得65+13项付款窗口修复资格，以及scoped导出150项Python、4630项native断言和两个改动TU语法资格。Root实际应用后主树新增组合检查24项PASS，继承XQOL兼容修复相关29项PASS；生产DLL和新现场尚未执行，源码/fixture不授付款业务通过。下一现场优先沿R0172已有route自然续行，实际接近海上转换才开360秒短录像，成功登船后在ring余量内做一次合法Halt探索；另一次改道必须保留自己的完整后果窗口。

12:02Z追加：现有RouteBindings的实际signed64/Q100000移动锁定cutoff已通过四文件最小增量发布到 `current_movement_progress.loaded_movement_lock_cutoff`，不添加推断locked。读取独立于ETA成功与否，disabled/非暂停/clock不符保持null，旧shape仍可消费。真实Attach+serializer有11场景32断言、实际movement block consumer有60检查；Root主树的cutoff/scoped/cache组合实际 **74 passed**。这仍不是本机cutoff数值实读或Halt结果；下一现场才观测。外置资格为 `strength-scope-bloat-a01/halt-cutoff-a01/ROOT-DELIVERY-PYTEST.actual.json` 及其精确source/compiled wire pins，未把故意重复war_ids的fixture整行归一化失败改成通过。

容量统一ACCEPT在 `continuation-a02/CAPACITY-ACCEPTED.actual-a01.json`，1546B，SHA `29d8ca27f4f70814640dd240577f22f7c481c617f2007a479cd3a5e87e134283`：现项目C保守上界161126913919B、本轮合计新增峰6375342080B、160GiB例外原截止不变，全部子lane共用512MiB，Root唯一重型写入协调者；不得每lane重新消费同一份free。新raw1.5GiB、Driver128MiB/单包16MiB、natural56/payment384先止线。全部下一场计划结果仍为pending，计划校验不代替屏幕租约、新鲜离线、实际新PID与运行证明。

## 2026-10-16 滚动补录：R0174闭场、驻定对照与新Halt原片

本节补记10月15日UTC的实际现场（北京时间10月15日晚）及跨日知识整合。来源机器为 **`desktop-3fevhd2-1c74096080`**；运行源码仍为`1463bd9b4b89612d283dd45ac4ec9efbf22f048d`，a05 DLL SHA为`7929217c07ff4405445611558040cc282df98dcebc79d16f5a1b4e6bdc049b1b`。闭场之后Root才向工作树apply后继专题/consumer/关联候选，不追认为R0174已部署能力；未来a06另做生产构建和新现场资格。

### 已完成的窄事实

R0174实际PID17468、创建FILETIME134365505726865638、generation1、episode`native-31254-0d067159706e`、Robert31254、Army18。实际载入共同冻结seed SHA `9ab3b0d05bdc1a0c4ef2d81a9dc27cec3f66e9af2871b5cac11776ddc6ddb784`。T0 raw53145048至第21日53145552，每日exact+24、1tick、overshoot0且暂停；Army18始终在2624、完整空route，完整compact兵力1196/1196。第11日按原政策拒绝marriage通知，第15日bookmark.1070选择首个显示选项A，与历史处理一致；恢复只重读原Arm对应的status/final，不重发Arm/Resume。

完整`--phase pair`检查在`2026-10-15T15:55:02Z`实际PASS。它支持“共同保存T0的21日驻定回放对照，与历史R0173保存T0后续行作有限比较”；历史treatment当时**没有重新load9ab3**，不是两臂新冷载、同observer build、同一epoch或通用随机世界完全等同的证明。各臂sequence只在自身窗口使用，不跨窗口比较序号。控制臂合格登船回调0，不证明零总支出或免费登船。原R07仍缺七日以内窗口、避经济结算及静止T0后新Move，R01完整新比较T0/统帅/ABC目标冻结仍缺。来源为`t0-control-pair-closeout-a01/pair-check.actual-a01.json`（2337B，SHA `cf63da7e5858b4cd35b64784e36e57bad3bbd3c3b18cc1f9e20665abc9753fa1`）；[R0174专题和便携原件](../ck3-native-ai/episode04-r0174-common-t0-control-12004.md)供其他机器相对路径重算，不要求原机C盘路径。

新Halt原片真实 **45秒、1,350帧、2560×1440/30fps、无音轨**，56,479,663B，SHA `6d28162df56f95b7ea85c252dd8d61794c73b87c00c54b6ab7002945f46f1f12`。一次完整strict decode及probe通过，未重哈希/重编码原片。候选0–4秒展示移动转待命，4–20秒展示待命后态；左上沿海tooltip遮挡持续存在，连续clean和人工1×/signoff均pending。SDK墙钟与encoded PTS未校准，精确Halt编码帧未知，不能按名义墙钟指定事件帧。**R0173旧6分钟raw没有Halt**仍为正确历史；本次是R0174另一次新录像，不改story-a02封存字节。

### 新raw财务观测与未闭归因

新a05现场generic seq12已真实读到四项raw`500974,0,218610,0`，按原生有符号算式得到282364，whole-callback个人账户余额变化一致；day17/day21严格消费均PASS且指向同一保留事件，不重复计两笔。其OS unwound parent指向已闭合的`28F7840`函数内返回点，完整parent本体没有直接四项store；更上一层有限来源仍在追。这里的seq12属于R0174新记录，**不能倒填R0173旧seq12**。四term的producer/刷新节奏/时间单位/军事applied component仍未闭，`maintenance_attribution=unclosed`；算式匹配、parent或净钱包增加都不证明已付维护费。共享规则见[维护raw消费合同](../ck3-native-ai/war-payment-maintenance-cache-source-12004.md)。

### 保存、正常退出与后续门槛

终态date53145552普通checkpoint保存成功，69,730,879B，SHA `8cc8b11cf00561513625b6ef28c8e22d9104f6173b684b233c9687edeb67bb88`。Root已完成stock正常退出、实际exit0、SDK/keeper及Game/recorder树回收、显示恢复，15:59:10Z屏幕CAS **5419→5420**释放。最初一次WM_CLOSE短等回执仍是pending，不将它改成独立退出证明；实际正常闭场来源由R0174便携bundle保全。

| 范围 | 当前实际完成 | 本次增量的边界 |
| --- | ---: | --- |
| 已有Review01制作、机器审计、客户端交付 | 3/3，100% | 原28:55.80交付保持；人工1×/signoff仍单列pending |
| Review02研究整卡R00–R13 | 3/14，21.4% | R00/R02/R11已闭；本次pair和新raw不增加整卡分子 |
| 新版合格动态证据包 | 0/11，0% | 已新增45秒Halt原片和20秒候选，clean尚未授予 |
| 新中文替换草稿覆盖 | 24/69，34.8% | story-a02为有界草稿，不等于69段全文冻结 |
| Review02最终冻结稿 / 声音 | 各0/69，0% | 24段草稿、源码映射不抵扣最终稿和音频 |
| 新版render / 审计 / 人工完整签核 / 指定交付 | 0/4，0% | 不用Review01代填新版里程碑 |

本轮跨日接续窗口优先构建/资格native a06并取得R12锁定Halt、R13锁定重定向各自真实后果；原源与当前a05不热冒充a06。核心研究目标暂估北京时间 **10月17–19日**，新Review目标窗口 **10月18–21日**，均为调度估计，依赖自然低库存、实际补员/维护来源及串行ABC，不能保证按时发生。新现场只按[锁定路线手册](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/locked_routes/README.md)重绑当前版本/机器/PID/实际route/cutoff；研究、镜头、稿声和成片各自结算。共享512MiB子包池和原复核截止 **2026-10-16T07:45:01.597Z**保持，不自动续期。


## 2026-10-16 R0175/R0176：锁定行为实证与共用代码入库

本节机器 `desktop-3fevhd2-1c74096080`；观察截止2026-10-15 19:01:28 UTC（10月16日03:01 CST）。两场实际运行source `dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb`、a06 DLL `b7b8cf33742ab60f9b5db439b30b7f83b075d8640bfce2e249c472383d0969d7`、游戏1.20.0.4/build25734779；下一a07源码整合不回填旧场。

R0175独立正常Move后首段进度96666/100000，大于实际锁定线50000；一次Halt将尾段截为原front1036，仍实际走完首段，随后次日保持空路线静止。31代时钟共32自然日。R0176从正常驻定seed新Move，五个自然日后进度95108、剩余25714，原路线 `[8653,1034,1033]`；一次typed改道独立读回 `[8653,8645]`，实际先到8653，再到8645，九代时钟共13自然日。两场均normal exit0、SDK/录制/keeper退场和屏幕CAS释放，原始错误及只读恢复均保留。

研究整卡现为 **R00/R02/R11/R12/R13，5/14＝35.7%**；R03–R13业务实验 **3/11＝27.3%**。各45秒原片均严格全解码通过；R13实际最终抵达回包在录制起点后65.61秒，整体后验完成69.53秒，均在片外。连续clean、人工1×和新版合格动态包仍不增加信用（0/11）。R09暂停态selected93实际拆合保留250/250物理DATA；原Army18空DATA/cache1/1的角色ArRg59被移除，其Char34232成为新军162的实际统帅，合军后成为93统帅；这不是一名物理士兵死亡。原strict unrelated freeze失败保留，R09整卡仍未关闭。

便携原件、严格离线重放与共享专题分别落在 `docs/ck3-native-ai/acceptance/2026-10-16-episode04-r12-r0175/`、`2026-10-16-episode04-r13-r0176/` 和对应 `episode04-r12-locked-halt-r0175-12004.md`、`episode04-r13-locked-reroute-r0176-12004.md`、`episode04-r09-selected93-micro-actual-12004.md`。智能体消费者在 `ck3_autonomous_player/src/xar_autoplayer/bridge/`；视频/Root分阶段组合在本期 `tools/review02/`；不会把外置本机launcher当作通用运行库。source-a03新增13段草稿及9张SVG演示卡，新旧草稿合计37/69，仅为草稿覆盖。

并发完成补员权限与军务callback只读接线、围城/劫掠residual预算、零库存触发窗口、县入境loaded floor读口、四项现金缓存actual writer消费者、特殊兵资格，以及A/B/C分阶段组合。源码和cold资格均独立于下一a07完整构建/新实机；维护费writer、实际补员ADD、R03/R04/R05正因果、费用两fresh-arms与正式ABC仍继续执行，不把计划、ACK或测试数量算作完成。

## 2026-10-16 本机R0177闭场、R03原件与story-a05草稿

本段所有现场、素材和稿件事实均属 machine_id: `desktop-3fevhd2-1c74096080`，按Root本次实际回执滚动追加。

- R0177已有Root实际CLOSED回执：3219 B，SHA-256 `9a2f12db0d934f8cb01236c7ca8e88a1515b18ef552677ccc13df70841bc9797`。coastal原片45秒/1350帧，完整解码PASS；`clean=false`、`human=false`，不授连续clean或人工签核。
- R03原件在raw53147472、同一callback188中，7条preferred writer实际扣兵11（1+1+3+1+2+1+2），siege11/raid0，原件正消费通过。正式整卡审结仍待Root；本次汇报暂保留整卡5/14＝35.7%、核心业务3/11，不先增加分子。
- [story-a05完整草稿](../../promo/ck3_native_war_ai/episode-04-march-logistics/review02/story-a05/README.md)为69/69＝100%，8351字；`TTS/provider=0`。这是草稿接受率，不等于最终冻结、声音、新成片或人审完成。
- 共享源码解释见[拆合军库存权重/取整顺序](../ck3-native-ai/episode04-split-merge-stock-weight-order-12004.md)、[统帅容量与零准备量](../ck3-native-ai/episode04-commander-capacity-zero-preparation-12004.md)。新增source的最终提交、a08 DLL、构建及新冷验结果由实际回执另记，本段不预填未来SHA、CI通过或实机资格。

## 2026-10-16 R183 截断录制、共享修复与专属回收

本节机器仍为 **`desktop-3fevhd2-1c74096080`**。当前入口统一为[缺口与执行图](../ck3-native-ai/episode04-current-execution-map-12004.md)，其中明确研究整卡 **6/14（42.9%）**、核心业务 **4/11（36.4%）**；R03 已由正式围城专题接受，前节“待Root审结”的5/14属于较早切点。合格连续动态 **0/11**、最终稿/声音各 **0/69**，69/69仍是草稿覆盖。

R183使用 source/native `20c7319b6964c80fa419540cf4e30852feff4810`、a26、CK3 1.20.0.4，独立新进程身份和正常保存已核；输入为R182正常checkpoint。首次 `gdigrab hwnd` 得到黑图，修正为实际客户区 `[640,360,1920,1080]` 的1280×720屏幕区域采集。07:44:49 UTC实际开录，0.3726659秒后Resume；原配额07:45:01.597截止，外置recorder在07:45:02 abort，保留239帧／实际7.966秒partial。容器90秒字段不是内容时长。三日原生回执末date53148000、Army18仍2635围城，不证明三日全部入片。游戏07:45:38 timeout清理，非正常UI退出，没有拍后新checkpoint。08:26:18屏幕CAS5732→5733，waiting/resources=[]。精确来源见[R183便携专题](../ck3-native-ai/episode04-r183-window-capture-12004.md)和[视频结果](../../promo/ck3_native_war_ai/episode-04-march-logistics/r183-capture-result-2026-10-16.md)。

本轮canonical recorder改为动态客户区区域采集，保留原始全桌面预检图，独立250ms监测前台、尺寸、进程身份及遮挡；开始和spawn前均要求完整片长加至少120秒闭场余量，容量JSON精确绑定machine/scene/run/source。回执连续写失败也必须清理FFmpeg。R06 reader另修首key命中后无关尾项读取与depth诊断上一层残留，8层及其他预算不扩大。它们是源码/离线资格，**不追认为R183已部署或新实录通过**，下一生产构建与实机另记。

专属回收线程已实际回收156件过期派生及验证重复对象，已知单链接分配 **28,545,642,496B（26.59GiB）**、失败0；C25件、D131件。原件keeper和当前E04恢复基线不在删除清单。机器本地每日北京时间04:00的只读巡检任务已用普通用户最低权限安装，并由Task Scheduler实际运行exit0；自动发现候选不等于自动删除新对象。工具、精简availability记录、调度冻结与读回见[维护记录](../maintenance/storage-retention-2026-10-16-dedicated-worker.md)。旧07:45额度及旧D例外均已到期，没有改旧回执；下一重型任务必须单独fresh review及原子登记。

## 2026-10-18 最新移动准备切点

`machine_id: desktop-3fevhd2-1c74096080`。后继见[R200/R201交接](2026-10-18-war-episode04-r200-r201-movement.md)：R200环境失败，R201 23闭环+独立day24，事件已确认但timeout/CK3 exit1、无推进后的正常闭场Save；不续作S0。R199正常源仍是后继冷载依据，计数9/14、6/11、0/11、0/3不变。
