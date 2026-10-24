# 宗教礼仪融合：可行性分析

研究日期：2026-10-24。状态：**research / 静态研究完成，未开始模组实现**。

## 1. 结论

**可以沿文化融合的操作方式，设计宗教与礼仪的双来源选择、组合预览和创建流程。当前最有依据的实现载体，是原生动态 Rite，以及由 Rite 分离产生的新 Faith。** 文化融合的界面布局可以借鉴，但它的原生模型不能直接换成宗教对象使用。

本轮不只找到了界面名称或本地化：已核对文化融合、礼仪创建与编辑的真实 GUI callback 登记；进一步追到了 `create_dynamic_rite` 的原生 effect 工厂、参数解析和构造路径。该 effect 支持指定核心信条与教义，并非只能随机生成礼仪。因此存在不改游戏二进制、由正常模组脚本创建融合结果的具体候选路线。

| 目标 | 当前判断 | 已有依据与剩余限制 |
| --- | --- | --- |
| 两个同 Faith 的 Rite，选取双方内容生成第三个 Rite | **有较强静态可行性依据** | 动态创建继承创始者当前 Rite，支持显式核心信条、教义覆盖；仍需验证实际输出、分歧及后续钩子。 |
| 不同 Faith 的礼仪／教义融合，生成独立 Faith | **有条件可行，需原型验证** | 可以创建动态 Rite，再通过原生分离机制生成 Faith；合法候选、归属宗教、领袖与圣地必须单独处理。 |
| 跨 Religion 的内容融合，例如儒家与基督教 | **存在内容组合路线；不能承诺任意组合均合法** | 以一方为宗教归属，吸收另一方允许的内容；宗教限定、教义锁、特有脚本不会因复制教义而全部迁移。 |
| 新结果同时具有两个原生父 Faith／Religion | **未找到对应公开模型与接口证据** | 已观察的 Rite 只有一个 parent Faith；文化的双亲关系不能直接移植。双来源历史可以作为模组自己的记录。 |
| 任意两 Religion 动态生成第三个全新 Religion／Family | **当前证据不足，不作可实现承诺** | 本轮未找到相应精确 effect 名称或创建合同；动态 Faith 不等于动态 Religion。不能以一次名称未命中断言引擎绝对做不到。 |

建议后续先验证“同 Faith 的两个 Rite → 精确组合的新 Rite”，再验证“新 Rite → 独立 Faith”。跨宗教组合在此基础上逐项开放。该顺序是研究建议，**本轮没有执行原型或开始编码**。

## 2. 命名、范围与版本基线

新目录为 **`mod_religious_ritual_fusion/`**，沿用仓库 `mod_<英文小写下划线>` 约定。中文暂用用户指定的“宗教礼仪融合”，英文工作名为 Religious & Ritual Fusion；脚本前缀、版本号与 Workshop ID 尚未分配。

用户本轮要求观察原版代码、二进制并写可行性报告。本目录仅保存研究文档、来源身份和有限二进制证据；没有 descriptor、生产脚本、GUI 覆盖、构建器、fixture 或已注册产品。

本轮机器为 **`machine_id: 4-8e1c2f1861`**，由 `tools/ck3_live_run_id.py machine` 实际读回。研究从 `2026-10-24T14:26Z` 起进行，逐项观察时间见[来源回执](evidence/source-observation.json)和[二进制回执](evidence/binary-observations.json)。

| 来源 | 本机实际读取 |
| --- | --- |
| 安装目录 | `C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/`，仓库的 `Crusader Kings III/` 链接解析到此处 |
| launcher 版本 | `launcher/launcher-settings.json`：`rawVersion=1.20.0.4`，`version=1.20.0.4 (Crozier)` |
| Steam build | 当前安装对应 `appmanifest_1158310.acf`：`buildid=25734779` |
| EXE | `binaries/ck3.exe`，101,040,248 B，SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518` |
| 二进制地址域 | ImageBase `0x140000000`；报告地址均为该 SHA 对应的 RVA，文件偏移另按 PE section 映射 |

**用户已明确确认：Empire Faith Gate 就是原版的一个版本，没有第三方篡改。** 本报告采用这个版本作为有效研究基线，不把相关名称、注释或规则认定为污染。此前仅凭标记作出的第三方修改判断已撤回。版本差异仍按具体文件 SHA 绑定，不能将本轮结论不加复核地外推到其他 CK3 build。

本轮没有启动 CK3、执行 EXE 内函数、修改游戏文件、切换 Steam 状态或开展 Steam 在线完整性操作。异机既有研究仅用于定位入口，本机二进制结论已有独立字节证据；异机实机通过与安装状态不作为本机验收。

下文游戏路径均相对安装目录的 **`game/`**。行号对应来源清单中的实际字节；二进制地址与来源详见[二进制说明](binary-observations-2026-10-24.md)。

## 3. 必须区分的四个层级

```mermaid
flowchart LR
    R[Rite 礼仪] --> F[Faith 信仰]
    F --> G[Religion 宗教]
    G --> H[Religious Family 宗教组]
    C[角色与伯爵领] --> R
```

`common/religion/rite_types/_rite_types.info:35–40` 定义礼仪的 parent Faith；`faith_types/_faith_types.info:2–3` 要求 Faith 指定 Religion。Rite 的核心信条和教义是当前组合玩法的主要载体：同组的 Rite 教义优先于 Faith／Religion 的默认项，未填组才补入 Faith 的内在教义，见 `_rite_types.info:59–74` 与 `_faith_types.info:29–44`。

因此“宗教融合”有两种不同的产品解释：

1. **玩法上的宗教融合**：形成带有双方来源内容、名字和传播规则的新信仰。可以评估由新 Faith 承载。
2. **引擎分类上的 Religion 融合**：运行期间创建第三个 Religion，并拥有两个 Religion 父节点。当前没有证据支持这个等同关系。

本报告不擅自将第二项降格成第一项。后续规格应明确用户希望达到的层级；本轮同时列出两者的可行性边界，不以命名或图标假装引擎身份已经改变。

## 4. 文化融合：可以借鉴什么

### 4.1 真实流程与 GUI

`gui/window_culture.gui:652–707` 从目标文化页面进入融合；`gui/window_hybridize_culture.gui:7–9` 绑定 **`HybridizationWindow`** 和封臣转换窗口。最终按钮在 `:1288–1290` 以 `CanHybridize` 控制可用性，再调用 `HybridizeCulture`。

窗口提供双方来源、支柱／传统／外观选择，以及革新、人物／领地转换、费用和冷却预览。这套信息顺序适合新产品：**选择来源 → 双方内容对照 → 按组选择 → 结果与费用预览 → 确认 → 查看实际生成与采用情况**。

二进制中 `HybridizeCulture` 的 callback 登记 RVA `0x233746` 指向 thunk `0x15330c0`，后者调用真实方法 `0x1530620`。这证明 GUI 接的是文化专用原生行为，不能复制窗口后把其 Culture 参数改称 Faith 参数就获得新功能。

### 4.2 规则可借鉴，数值与系统不能直接搬用

| 文化融合内容 | 实际来源 | 对新产品的意义 |
| --- | --- | --- |
| 正式资格规则 | `common/scripted_rules/00_rules.txt:878–886` → `can_hybridize_culture_trigger` | 新产品也应让显示、确认与实际创建使用一致的资格规则。 |
| 不同传承、禁止父子融合、领内存在目标文化 | `common/scripted_triggers/00_cultural_triggers.txt:473–527` | 是文化语义，宗教不能原样套用“传承”。可借鉴地域接触与防止无意义重复融合。 |
| 接纳度门槛 | `common/script_values/00_culture_values.txt:148–235`，基准 40，并有修正与 0–100 限制 | 宗教敌意不是文化接纳度，也不是融合成功率。若需要长期融合度，须自行设计。 |
| 文化年龄冷却 | 同文件 `:265–286`，默认 50 年，规则可改为 100／25 年或无冷却 | 可以借鉴冷却制度，不能直接让 Religion 消费文化年龄。 |
| 费用 | `common/scripted_costs/00_costs.txt:1–132`，基础 1000 威望并受领地数、接纳度等影响 | 宗教融合应另定虔诚／其他资源费用，不能拿文化报价冒充原生宗教报价。 |
| 从双方贡献内容 | `localization/english/gui/culture_hybridization_window_l_english.yml:43,62` | 建议要求双方各至少提供一个实际差异项；共同项不重复计数。具体规则尚待确定。 |
| 融合专属传统合法性 | `common/culture/_cultural_traits.info:38–59` 的 `can_pick_for_hybridization` | 文化已有专属规则；宗教方案不能假定同名专属规则也存在。 |
| 双亲与转换 | `common/on_action/culture_on_actions.txt:126–167`；`common/scripted_effects/00_culture_effects.txt:450–775` | 原生文化存在两父文化及传播钩子；宗教结果要自行定义双来源历史与采用范围。 |

文化文案还说明两父文化接纳度 100%、创始者成为文化领袖、每位统治者一次融合；它们是原版显示合同，不能据此宣称宗教结果自动得到相同关系。人物、领地转换有实际条件和分支，也不能简写成“双方全体信徒立即改宗”。

## 5. 礼仪改革：现有创建器能提供什么

### 5.1 原生草案与最终提交

`gui/window_faith.gui:1320,1364,1379` 通过 `OpenGameViewData('rite_creation', FaithWindow.GetSelectedRite)` 进入礼仪编辑／创建。创建和改革共用 `RiteCreationWindow`，由不同模式与最终判断区分：

- 教义选择：`gui/window_rite_creation.gui:1251–1253` 先检查 `DoctrineItem.CanPick` 与 `pam_know_doctrine`，再调用 `SelectDoctrine`。
- 核心信条选择：`:1466–1478` 使用 `TenetGroupItem.GetTenets`、`TenetItem.CanPick` 与 `SelectTenet`。
- 最终确认：`:598–625` 分别由 `CanEditRite`／`CanCreateRite` 控制，再调用 `EditRite`／`CreateRite`。

本轮二进制闭合了 `SelectDoctrine → 0x14f46f0` 的真实草案写入，以及 `CreateRite → 0x14f5130`、`EditRite → 0x14f49c0` 的真实方法入口。它们不是单纯改变按钮文字或 GUI 临时变量。

但是，现有创建器的来源是当前 Rite，没有在本轮找到“设置第二来源 Rite，并把双方候选自动合并到原生草案”的公开 GUI 接口。**可以复用其合法性与呈现思路，不能承诺直接给它增加一个参数就完成双来源融合。**

### 5.2 知识、互斥和教义归属

`common/scripted_guis/pam_scripted_guis.txt:82–91` 的教义知识门要求已知该教义，或拥有 `prophet_perk`。核心信条按钮使用自己的原生 `CanPick`；没有额外同名 scripted GUI，不代表完全没有知识或其他限制。

`common/religion/doctrine_types/_doctrine_types.info:84–109` 和 `tenet_types/_tenet_types.info:78–90` 允许用本轮草案的 `selected_doctrines`／`selected_tenets` 检查互斥，并提供 actor 上下文。融合不能把双方的所有婚姻、神职、领袖等教义简单并集：同一单选组必须确定一个最终值，互斥核心信条、DLC 条件与宗教限定仍需有合法规则。

教义锁同样重要：`doctrine_group_types/_doctrine_group_types.info:25–39` 区分 Rite／Faith／Religion 锁。创建新 Rite、分离新 Faith、迁移到不同 Religion，可能分别清除对应教义。**预览时能选到，不能代替最终创建、分离之后仍保留的证明。**

### 5.3 “创建新礼仪”和“创建新信仰”不是两个随意换名的结果

`common/defines/00_defines.txt:831`：`RITE_CREATION_DIVERGENCE_FAITH_THRESHOLD=100`，原生创建草案达到该分歧值会产生 Faith；`:833` 的异端阈值为 `65`，是另一项规则，不能混用。GUI `window_rite_creation.gui:506–522` 分别显示当前分歧、异端阈值和将创建 Faith 的判断。

两个相同 Faith 的 Rite 融合，组合相对主礼仪的分歧仍可能过大。若走原生草案创建路线，达到创建阈值会产生新 Faith；脚本 `create_dynamic_rite` 的帮助则明确先在当前 Faith 内创建 Rite，不能未经验证就套用 GUI 的即时分支。两条路线都需要观察最终异端状态及后续分离。产品应在确认前明确结果类型，不应为了满足标签而偷偷调高全局分歧阈值。

## 6. 关键原生能力：指定内容创建动态礼仪

### 6.1 `create_dynamic_rite` 是真实 effect，且支持精确输入

原版 `common/scripted_effects/00_religion_effects.txt:1122–1129` 包装了 `create_dynamic_rite`。本轮又核实 EXE 中的真实登记与类型：

- effect 登记 RVA `0x5bd181`；entry vtable `0x48219a0`，类型为 `CEffectEntry<CCreateDynamicRiteEffect>`。
- 工厂 `0x2c95380`，真实 effect vtable `0x48219d0`；parser 为 `0x2c91b10`。
- 原生帮助文本 RVA `0x481fbb0`，并有实际 scope-expression 数组解析分支。

原生帮助明确的输入合同如下。此表是接口研究，**不是已经写入模组的脚本**：

| 字段 | 原生说明 |
| --- | --- |
| 调用 scope | Character；在该角色当前 Faith 内创建，角色成为创始者，继承其当前 Rite 的内容。 |
| `save_scope_as` | 保存新 Rite 的实际 scope。 |
| `convert` | 是否让创始者改信新 Rite，默认 `no`。 |
| `core_tenet_override_entry` | 可重复的 tenet scope，支持 `tenet:some_tenet` 和 `scope:saved_tenet`；最多 `FAITH_CORE_TENETS_CAP` 个。 |
| `doctrine_override_entry` | 可重复的 doctrine scope；同组替换，没有同组项则添加。 |
| `target_divergence` | 默认 `0`，此时忽略随机补分歧目标；非零且显式覆盖不够时，会再随机调整以接近目标。 |
| `include_unknown` | 随机挑选是否可包含创始者未知项目，默认 `no`。不能据此猜定显式覆盖的全部知识规则。 |
| `override_tenets_first` | 随机调整时优先核心信条还是教义；默认 `yes`。 |

名字与图标会根据**覆盖之后**的内容生成。对于要求选什么就生成什么的融合，候选路线应保持 `target_divergence=0`，避免主动要求随机补齐；同时仍需验证其他创建阶段和后续钩子不会改变已选结果。

### 6.2 核心信条能否精确得到三个选项

帮助文本把核心信条覆盖描述为替换创始者最不喜欢的项目。进一步的实码追踪表明，这并非逐条随意替换一个槽位：原生构造路径会先汇总、去重目标集合，再在不足上限时从原有核心信条补充；原有核心若未入选，会降为较低状态，选中项及新增目标成为核心。

当前 `common/defines/00_defines.txt:907` 的 `FAITH_CORE_TENETS_CAP=3`。因此，在**三个 scope 有效、互不重复，且目标分歧不要求随机补齐**等前提下，构造器层有能力承载精确的三个目标核心集合。它支持双来源选择的核心需求，强于“只能碰运气生成”的判断。

仍需区分两件事：未入选的旧核心可能作为较低状态继续存在，不能说已彻底删除；构造器输出也不等于后续改宗、分离、保存和冷重载之后的最终状态已经通过。详细地址与切片以[二进制回执](evidence/binary-observations.json)为准。

### 6.3 创建 effect 不自动等同于原生 GUI 全流程

直接调用 effect 与点击原生创建按钮是两条入口。原版 `common/on_action/religion_on_actions.txt:442` 明确说明 **`create_dynamic_rite` 跳过 `on_rite_created`**。原生按钮触发的创建链在 `:418–456` 会处理朝廷、领地、初创保护和后续转换窗口；不能认为调用 effect 后这些都会自动发生。

融合应有自己的共享完成路径，围绕实际新 Rite 统一处理来源记录、收费、创始者与采用范围、通知、冷却和保存；如果复用原版 helper，必须使用其真实前提。不能盲目补发整个 on_action，制造重复转换、错误 scope 或重复收费。

同样，effect 注册成功不保证已经执行了原生 GUI 的 `CanPick`、知识、资源与创建次数检查。若采用脚本创建路线，需要明确哪些仍由原生能力判定、哪些由新产品资格规则负责，并验证预览和提交一致。

## 7. 宗教融合的落点与跨宗教限制

### 7.1 独立 Faith 有原生入口

`detach_rite_to_new_faith` 已核到真实 effect 登记 RVA `0x5bd391`、类型 `CDetachRiteToNewFaith`。原生帮助说明：将目标 Rite 从当前 Faith 分离，创建新的 Faith，并支持保存实际结果 scope。原版 `common/scripted_effects/pam_effects.txt:6749–6759` 用它宣布礼仪为异端；新建 Faith 的原生生命周期也由 `religion_on_actions.txt` 的创建钩子处理。

因此，“创建融合 Rite，再形成独立融合 Faith”有具体接口基础。仍需核实新 Faith 的主礼仪、创始者、领袖、圣地、热忱及旧 Faith 关系；不能将分离当成无成本改名，更不能用原版宣布异端的整套处罚效果冒充中性融合。

### 7.2 合并既有信仰与创建第三个结果不同

`set_parent_faith` 已核到真实类型 `CSetParentFaithEffect`。原版 `pam_effects.txt:7383–7419` 的合一教会逻辑使用它迁移已有礼仪，注释明确信徒随礼仪一起迁移；`00_major_decisions_scripted_effects.txt:832–869` 的弥合分裂也使用它。

这是“把某个 Rite 归入另一 Faith”的能力，**不是两个 Faith 自动混合教义并产生第三个 Faith**。对现有 Rite 直接迁移还可能影响其全部信徒，因此不应作为创建新融合结果的无声前置操作。

### 7.3 跨 Religion 内容吸收需要一个明确归属

动态 Rite 默认产生于创始者当前 Faith。可研究让结果保留 A 方 Religion 分类，并吸收 B 方允许的信条与礼仪内容，再按需分离新 Faith。这样产生的是有双来源历史、单一原生归属的融合信仰。

跨宗教的限制不是只有一个按钮门：

- 部分组的 `is_available_on_create` 直接检查 Religion，见 `doctrine_group_types/00_doctrine_group_types.txt:118,126,134,182,191`。
- Rite／Faith／Religion 锁会在不同层级变化时清理内容。
- 神职、领袖、圣地、伟大工程、特有事件与局势还可能直接检查 Religion 或特定 Faith，不会仅因复制某个参数就全部启用。
- 敌意、圣战、婚姻、罪恶／美德等会消费最终归属和最终教义，需以实际结果验证。

本轮没有证明 `set_parent_faith` 对任意跨 Religion 目标都无条件成功，也没有证明可以复制对方全部固有机制。报告保留可研究路线，不把“没有闭合”写成“绝对不可能”。

### 7.4 双来源谱系与双方关系

已观察的原生结构不提供文化式双亲 Faith／Religion 关系。可以评估让新结果保存两个来源 Rite、来源 Faith 以及创建时的所选内容，作为模组自己的融合历史；名称、创始者或当前 Father Faith 都不能代替两个来源的稳定身份。

这也不自动带来“双方都视结果为正信”。原版敌意由单一归属、教义、领袖及其他规则共同决定，且可能有方向差异。如果希望获得文化式的双方友好关系，需要另定规则并验证两个方向的实际敌意；不能仅加一个好感修正就宣称原生敌意已经改变。

## 8. GUI 建议：保留文化融合体验，接礼仪数据

建议的信息结构为 A 来源／B 来源／结果三栏，按核心信条、主要教义、婚姻、罪行、神职等组选择，明确每项来源。共同项只显示一份，互斥项需要选择，不能对两个单选值同时打勾。预览显示最终所属 Religion／Faith、将新建 Rite 还是 Faith、分歧风险、费用、领袖与采用范围。

**来源二的选择已有可复用的原版 controller。** `gui/decision_view_widgets/decision_view_widget_select_rite.gui:1–52` 使用 `select_scope_object`，将条目转成 Rite，提供选中、禁用、名称和图标；`common/decisions/10_religious_decisions.txt:2176–2228` 有从 Religion 遍历 Faith／Rite、填入 `item_list` 并在 effect 消费 `scope:selected_item` 的完整先例。可将玩家当前 Rite 作为来源一，决策选择器选来源二，再进入融合对照窗口。

`common/decisions/_decisions.info:270–368` 同时说明一个决策最多嵌入一个自定义 widget，玩家选项与 AI 选择有各自接口。宗教页的 `RiteWindow.GetFaiths`／`FaithItem.GetRites` 可供浏览参照，但条目可见不代表可融合；选择资格应使用产品明确规则。

原版已有双 Rite 显示的直接参照：`gui/shared/portraits.gui:2317,2331` 从 Situation 的 `schism_mainline_rite`／`schism_competitor_rite` scope 变量取得两个 Rite 并显示图标；其生产者为 `common/scripted_effects/pam_effects.txt:11930–11941`。这证明原生 GUI 能通过 scope 变量绑定两个礼仪对象，不能据此外推现有 `RiteCreationWindow` 已支持双来源注入。

两种候选路线：

| 路线 | 优点 | 主要成本与限制 |
| --- | --- | --- |
| 双来源选择页 → 原生礼仪创建器 | 复用原生报价、合法候选、最终确认和大部分外观编辑 | 尚无把任意双来源选择整体注入真实草案的公开接口证据；若只能人工重选，体验可能不符合需求。 |
| 独立融合窗口 → scripted GUI → `create_dynamic_rite` 等原生 effect | 能严格表达双来源、单组选择和融合专属规则；已有显式覆盖能力 | 需要自行维护候选、报价、提交前重验和完成路径，不能假称自动具备原生窗口的全部守卫。 |

**目前第二条的创建路径证据更完整；第一条的直接草案注入仍待证。** 可先原型验证数据创建，再确定是否需要完整独立窗口，避免先复制大 GUI，最后发现提交方式不支持所选内容。

`gui/scripted_widgets/_scripted_widgets.info:1–9` 明确允许注册原生代码没有直接引用的独立 widget。因此可以评估“决策选择来源二 → 脚本保存来源 → 独立融合窗口 → scripted GUI 提交”的接入方式，减少整文件覆盖。该注册只创建 widget，**不会注册新的 native GameView/controller**，不能凭此编造一个新的 `OpenGameViewData` 名称。同路径 `.gui` 整文件覆盖会增加升级及其他 UI 模组冲突，见仓库 [GUI 机制笔记](../../docs/gui-system.md)。本轮没有复制或覆盖原版 GUI。

图标和本地化也要使用真实 API：EXE 帮助中存在 `set_rite_name`，支持名称、描述、形容词、单复数信徒名的 key／动态描述；动态创建还会按最终内容生成图标与名称。但本轮没有证明独立融合窗口能把任意输入文本、颜色、图标全部写入原生对象，不先承诺与文化外观选择器完全等价。

## 9. 尚需形成的玩法规则

以下是后续规格问题，不是本轮已替用户确定或实现的限制：

| 问题 | 建议的首轮研究取值 |
| --- | --- |
| 两种功能的边界 | 礼仪融合创建第三个 Rite；宗教融合评估创建第三个 Faith，并明确其 Religion 归属。 |
| 哪些目标可选 | 先研究当前领地、相邻领地或已接触的 Rite；不能把全世界任意两个对象默认为已经相互接触。 |
| 双方贡献 | 双方各至少一个不同内容；共同项不计作独立贡献，避免把普通改革换名为融合。 |
| 核心信条 | 遵守当前上限与有效候选；不默认把两边六个核心全部保留为核心。其他信条状态需要明确展示。 |
| 宗教特有教义 | 按归属、锁与实际可用性处理；不能全量照搬。 |
| 接纳、费用和冷却 | 可参考文化流程，具体数值另定；不硬搬文化 40 接纳度、1000 威望或 50 年。 |
| 人物与领地采用 | 明确本人、朝廷、封臣、伯爵领各自范围；两来源全体信徒不应被默认为强制转入。 |
| AI 与多人 | 玩家主链验证后再接同一共享规则；未实测前不承诺 AI 自动融合或多人同步通过。 |
| 新旧档与来源变化 | 保存后能恢复来源与选项；来源礼仪后来改制、迁 Faith 或消亡时，仍能解释创建时的历史。 |

## 10. 下一阶段的最小验证顺序

下列验证**均未执行**。用户本轮明确要求先研究，故不以报告完成为依据自动进入实现。

1. **同 Faith 创建闭环。** 选两个已存在 Rite，传入三个有效且不重复的核心 scope，以及来自双方的若干教义；`target_divergence=0`。确认新对象身份、最终三核心、旧核心的剩余状态、同组覆盖及两个来源不被改写。
2. **创建后生命周期。** 验证 `convert=no/yes`、实际创始者、费用／冷却以及 `on_rite_created` 的真实覆盖差异；检查知识、互斥、无效或重复 scope 的实际行为，不能仅以 effect ACK 判通过。
3. **独立 Faith。** 以实际新 Rite 做分离，确认 Religion、主礼仪、教义锁清理、领袖、圣地和双方敌意；原版自然高分歧创建与显式分离分别验证，不能互相替代。
4. **GUI 完整链。** 使用真实入口完成目标选择、内容选择、预览、取消与提交。取消不生成对象或收费；多人或窗口打开期间局面变化时，提交消费实际最新合法状态。
5. **传播与持久化。** 观察人物／领地采用、原版近亲改宗连带及真实后态，再保存并冷重载验证结果、来源与冷却。仓库已有[婚后改宗传播笔记](../../docs/grammar/ck3-120-rite-change-family-propagation.md)，不能假定 setter 只影响一个角色。
6. **代表性跨宗教组合。** 先选一对明确有差异的宗教，验证受限组、特有脚本和敌意，不将单例通过外推为全部宗教互融。

未来实机复用仓库公共验收流程及当次机器／runtime 绑定。新增构建、生成、分析工具按 Java + Maven + Quarkus 规范建立，默认 `mvn` 须逐机核验且不低于 3.10.0；CK3 游戏内脚本与 GUI 保持原生格式，普通玩家安装不应因此需要 Java 后端。

## 11. 风险排序与当前交付边界

最值得先验证的是**精确组合经过全部创建后处理后是否仍精确、Rite／Faith 结果类型是否正确、GUI 能否表达并提交同一选择**。这三项直接决定用户要求的功能能否成立。跨宗教特有机制、领袖、圣地与传播应跟随已选产品范围逐项验证，不为理论上的所有组合先展开全量矩阵。

当前交付是研究报告、来源 SHA 和有限反汇编证据；没有模组生产代码，没有功能实测、多人通过、性能结论、发布或缓存验收。报告中的候选、建议与未来验证不写成已经实现。

## 12. 存储与来源保留

本任务读取并沿用仓库[通用存储策略](../../docs/storage-retention-policy.md)与[版本化参数](../../docs/storage-retention-policy.json)，`policy_version=1.0.0`。任务开始及闭场容量、协调账本来源和实际输出大小见[来源回执](evidence/source-observation.json)。只新增小型文档和证据摘要，不复制安装树、EXE、存档、完整文本导出或全量反汇编。

本次没有进行重型写入准入，未知的项目占用、系统增长预留与生效配额保持未知，不拿别的闭场任务准入或单次空闲容量当作本任务预留。没有删除资产，也没有部署自动回收器。记录类资料按 180 日复核；安装升级后以新版本重新核相关入口，不改写本轮历史来源身份。
