# 战争四期：本机恢复与 Review02 前置

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
