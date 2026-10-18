# R05：一次性降低初始补给的公共研究夹具

2026-10-18 R207补正：实际0.999只减99900（Q100000），未形成低库存。新代码以`supply_loss_amount`表达绝对减量，旧fraction配置保留字节且仅作绝对减量历史别名；新公共full-wire/managed run绑定已接线。当前结论、原件与下一116.51751目标0的未实机边界见[实际单位与公共查询修复](episode04-r05-initializer-amount-common-wire-12004.md)。以下保留原候选及当时未验收事实。

本候选实现可复用的 `subtract_supply` 初始化，解决从 stock300 等待大量成功 updater 的场景准备成本。它只产生**受控初始库存**，不推进游戏日，不调用 updater，不改兵数；自然补给更新和实际饥饿扣兵仍各自待实证。R05、ordinary starvation 正例、影片及 ABC 信用均不增加。

编制机器 `machine_id: desktop-3fevhd2-1c74096080`，2026-10-18 UTC；代码依赖基线 `19024b4d79d818a88709c9932ca4eb364d81ef33`。目标 exact1.20.0.4 / Steam25734779 / EXE `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518` 是既持来源 pin，本次没有读/哈希 EXE、SDK、桌面、游戏启动或 native 构建。机器状态与实机资格不得外推到另一机器。

## 三个结果分别记录

| 阶段 | 本候选做什么 | 尚需真实结果 |
| --- | --- | --- |
| 初始条件 | 生成仅含一条 `subtract_supply = 0.999` 的人工决议；唯一 owner/location 目标、固定 character once flag、磁盘 claim、独立前后 typed 检查 | 实际决议可见/可选/一次 Confirm；同日同 PID/generation/Army/CArmy/ordered DATA 身份及逐 physical current/max/state 守恒，库存确实下降至 raw<1000000 |
| 自然更新 | 复用已有普通 exact-day 推进与 full-history 查询；本 initializer 的推进数为0 | 正常 callback 的实际 before/after stock、admission、真实 pointer bucket、loaded levels 和有效损耗参数 |
| 自然饥饿扣兵 | 复用现有 parent/writer consumer，不造新写兵接口 | 同场完整供给 writer，调用关联成立、writer 当场 stock<10、unique physical debit>0；preferred/residual 与其它来源分别列账 |

stock初始化到0仅能建立零库存起点；不能称拍到自然正库存耗尽。初始化后若仍≥10，记录 `supply_changed_not_low_stock`，保留 claim 并停这个初始化 lane；不换 prefix、换决议 key 或重复 Confirm。百分比显示和 stock clamp/base 分列，不能把源码显示格式写成实际算术通过。没有 `deplete_army_by_percentage`、spawn、改兵数、console 或内存写入。

## 真实入口与当前 native 边界

入口是现有 [公共 mod acceptance](../ck3-mod-upgrade-fast-validation.md)，由新独立 catalog `tools/ck3_mod_acceptance_r05_products.json` 选择 `r05-mechanism-research / initialize-ordinary-low-supply`。只提供 case data/adapter；host、source、DLL、injector 和配置仍由一份 common runtime manifest 选定。

```text
python -B -X utf8 tools/ck3_mod_acceptance.py plan --runtime <common-runtime.json> --products tools/ck3_mod_acceptance_r05_products.json --product r05-mechanism-research --case initialize-ordinary-low-supply
python -B -X utf8 tools/ck3_mod_acceptance.py prepare --runtime <common-runtime.json> --products tools/ck3_mod_acceptance_r05_products.json --product r05-mechanism-research --case initialize-ordinary-low-supply --case-inputs <r05-inputs.json> --prepare-output <new-external-preparation>
```

后续继续同一公共 `allocate / preflight / run / verify`，用其实际 `--prepared-case`、`--run-context`、keeper/Steam/容量/normal-close 参数；本页不另造 launcher。单独 `prepare_r05_low_supply_fixture.py --output <new-external-package> --province-id <actual-location>` 只生成可审核 mod，不启动游戏。`run_r05_low_supply_initializer_once.py` 是公共 adapter 复用的 request-relay 实现，不是替代公共入口的启动器。

输入 `r05-inputs.json` 使用公共现有结构：顶层 `state_dir`（新外置路径）、`saved_campaign`（save、bytes、sha256、player_id、date_raw），以及 `case_inputs`。后者绑定 normal source 的 `normal_checkpoint_receipt` / `normal_checkpoint_build_receipt` / `open_kaishek_preflight` 三个 `{path,bytes,sha256}` pin，四份 `plain_configuration` pin（`pdx_settings.txt`、`tutorial.txt`、`presets.txt`、`player/game_rules/presets.txt`），`province_id`，可选 `supply_loss_fraction` / `decision_key`，以及公共五项显式 `budgets`。`army_id` / `carmy_id` 可省略，由**当前加载后的 typed snapshot+Strength**唯一定位；若显式提供则必须与当前 ID 一致，不借旧 PID 的 Army/CArmy ID。原 readiness 最低1800秒继续由公共层处理，不延长 Root 当场总期限。

源 checkpoint 必须经原 `checkpoint_source` 库函数核对真实正常 Save、pure-vanilla 原始生命周期、exact build、actor/date/bytes/SHA；这只读取旧 bootstrap 的底层能力。原 `capture_bootstrap.load_prepared` 的 `enabled_mods=[]` gate 完全不改。新 profile 的 sole mod 通过公共 `materialize_product_profile` generic content carrier 挂在 `mod/product.mod`，metadata 明确 `research_fixture_mounted=true`、非 vanilla/玩家产品业务场。公共 helper 的 `fixture_mounted=false` 仅表示无第二份 fixture mod，不能据此把本场称作纯原版。受控场 Save 不倒灌为 pure-vanilla T0 或 ABC 输入。

本机 a35 的 CMakeCache 实际三项为 **OFF**：

```text
XAR_CK3_ENABLE_INGAME_DECISIONS_OPEN_PRIVATE_V1
XAR_CK3_ENABLE_INGAME_DECISION_ITEM_ACTIONS_PRIVATE_V1
XAR_CK3_ENABLE_INGAME_DECISION_OUTCOME_PRIVATE_V1
```

源码有独立 `.4` 版本分支，并非把 generic ingame UI 的 Army-only 支持外推成决议支持：`bridge.cpp` 专用 opener/actions → `IngamePrivateGuiIdentityAdmittedV1` → `.4` GUI revision/RVA/pin → keyed selected detail/owner dispatch；`.4` 决议常量单独在 `ck3_12004_ingame_decision_v1.hpp`。两个前端观察依赖 flags 在 a35 为 ON，三决议 flags 仍为 OFF。改为 ON 只是后续 coherent common native 的必要配置，不证明 loaded pins、实际 actor/receiver 或 GUI 能用。本 adapter先读真实 advertised capabilities，不足时在导航/效果前失败；当前没有此新场 native/cold/live 资格。

必需的实际能力为 query-army-strengths、activate-ingame-decisions、query/select-ingame-decision-item、confirm-ingame-decision-outcome、inspect-gui-window-tree、query-frontend-gui-route（完整协议字符串见代码 `REQUIRED_CAPABILITIES`）。动作复用现有 `ck3_open_ingame_decisions_v1` → `ck3_select_ingame_decision_item_v1(decision_key, expected_revision)` → 一次 `ck3_confirm_ingame_decision_outcome_v1(decision_key, expected_outcome="decision_closed", expected_revision)`；公共 revision 与 native revision 独立绑定。UI ACK/窗口消失与独立 stock/physical 后验分别保存。

## 唯一 Army 和混合兵种

优先由 Root 绑定旧正常 S0 的2644候选，新场必须新读：同一玩家 owner 在该 province 恰好一支 Army、native controllable、regular/state1、非 combat/retreat、gathering0、route完整空、full DATA/physical aliases 与持久 raw138 参照完整。R204 savednormal 的 retreat 状态不合格，不能仅换路径名追认普通场。

这里的 ordinary准入指**Army 当前业务状态**。regular Army 可以包含 raw138 为0和1的混合 DATA；initializer 原样保留分类与每个槽身份/人数，不盲拒整个混合军，也不为初始化要求 split。raw138不是本代码命名的 flag/enum，更不是供给损耗资格。至少20名 physical current 是防止明显过小样本的准备条件，**不是≥20名真实供给 eligible 的证明**。后续必须从当次 loaded参数、实际供给 eligibility/budget/parent/writer 判断哪些槽扣兵；不可补员与是否供给损耗分别解释。完整 Army 净人数也不能代替逐供给 writer 的 physical debit。

固定 once flag 对所有生成 decision key 相同。Root/state 内 claim 的身份使用 machine/PID/真实 process creation/episode/Army/CArmy，prefix 不参与 key；在 Confirm 前 fsync。成功、超时、结果未知或低库存未达成都不重投；原始 ACK 与独立后态保留。公共 host 仍持有 actual OS process 身份，initializer 不新建 SDK client、Arm、Resume 或日步。

## 实际离线预验及后续最小窗口

[原始 OpenKaiShek 回执](acceptance/2026-10-18-r05-controlled-low-supply/PREFLIGHT.raw.json)与[15项诊断](acceptance/2026-10-18-r05-controlled-low-supply/VALIDATE.raw.json)逐字节保留。本机 `D:/workspace/open_kaishek` commit `721bc276c94ee46d1c54668564b88ce0e2e4d5e5`，JAR SHA `6ac143ebf03f3e1a041dff01b2d808e60de8e289d18cebf9855682f0a80b6d82`；命令与4文件 corpus SHA 见 [语法预验绑定](acceptance/2026-10-18-r05-controlled-low-supply/script-preflight.actual.json)。CLI exit1：**root_scan parser GREEN，1文件836B/0诊断；validator RED，15 UNKNOWN_OPCODE**。旧profile `ck3-1.19.0.6` 的 fingerprint 不是目标 `.4`，没有 `.4` 决议语义资格；top-level IR/runtime GREEN 是另一个 synthetic demo，不计本 fixture。descriptor/两份 localization 仅绑定字节，未授语义验证。

15项未知覆盖 picture/reference、decision_group_type、ai_check_interval、selection_tooltip、is_shown、is_valid、add_character_flag、province scope、every_army_in_location、army_owner、this、subtract_supply、ai_potential、ai_will_do.base。它们的实际原版 scope/effect来源与 `.4` 专用 handler见[来源切片索引](acceptance/2026-10-18-r05-controlled-low-supply/source-index.json)。[本机原版决议文档](acceptance/2026-10-18-r05-controlled-low-supply/script-documentation-source.json)明确 effect 的 character scope、AI interval0表示从不检查、picture/tooltip/trigger字段及默认 confirm loc；当前 realm group实际存在。两语言已补默认 `_confirm`，836B决议本体不变。原版 `natural_disaster_army_damage_effect` 分别调用 subtract_supply 与 deplete；本生成器仅抽取前者。原版 supply-loss value 和英文显示支持“百分比”的来源解释，不授 native比例基数/clamp。

公共 prepare允许复用实际 parser GREEN 这一已覆盖子集，明确保留 validator RED/unsupported，不要求虚构完整 `.4` validator GREEN。若新生成 province/fraction/key 改变文件字节，须按新的 corpus 重新运行真实可覆盖语法预验并绑定新 pin；不复用本2644旧字节的预验。没有覆盖结果或实际语法 RED 时停在准备前。未来真实 CK3/MCP 承担 native scope/effect 的首次资格。

当前 case 合同止于一次初始化，`run_case` 返回后由公共层正常闭场，未接自然日循环。若下一场需要**同场**R05采样，实际代码接点是该函数的 `client.checkpoint('r05-controlled-initializer-outcome', result)` 之后、return之前：复用公共 `client.advance_day(days=1)`、现有 full-history 查询和 parent/writer consumer，并遵守Root当前有限预算；不能把以下下一阶段步骤当作本包已执行的动作。无需为此另加SDK/native primitive。

该下一阶段重新建立各 journal fence、loaded表、当场 rate/stock、真实 admission及 all30桶。若得到正低库存且实际负 rate足以一次归零，以**下一真实选中 callback**为目标；若桶/身份稳定，最多30个 exact自然日只是覆盖调度机会，不能保证成功，Root deadline/存储/退出余量先到则停止。初始化到0另记，不假造低→0镜头。使用 [既有自然执行卡](episode04-r05-next-starvation-12004.md) 与 `join_actual_supply_parent_writer_observations_v1`，preferred-only小计和 residual分类分列。后续自然 casualty 正例没有取得之前，研究总账保持原状态。

12项既有新增代码合同之后，本增量补了实际 parser-only 消费检查；最终精确运行次数、耗时和 stdout见[离线检查回执](acceptance/2026-10-18-r05-controlled-low-supply/offline-checks.actual.json)。这些检查执行真实生成器、公共 Selection/profile filesystem primitives、checkpoint库导入与 CommonRelay/once代码；SDK/OS-held process/native语义边界使用合成值，不是 CK3 业务通过。只需复跑这一必要新合同命令，不跑旧18矩阵。外置候选按通用存储策略48小时复核可重建派生物，小来源/结果记录180天复核；不是永久保留授权。
