# 0.1.0 首次发布准备

2026-10-30T11:16Z，`machine_id: desktop-3fevhd2-1c74096080`：用户最新明确要求“现在立刻发布，发布以后继续剩余测试”，已据此公开更新同一条目3826991345至0.2.0。正式56文件来自Source98，当前后继工具提交不改变产品载荷；上传前后逐文件verify均0，原生Submit EResult1，公开标题/完整描述/全部标签/可见性/完整Change Notes均精确回读。Steam已由11:15:31Z后台原生探针确认恢复离线。完整Core与13用例、实际缓存加载及五张新实拍仍未完成，继续测试；这条明确指令覆盖旧稿的完整业务先行发布顺序，不降低剩余测试断言。见[0.2.0实际发布记录](acceptance/publication-0.2.0-2026-10-30.json)和[永久更新记录](../../docs/release-changelogs/dynastic-esotericism/0.2.0.md)。以下保留历史计划与0.1.0事实。

2026-10-25T13:30:38.536581Z补记，machine_id: desktop-3fevhd2-1c74096080：用户明确改为“先发布，然后继续本地验证；有问题修复验证后更新”。该最新指令取代下文历史草案的完整业务先行顺序。现已公开首发0.1.0测试版，Workshop ID 3826991345；实际Create/Submit EResult1，公共API全文/可见性/标签一致，Steam后台确认恢复离线。完整业务、缓存验收仍未通过，公开Change Notes页HTTP429待补查。首发实际正式包来源6241c6134ddb5a166f5c7228f3bf84b178487e74，25文件，manifest未预填tag；历史构建来源不改写。后续同条目更新仍须修复后验证。见[首发实际记录](acceptance/first-publication-2026-10-25.json)。

状态：DRAFT／NOT_PUBLISHED。产品 Workshop ID 未分配，不预填其他产品 ID；用户本次已明确授权测试验收后发布。

标题拟用“宗族化密教 / Dynastic Esotericism”；描述源为 [BBCode](../../workshop/dynastic_esotericism_description.bbcode)，完整更新说明源为 [Change Notes](../../workshop/dynastic_esotericism_change_notes_0.1.0.txt)。当前文字描述目标行为；业务验收后按真实结果复核并冻结，不能以草稿推导已发布事实。

正式构建使用产品 Java／Quarkus CLI，从显式 allowlist 生成无内部 Workshop ID 的 staging、ZIP、逐文件 manifest。拟发布 tag `dynastic-esotericism-v0.1.0`，只有确定 source commit 后建立；Maven 使用默认 `mvn`，版本符合根规范。

流程按 [test-plan.md](test-plan.md) 的 REL-01 至 REL-07：先源码业务通过，后真实首发、公开全文与兼容标签、实际 Steam 下载及缓存加载、离线恢复、永久 initial-baseline changelog 与 master 推送。发布前冻结文本、预览图和构建来源的精确哈希。原生首次创建结果未知时保留回执并先核已创建目标，不重复 CreateItem。

正式发布前确认各语言处理符合仓库本地化流程；当前核心制作使用简体中文、英文。未实际运行的其他版本与多人均不宣称已通过。

2026-10-24T10:43:27.089053+00:00 准备观察：`machine_id: desktop-3fevhd2-1c74096080`。Root直接审阅正式预览图（SHA-256 `3a81e6c88de042dc91ca88a0388b7a811be7030cbb3308a3e4a4e1813a40c17f`），标题与产品一致。只读 PE `symbols` 实际退出0：本机 Steam API DLL SHA-256 `1db3fd414039d3e5815a5721925dd2e0a3a9f2549603c6cab7c49b84966a1af3`、1065 exports、所需符号无缺失；原回执 `C:/ck3-dynastic-esotericism-20261024/publishing-readiness-a01/symbols.actual.json`。该命令未加载 Steam API、未联网、未创建物品或上传，不证明账号、EULA、发布及下载资格。
