# 361 三期事故、积弊与共享平台 CK3 运行时

状态：全包 `static-ready`；Incident/X 子闭包 `startup/full-entry production-candidate GREEN`

实机状态：exact Incident/X production closure 已完成入口层实机；delayed-path/业务语义仍未实测

本包把 Python L0 参考模型中的 X192–204、Y205–216、Z217–228 共 37 条机制投影为实际
Paradox scripted effects 与 character events。中央 phase-two stages 4–6 已逐域接入 X/Y/Z，并能把
“确有事故”和“本轮无事故，N/A”分开收口；下一轮组织证据的只读输入也已接入权威八分项 KPI。
共享考核 effect 中的一次性消费调用已经合并。2026-09-04 的 exact Incident/X production closure 已通过
CK3 full-entry，但该轮没有触发 X 案卷或验证 delayed event，因此仍不得把本包写成 `fixture-live`、
`production-live` 或 `complete`。

## 文件与所有权

- 权威生成器：`tools/gen_361_incident_platform_runtime.py`
- 生成 effect：27 个按 capture/probe/KPI、X/Y/Z apply/debt/dispatch/deadline/lifecycle 与 portfolio 用途分组的
  `common/scripted_effects/zg361_incident_platform_*_effects.txt`
- 生成 script value：`common/script_values/zg361_incident_platform_runtime_values.txt`
- 生成 event：12 个按 X/Y/Z deadline/result/debt 用途分组的 `events/zg361_incident_platform_*_events.txt`
- 本地化：九个 `localization/*/zg361_incident_platform_l_*.yml`
- 静态契约：`tools/test_zg361_incident_platform_runtime.py`
- Python 参考：`tools/zg361_phase3_incident_platform_model.py`

本包不修改共享 `zg361_effects.txt`、`zg361_events.txt`、interaction、on_action、考核榜 GUI 或共享
case kernel。旧 `zg361_incident_platform_runtime_effects.txt` 与
`zg361_incident_platform_runtime_events.txt` 已从产品树移除，generator `--check` 会拒绝其回流。中央 stages 4–6
的适配器由 `gen_361_phase2_central_runtime.py` 生成；共享 KPI 冻结点只保留一行明确调用，避免多个并行施工包争写同一中央文件。

## 真实适用性：没有事故就是 N/A

`zg361_ip_capture_real_incident_effect` 是 X/Y/Z 唯一适用性 producer。它不掷骰子、不按概率制造宕机，
只冻结调用当刻已经存在的 CK3 世界或资源事实：

| source kind | 必须同时成立的真实事实 | consequence kind |
|---:|---|---:|
| 1 | 受评者正在战争中，且其首都伯爵领控制度不高于 50 | 1：战时世界/治理损害 |
| 3 | 受评者个人金币小于 0 | 2：真实资源赤字 |
| 4 | 管理者是有国库的天朝制领主，且国库小于 0 | 2：真实资源赤字 |
| 5 | 受评者首都伯爵领控制度不高于 50 | 3：真实世界控制损失 |

source kind 2 刻意留空。**管理者仅仅处于战争中不是平台事故，受评者仅仅处于普通战争中也不是事故**；
战争必须与受评者首都控制崩落同时存在，才能落 source kind 1。这样不会把日常战争批量换皮成“线上事故”。

shared detector 以 `owner + subject + review cycle + probe serial` 缓存，同一轮 X/Y/Z 可以复用同一事实；
但它只服务当前开案计算，不再充当三份长期终态的 provider provenance。每个 domain 只在 N/A 即将发布，
或 positive case kernel 已确认开案成功后，把完整 detector tuple 冻结到 `zg361_ip_{x,y,z}_probe_*`；
被拒绝的重复/冲突开案不会破坏旧 receipt。这样中央 stage 4–6 分别推进时，后一个
domain 的新 detector 不会覆盖前一个 domain 的终态，也允许同一 paused frame 诚实保留跨 stage/cycle 的
`{na, incident}` 组合。首次 detector 结果为 0 时，后来发生的战争或赤字不能追溯性地把本 profile 的
N/A 改成事故；下一正式考核轮才可重新观测。
首次有效 probe 会在受评者身上、同一业务对象时点冻结三项原生资源事实：受评者个人金币
`zg361_ip_probe_subject_gold = gold`、管理者国库
`zg361_ip_probe_manager_treasury = ROOT.treasury`、受评者首都控制度
`zg361_ip_probe_capital_control = capital_county.county_control`。fresh producer 除统一天朝制管理者 trigger 外还显式
复核 `government_has_flag = government_has_treasury`；生成器没有“缺失时写 0”的分支。缓存复用也要求三项变量
全部存在，因此变量存在性就是 profile freeze 的上游完整性门；provider 最终只读取相应
`zg361_ip_{profile}_probe_subject_gold/manager_treasury/capital_control`。残缺旧帧不能伪装成完整 probe。
结果为 1 时才递增 `zg361_ip_incident_serial`，并冻结 source、consequence 与同帧资源快照。

## 可接线入口

中央 phase-two 管线依次调用：

```text
stage 4 -> zg361_ip_open_x_case_effect
stage 5 -> zg361_ip_open_y_case_effect
stage 6 -> zg361_ip_open_z_case_effect
```

每个入口都先调用真实适用性 producer，并在成功业务分支中冻结本 profile 的完整 10 字段 receipt，然后只有两条可达路径：

1. `probe_result=1` 且 source/consequence 均为正：复制同一事故 tuple 后打开真实 case；
2. `probe_result=0` 且 source=0、consequence=0：不调用 case kernel，只写 exact N/A receipt。

中央适配器只接受包含 owner、subject、cycle、reason=1、probe serial、N/A receipt、
`final_applicable=0`、`final_kpi_staged=0` 且 case 未激活的完整 N/A tuple，并把该 stage 冻结为
`status=3`。缺字段、任意零值或伪造的空 case 都是 typed RED，不能冒充 N/A。

独立调试/组合入口仍可由管理者 scope 调用：

```text
zg361_ip_open_portfolio_effect
```

它只选择一名直属可考核官员，并依次探测三份相互独立的 X/Y/Z 案卷。需要显式选择对象时，调用：

```text
zg361_ip_open_x_case_effect = { SUBJECT = scope:subject }
zg361_ip_open_y_case_effect = { SUBJECT = scope:subject }
zg361_ip_open_z_case_effect = { SUBJECT = scope:subject }
```

组合入口另保存管理者的 `zg361_ip_portfolio_cycle`，同一 `zg361_review_serial` 重放只会 no-op；只有下一轮
正式考核序号才能再次探测。中央管线不用该 all-domain ABI，而是逐域串行推进，避免三张玩家事件同时涌出。

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
source-derived 结论。当前 full-entry 只证明这些文件能随 exact 候选进入暂停地图且没有 material error；ROOT/scope 与
延迟生命周期仍待 seed 业务实机日志验证。若实机行为不同，应保留失败 artifact 后修正，不能用 OCR 猜状态。

## 每条机制不是政策卡空壳

每个 `zg361_ip_mNNN_apply_effect` 均具备：

- 完整五元 ticket；
- 共享 operation receipt，以及独立 owner/subject/cycle/case/state/choice 回执；
- 同一案同一编号只执行一次的 `done_owner + done_subject + done_cycle + done_case + done_state` 闸门；
- A（证据充分）、B（快速强推）、C（延期并背政策债）三条路线；
- A/B 冻结逐编号唯一业务对象类型、object id、五元身份、consumer contract、资源账标记与适用期限；
- C 不再写 A/B 业务字段或运行其业务消费者，只写 exact owner/subject/cycle/case/state、type/id/consumer
  contract、`due_cycle=current+1`、open/consumed/escalation 与负向结果；每个编号有独立 hidden due consumer；
- 读取前序对象的 22 项机制必须逐项证明前序 exact object 的类型、consumer contract、owner、subject、cycle、case、state
  均属于本案，并且业务对象与指定 consumer 都已执行；前序走 C、缺失或属于旧轮时，
  本项在 receipt 之前级联为 C，禁止偷读上一轮残留变量；
- `result_score -> domain score_delta -> averaged final_score -> exact next-cycle pending tuple` 的真实消费者；
- `zg361_ip_next_cycle_kpi_value` 只读完整、到期且未消费的 X/Y/Z tuple，并且只作为第八项
  `zg361_kpi_organization_evidence_value` 的子项，不新增第九种 KPI；
- 必要时再被后续编号读取，不能只写一枚永远没人看的 flag。

已有机制卡选择优先。未配置时玩家走 A；当**已经由上述真实事实建立事故案**后，获授权 AI 管理者若在战争中
走 C、低 stewardship 时走 B，否则走 A。这只决定现有案卷的处置路线；管理者战争本身不会创建事故。
AI 路线完全后台执行，不向 AI 打开玩家事件或 GUI。

## X192–204：事故、值守、复盘

- 192–195 冻结轮值深度、英雄负载、值守补偿、等量目标减免、假警报与漏报风险；
- 196 独立冻结申报等级与校正等级，保存 integrity gap；
- 197 的指挥/救火分功恒为 100%，198 从救火毛功中一次扣除根因过失；
- 199 保存有限观察期的预防功；200 保存限时限范围授权与命令日志；
- 201 冻结时间线节点，202 的 owner/期限消费者显式引用它；
- 203 累计同类复发并把行动项事实送到管理责任账；
- 204 读取冻结严重度，结算可靠性预算并产生停止上线 gate。

终态把 13 条结果平均为 `zg361_ip_x_final_score`，冻结 origin/due cycle、case、incident、source、
consequence 与 score 的 pending tuple，只影响下一轮 KPI，不回写已冻结的旧考核档位。

每个终态 producer 都用 `due_cycle = origin_cycle + 1` 并冻结 `due_offset=1`。读取采用两条等价的
prospective-cycle 口径：B1 已经在 KPI freeze 前给出当前 `b1_cycle_serial`，所以直接要求
`b1_cycle_serial >= due_cycle`；legacy/no-B1 路径在 `zg361_compute_kpi_effect` **之后**才把
`review_serial` 加一，所以 freeze 当刻 `review_serial == origin_cycle` 正好代表正在计算的下一轮。
把 legacy 分支机械改为 `review_serial >= due_cycle` 会反而晚一整轮。静态契约同时断言 producer 的
`origin+1` 写法、offset、两条读取 guard，以及 early/exact/malformed 正负例。

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

静态测试覆盖 exact 37 ID、A/B/C、逐项 exact object/consumer/resource/deadline、C 无业务对象、37 个逐 ID
policy-debt 到期事件、完整五元 done/operation/object/debt 身份、阶段唯一推进、14 个 case deadline、三张玩家
结案事件、真实事实 producer、严格 N/A、下一轮 pending/read-only value/一次性 consumer、权威 KPI 仍精确八项、
真实管理者国库同帧冻结且绝不补零、双付款原子预检、容量/份额守恒、九语 key 集以及“零新增
GUI/decision/interaction/on_action”。

### 2026-09-04 用途分片与 Incident/X production closure

- 历史 aggregate effect 为 `700,085 B / 124 effects`，SHA-256
  `0C228FAABB5F6B7DCDABFD32A071CA82F0C1EF15C08AB0BD07C25AF3A467DACD`；历史 aggregate event 为
  `8,573 B / 54 events`，SHA-256
  `49577D5475FBF6B22006021F4FADED2A248C7E193840A283FB043F7AAAC0E091`。两者现在只作为 generator 内存中的冻结
  parity reference，不再作为产品文件。
- 完整输出为 27 个 effect 用途分片和 12 个 event 用途分片；124/124 effects 与 54/54 events 的顶层 block 均保持逐字节
  parity。所有分片最多 `7` 个定义，落在目标 `1–10` 内，没有超过 20 的例外。
- X production 增量精确选择 11 个 effect 分片和 4 个 event 分片，含 47 个 Incident effects / 20 个 events；加上冻结
  case-kernel 依赖后，production 固定点为 `60 effects / 20 events / 6 triggers`，没有 Y/Z 定义夹带。
- `zg361_ip_consume_due_kpi_inputs_effect` 已在 `zg361_compute_kpi_effect` 的 subject scope 中，紧接组织证据与 KPI
  冻结语句之后、后续 consumer/档位判断之前恰好调用一次；normal/`-O` 静态测试锁定“先冻结、后消费”，当前 X
  production closure 也显式包含该 consumer。
- exact 候选位于 `_runtime/phase2-incident-x-production-closure-20260904-r3`，为 `135 files / 9,158,442 B`。
  source/formal/file-list SHA-256 分别为
  `ACC693206AAA03AEEDFB829911778275ED4D4F2EEF31CF4DCE6DE7D46F34BF3E` /
  `AF8F0DECE9477FDD60B6C96D0E09A27BFC9E55CEED40A9804B70ACB986D57A2D` /
  `045F56D78FB036CDF69225912F9B046673FCD528E99A69571363133A65EA2262`；projection SHA-256 为
  `CF379F38DA8C471DDCCDB6522D7E0864098596737862B5E2A703AECA94E40CB7`。
- 首次 live attempt `phase2-incident-x-full-entry-20260904-r1` 在 `0.338 s` 因 probe 从当前 worktree 推导出不存在的游戏目录而
  harness RED；CK3 未启动，report SHA-256 为
  `1CF7A2B014D8BBD9F39C6D1423B2E39BB5B7BCDBA21D1505CD4CECB7F5DFDC51`。这不是候选内容 RED。
- r2 显式设置 `XAR_CK3_EXE` / `XAR_CK3_GAME_DIR` 后，在 exact CK3 `1.19.0.6`、EXE SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 上以 `188.303 s` 完成 full-entry GREEN：
  8/8 entry gates、3/3 game-state markers、exact mount、`material_error_lines=[]` 与 cleanup 全部通过。artifact 为
  `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-incident-x-full-entry-20260904-r2`，report SHA-256
  `1D41298B8987AA473304AE70FC53628639DE7700BBE5A9D7484A6BF76F566FE2`，地图截图 SHA-256
  `F75097D9C20B610F81CA60837DF879865E26866F65AC76E7D40C1DF300C34B2A`，`ck3_running_after=false`。
- 本轮没有加载性能 RED，因此没有触发追加文件边界 A/B。该结果只把 Incident/X 候选提升为
  `startup/full-entry production-candidate GREEN`；没有证明 X delayed-path、N/A/incident 分支、KPI consumer、paused native
  snapshot 或 production OODA。

用途分片、消费者迁移与静态合同已由提交 `df77ed636c51c51f99f534d8efbb559b94c639d2` 推送。

仍需由统一批次完成：

1. full-entry 已用 CK3 parser/error.log 排除当前入口层 material error；仍需用真实 X delayed-path 验证 scope 与生命周期语义；
2. Incident provider 把三份 profile 固定 allowlist 从 49 增至 50，并只从受评者变量
   `zg361_ip_probe_manager_treasury` 解码 Q100000 国库余额；provenance 必须从 `not_recorded_by_mod` 更新为本
   mod 变量，缺字段仍是 typed unavailable，禁止读取 caller-selected owner scope 或补 0。随后通过 MCP 查询
   applicability probe、N/A/incident tuple、owner/subject/cycle/case/state、每编号 receipt、三项资源快照、
   pending 与 consumed receipt；
3. 在一次启动中覆盖 incident/N/A、X/Y/Z 正常、stale、重复调用、资金不足、玩家/AI、伯爵/男爵 subject；
4. 保存 paused artifact 后才升级 readiness。

固定 seed fixture 还会调用 Workforce 入口 `zg361_we_open_portfolio_effect`；当前 Incident/X 候选并未包含该入口的完整生产闭包。
此前 callable/event-only 扫描的五-root `2034 effects / 578 events` 与 Workforce root `385 effects / 161 events` 漏掉
court-position definition 的 `on_court_position_*` native callbacks，现已被 supersede。callbacks 对五-root union 净增
`8 effects / 2 events`；单独遍历 Workforce root 时还会从 role-failure 继续进入 probation publish，另拉入 `4 effects` 与
`zg361wpf.1`。
`zg361_we_open_portfolio_effect` 的完整闭包为
`397 effects / 164 events / 6 triggers / 0 values / 2 court-position definitions`；五个 product roots 在 candidate 内的完整
materialized closure 为 `2042 effects / 580 events / 6 triggers / 0 values / 2 court-position definitions`。Workforce root 与
Incident/X r3 provider 的交集为 `83 effects / 22 events / 6 triggers`，故相对 r3 的增量仍为
`314 effects / 142 events / 0 triggers / 0 values / 2 court-position definitions`，新增可见本地化为 `28 keys / 5 files`，
最终 overlay/candidate 文件数待 renderer 与 mixed-owner 分片稳定后由 builder 生成，不在当前阶段冻结。Manager 43-effect owner
的增量仍为 0，不在这条闭包内。因此下一施工项不是
直接拿 B2 r2 或当前 Incident/X tree 跑 seed，而是只把该 native-callback-aware Workforce closure 按用途物化；候选通过同树
full-entry 后，才进入 seed/paused-native。

C 路的逐编号 consumer 到期后先核对原 write/debt 五元身份与 incident provenance。核验通过时不直接改
mutable KPI，而是把每笔 `-1` 聚合进受评者的 `zg361_ip_policy_kpi_*` pending；只有 staging 成功才关闭原债务。
policy aggregate 把已到期债务的 due cycle 冻结为自己的 origin，再生成 `due=origin+1/offset=1`；同一 pending
只接受同 owner、subject、origin 的其他到期债，避免跨轮混包。它使用与 X/Y/Z 相同的 B1/legacy
prospective-cycle 双分支，既不能在 staging 当轮偷跑，也不会在 legacy 路径额外晚一轮。
该负向 aggregate 与 X/Y/Z 终态分一样由第八项组织证据读取，并由同一个 post-freeze consumer 一次性清理。
closed 重入幂等，cross-owner/错案或 provenance 不完整均 fail closed。该静态闭环仍需跨存档实机证据，
不能仅凭生成文本提升 readiness。

OCR 只可在 native/MCP 状态已经闭合后截取最终画面，不可承担导航、状态真值或 GREEN 判定。
