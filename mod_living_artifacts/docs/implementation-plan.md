# 活武器：实现与验收方案 v0.1

日期：2026-10-22。本文区分**产品要求、静态可行依据、尚待原型验证的接口**。当前只交付文档，不注册游戏、不生成 staging、不上传 Workshop。玩法与数值以[详细设计](design.md)为准；不在两份文件分别维护两套参数。

## 1. 本次静态观察及资格边界

`machine_id: pc-20260924rtuf-f11af23c08`，静态观察时间 `2026-10-21T18:30:20Z`（北京时间 2026-10-22）。实际读取根为 `C:/SteamLibrary/steamapps/common/Crusader Kings III/game/`；来源定位通过注册表 SteamPath 与 `libraryfolders.vdf` 读取。`appmanifest_1158310.acf` 声称 `buildid=25734779`，**未核对 EXE SHA、实际运行进程或加载来源，不能据此认定当前 CK3 版本或实机资格**。路径仅定位这台机器的观察，不是跨机器配置。

下面路径相对该 `game/`，只代表当时磁盘文本。精确 SHA 与闭场检查保存在[工作回执](evidence/design-session-2026-10-22.json)。本次没有启动 CK3、没有查询/改变 Steam 在线离线状态，也没有以历史记录推断本机 Steam 状态。

| 能力 | 实际来源 | 能支持的结论 |
| --- | --- | --- |
| 换主 | `common/on_action/inventory_on_actions.txt:1–8` | 实名为 `on_artifact_changed_owner`；root 是 artifact，提供 owner、old_owner；新持有者/旧持有者作用域须按存在性判断 |
| 继承 | 同文件 `31–39` | `on_artifact_succession` 在换主前触发；文本说明换主后仍调用 changed_owner。适合由后者统一更新，避免两次重置共鸣 |
| 物品变量 | `common/scripted_effects/pam_effects.txt:14195–14259` | 原版在宝物作用域使用 `set_variable`、`change_variable`，存在物品内状态的静态依据 |
| 宝物修正 | 同文件 `14203`、`14230`；`events/artifacts/artifact_events.txt:2258,2425` | 有 `add_artifact_modifier`、`remove_artifact_modifier` 实码；效果、条件与刷新仍需原型测试 |
| 装备查询 | `common/court_positions/tasks/00_antiquarian_tasks.txt:251–257` | 原版 `any_character_artifact` 内使用 `is_equipped` 与 `artifact_slot_type`，可组合过滤，不按名字识别 |
| 季度盘点 | `common/on_action/yearly_on_actions.txt:2974–2979` | 有 `quarterly_playable_pulse`，root 是角色。其季度相对角色周期，不保证固定日历季度 |
| 个人槽位 | `common/artifacts/slots/00_default.txt:7–53` | inventory 类包括 crown、regalia、armor、weapon、brooch、trinket_1/2/3、journal |
| 物品类型与类别 | `common/artifacts/types/00_types.txt:6–240,447–465` | 具体 sword/axe/bow 等类型和 primary_armament 槽位类别不同；应按类别过滤，逐项验证新类型兼容 |

当前已读样本中没有找到 `on_artifact_created`、`on_artifact_equipped`、`on_artifact_unequipped` 或 artifact 模板的 on_equip 回调。`yearly_on_actions.txt` 中也没有 monthly 命名入口。**未找到不能证明引擎绝无此接口，但不能在实现中凭名字创造回调。** 创建覆盖率与月度调度分别采用下面的发现/原型流程。

官方 [Artifact modding](https://ck3.paradoxwikis.com/Artifact_modding) 与 [Effects](https://ck3.paradoxwikis.com/Effects) 页面本次读取返回 401，因此不把未读内容当成当前接口证明。仓库[宝物历史研究](../../docs/artifact-history-modding.md)是历史 1.19.0.6 静态结论，`machine_id: unknown`，所属机器未核实，仅作研究线索；不追认为本次实机结果。原生历史条目没有当前已证实的任意自定义 type，可用原创管理事件表达成长，不覆盖全局 history 本地化。

## 2. 必须先完成的两个原型

### P0-A：穿脱即时生效及全身上限

设计选择物品保存成长、角色单一修正投影，以实现全身上限和 AI 休眠。但只按季度重算会让卸下的装备继续提供收益，换主还可能暂时使新旧主人同时获益，不能作为发布实现。

原型需实际演示：装备两件 → 更换一件 → 卸下全部 → 赠送 → 玩家切换 → 保存重载，每一步在状态结算后，六项净增量、健康和已装备列表一致；不要求玩家再点一次刷新按钮。先研究目标版本是否提供可靠的原生接入或可按游戏状态自动求值的修正。不得把命令 ACK、GUI 打开或下一季度终于修好当成即时语义通过。

若做不到，推荐技术退路是**本模组独有的原生 artifact modifier**，利用原生装备启停，并将多件规则修订为逐槽/逐件预算；换主回调负责玩家范围的激活与 NPC 休眠。此退路的六路线缩放、反噬及 NPC 行为同样需验证；不能悄悄去掉设计中的全身上限。原型结束先更新产品合同，再进入批量生成器施工。

### P0-B：每月结算与旧库存发现

季度 pulse 可承担兜底发现，但不能拿“当前已装备”证明过去三个月始终装备。月度成长需用经过验证的游戏内事件调度/已存在回调，按角色绑定一次调度链，并以结算月去重；若只能采用固定天数的延迟，先明确修订产品时间单位，不将 30 天说成所有游戏月。

启动/载入/多人加入入口也需从目标构建原版文件确认再接入。重复载入不得复制调度链；角色死亡、退出玩家身份、继承切换应终止旧链并给新玩家恢复链。不能每次读档补发历史经验。原型至少覆盖跨月、暂停、重载和两名玩家。

季度盘点每玩家每批最多检查 50 件未判定的候选；大型库存分批继续，保存进度，避免每季从头扫描而永远漏掉末尾物品。“最迟 3 个月识别”只适用于常规库存单批覆盖；超过 50 件的旧库存明确显示“正在分批检查”，不宣称所有库存都保证同一期限完成。首次打开管理入口可以检查当前选择的未判定装备，仍使用同一幂等效果。

## 3. 脚本组织与独立运行

统一前缀 **`xalw_`**，事件 namespace **`xalw`**。下列是未来实现目录计划，尚未创建运行文件：

```text
mod_living_artifacts/
  descriptor.mod                         # 实现后才加入，不含 remote_file_id
  common/on_action/xalw_on_actions.txt
  common/scripted_triggers/xalw_triggers.txt
  common/scripted_effects/xalw_artifact_effects.txt
  common/script_values/xalw_values.txt
  common/modifiers/xalw_modifiers.txt
  common/decisions/xalw_decisions.txt
  common/game_rules/xalw_game_rules.txt
  events/xalw_events.txt
  localization/simp_chinese/xalw_l_simp_chinese.yml
  localization/english/xalw_l_english.yml
  tools/build_release.py
  tools/validate_static.py
  tools/generate_growth_modifiers.py
  docs/...
```

如使用 artifact 原生修正，另按目标构建核实的目录加入本模组修正定义；如必须使用 GUI，再加入最小 widgets 与脚本 GUI。不可为展示效果先复制覆盖整个原版库存界面。`script_values` 目录拼写固定；所有游戏脚本和 yml 使用 UTF-8 BOM。

原版 on_action 扩展只追加 `on_actions = { xalw_... }` 子钩子，不写同名 effect 替代原版处理。同名键覆盖而非自动合并，必须有加载测试。所有子钩子首先限制当前玩家，或旧/新 owner 至少一方是玩家的必要换主清理链；不枚举 AI 世界库存，不给 AI 留培养事件入口。

构建器未来采用明确白名单，输出外置 staging，排除 docs、测试、工具、源截图及 runtime；不猜文件总数、Workshop ID 或 supported_version。后两者以首次正式目标构建与实际发布为准。需要确认原生 artifact 系统与所选活动各自的 DLC 条件：核心月度/训练/管理不依赖活动 DLC，活动项按当前已拥有内容隐藏；如果核心 personal inventory 在目标配置不可用，明确最低版本/DLC，不虚构免费可用性。

正常玩家只需 CK3 与模组包。Python 是开发工具，MCP 是项目验收通道，不进入玩家的线上运行依赖。

## 4. 单一状态合同

### 4.1 身份与分支

状态以**物品内变量为真源**；角色只有可重建的装备汇总、通知去重、调度与冷却。没有该模组命名空间变量表示“未检查”；不能把缺失当作已检查失败。

文档化逻辑模型如下，未来 Python 工具使用共享 `TypedDict` 或 dataclass，状态用 `Literal`。JSON 是传输/调试表示；游戏变量是扁平实现，两者由一个集中编码器与解析器转换。此处定义合同，不声称已经有解析器。

| 字段 | 类型与必填规则 | 语义 |
| --- | --- | --- |
| `schema_version` | 严格整数，当前 1，所有已检查记录必填 | 迁移版本，脚本 `xalw_schema_version` |
| `kind` | `ordinary` / `living`，必填 | 判定结果；脚本 `xalw_kind` 用固定码 0/1，编码器转枚举 |
| `level` | 1–15 的整数，仅 living 必填 | 已确认的成长等级 |
| `total_xp` | 0–10,500 的整数，仅 living 必填 | 终身累计经验；暂停不抹除 |
| `routes` | 固定六键对象，仅 living 必填 | edge/command/majesty/fortune/whisper/insight，各整数 0–6，总和等于 level；脚本统一映射 `xalw_rank_<key>` |
| `innate_route` | 六条路线枚举之一，仅 living 必填 | 觉醒时的初始天性，独立于后来路线点数，不能每次查询重新抽取 |
| `personality` | 六个固定枚举之一，仅 living 必填 | protective/warlike/proud/greedy/curious/gloomy |
| `growth_mode` | active / paused，仅 living 必填 | 玩家是否主动暂停成长；与封印分别保存 |
| `attuned_character` | 角色引用或 null，仅 living 必填 | 当前共鸣角色；未连接/失效为 null，不用 0 冒充角色 |
| `resonance` | 整数 0–100，仅 living 必填 | 未连接为 0；首次有效连接为 20 |
| `attunement_months` | 整数 0–12，仅 living 必填 | 当前共鸣持有人的已结算装备月数，12 后截断，仅用于性格事件资格；换主重置，物品总经验不重置 |
| `pending_upgrade` | 对象或 null，仅 living 必填 | 对象含 `to_level`、`choice_revision`、`choices`（有序、不同路线的数组）；按当前未满路线生成并冻结 |
| `sealed` | 严格 bool，仅 living 必填 | 逻辑值；游戏边界明确以 0/1 编码，其他数值拒绝 |
| `unseal_available_on` | 游戏日期或 null，仅 living 必填 | 封印期间必有最早解封日，未封印时 null；不会自动解封 |
| `appeased_until` | 游戏日期或 null，仅 living 必填 | 安抚效果截止；不存在为 null，不用空字符串 |
| `appease_available_on` | 游戏日期或 null，仅 living 必填 | 安抚下次可用日，不能在转赠时删除 |
| `last_growth_month` | 严格整数或 null，仅 living 必填 | 已结算的游戏月序号，首次未结算为 null |
| `last_notice_level` | 严格整数 0–14，仅 living 必填 | 已发送的可升级通知对应的当前等级；初始为 0 |

普通记录只有 `schema_version`、`kind=ordinary` 两项，不留一组无意义的 level=null 等字段。未检查没有记录；它与 ordinary、living、living 的 null 待选具有不同语义。

游戏日期的 JSON 表示统一为 `{"year":1066,"month":9,"day":15}`，各项严格整数，并按目标游戏日历校验。不要把 CK3 游戏时间误写成现实 UTC；证据的观察时间另用带时区 ISO 8601。角色/宝物对外引用使用规范十进制字符串与明确作用域；进程地址、临时 GUI index 不能作持久身份，游戏内优先持久 scope 引用。

角色冷却集中为 `training_available_on`、`feeding_available_on`，通知使用独立 `last_personality_event_on`；活动/战斗去重与冷却也放在同一份共享角色合同。允许 null 表示从未进行，不把空列表解释为“所有冷却完成”。结算字段若加名或改名，生产者、管理页、存档迁移、调试导出与回归用例一起修改。

### 4.2 不变量与迁移

- ordinary 不能再次抽签；未知较高 schema 不覆盖，不凭错误字段把它当作未检查重抽。
- `sum(routes)=level`；`total_xp` 至少达到当前级阈值；15 级不保留 pending；候选的 to_level 必须等于 level+1，且有足够经验。
- 待选列表含 1–3 个不同有效路线，不能选择满 6 的路线；实际初始参数通常会有 3 个。数组顺序就是显示顺序，不排序后重解释选项。
- 共鸣角色与持有关系须可解释；失去角色时清空引用和共鸣，不销毁物品经验。共享 multiplayer 物品由真实 owner 唯一结算。
- “尚无 pending”用 null，“有 pending 但 choices=[]”是非法，不允许空列表偷偷触发重抽。
- 角色收益、累计路线映射与脚本修正为派生数据，变更后从账本重建，不能作为第二套经验真源。
- 升级旧 schema 时先保存最小迁移诊断，再确定性转换；缺少决定原身份的历史数据时标记该件待修复，不据猜测补一把活武器；其他装备继续正常运行。

工具边界拒绝 bool 充当整数、浮点充当整数、未知字段/状态、缺必填与非法 null；不靠宽泛 Any、cast 或 type ignore 消除错误。所有 ID/FILETIME 等 64 位外部值用规范十进制字符串，若接口要求数值先验证安全整数范围。保存前后只在约定 JSON 类型域中比较，choices 一律编码为数组，不因 Python tuple→list 变化误报篡改。

## 5. 事件与结算顺序

所有检查统一使用 scripted trigger：玩家资格 → 真正持有/装备 → 合格个人类别 → 未封印 → 未暂停 → 未满级。发现判定不要求装备，经验结算才要求装备。

### 5.1 发现

先确认物品有效且无检查记录；抽取一次；写 schema、判定结果；成功才初始化 living 的全部必填字段；最后登记通知。不能先发成功事件，再在事件选项里进行第二次抽签。已检查版本不随产品 minor 升级清零。

### 5.2 升级

经验到账 → 截至上限 → 若当前可升级且 pending=null 则抽并保存候选 → 通知一次。玩家确认时再核 owner、等级、经验与同一候选版本；有效才给选定路线 +1、level +1、清 pending 并刷新收益。仍有下一等级资格时再生成一组，玩家可稍后处理。重复进入或旧事件选项不能再次加点。

### 5.3 换主与继承

只在实际 changed_owner 后统一处理，不在 succession 预回调重置一次再在实际换主重置第二次。清旧玩家派生收益，保存物品成长；新 owner 为玩家则初始化新共鸣连接并刷新，新 owner 是 NPC 则进入休眠。owner/old_owner 任一不存在时按真实无主状态处理，不能解引用空 scope。

### 5.4 喂养与付费操作

事件保存明确目标与材料引用，在最终确认时重新检查并执行。材料销毁成功与经验发放必须位于同一可靠的脚本结算路径；若 effect 无法提供结果证明，原型要覆盖不能销毁的情况，不得先给经验再假定销毁成功。报错或结果未知时不自动重放付费行为。

训练/喂养冷却保存在角色，安抚/封印冷却保存在物品。每项操作都先展示当前实际报价、可得增量与溢出，再检查原生可负担状态。检查与扣费之间发生状态变化则退出并提示，不使用负金币“借款”。

### 5.5 活动与战斗增强

只接入有明确玩家参与、真实完成/胜负及唯一事件身份的原版路径。冻结奖励时的物品列表和显示顺序，计算一次角色奖励池、分配并写去重标记。同一活动经多条 on_action 抵达不得重发；战斗在月度角色限额内结算，活动在每件季度限额内结算。没有可靠唯一 ID 时，先不实现该渠道，不能拿现实时间戳或日志行号当游戏事件身份。

## 6. 验证范围

这次仅是 Markdown 与小型回执，执行文档链接、数值一致性和 diff 检查，不为文档编写游戏测试，也不声称 CK3 验收通过。以下为未来实现的必要代表性用例。

| 范围 | 代表用例与可见后验 |
| --- | --- |
| 生成/旧档 | 强制测试 0% 与 100%；低品质、历史宝物、各个人类别、旧库存与大库存分批；普通失败记录重载/往返赠送仍失败 |
| 路线 | 1→2、10→11、14→15；路线满点不再出现；三选一与以后再说；重复旧选项不二次加点 |
| 时间 | 月度跨年、暂停恢复、跨月重载、多个入口不得重复结算；同一角色只有一条调度链 |
| 装备/效果 | 装备、原生卸下、换槽、多饰品、达上限、共鸣跨档、封印；对照基础属性与额外投影，确认即时消失 |
| 反噬 | 10 与 11 级边界、多件饥渴上限、安抚但全身仍达上限、到期恢复、健康修正移除、季度压力只结算一次 |
| 交易/继承 | 玩家→AI→玩家、玩家死亡、其他继承人实际得物、无主、多人互赠、转赠中的待升级/封印/安抚与冷却 |
| 喂养/费用 | 正常销毁一件普通材料、材料已转手/已装备、金币不足、误选自身、活武器/特殊物品不能作材料、经验溢出与取消不扣费 |
| 持久化 | 六路线、总经验、有序候选、引用、null 与缺失、冷却往返；错字段、缺字段、bool/浮点整数、未知 schema 不被当成新装备 |
| 兼容 | 独立加载；与主模组双向顺序；只覆盖确有风险的同类 artifact hook/modifier；未知 total conversion 明确不作通用兼容承诺 |
| 界面 | 简中实际显示、按钮原因、十级门槛确认、通知合并、原生操作后读回；没有 raw key 或误导性的无代价预览 |

构建/生成器引入时运行修改范围的真实静态类型检查、针对上述边界的必要回归和发布 staging 校验；不抄实现细节写一堆无价值测试。随机参数以可控 fixture 检查分支与独立单次判定；自然样本只能用于平衡观察，不能用小样本掉率接近 5% 代替逻辑验证。

未来实机只走仓库 `tools/ck3_mod_acceptance.py` 公共 `plan / prepare / allocate / preflight / run / verify`，注册产品 adapter 与 case；执行前依合同绑定机器 ID、实际 EXE/来源与新鲜后台 Steam 离线回执，使用简中。先评估 `open_kaishek` 可覆盖语义，适用则离线预验；本次文档没有运行语义，因此不适用，不制造预验 GREEN。MCP 后验区分调用与真实状态。

## 7. 交付顺序

1. **原型包**：先验证 P0-A、P0-B、个人类别与选择器；记录实际版本、机器、来源与无法覆盖的语义。需要调整的数值投影或时间单位先更新设计。
2. **核心包**：一次判定、物品账本、月度经验、成长、共鸣、旧档、中文管理与保存重载；此时应已能完整培养与传承一件活武器。
3. **代价与材料包**：反噬、安抚、封印、训练/喂养、费用与冷却；验证玩家实际失去材料与实际获得收益。
4. **内容与兼容包**：性格事件、英文格式、各槽位与转赠/继承代表案例；活动/战斗按接口证据决定是否接入，未接入明确列限制。
5. **正式发布包**：只有用户明确发布时才做其他语言、封面与 Workshop。使用正式 builder staging；实际上传、真实订阅缓存加载、永久 changelog 与完整 Steam Change Notes 公开回读依仓库规则交付。当前没有发版授权或发布事实，不预填 item ID/tag/兼容标签。

本次小型文档与出处按[通用存储策略](../../docs/storage-retention-policy.md)的 record 类复核，不下载完整游戏/网页镜像，不生成大日志。后续原型运行按统一策略做开始、重型写入前与闭场检查，机器配置只登记本机根目录、卷和预留；不另立永久保留规则。
