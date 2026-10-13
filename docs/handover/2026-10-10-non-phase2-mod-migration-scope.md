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

### 同日 A210 重整河山 D3 实读与导航边界

A210/R0020沿用同一Source20，实际D1完成原24小时自然区间，Chaos回调一次；当前两事件由原typed入口分别消费，没有重放日控制或D2 dispatch。D3实际`effective_single_heir_qualified=true`，表示`realm_baseline_no_override`：actor34422、Later title18371、日期53144400、engine first heir37989、own law count0/laws[]。原`script_own_single_heir=false`与`holder_realm_single_heir=true`分别保留，不把空own-laws改判成任命法。资格原件`R0020/case-output/rmtm-effective-law-d3-qualification.json`561字节/`936a7a6254cb0a459efd04b14c1ca9ccbfe0fdb1db254490229cee1e316efdf4`，仍为source_pass/business_pass=false；不是核心D8或真实继承通过。

自动到D4的owned-GUI await后，执行者调用已注册`ck3_open_character_window_v1(character_id=34422)`，共同host实际报工具错误并自动退出。选定Source19的`ingame_ui_contract.py:85–88`只给当前1.20.0.4的character/query只读例外，character/open进入`current native UI supports army query and select only`拒绝；`native_driver.py:5650–5651`的opener确实走此路。表面注册不证明当前backend支持。原错误和自动结束事实保留，无法追认已不存在的热修复窗口；没有九卿预算签核、Continue或真实继承动作，没有产品失败的证明。

下一场仅对已实证不支持的角色/头衔/领地/九卿预算导航使用当前原PNG和规范坐标映射，其他已qualified的title-holder/own-laws只读及Decisions open/query/select继续复用。决议Confirm不得误调用仅白绮白名单的`ck3_confirm_ingame_decision_item_v1`（选定driver6624–6627）；RMTM按既有通用outcome合同或亲审当前原图映射点击。此为操作路线纠正，不增native、平台、业务门槛或全矩阵，不重跑已有静态结论；新动态头衔的当场身份与原physical AND仍须真实绑定。

A210 public run/verify实际均2，native实际OS1、tree/job/control清理完成，normal/retained OS资格未取得。observer实际15、keeper/allocator实际0及CAS10080后，真实52 CLOSED8393字节/`c202bd68f21a5ac1335098dd1b9da480011b060d9646a9061a692a399bd5f76e`，POST4851字节/`0f802e6c6445da4b9ca2a4be1fa428c05bd20d99d2d559e71f0cae1190372dda`；closure3全true，保守U49040981656，新增215058200字节，不授normal或业务PASS。关键原件由迁移执行者保护至10月18日复核；当前空间足够候选场，仅在下一次锁内准入确认，不为此再清理同一批文件。

### 同日 A211 调用格式失败及实际资源闭场

A211/R0021使用全新profile和同一Source20，原readiness在273.78秒内进入hold；D1提交行实际完成24小时，日期53144328→53144352、actor34422、after paused=true。执行线程容量错误恢复后，当前事件查询计划误用`arguments`而非宿主实际读取的`args`；所需`event_instance_id`因此未传入，MCP参数校验失败并自动清理退出。错误计划原件253字节/`38f58636990e46be4760489af732ef11cf6272d2121810e24e88ff42245b2574`完整保留。没有事件选项消费、D1重发、角色导航、D1审核签名或核心通过信用，不把测试调用错误归为产品失败。

Root接管纯资源闭场：run/verify实际2，native报告8063469字节/`cbb86f50e5c1d2308952085e9033913981dbadb464adfcf05d6e543481d39507`，CK3原实际OS1、cleanup=true，无normal0。observer实际15、keeper/allocator0及CAS10119后，真实52 CLOSED8394字节/`6731b7c5db5daef52521f23b0651979f51fa27c9a06e1cd8feeeb5db8ef9da37`，POST5139字节/`dbe8cb1048d5e0b8d13a6ef5562b5eb2754b3f238698af2d61149b78856f745a`，closure3全true。保守U49263656992、新增218481032字节；free29053530112字节仍须下一场锁内重新准入，不从失败闭账推定空间或业务PASS。原件保护至10月18日复核，当前只评估两个已闭场的生成shader，不回收关键事件、图像、配置或报告。

`ck3_mod_acceptance_queue_control.py`仅增加入队前拒绝`arguments`及非对象`args`的输入保护；正确计划字节、失败生命周期、一次提交和原host预算不变，不修改冻结Source20或产品业务。对应六项合成调用器检查一次实际0，回执`focused-controls-20261013-08/queue-args-guard-tests-01-process-exit.json`963字节/`786b668c13f87970261e9122a05caaec1aa07caddd0f4ec92b4cff1645b9c7e3`；这不是新增功能实机通过或全套静态重验。两产品仍未正式发布。

### 2026-10-13 用户新增本机 Steam 联合发布门禁

用户明确要求：体验优化与重整河山两款发布前功能验收全部完成之前，**这台机器禁止 Steam 上线**。本机继续离线开发与实机；不得因为其中一款先通过而提前联网上传、下载或做在线发布准备。先前单款先发布的计划取消。两款实际发布前验收均完成后，才允许同一联网窗口统一提交两产品、公开完整Notes/tags回读及真实下载缓存核对，网络工作完成立即恢复离线；后续缓存实际加载仍先取得当次新鲜离线证据。此门禁只约束本机Steam，不外推为其他机器已获上线授权，也不把代码、CI或局部实证当作两款验收完成。

### 同日两个 shader 回收与 A212 原图时效拒绝

Root亲审新精确作用域和producer后，A210/A211已无恢复或未来seed用途的两个生成shader根按原237流程实际回收：7560文件、315999840分配字节、8批、43.7783秒，admit/execute/close均0，未删目录或任何非cache原件。源10874字节/`72757e467cc077cb0b25482b1f16589f395d8b0f45335d83e19ed8adeb15a88c`；小scope5223字节/`f1a1d49d91fa3d7c52c0e5c456e5385cb6d96a42b69634d36b0396ef2f549f39`；实际237 CLOSED2216字节/`219f6bd5e27858412a0f093759e280a6aab042596cd36598c91b89af2d1972e4`。保守U仅加一次16MiB到49280434208，未抵扣删除量或另收控制费；旧shader原路径不可读，可重编新cache但不保证历史字节恢复。所有事件、原图、typed/native、fixture、save/config与失败闭场证据保留至10月18日复核。

A212/R0100为Root实际reviewer。Root亲审本场两张1920×1080原始挑战图，读回`eb710ea38380`与`6b06fa9f0798`及同图Steam“离线模式”；只证明当次挑战像素响应，不把停滞任务栏时钟称为新鲜。Steam恢复非置顶/最小化且未改模式后才启动。UI实际读到原门槛50%，设置100并执行原提交按钮；通过既有`advance-day {}`逐次24小时自动暂停，十自然日后原队列完成、设置按钮重新可用。没有手动HUD长跑、变量清理、改信代设或原版公式复验。

Root随后准备重开时，action0020的plain映射点击引用原图已超过60秒；canonical mapper以`SourceImageAgeError`在输入前拒绝，未发点击。controller保留错误并结束；只有anchor记录，不给100重开、恢复或地图清理信用。原自动正常Quit实际成功，retained OS0/native0、managed/thread/cleanup=true，业务失败保持。委派`/root/a212_resource_close`仅完成资源闭场；正常路径仅作原消费context路径规范化及verify/stop_keeper/release的精确delegate actor元数据适配，不改原回执、不重跑verify、不放宽身份/占用/退出守卫。run/verify实际2、observer15、keeper/allocator0、CAS10202后，POST8676字节/`caebccc4ef6719deb81f9d0513382a5fe769a74408b641500c790f73b8235aba`，52 CLOSED7816字节/`5baa078174caa9443fdab5f19404fc4a12f215cf7b48170fb6c46294aebc8390`；closure3全true，U49737368488，新增452739976字节，仍非业务通过。

下一轮保持同一四段合同和Source20，按钮优先复用已有的本场亲审模板与实际新捕获像素校验，不能跨run迁用图片或扩大原图时效。当前预算与空间须重新核验，不把正常退出或十天推进算作UI完成。本机两款全部发布前验收前Steam禁止上线的门禁继续生效。

### 2026-10-14 00:21 北京时间：旧测试输出精确退役

下一场空间不足时，没有降低系统6GiB、安全20GiB、OTHER6MiB或UI1.25GiB预算，也没有把历史已删的大报告重复算作候选。只在这两个产品的既有范围评估：当前七项业务与R33/R36、R17 D8唯一原件、当前模板、Source19/20和A210/A211/A212代表故障证据继续保护；明确结束旧全量UI、重复正常退出导航、行政LIST及已被后继替代的传输全文重放用途。

Root亲审新producer、压缩scope的46组精确边界及reference-only计划后，原237的admit/execute/close均实际0。实际回收4538文件、807805744分配字节，5批、35.1970秒，正文哈希0：A212生成shader3780份，另758份已退役LIST/旧退出及导航PNG/传输流。目录未删，所有计划外对象和当前输入保持。旧758份原始全文/图片不可恢复；shader可重编，不声称能恢复历史字节或重评旧GREEN/RED。

外置`closed-old-qol-output-retirement-controls-20261013-01/retire_closed_outputs_01.py`8179字节/SHA-256 `d3ff4da6ad26983f31c5a50aceba2c0261489ef066f38972777a85fd672393db`；scope50396字节/`3894447faecd6203261ed43f390e09e769689cf2fa4268a281872a87e3c5fc46`；计划1804字节/`63e4aa40da4a327c8d6157abea0b40830b53ab7731622719326c01cfd8858e52`。实际摘要`closed-old-qol-output-retirement-20261013-01/ACTUAL-SUMMARY.json`2155字节/`bd54e01c3088a558a86f617ab2e09e4dd580965788b0680cdabbb7c37e1fc008`，237 CLOSED2244字节/`76e99fb1c32824716c6f2c00cf9f464015035bd0476ed2dca5fc9f87c77b81dc`，实际execute parent1011字节/`ca550be3fc368113902dffdfb42f9da0e4b21d2e5b2419662051b91f694f2c7c`。三阶段原wait和各批小回执均保留；控制子额度131072包含在本包16MiB中，不另收费。详细metadata于10月18日复核，小型回执180日复核，不自动延长。

保守U当前只加完整16MiB至49754145704，未抵扣删除收益；后续如核销必须证明原已计入的精确对象与实际删除，并且只抵扣一次。操作前后卷free差额不排他归因于本次回收；00:21实际free29625028608字节，下一UI预计required29265756160，但仍须新的锁内准入。此为容量恢复，不是产品功能通过。9b3d7e9的官方CI38414967231与线性历史38414967365均实际success；剩余验收仍为XQOL UI四段及RMTM两个cell，发布仍0/2，Steam保持离线。

### 2026-10-14：A213 闭场与受控轻量 UI 夹具

A213/R0101的实际执行者为`/root/focused_ui_operator`，Root只审容量，不冒称亲审GUI。实际只记录anchor50；真实Save100触发原生产异步队列，33次单日推进均实际自动暂停，最后设置按钮重新可用，但未在原期限内完成重开、恢复及清图。run实际0、verify2，正常Quit及retained OS0成立；不能将这三个资源结果算作四段业务通过。观察器早在第11次采样、约300秒处以`GUARD_OBSERVABILITY_LOST`退出2，原错误仅保存`FileNotFoundError(2)`，没有路径或堆栈，确切丢失对象UNKNOWN。不得事后声称observer15或全程监测合格。52 CLOSED8446字节/`e1d20fbdc8bb2b8ed814859ecccaec4034f8f554f74372b507ed451138c50d4c`，POST5666字节/`93f83cd8db248ec27a0d031dc0908c6fa978d934cbb53c252e099c5a485c4fd4`，closure3全true、保守U50275830128；历史业务仍false。

下一场仅减轻测试夹具：保留真实Song actor、原faith/政府/头衔、正式27文件、Source20、readonly9、四段顺序及原预算。启动前只把三个生产接收域中的AI courtier/vassal-or-below/tributary faith对齐玩家，显式标注`controlled-zero-recipient`准备；实际零池及引擎效果仍须新实机确认。Save100仍走真实生产派发与自然finish，不手工清pending、改门槛或候选旗标；UI开始后禁止改信。既有异步业务结论不重跑。新增唯一shape/inverse测试实际1项通过，逆移除seed块后原启动正文1579字节/SHA-256 `4f6591f18068e9891b0e49ec7ddd791d63b3b64b10fcaa84717f0c139b1b7ca5`精确一致；不是实机PASS。

监测只针对实际缺失错误增加受限处理：枚举后stat/open的文件消失，必须对同一路径再次lstat确认不存在才记为已消失条目；仍存在、访问拒绝、未知对象、必需根不可扫描及原native身份/分配门禁继续失败闭锁。最多保留16个路径例子，不读业务文件正文、不降低阈值、不抵扣容量；此为非原子扫描的竞态修复推断，不声称已确定A213的缺失路径。单项生产open路径回归实际通过。后续观察器终止须及时停止业务并按真实退出闭账。

本次另实际回收3948文件、524997424分配字节、5批/24.6591秒：A213生成shader3780份，以及168份已结束用途的纯LIST、传输流和非关键导航/旧正常Quit原图。A213关键14图、旧records与各故障代表、R17 D8、七项业务、typed/native/error/配置/原关闭证据继续保护至10月18日复核。旧168份原始字节不可恢复，shader可重编但不是历史原件；目录及计划外对象未删。producer02仅纠正冻结01误投影的三处U数字；首次close因路径分隔符比较失败，03只在消费实际固定operation时内存规范三条路径，原证据不改，第二次close实际0。实际摘要位于外置`a213-closed-output-retirement-20261013-01/ACTUAL-SUMMARY.json`；控制和逐批小回执保留180日复核。完整16MiB收费一次，不以全卷free差额冒称本次精确收益，不把回收或新夹具算作发布完成。本机Steam联合验收门禁继续生效。
