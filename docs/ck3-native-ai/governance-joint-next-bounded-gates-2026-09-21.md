# 标准封建治理与 M5 联合调度：下一轮有界验收合同

## 结论

本合同冻结在 agent `master@c458ef0e8231fcebe0e7d878b6dbe5525074ab02`、CK3
`1.19.0.6`、EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
它只覆盖标准封建普通 production 场景，不扩大政府、宗教或 DLC 矩阵。

当前没有一个可以诚实完成“两游戏年治理 + M5 联合选择”的单次候选：建设、生活方式与派系礼物已有各自的窄 typed 路径，
但建设尚未进入正式策略消费；婚姻只有私有只读候选；联合台账又明确缺少联盟、补给、战役成本、长期承诺与共享预算输入。
因此不能把 `joint_selection_ready=false` 改成 true，也不能用现有 `native_candidate_score` 和宣战 ID 猜跨域效用。

以下四个门可以按顺序消费同一个合适 campaign；同一时刻仍只允许一个 CK3。任一门出现动作状态不明时，先读物质状态，
不得重投。它们是 bounded 功能验收，不新增永久长跑。

## 当前实现清单

| 能力 | 当前正式/受控入口 | 已有证据 | 当前最小缺口 |
| --- | --- | --- | --- |
| 建设 | 私有 `g2_player_world_building_action_private_v1` 与 stock Province active-construction receipt | R746 同帧 981 个定义、6 个真实合法成本元组；action runner 与 pending/readback 合同已实现 | 尚无一次真实 submit→独立施工状态；也没有 `native_auto_run` 的 durable pending/下一 turn consumer |
| 生活方式 | `native-auto-run` 私有 `--allow-private-lifestyle-formal-trial`；query→perk submit→receipt 已接 service | R757 LIFE2 状态 live；R764 证明普通 map-paused GUI owner 不可用；window-independent perk fallback 已静态接通 | 需要一帧原生最终允许 `cutting_corners_perk` 的标准封建和平场景及真实动作链 |
| 封臣/派系 | `native-auto-run` 私有 `--allow-private-faction-gift-formal-trial`，有持久 pending ledger 与 cold recovery | 同帧 root、预算选择器、submit/receipt/cold classifier 的聚焦测试通过 | 需要 targeting faction > 0 且存在合法直属封臣收礼人的真实场景 |
| 婚姻外交 | 私有 observed-heir/ranked 只读查询 | R725 原 DLL 观察 657 个 CanSend/raw0 行；raw0/1 接受、raw2 拒绝修复已静态通过 | 修复版 live 复验、typed proposal、actual pair 关系/联盟后置与正式消费均缺 |
| M5 联合台账 | `build_joint_candidate_ledger` | 能去重并只计原生合法婚姻/战争行；聚焦 normal/`-O` 通过 | 设计上始终 `joint_selection_ready=false`；缺少共同效用输入，不是可由文案解除的 live-only 门 |

## Gate G4-C：真实建设与正式后续消费

优先复用 R746 的标准封建、相同 exact build、DLC/mod/load order 与同一来源存档；新 DLL/agent 制品必须单独记录 SHA-256。
候选构建只打开现有 player construction read/action 私有开关，公共 query/action/MCP 继续 OFF。

有界窗口：每个私有 mailbox step 最多 12 秒；若起始帧有 pending interaction，最多允许 4 个正式 `auto_turn` 清理；
只提交一次建设动作。成功必须同时满足：

1. 普通 production paused frame；玩家仍是相同存活封建 actor，当前无 active event；
2. preflight 完整重读玩家直辖 Province、原版最终合法性、十槽成本与 active construction；至少一个 legal tuple 的非黄金成本全为零；
3. 动作后至少保留 `20_000_000` Q100000 黄金；选择最低成本合法 tuple，确定性 tie-break 为 Province、slot、BuildingTypeID；
4. native validator、materialize、receiver 各调用一次，ACK 只能标 `pending_receipt`；超时/未知时只查询 stock state；
5. 独立更新后的 paused proof epoch 看到匹配 actor、Province、slot、BuildingTypeID 的 active construction；
6. 下一正式 turn 消费该结果并保存 checkpoint；新 CK3 进程 cold restore 后确认该施工仍存在或已完成，且没有第二次 submit。

第 1–5 项现有 controlled runner 已有入口。第 6 项之前的确定代码依赖是：把 construction pending identity、物质 receipt 与
已消费 action ID 写入正式 driver-state/checkpoint，并在 `GameplayBridgeService.plan_turn` 接入下一 turn 消费；不能用研究 runner
直接调用冒充 production loop。该接线应复用派系礼物的 durable pending 语义，不新建通用启动平台。

## Gate G4-L：生活方式最小正式动作

使用普通 production `native-auto-run`，只额外启用现有 private lifestyle formal trial。窗口上限沿用预览 bounded contract：
20 turns / 900 秒；本门只允许一次 lifestyle submit。

起始 scene 必须由公共 campaign-root 证明 feudal + at peace，且 private same-frame query 必须返回：玩家未拥有
`cutting_corners_perk`、管理生活方式有未花点、stock perk validator 最终允许。否则如实收口为 `no_legal_scene`，不得用 R757
的军事点数凑管理候选。GREEN 链为 query→typed perk submit→独立新 paused frame `HasPerk=true`→下一正式 turn 消费→checkpoint。
随后新进程 cold restore 必须继续同一高层治理目标且不重复选择该 perk。普通 map-paused 下的 focus 路径仍不在本门范围。

## Gate G4-F：一次真实封臣/派系干预

只在公共同帧 root 给出 `player_targeting_faction_count > 0` 时启用现有 private faction formal trial，并给本次真实轮次传入唯一
`private_faction_round_id`。窗口上限 20 turns / 900 秒；只允许一次 gift submit。

private query 必须证明 source faction 正在针对玩家、未处于 faction war、recipient 是存活 AI 直属有地封臣和 faction leader/member、
stock gift 最终合法且自动接受、当前没有同一 gift opinion，并在支付后保留至少 `10_000_000` Q100000 黄金。GREEN 链为：
同帧 root→合法预算候选→精确 pre-submit checkpoint→typed gift 一次→独立 gold/opinion/faction requery→下一正式 turn 消费。
随后真实新 PID cold restore 应由 persisted source faction/recipient ID 分类 applied 或 unchanged；unresolved 保留 RED，禁止重送。

若 targeting count 为零，这是合法 known-empty 场景，但不能代替“真实封臣/派系干预”门。现有 R739 类零场景不应反复运行。

## Gate M5-Q：修复版婚姻候选只读复验

在 R725 同版本标准封建存档或等价 ordinary scene 上运行修复版 observed-heir private query，360 秒总界；零动作、零 UI、零日期推进。
要求公共 root 的 first heir 与 private subject 一致，storage 完整扫描，至少五个不同 candidate，且至少一个
`recipient_answer_status_raw=0` 被判为允许。若不足五个，只记录真实数量并换合法场景，不复制行、不用战争行遮盖家庭候选。

本门只关闭 raw0 B1 与合法候选来源，不授权婚姻动作。下一动作包必须先提供 actual secondary pair 的 spouse/betrothed 与具体 alliance
before/after 查询，再接 typed proposal、pending resolution、checkpoint/cold restore。公共广告保持 OFF。

## M5 联合选择器的准确依赖

在修改 `joint_selection_ready` 前，同一 paused decision frame 至少需要下列 typed 输入：

- 共享：可支配资源和最低储备、当前战争集合、允许的并发战争上限、已有 alliance/婚约和未确认动作；
- 每个婚姻候选：actual pair 角色、原生最终合法性/接受度、预期 marriage/betrothal、具体新增或保留 alliance pair、最低长期承诺分类；
- 每个战争候选：攻守双方战略力量、盟友可参与性、集结和补给可达性、声明/维持成本、已有战争冲突、可验证的退出风险；
- 每个候选：同一 utility scale 的保守下界和预算占用；unknown 必须阻止该行参与比较，不得当成零。

首次选择器只需确定规则：先排除不合法、typed action 不可用、预算/补给/多战争冲突行，再按保守效用下界降序；并列按稳定
candidate ID。允许拒绝高风险机会，但只要存在满足阈值的合法候选就不能永远 no-op。一次决策帧最终只提交一个动作。

当前 master 没有这些共同输入，因此没有一个“只改几行 Python”且不会猜字段的安全 B0/B1 修复。下一代码包应先补上述最小只读
projection；若只得到婚姻 native score 或战争 declaration ID，仍不得实现跨域选择。

## 验证结果与执行状态

- 治理/联合 Python 聚焦集：normal 17/17、`-O` 17/17 GREEN。
- 建设/lifestyle runner 聚焦集：normal 4/4、`-O` 4/4 GREEN。
- 本次只读评估没有启动、停止或操作 CK3；检查时已有其他负责人持有唯一 CK3 实例，以上 live gate 均应继续排队。
- 未更新 `g2-requirements-v1.json`；本合同不改变 G2 `1/8`。
