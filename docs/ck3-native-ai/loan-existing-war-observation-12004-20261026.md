# 普通战争命令旁的借款观察接线

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-26，本轮恢复后的静态源码审读；精确来源与同源图见 `D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/native_loan/RESEARCH-PLAN14.json`。这不是当前运行资格或借款实机验收。

现有普通战争阶段在已经选中军队等战争命令时走 `observeRecovery`，原来只保留佣兵恢复观察，绕过安静分支里的借款／退款缺口评估。finance owner 的 `war_review15` 候选现在沿这条实际 caller 补入同一观察链。它保留原 `ActionCommand`，不选新借款动作，也不枚举佣兵市场。

实际源码链是：当前 canonical state、既有 ROOT 读 → `OrdinaryWarPriority.observe` 与现成 `FinancingGapCodec` → `observeExistingWar` → 仅存在真实资金缺口时调用一次 cash supplier → 原 `CashObservationReads` publisher → `OrdinaryCashObservation.fromOriginal` → `LoanFinancingCodec`／`EmergencyFinancingAssessment` → 向原 draft 添加诊断。没有缺口时不取 cash；战争以外、前台、退出及终态工作不进入此分支。

ROOT 由原 `CanonicalRootReads` 的 canonical witness 或原读取路径产生，保留 `requireCurrent`；cash 在同一个 writer Session 的 `currentPlanning` 内选择真实 family，并保留原 receipt、内部 normalized 数据、完整 frame 及实际 canonical pending。新 helper 检查 state 的当前身份等于原 planning `before`，priority 保留的 snapshot 等于实际 snapshot。预算的 ROOT actor、native revision、date 守卫仍由现成消费链执行，不将公开文本输出拼成内部 loan input。

源码审读发现并交唯一 owner 修复了一个具体 API 错误：当前 `OrdinaryPolicy.Annotate` 的 record component 是 `retained`，候选中的 `draft()` 不存在。owner 已将生产 caller 与测试的三处调用改为 `retained()`，本岗读回了修正。这里只记录源码 API 不匹配及修正，未执行编译，不能称为真实 Maven RED 或 PASS。

候选测试沿保留原 cash corpus、现成 publisher 与真实 adapter 构造软件链，使用不相等的 public／native revision。新增检查保留原命令对象和 body、一个 cash 调用、无缺口零查询、UNKNOWN 原 pending 不释放、未收到本金 credit 为零。测试代码仍未编译或执行。测试只有 helper 层的普通战争 draft，不能替代已安装 `OrdinaryFinancePolicies.observeRecovery` 的运行验收。

该候选依赖 finance NEXT13 的完整 collector／runtime 及其合同。当前 Host 仍是旧 collector，不能整叶复制 `war_review15` 覆盖它，或把本次源审当成采用完成。Host 的采用、Java 测试、独立 SDK continuation 与完整 CI 各自另计。`seed_io13` 仍依正式 C14，没有本轮采用或执行证据。

```mermaid
flowchart LR
  W[已选普通战争命令] -->|static-confirmed| G[当前state及ROOT形成原资金缺口]
  G -->|static-confirmed: 有缺口才读一次| C[原cash family及canonical pending]
  C -->|static-confirmed| A[严格loan assessment和诊断]
  A -->|static-confirmed| R[保留原命令及UNKNOWN; credit0]
  R -. unknown: 当前原生执行和付款后态未闭 .-> P[实际借款到账]
```

付款研究继续沿 `pay_short_term_gold` 的实际4注册 → runtime execute → 资源 writer → 独立双方钱包、债务与名单后态。旧1.19入口只作历史导航。当前 source profile 的 `HOLY_LOAN_SOURCE12004` 仍为 OFF，完整 offer、实际出借人履约、动作入口和归因到账尚未资格化；本次观察接线不能开启它，未到账本金也不能进入军费、建设或佣兵预算。

本岗在共享原生索引发布前额外运行过现成 fingerprint 与 RTTI helper：fingerprint 对当前安装 EXE 得到目标 SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；`PayShortTermGold` 类型名零命中，后续 `Gold` 输出过大截断且没有保留完整输出。零命中和截断均不证明原生没有付款实现。它们不是 RawWindow 资格；后续已停止独立 EXE 读取，固定字符串定位缺口已交唯一 b64 owner，未猜 RVA、未取得新 effect body。只读文件 hash 不证明已加载实现。

本轮没有 Maven／JVM、Native 构建、Game、贷款、偿还或新游戏日。记录与源码候选受统一存储策略约束，小型记录在 2026-11-01 复核用途；容量授权复核仍为 2026-10-26T08:00:00Z，不自动延长。
