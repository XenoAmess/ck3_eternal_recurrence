# 现役反制原版 helper 的同帧调用安全审计（2026-09-27）

后续[被动捕获锚点审计](active-counter-native-output-capture-anchor-2026-09-27.md)定位了原版 wrapper 中 helper 返回后、向量仍由 caller 持有的 `0x23CAF25`。它支持优先观察真正的日界调用结果，避免为了取数在暂停帧主动再调用一次 helper；该锚点尚未完成 detour 实机验收。

## 判断与证据边界

**有条件可行，尚未获准作为现役预测的已验证输入。** 在 CK3 **1.19.0.6 exact EXE**、暂停的同一个 native application-main sample 中，已有 v3 代码能调用原版 `resolve_counter_classes`（RVA `0x23CF1B0`）；现役 battle-control 也已取得真正的两侧 MAA entry、primary owner、class、chunk、target 和 context。因此可以构造两方向的**当前帧** class damage-retention 向量。但它必须使用当前 `CCombatSide+0x40` 的 entry，不得复用 v3 假定首次接战的合成 roster 或已算好的向量；调用前还要补足所有原版无界索引的验证，并证明 helper 的内部临时分配、输出 header 和采样一致性在真实进程内安全。静态审计不等于实机 GREEN，更不等于下一战斗日的预言。

证据绑定本机 `ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。可用同仓 [SHA-pinned 只读反汇编器](../../ck3_autonomous_player/native_bridge/research/extract_active_advantage_sources.py) 的 `counter_side_caller`、`counter_damage_wrapper`、`counter_class_resolver`、`counter_current_chunk` 名称重放；命令示例见下文。以下 RVA/布局不得自动外推到新版 EXE。

## 原版调用的精确形状

`0x23CB1D0` 是按一侧计算出伤的调用者。它在 `0x23CB1EC` 令 `RBP=本侧 CCombatSide`；`0x23CB41B` 令 `RDX=&本侧+0x40`，`0x23CB413..41F` 令 `R8=&对侧+0x40`，然后 `0x23CB430` 调用 `0x23CAE70`。`0x23CAE70` 在 `0x23CAF20` 把 `RDX=被反制 entry header`、`R8=实施反制 entry header`、`R9=context scale` 转送给 `0x23CF1B0`，再依原 entry 顺序把 class retention 作用到本侧的伤害。两侧 `+0x40` 是 MAA entry 数组；`+0x28` levy bucket 不在这次 helper 的入参中。`0x23CB3B7..40E` 从两侧 `+0x70` 的**主参与者**解析 modifier aggregator，调用 `0x2946B50`：被反制侧 resistance enum `0x107`，实施侧 efficiency enum `0x106`。实际选中将领不替代 primary owner。

ABI 为 Windows x64：`void resolve_counter_classes(PdxArrayHeader<Entry60>* countered /*RCX*/, PdxArrayHeader<Entry60>* countering /*RDX*/, PdxArrayHeader<int64>* out /*R8*/, int64 context_raw /*R9*/)`。这里按 helper 的直接 ABI 计，外层 wrapper 的寄存器顺序另见上段。每个 header 为 16 字节：data pointer `+0`、int32 capacity `+8`、int32 count `+0xC`。每条 entry stride `0x60`，helper 实际读 full `RegimentID` `+0x08` 与当前作战人数 `+0x18`（Q100000）；其余字节可置零。**推荐复制完整有序 `+0x40` bucket 到调用者拥有的稳定缓冲，再用这些副本构造 header**。如果为了最小载荷只合成两个字段，也必须从同一 bucket 逐条拷贝、不筛掉 class 为负的 MAA、保留顺序和 count，不能按 army roster 重建。空 bucket 用 `data=nullptr,capacity=count=0`。输出 `int64[class_count]` 预分配且初始化为 `100000`，输出 header 的 capacity 和 count **都**设成原版 rules `+0xF14` 的 class count，避免 `0x23CF68D..6B9` 调用 `0xAF4BF0` 扩容；调用后仍须核对 data/capacity/count 未变。context 直接用本次 owner aggregator 所算 `0x2946B50` 的 Q100000 值，不能只把两个 modifier 自行相乘或拿 v3 旧 context。

必须反转方向调用两次：`side0 <- side1` 与 `side1 <- side0`。输出索引是原版 class index，`100000` 表示无反制折损；它是**此刻两个 entry bucket 与 owner context 的函数结果**。现有 `active_counter_inputs_v1` 在 `ck3_11906.cpp:14470-14675` 已按真实 MAA bucket 读 class、stack、target、chunk、owner context；现有结构**没有**调用原版 resolver 或发布这两条输出向量。

## 安全性审计：不能省略的检查

| 范围 | exact EXE 锚点与风险 | 可验证门槛 |
| --- | --- | --- |
| class_count／栈 | `0x23CF1E2..21F` 读取 rules `+0xF14`，按 class 数探栈并动态 `sub rsp`；`0x23CF4E9..510` 为第二数组再次探栈。无界 class 数会放大栈／临时缓冲。 | 使用现有 `ReadCounterClassCount` 的 `1..4096` 上限，并在调用前后确认 rules 指针、class count 没变；每方向最多两次受控调用，不在循环按 entry 重复调用。 |
| 目标 class | countering 循环 `0x23CF378..4BE` 从 inner type `+0x2B8/+0x2C4` 遍历 stride `0x10` 的 target，并在 `0x23CF4B2..4BE` 以 target class 对 scratch `[data+class*8]` 加压；这里**没有可见的 class 上界检查**。 | 对**全部**传入 MAA（包括自身 class `<0` 的 entry）验证 full ID、inner type、target pointer/count/stride、每个 target class `0<=idx<class_count`、有界总目标数与稳定性；不能只验证 active v1 `status=available` 的 rows。 |
| own class／chunk | countered 循环 `0x23CF648..669` 对负 own class 跳过，但非负 class 直接作为第二 scratch 数组索引，未见 `idx<class_count` 检查；`0x23D2B90` 通过 full ID/generation 回查 regiment、inner type `+0x68` stack、entry `+0x18`。零 stack 分支 `0x23D2BED..F5` 是 `mov eax,0xffffffff; mov qword [r10],rax`，实际写入 **`0x00000000FFFFFFFF`**，并非 signed int64 的 `-1`。ID 无效时原版会回退默认 object，可能悄悄算错。 | 对全部 entry 验 full generation ID、归属 CArmy、非负人数、inner type 稳定、stack `>0` 且计算 chunk 非负且不是零 stack sentinel；own class 只允许 `-1` 或 `[0,class_count)`；若其它负值存在要按原版负 class 规则单独核对。确认目标表与 chunk 的原始字节二次读取相同。 |
| owner/context | `0x23CB3B7..40E` 使用两侧 `+0x70` 的 primary，而 v3 用请求首军 owner。owner 可能在采样期间重排或 generation 变化。 | 同一 combat sample 内验证两侧 side back pointer、primary full ID、owner generation、aggregator 和 context；两方向分别求 context，不能借 selected commander，也不能沿用上次的值。 |
| 输出和临时内存 | `0x23CF687..6B9` 可能调整调用者输出 header；`0x23CF285/2C8`、`0x23CF57B/5B8` 对两组内部 scratch 仍做 allocator vcall，另有 `0x23CF256/54B` 的间接初始化调用。预分配输出**并不使 helper 零分配**。静态调用图没有看见直接 RNG 或 world-state 写，但间接目标和分配行为尚不能据此宣称无副作用。 | 独立受控 canary 先测两方向调用的崩溃／分配／线程约束；运行时只能在原 native application-main 暂停读事务内调用。输出 buffer 独占，前后校验 header 和 canary、禁止原版重分配输出；失败整子域 unavailable，不发布部分向量。 |
| 整帧一致性 | helper 期间读取全局 rules、regiment store、type、owner 和 entries，不能靠一次 JSON 绑定证明同帧。 | 采样前后核对 CombatID/full generation、province/date/episode、dispatch-in-progress=0、两侧 bucket header+每条 ID/current、primary/owner、rules class count、type/target、context。任何不一致丢弃整个双方向结果。 |

`0x23CF1B0` 的直接调用包括 rules getter `0x82DC40`、栈探针 `0x3E26A40`、清零 `0x3E29280`、当前 chunk `0x23D2B90` 和输出调整 `0xAF4BF0`；另有间接 allocator 调用。只能说其**观察到的显式写入目标**是调用者 output 与临时 scratch；必须用受控进程证据排除隐藏副作用。`0x23D2B90` 把 chunk 写入调用者给的局部结果，同时可能对无效 ID 走默认 object，所以“未崩溃”并不代表身份正确。

## 与 v3 `ReadCounterResolution` 的差异

| 输入／门禁 | v3 `ReadCounterResolution`（`ck3_11906.cpp:9302-9456`） | 现役同帧目标 |
| --- | --- | --- |
| entry 集合与数量 | 遍历假定请求中两侧每支军队的 `army.regiments`，不限定 `CCombatSide+0x40`。 | 原版 side `+0x40` MAA bucket，顺序、count 与每个 full RegimentID 原样。 |
| 当前兵力 | synthetic `entry+0x18 = regiment.current_soldiers * 100000`。086 中同 ID 的 51/51 个现役 entry 值与此不同。 | 真实 entry `+0x18` 的 Q100000 current fighting，不由整数士兵数重建。 |
| owner/context | 每侧首支请求 army owner，解析 aggregator 后用 `0x2946B50`。 | 每侧 `CCombatSide+0x70` primary owner；本侧 resistance／对侧 efficiency。 |
| resolver ABI／输出 | 已用 16 字节 header、预分配 `int64[class_count]`、后验 header 与 ID/owner generation。 | 可复用**ABI 和输出后验模式**，再增加真实 bucket 前后校验、所有 class/targets 安全检查与两个方向同一事务。 |
| 可声明含义 | v3 `available` 是 `explicit_hypothetical_contact`，不是当前战斗。 | 通过门槛后仅可称“当前帧原版 class retention 观察”；下一主战日仍受 entry、owner、modifier 和调用时序变化影响。 |

现有 active v1 对 class `<0` 直接标 `absent` 并跳过 stack/targets/chunk 的完整读取；这对它当前的说明性载荷可接受，**不足以作为 resolver 的安全证明**，因为原版 countering 循环仍遍历该 entry 的 target 表。实现时应在调用前用独立的完整验证路径覆盖它，或明确证明这些 inner type 的 target count 为零。也不能把 v3 `output_header` 预分配的成功经验扩大成 helper 无内部临时分配的结论。

## 最小实现与验收门槛

1. 新增只读、默认关闭的本机诊断路径：以现有 battle-control 已解析的 `combat` 和两侧 side 为起点，复制原 `+0x40` entry 顺序，做上表全部上下界、generation、type 与 target 验证；两次调用绑定同一个样本身份和日期。先作为诊断字段输出原始 class_count/context/两个方向完整向量及源码证据版本，不提升 active forecast ready。
2. 聚焦静态/合成验收应覆盖空 bucket、负 class（仍可能有 targets）、零 stack、无效 full generation、target class 恰好等于 class_count、entry 数/count 不一致、owner 在前后改变、输出 header 被重分配、两方向互换。原版 helper 崩溃不受 C++ `try/catch` 保护，故越界必须**在调用前**拒绝。
3. 在获准的受管离线实机中，用 frozen 086 同一 native sample 验证两向调用未变更 battle 世界字段、输出 header/canary 稳定、与独立 Q100000 公式逐 class 一致；再用被动原版日界 trace 对照真实 `0x23CF1B0` 输入／输出，至少覆盖 class `<0`、一团归零、增援和 primary 变动。此审计未启动 CK3，故这些均为未来门槛而非既成事实。
4. 只有上一步通过，才把向量接入 active typed 续算；仍要独立研究下一日读口和状态更新顺序。失败时保持 `active_regiment_counter_class_stack_context` 缺域和现有 fail-closed 策略。

只读重放示例（使用本机已验证的 Python 环境）：

```text
<verified-python> ck3_autonomous_player/native_bridge/research/extract_active_advantage_sources.py --exe <exact-1.19.0.6-ck3.exe> --function counter_side_caller
<verified-python> ck3_autonomous_player/native_bridge/research/extract_active_advantage_sources.py --exe <exact-1.19.0.6-ck3.exe> --function counter_damage_wrapper
<verified-python> ck3_autonomous_player/native_bridge/research/extract_active_advantage_sources.py --exe <exact-1.19.0.6-ck3.exe> --function counter_class_resolver
<verified-python> ck3_autonomous_player/native_bridge/research/extract_active_advantage_sources.py --exe <exact-1.19.0.6-ck3.exe> --function counter_current_chunk
```
