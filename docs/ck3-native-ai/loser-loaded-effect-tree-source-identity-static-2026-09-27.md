# 败方 on-action 的装载名与执行树：来源身份仍未闭合

日期：2026-09-27。接续[被动探针 ABI/身份预检](loser-warscore-trigger-passive-probe-abi-preflight-2026-09-27.md)，仅对 CK3 1.19.0.6 的 EXE 和原版脚本做只读静态审计。EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；`combat_on_actions.txt` SHA-256 `B35D696F472E801BB332D7204AA46008349E8AFBFDB38985C781EB099BBFB233`。没有启动或附加 CK3，也没有安装 hook。

## 新闭合的有限边

1. **定义名确实进入 on-action 数据库的静态初始化路径。** MSVC RTTI 将 primary vtable `0x4311910` 标为 `COnActionDataBase`，另有次级表 `0x4311948/0x4311978`；`0x25047F0–0x250480F` 把三表安装到同一 `RBX` 对象。后续同一初始化函数的 `0x2505287/0x2505294` 通过 `[RBX+0x50]+0x960` 写入 `on_combat_end_winner`（字符串 RVA `0x4311D28`），`0x25052A4/0x25052B1` 通过 `+0x980` 写入 `on_combat_end_loser`（RVA `0x4311D10`）；共同调用 `0x7E9530` 复制指定长度的字符串。这证实**名称注册槽**，尚未证实它与运行时 `database+0x260` 的加载指针有可直接遍历的固定偏移关系，更不指向第 563 行子 trigger。
2. **通用 effect dispatcher 有三类可见子执行边。** 在 `0x33F8D00`，当前 effect 节点 `+0x2B0` 给出数组基址、`+0x2BC` 给出计数，步幅 `0x30`；在 `0x33F8720`，`+0x2F8/+0x304` 是另一数组基址/计数，步幅 `0x48`；`0x33F8633→0x33F8653` 还从 `+0x348` 取子指针并递归 dispatch。它们是**执行时遍历的有界候选字段**，但数组元素内哪些回调通向 `if combat`、其子 trigger 如何存放，尚未静态闭合。因此不能按磁盘脚本的文本顺序，把某个数组索引猜成该条件。
3. **解析期确有一段 40 字节记录搬运，但不能命名为来源行号。** `CCombatWarscoreTrigger` vtable `0x437D490+0x28` 指向通用 parser 方法 `0x334B490`。其 `0x334B55B` 在特定分支调用 `0x3B91D20`，`0x334B56E–0x334B585` 把其 0x28 字节结果写到 trigger `+0x10..+0x37`。该记录生成函数读取 parser 上下文 `+0xE0` 内节点的字符串/整数及 parser `+0x258` 的字符串，再调用 `0x3BA2750` 变换字符串。现有反汇编没有证明这些字段分别是什么文本、是否为文件/行号、是否在本条 literal 分支保留，也没有把该记录连到 `CCombatWarscoreTrigger` 的第 563 行实例。**不得把其中的 dword `+0x10` 或类型注册 key `trigger+0x08` 擅自称为源行号。**

现阶段形成的精确阻断点是：`COnActionDataBase` 的败方名称槽 `+0x980` → 运行时败方 effect 根 `database+0x260` → dispatcher 子表/递归边 → `CCombatWarscoreTrigger` 对象。这条链的**名称槽到 loaded 根**以及**执行节点到具体 trigger**两跳都没有具备可复核的静态对象对应；解析期 0x28 字节记录的语义也未解码。原版文件中 `warscore_value` 只出现一次，不足以补齐对象身份。

## 下一次安全观测方案与拒绝门槛

先继续离线审计 `COnActionDataBase` 的装载函数，把败方名槽和 `+0x260` 的写者关联，核实两个执行数组的元素结构及 callback 子对象；再查解析期记录的字符串变换/字段含义。若仍不能静态唯一绑定，下一次受管同场只能做**候选遥测**：在唯一 CK3 owner 和精确 EXE/DLL/VFS 门禁下，容量受限地记录败方 root、实际递归父链和候选 trigger 指针/返回位置；离线比对 parser 来源与原版脚本后，才决定是否安装 `0x99FAF0` 取数 hook。候选命中不得标为“第 563 行已验证”。没有 VFS 来源、唯一父链、节点指针三项回读时，拒绝安装权威归因 hook；不调用 parser/evaluator/mutator，不覆盖旧回执。

## 可复核证据

[静态 verifier](../../ck3_autonomous_player/native_bridge/research/verify_loser_loaded_effect_tree_static.py)校验两份 SHA、RTTI 类型名、两个原版 on-action 名称、trigger parser 虚表槽及 24 处精确指令，成功仍输出 `source_line_field_verified=false` 和 `complete_root_to_trigger_parent_chain_verified=false`。

```text
<verified-python> ck3_autonomous_player/native_bridge/research/verify_loser_loaded_effect_tree_static.py --exe <exact-ck3.exe> --on-action <exact-combat_on_actions.txt>
<verified-python> ck3_autonomous_player/native_bridge/research/find_rtti.py COnActionDataBase --exe <exact-ck3.exe> --slots 3
```

仓库外原始记录位于 `D:/workspace/ck3_native_war_ai_promo_work/normal-result-trigger-abi-static-20260927/`：`on-action-rtti.txt` SHA-256 `7446CCC9F4D9744C52970B6ADA5D25A548DC20A5721C936854278DE94AE9DFFD`；`on-action-constructor-span.txt` `BDBEC40D9A2A7E22C058E0F0A82BBA23F3AD79C6C7CB6228A70E4C39ACE8445D`；`on-action-name-slots.txt` `C5A59B9A080D008DC75494FB4FF38D0627BED84B0382CF7744C780A957E291AF`；`effect-vector-30.txt` `8EF9DB31C14AF12AB1511558C4A71979FD2D70F4D95A6E3362A1ED8B5F0C51D5`；`effect-vector-48.txt` `FF6B299F14900E0832DAB7489B43086119E1E54683609CE6AB72D516AC5BCB49`；`parser-record-builder.txt` `956A66FA70D5A25F67A61A2FE2DE0112965AC6B543DCE26BBE8F74FF7445A6CA`；`trigger-base-parse.txt` `B740501DF7F9AB4C03D122EBC9F73A17278E1567649C42D67668C0F33105790C`。
