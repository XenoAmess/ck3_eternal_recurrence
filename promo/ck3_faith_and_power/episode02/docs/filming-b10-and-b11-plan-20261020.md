# B10朝圣规划实拍与B11后继验证

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
