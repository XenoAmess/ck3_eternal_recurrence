# 宣战关系网络共同门：规则加载与 scope 绑定

本包闭合 [关系网络专题](war-film-declaration-relationship-network-2026-09-23.md) 保留的一个缺口：
`0x1B35DF0(root, candidate)` 的共同门确实加载并求值原版 `can_potentially_call_ally`。
它使用 `root` 作为 `WARRIOR`，将候选角色绑定为 `scope:ally`，即 `JOINER`。
证据限于 CK3 `1.19.0.6` 的精确 EXE 和下列原版文件；没有启动、注入、连接 pipe 或读取游戏进程。

本包有 **5 条 static-confirmed、2 条 unknown、0 条 live-confirmed**。
这是本包声明的证据边数，不是关系网络、外交 AI 或整个决策树的完成百分比。
旧关系网络九件保持冻结；本文追加新的加载证据和一个具体读表勘误。

## 身份与证据

- EXE：95,206,008 bytes，SHA-256 `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`。
- [先行计划](research-plans/war-film-relationship-gate-20260923-r1/plan.json) 与
  [初始检查](research-plans/war-film-relationship-gate-20260923-r1/check.json)。
- [静态合同](research-plans/war-film-relationship-gate-20260923-r2/static.json)：19 段连续、完整解码的指令区间，
  每段含原始 bytes、RVA 和 SHA；同时保存实际 token 行、虚表、源文件 SHA 和源码摘录。
- [结果计划](research-plans/war-film-relationship-gate-20260923-r2/result-plan.json)、
  [检查结果](research-plans/war-film-relationship-gate-20260923-r2/check.json)、
  [同源图](research-plans/war-film-relationship-gate-20260923-r2/graph.md)。
- `game/common/scripted_rules/00_rules.txt:846–856`：SHA-256
  `f47917fe70afc416a536096e8e051287af567c807a90a43b2e974e8412b495bc`。
- `game/common/scripted_triggers/00_war_and_peace_triggers.txt:166–221`：SHA-256
  `4e3d7db2931b313f132d5228babdbb60a67dd28e9898a337be78b2fc1def862e`。

## 从规则名到实际消费地址

| 阶段 | 精确指令或数据 | 闭合内容 |
| --- | --- | --- |
| lexer 名字注册 | `0x42C7830` 的 16 字节为 `2935000000000000c83b2a4401000000` | `{token=0x3529, pointer=module+0x42A3BC8}`；指针指向 `can_potentially_call_ally` |
| 读表布局 | `0x3B580E2` 读 `[r15-8]`，`0x3B580E9` 读 `[r15]`；`0x3B58279–0x3B58294` 按 token 写字符串索引 | token 在名字指针之前。循环每次前进 `0x10` |
| 游戏规则注册 | `0x1B34AA8` 写 index `0x1D`，`0x1B34AB0` 写 token `0x3529`；`0x1B34ABF` 写 scope kind `4` | 第 29 项与这个具体规则名正式相连；不是相似文本推断 |
| 注册表进入脚本系统 | `0x203D340 → 0x1B34610`；`0x203D34D → 0x2043010`；`0x203D51D → 0x332C380` | 本地三字段表进入 setup 对象 `+0xD0` |
| 注册表进入 loader | `0x332C579–0x332C587` 复制 setup `+0xD0`；`0x332C6DF–0x332C6F4` 复制到全局 `module+0x576AF88` 所指对象 `+0xF0` | `0x33ED7E0` 随后把这张表复制到规则 singleton `+0x2B30` |
| 读取原版规则目录 | base constructor `0x33EDE95` 写入 `common/scripted_rules`；load `0x33ED806 → 0x33EF390`；虚表 `+0x38 → 0x33EE960` | 逐文件、逐条解析该目录；`0x33EF0D0` 使用解析条目，按其虚表读规则正文 |
| 后置绑定数组 | `0x33EDB48` 取注册 token，`0x33EDB4C → 0x3B58970` 还原名字，`0x33EDB7D` 取名字 hash，`0x33EDB87 → 0x33EEF90` 查已解析对象 | 同一个查找 helper 也被 `0x33EFA56` 的条目创建/查找路径使用 |
| 复制到消费槽 | `0x33EDDAD–0x33EDDC5`：`array + index * 0xE0` 接收解析对象 `+0x38` 的 trigger 数据 | `29 * 0xE0 = 0x1960`；另复制 `+0x50`、`+0x98` 的附加数据 |
| 共同门消费 | `0x1B35E35 → 0x1B36670`，读 singleton `+0xF08`，加 `0x1960`，`0x1B35E4D → 0x334C510` | 同一个数组第 29 项成为候选共同门的布尔求值对象 |

正确规则 singleton 槽为 **`module+0x57C2060`**。它的 `+0xF08` 是一个 stride `0xE0` 的对象数组指针；
`+0x1960` 是该数组第 29 项的位移。它不是另一种对象中独立命名的硬编码成员。
加载器在缺少定义时另有日志和默认构造分支；本包证明正常定义如何绑定，并没有观察本次游戏内加载是否成功。

## scope 方向与默认原版内容

`0xC060` 用字面量 `ally`（RVA `0x4095988`）注册命名槽 `module+0x57EB86C`。
`0x1B35E00–0x1B35E08` 用第一个角色参数构造 root context；
`0x1B35E18` 读取第二个参数的完整 CharacterID `+0x18`，加 kind `4`，
然后 `0x1B35E25–0x1B35E30` 用该命名槽绑定候选。
因此这里的 `ally` 是传入的候选，不是玩家、战争另一方或另一个全局角色。

原版规则正文把参数交给：

```text
can_potentially_call_ally_trigger = { WARRIOR = root JOINER = scope:ally }
```

令 `W` 为本次 actor 或有效 target，`J` 为当前候选，脚本的两组检查均需通过：

| 检查 | 原版默认条件及例外 |
| --- | --- |
| J 是 W 的下级 | 通常要求 J 的 `target_is_liege_or_above = W` 不成立。若 J 就是 W 的 `diarch`，或 J 满足 `is_confederation_member` 且 W 属于 J 的 confederation，则此组的普通上下级排除不执行 |
| J 是 W 的上级 | 当 J 的 `target_is_vassal_or_below = W` 成立时，W 需有 `vassal_contract_liege_forced_war_override`；不是该上级关系时，这一组直接通过 |

这是具体脚本文本的语义整理。内部 `target_is_*`、契约和 confederation trigger 的所有 native 实现没有在本包逐个重追。
尤其原版注释写了 confederation leader 的“defensive wars”，但本段条件本身只检查角色关系与成员资格，
**没有读取当前战争、防守方或 CombatID**。不能用注释给共同门补上一项战争侧别判定。

影片可以说明：关系候选先过“潜在可召战”的共同门，再过 actor 端额外过滤；
不能说存在婚姻、联盟或 confederation 关系就必然计入。
上一专题已闭合的 actor 在战、人类玩家、同 confederation、特定 suzerain 排除继续适用。
共同门通过也不保证之后接受召战、实际出兵或加入同一场战争。

## 勘误、已排除路径与停止条件

前一轮探索把 `0x42C7838` 字符串指针后面的 `0x352A` 当作该字符串 token。
真实 initializer 证明 token 在指针之前，正确值是 **`0x3529`**；
`0x352A` 属于下一行。因此，先前“未找到 0x352A 的真实注册指令”不能否定本规则的实际注册。
旧专题只将名字保留为 unknown，没有把那个错误候选写成已确认语义；新证据在这里追加，旧包不回写。

已经排除：`0x99CF02` 的调用位移内字节、`0x43CBC74` 附近的无关 modifier descriptor、
其他对象/UI 对 `0x1960` 的访问，以及仅匹配 `scripted_rules` 后缀的目录字符串。
这些路径不会再作为该绑定的候选入口重复扫描。

名字、注册索引、loader 拷贝与 scope 方向已经达到先行计划的停止条件。
仍未知的是当前进程实际规则对象/覆盖集合、共同门的运行结果与后续参战结果，
以及每个嵌套 trigger 的完整 native 实现。本包在此停止，不扩大到整个外交或进行实机实验。

## 一次离线复现

使用本隔离 worktree 的 `tools/.venv/Scripts/python.exe`（Python 3.14.7、capstone 5.0.9、pefile 2024.8.26）。
输出目录必须尚不存在；工具默认不改任何旧计划、ABI、游戏文件或证据。

```text
tools\.venv\Scripts\python.exe ck3_autonomous_player/native_bridge/research/war_film_relationship_gate_extract.py --output-dir D:/workspace/ck3_war_film_research_20260923/relationship-gate-reproduce-r1
py tools/native_research_plan.py check D:/workspace/ck3_war_film_research_20260923/relationship-gate-reproduce-r1/result-plan.json
```

复现结果与入库 `static.json`、`result-plan.json` 精确 bytes 相同；初始/结果计划检查、图生成、LF、
本专题相对文件链接和 Python 语法的检查收据保存在外置
`D:/workspace/ck3_war_film_research_20260923/relationship-gate-r1/validation-receipt.json`。
计划工具只检查声明与证据字节，不会替代上述静态解释或证明 live 成功。
