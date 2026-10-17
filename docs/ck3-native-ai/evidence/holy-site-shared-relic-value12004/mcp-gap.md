# 共享圣地、逐 faith 认可与非空换物：MCP 缺口及最小只读增量

现有 MCP 已能回答“一个圣地关联哪些 faith、各自普通还是主要、共用哪些槽位”；尚不能在同一 owner capture 中回答“每件已供圣物和待换入候选分别被全部关联 faith 如何认可”。建议补一个有上限的原生认可矩阵查询，然后安排一次合法非空槽位替换补测。本轮仅提出设计，没有实现、构建、部署或取得新实机资格。

machine_id: `4-8e1c2f1861`；研究 UTC：2026-10-17T18:21:09.093663+00:00；当前读取的仓库 352ed2552fba0b0557dd61df09282cda82daa820：`352ed2552fba0b0557dd61df09282cda82daa820`。本次重新执行机器身份工具；R7/R8 事实来自同机器既有小回执，原观察 UTC、原包 SHA、机器绑定投影与当前源码 SHA 均在 [capability-evidence.json](mcp-gap.evidence.json)。没有读取大型 wire，也没有访问 CK3/Steam/屏幕或改动 a05/a06。

## 已有能力与准确边界

| 工具及参数 | 可用于规划的字段 | 不能推出 |
|---|---|---|
| `ck3_query_player_holy_site_v1(expected_revision, holy_site_id=None)` | `selected_holy_site.associated_faiths[]` 各行 `faith_id/available/faith_lists_site/eminent`；当前 faith 名单、嵌入库存 owner 与物品 ID | 世界 registry 不是可采用候选；站点成员/主要等级不是认可或收益 |
| `ck3_query_player_holy_site_relic_context_v1(expected_revision, holy_site_id)` | 完整 `associated_faith_ids`；共享 `inventory.slots/artifact_ids/artifact_objects`；玩家与县主 faith 的 `recognition_*`；缓存和当前原版 rarity producer | 没有任意 `faith_id` 参数；未入站的换入候选也不由此逐物求值；无法组成全部关联 faith 矩阵 |
| `ck3_query_player_holy_site_relic_permissions_v1(expected_revision, holy_site_id, artifact_id=None)` | 玩家库存、当前候选、站点槽位、指定物 permission 与当前按钮 | `can_enshrine=true` 不等于全部 faith 认可、已选中、已行动 |
| `ck3_query_player_holy_site_relic_action_context_v1(expected_revision, holy_site_id, artifact_id)` | 实际 owner、effective slot、`replacing_artifact_id/replacing_artifact`、三份原生文本和冻结 preview SHA | 返回替换目标不等于替换发生；ACK 不等于所有权、收益已经生效 |

等级必须存为 `(faith_id, holy_site_id)` 边。R7 降麦加/升纳杰夫后，site32 的 Faith50 与 Faith51 均为主要；R8 从原 C2 的另一分支弃用32，只移除 Faith50 关系，Faith51 主要关系和站点世界对象仍在。两场不是同一条连续状态。

库存/槽位属于 HolySite 对象，不能为每个 faith 另造一份槽位。认可属于 `(artifact_id, faith_id)`；个人装备收益与最终受益者又是别的观察域。把这三个键分开，可避免“我换掉自己 faith 的圣物，对其他 faith 没影响”的错误假设。

R7 的站点32在 `[51,50]` 关联名单不变时，实际槽0为 `null→237→null`，当前原版 rarity 与缓存均为 `0→4→0`，Active `false→true→false`。神器237动态圣化列表为空，而原生对 Faith50 的认可为 true；不能按空列表或物品名称判 false。该场玩家和县主均为 Faith50，两个 recognition 字段重复观察同一个 faith，**没有读取 Faith51 对237的认可**。

R7 供奉前 effective slot0 的 replacing=null；撤回也是单独有成本动作。R8 Create 将237装到新站点326，关联名单仅 `[50]`。这两场都没有“从非空槽位 O 换成 N”的实机证明，也没有取得跨 faith 价值变化后验。

## 建议的同 owner 只读矩阵

新工具建议为 `ck3_query_holy_site_relic_faith_recognition_matrix_v1(expected_revision, holy_site_id, candidate_artifact_ids=[])`。`holy_site_id` 和每个 artifact ID 都是完整 uint32，`0` 有效，`0xFFFFFFFF` 禁用，禁止 bool 冒充 int。候选最多4件、无重复；空列表只查当前全部非空槽位物品。

scope 为“当前非空槽位中的物品去重后并入显式候选” × “该圣地全部关联 faith”。每行保留物品对应的所有槽位下标；原始 faith 顺序和槽位内容仍完整保存。不能把去重矩阵拿去重写原版 current-rarity producer，后者自有逐槽求值语义。

固定上限：64个关联 faith、64个槽位、4个显式候选、8件不同物品、256次原生 predicate。任一源范围或乘积超过上限，**在 getter 前整体拒绝**，记录真实数量、超限项，`available=false/matrix_complete=false/cells=null`；不返回一小段后冒称全部关联 faith。容量够时枚举全部计划格，即使某格 getter 失败也保留该格的 unknown。

响应 schema 建议 `ck3_12004_holy_site_relic_faith_recognition_matrix_v1`；step `query-holy-site-relic-faith-recognition-matrix-v1`，domain `holy_site_relic_faith_recognition_matrix_v1`，result key `holy_site_relic_faith_recognition_matrix`。独立默认关闭开关 `--private-holy-site-relic-faith-recognition-query`，Driver 属性 `allow_private_holy_site_relic_faith_recognition_query`；server 和 managed host 须完整转发，不混入动作 opt-in。

核心字段为 `capture_epoch/date_raw/played_character_id/requested_holy_site_id/requested_candidate_artifact_ids`、完整 `associated_faith_ids/slots/artifact_ids`、`scope_complete/matrix_complete`、`cells[{artifact_id,faith_id,available,value,unavailable_reason}]`。每格 `available=true` 才表示已知 true/false；失败时 value=null。稳定 capture 可 `available=true` 而 `matrix_complete=false`；全局身份/源数组漂移则整矩阵无效、cells=null。`action_ready/business_outcome_observed/beneficiaries_observed` 固定 false，beneficiaries=null，不产出 `ActiveForFaith` 或收益金额。

复用已有 1.20.0.4 原版 getter `0x2530EF0`，ABI 为 `bool(artifact*, uint32 faith_full_id, tooltip_or_null)`，第三参 null。其完整代码 SHA 为 `f4c88f9285220a2deaea89f88696e327f6a19657704fa3d261f4b29cd90995d4`。它结合动态圣化集合与模板 compiled trigger，不能在 Python 只扫描集合来模拟。现有代码已按玩家/县主 faith 调用这个函数；任意显式 faith 运输与批量守卫仍属于新施工，不能追认已通过。

全部调用进入既有暂停的 religion owner callback。一批开始与结束核对 site storage/fullID、完整关联 faith 列表、槽位表头与各项内容、每个 artifact/faith storage/fullID，以及 artifact rarity、owner、模板/trigger 绑定和动态圣化集合；actor/rite/faith/date/build/generation 也须一致。同一 capture 顺序求值减少 N 次独立查询的穿插，但**不是同时求值**；冻结上述字段也不能证明任意更深脚本或 RNG 状态未变。响应明确 `evaluation_atomic=false/script_rng_effects_verified=false/script_rng_effects="unknown"`，MCP `readOnlyHint=true/idempotentHint=false`。

新代码须冻结 exact EXE、加载中的 getter/注册 callback/resolver 与新增 reader body、实际游戏/mod 来源清单；缺失或 SHA 不符时原生入口 fail closed。保留原版触发器执行，不主动刷新世界缓存。现有基础 relic-context 只有 exact-EXE 绑定与相关历史源码包；不能把新增 `loaded_source_pins_verified` 的建议写成旧字段已存在。全局 current rarity/Active 继续独立调用现有站点域，不从矩阵自行求一个“每 faith Active”。

可另外做最窄 pair primitive `ck3_query_artifact_faith_recognition_v1(expected_revision, artifact_id, faith_id)`，用于诊断；它不含虚构的 site 参数，因为 native predicate 自身只接 artifact/faith。连续 N 次 pair 调用不能假装是同帧原子矩阵；一期正式对比优先矩阵。

## 最小两 faith、非空换物补测

| 阶段 | 最少采集/动作 | 能授予的结论 |
|---|---|---|
| 准备 | 新鲜合法实验分支，同一完整 site S 至少关联 A/B，槽k有旧物O，另有实际合法候选N；两物不同 | 只是准备。R7/R8历史 ID不能直接当当前资格；若没有合格N，记录缺口，不造可行性 |
| 替换前 | 一批全关联矩阵，重点检查 O/A、O/B、N/A、N/B 四格；另读关联/等级、全槽位、两物owner/库存与原版当前 rarity | 各格 known true/false 与完整前态。至少存在一处 O/N 认可差异才足以讲跨faith取舍；完全相同只证明机械替换 |
| 单次替换 | 选择N、明确槽k；fresh action-context 必须给 effective=k、replacing=O；绑定新 preview，`relic_expected_replacing_empty=false/expected_replacing_artifact_id=O`，按原生条件只提交一次 | ACK只记 attempted/pending；不能宣布O去向或净收益 |
| 独立后验 | 重新读全关联矩阵、站点槽位、两物owner/玩家与site库存、其他槽位、关联等级、current/cache rarity；四格认可也重读，因on_action可能改认可来源 | 明确 k:O→N、旧物实际去向及其他共享字段变化；不假定旧物回玩家。全局Active/rarity与逐faith认可分别报告 |
| 未知/差异 | native attempted 后未能核清，保留pending并独立查询；不用第二次点击解决 | 未知不是未行动；不能改 revision 绕过重复守卫 |

新 reader 资格只运行本次必要新包：两faith混合true/false；空动态列表但模板true；单格getter失败/null；faith/artifact代际失效；source-pin拒绝；批内faith/slot/owner漂移；cap拒绝且getter调用0。完整新 C++ serializer 原包再走实际 Driver→Service→MCP，不手造正例、不重跑旧矩阵。此表均为待执行计划，本研究没有运行这些格。

对智能体，候选换物应比较“每个受影响 faith 的旧认可→新认可”以及独立观察的共享槽、原版current rarity和物品归属成本。若有任何关键格 unknown，保留未定估值；即使全部认可已知，也不能把认可布尔直接当最终修正收益。最终 modifier/beneficiary 读口由 runtimeagent 独立研究，本提案不重复或预授其资格。

## 实现补注：复用既有两个工具

`machine_id: 4-8e1c2f1861`；2026-10-17追加的实施选择。上文是18:21保存的独立新工具／独立opt-in提案，保留其原身份；Root后来选定复用既有context与action-context，**没有把该提案tool或flag注册成公共入口**。本补注随a03原生源码合入应用，不改原提案或冻结的JSON。

实际工具签名仍为`ck3_query_player_holy_site_relic_context_v1(expected_revision, holy_site_id)`及`ck3_query_player_holy_site_relic_action_context_v1(expected_revision, holy_site_id, artifact_id)`；前者附可选`recognition_matrix`和`modifier_aggregate_observation`，后者只附矩阵。没有新增参数、tool、macro、flag、private opt-in或动作权限；permissions工具不改。正常公共owner路径扩展，旧四参数reader默认owner=null时不加字段或native调用，旧包缺字段仍兼容，preview canonical/hash不变。

矩阵改取关联＋玩家／县主Faith，以及实际槽物品＋窗口candidate cache＋action请求物，保留原来源顺序／重复后另列去重。各维上限64、最多256次新增predicate；原提案的显式候选4件／去重8件等数字不再作为这个实施版本的运输合同。未知cell保留null，漂移整矩阵未知；无per-Faith Active、收益推算或原子性承诺。

固定PC观察仅两个当前type固定块及当前玩家／派生县主的实际总聚合。u16键与定义Q64值沿当前PC读取，不猜属性名称；聚合值不是单圣地贡献，scaled和county净值未覆盖，默认cache不当零。完整限制及a03候选SHA见[主专题实施补注](../../holy-site-shared-relic-value12004.md#实现补注复用既有两个工具)与[实际观察专题](../../holy-site-effect-observation-12004.md)。本轮只有文档审阅，没有新build、测试、原生包消费或实机信用。
