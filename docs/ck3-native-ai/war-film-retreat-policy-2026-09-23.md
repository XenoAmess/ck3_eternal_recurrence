# 战争影片补研：普通战争主动撤退与 normal/desperate 入口

本包日期：2026-09-23。范围固定 CK3 **1.19.0.6**，EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
本轮实际读取本地 EXE、PE runtime-function 表、指令与原版 define；**零 CK3 启动、零 live observation、零新增实机素材**。
本页独立追加，不改写既有专题的历史证据。

## 本轮结果

1. **[static-confirmed] 找到 normal/desperate 的实际生产谓词与写入链**：
   `0x185A270 → 0x186B310 → coordinator+0x68 bit4 → coordinator+0x88`。
   因而 [combat-prediction.md](combat-prediction.md) 中“完整上游尚未闭合”的下一入口，
   已收窄为下述可重演的 raw 分支树及其输入语义/实机绑定；不再只有 `.5/.4` 两个常数。
2. **[static-confirmed，限定两条调度路径]** 普通 representative 与 follower 移动分派都在
   active-combat predicate 为真时返回/跳过，不能拿这些路径证明通用战争 AI 的战中主动撤退策略。
3. **[unknown] 通用 war AI 的 battle-odds → 主动撤退选择仍未找到**。本轮 direct-call/absolute-pointer
   census 和局部 caller 展开不能证明不存在 indirect/vtable caller。
4. **[unknown，已定位矛盾]** desperate 的 warscore 分支实际比较 `cached_score >= threshold`；
   缓存写入包含攻守方符号变换。它不能直接按 define 注释配成“敌方领先，所以 AI 绝境”。
   需要下面列出的同一暂停帧身份/分数对账。

## 原始计划、工具与证据

- 初始计划：[war_film_retreat_plan_a01.json](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_plan_a01.json)。
  实际提取前由 `tools/native_research_plan.py check` 检查；初始收据在
  `D:/workspace/war_film_retreat_plan_a01.check.json`。
- 结果计划：[war_film_retreat_results_plan_a01.json](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_results_plan_a01.json)。
- 同一结果记录生成的图：[war_film_retreat_results_graph_a01.md](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_results_graph_a01.md)。
- 人工审阅的静态 source contract、逐指令摘录与外置产物哈希：
  [war_film_retreat_evidence_a01.json](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_evidence_a01.json)。
- 可复现提取器：[war_film_retreat_extract.py](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_extract.py)。
  只读磁盘，不启动/附加进程；exact EXE 不符直接失败；输出拒绝覆盖。
- 完整过程产物永久保留于 `D:/workspace/ck3_war_film_research_20260923/retreat-a01/`。
  其中 `array-registration-corrected.json` 的 SHA-256 为
  `BD6736D6547FC33A44404FEB9B4721A87B79BDDE6D1DA66F6E61E31228EFA66E`。
- 显式使用已先 probe 的主工作区解释器
  `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`：Python 3.14.7、
  capstone 5.0.9、pefile 2024.8.26。没有安装依赖或更改 venv。
- `open_kaishek` 本包为 `not-applicable`：研究对象是 EXE 调用/寄存器/内存字段链，
  未调用脚本 runtime、进行存档回放或运行游戏。

机器检查只验证计划结构、引用和文件完整性；反汇编提取只证明 exact-build 字节与定位。
下述分支语义是对这些指令的人工分析，不是工具自动证明，更不是 live readiness。

## normal/desperate：producer → caller → consumer

### 数据来源与缓存

| 输入/输出 | 本轮精确链 | 范围边界 |
|---|---|---|
| mode 更新 caller | `0x18552C6 → 0x185A270`；callee 在 `+0x2C == 0` 时早退 | tick、倒计时映射由并行 target 包负责；这里不重定义 cadence |
| A、B 两个 power qword | `0x185A2A0/+2A7` 读 coordinator `+0x1B58/+0x1B60` | 不是单场 encounter ratio，不是 UI 兵数或胜率 |
| A、B producer | `0x184D960` 在 flags bit2 下调用 `0x184C3B0/0x184C5D0`，在 `0x184DD9B/+DDDD` 写 cache `+0xFF8/+0x1000`；cache=`coordinator+0xB60` | 前者扫描 coordinator `+0x20` CharacterID 数组并累加匹配 WarID 记录的 `+0x40`；后者扫描 CWar 的一侧并有角色域 `+0x308` 回退。所有外交聚合含义仍需另外绑定，不能命名成纯兵数比 |
| GHW flag | `0x185A296..2C9` 读 `CWar+0x100 → CBType+0x1718 bit17` | 与现有 prewar CB 研究的 `is_great_holy_war` 绑定一致 |
| side bit | `coordinator+0x68 bit2` | helper `0x18557D0` 在 bit=true 时取 `CWar+0x288`，false 时取 `+0x28C`，并 generation-safe 解析 CharacterID；实际 AI 身份/立场仍需同帧对账 |
| stack count | coordinator `+0x5C` | 即 `+0x50` pointer array 的 count；不是单支军队士兵数 |
| realm-size 输入 | `0x186B51A → 0x18557D0`，返回 Character 的 `+0x1B8` 对象，其 dword `+0x1D0` | 字段通过 realm-size define 数组消费；本包无 live 对账 |
| signed score | `0x184DE24 → 0x222A8A0(war,nullptr)`，乘 `2*bit2-1` 后写 cache `+0xFD8`，即 coordinator `+0x1B38` | precise sign-transform 已确认；不得依据变量注释省略符号 |
| mode 输出 | `0x185A2D5` call 的 AL 写 `+0x68 bit4`，随后选择 `.5/.4` 并在 `0x185A309` 写 `+0x88` | 只选择接战门槛；不等于最终选择目标、接战或撤退 |

### define 注册与 executable consumer

| define | 原版值 | runtime global | 注册体 / 名称字符串 RVA |
|---|---:|---|---|
| `COMBAT_RATIO_THRESHOLD` | 0.5 | `0x570DF68` | `0x18AA320` / `0x4194F88` |
| `COMBAT_RATIO_THRESHOLD_DESPERATE` | 0.4 | `0x570DF18` | `0x18AA490` / `0x4194F60` |
| `GHW_ATTACKER_DESPERATE_THRESHOLD` | 0.75 | `0x570DF88` | `0x18AEFE0` / `0x4196088` |
| `GHW_DEFENDER_DESPERATE_THRESHOLD` | 0.5 | `0x570DF80` | `0x18AF150` / `0x4196060` |
| `IS_DESPERATE_REALM_SIZE_THRESHOLDS` | `[5,10,15]` | pointer `0x4F56778`、count `0x4F56784` | `0x18AF2C0`、array wrapper `0x18AF310` / `0x4196038` |
| `IS_DESPERATE_WARSCORE_THRESHOLDS` | `[25,50,75]` | pointer `0x4F56760`、count `0x4F5676C` | `0x18AF4D0`、array wrapper `0x18AF520` / `0x4196260` |

原版文本定位：`game/common/defines/ai/00_ai.txt:1190–1202,1475–1506`。
该文件 SHA 及所用行全文已进入 source contract。数组按 runtime stored order 消费，不能假定任意 mod 后仍是这些默认值。

### 已确认的 raw 决策树

下列 `qdiv` 指原生 Q100000 除法路径，不把它替换成浮点计算。
这是用于正常非负 power 输入的可读摘要；溢出处理和零分母 sentinel 的完整指令保留在
`producer-functions.json`，本包没有把极值分支写成 Python 可调用原生预测器。

```text
input A = coordinator[+1B58], B = coordinator[+1B60]
if signed(A) >= signed(B): return false                 # 186B32E..331
side_bit = (coordinator[+68] >> 2) & 1

if is_great_holy_war:                                  # 186B369..36C
    r = qdiv(A, B)
    if side_bit and r < GHW_ATTACKER_THRESHOLD: return true  # 186B426..431
    if r < GHW_DEFENDER_THRESHOLD: return true          # 186B437..43E

if side_bit: return false                              # 186B444..446
if coordinator[+5C] > 1:
    r = qdiv(A, max(B, 100000))
    if r > 75000: return false                         # 186B50E..515

leader = resolve_role_selected_primary_leader()         # 186B51A
if leader[+1B8] is null: return true                    # 186B526..529
size = leader[+1B8][+1D0]
if size <= 1: return true                              # 186B531..534

threshold = warscore_thresholds[last]
for i in stored_order(realm_size_thresholds):
    if size <= realm_size_thresholds[i]:
        threshold = warscore_thresholds[i]
        break                                         # 186B561..574
return coordinator[+1B38] >= threshold                  # 186B578..57F

# caller: true -> bit4=1 -> .4; false -> bit4=0 -> .5
```

明确的等号边界：`A==B` 不进入此 helper 的 desperate；GHW threshold 用严格 `<`；
普通分支的 `.75` 用严格 `>` 拒绝，所以恰 `.75` 继续；realm-size 档位用 `<=`；
最后 warscore 用 `>=`，恰 25/50/75 通过对应档位。
这些是本轮静态分析结论，尚不是游戏中的新实测案例。

### 分数符号为何必须先裁决

`0x184DE03..DE2D` 实际做 `score_raw = total_raw * (2*side_bit-1)`。
`0x186B578..B57F` 实际做 `score_raw >= threshold`；没有隐藏的取绝对值或随后反号。
`0x222A8A0` 自身按两侧 component 求差并 clamp 到 `[-100,100]`（`0x222AA22..AA35`），
其返回后在此 caller 中只有上述乘法。

既有 [war-termination.md](war-termination.md) 将 `0x222A8A0` 称为 attacker-relative，
而 `00_ai` 注释说 opposing/attacker war score 超过门槛。
若继续采用既有角色/正负命名，代码和这段注释不能直接拼成“处于败势才绝境”的解说。
本轮**不按注释改写 EXE 比较，也不把旧文名称当新的身份实证**；保留 exact raw tree。

最小裁决样本不是重打一局完整战争，而是同一 exact paused revision 下读取：

- coordinator/War 的 full generation IDs；coordinator CharacterID 数组；`CWar+0x288/+0x28C` 两位 primary 的真实身份与攻守方；
- coordinator `+0x68` 原值、bit2/bit4、`+0x88`、`+0x94`、`+0x5C`、`+0x1B38/+0x1B58/+0x1B60`；
- cache `+0xFF0` 回指 identity、被 `0x18557D0` 选中的 CharacterID、`+0x1B8/+0x1D0`；
- 同一 WarID 的现有受支持 total-score query，以及真实战争面板的攻守方/显示视角；
- CB stable key/bit17、当次 runtime define 数组。

暂停帧能裁决字段映射，不能证明新 producer 刚运行。解释一次 mode 切换还需要另行授权的自然推进窗口，
在实际 `0x185A270/0x186B310` 生产时记录前后 bit4、threshold 与这些输入；不用主动调用 mutating dispatcher。

## 普通战争主动撤退：本轮排除与新入口

| 实际检查 | 结果及边界 |
|---|---|
| `0x2308250` direct-call census | 再现 UI/validator/任务/terminal 等 direct references；不能从这些引用直接认定通用战争 policy |
| `0x2308850` apply xref | 两个直接调用点仍在 `0x26B4710`，证明通用 move apply 的 active-combat 分派，不证明谁决定撤退 |
| ordinary representative | `0x1872208` 调 `0x2248A80(CUnit)`，true 在 `0x187220F` 跳 `0x18726A0` 返回；位于后续 movement validation/route 构造之前 |
| ordinary follower | `0x1872916` 同 predicate；true 在 `0x187291D` 跳 `0x1872BB1` 跳过该 CUnit；后续 kind2 movement 在 `0x1872A00` 等处 |
| 新展开的 movement caller | `0x18793B0` 能走 `0x2248860 → 0x186B190 → 0x26B5080` 并提交 movement；它的 direct callers 为 `0x18CEF69/0x18CF127/0x18D14B9/0x18D15D9`。本包未将其归因为普通 war odds policy；目的省从 owner Character 的 `0x2606760` helper 得到，不存在本轮已证明的 battle-odds score |
| 另一个 caller | `0x184818D → 0x1874A10` 来自 stack 遍历；该分支仍需向上定位业务触发，不能因能构造 move command 就写成“判断败势撤退” |

`0x2248A80` 的实际 predicate 沿 CUnit `+0x178 → CArmy+0x128 → CCombat` 做 full-ID 校验与 validity test，
并要求 CUnit `+0x18==0`。本轮重新提取了该链；与
[battle-terminal-and-reentry.md](battle-terminal-and-reentry.md) 的旧研究一致。

本轮负结论仅适用于上述已枚举路径。下个最小静态实验优先追 `0x184818D` 的完整 parent/caller，
以及 `0x18793B0` 四个 caller 的任务来源；若都归入已有任务/重定位动作，再沿 move-command vtable
`0x432BF48` 与普通战争 active-combat 调度寻找未枚举的间接入口。不能把 direct-call census 的零新 policy
解释为“CK3 AI 永远不会主动撤退”。

## 复现与交付范围

```text
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe ck3_autonomous_player/native_bridge/research/war_film_retreat_extract.py functions 0x186B310 --exe C:/SteamLibrary/steamapps/common/CRUSAD~1/binaries/ck3.exe --output FRESH_OUTPUT.json
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe ck3_autonomous_player/native_bridge/research/war_film_retreat_extract.py refs 0x186B310 0x2308250 0x2308850 --exe C:/SteamLibrary/steamapps/common/CRUSAD~1/binaries/ck3.exe --output ANOTHER_FRESH_OUTPUT.json
py tools/native_research_plan.py check ck3_autonomous_player/native_bridge/research/war_film_retreat_results_plan_a01.json
py tools/native_research_plan.py render ck3_autonomous_player/native_bridge/research/war_film_retreat_results_plan_a01.json --output FRESH_GRAPH.md
```

完整实际 argv、解释器、依赖、EXE 哈希及每个产物的 SHA 已保留。输出含路径/argv 等环境记录，重跑不要求 JSON
字节相同；应复核同一 EXE 上对应 RVA 的指令及分支。`FRESH_*` 是调用者提供的新路径，不代表本包已存在的文件。

当前 `mode_selector_raw_static_ready=true`，`mode_input_business_mapping_complete=false`，
`mode_selector_live_ready=false`，`generic_active_retreat_policy_ready=false`。
影片可以据此规划有意义的取景：同一战争 AI 的实际 mode/threshold 改变及对应决策后果；
在取得案例前不能把本页图解冒充实机，或用玩家撤退命令证明 AI 自己作出了选择。
