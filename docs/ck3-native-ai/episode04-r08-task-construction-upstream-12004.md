# R08：任务构造与scheduler上游静态证据

`machine_id: desktop-3fevhd2-1c74096080`；原静态记录时间2026-10-21 09:52:20 UTC。详见[完整发现与限制](evidence/episode04-r08-task-construction-20261021/FINDINGS.md)及[12份小原件的来源清单](evidence/episode04-r08-task-construction-20261021/SOURCE.actual.json)。原版映像来源为1.20.0.4；原整EXE SHA复用，未重新全量哈希，不授当前安装或运行资格。

已解码的来源链从`28F6FCB`调用进入任务构造，经reference wrapper、提交/worker路径、vtable thunk到`290DC00` scheduler。调用者为本任务选择`owner+2630+bank*2640`描述符；同一函数里的另一处`day%30`选择不同描述符，不能把它直接套到本任务。

原09:52封件列出的“数组生产者未知”保留其时点。10:15的[独立后继封件](evidence/episode04-r08-task-construction-20261021/selector-a03/FINDINGS.md)进一步找到了真实数组生产路径：完整`28F42D0`比较原DWORD Character ID的无符号mod30与日期派生ordinal的mod30，相等才append到同一目标描述符。日期ordinal使用signed32(date_raw−43800000)/24向零截断；准备函数使用clock低DWORD+24。

原a03“phase与bank交接未知”的封件保持原样；[a04独立后继](evidence/episode04-r08-task-construction-20261021/phase-a04/FINDINGS.md)进一步解码出pre→execute→bank flip→TurnTick的静态顺序：先以oldDate+24准备，随后global date+24并消费。对保持稳定且符合该路径条件的成员，示例旧日期余数22会先选23、再选24。这仍不是实际Game的成员资格、父回调或付款证明，不能把它改写为每次推进一天都保证命中。

后继还记录本映像的manager primary vtable为`4764908`，旧resolver源码里的`47648F8`是错表；不能把旧源码当作已经可用的新bank查询。

[a05正常生产者与净额结算](evidence/episode04-r08-task-construction-20261021/normal-producer-a05/FINDINGS.md)在本映像中进一步找到：c=`X+28`由与当前军费向量相同的两个callee及参数计算gold slot0；d=`X+30`是条件工资、宫廷amenities和传奇费用来源之和。它们是缓存的率或分量来源，不能据此宣称已经发生整笔付款。

已持结算函数使用`N=wrap64(a-b-(c+d))`。N为正时可以在c非零的同时得到较小ADD；N非正时，c权重的SUB分摊的是净缺口，不是gross c整笔军费。原版固定点分配保留分阶段精度、舍入和溢出规则，不能无条件用普通`x*y/T`替代。a/b仍保留raw名称，不擅自改名总收入/总支出。TopLiege getter发生在settlement之后，其返回角色不能反过来重命名前面的personal-wallet payer。

来源关联已比旧a02/a03封件更明确，但实际同实例成员关系、live cache刷新时期、独立付款回调、余额变化及通用周期仍须当次原生证据；旧“当时未知”原件不覆写。没有把本次静态研究计成R08实机通过。

小型binary span、选取指令与SHA保留供重建，未安装hook、运行native测试或推进游戏。正式R08、Game业务、payer/cadence资格均不由这份专题增加；普通planner不自动加载。
