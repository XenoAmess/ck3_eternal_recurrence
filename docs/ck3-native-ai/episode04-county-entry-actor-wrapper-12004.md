# R04：actor+县谓词2C09DF0首先校验县，再委托关系判断

actual1.20.0.4的2C09DF0不是一段已闭合的“敌方县”规则。它只先校验County-like
对象与完整Land身份，然后将一个实际helper返回对象和actor交给尾调用2C09620。
两个callee都未在本轮读取，不能把最终bool翻译成敌对、可补员、相邻或同realm。

来源机器desktop-3fevhd2-1c74096080，EXE SHA
98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518。
实际完整extent2C09DF0..2C09E73，共131B/37条指令，SHA
344dc31069a905f0615c45fd59967f35530a14f75e496cda079841c897a3652b。
8个jump包括合法外部tailJMP，另有1个直接CALL。没有跟进callee。

## 与24E2230的真实连接

已闭[县条件24E2230](episode04-county-entry-condition-12004.md)在mode1调用本函数：
sourceCounty一次24E22AE，targetCounty两次24E22EC/2343，每次AL都必须true。
本wrapper的RCX是actor，RDX是非null县对象。原body没有县null自卫，不能把它用在
任意猜测指针上；现有上游先校准入。

| 实际位置 | 读取/分支 | 可以确认什么 |
| --- | --- | --- |
|2C09DF6..9E03|[County+3E0]必须为0x436F4461 CoDa|不匹配立即false|
|2C09E05..9E38|读取County+18完整int32 ID；slot5D1DAF8，mask24索引、capacity+2C、objects+20的16B行+8，再核object+10完整ID|未用低24位冒充完整身份；失败取slot5D1DAE0 fallback|
|2C09E41..9E4E|resolved/fallback object+14必须Land，object+10不能-1|有效县关联Land对象的身份准入，不是关系true|
|2C09E50..9E53|CALL24D4ED0，RCX=原County|返回receiver正式类型未知|
|2C09E58..9E66|RAX→RCX、原actor→RDX、R8D=0，恢复栈后JMP2C09620|真实尾调用；最终AL由未展开callee决定|

因此本函数的立即false只有County魔数不符或Land身份准入失败；有效身份仍不能
推出true。真正关系语义的最小下一源码入口是**2C09620**，显式参数如上，raw0的
含义也未知。共同helper24D4ED0仍未展开。本包不自动读取两者。

R0180已有的source2635/target2645/actor31254/mode1与双definition1B1、B100，
只证明上层实际最终false，不能辨认是县对象相同、某次本wrapper身份失败、某次
委托关系false，还是目标raw集合的另一条检查拒绝。每次重复调用都保留，未假定
callee无sideeffects或把两次target结果合并。

## 已发布只读值仍不足以筛出true

现有strength query发布24E2230的最终bool、actor/source/target/mode；movement
发布双definition字节。war occupation query可提供holding/province/county_title_id、
legal holder与occupier。这些可以缩小正常军事候选，却没有本wrapper实际County+18
原值、registry解析结果、24D4ED0返回receiver身份或2C09620结果。
即使county_title_id是有效的标题引用，也不能冒充该次真实参数的完整关系判定。

Root可以继续复用现有`ck3_query_war_occupation_targets_v1(war_id=4,
expected_revision=freshR)`加已广告的合法preview，挑选具备当前实际来源的候选。
但在不改变stored route的情况下，当前口没有任意candidate的县bool；不能保证
下一Move前就筛出true。另一lane准备的既有preview可选child应直接调用已绑定的
24E2230，保持exact firsthop/actor/mode和frame身份，不能以地图敌方或holder关系
替代原生返回。那是未来候选能力，本包没有部署、SDK调用或动作。

## 两次读取与失败保全

首轮reader把所有jump必须在本体内作为额外断言，遇到合法tailJMP2C09620后失败，
而原字节与逐read账本尚未写盘。该失败原样保留；首轮精确计数为null，只能证明
代码守卫上界8192Bcode/512Bmetadata/48reads。Root明确批准新的独立attempt与两次
累计上界16384Bcode/1024Bmetadata/96reads，未删旧失败。

第二次前重新通过native_research_plan check，实际131Bcode/224Bmetadata/21reads。
因此包括首轮未知精确计数在内，累计保守上界为8323Bcode/736Bmetadata/69reads。
不声称一次成功，不把重建或推测值当首轮实际账本。两轮均未执行EXE、SDK、游戏、
桌面、构建或主仓写入；没有整EXEhash或callee读取。

归档中的stdlib verifier只核原件字节、完整37条指令拼接、8个jump目标、实际外部
tail和唯一CALL，不执行native语义。R04 positive、实际县扣兵、clean、动态镜头及
人工签核均没有新增信用。
