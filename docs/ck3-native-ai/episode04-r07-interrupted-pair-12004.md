# R07 v2：一次真实登船付款，对照在第31日被战斗打断

结论是 **COMPETING_COMBAT_INTERRUPTED_CONTROL**。R178有一笔来源合格的自然登船扣款；R179只完成30日，第31日出现真实战斗，不能成为完整32日对照。`full_v2_qualified=false`、原R07 v1仍未通过。本包不增加已关闭视频卡，不改变既有6/14口径，也不给旧陆地行军原片或未录制阶段登船动态镜头资格。

## 两场实际输入与来源

来源机器 `desktop-3fevhd2-1c74096080`；游戏1.20.0.4/build25734779，EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。两场使用同一实际源码 `b42afbbd85df3802b1fa6222f7aac403c2adf735` 与a08 DLL SHA `e4ee59c72b488d4d089e653310f61f28467a1a25645043e28a1d725d4e247329`，独立正常加载同一S0：71631396字节、SHA `e6ee95c3184c00989af660c5d765a27622fd5b93f9e8930fdc5a5ed56e157d67`、日期53146848。角色来源链指向历史1128的罗贝尔，实际runtime31254；数字ID不是跨机器身份常量。

R178 treatment在正常加载后把Unit93从2624移向海省1036，完成32日。R179 control从同S0原地观察，30日完整；第31日 `date_raw=53147592` 的独立暂停帧显示Unit93仍在2624、route complete_empty，却已 `in_combat=true/state2`。原runner的战斗守卫拒绝继续。没有伪造local08/09 complete，没有重提已提交或结果未知的Arm/Resume。

## R178：自然父链与一金币实际扣款

生产严格消费者 `r07_v2_contract.consume_window` 与 `war_payment_observations_v1.normalize_journal` 已分别消费两个完整分窗。第二窗唯一合格记录：Unit93、内部CArmy85、Province1036、payer31254的personal账户，requested raw100000（Q100000，即1金币）；whole-original callback余额25567301→25467301，实际减少恰好100000。

同一clock140715344888360/TID18068的实际顺序为：natural entry75376669 → transition entry75376671 → gateway entry75376672 → writer entry75376673 → writer return75376674 → gateway return75376675 → transition return75376676 → natural return75376678。唯一对应natural returned-parent保留同日entry/return fence。实际caller return分别为 `2A9A8C5/24E8F40/28B99B2`；不是按时间接近或不同journal序号猜父子关系。

transition before/after实际观察Unit93/CArmy85/Province1036，entry `Army+1D4=0`，满足此付款分支。不能因军队被称为特殊兵就替换该原生源条件。两个具名完整Driver原件起终分别7,729,271与9,938,047字节，原独审核其既有SHA后只投影所需字段：完整DATA签名相同，4个unique physical chunks，总current/max250/250。库存/容量100/100不是付款证明，付款由真实钱包写入链单独证明。

32份实际daily complete摘要均已逐条审查：日期+24、clock generation1..32、speed5、每次1 tick、0 overshoot、实际暂停、同PID/create-time/episode及本窗previous→latest fence连续。connection generation1由独立admission/cash绑定；daily摘要没有独立该字段，不能把clock generation混作connection generation。两窗终点自然retention46/18，未覆盖/失败计数为0；payment sequence3/4各属自己的epoch/window，不跨窗接序号。

第32日只是没有新增合格登船callback，仍新增local seq4 generic ADD263646。两窗其它generic钱包记录不被命名为维持费；`maintenance_attribution=unclosed`，不把整窗净金差称作登船费。

## R179：有限30日与真实中断

30份已完成摘要均实际重审，通过日期/时钟/暂停/本窗fence、原地2624 regular空route、无combat的检查。现有单窗严格消费者又独立消费截至第23日和第30日的完整cash journal：所选Unit93合格登船callback均为空。第一窗natural46/payment seq3，第二窗natural14/payment seq0；第一窗generic ADD111391仍不归因维护费。

这些空结果只属于完整的前30日，不证明免费登船，也不能代替第31/32日对照。第31日竞争性战斗使完整配对无法验收；本包没有在中断后补读未来不存在的daily complete，更不把该场续作32日。

Root随后保全中断ARCHIVE（cash/full93/clock只留引用）、独立sampling OFF/readback、正常存档与正常退出。正常保存为日期53147592、73053077字节、SHA `24f646991e44d992d40351be35c825af18929bf4170de7bae63d2f5534b55893`；本包没有读取或重哈希该save。两场actual exit0、game/recorder/SDK/keeper关闭，R179 CLOSED确认both closed/source freeze released。恢复性操作不授本场业务通过。

原失败启动、CLI外层输出失败及恢复保留在ZIP历史成员/来源索引。scout已成功完成且internal out存在；外层目录写失败后的恢复明确 `SDK_requests_reissued=false`，不把恢复当第二次游戏请求，也不覆盖原失败。

## 跨机器检查与边界

本页配套 [MANIFEST](evidence/episode04-r07-interrupted-pair-12004/MANIFEST.json)、[compact ZIP](evidence/episode04-r07-interrupted-pair-12004/compact-evidence.zip) 和 [stdlib verifier](evidence/episode04-r07-interrupted-pair-12004/verify_compact.py)。在任意有Python3.10+的机器运行：

```text
python verify_compact.py --directory <本目录evidence/episode04-r07-interrupted-pair-12004>
```

校验器验证归档与成员字节、32/30日事实表、所保留同clock/TID子链、请求与整callback余额差、完整小DATA起终稳定及实际中断/封场。ZIP包含已审紧凑投影、既有消费者结果和小型封场/历史metadata；不含完整cash/Driver/pipe/save/video/EXE。因此它不会冒充完整原生journal/session重放。重放生产消费者仍须取得成员所pin的真实原件，不能制造同名替代。机器相关事实仅归属于原机器/会话，源码与校验器可复用。

下一轮a09、R04/R06不需要等待无限重试R07。若重做R07配对，应建立新的完整无竞争事件对照，两臂各独立正常加载、同源/DLL和cohort、分窗及32日证据，不能把本次30日接到另一进程补齐。外置过程包按Root原2026-10-16T07:45:01.597Z复核，不自动延长；本次只新增共享知识和事实，不改旧接受范围。
