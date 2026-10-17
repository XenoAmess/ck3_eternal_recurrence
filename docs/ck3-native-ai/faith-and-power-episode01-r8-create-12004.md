# 第一期R8 Create：普通智慧圣地的新实例、付款与圣物后态（1.20.0.4）

R8在W退出纳杰夫之后，以type=site_of_wisdom、barony6622、单件神器237成功创建新实例326。世界已加载registry从326行增至327行，旧行完整不变；Faith50名单独立追加326，实际支付2000虔诚。新站点是普通圣地，已实际Active、有效圣物稀有度4；其所有信徒主要圣地修正仍不适用，具体受益人属性未测。

`machine_id: 4-8e1c2f1861`；run `4-8e1c2f1861--faith-and-power--R0008`，PID21564/create1792253831.3987103。source `02eea1e57a44a733cb833038b55a5fdc7bd4302a`，a06 DLL SHA-256 `7a5ef6ca4eeb05c56d0f96b2ace2409bff704d067e66136f2b29dd253c3475c7`。以下原生事件均来自2026-10-17原件UTC字段；离线投影时间16:41:43 UTC。完整参数、回执SHA、过程身份与来源见[小证据](faith-and-power-episode01-r8-create-12004.evidence.json)。本段只结算Create链，后续保存/退出另验。

这是用户批准“允许独立机制实验存档，明确标注准备内容（推荐）”的准备场景，来源C2继承累计额外+5000虔诚及个人Maliki，非普通长局积累。R8从原C2冷载后先完成[W退出](faith-and-power-episode01-r8-abandon-12004.md)，本次Create使用W后的五站点与3250钱包作前态。没有借用R7圣物撤回后的余额、站点状态或神器所有权读回充当R8前态。

创建前的原生模型与选择经历了三个不同状态：

| 状态 | 实际选择 | 原版普通CanCreate / bypass | 其他观测 |
|---|---|---|---|
| 窗口刚开，16:27:17.324528–17.565624+00:00 | type=null，barony6622，artifacts[] | false / 0 | available/models_complete=true；10个type可pick、4地点、3神器 |
| 选择wisdom后，16:28:21.775152–22.219058+00:00 | site_of_wisdom，6622，[] | false / 0 | 原生tooltip：稀有度总和0，需要3 |
| 再选237，16:28:22.996055–23.244701+00:00 | site_of_wisdom，6622，[237] | true / 0 | rarity raw400000/scale100000=4，原按钮enabled=true |

完整候选地点为[6622,6687,6698,6701]，神器为[237,267,277]；10个type及各原生pick结果均在小证据中。选择type与237的两个typed动作分别返回ui_selection_verified，并经随后独立context核对完整已选元组；barony6622在本场选择过程中保持不变，没有虚构地点选择动作。“需要3”是本场原生提示的稀有度总和门槛，不是三件神器；这一次单件237、稀有度4即可合法。不能由此证明任意神器、任意地点或其他type组合都合法。

三个context的缓存资源向量均为[0,0,200000000,0,0,0,0,0,0,0]，scale100000，对应2000虔诚；但 `cached_quote_freshness_observed=false`，独立affordability读口也未观察、值为null。最终实际成本由同场钱包3250→1250独立确认，与本次缓存预览2000一致。不能把CanCreate=true写成独立affordable=true，也不能把该缓存当成未来任意一次创建的最终新鲜报价。

唯一 `ck3_create_holy_site_once_v1` 于16:33:54.622407–55.127089+00:00提交，绑定预览SHA `17fc5cfd94d5ece7752e258af0a94805d760d3bbddedc51b64641f7caf88f794`。原回包实际为accepted=false/available=false、dispatch_invoked=true/native_dispatch_attempted=true、status=verification_pending、create_dispatched=true，且business_outcome_observed=false，原因明确要求独立世界后态。accepted=false在这里不证明未提交或失败；一次键已消费、重放被阻止，不能据此重发。

后续独立证据形成成功链：

| 查询 | 原件时间（2026-10-17，+00:00） | 实际结果 |
|---|---|---|
| 钱包snapshot | 16:33:55.368604–55.610583 | 1250虔诚；public/native revision5/4，date51394920且paused=true |
| 完整当前Faith名单 | 16:33:55.882740–56.245453 | [26,27,0,14,29,326]，相对W后唯一新增326 |
| 明确查询site326 | 16:34:53.980566–54.335305 | available/type智慧/barony6622，Faith50 available+lists=true、eminent=false |
| 独立relic326 | 16:34:55.341863–55.580445 | Active=true、有效稀有度4、库存[237]、槽0=237 |
| 独立artifact237 context | 16:34:55.795101–56.092636 | character owner=null、HolySite owner326、site equipped=true、player-owned reference=false |

W后世界loaded registry roster原有326行，Create后327行；两次roster_available=true且unreadable_slots=0，所有旧326行逐项相同，唯一新增行是{326,site_of_wisdom,6622}。两次loaded_registry_slot_count都为1024，这是registry槽容量，不能当作当前世界实例数。该世界差集加上原版Create回调来源及新对象后读，区分了本次新建实例与采用一个已经存在的站点。

当前Faith的T/E/R由5/3/2变为6/3/3，主要数仍3。旧五站26/27/0/14/29的完整已读type、barony、关联Faith及等级、库存字段都与W后相同；artifact IDs依次仍为[60]、[61,62]、[63]、[64]、[65]。0是有效Jerusalem ID。整个R8从原C2到这里总数又为6，但成员已经由32换成326；只比较数量会漏掉这个变化。实例326是本run实际发现的ID，规划器应从新读差集获取，不能硬编码为所有局面的智慧圣地。

独立relic读回中，326仅关联Faith50；county6621/barony6622的holder为玩家15893，个人rite15/Faith50，county_holder_faith_associated=true。缓存Active=true/rarity4与新调用原版rarity producer的结果一致，cache_evaluation_disagreement=false。神器237 rarity_level4、native HolySite owner326、槽0=237且槽1/2为空；其动态sanctified_faith_ids=[]，原生对玩家/县主Faith50的认可均true。空动态名单不能代替原生认可结果。

玩家个人后库存为[188,189,267,277]。本组没有单独捕获Create前237的完整owner对象或个人库存快照，只保留了原生创建候选中的237；因此严格结论是新站点持有/装入237、后态不再是玩家owned reference，不借R7前态制造R8所有权前后表。打开326后普通HolySite窗口的selected_artifact_id仍null，当前remove按钮false；创建窗口中选过237也不等于新HolySite窗口已选神器，后续动作须重新观察选择和预览。

来源定义与实际收益继续分开：

| 静态定义 | 对本实例的含义 | 实际后验 |
|---|---|---|
| site_of_wisdom的county_holder_character_modifier：learning=2；county_modifier_scaled按有效稀有度缩放建造成本和development_growth | 属于县主/伯爵领层；普通或主要都可能适用 | 本次只读到Active/rarity及县主身份，未读取实际learning或县修正净值 |
| faith_character_modifier：diplomacy_per_piety_level；faith_character_modifier_scaled：两类lifestyle XP | 原版info明确要求该Faith的eminent主要等级 | Faith50实测eminent=false，这些全Faith主要修正不适用；未用创建成功授予所有信徒收益 |

类型定义 `common/religion/holy_site_types/01_dynamic_holy_site_types.txt` 72–96行，SHA-256 `30cac0199fb08edccfb6b4e96f505efa20ba0adb897846f121db80e51511e6bc`；收件人与等级合同 `_holy_site_types.info` 32–78行，SHA-256 `b7f321911c857a5214eb2681d48a700020c125377df0d7d4936928a500b6f33e`。新实例的 `world_effects_applied_observed=false/beneficiaries_observed=false`，不把缓存Active升级成所有受益人重算已验。原版Create的构造/重计费/清预览来源继续见[一次创建合同](holy-site-creation-create-once12004.md)；其中建立时的“尚无实机成功”保留为历史，本次成功只由上述独立回执追加。

供游玩智能体使用的规划规则：

1. 先完整观察模型与选择，再为type/barony/有序神器元组作决定。type可pick、artifact在候选中和最终CanCreate是不同资格层；模型available但type=null是未完成选择。
2. 每次选择后重读元组、正常CanCreate/bypass、原生warning与预览身份。稀有度按实际总和规划；一件合格神器可足够本场，不推广为任何一件都足够。
3. 预览匹配只证明配置一致。保留缓存报价新鲜度及独立affordability未知，实际成本用同场钱包结算；本次Create实付2000，不能套用W采用/退出的1000。
4. attempted/pending或accepted=false但dispatch=true时保留已消费意图，只做独立查询。窗口reset/unavailable既不证明世界失败，也不证明世界成功。
5. 成功按完整Faith差集、世界registry差集、新对象type/barony/关联/等级、钱包及库存/owner分别核实。所需字段缺失时维持该项unknown，不借窗口生命周期补齐。
6. 将普通Active与主要全Faith加成分开；评估神器供奉机会成本与地方收益后再优化。本次没有证明净收益最优，也没有授予再次创建的资格。

本组未独立读取实际奉献度、创建冷却/免费额度、王国数量、具体受益者修正、后续存档、正常闭场或媒体人审。这些保持unknown；公共完整规划器与whole-product验收不随单次Create成功自动完成。

后继补注（machine_id: 4-8e1c2f1861）：[R8 D3保存与正常闭场](faith-and-power-episode01-r8-closure.md)及[小回执](faith-and-power-episode01-r8-closure.json)补齐本篇建立后的事件。2026-10-17T16:42:44.947187–45.194231+00:00独立OS0，16:43:34.062600+00:00 CAS11495 done/resources[]；D3已保存/冻结，但Driver绑定不匹配、未冷载。public verify原exit2/research holder完成，三raw正常收尾仍未人审，whole-product业务资格不增加。原尚未闭场边界保留为当时截点。
