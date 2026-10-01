# CK3 1.20.0.2 full Doctrine choices named queue fixture

2026-10-01：新专用 `permitted_executor_religion_draft_doctrine_choices12002` 实际 owning queue fixture 首次 `/O2 /W4 /WX` 构建与运行 **1 case / 7 checks GREEN**。游戏 exact-build 为 1.20.0.2，EXE SHA-256 `AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D`。

只运行一个与[已冻结 generic caller](religion_reform12002_fullchoices_mailbox_fixture.md)相同的 `visible-four-slots` 输入。新 fixture 清空 generic 及当前实际 header 内全部其他 permit，只设置此 dedicated field 为 `ExecutePlayerReligionDraftDoctrineChoicesMailbox12002`；随后走真实 `Run → TrySubmit → owner Drain → actual fullchoices reader → Finish → Wait/Reclaim → complete command_result`。没有 mock admission 或补写 DTO/protocol metadata。

四个实际 selected slots 的组来源数量为 6+6+3+0，共 15 条，最终五条可选。duplicate、ShouldDisplay false、CanPick false、knowledge/Prophet false 与 zero-source 直接复用冻结 backing，实际 trigger/knowledge/Prophet 次数为 24/9/4。actor=50331652、date_raw=53175816、snapshot_revision=701；capture_epoch 来自实际 owner pump，值为 3。

## 证据与 source 边界

结果：`Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-reform\fullchoices-named\attempt-001\result.json`，SHA-256 `02779edf9af8601a5b6be7c26c75dcc0656389076341d29d7ec0bb7e15829f1d`。

实际原始协议：`fullchoices-named/attempt-001/wire/visible-four-slots.json`，SHA-256 `ced894ce0769bef6a56896aee92b77604c002d284af9c703bce1944e36878bd8`。与冻结 generic packet **逐字节一致**，完整 `protocol_version=1 command_result` 中的 child 是 `result.player_religion_draft_doctrine_choices`，schema 为 `ck3_12002_current_draft_full_doctrine_choices_v1`。

runner 只将冻结 generic C++ helper 的外层 `main` 在 Z artifact 副本中重命名，保留其嵌套旧 main 重命名；没有改冻结源。新的 `main` 是唯一执行入口。旧 query 12 cases、generic fullchoices case、native provider matrix、R7 matrices 都没有再次运行。

当前 `main_thread_query_mailbox_v1.cpp` 与 `ck3_12002_query_mailbox.cpp` 两份共享源重新编译以消费实际 new named field，其余 production 对象来自冻结 O2 cache。receipt 保存精确源码、对象、helper 副本、当前 header permit 清单及 raw wire 哈希。新三源只包含 `fullchoices_named_test.cpp`、`fullchoices_named_tests.py` 和本文；精确完整路径及 SHA 在 `fullchoices-named/final-source-package.json`。

定义：production `XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_DOCTRINE_CHOICES_PRIVATE_QUERY_V1=1`；fixture-only `XAR_REFORM_MAILBOX_STANDALONE_ADAPTER=1`。本包没有修改 shared registration、CMake、runtime 或生产 provider。

## Readiness

此证据新增 **static-ready named queue fixture**，证明实际 dedicated runtime admission 与 complete caller output。InstallEnvironment 的 install/copy 传播、中央 Register/Populate/router 的 whole DLL 检查由共享集成 owner 独立交付，本单 case 没有执行安装过程。

未接触 CK3、pipe、UI、Steam，没有 live 或宗教动作 outcome 声明，也未把 full Doctrine 候选当作完整 Tenet/最终改革合法性。下一步由 root 用 paused 游戏读取本 query。日/周字段在 `fullchoices-named/report-fields.md`，Git commit/push 由 root collector 执行。
