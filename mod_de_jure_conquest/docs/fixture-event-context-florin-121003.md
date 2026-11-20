# DJC R0002：事件上下文隔离候选

`machine_id: desktop-3fevhd2-1c74096080`；目标 CK3 1.21.0.3 Florin/build26785313，EXE SHA `859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28`。本次仅维护外置测试夹具、真实日志消费者及回归；五份生产脚本、战争目标策略、费用、AI 规则和原 72 谓词没有改动。

## 实际 R0002 事实

R0002 已正常退出，原日志和错误资格均保留：KINGDOM attacker 8/8 后，white_peace 只有 AI 不可用与两个 realm 不同通过，原 Native `can_declare_war` 为 FALSE，已知 .900 在 1066.9.24（9 自然日）暂停；最终 checker 仍为 RED 10/24，0 SAVE。

原 debug SHA `0e93e3b24171f4cef1d7ae59d7cf3ca5ceab08d019dc232e133aee85db5aac2f`，error 6204 B/SHA `fc4e65db35ba7149503f7c69e91feba8771f1d8fb5a632725c12efcbcd6859ad`。163 个同名布尔在首次成功与失败准备帧相同，排除这些已观测字段发生变化；不能将其外推为所有 Native 内部门相同。

失败帧真实 Root 为 Robert36423/d_apulia，主防守者 Richard37846/d_capua；失败时首都 Vannes2154、Root 为 Apulia2619。首次首都没有真实读回，不能倒推它相同。第 10873 行的永久 `target` 为 Dynasty2798/InternalKey1044019；八份重复 scope dump 显示同一个对象，且继承了大量世界初始化 saved targets。首次 Native TRUE 时的 incoming target 未读回，不能假定也为该 Dynasty。scope 污染是有据待检候选，尚非唯一原因。

a05 失败诊断第 390 行又设置 `save_temporary_scope_as = target`，实际出现“temporary target 'target' same name as permanent target”。三档 CB 的 pre_alias 查询都在该语句之前为 FALSE；依赖 reserved aliases 的后续 UI/group 读数不能当作干净资格。该错误不追改为已通过，也不删除原 merchant、weak formatter 或 stock GreatWall 错误。

## 最小受控准备

既有生成器新增显式可选 `--clear-inherited-target`，且必须同时提供 `--diagnose-eligibility`。无新参数时保留原默认 fixture 的字节和业务合同；普通诊断仍不清 saved target。

每个 Ready 保留原两自然日、压力、县主、独立性、truce、资金和外部领地准备谓词。只在该真实准备通过后：

1. 以 `djct_probe_frame_*` 独立 temporary aliases 记录真实 Root、原两 holder/两 top、goal、两首都及 incoming target/adventurer。所有引用都在存在性门内；未创建虚构 target 或 adventurer。
2. 记录 incoming target 是否存在、是否等于真实 goal、各身份是否仍相等，并查询原 `can_declare_war`。首次 Ready 也会记录，不推定其初态。首次或实际 pre-query FALSE 时只作一次 Root context dump，包含全部独立别名和真实引擎类型；失败 helper 不再重复八次整个上下文。
3. 仅显式参数启用时调用原版正式效果 `clear_saved_scope = target`。立即核对 target 不存在、Root/goal/原两 holder/两 top 身份相同；异常进入已知 .900，不能继续开战。
4. 同帧再记日期、查询同一个原 Native 谓词并复核身份。引擎查询后 target 是否重新出现另作观察，不无依据要求查询后仍不存在。随后进入原 72 谓词的原 Native 门，只有该门真实通过才按原路径 start_war。

`clear_saved_scope` 在当前 `00_artifact_badge_scripted_effects.txt:390` 等有真实调用者。`01_ep1_court_artifact_creation_effects.txt:1482` 实际把可为 title/house/dynasty 的 `$TARGET$` 保存为永久 `target`，是类型污染的具体来源候选；没有本次完整调用链证据，不能据此断定这次 Dynasty 来自该行。当前 `_casus_belli.info:74–75` 明确 valid_to_start 的 target 应为目标 title。

这个清理只处理夹具正在评估的事件上下文名字，不改变政府、头衔、资金、truce、旗标、日期或世界数据，也不直接设置生产期望的 goal 为 reserved target。所有临时别名均带独立前缀；不再覆盖 attacker/defender/recipient/target。需要这些 reserved scopes 的 UI/group helper 诊断明确省略，保留缺口，不制造假 scope。

## 消费与资格

新合同字段 `event_target_context="CLEAR-INHERITED-TARGET-BEFORE-NATIVE"` 显式披露该准备。日志消费者保持原 24/72 marker 计数，并额外要求每 cell 一次成对 pre/post、即时 clear 后不存在以及身份一致读回。缺失/错误/重复或错字段类型均拒绝；诊断不额外产生 PASS，不取代原 Native 门。

下一 fresh KINGDOM 可复用既有受控三 outcome 世界顺序，生成参数：

```text
python -B mod_de_jure_conquest/tools/gen_acceptance_fixture.py --tier kingdom --diagnose-eligibility --clear-inherited-target --output <D盘新fixture>
```

现场应分别报告 first 的实际 pre/post 和 white_peace 的实际 pre/post。只有真实同一 Root/date/goal/holders 的 preFALSE→postTRUE 才能给该有限上下文干预的因果证据；preTRUE→postTRUE 与 preFALSE→postFALSE 不得混写。软件候选、模拟回归或清理开关本身不证明产品已修、唯一原因、KINGDOM24、完整9cell72或实机错误清零。

原 .800/.900/.901、单 tier 18 日上界、三 fresh tier 汇总、普通 GUI 扣费和同局物理 SaveLoad 的独立义务均不变。所有本候选的新 Game/GUI/NativeABI/SaveLoad/完整产品实机结果均为 NOT_RUN。
