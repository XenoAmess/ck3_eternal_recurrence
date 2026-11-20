# 普通 GUI 期货交易的零日局部验收

`futures-gui-transactions` 是独立的 saved-campaign case。它沿现有 GenericAdapter 的两个 `at_day:0` Root phase，在同一原生日期暂停操作。它不替代 `derivatives` 的14日盯市、资金费、强平、到期及债务条件，也不改变 financial clock。正常退出和 OS/Native 清零仍由共享 postclose 验证；phase里不预称已经关场。

加载正式产品与原有限 XFMA story catalog 的 `visible=no` 被动声明。没有 fixture emitter、业务脚本、timer、on_action、observer ARM、变量初始化、资金、价格或对手方设置。旧观察 story 可以正常载入，但其完成标志不获得本轮信用，未知类型不悄悄加入 catalog。

第一 phase `bind-current-financial-baseline`：从实际最新物理 SAVE 冷恢复，先保存并独立比对完整已支持金融图，核当前合法 private account、余额/冻结、原 contract/asset/oracle 与权限。必须在任何新金融 GUI 交易前留下这档新 baseline。Root response 额外给 `baseline_archive`、`baseline_audit`、`baseline_raw` 三个 FilePin，全部属于该 response.evidence。

第二 phase `normal-gui-transactions-and-saved-reconciliation`：正常当前 GUI 选择、提交并逐步留档。六格为 `long`、`short`、`leverage_selection`、`add_margin`、`withdraw_margin`、`reduce`。Root response 的 `futures_gui_transactions` 必须恰好包含六格：

- 未有资格、流动性或实际 fill：`{status:"NOT_OBSERVED",reason:<真实原因>,evidence:[实际FilePin或空列表]}`。委托 accepted/handled 不会自动升级为成交。reduction 委托尚未成交也保持 NOT_OBSERVED，可保留它的原件。
- 已观测：`status:"OBSERVED"`，提供 `before_archive`、`after_archive`、`audit`、`raw`、`gui_actions:[{query:<pin>,activation:<pin>}]`，以及 adapter 中该格的四条共同断言和一条专属断言，全部明确为布尔 true。所有引用须在本 phase.evidence 中且原文件 SHA/bytes 未变。它们是 Root 独立原始证据审阅；Python 不把 JSON 形状当成已执行金融业务，也不生成这些 true。
- 两个 archive receipt 必须保留 Native 原 `physical_save_confirmed=false`，由 accepted、SDK checkpoint.status=saved/实际size/SHA/date、materialization.available=true 和独立 exact_copy/same_file=false 共同绑定同原生日期的独立前后档，不能以一份档案充当两个端点。原金额、双方账户/权益/冻结、每单累计手续费及无关资产都要按实际 audit/raw 核对。源码测试使用 authored 端口，仅验证消费者控制流与拒绝边界；不授实机金融信用。

最多六档新物理 SAVE，每档≤256MiB：baseline，LONG与杠杆3联合，SHORT，add，withdraw，reduce。联合步骤允许两格引用同一对真实前后档及各自原GUI收据；不把一个真实 fill 计成两笔交易。若某格缺项可少用档，不能新增 SAVE/重放来追求随机成交。累计外档上界为1536MiB，实际 local copies、archives、读回、日志、运行静态依赖另按 Root 的真实 aggregate admission 计入，case登记不是存储许可。

原13/14已撤单、原11的4→2减仓不得重放。后继选择以实际新 SAVE、当前页和 fresh query 为准，不能用已闭 R35/R37 的 widget path、票据或版本派发。模型指数与币来源分开；杠杆选择只改新票据，不改已有仓位倍率。保证金追加、提取及减仓必须分别留下真实后态，不能只凭最终净0断言往返成功。

可先运行新 LONG3 一手，再按实际独立对手/资格考虑 SHORT5；追加默认100c须有真实 private free，提取须满足当日结算、无pending、live oracle和initial+提取额。无资格或无成交不能靠改价、注资AI、设置业务变量、重ARM或延长日期解决。

`observed_cells` 只列有完整独立原件的格，`not_observed_cells` 原样保留缺项。`business_pass`、`product_release_pass`、`derivatives_acceptance_pass`、`financial_clock_qualified` 均保持 false。正常 close 后本 case 的协议完成也不能升级为全期货或完整产品通过。

2026-11-20 Root实际执行：新模块15项普通模式通过，同15项优化模式通过；受影响的 `tools.test_generic_product_day_boundary` 和 `tools.test_continuous14_clock_diagnostic` 首轮40项中39项通过，1项旧策略清单测试失败。该测试原来把显式stop也算成observe；仅修正这项清单断言并单独重跑原失败方法通过，原两个observe作用域约束保留。没有重跑未变SDK、Host或Native，也未授实机信用。见[实际软件证据](../../docs/maintenance/evidence/2026-11-20-financial-markets-futures-gui-case.json)。

准备会按原 resolve_post_start 绑定实际普通书签条件。运行与验证同样先调用这个原解析器，再严格比较 prepared config；原模板保持null，非null原条件不得覆盖。前后端点及六档计数按 receipt.archive 的真实SAVE路径/签名去重，不能用两个receipt别名伪造两个档。01错误形状和来源对照保留，02另增真实R37协议与完整saved prepare→run→verify源回归。

第二phase还必须给 `physical_archives:[FilePin,...]`，明确列出本场全部实际SAVE的archive receipt，包括未成交、拒绝、NOT_OBSERVED步骤的档案及baseline。每个receipt必须属于该phase.evidence；按真正archive SAVE身份核唯一、同日和总档数≤6。OBSERVED格的两个端点必须在此表；一个未成交步骤的真实SAVE同样消耗预算，不因没有业务信用而漏计。

## R0041：既有仓位连续14自然日的端点补证

2026-11-20，机器 `4-8e1c2f1861`，实际运行 `clock-cadence-continuous14`，只有 D0/D14 两档 SAVE，没有新增金融 observer 或 GUI 交易。本次补证不增加上文零日交易六格的信用。Native 日期 `53146992→53147328` 推进14日，但金融日 `108→121` 只有13日；缺日事实另行保留，不报告14次金融结算通过。

到期仓位66（原生 Story8747）保留原双方账户、两手和3倍杠杆，金融日120留下 `kind4/status2/last_settled_day120/archived_day120` 的完成记录，mark从103变101。双方原抵押8748/8749各从69c变0且状态2，未用记录消失推断平仓。末次 `settlement_complete=1/shortfall=0/pay_now=0`，pending付款、金额和已付字段已按脚本清除；这些末次字段不能还原累计付款，也不能把各69c都称为纯退款。

永续仓位65（原生 Story8742）仍为两手开仓，mark95→100，最新为第121金融日kind1完成记录；多方原抵押64c不变，空方190c→180c。没有 `last_funding_day/funding_rate` 的实际字段。原始读回的合约253末次成交为第115日、300c、3手，在第121日不满足资金费10000c、10手及成交新鲜度门；本场未证明合格非零资金费付款。

账户54 free/reserved为 `8287/364→8370/295`，总额+14c；6422为 `67/568→620/0`，总额−15c；7509为 `176/640→176/630`，总额−10c。54的+14c与66空方价格差+4c和65多方价格差+10c相符，但原有持仓和其他现金流不获得逐笔归因。两个完整金融图均无账户抵押对账差异、无未归属抵押、余额非负；这证明端点内部账实一致，不证明跨日封闭系统守恒。

Root已实际执行薄算术消费者，原wait0、0.2031229秒，结果范围为 `LOCAL_ENDPOINT_ARITHMETIC_ONLY`。原终点pipeline因比较报告超过8MiB退出1的失败仍保留；仅续读已完成的metadata生成恢复摘要，未重做SAVE或将原失败改为0。仍缺逐日付款历史、可独立归因的退款金额、合格非零资金费、同日重复支付实测及全期货验收。见[本次原件与局部范围](../../docs/maintenance/evidence/2026-11-20-financial-markets-r0041-derivatives-endpoints.json)。

原件另证本场正常关场：Game、Host、keeper以及公共run/verify原退出码均0，`native_cleanup_proven/normal_close_qualified=true`；随后公共lease为done、CAS15719、resources为空。该闭场资格只证明本场收束，不增加金融日覆盖或完整产品通过。
