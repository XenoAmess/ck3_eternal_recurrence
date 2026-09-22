# 宣战关系网络：哪些来源计入军力，哪些在己方被排除

本包把 `0x1879850` 的六个来源和三组 actor 额外过滤落实到原生名字。**己方与目标方的网络估值并不对称**：
己方不计已经在战中的候选、人类玩家、同邦联成员，以及满足下述宗主保证条件的候选；目标方关闭这三组额外过滤。
两边仍都执行共同谓词。纳入估值不保证实际求援被接受或军队到场。

范围为 CK3 `1.19.0.6`，EXE SHA-256
`2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`。
本包只读 EXE 与当前原版脚本，没有启动 CK3，没有 live、提交宣战、发送求援或参战结果。
这是[既有宣战专题](war-declaration.md)和[军力缓存 producer](war-film-declaration-power-cache-2026-09-23.md)的独立追加，
不覆盖旧 ABI、旧结论或历史证据。

## 来源顺序与实际对象

collector 的两个实参是被遍历的 `CCharacter*` 和五指针配置；配置根和开关都是本次同步调用的局部量。
`0x1878A00` 的既有调用合同是 target `{target,0,0,0,&sum}`、actor `{actor,1,1,1,&sum}`。
本表的“候选”还必须通过后续共同谓词与所启用的额外过滤。

| 顺序 | 正式来源 | 本轮直接指令 | 候选与来源条件 |
|---|---|---|---|
| 1 | 完整配偶数组 | `0x18798D3..0x1879B35`：Character `+1A0 → FamilyData+20`，4 字节 full CharacterID | 遍历完整数组，不只 primary spouse；要求可供读取的 military 数据 |
| 2 | 订婚对象 | `0x1879B40..0x1879C46`：FamilyData `+10` | 非 `-1` 的 betrothed full ID，解析并检查 military 数据后调用过滤 helper |
| 3 | 外交关系中的有效联盟 | `0x1879C46..0x1879DF8`：Character `+1A8 → +20`，16 字节 `{CharacterID, relation*}` 行 | 先排除配偶、订婚对象；要求 relation `+94 != 0` 且 `+1A9 == 0`，然后取该行角色 |
| 4 | 有参战义务的属国／朝贡国 | `0x1879DF8..0x187A20E`：military `+248` 的 `CSubjectContractID` 数组 | 解析 contract，取 `contract+20` 的 subject；要求显式存在 `tributary_war_participation_obligation`，且 current level 不等于 default |
| 5 | 提供战争保证的宗主 | `0x187A20E..0x187A412`：root military `+1C8` 自身契约 | 要求显式存在 `suzerain_war_participation_guarantee` 且 non-default，候选取该契约 `+28` 的宗主 |
| 6 | 所属邦联成员 | `0x187A412..0x187A770`：Character `+1C0 → +80` 的 ConfederationID | 解析邦联后遍历 `+18` 成员数组、signed count `+24`；排除 root 自己和先前已见 ID |

命名并非从偏移大小猜测：

- 配偶／订婚字段复用[婚配 ABI 的明确字段](../../ck3_autonomous_player/native_bridge/research/marriage_proposal_native_binder_v1_abi.json)；
  本轮重新提取 `0x2608380` 配偶数组 getter 和 `0x26090E0` 订婚 getter。
- 联盟关系行与[已定位的 `IsAlliedTo` 原生入口](m5-r0082-candidate-alliance-projection-abi-2026-09-22.md)
  `0x2661E00` 闭合：该入口也先识别配偶／订婚，再经 `0x2610840` 查同一 relation map，并检查相同 `+94/+1A9`。
  这里只称该组合为有效联盟判定，不另猜两个字段各自的生产／失效周期。
- 契约类型和 `+20/+28` 两端复用[强制属国／朝贡参战者](prewar-encounter-inputs.md)的 RTTI 证据。
  本轮独立提取 `0x2D59578 → database+F18`、`0x2D595B1 → database+F28` 的字符串绑定，
  分别是 `tributary_war_participation_obligation`、`suzerain_war_participation_guarantee`。
  collector 比较当前 level 与 `term+AB40` 的 default，不以“有这份契约”直接判定参战义务。
- `GetConfederation` 字符串在 `0x4100BF8`；注册 `0x5063DE/0x50644C` 绑定 callback `0x2621B50`，
  callback 调用 `0x2601D20`，精确读取 Character `+1C0 → +80`，并使用与 collector 相同的邦联 storage。

## actor 与 target 的过滤差别

| 条件 | actor 网络 | target 网络 | 独立命名证据 |
|---|---|---|---|
| 共同谓词 `0x1B35DF0(root,candidate)` 为 false | 排除 | 排除 | 原生调用与返回分支已闭合；对应 authored rule 的名字尚未闭合，见后文 |
| 候选已经在战中 | 排除 | 不开启此额外过滤 | `IsAtWar` 字符串 `0x4304B68`，注册 `0x50CF7D/0x50D003 → 0x2622F10 → 0x2610510`；检查 military `+318/+0C != 0` |
| 候选是 human-player CharacterID | 排除 | 不开启此额外过滤 | `0x187591D → 0x28BCEB0`；其他内联分支查同一 human-player 集合 |
| root 与候选具有相同且都非 `-1` 的 ConfederationID | 排除 | 不开启此额外过滤 | `0x187593F → 0x28B00D0`；与上述 `GetConfederation` getter 的字段完全相同 |
| 候选等于 root 的原生 `GetSuzerain` 结果，且 root 自身契约有显式 non-default 战争保证 | 排除 | 不开启此额外过滤 | `0x187594B → 0x2613520`，再 `0x187597A → 0x22552E0`；后者读取 `database+F28` |

`GetSuzerain` 字符串 `0x43254B8` 的注册 `0x50497B/0x5049B4` 绑定 `0x2620F30`。
该 callback 与 collector 使用的 `0x2613520` 具有相同读取和有效性分支：从 root 自身契约 `+28` 取角色，
经 `0x2937D50` 选择该角色或 root；因此这里保留“原生 GetSuzerain 结果”这一精确条件，不改写成任意领主链。

**对旧标签的勘误：**[旧 ABI](../../ck3_autonomous_player/native_bridge/research/war_entry_assessments_v1_abi.json)
的 `filter_c = same-realm/liege/government exclusions` 只能视作当时未定名的描述。
本轮证据将第一项定名为 **同邦联**，并将后续项定名为 **宗主与 non-default 战争保证组合**；
不能在影片里继续画成“同领地全部排除”或“某类政体一律排除”。原文件未被修改。

## 累加、去重与不能越过的边界

通过过滤后只做 `sum += candidate.military[+308]`。该 collector 内没有按每位盟友乘一个百分比的步骤；
`+308` 本身的数量／power、MAX／CURRENT 区别由[缓存专题](war-film-declaration-power-cache-2026-09-23.md)说明。
actor 的 State16 基础项及 target 后续调整仍属于 `0x1878A00` 的其他步骤，不能用本网络和代替最终 ratio。

seen vector 的位置也影响准确表述：前面配偶、订婚、关系来源在进入候选过滤后，即使被共同谓词拒绝，
也会把 ID 放入 seen；后面的契约和邦联来源检查 seen 后跳过重复者。关系来源另行排除配偶／订婚。
这证明了来源间按顺序抑制重复，**不证明**该函数会对人为破坏、含重复 ID 的配偶数组做通用去重。
seen 仅属于此次调用，最后 `0x187A770..0x187A789` 释放；不能缓存到下一帧。

共同谓词的静态边界为：`0x1B35DF0` 构造 root scope，把 candidate full ID 绑定到一个 scope 槽，
然后对 singleton `+F08` 对象的 `+1960` 子对象执行 trigger 求值并返回 bool。
当前原版 `common/scripted_rules/00_rules.txt:846–856` 的 `can_potentially_call_ally` 明说供宣战 AI 使用，
并转发到 `can_potentially_call_ally_trigger(WARRIOR=root, JOINER=scope:ally)`；这是强候选，
**本包没有闭合该文本加载到 `+1960` 的映射**，所以不把其完整脚本排除项升级成 instruction-confirmed。
检索到 token 字面量或相似 UI 调用不能补足此边。

影片可以说：“估值先列出婚配、联盟、参战契约和邦联来源，再做共同资格检查。己方还剔除已经在战中的候选、
人类玩家、同邦联成员，以及满足特定保证条件的宗主；敌方没有照搬这些额外剔除。”
不能说：“所有盟友都被计入”“这些人一定接受求援”“同领地一律不算”或“现在估出的军力就是开战后到场军力”。

## 冻结证据与下一最小观察面

- [初始离线计划](research-plans/war-film-relationship-network-20260923-r1/plan.json)及[计划检查](research-plans/war-film-relationship-network-20260923-r1/check.json)。
- [精确 bytes／字符串／原版 source 摘要](research-plans/war-film-relationship-network-20260923-r2/static.json)。
- [结果计划](research-plans/war-film-relationship-network-20260923-r2/result-plan.json)、[检查](research-plans/war-film-relationship-network-20260923-r2/check.json)、[图](research-plans/war-film-relationship-network-20260923-r2/graph.md)。
- 新工具：[初始计划与有界提取](../../ck3_autonomous_player/native_bridge/research/war_film_relationship_network_extract.py)、
  [确定性冻结器](../../ck3_autonomous_player/native_bridge/research/war_film_relationship_network_freeze.py)。
  默认游戏是同 hash 的 `C:/SteamLibrary/steamapps/common/CRUSAD~1/binaries/ck3.exe`，可显式传 `--exe`／`--game`。

复现时使用已安装 `pefile`、`capstone` 的本 worktree 解释器，新输出目录必须不存在：

```text
tools\.venv\Scripts\python.exe ck3_autonomous_player/native_bridge/research/war_film_relationship_network_freeze.py --output-dir D:/workspace/ck3_war_film_research_20260923/relationship-network-reproduction-new
tools\.venv\Scripts\python.exe tools/native_research_plan.py check D:/workspace/ck3_war_film_research_20260923/relationship-network-reproduction-new/result-plan.json
```

本次为 **8 条 static-confirmed、3 条 unknown、0 条 live**。这里的条数是冻结计划边数，不是全 CK3 决策树完成比例。
下一步最小观察面是：同一 actor／effective-target／revision 的六类来源身份、候选 IsAtWar/human/ConfederationID/
宗主契约 term 与 level，以及原生最终网络总量。既有 `war_entry_assessments_v1` 只给总量，尚不能据此识别每个贡献者。
缓存时效、关系建立／失效 producer、真实接受、加入同一 CWar 仍须另有原生观察；本包不新增 MCP schema 或 live runner。
