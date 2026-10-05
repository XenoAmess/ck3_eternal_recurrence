# Character 任务贡献的原生属性准备：291DED0 / 291DCE0

2026-10-05，CK3 1.20.0.3 / Steam25652598 / EXE SHA-256 94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6。版本身份复用已冻结证据，没有重新扫描或哈希全 EXE。两个初始 body 与四个必要共享 helper 均由唯一 owner 读取／缓存；已有下游 evaluator、modifier kernel 和 caller 元数据直接复用。

本页记录 Character/model 的属性准备输入。291C2A3→291DED0 与 291C2AE→291DCE0 都接收 RCX=model、RDX=Character；model+8 是该 Character，model+10 是属性 context。它们不是战斗 constructor，也不直接赋值六项属性。原生树先落盘，随后才实现本文的纯计算适配。

## 原生次序

~~~mermaid
flowchart TD
  P["291C0D0 caller: model / Character"] --> A["291C2A3 → 291DED0"]
  A --> AC["Character+1C0; ordered +230 task IDs"]
  AC --> AR{"strict registry full key; node+39 unfrozen?"}
  AR -->|yes| AO["31ABF40: task-owner scoped modifiers"]
  AO --> AP["original PositionType+DD8; incumbent scope; 2872840"]
  AP --> V["ordered evaluated CModifier vector"]
  AR -->|no| AS["skip this task's two contributions"]
  V --> W["291B4F0: owned modifier retained; 2438850(context, modifier, 100000)"]
  W --> B["291C2AE → 291DCE0"]
  B --> BC["Character+1B8 → +F0 task key"]
  BC --> BG{"outer unfrozen and native 31B5450 gate?"}
  BG -->|yes| BP["original definition's Position map first"]
  BP --> BT["31ABC90: clone delegation OR own +400 declarations"]
  BT --> BV["ordered councillor scoped evaluated modifiers"]
  BV --> W2["same 291B4F0 unit-Q context handoff"]
  BG -->|no| BS["no B contribution"]
  W2 --> K["existing six-skill numeric kernel inputs"]
  K -.-> U["future changed ScriptValue / validity witnesses and generic new-key/grow/empty-copy writer"]
~~~

A 的 Character+1C0 为 null 时退出。ordered +230 的完整 task keys 经 registry5D1DEA0 解析，比较 node+10 完整 key，并保留 default5D1DDF8 的解析边界。冻结 node+39 会同时排除 task-owner 和 Position passive 两项；未冻结任务先调用31ABF40，再从原始 TaskType+40 的 PositionType+DD8 评估 incumbent scope 的 passive declarations。旧宗教专题已闭的 +438/+444 task-owner collection 是此分支的一个子集，完整291DED0还包含 Position passive。

B 从 Character+1B8 的 link+F0 获取任务 key，使用相同 registry/full-key 规则，先排除冻结任务，再执行31B5450。该 gate 包含 incumbent+40 的严格 Character 解析、owner+44 对两个实际 owner-context getter 的匹配、Character link 对 Task+10 的回链、Character 有效性和 position-parameterized valid_character。31BCF90 的 compiled condition+1C38 及28BFC70已有来源复用；28C00A0仅以 Character*、int32*out 的实际 raw-ID ABI 记录，不为它猜一个 employer 名称。31B5450内部 frozen 分支返回 true，不能覆盖外层 DCE 的冻结排除。

B 先评估原始 definition 的 Position map，然后调用31ABC90。TaskType+1358 的 clone 存在时递归委派，跳过本定义 +400 的 declarations；没有 clone 时按 +400/+40C 的 stride8 原生顺序处理。scope 包含 Character ID 与 node+44，并使用已观察 tag4 / keyword globals5D4BE24、5D4BE28。原始 Position map 不随 clone 替换。

## 完整 modifier 向量与单位

2872840 读取 Position+DD8 的 stride2B0 declarations；2872320 在真实 scope 下评估 signed scale，scale=0 跳过，非零经24FD2F0复制、23033A0以 Q100000 缩放、23034B0完成。31ABC90使用同一已闭评估／复制／缩放流程。负 scale 与合法零值必须按来源保留，不能把未观测转换为零。

291B4F0 的三个 chained fragments 共414 bytes。它通过 model+240 分配1C0 CModifier，在 model+248保留指针，搬移 string/shared-object metadata，复制 uint16 property IDs 与 signed int64 raw values，再调用2438850(model+10,new_modifier,100000)。这是权重1.0的完整属性 context 输入；当前 task_owner_monthly_piety_v1 读取的 ID97 标量不足以替代此向量。

| 输入阶段 | 必需数据 | 观测／计算边界 |
|---|---|---|
| A prefix | 真正的 before291DED0 context | 当前完整 context 已含 A，不能再次附加 A |
| A contribution | stored task 顺序、owner/incumbent、冻结状态、task-owner 后 Position passive 的已评估 ID/raw 向量 | native scope / scale 在上游完成 |
| B prefix | 已包含 A 的真正 before291DCE0 context | B 不重新附加 A |
| B contribution | native gate/component witnesses、原 Position 后 clone-selected councillor declarations 的向量 | current gate bool 不自动延伸至未来改变的条件 |
| context handoff | 原生行顺序、权重100000、实际 postbranch aggregate | contribution requests 与 aggregate postimage 分开 |
| six-skill cache | 已有 NativeSkillCacheInputs12003 与上述 context | 复用既有计算器，不创造 property key 分类或 new-key 写入公式 |

## 最小纯计算实现

新增 simulation/battle_context_evaluated_rows_12003.py，source SHA-256 76794da6630276b4019e4f5a4cc851407caeba76ed54c2ba2f3f480fd1087288。

~~~python
append_evaluated_context_rows_12003(
    prefix_before_branch, emitted_modifiers,
    aggregate_properties_after=actual_postbranch_aggregate,
)
compute_evaluated_context_skills_12003(
    inputs_before_branch, emitted_modifiers,
    aggregate_properties_after=actual_postbranch_aggregate,
)
~~~

每个 EvaluatedContextModifier12003携带 PropertyContainer12003(keys_u16,values_q64,count) 和 source provenance。适配器保留 prefix，按原生2438850语义跳过已知 properties.count==0 的 modifier；空 modifier不占 weighted row 或 native_index。非空 WeightedModifierRow12003按实际 appended ordinal编号，weighted_count只增加实际附加行数，每行 weight_q64=100000。全部已知为空时 prefix保持原样；missing properties仍保留partial，不转换为空。明确提供的 postbranch aggregate属于实际输入，已评估的 declaration scale不再乘一次。后者交给既有 compute_six_skill_cache_from_native_inputs_12003。结果包含 projection/context/contribution ledger/missing inputs，以及原计算器的 NativeSkillCacheResult12003。

不存在公开完整 generic2438850 writer；有限 existing-key private combiner不能当完整 writer。适配器不推导 new-key/grow/empty-copy postimage，不隐式把当前完整 context 当 prefix，也不把一个未来 gate/ScriptValue 当原生观测。明确的空贡献向量可以表示该阶段没有贡献；缺失数据沿既有计算器保留 partial 和具体输入名。

## 只读 observer 的最短施工入口

现 campaign-root positions[].task_owner_monthly_piety_v1 已绑定31ABE10、2303700、9F24F0，但只发布 owner-task ID97。下一最小同源 additive leaf 应在 native builder 临时向量的既有生命周期内复制 ordered IDs/raws、实际 scope IDs、task/definition/clone/Position 来源、冻结及 gate witnesses、各 declaration 的 signed scale 与角色；councillor使用31ABC90，不能用 owner evaluator替代。B可直接发布31B5450 native bool及实际组件/28C00A0 raw ID getter结果。读取计划不调用291DED0/291DCE0/291B4F0去修改已有 model。

该 observer 是已闭 source/ABI 的实施计划，尚未实现或 paused 验收。before-branch prefix 与实际 after-aggregate 的来源仍需按各阶段明确提供；未来 trait 导致 ScriptValue 或 valid_character 改变时，应消费对应新 operands/evaluator 入口。不得把 field 名称、旧 scalar 或适配器测试算成 native live。

## 一次必要验证与 evidence

首轮唯一 causal fixture **GREEN 1/1，exit0，0.3611s**，使用真实 readonly g75 六属性 kernel，无 mocks 或 native callbacks；-O 下使用显式检查。prefix 含 prowess+4，task-owner 提供非空正向六项及 absolute3，Position 提供每项−1；预期与实际 raw/final6 均为 [11,12,13,14,15,16]。额外正／负 Q1尾贡献验证 prowess Δ+2，prefix不变、native rows0/1/2、权重100000、提供的 aggregate保留。没有重跑旧用例。

Root review确定了一个生产源偏差：初版对已知count0仍附加weighted row，导致count与后续index偏一。修正只跳过count0、使用实际附加ordinal，并复用held/v82已闭empty-skip来源。原两路径补丁与首轮六属性GREEN保留；新增一条empty→nonempty生产函数causal检查由同一源码owner独占，结果与实际命令见empty-row-source-correction/ROOT-DELIVERY.json。该检查不重跑六属性用例或旧tests。

统一外置证据：Z:/ck3_mod_rewrite_process_assets/g2-resume-20261005/battle-context-preparation-291c-v84/ROOT-DELIVERY.json。分支源树与输入账本位于 branch-291ded0/ 和 branch-291dce0/；A保存414-byte291B4F0与647-byte2872840共享缓存，B保存493-byte291DCE0、382-byte31ABC90、433-byte31B5450。caller唯一共享解释位于 sibling battle-context-preparation-two-branches-v84/SHARED-CALLER.md。

状态为 source-closed branches + static-ready pure primitive。native observer/publication、完整 future context/ScriptValue/new-key callback、Entry refresh、MC和胜率仍未完成。本工作 SDK、pipe、游戏进程／窗口、实机新增日、native fullbuild、共享源码修改和 Git操作均为零；Root独占合入与发布。

## 2026-10-05：task/position 当前输入观测施工

沿用 1.20.0.3 / Steam25652598 / EXE SHA94B55397…02A6；唯一任务字段为 current_person_state.current_context_task_position_inputs，与 Knight 的 current_context_source_inputs 独立。源树、ABI、外置源码及唯一聚焦验证配方见 Z:/ck3_mod_rewrite_process_assets/g2-resume-20261005/battle-context-passive-task-observer-v85/ROOT-DELIVERY.json。

A 由 Character+1C0 取得 owner council，保留 council+230/+23C 的任务原序、完整 key/default 来源与 frozen39；original TaskType+438/+444 owner 声明和 original Position+DD8 passive 分开。B 保留 Character+1B8/F0、原生31B5450 bool，先 original Position+48，再 clone terminal TaskType+400/+40C。31ABE10 owner aggregate 使用独立 align8 scopes32：Task40 incumbent、实际 Character18 owner、zero32/null64/false8；aggregate 与逐条输出独立。

复用既有 pilgrimage 的9F9E20/87E0E0/373A110 构造与析构 caller-owned native scope，再由2872840读取实际声明的 scaled/finalized 属性。声明 scale 不重复求值，未直接观测时保留 null。临时 vector 使用已见 caller0x71E0 保守存储上界、实际 constructor/header/cleanup，不声称该上界是 sizeof。

raw tasks、owner aggregate、逐条贡献 readiness 各自记录；未知 owner-clone 贡献选择仅 A 分支 partial，其他观测保留。beforeA/beforeB 与 postaggregate 未从当前 fullcontext 推造。Dynamic materialized prior-prefix 的精确阶段是291C204→291D1D0之前，还须完成其后至 A/B 的各个实际贡献阶段。

外置代码已通过两个生产 TU 与一个夹具 TU 的首次严格编译；唯一 A+B compound 由真实 ReadInputs12003→serializer 首次 GREEN，再经正式 normalizer→parser→corrected append helper GREEN。Python 首次 build_release 导入路径 harness RED 原样保留，仅补 readonly tools PYTHONPATH 后重试该消费步骤，原生及旧六stat测试未重跑。battle.cpp 只获严格编译信用，本 direct helper fixture 未链接它；actual prefix/postaggregate 仍缺，声明场景索引 A[1,2]、B[3,4,5]/count6 不冒实机观测。详细 receipt 见同包 focused-run-01/ROOT-FOCUSED-RESULT.json；状态 static-ready，Root 后续集成及 paused 实机验收待完成，native live、完整 future context、MC、胜率与新游戏日均为0。SDK/pipe/game/process/window、共享源码/Git、旧测试与全构建均为0。
