# 第二期R5：精神信仰领袖建制与大圣战边界

2026-10-20。本文保存本期实际完成的来源研究与原生施工边界，回答“普通圣地是否足够建制、主要名额省什么、付费后谁得到权力”。影片范围仍由[导演案](director-plan.md)与[执行计划](research-and-production-plan.md)管理。本文不是建制或大圣战已经成功的实机报告。

## 1 来源、机器与证明范围

本包的机器为 **machine_id: 4-8e1c2f1861**，写入前由 tools/ck3_live_run_id.py machine 读回。Root于2026-10-19T18:54:20.430481+00:00读取appmanifest、launcher配置和EXE的安装身份是 **CK3 1.20.0.4 / Steam build25734779**；EXE SHA-256为98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518。这不代替任何新场次的运行时、加载来源或Steam离线资格。

同机于2026-10-19T19:04:43Z—19:04:46Z读取实际game树12份来源，并与jesec/ck3-mod-base固定commit **074429b3f6d9352a3cf4c5671725fee2f41267ba** 的原始字节比较，12/12一致。镜像是资源来源，不是引擎C++源码。2026-10-19T19:53:55.363585+00:00重新读取12份实际文件，12/12仍与冻结SHA相同。实际根目录为C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game，只对上述机器及观察时间有效。

[来源manifest](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b1-a01/research/power/source-manifest.a02.actual.json) SHA-256：c1c9b5ea6baa7f421e64665b8791c041b44a1d982e0c01931876d4b175a486ae。第7节将完整来源SHA和行号写入仓库；其他机器不必具备这个绝对路径。

本R5包业务实机样本为 **0**。脚本条件、效果声明、实现候选、合成消费者检查、实际提交与独立后态分别记录，不能将以下公式补写成已扣款、已授予或已宣战。外置资料按[统一存储策略](../../../../docs/storage-retention-policy.md)复核，当前用途复核时间为2026-10-26T19:02:10.097469+00:00；固定来源知识可以按commit/SHA复核，过程原件不默认永久保留，回收后须标明不可读。

## 2 精神信仰领袖建制：显示和最终条件

人物当前Rite、Faith.main_rite、Faith和Religion是不同对象。信仰领袖来自faith.religious_head，礼仪领袖来自rite.head_of_rite；不能用任意礼仪领袖头衔、个人信条或县民信仰替代Faith制度及控制权限。

S01的create_hof_decision.is_shown要求以下AND：

1. is_landed=yes **OR** government_is_theocracy。
2. Faith具有spiritual_head_of_faith **OR** temporal_head_of_faith参数。
3. Faith不存在实际religious_head。
4. Faith没有block_from_create_hof_parameter。

is_valid还要求 **is_landed=yes**，并调用can_create_head_of_faith_title_trigger(FAITH=root.faith)。所以无地神权人物可能满足显示支，却不因此可以确认。窗口出现、条目选中和原生CanConfirm分别记录。

S02的1532—1552行优先按Faith精神参数走精神分支，其次按世俗参数走世俗分支。精神分支1488—1528行的AND如下：

| 条件 | 精确口径 |
| --- | --- |
| 特殊分裂门槛 | 仅当Faith恰为faith:christian_faith **且** situation:the_christian_church存在，额外要求全局pam_great_schism_decision_taken；不是对全部基督教Faith一律施加。 |
| 圣地 | num_realm_holy_sites_faithful_holders(COUNT=1,CHARACTER=root)。普通圣地可以计数，未要求主要。 |
| 奉献等级 | 人物Rite不是Faith.main_rite时>=3，否则>=2；S04将high_piety_level定为3、medium_piety_level定为2。等级与钱包虔诚数量分开。 |
| 制度禁止 | block_from_create_hof_parameter不得存在。 |
| 既有身份 | 人物不能已经是本Faith的religious_head。 |

S02的1405—1449行检查圣地county的 **is_holy_site_controlled_by=角色** 和 **county.holder.faith=角色Faith**。不是只看县民信仰或采用列表。控制谓词的全部政府例外未在这段脚本展开，须使用原生结果或最终许可。

邦联分支必须保留：存在confederation时，另有至少一处county同时通过本人的控制谓词和持有者Faith条件；一般COUNT分支还可计入非house-based邦联成员控制的地点。不能把经成员计数自动当作本人那项条件也通过。首例选择无邦联人物只是缩小场景。

隐藏事件还会复验。S06的.0002要求无religious_head、明确has_doctrine=doctrine_spiritual_head和精神建制trigger；.0012要求既有religious_head_title存在但无holder。带scope:rite的自动创建流程还检查其为main_rite；玩家force_create入口特意不提供该scope。Faith参数通过不代替隐藏事件的全部条件，也不证明效果发生。

这是脚本合同，实际支付能力、普通requirements设置、最后一次CanConfirm和提交仍须现场核实。独立、成年是建议场景的稳健选择，不增加为此精神决议的普遍脚本门槛；世俗分支的等级或上级头衔限制不外推到这里。

## 3 主要圣地改变哪些费用

定义 **E**：存在本Faith的主要圣地，其county通过is_holy_site_controlled_by=root，并且holder.faith=root.faith。仅有关联主要圣地、县民同Faith或其他人控制，不等于E。

S03的4094—4188行对人类精神路线给出：

- **虔诚**：200 ×（非主流Rite则2，否则1）×（E则1，否则1.5）。
- **金币或国库**：0.5 × medium_gold_max_value ×（E则1，否则1.5）。决议使用treasury_or_gold，实际币种保留原生资源槽。**金币没有非主流×2。**
- AI价格另乘0；不能用作玩家免费路线。

| 人类精神路线 | 有E的源码虔诚 | 无E的源码虔诚 | 金币/国库关系 |
| --- | ---: | ---: | --- |
| 主流Rite | 200 | 300 | 无E为有E的1.5倍 |
| 非主流Rite | 400 | 600 | 与主流同式，不额外×2 |

S04的83—114行以300为medium_gold_max_value起点；有culture时，晚期中世纪乘3、中期中世纪乘1.5、早期中世纪乘1，其余乘0.75；无culture时保留300。因此112.5、150或225等计算例不是所有人物固定价格。正式旁白采用实机官方时代名称。

表中数字是源码算式，**不是本期实际报价或成交事实**。H1保留同一actor、Faith/current Rite/main Rite、文化时代、币种和原生上下文；普通→主要的操作支出与建制费用分账。关系和缓存读回后重新取得完整十资源raw向量、affordable、requirements及CanConfirm。缺失项不能补0；requirements-bypass未知或非0不能批准普通确认，也不得为实验修改该设置。

## 4 收件人、main_rite与确定司祭路线缺口

静态调用链为：create_hof_decision.effect → S05的force_create_head_of_faith_title_effect（279行起）→ 无religious_head_title时S06的faith_creation.0002 → S05的set_up_dynamic_spiritual_hof_title_effect（383—522行）；已有空title则走S06的.0012（156—260行）。

新建和重建的收件人优先序均为：

1. 建立者是clergy：给自己。
2. 内部theological_agent_puppet与建立者同Rite：给该傀儡。
3. 外部external_theological_agent_puppet与建立者同Rite：给该傀儡。
4. 真实cp:councillor_court_chaplain与建立者同Rite：给该司祭。
5. 同Faith神权封臣：按head_of_faith_selection_weight排序。
6. 否则生成同Faith、同Rite、同culture的新神职人物。

第5支权重在S03的76—134行，包含性别教义、领地/圣地、头衔、善恶特质、奉献等级、学识与外交。本期未还原并列顺序及实际集合，不能预先点名胜者；生成范围也不是已生成角色的属性。

新title为duchy级，设置landless_title及继承/claim规则，并从圣地候选分层选择首都county。**设置首都不等于把该county领地交给领袖。** 实际title、holder、capital和上下级关系仍须后读。新建路径另保障same_faith_theocratic_succession_law；不能据此宣称重建执行同一法律操作。

**新建和重建都在建立者Rite不是Faith.main_rite时，把建立者Rite设为main_rite。** 新建写入在S05的497—505行，重建在S06的251—258行。非主流Rite不仅多付虔诚，也会通过这条建制声明取得主流地位；这不等于创建新Faith或人物自动改信。人物FaithID、人物RiteID和Faith.mainRiteID分别读回，不能预填后态。

force_create另声明增加Faith的major_fervor_gain，并安排次日.1010/.1011通知。即时头衔后态和稍后通知分开，ACK不证明授予；未推进到通知时不伪造它已经出现。

### 4.1 确定宫廷司祭路线尚未实际合格

建议首例是非神职、有地、无邦联玩家，精神制度，无实际领袖且无title，current Rite=main Rite，一座受控且县主同Faith的普通圣地，奉献等级至少2，真实宫廷司祭与玩家同Rite。

这只是**准备目标，不是已找到合格存档的事实**。要保证司祭收件，必须实际证明玩家非clergy，而且内/外两种同Rite神学傀儡不抢先。已有clergy appointment读口能核真实incumbent与双方Rite；本轮未找到已验公共观测完整证明前序clergy/puppet输入。准备清单、人物称号、任意主教或“你的总主教”不能代替。

因此仍需有限原生输入：actor.is_clergy、两固定puppet的fullID与Rite或实际absence、真实cp fullID与Rite。前序任一unknown，就不能称“确定会给司祭”；没有typed getter来源时先定位，不猜偏移。

新Faith创建时若已满足自动建制条件，可能已经产生领袖而使决议隐藏。应先读head/title，不改原版trigger、不直接调用force_create代替玩家决议。独立实验准备明示，不计普通战役成绩。

普通统治者付费后若头衔给司祭，建立者**没有因此成为能亲自发动精神大圣战的信仰领袖**；谁付费和谁获得直接操作权需要分别解释。

## 5 大圣战的三个层次

### 5.1 Religion级解锁

S07的1278—1295行在faith月度事件表列出.0010与.0001。它证明authored入口，不证明本月已运行、实际调度时间或缓存已刷新。

S08的.0010（1047—1192行）在Faith scope下要求以下AND：

1. suitable_faith_for_any_ghw_trigger：S09的69—91行检查 **Faith.main_rite** 的GHW参数，或“改革后GHW且非unreformed”；精神/世俗领袖制度；divine_destiny **OR** 没有holy_wars_forbidden。
2. 本Religion没有variable_ghw_unlocked，且全局没有variable_ghw_global_unlocking_cooldown。
3. 如果religious_head存在，他不得被囚禁。这里是可选作用域，**不是必须先建立实际领袖才可宗教级解锁**。
4. 当前Faith的num_county_followers>=35。
5. 以下OR至少一支成立。

| OR分支 | 限定 |
| --- | --- |
| 天主教历史局面 | 耶路撒冷失守且>=1095；拜占庭相关原因且>=1000；欧洲相关原因且>=800；或罗马最高领主属于其他Religion。各相应分支要求当前Faith为catholic。 |
| 日期开放 | 日期>=1100；前面其他AND仍须满足。 |
| 至少两处失控 | 日期>=800，至少两个关联圣地barony的holder.top_liege属于其他Religion。不是任意不同Faith、县民异教或一般hostility。 |
| 伊斯兰跟随 | 基督教Religion已解锁；当前Religion为伊斯兰；至少一处同口径失控圣地。 |
| 其他Religion跟随 | 基督教和伊斯兰Religion均已解锁；当前不是二者，且至少一处同口径失控圣地。 |

历史原因trigger可沿S08的926—1045行继续展开，本期未实测全部地理分支。实际声明效果分别写入：**Global**解锁间隔3650天、**本Religion**首战等待120天、**本Religion**解锁flag，然后发.0011。Faith事件被触发不代表变量在Faith身上；通知ACK也不证明变量或战争。

### 5.2 当前Faith的精神大圣战许可

S10的launch_undirected_great_holy_war_decision（3063—3167行）要求玩家本人是本Faith的精神领袖；有PAM且为papacy的领袖应走bull路线，不能冒充同一入口。

实际许可还包括Religion已解锁、main Rite的非定向GHW教义、本Faith无GHW冷却且无现存GHW、存在合法目标、人物可用成年且未囚禁，以及原生费用/最后许可。单有解锁、圣地数或虔诚不足以证明可发动。

原版从any_kingdom和选王国widget取得目标。S09的93—117行要求相应法理层级、至少5个敌对到足以圣战的county，并排除相应敌对最高领主军力超过本Faith aggregate军力的目标。**Faith aggregate军力不是玩家个人兵数，也不是胜率。** 本期不为说明这项规则重建全世界目标搜索或完整战争策略。

### 5.3 120天例外与准备阶段

S08的.0001（41—131行）还要求精神制度、实际领袖、解锁与冷却；玩家精神领袖须有请求变量。有效非定向教义/目标与显式选目标分支分别保留。

**首战120天不是所有合法玩家路线的绝对等待。** .0001的54—66行只在领袖没有显式选定目标时检查Religion首战等待。S10玩家决议可以写player_ghw_target_kingdom并直接触发.0001，该支不受这项等待检查，但其余资格和支付条件仍在；不是任意玩家无条件跳过全部门槛。

start_great_holy_war在此声明的是准备阶段，delay为{365 545}。存在Faith.great_holy_war对象，不等于有独立ghw_war。本期最小观察是Religion flag、Faith入口/拒绝、领袖身份和等待/目标理由，不要求自然战争终局。没有拍到触发过程，就只讲来源规则和当前状态。

## 6 原生复用与a02候选状态

完整有限设计在[外置native工作包](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b1-a01/research/power/native-work-package-a01.md)及同名JSON，冻结19份实现源码SHA。

| 能力 | 实现入口 | 边界 |
| --- | --- | --- |
| 真实选中决议 | bridge/mcp_server.py:4241 → service.py:14791 → native_driver.py:8122 → native_bridge/src/ingame_decision_item_v1.cpp:352 | 现有通用identity/model查询不授动作资格。 |
| terms getter | ck3_12004_holy_site_adoption_detail.cpp:123—218、259—307 | exact.4 CanConfirm、requirements、tooltip、cost、raw10 quote/affordable、cooldown已有；不能给create_hof伪造HolySite selected_item。 |
| 普通Confirm | mcp_server.py:4183的ck3_confirm_ingame_decision_outcome_v1 | 可复用create_hof_decision＋decision_closed的一次性正常dispatcher；本case未实机资格，详情关闭只证明UI。 |
| 后态 | ck3_12004_religion_adopted_observers.cpp:135—158、195—212；player_rite_governance_private_transport.py:35—41、122—129 | .4走真实.4 binder后复用软件DTO。legacy文件名不证明旧image ABI可以使用。 |
| 司祭 | mcp_server.py:2337与player_clergy_appointment_private_transport.py | incumbent/Rite可复用；clergy/puppet优先输入未齐。 |

bridge相对ck3_autonomous_player/src/xar_autoplayer/；C++相对ck3_autonomous_player/native_bridge/。以上是源码定位，不证明当前二进制已发布或通过本case。

### 6.1 已审a02仍未编译或实机

[a02说明](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b1-a01/research/power/patch-candidate-a02/README.md)和manifest绑定冻结原HEAD17f7fb69cdae7fd67afdd385f5b1e922d17e2a0c。累计patch SHA-256：**093592632aec349778718c01a5eaa0020160ff296cd9306fdf055baaf9916812**。

- 7文件有限候选，只给现有keyed query加只读selected_terms；复用已证明getter，不增加write、Confirm、效果预览或GHW动作。
- 当前只支持**实际named参数为空**的选中上下文。非空返回unavailable；空参数不证明没有widget，也不是全决议支持。旧HolySite完整选择和ID守卫保留。
- 仅公共read-only query启用terms；Select/Confirm内部model守卫默认不启用，不增加额外getter。
- a01独立审计发现P2：available terms未关联外层真实选中详情。a02只改Python消费者，要求outer model可用、4项detail proof全真及相同整数actor fullID；守卫在outer unavailable早退前。a01拒绝记录原样保留。
- 同机2026-10-19T19:31的11项**合成packet生产消费者**检查通过：7个矛盾负例先被实际a01消费者接受，再由a02新守卫拒绝；4项正常/兼容正例通过。回执SHA-256：84e4f680376f08ac590f705e2a1c6ebe383ccd4b17b7c5f634ec0efc173cb89e。这不是实际native serializer wire。
- [独立复审](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b1-a01/research/power/patch-candidate-a02/INDEPENDENT-REVIEW.md)于2026-10-19T19:31:58.551611+00:00给出 **PASS_SOURCE_REVIEW_READY_FOR_CLOSED_SCENE_VALIDATION**，关闭R5-REVIEW-01；审计者读取源码和回执，未独立重跑测试。
- **本R5包没有编译、link、native fixture、真实Driver/Service/MCP wire资格或建制实机。** 独立source PASS不提升这些层次；Root后续应用/验证须追加实际回执，不能追认旧候选通过。

### 6.2 GHW只读组件仍待施工

只扩当前玩家religion context：actor/Faith/Religion/main Rite/HoF完整ID；Religion解锁和首战等待presence/expiry；Global解锁间隔；Faith自身GHW冷却、GHW对象及独立war ID；当前launch decision的shown/CanConfirm/拒绝或papacy＋PAM bull路由；主流Rite制度、领袖囚禁、请求和显式target存在。

缺失值保留available/真实absence/原因，不能置false。compiled trigger未定位时，source-derived解释与native final gate分开。不建任意actor或任意变量内存访问器，不加GHW动作。要证明自然月度生产，另立on-faith-monthly窗口，不能在paused-only场次等待新生产。

### 6.3 最小场次合同

| 组 | 准备 | 业务证据 |
| --- | --- | --- |
| H1 | 同人物普通/主要两态报价；晋升支出分账。 | 完整原生价格/币种、主要关系、同源前后态；源码不代成交。 |
| H2 | 精神、新title、主流Rite路线；资格及真实司祭、前序优先输入核齐。 | 一次普通Confirm请求/ACK、UI关闭、独立钱包/title/holder/人物Faith/Rite/main Rite；unknown不重试。 |
| H3 | 当前Faith/Religion的GHW只读状态。 | 解锁、当前许可、领袖、目标/冷却分层，不要求发动战争。 |

先做真实native空参数/quote/affordable/bypass/context变化fixture，再经生产消费者消费原样wire；public/native revision故意不同。孤立normalizer不授公共链路通过。确定司祭前序输入未闭合时，不排保证成功镜头；主流case不冒充已实测非主流转main_rite。

新场次仍核机器、EXE、已加载来源、Steam新鲜离线画面、独占owner和容量；本文不授现场资格。独立实验起点和钱包分别呈现，未拍过程不由后态补造。

~~~mermaid
flowchart LR
    G[原版Faith GUI/决议列表] --> D[create_hof条件与费用]
    D --> C[普通原生Confirm]
    C --> E[新建或重建隐藏事件]
    E --> H[按优先序授title]
    H --> R[建立者Rite按条件成为main_rite]
    D -. unknown:本case原生terms资格 .-> Q[实际报价]
    R -. unknown:本case独立后态 .-> P[钱包/title/holder/Faith/Rite]
    M[Faith月度入口] --> U[.0010 AND/OR]
    U --> V[Religion解锁/等待与Global间隔]
    V --> L[本Faith与玩家launch条件]
    L --> S[GHW准备对象]
    S -. unknown:本期不要求 .-> W[真实ghw_war]
~~~

实线是已审源码声明，虚线为本期未取得的现场证据或范围外过程，不是完成比例。

## 7 actual4固定来源索引

路径相对固定commit074429b3f6d9352a3cf4c5671725fee2f41267ba的base/game/或同版本实际game根。完整SHA为实际文件和固定镜像的共同值，行号是人工定位，不是自动语义证明。

| ID | 文件与行号 | SHA-256 |
| --- | --- | --- |
| S01 | [common/decisions/dlc_decisions/pam/pam_decisions.txt](https://github.com/jesec/ck3-mod-base/blob/074429b3f6d9352a3cf4c5671725fee2f41267ba/base/game/common/decisions/dlc_decisions/pam/pam_decisions.txt#L1091)，1091—1222建制。 | fe113568051ccf2243f08543a522bc5afeb3e25e6fb97e5440d2fae7a4cb7a64 |
| S02 | [common/scripted_triggers/00_religious_triggers.txt](https://github.com/jesec/ck3-mod-base/blob/074429b3f6d9352a3cf4c5671725fee2f41267ba/base/game/common/scripted_triggers/00_religious_triggers.txt#L1405)，1405—1449计数、1488—1528精神、1532—1552分发。 | e9d0b56130464eabdcd670fa6cf814534d11c99da1e8b3fc1e69e9c3e36d2bb2 |
| S03 | [common/script_values/02_religion_values.txt](https://github.com/jesec/ck3-mod-base/blob/074429b3f6d9352a3cf4c5671725fee2f41267ba/base/game/common/script_values/02_religion_values.txt#L4094)，4094—4188数量/价格、76—134收件人权重。 | 9e55618b00b463589af310bd17511b4f260fea4d3acb43e512e209cfc1517ded |
| S04 | [common/script_values/00_basic_values.txt](https://github.com/jesec/ck3-mod-base/blob/074429b3f6d9352a3cf4c5671725fee2f41267ba/base/game/common/script_values/00_basic_values.txt#L83)，83—114文化时代价格、665—670奉献等级。 | c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef |
| S05 | [common/scripted_effects/00_religion_effects.txt](https://github.com/jesec/ck3-mod-base/blob/074429b3f6d9352a3cf4c5671725fee2f41267ba/base/game/common/scripted_effects/00_religion_effects.txt#L279)，279起force_create、383—522新title/收件人/main Rite/法律。 | 5bf6b0df3316f72f711507c310a349d508a3b83aef99373ea6440de20e4e4931 |
| S06 | [events/religion_events/faith_creation_events.txt](https://github.com/jesec/ck3-mod-base/blob/074429b3f6d9352a3cf4c5671725fee2f41267ba/base/game/events/religion_events/faith_creation_events.txt#L28)，28—47新精神入口、156—260重建/main Rite。 | 419c04b9ca889e96e572b894ec346ae6119af2fd6eb9be4833d6659edfba923e |
| S07 | [common/on_action/religion_on_actions.txt](https://github.com/jesec/ck3-mod-base/blob/074429b3f6d9352a3cf4c5671725fee2f41267ba/base/game/common/on_action/religion_on_actions.txt#L1278)，1278—1295月度入口。 | ef9367ddf5f89c912b895743f8b72441e88af3a5b03a5c1a9eddea0e5681ee2d |
| S08 | [events/religion_events/great_holy_war_events.txt](https://github.com/jesec/ck3-mod-base/blob/074429b3f6d9352a3cf4c5671725fee2f41267ba/base/game/events/religion_events/great_holy_war_events.txt#L41)，41—131发起/等待例外/准备、926—1045历史原因、1047—1192解锁。 | dfac5841107682613a78ec817d48c10b6ffb7ad411d9043901079de0a27897c0 |
| S09 | [common/scripted_triggers/00_great_holy_war_triggers.txt](https://github.com/jesec/ck3-mod-base/blob/074429b3f6d9352a3cf4c5671725fee2f41267ba/base/game/common/scripted_triggers/00_great_holy_war_triggers.txt#L9)，9—91教义/请求/目标标记、93—117合法目标。 | 7e449bcfa18bc02cf97cffff950d7b6f2d97aab7e0e93110db6c39d5e26505ba |
| S10 | [common/decisions/10_religious_decisions.txt](https://github.com/jesec/ck3-mod-base/blob/074429b3f6d9352a3cf4c5671725fee2f41267ba/base/game/common/decisions/10_religious_decisions.txt#L3063)，3063—3167玩家非定向大圣战入口。 | 6ef6123e5f0ae31789f8f854043ba4d11278af0470871ba77d3df0cffc2da30c |
| S11 | [gui/window_faith.gui](https://github.com/jesec/ck3-mod-base/blob/074429b3f6d9352a3cf4c5671725fee2f41267ba/base/game/gui/window_faith.gui#L5636)，5636—5658决议链接。 | 67924e58ccba26d95853ac48af35d91a774f5ce6d2e7f32a0a033de3b9d51521 |
| S12 | [gui/window_decisions_detail.gui](https://github.com/jesec/ck3-mod-base/blob/074429b3f6d9352a3cf4c5671725fee2f41267ba/base/game/gui/window_decisions_detail.gui#L139)，139/158效果与requirements，215—237 CanConfirm/Confirm/成本。 | 9007f4ba7c67314fa24ea6acc1fc709a4b185d7830230ebff479892e6046a469 |

## 8 本次自审

本次只写本文，未改源码、Git、构建、游戏、屏幕或原候选。已核：普通资格与主要费用分开；非主流金币不×2；clergy/puppet/cp优先序不漏；main Rite后果不简化为改信；Religion/Global/Faith分层；120天显式目标例外保留；准备对象与战争分开；a02合成consumer通过不外推编译/真实wire/实机；确定司祭优先输入缺口继续开放。
