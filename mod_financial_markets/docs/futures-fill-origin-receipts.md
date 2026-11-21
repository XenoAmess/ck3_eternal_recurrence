# 期货成交来源凭据

2026-11-21，machine_id: `4-8e1c2f1861`。本页说明R0055闭场后采用的P1来源字段；它不修复R54坏账，也不替代新SHORT／减仓的实际资金验收。GUI仍4/6。

凭据只在既有正成交路径、双方原fill_order效果之后，写入该次新仓及实际分配的close slice。旧来源仓、旧订单与历史记录不遍历、不回填；没有正成交、必要永久身份缺失或意图无效时，不发布完整版本。每个接收仓最多增加13个原始数值字段，没有新story、弱引用、全局流水号或历史扫描。版本最后写入，已有完整凭据不被后续调用覆盖；字段随原接收story的保留策略存在，不承诺永久历史。

| 字段 | 含义与存在条件 |
| --- | --- |
| `xfm_fill_receipt_version` | 当前协议1；必要来源通过检查后最后发布 |
| `xfm_fill_day` | 本次实际交易所金融日，不是原生日历日期 |
| `xfm_fill_lots` | 本次实际正成交手数 |
| `xfm_fill_mark_cents` | 本次撮合价，来自实际resting限价；不是未来结算价或Oracle资格证明 |
| `xfm_fill_buy_order_id`、`xfm_fill_sell_order_id` | 原BUY／SELL订单永久ID |
| `xfm_fill_buy_account_id`、`xfm_fill_sell_account_id` | 两张原订单的永久账户ID；不改称后继仓的当前多空持有人 |
| `xfm_fill_buy_intent`、`xfm_fill_sell_intent` | 0开仓、1普通减仓、2明确强制退出；不等于强平必已完成 |
| `xfm_fill_buy_close_source_id`、`xfm_fill_sell_close_source_id` | 仅对应一侧确有close来源时保存其原仓永久ID；开仓时保持缺失 |
| `xfm_fill_slice_source_position_id` | 仅该接收仓有slice来源时保存原仓永久ID；普通新仓无需填0 |

以上是最多13项，不是每份凭据都应有13项。条件缺失与真实0不同：可合法为0的是已明确的开仓意图；旧档没有字段仍是Unknown，不能根据当前余额、持有人或相似金额补齐。Java投影仍用原两遍EOF读取、typed数值与精确字符串报告；新增enum不增加SAVE解析遍数，不将原生story ID与永久ID混用。

在同一明确的world／scenario及期货订单永久ID命名空间内，买卖订单ID对可关联该次新仓与分配slice。原撮合每次消耗两边剩余手数的较小值，至少一张订单耗尽，因此未改写、未重放的同一订单对不会产生第二次正成交。跨独立fixture分支，即使数字相同也不是同一个因果身份。

凭据没有每次实付手续费、出生时free／reserved／margin余额，也没有额外现金或抵押分配效果。`lots × price`可精确导出该次gross，但不能把订单累计手续费差额或现余额当作本次已付费／出生资金。真正资金正确性仍需同一保存的账户、预留、费用与完整权利图另核。R54原audit2、失败与悬空引用不因此变为完整。

P1源码已经采用。首次受影响34项为32通过、2失败，原失败报告保留；两项新fixture在cash baseline后创建2000分replacement钱包，后继只前移创建时序。affected02的34项通过仅对应更早inline源码，不授最终资格。完整检查前发现的8处inline数值等式已改用5个具名pure floor值，未放宽既有校验器、VM或经济规则。

最终affected03退出0/51.5454612秒，42项全部通过（FullBook31、投影3、BuildContract8）。随后完整金融操作退出0/260.522071秒，其中原Maven子wait0/259.2541013秒；623个不同方法全部通过，失败／错误／跳过均0。完整窗口的409个产品源前后保持一致。34／42与623重叠，不累加。上述软件检查不补R54实机失败，也不授新SHORT／减仓通过。[实际采用、原失败及完整软件回执](../../docs/maintenance/evidence/2026-11-21-financial-markets-fill-origin-software.json)。

App16实际以skipTests打包，原wait0/8.8213017秒，没有新增测试信用。Raw准备0/0.373129秒、原javac0/1.688514秒及compiled proof捕获0，完成一次必要的小编译重绑；没有新增SAVE读取、业务或实机信用。后继共享Native来源已经变化，必须取得新的profile／DLL资格，不能用Q36代替新版资格。GUI仍4/6。

生产入口：[凭据效果](../common/scripted_effects/xfm_futures_fill_receipts.txt)、[普通撮合](../common/scripted_effects/xfm_futures_match.txt)、[减仓分配](../common/scripted_effects/xfm_futures_reduce.txt)、[投影字段](../tools/src/main/java/org/xar/ck3/markets/saveaudit/FinancialSnapshot.java)。[R54失败与软件修复边界](single-sided-futures-reduction.md)保持。
