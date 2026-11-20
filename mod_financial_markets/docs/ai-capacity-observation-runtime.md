# AI capacity 逐日观察协议 1

machine_id: `4-8e1c2f1861`。2026-11-20 已实现本观察协议并通过软件验证；尚未执行对应 CK3 长窗采样、压测或给容量档位通过。

实际离线 Maven verify 第二轮退出 0，用时 142.0217542 秒，474 项金融测试全部通过；另复用源码逐字节未变的 23 项共享解析器原始通过记录，共 497 个不同方法。第一轮 474 项中旧 profile 文件清单断言失败 1 项，已保存原报告，修正为同时允许市场演进与 AI 容量使用日结尾钩子后通过。8 个新增方法涵盖实际生成器及既有 AST VM；它们不证明真实 2048／4096／8192 币容量或游戏日连续性。参见[实际软件证据](../../docs/maintenance/evidence/2026-11-20-financial-markets-capacity-observer.json)。

请求仍是既有严格 schemaVersion=2 的 `ai-capacity`：account/coin 实际永久ID、scaleTier、actor和epoch字段均不变，四个正式marker名称不变。新建观察器明确写 `xfma_capacity_protocol=1`，日记录写 `xfma_record_protocol=1`。已发行旧manifest/源码/收据保持原字节；缺少该协议标志的旧观察器不会由refresh或日hook补初始化、升级、重Arm或补历史日。需要新观察窗口时仍须选择真实未Arm的epoch，不能删旧flag。

`AI_CAPACITY` 与现 `MARKET_EVOLUTION` 都订阅生产金融日结尾已有的 `xfm_finance_daily_observation_on_action`。监听器从实际玩家的本epoch story引用出发并核对owner，不把技术custodian当玩家。两个profile均没有独立days1 timer，并要求exchange.last_date与当前脚本日期相同后才能arm/refresh/观察；市场演进原记录及35日协议保持。其他profile的周期与窗口不变。

基线D0不冒充日样本。每次真实新金融日完成后最多分配一条 `xfma_ai_capacity_day_record`，持久列表为observer.`xfma_capacity_days`，最多395条。窗口日1..30是预热，31..395是365个正式样本。每条都保observer/exchange引用、记录号、实际金融day、当前脚本日期、上一条来源日期/金融day、实际window day及跳过的金融日数。不重写完成记录；重复hook/GUI读取不增加记录；分配失败留失败标志并记录attempt day，同日不重试。缺日只记录实际下一日及gap，绝不回填或把金融day转换成原生日期。

记录读取现有exchange population、委托/仓位数量、AI ordinary/attention工作与决策、队列schema/dirty/repair和daily诊断来源字段。每个字段都有`_available`；缺失时没有value字段，实际0则保available=1/value=0。只读现存计数器，没有新增全市场/全角色遍历，也不声称计数器已由实际业务图逐对象核实。`work_without_decision`仅在两个来源齐全且work>=decisions时保存差额，含义是消费工作但未派发决定，不是拒单/交易失败/成交量。hot books、独立成交者等没有现存源的指标仍需外部真实证据，不造值。

最终395日marker额外要求：395条记录、30warm/365measured、缺样0、必需来源缺失日0、工作计数不一致日0、没有分配失败、真实金融day仍在该窗口终点，以及原有no-gap/395/365/declared-inventory门。后日完整数据不能消除旧缺失。该marker只证明本观察窗口的记录条件，不证明实际人口身份、交易活性、资金守恒、P95/P99或完整产品通过。

没有任何毫秒、CPU或墙钟字段由script生成。真实wall时间、Native/public调用等待、SAVE/cold-load成本、合格hook/UI profiler及内存仍由真实外部运行采集并与source day对应。脚本日期按实际序列化保留；原生raw24日期连续性由既有公开日期边界及外部读档核对，不凭猜测的日期缩放在脚本补造。

读取持久记录时复用现有shared parser/generic raw observation路径，并分批保留完整395条union及缺字段；每批沿原4MiB/record/完整EOF/物理SHA限制。记录不是金融账户/币/订单/仓位，不需要新增金融enum或放宽缺失discriminator策略。本候选没有新parser/Host/Native/业务runner。外部读取若未实现本protocol批次解释，应报告未观察，不能拿旧02标量报告替代。

必要软件验证复用：

```text
mvn -q -f mod_financial_markets/tools/pom.xml -Dtest=FollowupFixtureTest,MarketEvolutionScriptContractTest test
```

新增测试使用同一既有AST VM，执行实际生产finance尾块→实际emitted on_action→emitted observer，分别覆盖395日、前置早到读取、重复回调、缺一天、缺来源一天、0与缺失、异常work、分配失败及技术owner切换。合成测试population只是明确软件输入，不是创建真实2048币的场次；未执行的测试不得标绿。
