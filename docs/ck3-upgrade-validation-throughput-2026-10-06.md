# CK3 1.20 迁移验证的吞吐与本机续行

用户在读取[10 月 6 日交接](ck3-upgrade-handoff-2026-10-06.md)后要求继续执行，并询问本批迁移为何缓慢、怎样改进。本文记录有实际失败依据的判断，不计算尚无完整阶段计时支持的原因占比。原产品顺序、正式发布门槛、过程资产保全与单机 CK3 独占保持。

## 已观察的成本

| 成本 | 具体依据 | 当前处理 |
| --- | --- | --- |
| 产品与验收工具同时迁移，失败难以直接归属 | TED 暂停控制、RMTM situation 初始化、QOL 夹具资格各有原 RED；详见交接各产品入口 | 每次重试只解决已定位的阻点，复用对应现成输入，不重新展开全矩阵 |
| 环境故障中断已有效的业务链 | CCC R2/R4 实际 ENOSPC，核心与剩余 GUI 信用分开 | 新鲜盘点后再开场，不把旧空闲量或压缩设置当作问题已解决 |
| 冷启动与载入重复支付 | 本次 R0005 验收器 10:59:47 UTC 开始，约 11:01:25 到达稳定书签页面，之后仍有地图载入 | Python 修复保留同一有效 CK3 进程；只有加载输入或 binary 改变、进程失效等实际条件要求时冷重启 |
| 启动判定阻止业务开始 | R0005 的 event-free owner gate 被介绍事件挡住，400 秒准入超时；未读 root 不能称政府不合格 | 用已有 typed 事件观测与正常选择处理已源审的介绍，原 policy 与预算不变 |
| 准备包未转成运行结果 | 交接有多套 READY/NOT_RUN 输入；5/10 正式发布完成 | 一个产品实际通过后立即完成正式构建、上传、公开 Notes、规定缓存业务和永久记录，不等待全批 |
| 单机独占与完整发布闭环 | 本机游戏/桌面/上传串行，公开回读与缓存业务均为现有门槛 | 后台只推进不冲突的下一入口和实际故障修复，不用代理数量替代实机吞吐 |

## 本次接手的实际增量

资源只读快照 `2026-10-06T10:40:57Z`：C 空闲 21,099,585,536 B（约 19.65 GiB），系统 commit 为 21,114,740,736 / 39,359,959,040 B，pagefile 5,100,273,664 B，CK3/验收器为空。交接停机的 3.35 GiB 已过时；改善原因 UNKNOWN，本次缓存删除、Steam 重启、pagefile 修改和系统重启均为零。[完整原件](C:/workspace/ck3-upgrade-20261006/resume-space-agent-01/resource-snapshot-01.json) / SHA-256 `0ca7ea09d8d28819abb2bd0ba17b05b26e7981f32cdadcb4bb7df64e6a629c59`。

[写入错误诊断](ck3-native-ai/runtime-write-error-context-2026-10-06.md)已在 master 提交 `69c163ff3c51fb54f5122c9fc8bff73f0113af74` 并普通推送。5 项必要检查通过；诊断不宣称修复 ENOSPC，也不重跑原产品核心。

新场 `4-8e1c2f1861--celestial-commerce-corruption--R0005` / a78 在新鲜离线原图与 nonce `228ad7760f4b` 亲审后一次启动。准入超时后仍保留同一 PID 12492 / generation 1 的暂停现场。介绍原图关闭后，追加只读双帧、原资格日志、campaign root 四步全部成功，原 Timeout 未清；完整原 RED 先另存不可变字节。实际 root 是独立 celestial/hegemony 皇帝 34422，早先按 ID 变化推测已切官员的结论撤回。

原 900 秒 hold 到时，报告 `2026-10-06T11:23:14.226025Z` finished / RED，`managed_session_thread_finished=true`、`cleanup_ok=true`，盘点无 CK3/该 harness/watchdog。keeper 实际退出0、线程已退出，末 seq4274 后单次 CAS4275 为 done/resources=[]。[实际释放回执](C:/workspace/ck3-upgrade-20261006/resume-root-01/a78-screen-release-01.json)。没有正常 GUI OS0、剩余生产 GUI、source PASS 或正式发布信用。具体源审、热观测、最小修复与下一输入边界见[启动介绍专题](ck3-native-ai/ccc-startup-dynastic-intro-2026-10-06.md)。

一次对无帮助入口的旧挑战脚本执行 `--help`，意外生成两张挑战图且当时未持有 screen lease；两图与报告完整移动到外置原件并记录[保全回执](C:/workspace/ck3-upgrade-20261006/resume-root-01/steam-challenge-mistaken-help-preservation.json)，没有 CK3 启动，不作为准入证据。后续正式挑战均在 a78 独占下执行。第一次正常挑战图未包含 Steam，第二次挑战在启动前已超 120 秒，均保留且不授准入；最终使用 recovery02/challenge03 的亲审结果。

## 后续执行方式

1. 按已通过核心与剩余 UI 分别记账，下一场只取得仍缺的生产决议 Confirm、撤销、traits/cooldown 和正常退出。
2. 先把真实启动介绍阻点修成通用 registry 知识及既有 typed 能力组合，再用新的冻结 Python 输入、原 DLL 开场；不重逆向或重编 native。
3. 每次冷试注明唯一改动、预期解除的实际阻点和剩余业务；如果同一失败未改变，不继续冷试。
4. 每个有效工作包一次必要验证后立即 commit/rebase/普通 push；失败事实与通过事实分开保留。记录阶段时间以便以后统计，不虚构总耗时占比或下一产品 ETA。

当前正式发布仍为交接的 5/10；本次写入诊断与启动修复不计作产品发布。下一项仍是 CCC，之后消费已有 QOL18/RMTM10/TED11 入口，361 最后。

## R0006：首次 map-ready 提前于有效通知查询

UI20 / a79 / `4-8e1c2f1861--celestial-commerce-corruption--R0006` 从 committed `13b4942a91fa5459d5dc37bf7de7e95c38cc27b6`、Source18 与原 DLL 开场。当次离线原图 nonce `df0d43bbfea5` 已亲审。12:12:12 UTC 新资源快照 C free20,598,800,384 B、commit20,641,062,912 /39,359,959,040 B、CK3为空，未清理或改系统。

12:17:48.136518 的第一次 typed context query 在30.009秒后失败，server stderr为 `application-main typed query failed or its snapshot changed`。首次 native map-ready 通知帧的原图仍显示载入0%；native observer此前存在 read-in-progress /4859ms读取。没有执行通知选择。原完整失败报告先永久保全；同一PID11412/generation1热现场的三个快照、资格、context共五步实际成功，12:29:16.016312 读到 `.0051`、ROOT34422、native0唯一shown/enabled，证明既有DLL可完成查询。

前两个快照仅相隔0.23秒，同cached pump epoch，观察入口正确拒绝；后取新frame3通过原严格递增要求。准备和前台交接消耗了剩余现场时间，正常选择23入口提交前原900秒hold已结束。报告12:33:20.701318 finished/RED；独立held OS handle在signaled后读到退出1，无GUI0或D0成功。`managed_session_thread_finished=true`、`cleanup_ok=true`、本场进程库存空；keeper退出0/线程退出/末4323，单次CAS4326 done/resources=[]。原报告SHA `d91ad8aa836325f417b3d5906cf6272b95bb77a4487d4fc97ff15020ccb8b1c1`，见[闭场库存](C:/workspace/ck3-upgrade-20261006/resume-root-01/a79-final-inventory-01.json)和[释放](C:/workspace/ck3-upgrade-20261006/resume-root-01/a79-screen-release-01.json)。

这次不是ENOSPC，也不是原政府policy或native capability缺失。下一修复只把通知query放到当前读取完成、同一owner稳定双帧之后，复用Source18/原DLL与原预算；正常通知及D1→D3连续执行，减少现场脚本准备与人工交接。上述热成功不追认旧RED为GREEN。

## R0007：启动修复生效，生产 Confirm/cancel 实际通过

查询时机修复 `b870f648ca15887db00b607d5d03d1e60bb51bdf` 已普通推送，原3项测试一次PASS（2.417s）；Source18和DLL不变。UI21/a80/R0007 实际owner epoch7678→7738后发通知query，13:01:08正常选择一次、eventgone，D0资格通过。D1第一步13:01:18.473237到D3实际root13:01:53.979849，连续原路线35.51秒，无error、无重排。

Root亲审当场介绍前后原图及D3/生产决议detail，真实点击“翻开账册”；随后既有getter实际读新xccc.1001并一次.f取消，fresh eventgone。actual Confirm游戏日期1066-09-18。第四档失去特质横幅有原图，但全四档缺失、冷却日期和正常GUI退出仍未取得，不以源码或横幅替代这三项。

人工逐图处理耗尽原hold，13:16:18.926299报告自身GREEN/errornull，但独立held OS handle在signaled后读OS1；报告GREEN仅覆盖已排步骤，不授完整source或release。managed thread/cleanup true，库存空；keeper实际exit0/threadexit/末4378后CAS4379 done/resources=[]。[实际库存](C:/workspace/ck3-upgrade-20261006/resume-root-01/a80-final-inventory-01.json)，报告27865494B/SHA `9bfc7d92d702bce0f7fc24a080321311d87858f0907856a32896ab2364b0557a`。

下一步将已审GUI导航连续执行，真实原图保存后由root亲审；模板只定位当前截图中的控件，点击仍经统一坐标map/receipt，真值仍由typed结果、原图与held OS handle证实。复用已有1.20.0.3正常菜单退出模板与0409/focus helper，原budget/source/native/core范围不扩张。


## R0008：读碰撞与实际 GUI 定位失败

UI22/profile12/a81/R0008从clean273b092f、Source18/runtime24/原DLL开场。当次Steam离线及nonce e0b7fbc5f24b原图亲审。14:03:06资源快照Cfree19,618,332,672B、commit21,205,581,824/39,359,959,040B、CK3为空；无清理、Steam重启或系统设置变更。

连续caller的base wait直接读取native-report.json遇到PermissionError13退出，游戏与harness仍有效。新外置hot caller复用queue16原1.4秒读碰撞窗口，保留原stdio，不重放Start。14:18:58实际通知正常选择/eventgone/D0成功；D1至D3的原17控制步骤14:23:24.459430至14:23:58.279070全部ok，加初始4步共21，实际官员29959/date53144400。

GUI row matcher未匹配，无该row click intent，Confirm未发生。随后一次Escape未关闭decisions面板，重复同一known-panel被拒绝。Root亲审当前原图、使用统一map/新receipt在实际row(1475,609)点开“定夺贪墨之策”；R7模板来自已选中row，本场实际未选中row图像不同，行位置也不同。位置变化本身不是失败归因，原matching receipt仍保留。后续hotdetail候选交付时现场已结束，未执行；不授Confirm/.f/traits/cooldown或GUI0。

原900秒hold不延长。独立held OS handle14:34:02.410613 signaled后读取exit1；报告14:34:03.756293 finished/GREEN/errornull仅覆盖已排21步，24,858,096B/SHA2a973105ede8ab4897dcf684b5f0efabd28e285c60cb1eb35dc520c55fdd35a1。managed thread/cleanup true，库存空；keeper真实退出0/threadexit/末4424后CAS4425 done/resources=[]。依据：[实际库存](C:/workspace/ck3-upgrade-20261006/resume-root-01/a81-final-inventory-01.json)、[释放](C:/workspace/ck3-upgrade-20261006/resume-root-01/a81-screen-release-01.json)、[GUI失败原件](C:/workspace/ck3-upgrade-20261006/resume-root-01/a81-hot-route-01/actual-gui/route-error-no-replay.json)。

本场再次证明有效业务链只需数十秒，临场修补与前台交接消耗的墙钟会超过原hold。下一输入在启动前备齐：复用原bounded reader、当前未选中row小patch、实际panel X关闭和正常退出；旧freeze和attempt保持。发布仍5/10，不增加核心矩阵或900秒预算。


## R0009：真实推进完成后的角色切换暂停窗口

UI23/profile13/a82/R0009从clean82dd839a、Source18/runtime24/原DLL开场。14:55:15资源快照Cfree19,365,683,200B、commit21,224,112,128/39,359,959,040B、CK3为空；15:06:30 Steam离线challenge nonce bfdd63fc12a4原图亲审。未切在线或改系统设置。

连续caller启动返回0后立即读取尚未创建的报告，FileNotFoundError导致caller退出；原CK3/harness有效。Root新外置hot continuation只移除已执行launch，核原PID16256/create-time1791299215.0864165、空控制队列及冻结base SHA后接续，保留原2100秒deadline和queue16/1.4秒读碰撞窗口，无Start或advance重播。

15:11:18实际通知正常选择、eventgone、D0成功，初始4步ok。D1 bound成功；15:11:27.618260 native8/date53144352已实际推进24天，actor仍34422。末端pause-map expected_revision8于15:11:27.847121提交、27.891343明确拒绝“CK3 map state is unavailable”；15:11:28.151984 native9同日期/实际actor29959/map_ready=true/paused=false。不能写成advance未发生或再次推进24天。R7/R8成功轨迹也先旧actor再新actor，但末端pause在新actor帧后提交并成功；三场对照支持仅D1等待实际角色改变后首次pause，running readiness=false不作为等待门禁，不预设官员ID，不重试opaque错误。

报告15:11:30.522695 finished/RED，RuntimeError: MCP tool ck3_execute_step returned an error: Error executing tool ck3_execute_step；10,181,355B/SHA9f16a0f0f36ade3ed97f0a7cf39480dacc54d2198b938f15e64c154de3e6591c。完整GUI23未执行，不授Confirm/.f/traits/cooldown/GUI0。native shutdown实际ck3_exit_code=1、job0/treegone/cleanup_proven=true、control files absent，managed thread/cleanup true，库存空；没有独立held OS0。keeper真实exit0/threadexit/末4440后CAS4442 done/resources=[]。依据：[实际库存](C:/workspace/ck3-upgrade-20261006/resume-root-01/a82-final-inventory-01.json)、[原native session](C:/workspace/ck3-upgrade-20261005/live/4-8e1c2f1861--celestial-commerce-corruption--R0009/native-report.session.log)、[释放](C:/workspace/ck3-upgrade-20261006/resume-root-01/a82-screen-release-01.json)。

并行调整：write_diagnostic负责有三场实证的最小PlanClient.advance显式wait_for_played_character_change opt-in及离线生产路径检查；ccc_resume_inputs复用Source18/DLL和GUI23准备UI24/profile14，把首次报告不存在纳入原deadline等待。默认advance、D2/D3、native ABI、业务门槛和原预算不变；其他产品已备入口继续保留，无重复矩阵。正式发布仍5/10。

最小修复已合入PlanClient.advance：仅显式native_campaign opt-in等待已完成observer的实际不同native玩家帧，继续原日期轮询和deadline再首次pause；默认路径未加等待。现有test文件一项真实R9薄状态回归覆盖默认/opt-in两分支，实际命令 `tools/.venv/Scripts/python.exe -B -m unittest test_ck3_12002_mcp_live.OfflinePlanTests.test_campaign_d1_actor_transition_wait_is_explicit_before_terminal_pause -v`（cwd `ck3_autonomous_player/native_bridge/research`）PASS/1test/0.012s；三场外置生产回放PASS/3/3.7514s。命令ACK和R9暂停后置是mock，未授新实机PASS。新的runtime31仅替换原runtime24 advance；Source18/index/registry/DLL和原冻结证据未改。

2026-10-06 15:38 UTC勘误：以上R0009“实际推进24天”及“再次推进24天”单位误记。原D1 kind=advance_day/days=1，date_raw从53144328到53144352增加24表示24小时，即1天；应读为“实际推进1天”和“再次推进1天”。原始帧/请求/attempt未改，末端pause窗口归因与修复不变。


## R0010：业务读回补齐、正常退出未完成

UI24/profile14/a83/runtime31从clean e712122d启动，Source18/index/f150 DLL原样。15:50:24 UTC资源Cfree19,046,473,728B、commit21,314,834,432/39,359,959,040B、无CK3；15:51:47 nonce cccffcc594b7原图Steam离线亲审，claim4452/keeper ready4453。新first-report FileNotFound等待正确进入原launch2100 deadline；实际started15:52:53.086599。

D0通知正常选项/eventgone/business bound成立。D1显式actor-change等待15:57:33.918603至41.115713 actualPASS，elapsed_hours24=1天；实际新官员29959/date53144352已paused。D2生产事件1001/选.d/D3原17控制步骤至15:58:10.029969全ok；初始4步合21。生产决议实际物理Confirm于1066-09-18触发xccc.1001/instance3，native typed context root29959；.f实际option_number5“从此封存这本账册”后eventgone15:58:38.016240。全部26排队step成功仅覆盖这些步骤，不能推出未排的GUI检查或正常退出。

GUI23随机人脸模板匹配相关度0.652307/no unique/no click；未开启人物profile。旧退出尾部physical X关闭decisions后一次heldEscape没有打开菜单，第二次被consumed门禁拒绝，原business/quit错误不改。Root沿同一paused PID4564/create-time1791301981.5564969，以新original/full1920×1080/统一map/PNGreceipt实点portrait，16:02–16:04亲审完整trait行四xccc_corruption_1–4缺失；16:04:26 disabled row及16:08:03 disabled Confirm tooltip原图明确“不可用，直至公元1069年9月18日”，与native Confirm1066-09-18精确+3年，无快进三年。依据：[root亲审](C:/workspace/ck3-upgrade-20261006/resume-root-01/a83-root-actual-business-visual-review-01.json)。该有界实际业务已成立，生命周期仍未通过。

原hold1791303150.8923366不延长，16:12:33.820355报告finished/GREEN/errornull、28,497,278B/SHAeebae1c268cf6893614858e7c46e9f07550d7be523039073dc9e4a355eb2e0b5；native shutdown16:12:32.916960 exit1、job0/treegone/cleanup_proven/controls absent。没有独立held OS0，仍不能正式sourcePASS/发布。Root下一工具实际执行16:22，比上一截图迟14分钟；OS monitor先返回NoSuchProcess，但root未中止后续两次mapped click，实际落在Explorer，已停止。原PNG/回执保留，未造成文件删除或移动；下一每次输入前原PID/ctime/HWND/deadline/sourcePNG身份本地核验，任依赖失败即停，只修这条实际失败路径。

managed thread/cleanup true、库存空；keeper真实exit0/threadexit末4491后CAS4493 done/resources=[]。依据：[实际库存](C:/workspace/ck3-upgrade-20261006/resume-root-01/a83-final-inventory-01.json)、[释放](C:/workspace/ck3-upgrade-20261006/resume-root-01/a83-screen-release-01.json)。其他过程素材全部保留，无Steam在线/系统设置/清理动作。

下一GUI24仅用本场固定三品徽章锚点定位portrait，及实际底栏pause-menu按钮鼠标打开，去除人脸和Escape依赖；原.92/.05/scale1两项只读定位一次均唯一。复用GUI23业务/原正常Quit后段，整条本地连续并本地核进程/时限，避免模型工具迟到重演。UI25/profile15只新六配置，Source18/runtime31/D1flag/base24/DLL/原预算复用。已完成核心11/FAIL0、其他五发布不重测；正式仍5/10。

已备QOL04b同场final6→原9步→宋任命/slider→正常Quit及后五独立场；赎金原fixture实际FAIL为ZQRS120，下一未消费plan14处expect literal与原args/source对齐，old/new/diff保留，未消耗run或改业务。Git常规fetch遇schannel握手失败，per-command openssl/HTTP1.1同TLS失败；已正常rebase到本地已取得origin/master6866e45eef7600b9e3506ce26453f47f3b253de2，尚需新的成功fetch/普通push，未把缓存ref当新网络成功。并行resource代理只读诊断既有网络入口，inputs准备UI25，root应用本场事实与午夜收口；不阻塞无依赖工作、不新增平台或完整矩阵。


## 2026-10-09 QOL R33：复用核心证据，分开补原guard与UI尾部（补记 2026-10-09T19:07:06+08:00）

R33已有 **core23 / day5 / final6** 真实证据；等待Root GUI Switch超时，**readonly9、UI25及正常退出均未资格**，原partial/normalfalse与CAS7599闭场保持，不因核心通过授productPASS。后续公共入口新增`guards_focused`，只执行两日原guard；`ui_tail`以新宋scope只执行原readonly9/UI25。两路各保实际运行身份、输入与结果，已有核心不重跑，原全部业务/正常退出门槛保持；任何partial不授产品通过。

Root后续每次游戏点击显式携带 **`--expected-foreground-hwnd <实际HWND> --max-source-age-seconds 60`**。执行前错窗口/过期源拒绝输入，执行后窗口漂移保一次已点击事实并拒绝读回资格；不自动重试。年龄门仅文件mtime补充，原新鲜原图/预览内容矩形/X-Y独立换算/PNG回执要求继续。既有记录与失败原件保留；本段无游戏、桌面输入或同字节mapper重测。
