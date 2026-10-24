# 0.1.0 首次发布准备

状态：DRAFT／NOT_PUBLISHED。产品 Workshop ID 未分配，不预填其他产品 ID；用户本次已明确授权测试验收后发布。

标题拟用“宗族化密教 / Dynastic Esotericism”；描述源为 [BBCode](../../workshop/dynastic_esotericism_description.bbcode)，完整更新说明源为 [Change Notes](../../workshop/dynastic_esotericism_change_notes_0.1.0.txt)。当前文字描述目标行为；业务验收后按真实结果复核并冻结，不能以草稿推导已发布事实。

正式构建使用产品 Java／Quarkus CLI，从显式 allowlist 生成无内部 Workshop ID 的 staging、ZIP、逐文件 manifest。拟发布 tag `dynastic-esotericism-v0.1.0`，只有确定 source commit 后建立；Maven 使用默认 `mvn`，版本符合根规范。

流程按 [test-plan.md](test-plan.md) 的 REL-01 至 REL-07：先源码业务通过，后真实首发、公开全文与兼容标签、实际 Steam 下载及缓存加载、离线恢复、永久 initial-baseline changelog 与 master 推送。发布前冻结文本、预览图和构建来源的精确哈希。原生首次创建结果未知时保留回执并先核已创建目标，不重复 CreateItem。

正式发布前确认各语言处理符合仓库本地化流程；当前核心制作使用简体中文、英文。未实际运行的其他版本与多人均不宣称已通过。
