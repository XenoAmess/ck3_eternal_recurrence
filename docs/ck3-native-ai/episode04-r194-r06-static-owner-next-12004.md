# R194 后的最小读口：静态 direct 来源的 Character 补员开关

机器 `desktop-3fevhd2-1c74096080`。依据 R194/a32（源码 `d7135ca3bf40c33c2d5416242ce844077f1e8cbe`）00:09:44Z 的[完整便携实证](episode04-r194-r06-frontier-12004.md)，两个 type635 来源都在 depth8 以 mode1/flag1、direct非空终止，direct+218 解析出完整 Character ID31254。这个值已通过实际 Character registry、代际ID和 `Char` magic复核。

## 这里的 owner 是什么

它是**静态 type635 来源对象持有的 Character 引用**，不是 Army18/Army93，不是把 direct 对象本身当作 Character，也不是把 callback+F0 或当前玩家替代 receiver。原版 `window_military.gui` 第488/898行将这两组外层控件绑定到 `MilitaryView.OnMilitaryReinforcementClick`，checked 第493/903行为 `MilitaryView.IsMilitaryReinforcementsEnabled`；GUI文件 SHA `4f5523d249c2e0a4d3c328d789ca375f154c2e102544782480936b4206c57eac`。这是 GUI model 语义。type635 的正式 C++ 类名、depth8 context 的具体构造 caller/RTTI 尚未证明，不在此补名。

原生 `1303D40` 的非空 RCX 原样传给 `12FF8D0`，后者 `12FF8EC` 从 RCX+218取 Character ID；`12FF91D` 读解析后 Character+1C0，`12FF929` 读 military+4A9。raw字节非零为enabled；null military 在原生 `12FF932` 合成0。失配时原生会选 fallback，本只读候选不追 fallback，保持 owner 身份不可用。完整346B及全部分支已在[held源码合同](evidence/military-refill-toggle-command-12ff8d0-12004.json)，无需新EXE读取或调用这个会构造命令的函数。

## 没有一个可以直接读取的持久 variables 表

`3AC38C0` 在 callback 调用内按 block+98/+A4 声明生成16B临时变量；`3AC3A93..3AC3AA4` 初始化pointer/type/raw标记。`3E4C0D3..3E4C11D` 取 block+B0 的最后一个signed32索引 `B0[BC-1]`，再读该临时表的pointer+0/type+8。R194稳定索引0/key635不是表地址，也不是已经求值的pointer。tree只读采集不创建这张表。

R194本地flag0使该声明仍pending；1–7没有eligible resolver覆盖；depth8的flag1/mode1使 `3AC1C00` 复制static direct并AL1，从父pending移除。这闭合的是**静态父解析分支**。没有观察callback执行/临时表/最终RCX，且 `3E4BC50` 下未读helper的传递副作用仍unknown；不能把静态来源推演改写成“native已选择最终receiver”。原 `current_variable_table_observed=false`、`native_receiver_selected=false` 必须保留。

下一步无需求一张本不存在的持久表，也无需执行provider：读当前已合法解析的**source-candidate Character**本身，即可给智能体补齐这个来源的实际开关输入。它应命名为候选来源状态，不命名为callback已求值结果。

## 具体施工位置与字段

在现有 `gui_refill_receiver_candidates_12004.hpp` 的 `continuation_direct_owner_218` 分支，`direct_owner_identity_verified=true` 的位置（当前约414行），还保有私有 `character` 指针。只在 parent mode1/flag非零/direct非空、完整Character资格通过时，复用同一个safe-load闭包：

```text
military = safe_load_ptr(character + 0x1C0)
if military == 0: native_enabled=false, basis=native_null_military_zero
else: raw = safe_load_u8(military + 0x4A9), native_enabled=(raw != 0)
```

不发布堆指针，不接受caller地址，不调用 `1303D40`、`12FF8D0` 或provider。现有 `ck3_12004_military_refill_switch_readonly.hpp::ReadMilitaryRefillSwitch12004` 已实现相同 Character+1C0/+4A9及身份重读；新读口必须通过计入原共享4096reads/64KiB/20ms预算的adapter复用它，或在同一现有load闭包作等价原始读取。不能绕过预算另起ReadProcessMemory。

建议在这一个匹配entry增加可选 `static_direct_owner_switch_12004`，且两次capture分别记录新叶私有身份/值再比对：

| 字段 | available规则 | unavailable规则 |
| --- | --- | --- |
| source / scope | 固定 `.4 12FF8D0_owner_218_character_1c0_military_4a9` / static_direct_source_candidate | 同固定来源；不冒充selectedreceiver |
| owner_full_id | 必须等于parent实际direct_owner_full_id，完整代际已核 | null；原parent的独立owner观察保留 |
| military_component_present | 实际读取的nonnull/zero | null |
| raw_byte_4a9 | component非空且完整双读一致时0..255；null组件时null | null |
| enabled | raw!=0；null组件按已闭原生zero分支为false | null，绝不补false |
| value_basis | raw_military_byte / native_null_military_zero | null |
| stable_double_read | true | false |
| status / unavailable_reason | available/null | unavailable/具体identity、read、budget或changed原因 |

字段availability独立于旧source primitive：新字节不可读或变化时，不得抹去已经独立合格的mode/flag/direct/owner来源；也不得发布半次raw。原完整full candidate仍depth8 unavailable，continuation仍按原source段资格判定。继续使用原frame/public/owner-thread及两次source identity比较，不增加采样、ring或总预算。可新增单个默认OFF编译开关，要求frontier开关ON；不新增MCP或query参数，旧profile省略该叶。

## 最小 fixture 与仍不授予的资格

一组生产reader/serializer focused fixture即可覆盖三条新增行为，随后用生产strict callback consumer消费wire：

1. R194型 depth8 static mode1/flag1/direct/owner31254；raw0与raw2分别发布false/true，source/owner/final callback identity不变。
2. null component发布available/native_null_military_zero、raw=null/enabled=false；component或byte不可读则新叶unavailable、raw/enabled=null，而原static来源不消失。
3. military指针或raw字节在A/B变化，只拒新叶；flag0 parent/dynamic provider分支不读取新字段。验证共享budget与OFF不读，同时用strict consumer拒绝owner与parent不一致、raw/basis/derived bool矛盾。

这次只交明确施工合同，没有实现或验证上述新读口。当前R194 raw4A9仍未观察，不追认普通Army/Regi查询中来源相同就已通过这条GUI路径。这个候选解锁的是**实际GUI静态来源owner的开关只读输入**；不授CanReplenish、command dispatch、开关转移、actual ADD或完整R06。若之后需证明最终临时变量表，最短入口是已闭 `3E4C090` 的实际调用内RDX variables descriptor及 `B0[BC-1]`，它需要独立调用观察，不能靠当前静态query猜地址或触发callback来取证。
