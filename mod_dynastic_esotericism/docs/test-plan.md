# 宗族化密教：测试与发布方案

版本：1；制定日期：2026-10-24。本文在[需求文档](requirements.md)之后、功能编码之前制定。目标版本 0.1.0；尚无业务 PASS 或发布事实。

## 测试分层与证据

离线校验确认文件格式、引用、两选项合同、生产者到 staging／manifest 消费者及重建一致性；实际游戏验证 GUI、宗族、好感和犯罪理由。先检查 `open_kaishek` 是否能覆盖确定性语义；可用则运行相应子集，不可用或不支持则记录实际原因与未覆盖范围，不能冒充游戏结果。

每个实机编号按 `tools/ck3_live_run_id.py allocate --mod dynastic-esotericism` 分配，回执带 `machine_id`、UTC 观察时间、实际 CK3 build／EXE SHA、产品 commit、staging manifest 和公共 runtime 绑定。实机前按当前规范后台确认 Steam 离线，领取本机唯一 CK3／屏幕槽；不抢占其他有效游戏或录制。

采用独立产品实验 profile 和公开标注的最小准备 fixture，具备足够虔诚、合法礼仪编辑资格以及下表控制人物；不把测试专用定义混入正式产品。生产入口仍以原版 GUI 或已有通用 MCP 操作触发，准备状态和测试动作分别记账。正常路径优先原生 MCP，动作未知结果不重放。

## 离线检查

| 编号 | 范围 | 通过条件 |
| --- | --- | --- |
| OFF-01 | 原生脚本与本地化 | BOM、括号与语法、命名空间及引用完整；不误用不存在的 effect，不追加覆盖原版已有 effect 的 on_action 块；每个 effect 文件符合仓库大小规则。 |
| OFF-02 | 状态合同 | 无／宗族化默认、双向绑定、人物迁移、背离／回归／关闭／重新开启的生产脚本与预期路径一致；跨 Rite 和跨 Dynasty 负例具有独立条件。可覆盖的真实脚本交由离线解析器校验。 |
| OFF-03 | 正式构建 | Java 编译与必要测试实际执行；从源生成正式 staging、ZIP 和强类型 manifest，再由真实消费者逐文件读回；验证漏文件、未知字段／错误类型、测试文件混入与 supported_version 兼容 tag。 |
| OFF-04 | 可交付包 | 正式内部 descriptor 无 ID，脚本和资源引用可用；README／描述不宣称未验多人或其他版本；版本、构建输入和所有文件 SHA 可追溯。 |

测试实现应覆盖真实构建生产者到校验消费者，不用与实现同构的断言替代验证，不为文案或可逆低风险改动额外扩展测试矩阵。

## 核心游戏场景

| 编号 | 对应需求 | 准备与动作 | 必须读回的结果 |
| --- | --- | --- | --- |
| LIVE-01 | 01、02、16 | 新局普通合格角色，无先知技能，打开礼仪创建／改革／编辑；切换两个选项后取消 | 两个选择可见可用；默认无；原 Rite、Dynasty、House、资源保持，未创建绑定。 |
| LIVE-02 | 02–04 | 在原生草案选择宗族化并实际提交；同 Rite 有玩家、AI、有地、无地和儿童代表 | 新 Rite 与唯一新 Dynasty／House 双向绑定；创建者及全部已转入信徒加入；未改信的创建者后代保持原归属；无额外模组费用。 |
| LIVE-03 | 03、12 | 对同一 Rite 编辑、重复同步；关闭后重新开启 | 不重复建族；关闭清除本来源规则且保留历史宗族；重新开启复用原绑定。 |
| LIVE-04 | 04、05 | 普通转入、转出、生成角色和实际出生；制造受支持的收养／旁支变化 | 最终 Rite 与应属 Dynasty 一致；合法本族 House 保留；出生次日已同步；记录周期校正实际耗时。 |
| LIVE-05 | 06–09 | 同族目标转为同 Faith 另一个 Rite，再转不同 Faith；绑定 Rite 观察者查看好感和处罚 | 两种背离均有且仅有本来源 -100；实际监禁理由成立；合法囚禁后处决／放逐理由可读，保留原版管辖限制。 |
| LIVE-06 | 07、08、13 | 第二个宗族化 Rite、非宗族化 Rite 和其他 Dynasty 的观察者查看同一背离者 | 各负例不获得本来源 -100 或犯罪理由；两个宗族化 Rite 交叉转换后没有旧族残留或新族误判。 |
| LIVE-07 | 10、11 | 回归绑定 Rite，保持另一独立原版犯罪；再次背离；由原版赦免后继续推进并校正 | 本来源随状态撤销，其他犯罪保留；持续背离不因修正反复刷新理由；重新背离及原生犯罪消费按真实结果记录。 |
| LIVE-08 | 05、14 | 保存正式场景并正常退出，冷重载；另做创建者死亡／族长变化代表路径 | 绑定、House、背离、-100 和实际罪行理由持续正确，不重复初始化、不重复建族；原版继承过程保留真实结果。 |
| LIVE-09 | 01、16 | 加载没有本产品状态的独立旧档，经实际显示的旧档启用入口初始化（如需要） | 缺省为无；原版可玩创建者两项知识可用；未启用的 Rite 与人物不迁族；初始化入口完成后消失；无错误日志。不能由fixture提前设置完成变量。 |

可以在同一次受管运行中连续执行有共同准备的场景，但保存每一步独立后态。只有涉及冷重载才重启；不逐个角色重启、不要求穷举全角色或全部原版宗教。实际没有执行的场景保持 NOT_RUN，不能从同类接口推算 PASS。

2026-10-24 R0001 后合同勘误：原生 `add_known_doctrine` 仅支持 `is_playable_character`，知识断言仅对满足该原版资格的创建者适用。LIVE-02／04 的儿童、无地 NPC、生成角色与真实新生儿仍必须通过完整 Rite／Dynasty／House 归属断言；不可玩角色不再被要求接受原版拒绝的知识副作用。第二 Rite 的测试输入使用实际可玩成年伯爵，经原版转礼仪与知识初始化后创建，不直接赋予测试知识。下一场必须检查新局、转换、生成与出生阶段没有不可玩知识错误，并重新执行全部既定核心场景。机器与原失败日志来源见需求文档末尾；R0001 的失败结果保持不变。

人数、Rite／Dynasty／House 对象、角色当前归属、好感逐项来源、`has_imprisonment_reason`／`has_execute_reason`／`has_banish_reason` 与交互最终理由须来自实际原生读回、游戏保存内容或实际界面。解析错误、raw key、错误罪行方向、跨派污染和未移除的本来源均为业务失败；fixture／宿主故障单独分类并保留原回执。

2026-10-25，`machine_id: desktop-3fevhd2-1c74096080`：R0009 的原 `binding_and_members` FAIL 保留。下一轮 capture 后的原 `des_acceptance.2` 改在真实 +2 日检查，仅用于区分原版转换与 `on_rite_change` 的完成时序；生产同步、全成员量词及 REQ-05“同次同步”不变。这不是两日产品时限或修复通过。Root 须在真实 +1、+2 日分别读取完整原生成员集合及同帧保存，逐 ID 对照 Rite／Faith、存活、实际 House→Dynasty 和 stock `changed_rite_flag` 原始 presence／value／tick，保留新增／消失及原 House。缺失、null、false 不合并，不以不同 House 直接推断不同 Dynasty。单个 flag 不能独立证明本次回调时点。+2 仍有任何活成员未归族或原必要守卫失败即保持 FAIL，不等周期校正、不补写状态、不筛除新增者；即使 +2 后态通过，也不能替代 LIVE-04 的普通转换时序验收。详见 [R0009 原件摘要](acceptance/R0009-2026-10-25.json)。

真正多人场景尚无预先资格，不以单人多角色控制宣称多人通过；首次发布如未进行多人验收，明确标注“多人未验收”。其余上述首版核心功能未通过时不公开发布完整功能版本。

2026-10-24 R0003 后、R0004 分配前调整：首次 GUI phase 以实际 `DESAF: TEST PASS fixture_ready` 为门槛；原准备事件使用 `days = 1`，到第 1 日不能替代事件、知识及资金后态。开局保留原 Catholic／Roman Rite，最终资格按原生草案 `Can` 验证。R0003 实际单日动作耗时 8.566 秒，至后续 snapshot 完成共约 12.315 秒；400 日的纯日推进规划估计约 82 分钟。故下一场预先固定 hold 9000 秒、整体 timeout 10800 秒，readiness 1800 秒、正常退出预留 180 秒、400 自然日上限不变。R0001–R0003 原输入、3600／5400 秒预算及 RED 结果不修改；运行中仍不得延长 deadline。此安排与语法修正均不授予业务通过。

R0003 引擎实际报告的 fixture 错误对应四份资源修改：族长读取由不存在的 `dynasty_head` 改为原版 `dynast`，仍要求存活且不是已死创建者；曾尝试对 `$PASS$`／`$FAIL$` 去除模板引号；独立 outsider 和既有未改信后代分别补 `location = root.location`，不添加 employer，也不改变后代的 Faith／Rite／House／father 负例。四文件 grammar parse 已实际退出 0、diagnostics 空且 roundTrip true；`ck3-1.20.0.4` semantic profile 未注册，validate 为 4／UNSUPPORTED。**R0004 已证明去掉模板引号没有修复整句参数的引擎展开，不能把该尝试记作成功修复。** 原件与 SHA 见[交接第 4.1 节](../../docs/handover/2026-10-24-dynastic-esotericism-vacation-handover.md)。

Java `FixtureEmitterTest` 验证实际资源生产、打包字节／源一致、manifest 和各 case 文件边界；它没有 CK3 语义解释能力。四项修正的正确性须由重新构建的 JAR／fixture 和下一场真实加载及业务后态确认，不新增源码字符串匹配来冒充语义回归。首个非 confirm 礼仪开窗若返回 pending，保留原 native receipt，用 action context 的 `observation=draft/current_rite` 独立查询；不得对它调用只接受 final-confirm claim 的 collect，也不得重放 open。仅 `confirm_once` pending 可 collect，最终仍须独立 verify-completed。

2026-10-24 R0004，`machine_id: desktop-3fevhd2-1c74096080`：实际加载继续报告四组参数化日志的 `Unknown effect: TEST/NEGATIVE`、case token 和 `else/else_if not following an if`；业务保持 RED。2026-10-24T13:43:22.948973Z 的原件观察在 `C:/ck3-dynastic-esotericism-20261024/R0004-load-error-a01/actual.json`，7,362 B 错误日志 SHA 为 `b54a431decfc4efc705a4b99b9ac2e475ca1ac9b2d528e56a632df20ce4deff8`。新候选把 `.3/.4` 的四个 helper 调用替换为原文静态带引号日志，删除两个仅重复检查并记录日志的 helper，保留引用恢复效果。既有 lexer／AST parser 已逐项证明：外层 `limit` 包含 positive helper 全部五项断言，外层 outsider scope 与 negative helper 五项断言 AST 完全相同；完整 `limit`、原 else FAIL、scope 及最终 verified flag 均不改变。

新增 Java 回归从真实 `FixtureEmitter` 产物读取 marker 合同，用既有 lexer／AST parser 检查必需 marker 的静态日志定义及原 R0004 完整守卫，并要求实际保全的 R0004 两份坏资源被拒绝；原件与 AST 基线在 `tools/src/test/resources/acceptance-r0004/`，不进入正式包。该用例还检查关系准备只能由 fresh setup `.1` 的 immediate 调用一次；独立读回入口只能调用观察 helper，helper 除 fixture 自身旗标／命名 scope／日志外没有状态写入。当前仅从 Java 用例抽取的兼容 probe 实际确认收紧 presence 守卫后的源候选 22 个 marker／两组守卫／准备路由／只读关系入口通过、原 R0004 输入以四个非字面量日志拒绝；回执为 `C:/ck3-dynastic-esotericism-20261024/R0004-static-log-and-rite-input-probe-a03.actual.json`（1,656 B，SHA `f9fcd881ed2c4d2c5b9a3f1b55039e36bfda3df3fffe324875e45ca4ad8df3f3`）。完整 Maven／新 JAR／新 fixture 待合并候选的干净 checkout 一次构建；这些 AST 检查仍不授 CK3 语义或业务通过，也不热改 R0004 冻结源码。

R0004 的实际 native Can 在名称、`des_dynastic`、资源齐备后仍以“你没有傀儡可以创建礼仪”拒绝。新 fixture 明示准备原版角色关系：保留现任 `cp:councillor_court_chaplain`；缺失时在符合原版资格的玩家上仅调用一次 `assign_landed_realm_priest_effect`，由其现有筛选选人，仍缺失则 FAIL。只有明确存在的实际司祭为 AI 成年非无能、没有操控者、玩家神学傀儡槽为空时，才按原版 `set_puppet` 和共享无选项副作用 helper 建立真实 `theological_agent_puppet` 关系；fresh setup 不传六项互动支持 scope。不清理冲突关系、不任意生成替代角色、不修改 Can 或产品绑定，也不声称已经调用／接受互动或支付其 100 虔诚费用。原版来源与完整 SHA 在 `C:/ck3-dynastic-esotericism-20261024/rite-permission-diagnosis-a01/diagnosis.actual.json`（67,960 B，SHA `3bdf73da04af31c7d0049e0f18f7fc431d4e257421eb76e450b69976ab52a963`，同一 `machine_id`）。

setup 与独立读回决议分别重读真实 cp、神学傀儡、反向操控者、`is_puppet_action_valid`，逐项记录静态 PASS／FAIL；聚合资格还要求同一 cp、原版 actor/recipient 约束和 `can_create_rite_trigger`。`fixture_ready` 必须消费这次实际读回得到的 fixture 旗标。这里认证范围只是原版角色关系和已知脚本门禁；后继实机须在独立 epoch 读取 council full ID，并填齐五项名称、教义和资源后，读取草案完整 native Can，再执行原有 prepare／confirm-once 与 Rite 独立保存后态。当前新关系输入尚未实机执行，R0004 仍为 RED。

## 真继承后由新族长重新开启：后继 core 候选

2026-10-25，`machine_id: desktop-3fevhd2-1c74096080`：R0007 已在实际 CK3 1.20.0.4 创建 Rite 150／Faith 13，实际玩家为 31254；随后 capture 决议因 House 使用 Character 的 `dynasty` 链而原生拒绝，整体仍为 **0/6、业务 RED**。产品四处 `house_dynasty` 修复见[引擎错误记录](2026-10-25-engine-house-dynasty-fix.md)，须由新构建／新图／新实机验证；不回写 R0007。下列配置、fixture 与共享 clock 的继承支持均为待验候选，不能把源码准备当作已继承。

core 原始 JSON 本身是 adapter 配置。现有三个策略字段放在它的**顶层**：`allow_actor_change=true`、`actor_transition_days=[]`、`continue_as_heir_requirements`。不新增嵌套 `adapter_config` 或其他公共字段。空 transition 数组不预选任何自动 adapter advance 序号；它不是日期表。actor 许可只允许观察身份中的玩家分量改变，同 run／pipe／PID／generation、暂停可用原生帧、日期单调、最初起日及截止日守卫保持；缺少字段的其他 case 仍默认禁止。共享 clock 必须从同一已 pin 的原 prepared contract 顶层消费该布尔值，不能重置计时或用第二份可编辑 JSON 提权。

以下四条既放入 `continue_as_heir_requirements`，也放入 phase 5 的普通 requirements。内部推进可能不触发 adapter 的 dead-player fallback，Root 仍须逐项保留真实原件：

1. `actual_predecessor_death_and_primary_title_succession`：前任真实死亡，原主头衔实际继承。
2. `actual_current_player_is_the_pinned_living_primary_heir`：新存活玩家等于事前 pin 的真实 primary heir。
3. `actual_same_primary_rite_and_bound_dynasty_survive`：原 primary Rite 与绑定 Dynasty 身份持续一致。
4. `actual_native_current_rite_head_is_the_successor`：新玩家确为当前原生 Rite head；继承头衔不自动等于成为 Rite head。

六个 phase、旧 required assertions 和原 marker 含义全部保留。phase 1–4 仍完成默认／取消／真实创建、成员、同 Faith／跨 Faith 背离、罪行方向及悔改。phase 5 的内部顺序调整为：

1. **旧 Root 存活且仍为玩家时先做完长程观察**：`des_acceptance_extended_start_decision`、第二 Rite 31 日、cross-rites／migration、独立 stock crime 加 repentance、实际出生再推进恰好一日、生成／合法旁支／外改 House 校正、原 61 日 timer 证据，以及**既有第二位 NPC founder 死亡后真实 31 日稳定性**。第二 founder 证明不能被新的玩家死亡替代。所有 observer、真实日期与原 actor 证据在转移前固定；允许时间重叠不保证预算足够。
2. `des_acceptance_primary_heir_prepare_decision` pin 真实前任／primary heir／primary title，仅以公开 stock `set_character_rite` 输入让真实继承人进入已创建的同 Faith Rite。至少经过一个实际自然日后，`des_acceptance_primary_heir_readback_decision` 重验继承人仍相同、存活成年、实际继承资格及自然形成的 Rite／Dynasty／House；另留 native 与独立 Save 读回。不能设置其 House／Dynasty 或产品绑定；未成年、失位、缺失或不合格为 NOT_READY。
3. 对实际旧 head 执行 `des_acceptance_edit_input_prepare_decision` → `des_acceptance_edit_input_readback_decision`，只复用原空槽神学傀儡准备并读回真实关系。编辑 readiness 与创建 readiness 分开；创建后 `can_create_rite_trigger=false` 不等于不可编辑。实际选择 None，验证实质草案变化、完整原生 Can／报价，确认一次并独立核 closed、同 Rite／Dynasty。
4. 所有旧 Root observer 完成且 closed 已证实后，`des_acceptance_primary_death_stage_decision` 一次安排次日 stock death；用已有事件边界推进观察真实转换。先从 native 与独立 Save 证明上述四项，再调用 `des_acceptance_successor_readback_decision`。它没有选择／设置玩家或 head 的功能，不等待额外 fixture 事件；缺少自动续行的可用原生帧、要求未支持的 Continue 或新玩家不是实际 head 均停止为真实未合格，不改原版一次限制。
5. 在真正新 head 上再次执行同一 edit prepare／readback，独立确认其 `has_edited_a_rite` 未用过；不清除、复制或伪造原版 once flags。实际选择 Dynastic、完整 Can／报价、确认一次、处理真实事件并独立核 reopened 与原绑定复用。
6. **最后才在最终新当前 head 上完成原赦免整链**：`des_acceptance_pardon_prepare_decision` 后真实一日 → 实际合法 `pardon_interaction` 一次 → `des_acceptance_pardon_observe_decision` 后真实 31 日。保留每个原 pardon assertion／marker；不能迁移旧 Root 已完成的赦免观察。独立原版犯罪保留仍由前面的原 observer 证明；最终新 head 对目标的实际读回要求本来源 trait／opinion／pair 保留、三种产品犯罪理由均无，不能借 actor 改变豁免。

fixture 单一命名合同为上述六个新决议，新增唯一 marker `DESAF: TEST PASS actual_primary_heir_successor`；旧 22 个 literal marker 保留。三引用是 `des_test_ref_predecessor`、`des_test_ref_primary_heir`、`des_test_ref_primary_title`。`des_test_primary_heir_prepared`／`des_test_primary_heir_ready`／`des_test_primary_death_staged` 只属于旧 Root；`des_test_successor_verified` 仅在新 Root 实际身份守卫成立后设置。原 `global_var:des_test_extended_owner` 保持前任审计锚点，不另设可切换 owner。仅迁移 fixture producer 明列且确实存在的有限引用与已证实历史旗标，历史证据仍归原 actor；不迁移 pardon／reopened／冷载锚点、准备计时器或待执行事件，不扫 `des_test_*` 前缀，不复制／直接写产品状态、原版 flags、head 或 player。资源生产者、Java emitter 与 Root 消费者须共同核这个合同。

phase 6 的 `reopened_binding` marker 只使其可就绪；phase 5 必须先完成新 head 的真实 pardon31 后才返回。phase 6 再核全部已 pin 长程原件、前任／继承／新 head／原绑定和最终赦免后态，再为**当前新 head 与最终目标**调用 `des_acceptance_cold_anchor_decision` 并实际 Save。保存的 player ID／date、Rite／Dynasty／House／关系必须独立解码；cold 使用这份精确保存与当前新 head，零自然日重载后仍须检查新 head 对目标无三种产品犯罪理由。原前任 Save 不能改标签充当新 head 保存；独立 old-save bootstrap 仍必做。

400 自然日、9000 秒 hold、10800 秒整体 timeout 以及原 readiness／正常退出预留不变。死亡／赦免前须测实际已用天数与剩余墙钟，不能延长冻结场次。完整 Java clean verify、producer／资源／manifest／包导入闭环与共享 clock CI 通过后才可构建新候选图；它们仍不替代实际继承、两次原生编辑和完整六 phase 业务。

## 发布验证

| 编号 | 必须完成 |
| --- | --- |
| REL-01 | 冻结 0.1.0 正式 source commit／tag、staging／ZIP／manifest；版本和说明一致；未上传前保持 Workshop ID 未分配。 |
| REL-02 | 首次真实 CreateItem／SubmitItemUpdate 成功，核 owner、app 与新 item；首次公开说明写明本模组初始基线、真实范围和限制。 |
| REL-03 | 提交前冻结完整 Change Notes 文本、字符数、行数和 SHA-256；匿名读取目标 changelog 条目并按 HTML 解码、换行规范化后全文精确匹配，保存 entry ID。 |
| REL-04 | 匿名回读标题、描述、完整 tags 与兼容版本右栏；只从正式 descriptor／单一 registry 派生兼容 tag，保留原分类字符串及顺序。 |
| REL-05 | Steam 实际下载新物品；逐文件与正式构建一致；通过公共 `workshop_cache` 验收证实 CK3 实际加载该缓存，只需稳定主菜单和日志／原生加载证据，不重复业务场景。 |
| REL-06 | 正常退出游戏、保存必要证据、释放 keeper／租约，恢复并读回 Steam 离线；重建 staging 去掉启动器可能写入的内部 ID。 |
| REL-07 | `docs/release-changelogs/dynastic-esotericism/0.1.0.md` 永久记录 initial baseline、实际 item、日期、tag／commit、玩家变化、兼容、限制和全部证据，提交推送 master。 |

## 测试结果文件

结果写入产品 `docs/acceptance/`，实际运行大文件放获准外置目录，小型总结入库。结果表逐项包含 PASS／FAIL／NOT_RUN 与实际证据，不预填成功。若共享宿主、Maven、离线状态查询或存储准入阻止实机，继续不依赖该故障的编码、离线检查和发布材料准备，同时修复实际阻点；不把源码准备完成写成整个产品已验收或已发布。
