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

## 2026-10-02：R0146 实际完整监测与归因边界

R0146 使用独立冻结源码 `e88dbc5bb36cf931ee49e39815767cc68fa497eb`、`C:/w/e2cap1001g`，DLL SHA-256 `F52FFE6DDFB3C5C4B851E2C14EBB1A6A7DE10D916494E82D71F9FE71BE3D41CD`。本次原生 session 为 `native-29829-03d8b549b8f8`，CK3 PID `4836`；日期只推进 `53146848 → 53146872` 一次。每日 token `458463955581375536` 与独立 monitor token `458463955581383966` 没有复用旧 run。

在 monitor arm 前保存两角色、两侧骑士名单和完整战斗窗的原版画面，再关闭角色与战斗展示窗。原生读数确认两个窗口都不可见，另用 `subject_army_id=18` 独立确认仍是 `Combat16777218`。原始一天推进后立即导出 trace 和 monitor，完成导出才重新打开次日 UI；没有修改游戏机制或监测容量。

本次 full trace 有 184 条 scoped 记录、七个 phase；monitor 有 11 条记录，`failure_flags=0`、未截断、实际卸载。getter 观测 77 次，保留三次、非空相同读数抑制 74 次；写入没有聚合。原监测失败窗口 R0145 仍保留，不能把它改称完整。

真实 setter seq5/6 的目标是 full-ID `34120`，变量由 absent 变为 `axe`。原请求 words 为 `[133143986179, 8895]`，由当次已加载 identifier table 独立读得 epoch0/count51544/key `axe`；没有从 after save 回填。原 nearest notification ancestor 是 `death_management.1202`，definition ID `4491202`、ordinal `7363`、immediate-root hash `3950042204`。完整原节点与 definition 指针只在此进程有效。

该 producer 的实际 execution-context 为 `136668556848`，root-scope 指针 `136668561024`，原 words `[133143986180, 38574]`。这只能读出实际通知接收者；不能把 `38574` 称作受害者 `33437`。所有本次 monitor 记录的 current-death-commit context，以及 producer 的 activation-death-commit context，实际均未读到。原 e88 reader 只在既有 getter/setter/guard 采样点导出关联，因此完整监测仍不足以读出 deferred commit 的 manager 六参；后续独立的原提交入口/返回观测必须在新 run 实际采到，不能补写 R0146 原件。

house guard seq2/3 原生读到 `1105 ↔ 1053`、`default_house_relation`，原返回 AL 为 false。可以陈述这个 guard 没有通过；具体哪个子条件失败仍未知。成长与勋号分支的原版命名身份、通知 named `dead_character` 与实际提交的绑定也继续 pending。完整十三域链及六项全完成没有升级，视频优化仍等待前置研究完成。

本次只读核验实际通过 78 项 causal 门、原冻结 monitor verifier、四份独立 Rakaly 存档解码和 owner/entry 对账。有限 entry 域六个 owner、69 条前态 entry、七个 phase、十二个 snapshot 已对账；初始 arm 的有效 stats 刷新与本次死亡操作分开记账，不能把存档端点提升为每条 CPU 写入证明。

封存目录：`C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0146-four-save-causal-entry-owner-audit-reinforcement-a01/`。终封 `R0146-current-causal-entry-owner-audit-final-seal-a01.json` 为 77,179 bytes，SHA-256 `BBCDB90AB8E5AEAA4B7A7F952A4E01E83BCCE6895C675F9AC74DF8E64846164B`，包含 217 个永久保留资产和全部实际 argv/stdout/stderr。root 独立重核其中 240 个去重的文件 pin 通过，回执为 `C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-10-display-closed-observation/R0146-sealed-audit-root-pin-inspection-a01.json`，SHA-256 `9780F41EF5B1E1C7EBD38CA10F1E9512B7EB7681292C6E2183AB1666293A6DD3`。

完整 monitor 原件：`C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-display-closed-live-20261001-a10/scoped-ui-research-attempt-01/variable-monitor-finish.json`，155,581 bytes，SHA-256 `71AF2ACB0FD40BFBB38A35F04E6CC44E4472AAB3B9F4BCF8EE4893A507A23BDB`。本次结束已实际停止游戏、恢复显示设置并释放屏幕独占；Steam 保持离线，未拉取、合入或复制较新 master 内容。

## 2026-10-02：命名死者查找 ABI 已核实，实机读数待采

新的独立静态专题已确认 `CJominiEventTargetLink` vtable RVA `0x44DE928` 的原 `+0x20` 槽为 `0x340F840`。原 `0x336AB40` 在 `0x336ABD5/0x336ABD9` 把执行上下文 `+0x18` 的指针传入 evaluation context 同一字段；`0x340F864/0x340F868` 随后将它作为 `0x3359690` 的 saved-target store 参数。这条路径来自原指令，没有把 UI ActiveEvent 的布局套给执行上下文，也没有假设非多态 store 有 vtable。

原查找先遍历 store `+0` data/`+0xC` signed count，主表 stride `0x20`、key dword `+0`、原 16B value `+8`；第一个同 key 的行胜出，即使其 kind 为零也遮蔽父级。只有主表未匹配才读取 store `+0x3D0` 的 parent，再遍历 parent `+0x18` data/`+0x24` signed count，stride `0x18`、同样 key `+0`/value `+8`。原缺失返回只写 kind/aux 的低 dword 零和 payload qword 零，不写 bytes4–7；观察器不得虚构一个实际读取过的全零 16B 值。

实施范围只是在既有匹配通知 root 和真实两角色 setter 的观察点读取这条原路径：预 arm 从已经初始化的 identifier 表唯一识别 `dead_character`，保存完整 key/epoch/index 与当次原 typed words，核对角色 full-generation，并用两次稳定读取检查指针、count、所选行和值。不得调用原查找、字符串 helper 或虚拟执行函数，不增加游戏 hook，不改变 monitor 容量。原 receiver words、六参提交、current/activation 的独立含义仍保留。

ABI 原件：`C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0146-notification-dead-character-context-ABI-reinforcement-a01/notification-named-dead-character-ABI-READY-a01.json`，17,003 bytes，SHA-256 `5A0D2FC989D915BC1715CB7C7A9CD7B67D0C7F7FBEA865E3B742C7EA03583D23`。原叶函数 162 bytes 的 SHA-256 为 `C67153261D5BC5F8A85859B6E951F8CE446F080025DCBC61EF0FFBCC5CA9B083`。root 从本机 EXE 独立比对了 36 个指令锚、完整叶函数、类型信息和实际虚拟槽，回执 `C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-11-original-commit-and-scripted-identity/root-original-named-scope-ABI-recheck-a01.json`，8,436 bytes，SHA-256 `7D36D1A49D10CD0D2A188BDF2EE2A5F43A35A1B66B65E0A136B8895051E8B2CC`。

这只证明新增被动读数的静态依据。R0146 未发布 store 或其行，旧进程已经退出；不能回补其死者。新代码、离线夹具或 ABI READY 也不等于新 run 已读到 `33437`，必须等待实际采样及 same-run 提交、setter、存档的独立对账。
