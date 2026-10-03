# R0002矩阵资格失败与R0005-CN夹具修复

2026-10-03，真实游戏验收语言按用户明确修正为**仅简体中文**，其他八语只做基本格式、键与占位符规范检查。R0001简中实际证据保留。R0002英语实机属于调试证据，不作为简中功能签核，不设置后续英文或多语言实机门禁。当前产品尚未发布。

## R0002实际观察

本机CK3 1.20.0.3、Steam build 25652598；运行候选为 `86302d2889d75f032554f4051babc6d4f17c9b3a`，16份production文件及7份R0004夹具。主线程普通GUI向Capua宣战，暂停日期raw53144328不变，原始整数差值为50威望／300虔诚，战争4、原生目标d_capua／2221。真实回读的主／次防守方、原生目标捕获存在性和身份四项均PASS，实际参战角色为Robert 31254、Richard 32512、Sergios 32909。只读原版Peace of God条件也实测为Capua／Salerno符合、Naples不符合；后者FALSE是正常负条件。费用仍区分CB预览200虔诚和操作总扣300虔诚，不声称独立捕获过附加分支执行。

该阶段49份输入保全于外置 `de-jure-R0002-gui-phase-R0001/`，报告内容按仓库canonical LF保存为 [英文调试回执](r2-gui-english-diagnostic-2026-10-03.json)，原始外置报告SHA-256 `e04de3fda6ebea70611696c1b00e04f08e5508acddba2c92a2af2b09f5e39d80`。这是公国修复效果的英语调试读回，不代表另外两档参战集合、完整结算矩阵、简中签核或原生和平入口通过。

随后主线程通过正常LoadGame界面重新载入原始暂停存档。真实014回读为raw53144328、角色31254、stress0、威望raw220000000／scale100000即2200、虔诚raw15000000／scale100000即150、无战争，证实此前GUI白和后态已丢弃，**没有与矩阵混用**。保存中的唯一djct.1队列随正常时钟执行，实际BEGIN一次，没有手工再触发init。

第一格公国进攻者胜利的八项语义marker均PASS，包括原生资格、真实参战方、捕获目标、双方目标县归属、战争结束、目标外县与已有县保持。第二格公国白和的AI不可用与不同realm均PASS，但 `duchy_white_peace_native_eligibility` 实际FAIL。旧夹具记录FAIL后仍强制 `start_war`，最终暂停raw53144448有战争16777220、目标2221、主守方32512；这个强制创建的战争不能把资格FAIL变成PASS。九格矩阵为**RED，未出现DONE**。

87份失败输入保全于外置 `de-jure-R0002-matrix-red-R0001/`，报告内容按仓库canonical LF保存为 [矩阵RED回执](matrix-red-evidence-2026-10-03-R0002.json)，原始外置报告SHA-256 `dd3c914889fd59ce46ea57ebdbc62ed6711f2a068cbe9555cc0358e27baad91b`。本阶段error-final.log与矩阵前error.log逐字节相同：17358字节、SHA-256 `5eed2d9d612a16c2ff11d39695be8ef6016985d888ba7dfda63c3a43b7f66942`。58条原有初载court_scene无效角色诊断原样保留；新增诊断字节为0，没有本轮同持有人重置错误。不能把该日志写成空日志或全部无错误。

## 诊断依据与边界

生产公国胜利保留 `add_truce_attacker_victory_effect`。安装版本 `00_war_effects.txt:1982` 在进攻者scope向主守方执行 `add_truce_one_way`；白和／战败也使用相同方向的原版停战政策。旧夹具每格恢复目标县持有人、补资源，却没有重置上一格的停战。这是原版源码支持的原因候选，R0002未在第二格开战前直接回读has_truce，因此不能宣称该历史现场唯一原因已经证实。

安装1.20.0.3真实原版 `events/councillor_task_events/chancellor_task_events.txt:623` 使用当前角色 `cancel_truce_one_way = scope:target`；本轮采用这一精确定向合同，不猜测不存在于原版脚本的remove_truce入口。原始文件SHA、片段与未执行的只读探针见 [原版合同回执](native-truce-contract-2026-10-03.json)。该探针可读原持有人／top liege、与玩家是否同realm及双向停战；本工作包没有向游戏发送它。

## 最小夹具修复与静态验证

根线程确认R0002停止与清理后授权修改生成器，本轮生产运行文件**改动0**。仅 `tools/gen_acceptance_fixture.py` 在每格恢复县后读取玩家向当格实际主守方top liege的has_truce；有则执行原版 `cancel_truce_one_way`，再次读取同方向has_truce。取消前后写入DIAGNOSTIC TRUE／FALSE，既不伪造通过，也不增加72条语义marker。资格判断为FALSE时记录原有FAIL，停止该格，不创建战争或安排下一阶段。

新外置夹具为 `C:/workspace/two-mod-maintenance-20261003/de-jure-fixture-R0005-CN/`。此前准备但未应用、未实机的R0005候选及所有R0001—R0004树继续原样保留。新输出7文件；共享Clausewitz parser解析全部5份脚本，九处start_war均位于原生can_declare_war条件内部；两次内存生成精确一致；72条唯一语义marker与R0004完全相同；变动仅三档events与fixture-contract。16份production hash逐项仍与冻结R0002来源相同，没有重复运行不变的生产static或构建。

精确生成器／新夹具SHA、结构检查和限制见 [R0005-CN修复复核](fixture-repair-review-2026-10-03-R0005-CN.json)，原始外置复核SHA-256 `5701053052ca3fe316237b9ecec41e82d99e4925802fd99306b0f454aefbb1fd`。外置检查器前两次误用共享parser的AST接口，分别出现Block不可迭代、Entry无children；修为现有Block.entries／Entry.value.entries后通过，公共parser未改。失败脚本和分类记录保留于 `de-jure-fixture-r0005-cn-harness-check-history.json`，不是CK3产品RED。

**R0005-CN仍为live NOT_RUN。** 新简中attempt应从原始clean暂停存档执行唯一init，实读每格停战前后条件，核对全部72条语义PASS、一次BEGIN／DONE及真实诊断。若再次出现实际资格或结算FAIL，保留失败后按证据修复，不能用计划或结构通过替代实机。脚本end_war覆盖真实生产CB结算，不覆盖原生和平按钮合法性、保存重载迁移、并发战争、自动军队或生产持久停战期限。

## 入库报告换行与身份

上述原始外置报告及第一份准备冻结原样保留。仓库对JSON要求LF，四份新增JSON仅规范化CRLF为LF，解析内容精确相同；canonical LF来源同时保存在外置 `de-jure-r3-doc-reports-canonical-LF-R0001/`，以这些来源bytes与仓库副本逐字节核对，避免提交时换行改变SHA。

| 入库报告 | canonical LF SHA-256 |
| --- | --- |
| [r2-gui-english-diagnostic-2026-10-03.json](r2-gui-english-diagnostic-2026-10-03.json) | `d83e7160ca4ff4363caeb72a0fd3d74c9db5ecb25764edb2e43fcb92bd8fea30` |
| [matrix-red-evidence-2026-10-03-R0002.json](matrix-red-evidence-2026-10-03-R0002.json) | `9eaf83345b815392c9032c7ceb493ad50ca32e729ac680c77de543f26282b7b1` |
| [fixture-repair-review-2026-10-03-R0005-CN.json](fixture-repair-review-2026-10-03-R0005-CN.json) | `5678501dae87071dc417610383a60a720ebb435e127bc5965eacbe3c4b08536d` |
| [native-truce-contract-2026-10-03.json](native-truce-contract-2026-10-03.json) | `7928bdc3877274218b6ef83ce741e0fa4cdf2cd64d9dc47033049e5bf8f745c7` |
