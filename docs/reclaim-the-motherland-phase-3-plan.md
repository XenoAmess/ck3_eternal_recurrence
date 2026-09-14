# 《重整河山》三期需求静态分析与版本计划

状态：**release-complete；已并入联合 `0.4.0`，源码树 L1、Workshop、fresh-cache L3 与永久 changelog 全部 GREEN**

计划版本：原拟 `0.3.0`，实际与四期合并为 `0.4.0`

产品目录：`mod_reclaim_the_motherland/`

Steam Workshop item：`3798404599`

分析基线：CK3 `1.19.0.6`、《溥天之下 / All Under Heaven》、本项目 `0.2.0`

> 实施结论（2026-09-14）：静态候选 `single_heir_succession_law + always_follows_primary_heir` 能生成正确主继承人，但真实死亡事务仍会销毁空法理动态霸权。最终窄修复把同一 title object 设为“销毁但不删除”，在死亡前冻结引擎已算出的主继承人、直属忠臣 realm 与九席 incumbent，并在次日恢复同一 title object；执行复辟时再恢复“销毁即删除”。源码树 R0024 已证明同一后朝、忠臣封臣树、个人伯爵领、唯一官署 entitlement 与九席全部跨死亡延续。

## 1. 三期目标与优先级

三期建议只交付两个目标，并按以下优先级推进：

1. **P0：后朝霸权可靠继承**。后朝持有者死亡时，动态的“后唐／后宋”等霸权必须由其主继承人继承；保留下来的直属封臣树继续属于同一后朝，不得因为顶级头衔失效而全部独立。只有角色确实没有合法主继承人时，才允许按游戏正常无嗣逻辑处理。
2. **P1：保留前朝三省六部班底**。进入群雄割据后，只要前朝仍是当前唯一有资格延续帝国官署的后朝，就保留原来的九个部院官职及合资格的原班大臣；只让实际随叛军离朝、死亡或失去任职资格的人离任，再补足真正出现的空缺。

两个目标有关联但必须分开验收。P0 是已经影响跨代游玩的缺陷，必须先独立闭环；P1 不得成为继承修复的前置条件。

## 2. 静态分析结论

### 2.1 后朝继承：可行，且修复面较小

当前 `rmtm_create_restoration_hegemony_effect` 创建动态霸权后设置了：

```text
set_always_follows_primary_heir = yes
```

但没有给动态头衔添加任何显式的 title succession law。`_landed_titles.info` 对该字段的定义只是“该头衔是否总是由主继承人继承”，它不是一条产生继承顺位的继承法。当前二期实机验收验证了动态头衔创建、空法理、保存重载与复辟，却没有真正执行“旧天子死亡 → 儿子继承”的生命周期用例，因此没有覆盖用户现在报告的断裂。

原版《溥天之下》提供了高度相似的静态对照：`tgp_create_meritocratic_ruling_regent_title_effect` 创建一个单独继承的动态礼仪王国后，会明确执行：

```text
scope:monarch_title = { add_title_law = single_heir_succession_law }
```

这说明动态 titular title 若要可靠地产生继承顺位，原版做法不是只依赖 title flag，而是显式添加单继承人头衔法。`single_heir_succession_law` 使用“继承／子女／年长者／单继承人”模型；天朝制／功绩制独立统治者也在该继承法的许可范围内。

因此，当前最强的静态判断是：

- **空法理本身不是直接原因**。空法理只表示没有法理子头衔，不会自动等于不可继承。
- **缺少显式 title succession law 是最可能的直接原因**。现有 `always_follows_primary_heir` 应保留，但不能继续把它当成完整继承合同。
- 最小修复候选是在动态后朝授予旧天子后，为它添加 `single_heir_succession_law`，再让 `always_follows_primary_heir` 保证它和角色主继承人一致。
- 最终因果仍须由一次受控死亡实机用例确认；静态分析不冒充已经完成该运行时证明。

### 2.2 旧存档必须迁移

只修改新建后朝的创建 effect，会让 `0.2.0` 既有存档里的动态后朝继续缺少继承法。三期必须同时提供一次版本化迁移：

1. 新建后朝时立即添加继承法。
2. 新游戏／读档初始化时，枚举带 `rmtm_restoration_hegemony = yes` 标记的既有头衔。
3. 只对缺少 `single_heir_succession_law` 的后朝补法，不改变其持有者、名称、纹章、首都、法理或恢复进度。
4. 迁移后验证 `current_heir` 存在且与持有者的主头衔继承人一致；如果角色本来就没有合法主继承人，记录为正常无嗣而不是强造继承人。
5. 迁移必须幂等；同一存档重复加载不重复产生通知、声望费用或其他玩家可见副作用。

不建议用死亡 on_action 强行把所有封臣逐一转给儿子。正确的顶级头衔继承应让 realm 层级自然随主头衔延续；逐封臣抢救会绕过正常继承、战争和契约规则，反而扩大风险。只有显式继承法在实机中仍无法生成正确 `current_heir` 时，才评估窄范围的 succession repair，而不是一开始就做双重接管。

### 2.3 三省六部：可以保留，但不是删一行代码

当前全部大臣离开有两层确定原因：

1. `rmtm_chaos_shattering_effect` 对全部 `former_vassals` 明确执行 `destroy_held_ministry_titles_effect = yes`，会销毁其持有的部院头衔。
2. 原版 `tgp_has_access_to_ministry_trigger` 同时要求统治者持有 `h_china` 且采用天朝政体。后朝建立后旧天子失去 `h_china`，因此四个额外部院席位立即失效，五个标准内阁席位也不再按部院官职运行。

原版九个官职头衔为：

- `e_minister_chancellor`
- `e_minister_censor`
- `e_minister_grand_marshal`
- `e_minister_of_personnel`
- `e_minister_of_revenue`
- `e_minister_of_rites`
- `e_minister_of_war`
- `e_minister_of_justice`
- `e_minister_of_works`

它们都是 `h_china` 下的全局唯一无地头衔，并设置了 `destroy_if_invalid_heir = yes`。四个额外 council position 直接用 `tgp_has_access_to_ministry_trigger` 作为有效性门禁；五个通用 council position 也用同一 trigger 切换成部院名称、候选规则和授官效果。因此只跳过 `destroy_held_ministry_titles_effect` 会留下很快失效的头衔，并不能真正保住三省六部。

### 2.4 推荐保留范围

三期建议保留的是：

- 九个部院席位和对应官职头衔；
- 原班大臣的实际 council 关系；
- 官职既有的任务、修正、候选资格和正常后续替换；
- 后朝仍无新天子时的官署连续性。

三期不建议把以下内容一并伪装成仍然拥有天命：

- 只对 `h_china` 开放的天朝大工程和国家特权；
- 与新王朝天命、稳定期和正统性直接绑定的效果；
- 完整的 `grand_secretariat` 权力分享／摄政制度。

最后一项需要特别说明：原版 `on_diarch_change` 明确规定，统治者不再持有 `h_china` 时结束 `grand_secretariat`。同时该制度的候选评分多处直接读取 `title:h_china.holder`。若要完整保留它，需要大范围复制或覆写原版 diarchy on_action，兼容风险远高于“保留九席与原班大臣”。三期推荐让正式的中书门下权力分享制度随天命中断，但让三省六部作为前朝官署继续办公；这既符合“前朝霸权尚存”，也避免后朝在割据后仍拥有全套新天子权力而过强。

### 2.5 官署只能有一个当前归属

九个 `e_minister_*` 是全局唯一静态头衔，而本 mod 允许多个历史后朝并存。因此不能让多个后朝同时拥有各自完整的一套原版官职头衔，否则同一官职会在不同朝廷之间反复转移。

推荐规则是“官署随最近失去天命的朝廷”：

- `h_china` 无持有者时，最近一次从 `h_china` 转成后朝的统治者获得前朝官署资格。
- 更早的后朝仍保留其后朝霸权和复辟资格，但只有普通 council，不再占用九个全局官职。
- 任何人取得 `h_china` 后，九个官职回归当前天子；旧后朝的官署资格暂停，但人物可以继续作为普通廷臣或普通 councillor 留在旧主身边。
- 新一轮群雄割据再次销毁 `h_china` 时，官署资格转给这次最新失国的后朝。

这条单归属规则是兼容原版全局 title 模型的最小方案。若以后要求多个后朝同时拥有完全独立的三省六部，就需要另立九套动态／复制官职、重做五个通用 council position 的授官分流和相当一部分 UI／事件判断，应作为单独大版本，不应混进本期。

## 3. 三省六部的具体保留策略

### 3.1 人员口径：优先原班，不额外随机清洗

建议把“内阁人不动或者少量离开”定义成确定性规则，而不是再掷一轮随机数：

- 群雄割据前先冻结九个官职各自的 incumbent。
- incumbent 在二期忠诚结算后仍属于旧天子的 realm、仍存活并满足原版 councillor 基础资格，就原位留任。
- 如果 incumbent 本身是有地诸侯，并已经按二期规则叛离旧天子，则随自己的势力离朝并失去前朝官职。
- 因死亡、失能、宗教／性别法律或其他原版硬资格而不再可任职者正常离任。
- 不因为普通低好感、野心或一次额外随机判定清洗现任大臣。二期已经决定谁留朝，三期不重复掷骰。
- 只对真正空出的席位调用补缺逻辑；先从留朝 realm 中选择原版合法候选，不重置仍然有效的 incumbent。

这样通常会保留绝大多数原班人马，少量离开也能由“本人随叛军离朝”或原版硬资格解释，而不是凭空发生。

### 3.2 官署资格 trigger

覆盖原版 `tgp_has_access_to_ministry_trigger`，保留原有条件并加入受限的后朝分支。语义应等价于：

```text
采用天朝政体
AND
(
  持有 h_china
  OR
  (
    持有当前官署归属标记的后朝霸权
    AND h_china 当前无人持有
  )
)
```

原版注释本身说明该判断被封装成 scripted trigger，目的就是便于统一调整。通过一个受哈希锁定的 trigger override，可以让四个额外席位和五个通用席位继续沿用原版 council 定义，不需要复制整套 council 文件。

后朝分支必须继续要求天朝政体。若角色因其他机制变成封建、游牧或其他政体，则不应只凭后朝头衔获得三省六部。

### 3.3 群雄割据事务顺序

推荐按以下顺序修改 `rmtm_chaos_shattering_effect`：

1. 在任何头衔／封臣变更前冻结九个 incumbent、原 council position、旧天子和二期候选名单。
2. 完成二期尊王派一次性忠诚结算。
3. 创建动态后朝，授予当前官署归属标记，并在销毁 `h_china` 前让扩展后的 ministry access 已经成立，避免出现一帧“官署无效”。
4. 销毁 `h_china`，继续现有独立、改国号保护和层级重组。
5. 对仍在旧天子 realm 且资格有效的 incumbent，跳过 `destroy_held_ministry_titles_effect`。
6. 对已经叛离或不再合格的 incumbent，执行原版官职销毁／离任流程。
7. 在裂解事务结束后的受控 reconciliation 中复核九席，只补真正空缺；不得对全部九人重新执行一次 `got_minister_position_effect`，避免重复触发迁居、修正、参与者和权力分享副作用。
8. 复核官职头衔首都仍跟随旧天子首都，且九席没有落到另一个后朝。

### 3.4 后续交接

- **后朝持有者死亡**：后朝霸权先按 P0 继承；九席继续属于继承后的同一 realm。大臣不因换君自动清洗，按原版 council／任职资格处理。
- **原后朝宣称复辟**：先获得 `h_china`，再销毁后朝霸权。官署 access 从“后朝分支”无缝切回“`h_china` 分支”，不重建全部大臣。
- **别人先宣称天命**：官署归属回到新天子。旧后朝保留霸权与复辟资格，但不与新天子争抢全局唯一的九个 `e_minister_*`。
- **再次进入群雄割据**：新的失国者成为最近前朝官署继承者；旧的多个后朝继续存在，但只有最新前朝保留完整九席。

## 4. 计划工作包

### P3.0：合同、兼容基线与观测

- 把本文件冻结为三期权威计划。
- 更新当前 README，明确 `0.2.0` 的死亡继承是已知缺陷，撤回“已经可靠跨代传承”的过度声明。
- 为后朝 title law、`current_heir`、官署归属、九席 incumbent 和离任原因增加 development acceptance 观测；正式 staging 排除验收专用内容。
- 锁定本期涉及的原版 trigger/effect/council/on_action 源文件哈希。

### P3.1：后朝继承与旧存档迁移

- 新建后朝时添加 `single_heir_succession_law`，保留 `set_always_follows_primary_heir = yes`。
- 增加一次幂等的旧存档迁移，为带标记但缺法的既有动态后朝补法。
- 静态断言不修改 title name、CoA、capital、de jure children、持有者和 restoration marker。
- 先独立完成“死亡前继承预览”和“死亡后 realm 连续性”验收，再进入官署开发。

### P3.2：前朝官署资格与单归属

- 增加“当前官署归属后朝”耐久标记和对应 scripted trigger。
- 最小覆盖 `tgp_has_access_to_ministry_trigger`，原版分支逐字保持，后朝分支只在 `h_china` 无持有者时开放。
- 多后朝情况下只允许一个 entitlement；新天子和新一轮失国的交接必须确定、幂等。
- 不扩张 `h_china` 专属大工程、天命和稳定期特权。

### P3.3：原班大臣保留与空缺补任

- 冻结九个 incumbent，并与二期忠诚结算结果对接。
- 从群雄割据的统一官职销毁段中排除仍在旧朝且合法的 incumbent。
- 实现一次受控 reconciliation：保留有效现任，只清退实际离朝／失格者，只补真实空缺。
- 明确 `grand_secretariat` 不在本期保留范围；确保它正常结束不会连带清掉九席。

### P3.4：回归、发布准备与公开文案

- 扩展独立 mod 的静态校验、release allowlist、旧存档迁移和兼容哈希检查。
- 更新中英 README、游戏内说明和 Workshop BBCode；只有再次收到明确发布指令时，才补齐其余七语并进入正式发布闭环。
- 正式发布时按现有 item `3798404599` 更新，完成 source L1、fresh-cache L3、订阅缓存复核、Change Notes 和永久 `0.3.0` changelog。

## 5. MCP 优先验收方案

### L0：静态与离线预验

- 先判断 `open_kaishek` 对 title law、scripted trigger、scope 和 on_action 的确定性语法子集；可覆盖的先离线预验，不支持的诚实记录 `not-applicable`。
- 验证新后朝和迁移后的旧后朝都具有 `single_heir_succession_law` 与 `always_follows_primary_heir`。
- 表驱动验证官署 access：`h_china` 持有者、唯一获授权后朝、未获授权旧后朝、非天朝政体后朝、`h_china` 已被他人持有。
- 验证九席列表无遗漏、无重复；群雄割据清退只命中实际离朝／失格者。
- 验证“原版群雄割据”规则完全绕过三期全部逻辑。
- 验证旧 `0.2.0` 存档迁移幂等，且 release staging 无 acceptance-only 标记。

### L1：受控源码树实机

在取得 CK3 排他槽后，使用原生 MCP 状态与命令优先完成：

1. 创建后朝后读取旧天子、主继承人、后朝 title ID、`current_heir`、title law、直属封臣和法理子头衔基线。
2. 保存重载，确认上述身份不漂移。
3. 令旧天子死亡；确认同一后朝 title object 由原主继承人持有，名称／纹章／marker／空法理不变。
4. 确认至少一个留朝直属诸侯及其完整封臣树仍以新后朝君主为 top liege，复辟决议仍由继承人承接。
5. 在群雄割据前记录九席 incumbent；割据后确认所有仍在旧朝且合法者保持同一人物、同一 position 和同一 minister title。
6. 安排一名兼任有地叛离诸侯的大臣，确认其随叛军离朝并只补该席空缺。
7. 保存重载并推进一次常规 council tick，确认九席不会延迟崩解。

### L2：生命周期与冲突矩阵

- 后朝连续死亡两代，顶级头衔和留朝 realm 均不裂解。
- 后朝持有者无合法继承人的正常边界。
- `0.2.0` 既有存档加载后补法，再死亡继承。
- 原后朝复辟：官署无缝切回 `h_china`，后朝头衔按决议销毁。
- 另一军阀先取天命：九席转入新天子体系，旧后朝不丢失自身霸权与复辟资格。
- 多个后朝并存：只有最新官署归属者拥有九席，不发生头衔来回抢夺。
- 与二期忠臣留朝／叛离、国号不变和完整封臣树全部联合回归。

### L3：正式 staging 与 fresh-cache

- 从正式 staging 而不是源目录执行同一关键矩阵。
- 通过订阅缓存读取后复核 title law、死亡继承、九席 incumbent、单官署归属和复辟交接。
- 保存真实游戏截图：死亡前继承界面、死亡后同一后朝与 realm、割据前后九席对照。截图是展示证据，不替代 MCP 状态证明。
- 自动报告、截图和日志不等于人工签核；正式发布前仍须完整人工审阅。

## 6. 验收退出标准

`0.3.0` 只有同时满足以下条件才可标记完成：

- 新建后朝和 `0.2.0` 旧存档后朝都能由主继承人可靠继承。
- 继承后不是只剩个人直辖领土；至少受控样本中的留朝直属封臣树完整保留。
- 后朝名称、CoA、capital、空法理、restoration marker 和复辟资格跨死亡保持。
- 群雄割据后九席中所有“仍在旧朝且合格”的 incumbent 不变；离任均有实际叛离或原版硬资格原因。
- 空缺补任不重置其余现任，不重复触发全部授官副作用。
- `h_china` 和前朝官署永不同时归属于两个朝廷；多后朝场景没有全局官职争抢。
- 正式 `grand_secretariat`、天朝大工程和天命专属权力没有被错误授予无天命的后朝。
- 原版游戏规则分支与 `0.2.0` 的忠臣／国号／复辟链全部回归 GREEN。
- 发布时完成构建、source L1、fresh-cache L3、Workshop 更新、订阅缓存复核和永久 changelog。

## 7. 风险与取舍

| 风险 | 处理口径 |
| --- | --- |
| `single_heir_succession_law` 添加后仍没有 `current_heir` | 先保留 RED 证据并检查角色政府／主继承人；只有证明 title law 不足时才增加窄 succession repair |
| 旧存档动态 title 难以枚举 | 以耐久 `rmtm_restoration_hegemony` marker 为唯一迁移选择器，不按名称猜测 |
| 删除官职清退后出现延迟失效 | 先保证 access 在销毁 `h_china` 前连续成立，再做一次受控 reconciliation，不用循环重授全部九席 |
| 多后朝争用全局 minister titles | 强制单一官署 entitlement；不在本期复制九套官职 |
| 后朝保留全部天朝能力导致过强 | 只延续 council 九席与官员，不开放 `h_china` 专属大工程、天命和正式 Grand Secretariat |
| 大范围原版 override 难维护 | 优先覆写封装好的 access trigger，并对原版源文件做 SHA-256 锁定；不复制 council position 全文件 |

## 8. 静态证据基线

本次分析没有启动 CK3，也没有占用主屏幕。关键原版文件哈希如下：

| 原版文件 | SHA-256 |
| --- | --- |
| `common/landed_titles/_landed_titles.info` | `50C05B55A2BD2EAC0C5905B6DBA58280D1301483E435AE5DBB4CF99643D5DE5D` |
| `common/laws/00_succession_laws.txt` | `F4140755CE89B2BC0C7B5BB80E9318EFD7A7AE7ECE2E8129119C2EBE9BB9C532` |
| `common/scripted_effects/10_dlc_tgp_korea_scripted_effects.txt` | `B7AB103918965364D20110B76831E8F48D53506AB673402BCFC3C9761E473940` |
| `common/scripted_triggers/10_tgp_triggers.txt` | `8294C1D72ECC909428ABFBA27D6F10B127D796D2BEE350D1BB95024F36D60C99` |
| `common/scripted_effects/10_dlc_tgp_scripted_effects.txt` | `AEF36B884DC5E315DD5C655BC96012FF9FA8BB46BB0AF2C18FA878C890907747` |
| `common/council_positions/01_ministry_positions.txt` | `891B6B129BE55D4BA4678A83B93A240BA53B3705C618C02B116F99C1A2E75272` |
| `common/council_positions/00_council_positions.txt` | `8D667AFE296D987F2E849A5C55B17EF9A98E73B9E73E925898EA2986B3155909` |
| `common/landed_titles/02_china.txt` | `342F67E4D3E27A66B05A7257493A28C32AD8C0F9D9B314C0E18BDD8261165811` |
| `common/on_action/diarchy_on_action.txt` | `C951D13FF0AF6FD31AF4201CB83C17582745DF3BD22A1CBD85F31031943869FB` |
| `common/succession_appointment/celestial_minister.txt` | `3FC234757C77302F15F2FDBD4C8A197D350FF11C6D1883C7EB66D758D8BAFD4B` |

当前 mod 直接证据：

- 后朝创建与继承 flag：`mod_reclaim_the_motherland/common/scripted_effects/rmtm_dynastic_cycle_effects.txt`。
- 当前统一销毁官职的段落：同文件 `rmtm_chaos_shattering_effect`。
- 当前生命周期验收缺口：`mod_reclaim_the_motherland/README.md` 的原阶段 C 列出死亡继承目标，但 `0.2.0` 的正式验收方案与最终实机报告都没有执行死亡事务。
