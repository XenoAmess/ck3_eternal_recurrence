# 原生金融运行合同 v1

2026-11-18；施工合同。以下名称是各原生模块共同接口，源码存在及实机通过分别验收。

## 单位与账册

- 金币以整数分存储，100 分 = 1 金；价格是每手 100 枚币的整数分，订单数量为整数手，持仓数量为整数枚。
- `global_var:xfm_exchange` → `xfm_finance_exchange` story。日序为 `xfm_day`，日期守卫 `xfm_last_date`。手续费资产 `xfm_fee_cents`；真实违约基金账户引用 `xfm_default_fund_account`，初始 0。
- 业务 story 的技术 owner 不等于法律 holder/controller。角色 `xfm_account` 是主账户，`xfm_accounts` 是全部合法账户列表，`xfm_inherited_accounts` 是继承账户列表。可选 `xfm_active_account` 须验证账户 holder 等于当前角色。
- `xfm_finance_account`：`xfm_account_id`、`xfm_holder`、`xfm_system_account`、`xfm_account_frozen`、`xfm_inheritance_state`；`xfm_free_cents`、`xfm_reserved_cents`；`xfm_positions`、`xfm_orders`、`xfm_reservations`、`xfm_debts`、`xfm_claims` 名单；`xfm_holdings_count`、`xfm_open_orders_count`、`xfm_open_positions_count`。
- `xfm_free_cents` 只来自真实存款、资产销售、其他已扣源账户转账或合法历史资产迁移；绝不镜像角色 gold。系统账户不得私人提取，也不自动从 controller 私人金币补款。
- `xfm_beneficial_owner` 是当前实际受益角色；`xfm_legal_entity` 可绑定币。`xfm_finance_refresh_beneficiary_effect` 会先刷新真实主体控制者，再按账户角色识别：发行/做市账户跟控制者，创始配售账户仍跟 `xfm_founder_beneficiary`，不能把旧创始人私产转给新统治者。交易前刷新，不能仅依赖每日缓存。
- `xfm_finance_reservation`：`xfm_reservation_id`、`xfm_account`、`xfm_remaining_cents`、`xfm_status`（1有效、2耗尽）。一项冻结只对应一个唯一 story，部分支付/释放扣同一剩余额。
- `xfm_finance_position`：`xfm_coin`、`xfm_account`、`xfm_quantity_units`、`xfm_reserved_units`；账户和币两侧均有反向索引。

## 公共资金 API

“角色/账户/reservation root”均指调用时当前 THIS，不能假定真实 ROOT 被 scripted_effect 重绑定。输入均是当前 scope 的变量；成功结果 `xfm_result = 1`，失败为 0，失败不产生付款。调用方自行保留独有前缀 scope，不能依赖 finance 私有 `xfm_fin_*` 别名。

| Effect | 当前 scope | 输入 | 输出/行为 |
| --- | --- | --- | --- |
| `xfm_finance_bootstrap_effect` | 角色 | 无 | 若无交易所则创建；重复调用不重新发资产 |
| `xfm_finance_ensure_account_effect` | 角色 | 无 | 主账户 `var:xfm_account` 与 `scope:xfm_account`；角色 exchange 引用 |
| `xfm_finance_select_account_effect` | 角色 | 可选 `xfm_active_account` | 验合法 holder；输出 `scope:xfm_account` |
| `xfm_finance_create_account_effect` | exchange | 无 | 零余额系统账户 `scope:xfm_created_account`、`xfm_result_account` |
| `xfm_finance_deposit_effect` / `withdraw_effect` | 角色 | `xfm_request_cents` | 真实角色 gold 与所选非系统账户 free 的反向变更 |
| `xfm_finance_ensure_funds_effect` | account | `xfm_request_cents` | free 不足时仅从合法存活 holder 实际 gold 补缺；系统账户不补 |
| `xfm_finance_transfer_effect` | account | `xfm_request_target` account、`xfm_request_cents` | 源 free → 目标 free，先检查双方与金额 |
| `xfm_finance_fee_effect` | account | `xfm_request_cents` | 源 free → exchange 手续费账 |
| `xfm_finance_reserve_effect` | account | `xfm_request_cents` | free → reserved；输出 `xfm_result_reservation` 和 `scope:xfm_reservation` |
| `xfm_finance_release_effect` | reservation | `xfm_request_cents` | 此冻结部分 reserved → 原账户 free |
| `xfm_finance_pay_reserved_effect` | reservation | target account、request cents | 此冻结部分 reserved → 目标 free |
| `xfm_finance_fee_reserved_effect` | reservation | request cents | 此冻结部分 reserved → exchange 手续费账 |
| `xfm_finance_split_reservation_effect` | reservation | request cents | 同账户内新建独立冻结；不经过 free，不改变 free/reserved 总额 |
| `xfm_finance_otc_effect` | 买方 account | target 卖方 account、request coin/units/cents | 先建/核买方持仓，再原子交割真实币与真实现金；不改现货收盘价 |

上述金额必须是正整数分，拒绝负数、零、分数、超额请求；单次公共资金/币转账最多100,000,000分/枚，大额退出分批并记录 pending。所有支付须有同笔资金来源。款项不足不会创建无资金赊账；债务模块另行登记实际未付义务。需要同时拆分两边保证金的期货成交，先成功创建并验证全部新对象，再一起分配两边冻结，不能串行两个 split 后假定第二个一定成功。

`xfm_finance_capitalize_default_fund_effect` 用已收到的手续费现金及累计已拨数字计算10%目标；同额减少 `xfm_fee_cents`、增加基金 free，零费用不拨钱，也不反复按剩余额收10%。自愿捐助使用普通受检 transfer。

## 币与现货 API

- 全局币列表：`xfm_coin_registry`；`xfm_finance_coin` story，每币永久 `xfm_coin_id`。正常上市容量默认4,096（配置2,048/8,192）；注册档案预算为上市容量4倍，待办预算为8×30。`xfm_registered_coin_count`、`xfm_pending_coin_count`、`xfm_active_coin_count` 分开，摘牌不注销资产但释放 active 槽，不能把终身累计注册数当上市数，也不能把未经压力验证的数量称为达标。
- 币字段：`xfm_controller`、`xfm_issuer_account`、`xfm_supply_units`、`xfm_listing_state`（0募资、1挂牌、2警示、3摘牌公告、4仅减仓、5停牌、6OTC、7归档）、`xfm_trading_open`（0/1）；`xfm_spot_orders`、`xfm_holders` 名单。
- 行情：`xfm_last_price_cents`、`xfm_best_bid_cents`、`xfm_best_ask_cents`、`xfm_last_trade_day`、`xfm_price_version`、`xfm_qualified_volume_cents`、`xfm_day_volume_units`；当日 OHLC 为 `xfm_day_open_cents/high_cents/low_cents/close_cents`，上一完成日为 `xfm_prev_*`。独立成交认证及期货适格规则不得只看最后一笔价。
- `xfm_bid_depth_cents` 是外部真实可执行买盘本金，初始化为0，每次簿刷新和日结明确重算为0再累计；供挂牌需求复核以200分作信号。逐笔只读本币至多64个有效订单，先核账户未冻结、唯一买单冻结及真实余额；扣留原订单累计剩余手续费上界，再按限价换算整手，受剩余手数与账户reserved/此reservation余额共同上限约束。关联发行主体、controller本人、maker及同实际受益人买盘不计外部需求；它们真实可执行的报价仍可显示。没有币价、成交或持有人数量被此统计改写。
- 原生文本名称的未核实 story getter 不能当作公共已可用 API；UI 使用永久 ID/已验证本地化或主体原生名称，名称输入由 UI 单独实证。

| Effect | 当前 scope | 输入 | 输出/行为 |
| --- | --- | --- | --- |
| `xfm_finance_create_coin_effect` | 角色 | 无 | `scope:xfm_coin`、`xfm_result_coin`；供应0、未上市；费用/权利由发行模块先核 |
| `xfm_finance_lookup_position_effect` / `ensure_position_effect` | account | `xfm_request_coin` | 输出 `scope:xfm_position`、`xfm_result_position`；ensure 可建零持仓 |
| `xfm_finance_mint_effect` | coin | target account、`xfm_request_units` | 发行模块已核增发权后调用；同步加供应和持仓，不增金币 |
| `xfm_finance_burn_effect` | coin | target account、request units | 只销毁该账户未冻结真实币，同步减少供应 |
| `xfm_finance_transfer_coin_effect` | account | target account、request coin、request units | 仅转未冻结可用币，守恒，不复制供应 |
| `xfm_spot_submit_effect` | 角色 | selected coin、order side/limit cents/lots/ioc | 实际冻结金币或币后建原始订单，价格时间优先匹配 |
| `xfm_spot_submit_account_effect` | account | 同上 | 内部主体账户入口；调用者先核控制权，不授公开私人系统账户权限 |
| `xfm_spot_cancel_effect` | 角色 | `xfm_selected_order` | 验法律账户所有后撤单，释放该原订单剩余资产 |

角色现货输入完整键：`xfm_selected_coin`、`xfm_order_side`（1买2卖）、`xfm_order_limit_cents`、`xfm_order_lots`、`xfm_order_ioc`（0 GTC、1 IOC）。输出 `xfm_result`、`xfm_result_order`。订单 story：`xfm_coin/account/side/limit_cents/original_lots/remaining_lots/filled_lots/filled_notional_cents/fee_paid_cents/order_id/status`（1挂单、2完成、3撤销、4过期）。

手续费按**原始订单累计成交额**收取：`max(ceil(累计本金×0.003),1分)`，本次只收累计应收减已收。买单冻结限价最大本金与累计费用，卖单冻结实际币。订单可部分成交、价格改善，撤单不另收未成交手续费。交易双方各缴一份费用，不创建对手钱或库存。

盘口最优价和撮合共用 `xfm_spot_order_executable_trigger`：市场可交易、账户可用、买单确有自身冻结或卖单确有同账户同币冻结库存，并至少可执行一整手。撮合数量同时受双方保守可执行量限制，避免无抵押最优单挡住后续真实对手盘。深度不含手续费；若历史数据的冻结余额异常偏少，先按全剩余委托的费用上界保留，宁可少报整手，不能多报钱。

GTC新余量准入消费共同配置（全局8,192、每账户32；每币现货簿及每个期货合约按容量规则为32／64／128，默认64）。降低设置仅阻止超额的新余量入簿，不删除或取消旧挂单。现货保持每次64个fill的工作预算，期货保持32个；旧簿的最优价选择、撤单、减仓和清算不以新深度拒绝。期货行情投影仍读取至多128个当前本合约订单，保证降档后原簿尾部的最优单不会被新32档截掉。IOC只作为同步临时 taker，不占持久active槽，满簿仍可吃现有真实对手盘；结束必完成或撤余量。所有订单story总预算24,576；终结立即移出active名单，短期历史链保留约2,048项，超量每终结清一项、每日另清最多256项，仅终结日在当前日之前、无冻结残量且 `xfm_external_refs=0` 才销毁。其唯一已清零买单冻结同步退出账户索引并回收；外部需保留订单或其冻结时须登记订单 `xfm_external_refs`。存在义务/真实引用者保留，不能清账伪造归零。

`xfm_spot_maker_effect`、`cancel_maker_effect`、`cancel_coin_effect`、`withdraw_maker_effect` 都是coin当前scope。做市账户独立，初次从真实 maker reservation 转入资金及至多2,500枚实际库存；之后只用自身资产报价。撤资停止新增报价、撤自己的单，按单笔上限分批返还；`xfm_maker_withdrawal_pending=1` 会在每日继续，未付/冻结资产不删除。容量规则的32／64／128是新挂单余量深度，不是同时活跃的热簿数量，也不是已通过的性能或总驻留上界；冷币即时路由仍开放。

`xfm_price_version` 每笔真实成功现货fill增一，是行情修订号，**不代表预言机合格**。`xfm_qualified_volume_cents` 只由 oracle 接受样本时维护。真实成交调用 `xfm_oracle_record_trade_effect`：coin当前scope，账户scopes `xfm_trade_buyer/seller`，角色scopes `xfm_trade_buyer_holder/seller_holder`，数值scopes `xfm_trade_price_cents/lots/notional_cents/day`。

## 每日和发现

交易所 story 每日先比较 current_date 与 last_date，由D−1更新日序为D并重置发行预算；随后 `xfm_spot_daily_effect` 关闭上一日日线/到期单、`xfm_oracle_daily_effect` 消费D−1样本发布D结算标记、`xfm_finance_capitalize_default_fund_effect` 拨真实已收费用、`xfm_futures_daily_effect` 按D结算；再调用 `xfm_coin_daily_effect`、`xfm_listing_daily_effect`、`xfm_debt_daily_effect`、`xfm_news_daily_effect`（均 exchange 当前 scope），**最后**运行AI候选，新增成交记D日。只有主clock加日序，模块不得各自+1。同一日重载不得再执行。各模块另对独立到期/回执保幂等。

初始一次 `every_living_character` 建链队列；出生与非出生 created hook 入队。字段：exchange `xfm_ai_head/tail/count`、角色 `xfm_ai_next/queued`。每日最多512候选弹头处理（配置128/1,024）、活人移尾，至多当日起始队长，避免小队反复处理。成年AI调用 `xfm_coin_ai_effect`、`xfm_spot_ai_effect`、`xfm_futures_ai_effect`；现货关注名单 `xfm_finance_watchlist` 上限6、过期币移出并重数，发行模块每日上市预算最多8。没有全AI×全币每日扫描。

现货每次候选有25%机会释放一个没有真实现货持仓、未平期货持仓或未结委托的旧关注，再从上市币发现候选；避免最初六个币永久占据注意力，同时不移除仍有风险的币。宣传只在30日注意窗口内影响候选偏好，受同一关注上限、真钱预算和自主买卖判断约束，不保证买入或改写价格。

## 死亡与继承

法律 holder 在 on_death（原版此时尚未真正死亡）处理：撤现货挂单；存在合法 primary_heir 时原 account 的 holder 迁继承人，账户ID、资产、保证金、债务引用不变，加入 heir 全账户/继承列表，不覆盖 heir 主账户。无 heir 则冻结、state2、原 holder 引用保留；技术 custodian 不因此取得受益权。合法未成年继承的操作资格仍须受监护/成年规则控制。

A0 历史账必须一次迁移并打标：币、账户、原始受益人与实际池/费用资产按来源转分；不把同一原 story 导入两次，不清旧证据，也不能保留两个可支配同一资产的入口。原生加载、金额精度、顺序匹配、scope隔离、保存重载与性能分别实测，本文不授实机资格。

实际迁移先收集A0来源列表一次，再按逐源标记恢复现金/受益人/持仓；创建失败留受限资产与未完成标记，每日只重试已收集的旧小名单，不重扫全世界。旧费用已消费元数据不复活为现金；旧交易费用现金与真实池/保证金/预存才进入对应新账。供给核对不等时暂停该币新交易并保留所有来源，补全后解除迁移自身的暂停。旧个人币指针在原来确指旧story时更新，旧story保留新币迁移链。
