# 礼与道 R10 实机验收终局记录（2026-10-06）

**R10生命周期已实际闭合，Phase1总体仍NOT_GREEN／未完成。** 本局完成限定的一次正式JOIN与一次正式DETACH；第二JOIN、完整JOIN→DETACH→JOIN循环、R11冷载持久性与C3／I3b／修习切人／I4正式矩阵未执行。本报告允许保存真实RED与NOT_RUN，不把正常退出当业务总验收通过。

冻结源d0f8fa3b9d444828759443aa018bfd7ad31b398d，stock1.20.0.3，production70＋fixture52；本局actualPID13436、create1791196395.7422996、creationFILETIME134356699957422997。实际SDK1–253、254Client关闭标记均有原request／response／SDK／native／本地收据映射；requestId与sequence在原0030工具名拒绝后错位，仍按真实两个字段保存。历史报告001–004、cut150及149补充、151–200ledger和全部坏attempt不改。

## 业务结论

首次实际JOIN仅授给nonce14：171为opening，187为sourceSigned／targetRequested／targetSigned均1的三签授权，189正式commit→190 typed lyd.228→191ACK→192独立保存183检查。joins1→2／detaches2，扣300G／1500P，钱包1543／5650／2200→1243／4150／2200。Rite169 parentFaith106→104；Faith104 mainRite159是另一字段。actor31254及sourceNPC65865随169转104，targetNPC65866仍104／159。旧Faith106创建backupmainRite187，完整tenets与旧169一致；既有heads、完整tenets、政治7title、person、actorlanded与playable保护成立。169HoR31254、transitionCD1825、ownerreleased、reset5、XP0。保存body留外置，191ACK及193行查询本身不授结案／冷却禁用信用。

原前七轮仍分别保留：两次接收签署拒绝与五次取消；NPC票的identity省略保持NULL，不补0、不推随机draw或AI具体原因。171原owner-only RED及新增targetRite159合法当轮票counter资格证据分列，不能改写原失败或倒填precommit／final facts。

第一次DETACH的201–216实际事件／withdraw trace保留，但没有独立保存，**不倒填AST result3**。第二次nonce16：235独立source签署／source2of2／player1of1授权，237 formal native1／publicoption2→238 typed100 lyd.228→239ACK→240独立保存120检查。DETACH2→3、JOIN2保持，扣200G／1000P，钱包1243／4150／2200→1043／3150／2200。新Faith107 mainRite169，169 parentFaith104→107；旧104 main159及106 main187保留。169HoR31254，但107 HoF invalid／无headtitle，**不能称actor为HoF**。transitionCD1825、ownerrelease、reset6、XP0以及全registry合法关系／tenets／heads／政治7title／person／actorlanded／playable保护成立。仅本轮16记1次正式DETACH。

196fixture confirm原RED（actual frame crossed）完整保留；197独立观察／198typedfixture.4／199ACK／200保存证明操作实际reset5→6、169transitionCD删除，schoolCD349保持。未验证的原claim未清除或覆盖，因此243新的reset confirm在派发前被安全门拒绝：`decision action already claimed with an unresolved result; no retry at any revision`。**243无新reset派发**；244fresh仍public112／native111／noevent，钱包1043／3150／2200。不能把196后验reset改为原调用PASS，也不能把243改为fixture又成功。

第二JOIN本轮NOT_RUN，完整循环未完成；下次session可从actual240同campaign续测。显式fixture reset不等于自然五年到期。193action_qualified=false是serializer恒值，当前query没有enabled／is_valid字段，MCP直接禁用或CD rejection未观察；源码＋保存的CD资格推断另列。

## 实际生命周期闭合

245只读query→246prepareunknown→247freshsnapshot→248stage查询→249continueonceunknown→250freshsnapshot→251query→252confirmonce→253**同原retained HANDLE**只读observer。原HANDLEtoken c3d6cb9a49b45eacdd12e64815c8f49a，waitsignaled／exit0／typed_normal_exit=true，observer native_submission_count0并dispose；未知dispatch返回与后续真实终态分别记录，没有重发prepare／continue／confirm。autosave_verified=false，最后保全业务存档是240，不伪称退出autosave验证。

254实际Client close／sessionclosed，OS process census证明CK3／Client／keeper全absent。keeper STOP→FINAL thread_exited=true、failureNULL、lastseq3160；freshCAS3160→3161 DONE、resources[]，freshlist无holder，ROOT据实际闭合释放source freeze。**Client与keeper的OS exit code未实际取得，均NULL／UNKNOWN，不写0。** 原keeper FINAL里的screen_released=false是CAS前事实，不能单独替代后续3161 release收据。

## 日志与未完成范围

日志包名称r10-log-preterminal-cut244-readonly-review-20261006-001保持历史原样；最终收据证明其UTC18:07:35单次capture发生在18:04实际游戏退出及Client sessionclose**之后**。cut244表示业务数据范围，并非实际capture阶段；本报告追加时间勘误，不重写旧包或重读live日志。

新error.log138556B，SHA2da1ee0f6bb1469b250707790d0abd221d1b32f0e395ae221988cb3e1e59ed1a；debug.log666846B，SHAd8174957720cceaab1c1044c3defbdf1a8300037234f35d3c69141720b4a8460。578个完整unused记录／289签名各2次均绑定重新核SHA的I4fixture，production0；捕获字节内runtimeeffect／trigger／scope错误0。12条其他W（3bookmark＋9holyorder优先级）及账号无token、camera、占位材质等debug问题原样保留。**cap／truncation／后期持续coverage／flush完整性仍NULL，无whole日志GREEN或整体产品PASS。**

实际release编译成功，但outerbuildREDexit1／Defender一次注册失败effectivenessfalse保留；礼与道静态159／static70／repro属于已封sourceL0。通用CI两历史文档名称失败仍RED，最小两文件修正候选留外置，本包不改main或复跑CI。launch001argcase／002refpathbug、nofork检查与003actualonecreated、等待超时却后来返回而未重发、错误期待值、prequeue拒绝、reader期待key错误、helper002资格拒绝等各自保留并区分作者／reader／环境／业务来源。

C3宗主／挑战者／death／reload，I3b正式dynamicFaith仪式，修习切人四mutations，I4正式144product矩阵与R11冷载持久性均NOT_RUN。inert helper、离线构建、源码匹配和MCP ACK不能替代这些业务事实。

## 证据与导入

本候选只新增SDK201–253及254close原件核查，旧1–200 raw body／90MB存档／AST与旧测试不重扫。SOURCE-REFS复用旧ledger及认证sealed INDEX全部payload映射；所有大保存只列外置路径、bytes与历史SHA。ROOT-only importer按originalSHA短路径保留全部所列必要原件；原字节单次读、hash核对、lossless gzip并当场解压SHA验证，生成真实storedbytes／SHA和ORIGIN／INDEX，避免长路径与伪造压缩摘要。候选及旧失败均append保留，主树／Git／游戏操作仅ROOT执行。

关键原件：[192 JOIN 183检查](archive/9f0b3463d523081d4613100da6c8712bc2e10cb25b13c4aad69c7bbd49ca33c1.json)；[235授权](archive/d9ef009f34e5cd4ea190de9419c68f1011a35f3360a4675096003b94281445f0.json)；[240 DETACH 120检查](archive/9da63fb2b9eb045c6c9609638edec6071411bbd1592cee20be8bbce772701239.json)；[ROOT终局边界](archive/898fd997fbbaac6bb127a5d8f9f080077baf545b24b990db7d6d4c6811b6000c.json)；[生命周期闭合](archive/7f5fe972d0166c29981d5e10a2869ba7844f557faffdb04127997d6cb347af4d.json)。
