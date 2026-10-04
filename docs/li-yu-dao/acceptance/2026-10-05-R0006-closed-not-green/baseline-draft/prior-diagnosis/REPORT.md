# 礼与道 R0006：完整运行错误分类与证据小包准备

结论：普通战役与正式入学的已保存快照 error 为零；打开 I2 资格夹具后出现运行显示／预览错误。本诊断完整解析实际 15,407,716 bytes error.log 的 **47,166** 个 [E]，整体仍为 **NOT_GREEN**。本包制作时退出和最终日志尚未完成，不记 normal_exit 成功。冻结源为 `3d3305e75cf642a7a82bef5f9aee03dc76b3c10e`。

实际失败快照路径是 `live-attempt-006/log-observations/i2-qualification-failed-001/error.log`，没有额外 logs 子目录。原 SHA-256 为 `6ee8a5cc3cdb3e13c558f1db3456552d810bfff49deebe761e37a45cb9f1d4ae`。[完整原字节无损压缩](raw/i2-qualification-error.raw.log.gz)解压后逐字节相同；原件仍保留外置，没有修改。

## 完整分类

| 类型 | [E]数 | 首／末本地时间 | 主要脚本位置 |
|---|---:|---|---|
| 条件本地化缺失 NOT_has_variable_trigger | 3 | 21:53:36 | fixture triggers line69、11、12各1条 |
| learning_delta变量未设置 | 15,721 | 21:53:36—21:58:03 | fixture effects line76 |
| var链接返回unset scope | 15,721 | 21:53:36—21:58:03 | fixture effects line76 |
| ScriptValue得到none类型 | 15,721 | 21:53:36—21:58:03 | fixture effects line76 |

按全部错误块的 **主要 Script location** 检查，夹具 47,166、产品 0、未知解析器／API 0、未分类 0；不是从日志尾部推断。3条本地化错误另引用原版 `00_debug_triggers.txt:157`，这是缺失显示文本的原版次级位置，不把它重复计成产品错误。另有资格决议 line18 的调用栈引用。[逐条分类](classification/all-47166-records.jsonl.gz)、[独立签名与首个原始块](classification/signatures.json)、[所有位置](classification/locations.json)可复核。

其中 31,442 条明确标注 while building tooltip/description，3条是条件显示本地化；15,721条none类型消息未显式标注tooltip，虽与同位置tooltip对成组出现，只能将关联写成推断，不能据此证明资格效果实际提交。没有Unknown trigger/effect/parser类错误，不代表该夹具功能成功。

## 快照与保存状态边界

formal-entry-001 原回执为13:06:45.878821Z，error.log实际0 bytes；其他阶段的完整原回执与error哈希见[报告](report.json)及 snapshots。普通战役／正式入学零错误与资格显示阶段爆发错误是各自的实际日志状态，不将后期失败倒写成早期失败。

保留六个已成功独立存档比较的 compact-summary、匹配 addendum、原INDEX和README：原版儒家夹具、正式入学、择师取消、朱子择师、祭修取消、朱子祭修A。每个只证明其显式场景；未重新解析存档，也不借六项PASS宣称R6整体GREEN。对应90MB原存档、12MB全图和完整读回包永久留在原外置位置，精确路径／SHA／bytes在compact与原索引中。本包只复制摘要与索引，不重复大文件。0027资格失败存档读回仍待另一个agent交付。

## 源码解释与后续小包

实际挂载的资格 effect 先set_variable计算学识差值，再在line76将该var交给add_learning_skill；native显示预览报告这条var未设置。[原挂载源码](source/mounted-i2-fixture/common/scripted_effects/lyd_r4_fixture_effects.txt)及display guards、decisions保留原字节。这个定位可用于后续修复显示预览，诊断没有修改源码或给未测试方案成功信用。

[永久包准备清单](permanent-package-plan.json)列出必须保留和仅索引的资产。退出后需另收最终error/实际process回读、keeper FINAL/CAS/allocator，才能冻结R6最终永久投影；当前包不冒充最终退出包。操作限外置只读诊断及投影：tracked/git/game/screen操作0，原资产不删改。
