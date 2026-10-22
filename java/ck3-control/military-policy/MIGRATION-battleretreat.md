# 当前战斗撤退诊断叶的 Java 迁移

2026-10-22。独占包 `org.xar.ck3.control.military.battleretreat`。状态：Java 源码与原生产者差分向量已准备，统一 Maven 验收与真实消费者切换分别由集成负责人记录；本文不授予实机或执行资格。

## 原链与接管边界

原叶为 `ck3_autonomous_player/src/xar_autoplayer/simulation/battle_current_retreat_policy.py::assess_current_battle_retreat`。唯一直接生产消费者是 `war_active_retreat_v1.py::_budget_assessment`，原链为：

```text
严格 native battle control normalizer
  → adapt_current_battle_condition
  → run_frozen_main_tick（显式 DrawState(0, 0)）
  → assess_current_battle_retreat
  → propose_retreat / ordinary active-retreat consumer
  → 唯一现有提交权威与独立后态核对
```

Java `BattleRetreatPolicy.assess(Request)` 只接管最后一个纯诊断函数；不迁移上游 frozen-tick 算术、普通防御预算、友军集结点筛选、原生 route/token 复验、提交、UNKNOWN 排除或后态验证。原提交权威及 once-only ledger 继续唯一，不启动新服务或每次新 JVM。Quarkus 宿主后续通过进程内调用承载该叶。

直接消费与回归入口已检查：`war_active_retreat_v1.py::_budget_assessment`、`tests/unit/test_battle_current_retreat_policy.py`、`tests/unit/test_ordinary_active_retreat_v1.py`。Java 纯叶与 golden 通过之后仍须在实际普通 planner/registered service 链中替换消费者，执行原 preview→order→independent post、失联不重放及 stale-source 拒绝回归；没有该结果不能写“消费者已迁移”或删除旧实现。

## 合同与语义

`BattleRetreatCodec` 接受 `schema=current-battle-retreat-inputs/v1` 的严格投影合同。顶层必填：`schema`、`battle_frame`、`maximum_next_tick_hard_loss_raw`、`frozen_main_tick`、`retreat_preview`。后两项允许显式 `null`；缺字段、空对象与 `null` 不等价。它不是完整 native DTO normalizer，不证明被投影掉的合法性/身份字段已校验。生产适配器必须先完成既有完整 normalizer，再按单一合同投影，禁止将任意对象伪称为已归一化来源。

投影保留本叶实际读取的全部字段：battle 10 项 observed identity、ready/phase_raw/winner/forced winner/finalized、legality 三项；tick 八项 observed identity、每侧 levy getter/存量以及 loss status/owner ledger；preview 十项 observed identity、action/status/reason、source revision、target 与 candidate token。其余 native DTO 内容仍归原 normalizer 和现有 native 执行入口负责。集合保持原顺序；不新增排序、默认预算或自动选择目标。

- 输入为严格 UTF-8 JSON，拒绝重复、额外与缺失字段，最大 65,536 B；输出最大 16,384 B。
- revision 保留原 Python-only JSON 数值 uint64 域，模型用 `BigInteger`；snapshot revision 必须为正，preview public revision 允许 0。跨 JavaScript 使用必须另经统一规范十进制字符串合同，不能经过 `Number`。
- 日期为 signed int64；combat handle 为 signed int32 且拒绝 `-1` 缺失哨兵。public CUnit 为非负 int32，保留合法 slot 0；province/owner 为正 int32。bool、float、string 均不能替代整数。
- 显式预算与 hard-loss 用 `BigInteger`，保留 Python 任意精度整数比较；预算必须非负。缺失或负的 owner delta仍请求真实输入，不转成零损失。所有预算判断使用严格 `hard > budget`，相等继续观察。
- tick 八字段必须全部匹配；preview 十字段必须全部匹配。任何漂移要求重新采集/重算，不复用 token。对侧实际有 levy 但原 getter 未观察，仍请求该侧真实 levy operands。
- 一个选定 owner 必须恰有一条 hard delta；重复行或无行均不可用。native reason codes 与 missing inputs 保持输入顺序。
- `order_active_combat_retreat` 只是 proposal：`complete_transition=false`，胜率与追击损失仍为 `null`，目的地安全仍为 `false`。合法路线不证明撤退更便宜、目的地未来安全、败战或战争结果。

## 已取得与待执行的证据

`src/test/resources/battleretreat/current-retreat-golden.json` 为真实旧 Python producer 的冻结结果，32 向量，107,656 B，SHA-256 `1351a9dce0f3dce06199dc13bf65b66c9c74dd30f03691930a0cec410b8c59613`。其中 5 个向量来自真实 normalizer→adapter→runner→policy；其他向量明确标记为 frozen leaf 的分支变体，不能称为完整 native 归一化通过。捕获时原 policy 的 2 项测试实际执行成功；metadata 固定五个原生产/消费者文件的 SHA、长度与时间。

机器事实仅适用 `machine_id: xenoamess-full-tower-eb9d2c1186`；观察时间和源码身份在 golden metadata。捕获只执行原离线 producer 和其原测试，没有 Game、MCP、Native RPC、账本或保存修改。默认 JUnit 只读仓库 resource，不依赖未跟踪 Python、临时 oracle 或场次目录。

Java JUnit 为 32 个 golden 动态用例与 5 项边界/类型测试（实际测试计数以 Surefire 为准），涵盖原输出完整比较、输入序列化往返、uint64/slot 0/signed date、任意精度预算、错类型/缺字段/unknown/duplicate/malformed UTF-8、tick 八字段与 preview 十字段逐项漂移、token 缺失及不授结果信用。完整 `military-policy` Maven 编译使用 `-Xlint:all -Werror`，由 Root/M7 单一构建入口统一执行；本 lane 未另开 Maven、下载依赖或创建新构建编排。

静态/差分通过、普通消费者闭环、当前 Game 实测、真实 SAVE 与长期性能分别记录。当前没有实机接管、退兵结果、保存信用或秒/日改善。
