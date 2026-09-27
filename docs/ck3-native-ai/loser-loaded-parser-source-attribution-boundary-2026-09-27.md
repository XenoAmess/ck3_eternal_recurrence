# 败方 loaded 根的解析来源：同实例已接通，行级身份仍需运行时证据

日期：2026-09-27。接续[名称到 loaded 根的序号映射](loser-on-action-name-root-index-map-2026-09-27.md)及[根内调度结构](loser-effect-root-gate-and-child-dispatch-static-2026-09-27.md)，本轮只读检查 CK3 `1.19.0.6` 的加载/解析链。EXE SHA-256 为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；原版磁盘 `combat_on_actions.txt`、`combat_events.txt` SHA-256 分别为 `B35D696F472E801BB332D7204AA46008349E8AFBFDB38985C781EB099BBFB233`、`CF4E7F43786477DF43319638138232086CFD477FEE0F2951B34DD41BE265CADD`。没有启动或附加 CK3，没有读活内存。

## 此次新增的静态父链

`COnActionDataBase` primary vtable `0x4311910+0x28` 指向 RVA `0x33F73E0`。通用 loader `0x33F75C0` 在 `0x33F76E5` 对这个数据库虚表槽发起 factory 调用，并把返回的根对象保存为 `R13`。factory 在 `0x33F7473` 分配 `0x358` 字节，于 `0x33F74B9` 调用构造函数 `0x33F3020`；构造函数把根的 vtable 设为 `0x44DC3B0`，初始化 `+0x2B0/+0x2F8` 执行数组与 `+0x338/+0x348` 等指针。根的 `+0x30..+0x57` 在 `0x33F79EB–0x33F79FE` 接收 40 字节记录；此前 `0x33F781C/0x33F7906` 从解析上下文的当前节点 `+0x30` 读取输入，经字符串处理后填充记录。**该记录存在已证，字段是文件名、行号或别的属性尚未证。**

loader 随即在 `0x33F7A13` 调用同一 `R13` 的 vtable `+0x18`。该槽指向 `0x3B8B110→0x3B8B140`；后者在 `0x3B8B169` 调用 `0x3B91D20` 生成当前 parser 节点的另一份 40 字节记录，并在 `0x3B8B1D5` 经根对象的 parser callback 虚表 `+0x20` 处理子项。根虚表 `+0x20` 指向 `0x33F3660`，其分支随解析 token 决定填入哪种字段/子对象。独立的 `CCombatWarscoreTrigger` 虚表 `0x437D490+0x28` 指向 `0x334B490`，后者在 `0x334B569` 调同一 `0x3B91D20`，并在 `0x334B56E–0x334B585` 把 40 字节结果复制到 trigger `+0x10..+0x37`。**相同记录形状只表明共用 parser 来源机制，不证明某个 trigger 是该根的子对象。**

文件路径也并非写死在 EXE：数据库加载方法 `0x2506B30` 通过 `0x2506C3C–0x2506C56` 拼入运行时枚举的目录项，在 `0x2506C99` 构造 path view，并于 `0x2506CA5` 把数据库主实例及该 path view 传给 `0x33F75C0`。这闭合**动态 path 参数**的传递，而不是正在运行进程实际 VFS 的解析结果/bytes；仅有磁盘原版 SHA 不能排除 mod、`replace_path`、加载顺序或另一路来源。

## 为什么还不能按路径或序号把第 563 行唯一绑定

原版文本的 `on_combat_end_loser` 第 563 行是 `combat = { warscore_value >= 15 }`；原版 `combat_events.txt:2238` 存在完全相同的比较。已证 loader 把败方名称序号 76 映射到执行根序号 76，且本轮把这个根接到通用 parser；**尚未观察**实际 VFS 返回哪个文件内容、`0x33F3660` 如何把这段 `if/limit/combat` 编译入根的哪一个数组/递归边、解析期 trigger 指针是否原样进入运行时树。解析记录里的两个字符串和一个 dword 尚未被证实是可还原的“文件/行”坐标。两种执行数组分别按 `0x30/0x48` 步幅存放不同元素，另有 `+0x338` 门和 `+0x348` 递归；它们的索引不能直接当磁盘文本第几个 `if`。因此 `CCombatWarscoreTrigger` 类型、`>=` 操作码、Q100000 RHS `1,500,000`、`76` 号根或某个深度/序号，无论单独还是拼接，均不足以排除同文字 event 候选，也不证明加载实例真的来自第 563 行。

## 下一次受管实机的两阶段只读身份合同

Steam 当前 UI 新鲜度门 RED，以下仅是**未来采样合同**，不代表已经安装探针或得到观测。

1. **加载期候选身份。** 在唯一 CK3 owner、精确 EXE/DLL、VFS mount/`replace_path` 与存档指纹门禁下，容量受限地记录 `0x2506CA5` 调用的逻辑 path view、实际解析到的 VFS 来源及**同一次打开的文件 bytes/SHA**；不能用当前磁盘文件代替。记录数据库实例、名称匹配序号 76、`0x33F76E5` 返回的 `R13` 根、根 vtable、`+0x30` 原始 40 字节及 parser 对象身份。在同线程、同一 `R13` vtable `+0x18` 调用栈内，只把 vtable 为 `0x437D490` 的 `0x334B490` 调用记作候选，并保存其 parser 当前节点身份、原始 `+0x10` 记录、trigger 指针及可验证的父调用边；不能按相同阈值筛选代替父链。若 VFS bytes、parser 记录字段语义、展开/引用脚本来源或父链不能把它唯一对应到实际源第 563 行，停在候选层，不宣称行级身份。
2. **执行期对象延续。** 同一次自然正常终局记录 CombatID、WarID、日期、败方、线程和 `0x230B0EE` 的根指针，核对它与加载期 `R13` 的对象延续；沿已证 `+0x338` 节点门、`+0x2B0` 与 `+0x2F8` 数组、`+0x348` 递归，保存有界父指针/数组槽/返回结果。只有解析期候选 trigger 指针能在该根的**唯一执行父链**上出现、实际 VFS 源为败方 on-action 第 563 行，并排除 event 同字面量候选后，才进入既有 [`0x99FAF0` ABI 取数门](loser-warscore-trigger-passive-probe-abi-preflight-2026-09-27.md)，被动复制该实例操作码及求值后的 LHS/RHS raw。若解析/执行对象被复制或重建而没有可验证映射、容量溢出、重入/线程错配或来源歧义，标 RED。探针不调用原生 parser/evaluator/effect、不改变控制流，也不把候选比较命中写成真实 `-50` 正统性写回；后者另需同场 mutator 与人物前后值证据。

## 可复核性

[exact-build verifier](../../ck3_autonomous_player/native_bridge/research/verify_loser_loaded_parser_source_chain_static.py)校验三份输入 SHA、36 个指令锚点、7 个 call 目标及四个虚表槽；本机用 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`（Python 3.14.7，`pefile` 可用）通过。输出明确保持 `record_fields_decoded_as_source_file_and_line=false`、`actual_vfs_path_and_bytes_verified=false`、`source_line_563_to_loaded_trigger_unique=false`。仓库外只读原始 loader 反汇编保存在 `D:/workspace/ck3_native_war_ai_promo_work/normal-result-trigger-abi-static-20260927/loser-loader-span-20260927.txt`，SHA-256 `C897D3D784129955F518AC68D1B871CC5108136D3FB1E430FDB7A4435F5E0EBC`；本页可由 verifier 和 exact EXE 重新生成关键范围。

```text
<verified-python> ck3_autonomous_player/native_bridge/research/verify_loser_loaded_parser_source_chain_static.py --exe <exact-ck3.exe> --on-action <exact-combat_on_actions.txt> --combat-events <exact-combat_events.txt>
```
