# 战争影片补研 a03：战争分数方向与 desperate 比较

日期：2026-09-23。固定 CK3 **1.19.0.6**，EXE SHA-256
`2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`。
本包实际读取本地 EXE 的注册、vtable、原生 UI consumer、角色生产者和指令分支。
**零游戏启动、零注入、零进程采样、零新增影片实机素材**；a01/a02 的文件与哈希保持冻结。

## 结果

1. **[static-confirmed] `0x222A8A0` 返回 attacker 视角的整数战争分数。**
   原生 `attacker_war_score` 直接使用它，`defender_war_score` 使用相反数。
   这次通过 EXE 的名称注册和实际 evaluator 绑定，未把旧文命名或 define 注释当证明。
2. **[static-confirmed] coordinator `+0x68 bit2` 表示本 coordinator 的 attacker 身份。**
   实际创建者检查传入 Character 的战争一侧成员关系，并把同一 Character 添加到 coordinator。
   `+0x1B38` 因此缓存己方分数：攻方为 raw，守方为 `-raw`。
3. **[static-confirmed] 普通守方的末端 desperate 分支确实是 `own_score >= threshold`。**
   没有 caller/GUI wrapper 反号可以把它改解释成“对方领先达到阈值”。
   它与原版 `00_ai.txt:1499–1500` 的文字说明存在差异；本包不把差异升级为已证实的游戏 bug，
   也不猜测开发意图、实际触发频率或所有局面的行为结果。
4. **[unknown] 普通战争的战中主动撤退 policy 仍未闭合。**
   额外展开的 `0x1851440` 是 `0x184D960` 调用的 cache 聚合入口；active-combat 的值在这里
   分流聚合输入，未形成 odds → 选择撤退 → 命令结果链。不能把它包装成新发现的撤退策略。

## 证据与复现

- 提取前计划：[war_film_retreat_plan_a03.json](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_plan_a03.json)。
- 审阅后的 source contract：[war_film_retreat_evidence_a03.json](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_evidence_a03.json)。
  包含逐指令摘录、名称与 vtable 原始数据、完整外置产物 SHA 和冻结来源快照。
- 结果计划：[war_film_retreat_results_plan_a03.json](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_results_plan_a03.json)，
  [检查收据](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_results_check_a03.json)，
  [同源图](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_results_graph_a03.md)。
- 复用 a01 的 [war_film_retreat_extract.py](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_extract.py)；
  本包新增 [literal locator](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_score_locator.py)
  和 [证据汇总器](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_freeze_a03.py)。
- 完整探索产物：`D:/workspace/ck3_war_film_research_20260923/retreat-a03/`。
  保存了没有命中的扫描，以及因 `--extent` 从 runtime-function 起点计算而未覆盖目标地址的初始窗口；
  它们是过程资产，不用于证明未实际读到的指令。
- 实际解释器：`D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`，
  已显式 probe 的 Python 3.14.7、capstone 5.0.9、pefile 2024.8.26；没有安装或改变依赖。
- `open_kaishek: not-applicable`：本包分析 EXE 角色与带符号算术，不执行脚本 runtime、存档回放或 CK3。

结构检查和哈希检查只证明文件、引用及 exact-build 定位；以下语义来自人工审阅指令。
它们不自动证明语义正确，不证明 producer 在一帧内运行过，也不构成 live readiness。

## 1. 原生 score trigger：名称 → 注册对象 → evaluator

| 链上节点 | attacker | defender |
|---|---|---|
| EXE 字面量 | `0x4375D58`：`attacker_war_score` | `0x4375D90`：`defender_war_score` |
| 名称注册体 | `0x53A510`；`0x53A521` 引用名称，`0x53A596` 写 token | `0x53A5B0`；`0x53A5C1` 引用名称，`0x53A636` 写 token |
| entry vtable | `0x4376F28`；`+8/+0x10 → 0x2849C00` | `0x4376F48`；`+8/+0x10 → 0x2849C10` |
| factory | `0x2849C00 → 0x284AA80` | `0x2849C10 → 0x284AAF0` |
| instance vtable 写入 | `0x284AAC1/0x284AAC8 → 0x43772E0` | `0x284AB31/0x284AB38 → 0x43771D0` |
| evaluator slot | instance `+0x100 → 0x284B8D0` | instance `+0x100 → 0x284B950` |
| 返回转换 | `0x284B928 → 0x222A8A0`，有符号扩展后乘 100000 | `0x284B9A8 → 0x222A8A0`；`0x284B9AD: neg eax`，再有符号扩展、乘 100000 |

所以整数 `raw` 与两个原生命名值的关系是：`attacker_war_score = raw`、
`defender_war_score = -raw`。trigger 的 Q100000 转换只改变单位，未交换方向。
`0x222A8A0` 自身的分项、特殊返回与 `[-100,100]` clamp 已保存在 a01；本包不另造分数公式。

## 2. 真正的攻守方与 coordinator 的身份

### primary scope 与 UI 互证

`primary_attacker` 字面量 `0x41D94C8` 经注册体 `0x329430` 绑定 vtable `0x41D99F8`；
其 `+0x20` evaluator `0x19DAD10` 在 `0x19DADC2` 读取 `CWar+0x288`，再完整校验 Character ID。
`primary_defender` 字面量 `0x41D9518` 经 `0x329500 → 0x41D9A70`，
evaluator `0x19DABC0` 在 `0x19DAC72` 读取 `CWar+0x28C`。

原生 UI helper `0xC568A0` 独立将这些 primary 与成员数组分组：

| 当地玩家身份 | 判断点 | role | `0xD5D720` 的符号 |
|---|---|---:|---|
| `CWar+0x288` primary attacker | `0xC568E8..0xC56901`、`0xC569DD..E4` | 1 | `raw * 1000` |
| `CWar+0x28C` primary defender | 同上 | 2 | `raw * -1000` |
| `CWar+0x20` 成员 | `0xC56913..26`、`0xC569D4..D8` | 3 | `raw * 1000` |
| `CWar+0x80` 成员 | `0xC5691F..34`、`0xC569D4..D8` | 4 | `raw * -1000` |

`GetWarScoreFraction` 名称注册 `0xB4380` 把 callback 指向 `0xD5FA70`，
在 `0xD5FA87` 调 `0xD5D720`；另一注册 `0x2AE5B0 → 0x16B1070`，
在 `0x16B1087` 调 `0x16AFCC0`。后者直接检查 `CWar+0x20` 成员关系：
`0x16AFD0C` 为真时 `0x16AFD22` 乘 `+1000`，为假时 `0x16AFD33` 乘 `-1000`。
这是静态 GUI consumer 互证，不是本轮实际打开了战争面板。

### 实际角色生产者 `0x1885440`

输入为 manager、`CWar*`、`Character*`。从传入 Character 的 `+0x18` 读取完整 ID：

1. `0x18854C7 → 0x2224870(CWar+0x20, CharacterID)` 为真，`0x18854D0` 置 `r12b=1`。
2. 否则 `0x18854DF` 必须确认同一 ID 在 `CWar+0x80`；都不在则返回。
3. `0x188561A..1E` 写 `coordinator+0x1C = War full ID`。
4. `0x1885621..38` 清除旧 bit2，再把 `r12b << 2` 写入 `coordinator+0x68`。
5. `0x1885780..57C9` 把同一 Character ID 加入 `coordinator+0x20` 数组。

故这不是“缓存对手身份”的 bit。构造函数 `0x1852400` 清零 flag；
`0x1854180` 是加载记录时恢复字段的路径，不能拿它代替实际角色生产者。

## 3. 符号矛盾如何收敛

cache=`coordinator+0xB60`，`cache+0xFF0` 回指 coordinator。
`0x184DDFC..0x184DE10` 从回指读取 bit2 并计算 `2*bit2-1`；
`0x184DE24` 调 getter；`0x184DE29` 乘该符号；`0x184DE2D` 写 `cache+0xFD8`。

```text
bit2 = 1  # 自己是 attacker
coordinator[+1B38] = attacker_war_score

bit2 = 0  # 自己是 defender
coordinator[+1B38] = -attacker_war_score = defender_war_score
```

在 a01 已还原的普通战争路径中，只有守方继续到最后分数判断。
它仍有 `A < B`、多 stack 时的 `.75`、realm-size 等前置条件，不能删掉这些条件只讲分数。
末端 `0x186B578` 是 `cmp [coordinator+0x1B38], r9d`，
`0x186B57F: jl false`；不小于则在 `0x186B581` 返回 true。
对应未经 mod 修改的 define 数组为 realm `[5,10,15]`、warscore `[25,50,75]`。

仅用于说明符号的代入例子：其他前置条件已通过、选中门槛为 25 时，
`attacker_war_score=-25` 使 defender cache 为 `+25`，通过末端判断；
`attacker_war_score=+25` 使 defender cache 为 `-25`，不通过。
**这是指令算例，不是已观察到的 AI 选择。**

原版 `game/common/defines/ai/00_ai.txt:1499–1500` 将该门槛描述为 opposing/attacker 分数。
源文本 SHA 为 `c78f9cd8df9938cc9f38e817bcb6e32cd13720b5bd9de077b85e3e1c6f030293`。
本轮已闭合“原始总分方向”和“己方缓存方向”，不再要求 live 才能判断这两个静态映射；
仍不能仅凭这点断言注释错误的成因、设计意图或实际游戏频率。

`0x18AF340` 是数组长度检查，不是反号函数。加载后的数组是否被 mod 改写、特定存档中缓存是否新鲜，
仍属于会话证据；本包的原版数值与静态入口不能替代这些证据。

## 4. 一次有界的 active-combat 上游补查

完整提取 `0x1851440`；direct-call census 找到 `0x184DCD9`，位于 cache updater `0x184D960`。
该入口遍历 Character 的 Unit ID 容器，`0x1851642` 调 `0x2248A80`，保存 active-combat 布尔值。
`0x18519E1..0x1851A36` 用该布尔值把数值分到不同临时聚合槽；
随后 `0x1851A71/0x1851A90` 调聚合 helper。这里没有找到已归因的战中撤退命令。

此结论限定于已读入口和直接引用；没有递归穷举所有 indirect/vtable 路径。
a02 对 raid/barter 主路径 active gate 的勘误继续成立，counterraid 路径未被否定。
normal/desperate 选择接战门槛也仍不等于主动撤退策略。

## 后续最小实验

无需再为总分方向重复扫 EXE。下一次获协调者安排的同一会话，可复用 a02 的 research-only paused sampler：
绑定 CUnit/Character/War/coordinator 的 full ID 与双方身份，记录原生战争面板视角、total score、
bit2/bit4、`+0x1B38/+0x1B58/+0x1B60`、realm size、runtime define 与缓存计时器。
两次暂停快照一致只证明读取稳定，**不证明 mode producer 运行**。
真实解释一次变化仍需要自然推进窗口中的 producer 前后记录，再将 threshold 变化与目标/动作结果分开验证。

若下一包继续纯静态撤退研究，应沿 a02 保留的 move-command virtual dispatch 与普通战争 active 调度
恢复新的策略 caller；不能用本包的 cache 分类冒充该 caller，也不能据此宣称 AI 永不主动撤退。

本包一次 scoped 验证覆盖：新文件 LF/JSON/AST、所有索引产物 bytes/SHA、a01 七文件与 a02 八文件不变，
以及结果计划 check/render。收据保留为外置 `retreat-a03/scoped-review.json`；不重新运行 a02 synthetic tests。
