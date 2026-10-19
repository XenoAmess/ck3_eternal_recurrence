# M4：复用实际军费查询的普通 planner 交接提案

状态为只读定位完成、后继窄补丁待 Root 授权。本轮唯一新增本文件；前一轮冻结十件保持原字节。`machine_id: xenoamess-full-tower-eb9d2c1186`，实际再次运行 `py -B tools/ck3_live_run_id.py machine` 核对；源审观察时间 `2026-10-19T06:38:54.051627Z`，精确文件 SHA 见末尾。本轮无 Game、RPC、活 Driver 对象/目录、SAVE、构建或测试访问。

## 已有的真实来源与调用顺序

表中 Python 路径相对 `ck3_autonomous_player/src/xar_autoplayer/`；Native `bridge.cpp` 相对 `ck3_autonomous_player/native_bridge/src/`。行号属于末尾固定源码。

| 位置 | 实际合同及对交接的影响 |
| --- | --- |
| `bridge/native_driver.py:4155 query_war_cash_current_resources_private_v1` | 已有薄调用，不保存当前 cash 观察，不新增 endpoint。源码审阅不等于读取运行 Driver。 |
| `bridge/war_cash_private_transport_v1.py:251 query_war_cash_current_resources_private_v1` | 现有唯一查询路径；266 行 normalizer 得到真实 cash DTO，最后添加实际 queried snapshot/public/native revision。这里拥有查询实际返回的 before snapshot，适合发布小观察槽。 |
| `bridge/g2_private_query_transport.py:23 read_private_g2_native_query_v1` | 检查既有 permission，取实际 before，44–50 行发送一次既有 execute-step，78–82 行读 after 并核 `_binding`，仅返回 before/result。`_binding` 包含 public/native/date/actor/window 等，但没有完整 episode/PID/connection。不能把它外推成完整 planning frame。 |
| `campaign_score_monthly_met_v1.py:20 collect_monthly_met_candidate_v1` | 56 行调用实际 driver cash query；48/66/83/88 行拥有自己的完整 frame/bookend；packets/source_frames 仅为本次 MET 局部输入，返回的是月度指标，不能从中重造下一 AUTO 的 cash DTO。 |
| `bridge/construction_monthly_budget_v1.py:195 query_construction_monthly_budget_private_v1` | 203 行同一 driver cash query，182 行保留真实 source_cash_resources。它通常在 `construction_formal_consumer.py:290/592` 才产生，晚于普通战争 consumer；不可在更早的 Service:2295 假定它已经存在。 |
| `holy_order_siege_reinforcement_v1.py:213` | 真实增援后成本查询也走同一 driver 方法；其中 receipt 是历史后验，不自动成为下一 planning frame 的现金输入。 |
| `bridge/service.py:2295` | 当前调用 `plan_war_mercenary_turn_v1` 仅传 snapshot/history/capabilities。已有新可选参数 `cash_resources`、`cash_source_frame` 尚未交入。 |
| `war_mercenary_consumer_v1.py:79 _loan_financing_input` | 已冻结实现会严格核完整 planning frame、query metadata 和 normalized loan leaf；输入默认空。153–163 行仅在实际融资缺口出现时合并只读观察。 |

## 推荐下一补丁：已有 query 发布，普通 planner 纯读取

不在每个 AUTO、Service:2295 或无条件战时循环新增军费/贷款 RPC。只利用上表实际发生的既有 cash query，新增一个有确切来源的、小型、内存观察槽；这不是声称旧 Driver 已经有该缓存。没有新鲜结果时仍为真实未知。

后继最小生产范围为三个叶；不需要改 NativeDriver、原 consumer 或增加 Native 功能：

1. **cash transport 原函数及同文件私有小 helper**：每次真正进入该 query 前清空旧槽；原 `read_private_g2_native_query_v1` 成功返回并经现有 normalizer 后，使用其实际 before snapshot 构造 schema 与 `Service._observed_planning_source_frame` 相同的完整 source frame。只复制八项身份：snapshot ID、public revision、Native revision、date、actor、episode、bridge PID、connection generation；必须严格核类型，PID 缺失不能依赖现有 `status=complete` 放行。再取一次已有 semantic reader 的 closing frame，仅用于关闭完整身份；这是 publisher 身份核对，不冒充额外原生读回或 ABI 资格。不发第二次 Native query，不导出 full history，不复制 full world snapshot。只保存小 cash DTO（含实际 queried metadata）、source/closing full frame、状态/原因和实际 loan ticket/epoch 引用；排除 payment journal 等无关 extras。使用 Driver 已有 `_driver_state_lock` 读写这个槽；测试替身没有该锁时不发布槽，不创建新锁系统。任何 query/normalize/closing 失败先前槽都不能继续有效。不会改变原合法 cash 返回结果或总体 status。
2. **Service:2293–2298**：只在现有普通战争机会中纯读取槽并将合格值传给两个已存在可选参数。机会沿用 consumer 的暂停地图、活动战争、无事件/交互窗口、quiet advance/route 与融资短缺/危局触发；强制窗口、具体军队命令及既有 pending 行为优先。纯读不调用 endpoint、snapshot 或 query，不扫描历史、不读磁盘、不从别的 packet 猜 frame。槽必须 source==closing==本次 `_observed_planning_source_frame(planning_snapshot)` 且逐项类型一致，实际 query metadata 也对应该 frame；否则只传空/未知诊断。现有 `_with_internal_planning_view` 持有 history/driver lock，本方案在其中只做同一已有 RLock 下的短读取，不加入等待 Native 的 IO。
3. **`construction_formal_consumer.py:522` 附近现有新支出入口**：仅在当前实际 war financing gap 存在时补一处明确延后：缺少同帧合法借款资格或本金报价、已知不可借，均不能以未来借款补足建设预算；记录缺失项并保留原战争/时钟 selected step。门必须位于现有 pending/receipt 处理后及新 optional quote/submit 前，不挡已有项目收据或军队动作。不把“没有贷款资格”泛化成和平期或现金本已非常充裕时的全局建设禁令。

若 Root 希望更早查询贷款，须另以一次真实战争融资机会证明该查询能改变当前决策，并按已存在 query 路径显式安排；本提案不预先引入该调用频率或新 route。

closing 的具体来源优先固定为已经存在的 `NativeHeadlessDriver.take_internal_semantic_snapshot:3000`：它调用 `NativeProtocolState.semantic_snapshot:1305`，后者在 condition 下复制当前已发布 semantic cache 和 diagnostics（1345–1352 行），没有 `endpoint.send`。所以是在原实际 cash query 完成后**增加一次本地 cached semantic copy、增加零次 RPC**；原 generic transport 的 after copy 没有从二元返回值导出，不能声称直接拿到了它。没有该既有 reader 时保留未知，不兜底新增 core query、force snapshot、publication flush 或等待新 revision；已有 cache 尚未出现时也不能用连接/心跳拼造 frame。该本地复制不创造新的 Native 时间点，不用于人为把 Q 刷新成 P。

## 查询前后 Native revision 必须保留真实语义

用 Q 表示实际 query-source frame，用 P 表示实际 closing/published frame，用 S 表示本次普通 planner frame。每个都含 public 与 Native revision，不能用一个号替代另一个。

- 当前 Native cash handler `bridge.cpp:14328` 将请求的实际 expected Native revision 存入 envelope，14360 核 worker revision 与 full snapshot，14390–14407 以独立后验 full snapshot 相等才序列化结果。DTO 的 `snapshot_revision` 属于 **Q**。该 handler 的局部函数没有 `++state_revision`，这不能证明整个 query/publisher 周期不推进 revision。
- `PublishSnapshot:12664–12673` 只有 snapshot、checkpoint 和 modal 条件都相同时才去重，否则递增 publication revision。查询、owner-pump 或相邻 publisher 更新后可能出现 P≠Q；Root 已明确要求对此保留真实身份。不能因都是只读、日期相同或差一号，就把 Q 的 packet 改标为 P。
- 现有 generic transport 若发现 `_binding(after) != _binding(before)` 会直接拒绝，cash 函数不会取得合法 DTO。保留该失败，不从 exception 或历史结果拼回所谓成功。槽清空，能力缺口保持未知，不自动重发。
- 即使 generic tuple 相同，新增完整 closing check 仍可能发现 PID/episode/connection 改变。必须让该 loan handoff unavailable；保留实际 Q/P 诊断，不回写 queried metadata。对能取得的 Q/P 分别原样保存；generic 未交出 before/result 时不能将调用前估计 frame 冒充实际 Q。
- 只有 source Q==closing P==当前 S 且完整身份/类型都匹配时，既有严格 consumer 才可消费。若未来确需消费跨 publication 的只读观察，必须另有合法、具体的原生 source-to-post 证明及单独合同；本次不放宽 frozen consumer，不使用 `revision+1` 规则，也不强制 P/Q 同号。

这是可实施的零新增 query handoff：实际 query 发布可证明的新鲜观察，后续 planner 纯筛选。不能保证每次 AUTO 都有可用贷款 quote；失配是信息缺口，不是伪造新鲜度的理由。

## 钱包与可选建设的结果

`wartime_construction_cash_v1.py:16 observe_war_financing_capability_gap_v1` 已从实际 wallet/root military buffer 判断危局或现金短缺；`construction_formal_consumer.py:522–547` 先保战争资金，629–659 再核具体建设的当前/全征召资金。接线只补同帧 loan 观察与缺口解释。

有资格且有报价也只是可筹款信息，**不能解禁当前不足的建设支出**。未到账贷款始终不加入 `played_character_gold`、`current_treasury`、monthly budget、雇佣可支付额或承诺余额；funding credit 保持 0。即使以后借款操作成功 ACK，也须另有归属明确的实际钱包到账与债务读回才能改变这条资金来源，本提案没有借款动作。未知或已知不可借时延后 optional new building/upgrade/holding，继续合法战争处理，保留 pending/receipt 优先级。

## 最小必要测试及自然采用边界

后继只需一份 focused 合成测试，复用现有 DTO fixture 与 fake semantic readers：

1. 已有 cash query 一次、完整 Q/P/S 相等时发布并传入真实 DTO；Service 纯读取计数为 **0 query / 0 semantic read**。未查询、普通非机会、缺少权限/锁或旧 Native 无 loan 子叶时，传空/未知，不能补一次隐式 RPC。
2. Q→P 的 Native/public revision 变化、相同号但 PID/episode/connection 变化、query metadata 失配分别拒绝；原 Q/P 不重标，原 cash status 不被 loan 交接失败改写。generic query 失败时旧槽已失效且 query 调用总数仍为 1。
3. 实际后续 query 或 frame/episode/connection 改变后旧槽不可消费；无磁盘复活，没有循环重试或复制历史 packet。小槽不得保留 payment journal/world/history。
4. 当前短缺/危局且资格未知、quote 缺失、已知不可借、报价/资格都有但未到账四种输入，均不能将未来借款计入钱包或建设/雇佣预算；只延后 optional 支出，原战争动作、时钟与 pending 收据继续。当前非融资缺口不新增全局建设禁令。

本轮没有运行这些测试，也没有 Native/GAME 资格。collector 已加入既有 cash query，带来额外 getter/root/scratch 工作；未来采用应借自然需要的 cash query 记录实耗、source/closing frame、Native capture epoch、实际单次读取次数和查询结果，比较同类自然样本，不凭源码或独立编译宣称性能收益，不为研究停当前实局或单独重跑大矩阵。

## 源码固定与闭场

以下 SHA 属于上述观察时间的实际源码读回；后继施工须重新核对相关叶是否已被 Root/M3 集中提交改变，不能据这些 SHA 推断任何当前安装或部署状态。所有前一轮十件只校验字节，不修改。唯一新增文件硬上限 16 KiB，计原 other-research 128 MiB/原复核期限；无外置 child、新测试或编译。`producer_closed=true`、`future_write_reserved_bytes=0`、`processes_left_running=0`、`allocated_bytes=null`、physical/parent budget credit 均为 0。

| Actual source (relative to ck3_autonomous_player) | Bytes | SHA-256 |
| --- | ---: | --- |
| src/xar_autoplayer/bridge/native_driver.py | 1612085 | f64d8c6478b37fe39a3baca6f7794b89a1e20072b443895b9e9e29de6158226f |
| src/xar_autoplayer/bridge/war_cash_private_transport_v1.py | 18284 | 6d6f4e9e1251305c5e9785f01831a735454301dcec1a1556a9a531b9193ced44 |
| src/xar_autoplayer/bridge/g2_private_query_transport.py | 4533 | 02db15ca2b070f814df06cad10da2bb9b4c8e2e1aec621f9228a5ab12f971315 |
| src/xar_autoplayer/bridge/timeline_blocker_private_transport.py | 5649 | 9a97a8f7b88bc6e2c4d26ce7fc9799900cc00d8fcc6868350bc4791b3f6429d7 |
| src/xar_autoplayer/bridge/service.py | 867830 | 9a22d369ffc245c7a26439a55819461a5c296a4fce015d1cf0ba85f86055e81e |
| src/xar_autoplayer/war_mercenary_consumer_v1.py | 24986 | f930fecd6a5c76855236a69dd6ef825a583bd139e921825410cd99cb26c707dc |
| src/xar_autoplayer/campaign_score_monthly_met_v1.py | 6340 | e1320a89bef5a0d8a5ebe8bc4af45f26845078a3365d10db7976e7a832fa0a8b |
| src/xar_autoplayer/bridge/construction_monthly_budget_v1.py | 9890 | 8bc0573083d6ab1e69bb6a04e30ad84e5f2c394742213d5ec263f37b9b357753 |
| src/xar_autoplayer/construction_formal_consumer.py | 38521 | ed408b47b0e9de3851a79aa06b4abaa631f8d663c46ee02e51b777905e75af5c |
| src/xar_autoplayer/wartime_construction_cash_v1.py | 16639 | 9eb2f93a573e2c6f467e6ff478c50d9856350cb4c436b5403fd0dd70351b772e |
| src/xar_autoplayer/holy_order_siege_reinforcement_v1.py | 14635 | 3ba4621da526a0cc4e10c5ca6bb33fe491e84805aee964ca08b54ff85a90673a |
| native_bridge/src/bridge.cpp | 1603076 | 9aac734ffd7e97f1193aec2dbddf3a670a7894c0d9163db932566c49293bc572 |

Pin read UTC: 2026-10-19T06:40:54.424569+00:00. Source: direct Python pathlib.read_bytes; no running Driver imported or instantiated.
