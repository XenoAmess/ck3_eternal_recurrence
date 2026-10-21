# 活武器：实现与验收方案 v0.4

2026-10-22。[详细设计](design.md)定义玩法，[异能图鉴](affix-catalog.md)定义异能与联动，[诅咒图鉴](curse-catalog.md)定义32种负面词条；本文维护实现结构、字段与实际证据边界。**已进入开发，生成器与游戏脚本存在；正式staging和实机通过另记，不能从本文推定。** 原生边界所需的参数调整见[实现调整](implementation-adjustments.md)。

## 1. 静态来源

`machine_id: pc-20260924rtuf-f11af23c08`。本轮静态观察时间 `2026-10-21T18:50:02Z`（北京时间10月22日），实际根 `C:/SteamLibrary/steamapps/common/Crusader Kings III/game/`。路径只定位此机文件，不是跨机器配置。原manifest声称build25734779，未核EXE或运行加载，不能据此授予运行版本资格。源SHA与文档检查见[修订回执](evidence/design-revision-2026-10-22.json)。

| 能力 | 相对game根的实际来源 | 结论与限制 |
| --- | --- | --- |
| 换主与继承 | `common/on_action/inventory_on_actions.txt:1–39` | `on_artifact_changed_owner` root=artifact，owner/old_owner按存在性读；succession在换主前，之后还会changed_owner，不重复处理 |
| 宝物变量与modifier | `common/scripted_effects/pam_effects.txt:14195–14259` | 宝物scope内set/change_variable、add/remove_artifact_modifier有实码；具体生效与持久化仍需原型 |
| 已装备/槽类判断 | `common/court_positions/tasks/00_antiquarian_tasks.txt:251–257` | `any_character_artifact`、`is_equipped`、`artifact_slot_type`已有用法 |
| 个人类别 | `common/artifacts/slots/00_default.txt:7–53`及`types/00_types.txt` | 包含brooch、journal与多饰品位置，不能只写剑甲三饰品 |
| 全角色兜底 | `common/on_action/_on_actions.info:13–17` | `random_yearly_everyone_pulse`覆盖所有角色；`quarterly_playable_pulse`仅可玩角色，不足以覆盖男爵/廷臣 |
| 原生四档rarity | `common/script_values/00_artifact_values.txt:105–123` | 可在artifact scope直接比较common/masterwork/famed/illustrious |
| 显示名 | `localization/simp_chinese/inventory/inventory_l_simp_chinese.yml:146–153` | 普通原文为空，大师级/名作级/卓越级有文本；后列legendary/rare是旧残留 |
| 颜色与quality | `common/defines/00_defines.txt:1581–1591` | 铜褐/绿/蓝/紫；quality、wealth各0–100，其合计经50/130/180阈值形成rarity，不等于rarity本身 |
| AI装备评分 | `common/script_values/00_artifact_values.txt:41–58` | 基础quality+wealth+rarity项+模板ai_score+`artifact_ai_will_equip_score`；只装备正分最佳项。hook root=持有者，artifact/current_weight为提供scope |
| 模板受益资格 | `common/artifacts/templates/_templates.info:49–53` | `can_benefit`优先于ai_score，不能靠抬分绕过 |
| 原生重铸AI | `common/script_values/00_artifact_values.txt:61–103` | 金币、战争与槽位限制属于重铸，不是新喂养CD |
| 原生销毁互动 | `common/character_interactions/00_artifact_interactions.txt:4385–4543` | 有高稀有度宗教条件、barony AI频率与欠债销毁；不能不加分析复用为四档喂养 |

注意 `00_artifact_values.txt` 内名为 `artifact_rarity` 的script value有初始1再加1/2/3/4，结果2/3/4/5；不拿它当0–3或1–4原生编码。所有生产者/消费者统一用四种明确枚举。

上轮未找到可靠的created/equipped/unequipped命名回调，yearly脚本未见monthly入口，本轮不凭想象补上。原版AI修复可用模板条件有证据，但未找到独立的mod附加repair回调。官方Paradox Wiki前轮读取401，历史[宝物历史研究](../../docs/artifact-history-modding.md)为1.19.0.6静态材料、`machine_id: unknown`；都不作为当前实机通过证明。

## 2. 架构调整

### 2.1 以原生物品修正承担穿脱

v0.1的“玩家角色单份六属性投影”不再是主方案。异能账本放物品，持续被动优先用本模组独有的 **artifact modifier**，由原生装备状态启停；事件异能在实际原版来源触发时检查真实owner、is_equipped及词条。玩家和NPC共享同一效果。

不再以全身固定六项属性cap作为核心。平衡改由六个异能槽/两个诅咒槽、词条阶数、明确触发频率、代价及同名联动规则控制。实现修订采用每件饥渴最高5点、全身自然叠加；原生artifact modifier保证卸下立即取消，不能每季修正一次残留。原因与其他原生接入调整见[实现调整](implementation-adjustments.md)。

不把完整物品能力复制到角色永久基础属性。不覆盖整个库存GUI，不通过伪改rarity骗AI装备。原版modifier与本模组modifier分名，突变仅移除本条对应增量，不误删原版属性。

### 2.2 所有持有者覆盖

创建/换主入口确认后登记持有者；拥有活武器者进入去重队列，失去最后一件后退出常规成长队列。全角色年度脉冲只做廉价候选检查并登记，不每月扫描全世界全部宝物；可玩季度入口仅为补充。

NPC与玩家库存按同样有界批次发现，每批最多50件未检查装备，后续继续；起始大库存保留cursor。队列延迟只延迟计算，不能永久排除男爵或无地角色；装备月份由实际观测/调度记录，不能以后凭当前装备状态补算过去一年。

无主、陈设、库存物品仍保留状态，但**不增长经验、不提供活武器加成**。不再做基础月龄补发。NPC正在装备的物品则正常每月+8，不能以“AI休眠”节省计算。

### 2.3 原生AI评分适配

接入原生模板ai_score或已证实的装备评分hook时，读取词条实际价值、角色处境和当前负担；保留原有cursed_artifact等逻辑和can_benefit资格。若修改单一原版script value，先确认覆盖语义与其他mod冲突，并对非活宝物返回原结果，不假装它能自动追加合并。

取得/失去/成长/镇压变化后唤醒装备与培养评估。无地角色不因AI原版销毁频率barony=0而失去新喂养能力。AI可以不选择危险装备，但真实适合的活武器必须能正常装备和生效；不能只证明评分字段变大。

## 3. 先做三个原型

1. **穿脱与被动**：玩家与NPC装备→卸下→换主→死亡继承→重载。加成、基础饥渴、事件资格随真实穿脱改变，卸下同时停经验与收益；已发金币、已成债务不倒带。不支持即时语义就修接入，不能要求玩家点刷新。
2. **月度与全角色**：验证游戏月调度、男爵/无地廷臣队列、旧库存登记、多人去重。只有真实装备且未镇压的月份有经验；每个角色一条调度链，镇压到期自动失效，不补库存经验。不把固定30天未经说明称作游戏月。
3. **自动跨级与四档喂养**：同一游戏时刻连续消耗多件普通、大师、名作、卓越材料，无CD；900/1000进度的10级物品再得1200，自动到12级且本级0，两次随机成长都发生，基础饥渴2。不展示许可弹窗；升级结果在通知前落盘。

已设计的36个异能仍需逐条原型，原版结算的战斗、秘密、关系、旅行等语义不因“定义了一行effect”而通过。优先实现图鉴的12个核心，不把名字相同的属性buff当作复杂异能完成。

## 4. 新状态合同（设计schema 2）

v0.1只有文档，没有发布过游戏脚本或存档生产者。因此直接用schema2设计新合同，**不用虚构的旧运行存档兼容层**，不保留routes、pending_upgrade、growth_mode、sealed或feeding_available_on别名。历史文档仍可经Git回看。

模型用共享TypedDict/dataclass，分支用Literal，外部JSON先验证再构造。游戏内部扁平变量与JSON对象由一个编码器/解析器转换；所有定义在同一registry引用，不把字符串散落在GUI、脚本和工具两端。

| 字段 | 类型/必填 | 合同 |
| --- | --- | --- |
| `schema_version` | 所有已检查记录必填的严格整数2 | 脚本xalw_schema_version |
| `kind` | ordinary/living | 未检查为无记录；ordinary仅schema_version与kind |
| `level` | living必填整数≥1 | 无15级玩法上限；不因数字储存精度静默舍入 |
| `xp_in_level` | living必填整数≥0 | 本级余额，自动结算完成时小于100×level |
| `pending_xp` | living必填整数≥0 | 已确认到账、自动结算中的经验；只是计算队列，不等待用户许可 |
| `growth_sequence` | living必填整数≥0 | 每完成一个成长结果递增，重复事件不再次改写 |
| `affixes` | living必填有序数组0–6 | 每项id来自registry、rank整数1–3，item内同id不重复 |
| `curses` | living必填有序数组0–2 | 与affixes分支同样明确；诅咒不是免费正向能力 |
| `personality` | living必填六枚举之一 | protective/warlike/proud/greedy/curious/gloomy |
| `diet` | living必填个人槽类枚举 | 与游戏原生个人类别对应，不用rarity代替 |
| `feeding_imprint` | living必填对象或null | 含category与expires_on，最近一次喂养倾向保留3游戏月；这不是喂养CD |
| `attuned_character` | living必填角色引用或null | 换主重建，失效引用不可冒充角色0 |
| `resonance` | living必填整数0–100 | 无连接0，新owner20；卸下不累计 |
| `growth_suppressed_until` | living必填游戏日期或null | 付费限时镇压，不能表示无限期；过期自动失效 |
| `suppression_chain` | living必填整数≥0 | 连续镇压加价计数，换主/卸下不清 |
| `unsuppressed_equipped_months` | living必填整数0–6 | 实际未镇压装备月，达6才重置连续加价 |
| `appeased_until` / `appease_available_on` | living各必填日期或null | 安抚效果与下次可用，独立于经验资格 |
| `last_settled_month` | living必填严格整数或null | 自然经验结算去重，无装备月也标已检查，不累欠经验 |
| `last_notified_sequence` | living必填整数≥0 | 通知游标不改变level，不读通知也继续成长 |
| `trait_runtime` | living必填有序数组 | registry逐id定义的有限状态联合：触发次数、截止日、被绑定角色等；没有状态为[] |

`AffixInstance`统一为`{id, rank}`；槽位就是数组位置，替换后继承槽位索引而不是排序。涉及扩展形态时必须在registry明确建模，不能附加任意字典。trait_runtime中不存在的条目与存在但状态null按各id合同区分，未知键拒绝；事务与通知不当成物品能力本体。

游戏日期JSON统一`{year,month,day}`，严格整数、有效游戏日历；现实证据用UTC ISO时间。物品/角色外部引用用规范十进制字符串及scope来源，游戏内部优先持久引用；不拿指针或GUI临时下标作存档身份。64位ID/FILETIME不经JS Number往返，要求数值的边界先验安全整数。

已经成立的债务/承诺放在独立角色义务账本，绑定承诺角色、来源物品与结算进度；物品突变、转赠、卸下不能删除应付余额。具体死亡处理按图鉴条目规定，不假设全部转给下一持有者。训练和安抚保留各自资格字段；**不存在feeding_available_on或喂养次数锁**。

不变量：schema未知不能当未检查重抽；0经验与缺失有别；affixes/curses容量与阶数合规；已完成成长序号与结果一致；无pending_xp时经验余额小于下级阈值；暂停资格只由真实未装备或有效付费截止导出。JSON入口拒绝bool/浮点充整数、错字段、缺必填、错误null与不合法日期；tuple/list通过统一数组编码验证往返，不因表示变化误判内容篡改。

v0.3继续使用设计schema2，新增诅咒ID进入同一registry，不新增第二套负面账本。诅咒替换继承被替换槽rank，不能复用正向突变的随机新rank。持续artifact罚值随卸装撤销；已施加伤病、公开秘密、损失与关系是已结算的角色/世界后果，依其原生状态保留；独立债务/承诺继续由义务账本承担。每个诅咒状态在trait_runtime的按ID联合类型中明确次数、截止与目标，禁止以无约束字典散存。

## 5. 自动结算与随机结果

### 5.1 经验到成长

验证owner与真实装备、未镇压 → 记录已确认经验来源 → pending_xp入账 → 按100×当前level逐级扣除 → 每级自动抽事件类别及异能/诅咒结果 → 应用/撤销相应本模组修正 → 保存新level、余额与growth_sequence → 汇总通知。

不能先等待管理窗口或“领取”按钮；允许性能分批续接，但不能引入模拟时间CD或由关闭事件无限拖住结果。一次源事件/材料只结算一次。待处理队列不是选择列表；过期窗口只能读已提交结果，不能重抽。

随机上下文在每级提交时固定：registry版本、当前槽位/阶数、性格、食性、尚未过期的喂养倾向、source事件与结果。2–10及11+权重、40%无偏好、满槽回退见设计，不在此重写另一套数值。对过载/重复调用，读取已提交序号，不能重新掷骰追认第二份结果。

### 5.2 四档喂养

新消耗路径按真实rarity与四档表计算，不调用原版销毁互动来自动获得金币/虔诚再加经验；喂养只产生设计承诺的成长。原生destroy_artifact基础effect可否用于精确消费需原型证明。材料销毁成功才给经验，失败或结果未知不重复提交。

批量每项独立核对目标仍装备、材料归属/未装备/非活、rarity和保护标记，冻结实际引用、食性倍率与经验后消费。目标若被转手、卸下或镇压，未处理项停止并读回；不能换一件同名物品继续扣。成功项经验及自动跨级结果已生效，不因后项失败倒带。

玩家可立即再喂；AI一次决策可处理多件。队列分页只限制计算块，不设置等待天数、年度上限、隐含饥饿恢复或升级后锁。

### 5.3 词条与联动

词条registry区分持续artifact_modifier、原版源事件触发、已成立义务。所有效果核对实际owner/equipped；诅咒不能借低共鸣变轻，镇压只按设计削弱随机正向触发。卸下即时撤掉持续收益和持续减益，不撤销已发生结果。负面持续项按所有实际装备物品相加，不使用正向同名取最高规则，也不放进基础饥渴5点cap；负面事件按诅咒图鉴标明的粒度去重。

联动统一引用同一源事件身份，基础触发→最多一次联动结算，产物不再当源。具体数值、概率、频率、rank3变化和AI权重以图鉴为真源；技术入口不确定时标pending，不能把“季度随机模拟一次”冒充真实战斗/秘密效果。

## 6. 脚本落点与构建

统一前缀xalw_、事件namespace xalw。未来目录为common/on_action、scripted_triggers、scripted_effects、script_values、modifiers、decisions、game_rules、按目标构建核实的artifact modifier目录，events和简中/英文本地化。数据表/生成器集中维护词条，生成文件只改生成器再运行。

on_action通过追加子钩子扩展，同名effect不会自动合并。原先玩家限定闸门在本独立产品改为真实角色/装备资格，AI与玩家同路径；不修改主模组和其他产品限制。无关角色只作廉价判断，避免全世界月度库存扫描。

所有游戏脚本/yml UTF-8 BOM，script_values目录拼写固定。管理先用原生决议/选择器，确有必要再最小GUI。构建白名单排除文档、测试和runtime，输出外置staging，不预填itemID、supported_version或文件总数。Python/MCP是开发验收工具，不进入玩家运行依赖。

## 7. 代表性验收与交付

详细执行前方案已分为[测试总方案](test-plan.md)、[内容矩阵](content-acceptance-matrix.md)和[执行/结果合同](acceptance-execution-contract.md)。下表是范围摘要，具体前置、数字、案例ID和证据要求以上述文档为准；所有计划用例当前NOT_RUN。

| 范围 | 必须证明的实际结果 |
| --- | --- |
| 全角色 | 玩家、AI统治者、男爵、无地骑士/廷臣均可获取装备成长，旧库存与新造均覆盖 |
| 自动成长 | 不打开通知照常升级；10→11自动生代价；15→16继续；一次喂多级逐级抽，不漏诅咒 |
| 卸下/镇压 | 卸下同时停经验与持续加成，重戴不补经验；仍装备镇压花钱、概率减半、到期恢复；继承不清加价 |
| 喂养 | 四档精确经验、食性倍率；同一游戏时刻连喂；无feed-CD字段；材料失败不发经验、取消不扣 |
| 异能 | 12核心分别有真实触发/收益/成本；rank、六槽/两诅咒、满槽突变、联动去重、债务不会因换装消失 |
| 重诅咒 | 首批8种有实际严重后果；三阶/两槽/保阶替换、多件持续减益相加、不能被镇压/低共鸣/基础饥渴上限削弱；卸下撤持续罚值但不撤已发生伤病/破财/秘密公开 |
| AI决策 | 真实选择并装备适合物品、喂多余材料、可支付才镇压；不伪改rarity，不喂掉每槽最佳备用或剧情物品 |
| 持久化 | 剩余经验、序号、词条数组顺序、义务、截止、空/缺失/null往返；错字段/类型/未知schema不重抽 |
| 展示/兼容 | 简中结果通知无升级许可；原版穿脱修复传承正常；主模组双向加载代表用例，不泛称兼容所有total conversion |

本轮只有文档检查，不运行游戏测试，也不声称静态类型或业务实机PASS。未来实现运行修改范围的真实静态类型检查与必要回归，游戏统一走tools/ck3_mod_acceptance.py公共plan/prepare/allocate/preflight/run/verify，绑定机器、EXE来源与新鲜后台Steam离线回执，使用简中。先评估open_kaishek离线可覆盖子集；文档修订无运行语义，本次不适用。

交付顺序：三个原型→全角色自动成长与四档无CD喂养→12核心异能/8种重诅咒与AI决策→其余图鉴内容和高风险联动。发布仅在用户明确指令后进入；当前不注册/上传Workshop、不补其他语言。所有素材/日志按通用存储策略检查，本次只保存小型文档和出处；旧v0.1/v0.2回执保持历史，不把旧hash和新文档不一致说成篡改。
