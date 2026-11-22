# 债务、危机与世界新闻运行合同

2026-11-18。本包已实现 CK3 脚本及 Java 参考领域代码；实际游戏加载、保存、死亡与后台通知须由公共验收给出独立结果。软件测试不能替代游戏通过。

## 结算与有限基金

期货结算源 story 调用 `xfm_debt_cover_shortfall_effect`，先设置 `xfm_request_debtor`、`xfm_request_creditor` 为真实账户 story，`xfm_request_cents` 为未付款的正整数分，`xfm_request_day` 为该原始结算日，`xfm_request_kind` 为 1盯市、2资金费、3强平、4到期。输入仅为已支付保证金之外的缺口，不能再登记已付款本金；正常新结算使用当前 `exchange.xfm_day`，失败恢复保留原日与原始 pending journal。

`xfm_request_fund_eligible=0` 表示该损失不承保；缺省为1，但资金费永远不承保，防止无本金的关联方资金费消耗基金。基金来自 `exchange.xfm_default_fund_account` 的实际 free，初始0。实际基金付款之后，相应部分转成基金对债务人的追索；原赢家只保留没有收到的部分。两份索偿之和等于同一笔原始缺口，不会让赢家再领取一份已付金额。

债务金额是义务，不是单笔现金转账：本版本单笔claim允许正整数至1,000,000,000,000分，大跳空超过支付入口上限仍完整记债。实际基金单笔代付上限100,000,000分，且不超过真实基金余额；其余全部保留为赢家未付债权，不截去损失。超过支持边界的结算须保留原 pending，不能静默视为结清。

`xfm_debt_donate_fund_effect` 允许玩家自愿将所选非系统账户的实际 free 捐入基金，输入 `xfm_ui_fund_donation_cents`（缺省1000分）。它不自动从其他账户、遗产以外的私人金币补款，也不授予收益权或领取基金的资格；不足时无付款。手续费向基金的真实资产分配由共同钱包独立处理。

输出 `xfm_result=1` 和 `scope:xfm_debt_receipt`。相同源、日和种类重试复用原回执；金额、当事人或承保资格冲突返回-2；早于该源同种类已处理日的请求返回-3，不再次付款。未来结算日拒绝；从原始 pending journal 恢复的旧日可正常首记，到期日保留原结算日，不刷新逾期时钟。源 story 保存每种类最新日与永久回执，既有债务永久保留独立 story，不能删除源再重用身份。

债务 story 包括永久 `xfm_debt_id`、源与日/种类、`xfm_debtor_account`、`xfm_creditor_account`、`xfm_fund_account`，以及 `xfm_original_cents/fund_paid_cents/winner_unpaid_cents/fund_recourse_cents/outstanding_cents/repaid_cents/written_off_cents`。账户 `xfm_debts` 与 `xfm_claims` 建反向索引。活跃债务另列 `xfm_debts_active`；结清后只移出活跃列表，历史债权不被销毁。

有 `source.xfm_coin` 的债务同时写入该币的 `xfm_claims` 历史列表，增加 `xfm_unresolved_claim_count`。完全偿还或经真实债权人减记至0后只减一次计数；有存量索偿的币不能被称为完全无义务归档。

Java `DebtLedger` 仅准备 `CoverPlan`/`RepaymentPlan` 的真实付款计划，调用者在共享钱包原子 batch 成功后 commit。失败 abort，不把尚未付款当作余额。保存拒绝未提交计划，恢复按完整回执、逐版付款及减记记录重建现状，不能只改当前合计来洗债。

## 偿付、援助与重整

`xfm_debt_repay_effect` 当前为债务 story，输入 payer账户、金额分与该 payer 单调递增的 operation。先向赢家未付债权付款，再向基金追索付款；每次仅按实际转账成功额减少债务。重复 operation 无二次付款。实际应付额是请求与未偿债务的较小值；余额不足拒绝本次请求，超出债务的部分不扣款，不创造零钱或退款。亲族援助为真实赠与付款，不隐式新建贷款。

玩家当前角色 `xfm_debt_pay_selected_effect` 使用已选择的合法账户，读 `xfm_selected_debt`、可选 `xfm_ui_debt_pay_cents`（缺省1000分），可为本人或他人实际付款。`xfm_debt_restructure_selected_effect` 只允许该债权人的实际法律 holder 自愿减记其赢家债权10%（一次）并展期30天；不减记别人的基金追索。`xfm_debt_reject_selected_effect` 记录债务人拒债，权利仍在。

AI 每日每账户最多使用500分偿债预算；非继承的个人账户可从其本人实际金币补足，系统账户与继承账户不自动动用技术 owner 或继承人的私人金币。所有存量义务仍每日处理。死亡不删除债务，原账户的继承/冻结由共同底座裁决。

实际至少1金的第三方援助可产生一次有期限感谢；同一个受援账户不会向同一援助人反复刷好感。实际债权人同意重整后可产生有期限感谢，首次拒债对实际债权人产生有期限失信关系。系统账户的技术 owner 不因公共基金付款而取得私人感谢，不凭欠债生成监禁或其他未经授予的政治权利。

## 危机与20种叙事

首次严重危机要求成人 AI、本人的非继承个人账户、持续逾期至少30日、债务超过24个月可偿收入且大于10金，并已存在严重压力。首次尝试真实亲族援助及实际 AI 债权人展期，记录机会；没有可用亲族时不伪造救助。

持续严重债务逾期7日后可对原成年 AI 债务人每7日增加一次压力，避免只有原本已经高压力的角色才感受到违约。援助与重整宽限期内暂停这项增加，玩家和遗产继承人不走该自动压力路径。

每7日评估一次，至少持续14日且有2次评估之后才可能进入罕见终局。最终再次检查成人/AI/存活、法律 holder 未替换、压力3、仍有真实严重债务，没有宽限或援助保护期；free、reserved、持币种数、挂单数及期货仓位数均必须已知且为0，角色外部金币也必须耗尽。缺字段、玩家、儿童、遗产继承人、有财产或已获得有效援助均不能进入终局。游戏规则关闭危机离世时，援助、债务及其他后果继续。

终局候选中死亡权重1、受保护生活9、继续求生190；即使财务条件相同，也不是确定的自动死亡。受保护生活仅提供风险缓和，不送金币或免债。死亡标记在真正 `death_suicide` 前保存，同一危机不执行二次死亡。

20种中英叙事来自实际所在省份、身份、特质、技能或宗族。17/18分别为真实战争军事角色的军书和实际剑客的挑战书，不假造战死或决斗结果。叙事无实施步骤、器具操作或伤情；不提供玩家自杀按钮。详见主设计的20项清单。

## 新闻与性能

业务 story 设置公开 actor、kind 后调用 `xfm_news_record_effect` 记录一个已经发生的新事实；其业务状态须先幂等结算。已有实际 revision 的调用者可直接将 `xfm_news_fact_counter` 设为该 revision，再 `xfm_news_enqueue_effect`；相同source/revision不重建条目。kind为1债务、2实际援助、3重整、4危机、5离世、6恢复、7上市、8退出、9调查披露、10融资失败。

每条新闻是持久 story，包含 source、event_id、全局 `xfm_news_id`、actor、kind、day、scene。`xfm_news_entries` 为完整世界新闻簿，无关系或距离过滤，不公布秘密金额。普通消息与死亡优先消息使用两条单链；每个人类玩家保存下一条指针，日处理只走最多3次跳转，不扫描全部历史。被限速的消息仍在队列与新闻簿；高频普通消息不会挡住死亡消息。玩家继承须迁移两个队列指针与当日送达计数。

真实通知使用原版 `send_interface_toast`、`event_toast_text_neutral/bad` 与 `every_player`，不触发大事件确认、强制暂停、前台激活或置顶。正文由 text 样式读取；`localization_values` 显式传递接收者、新闻条目与当事人三个命名作用域，语法依据本机原版通知实例。当前代码限制为每游戏日3条总计；原版 `gui/hud_notification_templates.gui:554–593` 的 `ToastMessageHandler.GetMessage` 只提供一个 active message，三种样式互斥，静态 UI 证据支持不会同时铺开所有来信。R0065 实机仅观察到标题，正文与身份关联未通过；后续源码修复及14项相关检查通过不改变该失败记录。修复后的正文、队列送达和焦点仍须后台实机验收。

## 原版接口依据与验收范围

本轮读取 CK3 1.21 安装文件：`common/scripted_effects/20_health_effects.txt` 的 `death = { death_reason = death_suicide }`；`common/deathreasons/00_event_deaths.txt` 的公开 suicide cause；`00_ep3_decision_effects.txt` 的 neutral toast；`00_activity_effects.txt` 的 bad toast；`00_decisions_effects.txt` 等的 `every_player`；`11_dlc_pam_scripted_effects.txt` 的 `remove_list_global_variable`。这些证明所用原版接口存在，不授予新脚本在游戏内的完整资格。

本轮执行机器 `machine_id: 4-8e1c2f1861` 的 1.21 安装文件 `common/script_values/_script_values.info:29–30,79–87` 明确：脚本公式 `max` 是上限，`min` 是下限，按书写顺序执行。例如15经过 `max=10` 得10，负数经过 `min=0` 得0。因此本模块基金、付款、偿债预算采用 `max` 限制实际余额和债权，收入与逾期的非负下限采用 `min=0`。2026-11-18 修正了此前写反的原生公式；Java 的 `Math.min/Math.max` 保持其语言自身语义。本次源码修正尚须实际游戏用余额不足、跨日逾期和重整金额验证，不能由源码检查推定已通过。旧稿的 desktop 机器 ID 来自历史升级摘要中的作者常量，已据实际机器识别纠正；原软件结果及纠正收据分别保留。

验收须覆盖：有限基金不足、资金费不承保、同结算重试/冲突、援助同日阻止旧终局、玩家/儿童/遗产/持资产拒绝、20条件叙事可达、远方人物对多个人类广播、队列限速及保存继承、无暂停/焦点变化和实际场景性能。
