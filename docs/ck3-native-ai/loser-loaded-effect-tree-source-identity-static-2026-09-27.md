# 败方 on-action 的装载名与执行树：来源身份仍未闭合

日期：2026-09-27。接续[被动探针 ABI/身份预检](loser-warscore-trigger-passive-probe-abi-preflight-2026-09-27.md)，仅对 CK3 1.19.0.6 的 EXE 和原版脚本做只读静态审计。EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；`combat_on_actions.txt` SHA-256 `B35D696F472E801BB332D7204AA46008349E8AFBFDB38985C781EB099BBFB233`。没有启动或附加 CK3，也没有安装 hook。

**2026-09-27 追加状态：**下文保留的是本轮初查时的缺口。后续[同实例、同序号映射](loser-on-action-name-root-index-map-2026-09-27.md)已静态闭合 `on_combat_end_loser` 名称序号 76 → 败方执行根序号 76，并证明构造、加载、getter、dispatch 使用同一数据库实例；下文“名称槽到根尚未闭合”不再是当前状态。根到脚本第 563 行具体 trigger、操作码/RHS 和 VFS 实际来源仍未闭合。原版另一事件也有相同 `warscore_value >= 15`，故数字相同不足以绑定脚本实例。

## 新闭合的有限边

1. **定义名确实进入 on-action 数据库的静态初始化路径。** MSVC RTTI 将 primary vtable `0x4311910` 标为 `COnActionDataBase`，另有次级表 `0x4311948/0x4311978`；`0x25047F0–0x250480F` 把三表安装到同一 `RBX` 对象。后续同一初始化函数的 `0x2505287/0x2505294` 通过 `[RBX+0x50]+0x960` 写入 `on_combat_end_winner`（字符串 RVA `0x4311D28`），`0x25052A4/0x25052B1` 通过 `+0x980` 写入 `on_combat_end_loser`（RVA `0x4311D10`）；共同调用 `0x7E9530` 复制指定长度的字符串。这证实**名称注册槽**，尚未证实它与运行时 `database+0x260` 的加载指针有可直接遍历的固定偏移关系，更不指向第 563 行子 trigger。
2. **通用 effect dispatcher 有三类可见子执行边。** 在 `0x33F8D00`，当前 effect 节点 `+0x2B0` 给出数组基址、`+0x2BC` 给出计数，步幅 `0x30`；在 `0x33F8720`，`+0x2F8/+0x304` 是另一数组基址/计数，步幅 `0x48`；`0x33F8633→0x33F8653` 还从 `+0x348` 取子指针并递归 dispatch。它们是**执行时遍历的有界候选字段**，但数组元素内哪些回调通向 `if combat`、其子 trigger 如何存放，尚未静态闭合。因此不能按磁盘脚本的文本顺序，把某个数组索引猜成该条件。
3. **解析期确有一段 40 字节记录搬运，但不能命名为来源行号。** `CCombatWarscoreTrigger` vtable `0x437D490+0x28` 指向通用 parser 方法 `0x334B490`。其 `0x334B55B` 在特定分支调用 `0x3B91D20`，`0x334B56E–0x334B585` 把其 0x28 字节结果写到 trigger `+0x10..+0x37`。该记录生成函数读取 parser 上下文 `+0xE0` 内节点的字符串/整数及 parser `+0x258` 的字符串，再调用 `0x3BA2750` 变换字符串。现有反汇编没有证明这些字段分别是什么文本、是否为文件/行号、是否在本条 literal 分支保留，也没有把该记录连到 `CCombatWarscoreTrigger` 的第 563 行实例。**不得把其中的 dword `+0x10` 或类型注册 key `trigger+0x08` 擅自称为源行号。**

现阶段形成的精确阻断点是：`COnActionDataBase` 的败方名称槽 `+0x980` → 运行时败方 effect 根 `database+0x260` → dispatcher 子表/递归边 → `CCombatWarscoreTrigger` 对象。这条链的**名称槽到 loaded 根**以及**执行节点到具体 trigger**两跳都没有具备可复核的静态对象对应；解析期 0x28 字节记录的语义也未解码。原版文件中 `warscore_value` 只出现一次，不足以补齐对象身份。

## `+0x260` 同值偏移的排误（2026-09-27 追加）

从 `COnActionDataBase` 同一初始化函数再往前核查，`0x2504C2B–0x2504C43` 从 `[RBX+0x50]` 取**名称注册表**，在该表 `+0x260` 写入长度 11 的 `on_birthday`（RIP 源字符串 RVA `0x4299FE0`）。真正的 `on_combat_end_loser` 名称注册槽是同一表的 `+0x980`，位于 `0x25052A4–0x25052B8`。执行侧 `0x230B0A9–0x230B0AD` 则先从 `[RDI+0x38]` 取**另一个基址表达式**，再从它的 `+0x260` 取败方 loaded effect 根，并在 `0x230B0EE` 传给 dispatcher。两个 `+0x260` 的字面偏移相同，基址与用途不同；把注册表该槽当败方执行根，会实际落到 `on_birthday` 名称，构成错误身份链。

[精确偏移排误 verifier](../../ck3_autonomous_player/native_bridge/research/verify_loser_name_slot_collision_static.py)冻结两份 SHA、14 处指令及三条名称源的 RIP 相对目标；本机通过。它只证明这条**错误映射必须排除**，没有反向证明名称槽 `+0x980` 如何装载到执行根，也没有绑定 `combat = { warscore_value >= 15 }` 的 runtime trigger。当前 `>=15` 的 opcode `+0x50` 和求值后的 RHS raw 仍未实测。

```text
<verified-python> ck3_autonomous_player/native_bridge/research/verify_loser_name_slot_collision_static.py --exe <exact-ck3.exe> --on-action <exact-combat_on_actions.txt>
```

## 下一次安全观测方案与拒绝门槛

先继续离线审计 `COnActionDataBase` 的装载函数，把败方名槽和 `+0x260` 的写者关联，核实两个执行数组的元素结构及 callback 子对象；再查解析期记录的字符串变换/字段含义。若仍不能静态唯一绑定，下一次受管同场只能做**候选遥测**：在唯一 CK3 owner 和精确 EXE/DLL/VFS 门禁下，容量受限地记录败方 root、实际递归父链和候选 trigger 指针/返回位置；离线比对 parser 来源与原版脚本后，才决定是否安装 `0x99FAF0` 取数 hook。候选命中不得标为“第 563 行已验证”。没有 VFS 来源、唯一父链、节点指针三项回读时，拒绝安装权威归因 hook；不调用 parser/evaluator/mutator，不覆盖旧回执。

这一采样应明确分两道门。第一道只记录 `0x230B0EE` 当次败方调用的 loaded root 地址与 dispatcher 的父子边、候选 trigger 指针，并同时取得该进程实际 VFS 脚本 bytes、同场 CombatID/WarID、日期和败方身份；若仍找不到名称槽到 root 的写者，结果只能叫“败方执行树中的候选”，不能叫“磁盘第 563 行”。第二道须先离线证明该指针是唯一的原版条件节点，才允许在同一次调用上下文中被动读 `trigger+0x50`、`0x99FAF0` 两侧 raw qword 和返回值；`+0x08` 类型 key、文本唯一性、相同 `+0x260`、同一回调时间或单个 comparator 命中均不满足身份门。任何容量溢出、重入/线程交错、VFS 不符或父链歧义都保留 RED，不调用原生求值器或 effect。

## 可复核证据

[静态 verifier](../../ck3_autonomous_player/native_bridge/research/verify_loser_loaded_effect_tree_static.py)校验两份 SHA、RTTI 类型名、两个原版 on-action 名称、trigger parser 虚表槽及 24 处精确指令，成功仍输出 `source_line_field_verified=false` 和 `complete_root_to_trigger_parent_chain_verified=false`。

```text
<verified-python> ck3_autonomous_player/native_bridge/research/verify_loser_loaded_effect_tree_static.py --exe <exact-ck3.exe> --on-action <exact-combat_on_actions.txt>
<verified-python> ck3_autonomous_player/native_bridge/research/find_rtti.py COnActionDataBase --exe <exact-ck3.exe> --slots 3
```

仓库外原始记录位于 `D:/workspace/ck3_native_war_ai_promo_work/normal-result-trigger-abi-static-20260927/`：`on-action-rtti.txt` SHA-256 `7446CCC9F4D9744C52970B6ADA5D25A548DC20A5721C936854278DE94AE9DFFD`；`on-action-constructor-span.txt` `BDBEC40D9A2A7E22C058E0F0A82BBA23F3AD79C6C7CB6228A70E4C39ACE8445D`；`on-action-name-slots.txt` `C5A59B9A080D008DC75494FB4FF38D0627BED84B0382CF7744C780A957E291AF`；`effect-vector-30.txt` `8EF9DB31C14AF12AB1511558C4A71979FD2D70F4D95A6E3362A1ED8B5F0C51D5`；`effect-vector-48.txt` `FF6B299F14900E0832DAB7489B43086119E1E54683609CE6AB72D516AC5BCB49`；`parser-record-builder.txt` `956A66FA70D5A25F67A61A2FE2DE0112965AC6B543DCE26BBE8F74FF7445A6CA`；`trigger-base-parse.txt` `B740501DF7F9AB4C03D122EBC9F73A17278E1567649C42D67668C0F33105790C`。
