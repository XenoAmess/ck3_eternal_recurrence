# 有限资金回兑

本页描述模组新增的发行人回购服务。它是发行人自愿支付的有限用途，实付回购额不等于外部营收、利润、广泛需求或币价保证。发行人、交易者与 AI 使用同一套真实金融账户；无系统补钱、隐含销毁或未兑付债权。

## 正常玩法

在现货票据的回兑区查看固定单价、原始预算、剩余预算、到期市场日与当前市场日。控制人可设下一窗口单价、预算和期限，确认后从该币发行账户的可用现金预存。默认草案为每 100 币 20 分、预算 1000 分、期限 30 日；GUI 可选 7/30/90 日。发布成功后，单价、期限和总预算不能中途修改、撤回或追加。即使预算售罄，也要等待原到期日及之后 7 日才能发布下一窗口，且须先收回未使用余额。

持有人选择自己的合法私有钱包，每次交付 1–100 手，每手 100 币。确认书固定本次钱包、币、窗口、价格、数量和当时剩余预算。其他成交、钱包切换、控制人继承、跨日或预算变化会使原确认失效，需重新取得确认书。同一角色每个市场日最多成功兑付一次；失败不占成功次数。服务不收交易费。

支付由专用回兑账户完成，持有人交出的币进入该账户的真实持仓。没有自动烧币。预算不足一手时明确显示售罄，零头留在该账户；到期后当前合法控制人可把未使用现金转回同币发行账户，包括此时已归档的币；归档币不能发布新窗口。取回的是项目现金，不直接加角色金币。已经支付的资金不能取回。

## 金额、权限与失败合同

所有金额为整数分。公开发布入口允许单价 1–1,000,000 分/100 币、预算从一手价格至 100,000,000 分，期限为当前市场日之后 1–90 日。单次兑付不超过 100,000,000 分，累计支付与累计交付各限制在 1,000,000,000,000 以内。它们是模组初始服务限额。

控制人必须通过现有发行实体权限检查。资金只来自发行账户的 free，不能消费 reserved、做市预算、保证金或个人金币；回兑不调用补款入口。专用账户是 system=1、legal_entity=该币、redemption_only=1 的正常账户，不加入角色私有钱包列表，现有个人提现入口拒绝该账户。

持有人须存活成年、为所选私有账户当前合法 holder，账户可用、system=0、无项目 legal_entity，并持有足额未冻结币。当前控制人、发布时原控制人、发行账户、做市账户和专用账户的关联受益人不能借回兑制造用途记录。继承得到的合法私有副账户可手动使用；AI 只使用自己的主私有账户。

每次操作刷新真实控制权及受益人。通用 finance beneficiary refresh 目前识别 founder/issuer/maker；回兑专用分支实际调用该接口，再明确把专用账户 holder/beneficial_owner 同步为当前 coin.controller。继承不新建账户、不改窗口身份、价格、到期日或预算，也不让旧控制人失去后留下永久锁死窗口。新的控制人及其已有私有账户仍受关联拒绝约束。

窗口的 remaining 只是预算记录，真钱唯一存于专用账户。当前窗口要求 account.free=remaining、reserved=0；不一致时拒绝兑付/回收，不能用账面预算创造现金。新窗口 story 和兑付 receipt 都先创建成功，再发生对应转账。兑换调用现有原子 xfm_finance_otc_effect：末端重验现金、真实可用币与接收持仓创建；失败不支付、不记用途，不生成未兑现索偿。

成功才增加窗口 paid、币 lifetime_paid/lifetime_units、actual_utility_cents 与 project_spent_cents。预存预算是资产转移，不提前记项目支出。actual_utility_cents 是现有 30 日复核窗口，现有消费方会清零；累计额与永久收据独立保留。现有上市政策按零用途复核，1 分真实独立回购属于非零用途，本包没有偷偷提高或降低政策门槛。

回兑不写现货 last、price_version、合格成交量、oracle index/mark，也不生成价格样本或债务。现有 OTC 接受路径不能把专用系统账户选作普通卖家钱包来盗用现金。

## AI 与工作量

唯一新 caller 位于现有 xfm_finance_ai_decision_effect，在 spot AI 之后、futures AI 之前。继续使用已有 attention/ordinary 的每日总决策预算、角色同日保护及最多 6 币关注列表，不新增 world scan 或角色×全部币扫描。回兑消费者每次只选一个关注币、最多一手，并有独立角色日保护。它比较已发布回兑报价与扣现货卖出费后的 bid，使用现有真实主钱包持仓及相同 prepare/execute。没有持币或预算时直接失败，不补币不补钱；临时选择后恢复原选币和 active 钱包。自主发布预算不在本包。

## 守恒账例（合成测试）

发行账户 free=2000、reserved=500，用户 free=50、持币400；发行账户另持币600，总供应1000。发布每100币20分、预算100分：发行 free 变1900，专用 free=100，金币、供应及费用不变，尚无用途/支出。用户兑100币后，用户 free=70/币300，专用 free=80/币100；实付用途与项目支出各20，窗口 paid20+remaining80=initial100。到期收回80后发行 free=1980、专用 free=0，专用仍持100币。全程现金与供应分别守恒。

## 永久身份与 SAVE 审计接线

新增类型位于 common/story_cycles/xfm_redemption_stories.txt。两个类型的 owner 都是技术托管；on_owner_death 仅走已有 rehome，不把技术所有人变成法律受益人。有效窗口/收据永久保留，不复用 ID。失败时未支付的临时对象可结束。

| 类型/对象 | 字段与含义 |
| --- | --- |
| exchange | xfm_next_redemption_window_id、xfm_next_redemption_receipt_id：分别于成功资金预存、成功原子支付后单调递增 |
| xfm_finance_redemption_window | xfm_window_id；xfm_coin 与 xfm_coin_id；xfm_redemption_account 与 xfm_redemption_account_id；xfm_issuer_account 与 xfm_issuer_account_id；xfm_publisher（发布时角色） |
| 窗口固定条款 | xfm_price_cents、xfm_initial_cents、xfm_created_day、xfm_expiry_day |
| 窗口动态账 | xfm_remaining_cents、xfm_paid_cents、xfm_paid_units、xfm_reclaimed_cents；xfm_status=1有效/2不足一手/4关闭；可选 xfm_last_reclaim_day。到期以 expiry 与市场日比较为准，无每日改状态扫描 |
| xfm_finance_redemption_receipt | xfm_receipt_id；xfm_coin/xfm_coin_id；xfm_window/xfm_window_id；xfm_payer_account/xfm_payer_account_id（真钱支出专用账户）；xfm_payee_account/xfm_payee_account_id（私有收款账户） |
| 收据事实 | xfm_holder（当时交币角色）、xfm_controller（当时控制人）、xfm_paid_cents、xfm_paid_units、xfm_price_cents、xfm_budget_after_cents、xfm_day、xfm_status=1；可选 xfm_previous_receipt 指同币前一收据 |
| coin | xfm_redemption_account、xfm_redemption_window（当前窗）、xfm_redemption_last_receipt；xfm_redemption_next_publish_day；xfm_redemption_lifetime_paid_cents、xfm_redemption_lifetime_units；既有 actual_utility_cents 和 project_spent_cents |
| 角色 | xfm_redemption_last_receipt、xfm_redemption_last_success_day；报价 nonce 与 UI 草案不是真实现金余额 |
| 专用账户 | 既有 xfm_finance_account ID/free/reserved/holder/beneficial_owner/positions；新增 xfm_redemption_only=1，legal_entity=coin，system=1。收到的币采用既有持仓身份 |

创建、回收入口在 common/scripted_effects/xfm_redemption_windows.txt；报价、交付、收据生产者在 xfm_redemption_exchange.txt。窗与收据的 ref 和数值 ID 必须互相对上。每窗 initial=paid+remaining+reclaimed；每张收据 paid_cents=paid_units/100×price，金额、单位及全部 ID 为非负或规定的正整数；按窗收据合计应等于 paid/paid_units，按币合计应等于 lifetime。收据不是第二份现金，不应再加入总现金。

只有 coin 当前窗口可要求专用 free=该窗 remaining、reserved=0；旧关闭窗口仍永久存在，专用账户可供之后的新窗口复用，不能把所有历史窗口 remaining 加成钱包，也不能拿旧窗0余额覆盖新窗真钱。首次真实 SAVE 必须检查零值省略、实际 story 引用编码、永久 ID、余额与收据关系，不得缺字段补零。现有 reader 必须显式增加两类实体及上述字段；未接线或未知格式应 INCOMPLETE，不能只凭用途计数、fixture 或总数相等通过冷载。Cold 前后比较相同永久 ID 的固定事实和真实余额，控制人继承允许 holder 更新。

## 验证边界

外置 Java 生产脚本子集测试实际执行本包脚本及既有 finance cash/assets/OTC/policy、listing OTC 和需求复核入口；共享 Clausewitz SCRIPT parser，不新增通用解析器。显式替代边界为政治控制权解析、确定性随机、story 创建/失败、事件上下文捕获及无关业务 AI。现金、币、私有账户权限、报价拒绝、收据和新 AI 消费者仍执行生产脚本。

16 组实际通过：真实预存与固定条款、资金/权限/格式拒绝、现金与供应守恒、冻结币与旧 OTC 竞争、并发预算报价与重放、改钱包/币/ID/控制人/日期拒绝、关联与项目账户拒绝、分配失败、售罄零头/到期回收、预算与真账户不一致、月度用途清零与永久累计、原 AI 回调/主钱包、正常 GUI 捕获、普通 OTC 拒绝系统现金、累计上限、旧控制人死亡后的同账户继承与新控制人关联拒绝。

完整 16 组首次通过后，源审发现 CK3 不支持的两处内联数值等式；它们及四处 floor 等式已改为纯命名数值 helper 的双向比较，共享 Native 结构校验由 Root 扩展。修复后仅重跑受影响的 5 组（含小数拒绝、报价精确性、真实交付、继承、归档后到期回收）且全部通过，其余此前通过范围保留，不将旧全选结果冒充新源码全选。

这只是 Java 对明确脚本子集的验证。本包没有运行 Maven 全仓、CK3、Native、真实 SAVE 或 cold reload；游戏对新 GUI/event/story 的实际语义及存档审计资格待正式集成后验证。


## 未来成功收据的角色身份快照

`xfm_last_redemption_ai_day` 在 AI 资格入口通过后、选择关注币与尝试支付前写入。因此，真实前后存档出现该日标记，只能在来源闭包正确时证明该角色进入过 AI 回兑入口；空关注列表、无可用币或后续支付失败也会留下它。该标记会被以后访问覆盖。收据 `paid_units=100`、主钱包收款或“非玩家”身份都不能单独证明某笔回兑由 AI 发起。

身份扩展版本 1 仅在现有原子钱币交付成功后、为本次新建收据记录事实时写入。它不改变原 receipt ID、状态、前序收据、报价、nonce、AI 概率、资金来源或玩家选择。新收据增加以下可选字段：

| 字段 | 成功时的事实 |
| --- | --- |
| `xfm_redeemer_identity_version=1` | 身份快照最后写入的版本；原有 `xfm_receipt_id` 或已有该版本的收据不再补填或覆盖 |
| `xfm_redeemer_is_ai=0/1` | 实际交币角色在成功时由引擎 `is_ai` 返回的身份，不按玩家 ID、手数或日期标记推断 |
| `xfm_redeemer_primary_known=0/1` | 当时 `actor.xfm_account` 是否为带正整数永久 ID、holder/beneficial_owner 均属该角色、system=0 且无项目实体的金融主账户 |
| `xfm_redeemer_primary_account`、`xfm_redeemer_primary_account_id` | 仅 known=1 时存在的原主账户引用和永久 ID；冻结与否不改变主账户身份，也不授予付款权限 |
| `xfm_redeemer_used_primary=0/1` | 仅 known=1 时存在；实际收款账户是否等于该主账户，合法副账户收款仍保留原 payee 与实际金额 |

旧收据没有版本时身份为 unknown，不补填当前角色属性；known=0 时主账户引用、ID、used_primary 均缺失，不能默认为 0 或 FALSE。版本扩展也不证明发起者的低阶/无地身份、不证明先前发行费或账户余额祖先，更不认证一次 AI 决策的具体调用路径。失败支付没有此身份凭据。重载后仍须按原收据、角色、币、窗口与钱币转移独立对账。

现有 raw exact-story 工具能保留这些原始变量，但普通 FinancialSnapshot/SDK DTO 尚未自动投影新字段；不能凭缺字段补值后授予 AI 业务通过。新增六个 Java 回归方法复用既有共享 SCRIPT parser 和生产脚本 VM，实际执行 AI 入口、报价、原子 OTC、收据与真钱/币守恒路径；元数据覆写/旧收据测试只执行新增的实际 AST 子块，不再次调用有业务副作用的整个 record_receipt。政治解析、确定性随机、story factory/失败等沿原 VM 端口，不能视为引擎验证。候选提交时这些方法未编译、未执行；Root采用后在2026-11-20实际执行完整RedemptionScriptContract类45项及相邻发行/容量三类51项，合96项全部通过，原wait0/46.0902651秒。新增真实产品清单与脚本合同另1项通过，原wait0/7.878085秒。未在R0042热装，亦无新身份字段实机信用。[实际报告](../../docs/maintenance/evidence/2026-11-20-financial-markets-origin-receipts-ci-repairs.json)。整数账户 ID 的 floor 校验通过现有 values 文件新增的纯命名 helper，再以 `>= helper` 与 `<= helper` 双向比较；不用内联 floor 比较块。第六个方法从实际生产文件加载 helper、验证整数/小数/非正值、执行收据 AST，并在软件测试内替换再还原其定义以证明真实消费该 helper；VM 没有该名称的硬编码数值分支。


## 首次真实正额回收的窗口凭据

`xfm_reclaim_receipt_version=1` 仅在本次真实正额回收完成后、对照本次前后账户与窗口事实相符时最后写入现有 window。无新 story、付款、费用、随机或资格政策。凭据检查失败只保留未知，不撤销或阻止原合法返款。已发布但尚未回收的旧窗口可在采用源码后第一次真实正额回收时记录；早已完成、remaining=0/status=4、已有回收日/回收额或已有版本的历史事件不补证、不覆盖。原 `request_cents` 仍由原业务在转账前写入，凭据读取该新值，不消费旧残留请求、不改 request/result。

29 个不可变字段均以 `xfm_reclaim_receipt_` 开头：`version`、`day`、`actor`；`window/window_id`、`coin/coin_id`、`issuer/issuer_id`、`escrow/escrow_id`（真实引用与永久 ID）；`amount_cents/initial_cents`；`paid_before_cents/paid_after_cents`、`remaining_before_cents/remaining_after_cents`、`reclaimed_before_cents/reclaimed_after_cents`、`status_before/status_after`；`issuer_free_before_cents/issuer_free_after_cents`、`issuer_reserved_before_cents/issuer_reserved_after_cents`、`escrow_free_before_cents/escrow_free_after_cents`、`escrow_reserved_before_cents/escrow_reserved_after_cents`。

前值在原正额转账紧前采集，后值在原成功窗口更新后采集。两边核相同币、窗口、控制人及合法项目账户，永久 ID 为精确正整数，前值金额为精确整数；核 `initial=paid_before+remaining_before+reclaimed_before`、`amount=remaining_before=escrow_free_before`、`reclaimed_before=0`、`issuer_free_after=issuer_free_before+amount`、`escrow_free_after=escrow_free_before-amount=0`、两账户 reserved 不变、paid 不变、remaining_after=0、reclaimed_after=reclaimed_before+amount、status_after=4，且真实 transfer.result=1。数值运算只用于赋值，比较只对已采集标量，不用内联数学比较块。所有 `xfm_rr_*` 临时变量与别名在入口/出口清理，无逐日扫描和持续日志。

该凭据让一次真实 terminal SAVE 在字段已实际序列化且来源正确时保有本次前后事实，仍不是独立外部银行审计或未观察的业务通过；须核物理 SAVE、同 ID 原始数据及原资金账。旧 SAVE 缺字段为 unknown，不借其他场次代作 before。四个新增 Java 方法覆盖生产发布/兑付/回收与真实 transfer AST、原真钱与币守恒、失败及缺证仍合法付款、历史不补/版本不覆写、实际转账后注入错误 credit/reserve/request/ID/window 的拒证。2026-11-20实际执行完整RedemptionScriptContract49项及真实产品合同另1项，共50项全部通过，原wait0/32.695634秒；完整金融模块验证另行执行。故障注入仅在软件测试中把实际转账 AST 后接损坏语句，不能授引擎行为或错误资金信用；原 VM 的政治解析、随机、story 创建等端口范围保持。新凭据尚未获得真实SAVE读回信用。
