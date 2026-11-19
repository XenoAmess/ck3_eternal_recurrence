# 独立业务验收矩阵与只读观察扩展

2026-11-18。六份后续 case 的公共注册与 Java 观察 profile 已采用；196文件统一金融版本在修复三处集成测试问题后，完整工具246项通过、0skip（首次239项的2failure/1error保留）。云端44359949157实际共享10项与金融246项共256项通过、0skip；静态包仍不授实机信用。第七场沿Q11/196文件取得有限主线程PSS取证，启动强制读取仍失败，原场已清树并释放。业务动作/游戏日/SAVE为零，不能由Q11及软件调用授予实机修复通过。正在从真实线程上下文与PE核实阻塞位置；旧heartbeat的active0不能排除observer在执行，raw可执行栈地址不是正式unwind。当前仍为`SOURCE_ADOPTED_SOFTWARE_PROFILE_NO_BUSINESS_CREDIT`。`core`只覆盖付费发行与现货子场；每个后续case必须生成自己的manifest和严格输入，不能借用core的五个标记。实际准备、场次、资金读回和物理保存分别验收。

本轮新增有限资金回兑还须在真实场次核发行现金预存、独立持有人交币与实付、过期余款回收、继承后的同一账户/条款，以及物理SAVE中的窗口/收据与现金；现有246项及7项新SAVE子例均不替代这些后态。期货盘口须核所选永久合约号、真实有资新仓委托、独立限价和实际交易日VWAP，不能拿现货报价或提交成功代替期货成交。

## 分组与有限预算

共享 `generic_product_adapter` 承担 prepare→allocate→preflight→run→verify、实际 Saved 启动、原生日期、GUI 证据、物理保存和正常关场。新增数据不创建另一个 runner。每组开始前固定自然日上限及墙钟预算，不在失败后扩期。

| case / JSON | 主要业务 | 自然日上限 | run / GUI hold / 正常退出预算（秒） | 必要的真实前置存档 |
| --- | --- | ---: | --- | --- |
| `derivatives` / `financial_markets_derivatives.json` | 做多、做空、杠杆、保证金、盯市、止损、实际强平与穿仓债权、资金费及到期 | 14 | 5400 / 1800 / 180 | 合格价格历史、真实资金和对手方；欲验穿仓需已有真实高风险仓位，欲验到期需窗口内到期合约 |
| `lifecycle` / `financial_markets_lifecycle.json` | D0公告、退出窗口、D15–20定价、D21终结或待结算、D30退出、OTC及债权保存 | 35 | 10800 / 3600 / 180 | 有真实外部持币人、订单、期货与未付债权的币；自动90日低需求及重上市另需真实已积累历史 |
| `delisting-gui` / `financial_markets_delisting_gui.json` | 独立正常GUI公告、同币kind8、实际单人通知、14/21/30日退出及权利保存；不代替完整lifecycle | 35 | 10800 / 3600 / 180 | 真实玩家控制币、私人账户和外部真实持币来源；期货/债权可选且必须同币，缺失分支未观察。候选尚未编测/注册ready，见独立说明 |
| `inheritance` / `financial_markets_inheritance.json` | 自然死亡、实际继承人、同一账户/义务、独立私人账户、无继承人冻结、新闻游标 | 14 | 5400 / 1800 / 180 | 真正临近继承的角色、真实财产及义务；实际继承人已有另一账户 |
| `cold-reload` / `financial_markets_cold_reload.json` | 物理SAVE、新进程冷载、业务图一致、同日刷新不重付 | 0 | 3600 / 600 / 180 | 其他真实业务场次的已确认物理保存及保存前完整读回；原进程正常退出 |
| `news-crisis` / `financial_markets_news_crisis.json` | 真债援助/重整、危机保护条件、远方新闻、普通/死亡双队列、实际随机叙事 | 14 | 5400 / 1800 / 180 | 真债已逾期且有真实压力/评估历史；保护对照角色和真实新闻积压 |
| `ai-capacity` / `financial_markets_ai_capacity.json` | 低阶/无地AI付费发行买卖、轮转、容量、全部既存义务、逐日性能 | 395 | 43200 / 7200 / 180 | 实际成熟市场；30日预热+365日测量；每档独立真实存档与基线 |

上述有限预算已写入公共 registry；定义可准备不代表已经 allocation。命令预算300秒、启动 readiness 1800秒及具体场次预算在正式 allocation 冻结。运行循环在预算内多次短等并持续报告；超时保留原件并记窗口未完成，不能删慢日或把365日降为100日。

Saved case 的 `required_startup=[]` 是有意安排：第一阶段 `at_day=0` 读取保存基线并通过正常 `xfma_observer_widget/xfma_arm_observer` 启用观察，之后才消费该 profile 的标记。不能在 Saved 启动门等待一个尚须 GUI arming 才能生成的标记。`cold-reload` 必须在启用观察或打开金融窗口之前取得业务图，以免初始化掩盖未加载字段；它的 profile 必须能在同日按钮检查时完成读回，不能要求跨日才发成功标记。

## 真实操作与判定

前置存档只提供它已有并有来源证明的业务历史。本场新增业务通过必须有本场前后读回和实际动作。观察器只写 `xfma_` 状态、技术观察 story、自己的日志和快照；禁止发钱、发币、下单、改价、改保证金、改压力、强制AI决策、强制死亡、修改继承人、改角色、快进业务年龄或删债。真实操作通过正式 GUI，由公共后台通道执行，全程最小化、非置顶、不激活前台。原生或 UI 通道不足时修共享通道或记 BLOCKED。

期货先固定所选资产、原生日期、双方实际经济受益人、账户、报价、杠杆和可支付额。合格币7个完成日最高3倍；14个完成日且上市30日等资格满足后最高10倍；模型指数最高5倍。当前没有真实独立多场所 producer，20倍的正确业务结果是拒绝，不能为测试虚构20倍资格。1/2/3/5/10倍分别获得支持条件内的正例和条件外拒绝证据。一次看见仓位不等于所有杠杆档已验。

退出、止损和强平必须看到真实资金支持的独立对手方成交；无对手方时保留订单或风险义务，不能按标记价造买家。跳空没有自然发生，便把穿仓子项记 `NOT_OBSERVED`，不操作测试变量制造穿仓。若真实发生，逐笔核对原始差额 `S`、实付保证金 `M`、基金代付 `F`、赢家未付 `W` 和基金追索 `R`：`S=F+W`、`R=F`；赢家实际收款 `M+F`，债务人新增债务 `W+R=S`。资金费欠付不承保，`F=R=0`。基金前后还须计入真实手续费注资或捐赠，不能只比较余额总差。

退市按实际公告日计龄，不按场次开始日重置。D21没有可靠窗口价就待结算；D30停止场所交易不销毁持币与债权。至少留一个健康市场对照，以证明摘牌只影响相应资产/场所。旧债未清时归档受阻；重上市不换币ID、不刷新旧债和发行冷却。

继承只跟实际自然死亡与原始继承关系。`allow_actor_change=true` 仅允许公共通道读回真实角色变化；`continue_as_heir_requirements` 只处理原生已发生的继承模态，不授予控制台换人。没有死亡则未观察到继承；已有死后存档只验加载后的权利保存，不反推死亡转换正确。原账户保留ID，真实继承人取得法律holder，原债/债权仍指向该账户；无继承人冻结保留死者，不把技术保管者当私人产权人。

危机须逐项证明年龄、AI身份、原holder、真实债务收入比、逾期、压力、评估成熟、无保护及已知零财产。玩家、儿童、继承账户、有财产、受援或规则关闭的对照，不以“14天没死”代替条件核验。援助必须真的付款或真实债权人同意，随后立即失去旧终局资格。随机终局不保证14日发生；不反复读档刷死亡、不强制20种场景。每种叙事单列实际发生证据与条件；17需真实战争/军事身份，18需实际剑客特质。未发生的叙事保留未观察到，软件可达性与游戏业务证据分别记。

新闻须选一个远方无关系来源，并同时出现普通与死亡优先积压，读每个人类的送达状态。单机只授该人类的送达证据；所有人类/多人一致性还需实际多个连接玩家。每个事实保留 source/revision/id，可从新闻簿翻旧页；限速后未送达仍应在队列。观察器不得自发死亡或新闻事实来通过该项。只读审阅、同日刷新和保存冷载不能重复扣款、创建事实或死亡。

## 最少只读数据合同

每份观察回执包含 schema/profile/observation_epoch、实际源码和正式包hash、`machine_id`、EXE/build/SHA、实际DLL、源保存hash、原生日期及当前玩家身份。以下是生产字段；除明确标注“待补”的身份/测量接口外，不新增假定字段。缺值、null、空集合必须区分，缺值不能当0。金额以整数分输出，64位原生身份以规范十进制字符串输出，拒绝bool/浮点冒充整数。

| 范围 | 必要生产读回 |
| --- | --- |
| 共同基线 | exchange `xfm_day/xfm_last_date/xfm_fee_cents/xfm_default_fund_account`；币/账户/订单/债务注册及反向索引；当前角色与实际原生日期 |
| 现金账户 | `xfm_account_id/xfm_holder/xfm_system_account/xfm_account_frozen/xfm_inheritance_state`；`xfm_free_cents/xfm_reserved_cents`；`xfm_positions/xfm_orders/xfm_reservations/xfm_debts/xfm_claims`；`xfm_holdings_count/xfm_open_orders_count/xfm_open_positions_count`；法律holder真实gold |
| 币和现货 | `xfm_coin_id/xfm_controller/xfm_issuer_account/xfm_supply_units/xfm_listing_state/xfm_trading_open`；真实持仓 `xfm_account/xfm_coin/xfm_quantity_units/xfm_reserved_units`；订单 `xfm_order_id/xfm_account/xfm_coin/xfm_original_lots/xfm_remaining_lots/xfm_filled_lots/xfm_filled_notional_cents/xfm_fee_paid_cents/xfm_status` |
| 价格来源 | `xfm_index_cents/xfm_mark_cents/xfm_oracle_quality/xfm_oracle_day/xfm_oracle_last_valid_day/xfm_oracle_valid_days/xfm_max_leverage/xfm_oracle_reason/xfm_oracle_source_id`；完成日价格及实际参与受益人样本；`xfm_last_price_cents/xfm_price_version`不能单独充当可靠价 |
| 期货委托/成对仓位 | contract `xfm_contract_id`；订单 `xfm_order_id/xfm_contract/xfm_account/xfm_side/xfm_limit_cents/xfm_leverage/xfm_remaining_lots/xfm_reservation`；仓位 `xfm_position_id/xfm_contract_id/xfm_contract/xfm_coin/xfm_long_account/xfm_short_account/xfm_long_leverage/xfm_short_leverage/xfm_lots/xfm_mark_cents/xfm_status/xfm_long_reservation/xfm_short_reservation/xfm_created_day/xfm_last_settled_day/xfm_last_funding_day`；两份reservation的 `xfm_reservation_id/xfm_remaining_cents` |
| 期货挂起清算 | `xfm_pending_payment/xfm_pending_day/xfm_pending_kind/xfm_pending_new_mark/xfm_pending_amount/xfm_pending_paid/xfm_pending_debtor/xfm_pending_creditor`；真实exit订单、实际成交价量、停止价/止盈价和对应仓位 |
| 债权 | `xfm_debt_id/xfm_source/xfm_source_day/xfm_source_kind/xfm_fund_eligible/xfm_debtor_account/xfm_creditor_account/xfm_fund_account`；`xfm_original_cents/xfm_fund_paid_cents/xfm_winner_unpaid_cents/xfm_fund_recourse_cents/xfm_outstanding_cents/xfm_repaid_cents/xfm_written_off_cents/xfm_due_day/xfm_overdue_days/xfm_state`；coin `xfm_claims/xfm_unresolved_claim_count` |
| 退市 | `xfm_notice_day/xfm_delisting_age/xfm_derivatives_reduce_only/xfm_termination_window_start_day/xfm_termination_window_end_day/xfm_termination_samples/xfm_termination_price_sum_cents/xfm_termination_price_cents/xfm_termination_price_certified/xfm_termination_requested/xfm_settlement_price_pending/xfm_active_listing_counted`；业务请求与实际状态转换 |
| 继承 | 角色 `xfm_account/xfm_accounts/xfm_inherited_accounts/xfm_active_account`；原生实际primary_heir及死亡事实；账户原holder/新holder、冻结/继承状态；余额和义务全图 |
| 危机 | account `xfm_crisis_state/xfm_crisis_actor/xfm_crisis_started_day/xfm_crisis_reviews/xfm_next_crisis_review/xfm_crisis_terminal/xfm_crisis_relief_until/xfm_aid_opportunity_recorded/xfm_last_debt_stress_day`；debt `xfm_extension_granted`；helper `xfm_financial_aid_cooldown`；规则状态、holder年龄/AI/压力/收入/外部财产；20场景所需真实上下文 |
| 新闻 | global list `xfm_news_entries`；exchange `xfm_news_head/xfm_news_tail/xfm_news_urgent_head/xfm_news_urgent_tail`；news `xfm_news_id/xfm_news_source/xfm_news_event_id/xfm_news_actor/xfm_news_kind/xfm_news_day/xfm_news_scene`；human `xfm_news_next/xfm_news_urgent_next/xfm_news_delivery_day/xfm_news_sent_today/xfm_news_cursor`；实际原生toast展示与焦点/暂停状态 |
| AI容量 | exchange `xfm_ai_head/xfm_ai_tail/xfm_ai_count/xfm_registered_coin_count/xfm_pending_coin_count/xfm_active_coin_count/xfm_new_listings_today/xfm_futures_open_positions_count`；actual角色队列next与身份；实际规则预算、关注名单、真实发行费和交易前后余额 |

期货 owner 已补入 contract `xfm_contract_id`、position `xfm_position_id` 及缓存的 `xfm_contract_id/xfm_created_day`，保留原story与法律账户引用。exchange 高水位为 `xfm_next_futures_contract_id/xfm_next_futures_position_id`，只增不复用；拆仓新slice各有新ID，原source不换ID。该源码身份合同尚待统一验证与实机证明。冷载按永久ID、合约ID、双方账户ID、创建日、mark/lots及reservation对应比较，不能靠列表下标或同金额总数认定同一仓位/清算源。

字段清单用于限定新增只读profile，不是要求每日扫描全世界全部历史。前后业务图在有限阶段完整读取；日常观察仅关注事先固定的相关对象及 bounded计数。新增注册/新闻/债权依永久ID增量读取，全部原始样本保存到场次目录。出现新事实最多发一次对应标记，不能每天重复同一 `TEST PASS` 字面量；共享 adapter 会拒绝重复标记。

## 当前观察 producer 与验收边界

1. `FixtureEmitter` 继续作为同一个 producer。core 保留 schema 1；六个后续 case 由严格的 `FollowupContracts` schema 2 输入选择 profile、epoch、目标身份与标记，不把新字段塞进旧 core 请求。实际源码闭包为六个 producer 源，manifest 与公共 Saved inventory 共同核对。
2. 每个 profile 使用有限的实际目标和独立标记，只增加 `xfma_` 观察状态。观察 marker 不等于 JSON 中各项业务要求已通过；相关账户、资产、合约、仓位和债权必须互相绑定，不能以另一对象的历史状态补足。
3. Saved 启用后按 profile 记录只读基线。继承观察拒绝对已有基线再次 arm，不覆盖原账户与原 holder；观察过程不改变法律资产关系。`cold-reload` 保留同日基线和刷新检查，不要求跨日才产生观察结果。
4. 观察器不能调用任何 `xfm_*_effect` 获得测试状态。对同一转账、手续费、债权和供应，用读回后的整数数据独立重算。生产trigger分支、源码包含某行、Java领域测试或观察器日志均不能单独授业务通过。
5. 观察profile只证明其明确谓词。例如“仓位存在”不证明正常GUI下单，“余额非负”不证明守恒，“离世已记日志”不证明全部保护条件，“新闻条目存在”不证明原生气泡实际送达。Root必须消费实际GUI动作、native前后图、日志和物理SAVE，并保留UNKNOWN原动作，不重放。

生产调度新增`xfm_ai_work_today/xfm_attention_work_today/xfm_ai_decisions_today`，分别累计两环实际出队尝试、关注尝试和进入三个消费者的角色数；还需实际存档读回确认。关注环的head/tail/count及角色next/queued/until_day、last_decision_day须冷载核对；计数不能单独证明每个角色的调用次序或资金效果。纯脚本不能可靠测出每日hook净耗时；需要合格只读Native/profiler的实际callback追踪，无能力时保留`UNMEASURED`，不把源码预算当实测。

## 原生算术必须有实际数值例

本轮在 `machine_id: 4-8e1c2f1861` 的CK3 1.21安装文件 `common/script_values/_script_values.info:29–30,79–87` 读取到：公式 `max` 设上限，`min` 设下限，按书写顺序执行；迭代器 `max` 是数量限制，属于另一接口。债务模块与期货模块已发现并修正相反理解导致的公式错误，旧静态通过不能替代修复后的业务验证。旧稿的 desktop 机器 ID 是沿用历史摘要的作者常量，已按本轮实际机器识别纠正，原测试报告不据此改写或重跑。

| 实际输入算例 | 期望原生读回 | 对应证据 |
| --- | ---: | --- |
| 150000分缺口、基金实际4000分 | 代付4000、赢家未付146000、基金追索4000 | 基金实际扣4000，赢家到账4000，债务150000 |
| 请求1200、欠900、payer free1000 | 付款900，余额100，债务0 | 非请求1200全部扣、非余额不足误拒绝 |
| 月可偿收入为负数 | 严重债务比较阈值1000分 | 先下限0，再乘2400，再下限1000 |
| 月可偿收入2金 | 比较阈值4800分 | 24个月×2金×100分 |
| 赢家未付9分，自愿一次减记10% | 减记1分，余8分 | floor后下限1，无基金债权误减 |
| 原due_day10，当前day40 | 逾期30日；账户各债最长逾期取最大 | 不归零、不刷新原到期日 |

表中是待在真实生产状态找到并核验的输入/预期，不授权fixture把输入写成这些数。正常GUI金额不恰好相等时，用观察到的实际整数先固定独立预期，保留同样边界类别。

## 容量与未覆盖范围

`ai-capacity` 沿现有方案保留30日预热、365个逐日样本。2048/4096/8192分档分别验，不能从128币smoke外推4096币。报告每日日实际active/pending/registered数、热点簿、真实未平仓、独立候选及实际交易数，保留P50/P95/P99/最大值和每个原始样本。512是候选预算，不等于每天512笔真实交易。真实AI因钱、冷却、需求失败也要保留其合法原因；不能为凑吞吐强制下单。

默认目标每日新增处理P95≤100ms/P99≤300ms、详情≤16ms、新增保存状态≤16MiB，仍需合格测量。MCP墙钟包含通信/等待不能直接标成hook耗时；完整存档大小也不能直接标成Mod新增状态。无归因能力只报告可观测量和基线差值。保守档1,024、默认档4,096、扩展档8,192的既存成对仓位上限分别按实际规则检查；全部既存仓位仍须每日处理风险，性能降级优先限制新增风险，不丢旧义务或新闻。

六组补发行/现货后的主要缺口，仍不自动覆盖宗族/政权概念宣发、实际用途/担保、拉抬抛售与披露、每种规则开关组合、版本迁移、所有20种自然叙事及真实多人竞争/重连。它们按主测试计划逐项留状态与后续真实业务证据。每个case `whole_product_release_pass=false`；任何一个或全部数据文件存在，都不构成完整Mod或发布验收通过。

## R0030实际业务证据追加（2026-11-20）

machine_id: `4-8e1c2f1861`。以下是R0030原物理档／独立读回取得的有限信用，不覆盖上方case约束或先前R0022／R0026／R0027／R0028／R0029事实。[共同原件索引](../../docs/maintenance/evidence/2026-11-20-financial-markets-r0030-sampling-and-independent-business.json)。

| 范围 | 实际结果 | 本轮仍未通过或未观察 |
| --- | --- | --- |
| 自然推进与保存 | raw53144856→53145696，真实35日／五份物理档 | financial22→56仅34次，缺raw53145072；D35 30项违例，Root连续采样断言false，整案未通过 |
| E5 post-finance观察 | 已观察记录与实际金融日对齐；D14自动诊断在手动Refresh前保存 | 不等于漏dispatch修复；Refresh不补历史，根因仍unknown |
| 基线既有AI募资失败／退款 | 两币2／3的失败退款见证、供给归零和state7；各1600冻结与原钱包返还独立相符 | 另79来自旧现货单到期；D35为原结果保持，不是新退款、新AI发行或费用实扣证明 |
| 原期货到期终态／抵押 | 三原仓转status2，六抵押归零；D14／D30／D35终态原记录保持 | 合约3仍status0；不授完整付款、索偿或exactly-once因果验收 |
| 财务端点对照 | D30→D35所有695个金融账户完整投影相同 | 未追全部原版gold出入金，不授跨系统封闭守恒 |
| 新AI发币／上市、低阶无地费用 | 可用性与未发生分支如实保留 | 本窗新发行／上市NOT_OBSERVED；初见rank／gold及registration元数据不替代发行瞬间身份与实扣 |
| 正常上市币退市／通知、危机与气泡 | 当前既存募资失败的归档／退款另记 | 不替代30日公告退市case；无toast送达、危机或容量通过信用 |
| 运行闭环 | 公共run2保留；Host0／正常关场true、Game0／Job0／keeper0、release15577资源空 | 正常关场不覆盖采样拒绝、完整产品或发布 |

D35原READCHAIN／内层读取超4MiB失败1保留；独立17／17／10分批恢复0不扩预算，不重跑游戏或SAVE，未读字段不按零处理。后继必须消费最新D35物理归档，继续独立退市case，不修改已保存时间戳或重放原动作；主测试计划其余未验范围保持原状态。
