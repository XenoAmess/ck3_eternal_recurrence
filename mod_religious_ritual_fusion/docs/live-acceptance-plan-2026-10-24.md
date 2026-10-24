# 宗教礼仪融合：实机验收执行方案

日期：2026-10-24。本文细化[测试验收方案](test-acceptance-plan-2026-10-24.md)的 L1–L3，供下一工作包接入和执行；**本次只制定方案，没有部署、启动 CK3、准备场次或执行实机用例**。产品范围和默认数值沿用[编码方案](implementation-plan-2026-10-24.md)，不在验收中另改玩法。

已知开发基线为生产提交 `42af27c3b1601a7066636a75414defd48972a3f0`：10 项离线测试、67 个正式载荷文件及 64 个脚本／GUI 文件 parser 预验已通过，见[静态回执](evidence/implementation-static-2026-10-24.json)。这不授予本方案任何实机 PASS。研究绑定机器 `4-8e1c2f1861` 的 CK3 1.20.0.4／build 25734779，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；执行时重新核对实际安装及运行时，不能继承历史机器资格。Empire Faith Gate 按用户确认作为该原版版本组成。

## 1. 本轮验收要回答的问题

1. 正式 staging 能否被该 build 原生加载，自定义融合窗口的 Tenet／Doctrine scope 是否真实可读、可选、可显示。
2. 同 Faith 礼仪融合和不同 Faith 宗教融合，能否经生产按钮各创建一次符合最终选择的对象，真实扣费一次并让创始者采用。
3. 不合格、取消、草稿失效、重复提交及 unresolved 是否按合同拒绝，双方原对象是否保持原内容。
4. 实际生成对象、双来源历史、收费、冷却和草稿／未决状态是否跨正常保存、退出和新进程冷重载保持。
5. 代表性跨 Religion 组合、既有存档与原版礼仪创建是否在声明范围内工作。

首期只验单人、简中主流程及英文显示检查。AI、多人、动态命名编辑、双父 Religion、全世界传播、Workshop 发布与缓存验收不在本方案通过范围。代表性组合通过不等于所有宗教组合兼容。

## 2. 启动前必须补齐的接入

截至本文编写时，RRF 尚无公共实机 case、业务 fixture 或原生窗口操作资格。以下是待交付项，不能把本文的拟定名称当作已注册接口。

| 待交付项 | 实现要求及完成证据 |
| --- | --- |
| 产品及编号注册 | 在 `workshop/products.json`、`tools/ck3_mod_acceptance_products.json` 和 `tools/ck3_live_run_id.py` 的 canonical key 登记 `religious-ritual-fusion`，Workshop ID 为 null；不借用其他产品 key 或重新从 R1 覆盖历史编号。 |
| Java fixture producer | 扩展本产品 Java／Maven／Quarkus 工具，生成独立 fixture、严格业务输入及 prebuilt manifest；不新增 Python 产品执行模块。正式 builder 的 67 文件清单与 fixture 清单各自固定，fixture 不进入正式 staging。 |
| 公共 adapter 配置 | 优先复用现有 `generic_product_adapter.py` 的 prepare／execute／verify 三接口，用产品 JSON 声明断言、GUI phases 和 source pins；公共缺口修共享实现，不另写私有 runner。 |
| 真实 GUI 操作 | 资格化决策 Rite 目标选择器、独立 RRF 窗口、候选列表、ScriptedGui 选择／取消／确认和诊断重开；存在原版 Rite action 不代表支持自定义融合窗口。 |
| 独立后态观测 | 取得当前角色资源、变量／列表、Rite/Faith 身份与实际内容、对象新增集合、冷却期限和存档读回；只读 provider／存档解析必须绑定该 build，不能以 fixture 写入的“成功标记”代替。 |

公共配置的现有合同来源为[统一入口](../../tools/ck3_mod_acceptance.py)、[prebuilt fixture 校验](../../tools/ck3_mod_acceptance_prepare.py)和[通用 adapter](../../tools/ck3_mod_acceptance_cases/generic_product_adapter.py)。接入时以实际源码校验字段，不从其他产品拷贝一套 host／native 版本。

- registry case 需声明 adapter/config、initial_plan、startup、五项 budgets、required_mcp_tools、normal_close、business_contract_applicable、case_scope 和通过范围。
- generic contract 需声明 schema/product/case_id/acceptance_scope、fixture_source、maximum_natural_days、failure_prefixes、gui_phases、source_contracts、post_start、required_startup 与 forbidden_startup。
- `ck3-mod-acceptance-prebuilt-fixture-v1` 固定 schema/product/case_id/machine_id/observed_at_utc/fixture_root/producer_source_pins/files/receipt。producer pins 为仓库内来源；文件表含 descriptor，拒绝额外文件、链接和漏列。receipt 的 required_markers、required_product_markers_minimum、fixture_contains_business_effects 如实填写。
- inputs 提供新的 state_dir、case_inputs.product_dir、prebuilt_fixture_manifest pin 和 plain_configuration；四份实际配置为 `pdx_settings.txt`、`tutorial.txt`、`presets.txt`、`player/game_rules/presets.txt`。

**generic prepare 只检查产品 descriptor 后复制，不消费 RRF 的正式 Java manifest。** 因此必须先执行本产品 Java verify，再把冻结 staging 交给 prepare，并核对部署／挂载副本与同一正式文件清单一致。准备成功、工具名存在或 `source_build_ready=true` 均不能代替动作及后态的实际资格。

## 3. 冻结输入与启动准入

每一场均从唯一公共 runtime manifest 和本机路径映射进入；产品不单独指定 host、source_root、DLL、injector 或 engine。记录实际 owner checkout HEAD、生产来源 revision、staging manifest SHA、fixture producer／fixture SHA、prepared-case SHA、runtime manifest pin、机器与版本，保留各字段原本的身份含义。

在 prepare／allocate 前完成以下检查：

1. 用 `tools/ck3_live_run_id.py machine` 取得稳定 machine_id；核 EXE 文件身份、SHA、build、源绑定目录和当次实际 DLC。版本或来源变化时先审查差异，不将旧 1.20.0.4 结果外推。
2. 对冻结代码执行必要的 Maven verify、正式构建和独立 verify。使用执行机器命令行默认 `mvn`，最低 3.10.0，逐机读回版本、home 和来源，不固定绝对安装路径。已验证且内容未变的同一工作包不反复重跑；修复改变载荷时形成新提交、新 staging 和新回执。
3. 先评估 open_kaishek 可覆盖的确定性部分。对本次载荷执行 parser，记录工具 commit／JAR SHA、profile、corpus SHA、实际命令和结果。当前只有通用 parser 证据，没有 1.20 融合语义认证；其不支持项明确保留。
4. 按[通用存储策略](../../docs/storage-retention-policy.md)与[参数](../../docs/storage-retention-policy.json)核容量、项目占用、输出峰值、其他未消费预留、系统增长预留和配额。预算未知时不进行实机重型写入；只读 free 快照不构成预留。
5. 读取任务总线和当前机器 owner／CK3 进程；同机仅一个受管实例。allocator 接续该机器最新真实 live／keeper／CAS 释放链，不因本产品首次实机而采用“新机器 bootstrap”。
6. 启动前后台运行 `tools/steam_offline_state_probe.py --receipt <new-path>`。当前公共门禁要求同机、实际 Steam 身份与合格原生来源，receipt 观察年龄 0–30 秒，`status=offline` 且 `offline_mode=true`。在最终准入前取得新鲜回执；不可用则不启动，不抢焦点、不截图、不切线上。

allocate 原始 `allocated-context.json` 保持不变；创建后继 context 加入实际 reviewer 和 steam_offline_receipt，公共 run 从 context 读取。没有 `--steam-offline-receipt` 这个 run CLI 参数。必须在动作前再次核 source／部署闭包；keeper 绑定 clean checkout 期间不热改该执行树，修复留到正常闭场后的后继工作包。

预算在 prepare 前声明。建议 UI／冷读 case 使用 command_timeout=300、readiness_timeout=1800、timeout=3600、hold_seconds=900、poll_interval=0.5、normal_close reserve=180 秒；包含多项真实操作的正向 case 使用 timeout=5400、hold_seconds=1800，其余相同。当前共享 readiness_timeout 最低为 1800 秒，这是截止上限而非要求等待时长。先按实际 adapter 校验预算关系，再冻结；运行中不延长截止来追认通过。

## 4. 可复现的场景准备

使用公共入口支持的标准开局和角色范围；优先沿用 1066 罗贝尔标准入口，fixture 的宗教与资源准备作为独立实验输入记录。若选择其他机制实验角色，须先核其适用授权范围，不能把既有影片实验例外默认为所有场次通用授权。

三组来源使用 fixture 专属对象，实际 definition keys 与运行时身份在 prepare 输入及准备后原生快照中固定，不使用历史动态 Rite ID。符号表示如下：

| 组 | 两来源的关系 | 预定核心与结果 |
| --- | --- | --- |
| S-R | A 与 B 为同 Faith 下不同 Rite | A=`{x,y,z}`、B=`{x,y,w}`；最终选择 `{x,z,w}`，z／w 分别证明 A／B 独有贡献。 |
| S-F | A、B 属同 Religion 的不同 Faith | 核心结构同 S-R，宗教融合结果的 Religion 应跟随 A。 |
| S-X | A、B 分属不同 Religion | 选择当次知识、DLC、原版条件均许可的实际组合；结果 Religion 仍跟随 A。受限内容另作拒绝对照。 |

x/y/z/w 必须替换为当前目录中真实、不同且最终组合合法的 Tenet keys。至少一组 B 为分歧 Rite，其独有核心 w 不属于母 Faith 主礼仪核心，专门发现错误的 `status=core` 过滤。固定一组实际可改的差异教义，验证 A 默认值切至 B 值后只保留同组一项。

fixture 通过原版准备通道建立来源和角色，不调用 RRF 的融合提交来制造待测“结果”。准备只写输入，准备完毕立即采集基线并停止 seed；生产操作阶段的观察／断言不得改钱包、冷却、选择结果或预期布尔标记。

角色基线为成年、有地、和平、未囚禁，无本产品冷却／未决状态，具有明确的 Rite、Faith、知识和 DLC。费用场景准备独立基线或独立受控角色：499／500、999／1000 虔诚。未知知识与先知 perk 的对照也使用明确输入；不在“知识应被拒绝”的用例中偷偷授予该知识。

至少保留创始者、配偶／近亲、廷臣、A 侧封臣与伯爵领、B 侧人物与伯爵领的实际身份和宗教，用于检验采用范围。无法找到合法跨 Religion 正向组合时，记录原生阻断和产品能力缺口；不能把取消正向用例或只测拒绝写成跨 Religion 功能通过。

## 5. 用例组织与执行顺序

下列 case 名称是**拟定的公共 case**，注册和 fixture 尚待实现。一个场次可以覆盖多个独立 cell，不为每条断言重启游戏；需要回到无污染输入时使用明确基线。冷重载必须另启进程。

| 顺序／拟定 case | 对应原矩阵 | 操作与必要结果 |
| --- | --- | --- |
| A `ui_and_rejection` | RRF-04、05、06、08、09、12 的新局部分 | 首次 L1 加载；检查决策目标、三栏、双语文本、图标和费用。先选择再取消／关闭／重开并切换来源、模式，世界对象、钱包、当前 Rite 与冷却不变；再执行下述拒绝 cell。 |
| B `rite_success` | RRF-01、06、07、10、11 的保存部分 | S-R，500 虔诚边界，经真实 GUI 选择 `{x,z,w}` 与差异教义并确认一次；核实际新 Rite、收费、采用、来源和历史。重复确认／重开决策不得新增对象或扣款。正常保存并退出。 |
| C `cold_reload`，kind=rite | RRF-11 | 消费 B 的真实存档和 product inventory，新进程冷加载，只读核对；不重 seed、重选或重建结果。 |
| D `faith_success` | RRF-02、06、07、10、11 的保存部分 | S-F，1000 虔诚边界，真实 GUI 确认一次；除公共断言外，核新 Faith、主礼仪、Religion、领袖与圣地。保存并退出，再运行 kind=faith 冷读。 |
| E `cross_religion` | RRF-03、09 | S-X 合法组合一次正向，再用受限内容作拒绝对照；核合法池、锁清理和结果归属。不可由 S-F 代授跨 Religion 通过。 |
| F `state_and_compatibility` | RRF-07、08、11、12 | 明确种入的 editing／unresolved 状态守卫、隐藏／重开及各自冷读；加载真实启用本产品前保存的旧档，核无批量改写，并做原版礼仪创建控制。各子项分别记范围。 |

最短业务链为 A 的取消和费用拒绝 → B → C；通过后继续 D 的创建与冷读、E 和 F。A 若只有原生解析失败，先保存最小原生日志并修产品；不继续后面的按钮场次冒充验收。某个独立 cell 无观测能力时只阻止依赖它的资格，仍可执行已准备好且互不污染的其他 cell。

### 5.1 真实 GUI 路线

打开宗教相关决策 → 选本用例来源 B → 确认打开融合草稿 → 读双方身份和候选 → 切换三个核心 → 将指定教义组切为 B 值 → 核最终内容及报价 → 点击生产确认 → 独立读回结果 → 打开“最近融合记录”核历史。

检查 `Scope.TenetType`／`Scope.DoctrineType` 的实际绑定、滚动后的候选及选择回显；不得出现空名称、原始本地化 key、错误图标或选择别项。核心总数从 2→3→尝试第 4 项时符合上限；已选项可移除，教义同组选择实际替换。知识提示、按钮可用性和提交后验需一致。

先检查当前 MCP 是否有足够的目标选择、候选操作、确认和查询能力；不足时先实现并资格化通用 typed 能力。原版 Rite 创建动作、fixture 直接调用 `rrf_commit_effect` 或改变量不能代替生产融合按钮的 GUI cell。只有 MCP 路线已有实证无法施工时才按项目规则降级，记录原因；视觉用于布局辅助，OCR 和按键 ACK 不构成状态真值。未资格化的通道不编造成现有可用工具名。

### 5.2 拒绝与变化 cell

| cell | 输入／扰动 | 拒绝断言 |
| --- | --- | --- |
| G1 来源与模式 | A=B、Rite 模式不同 Faith、Faith 模式同 Faith、不满足实际 `can_convert_to_rite` | 目标不可选或生产入口拒绝；不创建、不收费、不采用、不设冷却。 |
| G2 最终集合 | 0／2 个核心、尝试第 4 个、只有一方独有贡献、全公共项；注入重复核心或同组双教义作守卫负例 | 正常 GUI 不产生非法集合；受控非法草稿提交被拒绝。注入结果只授守卫 cell，不授 GUI 正向通过。 |
| G3 费用 | Rite=499、Faith=999；打开合法草稿后将实际钱包降至不足；500／1000 由正向场覆盖 | 不足时无本产品变更。暂停游戏记录日期和原始资源精度，不用界面取整文本计算净扣款。 |
| G4 actor | 未成年、无地、战争、囚禁、有效冷却、committing／unresolved | 入口或提交拒绝；保留输入合法性证据，不清掉成功冷却再证明“可再次融合”。 |
| G5 过期草稿 | 打开后 actor 改宗、A/B Faith 变化、选中核心或教义已不在来源、知识失效 | 最终提交重验并拒绝／要求重选，不按旧缓存创建。记录 GUI 是否及时失效；提交端拒绝不掩盖界面故障。 |
| G6 内容规则 | 未知 B 核心、未知 B 教义且无先知、先知对照、缺实际 DLC、原版互斥及 mode lock | 候选／提交条件与实际内容一致。至少覆盖 syncretism 自排除、一项合法苦行核心及冲突组合；缺 DLC 只能以真实未启用环境判定，不能伪造开关。 |

所有输入扰动均由 fixture／已资格化准备通道记录，固定扰动前后值。不能为制造“目标消失”擅自删除原版静态定义。实际不支持删除动态对象时，使用合法变更其 Faith／内容的失效场景，并把“对象销毁分支未执行”保留在覆盖表中。

### 5.3 成功的共同后态

成功必须同时满足以下独立断言，不能只看 toast、`rrf_state` 或 last_result：

- 本次新 Rite 的真实身份不同于 A/B；新增对象集合相对本次基线为一次创建。Rite 模式 Faith 不变且不新建 Faith；Faith 模式新 Faith 不同于双方，`new_faith.main_rite == new_rite`，新 Rite 属该 Faith，Religion 跟随 A。两模式均不新建 Religion／Religious Family。若引擎有附带对象，先查明归因，不静默放宽重复创建断言。
- 新 Rite 的实际核心集合**精确等于**提交前选择的三项，枚举其自身核心，不按母 Faith 主礼仪立场代替。未选 y 的真实 permitted／其他状态单独记录；所选教义每组符合预期，受锁清理内容亦核对。
- 真实虔诚净扣款分别为 500／1000，`rrf_charged_cost` 与其相符；后者不能独立证明钱已扣。actor 当前 Rite/Faith 采用结果；成功状态为 succeeded，草稿列表及来源变量已清理，结果引用和历史保留。
- 冷却的实际到期日为创建日加引擎十年，核存档／原生期限，不把十年粗算成 3650 日。不必自然空跑十年；另有即将到期 fixture 时只授期限边界守卫，不声称已自然经过完整十年。
- 结果 Rite 的 `rrf_rules_version`、`rrf_origin_a/b`、`rrf_origin_a_faith/b_faith`、`rrf_origin_mode/founder`、`rrf_origin_core_tenets` 和 `rrf_origin_doctrines` 与提交前快照一致；来源 A/B 的身份、所属、核心及教义未被融合改写。
- 创始者以外的近亲／廷臣／封臣／领地按预先记录名单读回。出现原版改宗连带时，用独立原版控制和调用链归因；不把未知扩散补写成设计行为，也不允许无意强制两来源全体信徒改宗。

确认后立即再试一次生产确认／调用路径，并读回新增对象、钱包、当前 Rite 和冷却均不再改变。暂停状态下先后提交也须受状态守卫；若没有可绑定的双击通道，仅授顺序重发通过，双击 cell 保持未执行，不用鼠标 ACK 补填。

### 5.4 未决状态与旧引用

当前实现有两条不同的部分结果路径：创建／内容后验失败可尚未扣款；`rrf_complete_success_effect` 则先记收费、扣费和设冷却，再采用，采用后验失败时已经扣款。两类分别读取实际对象、实际钱包和冷却，不能断言“unresolved 一律不收费”。任何未决都不能计为成功；若正常正向场进入未决，保留为失败／不完整并修复，不能以这段说明豁免正常收费与采用合同。

现阶段没有可靠的原生部分失败注入通道。fixture 种入 unresolved 或调用其标记 effect，只能验证“再次确认不重放、隐藏后守卫仍在、查看未决可重开、保存冷读仍受阻”，不能证明真实部分创建失败分支已覆盖。真实故障若发生，保存该次最小对象和费用证据，修共享生产路径，再用独立后继场重验。

提交开始不会主动清空 actor 的 `rrf_last_result_rite/faith`，本次未生成对象时可能仍指向旧成功结果。每次保存提交前的引用和已存在对象集合，通过实际新增对象与本次来源／模式识别结果；last_result 存在不等于本次创建。Rite 模式亦不把历史 last_result_faith 误认为本次新 Faith。

### 5.5 保存、冷重载与旧档

B 与 D 各产生一份真实成功存档，分别进行新进程冷读；使用实际保存成功后的文件身份、bytes/SHA、player ID、游戏日期和完整 product inventory，不能换成 seed 存档。确认上一进程已正常退出，再分配新场，PID／出生时间与前场不同。

冷读 fixture 必须使用 saved_campaign 路线并禁用所有 seed／修复写入。对照保存前后：对象的持久身份及关系、三核心、各组教义、actor 的 Rite/Faith、钱包、冷却到期日、双来源历史、收费记录均保持；打开历史窗口和再次确认不得重复收费。editing 的来源／选择和 unresolved 的引用／禁重放另各做一次冷读，不能用成功存档代替它们。

旧档场的输入必须是本产品尚未加载时真正保存的 `.ck3`，并保留当时 mod inventory；“加载本产品后清空 rrf 变量”不算旧档。加载后对未操作角色、来源宗教和全局对象作基线比较，确认无批量重写，再从原版 UI 做一次真实礼仪创建控制。控制测试单独计对象变化和资源，不能污染 RRF 的一次创建／收费断言。新局 L1 与旧档业务分别授予范围，不由主菜单成功加载外推。

## 6. 公共入口执行模板

**以下是接入完成后的模板，本轮未执行；尖括号必须替换为实际绑定值后才能交给 cmd.exe。** 所有模式使用同一 `--runtime/--products/--product/--case`，其中 product 为拟注册的 `religious-ritual-fusion`。

```text
<verified-python> -B -X utf8 tools/ck3_mod_acceptance.py plan --runtime <machine-runtime.json> --products tools/ck3_mod_acceptance_products.json --product religious-ritual-fusion --case <registered-case>
```

沿用上述四项选择参数，将 mode 替换并追加：

| 顺序／mode | 当次追加参数及消费内容 |
| --- | --- |
| 1 `prepare` | `--case-inputs <frozen-inputs.json> --prepare-output <new-prepared-dir>`；生成 prepared-case，state_dir 与输出均不能复用旧目录。 |
| 2 `allocate` | `--prepared-case <prepared-case.json> --attempt aNN --keeper-output <new-keeper-dir> --previous-live <latest-live-dir> --previous-keeper <latest-keeper-dir> --previous-release <actual-latest-release.json>`；有中间 screen epoch 时加真实 `--latest-screen-release`。按实际 allocator 输出保留 context 和 keeper HANDLE。 |
| 3 `preflight` | `--prepared-case <prepared-case.json> --run-context <reviewed-context.json>`；核 pins、输入、budget、工具、部署和来源。准备后也可先做不带 context 的预检，不能因此省略分配后检查。 |
| 4 `run` | `--prepared-case <prepared-case.json> --run-context <reviewed-context.json>`；context 已绑定实际 reviewer 和新鲜后台 offline receipt，完成该 case 的真实操作、保存与正常闭场。 |
| 5 `verify` | 与 run 相同的 prepared/context；只读消费原场业务、GUI 和 normal-close 证据，不重新执行业务。 |

allocate 取得的完整 run ID 使用当前机器和产品的真实递增编号，例如结构为 `machine_id--religious-ritual-fusion--R<n>`；aNN 是 attempt，不代替 run ID。实际 CLI、映射或公共合同更新后先核 `--help` 和源码，不照抄历史 FINAL manifest、旧机器盘符或旧截图流程。

每步检查内层退出码、超时及终态，前置失败不继续启动。run 完成后核实际 OS 退出、原 native cleanup、保存可读性、keeper 停止及最后序号，并经原 CAS 释放资源。verify 不授正常闭场时，该场不能获得完整 case 通过。后台退出接口优先，不能用强杀进程冒充正常退出。

## 7. 证据、判定与收口

每个 cell 的证据链为：**冻结预期 → seed 实际基线 → 动作前快照 → 单次操作请求及 ACK → 独立后态 → 保存／闭场 → 公共 verify**。GUI 证据和原生状态分别记录；日志中的预期标记、toast 或请求 ACK 不替代实际对象、钱包和保存内容。

小型汇总至少包含 machine_id、UTC 观察时间、run/attempt 全 ID、case/cell、owner checkout 与生产 revision、EXE/build、runtime/prepared/staging/fixture pins、PID 与出生时间、存档 pin、动作身份、ACK 状态、前后实际值、断言、证据路径、退出／cleanup／CAS、各 phase elapsed 和不支持项。运行时数值 ID 及 64 位身份使用规范十进制字符串；definition key、scope 类型和 flag 状态单独分型，缺失不写成 0，跨进程不用内存地址充当持久身份。

| 方案状态 | 判定 |
| --- | --- |
| NOT_RUN | 尚未执行；本文所有实机 cell 的初始状态。 |
| BLOCKED | 前置接入、预算、来源、离线准入或观测通道不满足；不是产品 PASS，也不自动归因产品玩法失败。 |
| FAIL | 实际运行发现违反已冻结断言，如重复收费、错误核心、来源被改写、按钮失效或保存丢失。 |
| UNKNOWN | 操作结果或证据不完整，无法判断；保留实际引用，不自动重发未知创建。 |
| PASS | 该 cell 的操作及独立后态均通过，且所声明边界的公共验证与正常闭场满足。 |

上述是报告显示状态，持久字段遵循公共入口现有合同，不新增互相矛盾的资格字段。`READY_FOR_EXISTING_REVIEWED_LAUNCH`、prepared 的 `NOT_RUN/NOT_ASSESSED` 均不授业务通过；`case_acceptance_pass` 还依赖 case／GUI／normal-close 的实际 qualification，公共 `product_release_pass` 保持 false。单场不授整产品或发布资格。

两模式实机验收收口要求：B/D 正向与各自冷读、A 的真实 GUI／拒绝、E 的代表性跨宗教、F 的状态／旧档控制全部有逐 cell 结果，必需项无 FAIL／UNKNOWN／BLOCKED；不能因为某项难测就移出必需范围。不可达的原生故障注入分支单独列作未覆盖可靠性范围，不用种入状态冒充；对外仅声明已有证据的范围。

失败先提炼最小原生日志、请求／后态和来源 pin；修回共享生产路径，按改变范围做必要回归，冻结后继提交和 attempt，不改写旧失败。仅文档或不相关输入改变不触发全矩阵重跑。source 业务验收与后续缓存验收严格按各自合同执行，本文不重复引入发布门禁。

资产按统一策略分级：正式代码／精简记录 180 天复核；build 与 checkpoint 默认 14 天；原始日志／截图／trace 默认 30 天；巨型派生物优先按 48 小时评估。当前冷读依赖的唯一存档设用途和最长 7 天保护复核，不能到期自动删，也不因历史失败永久保留全量原件。每场正常闭场时记录实际大小、可读性与期限，不复制完整游戏或每个 cell 一份全量存档。

## 8. 本次文档工作包记录

machine_id：`4-8e1c2f1861`；观察时间 `2026-10-24T15:46:27.449188Z`。来源为本轮 `tools/ck3_live_run_id.py machine`、现行公共入口／adapter 源码和受控目录文件读取。任务开始卷总容量 511776722944 bytes、可用 91192225792 bytes；仅新增方案与索引，未做重型写入、容量预留、清理或实机准入，不将这份快照当作后续启动许可。

本轮不运行 Maven／游戏矩阵，不修改产品代码、公共注册或运行时。交付检查仅覆盖文档链接、与当前实现／CLI 合同一致性和 Git diff；全部实机结果保持 NOT_RUN。

闭场容量观察：同机 `2026-10-24T15:56:21.272871Z` 可用 91185774592 bytes；并发卷变化不归因于本任务。三份文档共检查 18 个本地链接，缺失 0；`git diff --check` 通过。新方案为小型 record，按 180 天复核归纳，不新增构建、存档或原始实机资产。
