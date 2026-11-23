# R0078／E8：35日连续窗口有限验收通过

2026-11-23，机器 `4-8e1c2f1861`，CK3 **1.21.0／26622941／2F2B**。本轮来源 `34d788d39da69654e389fa7a82bc29c3173c780f`，Core52／Q55；R77／Q54作为代码载体，唯一物理输入是原R74 D35存档。

原run返回 **0／2539.4568096秒**，原verify返回 **0／1.3274255秒**。四个已实际发表阶段的5／3／3／5项断言全部为true，公共`case_acceptance_pass`及`qualified_boundary_pass`为true。`business_pass`、`financialCertified`和整产品／发布资格仍为false。

| 检查点 | 原Native raw日期 | SAVE字节 | 完整独立解析次数 |
| --- | ---: | ---: | ---: |
| D0 | 53152920 | 233250248 | 8 |
| D14 | 53153256 | 238916043 | 8 |
| D30 | 53153640 | 240335959 | 8 |
| D35 | 53153760 | 237264183 | 8 |

四份SAVE共32次完整解析。观察器218104376保留基线加35日共36条原记录：金融日354..389、脚本日389705..389740，与35个实际Native 24小时区间一致；`issues=[]`、连续性及35日窗口判断为true。只ARM8一次，三次只读refresh，无手动推进日或重ARM。D0的25352条Whole金融／新闻记录与输入精确相等；之后市场自然变化，不称35日状态恒定或全局资金已恒等核清。

登记币158→182、活跃150→138、pending3→0；新永久ID159..182共24枚，旧币无缺失。独立D14证据核到其中23枚AI发行的完整原收费腿：2300分登记费、520分真实补款；21名原barony发行者与2名`is_landed=0`发行者。原`highest_tier=-1`保留Unknown，不改称某个阶级。此证据不覆盖其余新币全部现金腿或全世界aggregate Gold，也不证明所有AI具有相等发行机会。

本场最多观察64币／64仓，optional expiry未选择。完整生命周期、所有期货分支、4096币容量、395日性能、20债务终局、全球可见气泡、多人与完整产品／Workshop首发均未因此通过。R74原missing337／final GAP、R77原PARTIAL及既往失败保持历史事实，不能回填成通过。

Game19092、Host、retained OS、Job、keeper2108及allocator均完成正常0／清理闭合，CAS16367→16368，状态done、资源为空；`autosave_verified=false`保持。D35归档是**下一次自然续行的已选输入**，尚未再次装载。

精确原wait、四份ARCHIVE及SAVE身份、D35 facts／Root判断、D14独立收费证据和闭场收据见[本轮紧凑索引](../../docs/maintenance/evidence/2026-11-23-financial-markets-r0078-e8-continuous35.json)。[Q55文档](native-q55-qualification.md)中的“E8尚未执行”是该离线资格形成时的较早切点，本篇记录随后完成的真实窗口；[独立存档退役可用性](closed-independent-save-retirement-availability.md)保持原结果。
