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
