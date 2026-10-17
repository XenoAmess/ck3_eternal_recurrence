# R04：县条件relation core2C09620的真实分支

本体已闭actual1.20.0.4 **2C09620..2C096DF**，191B/58指令/11内部jump，
SHA701c63b6a5f7ed78ce75d6a591fcc4dc0ae2464267a05a23f5b5feb3a3cd8edb。
来源机器desktop-3fevhd2-1c74096080，exactEXE
98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518。
独立native_research_plan check0后，一次22reads/244Bmetadata/191Bcode；
原字节和逐read账本在decode前落盘。两位owner确认未持/不并读该entry；
未读任何callee、未运行EXE/SDK/游戏/桌面/构建或写主仓。

## receiver、actor和第三个参数是什么

[县包装器2C09DF0](episode04-county-entry-actor-wrapper-12004.md)把
24D4ED0(County)实际返回指针放RCX，原actor放RDX，R8D置0再tailJMP本函数。
这里receiver保存到RSI、actor到RDI，R8整个64位保存到RBX，并被TEST和指针比较。
因此第三个参数是**可空对象指针**，不是县mode、布尔开关或已命名enum。
wrapper的实际值是null。

独立helper来源已证明24D4ED0返回Char-like/Characterregistry对象或合法fallback；
其优先callee语义未展开，不能直接把receiver等同于legal holder/controller。
本体直接读取receiver+18与actor+18作完整CharacterID比较。二者相同立即false，
不调用下面任何关系helper。

## 完整条件顺序

| 实际位置 | 行为 | 证明边界 |
| --- | --- | --- |
|2C0962F..963E|receiver+18等于actor+18直接false|比较完整值，不是低24索引|
|2C09644..964F|CALL28BC250；入口RCXreceiver/RDXactor保持，返回对象+20读int32；-1跳过直接war路径|既有迁移ledger称roster_pair_lookup_source176B，正文未在本包读|
|2C09651..9687|按完整ID解析registry5D1DE58，+8完整ID匹配；失败取5D1DE40 fallback|既有exact4 world ledger确认它是War registry；fallback没有额外tag/ID准入|
|2C09687..9698|selectedWarOrFallback+358 byte为0，且aux为null或**aux==selected对象**，直接true|原始+358的业务名未知；9698是JE，不是“不等”|
|2C0969A..96AA|CALL2C09580(receiver,actor,aux)，ALtrue就true|callee正文/关系名未知|
|2C096AC..96B9|否则CALL2C09780(receiver,actor)，ALtrue就true，否则false|第二个OR分支，callee未展开|

注意直接war路径先要求pair返回WarID不是-1，但registry解析失败会走原生fallback，
随后仍读其+358。不能把这一段简写为“在任意active war对立两侧就true”，也不能
以公开war active/can-end或地图标色替代+358。其余路径是两个实际predicate的OR，
没有把未知结果自动补false。

前一条工作消息把aux与selected对象的比较口误写成“不等”，已勘误。
**实际2C09698的JE74 21要求相等**。wrapper当前aux=null的结论不受此口误影响；
归档source、合同和verifier全部按原始JE处理，不沿用那句话。

## 与24E2230串接后，哪些能指导正常目标选择

mode1的sourceCounty一次、targetCounty两次都先经2C09DF0验证CoDa和完整LandID，
再进入本relation。若取得某次真实helper返回receiverFullID且等于actor，可精确
排除这一次关系；但当前publicDTO没有source/target对应的helper返回身份，
不能把holding legal_holder恰好等于actor当成已观察receiver。

现有war occupation口给WarID、province、county_title_id、holder/occupier和side，
可以构成正常军事候选来源；final countycondition给stored第一边的actual布尔。
这些没有当前receiver、pairrecord+20、selectedWar/fallback+358和两个OR结果，
因此仍不足以在任意Move前完全预测true或解释R0180哪一gate失败。

县owner的未来preview可选child可直接复用现有24E2230，绑定actualfirsthop/actor/
mode和frame，不需要先猜上述关系名；这个publisher尚属其独立候选，本文不授
当前runtime能力。保持正常只读shortlist和已广告的合法preview即可；本体没有
提供一个可以仅靠现有holder/敌方抬军值推出true的新selector。

R0180 source2635→target2645的双definition1B1、B100、mode1/false保留为实际
控制观察。它没有说明receiver是谁、具体哪一谓词拒绝，不能授R04 positive或县
实际损耗0。即使本relation三次都true，上层24E2230还有目标集合检查，不能遗漏。

本scope不跟进28BC250、2C09580、2C09780；receiver helper24D4ED0由独立owner
读取，本包只引用其小receipt。若继续取得源码，需要Root另授具名唯一entry，
不能把本体完整等同于全部外交关系语义已闭。

同名evidence目录保留完整原件及stdlib verifier。验证只核191B拼接、全部11
分支、三CALL和aux-null/相等原始字节；不执行CK3、不制造实机/clean/动态/人工
签核信用。code/knowledge可移机，历史机器与当前运行资格分别保留。


## 2026-10-17 R197 后续实证：relation original entry/return 已发布

上述 public DTO 尚未观察的描述保留为当时边界。本次后续实证见
[R197 relation wire](episode04-r197-county-relation-wire-12004.md) 与其中精确原件索引。
机器 desktop-3fevhd2-1c74096080、场次R0197/source85eb547c、date53148192，
唯一2635→2634只读preview中：source receiver34960/actor31254、pairWar4、
selected+358=0、direct gate=true、actual ALtrue；target-first receiver34232/
actor31254、pairWar-1、direct gate=false、actual ALfalse。两个 relation leaf
均available且same-thread/FullID稳定，production typed consumer已接收。

这补上了实际receiver/pair/War与原生AL的wire证据。目标War=-1后的selected
War/+358 null是合法跳过；仍未观察2C09580和2C09780各自的自然entry/return。
unknown_or_inputs=true及unknown_or_result=null继续保留，不由最终ALfalse填值。
下一窄口优先2C09580/返回2C096A8，随后2C09780/返回2C096B7；后者R8没有
在前一CALL后重装，不能沿用第一口aux合同。当前会话不热改、不重复扫路线。
县physical positive、邻接Q、自然县caller和视频clean span均不因此取得资格。


## 2026-10-17 OR 上下层的有限静态闭环

两个静态批次新增完整2C09580/2C09780（149B/107B）、2C090D0/2C096E0
（298B/149B）及H28BFD80（152B）源码。来源机器desktop-3fevhd2-1c74096080，
exact1.20.0.4/Steam25734779与本页同SHA；可移机知识不等于目标机器实机资格。
详见[统一源码与代码入口](evidence/episode04-county-or-static-12004/README.md)和
[精确portable索引](evidence/episode04-county-or-static-12004/source-index.json)。

2C09580(A,B,F)：完整ID相同false；D0=2C090D0(A,B,F)为true亦拒绝。否则顺序
短路OR：2C09280(A,B,F)、2C09280(B,A,F)、2C09410(A,B,F)、2C09410(B,A,F)，
每次明确重装原F。后两callee body仍未知。2C09780则先求H(A)、H(B)，再调用
G=2C096E0(A,B,H(B))；false后G(B,A,H(A))，只消费AL，不补入口R8含义。

D0沿A的context+318列表解析完整WarID（含registry/fallback和可空F对象过滤），
先测M(W+20,A)，false才测M(W+80,A)，随后B只查已选descriptor。因此不是
两descriptor对称OR；没有+358/ID-1显式门禁，M2494B40仍未知。

G的2911DD0/29131C0返回true均拒绝，第二调用没有重装R8；正向短路为
2C458C0(A)&&2C4BD20(B)。否则2C10020(A,&slot=F)只核返回Character magic和
ID!=-1，没有返回ID==B、指针==F或null守卫，A/B业务上下级身份未闭。

H独立原生body沿context父链接或+1B8→+C8完整ID注册表链接上行，返回终点
Character；40条可达指令/零CALL，无exact pdata。96B+64B两读不重叠，160B含8B
body后padding，不借邻函数unwind。其结构与当前Campaign/TitleHolder采用的
top_liege绑定一致；R08同入口expense-context alias不能证明军事payer。

六个新下层2494B40、2911DD0、29131C0、2C458C0、2C4BD20、2C10020继续unknown，
此前2C09280/2C09410也未展开。原始失败、H96B未闭场和首批metadata账本事后
重建事实均保留。原静态check/render不冒充新live资格；本次合包没有重跑检查。

R197实际内层OR仍unknown，physical positive仍false；不从outer ALfalse倒填。
可复用proposed Python DTO逐字归档，未接collector/publisher/Driver/生产consumer，
也不授R198或视频资格。此知识可解释已观测负例，不能代替自然到达、物理writer
正减、clean span和动态拍摄。下一观测只取P TLS内自然原调用，不额外调用谓词。


## 2026-10-17 first OR 的四方向函数增量

上节“2C09280/2C09410尚未展开”保留为当时边界；此后独立读取已完成两体
220B/360B和各16B/28B unwind。机器desktop-3fevhd2-1c74096080，exact1.20.0.4
与同EXE SHA；新code580B、metadata含unwind272B、25reads，无CALL追读。

2C09280(A,B,F)把栈context初始两个qword写为{B,F}；实际2C09360调用是
RCX=&context、RDX=A，不是直接把B当RCX。其ALtrue保留A，false才调用
2C0FEC0(A,&同context)取返回Character；不假定opaque前callee没有改context。
selected须magic正确、ID!=-1且不同于原B。随后28BC250(原B,selected)的pairWarID
须!=-1，经完整ID registry/fallback，+358=0且原F为null或对象指针相等才true。
两个新helper2C09360/2C0FEC0未读，不先命名层级/敌我。原B/F从非易失寄存器取，
不受context是否改变的假设替代。返回只消费AL。

2C09410(A,B,F)遍历A的context+318完整ID列表。非null F按record+8完整ID过滤，
不是D0或09280尾gate的指针比较。M(record+20,A.ID)true优先取+28C；否则
M(record+80,A.ID)true取+288，都false取-1。selectedID经Character registry/fallback
后调用2C09280(C,原B,null)；没有独立-1 skip，也不透传原F。M2494B40仍未知。

已闭合firstOR四方向的本体和字段链；不能把这句升级为所有helper或实际触发已闭。
09280的自然return callers为095B7/095C9与09410内09534，后者F明确为null；
09410的callers为095DB/095ED。深层09280出现次数随枚举变化，不借用外层单调用DTO。
最小下一原生观测仍可只捕09580/09780原调用的AL及实际输入，分别过滤096A8/096B7，
默认OFF且限定当前P TLS；不额外调用谓词。R197实际OR仍unknown、physical positive
仍false，未授新runtime/视频资格。精确增量见共享evidence归档及Root交付索引。

本轮可复用入口：[四方向函数增量](evidence/episode04-county-or-directions-12004/README.md)、
[portable源索引](evidence/episode04-county-or-directions-12004/source-index.json)。


## 2026-10-17 context predicate 与候选 selector

上述09360/0FEC0未持body是当时边界。本轮已补齐exact1.20.0.4的176B/347B
完整体及独立12B/20B unwind；机器desktop-3fevhd2-1c74096080，EXE同本页SHA。
元数据先定界后一次31reads：code523B、metadata含unwind332B，在2048B/512B限内；
没有跟进新callee。原始片段、完整读账本、错误SHA准入拒绝与修正后check均保留于
[新helper源码入口](evidence/episode04-county-or-context-12004/README.md)及
[portable源索引](evidence/episode04-county-or-context-12004/source-index.json)。

09360(ctx,A)的B/F来自ctx[0]/ctx[1]，不是入口R8。入口完整ID相同或
D0(B,A,F)的ALtrue均返回true，供09280保留原A；D0false后重新读B，此时第二次
sameID反而返回false，否则pair28BC250(B,A)经完整WarID/registry/fallback、raw358=0
及当前ctx[1]为null或等resolvedWar指针才true。D0在这里用于接受candidate，不能
照搬09580对D0true的负向使用，也不假设交换A/B对称。本体无context槽写入、
不向下层传ctx地址，但不能把多次槽读取冻成初始化值或泛称所有callee pure。

0FEC0(A,ctx)的seed来自28BFC50(A)原调用；seed==原A直接返回全局Character
fallback。循环先算next再测试current；sameID或D0true接受current。D0false后
重读ctx，第二次sameID走advance；否则用postD0保存的F做pair/358/指针门禁。
失败仅在current!=next时继续；固定点失败返fallback，不返原A或最后candidate。
返回完整RAX Character指针，不是AL bool；没有visited/maxloop界。parent来源是
context父链接或+1B8/+C8完整ID解析。28BFC50本轮未读body，既有provider的
immediate_liege采用名不冒充此入口的独立源码证明；2494B40等旧下层仍unknown。

下一最窄数据口可在既有P/firstOR TLS内记录09360自然entry/return（caller092AF）
的实际ctx两槽、candidate A和AL，以及0FEC0（caller092C0）的实际输入和返回
Character ID/fallback身份。字段仍是proposed观测合同，不是当前capability或新API；
defaultOFF、不额外调用谓词。原OR口09580/09780仍按096A8/096B7绑定。
R197实际OR仍unknown，physical positive仍false；static不抵扣实机/视频/性能验收。
