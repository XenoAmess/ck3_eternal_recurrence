# 2026-10-10 本执行线职责纠正：只做天朝二期以外的mod迁移

用户本次明确纠正：“这些跟你有什么关系？你负责的是天朝二期以外的 mod 迁移。”上下文是执行者错误追问G2最新6067存档、12路证据及SDK/DLL可访问地址。此输入不再向用户索取，也不构成本执行线的等待项或完成条件。

本记录适用于当前C:/workspace/ck3_eternal_recurrence迁移执行线及任务总线ck3-upgrade-resume-20261006-root-01，不改变其他owner负责的天朝二期/G2任务。当前继续原十产品迁移清单内的未完成产品：XenoAmess体验优化QOL、重整河山、天朝特色361制现有公开版本0.3.0→0.3.1兼容/语言维护；仍保持361玩家产品最后。已完成七产品信用保留，分母仍10。

361既有版本维护与v0.4天朝二期运行时/领域新功能施工分开；本执行线不接手二期研发、资产、宣传或实机，不因产品同目录而扩展职责。G2研究、跨机资产调查/传输、6067恢复和长期游玩全部移出本执行线后续计划。既有薄调查只保留为发生过的历史记录，按统一存储策略到期复核，不追加预算或执行。

统一mod验收底座、必要MCP能力、源码/staging功能验收、正式上传、完整公开Change Notes与标签回读、真实Steam下载文件一致且CK3加载、正常闭场及永久changelog commit/push继续。共同底座中已有其他用途的代码不回滚，也不凭代码存在继续做超范围任务。

此前交接/日报中“迁移之后自动继续G2”的段落是本次纠正前历史计划，不能作为当前授权。本轮迁移闭环的完成判定不再依赖G2或天朝二期。廷臣具体礼仪等独立后续需求保持原交接记录，不纳入本轮迁移分母或自动扩成新功能工作包。

本纠正在R64实机活场期间先外置保全；待其11:46:53.979646Z真实CLOSED、allocator/keeper退出0及CAS8348释放后才由Root写入正式docs。结果见[R64](../xqol-r64-merit-qualification-2026-10-10.md)。

## 2026-10-13 用户再次缩减测试范围

当前先完成体验优化和重整河山，361不进入本轮。原版灵性满足、Offer资源算术、合法性、重复拒绝矩阵不属于两产品的迁移验收。已通过分项不因换场重复执行。

体验优化的当前`ui_tail`改为`persistence_smoke_v2`四项：实际读取anchor、保存100后重开读回、恢复anchor后重开读回、实际关闭面板回到干净地图。旧`representative_slider_v1`七项和原UI25控制分支保持，不把新四项称为旧矩阵全通过。保存0不再实机重复：生产`xqol.100`两个端点共用同一段draft→persistent赋值及dispatch，无按数值分支；这仅是静态同路径覆盖，不是save0实机PASS。自然重新启用仍是重开前提，不脚本清pending、不setfaith、不检查通知数量。

本机A204/R0094已实际记录anchor50、取消0后重开50、取消100后重开50，分别保存在其`case-output/ui25/action-0003.review.json`、`action-0008.review.json`、`action-0013.review.json`（SHA-256分别为`8808f82b98c88ea8a55ef2b44d15b2118afe76d76d8f89073b89a503bd0c299b`、`41f07484ab52397fcb2d25e1cac0bba59e9a42d66a17f72a1225cb4053d2ef94`、`976f3faeb66aaa9577565ad16bb88cb2f10c09b47fe4195fb10ec352a0646087`）。这些只能在最终报告单独引用，不能注入新场records。

A204随后因执行者在未暂停地图提交query-decision而被接口拒绝，安全清场；不是已证明的产品失败。其public run/verify均2、实际retained OS1/normal=false、allocator0/observer15/keeper0、CAS释放及closure3全true，失败原件保留。资源闭账为本机协调目录`focused-ui-a204-reviewed1gib-20261013-01-reservation-52-closed.json`，8437字节/SHA-256`d4776860aa13f4344a2143ce25b317eaf73e1868e8a53126f35fa4334b1da870`；不把资源CLOSED当成业务PASS。后续先暂停并确认当前snapshot再做决议语义查询。

离线回归`test_ck3_mod_acceptance_xqol_minimal_scope.py`实际8项及`test_ck3_mod_acceptance_xqol_ui_tail_binding.py`实际3项通过；历史inverse/原预算/readonly9/guard独立证据/normal0门槛未降低。这不代替尚待执行的保存读回。重整河山仅保留26步/D8核心继承链及50/51复辟门槛一次，不重跑36项或P4全矩阵。外置失败关键证据由当前迁移执行者保护至2026-10-18复核；当前有效基线、原始错误与生产输入继续保留，不凭失败或目录名自动删除。

### 同日 UI 执行工具故障与最小修复

A205/R0095正常OS0退出，但只记录anchor：public run0/verify2，保存100后的重开、恢复及清场仍为GAP。多次截图往返超过60秒，旧操作只刷新而未点击；不得追认为通过。其52闭账8786字节/SHA-256`36807b0cd662dbe3e1526624e64028b3a0be5ecf2aa254c9c7d0d49eddd59c89`。原观察器在游戏退出之后另因卷可用空间触线退出2，压力RED也保留。

A206/R0096实际target模板像素完全相同，但标题layout最大通道差21、相关度约0.99905，原1级量化阈值拒绝；`click_attempted=false`、`click_completed=false`，不是mod业务失败。旧控制器因此结束场次，原public run/verify均2，normal0退出及closure3独立完成；52闭账7799字节/SHA-256`b7a421e0fa54379437e338146e1ee98c680ed621571ce8e43ce4b26dc7059b16`。

当前控制器仅对明确唯一匹配、完全未输入的像素拒绝保留原结果并复核原PID/焦点/租约/期限后发布新sequence，交还执行者重新观察；不重放旧请求、不自动换锚、不授业务记录。歧义、守卫失败或任何输入尝试仍中断，像素阈值与预算不变。`reviewed_template_source`允许显式使用本场已亲审的旧原图：当前request仍绑定latest await，原模板helper自行采集新像素、匹配并走坐标门禁，不虚称自动截图已有人审。四项业务记录仍须亲审实际关键图。针对本次真实故障的3项离线测试和增量2项测试分别实际通过；这不是尚待补齐的GUI实机PASS。

本次存储回收均有逐文件小清单：`closed-a203-a204-retirement-20261013-01`实际回收3828文件/296768304字节；`closed-a205-evidence-retirement-20261013-01`实际回收3813文件/578270000字节。后者仅16条已结束完整传输重放用途的流、17张非关键中间PNG及A205生成shadercache；完整native报告、typed/业务读回、错误、压力、关键PNG、正常退出图、存档与当前输入保留至10月18日复核。已删原件不可读取，不制造替代原件，不改旧GREEN/RED/GAP。回执位于本机外置`ck3-upgrade-20261010`对应同名目录；实际可用空间独立复测，未按候选容量预先记收益。
