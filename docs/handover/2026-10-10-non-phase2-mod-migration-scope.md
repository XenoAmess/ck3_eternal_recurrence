# 2026-10-10 本执行线职责纠正：只做天朝二期以外的mod迁移

用户本次明确纠正：“这些跟你有什么关系？你负责的是天朝二期以外的 mod 迁移。”上下文是执行者错误追问G2最新6067存档、12路证据及SDK/DLL可访问地址。此输入不再向用户索取，也不构成本执行线的等待项或完成条件。

本记录适用于当前C:/workspace/ck3_eternal_recurrence迁移执行线及任务总线ck3-upgrade-resume-20261006-root-01，不改变其他owner负责的天朝二期/G2任务。当前继续原十产品迁移清单内的未完成产品：XenoAmess体验优化QOL、重整河山、天朝特色361制现有公开版本0.3.0→0.3.1兼容/语言维护；仍保持361玩家产品最后。已完成七产品信用保留，分母仍10。

361既有版本维护与v0.4天朝二期运行时/领域新功能施工分开；本执行线不接手二期研发、资产、宣传或实机，不因产品同目录而扩展职责。G2研究、跨机资产调查/传输、6067恢复和长期游玩全部移出本执行线后续计划。既有薄调查只保留为发生过的历史记录，按统一存储策略到期复核，不追加预算或执行。

统一mod验收底座、必要MCP能力、源码/staging功能验收、正式上传、完整公开Change Notes与标签回读、真实Steam下载文件一致且CK3加载、正常闭场及永久changelog commit/push继续。共同底座中已有其他用途的代码不回滚，也不凭代码存在继续做超范围任务。

此前交接/日报中“迁移之后自动继续G2”的段落是本次纠正前历史计划，不能作为当前授权。本轮迁移闭环的完成判定不再依赖G2或天朝二期。廷臣具体礼仪等独立后续需求保持原交接记录，不纳入本轮迁移分母或自动扩成新功能工作包。

本纠正在R64实机活场期间先外置保全；待其11:46:53.979646Z真实CLOSED、allocator/keeper退出0及CAS8348释放后才由Root写入正式docs。结果见[R64](../xqol-r64-merit-qualification-2026-10-10.md)。

## 2026-10-13 用户再次缩减测试范围

当前先完成体验优化和重整河山，361不进入本轮。原版灵性满足、Offer资源算术、合法性、重复拒绝矩阵不属于两产品的迁移验收。已通过分项不因换场重复执行。

体验优化的当前`ui_tail`改为`persistence_smoke_v2`四项：实际读取anchor、保存100后重开读回、恢复anchor后重开读回、实际关闭面板回到干净地图。旧`representative_slider_v1`七项和原UI25控制分支保持，不把新四项称为旧矩阵全通过。保存0不再实机重复：生产`xqol.100`两个端点共用同一段draft→persistent赋值及dispatch，无按数值分支；这仅是静态同路径覆盖，不是save0实机PASS。自然重新启用仍是重开前提，不脚本清pending、不setfaith、不检查通知数量。

本机A204/R0094已实际记录anchor50、取消0后重开50、取消100后重开50，分别保存在其`case-output/ui25/action-0003.review.json`、`action-0008.review.json`、`action-0013.review.json`（SHA-256分别为`8808f82b98c88ea8a55ef2b44d15b2118afe76d76d8f89073b89a503bd0c299b`、`41f07484ab52397fcb2d25e1cac0bba59e9a42d66a17f72a1225cb4053d2ef94`、`976f3faeb66aaa9577565ad16bb88cb2f10c09b47fe4195fb10ec352a0646087`）。这些只能在最终报告单独引用，不能注入新场records。

A204随后因执行者在未暂停地图提交query-decision而被接口拒绝，安全清场；不是已证明的产品失败。其public run/verify均2、实际retained OS1/normal=false、allocator0/observer15/keeper0、CAS释放及closure3全true，失败原件保留。资源闭账为本机协调目录`focused-ui-a204-reviewed1gib-20261013-01-reservation-52-closed.json`，8437字节/SHA-256`d4776860aa13f4344a2143ce25b317eaf73e1868e8a53126f35fa4334b1da870`；不把资源CLOSED当成业务PASS。后续先暂停并确认当前snapshot再做决议语义查询。

离线回归`test_ck3_mod_acceptance_xqol_minimal_scope.py`实际8项及`test_ck3_mod_acceptance_xqol_ui_tail_binding.py`实际3项通过；历史inverse/原预算/readonly9/guard独立证据/normal0门槛未降低。这不代替尚待执行的保存读回。重整河山仅保留26步/D8核心继承链及50/51复辟门槛一次，不重跑36项或P4全矩阵。外置失败关键证据由当前迁移执行者保护至2026-10-18复核；当前有效基线、原始错误与生产输入继续保留，不凭失败或目录名自动删除。

### 同日 UI 执行工具故障与最小修复

A205/R0095正常OS0退出，但只记录anchor：public run0/verify2，保存100后的重开、恢复及清场仍为GAP。多次截图往返超过60秒，旧操作只刷新而未点击；不得追认为通过。其52闭账8786字节/SHA-256`36807b0cd662dbe3e1526624e64028b3a0be5ecf2aa254c9c7d0d49eddd59c89`。原观察器在游戏退出之后另因卷可用空间触线退出2，压力RED也保留。

A206/R0096实际target模板像素完全相同，但标题layout最大通道差21、相关度约0.99905，原1级量化阈值拒绝；`click_attempted=false`、`click_completed=false`，不是mod业务失败。旧控制器因此结束场次，原public run/verify均2，normal0退出及closure3独立完成；52闭账7799字节/SHA-256`b7a421e0fa54379437e338146e1ee98c680ed621571ce8e43ce4b26dc7059b16`。

当前控制器仅对明确唯一匹配、完全未输入的像素拒绝保留原结果并复核原PID/焦点/租约/期限后发布新sequence，交还执行者重新观察；不重放旧请求、不自动换锚、不授业务记录。歧义、守卫失败或任何输入尝试仍中断，像素阈值与预算不变。`reviewed_template_source`允许显式使用本场已亲审的旧原图：当前request仍绑定latest await，原模板helper自行采集新像素、匹配并走坐标门禁，不虚称自动截图已有人审。四项业务记录仍须亲审实际关键图。针对本次真实故障的3项离线测试和增量2项测试分别实际通过；这不是尚待补齐的GUI实机PASS。

本次存储回收均有逐文件小清单：`closed-a203-a204-retirement-20261013-01`实际回收3828文件/296768304字节；`closed-a205-evidence-retirement-20261013-01`实际回收3813文件/578270000字节。后者仅16条已结束完整传输重放用途的流、17张非关键中间PNG及A205生成shadercache；完整native报告、typed/业务读回、错误、压力、关键PNG、正常退出图、存档与当前输入保留至10月18日复核。已删原件不可读取，不制造替代原件，不改旧GREEN/RED/GAP。回执位于本机外置`ck3-upgrade-20261010`对应同名目录；实际可用空间独立复测，未按候选容量预先记收益。

### 同日 A207 未启动场次的续跑恢复

A207/R0097的两次public run均在nonce有效期检查拒绝，实际没有launch/host/native/case-output；observer随后因原10800秒有限窗口到期退出2。keeper和allocator实际0退出，CAS9978已释放，不能伪造CK3 OS0或正常业务验收。实际52 CLOSED为本机协调目录`focused-ui-a207-reviewed125gib-20261013-01-reservation-52-closed.json`（38413字节，SHA-256 `004769dea1b95aa636c1a9f8fd830b3e07b1f1e75496901c6cc01ee23ed7fb32`）；其三项closure只表示未启动进程不存在、未建native session、现场租约闭合。保守项目占用47854983016字节，未把已释放1.25GiB预留永久计为占用，也未抵扣假想回收量。

原public allocate只认识正常native闭场、特定checkout失败或pre-READY argparse失败，不能消费这个真实READY但未启动的状态。新增独立`previous_allocated_unused_closure`分支，绑定原READY/frozen、两次LAUNCH_FAILED/NOT_ASSESSED、observer2、keeper/allocator0、实际CAS及当前无进程；旧分支不变，不授native/OS0/业务信用，不改runtime。以本场实际原件直接调用生产分支：第一次暴露release路径str/Path错误，修正后第二次实际通过。回执`focused-controls-20261013-07/allocated-unused-actual-fixture-02-process-exit.json`（992字节，SHA-256 `d902fa864fe19ca10d71bae019bb459876e6958b912c453d3382218e69948a37`），stdout4014字节/SHA-256 `68f142c399d19d9f2eb0300612e3d68056f059d359eada91fd9bd074e3162796`。这只是恢复后续分配的资源前提，不是四项GUI实机PASS；原失败与过期窗口均保留。

A207还实际回收370份已结束行政快照重放用途的纯LIST stdout，148520960字节；185份非LIST输出、全部argv/result/stderr、nonce原图及READY/observer/closure/CAS保留。旧LIST正文不可恢复，不能以保留摘要冒充全文仍可读。执行和闭账均实际0；外置`a207-administrative-list-retirement-20261013-01/ACTUAL-SUMMARY.json`1359字节/SHA-256 `c5b0679eaf7b396367756fcacb9c6a6f3a9e4b0dd5a884551378370422728146`，237 CLOSED2256字节/SHA-256 `bc399785f3c4f34c20681d88d0e1b5161081311f0d3fd16a2cdb35e993205b4c`。此为明确提前用途退役，不是TTL已到、可重建或同SHA副本论证。

原52空间准入也实际暴露同一未启动前驱的不适配：首次A208准入因假定`original_launch_pin`存在而在写预留前退出1。外置小carrier仅加入真实no-game前驱分支，调用已验证的公共资源函数，作为独立pin写入Root峰值审阅；不制造launch pin、不改旧normal门或配额公式。第二次实际准入0，A208正式52预留73225字节/SHA-256 `4d060b79c1c3c3ad39e259c5e9d817bbb7a4e9e93926b39b13b242b5b6b8390f`，当次free29385191424/required29265756160，保守U47876216680；未从U抵扣删除量。实际GUI验收另记，不将准入算业务PASS。

### 同日 A208 界面入口焦点修复

A208/R0098第一次run因执行者nonce转录错误在启动前拒绝；新鲜离线双nonce由实际执行者`/root/qol_remaining_readiness`亲审，第二次run真正启动CK3 PID17924，通过Song/原readonly9后，在首次UI发布前被`Current CK3 foreground/focus unavailable`拒绝。没有UI输入或四项record；失败瞬间HWND/PID未被原guard记录，明确为UNKNOWN，不借后续截图追认。后续退出置前原回执实际记录before为Steam PID13460、after为同一CK3 PID17924/HWND3016276且focus成功；这支持复用现有置前初始化，不证明失败瞬间全部状态。

原工具自动进入正常Quit，未能保留热修复窗口。其run/verify均2，normal退出及保留句柄OS0实际成立；observer15、keeper/allocator0和CAS10003后实际52 CLOSED为7815字节/SHA-256 `f9323b3f7a9cdd7a51e2ea6be23177016c26160f81f790e4ef37aba36bd8ccc3`，保守U48172919064字节。closure的字符串路径比较也曾误拒绝合法正斜杠context；只在外置closure薄层内存中规范prepared路径，原context与全部pin未改，旧失败保留。

当前仅把已经实机证明可用的无输入focus能力提取为`CaseClient.focus_retained_process`，原Quit wrapper/回执名保留；UI入口在首次snapshot前调用同一能力，保留原PID/ctime/唯一可见HWND/租约/2秒读回守卫及90秒退出预留。不放宽原UI前台条件，不授业务信用，不更换common native/runtime。受此次入口变化影响的5项离线控制器测试实际通过（`focused-controls-20261013-07/ui-entry-focus-tests-01-process-exit.json`957字节/SHA-256 `ebea24979c4eefc10c1af1327d72a778c0dee812e50a8105b8960ca07243d194`）；四项真实GUI仍待新场补验。主线CI的既有文档禁用shell字面引用另已改为不含禁词的历史说明，只对该文档运行原validator实际无违规，不重跑无关业务矩阵。

### 同日 A209 自然死亡中断与单日暂停操作修正

A209/R0099实际入口置前成功：`ui-entry-foreground.json`600字节/SHA-256 `b22d31873ca6daabb7bbe5be0463e9cb2b7e03266ebed8af0473e55d97a9a7b1`，从Steam前台切换到原CK3 PID18348/HWND2360784，没有鼠标或键盘输入。实际执行者`/root/qol_remaining_readiness`亲审并记录anchor50与保存100后重开100；关键原图为`scene-0005.png`2421426字节/`337ebd8e2bc8322d4da0063f85ec573f34b1b27d5b30c3a3be572f2170b6d7a8`、`scene-0016.png`2420942字节/`0743c8c9bbcae11f83d20d7f4f941ab9255af4350f1a0600c9d23542962e6f32`。仅2/4项成立，不注入其他场records或追认产品通过。

恢复50的Save后实际仍paused=true；真正放开时间的是随后人工HUD resume。10:43:39Z至10:44:02Z的原生日期由53145888走到53146872，23秒推进41天。随后赵曙自然死亡，原图日期为1067.2.6；先前口述2.4更正，以原图为准。HUD模板目标不再存在，原像素门禁无输入拒绝；不能把继承窗口当作原地图继续记录恢复/清场。人工正常Quit未在原hold内完成，run/verify均实际2；原normal结果保留retained signaled=false/exit=null/normal-qualified=false，不根据后续进程已消失追认OS0。最终原native报告另真实finished/cleanup，keeper和allocator实际0，CAS10052释放；这些只授资源事实，存储闭账另取实际回执。

只为这个已发生的操作故障，在原UI控制器增加无参数`typed advance-day`，复用已有`CaseClient.advance_day()`真实推进一天、自动暂停并读回完整原生帧；其24–48小时、事件、同actor/pipe/generation及原预算守卫不变。后续自然重新启用改用这一步，不再放开HUD后等待模型往返。未改产品文件、四项范围、native或common runtime。新增3项离线mock测试一次通过，回执`focused-controls-20261013-07/ui-natural-day-tests-01-process-exit.json`957字节/`eee49ebab3079635ec199f57fe7d9bb35b365825cb5003a55da5eb4ef439d6ad`；不将离线修复称为剩余GUI通过。

此前A208闭场输出另已精确回收4324文件/452195120字节：3780份生成shader、540份已结束用途的纯LIST和4条传输流。关键native/typed/error/退出/配置存档保留；544份旧LIST/传输正文不可读取，shader可重新生成但不是历史原件。实际237闭账`post-r76-a208-closed-output-retirement-01-reservation-237-closed.json`2229字节/`b75b53952efbd9e2537d7fa658b114775aee495b5af34c86ad3728d93d3afe5a`；小型实际摘要`a208-closed-output-retirement-20261013-01/ACTUAL-SUMMARY.json`2133字节/`12b58d641a280d8ed95e7d2bebaa1cb00c3ad76747a35397a894b0d07710defa`。不重复抵扣保守U或把候选量当新准入收益。

ad61be99对应官方CI38380556374实际失败于另一既有handover中的禁用shell字面引用，产品离线测试步骤已成功。只修改该历史说明的措辞，原validator对该文件一次实际无违规；不是重新开放禁用shell，也不重跑无关业务。

11:09:30Z，A209真实失败资源闭账完成：52 CLOSED8502字节/SHA-256 `b736ce6f2f141f62c74dbde375f76e1866d7aaeb8f44a93fe3a0385654b290a5`，POST6421字节/`2bb985b0413d575d96c4c6fcf497e8cb17bc1cb123e51f3765af2f519b89c0b4`。三项公共资源closure均true；原native报告实际status GREEN但shutdown OS1，原normal结果仍为unsignaled/OSnull，observer实际2/VOLUME_FREE_SOFTSTOP，分别保留，不互相追认。保守U48804689792字节，新增闭场路径上界610799208字节；没有释放未来业务信用。

随后只回收已明确结束用途的3913个精确文件，714109744字节：3800份生成shader、A199/A200/A202/A209共16条传输流、82份纯LIST、13张非关键导航中间PNG，以及A209生成的`last_save.ck3`和`save games/autosave.ck3`。两存档不属于原37输入且旧角色恢复/seed用途已结束，后继均fresh fixture；不宣称它们同SHA或可重建。113份原始正文/图像/存档已不可恢复；关键成功读回、restore50、死亡、guard/normal/pressure、typed/完整native报告、配置和continue历史原件保留至10月18日复核。没有删除目录或未列入文件。

该回收实际admit/execute/close均0，5批、24.7761秒、无大正文hash；11:21:46Z实际237 CLOSED2231字节/`0130265b9775c1a290a6e8c303f3a54350bd5340771bf786591dbf15d3134968`，实际摘要`a209-closed-output-retirement-20261013-01/ACTUAL-SUMMARY.json`2134字节/`e483873afaea82549f3d04ca6cce7672d8e48a5d6601e7670964039486f4d89c`。全包16MiB仅收费一次，下一保守U48821467008，不抵扣删除量、不重复收control费。11:22Z freshfree29414191104字节；全卷变动不全部归因于本次回收，下一场仍需原锁内实际准入。

d750fa735对应官方CI38387841505已实际completed/success；只绑定该提交。后续剩余功能验收和两产品正式发布、真实缓存加载、永久changelog均仍未完成，不把CI或资源闭场标成发布完成。
