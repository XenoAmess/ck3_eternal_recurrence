# resume63：代码、数据与接收者的有限研究结果

machine_id: xenoamess-full-tower-eb9d2c1186。观察截止2026-10-27T05:08Z。REA6.8.0（160d821ac9a0310afcb8d1fc427862dd6508add5）、Rizin0.9.1；CK3 1.20.0.4/build25734779，EXE101040248B/SHA256 98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518。方法见[框架研究](resume63-framework-workflow.md)。本页仅研究结论，无Game资格。

M1原C17 RF10668B含代码10596B及两表72B。完整线性守卫exit2、REA未运行的原件不改。新C18复用这些字节，通过正式REA raw接口显式限定代码区：2450指令、536相对目标、18表项及CALL278C13D→2787C10均独核一致。原raw0地址须加RF入口VA142789F70归一，不能误加imagebase。

自动图541节点/887边，独建正常图541节点/882边；多出五条case目标自环，原offset64C/76F/77A/75E/5A7均无对应自跳。其余合法自环保留。AF统计877的内部口径未知。结论是字节与代码一致、自动CFG不完全准确，手图不能改写自动图为PASS。四个unsafe.ptr原token18446744073668092048原文保留，不消费JSON Number舍入值。raw subject arch=null及非native dossier边界保留。

M1可确认A=entryRCX+18的两条候选路径；第二路径的Char检查针对旧slot+78，未证明新返回有效。B=entryRCX+140的填充、配对和自然触发仍UNKNOWN，CALL也可被绕过。

M4新增raw入口窗口176B（无PDATA覆盖，不称完整RF）及DATA44。两decoder52条一致；入口可达41指令/165B，指令图41节点52边，基本块图15节点26边。该范围无CALL或内存写，R11未触；R9=RCX只改寄存器，不写原输出指针。可限缩旧470B首callee的不确定性，第二callee仍opaque。44B精确为BUILDING_NOT_THE_DIRECT_BARONY_HOLDER_CANCEL，仅证共传的descriptor字节；localization查表、formatter业务、退款及完整CanCancel均未闭。

M5新增RF[2E8DA30,2E8DD35)773B：171指令、11块16边双核。入口U保在R14；正常ABI返回路径返回U。U经局部槽/descriptor传给两个opaque调用；七个directCALL没有31C7680只证明本体直接目标，不证明整图无注册。注册receiver351是否等于U、对象类、默认值、战争资格均UNKNOWN。

这些结果没有改动生产Java。现有ConstructionRefundSource继续empty quote/credit0，不能据提示文本放行退款；M5观察不授战争提交。M0角色合同及真实19行Native语料的Java/兼容消费者另已落地，Main编译、Python22项与77子测试/范围类型通过均不等于实机。完整八M与Java新增游戏日仍待真实运行。

所有新provider已闭场，独审复用原件，没有新增采样。C18最小close37.406s、provider2.133s，READY至发行456.875s另计，不能称整体提速。未测模型token收益。

证据均在D盘，以下是独审精确引用：

| 结论 | 原件 | bytes / SHA256 |
| --- | --- | --- |
| C18 | [M1独审](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m1-c17-rea-split01/INDEPENDENT-M1-REVIEW01.json>) | 4029 / 9271286d0aeec82c58ecce4a55e496be36fc6e3fe92a893e102f15cff6ddbebf |
| M4 | [REA独审](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m4-cancel-rawentry12ac900-data44-01/INDEPENDENT-REA63-REVIEW01.json>) | 2799 / 7c4b803394b994f37e62310786cd1559128a33f1507f819a79a6422659cac42b |
| M5 | [M0独审](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m5-registration-link2e8da30-01/M0-INDEPENDENT-REVIEW01.json>) | 3739 / bd647181a204e7ecb2fbfed446fe7376b1f764cb287554b891183781b9d12780 |

原失败、unsafe数值及截断展示与完整原件的差别均保留。时效和回收沿用[通用策略](../storage-retention-policy.md)；不自动续期。
