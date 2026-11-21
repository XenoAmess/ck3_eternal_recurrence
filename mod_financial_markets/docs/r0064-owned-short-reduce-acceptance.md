# R0064：自有SHORT真实减仓，GUI业务有限累计6/6

2026-11-22，machine_id: 4-8e1c2f1861。本机CK3 1.21.0／build26622941，scene20261122a／R0064，实际运行与Q46来源为 `f358282571eafb9900b9d3067ab4efdc295e9709`。本场没有新Node／Native／Java重编，不改写既有资格来源。

本场沿R63最新保存继续，使用现有自然14日减仓v2合同，保留三份真实物理SAVE，日期为raw53151024／53151024／53151360。Root已分别核订单、P1／余仓、保证金与现金；本次通过不是把回调ACK或历史成交倒填到旧零日合同。

## 真实平空单、关闭切片与余仓

正常GUI新BUY减仓单432／native21519，一手、票据1x、限价及实际成交gross122分，本单累计手续费1分，指向玩家原SHORT191／native16795353。终点原191从1手变0，status2；P1关闭切片206／native83893189以版本1凭据明确绑定BUY432／SELL436及slice_source191、buy_close_source191。

真实对向SELL436来自账户95／native159，holder与受益人均34183，与玩家账户2／native54、角色31254独立。SELL436累计gross244含其他成交，本次只归因P1绑定的122分，不把对手全部成交或钱包变化算成本次减仓。

余仓207／native83893868保留原LONG账户1839／holder及受益人31915，并由独立SHORT账户95承担另一侧；它不是玩家重开仓。原LONG的120分抵押保留在reservation16186，玩家关闭侧16187为0，独立余SHORT的16188终点117分。Raw16优先保留实际对手账户159与关闭切片等关键对象；余仓207保留在完整audit／whole，本场不冒称也有其完整同遍Raw。

## 现金净增8分不是平仓利润8分

PRIMARY可用8084→8166（＋82），冻结389→315（－74），合计净增8分。端点独立核算为：其他旧仓正向mark／lot变化24分、负向15分，净9分；原空仓端点保证金减少58分，本单费用1分。于是可用＋82＝24＋58，冻结－74＝－（15＋58＋1），总额＋8＝其他仓净9－本单费用1。

这不是“平仓赚8分”，也不是fill瞬间的保证金或完整逐日银行流水。对手及全局费用还包含其他AI业务；完整未裁剪audit与whole自然变化保留，不能跨14日要求全图原样不变或将全局差额归于本单。

## 原失败、真实日进与正常闭场

原terminal pipeline与Raw作者均退出1并保留。slice04后缀从第一个尚未执行的Raw开始，复用原先7个成功子操作，实际退出0／45.7403545秒；只完成首次Raw及后继metadata，不重SAVE、归档、audit或whole，不把旧父pipeline改记0。

Root核实一次原ARM／resume和14个同owner Status样本，Native推进子段35.288238秒，完成14个游戏日边界、无中间暂停／越界／abnormal；这个子段不是含保存、读取及等待的端到端性能。金融日274→289（＋15）只记端点，不推出每日覆盖、付款次数或R63差1已被修复。

公共run实际退出0／2058.7681508秒，verify退出0／16.9899553秒；本case／qualified boundary有限通过，product release为false。Game3892、Host、Job、keeper及allocator均实际0，CAS16077→16078、done/resources[]。closure通用note仍含旧run／verify2句式，原件不改；本场以typed字段、原wait和released实际0为准。

本次自有SHORT减仓授OBSERVED，期货GUI六项业务有限累计6/6；减仓使用当前14日／三SAVE的v2合同，不倒签旧零日case，原R54失败、R57跨日事实和R63 GAP保持。完整Mod、正额资金费、长期容量／性能、全局通知及Workshop首发仍未通过。既有35次历史AI付费发行、其中4个无地阳性的旧批次范围保持，本场不重计或外推全体AI能力。

[实际订单／P1／现金核算、原失败与正常闭场pins](../../docs/maintenance/evidence/2026-11-22-financial-markets-r0064-owned-short-reduce.json)。本文作者只读已成元数据，不新增实机、SAVE读取或编测信用。
