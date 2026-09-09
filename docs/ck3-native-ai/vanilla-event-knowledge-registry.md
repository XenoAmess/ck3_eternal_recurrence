# CK3 1.19.0.6 原版事件知识 Registry

## 当前状态

- [static-ready] 共享 registry 已实现在
  `ck3_autonomous_player/src/xar_autoplayer/vanilla_events/`。它提供合同构建、冲突检测、`$player` 物化和 JSON-safe 查询；全部能力均为离线只读，不依赖已启动的 CK3。
- [static-ready] `ck3_query_vanilla_event_knowledge_v1` 已注册到正式 MCP server。它只按 stable event key 与 CK3 build 查询知识，不选择按钮、不推进时间、不修改存档或 registry。
- [static-ready] 本包默认扁平 registry 为 **165 个 unique vanilla event key**。原冻结迁移 key 集不变：`tgp_china_ministry.0100` 从 manager-original 抽成独立通用 owner 后，当前 legacy buckets 为 20 个 vanilla shard、56 个 manager-original、79 个 embedded-original，另由独立 records 接回同一 stable key；该抽取不新增 key。`.1101` 仍是上一轮唯一新增 key，因此总数保持 165；数量由 registry/migration 测试冻结。
- [static-ready analysis / mixed live evidence] 当前已提交包同时发布 **165 条 analysis** 与 **16 个 observation keys**。缺少已冻结 source hash 的旧结论只按既有合同注释、docs/tests 标为 migration-only，不编造 hash；`TGP0160`、`great_holy_war.0011`、`TGP0020`、`TGP0001`、`epidemic_events.1064` 及 R374 后续八个共享事件已完成 production runner 的真实 drain/advance。`stress_threshold.1721`、`epidemic_events.5009` 的第二次合法出现和已迁移条目的选择前 RED observations 均继续保留；第十四、十五个 observation 分别是 `faction_demand.2001` park8 与 `faction_demand.1101` park9 的选择前 RED，第十六个是 `tgp_china_ministry.0100` 的 foreground UI identity RED，不能当作 paused native observation；后续 GREEN 也不得删除既有 RED。
- [static-ready context profiles] prebootstrap 的 `spymaster_task.0381`、`spymaster_task.0399` 两条记录继续作为 seed-capture 上下文 profile 保存，不混入默认扁平 registry。它们与默认 manager 合同使用相同 event key、但冻结不同阶段的精确存档 shape，强行压平会造成有意义的合同冲突。

当前状态表示 registry、默认数据组合和只读 MCP 可以被静态消费者使用，不表示 165 条记录都已有独立 production-live exemplar，也不表示 CK3 自动玩家已经具备完整事件效用判断。production runtime 当前已提交包组合 `304` 条事件合同；共享 registry 的 production-live 标签严格只落在十三条已完成选择与 advance 的切片。park8 的 `faction_demand.2001` 是第十二条；park9 的 `faction_demand.1101` 已在 R374 同一 PID `51852` / generation `1` 选择 authored1/native0，instance `1055 -> null`、snapshot `native:2057 -> native:2058`、revision `2058 -> 2059` 且 postcondition GREEN，成为第十三条。因此十三条 GREEN 之外还有 `152` 条非 live 记录。该增量不改变 T0 产品进度。

T0 当前仍为 `50%`、canonical stage `8/11`，source checkpoint `3/4` 且只缺 `capture_cross_cycle_endgame`；T0-P1 未签收，T0-P2 继续 `LOCKED`。`strict 4/361` 与 `definitions 106/626` 只是非阻塞 backlog。

## Exact-build 边界

Registry v1 只支持：

- CK3 `1.19.0.6`；
- `ck3.exe` SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；
- canonical `event_definition_key`，例如 `ep3_decisions_event.2001`。

查询其它 build 会返回 `status=unavailable` 与 `unsupported_ck3_build`，不会从相邻版本猜测兼容性。v1 response 同时返回上述 EXE SHA，供消费者绑定 provenance。

当前扁平主键是 exact build 下的 stable event key。v1 尚未接收 playset 或 effective-definition fingerprint；如果其它 mod 覆盖了同名原版 definition，消费者必须将 stock 记录视为不适用，不能因为 key 相同就继续选择。将来若把 effective definition 纳入公共 schema，必须作为显式版本演进，不能改变 v1 的含义。

升级 CK3 后，即使 event key 未变，也要先重新比较定义、相关 ABI 和选项语义。旧 build 的静态记录或 live exemplar 不会自动升级成新 build 证据。

## Canonical ownership 与默认组合

共享 package 是原版事件合同的 canonical owner：

- `records_vanilla_shards.py`：20 条原版专题 shard；
- `records_manager_a.py`、`records_manager_b.py`：57 条 manager-original；
- `records_embedded.py`：79 条原先内嵌于 T0 runner 的 vanilla 合同；
- `records_tgp_movement.py`：当前独立 TGP movement 合同及其分析/观察元数据；
- `records_tgp_dynastic_cycle.py`：独立 TGP dynastic-cycle 合同及其分析/观察元数据；
- `records_tgp_treasury.py`：从旧 manager 条目抽出的 TGP 国库预算通用合同、exact-build 分析与 foreground UI identity RED；
- `records_vassal_interaction.py`：自动接受的封臣头衔索取信件的通用合同、exact-build 分析与选择前观察；
- `records_trait_specific.py`：按需登记的 trait-specific 原版事件合同、exact-build 调用/效果分析与实机观察；
- `records_death_management.py`：按需登记的新 death-management 原版事件合同、exact-build 调用/效果分析与实机观察；
- `records_faction_demand.py`：按需登记 claimant/peasant faction demand 的通用合同、exact-build 调用/效果分析与选择前实机观察；
- `records_analysis_vanilla_shards.py`、`records_analysis_manager_*.py`、`records_analysis_embedded_*.py`：把已有结论迁移为默认 analysis；没有既有 source hash 的条目保持 migration-only；
- `records_prebootstrap.py`：两条不进入默认扁平表的上下文 profile；
- `registry.py`：构建、物化与只读查询实现。

`build_vanilla_event_registry` 对合同、analysis 与 observations 做防御性深拷贝，并拒绝 metadata 引用未注册的 event key。重复 key 的 canonical JSON 完全一致时去重；内容不同时抛出冲突，并保持先前 active registry 不变。查询返回新的 JSON-safe 副本，调用方修改 response 不会污染 canonical record。内部 legacy tuple 到 MCP JSON 边界才投影为 array，metadata 的整数 option key 也只在 JSON transport 中规范化为字符串。

产品不应再复制共享原版事实并长期维护第二份权威定义。迁移期间可以保留 legacy adapter，但必须由定向 parity 测试证明它与 canonical record 一致；产品目录只应新增产品自己的用途约束和后置断言。

## Invariant contract 与 observation exemplar

Registry 将“可复用合同”和“一次实机看到的值”视为两种不同信息。

Invariant contract 用来匹配和处理事件，典型字段包括：

- root、named saved scope 的类型与相等/互异关系；
- source-reviewed 的 scope/option projection variants；
- authored native index、rendered option count 与选择映射；
- source 明确呈现但当前不可选的 native row；`disabled_native_option_indices` 只允许声明 `native_option_indices` 的严格子集，选择目标不得落入该集合；
- 日期/occurrence policy；
- 用于有界 drain 的 `selected_option_number` 与 `selected_native_option_index`。

Observation exemplar 记录一次具体运行的 date、event instance、角色 ID、实际 projection、artifact/checkpoint hash 和是否尝试选择。除非原版定义明确提供 exact anchor，这些值不能因为出现过一次就成为通用日期或人物合同。

v1 的 156 条迁移基线以保持现有 T0 合同逐值 parity 为首要目标，其中仍可能包含原 seed 的日期或人物锚；它们不能自动宣称已经完成全面的 campaign-neutral 归一化。新增或实质修订记录应逐步采用合同/观察分层，不能为了“清理数据”而破坏已经验证的 legacy 行为。

### 当前完整分层样例与首批 live 切片

`records_tgp_movement.py` 对 `tgp_movement_events.0160` 同时维护三块互不混淆的数据：

- `VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS`：默认 registry 消费的 campaign-neutral 合同，玩家用 `$player` sentinel 延迟绑定；
- `VANILLA_TGP_MOVEMENT_ANALYSIS`：exact build/EXE、四个原版来源文件 SHA-256、定义行号、yearly caller 与十年 cooldown、三个选项语义、`after_effect=None` 和 safe-option rationale；
- `VANILLA_TGP_MOVEMENT_OBSERVATIONS`：R372 paused-live exemplar，包括 artifact/hash、`date_raw=53436720`、instance `668`、本局人物 ID、scope raw type 和 `selection_attempted=false`。

R372/R374 的日期、instance 和人物 ID 不进入新建或已触达迁移后的通用 timeline contract。当前 MCP v1 的既有 knowledge envelope 以彼此独立的 `contract`、`analysis`、`observations` 字段返回这三层；本包全部 165 条记录已有 analysis，十六条拥有 observation metadata。元数据不会混入选择合同或被物化成当前人物约束。`.1101` 已进入默认静态组合，实际 MCP 查询返回 `available` 且三层投影均可严格 JSON 往返。

R372 已在同一 PID/session 上把 `TGP0160`、`great_holy_war.0011`、`tgp_dynastic_cycle_events.0020`、`tgp_dynastic_cycle_events.0001` 与 `epidemic_events.1064` 从共享记录解析到真实 option submission，并验证旧 instance 消失或 advance；R374 又把 `.7031` authored3/native2、`.1001` authored2/native1、`.1005` authored6/native5、`.0040` authored1/native0、`.4001` authored2/native1、`.1007` authored1/native0、`.2001` authored3/native2 与 `.1101` authored1/native0 依次同 PID drain 并验证 instances `978`、`988`、`1007`、`1038`、`1040`、`1046`、`1050`、`1055` advance，因此十三条均为 `production-live primitive`。`.1007` 的动作后 snapshot `native:1779 -> native:1780`、revision `1780 -> 1781`；`.2001` 的动作后 snapshot `native:1847 -> native:1848`、revision `1848 -> 1849`；`.1101` 的动作后 snapshot `native:2057 -> native:2058`、revision `2058 -> 2059`，三者 postcondition 均 GREEN。`stress_threshold.1721` observation 保留前一次真实 RED：共享模块 reload 实际已经生效，错误是 submission 阶段再次按 base contract 解析，导致提交了 base route；这不是 reload failure。`.5009` 的第一次交付曾真实 GREEN，第二次交付则证明旧 `max_occurrences=1` 错误。选择前 RED observations 不因后续 GREEN 删除。

park8 的 `faction_demand.2001` #1050 在 PID `51852` / generation `1` 选择 authored3/native2，instance `1050 -> null`、snapshot `native:1847 -> native:1848`、revision `1848 -> 1849`、`postcondition_verified=true`，现为第十二条 production-live primitive。package commit `3bb5169ca2b81701a8ea49e9d842de36f39fd87b` 已按 rebase-only push；Official Runner run `34404896747` / job `102645406781` 约 4 分 26 秒 completed/success、失败步骤为空。T2 `.2001` 兼容审计为 `NO-CODE-CHANGE`。

park9 的 `faction_demand.1101` #1055 动作前状态为 PID `51852` / generation `1`、date `53607792`、root/player `32904`、snapshot `native:2057`、revision `2058`、paused，且 `selection_attempted=false`、`process_restart_required=false`。四个实见 scope 为 `faction` faction/raw25、`peasant_county` landed_title/raw5、`peasant_leader` character `33633057`/raw4 与 `new_title` landed_title/raw5；native0/native1 均 shown/enabled、非 fallback/cancel。合同允许有限产品观察窗口内重复出现，并选择 authored1/native0。原版不是 daily pulse：满足不满门后按月检查，普通积累约 50 个月，高不满加成时约 7 个月，`MAX_DEMAND_DELAY_DAYS` 另保证最多 90 eligible days 后更新。接受在有效条件下损失 50 legitimacy；top-liege 路线对成员县扣 75 control、施加十年 modifier 并销毁派系，Dynastic Cycle 的 lower-liege 合法变体会升级为面向 top liege 的派系但不会在该按钮边界立即开战。拒绝则立即开农民战争、各成员县扣 25 control、生成军队，并由 CB 另扣 100 legitimacy。选择接受是避免立即战争的有界路线，不代表零代价。leader setup/war tail 中出现的 faith/struggle/Mandala 仅是附带语义，不扩展通用宗教策略。产品绝对 deadline `53635896`，动作前尚余 `28104` 小时、即 `1171` game days。commit `0880b4d579b92685be0696df5a5a32d701db5ed2` 推送且 Official Runner GREEN 后，R374 同 PID/generation 选择 authored1/native0，old instance `1055 -> null`、snapshot `native:2057 -> native:2058`、revision `2058 -> 2059`、`postcondition_verified=true`，所以该条已是第十三条 live。

`.1101` 的 exact-build analysis 冻结以下九份原版 source SHA-256：`events/factions/faction_demands.txt` = `B06241E67B6692F51FCFC6021E4DBE085C9E25A50B9CD08957CBCC9E25AEBEA9`；`common/factions/00_peasant_faction_new.txt` = `3B54AA8E610EC8F767B86F33F75A7D90A64FA199B0AC1AE37D59A476B4EC04E2`；`common/factions/_factions.info` = `FB47457AABE7C7DF78555B4DFBA74B8932DAE468C45EBB2D1381CADDC2B7E019`；`common/defines/00_defines.txt` = `C1ECA141C71EC1E741CA5336E01BB538EEFAEC05B0684EDEC477CFC9053C3807`；`common/scripted_effects/00_faction_effects.txt` = `C8E0B3C57665F775973BC8559166CD1F6414471CA25017800777C3C6466DC5D3`；`common/scripted_effects/06_dlc_ce1_legitimacy_effects.txt` = `DEE9D48221B49EF41490D04451ACD6DBFD4994A50EAD9D006F831F41A6247A83`；`common/script_values/00_faction_values.txt` = `4EE4098080B8C4536E74B047801F8715DD5EB0BCDCBAC04A8E3BF563D6555932`；`common/script_values/00_legitimacy_values.txt` = `13E43166356B5DD99358F435330B03CB9BE95AB5913280318B01681186E23A2E`；`common/casus_belli_types/00_peasant_war_new.txt` = `3429D8884AA45F09291B807B6931D7FCAA629458ECCEE59AE2EA682D69F46AAF`。park9 immutable report / driver-state / hot-recovery SHA-256 为 `BA39B64ACC3224E8F1F5D5C04719A04106430D7F2F2551DEC52CCEC514FC3AA6` / `78C84C846ED9D2F05AF153EC9302C4C3A85C645FD0B33316CD212B10E342C494` / `4E3B59B3EB6328939D2008BD2DD4138546C0224F76D62297D19415138DF577E6`。实际 MCP list/call 返回 available、三投影和 authored1/native0 JSON roundtrip；T2 为 `NO-CODE-CHANGE`，Python normal/`-O` 各 `42/42`、open_kaishek `3/3` GREEN。commit `0880b4d579b92685be0696df5a5a32d701db5ed2` 已按 rebase-only push；Official Runner run `34408112586` / job `102655870657` completed/success，约 3 分 31 秒、失败步骤为空；同 PID live retry 如上 GREEN。

`.1101` 动作后，CK3 前景可见 `tgp_china_ministry.0100`“宋国库”及三条简中选项，但 native publisher 仍给出 `paused=false / active_event=null`。截图 `_runtime/p2r374-active-boundary-continuation-live/park9-post-selection-ck3-screen.png` 的 SHA-256 为 `B2E57E4B90EC82EBA96500B7D0B1F963A6EE46F521E4E5250C1A3BE113C7047B`；它只以标题与三项 localization 精确匹配证明前景 UI identity，不能提供 event instance、date、root、saved scopes 或 option-state，也不能冒充 paused live observation。exact-build source SHA-256 已审阅：`events/dlc/tgp/tgp_china_ministry_events.txt` = `87358436D60431BC80DA0376DD1BB2C47696EFCDE813148C69883768439980EE`；`common/on_action/yearly_on_actions.txt` = `0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA`；`common/scripted_effects/10_dlc_tgp_scripted_effects.txt` = `AEF36B884DC5E315DD5C655BC96012FF9FA8BB46BB0AF2C18FA878C890907747`；`common/scripted_triggers/10_tgp_triggers.txt` = `8294C1D72ECC909428ABFBA27D6F10B127D796D2BEE350D1BB95024F36D60C99`；简中 localization = `6AD38C15CAE1CD3EAC713EDBC1566C7D42D8CE3B94291139F976C439020F8210`。source-reviewed 终止路线是 authored2/native1“维持原有分配方案”。该路线后来只为解开前景遮挡而通过明确标注的 visual-coordinate fallback 执行；随后以坐标关闭宣战通知、activity detail、唯一选项胜利窗并用 Windows `SendInput` 发送空格。以上都不是 MCP action，不能给 `.0100` 记 live；native instance/date/root/scopes/option-state 仍缺。该通用包已由远端 commit `b51ccd9` 推送；它从既有 manager key 抽取，因此 contract/analysis 总数仍为 `165/165`，新增的 identity-only RED 使 observation keys 变为 `16`。

visual recovery RED sidecar `_runtime/p2r374-active-boundary-continuation-live/r374-visual-recovery-red-evidence.json` SHA-256 为 `003875E75BB05A8CF74AF27760DDC311B9F504C3A9FA51F5E3FDBD01831AB4EC`，冻结 driver snapshot SHA-256 为 `B83EFAAA2574ACCDEF533C5F2B8A38BAC20255237D18D32C35B87D3F42F48F43`；它明确标记 `mcp_only=false / coordinates_used=true / send_input_used=true / production_live_credit=false`。driver command `#3200` 返回 `pause-map=submitted`，`#3201`--`#3355` 共 `155` 次均返回 `already_paused`，而旧 runner 仍未读到新 paused frame。因此 live 计数保持十三条，`.0100` 仍只有 UI-identity RED。

commit `ac6f63c` 已把 direct 幂等 map-control ACK 与 semantic 后置帧绑定在同一命令 deadline：矛盾时只提交一次并进入可热恢复 typed RED，不能继续自旋；normal/`-O` 定向测试与 Official Runner run `34413044308` / job `102671610904` GREEN。native 根因进一步缩到 ACK 决策与 publish 之间的二次读取：native adapter 已用一次可信 snapshot 判定 `already_paused` / `already_running`，bridge 却丢弃它并立刻做第二次全量读取；自动暂停边界的第二读可返回陈旧 `paused=false / active_event=null`。commit `9ccd3995418549b18f46190c3061ede5714c81e5` 已按 rebase-only push，把判定 ACK 的同一 snapshot 交给 timeline publisher，并在幂等 ACK 时强制发布；MSVC Release 定向 CTest `2/2` GREEN，新 DLL SHA-256 为 `18787F7F7F0A9BAF85C7D6979AB8AD20C8CF80D553AA6CA8D2AB87CF18DB0840`。Official Runner run `34415670708` / static job `102679886593` completed/success，约 4 分 36 秒、失败步骤为空。

该修复改变 DLL，故 R375 必须受管重启而不能原 PID 热加载。恢复基线是 `date_raw=53602440`、`144254384` bytes、SHA-256 `2B683351CF79ADE9DD5A931090DE8E6AF1D4F57FD65FFAFBB3CF18B7436BD97E` 的 `autosave`。R374 report 的 `target_progression.timeline_interrupt_drains` 共 `455` 条；按 `date_raw < 53602440` 严格裁切后保留 `453` 条，边界及之后的 `travel_danger_events.3002`、`debate_event.5110` 两条丢弃并重采。`.1101` 尚未写入该 ledger，所以是额外第三个重放事件；总回放窗口约 `223` game days / `3` events。只有新进程重新取得 native 同帧、MCP option submission 与 advance，才可为重新遇到的 `.0100` 增加 live credit。

`.2001` 的 exact-build analysis 冻结以下原版 source SHA-256：`events/factions/faction_demands.txt` = `B06241E67B6692F51FCFC6021E4DBE085C9E25A50B9CD08957CBCC9E25AEBEA9`；`common/factions/00_factions.txt` = `0A47171476811DD16EBD44A7335EAEBD17376FD87E41290F72B5C6785365B276`；`common/factions/_factions.info` = `FB47457AABE7C7DF78555B4DFBA74B8932DAE468C45EBB2D1381CADDC2B7E019`；`common/defines/00_defines.txt` = `C1ECA141C71EC1E741CA5336E01BB538EEFAEC05B0684EDEC477CFC9053C3807`；`common/scripted_modifiers/00_faction_modifiers.txt` = `CD3DAA9DA33C3DFD15934CA30C1B2D7381E0B3968337BF52A7CBC2F9F2237102`；`common/script_values/00_faction_values.txt` = `4EE4098080B8C4536E74B047801F8715DD5EB0BCDCBAC04A8E3BF563D6555932`；`common/on_action/faction_on_actions.txt` = `A4E3EDA2F31CB08D29DEAE1A1CDBD89256973A81FC1A1D4DF00D9CF5BBCB68FB`；`common/scripted_effects/00_faction_effects.txt` = `C8E0B3C57665F775973BC8559166CD1F6414471CA25017800777C3C6466DC5D3`；`common/scripted_effects/06_dlc_ce1_legitimacy_effects.txt` = `DEE9D48221B49EF41490D04451ACD6DBFD4994A50EAD9D006F831F41A6247A83`；`common/scripted_effects/00_war_effects.txt` = `A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D`；`common/casus_belli_types/00_civil_war.txt` = `CFF84009E58F5D6386A6D7501CFF084CB206A542E7D0CFA221ED2CC050A9DA68`。park8 immutable report / driver-state / hot-recovery SHA-256 为 `AC7EF0A37844A7F0B252917DAB0922B77721F0CAE6FB2A7416BC0F4420BCF9CA` / `FDFD7C0B2AB7DF6DC936B9FC01D611F1F5425BA6E571CBB74942BF08A68A9F28` / `89B4F2F8F6ADD2243C0CAD803766EB6B82491D0EF8E3C3BCCC6B55E5BC41B561`。park9 `.1101` immutable report / driver-state / hot-recovery SHA-256 为 `BA39B64ACC3224E8F1F5D5C04719A04106430D7F2F2551DEC52CCEC514FC3AA6` / `78C84C846ED9D2F05AF153EC9302C4C3A85C645FD0B33316CD212B10E342C494` / `4E3B59B3EB6328939D2008BD2DD4138546C0224F76D62297D19415138DF577E6`。

批量迁移 analysis 的证据等级低于带 exact source hash 的逐条审阅：它只复用已有合同注释、历史 docs 和 tests。若旧证据没有保存 source hash，metadata 必须明确写 migration-only；不得为了让字段看起来齐全而事后猜测 hash。

Prebootstrap 两条记录采用同一原则，但它们表达的是某个 seed-capture 阶段的精确上下文，不是默认 manager 语义，所以保留为命名 profile，而不是与同 key 的 manager record 竞争 canonical 扁平槽位。

## Safe-choice 语义

当前 v1 沿用经过原版定义审阅的：

```text
selected_option_number       # 1-based consumer 编号
selected_native_option_index # 0-based CK3 authored index
```

这里的 safe choice 只表示对既定用途的最小、有界 drain 路线，例如终止支线、避免新 follow-up 阻塞链、避免资源支付或保持当前任务；它不表示“最佳选项”“绝对无副作用”或完整 campaign utility。TGP0160 就明确记录：native 2 避免十五年 scheme block 和 gold transfer，但仍有少量 intrigue lifestyle XP 与 ambitious stress 影响。

消费者选择前仍须从同一 paused revision 验证 event key/instance、root/scope shape、shown/enabled 以及 native/rendered mapping：合同声明在 `disabled_native_option_indices` 的 row 必须 `shown=true && enabled=false`，其余登记 row 必须 `shown=true && enabled=true`，且 selected native 不得属于 disabled 集合。选择后须观察 event instance 消失或前进，以及用途需要的状态后置。Command ACK 不是完成证据。

若当前 projection 与合同不符、登记选项不可用或缺少满足当前用途的知识，消费者必须保留 paused RED，并按“查原版定义 → 最小修复 → 定向重跑”补记录。不得降级为 OCR 猜测、盲点第一个按钮，或把 `is_cancel_option` 当作无效果证明。

## Consumer 边界

### CK3 自动玩家

自动玩家和运维 agent 可以通过 MCP 读取当前 stable event key 的 canonical timeline contract，再结合 `current-event-window-context` 和 campaign policy 决定是否采用登记选项。MCP tool 已可调用，但 registry 不直接提交 `select-event-option-N`，也不自动替代现有策略层；选择、instance/revision 绑定和后置验证仍走既有 gameplay command 链。

Registry 是离线静态数据，因此另一台机器只需取得同一仓库/package revision 和依赖，即可通过同一 MCP 查询；不需要复制原机器的 CK3 进程、绝对 artifact 路径或用户存档。

### T0 天朝二期 validator

T0 的 migration parity 测试逐 bucket 对照旧合同，并冻结 `20/57/79` 数量、156 个迁移 unique key，以及两条 prebootstrap 有意 overlap；再加八个独立记录（含本包 `faction_demand.2001`），默认合同与 analysis 均为 164。后续 T0 consumer 应按实际产品路径查询或物化所引用的记录，并继续用产品自己的 window、occurrence、source checkpoint 和业务后置条件验收。

共享 registry GREEN 只说明引用的原版中断知识可解析且与迁移基线一致；它不能提升 T0 stage、四类 source、full-tree 或媒体 readiness。Prebootstrap validator 必须显式选择对应 profile，不能从默认扁平 lookup 取得 seed-capture shape。

### 其它 mod validator

其它 mod 可以复用默认 registry 的相同 event key，并在自己的 validator 中增加窄用途约束和产品后置条件。Validator 只检查该 mod 实际引用的记录；若 mod 覆盖同名原版 event definition，必须建立自己的 effective-definition 合同或返回不适用，不能修改共享 stock record 来迎合单个产品。

## 当前 read-only MCP

正式接口为：

```text
ck3_query_vanilla_event_knowledge_v1(
  event_definition_key,
  ck3_build = "1.19.0.6"
)
```

成功时返回：

```text
schema = xar.ck3.vanilla-event-knowledge
schema_version = 1
status = available
event_definition_key
ck3_build
ck3_exe_sha256
contract
analysis
observations
unavailable_reason = null
```

非法 key、未知 key 或不支持的 build 返回相同 envelope、`status=unavailable`，且 `contract/analysis/observations` 均为 `null`；`unavailable_reason` 分别为 `invalid_event_definition_key`、`event_definition_key_not_registered` 或 `unsupported_ck3_build`。

该 MCP 查询不访问 gameplay driver：离线测试用一个任何 backend 调用都会报错的 driver 验证 tool 仍可 list/call。接口不接受本地路径、人物 ID、按钮选择或写回 payload；返回记录是 detached JSON，不会修改服务端 registry。

## Migration 与兼容

- Schema 当前为 `xar.ck3.vanilla-event-knowledge` v1。消费者必须检查 schema version；未来破坏性字段语义变更应使用新版本，不能静默复用 v1。
- 迁移测试保证 legacy buckets 逐值相等、默认合同与 analysis 均精确覆盖 164 key，并拒绝意外 duplicate/conflict；默认组合故意不加入两条 prebootstrap context profile。
- `$player` materializer 只替换值完全等于 sentinel 的字段，不改写包含该字样的普通字符串，并返回独立副本。
- 查询边界统一将 tuple 投影为 JSON array，从而允许原 Python consumer 保持旧合同类型，同时让 MCP 跨进程、跨机器稳定序列化。
- 新 CK3 build、改变的原版 definition 或 mod override 都需要显式新证据；v1 不提供“相似版本大概兼容”的 fallback。
- Analysis 与 observation metadata 可以增量补充，但不能改变同一 timeline contract 的选择语义而不触发对应定向回归。

## 明确不是 `361/626` exhaustive gate

默认 164 key 是当前按需积累的复用资产，不是覆盖率目标。Registry 不要求在继续 T0、运行其它 mod、CI 或发布前枚举全部 `361` 个场景或 `626` 个 definition。

- `known/total` 只可作为 discovery telemetry，不能换算产品完成百分比；
- 未遇到、未引用的 definition 不进入发布或实机前置门；
- 缺失记录只阻塞真实停在该事件上的下游选择，其他非冲突工作继续；
- 全树扫描可以发现候选和重复项，但不能取代产品验收，也不能自动制造“必须全收录”的任务；
- T0 完成标准仍是主体工程、内容、约定测试矩阵与 hard-gated 最终媒体，不由 registry 数量决定。

Registry 的价值是让已经付出过的原版定义分析可以被下一次事件、下一条 T0 路径和其它 mod 复用，而不是建立一条无限扩张的全树验收线。
