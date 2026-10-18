# Faith、当前礼仪、主流礼仪与个人信条：1.20.0.4作用域

machine_id：`4-8e1c2f1861`。2026-10-19只读核对本机现有原版资源，以及2026-10-17已封的同机1.20.0.4缓存；缓存绑定EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本包没有读取游戏进程、重算EXE哈希、启动游戏或取得新截图。逐次实际UTC和每段字节、来源SHA在下方证据中；这是静态作用域证明，不是当前Can或新的实机结果。

## 两条原生参数查询确实不同

| 原版查询 | 原生读取对象 | 智能体应核对什么 |
|---|---|---|
| Faith作用域的`has_doctrine_parameter` | 该Faith的主流Rite，再读它的布尔参数集合 | actor Faith ID、该Faith mainRite ID及其参数；不能拿actor currentRite同名参数替代 |
| Rite作用域的`rite_has_parameter` | 传入的这个Rite的布尔参数集合 | 脚本究竟把哪个Rite传进来；`root.rite`是操作人当前Rite |
| Character作用域的`has_personal_tenet_flag` | 该人物持有的个人信条定义中的个人参数集合 | 该人物实际个人信条与个人flag；不能替代前两条 |

`CHasDoctrineParameterTrigger`精确RTTI的当前vtable为`0x47BA978`；slot25指向完整`0x2B29150–0x2B291FE`。它验证Faith scope13，解析完整Faith ID，从Faith `+0x98`取主流Rite ID，再解析Rite，于`+0x7B8`调用membership `0xB9DE80`。`CRiteHasParameterTrigger`精确RTTI的vtable为`0x4785298`；slot25为完整`0x2AE9F50–0x2AE9FBE`，验证Rite scope42后直接读该Rite `+0x7B8`。所有直接跳转均落在各完整leaf内。两条不是按旧版本统一偏移猜出的别名，也没有从getter名称推断委托。

证据：[原生两条完整leaf及RTTI定位](evidence/faith-rite-parameter-scopes12004-v6/native-scope-probe-a02.json)，SHA-256 `2c7149706b205776f932dbfa220a457d8af59f296537acbe9fe9496e252d1516`。a01使用宽松类名匹配，曾包含两个`CTriggerEntry`定位项；a02只保留精确目标类，两种locator不混作语义证据。

个人分支`0x2B2BCF0–0x2B2BDBF`验证Character scope4，检查Character `+0x1C8`扩展，调用完整getter `0x28BD070–0x28BD10A`取扩展`+0x88`的个人信条集合，逐定义`+0x740`检查个人token。它不读Rite `+0x7B8`。原版`_tenet_types.info:137–144`明确个人参数用`has_personal_tenet_flag`检查；这是另一份数据，并非同名信条自动同时给三个对象授权。[原文和完整个人分支](evidence/faith-rite-parameter-scopes12004-v6/stock-and-personal-sources-a02.json)，SHA-256 `75bc24338d164e77acd68cb8ab18b956b2a42babc7ea20eeada9f45595167b5f`。

## 对采用和建筑决策的影响

定向综摄采用调用`actor.faith.faith_is_syncretic_with(F)`；`00_religious_triggers.txt:3537–3567`在Faith上查`christian_syncretic_actor`或`islamic_syncretic_actor`等参数。因此配置目标是**准备采用圣地的那个Faith的主流Rite**。合法修改既有主流Rite，或创建一个以所选Rite为主流的新Faith，均要按实际结果读回。只在旧Faith下创建一支非主流Rite，不能因此推定旧Faith取得该参数。

顺应／adoptionism的特殊采用分支则在`50_holy_site_decisions.txt:521–527`显式查`root.rite.rite_has_parameter = allow_adopt_any_holy_site`。这里读取操作人当前Rite，不能把它也改成Faith主流Rite。新旧身份、参数、目标、管理权、费用和正常最终Can仍各自核对；静态参数关系不免除其他AND条件。

综摄的两种选择具有不同效果。`00_tenet_types.txt:4119–4132 /4199–4211`的个人列表有`can_use_*_artifacts`等个人能力，却没有定向采用所需的`*_syncretic_actor`；后者在礼仪`parameters`中。顺应及adoptionism的个人列表同样没有`allow_adopt_any_holy_site`。但不能从此概括“个人信条所有参数永远无用”，应按每个实际consumer的作用域判断。

特殊建筑还要看各自脚本。有些综摄替代项读取**地产持有者**当前Rite；不能偷换成操作人的当前Rite，也不能以人物个人综摄flag代替。圣地关联、普通／主要等级属于Faith与HolySite的关系，不是每支Rite各有一套圣地名单。[建筑分支专题](special-building-religion-holy-site-gates12004.md)保留逐建筑的AND/OR和建造／启用区别。

## “某信仰认可圣物”仍然是Faith作用域

`0x2531320`并非接收一个任意Faith参数：它从圣地伯爵领持有者的当前Rite导出Faith，先检查该Faith在圣地关联集合内，然后调用`0x2530EF0(artifact, holderFaithID, null)`。后者认可条件为物品显式Faith圣化列表，或以目标Faith为root、artifact为辅助scope执行物品类型模板trigger。模板可再检查宗教、Faith或参数，不能统一说“认可只由主流Rite核心决定”。模板若使用Faith `has_doctrine_parameter`，才依照本页证明继续委托主流Rite。

因此旁白“这个信仰认可该圣物”保留Faith称谓；不要替换成每位人物当前礼仪分别计算独立总稀有度。原两函数的保留原件及SHA在[同一证据包](evidence/faith-rite-parameter-scopes12004-v6/stock-and-personal-sources-a02.json)的`recognition_reused_evidence`，其本次读取是复用既有来源，不授新实机资格。

## 原版实际栏目怎样指认

| 位置 | 原版key／实际中文 | 原版GUI路径 |
|---|---|---|
| 人物个人选择窗口 | `PERSONAL_BELIEFS_VIEW_TITLE`＝“个人信念” | `window_personal_beliefs.gui:529`的`ToggleGameViewData('personal_beliefs_window', GetPlayer.Self)` |
| 个人信条栏 | `PERSONAL_BELIEFS_PERSONAL_TENETS_HEADING`＝“你的[personal_tenets]”，即“你的个人信条” | 同GUI `151`栏头、`169–194`的`GetPersonalTenets`列表；`835`添加、`915/923`个人选择回调 |
| 创建／修改礼仪的核心栏 | GUI `[core_tenets|E]`；中文`game_concept_core_tenets`别名到`game_concept_tenets`，实际屏显“信条” | `window_rite_creation.gui:183/190`栏头与`GetTenets`；`197`打开该slot候选、`1475–1476`原CanPick与SelectTenet |

具体localization源：`gui/personal_beliefs_window_l_simp_chinese.yml:8–11,34–44`，`pam_game_concepts_l_simp_chinese.yml:156–159`，`game_concepts_l_simp_chinese.yml:1343–1347`。完整相对game路径、SHA和原文行均收入证据。讲解可以把后者说明为“礼仪的核心信条”，但指着画面时不能声称栏目实际写着“核心信条”。新并排原版截图仍待唯一runtime采集，本页只有源码证明。

## 对最终旁白的具体修订

冻结稿SHA `ee3d239d71bf9c1d5ed14eb84b41a6ad769496690b05c271e69efb48feee9b8b`有144cue，其中21cue、31处“礼仪”。逐词表、完整替换句和最终spec／两方向native-card的相关JSON pointer在[逐词审计](evidence/faith-rite-parameter-scopes12004-v6/rite-word-audit-a02.json)。31处没有应机械改为Faith的确定对象错误；需澄清C03-02/06/14/11、C07-07，另在C03-05用上表真实栏目区别个人和礼仪选择。

C03-11的“随礼仪语言”须改。`00_pam_tenets.txt:1580–1595`按原版`first_valid`条件选择继承说／义子论／嗣子论；`pam_scripted_triggers.txt:78–112`涉及所属Faith、指定Rite、是否已有预设礼仪语言以及礼仪领袖文化／语言。建议改为“依照原版的礼仪命名条件，它可能显示为……”，同时改spec的label与spoken_anchor。逐词审计只核词的对象与相关作用域，不等于影片画面、音轨和全部机制已经验收。
