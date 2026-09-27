# 败方战分 trigger：被动探针 ABI 与身份预检

日期：2026-09-27。这是 [单场战分比较器补证](warscore-trigger-generic-ge-and-loaded-node-gap-2026-09-27.md)之后的一步**纯静态**预检；没有启动或附加 CK3，也没有安装 hook。目标 EXE 是 CK3 1.19.0.6，SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；原版 `combat_on_actions.txt` SHA-256 `B35D696F472E801BB332D7204AA46008349E8AFBFDB38985C781EB099BBFB233`。

## 已证的入口和取数时点

Windows x64 调用现场：RVA `0x230B0AD` 从 loaded effect database `+0x260` 取得败方 effect **根指针**，而 `0x230AFF4` 的 `+0x258` 是胜方根。`0x230B0E3–0x230B0EE` 设置 `R8=&[rsp+0x50]`、`RDX=败方根`、`RCX=RDI`，再调用通用 effect dispatcher `0x33F8350`；紧接着的返回位置是 `0x230B0F3`。这为“正在 dispatch 败方根”的**调用范围**提供精确锚点，但不是其中某一条子脚本的身份。dispatcher `0x33F8633→0x33F8653` 还会从当前根 `+0x348` 读取子节点并递归调用自身，所以简单的败方范围标记包含更深层调用。

`CCombatWarscoreTrigger` 的通用比较函数 `0x99F920` 使用 Windows x64 ABI：入口 `RCX=trigger`、`RDX=求值上下文`；`0x99FA6D` 通过虚表 `+0x100` 把 LHS 写入当前栈帧 `[rsp+0x298]`。`0x99FA77` 若发现 trigger `+0x120==2` 会转入另一分支，因此不能在函数入口假定 RHS 已求值。普通分支 `0x99FAA9` 调用 RHS 表达式 evaluator，`0x99FAAE` 从 trigger `+0x50` 读取操作码；当操作码为 `0x3CB`，`0x99FAED` 已把 RHS 原始 qword 读入 `RAX`。因此在 **RVA `0x99FAF0` 指令执行前**，该分支上 `RBX=trigger`、`[rsp+0x298]=LHS raw`、`RAX=RHS raw`，随后 `cmp` / `setge` 给出包含等号的 signed 比较结果。这是最小、无需再调用原生 evaluator 的**候选取数时点**；探针若未来获准实现，只能同步复制标量到容量受限的缓冲区，不能保留栈地址或调用原生函数。

## 当前无法绑定具体脚本实例的原因

本安装的原版 `combat_on_actions.txt` 中，`combat = { warscore_value >= 15 }` 和 `warscore_value` 字符串都只出现一次；这只说明**磁盘文件文本**中的唯一性。它不证明实际 VFS 装载来源，也不排除败方 effect 期间递归触发其他脚本的同类 trigger。

更重要的是，trigger `+0x08` **不能**充当脚本行号或节点唯一键：注册路径 `0x53C3E6` 将 `warscore_value` 注册 key 写入 registry entry `+0x10`；工厂 `0x284F63E→0x284F641` 又把该 entry `+0x10` 复制到每个此类 trigger 的 `+0x08`。现有静态证据没有从 `0x230B0EE` 的败方根指针到 `0x99F920` 的具体 `RBX` trigger 指针的唯一父链/定义位置映射。`vtable=0x437D490`、操作码 `0x3CB`、RHS `1,500,000`、处于败方 dispatch 范围，即使组合起来也只是**候选过滤条件**，不能代替节点身份。

因此本轮明确**拒绝安装或解释为权威的比较器归因 hook**。否则可能把别处的 `warscore_value` 命中错记为原版败方第 563 行的求值；没有命中也可能只是前置脚本门未通过，而不是阈值逻辑不存在。

## 下次受管同场采样的放行门

1. 冻结 EXE/DLL 和实际 VFS 载入的 `combat_on_actions.txt` 来源与 bytes，确认与计划的脚本一致；同时冻结 CombatID、WarID、败方身份和日期。
2. 先用**只读**解析期来源位置/definition key，或经另行核实的 loaded effect 树父链，从 `database+0x260` 的败方根唯一走到该 `combat = { warscore_value >= 15 }` 的 trigger 指针。需要保存父链、节点指针、vtable、来源文件/行的同场原始证据；不能把 `+0x08` 注册 key 当成位置。
3. 只有该指针已唯一绑定，才考虑在 `0x230B0EE` 到 `0x230B0F3` 的**同线程**败方范围内，于 `0x99FAF0` 的已求值分支被动复制 `RBX`、`+0x50`、LHS/RHS raw；节点指针必须精确相等。记录应有容量上限、溢出拒绝、配对退出/异常清理，不调用 evaluator/mutator；出范围后不解引用任何暂存指针。
4. 对照 `CCombatResultData+0x40` 和 effect 前后 postcondition 时使用同一 CombatID/WarID/date。来源、父链、节点、时序、取数任一不一致即 RED；未进入比较分支则保持 inconclusive。

## 复核

[静态 verifier](../../ck3_autonomous_player/native_bridge/research/verify_loser_warscore_probe_abi_static.py)校验 EXE/原版脚本 SHA、唯一文本声明、23 个机器锚点和败方 call 目标；通过时仍明确输出 `loaded_loser_trigger_node_bound=false`、`authoritative_attribution_hook_install_ready=false`。

```text
<verified-python> ck3_autonomous_player/native_bridge/research/verify_loser_warscore_probe_abi_static.py --exe <exact-ck3.exe> --on-action <exact-combat_on_actions.txt>
```

仓库外原始反汇编位于 `D:/workspace/ck3_native_war_ai_promo_work/normal-result-trigger-abi-static-20260927/`，分别为 `loser-call-site.txt` SHA-256 `6034FAD8C8E359919CE95921932527190B44DEFFE03F48C3D524F83445CA8CFD`、`effect-dispatcher.txt` SHA-256 `2A05438E5E64709E2881E013032DDA338AA413DE4AA1EE13CA9BB52C8A9B63FE`、`trigger-compare.txt` SHA-256 `01F37B22745980FACF0E033A4C1986B8D97C4E5FBA924C2ADCE0B38F120C8FB1`、`trigger-factory.txt` SHA-256 `5B0012052232E224D1B9B5B5307A6D734CC46B3C66E73C57AE28CFE2C2FFD615`、`trigger-registration.txt` SHA-256 `0E4AB4977933DE367EDE5A32B41B5A653EDF2CBB316270DB56796074528820C3`。这些是有限反汇编证据，不是运行时 loaded node 的转储。
