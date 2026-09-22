# 战争影片补研：原生白和的发送调度与实际接受比较（2026-09-23）

本轮是 CK3 **1.19.0.6 的只读离线研究**。没有启动、附加或调用 CK3，没有新实机帧、自然白和案例或 action postcondition。没有修改既有专题或影片结论。目标是把“想提出”“预判可继续”“发送命令决定接受”三件事接到真实 native consumer。

## 结论与本轮增量

1. **原版普通白和的收件人接受比较是 signed `raw > 0`，等于零不通过。** `raw` 是 Q100000 接受分，不是百分比。既有 [war-termination.md](war-termination.md) 已记录预判比较；本轮独立复验，并补到发送命令实际消费者、字段解析和白和定义的默认标志。
2. **`0x2C43B40` 的 `status != 2` 不可推广成所有交互的实际接受结果。** `status 1` 包含随机接受和谈判入口；真正发送命令还能抽样或进入拒绝后的谈判。普通白和没有启用这两个标志，故不能拿通用例外否定其普通严格正分路径，也不能拿白和的普通路径代替所有交互。
3. **找到生产调度链，而非 GUI 或 CSV 诊断入口。** `0x18876D0 → 0x183DEC0 → 0x18813E0 → 0x1880C20` 读 tier 对应的月份频率、以角色身份错开月份，再准备候选和 context，经过接受预判、主动意愿随机筛选、CanSend，构建并分派 `CSendCharacterInteractionCommand`。
4. **`ai_will_do` 不是 `ai_accept`。** 此生产候选循环将主动意愿截为整数后减去 `0..99` 的随机整数，保留严格大于当前最佳值的候选，最佳值初始为零。它既有不发送的可能，也有多收件人间的竞争。不得说“接受分为正，所以 AI 现在一定主动白和”。
5. 白和脚本的 county–hegemony `12` 是考虑频率的月份参数，barony 为 `0`。本轮闭合的是 native 月份筛选和真实发送链；**尚未闭合上游 actor 工作列表的入队/重建时间，不能据此许诺每 12 个月的某一天一定发出一次提议。**

## 固定输入与可复现材料

| 输入 | 精确身份 |
|---|---|
| `ck3.exe` | 95,206,008 bytes；SHA-256 `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86` |
| 实际读取路径 | `C:/SteamLibrary/steamapps/common/CRUSAD~1/binaries/ck3.exe`；根线程另有同 hash 的 `D:/Crusader Kings III^/binaries/ck3.exe` 身份收据 |
| 原生脚本 | `game/common/character_interactions/00_war.txt`；完整文件 hash、白和块归一化 hash 与顶层字段保存在字节摘要 |
| 白和定义 | `end_war_attacker_white_peace_interaction`，1002–1920；`special_interaction = end_war_white_peace_interaction` |
| 解码环境 | 本 worktree `tools/.venv/Scripts/python.exe`；Python 3.14.7，Capstone 5.0.9，pefile 2024.8.26 |

跟踪材料位于 `ck3_autonomous_player/native_bridge/research/`：

- `war_film_peace_plan_20260923.json`：提取前冻结的研究合同；原始 unknown 不倒填成事先已知。
- `war_film_peace_extract.py`：exact-EXE SHA 门槛、PE `.pdata` span、direct call/jmp、限定 RIP/string locator、显式 leaf/data window 提取；输出目录必须不存在。
- `war_film_peace_summarize.py`：逐 span/指令复验实际 EXE bytes；token 表、解析跳表和命令 RTTI 绑定；没有执行游戏或模拟 native 决策。
- `war_film_peace_bytes_20260923.json`：26 个 `.pdata` span 的身份、753 条选定指令、脚本顶层字段、跳表/RTTI/显式窗口和原始提取 SHA。
- `war_film_peace_frequency_fields_20260923.json`：后续补追频率 loader 和 tier getter 的独立原始提取。
- `war_film_peace_result_plan_20260923.json` 及生成 graph/check：本轮结论与剩余 unknown；文件 hash 检查不宣称语义自动证明。

完整 `.asm` 与 `extract.json` 保留在 `D:/workspace/ck3_war_film_research_20260923/peace-policy/`。`final-extract-r1/` 是主冻结提取，`frequency-fields-r1/` 是新增频率字段问题的补充。探索过程的成功目录没有改写。几次请求没有 `.pdata` 的 leaf/data 地址被工具明确拒绝；后来使用显式窗口，未把窗口边界谎称为函数边界。

重现摘要（输出路径须换成不存在的新文件）：

```text
tools\.venv\Scripts\python.exe -B ck3_autonomous_player\native_bridge\research\war_film_peace_summarize.py --exe C:/SteamLibrary/steamapps/common/CRUSAD~1/binaries/ck3.exe --extract D:/workspace/ck3_war_film_research_20260923/peace-policy/final-extract-r1/extract.json --war-script C:/SteamLibrary/steamapps/common/CRUSAD~1/game/common/character_interactions/00_war.txt --output D:/workspace/ck3_war_film_research_20260923/peace-policy/summary-reproduction-new.json
```

从 EXE 重做完整提取时，使用字节摘要 `extract.args` 中全部 `rva/call_target/window/data_window` 参数，传给同目录的 `war_film_peace_extract.py`，并指定一个新 `--output` 目录。这些参数是已执行输入，不是待实现的 CLI。逐条解释见下文；提取器的 “instruction boundary” 只指在线性 `.pdata` 解码中识别到该位置，仍须人工核对控制流。

## A. 白和到底启用了哪种接受模式

[static-confirmed] 原生 token 表以 **ID 在前、字符串指针在后**排列。不能把字符串之后的下一个 ID 当成该字符串的 ID。

| key | token | parser 路径 | definition 字段 |
|---|---:|---|---|
| `ai_frequency` | `0x770` | `0x2C3968D` 的减法分派 → `0x2C396A9` → `0x2C46C60` | `+0x29FC` 频率对象 |
| `ai_frequency_by_tier` | `0x3C29` | `0x2C3B2A1` 相等跳至 `0x2C396A9`，同上 | 对象 `+0x10` 起七个 int32，即 definition `+0x2A0C` |
| `ai_maybe` | `0x3168` | byte table `0x2C3B61C` index 0；target table `0x2C3B5DC` → `0x2C3A852` | `+0x2A58` |
| `ai_accept_negotiation` | `0x326A` | byte table `0x2C3B730` index 3；target table `0x2C3B714` → `0x2C3AAD9` | `+0x2A55` |

这里 parser 的 `this/R15` 是 definition `+0x2A80`：构造器 `0x2C3860F` 绑定 vbtable `0x43F5998`，实读 signed dword 为 `[-8, 0x2A78]`，加上 vbptr 自身 `+8`。故 parser 的 `R15-0x28/-0x2B` 正是上述两个 bool，不能把负偏移误认为另一个对象。

[static-confirmed] 构造器 `0x2C39196` 写 `qword [+0x2A50]=1`，`0x2C391A1` 写 `dword [+0x2A58]=0x100`，所以 `+0x2A55` 与 `+0x2A58` 默认均为零。白和块的顶层字段扫描确认没有 `ai_maybe`、`ai_accept_negotiation`、`auto_accept`、`send_option`、`ai_intermediary_accept`；这不是靠注释猜默认值。其 `ai_targets` 明示 `primary_war_enemies`，频率表见 1014–1021。

此静态适用范围为冻结的原版定义。mod 覆盖、不同 build、不同 context（尤其人质交换、intermediary、玩家/作弊设置）须重新绑定，不得沿用为实机证明。

## B. 预判比较与发送时比较是两层

[static-confirmed] 收件人 raw evaluator `0x2C44320` 用 context `+0x2DC` 收件人，在 definition `+0x1BA8` 求 `ai_accept`；actor `+0x2D8` 与收件人相同则写 `10,000,000`。主动意愿 `0x2C44410` 则以 actor 求 definition `+0x1AE8` 的 `ai_will_do`。两者都调用 compiled value evaluator `0x337B210`，scope 与字段不同。

| 层 | 关键指令 | 精确含义 |
|---|---|---|
| 预判普通 recipient | `0x2C43DD4 call 0x2C44320`；`0x2C43DD9 mov rax,[rax]`；`0x2C43E1D test rax,rax`；`0x2C43E20 jle 0x2C43EAD` | signed int64 raw `>0` → status 0；`<=0` → status 2 |
| 预判随机标志 | `0x2C43DF8` 检查 `+0x2A58`；`0x2C43E01 cmp raw-1,0x98967E` / unsigned `jbe` | `1 <= raw <= 9,999,999` 时进入 status 1；不是已经抽中接受 |
| 预判谈判标志 | `0x2C43E0A` 检查 `+0x2A55` | 可进入 status 1；原版 info 96–101 说明拒绝后可能走 negotiation event chain |
| AI 候选消费预判 | `0x18BB077 call 0x2C43B40`，`0x18BB07C cmp al,2` | 无选项、非忽略接受的普通路径剔除拒绝候选；它是提议准备阶段 |
| 发送命令实际 recipient | `0x26B31DC test rbx,rbx`；`0x26B31DF setg r9b` | `RBX` 是命令携带的收件人 raw；普通路径严格 `>0` 形成 recipient bool |
| 发送命令随机 recipient | `0x26B31B5`–`0x26B31D6`：范围检查、`0xD9D530`、`cmp rax,rbx; setle r9b` | 启用 `ai_maybe` 且 raw 在 `(0,100)` Q 区间时，将一次原生随机整数与 raw 比较 |

`0xD9D530` 使用上下界差加一再取模，调用参数为 `0` 和 `10,000,000`；此处上下界均包含。不能把它强写成无限精度、恰好 raw/100000 的百分比概率。普通白和不进入此随机接受分支。

[static-confirmed] 发送命令的类型身份来自 RTTI：vtable `0x40829C8` / `0x40829F8` 的 COL 分别为 `0x45A02B0` / `0x45A02D8`，TypeDescriptor `0x513C108` 是 `CSendCharacterInteractionCommand`。`0x26B32D0` 从命令 `+0x340` 取 **intermediary raw** 到 RDX、`+0x348` 取 **recipient raw** 到 R8，以 command `+8` 为 context，调用 `0x26B30A0`。不要交换两名角色。

`0x26B30A0` 最后把 intermediary bool 放 R8、recipient bool 放 R9，尾调 `0x2752620`。后者还在 `0x275264D` 重跑 CanSend；普通非 auto-accept 分支在 `0x275287B` 保留 recipient bool，并于 `0x27528D9` 交给 `0x2752900`。所以本轮证明的是**真实发送路径的接受布尔及传递**，没有用这个离线布尔冒充某场战争已经结束。

外层 `0x2C43B40` 的 auto-accept/同人 shortcut、intermediary 和 status 3 仍须保留。它先求可能存在的 intermediary，再始终求 recipient；不是“只有 intermediary 同意才求 recipient”。intermediary 为 1 时使用 `0x4403A98` 表 `01 01 02 00` 合成；无 intermediary 时内部标记 3，使用 recipient 结果。状态 3 缺失态也不能被 `3 != 2` 机械宣传为接受。

对合法、普通 AI 收件人、无 intermediary 的原版白和，在本层可解释的边界值为：

| 收件人 raw | 显示分数 | 普通 recipient bool |
|---:|---:|---|
| `-1` | `-0.00001` | false |
| `0` | `0` | false |
| `1` | `+0.00001` | true |

这是指令边界的静态推导表，没有执行合成游戏案例。该接受 raw 也不是 `ai_will_do` 的整数抽选值。

## C. 生产机会入口、月份错开与主动发送

[static-confirmed] 可追溯生产路径：

```text
0x26D3E80 → 0x18876D0（AI 更新/工作列表消费）
  → 0x183DEC0（actor 工作项；受总开关与 actor 状态门约束）
    → 0x18813E0（tier 频率/月相位/可用性/本轮交互列表）
      → 0x1880C20（该定义的候选收件人和发送）
        → 0x1880B80 → 0x1880930 → 0x18BB040 → 0x2C43B40
        → 0x2C44410（actor ai_will_do）→ 随机 margin 竞争
        → 0x2C43F00（发送前合法性）
        → CSendCharacterInteractionCommand → 0x26B32D0 → 0x26B30A0
```

`0x18876D0` 的串行调用在 `0x18879AB`；并行 wrapper `0x1889E80` 尾调同一 `0x183DEC0`。`0x183DF47` 调 `0x18813E0`；另有 `0x1881310` 的列表入口进入同一候选流程。这里不把 debugger/forced single interaction 入口当自然调度，也不使用 `0x19126D0` 的 `ai_interactions.csv` 诊断来证明发令。

[static-confirmed] 频率字段的数据链：definition `+0x29FC` 的构造函数 `0x25D4170` 接收两个 token `0x770/0x3C29`，值数组为对象 `+0x10`。reader `0x2C46C60` 按 token 路由到 `0x25D4220`（统一频率）或 `0x25D4450`（tier 表）。后者 `0x25D4484` 取数组 `+0x10`，终点为 `+0x1C`，即七个 int32；原版脚本的月份单位由 `_character_interactions.info:531–543` 明示。

`0x2C3E7FF` 是 `.pdata` 分段，不声称为独立入口。其 `0x2C3E875` 按 tier 检查同一频率数组，只有正值才在 `0x2C3E8C7/0x2C3E90D` 将 definition 指针追加进该 tier 的候选表。表首对应 database `+0x1170+tier*0x18`；`0x183DF32`–`0x183DF47` 计算并传入相同布局的表。因而白和的非零频率确实参与生产候选表，不只是一个未找到消费者的脚本字段。

[static-confirmed] `0x18813E0` 从 game date 得到月份序号 `M`：`0x188142A` 读 date，减 `0x29C55C0`，除 24 得 day，再以 365 日年和 `0x4043000` 月份查表得到 `12*year + month_index`。`0x188148B` 读 actor full CharacterID，再与 `M` 相加。`0x1881619` 读 `F=int32(definition+0x2A0C+tier*4)`；`F<=0` 在 `0x1881623` 跳过；否则 `0x1881631 idiv rcx`，`0x1881637` 在余数不为零时跳过。月相位门为：

```text
F > 0  且  (M + actor_full_CharacterID) % F == 0
```

这是每次调度访问时的门；没有证明上游何时把这个 actor 加进本轮列表。tier 普通 getter `0x2601F90` 有无头衔/备用头衔路径，`0x1881529`–`0x18815CE` 另有 tier 为 0 时的处理，不能把所有角色都假定为伯爵。原版白和 county/duchy/kingdom/empire/hegemony 同为 12，barony 为 0。

[static-confirmed] 月相位通过后，`0x188165E` 按定义的字段状态选择 `ai_potential` 或 `is_available` trigger 并在 `0x1881675` 求值，合格定义进入列表。`0x1881A32`–`0x1881A75` 做带随机下标的列表交换；`0x1881B1E` 逐定义调 `0x1880C20`。本轮没将列表打乱声称为按战争收益进行全局最优排序。

[static-confirmed] `0x1880C20` 用 thread-local context、definition、actor 初始化真实 context；按定义的 recipient 集合准备候选，有目标数量限制/过滤及候选机会门。进入 `0x1880F5F` 的候选调用链会填写 recipient、建立 special context、验证目标、处理 title/secondary/options 和接受预判。白和无 send options，故普通 `0x18BB040` 分支适用；特殊分支的完整一般算法不由本例外推。

已通过准备的候选在 `0x1880F74` 求 `ai_will_do`，`0x1880F7C`–`0x1880F97` 作 signed raw/100000 的向零整数截断。`0x1880FF0`–`0x1881001` 得到 `margin = integer_will_do - (random31 % 100)`；`0x1881006 jle` 拒绝不严格超过当前最佳 margin 的候选。最佳 margin 起始为 0；相同 margin 不替换先前候选。选中后仍在 `0x1881057` 跑 CanSend。

`0x18811AE` 与 `0x18811BA` 放入已由 RTTI 绑定的发送命令 vtable，复制 context，并把 intermediary/recipient raw 经 `0x28FA1A0` 写入命令；该 helper 保留普通 raw，但存在玩家/调试开关 override，不能省略为通用恒等函数。`0x1881232` 的 command 虚调用产生待分派对象，`0x1881257` 调 dispatcher `0x341D990`。这是实际命令链的静态身份，**不是本轮发出过命令的运行日志**。

## 仍未宣称闭合的部分与影片可用表达

| 问题 | 本轮边界 / 下一步 |
|---|---|
| 自然白和具体在哪一天发出 | AI manager 的 actor 工作列表创建、刷新和跳过周期尚未追完；已找到生产 consumer 与月份门，不能把 `12` 说成发送日倒计时 |
| 某场战争的最终接受数值 | 必须绑定同一真实战争、双方身份、context、special data、随机状态与实际原生求值；本轮没有 live score |
| 白和是否真正结束战争/交换人质/停战生效 | 接受布尔传入后续 manager 与 war special handler；要结合已存在的 outcome 专题和新授权的实机前后态，不由本包的离线 comparator 单独证明 |
| 玩家收件人、中介、mod 开启 ai_maybe 或谈判 | 必须保留分支；`status 1` 不保证实际接受。不能从普通无中介白和推广 |
| 其他外交交互或其他版本 | 只允许复用研究方法；地址、结构偏移、脚本默认和概率规则须重新绑定 |

影片可以说：“白和要分两张账：AI 是否想提出，与对手是否愿意接受。原版普通白和的接受分过零才通过，零分还不够；主动提议还有它自己的月份机会和随机筛选。看到接受分为正，并不意味着这一刻会主动求和。”

影片不能说：“所有原生交互只看分数正负”“status 1 就是对手已答应”“每年固定日期必定白和”“我们这次看到了 AI 自然求和”。本轮可配静态门槛图、真实指令证据卡与明确标注的教学算例，不能伪造自然实机因果。
