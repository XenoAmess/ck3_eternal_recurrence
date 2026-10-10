# Native71：1.20.0.4 第二侧原始值提供器

实际调用点 `2B95C52` 的第二侧提供器已闭合为 `[2B953E0,2B955BD)`，477 字节。`RCX` 是输出 Q64 地址，`RDX` 是调用方保存于 `R13` 的第二角色；函数返回原输出地址。它先取得现有 Family fertility 输入的同一原始 seed，再应用 BF 年龄修正、第二侧年龄档倍率及条件末倍率，输出独立的 signed raw。不能把这个输出直接别名为 fertility，也不能称为受孕概率。

范围固定为 CK3 `1.20.0.4` / Steam build `25734779`，持有输入 SHA-256 为 `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`。本包未重新计算完整 EXE 哈希，未运行游戏。第一次源闭合记录在 [SOURCE-CLOSED.json](SOURCE-CLOSED.json)，产生时实现尚未写入；来源图使用 [SOURCE-PLAN-CLOSED.json](SOURCE-PLAN-CLOSED.json) 生成 [SOURCE-GRAPH.md](SOURCE-GRAPH.md)。检查工具只验证结构和文件身份，不证明语义或实机结果。

## 实际数据链

| 阶段 | 精确输入与行为 | 证据位置 |
|---|---|---|
| 调用方 | `RCX=&stack50`，`RDX=secondCharacterR13`，返回后 `2B95C57` 读取 signed Q64 | continuation-17 的 [实际 pair provider](../continuation-17/root-literal-source/pair-value-provider-2B95670.json) |
| seed | `Character+1B0` 非空且 `28BB4C0(Character)` 为真时读取 `extension+2E0`；其他分支为 0 | `2B95400..28`，复用现有 actual4 Family 的 `FertilityRead.effective_raw` |
| modifier | `28C3AC0(Character)` 返回 C；在 `C+68` 的 unsigned-word keys、`C+74` 的 signed-DWORD count 中 lower-bound 查 key `0xBF`；命中从 `C+D0` 的 Q64 values 取 raw，已证明缺 key 为 0 | `2B9542B..A2` |
| 年龄 | `Character+6C` signed word 非负时选它，否则选 `+68`；BF raw 非负加 50000，负数减 50000，保留 Q64 wrap；signed trunc `/100000` 后用低 DWORD 做年龄减法，保留 32 位 wrap | `2B95494..DA` |
| 第二侧档位 | 从 QWORD slot `545FD64` 取低 signed DWORD；count<=0 用档 0；否则按 `545FD58` 指向的 DWORD 阈值原始顺序，选择首个 `adjustedAge>=threshold[index]`，全未命中用 index=count | `2B954DC..FF` |
| 档倍率 | `545FE08` 指向 Q64 array；只读取所选档的一项，以原生 `/100000` 运算与 seed 相乘 | `2B954FF..2B95593` |
| 末写入 | `2B9559C` 实际调用 `2B950E0(out, prefinal, Character)`；三个指针 `+1C8/+1C0/+1B8` 都为空且 `+1B0` 非空时再乘 Q64 slot `5C69E10`，其他分支保留 prefinal | [FINAL-WRITER.asm](FINAL-WRITER.asm)，`2B950E0..2B951C7` |

第二侧没有第一侧的子女数扣减。本包没有重复捕获第一侧提供器，也没有接管 pair 的短路逻辑、调度条件、随机运算或自然怀孕生命周期。

## 乘法必须保持原生中间值

共享的 [conception_value_arithmetic_12004.hpp](candidate/include/xar_bridge/conception_value_arithmetic_12004.hpp) 使用实际第二侧和末写入的相同运算。

两个 raw 都满足 unsigned `raw+3037000499 <= 6074000998` 时，结果为 `trunc(Wrap64(a*b)/100000)`。否则取 signed `big=max(a,b)`、`small=min(a,b)`，计算 `q=trunc(big/100000)`、`r=Wrap64(big-q*100000)`，返回 `Wrap64(q*small + trunc(Wrap64(r*small)/100000))`。乘法和加法都保留原生低 64 位；宽整数全乘后统一除法会改变溢出路径。

末写入是无 `.pdata` 项的实际 frameless 叶。为闭合其两个返回分支只捕获 `[2B950E0,2B951D0)` 240 字节，逻辑末端是 `2B951C8`，之后 8 字节均为 `int3`。它没有下游调用。

## 当前输入读取边界

[头文件](candidate/include/xar_bridge/conception_second_value_12004.hpp) 与 [实现](candidate/src/conception_second_value_12004.cpp) 提供精确 build binding、当前输入收集及纯计算。Root55 从现有 Family 读取得到同一帧的 seed，并提供已解析的角色指针和 fullID；读取器复核 `Character+18` 的 fullID、extension/gate seed 一致性，然后复制必要输入。

`28C3AC0` 的既有完整 220 字节证据复用自 [character_modifier_aggregator-DETAIL.json](Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261007/battle-pursuit/migration-steam25734779/actual4-domain/combat-map/pass01/character_modifier_aggregator-DETAIL.json)，key `new.instructions`。当前 collector 只读取闭合的 owned 分支：`Character+1B0 -> extension+258 -> Model`，要求 `Model+8==Character`，C 为 `Model+10`。无 model 或 owner 不符时返回 `modifier_context_owned_model_unavailable`，结果保持未就绪。

原生 getter 的 fallback 返回默认 C `5D67B90`，其 lazy guard 位于 `5D67B80` 并与 TLS epoch 比较。直接只读该默认 context 的初始化就绪合同仍未闭合。因此 collector 不调用 getter 或 initializer，不把缺失输入当作 BF=0。已证明 keys 内缺 key 与 context 不可读是两个不同结果。

年龄阈值只复制直到原生首个命中或 count 耗尽的前缀；正 count 大于 observer 明示预算 1024 时返回 unavailable。count<=0 不读取阈值指针。只在原生条件末倍率分支需要时读取 `5C69E10`。纯计算复核前缀与所选档一致，并保留 `ready/reason` 和 optional 数值。

## 聚焦验证与交付

本包 local `compile-focus01` 在 MSVC 环境准备阶段失败，编译器调用、构建和测试均为 0；已保留 [ENV-SETUP-RED.json](compile-focus01/ENV-SETUP-RED.json)。该失败不能记为实现失败或验证通过。

唯一一次新的 arithmetic + second collector 聚焦验证已交中央执行者 10，冻结请求为 [CENTRAL-FOCUS-REQUEST.json](CENTRAL-FOCUS-REQUEST.json)。输入包含实际共享 helper 的 15 项 constexpr 断言、实际第二侧 reader 及 [新 fixture](candidate/conception_second_value_12004_focus.cpp)，覆盖 native fast/split、正负半单位调整、fullID、owned BF、档选择、条件末倍率、缺失输入和 observer 预算。此处先记录为待执行；结果由中央独立回执补入。

2026-10-10 `09:45:53 UTC` 更正进度：中央实际 [root-first/RESULT.json](root-first/RESULT.json) 为 `FIXTURE_GREEN_DEFENDER_PENDING`。精确 MSVC `/std:c++20 /W4 /WX /Od /MD` compound compile 一次、exit 0，15 项 constexpr 断言通过；fixture 唯一执行一次、exit 0，stdout/stderr 均为空，声明输入前后未变。共享 header 最终 pin 为 `e020c8b81ad12c40bfce9c29e580ebf14ca1c89a0146b50bfeb99fff3023ad91`。新 EXE 精确路径的 Defender 登记返回 `settings_failed` / `admin_required_for_verified_readback`，未执行 Add 或 UAC，永久排除尚未完成；Root 明确允许这一次 owned-memory fixture 执行。离线叶验证通过与系统设置 PENDING 分别记录。

第一侧执行者 47 复用同一共享 helper；Root55 接入共享 production query。本包仅交付独占候选文件与证据，没有修改仓库、Git、共享 core 或游戏。任何 fixture 通过都只支持离线给定输入的叶行为；自然 call、pair 完整结果及实机能力仍由其拥有者举证。

## 存储与来源

实际新 build 读取为两次有限范围，共 717 字节；getter 220 字节复用已有解码，没有重复 capture。原始新字节由 D 上统一 `shared-span-cache` 独占范围保存，本包记录其精确路径；没有在本包另存 bin 副本。元数据、topic、候选与回执按仓库统一存储策略保留有限复核期限，闭场清单见 `CLOSE-STORAGE.json`。
