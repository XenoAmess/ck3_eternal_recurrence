# H2743 受降代价：下一条只读 ABI 探针与不可观测边界

状态：**静态设计；未新增 live producer；`effect_projection_complete=false`、`material_complete=false`、`recommended_outcome=null`、`action_literal=null`。** 本页仅针对 H2743 WarID `16777231`、CK3 `1.19.0.6-steam23530548`、attempt-12 的守方投降选项。没有启动或附着 CK3，没有读取真实秘密、预演 effect、改变正式暂停帧或执行投降。

## 能从暂停前态取得什么

[#448 的 H2743 输入包](h2743-surrender-preaction-native-input-bundle-2026-09-29.md)已绑定 checkpoint SHA `A5012030DA500A4352EF79D1EA10269D45DD5D19DAC508E22DD835663A5106E9`、`native:3`、public/native revision `4/3`、raw date `53217264`、connection generation `1`。它给出目标 Title ID `[2128]`、当前 holder/liege、双方各七种资源余额、部分休战谓词和选项合法性。这些是**已读前态**，不是终战差额。`source_bytes_authenticated_here=false` 说明纯输入包没有重验原始存档字节，必须与原 attempt 的字节回执一起使用。

磁盘[双根校验器](../../ck3_autonomous_player/native_bridge/research/verify_h2743_surrender_root_coverage.py)本轮运行返回 `known_script_roots_bound_only`：六份原版脚本逐字节 SHA 匹配，`individual_county_de_jure_cb.on_victory` 和 `on_war_won_attacker.effect` 两个**最低必要**根与关键边仍在。它没有证明当前装载的全部根、实际分支或写集合；`all_enabled_roots_known=false`、`full_write_set_known=false`。原版 `war_on_actions.txt:1295` 会进入 FP2 付款 helper；`03_dlc_fp2_scripted_effects.txt:1234–1320` 的实际付款在 payer 上的 `pay_short_term_gold`，后续 `show_as_tooltip` 只是向 helper 展示同一金额，不能计第二次付款。

| 问题 | 目前可读或可算的输入 | 仍不能声称的结果 |
| --- | --- | --- |
| CB/title | 当前 War/CB index/key、目标列表及 Title2128 当前 holder/liege。 | 运行时 `scope:target`、`cb_prestige_factor`、完整 title/封臣 old→new；`setup_de_jure_cb` 和 resolver 会写 context/变更队列。 |
| FP2 真钱 | 双方当前 gold；脚本说明 helper 阵营决定 payer 为 primary attacker 或 defender。 | 哪些 helper 被标记欠款、各自贡献是否达阈值、真实 payer/金额、其他资源 effect、14 行 signed delta。 |
| 休战 | 脚本候选方向 `30097→29829`；部分 flexible/nomadic 前态；静态天数公式。 | SHORT/LONG/BORDER 的原生等价值、求值后天数、本次尚未写入的实际 expiry 与覆盖/合并结果。 |
| 装载效果 | 六份磁盘源码的必要根与边。 | 本 War 实际 loaded selector、全部 DLC/mod 根、条件 true/false、RNG、next-tick 与延迟 effect 的完整写集合。 |

## 最小 ABI 探针：先证明输入，不触碰效果

### A. FP2 角色变量与参战贡献

1. **磁盘静态阶段**：固定 EXE SHA `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`、上述 FP2 脚本 SHA `366469115EA2DED577B5DEB57DFD456340A1E2FA2D494DC2B20C36CB3FC5A710`，只反汇编定位角色 scoped variable 的**只读查找**、name/key 编码和 variant 值解码，以及 war contribution 的只读入口。为每条候选冻结完整 RVA 区间、指令 SHA、调用边、对象/返回值 ABI，并用磁盘负例检验字节漂移。现有 `ck3_11906.cpp` 的 `FindGlobalVariableValue` 只处理**全局**容器；其 `+0x10/+0x1C/0x20` 布局不得套用到角色变量。当前仓库没有已验的角色 owed-variable 或 contribution ABI，所以本阶段的实际状态仍是 `no_validated_character_variable_abi`。
2. **将来的暂停只读阶段**：先取得 H3937 同帧**完整**参战 roster、阵营、每人的 full CharacterID/generation 与 war contribution；缺一个参与者即不能给 FP2 总额。对每个 helper 双读 `owed_contract_assistance_war`、`owed_contract_assistance_contribution`、`owed_contract_assistance_gold`，并把 war 类型变量与本 War 的完整 ID/generation 比对。金额、贡献、阈值须保留原始定点值/类型和单位，不能由显示小数回算。需要证明「无变量」是完整容器查询后的真阴性，而非未知 key 或未扫完对象。
3. **纯数据候选**：只在全部 helper、阵营、变量、贡献及 `is_attacker_in_war` 等价性已证时，按源码比较 `war_contribution >= owed threshold`，列出每一笔 payer→helper 候选及求和。它仍只叫 `fp2_payment_candidate`；`pay_short_term_gold` 的实际金额语义、折扣/四舍五入、失败分支、其他 on_action effect 与完整净资源变化未闭合前，`signed_resource_delta=null`。不得用当前余额或“脚本未见显式赔款”填零。

新 DLL 须默认关闭这一查询，使用独立 candidate 名和新 SHA；每个底层读口只接受暂停同帧、精确 EXE、完整对象身份，双读并比较原生 revision、raw date、所有结果及前后 Snapshot。解析失败、异常、重入、指针/代次漂移、部分 roster、变量 variant 不认识、FP2 是否启用未知，逐域返回 typed unavailable，不能静默排除 helper。**不调用** FP2 helper、`war_contribution` effect、loaded-effect preview、`setup_de_jure_cb` 或任何会构造/修改容器的 accessor。第一条真正可实现的新读口应止于角色变量和贡献的原始前态，不发布终战净额。

### B. 当前有向休战槽与未来 expiry

[精确 EXE ABI 冻结](../../ck3_autonomous_player/native_bridge/research/g2_actual_truce_expiry_v1_abi.json)显示，`HasTruce` RVA `0x26631E0` 和 `GetTruceEndDate` RVA `0x2663250` 调用只读 relation lookup `0x2610840`；`CAddTruce` 的 normal/forced 路径 `0x2EDAD20`／`0x2EDB3A0` 使用 get-or-create `0x26108F0`、duration evaluator `0x3373000` 及槽清理。现有 `ReadRaiktorActualTruceExpiryV1` 又把 owner 固定为当前玩家 Robert。因此该 getter 即使 GREEN，也只返回**已经存在且已应用**的 Robert→某人关系；它不读取 H2743 投降后尚未产生的 Landolf→Robert expiry。

若需补一个安全前态读口，可在另一个默认关闭的候选中，把 owner 改成明确的 full-generation Landolf `30097`、toward 明确为 Robert `29829`；复用只读 relation lookup，双读当前 pair 的 `HasTruce`/end date，并确认 Snapshot 和对象身份不漂移。返回字段必须命名为 `preaction_existing_truce_expiry_date_raw`，无槽只报告 `no_existing_truce`。它可以帮助将来解释旧槽合并，却绝不能填 `post_surrender_actual_expiry_date_raw`。

原版 `00_war_values.txt:7–65` 给出 `max(730, 1825 - 450*flexible - 900*short + 900*long - 730*both_nomadic) * (border_raid_pair ? 2 : 1)`。五项谓词及 stock 求值语义全证后，也只可给 `script_candidate_days`。实际 expiry 取决于 `CAddTruce` 计算、旧槽覆盖/合并、日期单位和写入持久化；暂停**前**不存在可供读取的本次写后槽。不得调用 `0x3373000` 或 CAddTruce 来“查询”，也不得重试此前崩溃的 loaded-effect preview。纯数据模拟若不能逐条证明上述 native 语义，应停在 candidate days；写后实际值只可能来自另外获准的隔离副本自然执行与事后读回，不能冒充本帧观察。

### C. loaded effect selector

当前 War 的 CB 指针/index/key 只证明这场战争绑定哪个 CB；磁盘双根只证明源码边。没有已验的**无副作用** ABI 可从正式暂停态枚举实际编译节点、其全部条件、DLC/mod 注入根和 write set。下一步先做磁盘/内存**只读枚举设计**：冻结装载模块与 DLC/mod 集、root 注册表和 node 指针/source ID 映射，输出所有无法解释的节点；只有完整性与身份可证明，才考虑默认关闭的原生读取。单个 dispatcher callsite 或一次被动 trace 仅覆盖到达的节点，不能证明未到达条件为 false；现有[被动 observer 研究](h2743-clone-passive-observer-seams-2026-09-29.md)仍缺完整上下文和全树证明。找不到安全枚举入口时，`enabled_effect_tree.status=unavailable`，不得为了填 selector 调用 loaded-effect evaluator/preview。

## 门禁、实机前置与交付边界

静态只读研究可不占屏：运行六源 verifier、核 EXE 和 `g2_actual_truce_expiry_v1_abi.json` 的 RVA/字节/调用边，提交反汇编证据和负例。本轮以原版 `ck3.exe` 重跑冻结器，EXE SHA、PE 元数据、全部八个原生区间 SHA、调用边和方向槽断言通过；`--check` 最终仍因冻结 JSON 的**七项桥接源码 SHA** 旧值而报 `artifact is stale`。新只读结果保存在 `D:/ck3-research-artifacts/war31-h2743-20260928/h2743-truce-abi-recheck-20260929.json`，SHA-256 `4583CA633716891AF2981DFD6F45DFB9C8E48965DCDC3798E47F54BC1AC6F2FF`；与原 JSON 的差异仅是这些源码 SHA，**没有**原生 ABI 字段差异。旧冻结文件未覆盖，因此不能将整个旧 artifact 的 `--check` 记为 GREEN，未来新候选应另存自己的 ABI 产物和 source pin。

任何新 ABI 候选必须有精确源码 commit、新 DLL SHA、独立 workdir/attempt、普通及 `-O` 负例；拒绝旧 DLL 冒充新字段、错 EXE、错脚本、H2743 帧漂移、合成 backend、缺 roster/变量、对象 generation 变化、getter 方向反转、把旧槽标成未来 expiry、把 tooltip 计为第二笔付款。不能把静态通过写成 live ready。

未来若要受管实机读**前态**，先由高优先级屏幕任务释放并取得任务总线独占，核当次新鲜 Steam 离线原图；以 SHA 固定的 H2743 save/driver/sidecar、EXE、injector 和**新** candidate DLL 执行 no-launch/CLI 静态准入，另开 append-only attempt。只允许同一暂停会话的 snapshot 前后、baseline 双读与新 getter 双读；零日期推进、零投降、零 effect 求值。任何门 RED 保留回执并结束该 attempt；释放屏幕和进程后才能汇总。旧 attempt-12 和正式 Robert 帧不得改写。

完整 title/封臣 old→new、F、FP2 实际净支付、所有条件/第三方/延迟 effect、投降后实际有向 truce expiry，**没有一个**可由当前已验的暂停前态 getter 精确观察。另立授权的隔离 clone 自然动作实验可以得到反事实样本，但须精确资产/DLC/mod/起始帧绑定、至少两次独立 replay、完整前后与冷加载读回；它仍不是正式帧的只读预测，且不能单靠两次余额差证明条件树完整。本页不实施该实验。正式比较继续 `comparison=unavailable`，所有未证 material 字段为 `null`，也不构造终战动作。
