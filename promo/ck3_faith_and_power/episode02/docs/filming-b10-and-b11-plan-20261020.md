# B10朝圣规划、B11生产资格与B12装备实拍

## 10月20日11:05：B11生产资格完成，B12装备／卸装已观察，供奉未执行

`machine_id: 4-8e1c2f1861`，本节依据截至`2026-10-20T03:05:27.175574Z`的[B12闭场清点](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b12-a01/STORAGE-CLOSURE.actual.json)。B11固定native编译源`6665fdeb`的新DLL为15,521,792 B，SHA-256 `6f25cc1ed08d3f1169c85ae5e9c20a6a89fb7a92d7666323092299460206eb2c`；[15个有限原生目标](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b11-a01/qualifications/revision-a03/PUBLIC-RUNTIME-QUALIFICATION.expanded.actual.json)原等待均0。[朝圣SDK38项](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b11-a01/qualifications/sdk-seam-preparation-a01/actual-a03/sdk-pilgrimage/RESULT.actual.json)、[库存body5项／15个consumer组合](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b11-a01/qualifications/sdk-seam-preparation-a01/actual-a03/inventory-body/RESULT.actual.json)及[当前公共native consumer](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b11-a01/qualifications/public-native-consumer-a01/RESULT-a01.actual.json)分别实际通过，库存outer明确模拟；这些资格不合成实机数量。当前公共输入源`befd887f`与原DLL编译源分别绑定，B10报价、Start、付款和旅程的缺口未因构建通过而关闭。

B12运行`4-8e1c2f1861--faith-engine--R0006`，同一CK3 PID7496／connection generation1，玩家15893、date_raw51394920。[原first-four结果](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b12-a01/live/4-8e1c2f1861--faith-engine--R0006/case-output/firstfour-integrated-result.json)因Python消费者假定公共row含before帧而PARTIAL；同进程hot修兼容只读after形状后继续，原失败保留。后继[hot结果](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b12-a01/hot-recovery-a01/case-output/firstfour-integrated-result.json)取得两人物原文及库存Open sequence39的独立post=true，但选到court物品237，被个人物品／空合法槽guard拒绝，没有强行装备237。Root只读核对188、189、237、267、277五件，267是其中唯一个人宝物栏物品，位置为礼器。

实际物品267装备只提交一次，sequence52的初始回执仍待后验；随后独立`b12-equip-post52-a01`为desired_inventory_state_observed=true，另一独立item267读取为equipped=true／slot1。卸装只提交一次，sequence57的独立post同样true，另一读取为equipped=false。来源：[原native-report](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b12-a01/live/4-8e1c2f1861--faith-engine--R0006/native-report.json)中的同名steps及`b12-equip-independent267-a01`、`b12-unequip-independent267-a01`；[装备初始回执](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b12-a01/personal-resume-a01/case-output/r0006-personal-a01-firstfour-004.actual-results.json)不能单独代替这些独立后态。267虽显示名“先知斗篷”，原版类别为“卓越级礼器”，不与旧237混同，也不称穿戴斗篷或宫廷台座展示。上述证据只证明个人槽状态，人物净收益和单站归因继续未证。

供奉仅完成选物与报价读取；`02:42Z`拟交公共队列时，原hold已在`02:39:53Z`结束，队列拒绝。`enshrine-once`的意图稿／plan不等于提交，原native-report没有供奉动作调用，不声称物主转移、圣地槽变化、付款或供奉后收益。[闭场直接审阅回执](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b12-a01/STEAM-OFFLINE-CLOSE-REVIEW.actual.json)明确`enshrine_plan_submitted=false`；未知／未提交动作不自动重放。B12不包含普通圣地升主要圣地，类型拒绝也不关闭同地点冲突槽。

唯一[原片](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b12-a01/captures/b12-items-a01/raw-gameplay.mkv)为119.966秒、85,394,970 B，SHA-256 `1ed602e607f180199aba15afaffbdf91fd1fca68387910bb4375d3ef2703fc26`，2560×1440、无音轨、VFR。[媒体QA](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b12-a01/media-review-a01/REVIEW.actual.json)实际strict decode0，半开原PTS`[26.000,32.000)`共122帧已全审，只签同一物品进入个人宝物栏礼器位置的6秒source转场；字幕与最终合成、整take及全case未签。卸装及供奉准备在take之后，仅保留PNG／native，不能剪成同一段连续实录。

原hold到期自动清理后，[公共run原等待2](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b12-a01/commands/run-a01/execution.actual.json)、[原host等待0](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b12-a01/live/4-8e1c2f1861--faith-engine--R0006/host-original-process-exit.json)、[allocator原等待0](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b12-a01/commands/allocate-a01/execution.actual.json)分别保留。[normal-close](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b12-a01/live/4-8e1c2f1861--faith-engine--R0006/case-output/normal-close-result.json)为false，未取得CK3正常Quit或保留handle OS0资格；host0不能替代。Root直接审阅fresh Steam新图确认离线，[显示恢复](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b12-a01/DISPLAY-RESTORED.actual.json)实读1024×768，[screen CAS释放](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b12-a01/SCREEN-RELEASE.actual.json)于`02:53:56Z`完成sequence12550。进程和屏幕已释放，整场业务仍PARTIAL。

容量方面，[B10 profile精确回收](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/reclaim-b10-profile-execution-a01/EXECUTION.actual.json)3,765项／226,186,032 B、[B11非S14中间物回收](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b11-a01/qualifications/intermediate-reclaim-execution-a01/EXECUTION.actual.json)867项／435,147,408 B已执行，原件不可读取；原日志、原片、DLL及14份活跃S14支持对象保留，不自动回填旧grant。B12闭场分配上界560,955,392 B已包含profile、原片和QA，不叠加各子目录。

闭场后的Python修复已落当前Root：[first-four21项](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/b12-firstfour-root-fix-a01/CLOSURE.actual.json)实际PASS、0skip；[A1 after-only15项](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/a1-builder-root-application-a01/DELIVERY.actual.json)实际通过；五个capability规则的10项有限factory／Selection检查按原同源回执复用，未新跑完整builder。[R19事件兼容](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/r19-after-only-row-compatibility-a01/ROOT-APPLICATION.a01.actual.json)复用同源6项窄检查，Root实际import0，不写新跑6项。旧失败和B12实际原件均未改写，本轮不要求重建未变的native DLL，也未重跑native／SDK大套件；这些源码检查不关闭A1／H2／P3结果槽。

下一场B13仍需新grant、当前Python源码冻结与公共来源绑定，再补供奉、A1受控对照、H2领袖建制和P3完整朝圣。runtime／来源研究、案例输入和画面审阅继续并行；下场拟由filmingprep单机独占现场全流程，连续承担准备、原图审阅、合法once动作与正常Quit／闭场，减少跨代理手动交接耗尽hold的风险，保留审图和独立后态门槛。现有9:25.888样片、65条固定声音23:32.267、正式51／65视觉绑定和24项required未全闭的口径不变；本轮6秒source QA没有直接增加正式绑定。约27–30分钟仍是补800–1600字真实案例后的预测，案例配音和全片审计待证据gate完成。

## B10原场与当时后继计划（00:15截点）

machine_id: `4-8e1c2f1861`。运行`4-8e1c2f1861--faith-engine--R0005`，实际闭场截至`2026-10-20T00:15:35Z`（北京时间10月20日08:15）。本场采用B9生产DLL；新增事实止于类型确认、目的地选择及正常闭场，没有出发或完整旅程通过。

## 本场实际推进到哪里

stage1的`selected_pious=true`已由独立原生读取确认，Root审阅当次原PNG后，一次类型Confirm进入stage2。Rome／province2577的`can_select=true`，实际选择后进入stage5，再次独立读取保留同一目的地。这个Confirm只确认朝圣类型，不是Start，也不是付款。来源：[类型确认](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b10-a01/live/4-8e1c2f1861--faith-engine--R0005/case-output/ordinary-pilgrimage-0007.actual-results.json)、[目的地可选](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b10-a01/live/4-8e1c2f1861--faith-engine--R0005/case-output/ordinary-pilgrimage-0008.actual-results.json)、[实际选择](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b10-a01/live/4-8e1c2f1861--faith-engine--R0005/case-output/ordinary-pilgrimage-0009.actual-results.json)与[独立stage5后读](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b10-a01/live/4-8e1c2f1861--faith-engine--R0005/case-output/ordinary-pilgrimage-0010.actual-results.json)。

`quote0011`及Root后继`b10-quote-refresh-a01`均为`unavailable / typed_full10_quote_unavailable`，`quote:null`。后者的队列提交退出0只表示一次提交完成，真正领域结果在原native-report同名步骤中仍不可用。Start意图和调用都为false，钱包仍243金币，未取得新活动身份、付款或journey。[原quote](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b10-a01/live/4-8e1c2f1861--faith-engine--R0005/case-output/ordinary-pilgrimage-0011.actual-results.json)、[含refresh实际步骤的native-report](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b10-a01/live/4-8e1c2f1861--faith-engine--R0005/native-report.json)与[本场结果](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b10-a01/live/4-8e1c2f1861--faith-engine--R0005/case-output/ordinary-pilgrimage-result.json)分别保留，不改记成功。

GUI的70金币不能代替完整报价。B9将成本读取内部失败合并成一个错误，本场不能据该字符串唯一确定失败分支，也不能推断余额不足。后继源码审查定位到当前planner之外额外要求HostView activity-key的守卫；B11拟作窄修并增加内部诊断，同时保留类型／人物／选项、全部十资源成本、真实CanStart、两遍稳定和配置指纹检查。具体实际原因仍待新诊断构建及新场原生结果验证。[窄修来源与边界](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/b10-stage5-quote-diagnostic-a01/DIAGNOSTIC.a01.md)是源码候选，不是报价已修好或新的构建通过。

## 原片与三段可选画面

[本场原片](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b10-a01/captures/ordinary-pilgrimage-start-a01/raw-gameplay.mkv)实测114.800秒、97,564,894 B，SHA-256 `c66a01f471a95ea5cf6821dcde876200ef6e8caaaed79bb81eefbb9974e48d23`，2560×1440、无音轨、2,308个VFR原帧；严格解码通过。原PTS取自实际源帧，不用帧号÷30或mark偏移。[媒体QA原件](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b10-a01/media-review-a01/REVIEW.actual.json)SHA为`f3565b0ac3f61faa86b812839472dcab8304cfaae91f28e1944e621af32d326b`，只登记候选，未授整段clean或最终布局签核。

|原始PTS候选|实际画面与可用语义|必须保留的标注/限制|
|---|---|---|
|45.000–51.000秒|stage1虔诚／世俗两类型卡|“朝圣类型选择｜尚未出发”；不能充作目的地、费用或结果|
|80.000–86.000秒|实际类型Confirm之后的stage2目的地选择|“类型确认后：选择目的地｜尚未出发”；不要沿用B8的“尚未确认”|
|100.000–105.967秒|已选择native Rome2577，GUI目的地显示梵蒂冈的stage5旅行/活动面板|“罗马目的地旅行规划预览｜尚未开始・完整报价未核实”|

stage2／stage5中下部地图有马切拉塔hovertooltip，不授整帧clean。它不是Rome2577拒绝证据，不能把该tooltip、本场可选的罗马和GUI梵蒂冈混成一个地点。后期优先保留有语义的面板区域，仍须窄片段与1440p字幕布局审阅；三候选不增加当前51条合格绑定，也不关闭required结果槽。

## 正常闭场与原失败分别记录

Root用原版typed Quit，独立保留进程观察确认CK3 PID15128退出0、cleanup完成；原host实际Popen.wait0、公共run0，成功allocate-a02的原父进程实际等待keeper0。首allocate-a01曾因预分配目录问题退出2，原件保留，不能写成所有分配均成功。来源：[正常闭场](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b10-a01/live/4-8e1c2f1861--faith-engine--R0005/case-output/normal-close-result.json)、[原host等待](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b10-a01/live/4-8e1c2f1861--faith-engine--R0005/host-original-process-exit.json)、[keeper原父进程等待](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b10-a01/live/4-8e1c2f1861--faith-engine--R0005/keeper-actual-parent-exit.json)及[成功allocate-a02](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b10-a01/commands/allocate-a02/execution.actual.json)。

闭场[Steam当次新图直接审阅](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b10-a01/STEAM-OFFLINE-CLOSE-REVIEW.actual.json)确认离线，窗口位移新鲜度证据另存于所引原件；[显示模式实读恢复](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b10-a01/DISPLAY-RESTORED.actual.json)为1024×768。`00:15:35Z`[screen CAS释放](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b10-a01/SCREEN-RELEASE.actual.json)为done／sequence12500。这些是退出与现场释放事实，不授朝圣业务成功。

## 已完成的离线接线与仍待B11的资格

observer原6目标／68 owned场景不重跑、不改分母。其后人物链完成core17、serde13断言及2个真实序列化body语义、真实parser／protocol15的独立build/test0；原wire RED保留，仅修正夹具对合法JSON换行转义的断言，生产serializer未改。以上计数分别代表场景、断言、body和请求检查，不能相加为实机用例总数。[Actor原生有限结果](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/observer-owned-fixtures-a01/ACTOR-RESULT.actual.json)明确不授实际工厂、getter ABI、owner／TLS、loaded DLL或两人物实证。

[Actor实际body到SDK](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/actor-native-body-sdk-consumers-a01/SDK-NATIVE-BODY-CONSUMPTION.actual.json)另为2个body、6个consumer组合通过：真实生产serializer输出被原字节消费，但Query DTO、outer／hello／snapshot为明确模拟。它与既有GHW body9／27组合、朝圣SDK38及Root生产器33分别记账，不证明原生工厂或游戏后态。单站归因继续false/null，直到原版说明实际标出所选站点并取得独立绑定。

并发路现在由已完成源码进入B11组合验证：observer／actor／inventory的接线与stage5报价附加守卫窄修共同准备新输入；有限消费者、人物/物品来源研究和前四章组合case并行，生产构建与现场仍按冻结版本和容量准入推进。[B11准备自审](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/b11-build-preparation-a01/SELF-AUDIT.actual.json)仅为source-plan通过，[inventory接线交付](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/inventory-open-global-integration-a01/DELIVERY.a01.actual.json)也不代表新DLL或实机已通过。

下一步先合入并独立审查B11源码，运行所需有限验证、构建新生产DLL、核当前SDK与loaded来源，再以新runtime／新额度取得独占现场。前四章组合case要在同源起点核库存/个人位置、物品说明、供奉前后owner／槽位／钱包，以及两人物真实属性与来源；打开inventory不等于装备，读到总属性不等于单站净增益。朝圣则先取得完整配置报价和真实CanStart，再决定是否一次Start、付款、抵达与归返；未知动作不重发。没有固定现场ETA，按每个gate的实际结果继续重估。

## 当前片长与交付边界

[前四章9:25.888样片](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/sample/render-a02/native-run/derived/direct/episode02-review.mp4)已可审阅；七章65条固定声音展示实测23:32.267。完整首版仍以约27–30分钟为作者目标，实际案例声轨和完整影片时长未测。51/65视觉绑定、14个实拍位及24项required结果绑定仍待补齐，正式全片未就绪；本场规划进展与后继软件资格不改变这些门槛。
