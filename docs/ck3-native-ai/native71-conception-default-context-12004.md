# Native71：1.20.0.4 默认 modifier context 的当前输入闭包

第二侧实际 provider `2B953E0` 在 `2B9542B` 调用 getter `28C3AC0`。getter 在 `Character+1B0 -> extension+258 -> Model` 可读且 `Model+8==Character` 时返回 `Model+10`；已知 extension/model 为空或 owner 不符时，原生选择默认 C `5D67B90`。46b 为已初始化的默认 C 提供当前只读输入，沿用 55 现有 `ReadConceptionSecondValueInputs12004` hook 和纯 second consumer。第一侧 47b 的新 overload 共用相同 resolver，由 55 接入。

本包固定 CK3 `1.20.0.4`、持有 EXE SHA `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`。旧 46 的 717 字节 provider/末 writer 与 220 字节 getter 均复用。新的 guard/header 103 字节、footer 96 字节及实际 BF 容器 destructor 173 字节来自现有精确缓存；atexit wrapper 23 字节和实际 callback 83 字节为本包仅有的 106 字节新读取，没有重复原始 bin。47b 独占三个 default 构造器及实际 virtual callback 输入图。

## 源定义与读取条件

| 定义 | 实际行为 | 本包结论 |
|---|---|---|
| `4223A84(&guard5D67B80)` | guard 0 改为 -1；-1 等待并重试；其他值走 completed 分支，刷新调用线程 epoch | observer 对 0/-1 保持 unavailable，不调用 header |
| `4223A24(&guard5D67B80)` | increment global epoch `543F090` 后写入 guard，再写 TLS epoch | 默认对象的构造与字段发布在 getter 调用此 footer 之前完成 |
| default keys 构造 | C+68 pointer=C+88，C+70 capacity=32，C+74 count=0 | 原生 completed empty count 是 BF 缺 key 的数值 0 |
| default values 构造 | C+D0 pointer=C+F0，C+D8 capacity=32，C+DC count=0 | 只使用当前可读存储；不把缺失字段当作 empty |
| `436B930` 注册 callback | 调用 `9F24F0(C+68)` 后清理 C 的 outer/base 存储 | guard 保持 completed 不能单独证明存储存活 |
| `9F24F0(C+68)` | 清零 keys 与 values 的 pointer/count/capacity | default metadata 已 reset 时返回 unavailable |

原生构造与 guard 合同由 [SOURCE-CLOSED-46b.json](SOURCE-CLOSED-46b.json) 及 [47b 源闭合](../continuation-47b/SOURCE-CLOSED-47b.json) 固定；46b 源冻结时实现未写入。图和边来自 [SOURCE-PLAN-CLOSED.json](SOURCE-PLAN-CLOSED.json)，生成图见 [SOURCE-GRAPH.md](SOURCE-GRAPH.md)。工具只检查结构和文件哈希。

## 生产增量

[共享 resolver 头文件](candidate/include/xar_bridge/conception_modifier_context_12004.hpp) 与 [实现](candidate/src/conception_modifier_context_12004.cpp) 复核同 query 的 Character/fullID 和实际 getter 分支。已初始化默认分支要求 guard 不为 0/-1，两容器 pointer 非空、capacity 正、count 在有效容量内；观察结果携带 source、C 地址、角色身份、guard 与两份 metadata stamp。读取 BF 后再复核这些字段，变化或 reset 时不发布输入。

[第二侧增量](candidate/src/conception_second_value_12004.cpp) 保持已接入的公开读取签名，调用同一 resolver 并在最终输出前复核观察结果。其 [输入类型](candidate/include/xar_bridge/conception_second_value_12004.hpp) 额外保留 modifier context 观察来源。纯算术、年龄档、末倍率与现有 raw 数值语义均未改变。

47b 提供 `ReadConceptionFirstValueInputsWithModifierContext12004` overload，使用共享 observation 并在 BF 复制后调用同一 recheck；原 owned-only API 保留历史行为。55 负责最小 hook 增量。Root 将 [production-default-increment.patch](production-default-increment.patch) 的新 resolver `.cpp` 纳入 native producer，并合并 first/second 增量。这里没有新增未来占位 API、调用 initializer 或接管游戏。

## 唯一新聚焦验证

冻结请求 [CENTRAL-DEFAULT-COMPOUND-REQUEST-a02.json](CENTRAL-DEFAULT-COMPOUND-REQUEST-a02.json) 将 resolver、第二侧增量、47b 第一侧增量和两份新的 default-case TU 编入同一个 executable，由 10 唯一执行一次。案例包括 initialized empty default、owner mismatch default、real zero seed、guard0/-1、destructor reset、读取中 guard/metadata 改变以及 owned 分支保持。原 46/47 与 arithmetic fixture 不重跑。实际回执待中央完成后补入；fixture 不提供自然游戏调用或概率 credit。

2026-10-10 `11:06:06 UTC` 更新：实际 [root-first/RESULT.json](root-first/RESULT.json) 为 `FIXTURE_GREEN_DEFENDER_PENDING`。五 TU 的唯一编译链接 invocation exit 0，唯一 executable run exit 0；stdout 明确报告 `first_default_current_context_join=GREEN`、未调用 native initializer、未运行 Game/SDK，stderr 为空。原 fixture replay 为 0。新 EXE 的精确路径登记实际返回 `admin_required_for_verified_readback`，未执行 Add 或 UAC，永久排除仍未完成；这与离线当前默认输入验证分别记录。

55 的已完成 [collector hook 交付](../continuation-55/addon-default-context/DELIVERY.json) 与 [实际最小 patch](../continuation-55/addon-default-context/default-first-hook.patch) 将 shared binding 放在同 query，按 current fullID Resolve 后传入第一侧 overload；第二侧沿旧签名自动使用增量。collector 从 `d164` pin 更新为 `75c227e3ce3c81456c0a1cf00b93d3a9c7aa4f67fc62d84b9782a7a8d980eee0`，Root 已收到可采纳文件。
