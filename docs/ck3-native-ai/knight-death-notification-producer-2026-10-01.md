# 本期死亡通知生产者的最小原生归因

本专题只绑定 CK3 1.19.0.6、Steam build 23530548 的本机 EXE。它给出可采集的入口；尚未发生的新实机调用不能写成已证实。本机 EXE SHA-256 为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。

冻结原件为 `C:/Users/1/ck3-a04-mechanism-evidence-20261001/knight-selector-causality-research-attempt-01/event-producer-abi-freeze-attempt-02/event-producer-abi-contract-a02.json`，11,825 bytes，SHA-256 `46AA0A18A4ED411B0F3C6063F322D3F2ED70844A5BAC145CEFF8CF77D5FFE87D`。里面保存原版脚本、逐指令静态报告的精确副本及大小/hash。七项原 EXE 字节检查通过，仅证明这份 ABI。首次封存脚本的 parser 指令期望误写 RBX 基址，而原件是 RDI 基址；其失败 attempt 与副本完整保留，第二 attempt 只纠正该原字节断言。

## 只读定义绑定

RVA `0x570F790` 是已经初始化的 `CJominiEventManager` singleton 指针槽：原 getter `0x2049234` 读取，构造函数 `0x33D3F1A` 写入，析构函数 `0x33D4000` 清除。采集只直接读取槽，不调用会断言、初始化或修改数据库的 helper。

其基类布局 `+0x40` 是定义指针数组，`+0x48/+0x4C` 为 capacity/count；原定义查找 `0x33D41D1/0x33D41D5` 按索引读取该数组。`+0x58/+0x64` 是平行的排序 calculated-ID 数组/count。`0x44DA080` 是基类构造 vtable 的静态锚，不能未经证据把派生 manager 的实际 vtable 强制等同它。

每个定义的 `+0x08` 是 calculated ID，`+0x0C` 是统计 ordinal，`+0x10` 是 MSVC stable-key string。`+0x230` 是 **qword 根指针**，不是内嵌 root 对象。原 parser 对 `immediate`（原生 key `0x6D1`）在 `0x33E639B` 取得此拥有指针槽地址，在 `0x33E63EF` 读取槽中的 root 再调用 parse 槽。`+0x228/+0x238` 分别属于 after/on-trigger-fail，不能混作 immediate。

预 arm 仅绑定 `death_management.1200/.1201/.1202/.1204/.1205/.1206/.1207`：有界验证 count/cap、数组、字符串；每个稳定键必须唯一，定义 ID/ordinal/root/vtable/hash/children 元数据须在第二次读取中稳定，root 之间不能有未解释的别名。未匹配节点不属于本期监控。原版脚本到已加载定义的来源关联仍须当次 stock-only 加载合同证明，不能单凭磁盘文件 hash 证明无覆盖脚本。

## 原执行槽

编译根 vtable `0x44CF030` 的实际游戏执行槽 `+0xB0` 指向 `0x3380EC0`；原中央 dispatcher 在 `0x3380CFB` 调用 `+0xB0`。因此只需独立观察 `0x3380EC0`，无需再 patch 已被每日 trace 使用的 `0x3380A00`。

原 ABI 为 `void __fastcall(void* root, void* execution_context)`，RCX/RDX 是原入参。完整覆盖前 15 bytes：`48 89 5C 24 08 48 89 74 24 10 57 48 83 EC 20`，没有 RIP-relative 指令或 relative control flow，回跳 `0x3380ECF`。根函数从 root `+0x40/+0x4C` 读取 children，在 `0x3380EE9` 原样调用每个 child 的中央 dispatcher，函数返回至 `0x3380F06`。

`+0x58 → 0x3380840` 是带 mode/extra 的文字/tooltip 生成执行，不是实际游戏效果 `+0xB0`，不用于此生产者归因。UI active-event 指针及 call stack RVAs 也不能替代实际根身份。

仅匹配预 arm 七个 root 时，在原调用入口保存 TLS producer、原函数恰调用一次、原返回后恢复上一层 TLS。matched 两角色 `signature_weapon` 原写入可继承这个 producer。嵌套调用须恢复，不把一条通知之后的写入误挂到已返回的根。所有原入参保持，返回 ABI 不制造业务 bool。

## 实际证据准入

新 run 需要同时满足：原 producer root 与预绑定定义 `+0x230` 指针相等；stable key、definition ID/ordinal、root vtable/hash 一致；setter 处仍在此原根 invocation 生命周期；setter 的原 owner/getter 解析到这两个 full-generation 角色之一，container、实际 `signature_weapon` key、原 setter node/context 都有证；requested typed words 由独立已初始化 native identifier table 的 epoch/index/name 解码，再与 same-run 原版存档比较。不得从最终 save 的 `axe` 回填 write 请求值。

独立 monitor token 和 managed-daily token 是两个窗口标识。它们可以不同，但必须由同一次 driver PID/connection/hello generation/source/DLL 与实际 begin/finish receipts 绑定；record 内各自 token 必须正确。不能只为“同 token”而人为把这两个标识改成相等。

通知接收者的 root scope 不一定是死者。当前没有独立 decoded `dead_character` named-scope ABI，保留原 context/root-scope words，不从接收者反推。producer 匹配可以证明指定 notification immediate 内发生了哪条两角色写入；若还要断言脚本 named-scope 的完整赋值链，需另有实际 scope 证据。

这项仅关闭 weapon 生产者。骑士选择器、typed death request/enqueue/commit、名册及战斗伤亡、13 域状态链仍须由同次实机各自判断；`whole_game_mutable_bundle_complete=false` 保留，不自动决定本案局部能否关闭。
