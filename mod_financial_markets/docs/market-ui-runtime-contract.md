# 市场界面运行合同

本文件记录生产界面及其调用边界。当前内容是源码与离线结构验证，尚不能代替 CK3 后台点击、状态变更、存档与重载验收。

## Alpha.2 布局修复（2026-11-24）

Alpha.1 玩家截图显示内容下移、市场区不可点击及详情视口过小。原版 `Window_Margins` 只设边距（`game/gui/shared/windows.gui:127`），`scrollbox` 默认是 100×100（`shared/lists.gui:3255`）；原窗口的多层百分比高度没有明确的有限父区域，且两栏总宽超出扣除边距后的宽度。它们是本次修复的源码依据；没有将推断写成已完成的引擎鼠标因果实验。

Alpha.2 改用明确的位置和尺寸：主窗 1320×920，内容区 1272×766，左侧 790×766，右侧 460×766，详情滚动视口 460×728。市场页 790×592 内，筛选、编号搜索、396 高的列表和底部翻页均有独立区域，列表不会覆盖翻页；资金与指数入口位于其上。长页单独滚动，隐藏内容使用原版有据的 `ignoreinvisible`，没有新增未知对齐属性或父容器透传。

交易表单位于盘口之前，摘要保留完整说明 tooltip；币号与账户号去掉会触发文本格式解析的前置 `#`。三份改动 GUI 的 129 个 `enabled`／`onclick` 表达式与 Alpha.1 完全一致，金融后端和存档字段没有改动。新增几何回归检查区域包含、相交及最低可用视口；OTC 原有快照检查改为按控件身份比较完整按钮，允许排版顺序变化且保留回调约束。

`machine_id: 4-8e1c2f1861` 于 2026-11-23T16:43:12Z 完成默认 Maven 3.10.0 的一次全模块 `verify`：57 个 suite、716 项、0 失败／错误／跳过，312.094 秒，运行内容与测试源码前后相同。先前测试辅助正则未处理按钮嵌套 size 的一次失败保留；修正后 6 项局部检查及完整验证通过。既有 `tools/target` 和依赖缓存复用，非整仓 Java reactor。此为软件和源码几何资格；现有 Native 查询不返回矩形／裁切范围，直接回调不能证明物理鼠标命中或最终视觉，故本次未新启 Game 冒充这些实测。

## 入口与控件

`gui/scripted_widgets/xfm_market_widgets.txt` 注册两个真实窗口：

| 根窗口 | 用途 | 稳定控件 |
| --- | --- | --- |
| `xfm_market_entry` | 正常玩家可发现的常显入口 | `xfm_market_open`，执行 `xfm_market_open_gui` |
| `xfm_market_window` | 主市场 | `xfm_tab_market/positions/orders/debts/issuer/news` |

决议 `xfm_market_open_decision` 同样调用生产 `xfm_market_ui_open_effect`。在世儿童与成年玩家均可只读打开。两条入口均先由公共金融层建立真实零余额账户，再开放窗口，不赠送钱、币或测试资产。资金变更、发行、杠杆等入口与确认选项同时要求成年；后台仍独立核验实际权限。游戏内窗口不调用操作系统前台或置顶接口。

操作按钮的 `name` 为对应 scripted GUI 去掉 `_gui`，例如 `xfm_market_deposit`、`xfm_market_issue_micro`、`xfm_market_buy`、`xfm_market_futures_long`。动态行使用 `xfm_market_coin_row` 等稳定名称，同名行须以实际 `child_path` 和行绑定的 story 区分，不能只按第几个按钮盲点。

## 数据与边界

- 角色根始终是 `GetPlayer.MakeScope`。选择行将实际 story 作为 `xfm_ui_item` 传入，所有金融操作仍由各自公共 effect 重新核验。
- 角色 `xfm_accounts` 中的账户可单独选择，`xfm_active_account` 是界面显示及普通现货、期货、存取款的账户。继承账户保持原 ID、仓位与债务。OTC 明确使用报价双方的主账户，与遗产账户选择区分。
- 金额显示为整数分除以 100 的金币；一手为 100 枚币。现货与期货票据最多 10,000 手，限价最多 1,000,000 分／手，步进达到上限时截断而不产生越界草稿。界面不自行扣款、成交、增发、免债或清算。
- 全币分页来源是 `xfm_coin_registry`，显式打开、刷新、翻页时排序并投影至角色的 `xfm_ui_coin_page`；每页 16 项。支持永久编号定位、发行主体类型、持仓筛选、编号／价格／成交量排序。右键任意角色的“查看发行和控制的币”通过真实角色作用域限定最初发行者／当前控制者，之后仍可分页和叠加筛选；清除筛选恢复全市场。没有随机选择一项持仓充当完整列表。
- 持仓、未成交委托、委托历史、债务及债权使用原生 `DataModelSubSpan` 分页，每个数据区最多 16 项。原生签名可追溯到 `game/gui/activity_window_widgets/imperial_examination_scoreboard_widget.gui:102` 与 `:151`。
- 盘口从币自己的 `xfm_spot_orders` 明确取买卖各五笔，按限价排序，展示订单编号与剩余手数。它是前五笔委托，**不是聚合五档**；真正价时优先由现货引擎执行。
- 新闻按永久 `xfm_news_id` 游标倒序，每页 16 条，可向旧报道翻页；最新按钮重新捕获锚点。不是丢弃旧消息的“最新 64 条”。当前生产者成功记录才递增 ID，且保留所有报道，因此向较新页加 16 的连续 ID 合同成立；若未来允许删新闻，应同步改为显式游标栈。
- 现货详情区区分最新成交、参考指数、结算标记与可成交报价。30 日 OHLC 和实际成交量读取共同现货层的固定槽；没有用随机曲线或宣传倍率伪造价格。
- 粮食／军需／商贸观察指数使用独立 `xfm_oracle_index` story，不伪造币供应或现货盘口。三个选择入口只开放期货票据，披露“模组观察指数、非原版浮动粮价、无实物兑付”。

## 功能调用

| 界面操作 | 公共调用／参数 |
| --- | --- |
| 存取金币 | `xfm_finance_deposit_effect` / `withdraw_effect`；`xfm_request_cents` |
| 现货买卖 | `xfm_spot_submit_effect`；selected coin、side、lots、limit cents、IOC/GTC |
| 撤委托 | `xfm_spot_cancel_effect` 或 `xfm_futures_cancel_effect`；实际订单 story |
| 筹备发行 | 确认实际主体、档位、募资目标与主账户；币名按绑定实体及永久编号显示；类型 1–7，微型目标 20–50 金、标准 200–10000 金 |
| 认购／完成／撤筹 | `xfm_issuer_subscribe/complete_offer/abort_offer_effect` |
| 宣传／章程／操盘 | 公共 issuer effect；增发与撤流动性有确认，控筹与项目金库出货使用真实限价单 |
| 恢复／退出处理 | 恢复真实做市资本、30 日重新上市观察、无外部持有人与索偿时清理失败发行的未分配库存；均调用公共生命周期 effect |
| 30 日退市 | 控制者确认后将币交给 `xfm_listing_announce_effect`，界面不删除资产 |
| 期货 | 确保实际合约，提交多／空、杠杆、手数、限价；契约与所选标的严格匹配 |
| 仓位管理 | 按选中账户确定多／空一侧；载入该侧现有止盈止损；补提保证金、减仓与设置止损调用公共 effect |
| 偿债／援助／重整 | 明确确认后真实付款，或由真实债权人同意减记与展期；拒债不消账 |
| 风险基金 | 当前账户可用资金的自愿、不可退回捐赠；不自动补扣角色金币，无收益权 |

微型 20 金募资预览的总支出／冻结为 6 金；标准 200 金为 55 金。登记费、上市费、预存维护、履约金与做市资本分别披露。预览只用于显示，公共发行层独立重算实际扣款。

## 确认窗口的对象与权限

每个确认事件在 `immediate` 保存独立的作用域与数值，不继续引用后来改变的面板选择。币相关确认固定币、手数、限价及 IOC；隐瞒增发按供应 10% 的公共公式保存实际枚数，供应或章程上限改变时拒绝旧确认；债务固定债务 ID 与付款额；捐赠固定金额；付款与控筹固定当时合法活动账户。发行固定主体类型、档位、募资目标、主账户及涉及的家族／宗族／头衔／信仰，确认时主体变更则拒绝。

接受时重新检查在世成年、账户 holder、非系统／非冻结及公共业务资格。退市的 coin-scope API 前另用 `xfm_issuer_controls_selected_trigger` 核当前实际控制权，不能仅相信旧 controller 字段。更换所选币、账户、数量或另开确认窗口不能让旧窗口按新参数执行；归属、余额、供应上限及状态变化仍由公共模块拒绝。取消不扣款。

## OTC 双方同意

右键买家选择 `xfm_market_otc_offer_interaction`，标准确认窗口只表示发送提案，不能视为买家付款。真正成交在买家收到的 `xfm_market.120` 事件中再次确认。事件保存卖家、买家、双方主账户、币、数量、单价、nonce、到期日及价格版本；接受时逐项重验，并调用公共原子交割。

卖家改变或撤回报价、过期、账户归属变化、价格版本变化、金币不足或币被其他委托冻结时，旧事件均不能按新条件成交。拒绝仅撤回对应 nonce，不撤销之后另发的报价。AI 收到同一提案时也须符合资金与价格条件，不自动创造购买力。

## 原版依据与待闭合项

已直接读取 CK3 1.21 安装文件：

- `game/gui/event_window_widgets/event_window_widget_enter_text.gui:7–18`：真实文本输入控件。
- `game/events/test_events/debug.txt:2082–2095`、`game/events/accolade_events.txt:172`：text controller、key 与 `text_target`。
- `game/common/scripted_effects/gdp_merchant_scripted_effects.txt:3207–3221`：`ordered_in_global_list`、`order_by`、`max`、`check_range_bounds`。
- `game/common/script_values/_script_values.info:29–30`：`min` 是下限，`max` 是上限；发行预览据此计算。
- 仓内已用的 `mod_religious_ritual_fusion/gui/rrf_fusion_window.gui`：`Scope.GetList` datamodel 与 `GetScriptedGui` 传真实 scope。

**未将未证明的 `Story.GetLocalizedText` / `Scope.GetLocalizedText` 塞入整个窗口。** 当前列表和详情按实际 `xfm_bound_entity` 生成有含义的名称：个人币、家族币、宗族币、王权币、圣约币、商社凭证、愿景币，附永久 ID 区分同名项目；家族／宗族／政权／信仰名称来自实际绑定实体，不随控制者改选伪造。通过已用的 `Localize(Concatenate(...))` 只选择当前类型的显示模板，再调用原版 typed scope getter；未使用 Story 字符串 getter。原生依据包括 `game/localization/english/core_l_english.yml:550/554/555` 的 Faith/Dynasty/House.GetName、`board_game_events_l_english.yml:81` 的 `MakeScope.Var(...).Title.GetNameNoTier`、`factions_l_english.yml:187` 的 `Var(...).Faith`。

本轮不开放任意手填币名，发行窗口只确认实际主体和资金条件。原版文本输入控件仅证明 Character 写入，未证明 Story 的对应读取；宠物故事使用 `Story.GetOwner.GetLocalizedText`，不能将共享技术托管者当作每个币的名字储存。进一步核实 `ep2_locale_events.txt:7867–7875` 及 `10_dlc_tgp_japan_scripted_effects.txt:33–36`：`GetFlagName` 只消费预设 flag，任意输入另走 Character.GetLocalizedText，不能替代 Story 文字 getter。已移除无显示消费的输入 widget 与发行层孤立 copy，避免让玩家输入永远不会展示的名字。名字子串搜索也未宣称可用；编号与分类筛选保持真实，不每帧创建 4096 个隐藏行。

后续实机必须通过公共 acceptance 入口验证：常显入口→真实点击→独立读回窗口可见；全球第 17 个币分页可达；选取真实行后下单、撤单与账户读回一致；继承账户、双边继承仓位的方向准确；儿童只读且不能触发资金变更；旧确认窗口在改选币／账户／数量后仍仅处理快照对象，权限转移时拒绝；旧 OTC 事件拒绝；中英文、存档重载及无错误日志。静态括号、BOM、引用及本地化通过不授予这些业务 PASS。
