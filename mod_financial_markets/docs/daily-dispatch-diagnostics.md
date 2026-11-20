# 每日金融调度诊断

R0030 实际保存了35个自然日，但金融日只增加34。新增诊断用于定位后继真实回调，不改变计时器、原日期守卫、业务处理顺序或观察尾钩子，也不补算已遗漏的历史日期。

首次有效交易所回调才初始化字段。定义加载、冷读、GUI打开与其他角色作用域不初始化它们。所有新增字段都在交易所上，以 `xfm_daily_` 开头。

| 字段 | 含义 |
| --- | --- |
| `attempt_count` | 有效交易所回调总次数，上限10亿 |
| `attempt_script_date` | 最近一次回调看到的脚本日期；不是Native raw日期 |
| `attempts_on_date` | 最近同一脚本日期的回调次数，上限1024；换日重置 |
| `attempt_prev_date_present` / `attempt_prev_date` | 进入原守卫前的 `xfm_last_date` 是否存在及其实际值 |
| `attempt_entered_dispatch` | 最近回调是否通过原守卫；不证明后续所有业务完成 |
| `rejected_count` | 回调存在但未进入原守卫的累计次数，上限10亿 |
| `last_rejected_date` / `last_rejected_prev_date_present` / `last_rejected_prev_date` | 最近一次拒绝的日期及原前置日期；成功后仍保留 |

表中字段省略了共同的 `xfm_daily_` 前缀。三个计数字段分别有 `_saturated` 标记：达到上限时仍为精确计数，下一次无法增加时标记为1，此后只能视作下界。同日计数及其标记在日期改变时重置；累计计数不会重置。

未饱和端点之间，回调次数增量减去拒绝次数增量，表示观察到的守卫进入次数。没有回调时诊断不会变化；缺失前置日期保留为缺失，不补成零。结合独立存档中的金融日与日期，可区分“未观察到回调”和“回调被守卫拒绝”，但端点不能独自证明引擎内部调度阶段。

软件测试执行真实诊断helper AST、原守卫及进入标记，并验证非诊断状态不变、作用域隔离、缺失日期、重复日期与饱和语义；业务effects没有在该测试子集中执行。源码与软件通过不代表R0030失败已修复，下一场仍需实际保存与独立读回。

以上字段衡量有效交易所helper入口；新增 raw 字段的测量位置更早。R0031 的14个自然日只观察到13次有效交易所回调、零次守卫拒绝，金融日由56增至69。该失败保留。闭场后增加的 raw probe 位于原 runtime effect 最前端，在切换作用域前保存实际调用者和引擎提供的 `scope:story`，再向类型为 `xfm_finance_exchange` 的全局交易所记录 `xfm_daily_raw_*`。它只清理两个专用临时别名，不使用 `prev`，也不替换原日业务调用的作用域、计时器或执行顺序。

raw 记录区分引用缺失、引用存在及其是否等于规范交易所；缺失引用移除，不写成ID零。最近一次不匹配的日期与实际引用持续保留，后续正确回调不会覆盖它。raw 与不匹配累计次数均在10亿饱和，下一次无法计数才置 `_saturated`，同日重复入口也计数。字段仍在首次实际可记录回调时惰性初始化。如果全局交易所缺失或类型错误，probe没有合法持久写入目的地，不能留下该次记录；probe之前未能执行的路径也不在测量范围。缺字段不能当作零次调用。

`machine_id: 4-8e1c2f1861`：2026-11-19 19:23:50—19:24:23 UTC，原操作 `MVN-financial-raw-entry-class01` 实际退出0，墙钟33.307秒，`MarketEvolutionScriptContractTest` 25项全部通过，失败、错误、跳过均为零。新增测试执行生产 raw helper AST，核对实际调用者与Story引用、持久不匹配、缺失全局、饱和、专用别名清理和金融状态零改写。这证明软件诊断语义，不证明引擎已按日调度或整包实机通过。

下一次真实14日窗口继续最新持久存档，分别保存基线和正常D14里程碑，比较未饱和的 raw、有效回调、拒绝计数与金融日增量，并核对持久不匹配的日期及引用。首次基线缺字段时，须保留“尚未初始化”事实，待真实入口初始化后解释累计值。raw 多于有效回调可缩小到作用域或进入有效helper前的路径；两者同样偏少仍不能排除全局缺失、probe前失败或其他未测路径，不能直接断言引擎没有调度。保持原失败及日期证据，不回放漏日，不回填观察值，也不据软件通过签署连续采样通过。

## raw 日期间隔诊断

新增字段只在真实 raw 入口已有的规范交易所记录中写入，不在读档或开大厅时初始化。它们不改 timer、`xfm_day`、`xfm_last_date`、原守卫或业务顺序，也不补算历史日。旧档已有 `raw_script_date` 时，从该真实前值继续；前值缺失时保留缺失，不能据此判断旧缺口。

下表字段均以 `xfm_daily_raw_` 开头：

| 字段后缀 | 含义 |
| --- | --- |
| `prev_script_date_present` / `prev_script_date` | 本次覆盖 `raw_script_date` 前，是否存在上一次记录日期及其真实值 |
| `script_date_delta` | 当前脚本日期减上次脚本日期；同日为0，逆向值保留符号；无前值时移除 |
| `first_gap_prev_date` / `first_gap_date` | 首次观察到日期差大于1的两端；首次写入后不覆盖 |
| `first_gap_missing_dates` | 两端之间未记录的脚本日序号数，即日期差减1 |
| `first_gap_attempt_count` | 当时已有 raw 累计计数，包含本次入口；计数达10亿后仅作下界，不宣称精确总序号 |

这是一组固定数量字段，不增长日期列表。`first_gap_date` 的存在表示首缺口记录已写入；不存在表示尚无可记录的前向缺口，不能填0。记录的是两次可持久化 raw 入口之间的日期空缺，不等同于证明引擎没调度，也不自动证明资金结算缺失。全局交易所不存在、类型错误或在 probe 计数前失败时，仍无合法持久写入目标。

日期差使用 CK3 脚本日序数，不用 Native `date_raw` 的24 ticks/日。`machine_id: 4-8e1c2f1861` 的1.21安装原件 `common/script_values/10_health_values.txt:817–829` 以 `current_date - historical_pregnancy_start` 后除30计算月份；`10_tgp_dynastic_cycle_values.txt:106–119` 以18250/36500日表示50/100年。新增软件用例显式提供389430等脚本日序数，保留旧VM默认输入行为；软件测试不授真实引擎定时或新存档资格。

### 独立连续十四日调度对照（方案与最初软件验证）

`financial-markets/clock-cadence-continuous14` 是独立诊断。已签来源合同仍为 `product_acceptance`，另将 `clock_purpose=continuous14_diagnostic` 精确绑定这个新case；旧 `CaseClient.advance_day`、Host `advance`、ProductClock `deadline` 继续只接受一天。它不替换生产timer，不补旧日，不给R33或此前缺口改判。

Q26的 `ReadFullSnapshotV1` 明确要求暂停，因此**运行中不请求Full**。旧candidate01以人造running Full做软件输入，不能证明真实通道可用，不采用。真实可复用的是DateSentinel Status：`bridge.cpp` 的Florin早分派直接读取原生哨兵slot；`ReadDateSentinelStatusV1` 等待完整Post锁后读同generation。它包含原ARM的start/target、实际last_observed_date_raw、completed_daily_ticks、speed/mode及暂停/失败标志。SDK查询前读取的semantic Snapshot只是已有缓存，不发新Native Full；这个旧缓存绝不记作当前运行世界。

实验从同局最新物理SAVE冷载，保存并独立读一次基线；以真实暂停fresh Full绑定玩家/世界/日期，单次ARM目标为当前 `+336`，单次resume，speed1。最多240秒、480轮轮询，每轮只读 `capabilities → DateSentinel Status → capabilities`。两端实时diagnostics必须仍是原pipe/PID/连接generation/精确HELLO，Status再绑定原ARM generation/start/target/speed/mode。仅收录实际第1至14个连续状态；重复slot读不增样本，n→n+2表示漏采样，诊断失败且不插值。它不能据此断言Native漏callback，更不能断言金融漏结算。

仅在Status实际观察到原第14 tick及deadline暂停后，才请求新的相关暂停Full，核实际终点 `+336`、同玩家/世界/进程/连接与speed1。中间没有新Full、角色/资源快照或金融日字段；也不声称观察过所有事件。途中原生提前暂停、异常、连接变化、时间或取样预算用尽、ACK不明，均保留 `INCOMPLETE_NEVER_REPLAY`，由公共入口原finally安全正常关场；不选择事件、不重发ARM/resume、不将分段运行拼成连续窗口。终点Full里实际存在的事件/通知仍如实保留。

成功路径只要求两个新物理SAVE：基线和终点，各自归档、审计并读取同一个exchange的完整原生AST。比较真实Native日期跨度、`xfm_day/xfm_last_date`、raw/helper计数、raw前值/first-gap以及原始 `dates`；缺字段仍记缺失。金融逐日只保留现有真实日志，缺日志时明确无覆盖，不从14个Native Status生成14个金融收盘。先读终点再作任何其他动作，禁止为了对齐数字先refresh、重ARM observer、改日期或补日。失败时没有合法终点便不强行制造第二份SAVE。

载体只声明现有有限被动XFMA类型：演进E1–E5、现货E1–E3、其余已支持E1/E2及原day/coin记录，全部无callback，不ARM新observer。实际续源若含目录外类型，必须先解决真实兼容性，不能丢弃旧记录。

结果恒为 `financial_daily_coverage_verified=false`、`business_pass=false`、`performance_pass=false`、`product_release_pass=false`。完成只证明这次连续Native窗口和取样合同；金融增量可以仍不足14。与先前逐日立即暂停窗口的差异仅提供暂停关联诊断，不单凭一次不同世界时段的对照判定根因。本候选不改SDK、C++或Native读取权限；Host Python改动是否涉及原编译输入或same-root delta资格，仍须按真实来源闭包核定。

Status 查询不是 lock-free 或零调度扰动观察：现有 Native reader 持有 `worker_lifetime_lock` 独占锁，原 Final 返回后的 Post 获取同锁共享；两者可能短暂互相等待。锁内只读已有 slot 和失败标记，无 pause、脚本或结算调用，但不能排除 worker 等待、主线程间接等待及共享机器负载对调度的扰动。对照结果只能提供有限关联证据，不授金融逐日、业务或性能信用。

有限被动目录另保留已采用 AI 观察器的 `xfma_ai_capacity_day_record`，只发射 `visible = no`，不带 AI on_action、ARM、effect 或新 epoch。它同步真实 emitter 的历史记录类型；R35 当前没有该记录，因此这不是已发生的冷载故障证明。未知 XFMA 类型仍不接受。

2026-11-20，machine_id `4-8e1c2f1861`：连续诊断新增15项软件测试实际退出0（4.3447373秒），既有产品用途14项回归退出0（13.3590758秒），严格类型检查退出0（1.7024064秒）。首次类型调用因 MYPYPATH 未包含项目 SDK 源目录而报两项未类型化导入；保留原失败，显式指向该实际源目录后通过，没有忽略错误或放宽类型规则。尚未执行本诊断实机，R33的14／13缺口仍未修复。详见[本次软件证据](../../docs/maintenance/evidence/2026-11-20-financial-markets-continuous14-software.json)。

### R0037：连续窗口端点实际均增加十四

2026-11-20，`4-8e1c2f1861` 使用 1.21.0／Steam26622941，从最近的 R35 物理存档恢复同一角色31254。R36在启动合同比较处失败且没有新存档，故未回滚已保存进度。R0037 的两个新物理存档独立归档并读回；起点4137条完整金融／新闻记录、十个全局状态及三个角色新闻游标与续源完全相等。

单次 ARM、单次 resume、speed1 连续推进14日，中间没有 Full、交易GUI、保存或暂停，14份 Status 均绑定同一PID／连接／generation。Native raw 日期53146656→53146992；原生交易所52的存档AST显示金融日94→108、raw入口13→27、有效helper入口38→52、脚本日期389444→389458。首缺口字段及尚未采用的ROOT入口字段仍缺失，不填零。终点共8608条完整记录，原记录无缺失，新增4471条，改变114条。

原终点比较工具因完整输出超过4MiB实际退出1，该失败保留。单独修复元数据输出上限至8MiB后，读取同一批已完成JSON得到5,254,855字节差异报告；输入仍限4MiB，没有重做SAVE、推进或原pipeline。正常Quit后 Game、Host和keeper均实际退出0，公共run／verify均退出0，租约15658→15659释放。

这证明本连续窗口端点三项计数均增加14，不证明逐日金融收盘覆盖、全部业务通过或性能达标，也不改判R33。源码只证明普通单日模式在每个目标Final后的Post调用pause，尚无Story队列完成栅栏；连续窗口还同时减少了中间Full／保存／ARM生命周期，不能把一次对照直接归因为暂停。详见[本次实机证据](../../docs/maintenance/evidence/2026-11-20-financial-markets-r0037-continuous14.json)。


### R0041：第十三日缺少可记录 raw 入口

2026-11-20，`machine_id: 4-8e1c2f1861`，同一1.21.0／26622941世界的连续窗口再次出现差异：Native日期53146992→53147328，14份Status均为原generation的连续1至14；独立存档原始AST中的金融日108→121、raw入口27→40、有效helper入口52→65，而`xfm_last_date`和raw脚本日期389458→389472。两端`xfm_daily_rejected_count`均有真实`type = value`变量块且省略identity，按该保存格式是显式零，不是缺字段补零。

基线没有first-gap；终点第一次记录的两端为389470→389472，missing_dates为1，gap_attempt_count为40，恰等于终点raw总数。因此缺少可记录raw入口的是本窗口D13（脚本日389471，对应已观察的Native raw53147304），首次间隔诊断在D14写入；不是已证实的冷载首日跳过。两端均没有ROOT入口probe，不能补成零或声称已经观察了真正引擎根入口。

生产raw计数在helper日期守卫之前执行，同日实际入口也递增；仅由`xfm_last_date < current_date`拒绝，不能解释raw也只增加13。但规范交易所不存在、类型错误或在持久记录前失败仍无法留痕，所以目前不能区分Story未调度、probe前失败或目的地暂不可用。没有逐日金融记录，也没有Story调度完成栅栏；本次金融逐日覆盖、业务及性能仍未通过，R0037的14／14只保留为另一个实际窗口。

本机安装的`_story_cycles.info:121`将`days`定义为两次attempt的间隔，124–126行明确省略chance时总是尝试触发；现有`days = 1`、`always = yes`没有可据此修成`chance = 100`的依据。对安装`common/on_action`的193份文本、2,049,584字节作有限具名daily／weekly入口查找，命中为零；文档列出的代码脉冲为年度／季度等，不能假设已有合法`on_daily`。文档确实支持脚本`trigger_event = { on_action = ... days = ... }`，但其排队有效性和作用域仍须另证，不等同于每日完成保证。本次只保存小型来源与扫描范围，不将安装目录整份脚本复制入仓库。

后继修复应执行真实金融链并保留未处理日期及实际输入来源；不得仅把金融计数补到14、复制历史价格／AI世界状态或回填本窗口验收。详见[本次端点与源码证据](../../docs/maintenance/evidence/2026-11-20-financial-markets-r0041-daily-gap.json)。
