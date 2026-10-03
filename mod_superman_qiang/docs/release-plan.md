# 1.0.0 发布方案

工坊标题：**超人强：越超人越强**。当前是新原创产品，Workshop item ID 在实际 CreateItem 成功后才能记录。目标 tag：`superman-qiang-v1.0.0`。描述、封面、实机 media、完整 Steam Change Notes 是独立发布输入，必须冻结精确字节后提交。

遵循 [验收方案](test-plan.md) 及仓库 [独立模组开发范式](../../docs/ck3-mod-development-paradigm.md)。本文件记录计划，不提前写上传、订阅、公开 Notes 或实机已通过的事实。

## 包内容

发布构建仅包含声明的运行文件和资产。源码、生成器、文档、测试夹具及验收日志均排除。内层 `descriptor.mod` 不带 `remote_file_id`；canonical ID 保存到用户目录外层 `.mod`。构建器应支持原创产品没有 upstream ID，不设置假上游或哨兵身份。

原版效果接入投影由生成器产出，绑定准确的游戏来源与 SHA。正式验收和发布使用同一投影字节。简体中文做语义及实机验收；其余目标语言只认证格式，翻译候选按仓库 MiniMax 工作流生成。

## 发布事实与证据归档

正式报告保存在本产品 `docs/release-1.0.0-<date>/`，至少索引：

- source commit/tag、ZIP/manifest/staging SHA 和可复现构建结果；
- 原生 GREEN run 的完整 ID、游戏 exact build 与实机 evidence；
- Change Notes 冻结全文、归一化规则、字符数/行数/SHA；
- Workshop create/submit 收据、预览及实机 media 源与公开 CDN 回读；
- 匿名 item 详情及完整 changelog entry 精确回读；
- 真实订阅缓存下载和 manifest 核对；
- GitHub release 附件字节校验、外层 descriptor、Steam 离线恢复证据；
- 永久仓库 changelog 的 master commit/push。

历史/失败 attempt 永久保留，不覆盖。正式 tag 指向经审阅的源码；后续发布证据 commit 可以在其后，但不得重新解释或改写被验收 staging 字节。
