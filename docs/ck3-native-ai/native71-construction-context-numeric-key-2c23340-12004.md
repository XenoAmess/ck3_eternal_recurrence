# Native71：actual 2C23340 的只读 numeric key 输入

本叶闭合 CK3 1.20.0.4 / Steam build 25734779 的实际 `2C23340`，只复刻已经到达的 `R9D=0`、第五参数 detail=NULL 分支。输出为可缺省的 signed Q64；它供 03 的 actual `2468DA0` 和 `2479C20` 组合调用消费，尚不证明某栋建筑的实际收益或独立归因。

源入口 `[2C23340,2C23536)` 共 502 字节，唯一 RET 在 `2C23535`，全部内部跳转已闭合。原始范围 SHA-256 为 `c0b5979a4c94cb23cb406ac4291fba3961587fbfa43da7989a3925bef98cabce`。本轮仅复用现有缓存，新增 binary source 读取 0 字节。执行映像固定 SHA-256 为 `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`。

源前冻结与实际源位于外置 `continuation-17c/SOURCE-FREEZE-BEFORE-LEAF.json`、`SOURCE-CONTRACT.json`、`source/ACTUAL-02C23340-DETAIL.json`。后续 `SOURCE-JOIN-46c.json` 保留原冻结的不可用边，并引用 46c 源前冻结后提供的窄 raw adapter；初始冻结文件没有覆盖。

原生 ABI 是 RCX 指向一个 Q64 输出，RDX 为实际 raw context，R8D 只消费低 16 位，R9D 为 flag，入口 stack+28 为 detail。03 已持有的实际 caller 在 `2468F98` 使用 key 1E9，在 `2468FC9` 使用 context 链导出的 WORD key。actual `2479C20` 的四个 caller 使用 1CF、1D1、1D0、1D2。输出 floor(raw/100000)、signed32 累加、owner/Province 关联及当前暂停帧前后检查全部归 03。

源依次执行以下步骤：

1. 加载 raw store slot `5D1DAF8` 与 raw default slot `5D1DAE0`。store 非空时读取 context+738 full ID，以 low24 索引、store+2C count、store+20 table、stride16 的 pointer+8 和对象+10 完整 ID 校验解析。原生 miss 选实际 default；store 空时不读取 context+738。
2. 调用 `2C42930` 得到候选 Character 指针。软件实现复用 38d 的 95 字节源及 22c 的 `2C42820` 192 字节源。接着读取 context+848 payload 和 DWORD[payload+3E0]；等于 `CoDa` 时第二集合为 payload+98，否则为 null。
3. 候选对象 DWORD+1C 为 `Char` 且 DWORD+18 不为 FFFFFFFF 时直接选择。否则消费 raw object+128，必要时沿 raw object+48 的 DWORD+64==1 与 raw object+E8 full ID 链重新选择，再经 Character store `5C67568` 与实际 default slot `5C67570` 解析。所有解析保留 full generation 校验和实际 fallback。
4. `28C3AC0` 的源按 Character+1B0、extension+258、model+8 owner 选择 model+10 或已经初始化且存储仍存活的 global default。复用 46c 的软件 raw adapter，不调用原生 getter，不触发初始化。physical full ID FFFFFFFF 只在上一条实际 Character DB miss→default 分支已证明时接入；现有 M7 signed API 的 admission 不变。
5. 初始化输出为零，依次在 `2C234B1`、`2C234DE`、`2C2350B` 调用 `2C4D530`。三个集合分别是 context+30、所选 payload+98、所选 Character modifier context，factor 均为 100000、detail/selector 均为 0。复用 14c 的实际源软件读取器，三个 returned Q64 按 modulo 2^64 相加。

`ReadContextNumericKey2C23340V1` 保留原始接收指针、低 16 位 key、解析分支、选中集合与每路 optional contribution。未选中的 null 集合、实际空集合或不存在的 key 可以贡献已知零；所选字段读取失败、未初始化的 modifier default 或读取前后变化保持 unavailable。key FFFF 是子函数的零返回分支，仍需先完成实际接收对象前缀。parent 不读 context+10，也不假设 context==Province。

所有软件依赖沿同一个 read callback 消费字段；parent 对实际读到的字段保存小型副本并在最终发布前逐项读回。03 仍须使用同一当前 query/frame 与 raw context 指针 bookend，独立调用本叶不能替代该外层关联。

新 no-main export `RunConstructionContextKey2C23340Scenario12004()` 包含 12 个源相关组合场景和两项 sum 回绕检查，交 03/10 的唯一新连接 compound 执行。本叶交付时验证为 NOT_RUN；没有重放旧 17/M7、46/47 或其他已 GREEN 的独立 fixture，也没有 CK3 调用或实机完成信用。
