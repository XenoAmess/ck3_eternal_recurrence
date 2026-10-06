# CK3 1.20.0.3：phase 候选角色 Rite 参数的最小只读施工包

2026-10-06，初始 source-only 包于 **09:19:55 Asia/Shanghai** 完成，状态为 research / 原生来源 static-confirmed。随后获准实施最小叶子，当前为 **Python contract/adapter offline-ready；native candidate 已写、待中央首次编译/新 CTest/实际 wire资格**；没有新 live 能力。冻结游戏为 CK3 1.20.0.3 Crozier / Steam build 25652598，EXE SHA-256 `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`。原生 source 基线 `57e8386d249723839bbb9dec532d352db07b46c9`，source-only 本地 commit `3cd63d3505f2f97d22f8ae02540d91a6707e0f6f`；后续实现仍复用同一来源，无新 EXE 读取、native build/test或游戏操作。

本机用户当前只允许后台工作；没有启动、连接或查询 CK3。本专题不恢复旧宗教或非战限制，也不改变执行授权。当前 bounded V2 planner 仍可独立推进；本包针对更完整 forecast 的真实缺输入。

## 已有链与当前缺口

source 基线的 [ReadCombatPhaseInputs](../../ck3_autonomous_player/native_bridge/src/ck3_12002_phase.cpp) 先读非宗教 operands，再无条件写 `available=false`，返回 `phase_inputs_unavailable`。非宗教读取成功时 reason 为 `phase_religion_and_rites_implementation_pending`。当时候选角色循环已解析同一 Character 的 traits、culture、misc、MAA 输入，但没有填角色 Faith/Religion、Rite 参数、Tenet 与敌方参与者 Faith hostility。旧 DTO 的三个默认 false 字段不能证明这些值被读过；下节的新叶子只补其中已闭合的参数来源。

现有 V2 `contextual_advantage` 已有独立的构造阶段宗教输入，包括选中 commander 的 adopted Rite hostility；[构造阶段 Faith/Rite 专题](combat-constructor-faith-rite-context-12003.md) 已闭合来源。它不覆盖 phase 的所有 commander/knight root，也不证明 phase 脚本中的 `Faith` hostility。不得为本任务重新研究它，或把它当成 phase 已完成。

`.3` 的 [当前 phase 源树](combat-phase-events-12003.md) 已封存调度与选择调用链；[当前人物 effects 投影](battle-phase-leaf-effect-fidelity-12003-2026-10-05.md) 已支持十三行 selected-event authored requests。当前 manifest 和旧 V3 producer 的 current-build AST/provenance 接线仍是不同层，十三行 effects 覆盖不自动填补输入、实际 loaded overrides、调度顺序或 callbacks。

## 原生输入树

实线为已封存 source 合同；虚线保留尚未闭合或未实读的分支。这里只声明图内列出的边。

```mermaid
flowchart TD
    M["2AD7F00：同一局部 seed；side0 → side1"] --> S["264D480：CharacterID + dayIndex 对 loaded interval 取模"]
    S --> C["3298EE0：Character root / named kind11 CombatSide"]
    L["5D27B90 loaded rows；5D4BD6C side token；5C69B4C interval"] -. "actual frame 未读" .-> C
    C --> V["按 source order：role → trigger → chance"]
    V --> W["3FAAB70：Q100000 trunc0 → signed weight → local draw"]
    W --> F["264E680：重新解析 Regiment/Character；effect+160"]
    F -. "外层日期顺序 / 同日 callbacks 未实读" .-> NEXT["下一战斗输入"]
    C --> P["同一候选 Character +B4 full adopted RiteID"]
    P --> R["28D2F90：GetRite；对象+8完整 ref"]
    R --> B["Rite+7B8 complete Boolean tokens；data+0/count+C/stride4"]
    B --> K["B9DE80 membership；3F4F900 stable key"]
    K --> D["root.rite.parameters.death_is_glory"]
    D --> SIX["commander/knight wounded、maimed、killed 六行 chance"]
    R --> FI["24FC560：Rite+4B8 source Faith identity"]
    FI -. "不能替代 adopted Rite 参数" .-> MAIN["Faith+98 main Rite"]
    R -. "rite_has_tenet trigger equivalence 未在本包闭合" .-> T["warmonger validity"]
    C -. "真实 enemy Side participant census 未闭合" .-> H["enemy participant Faith → root Faith；243E950 offset=false"]
```

当前 schedule/function RVAs、event 布局与 effects `+160` 来自旧封存 `.3` native-schedule 包，不是新 EXE 检索。stock 五日 interval 不能代替 `0x5C69B4C` 的 actual loaded DWORD。

## 最小工作包与实际收益

优先实施 **phase candidate adopted Rite complete Boolean parameters**。它用已存在的 native getters 与参数 copier，覆盖六个常见伤害/死亡行的 `root.rite.parameters.death_is_glory`；当前 stock 对该条件依 source order 乘 `1.1`，保持每步 Q100000 向零截断。它还提供 `knight_killed` 已选敌骑士的 `killing_bestows_heads` 与 `decapitation_steals_prestige_as_piety` 所需同源布尔参数，后者仍有 personal Tenet、人物资源及其他独立 dependencies。

选择这一包的必要性是确定的生产缺字段与六行 source consumer；无需闭合全部世界宗教、再次扫描 EXE、调用脚本 executor 或发明未来宗教状态。单独完成该包只解除相应 operand 的缺失；完整 V3、事件概率、native schedule、post-effect final stats 与未来 forecast readiness 仍按各自实际输入判断。

| 输入/入口 | 已有 exact `.3` 来源与最小读取 |
| --- | --- |
| 候选身份 | existing combat 的 commander / knight `character_id`；保留 source Army、source Regiment、role occurrence，不以相同 CharacterID 合并 provenance |
| adopted Rite | `Character+0xB4` full DWORD；`Character.GetRite 0x28D2F90`；raw ref 与返回对象 `+8` 对应，保留 full generation |
| source Faith | `Rite+0x4B8` full ref；`Rite.GetFaith 0x24FC560`，需要时复用 `Character.GetFaith 0x289E750`；不读取额外 fervor 等无消费者资源 |
| complete effective Boolean set | `Rite+0x7B8` 的 data `+0`、signed count `+0xC`、signed token stride4；`0xB9DE80` membership 与 `0x3F4F900` token stable-key copier |
| false / absent / unavailable | 同一 complete 集合中无 key 为 false；已确认 raw `0xFFFFFFFF` 为 adopted-Rite absent；合法 ref `0` 保留。缺 pointer、key 或不完整集合为 unavailable，不能写 false |

上述 `.3` 复用边界见 [当前宗教身份专题](religion-native-ai-faith-identity-12003.md) 的 getter/source/live 账本。既有 reader 仅接受实际 played actor；本包必须在已有 combat 查询中重用其内部已闭合的 Rite copy 逻辑，不能对 phase root 调玩家专用 query 或拼接独立 MCP epoch。它是新 candidate provider，不能继承玩家 getter 的 live 资格。

## 最短实施路线与 consumer

1. 增加一个独立 candidate Rite source helper 与专属 DTO/serializer 子块，消费已有 combat query 内已解析的 Character。复用 `religion_doctrine12002_tenet.cpp` 的 `ReadRite` 逻辑；它目前是 private helper，所以需小幅抽出 copier或局部复用，不能直接调用 `ReadPlayedTenetParameters12002` 换 root。
2. 首选在已有 **V2 combat query** 的 commander、knight 观察行各加 optional `phase_rite_parameters_v1`。该行的身份与 Army/Regiment provenance 已存在；叶子保留 `status`、`source_character_id`、raw adopted Rite ref、resolved `rite_id` / `faith_id`、`boolean_parameters_complete`、完整 stable keys、独立 reason。V3 candidate loop 可以复用同一 helper，并按其 native source-proof occurrence join 取值；V2 roster leaf自身不声称原生 candidate admission/order。
3. 现有 `combat_contract.py` 严格 normalizer 消费 optional 叶子；source-shaped adapter 将 complete 已观测集合映射到当前 manifest 的 `root.rite.parameters.*`。adapter 需按 actor/source occurrence 选叶子，不复用 Faith main Rite、不默认缺失 false，也不输出 native event selection。后续 `selected_enemy_knight` 使用同一角色叶子；当前已支持 effects 仍遵守其其余 dependencies。
4. 一个新必要 offline fixture 覆盖同源 complete true、已观测无 key、adopted/main 不同、合法 ref0、真实 unavailable，并让实际 C++ serializer wire 经生产 normalizer/adapter 消费。这里只列下一包的验收条件，本轮没有运行 fixture、编译或修改这些文件。

把 optional 输入放在当前可用 V2 查询，避免只补一个无法通过 advertisement 访问的 V3 私有诊断字段。完整 `ReadCombatPhaseInputs.available` 仍不因该单叶完成而变 true。当前旧 V3 diagnostic serializer 的 pending/AST 标记只能在各依赖真实接通后更新；不用新增权限门禁替代缺字段。

## 明确剩余依赖与实际帧请求

`knight_become_berserker` 的 validity 用 `root.rite.tenets.warmonger`、`root.religion.germanic`。已有 `24F88A0` 是五档 effective Tenet status，已有 Rite `+758` 是 Core collection；本包未获得 `rite_has_tenet` 的实际 predicate 合同，不能猜成 status 大于零/等于4或把个人 Tenet 当 Rite Core。下一源入口是已登记 `rite_has_tenet` trigger 的 Evaluate→actual predicate、同一 `.3` loaded Tenet definition 的 `tenet_warmonger` stable-key resolver；本轮不展开新查找。Religion identity/key 的 `2443D40` 与 `Religion+20 → definition+18` 已闭合，可在该独立 validity 包复用。

`knight_qualify_for_accolade` 的 enemy-participant条件保留**方向**：enemy participant 的 Faith → root Faith，`243E950(sourceFaith,targetFaith,false)`；不是 root adopted Rite→enemy Rite，也不是双方最大值。需先闭合真实 `any_side_participant` census（Army owners列表是否同构），再生成定向 pair ledger。现有 selected commander Rite hostility 不满足此 consumer。

最终 actual-frame资格需后续在获准机器/窗口由协调者读取；本轮到这条分支即停，没有采集或运行准备：

| 精确数据请求 | 用途与资格边界 |
| --- | --- |
| 当前 `.3` exact descriptor、source HEAD/DLL SHA、paused played Robert29829 普通战役 snapshot/native revision、requested full ProvinceID、同一 combat query occurrence | 绑定新 source leaf 的生产读取；日期相同的独立 religion query 不合并成 atomic epoch |
| 至少一个真实 commander 和一个真实 knight 的 Army/Regiment/Character provenance、raw adopted Rite ref、resolved full Rite/Faith IDs、完整 Boolean keys / completeness / reason | 证明新 candidate provider 实读；无需为测试改变人物宗教。参数合法空/absent、main/adopted不同与失败分支由专属 offline fixture覆盖 |
| `5D27B90` 实际 loaded source-order rows的 key、role+1B0、trigger+40、chance+110、effect+160 provenance；`5C69B4C` actual interval；`5D4BD6C` loaded named-side key及实际 Side scope | 完整 phase selection 的额外输入；不能用 stock manifest或default5补上，也不调用 executor `3765780` |
| 实际 CCombatSide ordered participant census及每个 participant Faith fullID、定向 Faith getter0..3结果/4 sentinel | 单独闭合 hostility consumer；不把假设的 unique Army owners当完整 census |

外层日期/局部RNG/full feedback是独立 engine-transition 依赖；paused source leaf不会证明 schedule尚待执行或下一 tick 的宗教状态。本轮 source-only包没有新的 live artifact、测试通过数或 forecast完整能力。

## 封存与报告

外置包：[phase-input-readonly-frontier](Z:/ck3_mod_rewrite_process_assets/g2-background-round6-20261006/phase-input-readonly-frontier/)。`CACHED-OPERAND-INVENTORY.json` 逐行列当前 manifest 的实际 refs；文件 SHA-256 `0bb56e3e14d481eccf69949266367df21eef8aa6ac4a606e1cb15d061f55c0b0`，与 [v7 effects](battle-phase-leaf-effect-fidelity-12003-2026-10-05.md) 的 canonical payload SHA属于不同哈希口径。`SOURCE-EVIDENCE.json` 保留读取片段、原路径和字节哈希；`RESEARCH-PLAN.json` / `MINIMUM-CONTRACT.json` / `FRAME-DATA-REQUEST.json` 将图与后续施工、实际帧依赖分开。

Oct6 / W41 **09:19 source-only里程碑**：完成最小输入包、Mermaid、六行具体 consumer与 exact RVA施工入口；当时 provider实现与资格尚未完成，原因是该轮只授权 source计划且本机禁止游戏连接。Root统一合并日报/周报字段，不编辑共享报告。

## 后续最小实现与唯一新验证

已写的 [候选 helper](../../ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12003_phase_rite_parameters.hpp) 只消费 combat query 中已有的实际 Character pointer。旧 played-Rite reader 的内部 `ReadRite` / stable-key copy 已抽为 [共享 copier](../../ck3_autonomous_player/native_bridge/include/xar_bridge/rite_boolean_parameters_copy.hpp)，旧 reader 和新 helper 调同一完整集合算法。没有用玩家专用 query 代替候选角色来源。

V2 commander 与 knight 行的 optional `phase_rite_parameters_v1` 已接入实际 collector、[独立 serializer](../../ck3_autonomous_player/native_bridge/include/xar_bridge/phase_rite_parameters_v1_serializer.hpp) 与 production normalizer。只有 exact `.3` adapter启用 helper；旧 `.2` 的缺叶子及旧 wire继续规范化为 `None`。实际 adopted Rite absent 为独立 `absent`，ref0保留；available 可有合法 absent source Faith。读取失败保留已读 raw/identity与 reason，完整集合标记 false且keys为空。它不添加 whole V2 input gap、不改 Monte Carlo gate。

[Python adapter](../../ck3_autonomous_player/src/xar_autoplayer/simulation/phase_rite_parameters_12003.py) 的 `PhaseRiteOccurrence12003` 明确携带 role、public source Army、Regiment与Character；`adapt_phase_rite_parameters_12003` 按该 occurrence消费规范化 V2叶子，同角色ID跨Army/role不合并。`apply_death_is_glory_modifier_12003` 只应用六行源码中的当前1.1 modifier，输入是该步骤前的running Q100000，不生成事件选择或整体 chance。V3 candidate loop复用同一helper与optional leaf serializer，`available=false` 和 advertisement保持原实际边界。

唯一新 [compound Python case](../../ck3_autonomous_player/tests/unit/test_phase_rite_parameters_12003.py) 经 **production full V2 normalizer → occurrence adapter →六行单步 consumer**：首次调用因 sparse checkout缺少已跟踪 `ck3_workshop_mcp` 导入依赖出现 harness RED，0 methods执行；保留原回执，最小 materialize该目录后，**方法首次实际执行 GREEN：1 method、0.010秒；进程1.3050092秒、exit0**。没有重跑旧 case或任何 passed path。覆盖 complete true/knownfalse、ref0、full generation、合法 source Faith absence、adopted/main来源分离、absent/unavailable/oldmissing、同Character多个occurrence、selected-enemy参数与signed Q100000 trunc0。

中央只需新 target **`xar_ck3_12003_phase_rite_parameters_test`** / 同名 CTest。它用 fake-memory callbacks运行实际 `ReadCombatSimulationInputs`，再投影 actual `AppendCombatCommander` / `AppendCombatKnights` 函数体，输出 `${CMAKE_BINARY_DIR}/ck3_12003_phase_rite_parameters_wire/` 下**五个新 wire**：`complete_true.json`、`known_false_main_different.json`、`zero_reference.json`、`absent_rite.json`、`unavailable_key.json`。`SERIALIZER-PROJECTION.json` 与 literal CPP是构建元数据，不计入 wire。子代理没有编译或执行 native fixture。

实现外置包：[phase-rite-parameters-provider](Z:/ck3_mod_rewrite_process_assets/g2-background-round6-20261006/phase-rite-parameters-provider/)。`FIRST-PYTHON-TEST.json/log` 保留导入 harness RED；`RETRY-PYTHON-TEST.json/log` 是首次实际方法 GREEN。`consume_new_phase_rite_wires.py` 是 Root首次新 native GREEN后才可执行的唯一生产消费 recipe；它消费刚产生的五个 wire，经过实际 commander/knight严格 normalizer与source adapter，不再次运行本 Python case或任何旧 wire。

尚未完成：中央 native build、新 CTest、这五个新 wire的生产消费、实际 paused candidate provider资格，以及上节列明的 warmonger/participant Faith hostility/loaded selection与完整 phase依赖。测试成功仅提高当前 Python输入合同资格，不声称完整 phase、forecast或人物未来最终状态。Oct6/W41的后续实现字段外置封存，由Root合并共享日报/周报。

## 中央首次编译与五个新 wire 资格

**2026-10-06 10:25:47.579963 Asia/Shanghai**，上述当时待办的中央 native 编译、新 CTest 与五个新 wire 生产消费已完成。当前叶子为 **static-ready：实际 collector、literal serializer、production row normalizer、occurrence adapter与单步 consumer 已离线贯通**；仍没有真实 CK3 frame或新的 live 资格。

Root中央修正批次的 exact native source为 `01d98c73ca42b91b5e39c827e32a07b1afe51479`，native build GREEN、124.917782秒。首次三个新 CTest于10:21:42 Asia/Shanghai开始并GREEN 3/3，含 `xar_ck3_12003_phase_rite_parameters_test`；进程0.4263953秒，CTest汇总0.38秒。来源为 [FIRST-THREE-READONLY-CTESTS.json](C:/codex-ck3-background/readonly-observer-batch/strict03/FIRST-THREE-READONLY-CTESTS.json)。此前中央两个 native RED由Root保留和修正；没有在本子线重新编译、重跑或扩展核查。

获准后，封存recipe首次且仅消费新目录 `C:/codex-ck3-background/readonly-observer-batch/strict03/cache-observers/ck3_12003_phase_rite_parameters_wire/` 的五个实际编译输出：complete true、known false/main different、ref0、absent Rite、key unavailable，**GREEN 5/5，0.2161987秒**。生产Python来源为 `Z:/gb0`，HEAD `07350179c3ac40f31f90e71bf0995087d9835c08`；native来源与生产HEAD分别记录。各wire的完整路径、SHA-256与逐occurrence结果见 [NEW-NATIVE-WIRE-CONSUMER.json](Z:/ck3_mod_rewrite_process_assets/g2-background-round6-20261006/phase-rite-parameters-provider/NEW-NATIVE-WIRE-CONSUMER.json)，serializer projection和CPP元数据未计作wire。

实际检查使用 production commander/knight严格行normalizer与 Army/Regiment/Character occurrence adapter：complete集合给出明确true或false；adopted Rite与main Rite不同时仍使用adopted来源；合法 Rite/Faith ref0保留；raw `0xFFFFFFFF` 的Rite缺席投影为独立absent与明确false；key读取失败保留 unavailable、已读来源与reason，拒绝产生chance值。root与selected-enemy-knight两种source path都消费同一角色叶子。running Q100000为 `100001` 与 `-100001` 时，true分支分别变为 `110001` 与 `-110001`，false分支原值保留。compiled-wire消费实际执行commander/knight的wounded、killed路径；六行支持及maimed路径的先前compound Python资格直接复用，没有重跑。whole V2 base readiness与input gaps保持独立，旧Python case、旧wire、子线native build/CTest及游戏操作均为0。

Oct6/W41资格字段外置于 `OCT6-W41-QUALIFICATION.json`，由Root合并共享报告。本次完成仅解除已观测 adopted-Rite Boolean operand的缺失；真实同query候选读取、native candidate admission/order、敌方Side participant census与方向性Faith hostility、actual loaded selection、局部RNG及完整反馈仍分别待闭合。下一 source-only包将专门研究 enemy participation occurrence→Faith getter来源，不与本资格提交混合；不改变整体V3 advertisement或forecast readiness。
