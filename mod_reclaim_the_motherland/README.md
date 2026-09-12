# 重整河山：设计与实现说明

状态：**0.2.0（二期）已实现并公开发布；L0、源码树 L1 与 Workshop fresh-cache L3 全部 GREEN。** 这份文档同时记录设计约束、当前实现与发布证据；上一公开版本为 0.1.1。

## 1. 产品目标

新增游戏规则“中华霸权统治者的命运”，提供两个选项：

- **重整河山（默认）**：中华霸权进入“群雄割据”时，旧天子失去中华霸权，但保住自己的领地、其他个人头衔和尊王派直属封臣，并以“后＋原朝号”的空法理霸权继续存在。
- **原版群雄割据**：完整执行 CK3 原版行为，方便兼容旧玩法与对照测试。

二期另增游戏规则“尊王诸侯的抉择”：

- **人心离散（默认）**：尊王派直属封臣会按战事、私怨、朋党、好感、性格、实力、合法性与恐惧等事实，在群雄割据的一刻作出一次留守或反叛判定。
- **誓死尊王**：兼容一期行为，所有尊王派直属封臣一律留下。

“重整河山”选项下，后朝持有者不能执行原版“宣称天命”；在群雄割据期间重新控制中华霸权法理领地的过半伯爵领（当前门槛为 51%，符合条件的朝贡国领地也计入）后，方可执行新决议“宣称复辟”。复辟完整执行原版“宣称天命”的效果，最后销毁复辟者持有的后朝霸权。

本 mod 依赖《溥天之下 / All Under Heaven》的天朝与王朝循环内容。首个实现基线为 CK3 `1.19.0.6`。

## 2. 已核对的原版机制

这项修改不能只在原版效果前后补发头衔。原版实际调用链是：

1. `situation_dynastic_cycle_phase_chaos.on_start` 触发 `tgp_dynastic_cycle.0081`。
2. 事件调用 `tgp_chaos_shattering_effect`。
3. 该 effect 先销毁旧天子所有高于王国级的头衔，重组旧封臣，最后执行 `force_step_down_landed_titles = yes`，这一步会让旧天子失去全部领地。

因此，新规则必须在 `tgp_chaos_shattering_effect` 的入口分流，并在自定义分支内跳过“彻底退位”，否则新授予的后朝霸权和保留领地仍会被原版后续逻辑清掉。

其他已确认事实：

- 尊王派的 participant group 是 `pro_hegemon_movement`。
- 进入群雄割据前，原版已经把实际朋党身份冻结到角色变量 `former_movement_member`；实现应读取这份历史事实，而不是重新按好感、性格或亲属关系猜测。
- “宣称天命”的门槛直接引用 `claim_mandate_china_county_percentage_value`，当前值为 `0.51`。
- 控制比例统计 `h_china` 的法理伯爵领；角色自身领地和其朝贡国领地都计入。
- 原决议最终调用 `tgp_claim_mandate_of_heaven_effect`。复辟应继续调用这个原版公共 effect，而不是复制约 400 行实现。
- 原版已经在正式脚本中使用 `create_dynamic_title = { tier = hegemony }`，所以每次崩解创建一个独立的空法理霸权，不需要预留有限数量的静态头衔槽。

## 3. 玩家可见状态机

| 状态/动作 | 原版选项 | “重整河山”选项 |
| --- | --- | --- |
| 进入群雄割据 | 原版彻底裂解 | 创建后朝霸权，旧天子失去 `h_china`，不被强制退位 |
| 旧天子的个人领地与其他头衔 | 按原版失去/销毁 | 保留；只明确销毁 `h_china` |
| 尊王派直属封臣 | 按原版裂解 | 按【人心离散／誓死尊王】决出最终留朝者；留朝者保留原关系、国号和封臣树，叛者按原版裂解 |
| 其他直属封臣 | 按原版裂解 | 先脱离旧天子，再进入原版的朋党领袖、长老、朝贡与弱势头衔处理 |
| “宣称天命” | 正常可用 | 后朝持有者隐藏且硬性禁止；其他军阀不受影响 |
| “宣称复辟” | 不显示 | 后朝持有者在群雄割据且独立、和平、成年并控制至少原版比例时可用 |
| 复辟成功 | 不适用 | 获得 `h_china` 并执行原版全部配套效果，然后销毁自己持有的全部后朝霸权 |
| 别人先取得天命 | 群雄割据结束 | 后朝不自动消失；它作为失国政权继续传承，可在未来一次群雄割据中再谋复辟 |

最后一行是本设计的拟定规则：它避免擅自增加“别人成功就强制销毁你的后朝”这一需求外惩罚，也允许多个历史后朝并存。若希望后朝只在本轮逐鹿中有效，可改成群雄割据结束时自动销毁。

## 4. 后朝霸权的数据模型

每次自定义裂解创建一个新的动态霸权级头衔，并保存为当前 effect scope。该头衔：

- 不设置任何法理子头衔，因此法理为空；收复进度仍始终对 `h_china` 的法理领地计数。
- 写入 title variable `rmtm_restoration_hegemony = yes`，作为决议资格、原决议禁用和复辟销毁的唯一耐久标记。
- 复制当时 `h_china` 的纹章、颜色，以旧天子的首都作为显示位置。
- 设置 `no_automatic_claims`、禁止自动按宗族或游牧规则改名，并在被销毁时删除动态 title object。
- 不设置“获得同级头衔时自动销毁”，因为销毁必须由“宣称复辟”的显式额外效果完成。
- 授予旧天子并设为主头衔；继承资格跟随头衔，而不绑定最初角色。旧天子死亡后，合法继承人继续承担复辟路线。

若一个角色通过继承等方式同时持有多个带标记的后朝霸权，执行一次复辟会销毁他持有的全部此类头衔。否则遗留的第二个后朝头衔会继续错误地封锁“宣称天命”。

### 4.1 “后唐/后宋”名称冻结

`h_china` 的“唐”“宋”等不是不同 title key，而是运行时的头衔名；玩家还可以自定义朝号。不能用一张“汉/唐/宋”枚举表，也不能让新头衔长期引用活的 `h_china` 名称，否则别人建立新朝后“后唐”可能漂移成“后宋”。

当前实现采用以下顺序：

1. 创建动态霸权，暂用兜底名称。
2. 对原版 89 个标准朝号逐一使用 `is_title_localization_key_used` 判断；匹配时把动态头衔名设置成生成的组合 key，例如 `$rmtm_restoration_title_prefix$$dynn_title_song$`，由当前语言直接渲染“后宋”“Later Song”等名称。
3. 若玩家使用了枚举外的自定义朝号，则用 `move_title_name_to` 无损转移原文字，并使用引擎原生 title prefix 表达“后/Later”。
4. 名称冻结发生在授予动态头衔并处理完 title-gain on-action 之后、销毁 `h_china` 之前；随后重置旧 `h_china` 的运行时名称。

这避免了 `set_title_prefix` 不会改写 `GetNameNoTierNoTooltip` 所暴露的标准朝号缺前缀问题，同时保持任意玩家自定义朝号不丢失。89 个组合 key 由 `tools/gen_reclaim_the_motherland_title_names.py` 向九种发布语言确定性生成，禁止手改生成文件。

## 5. 尊王诸侯的二期判定

候选人仍按**裂解瞬间的直属、有地、伯爵级以上尊王派封臣**定义，避免把一个间接封臣跨越其合法领主强行抽到旧天子直属层级。每名候选人只在这一轮群雄割据中结算一次，结果先冻结，再开始任何头衔或封臣关系变更。

1. 在销毁 `h_china` 前保存旧天子和全部旧 realm participants。
2. 若选择“誓死尊王”，候选人全部留守；若选择“人心离散”，先判定公开决裂与不可动摇的羁绊。正在与旧天子交战、宿敌/仇敌、家族世仇、不忠、好感不高于 -75，或已参加针对旧天子的独立/宣称者派系者必叛；至交/灵魂伴侣、具备足够好感的原尊王派领袖、忠诚且同宗且非负好感者，以及旧天子握有强牵制且好感不低于 -25 者必留。公开决裂优先于羁绊。
3. 其余候选人从 65 的基础留守概率出发。好感、朋友/情人、师徒、忠诚、安于现状会提高概率；野心、强力封臣身份、较高头衔、相对军力会降低概率；旧天子的合法性和对候选人的威慑也会影响结果。最终概率限制在 5%–95%，AI 只掷一次并保存结果。
4. 群雄割据 effect 无法同步等待多名联机玩家逐个确认。非 AI 候选人使用同一套冻结输入，但以 50 分为公开确定性分界，不替玩家暗掷随机数。这是 0.2.0 已知的联机交互边界。
5. 最终留下的忠臣保持原来的直属关系、完整下级封臣树、主头衔对象、title key、显示名称与玩家自定义名称；他们被明确排除在原版弱势 AI 王国/帝国头衔裁剪和改国号入口之外，不调用 `reset_title_name`。
6. 最终反叛者与原本就不属尊王派的直属封臣脱离旧天子，再继续进入原版的弱势头衔处理、征服者判定、朋党领袖/长老重组、朝贡关系、无地家族首领安置和逐鹿天命 story。男爵等结构性封臣跟随其合法伯爵领主，不单独抽离。
7. 在原版“重新归属”循环中排除仍以旧天子为 top liege 的角色，避免忠臣 realm 被转给其他长老，也避免忠臣领袖把已脱离者重新拉回旧天子的 realm。

这套判定保留了“加入尊王派”作为重要政治承诺，但不再把所有成员视作永不动摇；同时，留下的忠臣不会因原版割据重组从“青徐路”等既有国号跳成无关的新国号。

## 6. 两个决议

### 6.1 原版“宣称天命”覆写

保留原 decision key `situation_dynastic_cycle_claim_mandate_decision` 和原版全部条件、AI 参数及效果，仅在“重整河山”规则启用时增加双重保护：

- `is_shown`：持有任一 `rmtm_restoration_hegemony` 头衔时不显示。
- `is_valid`：重复同一否定条件，防止 AI、控制台或其他脚本绕过显示层直接执行。

没有后朝头衔的其他军阀完全按原版宣称天命。

### 6.2 新“宣称复辟”

新 key 为 `rmtm_claim_restoration_decision`，沿用原版 dynastic-cycle decision group、插画、和平/成年条件、冷却、AI 检查周期和权重。资格差异只有：

- 必须启用“重整河山”规则；
- 必须持有至少一个带 `rmtm_restoration_hegemony` 标记的头衔；
- 必须处于群雄割据且是独立统治者；
- 直接引用原版 `claim_mandate_china_county_percentage_value` 及其 `h_china.any_de_jure_county` 统计表达式，不另写 `0.51`。

效果顺序如下：

```text
冻结复辟者当前持有的全部后朝头衔 scope
复制原“宣称天命”的三日 flag
复制原 Greatest of Khans story/government 收尾
保存 dynastic-cycle situation scope
调用原版 tgp_claim_mandate_of_heaven_effect
销毁先前冻结且仍存在的全部后朝头衔
结束仍残留的后朝相关 story（如有）
```

这在行为上就是“原版宣称天命的完整效果＋销毁你的后朝霸权”，同时避免以后原版修复了内部效果而本 mod 仍运行旧的 400 行副本。

## 7. 入口覆写与兼容策略

计划只覆写两个原版 key：

1. `tgp_chaos_shattering_effect`：按游戏规则分派到自定义裂解或一份固定的原版兼容副本。
2. `situation_dynastic_cycle_claim_mandate_decision`：给后朝持有者增加禁用条件。

不覆写 `tgp_dynastic_cycle.0081` 事件、不替换整个 dynastic-cycle situation，也不复制 `tgp_claim_mandate_of_heaven_effect`。这能把与其他 mod 的冲突面压到必要的两个 key。

代价是：任何同样覆写上述两个 key 的 mod 都存在加载顺序冲突。descriptor/Workshop 页面必须明确列出这一点。兼容副本会绑定下面的原版文件 SHA-256；升级 CK3 后只要 hash 变化，静态校验就要求人工审阅上游差异，不能悄悄继续使用旧逻辑。

原版 `tgp_dynastic_cycle.0081/.0082` 的 tooltip 会继续沿用原版文字；本 mod 不覆盖原版本地化 key，避免加载时产生重复 key。玩家应以游戏规则说明、动态后朝头衔与新决议的实际结果为准。

## 8. 实际文件布局

```text
mod_reclaim_the_motherland/
  README.md                                      # 设计与实现说明，source-only
  descriptor.mod                                # 不含 remote_file_id
  common/game_rules/rmtm_game_rules.txt
  common/decisions/rmtm_restoration_decisions.txt
  common/decisions/dlc_decisions/tgp/zz_rmtm_mandate_override.txt
  common/scripted_effects/rmtm_dynastic_cycle_effects.txt
  common/scripted_effects/rmtm_loyalty_resolution_effects.txt
  common/scripted_effects/rmtm_generated_title_name_effects.txt
  common/scripted_effects/rmtm_vanilla_compat_effects.txt
  common/scripted_effects/zz_rmtm_vanilla_overrides.txt
  common/script_values/rmtm_loyalty_values.txt
  common/scripted_triggers/rmtm_loyalty_triggers.txt
  common/scripted_triggers/rmtm_restoration_triggers.txt
  events/rmtm_loyalty_events.txt
  localization/<九种语言>/rmtm_l_<语言>.yml
  localization/<九种语言>/rmtm_generated_title_names_l_<语言>.yml
```

统一命名空间为 `rmtm`。发布构建使用 `tools/build_reclaim_the_motherland_release.py` 的独立 exact allowlist：32 个运行时文件进入 staging，README 不发布。Workshop item ID 为 `3798404599`；`remote_file_id` 只存在于用户目录外层 launcher descriptor 与 ID-bearing 发布记录，绝不进入仓库内 `descriptor.mod`。

## 9. 实现与验收顺序

### 阶段 A：最小机制探针

- 按项目规则先检查 `open_kaishek` 是否能覆盖所用 parser/IR 子集，并记录其 commit、profile、CK3 build/EXE hash、fixture hash、命令和不支持项。
- 验证动态 `hegemony` 创建、空法理、授予、设为主头衔、存档重载和销毁。
- 验证实际朝号转移与中英文“后/Later”前缀，包括玩家自定义朝号。
- 验证动态霸权的继承人始终与主领地继承人一致；若引擎会把它分给别支，先解决继承合同再继续。

### 阶段 B：裂解与决议

- 实现游戏规则 dispatcher 和原版分支逐字语义对照。
- 构造至少三类直属封臣：尊王派、非尊王派、尊王派下属的间接非尊王派，验证最终 liege 树。
- 证明旧天子失去 `h_china` 但仍持有后朝、原个人领地与其他个人头衔。
- 证明后朝持有者无法执行“宣称天命”，其他军阀仍可执行。
- 在 50% 与 51% 两个边界验证“宣称复辟”，并验证朝贡国计数与原版一致。
- 验证复辟获得的政体、首都、合法性/奖励、封臣归附、官职与 situation catalyst 和原版宣称天命一致，且只额外销毁复辟者自己的后朝头衔。

### 阶段 C：生命周期和回归

- 旧天子死亡后由继承人复辟。
- 另一军阀先取天命后，后朝跨稳定期及存档重载继续存在；下一轮群雄割据仍能复辟。
- 多个后朝并存、单角色持有多个后朝、后朝持有者失去全部土地等边界。
- 规则设为“原版群雄割据”时，与原版角色头衔、封臣关系和 story 结果对照一致。
- 独立加载、与仓库其他 mod 的两种加载顺序、错误日志及本地化占位符检查。

正式完成标准不是“脚本能解析”，而是保存一份真实 CK3 `1.19.0.6` 的群雄割据→保留后朝→达到 51%→宣称复辟的完整实机 artifact。日常开发只写中英文本；只有收到明确发布指令后才做七语、release staging、Workshop 上传、订阅缓存复核和永久 changelog。

## 10. 原版基线锁定

本设计核对日期为 2026-09-08。CK3 executable SHA-256：

`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`

| 原版文件 | SHA-256 |
| --- | --- |
| `common/decisions/dlc_decisions/tgp/tgp_dynastic_cycle_decisions.txt` | `FFC1CE8BC35DDCAFA29956E4DC4159EB295E10E17FD0881CE5DD558671206651` |
| `common/script_values/10_tgp_dynastic_cycle_values.txt` | `D91DCDBF7038FAE3D8D71B9C4156B2B23744DE6F718A34DA26D1656BC48B7706` |
| `common/scripted_effects/10_dlc_tgp_dynastic_cycle_scripted_effects.txt` | `86574FB7CE246EF6D1B2741B211785D282AD39659E8771E0E5C714ACDC001782` |
| `common/situation/situations/tgp_dynastic_cycle.txt` | `748F2AF8CBDF97E01182FEFADF0B975E62AECE57D09AB1515C02E112DB56FAEA` |
| `events/dlc/tgp/tgp_dynastic_cycle_events.txt` | `C9904AAA01ABC8583E67D07866FAE8EF89274708BDA3929498DDDB2F24FC2153` |
| `common/landed_titles/02_china.txt` | `342F67E4D3E27A66B05A7257493A28C32AD8C0F9D9B314C0E18BDD8261165811` |

## 11. 已确认的四个设计口径

实现已经按以下四点执行：

1. 新规则默认选择“重整河山”，同时保留一个完全原版的选项。
2. 旧天子除 `h_china` 外保留所有个人领地与个人头衔；不继续执行原版的全头衔退位。
3. “尊王派封臣”按直属封臣判断，并完整保留这些直属封臣原有的下级 realm 树，不跨级抽取间接尊王派。
4. 别人先取得天命时不销毁后朝；后朝可跨王朝周期传承，并在未来群雄割据中复辟。

## 12. 当前实现与验证证据

2026-09-13 的二期实现状态为 **complete / production-live**：新增【尊王诸侯的抉择】规则、三段式一次性忠诚结算、留朝忠臣国号与封臣树保护、【人心向背】总结事件、九语发布本地化和 32 文件独立构建链均已落地并发布；一期的动态后朝、原“宣称天命”封锁与“宣称复辟”全链保持不变。原版兼容副本继续绑定 CK3 `1.19.0.6` 的源文件哈希。

`open_kaishek` 预验记录：

- commit：`890b32de49081b7b5510e40c5518dfb59d5c8a6d`；CLI contract：`b306a95`；JAR SHA-256：`7262e771ad3e1f5d724d663ac259a20e2a7df0c491d4c125f56cb4c3a604e75c`。
- profile/version：`ck3-1.19.0.6` parser-only root scan。当前 validator 不覆盖本 mod 的动态头衔、封臣重组和决议语义，UNKNOWN 诚实记录为 `not-applicable / cli-red`，不替代 CK3 实机。
- CK3 EXE SHA-256：`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- 产品 corpus：12 文件、50,804 bytes，root SHA-256 `d8f6001c810261521ecbd744cd121e8930dfdf9cc8dea8bb4ae2174ff0f04ee1`；parser GREEN。
- 外置验收夹具 corpus：8 文件、20,308 bytes，root SHA-256 `18e7ae11e6cec6e71df789f4766c3dd3349ec873f1b4c08f54eb114a023a0694`；parser GREEN。

最终静态验证：

- `py tools/test_reclaim_the_motherland_contract.py`：13/13 GREEN；另有 1 项因 detached worktree 不含被忽略的游戏副本而显式 skip。
- `py tools/validate_reclaim_the_motherland_static.py`：GREEN；32 个运行时文件、9 种发布语言、每种 112 个本地化键、12 个玩法脚本。
- `py tools/test_build_reclaim_the_motherland_release.py`：10/10 GREEN。
- `py tools/build_reclaim_the_motherland_release.py --check`：双构建可复现；开发快照 manifest SHA-256 `b3cdaa33f4ad1dc8a707e807533da339e1002533be2e582b67e4abd51c048712`，ZIP SHA-256 `5981535815e61dd92c5f681a2fea9f9804cd58ffb545f5fe6f1310d9af6c8550`。正式 tag 构建会因 manifest 内嵌 Git SHA 而取得自己的正式哈希。

源码树 L1 实机 run 为 `D:\workspace\ck3_reclaim_phase2_20260913_process_assets\reclaim\runs\desktop-3fevhd2-1c74096080--reclaim-the-motherland--R0004-source`，wrapper `report.json` SHA-256 为 `962c679a10ae669201eff32cb62f2cb442ab5189cffd0037ee9af4f03071f85a`，有效 `cell/report.json` SHA-256 为 `53ed9ecf85166c4f3e0335777c641b64f5043ffe7b7ec0fe56db1fd6b9bb83e9`。它通过 MCP readiness 和语义化事件选择完成 20 个顺序标记：必留忠臣原样保住【青徐路】头衔、名称与封臣树，必叛尊王诸侯脱离，一次性结果与【人心向背】总结可见；一期的后宋、空法理、个人领地、50%/51% 边界、复辟可见而天命不可见，以及完整原版天命效果＋后朝销毁也全部回归。运行中 source/runtime 未改写，项目 diagnostics 为 0，保护存储未变化，原生进程树和隔离 userdir 均完成清理。

完整 L0/L1/L3 证据和保留的 RED attempt 说明见 `docs/acceptance-report.md`，九语发布审阅见 `../docs/reclaim-release-localization-review-2026-09-13.md`。0.2.0 使用四张来自最终 GREEN run 的真实游戏截图，其中【人心向背】为首图，地图镜头由原生 MCP 定位到大宋首都开封。Workshop item `3798404599` 已公开更新：描述与入库 BBCode 精确一致，Change Notes 的 508 字/14 行全文已匿名精确回读，全新 32 文件订阅缓存严格核对并完成同矩阵 MCP-first L3。
