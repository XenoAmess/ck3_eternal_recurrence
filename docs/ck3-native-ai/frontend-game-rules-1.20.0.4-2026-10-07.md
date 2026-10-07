# Frontend game rules：本机 CK3 1.20.0.4 移植与构建

2026-10-07。本专题记录本机共享运行时及源码资格；实际 frontend Apply、独立 applied-instance 读回和产品实机仍待验收。构建绑定状态为 **LOCAL12004_BUILD_BOUND_NOT_PRODUCT_RUN**，不能授予 CCC/QOL/RMTM/TED 业务或 release 信用。旧 .3 实机、失败场与冻结输入原样保留。

本机升级为 **1.20.0.4 / build25734779**，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。原 frontend game rules 仅绑定 .3；现按本机有限命名函数、RIP操作数和VT/COL/type链的实际证据补 .4 profile，继续提供原规则选择、Next/Apply/Hide及独立应用实例查询。没有用统一RVA偏移猜ABI。[静态映射](C:/workspace/ck3-upgrade-20261006/ccc-frontend-rules04-readonly-map-agent-01/FRONTEND-RULES12004-STATIC-BINDINGS-06.json)保留完整来源。

## 精确隔离与原合同

原 .3 profile保留；.4由实际 `gui_abi_revision` 与 EXE SHA选择，native serializer输出同一环境的版本身份。Python只接受 .3/.4各自精确版本–SHA pair，混合pair拒绝；历史 `EXE_SHA256` export仍指 .3。实际 .4 Next `0x21DD6D0`、Apply `0x21DBD00`、Hide `0xBE9CF0`、getter `0x27F82D0`与各类型/布局证据在原映射中分别绑定。

当前owner/root/type/pair准入、两次稳定观察、原单次callback与禁止重放均保留。Apply ACK仍为 `applied_settings_proven=false`；只有之后独立读取当前真实 `CGameRuleInstance` 才能证明已应用，不以日志或按钮ACK代替。私有开关默认OFF不变，当前共享构建显式启用 frontend rules和原两个bookmark依赖；未扩展其他ABI或业务入口。

## 实际构建与相称验证

[共享READY packet02](C:/workspace/ck3-upgrade-20261007/local12004-runtime-build-01/LOCAL12004-SHARED-NATIVE-BUILD-BOUND-02.json)于06:04:11 UTC绑定全部来源，SHA `ae88112978f142b11eedb0dc932a898c3a1c0ad71249d9ab1e414a304062fb84`。来源基线 `38b0a9860f5c07269458fbcfcd5f8a09dfacb8d0`，source-index02包含7172文件、12个实际delta；[完整12文件patch02](C:/workspace/ck3-upgrade-20261007/local12004-runtime-build-01/local12004-complete-native-rules-python-build-fixes-02.diff) SHA `ba9bf1635faafa736e24d31aaa5a1af5051a4db719a9bdfa4e273a4de62602b0`。根操作者已检查patch适用性；正式合回提交单独记账，不改写冻结输入来源。

| 已有实际检查 | 结果及范围 |
| --- | --- |
| runtime compile/link build-execution05 | exit0，38.830744秒；13增量边、10编译单元，477个既有对象保留。实际编译属性和命令均由packet回链。 |
| rules Python contract02 | 17项PASS，8.854710秒；原 .3行为、.4 wire与混合身份拒绝，仅离线。 |
| host33 contract02 | 6项PASS，0.598040秒；精确身份、原owner/pump稳定门槛、启动通知正常选择及原managed completion/预算合同。 |
| native compound05 | 唯一组合检查编译exit0、执行exit0，执行0.081424秒；`/W4 /WX /UNDEBUG`，覆盖synthetic选择、Next/Apply/Hide、独立instance和混合身份拒绝。不是registered/live资格。 |

共享DLL为 [ccc-shared-build-frozen-02/xar_ck3_bridge.dll](C:/workspace/ck3-upgrade-20261007/local12004-runtime-build-01/ccc-shared-build-frozen-02/xar_ck3_bridge.dll)，8170496 B，SHA `6d42133f11d776bab72ed59c0732250ee5ead62b1217b141708f53e4d98fa290`；injector 39936 B，SHA `2f88068f48e817ee9c143f4e7d5529504f5d31395e660e30b30305ab7996b37d`。实际Defender精确路径回执verified，原路径保留、extensions/processes设置未变。构建lane未启动Steam或CK3。

两处实际构建修复保持现有开关语义：默认event-window binder也依赖只读faction environment binder，因此把 `ck3_12004_faction_alerts.cpp`纳入runtime，独立私有faction query/gift仍OFF；prisoner ransom动作OFF时显式消费未用的`step`参数，维持`/W4 /WX`。frontend私有macro只附加到实际消费的四个编译单元，避免无变化对象重编。build-execution01–04、compound02–04和host首轮错误保留；上述已有PASS无需重复。

## QOL原版源码契约

[QOL source review](C:/workspace/ck3-upgrade-20261007/xqol12004-vanilla-contract-01/CURRENT04-SOURCE-SEMANTIC-COMPARISON-01.json)确认所需19份当前 .4原版源码 **19/19 raw等于已完整审阅的 .3**，复用该完整源码审阅；七份关键QOL业务文件也等于已审阅 .3。与旧 .2 contract仅17/19 SHA相同，两个历史差异为 `common/scripted_effects/pam_effects.txt`和`common/scripted_triggers/00_religious_triggers.txt`。旧 .2两份全文不在既有归档中，旧 .2→当前完整语义差异仍未知，不把 .3/.4 raw相同改写成已证明旧 .2业务等价。

此次只增加 `tools/xqol_vanilla_1_20_0_4.json`来源契约及更新loader文件名；旧 .2 contract、原静态RED和产品业务字节保留。完整静态及九语格式一次PASS，0.417819秒，[FINAL02](C:/workspace/ck3-upgrade-20261007/xqol12004-vanilla-contract-01/XQOL-REVIEWED-SOURCE-CONTRACT-FINAL-02.json)回链实际结果。这里仅授源码/静态资格。QOL继续使用产品专属Source09 host33/PAM private host；当前CCC共享构建的两个PAM私有开关OFF，后续QOL需绑定其实际ON配置产物，不能借当前DLL授PAM实机信用。

## 尚待实际验收

由root持有本机现场，按既有卡绑定final source-index/DLL/host/profile及新鲜Steam离线证据，完成原frontend六工具真实选择/Apply与独立instance读回，再接各产品原业务和正常GUI/native/OS0条件。预算、markers和产品验收范围不变；本专题当前 **actual live NOT_RUN**，后续仅追加真实场、时间与结果，不覆盖历史，不预填产品PASS或发布完成。

## 2026-10-07 合回事实

根操作者逐字节比对12份源码与冻结source02，并采用已审阅的两份QOL来源契约；提交经普通fetch/rebase后成为 `cea89f9f13982d941c18e60904335214228fa6af`，已实际普通push到 `master`。主树工作区随后clean；冻结来源、正式产品tag和旧证据不随rebase改写。

## 2026-10-07 QOL/PAM 构建补充

QOL/PAM 独立构建已实际启用 religion context 与 personal parameters 两个私有读取开关，DLL 8588800 B，SHA `89642b8aeba5283f3f78281123b6e7a57a5f29f85f78e236c77385c7ec22bd76`。实际 build exit0、精确 EXE Defender 读回 verified；[PAM packet03](C:/workspace/ck3-upgrade-20261007/local12004-runtime-build-01/LOCAL12004-PAM-NATIVE-BUILD-BOUND-03.json)保留完整编译、配置与失败链接回执。CCC 原冻结DLL与source-index02不变。

两份 CMake 源码补丁将这两个宏限定到包含共享router头的完整19个消费单元，并在两个开关任一启用时登记33个既有纯数据provider；其他私有命令开关和广告资格不变。生产源码实际 CMake 配置成功，全部551份DLL编译输入的宏集合、FLAGS、INCLUDES与已构建PAM配置完全相同，仅归一化source root路径，无新增或缺失编译单元。[完整交付](C:/workspace/ck3-upgrade-20261007/local12004-runtime-build-01/LOCAL12004-NATIVE-MASTER-FIX-DELIVERY-01.json)回链这项验证。此项仍只授构建资格，产品实机待验收。
