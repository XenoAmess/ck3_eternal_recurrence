# 361 三期事故、积弊与共享平台 CK3 运行时

状态：`ck3-static-ready`

实机状态：`not-live-tested`

本包把 Python L0 参考模型中的 X192–204、Y205–216、Z217–228 共 37 条机制投影为实际
Paradox scripted effects 与 character events。它没有接入中央考核结算，因此在统一接线和 MCP-first
实机批次完成前，不得写成 `fixture-live`、`production-live` 或 `complete`。

## 文件与所有权

- 权威生成器：`tools/gen_361_incident_platform_runtime.py`
- 生成 effect：`common/scripted_effects/zg361_incident_platform_runtime_effects.txt`
- 生成 event：`events/zg361_incident_platform_runtime_events.txt`
- 本地化：九个 `localization/*/zg361_incident_platform_l_*.yml`
- 静态契约：`tools/test_zg361_incident_platform_runtime.py`
- Python 参考：`tools/zg361_phase3_incident_platform_model.py`

本包不修改中央 `zg361_effects.txt`、`zg361_events.txt`、interaction、on_action、考核榜 GUI 或共享
case kernel。统一入口由主集成批次接到正式考核链，避免多个并行施工包争写同一中央文件。

## 可接线入口

管理者 scope 可调用：

```text
zg361_ip_open_portfolio_effect
```

它只选择一名直属可考核官员，并在同一人身上打开三份相互独立的 X/Y/Z 案卷。需要显式选择对象时，调用：

```text
zg361_ip_open_x_case_effect = { SUBJECT = scope:subject }
zg361_ip_open_y_case_effect = { SUBJECT = scope:subject }
zg361_ip_open_z_case_effect = { SUBJECT = scope:subject }
```

组合入口另保存管理者的 `zg361_ip_portfolio_cycle`，同一 `zg361_review_serial` 重放只会 no-op；只有下一轮
正式考核序号才能再次自动开包。显式单域入口保留多宗事故/多笔积弊的能力，但每宗仍由独立 case serial 隔离。

入口本身不授予权限。真正开案仍调用共享 `zg361_case_{x,y,z}_open_effect`，因此必须满足：

- 管理者是在世、有地、天朝制公爵及以上领主；
- 对象是在世、有地、该管理者的直属受评官员；
- 伯爵和男爵可以成为 subject，但不能作为管理 ROOT；
- 玩家管理者与获授权的第二 AI 例外走同一资格口径；
- AI 不弹可见事件，只在后台结算；玩家管理者每域只收到一张结案回执。

## 三份真实生命周期

```text
X: on_call -> alerted -> classified -> commanded -> timeline_frozen
   -> reviewed -> actions_open -> resolved

Y: registered -> owned -> funded -> worked -> accepted -> closed

Z: proposed -> adopted -> migrating -> dual_running -> valued -> settled
```

第一阶段在开案后立即执行；后续阶段由 14 个 hidden character event 推进。每次调度顺序固定为：

1. 共享 deadline helper 比较 owner、subject、cycle、case、expected_state；
2. 过期成功后清除 pending ticket；
3. 同阶段的全部编号 operation 写完各自回执；
4. dispatcher 确认该阶段所有编号都有本案完整
   `done_owner + done_subject + done_cycle + done_case + done_state`；
5. 共享 transition helper 只推进一次，再预约下一阶段；
6. 终态冻结结果并只结算一次。

延迟 character event 的 ROOT 是接收事件的受评官员，不再是最初开案的管理者。因而所有后段政策读取、
AI 判断和付费都显式解引用案卷中的 `zg361_case_*_owner`，不能偷用 `root`。这是本包的静态
source-derived 结论，尚待 CK3 实机日志验证；若实机行为不同，应保留失败 artifact 后修正，不能用 OCR 猜状态。

## 每条机制不是政策卡空壳

每个 `zg361_ip_mNNN_apply_effect` 均具备：

- 完整五元 ticket；
- 共享 operation receipt，以及独立 owner/subject/cycle/case/state/choice 回执；
- 同一案同一编号只执行一次的 `done_owner + done_subject + done_cycle + done_case + done_state` 闸门；
- A（证据充分）、B（快速强推）、C（延期并背政策债）三条路线；
- A/B 冻结逐编号唯一业务对象类型、object id、五元身份、consumer contract、资源账标记与适用期限；
- C 不再写 A/B 业务字段或运行其业务消费者，只写五元 policy debt、`due_cycle=current+1` 与负向结果；
- 读取前序对象的 22 项机制必须逐项证明前序 exact object 的类型、consumer contract、owner、subject、cycle、case、state
  均属于本案，并且业务对象与指定 consumer 都已执行；前序走 C、缺失或属于旧轮时，
  本项在 receipt 之前级联为 C，禁止偷读上一轮残留变量；
- `result_score -> domain score_delta -> averaged final_score -> zg361_kpi_value` 的真实消费者；
- 必要时再被后续编号读取，不能只写一枚永远没人看的 flag。

已有机制卡选择优先。未配置时玩家走 A；获授权 AI 在战争中走 C、低 stewardship 时走 B，否则走 A。
这条 AI 路线完全后台执行，不向 AI 打开玩家事件或 GUI。

## X192–204：事故、值守、复盘

- 192–195 冻结轮值深度、英雄负载、值守补偿、等量目标减免、假警报与漏报风险；
- 196 独立冻结申报等级与校正等级，保存 integrity gap；
- 197 的指挥/救火分功恒为 100%，198 从救火毛功中一次扣除根因过失；
- 199 保存有限观察期的预防功；200 保存限时限范围授权与命令日志；
- 201 冻结时间线节点，202 的 owner/期限消费者显式引用它；
- 203 累计同类复发并把行动项事实送到管理责任账；
- 204 读取冻结严重度，结算可靠性预算并产生停止上线 gate。

终态把 13 条结果平均为 `zg361_ip_x_final_score`，只影响下一轮 KPI，不回写已冻结的旧考核档位。

X 的执行顺序是语义顺序而非编号排序：先冻结 #201 时间线，再由 #197 读取该版本完成指挥/救火分功，随后
#198 才做根因净额。这个顺序由 Python 模型的 `DOMAIN_EXECUTION_ORDER` 单点定义并被 CK3 生成器直接读取。

## Y205–216：积弊、维护、交接

- 205 的 toil 与 delivery 工时每条路线恒等于 100；
- 206 记录本金、利息与原始 owner 可见性，207 固定债务/业务容量也恒等于 100；
- 208 读取积弊余额与冻结预算后形成修补/重做/延期路线及还款后余额；
- 209 结算危险津贴或明确薪酬债；210–211 把 owner 轮换与非作者手册验收接成闭环；
- 212 用实际节省工时给自动化延迟计功；213–214 把拦错、审阅耗时、阻塞、覆盖率与关键漏测分开；
- 215 只有通过质量/必要性 gate 才释放旧务和 HC；216 保存四类交接或有责任人的 waiver。

## Z217–228：共享平台、迁移、内部开源

- 217 保存底线采用、强推或有审批例外；218 冻结客户分和战略底座分，任一不达线都不能冒充双高；
- 219 同时记录采用数、使用深度、确认节省和迁移负担；
- 220 展示成本并执行真实结算，后续 221 明确平台/使用方/改革预算三方份额且恒为 100%；
- 222 保存双跑工时、旧路退出日与是否真正关闭；
- 223 的重复扫描回执是 224 合并赛的前置消费者，225 再保存上游优先、合法差异与 fork 预算；
- 226 的贡献者/维护者功劳恒为 100%，227 的创始/扩展/维护分账也恒为 100%；
- 228 的平台根因、用户违规、强推决策责任恒为 100%，总损失只分配一次，并保存本地降级权。

## 金币与容量守恒

发生实际费用时遵循“国库 + 管理者个人金币”双付款：

- 193 值守补偿：地方国库 6 + 管理者个人金币 4 = 受评者到账 10；
- 209 危险津贴：地方国库 6 + 管理者个人金币 4 = 受评者到账 10；
- 220 平台费用：A 为 12 + 8 = 20，B 为 18 + 2 = 20，C 不扣款但留下成本债。

每次先在同一 limit 中验证政府国库能力、国库余额与个人金币，再同时执行两笔 debit；任一不足都不发生
部分扣款，而是写入明确债务并降低本域结果。193/209 的付款额与收款额相等。平台费是共享服务成本，
进入 showback/paid/debt 三态账，不伪装成对个人的奖励。

此外，205/207 的容量拆分、197/221/226/227/228 的功劳或责任份额均由静态契约逐路断言守恒。

## 本地化边界

简体中文和英文为本轮原创。法、德、日、韩、波、俄、西七种文件当前只放英文结构占位，保证日常开发可加载；
这不构成发布翻译。只有正式发版指令后才进入七语发布审计。

## 当前验证与下一步

本包可执行：

```powershell
py tools/gen_361_incident_platform_runtime.py --check
py -m unittest -v tools/test_zg361_incident_platform_runtime.py
```

静态测试覆盖 exact 37 ID、A/B/C、逐项 exact object/consumer/resource/deadline、C 无业务对象、完整五元 done/operation/object 身份、阶段唯一推进、14 个 deadline、三张玩家结案事件、
写到 KPI 的消费者、双付款原子预检、容量/份额守恒、九语 key 集以及“零新增 GUI/decision/interaction/on_action”。

仍需由统一批次完成：

1. 把 `zg361_ip_open_portfolio_effect` 接到正式考核结算后的下一轮事实链；
2. 用 CK3 parser/error.log 排除 Paradox 语法和 scope 误判；
3. 通过 MCP 查询 owner/subject/cycle/case/state、每编号 receipt、金币/国库、终态 KPI revision；
4. 在一次启动中覆盖 X/Y/Z 正常、stale、重复调用、资金不足、玩家/AI、伯爵/男爵 subject；
5. 保存 paused artifact 后才升级 readiness。

此外，C 路当前会产生可见且带 `due_cycle` 的 policy debt，但本包尚无统一的到期偿债/升级 consumer；在该 consumer
及其跨存档实机证据出现前，不能把“已登记债务”写成债务闭环。

OCR 只可在 native/MCP 状态已经闭合后截取最终画面，不可承担导航、状态真值或 GREEN 判定。
