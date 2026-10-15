# CK3 1.20.0.4 维护费：财务 getter 与四个原始 context 输入

本轮仅比较已保留的 exact1.20.0.4 / Steam25734779 财务来源与结算代码。
EXE SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。
**没有建立新的 getter→context 生产者边；四字段均不能命名为已支付军事维护费。**
`maintenance_attribution=unclosed`。本轮没有新EXE读取/哈希、编译、游戏、SDK或主树写入。
知识、代码和合成回归规则可移机使用；本机运行状态不能外推。

## 本轮已证来源及其边界

既有 `.4` [binder](../../ck3_autonomous_player/native_bridge/src/ck3_12004_war_cash_claim_terms.cpp)
以精确EXE SHA选择下列地址，复用caller-owned软件ABI和
[current reader](../../ck3_autonomous_player/native_bridge/src/ck3_12003_war_cash_current_reader.cpp)。
旧命名空间的复用不等于使用旧EXE地址；该reader的`.3 BindImage`不是`.4`绑定入口。

| 既有binding | Exact .4 RVA | 当前可证用途 | 对四raw字段的证明 |
| --- | --- | --- | --- |
| monthly_income |2BCA940|输出gross及secondary income|无赋值边|
| expense_context_character |28BFD80|返回传给完整支出的Character上下文|不能等同secondary raw context|
| monthly_total_expenses |2BCB160|完整支出，按原HUD ABI传secondary income、exclude_military=false|无raw字段命名|
| current_maintenance |2C13F60|当前十资源军事月费率|不是已付流水|
| all_raised_maintenance |2C152B0|全部集结情景的替代十资源月费率|不是应与当前率相加的分量|

reader获得gross及完整expenses后做溢出检查的`gross-expenses`，以新语义标记提供NET。
它没有raw读取`Character+1C0`、`context+2C0/2C8/28/30`；typed binding本身也没有
将getter输出写入这些地址。源中未出现这一边，不足以证明引擎其他callee不存在该边。
费用率与已付流水边界参见[当前现金专题](war-cash-current-resources-12003.md)及
[被动付款源链](war-payment-passive-12004.md)。

已保留的574B `.4` settlement函数为`28A6D10..28A6F4E`，完整代码SHA
`f2e377a5e4948042852a95bd5b4e0fe3d38159defb8eb5f823ec0fabb33fe348`。
其实际`mov rax,[rcx+1C0]`证明`context=*(Character+1C0)`，不是inline对象地址。

| 原始项 | 直接来源 | semantic getter name | producer store / refresh / military component |
| --- | --- | --- | --- |
|a: signed64 context+2C0|28A6D32 mov rbx,[rax+2C0]|unknown|null / unknown|
|b: signed64 context+2C8|28A6D39 sub rbx,[rax+2C8]|unknown|null / unknown|
|c: signed64 context+28|28A6D29 mov r8,[rax+28]|unknown|null / unknown|
|d: signed64 context+30|28A6D45 mov rsi,[rax+30]|unknown|null / unknown|

`28A6D4E lea rdi,[r8+rsi]`只算c+d；其后以signed64 wrap形成a-b-(c+d)，
正值路径在28A6D77调用personal ADD285EE40，实际return28A6D7C。
该完整函数没有直接调用表中五个getter，也没有日期条件。它的transitive callee没有全面展开；
因此不能据此断言全引擎无此关联或无周期。详见
[已保存source比较](acceptance/2026-10-15-maintenance-cache-source/SOURCE-RELATION.actual.json)。

旧R0173 seq12实际闭合caller28A6D7C、amount282364与个人账户whole-callback余额变动。
当时未采四输入或OS parent，不把后续a05计划、合成fixture或新观测回填旧记录。
本轮仅闭合“已有字段被该函数读取并参与算式”，连其是否属于带刷新epoch的cache也未证实。

## 拒绝数值命名的反例

- 正ADD可能同时包含多个相反方向的term，符号不能分离其中军事支出。
- 某term或差值恰等于gross、NET或军费率，仍缺producer、单位时间、账户和刷新来源。
- 十资源vector与四scalar的形状不同，既不能单凭形状证明alias，也不能证明无关。
- ExpenseContextCharacter返回Character，不因同名“context”就成为`*(Character+1C0)`。
- 旧1.19/`.3` GUI缓存、symbol名、统一RVA位移及historical GREEN不能命名`.4`字段。
- 稳定指针和两次相同值不是原子事务、刷新完成或日/月结算节奏的证明。

本轮source输入仅7个具名文本leaf，共47,289B；另接收1,108B的具名历史路由metadata回执，
仅证明其列出的四个历史前缀在该机不存在，不是全盘不存在证明，也不增加getter语义来源。
route metadata预览之后追加a02离线方案并冻结原始回执；本轮从未读取任何新EXE字节。
a01/a02离线native_research_plan正常check均通过；
`--for-observation`因offline-only且无真实producer trigger/live window拒绝，原结果保留。
这份研究没有取得现场采样资格。旧getter-map精确路径当前未取得可读原件时保持未知，
不使用旧全EXE扫描型verifier重建getter。下一次仅接收具名、已保留的小source/map，
先追加有限方案，或接收Root的新真实parent packet；具体输入/验边规则在
[NEXT-SOURCE-INTAKE](acceptance/2026-10-15-maintenance-cache-source/NEXT-SOURCE-INTAKE.contract.json)。

## Agent raw 可用性与拒绝规则

`generic_wallet_context_v1` 当前只提供原始 source context、entry 算式复核和有界 OS unwind parent。它不提供已经归因的军事维护费，也不提供调用周期。顶层 journal 和扩展内的 `maintenance_attribution` 必须保持 `unclosed`；`attribution_scope` 必须为 `raw_source_context_and_unwind_parent_only`。以下规则以实际生产 consumer `ck3_autonomous_player/src/xar_autoplayer/bridge/war_payment_observations_v1.py` 为准，重点区分“结构被接受”“观测值可读”“本次 callback 可绑定”与“业务含义已闭环”。

### 字段可用性与快照完整性

扩展是可选字段，仅允许出现在 `kind=2` 的 personal ADD、`caller_return_rva=0x28A6D7C` 记录中；固定 source entry 为 `0x28A6D10`。未编译开启、未选中 kind/caller 或旧记录可以完全没有该键。缺键表示这项观测不可用，不能补成空对象、全零、无费用或“没有该调用”。键存在时必须是字段集合完全匹配的对象；`null`、多余字段、缺少字段、错误版本/source 常量、非严格类型、越界整数或擅改 scope 都由 consumer 拒绝。Python `bool` 不能充当整数，`0/1` 不能充当布尔值。

| 实际状态 | Agent 可以保留的事实 | 不成立的推论 |
| --- | --- | --- |
| 某个 `value_2c0/value_2c8/value_28/value_30` 为 signed64，包括 `0` | 该字段有原始观测值；已观测的零继续保留为零 | 四值都可用、整体快照完整、业务费用为零 |
| 某值为 `null` | 该字段不可用，保留 unknown | 将缺失值补零，或从其他字段反推该值 |
| `context_identity_before` 为 `null/0` | 本次没有可读取的输入 context；四值必须全为 `null` | “读取到了四个零” |
| 输入指针有效，读值后 `context_identity_after` 缺失、为零或变化 | 保留每个已经读到的值，`context_stable=false`、`capture_complete=false` | 擦除已读值，或把输入指针稳定性冒充为已证明 |
| `context_stable=true` | 同一 snapshot 内两次 context 指针都非空、非零、相等 | 四值均已成功读取；before/after 两个 snapshot 之间没有变化 |
| `capture_complete=true` | 本 snapshot 指针稳定、`failed_reads=0` 且四个 signed64 均非空 | 原函数无其他副作用，或该 snapshot 是原子事务快照 |
| `context_values_stable=true` | before/after 都完整、context 身份相同、四个原始值逐项相同 | 两次观察之间没有瞬时变化，或这些字段已经具有维护费语义 |

`generic_wallet_context_v1.before/after` 是 context 快照；`record.before/after` 是既有 character/wrapper 等 frame。两套 `capture_complete` 不可互相代替。context 读完或原函数返回，都不能把 callback 金额的业务原因自动闭合。

### Signed 算式匹配不等于金额归因

仅当 context 的 before snapshot 完整时，consumer 复算：

```text
before_computed_add_raw = wrap_i64(value_2c0 - value_2c8 - (value_28 + value_30))
before_formula_matches_amount = (before_computed_add_raw == record.amount_raw)
```

这里明确采用 signed64 的二补码环绕，不能用无限精度结果、浮点换算、绝对值或正数截断替代。完整 before 算出 `0`，以及 `before_formula_matches_amount=false`，都是合法的已知观测。before 不完整时，computed 和 matches 必须同时为 `null`，不能将 unknown 降为 false。

`matches=true` 只支持“这些 before 原始输入按该 source 算式得到本次带符号 ADD 参数”。`matches=false` 应保留为 source 算式与金额不一致的诊断，不能反向命名为军费、维护费、收入或某一缓存的修正项。after 不完整或变化不会抹掉已经完整的 before 算式；它会限制跨 callback 稳定性结论。即使 matches 与 context_values_stable 都为 true，也尚未证明四个 source 字段的生产者、缓存口径、刷新时点，或它们与整段 callback 余额变化的一一对应关系。`balance_boundary=whole_original_callback_entry_return` 继续表示整段原函数的 entry/return 边界。

四个 term 的合同都仅为 signed64 raw。source 可证它们组合成传给 wallet 的 `amount_raw`；wallet 既有金额 scale 为 100000，不足以把每个 term 独立命名为“金币/月”“当前军费”或任何已知 getter 输出。各 term 的 producer、时间 basis 与缓存角色仍需分别证明，不能从总和的金额单位反推各项已具有相同时间口径。

### OS parent 的已知、未知与 trace 上限

`parent_trace.frames_absolute` 最多 32 个非零 u64 地址。`reported_frame_count` 在 `1..32` 时才可声明 capture 成功，成功时向量长度必须相等；失败时向量为空。provider 报告 `33` 可以作为失败诊断保留，不能越界读取 33 帧或伪造完整 trace。`truncated=true` 精确对应成功且报告 32 帧。少于 32 帧也不证明完整调用栈。

| Trace 证据 | 正确输出与研究用途 |
| --- | --- |
| module base 为零，或 `base+0x28A6D7C` 会溢出 u64 | 不匹配已知 caller；parent 保持 unknown |
| 已知 caller 在帧中缺失、出现多次，或是最后一帧 | 不选择任意一个 parent；`parent_return_absolute/rva=null` |
| 已知 caller 唯一且后面有一帧 | 保留该下一帧为 unwound `parent_return_absolute`，供有限 source 定位；这不是完整栈或静态直接 call edge 的证明 |
| parent 位于已声明 EXE image 范围内，base 非零且 image size 覆盖已知 caller RVA | 才给出 `parent_in_same_image=true` 与 `parent_return_rva=absolute-base` |
| parent 属于其他 image，或不能证明范围 | 保留 raw absolute，`parent_in_same_image=false`、RVA 为 `null`；不能减 EXE base 制造假 RVA，也不能仅凭地址猜模块 |
| capture 失败或达到 32 帧上限 | 保留失败/截断事实；不能由未见某 parent 推断它不存在 |

这些是 OS unwind 的局部原始证据。唯一同 image parent 可以成为下一轮有限反汇编的候选入口；foreign absolute 需要来源机器当时的模块映射和 image 身份后才能继续定位。两者都不能直接赋予费用类型或 date cadence。

### Journal 绑定与 own-account 资格单独检查

`normalize_journal` 接受一条类型正确的 generic raw 记录，不代表该记录已通过业务资格。generic ADD 的 kind 2 不进入 `expected_debits` 的 boarding 候选集合；该函数只对既有 kind 3/4 扣款链复核 qualified vector。合法但不完整、无 parent、TLS 深度超限、当前 session 不匹配或非玩家账户的 raw 诊断可以留在 journal 中，不能被 Agent 自动升级为本次 own-account 付款。

后续若要把真实 raw 记录绑定到一个有限研究窗口，应分别记录并核对以下证据，不能只读原生 `*_matches` 布尔值：

1. **来源与 retention。** journal的steam_build_id须为25734779；journal version/SHA与snapshot hello version/SHA各自绑定CK3_12004。hello没有独立build字段，不能称为对当前Steam安装build的独立读回；实际 `machine_id`、sampling 状态、读回完整性、retention ordinals、overwritten/publication failure 和 natural journal 丢失计数均保留。`read_complete` 是这次 journal 读回状态，不是对所有游戏付款来源的覆盖证明。没有记录、扩展未出现、sampling 关闭或已清理，均不能解释为零维护费。
2. **进程与当前局面。** admitted journal 会直接比对 snapshot 的 pid、connection generation、玩家 full ID、native revision 和 date low32，并要求 current session 的进程创建时间等身份项满足 `same_session(current,current)`。record 的 entry/return/current session 还要按 `same_session` 对 pid、创建时间、generation、玩家与 epoch/window 的实际规则重合；不能将 snapshot 未单独提供的创建时间称为额外独立交叉证明。可用的 source epoch 路径与同进程 no-load window 路径分别保留证据。`session_basis` 字符串不能代替实际重合检查，跨进程、载入或窗口的记录不能拼接成一次付款。
3. **Clock、线程、调用完整性。** 需要有效 clock identity、sequence、thread ID，entry/return 同 clock 同线程且严格有序；original 确实 called/returned、无 TLS depth exceeded，既有 frame 两端 complete 且 failed_reads 都为零。consumer 的 `complete` 检查这组边界；它不等同于 context 快照完整，也不单独证明 own-account。
4. **角色与账户。** 角色指针/full ID/Character magic/extension 的前后身份、玩家 ID、receiver、wrapper、second pointer 及账户关系应从 raw frame 重接。native `same_character_after`、`personal_wrapper_matches_character` 等 flag 不是足够证据。完整 callback、算式匹配或 parent 选中都不能替代“这笔记录确实属于当前玩家指定账户”。目前没有新增 generic kind 2 的 qualified military/maintenance claim。

既有 boarding qualified vector 还要求独立的 transition/gateway/writer/natural-parent 链、精确 caller/source、amount、session/clock 包含关系和整段余额扣减一致；consumer 会重新推导并拒绝不一致的 claimed vector。generic context 不修改这条资格链，也不能把已知 boarding 扣款推广为一般军事维护费。date/snapshot 绑定用于确定观测属于哪一帧，不是按日、月或自然阶段收费的周期证明。

### 下一轮有限 source 研究可用输入

可使用真实、有来源绑定的 context 指针身份、四个原始字段及各自 null/zero 状态、before 算式 match/mismatch、before/after 变化、raw stack 与经过范围证明的 parent RVA，缩小“谁写入这些字段、何时刷新、哪一 source 读取它们”的研究范围。应将有限 caller/site 清单、固定 image SHA、写入/清零/失效路径和各路径反证分开记录；未绑定的 raw 仍可形成待核假设，不能进入当前 own-window 的已证事实集合。parent 未知时仅可继续读取已明确列入有限计划的已保留源码或具名getter来源；不得新增EXE邻域、全image xref或填入猜测parent。

要声明缓存含义，需要对应 producer 的写入和失效合同；要声明 source callback 的 date cadence，需要日期推进/调度/重复调用边界的独立来源或有限实测证据；要声明军事维护费，还需要支付语义、账户与金额链的业务来源闭环。本节的读取完整性、公式一致性或序列时间不能替代其中任一项。

### 旧 seq12 与当前 getter 的不可回填边界

旧 seq12 的实际证据仅闭合其 caller、amount 和 account。四输入的 source 读取及算式路径可以在来源代码层闭合，但当时没有采集四个原始输入，不能把新字段、合成 fixture 或未来采集结果倒填成 seq12 的观测值、formula match、context 稳定性或 parent。a05 将来采集这些字段属于未来工作，不增加旧 seq12 或本轮 source-only 研究的实测信用。

本轮 `SOURCE-RELATION.actual.json` 没有建立新的 producer edge。四个 raw offset 的 `getter_semantic_name`、`producer_store_rva`、`refresh_trigger`、`applied_military_component` 全部保持 `null`；连“这个 secondary context 已被证明为缓存、其刷新 epoch 已知”本身也未闭合。既有暂停态 `monthly_income/monthly_total_expenses/current_maintenance/all_raised_maintenance/expense_context_character` getter 的 ABI 绑定不建立它们与四个 raw term 的赋值关系；`ExpenseContextCharacter` 返回 Character，也不能据名称等同于 secondary context 指针。

`current_maintenance` 与 `all_raised_maintenance` 的 rate 向量是两种情景的替代输出，不是应相加的 paid components，任一输出也不能代替已经支付的军事维护费。十资源向量与四个 raw scalar 的形状差异，既不能单独证明 alias，也不能单独证明完全无关；数值相同、差值相同或正 ADD 的符号都不能完成 producer/cache/paid-component 归因。若后续 Agent 需要估计，只能明确标记为另有合同的估计，不能写回本节 raw 字段或 `maintenance_attribution`。

上述 source 关系来自证据目录 `SOURCE-RELATION.actual.json`，5067 B，SHA-256 `9d8a9dc6c6025dc21ed38705d4e1862c0cb2aa9c3a3958e5c55d5762c86d55ce`；来源机器 `desktop-3fevhd2-1c74096080`，观察时间 2026-10-15 14:53:02 UTC。本节没有读取游戏 EXE、增加 source producer 事实或执行 a05。

### 已有回归证据与机器范围

本节复用已有证据，没有重跑测试或游戏。实际生产 consumer SHA-256 为 `b5b3d65abc26d5b42cacff197294f94d1f9157890f5838e810772f805360eb25`。合同为 `WIRE-CONTRACT.actual.json`（SHA `f902e28a8b2c27ea3bd147a0578b01bb6229261f20681c1a4f7f609e467bcc61`）及指针保值澄清 `WIRE-CONTRACT-ADDENDUM-a02.json`（SHA `a4c73d788ae3669701417a69a56c0e1a23b6a40d59455e1388ee9bfc02f83e0f`），原件历史路径见审阅receipt；跨机器消费请使用已入库的同SHA合同/回归素材，不按历史盘符定位当前运行资源。

| 已有 case / 报告 | 能支持的边界 |
| --- | --- |
| 16 native serializer fixture：`positive/default_off/wrong_caller/wrong_kind`；`failed_value_read/changed_context_pointer/null_context`；`missing_caller_frame/duplicate_caller_frame/foreign_image_parent/stack_failure/stack_provider_count_overflow/parent_unavailable_at_trace_end`；`changed_after_inputs/source_signed_wrap/available_zero_inputs` | 合成 Win64 callback 的 source 读值、ABI/序列化及 null/zero/wrap/parent 边界；其中 parent 帧和 module base 也是合成数据，不能将 fixture 的 `0x28A1234` 当成真实游戏 caller |
| `consumer-full-check-a01.actual.json`：16 native、110 malformed 拒绝、5 unknown 保留、9 legacy 精确兼容；SHA `0a567cab7f59999d02e81bf5bf31ff45fb9199e33aae27857c42cf57ddcb7f39` | 已有实际 consumer 调用，不是游戏运行结果；机器 `desktop-3fevhd2-1c74096080`，2026-10-15 13:43:50 UTC |
| `portable-source-a01/pytest-a01.receipt.actual.json`：140 passed = 9 legacy + 16 native + 110 negative + 5 unknown；SHA `116a1a86b80a3e6060ab501f6bb3186339b72b5c4586c09bbdeff379fee33de9` | 已有标准 production import、显式候选 overlay 的 narrow pytest，Python `-B -O`；机器 `desktop-3fevhd2-1c74096080`，执行区间 2026-10-15 13:58:03–09 UTC；没有 live-game cadence/维护费验收效力 |

新章节审阅机器为 `desktop-3fevhd2-1c74096080`，身份在 2026-10-15 14:49:47 UTC 的本轮只读检查中经 `tools/ck3_live_run_id.py machine` 新鲜读回；来源为实际 consumer、上述合同和既有回执。机器状态与历史验收不得外推到其他 machine_id；可复用的是合同、代码和有明确范围的合成回归结论。
