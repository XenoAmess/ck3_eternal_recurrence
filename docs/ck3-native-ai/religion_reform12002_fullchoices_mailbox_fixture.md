# CK3 1.20.0.2 full Doctrine choices owning caller fixture

2026-10-01：一个新 `/O2 /W4 /WX` owning caller 场景通过 **8 checks**。真实 `RunPlayerReligionDraftDoctrineChoicesMailbox12002` 完成 `TrySubmit → owner Drain → ReadCurrentDraftFullDoctrineChoices12002 → Finish → Wait/Reclaim → command_result`。游戏版本为 1.20.0.2，EXE SHA-256 为 `AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D`。

新的 caller 只包含冻结的 `religion_reform12002_query_mailbox_test.cpp` 内存与 owner pump helpers，并将旧 `main` 重命名。旧 12 case 主函数、R7 generic/named matrix 和 fullchoices provider matrix **均未执行或修改**。缓存保留冻结 production 对象；当前 mainthread、query envelope 与 religion context 三源及新 fullchoices reader/mailbox 两源按当前头重新编译。

## 实际输入与输出

唯一 `visible-four-slots` case 使用真实 backing：`window+0x790` 四个 48-byte selected slots，slot definition `+0x28`，definition group `+0xB08`，group source collection `+0x140/+0x14C`。四个 slot 的来源分别为 **6、6、3、0**，选中键为 `doctrine_a/b/g/j`，组为 `group_a/group_a/group_g/group_zero`。没有构造 popup 或利用 registry 替代当前 draft。

实际 binding 回调读取 definition 内的 ShouldDisplay、CanPick 和知识输入，并检查 actor、top scope、Prophet 实体指针。最终五条来源可选；同帧包含另一 slot 已选项的 duplicate exclusion、隐藏项、原生 CanPick 拒绝、知识与 Prophet 拒绝、零来源组。实际调用计数为 trigger 24、knowledge 9、Prophet 4，没有调用 popup/Tenet helper。未执行的短路字段由实际 serializer 输出 `null`，合法 `false` 保持 `false`。

原始协议由 C++ caller 输出，Python 只解析验证，未补写任何顶层 metadata：

- `type=command_result`、`protocol_version=1`、`ok=true`。
- `result.step=query-player-religion-draft-doctrine-choices-v1`。
- `result.domain_key=player_religion_draft_doctrine_choices_v1`。
- `result.backend_id=ck3-1.20.0.2-native-player-religion-draft-doctrine-choices-v1`。
- actual child 为 `result.player_religion_draft_doctrine_choices`，schema 为 `ck3_12002_current_draft_full_doctrine_choices_v1`。
- actual published revision 为 701，日期为 53175816，actor 为 50331652，capture epoch 为 owner pump epoch **3**。
- `available/draft_observed/doctrine_gates_complete=true`；完整四 slot/十五来源随 packet 交给 Python SDK owner。

## 验证与冻结

结果：`Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-reform\fullchoices-caller\attempt-001\result.json`，SHA-256 `c1aecf03c27736466e5d7437bc71963f5a2d72eb557ea13d7e1de3b5d96aecc6`。

原始 packet：`Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-reform\fullchoices-caller\attempt-001\wire\visible-four-slots.json`。receipt 保存 packet、所有编译输入与缓存对象的精确 SHA；`fullchoices-caller/final-source-package.json` 保存本工作包三份 owned source 的精确 SHA。

复现入口：

```text
tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\religion_reform12002_fullchoices_mailbox_tests.py --artifacts <new-Z-artifact-directory> --frozen-objects Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-reform\query-mailbox\attempt-003\O2
```

编译定义为 `XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_DOCTRINE_CHOICES_PRIVATE_QUERY_V1=1` 与 **fixture-only** `XAR_REFORM_MAILBOX_STANDALONE_ADAPTER=1`。精确新 production 源为 `religion_reform12002_fullchoices.cpp`、`religion_reform12002_fullchoices_mailbox.cpp`；定义与 source list 已交共享集成 owner。

## Readiness 与下一步

此证据只证明 **static-ready owning query wrapper**。fixture 将实际 generic `permitted_executor` 配为 exact fullchoices callback，真实队列 admission 与 drain 已执行；新的专用 `permitted_executor_religion_draft_doctrine_choices12002` 尚未在此验证。后续只需在共享 field READY 后执行独立单 case named wrapper；不要重跑本场景矩阵。

没有接触 CK3、pipe、UI、Steam，没有声明 live、完整宗教改革合法性或宗教 OODA。full Doctrine 候选闭合不代表 full Tenet gate、最终改革/创建合法性或动作 outcome 已闭合。日/周报告所需字段随 `fullchoices-caller/report-fields.md` 交协调者合并，Git commit/push 由 root collector 执行。
