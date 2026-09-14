# 《驱策朝贡国》需求与可实现性研究

## 产品命名

- 中文名：**驱策朝贡国**
- 英文名：**Tributary Expansion Directives**
- 仓库目录：`mod_tributary_expansion_directives/`
- 建议脚本命名空间：`ted`，所有脚本键使用 `ted_` 前缀
- 当前阶段：仅完成研究与设计；本目录还不是可加载、可发布的 mod

“Directives”既涵盖指定进攻目标，也给以后加入军费补贴、共同参战承诺、冷却与不同强制程度留出空间。

## 原始需求摘要

玩家作为宗主时，希望主动帮助自己的朝贡国扩张，因为更大的朝贡国通常意味着更大的潜在税基。核心玩法是：

1. 玩家选择自己的一个朝贡国；
2. 玩家指定一个希望它进攻的外国目标；
3. 朝贡国根据实力、关系和玩家提供的激励接受或拒绝；
4. 接受后，朝贡国以主攻方身份开战；
5. 胜利取得的土地归朝贡国，原朝贡关系继续存在；
6. 新领地日后产生收入时，宗主可通过既有朝贡合同获得相应收益。

重点不是“替朝贡国打一场宗主自己的战争”，而是“让朝贡国为自己征地并继续纳贡”。

## 结论

**结论为 GO：该需求可以实现，但应采用“自定义角色交互 + 自定义扩张 CB”的确定性方案。**

CK3 1.19.0.6 已有两条足够强的原版先例：

- `frontier_influence_war_interaction` 允许最高领主选择行政制边疆、海军或护军总督，再选择外国公爵领，接受后由该总督通过 `start_war` 开战；
- `fp3_request_turkic_invasion_interaction` 允许玩家选定受害统治者、从候选中选择入侵者，并以脚本直接发动事件 CB。

因此，下列关键能力都已由原版脚本证明可用：多角色选择、头衔目标选择、AI 接受度、脚本发动战争以及自定义胜利后的领土转移。

曼荼罗政体其实已经有一个部分解法：原版“扩张敕令 / Expansion Decree”会把属下和朝贡国判定为好战型 AI，并允许宗主花费虔诚召它们加入宗主的战争。如果玩家只想让所有朝贡国总体上更爱扩张，可以先使用该敕令。

但它不能指定敌人。CK3 另外暴露的 `ai_war_chance` 也只是角色级的总体宣战倾向，没有发现可稳定写入“优先攻击这个指定统治者”的目标级 AI 提示接口。无论使用敕令还是临时好战修正，朝贡国都可能攻击别人、选择别的 CB，或者长期不宣战，不能完整满足本需求。

## 原版现在能不能做到

### 没有通用的朝贡国拓疆命令

对 `game/common/character_interactions/` 的所有顶层交互进行扫描后，未发现“宗主指定目标，让自己的朝贡国为自身领地开战”的通用交互。`00_tributary_interactions.txt` 的顶层功能只有建立、索取、重申或终止朝贡关系，修改贡赋，以及提供/索取廷臣或伴侣等关系管理能力。

### 四个接近但不等价的原版功能

1. **扩张敕令（Expansion Decree）**

   如果玩家统治曼荼罗，可以选择 `mandala_decree_expansion`。它把朝贡国纳入 `ai_has_warlike_personality` 判定，确实会广泛鼓励扩张。这是“有没有现成方法”最直接的答案，但它影响所有合资格属下，没有目标选择器，也不保证某个朝贡国在特定时间向特定敌人开战。

2. **朝贡国战争支持（Tributary War Support）**

   合同条款 `tributary_war_participation_obligation_forced` 会让朝贡国自动加入宗主的战争。它不会让朝贡国成为主攻方，也不会把战果交给朝贡国，所以不能扩大其税基。

   扩张敕令还额外提供 `can_call_tributaries_for_piety`：宗主可花费虔诚把非盟友朝贡国叫进自己的战争。用途仍是支援宗主，不是让朝贡国自行拓地。

3. **召唤参战（Summon to War）**

   `frontier_influence_war_interaction` 的中文原版描述就是“召唤某位下属与外国统治者进行战争以获取公爵级头衔”。它是本需求最接近的现成功能，但只向行政制边疆/海军总督及天朝护军类封臣开放，并不向普通朝贡国开放；原版胜利逻辑还把领土交给进攻者的最高领主，不适合直接照搬。

4. **请求入侵（Request Incursion）**

   `fp3_request_turkic_invasion_interaction` 能资助合资格的外国军阀攻击指定统治者。它只在波斯斗争特定身份或天朝扩张派系等窄条件下出现，入侵者还受政府、文化、战争状态等候选规则限制，战果受益人也不保证就是玩家的朝贡国。某些局面下自己的朝贡国可能恰好满足候选条件，但这不是通用、可靠的朝贡玩法。

另外，宗主可以加入朝贡国的防御战争，部分朝贡任务奖励也能用金钱、发展度或革新间接增强朝贡国；两者都不能让玩家指定一场由朝贡国主动发动的扩张战争。

所以，曼荼罗玩家可先用扩张敕令提高总体扩张倾向；其他玩家只能等待朝贡国按普通 AI 自行宣战，或在特殊玩法中碰巧利用上述窄功能。原版仍没有满足“指定朝贡国 + 指定目标”的稳定入口。

## 朝贡收益假设

需求里的经济动机方向正确，但不能承诺“多一块地后贡金立刻严格增加”。原版金钱义务是比例税：

- 默认朝贡税为 25% / 50%；
- 天朝朝贡税为 5% / 10% / 25%；
- 霸权朝贡税为 10% / 15% / 30%；
- 官僚朝贡税为 5% / 10% / 25%。

因此，新领地在恢复控制、产生正收入并进入朝贡国经济后，通常会扩大可征税基础。以下情况会削弱或消除短期收益：零金钱义务、战争债务、低控制、昂贵军队、新领地交给低效封臣，或合同主要转移威望、兵员、牲畜等非金钱资源。

产品文案应写成“扩大潜在贡赋”，不应声称每次胜利都会立即提高当前贡金。

## 推荐玩法设计

### 玩家流程

1. 玩家右键自己的直属朝贡国，选择“发布拓疆令 / Issue Expansion Directive”。
2. 原生交互窗口只列出与该朝贡国接壤、属于外部统治者且满足安全规则的目标公爵领；首版可收窄为伯爵领以便平衡。
3. 玩家可选择：
   - 只提出建议；
   - 提供一次性战争金；
   - 后续版本再考虑承诺共同参战。
4. AI 朝贡国显示可解释的接受度，参考双方军力、目标盟友、债务、当前战争、对宗主的好感、恐惧、性格与贡赋条款。
5. 接受时再次用 `can_declare_war` 检查精确进攻者、守方、CB 与头衔；通过后立即建立一场自定义“朝贡拓疆战争”。拒绝或合法性变化时不发动战争。

“鼓励”应体现在朝贡国可以拒绝，以及玩家可用金钱提高接受度；不应伪装成一个不可验证的后台 AI 暗示。

### 推荐脚本拓扑

```text
玩家宗主（actor）
  └─ 直属朝贡国（recipient）
       └─ 相邻外部统治者（secondary_recipient）
            └─ 精确目标头衔（target）
                 └─ recipient.can_declare_war(...)
                    └─ recipient.start_war(
                      cb = ted_tributary_expansion_cb,
                      target = secondary_recipient,
                      target_title = target)
```

交互可复用原版已证明的字段：

```text
target_type = title
target_filter = secondary_recipient_de_jure_titles
populate_recipient_list = { ... add_to_list = characters }
can_be_picked_title = { ... }
on_accept = { scope:recipient = { start_war = { ... } } }
```

自定义 CB 应设为只能由脚本发起，胜利时明确把目标领土或合资格封臣交给 `scope:attacker`（即朝贡国），不能直接复用行政制 `influence_war_cb` 中交给 `scope:attacker.top_liege` 的结果代码。`start_war` 是执行器，不应假设它自动替代普通宣战界面的全部合法性与费用检查。

### 首版安全与平衡边界

- 只有玩家可以发出指令：`scope:actor = { is_ai = no }`；AI 永远不会主动使用本 mod 的交互。
- 接受者必须仍是发令者的直属朝贡国；等待回复期间关系变化则使交互失效。
- 朝贡国必须成年、有地、可行动、未被监禁、未破产、没有已集结军队，首版建议还要求当前无战争。
- 排除游牧牧民等原版明确不能开战的身份。
- 目标必须是外国、有地且位于外交范围内；不得是玩家、朝贡国本身、玩家封臣、玩家的其他朝贡国、玩家宗主链或同一统治层级内部成员。
- 朝贡国与目标之间存在停战、同盟、共同参战、强钩子或其他原版禁战关系时不可选择。
- 复用或等价执行原版 `herders_and_tributary_constraints`，禁止朝贡国攻击自己的宗主、宗主邦联成员和受保护的朝贡网络成员。
- 首版只允许陆地相邻目标，避免远征距离和海军能力造成明显坏局。
- 同一朝贡国建议 5 年冷却；战争金在对方接受时才结算，拒绝或失效不扣款。
- 胜利、白和平、失败和战争失效都必须有独立结果文案；不能只处理胜利。
- 默认不强迫玩家加入这场战争。若以后增加“承诺支援”，必须通过原版参战合法性检查并在成功加入后读回验证。

### 更“软”的备选方案

如果设计目标是不在接受瞬间开战，而是只提高朝贡国日后开战的可能性，也可以：把所选统治者和头衔保存为限时变量、只对该目标开放专用 CB、提高该 CB 的 `ai_score`，再临时增加总体 `ai_war_chance`。宣战、目标失效、断绝朝贡或超时后清理变量。

这个方案属于 PARTIAL GO：它更像真正的鼓励，但 AI 仍可能优先处理别的战争、攻击其他对象或直到变量过期都不行动。若用户最在意“我选谁，它就考虑打谁”的清晰反馈，首版应采用有接受/拒绝结果的即时 `start_war` 方案。

## 为什么不直接复用普通 CB

“让 AI 使用它当前拥有的任意合法 CB”听起来更原生，但研究阶段没有发现一个脚本接口可以同时：枚举该 AI 对指定目标的全部当前 CB、让玩家挑选其中一个，并把所选 CB 对象可靠地交给 `start_war`。不同 CB 还带有宣称人、费用、信仰、等级、冷却和特殊战果语义。

最稳妥的首版是一个用途单一、结果可说明的事件组自定义 CB。它不出现在普通宣战列表，只能由本交互启动，并在交互层提前完成合法性、军力和关系检查。

## 实现范围预估

若进入施工，最小产品需要：

- `descriptor.mod`；
- `common/character_interactions/ted_interactions.txt`；
- `common/casus_belli_types/ted_casus_belli.txt`；
- `common/scripted_triggers/ted_triggers.txt`；
- `common/scripted_effects/ted_effects.txt`；
- 简体中文与英文本地化；
- 静态解析/合同测试、确定性 release builder 与 manifest；
- 一套独立 userdir 的 CK3 实机验收。

当前研究没有创建上述运行时代码，也没有启动 CK3。

## 验收门槛

### L0 静态与离线预验

- 所有 CK3 脚本文件为 UTF-8 BOM，所有 key 使用 `ted_`，无原版顶层覆盖。
- 交互只允许玩家宗主对直属朝贡国使用。
- 候选列表只包含合法外部相邻目标；无目标时交互明确禁用。
- 接受路径的战争主攻方、守方和目标头衔作用域精确对应玩家所选对象。
- 发送时和接受时的 `can_declare_war` 必须使用同一进攻者、守方、CB 与目标头衔；任何失败都不调用 `start_war`。
- CB 的胜利结果把土地交给朝贡国，不交给宗主；失败、白和平和失效均不转移土地。
- 在 CK3 前，先运行 `open_kaishek` 能覆盖的 parser、schema 与有限运行时预验，并记录不支持语义。

### L1/L3 实机

- 在真实 1.19.0.6 局面中，玩家能看见交互并选择一个精确合法目标。
- AI 拒绝时不产生战争和费用；接受时只产生一场战争。
- 原生读回证明 primary attacker 是朝贡国、primary defender 是所选目标统治者、target title 是所选头衔。
- 胜利后目标领土归朝贡国，宗主没有直接取得领土，朝贡关系与合同未被破坏。
- 保存并重载后关系与结果保持一致。
- 用一块有正收入的测试领地证明稳定期后的贡赋变化；若没有增加，报告实际税基原因，不能仅凭领地数宣称经济目标完成。
- 覆盖关系在等待答复时终止、目标换主、目标头衔失效、朝贡国进入另一场战争等竞态。

## 主要未知项

这些未知项不影响“能否实现”的 GO 结论，但必须在实现期用离线预验和 CK3 实机关闭：

- `start_war` 在交互回答帧对所有政府和朝贡合同组合的失败反馈；
- 不同政府接收新封臣或整公爵领时的合法领土转移细节；
- 朝贡国进攻目标的宗主或另一个朝贡网络时，原版是否有额外自动参战/断约副作用；
- 玩家承诺共同参战时，宗主能否在所有相关合同下合法加入；
- 选择公爵领还是伯爵领能在收益、战争时长与滥用风险之间取得更好平衡。

## exact-build 证据

研究日期：2026-09-14。安装版本来自 `launcher/launcher-settings.json`：**CK3 1.19.0.6 (Scribe)**；Steam app manifest 的 build ID 为 **23530548**。`ck3.exe` SHA-256：

`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`

Steam `appmanifest_1158310.acf` SHA-256：`F81C1B26356405265502A65E4C45D9184CCF55E0050EC932E3CC5665AFF87CBE`。

下列路径均相对于 CK3 安装目录的 `game/`：

| 证据 | 关键行 | SHA-256 |
| --- | --- | --- |
| `common/character_interactions/00_tributary_interactions.txt` | 7、801、1398、1947、2033、2148、2779、3002、3492、3993、4321、5184：全部顶层朝贡交互，无拓疆战争命令 | `CF783E658F91D0D2EAA532663B6137CE640B1039F00478B53E7F92E104B15DF0` |
| `common/subject_contracts/contracts/special_contracts.txt` | 786–895：宗主保证与朝贡国强制参战条款；强制条款仅令其加入宗主战争 | `E34BF96F4E7932A121919CE1EC690DBD918F901586DF38944C0677A25E0533F4` |
| `common/laws/00_realm_laws.txt` | 2317–2359：曼荼罗扩张敕令提供朝贡召集与 `subjects_appear_more_warlike` | `EC96F526706B454A883B78429161B8C19D36B6DC8A5324C5DB95E73A6806E2DF` |
| `common/scripted_triggers/00_ai_value_triggers.txt` | 54–150：扩张敕令让朝贡国满足 `ai_has_warlike_personality`，但不指定目标 | `2025C05AFB98CBCFF5CDB2987B36E740D6DB358F53F8A932DDE0658AE46FFB8F` |
| `common/character_interactions/00_alliance.txt` | 1–63：扩张敕令允许花费虔诚召朝贡国加入宗主战争 | `919ED408EC735F64ED972E23A376CD618A2E207A0EA273F973C5B1F89440E39D` |
| `common/character_interactions/06_ep3_interactions.txt` | 11014–11248：`frontier_influence_war_interaction` 的下属、外国目标、公爵领选择与 `start_war` | `00BEA6E5C880BAB47B0F7DB55BE3D17156547787F6887E5AB22C2DC184A43CC0` |
| `common/casus_belli_types/07_ep3_admin_cbs.txt` | 1629–1773：脚本专用 `influence_war_cb`；胜利后领土转给进攻者最高领主 | `305622DE1A876510380355B2328E6989E377E5D32133A03AA24D9AB35B44D5A6` |
| `common/character_interactions/00_fp3_interactions.txt` | 346–927：指定受害者、选择入侵者、AI 接受度与 `start_war` | `7EBD9A71E78BFEC2653DD33F39CDD8D3A53BA1B7D5C908756495AB3C10E5CA5B` |
| `common/casus_belli_types/05_fp3_wars.txt` | 402–538：脚本专用突厥入侵 CB 与受益人领土转移 | `234DEC6EAEE859A6CF95D8D0BC66247CB22D74C69358806CA3C75E75C33C2AE9` |
| `common/character_interactions/_character_interactions.info` | 157–167、247–299、608–629、679–706：头衔目标、次要角色列表与发送时校验合同 | `F360C05B72CD2B0D87885E570FA55E70E41089DEFB4675BE5A82E390940D5D10` |
| `common/casus_belli_types/_casus_belli.info` | 36–69、122–130：CB 生命周期、目标头衔、脚本战争与 AI 字段 | `E3BACD9F3360837F6ED7D5F22B937AB7E79CB675AD804819A627CB73970CE699` |
| `common/scripted_triggers/00_war_and_peace_triggers.txt` | 901–952：牧民与朝贡网络的原版禁战边界 | `4E3D7DB2931B313F132D5228BABDBB60A67DD28E9898A337BE78B2FC1DEF862E` |
| `common/scripted_triggers/07_ep3_triggers.txt` | 1333–1338：带 defender、CB、claimant 与目标头衔的 `can_declare_war` 先验范例 | `A05CAD169B9C0708126A2D908E1858A241EB62D835F109705DC3144D08A8EF47` |
| `common/subject_contracts/contracts/default_tributary.txt` | 1–57：默认朝贡金钱义务是比例税 | `FBC900119DBC046042D7D47E69834E4E4818BC3C1F588395FC65EDF8A9818AC0` |
| `common/script_values/00_goverment_values.txt` | 184–212：四类朝贡税率 | `3E702835AA09212CB7D883F74E067BB9AFEBEF4C56D6E8C6CAD460769E63D87A` |
| `common/modifier_definition_formats/00_definitions.txt` | 2729–2735：只暴露总体 `ai_war_chance` 与 `ai_war_cooldown` 修正 | `959CF6842A9FCDB69DF4C7251E2BF8C6FE2A454363BD6C29D63AD6FD3FD60DDE` |

本结论是 exact-build 静态研究结论，不冒充 CK3 实机验收。
