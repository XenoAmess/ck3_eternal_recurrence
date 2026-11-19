# 正常 GUI 公告退市的独立验收

`delisting-gui` 是一个独立的 saved-campaign 业务 case，最长35个新增自然日。它明确允许在观察 Arm 和真实基线之后，玩家通过正式发行页进行一次公告退市并确认 `xfm_market.103`，随后自然观察14/21/30日。它复用 schema2、Java emit、公共 Saved prepare/run、后台 GUI、实际 Native、物理 SAVE 及正常退出，不创建另一套运行器。Root已采用并完成金融工具完整380项验证，复用精确未变的共享23项原件，合403个不同测试、0失败／错误／跳过；注册项现为可执行的 `ready`。尚未进行本案例实机公告或气泡验收，软件通过不授业务通过。

这不改变原案：`market-evolution` 仍只允许 Arm/Refresh、自然日、真实事件处理及保存，不能在其基线后公告；严格 `lifecycle` 仍要求真实期货和同币未清债权、退出后的原债保存及真实 OTC；`news-crisis` 仍要求债务、援助/危机保护、远方普通/紧急队列等证据，最长14日。新 case 不能授予这些旧案 PASS，`whole_product_release_pass=false`。

输入仍是现有 schemaVersion2 的七字段请求，caseId=`delisting-gui`。actor 使用实际 CURRENT_PLAYER 或有据 history character；accountId/coinId 是本次新物理来源 SAVE 的真实永久 ID，indexId/newsId、coldBaseline、scaleTier 必须 null。contractId、positionId、debtId 可不提供；提供时必须存在且属于同币，仓位须属于目标账户和指定合约。不得借用另一个模型指数或别币债权。无债务不是本窄 case 的失败，但未出现的债务/穿仓/终结支付分支只记 `NOT_OBSERVED`。

Arm 要求存活成人玩家控制真实 state1/2/4 币，有正供给、本人可用私人账户和另一个法律持有人的正持币来源。观察器保存币/账户永久 ID、供给、原公告日、真实新闻高水位、币自身事实高水位、控制者，以及按账户 ID 选出的一个外部持币 story/账户和原数量。外部账户不能只是同一法律持有人名下的另一个账户。它还最多保存64个真实同币合约引用，第65个仅置覆盖不足；不扫描全角色，不创建金融账户、币、仓、债、订单或新闻。所选外部来源是一个具体见证，不能代表所有持币人守恒；完整权利检查仍须独立物理 SAVE 审计。

本案普通入口是 `xfm_market_window` 的发行页、控件 `xfm_market_announce_delisting`，文字“公告退市（30 日退出期）”，随后真实 `xfm_market.103` 的 `xfm_market_delist_confirm`。“公告”没有额外费用或独立冷却，实际状态须为1至4且不是3；正常确认冻结实际 coin object 并重新核控制权限。实际公告日 N 必须等于本场 day0 基线日，不能在35日预算后才补30日。确认后读回 N、state3、age0、spot仍开、reduce-only，以及真实新 kind8 日志。仅按钮可用或确认 ACK 不算业务已生效。

| 检查点 | 必须取到的实际证据 |
|---|---|
| day0 / N | 正常按钮与103确认的完整原件，目标原生和永久 ID、状态前后、新新闻的 source/event revision/actor/kind8/day、同日物理 SAVE。重复读回不刷新 N；不得影响另一个指数或币的合约。 |
| N+14 | 同原公告及退出窗口，spot交易开放与reduce-only。若另测下单/减仓，必须有正常真实资金和对手方证据；无业务不填成功。 |
| N+15..20，N+21 | 实际完成日合格价格样本；3至6个样本时证书为真实总和/样本数向下取整，绑定同币、原 N、窗口N+15..20。少于3样本只能 pending，不造0价/最后价。不把证书请求等同每个仓位付款完成。 |
| N+30 | 原币 state5、trading0；只对届时真实仍开放的本币订单清剩余资产。币身份、供给、全部真实账户/持币/债权/待结算来源仍在。原始订单已成交、撤销或自然到期时，其退市撤单分支是未观察到。 |
| 最迟 N+35 或预算终止 | 独立读回、物理 SAVE、实际正常退出原件。缺少必需通知/退出/权利证据便不能给窄业务 PASS；不扩期、不复活旧动作或刷新通知。 |

原先 R22 的 BUY234 若仍保持到期日金融35，而公告在金融8，则它在公告后第27天自然到期，早于N+30=38。不能把该释放冒称退市强制撤单。正面退市撤单证据必须来自真实后到期订单在正常市场中自然存续；不能防止成交、修改到期日或制造买家。

kind8 在普通公告生效时立即记录到永久日志，并加入普通新闻链。下一正常金融日的新闻 dispatch 才可能发送；紧急链优先，总量每人每日最多3条，积压时不保证D1到达。可在各自然日后台只读查询实际 current toast，出现真实可用 DTO 时保留原 Host 结果及 named `recipient`、`display_entry`、`actor`，使用现有 app07 `audit-news-toast` 与真实物理 SAVE 和本次来源完成关联。空队列/空 stage/`deliveryfalse` 不是送达。`xfm_news_cursor`、`sent_today`、`delivery_day` 是发送进度，离线 `sourceJoinMatched` 也不是渲染确认；单人只能取得该收件人证据，不能授全人类广播。

观察标记仅包括准备、新同币kind8、14日窗口、21日证书或pending、30日场所退出、原权利来源仍在。它们只写 `xfma_` 和技术观察 story。新闻读取会移除缺失字段的旧读回并标available0；`xfma_delivery_confirmed` 和 `xfma_all_human_delivery_confirmed` 始终0。没有 `clean_retirement`、已送达或全金融通过标记。供给/持币/义务未终结时不能把 state5/6 叫完整归档；新观察器也不调用 archive 或 end_story。

每个 schema2 fixture 的有限被动目录增加 `xfma_delisting_gui_e1_observer`、`e2`，保留原 spot E1/E2/E3、所有旧 profile E1/E2、market-evolution E1/E2 和现有 typed record 类型。当前请求的唯一 active observer 有每日观察回调；其他保留类型只含 `visible=no`，不运行旧日志、付款或业务。新 case 不增加新的 record 类型。实际 SAVE 中若丢失 typed discriminator 且包含引用，现有 numeric-only retired admission 继续拒绝，不修改 FinancialSaveReader、布局推断、strict JSON 或 streaming limits。

本轮软件验收覆盖：新 schema 严格输入与旧债门不变、真实 Java producer 输出的条件树正反例（同币新闻、14/21/30日、价格向下取整与缺价pending、原持币/账户/合约/债来源）、无业务调用与被动E1、真实 emit→共享 Saved inventory→host copy、真实 Shared SaveReader 中 typed 新/旧E1并存及无discriminator引用拒绝。8个新增方法已包含在金融380项中，不另加计；共享23项没有重跑。这些是软件证据，不能替代引擎 parsing、正常GUI公告、实际通知和物理保存对账。原JUnit及wait见外置 `software-delisting01/SOFTWARE.actual.json`。
