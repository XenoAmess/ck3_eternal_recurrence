# R06 type635：最终 receiver 的变量来源与准备参数的区别（1.20.0.4）

这次增量将最终 receiver 的**直接写入链**收敛到已持 `3AC38C0 → 3AC1C00 / 3AC3EF0 → 3AC1C00`。刚闭合的 `3E4BC50` 准备另一个 scratch 缓冲区，本体没有直接构造最终 type635 变量。当前仍没有一个实际地址已知、尚未读取、且能据已闭调用边认定为最终 receiver 构造器的 callee；因此本轮没有消耗唯一的新函数读取额度。

机器 `desktop-3fevhd2-1c74096080`；离线复核时间与文件 pins 见 [增量记录](evidence/r06-type635-variable-origin-12004.json)。精确 EXE 1.20.0.4，既有 SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。源码基线 `6bf30840af44231653f8e914389b59c8798f2cc1`。没有新 EXE 读取、全文件 hash、SDK、游戏/桌面接触或构建。R189 的实机事实来自 [已冻结便携记录](acceptance/2026-10-17-r189-parent-prefix/EVIDENCE.actual-a34.json)，不是本次新观察。

## 两个缓冲区和四组不同的 count

以下 `block` 都是 `callback+10`。不能以字段名字相近合并它们。

| 原生来源 | 实际用途 | R189 当前已知 |
| --- | --- | --- |
| `block+98` 指针、signed `block+A4` count | 声明 key 数组（8B 一项）；`3AC38C0` 据此建立 16B 临时变量 | 第一次 full-capture diagnostic 为 count1；稳定 local/prefix 为 index0、declared type635 |
| `block+B0` 指针、signed `block+BC` count | 4B 索引数组；最后索引 `B0[BC-1]` 选择最终变量 | diagnostic index_count1；稳定 index0；不是已执行变量表 |
| `block+80` 指针、signed `block+8C` count | 0x30B literal/provider 记录，写 0x28B scratch 槽 | **未发布，unknown**；不能由其他 count 推出0 |
| `block+0` 指针、signed `block+0C` count | 0x40B preparation 记录；读取变量，再经动态目标写 scratch | **未发布，unknown** |
| `block+18` 指针、signed `block+24` count | 最终 receiver 的 0x18B 链 | R189 expression 为0；**不证明前两准备阶段没有执行** |

`3AC3918/391F` 将 `+8C` 与 `+0C` 相加，给 scratch descriptor 分配/初始化 0x28B 槽；`3AC3994` 另外读取 `+A4`，并在 `3AC3A93..3AC3AA4` 对 16B 变量写 pointer0、默认 type 和 raw byte1。这两个 descriptor 分别在 `3AC3B5D/3AC3B61` 作为 R8/RDX 传入 `3E4C090`，后者原样传入 `3E4BC50`。这是本体直接的数据流区别；未闭 callee 的别名、全局写入及其他传递副作用仍为 unknown。

## 最终变量的直接写入和选择

1. `3AC3AD0..3AC3B34` 逐声明查本地 definition 的 `+90/+9C`、stride50 表。首个 `entry+48` key 命中就调用 `3AC1C00(entry, &variables[i])`。
2. `3AC1D18..3AC1D32` 写入匹配 type。mode0 在 `3AC1D9A/1D9D` 将 `entry+0` 原样写入变量 pointer，再写变量 `+C=1` 并返回 AL1；**pointer0 也返回 AL1**。mode1 同样复制 pointer，`+C=0`。mode>=2 才沿 `entry+38` provider 虚表 slot2（`+10`）分派。
3. `3AC3B55` 调父解析器。`3AC401C/4020` 只在本地 entry flag4C 非零时让变量不进入 pending。父层 first-key-match 的 flag4C 必须非零，才会在 `3AC41A9` 调 resolver；AL1 才移出 pending。本地 AL1、父 entry 存在或 provider_present 均不单独证明最终变量已选定。
4. `3E4C0D3..3E4C11D` 取 `indices[index_count-1]`，从 **16B variables** 中读 pointer/type；`3E4C124..136` 做 expected-type / null 分支。`3E4BC50` 本体没有把 scratch 槽复制为这个最终 pointer 的指令。
5. R189 的 final chain0、kind3、flag0 意味着若最终业务目标实际被调用，`3E4C202` 的 RCX 是该变量 pointer。已闭 28B `1303D40` 对 RCX0 返回 AL0，不调用 `12FF8D0`。因此**空 pointer 不能靠该 wrapper 变成有效补员业务调用**；这不是对 R189 当前未观察临时表的 pointer 值作推断。

## R189 为什么仍不能授 receiver/getter 资格

两处控件的稳定 prefix0 和 prefix4 都是 type635/mode0/flag0、direct false/provider false。depth1–3 的 definition 存在但 count0；depth5–7 definition 不存在。每一步实际走 `context_e8`，frontier8 context 存在，但其 definition/count/entry 尚未读取。flag0 的 depth4 项被父解析器过滤，不能作为成功值覆盖本地变量；本地 mode0 的 AL1 也不会终结父 pending。

据已持直接写入链，R189 若未来执行该 callback，仍需要未观察的父分支或未闭传递效应才能得到非空最终 pointer。当前没有观察 native callback 执行或临时表，不能将这句话改写为“本场 pointer 确定为空”“GUI 点击失败”或“没有 provider”。同样不能将 `callback+F0`、玩家31254、Army18、父链 context 或 scratch 槽冒充 type635 receiver。

当前可执行的 source-qualified **receiver getter 候选仍为无**。已闭 `receiver+218 → 完整 Character → military+1C0/+4A9` 的读法仍需先取得真实 receiver。provider/helper 执行也未获资格。

## 下一步应拿什么，而不是泛追 helper

`3E4BCB5` 的 literal provider vtable+28 目标未知；`3E4BCC1 → 879390` 的已知输出连接是 scratch 目的槽。`87CCC0` 返回值参与默认 type 比较，其本体未读。这两条都不能据现持调用边命名为最终 type635 构造器；本轮不会为它们建立“receiver 上游”假边或读取地址邻域。

已有接口若增加一次最小只读观察，应保留固定 refill source/profile、双读身份及共享预算：

- 在现有 expression child 发布 signed `block+8C`、signed `block+0C` 两个**各自 availability** 的原始 count。它们只能区分 preparation 是否旁路；即使都0，也不能单独证明 receiver 已解析。
- 若某 count 正且在有限记录数内，再发布其 source-bound 实际函数 RVA；literal 是记录对象的 **vtable+28**，不是变量 provider 的 slot2。不能用 scratch provider RVA冒充最终 receiver provider RVA。
- 最终 receiver 的剩余精确缺口是**已存在 frontier8 的 definition/count/first matching key635 entry 及 flag**，或来自既有索引的实际 context/definition 构造者来源。任何进一步读取都须有独立限额/双读身份；本轮没有加深到16/64，也没有新增查询。

这些字段的缺失意味着现在不能给某个未读静态 callee 授予最终 receiver 来源身份。若下一次出现 actual eligible provider slot2 或实际构造 caller，才以那个唯一 RVA 建立新的有限源码计划；不追 null 地址，不执行 provider。

本轮 stdlib verifier 仅核对 held 字节、精确 call/写入指令、既有生产 strict normalizer 的 R189 prefix 和上述 count 的“未发布”边界。测试结果不是原生执行或补员成功。
