# 战争影片研究：求援、原生指派与玩家支援（2026-09-23）

本包只做离线 EXE 分析和下一次实验的准备，未启动 CK3、未运行 live、未制造新存档。
现有专题与历史 RED 不改写。冻结对象为 CK3 1.19.0.6，EXE 95,206,008 bytes，
SHA-256 `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`；
原版 `game/common/defines/ai/00_ai.txt` SHA-256
`c78f9cd8df9938cc9f38e817bcb6e32cd13720b5bd9de077b85e3e1c6f030293`。
本次实际读取 `C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe`。

## 首先更正：跨 stack 需求比较的方向与等号

[旧专题](battle-reinforcement-and-join.md) 的跨 stack 小节把门槛写成
`available_power_raw > quantized(request_power_raw * ratio)`。**本次直接重读同 SHA 的 EXE 后确认这条方向和等号解释错误。**
这是静态勘误，不是新 live 成功，也不是游戏版本差异。

`0x1848570` 的候选处理末段实际为：

```text
0x1848869  mov rcx,[r13+0x40]       ; 候选 requester 的 parent
0x1848872  xor r8d,r8d             ; false
0x1848875  call 0x1847F70           ; requester parent available power
0x184887A  mov r8,rax
...                               ; rdx = demand*ratio 的原生量化值
0x18488A2  cmp rdx,[r8]
0x18488A5  jge 0x18488EA
0x18488A7  mov r13,[null-subunit]
...                               ; 继续扫描下一个 CUnit / Province
0x18488EA  mov rax,r13
0x18488ED  jmp 0x18488CF            ; 公共返回尾部
```

因此在前置候选条件都成立时，**`quantized_required >= requester_parent_available` 会返回该 requester，等号通过**。
`required < available` 才继续扫描。比较值来自请求方 parent，不是即将派出的助手力量。
不得把这条需求检查讲成“助手必须有需求 1.5 倍的兵力”或“已有力量必须严格大于门槛”。

仅为边界说明的假设数值：若量化后需求为 150，则 available 为 149、150 时返回候选，151 时跳过。
这些数值不是实测军队或胜率。倍率选择仍是原生默认 1.5、达到相应围城进度条件时 1.7；
不能把倍率、本比较和 asking 的 0.66/0.75 滞回门限拼成一个公式。

完整原始控制流见冻结证据 `cross-stack-gate`，包含比较、两条分支和返回尾部。

## 这次新增的 PLAYER_SUPPORT 消费边

以下均从定义名 → 注册参数地址 → 实际消费指令追踪。不是仅凭名字解释行为。
全局槽为模块相对 RVA；记录偏移属于相应函数的参数对象，**不是** `CAISubunitStack` 的同名字段。

| 原版参数 | 值 | 注册 / 槽 RVA | 消费点与本次闭合的边 |
|---|---:|---|---|
| `PLAYER_SUPPORT_WANTED_COMBAT_RATIO` | 5.0 | `0x18B01F3` / `0x570DEC0` qword | `0x184FE37` 读取；`0x184F9E0` 最终把 `max(0, fixed_mul(record+0x38, ratio) - record+0x18)` 写入 `+0x48`，`+0x60` 写需求是否大于零。不是 asking 概率阈值。 |
| `PLAYER_SUPPORT_ATTACK_TARGET_MAX_DISTANCE` | 400 | `0x18B0363` / `0x570DEBC` dword | `0x184F819` 读取并平方；`0x184F838..0x184F861` 计算坐标差平方和，`ja` 丢弃超限目标，等号不超限。不是最短路线步数，也不能直接称为公里。 |
| `PLAYER_SUPPORT_ATTACK_MAX_ARRIVAL_DELAY` | 45 | `0x18B06A3` / `0x570DF28` dword | `0x1857E35..0x1857E49` 把 45×100000 加到既有时间基准，以 signed `jle` 保留候选，等号通过。此前 `0x1857CA1..0x1857CBC` 用 `0x22475E0` 累加路线边时间。 |
| `PLAYER_SUPPORT_IGNORE_BAD_SUPPLY_WITHIN_STEPS` | 4 | `0x18B09E3` / `0x570DFD4` dword | `0x187231B..0x1872324` 比较 CUnit `+0x44` 路线数量；目标与当前移动目标相同、parent target 有效且 parent `+0x79` 不是 2/3 时，`count <= 4` 提前返回，避免进入后续供给/改道判定。不能无条件讲成四步以内免补给规则。 |
| `PLAYER_SUPPORT_ENEMY_POWER_MULTIPLIER` | 1.5 | `0x18B0D23` / `0x570DEC8` qword | `0x1850375` 读取，缩放此前算出的缺口，写 record `+0x1E0`。这里是玩家支援记录的消费点，不是 `0x1848570` 的 1.5/1.7 分支。 |
| `PLAYER_SUPPORT_MIN_SIEGE_STRENGTH` | 1.25 | `0x18B0E93` / `0x570DED0` qword | `0x185041C` 读取，与 coordinator `+0x7C` 的整数基数作定点运算；与已有整数数量比较后可增加 record `+0x1F4`，并参与 `+0x1F8` 的需求布尔值。基数的正式语义仍需闭合。 |

`0x184F2E0` 在 `0x184F7B7` 和 `0x184F88F` 调用需求计算 `0x184F9E0`，
分别传入缓存项 `+0xF8`、`+0x58`；缓存项由 `0x1860D80` 在调用对象 `+0x2A0` 的容器取得。
随后 `0x184F8C8` 调 `0x18500F0` 计算支援/围城需求，`0x184F8D3` 调 `0x1850530` 刷新 Province 记录。
后者把三个 Province 向量映射到记录 `+4` 的 1/2/3；`0x1869947..0x18699BF` 根据这个值加载分数并累加。
原版分数定义为 one/two/three step = 1000/500/250。这里不是距离排序后“最近一支军队必来”的保证。

仍未闭合：玩家支援缓存如何完整进入所有候选调度；时间基准 `record+0xE0/+0xE8` 的正式含义；
`CAISubunitStack+0x34/+0x38` 跨 coordinator 请求字段的实际 writer。
当前没有证据把上述玩家支援记录直接等同于这两个字段，也不能因此宣称普通 AI asking 可以由玩家控制军队触发。

## 为什么旧两军实验无效，新实验如何先过结构门槛

历史 v6 的 31 个暂停帧 / 30 天观察已有 typed native membership，但 requester 和撤离军各自的 parent 都是 singleton。
`0x1848326` 比较 parent `+0x4C` 与 1，`jle 0x18484F8` 进入清位分支；只有 count>1 才会在 `0x184835B` 调求援生产者 `0x1872BF0`。
所以再等几天不能修复此结构。原有证据入口保留在
[owner-subset runner](../../ck3_autonomous_player/native_bridge/research/run_owner_subset_ai_reassignment_rejoin_live_acceptance.py)
的 `_singleton_requester_parent_cannot_ask_proof`。

最小实验采用 H（将撤离的 helper）、A/B（留守 requester parent）三支同侧 CUnit：

1. 在种子阶段准备三支可独立识别的 CUnit，先于战斗进行合法拆分/调度；不写内存强造 subunit 或 asking。
   三者进入同一个旧 CombatID、同一侧。种子控制权切换只用于构造来源，不能当作 AI 求援证据。
2. 只撤离 H；保存种子后移除临时夹具并用 production 冷重载，返还 AI 控制。
   记录 seed 与 production 存档 hash、episode，以及完整带 generation 的 CUnit/CArmy/Combat/coordinator ID。
3. 等 H 的 native membership 重新可读、撤离结束后暂停。A/B 必须仍在原 CombatID，且共享
   **同一 `(coordinator_id, unit_stack_stored_index)`，但 `subunit_stored_index` 不同**。
   A/B 两份父 subunit 向量必须完全一致、至少两项。三个 CUnit 只是数量下限，不能替代这一步。
4. 本次最小实验限定 H 为同 coordinator 的独立 parent，其 `support_search_province_ids_in_stored_order` 包含旧战场。
   H 此时不在战斗、不撤退、不 asking、尚未 assigned。所有单位均不受当前玩家控制。
5. 若三者合并成一个 subunit、A/B 分属不同 parent、旧战斗结束或 ID 变化，立刻以无效 fixture 收口，另做新 seed。
   不以增加等待天数、手动下达返回命令、直接写 assignment 或制造 CombatID 来补结果。

本包已实现 [离线预验工具](../../tools/war_film_reinforcement_fixture.py)。它读取真实既有 query response，
检查暂停前后 stamp、每军两次查询一致且 sequence 增加、完整身份、两次 roster、上述三军结构与候选 Province。
它返回 `structural-preconditions-met`，始终保留 assignment/ETA/join 未证明；不启动进程、不注入 DLL、不制作存档。
父 stack 的键不使用 selected CArmyID：它是所选 CUnit 的军队身份，不能代替 parent 身份。

```text
tools\.venv\Scripts\python.exe tools\war_film_reinforcement_fixture.py --template --output <new-capture-template.json>
tools\.venv\Scripts\python.exe tools\war_film_reinforcement_fixture.py --bundle <actual-capture-bundle.json> --output <new-fixture-check.json>
```

模板里的空 ID 和空帧必须由实际捕获填入。`recorded-native-responses` 是输入声明，不是工具对真实性的认证；
合成测试固定标为 `synthetic-offline-test`。没有新 source save 已被本包证明满足这些条件。

## 下一次 assignment → ETA → 同 CombatID join 最少还要什么

现有 [assignment reader/runner](../../ck3_autonomous_player/native_bridge/research/run_battle_reinforcement_assignment_live_acceptance.py)
已能提供 native membership、asking/assigned、需求 raw、assignment Province、route/ETA、当前 CombatID 与 contact-if-now。
下一次应先复用这些面，不必为了拍片先扩一套新接口。

| 阶段 | 必须取得的最小证据 | 不能替代它的东西 |
|---|---|---|
| 求援生产 | 新 daily tick 后 A/B 的 asking 与有效 request raw；parent 仍满足 >1 门槛 | 暂停着反复查询、控制权切换 ACK、旧 raw 残值 |
| 原生指派 | H 的 bit1 从 false 到 true，目标 Province=旧战场，同 revision 的 AI 控制与 requester 候选帧 | 手工移动回战场、只看到队伍朝相同方向 |
| ETA | direct target、remaining route 末端与 assignment 对齐，native `assignment_eta_date_raw` 可用 | 仅同一天预测 contact、用路程除速度自行宣称原生 ETA |
| 实际加入 | 旧 CombatID 仍 active；H 的 CArmy active CombatID 与同侧 roster 同时包含 H | assignment 自带未来 CombatID；省内另开一场战斗 |

若合格 fixture 仍不 assigned，最小新增只读观察面是一次匹配决策的
`candidate ordinal / candidate CUnit / parent / asking-valid / demand / selected ratio / quantized required / requester-parent available / comparison result`，
再加本地 helper 的 busy/asking/reserve 跳过原因。现有 wire 不完整暴露这些临时值；
仅靠最终 bit 不能区分候选顺序、需求满足、helper 忙碌和 producer 根本未运行。
更换为 cross coordinator 时另需 `+0x34/+0x38` 的生产来源，不能复用同 coordinator 的 bit0 解释。

同日 movement/contact 与全局 combat 更新顺序仍属既有未知。最小正向实验只证明本次完整序列，
不把日级暂停帧自动升级为全引擎精确调度顺序。

## 冻结、复现与验收边界

最终冻结版本为 r3：

- [source contract：17 个有界 EXE 字节段及解释](research-plans/war-film-reinforcement-20260923-r3/war_film_reinforcement_static_contract_20260923.json)
- [offline research plan](research-plans/war-film-reinforcement-20260923-r3/war_film_reinforcement_plan_20260923.json)
- [声明图与文件完整性检查](research-plans/war-film-reinforcement-20260923-r3/war_film_reinforcement_graph_20260923.md)

解释器为本 worktree `tools/.venv/Scripts/python.exe`，Python 3.14.7，pefile 2024.8.26、capstone 5.0.9。
抽取器逐块检查解码覆盖完整字节长度，冻结器使用 UTF-8 LF 后计算 SHA，避免 Git 换行正规化破坏证据绑定。

```text
tools\.venv\Scripts\python.exe tools\war_film_reinforcement_static.py --rva 0x1848570 --size 0x380
tools\.venv\Scripts\python.exe tools\war_film_reinforcement_static.py --refs 0x570DEC0 0x570DEBC 0x570DF28 0x570DFD4 0x570DEC8 0x570DED0
tools\.venv\Scripts\python.exe tools\war_film_reinforcement_freeze.py --output-dir <new-empty-research-directory>
tools\.venv\Scripts\python.exe tools\native_research_plan.py check docs\ck3-native-ai\research-plans\war-film-reinforcement-20260923-r3\war_film_reinforcement_plan_20260923.json
tools\.venv\Scripts\python.exe tools\war_film_reinforcement_fixture_test.py
```

`--refs` 是常见 RIP 编码 locator，并用 PE exception 函数边界内解码排除错位候选；
无 unwind 条目的短注册 stub 仍需从真实入口复核。它不是全指令形态的无遗漏证明。
离线 plan 的 7 条 static-confirmed 是本包作者声明并绑定 source contract，3 条 unknown 保持开放；
plan 工具检查文件与记录一致性，不替作者审定反汇编语义，也不给 live 授权。

本次一次有界验证通过：7 个结构/负控测试、native plan check/render、空捕获模板实际生成。
plan 检查为 `plan-consistent`，同时明确保留 `offline-only plan does not define a live observation window`。
外置 `validation-receipt.json` 保存实际 argv、退出码与 stdout/stderr 文件；不是新 live GREEN。

外置过程资料永久保留在 `D:/workspace/ck3_war_film_research_20260923/reinforcement-r1/`，
包括完整函数反汇编、slot xref、旧候选 locator 与两个未验收 freeze 草稿。
第一个草稿尚沿用旧文比较解释；第二个草稿的 delay 段末尾截断一条跳转；均仅保留溯源，最终结论以 r3 为准。
没有改变旧专题评级、历史 RED 或影片审阅结果。
