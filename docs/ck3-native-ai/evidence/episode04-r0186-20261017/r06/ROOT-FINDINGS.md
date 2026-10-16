# R186 R06 实际结果：本地空值已读稳，下一缺口在父来源

`machine_id: desktop-3fevhd2-1c74096080`；实际查询于2026-10-16T16:38:46.692522Z。source/native为d05b0c780b615faa714fdf0535403bb2e6941faf，a29 DLL SHA `e4f2b7200a0029a56d83904b627aff724fb654b6983753da4c66af9d4e06fbbf`。本包离线读取Root原响应并经当前严格normalizer验证，没有SDK、桌面、游戏动作或源码写入。

**新的本场事实是local-definition-only双读成功，但没有provider RVA。** 普通军务外层index220可见/启用；帝国分支index238隐藏/启用。两者相同local结果：available、stable_double_read=true、variable index0、declared type635、local definition entry count1、active1、definition与local entry存在。唯一entry是**mode0、flag0、direct_value_present=false、provider_present=false**；vtable/slot2/owner ID均null，owner身份未授予。

所以“provider指向哪个模块”的答案是：**本地条目未提供provider，不存在已观察RVA，也就没有可归属的目标模块。** 这些null是稳定本地条目的读数，不是provider读失败，不应转成0、猜成CK3 getter或解释为关闭补员。祖先层是否含provider仍未知，不能把“本地没有”外推为整条父链没有。

full candidate仍为unavailable，reason candidate_parent_depth_exhausted；pass1/read51/depth8，stage/kind为parent_walk/parent_depth_exhausted。definition/count均正确null；旧full index/type null、entries空、stable_double_read=false。local成功没有把full重写为成功，a30严格消费者本次接受这一独立组合。

## 来源含义与下一最小研究

已持actual .4的3AC1C00在mode0分支3AC1D9A将entry+0复制到变量，并在3AC1DA4返回AL1；这里的local entry+0实际为空。这是来源条件含义，**没有观察到生产调用执行或临时变量表**。3AC3EF0的3AC401C/4020只在local flag非零时排除pending，本场flag0说明不能靠本地空值结束receiver来源研究。父链按definition+108优先/context+E8前进，父匹配entry还受flag4C与resolver结果约束。

上一轮“若local有provider就沿实际slot2读source”的分支在此**不适用**；不得对凭空猜测的RVA发新source读取计划。当前最小可施工补充是保全原8层内实际已经读取的祖先prefix：在同4096读/64KiB/20ms envelope下独立双捕获其context/definition、匹配entry及合法provider RVA，旧full仍unavailable、native selected仍false。若稳定prefix出现合法且flag合资格的provider，再沿它的实际slot2做有限完整body来源计划；若前8层均无可用入口，才单独立项明确新profile的更深有界遍历，不静默把旧8层换成16/32。单凭read51无法推导父链真实长度或最终receiver所在层。

最终调用前还存在3E4BC50参数准备与运行期variables选择，尚未被本次查询观察；不能把本地mode0的源码复制规则当作最终receiver为null的实机结论。整个补充无需在Root当前拍摄中再提交动作或重复查询。

## 精确保全与资格边界

原响应1,029,909B、SHA `899bdbf59aa7a539b37af73631af2ed5776d4ccacb82a600f6d77a623c115f81`。`ACTUAL-ANALYSIS.json`记录两个widget的local/full原字段、frame/public binding和原响应pin；五份raw JSON都是从直接/body提取的**原始字节区间**，没有重新序列化，offset/长度/SHA在该分析文件中，SDK镜像没有重复计数。

完整identity原件7804B、SHA `b2028b75884555bd92d00105cfa531e7295ffc885562155788f6c9974a12f951`已按精确字节复制；它绑定PID16240、createTime134366417898733491、generation1、episode native-31254-68303c9ae4fb、actor31254。查询frame为native_revision3、pump25852/ticket7、owner thread24640、date53148432；public snapshot native:3/revision4。a29生产资格5611B精确副本包含三产物pins与source绑定；其game_started=false是开场前回执时点，不能否定后续真实query。

本次可增加的是**这场local只读叶的实际双读观察资格**。没有最终native receiver、开关动作/4A9转移、自然准备、实际ADD或完整R06业务正例，也没有新的连续合格镜头；这些统计不因本包增加。脚本只复验本包这一个明确原响应，输出存在时拒绝覆盖；不应把它当通用现场操作器。
