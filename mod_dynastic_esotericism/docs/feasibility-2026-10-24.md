# 宗族化密教：可行性分析

日期：2026-10-24。状态：**research，尚未实现或实机验收**。

## 结论

**核心需求有原生 GUI 数据模型与 CK3 脚本实现路线，当前没有证据表明必须修改游戏 EXE。** 推荐增加一个礼仪教义组，在原版界面选择“宗族化 / 无”；为每个启用的礼仪动态创建一个真实宗族，通过角色改礼仪、出生和生成钩子维护归属；用原版“弑亲者”的定向好感与惩罚理由机制处理背离者。

用户追加的监禁、处决要求也有直接的原版配置依据：好感修正可以携带 `imprisonment_reason`、`execute_reason`，而特质的 `triggered_opinion` 可以按教义参数和同宗族过滤。**这比只写一个“罪恶”描述更接近实际业务要求，但尚未证明它在新增动态礼仪、读档、改宗与赦免全过程中正确生效。** 新教义组的默认值、教义知识门、跨礼仪罪行过滤和状态同步仍是后续最小原型的验证重点。

本轮只创建文档目录并读取安装树、二进制和仓库知识，没有创建 descriptor、游戏脚本、GUI 覆盖、构建器、测试 fixture 或运行中的模组，也没有启动／操作 CK3、切换 Steam 状态或发布 Workshop。

## 命名与需求解释

目录采用仓库独立产品的 `mod_英文蛇形名` 惯例：`mod_dynastic_esotericism/`。英文名暂定 **Dynastic Esotericism**，产品 key 为 `dynastic-esotericism`，脚本命名空间拟用 `des`、对象前缀拟用 `des_`。尚无 Workshop ID，不借用其他产品或上游 ID。

这里的“礼仪”是引擎的 **Rite**，“宗族”是 **Dynasty**，“家族”是 **House**。不把整宗教 Religion、整信仰 Faith、家族 House 或氏族政体 Clan 当作礼仪／宗族的替代物。一个 Faith 可以拥有多个 Rite；同 Faith 的另一个 Rite 仍然算背离绑定礼仪。

“必须信仰”结合用户后续处罚规则，解释为宗族内部的宗教义务：背离者能够存在，并承受处罚。若立即强迫其改回礼仪或逐出宗族，就没有可被处罚的背离者，不能同时满足这些要求。

| 规则 | 研究采用的具体合同 |
| --- | --- |
| 界面选择 | 创建／改革／编辑礼仪的相应原生草案显示“宗族化”组，选项为“宗族化”和“无”；现有礼仪面板显示实际已提交状态。普通查看不直接改制。 |
| 默认状态 | “无”为预期默认；未确认选择、取消窗口或原生提交失败时，不创建宗族。现存未启用礼仪保持原状。 |
| 对应关系 | 每个宗族化 Rite 对应一个独立 Dynasty，宗族保存回指；不用名字、创建者或 Faith ID 代替 Rite 对象身份。 |
| 加入 | 创建者和所有信奉该 Rite 的存活角色，包括 AI、无地者与儿童，归入对应宗族下的 House。只处理创建者本人不满足要求。 |
| 背离 | 当前 Dynasty 是绑定宗族，而当前 Rite 不是绑定 Rite；不同 Faith 或同 Faith 不同 Rite 都满足。保留背离者的宗族归属。 |
| 好感 | 该 Rite 的其他信徒对背离者增加一项不叠加、不自然衰减的 `-100` 修正。最终总好感仍叠加原版其他修正，不要求总值恰为 -100。 |
| 罪行 | 同一观察者／目标组合同时具有实际监禁、处决理由；不能只改文案或只显示图标。放逐等其他理由可按原版旗标配置，不从“等”推导无条件离婚或全局惩罚权。 |
| 恢复 | 重新信奉绑定 Rite 后移除本产品造成的背离状态、好感惩罚和对应罪行理由；其他独立罪行保持。此项是状态型规则的建议解释，尚未执行。 |

## 本轮观察基线

本轮机器为 **`desktop-3fevhd2-1c74096080`**，身份来自 `tools/ck3_live_run_id.py machine`。时间、文件 SHA-256 与大小见[来源清单](evidence/source-observation.json)，二进制切片见[二进制研究](binary-observations-2026-10-24.md)。以下路径只代表该机器当时的安装，不是跨机器部署前提。

| 对象 | 本轮实读 |
| --- | --- |
| 游戏安装 | `C:/SteamLibrary/steamapps/common/Crusader Kings III/`，由当前 Steam 注册表、libraryfolders 和 appmanifest 交叉定位 |
| 安装版本 | `launcher/launcher-settings.json` 的 `rawVersion=1.20.0.4`、`version=1.20.0.4 (Crozier)` |
| Steam build | `appmanifest_1158310.acf` 的 `buildid=25734779` |
| EXE | `binaries/ck3.exe`，101,040,248 B，SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518` |
| PE 边界 | ImageBase `0x140000000`；PE FileVersion／ProductVersion 为 `1.0`，不能用它们推断 CK3 的业务版本 |
| 运行证明 | 未启动 CK3，未取运行期状态；本报告不授予 live、多人同步或发布资格 |

本轮直接读取的是**本机原版安装目录内的实际文件**。appmanifest 和安装路径不能单独证明每个脚本从未被修改；本轮未进行 Steam 在线完整性校验。两份核心 GUI 的 SHA 与仓库既有原版研究记录一致，是补充来源证据，不能扩大成整棵安装树未修改的证明。旧 1.20.0.2 文档只作索引，本文二进制结论绑定本轮实际 .4 EXE。

## 礼仪 GUI 与“宗族化 / 无”选择

原版 `game/gui/window_faith.gui:1288` 的教义列表来自 `FaithWindow.GetDoctrineCategoryItems`，组内通过 `DoctrineCategoryItem.GetDoctrineGroupItems` 展示已选教义。创建窗口 `game/gui/window_rite_creation.gui:315` 使用 `RiteCreationWindow.GetCategoryHelper('main_group').GetCategory`，同一窗口的第 598–625 行按模式分别调用 `EditRite` 或 `CreateRite`。因此用户说的礼仪创建和改革，不需要先假设是两个独立的原生草案对象。

原版 `common/religion/doctrine_group_types/_doctrine_group_types.info:7–46` 提供组分类、礼仪锁定与创建可用条件；`doctrine_types/_doctrine_types.info:44–54,72–109` 提供参数、所属组、显示／选择条件与特质。`rite_types/_rite_types.info:67–74` 明确 Rite 的教义能覆盖相同组的 Faith／Religion 教义，适合保存每个礼仪自己的选择。

推荐先把新组加入现有 `main_group`，用两个新 doctrine 表示“无”和“宗族化”，保持其分歧值为零作为首轮方案，避免无意改变原生创建新 Faith 的分歧计算。选项本身不占核心信条槽，也不使其他 Rite 自动宗族化。图标、本地化和显示范围仍需正式设计；不引入未要求的秘密组织、入教仪式或额外收费。

点击候选时，原版第 1253 行调用 `SelectDoctrine` 修改真实草案；最后仍由原生 `CanCreateRite`／`CanEditRite` 和确认流程提交。二进制已找到这些方法的真实反射登记与调用链，详见二进制研究；不是仅从文本中猜测函数可用。

**不能现在承诺“只加两个定义就会自动显示并可选”。** 新教义组在旧 Rite 没有该组值时是否自动纳入草案、默认选择哪个选项，以及现有礼仪面板如何展示缺省值，尚需验证。候选方案是在初始化为现存 Rite 补“无”，以后新建、派生与改革沿用统一的默认合同；不能先批量覆盖全部原版宗教定义。

另一个确定的门是第 1251 行的 `pam_know_doctrine`：除原生 `DoctrineItem.CanPick` 外，还要求角色 `knows_doctrine` 或拥有 `prophet_perk`。`common/scripted_guis/pam_scripted_guis.txt:82–92` 有完整条件，`passive_rite_learning_effects.txt:589–598` 有原版 `add_known_doctrine` 用例。因此新选项必须有知识初始化路线，不能要求所有创建者先拿先知技能，也不能仅因按钮显示就宣称可用。

只有上述原生分组路线实际不能满足指定布局时，才评估窗口投影。仓库 [GUI 笔记](../../docs/gui-system.md) 说明同路径 `.gui` 会整文件覆盖；直接复制两个大窗口会增加升级和 UI 模组冲突成本。当前没有理由先采用该方案。

## 动态宗族、家族与成员同步

原版 `common/scripted_effects/10_dlc_tgp_japan_scripted_effects.txt:9–47` 有 `create_dynasty` 并保存新宗族／House 的用例；`common/scripted_triggers/10_tgp_japan_triggers.txt:682–688` 说明其调用者可以已属于旧宗族。`common/scripted_effects/05_dlc_bp2_effects.txt:1097–1108` 则用 `set_house` 完成收养迁家。这些能作为生成真实 Dynasty 并把角色移入 House 的依据。新 Dynasty 和其初始 House 需要分别保存实际对象；不能把“创建新家族”误当成“创建新宗族”，也不能把旧宗族改名当作所有信徒的新宗族。

本轮 EXE 找到两项 effect 的实际注册和类型工厂，未找到精确 NUL 终止名称 `set_dynasty`，方案不编造这个接口。`events/dlc/pam/pam_decision_events.txt:950–953` 展示 `spread_to_descendants` 参数；本产品不能未经核对就把尚未改信的旧后代一并迁入。`dynasty_on_actions.txt:1–52` 还参与动态命名等处理，创建并非无副作用。

推荐的内部关系是：Rite 保存对应 Dynasty 与默认加入 House；Dynasty 保存唯一对应 Rite；角色的实际 Dynasty 由 House 归属决定。这些应保存为引擎 scope 引用，不把显示名或裸数字 ID 字符串当作对象引用。双向关系建立完毕后，按当前真实 Rite 批量同步现有信徒；以后按事件增量维护。已经属于正确 Dynasty 的合法旁支不反复迁回初始 House。

| 原版接入点 | 覆盖范围与限制 |
| --- | --- |
| `religion_on_actions.txt:418–422` `on_rite_created` | 创建者为 root；取得实际新 Rite 后创建绑定，再处理创建者与已转入成员。实际触发时序必须验证。 |
| 同文件 `725–732` `on_rite_updated` | root 为更新后的 Rite，有新增／移除教义列表；适合处理改革时开启／关闭选择。 |
| 同文件 `998–1002` `on_rite_change` | 覆盖角色 Faith 或 Rite 改变，但明确排除出生与生成。不能单靠它满足“任何人”。 |
| `character_created_on_actions.txt:1–18` | 覆盖非出生生成，包括脚本、角色设计器和多种原生生成人口路径。 |
| `child_birth_on_actions.txt:855–861` | 出生入口需要单独接入；核对其与礼仪、House 继承初始化的顺序。 |
| `religion_on_actions.txt:442` 周边说明 | `create_dynamic_rite` 跳过 `on_rite_created`。其他模组创建礼仪的脚本入口需要补同步或有限校正。 |

本轮没有在上述 on_action 集合找到覆盖所有 Dynasty／House 变化的通用钩子。收养、私生子合法化、庶支变化和其他模组直接改 House 后，必须有明确的再同步策略。建议正常路径走钩子，并做低频、范围明确的修正；不以每个角色每日遍历全世界作为默认实现。

扩展既有 on_action 时采用 `on_actions = { 本产品子钩子 }`；原版 `_on_actions.info:104–117` 明确不能靠追加第二个 `effect` 块来扩展已有钩子。出生文件第 976–1002 行还会分配家族，因此选择正确的后置同步点是实际需求，不能假设出生入口一触发，最终 House 就已稳定。

同时要防止 `set_house`、改礼仪、创建钩子互相重入导致重复建族。创建者身份不应充当永久索引：创建者死亡后，Rite 与 Dynasty 仍需独立保存并可读档恢复。若礼仪的 Faith 因分歧改变，绑定仍应追踪原 Rite 对象，不按 Faith 的变化另建一族。

**真实宗族不是额外的社团身份。** CK3 角色通过 House 属于一个 Dynasty。转入该模组宗族会离开原 House／Dynasty，而不是同时保留两份归属；这会牵涉姓氏、族长、宗族声望、传承、婚姻与继承资格、玩家接续等玩法。原来的血缘记录不应被模组重写，具体原生联动仍需观察。全部信徒加入同族后，原版亲族／同族约束也可能改变，不能把这一点隐藏在一个无说明的开关后。

## 背离罪恶、-100 好感与惩罚理由

### 原版已经提供的链路

`common/traits/_traits.info:149–160` 的 `triggered_opinion` 支持教义 `parameter`、`same_dynasty`、`same_faith` 等过滤。原版 `common/traits/00_traits.txt:11812–11816` 的弑亲者正是用教义参数加 `same_dynasty=yes` 引用 `kinslayer_crime_dynasty`；`common/opinion_modifiers/00_doctrinal_crime_opinions.txt:55–59` 再提供监禁、放逐、处决理由。

`common/opinion_modifiers/_opinions.info:58–83` 明确列出 `imprisonment_reason`、`banish_reason`、`execute_reason`、`revoke_title_reason` 和 `divorce_reason`。所以“其他人眼中有罪”是可以定向配置的关系，不需要给全世界施加相同犯罪状态，也不需要直接替换监禁／处决交互。

### 推荐候选

为“当前处于绑定宗族，但当前 Rite 不等于绑定 Rite”的角色维护一个专用背离状态特质。由特质的 `triggered_opinion` 引用一项 `-100` 好感修正，并给该修正配置监禁、处决理由；观察者需要具有宗族化教义参数，且与目标同 Dynasty。**不加 `same_faith=yes`**，否则跨 Faith 背离会逃过处罚。

这条路线复用了原版关系求值，可避免给每一对信徒／背离者建立大量永久 `add_opinion` 记录。回归后移除特质，预期随之移除该来源的好感和理由；不能把固定一年／十年的临时意见当作“背离期间一直有效”。原版其他犯罪、已发生的囚禁和死亡不由本模组回滚。

但该过滤仍有一项必须验证的前提：**观察者的宗族化参数必须来自其实际 Rite，而且当前信徒确实已同步到唯一绑定 Dynasty。** 若一个仍在旧宗族的人先转入另一个宗族化 Rite，在 House 同步之前也可能具有同一个布尔参数。不得把 `same_dynasty` 简写成 `same_rite`。需要验证同步顺序、不同宗族化礼仪之间的负例和参数取值来源；若原生条件不足以精确区分，就改用明确观察者／目标身份的定向关系维护，不能扩大罪行范围来迁就快捷实现。

“普通宗教罪恶”是另一层：原版罪恶／美德主要由 doctrine／religion 的特质配置产生。把共享背离特质直接列为所有宗族化礼仪的普通 sin，可能让不相关礼仪也施加原版罪恶好感和虔诚效果，造成多扣或跨族污染。因此第一阶段应明确显示“背离宗族礼仪”的专用罪行及原因；若还要求它出现在原版罪恶列表，须单独证明能维持同样严格的身份条件，不能以图标或文字替代真实监禁、处决理由。

### 有罪行理由不等于能对任何人立即执行

原版 `common/character_interactions/00_prison_interactions.txt:92–154` 仍调用 `allowed_to_imprison`。`common/scripted_triggers/00_scripted_triggers.txt:223–303` 保留领主、访客等管辖与身份条件；处决交互第 7057–7098 行仍检查目标是否被行动者囚禁。用户要求的是合法罪行理由，不能由此推导出跨国抓人、自动执行处罚或绕过原生交互资格。

后续验收必须查看实际处罚界面与罪行来源，分别确认监禁、处决是否获得本产品理由、是否仍产生其他来源的暴政／亲族后果；不能只读一个 trait 存在或提交 ACK。已有背离者被原版赦免／处罚后，持续背离是否重新提供同一理由，也需要独立确认。当前报告不承诺可无限重复惩罚。

原版 `00_prison_effects.txt:908–951,2680–2711` 实际消费 `has_execute_reason`／`has_imprisonment_reason`；新增特质还不会自动进入 `00_religious_triggers.txt:410–484` 的既有犯罪特质白名单。因此核心处罚界面与其他宗教事件的识别需要分别验收，不能把一处有理由外推成全部事件已适配。

`00_prison_effects.txt:2485–2512` 的 `consume_all_criminal_reasons_effect` 会消耗多类理由，原版赦免也使用它。**不能用它清理本产品的单一背离罪行**，否则会消耗行动者对目标的其他犯罪理由。持续背离期间也不能周期性反复移除、重加 trait／意见，以免刷新已赦免的理由；回归后再次背离能否产生一次新的犯罪实例，仍需实测原生消费记录。

## 改革、关闭选项与边界选择

首次启用需要建立宗族并收拢当前全部信徒；同一 Rite 继续编辑且仍选择宗族化时应复用原 Dynasty，不重复建族。创建“子礼仪”则有新 Rite 身份，即使名称／教义相同，也应新建自己的宗族，不沿用母礼仪宗族。

从“宗族化”改回“无”的历史规则没有在需求中指定。建议停止强制加入和该产品的罪行／好感规则，保留已存在的真实 Dynasty 及人物当前身份，不试图给每个角色恢复一个可能已经消亡或变化的旧 House。重新开启是否复用旧绑定、一个角色转入另一宗族化 Rite 是否允许离开原族、宗族命名和族徽来源，均应在进入实现前形成明确规则；本轮没有替用户执行这些设计选择。

同族出生但未信绑定 Rite 的儿童按原文字面满足背离判定；不自行添加年龄豁免。普通原生监禁、处决是否允许该身份，继续由原版交互决定。死亡人物保留历史，不追溯改写死者宗族；“所有信徒”在实时同步中指存活角色，伯爵领信仰不具备 Dynasty，不做伪造归属。

## 后续最小验证方案与交付边界

本轮的交付是报告，不开始下表的原型。若后续进入开发，先完成最短端到端链，再扩充兼容场景；不把源码、二进制登记、静态测试或一次接口 ACK 当作玩法通过。

| 验证 | 必须观察的实际结果 |
| --- | --- |
| 两选项／取消 | 新局、旧档、原版已有 Rite 均有可读默认；有无先知技能均能按设计选择；取消不建族、不迁人。 |
| 创建／改革 | 用原生界面实际提交；新 Rite 绑定唯一 Dynasty／House，创建者和既有转入角色全部加入；失败不留下孤立宗族。 |
| 人群覆盖 | AI／玩家、有地／无地、出生／生成／正常改宗，均按真实最终 Rite 加入；改 House 的既有剧情与庶支路径能被校正。 |
| 处罚正例 | 背离者保留该 Dynasty；本 Rite 信徒看到唯一 -100 来源，并有监禁理由；合法囚禁后有处决理由。 |
| 处罚负例 | 同 Faith 不同 Rite、其他宗族化 Rite、其他 Dynasty、已回归、已关闭宗族化各有对照；不相关观察者不获该理由。 |
| 原生限制 | 独立外国角色、有地／无地者、囚犯／非囚犯、已赦免者分别读回合法性、实际理由及暴政结果；不自动提交任何处罚。 |
| 持久化 | 保存／冷重载、创建者死亡、分支 Rite、重复编辑、Faith 分离后，绑定、House、罪行与 -100 保持正确且不累积。 |
| 多人 | 两名玩家观察同一目标，意见和理由按各自真实 Rite 计算；同步开关和改 House 不产生分歧。未跑前不宣称多人支持。 |

未来实机使用仓库公共 `tools/ck3_mod_acceptance.py` 流程及当次全局 runtime manifest。此文不给新产品另建私有 runner。未来新增宿主／构建编排按更新后 `AGENTS.md` 的 Java + Maven + Quarkus 规则办理；CK3 原生脚本与 GUI 不因该规则改写成 Java。实际实现文件新增／修改后，再做适合该范围的静态检查；本轮没有生产代码，静态类型检查不适用。

未来发布仍需要独立产品清单、正式 staging 构建、源码业务验收、真实 Workshop 上传／缓存加载和永久 changelog；这些均未执行，不能把当前目录视为已可安装产品。

## 存储与来源复核

本任务沿用[通用存储策略](../../docs/storage-retention-policy.md)和[版本化参数](../../docs/storage-retention-policy.json)。只保存小型结论、来源哈希和必要二进制切片，不复制 EXE、完整安装树、存档或全量反汇编。机器、观察时间、任务开始／闭场容量与未知预算项在来源清单记录。未完成重型写入准入，不把容量快照称为完整空间预留；本轮无重型采集、构建或游戏运行。

报告与来源摘要按 `record` 180 日复核；可重建的临时研究材料按 `derived` 48 小时复核。持续开发时重新读取实际安装与新版本，不从本机记录外推其他机器。证据过期或原始安装不可读取时保留来源身份和可用性说明，不以同名新文件冒充旧来源。
